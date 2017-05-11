#
# CFF.py
#
# Copyright © 2013-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'CFF ' tables in OpenType fonts.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.CFF import (cffbounds,
                         cffdict,
                         cffglyph,
                         cffindex,
                         cffutils,
                         charset,
                         charstrings,
                         encoding,
                         fdselect,
                         fontinfo,
                         privatedict)
from fontio3.fontdata import deferreddictmeta
from fontio3.utilities import walker, writer


# -----------------------------------------------------------------------------

#
# Private functions
#

def _bdc(x, **kwArgs):
    """
    Used as 'itemmethod' in cffindex. 'x' will be a StringWalker there.
    """
    b = x.rest()
    return b.decode('ascii', errors='replace')


def _bdcv(x, **kwArgs):
    """
    Used as 'itemmethod' in cffindex with validation. 'x' will be a StringWalker there.
    """
    b = x.rest()
    try:
        s = b.decode('ascii')
    except UnicodeDecodeError:
        logger = kwArgs.get('logger')
        s = b.decode('ascii', errors='replace').encode('ascii', 'backslashreplace')
        logger.warning((
          'V1066',
          (s,),
          "CFF string '%s' contains non-ASCII characters."))

    return s

def _ddFactory(key, d):
    chrstr = d['_charstrings'][key]

    if d.get('isCID', False):
        fdidx = d['_fdselect'][key]
        private = d['_privatearray'][fdidx]
        revcharset = None
    else:
        private = d['_private']
        revcharset = d['_revcharset']

    if d.get('doValidation', False):
        m = cffglyph.CFFGlyph.fromvalidatedcffdata
        logger = d.get('logger').getChild("glyph%d" % (key,))
    else:
        m = cffglyph.CFFGlyph.fromcffdata
        logger=None

    return m(
      chrstr,
      private,
      d['_globalsubrs'],
      revcharset,
      logger=logger)

def _numBytes(o):
    if o < 256: return 1
    elif o < 65536: return 2
    elif o < 16777216: return 3
    else: return 4

def _recalc_all(cffObj, **kwArgs):
    r = cffObj.__copy__()
    r._dOrig = cffObj._dOrig.copy()
    r._dAdded = cffObj._dAdded.copy()
    return(False, r)

def _sfloat(s):
    try:
        f = float(s)
    except ValueError:
        return 0.0

def _validate_glyphNames(d, **kwArgs):
    isOK = True
    logger = kwArgs['logger']
    for n in sorted(d):
        s = str(utilities.ensureUnicode(d[n]))
        if utilities.isValidPSName(s):
            logger.info((
              'V0929',
              (s, n),
              "The glyph name '%s' for glyph %d appears to be valid."))
        else:
            logger.warning((
              'V0930',
              (s, n),
              "The glyph name '%s' for glyph %d is not valid."))
            isOK = False

    return isOK

def _validate(d, **kwArgs):
    """
    .isValid() validation for CFF tables.
    >>> logger = utilities.makeDoctestLogger("CFF.isValid")
    >>> ed = utilities.fakeEditor(5)
    >>> ed.name = name.Name()
    >>> c = CFF()
    >>> ed.CFF = c
    >>> kw = {'logger': logger, 'editor':ed}
    >>> _validate(c, **kw)
    CFF.isValid - ERROR - The numGlyphs field in the 'maxp' table does not equal the number of entries in the CFF's CharStrings INDEX.
    False
    >>> for g in range(5):
    ...     c[g] = None
    >>> c.fontinfo.notice = 'Foo'
    >>> _validate(c, **kw)
    CFF.isValid - WARNING - The CFF 'notice' string 'Foo' does not match the name table copyright string 'Unknown'
    CFF.isValid - CRITICAL - Cannot validate CFF against the hmtx table because the hmtx table is missing or severely damaged.
    CFF.isValid - WARNING - CFF font has no GPOS (or the GPOS is damaged), but is non-monospaced. No kerning!
    False
    """
    logger = kwArgs['logger']
    editor = kwArgs['editor']

    isOK = True

    if editor.maxp.numGlyphs != len(d):
        logger.error((
          'V0940',
          (),
          "The numGlyphs field in the 'maxp' table does not equal the "
          "number of entries in the CFF's CharStrings INDEX."))
        return False

    # check CFF-stored names against 'name' table values
    if editor.reallyHas(b'name'):

        # CFF 'notice' vs copyright
        cfname = d.fontinfo.get('notice', '')
        if cfname:
            nname = editor.name.getNameFromID(0)
            if cfname != nname:
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'notice' string '%s' does not match the "
                  "name table copyright string '%s'"))
        
        # CFF 'version' vs version
        cfname = d.fontinfo.get('version', '')
        if cfname:
            nname = editor.name.getNameFromID(5)
            cfnamefl = _sfloat(cfname)
            nnamefl = _sfloat(nname.replace("Version ", ''))
            if cfnamefl != nnamefl:
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'version' string '%s' does not correspond "
                  "with the name table version string '%s'"))

        # CFF 'weight' vs subfamily name
        cfname = d.fontinfo.get('weight', '')
        if cfname:
            nname = editor.name.getNameFromID(17)
            if nname == u'Unknown':
                nname = editor.name.getNameFromID(2)
            if cfname != nname:
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'weight' string '%s' does not match the "
                  "name table subfamily string '%s'"))

        # CFF 'familyName' vs family name
        cfname = d.fontinfo.get('familyName', '')
        if cfname:
            nname = editor.name.getNameFromID(16)
            if nname == u'Unknown':
                nname = editor.name.getNameFromID(1)
            if cfname != nname:
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'familyName' string '%s' does not match the "
                  "name table family string '%s'"))

        # CFF 'fontname' vs psname
        cfname = d.fontinfo.get('fontname', '')
        if cfname:
            nname = editor.name.getNameFromID(6)
            if cfname != nname:
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'fontname' string '%s' does not match the "
                  "name table PostScript string '%s'"))

        # CFF 'fullName' vs full name
        cfname = d.fontinfo.get('fullName', '')
        if cfname:
            nname = editor.name.getNameFromID(4)
            # note, comparison is *both names* with spaces removed
            if cfname.replace(" ", '') != nname.replace(" ", ''):
                logger.warning((
                  'V1064',
                  (cfname, nname),
                  "The CFF 'fullName' string '%s' does not match the "
                  "name table full name string '%s'"))

    else:
        logger.error((
          'V1065',
          (),
          "Cannot validate CFF table against name table because the "
          "name table is missing or damaged."))


    # check CFF-stored advances against hmtx advances.
    if editor.reallyHas(b'hmtx'):
        for g in range(editor.maxp.numGlyphs):
            ca = d[g].cffAdvance
            ha = editor.hmtx[g].advance
            if ca and ca != ha:
                isOK = False
                logger.error((
                  'V0927',
                  (ca, ha, g),
                  "CFF advance %d does not match the hmtx entry %d for glyph %d"))

    else:
        isOK = False
        logger.critical((
          'V0928',
          (),
          "Cannot validate CFF against the hmtx table because the hmtx table is "
          "missing or severely damaged."))


    # VALIDATE-215. Why here? Specific to CFF...
    # re-visited January 2017. Logic:
    # kern or kerx present --> hasOldStyleKerning
    # hasOldStyleKerning and not(hasGPOS) --> Error (except typ1)
    # hasOldStyleKerning and hasGPOS --> Warning
    # not(hasGPOS) and not(monospaced) --> Warning ("should have kerning")

    hasOldStyleKerning = b'kern' in editor or b'kerx' in editor
    hasGPOS = editor.reallyHas(b'GPOS')
    isTyp1 = editor._creationExtras.get('version') == b'typ1'
    isMonospaced = False

    if editor.reallyHas(b'post'):
        isMonospaced = editor.post.header.isFixedPitch
    if not isMonospaced and editor.reallyHas(b'OS/2'):
        isMonospaced = (hasattr(editor[b'OS/2'].panoseArray, 'proportion') and
                 editor[b'OS/2'].panoseArray.proportion == 'Monospaced')

    if not hasGPOS:
        if hasOldStyleKerning:
            if isTyp1:
                logger.info((
                  'V1069',
                  (),
                  "Congratulations! You've found a rare bird: a CFF-based "
                  "'typ1' font with a kern or kerx table!"))

            else:
                logger.error((
                  'V1069',
                  (),
                  "CFF font has no GPOS but has kern or kerx table; this is "
                  "not supported."))
                isOK = False
              
        if not isMonospaced:
            logger.warning((
              'V1070',
              (),
              "CFF font has no GPOS (or the GPOS is damaged), but is "
              "non-monospaced. No kerning!"))
              
    else:
        if hasOldStyleKerning:
            logger.warning((
              'V1105',
              (),
              "CFF font contains a kern or kerx table. While not prohibited, "
              "it is probably not intended. CFF fonts can only make use of "
              "kerning in the GPOS table."))

    return isOK


# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CFF(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    Objects representing CFF tables. Note that the representation is
    abstracted to a (deferred) dictionary of glyphs plus some key
    attributes from TopDICT[0] as the 'fontinfo' attribute. Some
    structures/concepts that are part of a binary 'CFF ' table are not
    explicitly included here.
    """

    deferredDictSpec = dict(
        dict_recalculatefunc = _recalc_all,
        item_createfunc = _ddFactory,
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda i: "glyph %d" % (i,)),
        item_usenamerforstr = True,
        dict_validatefunc_partial = _validate,
        dict_keeplimit = 1000)

    attrSpec = dict(
        glyphNames = dict(
            attr_followsprotocol = True,
            attr_label = "Glyph Names",
            attr_validatefunc = _validate_glyphNames,
            ),
        fontinfo = dict(
            attr_followsprotocol = True,
            attr_label = "Font Info",
            attr_initfunc = fontinfo.FontInfo,
            ),
        )

    #
    # Methods
    #
    def _validateTightness(self):
        """
        Checks to make sure the keys are tight (that is, there are no numeric
        gaps and they start at zero). If they are not tight, an IndexError is
        raised.
        """

        minGlyphIndex = min(self)

        if minGlyphIndex:
            raise IndexError("The dictionary does not start at glyph zero!")

        maxGlyphIndex = max(self)

        if maxGlyphIndex != len(self) - 1:
            raise IndexError("There are gaps in the keys!")

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CFF object to the specified LinkedWriter.

        >>> d = utilities.fromhex(_testingData)
        >>> w = walker.StringWalker(d)
        >>> obj = CFF.fromwalker(w)
        >>> b = obj.binaryString()
        >>> b == d
        True
        """

        if self.fontinfo.isCID:
            self.buildBinary_CID(w, **kwArgs)
            return

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        cffstakes = {'cffstart': w.stakeCurrent()}

        self._validateTightness()
        umk = self.unmadeKeys()
        ceCopy = self.copyCreationExtras()

        # header
        w.add("3B", 1, 0, 4)
        offSizeStake = w.addDeferredValue("B", 1) # 'for all Offset (0)' (?)

        # Name INDEX
        fnbytes = utilities.ensureBytes(self.fontinfo.fontname)
        cffindex.buildBinary((fnbytes,), w)

        # Top DICT INDEX
        # MULTIPLE TOP DICTS NOT SUPPORTED - HARD-CODED INDEX FOLLOWS
        idxstart = w.getNewStake()
        idxinitial = w.getNewStake()
        idxend = w.getNewStake()
        w.add("H", 1) # count
        tdOffSize = w.addDeferredValue("B", 1) # offSize

        oFunc = cffutils.WriteIndexValue() # only for TopDICT
        idxbase = w._byteLength()

        w.addUnresolvedOffset(oFunc, idxstart, idxinitial, offsetByteDelta=1)
        w.addUnresolvedOffset(oFunc, idxstart, idxend, offsetByteDelta=1)
        w.stakeCurrentWithValue(idxstart)
        w.stakeCurrentWithValue(idxinitial)

        tdkeys = cffutils.topDictLabelDict
        resolvestring = cffutils.resolvestring

        fontstrings = ceCopy.get('_fontstrings', [])
        cs = self.glyphNames
        for s in list(cs.values()):
            # ensure we have all glyph names accounted for
            dummy = resolvestring(s, fontstrings)

        td = {}
        for k,v in list(self.fontinfo.items()):
            if k in tdkeys:
                tdk, ktype = tdkeys[k]
                if ktype == 'SID':
                    td[tdk] = (resolvestring(v, fontstrings),)
                elif ktype == 'array':
                    td[tdk] = v
                elif ktype == 'delta':
                    td[tdk] = v
                else:
                    td[tdk] = (v,)

        if cs.predefinedCharset == 0:
            pass # default; don't include
        elif cs.predefinedCharset in (1,2):
            td[15] = cs.predefinedCharset
        else:
            td[15] = 0xFF # dummy entry for offset

        enc = ceCopy.get('_encoding', None)
        if enc:
            if enc.predefinedFormat == 0:
                pass # default; don't include
            elif enc.predefinedFormat == 1:
                td[15] == 1
            else:
                td[15] = 0xFF # dummy entry for encoding

        td[17] = 0xFF # charStrings dummy entry
        td[18] = (0xFF,0xFF) # Private dummy entry
        if '_origTdAndOrder' in ceCopy:
            tdorder = ceCopy['_origTdAndOrder'][1]
        else:
            tdorder = sorted(td.keys())

        cffdict.buildBinary(
          td,
          w,
          originalOrder=tdorder,
          stakeValues=cffstakes)

        w.stakeCurrentWithValue(idxend)
        oFunc.maxoffset = w._byteLength() - idxbase
        w.setDeferredValue(tdOffSize, "B", oFunc.numBytes())

        # String INDEX
        cffindex.buildBinary(fontstrings, w)

        # Global Subr INDEX
        gsr = ceCopy.get('_globalsubrs', [])
        cffindex.buildBinary(gsr, w)

        # Encodings
        if 'encoding' in cffstakes:
            w.stakeCurrentWithValue(cffstakes['encoding'])
            enc.buildBinary(w, **kwArgs)

        # Charsets
        if 'charset' in cffstakes:
            w.stakeCurrentWithValue(cffstakes['charset'])
            cs.buildBinary(w, strings=fontstrings, **kwArgs)

        # CharStrings INDEX
        w.stakeCurrentWithValue(cffstakes['charstrings'])
        cs = []
        private = ceCopy.get('_private', privatedict.PrivateDict())
        for i in range(len(self)):

            if i in self._dOrig:
                # not modified; use the original binary charstring
                cs.append(ceCopy['_charstrings'][i])
            else:
                # modified; rebuild binary
                try:
                    obj = self[i]
                    if obj.isComposite:
                        cs.append(
                          obj.binaryString(
                            private=private,
                            accent=self[obj.accentGlyph],
                            base=self[obj.baseGlyph]))
                    else:
                        cs.append(obj.binaryString(private=private))
                except ValueError as exc:
                    # raise (new) exception, adding glyph id info
                    raise ValueError("Error building glyph %d: %s" % (i, exc.message))

        cffindex.buildBinary(cs, w)

        # offSize
        """
        For a non-CID font, the Private DICT is the largest possible
        offset pointed to from (0). So we can set header.offSize
        based on the current position.
        """
        w.setDeferredValue(offSizeStake, "B", _numBytes(w._byteLength()))

        # Private DICT
        w.stakeCurrentWithValue(cffstakes['privatestart'])
        pdkeys = cffutils.privateDictLabelDict
        pd = {}
        for k,v in list(private.items()):
            if k in pdkeys:
                pdk, ktype = pdkeys[k]
                if ktype == 'number':
                    pd[pdk] = (v,)
                else:
                    pd[pdk] = v
        if 'localsubrs' in private:
            pd[19] = private['localsubrs']

        cffdict.buildBinary(
          pd,
          w,
          originalOrder=private.get('origorder', sorted(private)),
          stakeValues=cffstakes,)

        w.stakeCurrentWithValue(cffstakes['privateend'])

        # Local Subr INDEX
        lsr = private.get('localsubrs', None)
        if lsr:
            cffindex.buildBinary(lsr, w)

        # Copyright and Trademark Notices (???)
        # Spec shows this on page 8. Does not make sense, since these
        # would be stored in StringINDEX and/or 'name' table.


    def buildBinary_CID(self, w, **kwArgs):
        """
        Adds the binary data for the CID-keyed CFF object to the
        specified LinkedWriter.

        >>> d = utilities.fromhex(_testingData)
        >>> w = walker.StringWalker(d)
        >>> obj = CFF.fromwalker(w)
        >>> b = obj.binaryString()
        >>> b == d
        True
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        cffstakes = {'cffstart': w.stakeCurrent()}

        self._validateTightness()
        umk = self.unmadeKeys()
        ceCopy = self.copyCreationExtras()

        # header
        w.add("3B", 1, 0, 4)
        offSizeStake = w.addDeferredValue("B", 1) # 'for all Offset (0)' (?)

        # Name INDEX
        fnbytes = utilities.ensureBytes(self.fontinfo.fontname)
        cffindex.buildBinary((fnbytes,), w)

        # Top DICT INDEX
        # MULTIPLE TOP DICTS NOT SUPPORTED - HARD-CODED INDEX FOLLOWS
        idxstart = w.getNewStake()
        idxinitial = w.getNewStake()
        idxend = w.getNewStake()
        w.add("H", 1) # count
        tdOffSize = w.addDeferredValue("B", 1) # offSize

        oFunc = cffutils.WriteIndexValue() # only for TopDICT
        idxbase = w._byteLength()

        w.addUnresolvedOffset(oFunc, idxstart, idxinitial, offsetByteDelta=1)
        w.addUnresolvedOffset(oFunc, idxstart, idxend, offsetByteDelta=1)
        w.stakeCurrentWithValue(idxstart)
        w.stakeCurrentWithValue(idxinitial)

        tdkeys = cffutils.topDictLabelDict
        resolvestring = cffutils.resolvestring
        fontstrings = ceCopy.get('_fontstrings', [])
        cs = self.glyphNames

        # unlike non-CID, we want to ensure that we do *NOT* include
        # our (synthesized) glyphnames in fontstrings (which later
        # becomes String INDEX), so we explicitly remove them.
        for s in list(cs.values()):
            if s in fontstrings: fontstrings.remove(s)

        fda = ceCopy['_fdarray']
        fds = ceCopy['_fdselect']
        pvtarray = ceCopy['_privatearray']
        td = {}
        for k,v in list(self.fontinfo.items()):
            if k in tdkeys:
                tdk, ktype = tdkeys[k]
                if ktype == 'SID':
                    td[tdk] = (resolvestring(v, fontstrings),)
                elif ktype == 'SIDSIDnumber':
                    kR = resolvestring(v[0], fontstrings) # Registry
                    kO = resolvestring(v[1], fontstrings) # Ordering
                    td[tdk] = (kR, kO, v[2]) # Supplement
                elif ktype == 'array':
                    td[tdk] = v
                elif ktype == 'delta':
                    td[tdk] = v
                else:
                    td[tdk] = (v,)

        if cs.predefinedCharset == 0:
            pass # default; don't include
        elif cs.predefinedCharset in (1,2):
            td[15] = cs.predefinedCharset
        else:
            td[15] = 0xFF # dummy entry for offset

        td[(12,36)] = 0xFF # fdarray dummy entry
        td[(12,37)] = 0xFF # fdselect dummy entry
        td[17] = 0xFF # charStrings dummy entry
        tdorder = ceCopy['_origTdAndOrder'][1]

        cffdict.buildBinary(
          td,
          w,
          originalOrder=tdorder,
          stakeValues=cffstakes)

        w.stakeCurrentWithValue(idxend)
        oFunc.maxoffset = w._byteLength() - idxbase
        w.setDeferredValue(tdOffSize, "B", oFunc.numBytes())

        # String INDEX
        cffindex.buildBinary(fontstrings, w)

        # Global Subr INDEX
        gsr = ceCopy.get('_globalsubrs', [])
        cffindex.buildBinary(gsr, w)

        # Encodings are not present/not allowed in CID

        # Charsets
        if 'charset' in cffstakes:
            w.stakeCurrentWithValue(cffstakes['charset'])
            cs.buildBinary(w, strings=fontstrings, **kwArgs)

        # FDSelect (CID only)
        w.stakeCurrentWithValue(cffstakes['fdselect'])
        fds.buildBinary(w, **kwArgs)

        # CharStrings INDEX
        w.stakeCurrentWithValue(cffstakes['charstrings'])
        cs = []
        for i in range(len(self)):

            if i in self._dOrig:
                # not modified; use the original binary charstring
                cs.append(ceCopy['_charstrings'][i])
            else:
                # modified; rebuild binary
                obj = self[i]
                if obj.isComposite:
                    cs.append(
                      self[i].binaryString(
                        private=ceCopy['_privatearray'][fds[i]],
                        accent=self[obj.accentGlyph],
                        base=self[obj.baseGlyph]))
                else:
                    cs.append(
                      self[i].binaryString(private=ceCopy['_privatearray'][fds[i]]))

        cffindex.buildBinary(cs, w)

        # FD INDEX (CID only)
        w.stakeCurrentWithValue(cffstakes['fdarray'])
        cffindex.buildBinary(fda, w, isFD=True, cffstakes=cffstakes, **kwArgs)

        # Private DICTs from FDs
        pdkeys = cffutils.privateDictLabelDict
        for i,private in enumerate(pvtarray):
            pd = {}
            for k,v in list(private.items()):
                if k in pdkeys:
                    pdk, ktype = pdkeys[k]
                    if ktype == 'number':
                        pd[pdk] = (v,)
                    else:
                        pd[pdk] = v
            if 'localsubrs' in private:
                pd[19] = private['localsubrs']

            w.stakeCurrentWithValue(cffstakes['privatestart%d' % (i,)])

            cffdict.buildBinary(
              pd,
              w,
              isFD=True,
              stakeValues=cffstakes,
              originalOrder=private.origorder,
              privateindex=private.index,
              **kwArgs)

            w.stakeCurrentWithValue(cffstakes['privateend%d' % (i,)])

        # offSize
        """
        For a CID font, the last Private is the largest possible
        offset pointed to from (0). So we can set header.offSize
        based on the current position.
        """
        w.setDeferredValue(offSizeStake, "B", _numBytes(w._byteLength()))

        # Local Subr INDEXes from Privates
        for i,pd in enumerate(pvtarray):
            if 'localsubrs' in pd:
                w.stakeCurrentWithValue(cffstakes['lsrstart%d' % (i,)])
                cffindex.buildBinary(
                  pd.localsubrs,
                  w,
                  **kwArgs)

        # Copyright and Trademark Notices (???)
        # Spec shows this on page 8. Does not make sense, since these
        # would be stored in StringINDEX and/or 'name' table.


    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        """
        km = kwArgs.get('keepMissing', True)

        r = self.__copy__()

        ce = r.copyCreationExtras()

        chrsr = ce.get('_charstrings').glyphsRenumbered(
          oldToNew,
          keepMissing = km)
        ce['_charstrings'] = chrsr

        cs = ce.get('_charset', None)
        if cs is not None:
            csr = cs.glyphsRenumbered(
              oldToNew,
              keepMissing = km)
            ce['_charset'] = csr
            ce['_fontstrings'] = [v for k,v in sorted(csr.items()) if v not in cffutils.stdStrings]

        enc = ce.get('_encoding', None)
        if enc is not None:
            ce['_encoding'] = enc.glyphsRenumbered(
              oldToNew,
              keepMissing = km)

        fds = ce.get('_fdselect', None)
        if fds is not None:
            ce['_fdselect'] = fds.glyphsRenumbered(
              oldToNew,
              keepMissing = km)

        r._creationExtras = ce

        for o,n in list(oldToNew.items()):
            if o in self._dOrig:
                r._dOrig[n] = self._dOrig[o]
            else:
                r._dAdded[n] = self._dAdded[o]

        r.glyphNames = self.glyphNames.glyphsRenumbered(
          oldToNew,
          keepMissing = km)

        return r


    #
    # Class methods
    #

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CFF object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> d = utilities.fromhex(_testingData)
        >>> w = walker.StringWalker(d)
        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = CFF.fromvalidatedwalker(w, logger=logger)
        test.CFF.Name.INDEX - DEBUG - Walker has 143 remaining bytes.
        test.CFF.Name.INDEX - INFO - INDEX count: 1
        test.CFF.Name.INDEX - DEBUG - offSize = 1
        test.CFF.TopDICT.INDEX - DEBUG - Walker has 120 remaining bytes.
        test.CFF.TopDICT.INDEX - INFO - INDEX count: 1
        test.CFF.TopDICT.INDEX - DEBUG - offSize = 1
        test.CFF.Top.DICT - DEBUG - Walker has 30 remaining bytes.
        test.CFF.String.INDEX - DEBUG - Walker has 85 remaining bytes.
        test.CFF.String.INDEX - INFO - INDEX count: 3
        test.CFF.String.INDEX - DEBUG - offSize = 1
        test.CFF.GlobalSubr.INDEX - DEBUG - Walker has 55 remaining bytes.
        test.CFF.GlobalSubr.INDEX - INFO - INDEX count: 0
        test.CFF.CharStrings.charstrings.INDEX - DEBUG - Walker has 53 remaining bytes.
        test.CFF.CharStrings.charstrings.INDEX - INFO - INDEX count: 2
        test.CFF.CharStrings.charstrings.INDEX - DEBUG - offSize = 1
        test.CFF - INFO - PrivateDICT length is 45
        test.CFF.Private.DICT - DEBUG - Walker has 45 remaining bytes.
        >>> d = utilities.fromhex(_testingData2)
        >>> w2 = walker.StringWalker(d)
        >>> obj = CFF.fromvalidatedwalker(w2, logger=logger)
        test.CFF.Name.INDEX - DEBUG - Walker has 143 remaining bytes.
        test.CFF.Name.INDEX - INFO - INDEX count: 1
        test.CFF.Name.INDEX - DEBUG - offSize = 1
        test.CFF.TopDICT.INDEX - DEBUG - Walker has 120 remaining bytes.
        test.CFF.TopDICT.INDEX - INFO - INDEX count: 1
        test.CFF.TopDICT.INDEX - DEBUG - offSize = 1
        test.CFF.Top.DICT - DEBUG - Walker has 30 remaining bytes.
        test.CFF.String.INDEX - DEBUG - Walker has 85 remaining bytes.
        test.CFF.String.INDEX - INFO - INDEX count: 3
        test.CFF.String.INDEX - DEBUG - offSize = 1
        test.CFF.String.INDEX.[1] - WARNING - CFF string 'b'T\\\ufffdmes Roman'' contains non-ASCII characters.
        test.CFF.GlobalSubr.INDEX - DEBUG - Walker has 55 remaining bytes.
        test.CFF.GlobalSubr.INDEX - INFO - INDEX count: 0
        test.CFF.CharStrings.charstrings.INDEX - DEBUG - Walker has 53 remaining bytes.
        test.CFF.CharStrings.charstrings.INDEX - INFO - INDEX count: 2
        test.CFF.CharStrings.charstrings.INDEX - DEBUG - offSize = 1
        test.CFF - INFO - PrivateDICT length is 45
        test.CFF.Private.DICT - DEBUG - Walker has 45 remaining bytes.
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('CFF')
        else:
            logger = logger.getChild('CFF')

        tblStart = w.getOffset()

        # read header
        if w.length() < 4:
            logger.error(('E2311', (), "Insufficient bytes for CFF header."))
            return None
        hdrMaj, hdrMin, hdrSize, offSize = w.unpack("4B")

        # read Name INDEX
        if w.length() < 4:
            logger.error(('E2311', (), "Insufficient bytes for CFF Name INDEX."))
            return None
        sublogger = logger.getChild('Name')
        nidx = cffindex.fromvalidatedwalker(w, logger=sublogger, **kwArgs)
        if len(nidx) != 1:
            logger.error((
              'V0939',
              (),
              "Length of CFF Name INDEX is not 1."))
            return None

        fi = fontinfo.FontInfo()
        fi.fontname = nidx[0]

        # read Top DICT INDEX
        if w.length() < 4:
            logger.error(('E2311', (), "Insufficient bytes for CFF Top DICT INDEX."))
            return None
        sublogger = logger.getChild("TopDICT")
        tdidx = cffindex.fromvalidatedwalker(w, logger=sublogger, **kwArgs)
        if len(tdidx) != len(nidx):
            logger.error((
              'V0939',
              (),
              "Length of CFF Top DICT INDEX does not match length of Name INDEX."))
            return None

        wTD = walker.StringWalker(tdidx[0])
        sublogger = logger.getChild("Top")
        td, tdorigorder = cffdict.fromwalker(
          wTD,
          doValidation=True,
          logger=sublogger,
          **kwArgs)

        # read String INDEX
        if w.length() < 4:
            logger.error(('E2311', (), "Insufficient bytes for CFF String INDEX."))
        sublogger = logger.getChild("String")
        sidx = cffindex.fromvalidatedwalker(
          w,
          logger=sublogger,
          itemmethod=_bdcv,
          **kwArgs)

        # read Global Subr INDEX
        if w.length() < 4:
            logger.error(('E2311', (), "Insufficient bytes for CFF Global Subr INDEX."))
        sublogger = logger.getChild("GlobalSubr")
        globalsubrs = cffindex.fromvalidatedwalker(
          w,
          logger=sublogger,
          **kwArgs)

        # parse out some Top DICT info into FontInfo
        tdops = cffutils.topDictOperators
        resolvesid = cffutils.resolvesid

        fi.isCID = (12,30) in tdorigorder

        # check duplicate TopDICT keys
        if len(set(tdorigorder)) != len(tdorigorder):
            logger.error((
                'V0976',
                (),
                "TopDICT has duplicated keys."))
            return None

        for k in tdorigorder:
            if k not in tdops:
                logger.error((
                    'V0977',
                    (k,),
                    "Undefined TopDICT key %d encountered."))

            elif k in (15, 16, 17, 18, (12,20), (12,21), (12,36), (12,37)):
                pass # bookkeeping data; do not store in fontinfo

            else:
                kinfo = tdops.get(k)
                label = kinfo[0]
                valKind = kinfo[1]

                if td[k]:
                    if valKind == 'SID':
                        fi[label] = resolvesid(td[k][0], sidx)
                    elif valKind == 'array':
                        fi[label] = td[k]
                    elif valKind == 'SIDSIDnumber':
                        fi[label] = (
                          resolvesid(td[k][0], sidx),
                          resolvesid(td[k][1], sidx),
                          td[k][2])
                    else:
                        fi[label] = td[k][0]
                else:
                    logger.error((
                        'V0978',
                        (label, k),
                        "Empty TopDICT entry for '%s' (%d)."))

        if 17 in td:
            """
            Charset and encoding depend on length of 'charstrings', so
            we need to grab that first.
            """
            wSub = w.subWalker(td[17][0])
            sublogger = logger.getChild("CharStrings")
            chrstrs = charstrings.CharStrings.fromvalidatedwalker(
              wSub,
              logger=sublogger)
            if chrstrs is None:
                return None
        else:
            logger.error((
              'V0862',
              (),
              "TopDICT missing CharStrings operator"))
            return None

        if fi.isCID:
            cidcount = td.get((12,34), (8720,))[0]

            # check for minimum-required CID operators in TopDICT:
            cidOK = True
            if (12,36) in td:
                wSub = w.subWalker(td[(12,36)][0])
                sublogger = logger.getChild("FDArray")
                fdaidx = cffindex.fromvalidatedwalker(
                  wSub,
                  logger=sublogger)

                fdarray = []
                fdnames = []
                pdarray = []
                for i,fdRaw in enumerate(fdaidx):
                    wFD = walker.StringWalker(fdRaw)
                    fdDT = cffdict.fromwalker(
                      wFD,
                      doValidation=True,
                      logger=sublogger)
                    fdarray.append(fdDT)

                    fdfontnameSID = fdDT[0].get( (12, 38) )
                    if fdfontnameSID is None:
                        logger.error((
                          'V0994',
                          (i,),
                          "Font DICT #%d missing required entry 'FD Font Name'."))
                        fdfontname = "Undefined FD %d" % (i,)
                    else:
                        fdfontname = resolvesid(fdfontnameSID[0], sidx)

                    fdnames.append(fdfontname)

                    if 18 not in fdDT[0]:
                        logger.error((
                          'V0995',
                          (i,),
                          "Font DICT #%d missing required entry 'Private'."))
                        return None

                    pLen, pOff = fdDT[0][18]
                    # Needed to do some gymnastics to limit the subWalker's length
                    # to private length...puzzling interplay of 'newLimit' & 'relative'
                    # for subWalker...
                    oDelta = w.getOffset() - tblStart
                    wFDSub = w.subWalker(pOff-oDelta, newLimit=pLen, relative=True)
                    sublogger = logger.getChild("Private")
                    pd, pdorigorder = cffdict.fromwalker(
                      wFDSub,
                      doValidation=True,
                      logger=sublogger)

                    pdops = cffutils.privateDictOperators
                    pdarray.append(
                      privatedict.PrivateDict(index=len(pdarray), origorder=pdorigorder))
                    for k,v in list(pd.items()):
                        if k in pdops:
                            kinfo = pdops.get(k)
                            label = kinfo[0]
                            valKind = kinfo[1]
                            if k == 19:
                                # local subrs
                                wLSub = w.subWalker(pOff + v[0])
                                sublogger=logger.getChild("LocalSubrs")
                                localsubrs = cffindex.fromvalidatedwalker(
                                  wLSub,
                                  logger=sublogger)
                                pdarray[-1]['localsubrs'] = localsubrs
                            elif valKind == 'array' or valKind == 'delta':
                                pdarray[-1][label] = v
                            elif len(v):
                                pdarray[-1][label] = v[0]
                            else:
                                logger.error((
                                  'V0996',
                                  (label, i),
                                  "Empty value for Private DICT entry '%s' "
                                  "(Font DICT #%d)."))
                        else:
                            logger.error((
                              'V0850',
                              (k,v),
                              "Encountered unknown Private DICT "
                              "operator '%s' with operands '%s'"))

                fi.subfontnames = fdnames

            else:
                logger.error((
                  'V0941',
                  (),
                  "TopDICT missing FDArray operator for CID-keyed font."))
                return None

            if (12,37) in td:
                wSub = w.subWalker(td[(12,37)][0])
                fds = fdselect.FDSelect.fromvalidatedwalker(
                  wSub,
                  nGlyphs=len(chrstrs),
                  **kwArgs)
            else:
                logger.error((
                  'V0866',
                  (),
                  "TopDICT missing FDSelect operator for CID-keyed font."))
                return None

            if 15 in td:
                # charset
                wSub = w.subWalker(td[15][0])
                sublogger = logger.getChild("Charset")
                cs = charset.Charset.fromvalidatedwalker(
                  wSub,
                  logger=sublogger,
                  nGlyphs=len(chrstrs),
                  isCID = True,
                  **kwArgs)
            else:
                # default charset 0
                cs = charset.Charset.fromvalidatednumber(
                  0,
                  **kwArgs)

            # otki/ce for CID case
            otki = iter(range(len(chrstrs)))
            ce = dict(
              doValidation = True,
              logger = logger,
              oneTimeKeyIterator = otki,
              isCID=True,
              _charset=cs,
              _charstrings=chrstrs,
              _fdarray=fdarray,
              _fdselect=fds,
              _fontstrings=sidx,
              _globalsubrs=globalsubrs,
              _origTdAndOrder=(td, tdorigorder),
              _privatearray=pdarray,
              )


        else:
            # non-CID

            # Check for any CID-related TopDICT entries, which should not be
            # present in a non-CID font.

            cidkeys = ((12, 31), (12, 32), (12, 33), (12, 34), (12, 36), (12, 37))
            for k in cidkeys:
                if k in td:
                    logger.error((
                      'V1005',
                      (k,),
                      "Non-CID TopDICT contains CID operator %s"))

            if 15 in td:
                # charset
                wSub = w.subWalker(td[15][0])
                sublogger = logger.getChild("Charset")
                cs = charset.Charset.fromvalidatedwalker(
                  wSub,
                  logger=sublogger,
                  strings=sidx,
                  nGlyphs=len(chrstrs),
                  **kwArgs)
            else:
                # default charset 0
                cs = charset.Charset.fromvalidatednumber(
                  0,
                  **kwArgs)

            if cs is not None:
                rcs = {v:k for k,v in list(cs.items())} # reverse charset
            else:
                rcs = {}

            if 16 in td:
                # Encoding
                wSub = w.subWalker(td[16][0])
                sublogger = logger.getChild("Encoding")
                enc = encoding.Encoding.fromvalidatedwalker(
                  wSub,
                  logger=sublogger,
                  **kwArgs)
            else:
                enc = None

            if 18 in td:
                # Private
                pLen, pOff = td[18]
                # Needed to do some gymnastics to limit the subWalker's length
                # to private length...puzzling interplay of 'newLimit' & 'relative'
                # for subWalker...
                logger.info((
                  'V1075',
                  (pLen,),
                  "PrivateDICT length is %d"))
                oDelta = w.getOffset() - tblStart
                wSub = w.subWalker(pOff-oDelta, newLimit=pLen, relative=True)
                sublogger = logger.getChild("Private")
                pd, pdorigorder = cffdict.fromwalker(
                  wSub,
                  doValidation=True,
                  logger=sublogger)


                # Convert raw pd into more friendly terms...
                pdops = cffutils.privateDictOperators
                private = privatedict.PrivateDict(index=0, origorder=pdorigorder)
                for k,v in list(pd.items()):
                    kinfo = pdops.get(k)
                    label = kinfo[0]
                    valKind = kinfo[1]
                    if k == 19:
                        # local subrs
                        wLSub = w.subWalker(pOff + v[0])
                        sublogger=logger.getChild("LocalSubrs")
                        localsubrs = cffindex.fromvalidatedwalker(
                          wLSub,
                          logger=sublogger)
                        private['localsubrs'] = localsubrs
                    elif valKind == 'array' or valKind == 'delta':
                        private[label] = v
                    else:
                        private[label] = v[0]

            else:
                # no PrivateDICT; error
                logger.error((
                  'V0863',
                  (),
                  "TopDICT missing required Private DICT entry."))
                return None

            # otki/ce for NON-CID case
            otki = iter(range(len(chrstrs)))
            ce = dict(
              oneTimeKeyIterator = otki,
              doValidation = True,
              logger = logger,
              isCID = False,
              _charset=cs,
              _charstrings=chrstrs,
              _encoding=enc,
              _fontstrings=sidx,
              _globalsubrs=globalsubrs,
              _origTdAndOrder=(td, tdorigorder),
              _private=private,
              _revcharset=rcs)

        return cls(
          creationExtras=ce,
          fontinfo=fi,
          glyphNames=cs,
          )


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CFF object from the specified Walker.

        >>> d = utilities.fromhex(_testingData)
        >>> w = walker.StringWalker(d)
        >>> obj = CFF.fromwalker(w)
        >>> obj.fontinfo.fontname
        b'ABCDEF+Times-Roman'
        """

        tblStart = w.getOffset()

        # read header
        hdrMaj, hdrMin, hdrSize, offSize = w.unpack("4B")

        # read Name INDEX
        nidx = cffindex.fromwalker(w, **kwArgs)
        if len(nidx) != 1:
            raise ValueError("Length of CFF Name INDEX is not 1 "
            " (multi-font FontSets not supported)")
            return None

        fi = fontinfo.FontInfo()
        fi.fontname = nidx[0]

        # read Top DICT INDEX
        tdidx = cffindex.fromwalker(w, **kwArgs)

        wTD = walker.StringWalker(tdidx[0])
        td, tdorigorder = cffdict.fromwalker(
          wTD,
          **kwArgs)

        # read String INDEX
        sidx = cffindex.fromwalker(w, itemmethod=_bdc, **kwArgs)

        # read Global Subr INDEX
        globalsubrs = cffindex.fromwalker(
          w,
          **kwArgs)

        # parse out some Top DICT info into FontInfo
        tdops = cffutils.topDictOperators
        resolvesid = cffutils.resolvesid

        fi.isCID = (12,30) in tdorigorder

        for k in tdorigorder:
            if k in (15, 16, 17, 18, (12,20), (12,21), (12,36), (12,37)):
                pass # bookkeeping data; do not store in fontinfo
            else:
                kinfo = tdops.get(k)
                label = kinfo[0]
                valKind = kinfo[1]
                if valKind == 'SID':
                    fi[label] = resolvesid(td[k][0], sidx)
                elif valKind == 'array':
                    fi[label] = td[k]
                elif valKind == 'SIDSIDnumber':
                    fi[label] = (
                      resolvesid(td[k][0], sidx),
                      resolvesid(td[k][1], sidx),
                      td[k][2])
                else:
                    fi[label] = td[k][0]

        if 17 in td:
            """
            Charset and encoding depend on length of 'charstrings', so
            we need to grab that first.
            """
            wSub = w.subWalker(td[17][0])
            chrstrs = charstrings.CharStrings.fromwalker(
              wSub,
              )

        if fi.isCID:
            cidcount = td.get((12,34), (8720,))[0]

            # check for minimum-required CID operators in TopDICT:
            cidOK = True
            if (12,36) in td:
                wSub = w.subWalker(td[(12,36)][0])
                fdaidx = cffindex.fromwalker(
                  wSub)

                fdarray = []
                fdnames = []
                pdarray = []
                for i,fdRaw in enumerate(fdaidx):
                    wFD = walker.StringWalker(fdRaw)
                    fdDT = cffdict.fromwalker(
                      wFD)
                    fdarray.append(fdDT)

                    fdfontnameSID = fdDT[0].get( (12, 38) )
                    if fdfontnameSID is None:
                        fdfontname = "Undefined FD %d" % (i,)
                    else:
                        fdfontname = resolvesid(fdfontnameSID[0], sidx)

                    fdnames.append(fdfontname)

                    pLen, pOff = fdDT[0][18]
                    # Needed to do some gymnastics to limit the subWalker's length
                    # to private length...puzzling interplay of 'newLimit' & 'relative'
                    # for subWalker...
                    oDelta = w.getOffset() - tblStart
                    wFDSub = w.subWalker(pOff-oDelta, newLimit=pLen, relative=True)
                    pd, pdorigorder = cffdict.fromwalker(
                      wFDSub)

                    pdops = cffutils.privateDictOperators
                    pdarray.append(
                      privatedict.PrivateDict(index=len(pdarray), origorder=pdorigorder))
                    for k,v in list(pd.items()):
                        if k in pdops:
                            kinfo = pdops.get(k)
                            label = kinfo[0]
                            valKind = kinfo[1]
                            if k == 19:
                                # local subrs
                                wLSub = w.subWalker(pOff + v[0])
                                localsubrs = cffindex.fromwalker(
                                  wLSub)
                                pdarray[-1]['localsubrs'] = localsubrs
                            elif valKind == 'array' or valKind == 'delta':
                                pdarray[-1][label] = v
                            else:
                                pdarray[-1][label] = v[0]

                fi.subfontnames = fdnames

            if (12,37) in td:
                wSub = w.subWalker(td[(12,37)][0])
                fds = fdselect.FDSelect.fromvalidatedwalker(
                  wSub,
                  nGlyphs=len(chrstrs),
                  **kwArgs)

            if 15 in td:
                # charset
                wSub = w.subWalker(td[15][0])
                cs = charset.Charset.fromwalker(
                  wSub,
                  nGlyphs=len(chrstrs),
                  isCID = True,
                  **kwArgs)
            else:
                # default charset 0
                cs = charset.Charset.fromnumber(
                  0,
                  **kwArgs)

            # otki/ce for CID case
            otki = iter(range(len(chrstrs)))
            ce = dict(
              doValidation = False,
              oneTimeKeyIterator = otki,
              isCID=True,
              _charset=cs,
              _charstrings=chrstrs,
              _fdarray=fdarray,
              _fdselect=fds,
              _fontstrings=sidx,
              _globalsubrs=globalsubrs,
              _origTdAndOrder=(td, tdorigorder),
              _privatearray=pdarray,
              )



        else:
            # non-CID
            if 15 in td:
                # charset
                wSub = w.subWalker(td[15][0])
                cs = charset.Charset.fromwalker(
                  wSub,
                  strings=sidx,
                  nGlyphs=len(chrstrs),
                  **kwArgs)
            else:
                # default charset 0
                cs = charset.Charset.fromnumber(
                  0,
                  **kwArgs)
            rcs = {v:k for k,v in list(cs.items())}

            if 16 in td:
                # Encoding
                wSub = w.subWalker(td[16][0])
                enc = encoding.Encoding.fromwalker(
                  wSub,
                  **kwArgs)
            else:
                enc = None

            if 18 in td:
                # Private
                pLen, pOff = td[18]
                # Needed to do some gymnastics to limit the subWalker's length
                # to private length...puzzling interplay of 'newLimit' & 'relative'
                # for subWalker...
                oDelta = w.getOffset() - tblStart
                wSub = w.subWalker(pOff-oDelta, newLimit=pLen, relative=True)
                pd, pdorigorder = cffdict.fromwalker(
                  wSub)


                # Convert raw pd into more friendly terms...
                pdops = cffutils.privateDictOperators
                private = privatedict.PrivateDict(index=0, origorder=pdorigorder)
                for k,v in list(pd.items()):
                    kinfo = pdops.get(k)
                    label = kinfo[0]
                    valKind = kinfo[1]
                    if k == 19:
                        # local subrs
                        wLSub = w.subWalker(pOff + v[0])
                        localsubrs = cffindex.fromwalker(
                          wLSub)
                        private['localsubrs'] = localsubrs
                    elif valKind == 'array' or valKind == 'delta':
                        private[label] = v
                    else:
                        private[label] = v[0]

            # otki/ce for NON-CID case
            otki = iter(range(len(chrstrs)))
            ce = dict(
              oneTimeKeyIterator = otki,
              doValidation = False,
              isCID = False,
              _charset=cs,
              _charstrings=chrstrs,
              _encoding=enc,
              _fontstrings=sidx,
              _globalsubrs=globalsubrs,
              _origTdAndOrder=(td, tdorigorder),
              _private=private,
              _revcharset=rcs)

        return cls(
          creationExtras=ce,
          fontinfo=fi,
          glyphNames=cs,
          )

    def getXYtoPointMap(self, id, **kwArgs):
        """
        Returns a dict mapping (xcoordinate, ycoordinate) tuples to
        point indices for id.
        """
        d = self[id]

        if getattr(d, 'contours', None):
            pts = (tuple(p) for c in d.contours for p in c)
            return {p:i for i,p in enumerate(pts)}

        return {}

    def unionBounds(self):
        """
        Returns a CFFBounds object with the union bounds for all glyphs in the
        CFF object.
        """

        CFFB = cffbounds.CFFBounds

        return functools.reduce(
          CFFB.unioned,
          (obj.bounds for obj in self.values() if (obj and obj.bounds)),
          CFFB(xMin = 32767, xMax = -32768, yMin = 32767, yMax = -32768))


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.name import name
    from fontio3 import utilities
    from fontio3.utilities import walker

    """
    Adobe's example (adapted) from the 'CFF' document (#5176), in
    Appendix D. It is "a subset with just the .notdef and space glyphs
    of the Times* font program that has been renamed. This font has no
    subrs and uses predefined encoding and charset."
    """
    _testingData = (
        "01 00 04 01 00 01 01 01 13 41 42 43 44 45 46 2b "
        "54 69 6d 65 73 2d 52 6f 6d 61 6e 00 01 01 01 1f "
        "f8 1b 00 f8 1c 02 f8 1d 03 f8 19 04 1c 6f 00 0d "
        "fb 3c fb 6e fa 7c fa 16 05 e9 11 b8 f1 12 00 03 "
        "01 01 08 13 18 30 30 31 2e 30 30 37 54 69 6d 65 "
        "73 20 52 6f 6d 61 6e 54 69 6d 65 73 00 00 00 02 "
        "01 01 02 03 0e 0e 7d 99 f9 2a 99 fb 76 95 f7 73 "
        "8b 06 f7 9a 93 fc 7c 8c 07 7d 99 f8 56 95 f7 5e "
        "99 08 fb 6e 8c f8 73 93 f7 10 8b 09 a7 0a df 0b "
        "f7 8e 14")

    _testingData2 = (
        "01 00 04 01 00 01 01 01 13 41 42 43 44 45 46 2b "
        "54 69 6d 65 73 2d 52 6f 6d 61 6e 00 01 01 01 1f "
        "f8 1b 00 f8 1c 02 f8 1d 03 f8 19 04 1c 6f 00 0d "
        "fb 3c fb 6e fa 7c fa 16 05 e9 11 b8 f1 12 00 03 "
        "01 01 08 13 18 30 30 31 2e 30 30 37 54 fd 6d 65 "
        "73 20 52 6f 6d 61 6e 54 69 6d 65 73 00 00 00 02 "
        "01 01 02 03 0e 0e 7d 99 f9 2a 99 fb 76 95 f7 73 "
        "8b 06 f7 9a 93 fc 7c 8c 07 7d 99 f8 56 95 f7 5e "
        "99 08 fb 6e 8c f8 73 93 f7 10 8b 09 a7 0a df 0b "
        "f7 8e 14")

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

