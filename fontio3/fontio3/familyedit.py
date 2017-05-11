#
# familyedit.py
#
# Copyright © 2011-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for families of fonts.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import fontedit
from fontio3.fontdata import deferreddictmeta, seqmeta
from fontio3.utilities import filewalkerbit, ScalerError

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_item(obj, **kwArgs):
    kwArgs.pop('editor', None)
    logger = kwArgs.pop('logger')
    subLogger = logger.getChild("Family")

    if obj.reallyHas(b'DSIG'):
        logger.warning((
          'Vxxxx',
          (),
          "TTC component font contains DSIG table."))
    
    return deferreddictmeta.M_isValid(
      obj,
      editor = obj,
      logger = subLogger,
      **kwArgs)

def _validate_sequence(seq, **kwArgs):
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild("Family")
    else:
        logger = logger.getChild("Family")

    isOK = True
    
    # table complement
    
    s_tables = set([])
    
    for e in seq:
        s_tables = s_tables | set(e.keys())
    
    for t in sorted(s_tables):
        t_OK = True
        
        for e in seq:
            if t_OK and (t not in e):
                t_OK = False
                
                logger.warning((
                  'V0577',
                  (t,),
                  "Not all fonts in the family have the '%s' table."))
        
        if t_OK:
            logger.info((
              'V0578',
              (t,),
              "Each font in the family has the '%s' table."))
    
    # 'name' table items
    
    s_familyName = set()
    for ei, e in enumerate(seq):
        if e is not None and e.reallyHas(b'name'):
            s_familyName.add(e.name.getFamilyName())
        else:
            s_familyName.add("Unknown (index %d)" % (ei,))
    
    if len(s_familyName) == 1:
        logger.info((
          'V0493',
          (),
          "Family names are the same for each font in the family."))
    
    else:
        logger.error((
          'V0494',
          (),
          "Family names are not the same for each font in the family."))
        
        isOK = False
        
    d_fullName = set()
    for ei, e in enumerate(seq):
        if e is not None and e.reallyHas(b'name'):
            d_fullName.add(e.name.getFullName())
        else:
            d_fullName.add("Unknown")
    
    if len(d_fullName) == len(seq):
        logger.info((
          'V0499',
          (),
          "Full names are unique for each font in the family."))
    
    else:
        logger.error((
          'V0500',
          (),
          "Full names are not unique for each font in the family."))
        
        isOK = False
    
    # 'OS/2' table items (including presence/absence)
    
    s_have_OS2 = {e.reallyHas(b'OS/2') for e in seq}
    
    if len(s_have_OS2) == 1:
        if s_have_OS2.pop():
            s_winAscent = {e[b'OS/2'].usWinAscent for e in seq}
            
            if len(s_winAscent) == 1:
                logger.info((
                  'V0495',
                  (),
                  "OS/2.winAscent values are the same for each font "
                  "in the family."))
            
            else:
                logger.warning((
                  'V0496',
                  (),
                  "OS/2.winAscent values are not the same for each font "
                  "in the family."))
        
            s_winDescent = {e[b'OS/2'].usWinDescent for e in seq}
            
            if len(s_winDescent) == 1:
                logger.info((
                  'V0497',
                  (),
                  "OS/2.winDescent values are the same for each font "
                  "in the family."))
            
            else:
                logger.warning((
                  'V0498',
                  (),
                  "OS/2.winDescent values are not the same for each font "
                  "in the family."))
                
            s_sTypoAscender = {e[b'OS/2'].sTypoAscender for e in seq}
            
            if len(s_sTypoAscender) == 1:
                logger.info((
                  'V0583',
                  (),
                  "OS/2.sTypoAscender values are the same for each font "
                  "in the family."))
            
            else:
                logger.warning((
                  'V0584',
                  (),
                  "OS/2.sTypoAscender values are not the same for each font "
                  "in the family."))
                
            s_sTypoDescender = {e[b'OS/2'].sTypoDescender for e in seq}
            
            if len(s_sTypoDescender) == 1:
                logger.info((
                  'V0585',
                  (),
                  "OS/2.sTypoDescender values are the same for each font "
                  "in the family."))
            
            else:
                logger.warning((
                  'V0586',
                  (),
                  "OS/2.sTypoDescender values are not the same for each font "
                  "in the family."))
                
            s_sTypoLineGap = {e[b'OS/2'].sTypoLineGap for e in seq}
            
            if len(s_sTypoLineGap) == 1:
                logger.info((
                  'V0587',
                  (),
                  "OS/2.sTypoLineGap values are the same for each font "
                  "in the family."))
            
            else:
                logger.warning((
                  'V0588',
                  (),
                  "OS/2.sTypoLineGap values are not the same for each font "
                  "in the family."))
                
            d_fsSelection = {
              e[b'OS/2'].fsSelection.binaryString()
              for e in seq}
            
            if len(d_fsSelection) == len(seq):
                logger.info((
                  'V0507',
                  (),
                  "OS/2.fsSelection values are unique for each font "
                  "in the family."))
            
            else:
                logger.error((
                  'V0508',
                  (),
                  "OS/2.fsSelection values are not unique for each font "
                  "in the family."))
                
                isOK = False
    
    else:
        
        # Note that we're only raising this if *SOME* fonts have an OS/2 table
        # and others don't.
        
        logger.error((
          'V0502',
          (),
          "Could not validate family 'OS/2' values because some fonts "
          "in the family are missing the table."))
        
        isOK = False
    
    # 'hhea' table items
    
    s_ascent = {e.hhea.ascent for e in seq}
    
    if len(s_ascent) == 1:
        logger.info((
          'V0503',
          (),
          "hhea.ascent values are the same for each font in the family."))
    
    else:
        logger.warning((
          'V0504',
          (),
          "hhea.ascent values are not the same for each font in the family."))

    s_descent = {e.hhea.descent for e in seq}
    
    if len(s_descent) == 1:
        logger.info((
          'V0505',
          (),
          "hhea.descent values are the same for each font in the family."))
    
    else:
        logger.warning((
          'V0506',
          (),
          "hhea.descent values are not the same for each font in the family."))

    s_lineGap = {e.hhea.lineGap for e in seq}
    
    if len(s_lineGap) == 1:
        logger.info((
          'V0581',
          (),
          "hhea.lineGap values are the same for each font in the family."))
    
    else:
        logger.warning((
          'V0582',
          (),
          "hhea.lineGap values are not the same for each font in the family."))
    
    # 'head' table items
    
    d_macstyle = {e.head.macStyle.binaryString() for e in seq}
    
    if len(d_macstyle) == len(seq):
        logger.info((
          'V0509',
          (),
          "head.macStyle values are unique for each font in the family."))
    
    else:
        logger.error((
          'V0510',
          (),
          "head.macStyle values are not unique for each font in the family."))
        
        isOK = False

    s_upem = {e.head.unitsPerEm for e in seq}
    
    if len(s_upem) == 1:
        logger.info((
          'V0913',
          (),
          "head.unitsPerEm values are the same for each font in the family."))
    else:
        logger.warning((
          'V0914',
          (),
          "head.unitsPerEm values are not the same for each font in the family."))


    # 'post' table items
    
    s_isFixedPitch = {e.post.header.isFixedPitch for e in seq if b'post' in e}
    
    if len(s_isFixedPitch) == 1:
        logger.info((
          'V0579',
          (s_isFixedPitch.pop(),),
          "post.isFixedPitch flag is %s for each font in the family."))
    
    else:
        logger.warning((
          'V0580',
          (),
          "post.isFixedPitch flag is not the same for each font "
          "in the family."))

    # finally, validate individual items
    
    for i,e in enumerate(seq):
        name = seq.makeLoggerName(i)
        item_logger = logger.getChild(name)
        
        if 'scaler' in kwArgs:
            scaler = kwArgs.get('scaler')
            
            if e.reallyHas(b'glyf'):
                try:
                    scaler.setFont(name)
                except:
                    raise ScalerError()
            
            else:
                kwArgs.pop('scaler')
        
        isOK = _validate_item(e, logger=item_logger, **kwArgs) and isOK

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FamilyEditor(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing whole families of related fonts. These are lists of
    Editor objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_validatefunc = _validate_sequence)
    
    attrSpec = dict(
        cameFromTTC = dict(
            attr_initfunc = (lambda: False),
            attr_label = "FamilyEditor came from a TTC",
            attr_showonlyiftrue = True),

        hasDSIG = dict(
            attr_initfunc = (lambda: False),
            attr_label = "FamilyEditor has a DSIG",
            attr_showonlyiftrue = False),

        version = dict(
            attr_initfunc = (lambda: None),
            attr_label = "TTC Version",
            attr_showonlyiftrue = True))

    attrSorted = ()
    
    #
    # Methods
    #
    
    def _makeChangedKeys(self):
        changedKeys = [None] * len(self)
        
        for i, obj in enumerate(self):
            obj.head.checkSumAdjustment = 0
            obj._updateDependentObjects()
            changedKeys[i] = set(obj._dAdded)
        
        return changedKeys
    
    def _makeStakes(self, w):
        stakes = []
        
        for obj in self:
            stakes.append({tag: w.getNewStake() for tag in obj})
        
        return stakes
    
    def _makeUniques(self, changedKeys):
        uniques = {}  # tag -> {avatar1: set(equals), avatar2: set(equals)...}
        allTags = functools.reduce(set.union, (set(obj) for obj in self))
        
        for tag in allTags:
            uniques[tag] = d = {}
            
            for i, obj in enumerate(self):
                if tag not in obj:
                    continue
                
                objIsRaw = (
                  (tag not in changedKeys[i]) or
                  isinstance(obj[tag], (str, bytes)))
                
                for avatarIndex, otherEquals in d.items():
                    avatarIsRaw = (
                      (tag not in changedKeys[avatarIndex]) or
                      isinstance(self[avatarIndex][tag], (str, bytes)))
                    
                    if avatarIsRaw and objIsRaw:
                        av = self[avatarIndex]
                        
                        if obj.getRawTable(tag) == av.getRawTable(tag):
                            otherEquals.add(i)
                            break
                    
                    else:
                        if avatarIsRaw:
                            changedKeys[avatarIndex].add(tag)
                        
                        elif objIsRaw:
                            changedKeys[i].add(tag)
                            objIsRaw = False
                            
                        if obj[tag] == self[avatarIndex][tag]:
                            otherEquals.add(i)
                            break
                
                else:
                    d[i] = set()
        
        return uniques
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FamilyEditor to the specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        forceVersion1 = kwArgs.get('forceVersion1', False)

        if forceVersion1 or self.version == 0x10000:
            vv = 0x10000
        else:
            vv = 0x20000

        w.add("4s2L", b'ttcf', vv, len(self))

        tStakes = [w.getNewStake() for obj in self]

        for tStake in tStakes:
            w.addUnresolvedOffset("L", stakeValue, tStake)  # OffsetTable
 
        if vv == 0x20000:
            w.add("3L", 0, 0, 0)  # ulDsigTag, ulDsigLength, ulDsigOffset for v2
        
        changedKeys = self._makeChangedKeys()
        uniques = self._makeUniques(changedKeys)
        stakes = self._makeStakes(w)
        headerChecksumRanges = []
        
        delKeys = {
          'baseStake',
          'changedKeys',
          'checksums',
          'familyIndex',
          'headerChecksumRanges',
          'lengths',
          'stakes',
          'uniques',
          'w'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        for i, obj in enumerate(self):
            startByteLength = w.byteLength
            
            obj.buildBinary_headerOnly(
              w = w,
              stakes = stakes,
              baseStake = stakeValue,
              familyIndex = i,
              stakeValue = tStakes[i],
              **kwArgs)
            
            headerChecksumRanges.append((startByteLength, w.byteLength))
        
        checksums = {(i, tag): 0 for i, obj in enumerate(self) for tag in obj}
        w.addIndexMap("checksums", checksums)
        lengths = checksums.copy()
        w.addIndexMap("lengths", lengths)
        
        for i, obj in enumerate(self):
            obj.buildBinary_tablesOnly(
              w = w,
              stakes = stakes,
              changedKeys = changedKeys,
              uniques = uniques,
              familyIndex = i,
              checksums = checksums,
              lengths = lengths,
              headerChecksumRanges = headerChecksumRanges,
              **kwArgs)
    
    @classmethod
    def frompath(cls, path, **kwArgs):
        """
        Creates and returns a new FamilyEditor for the TTC specified by path.
        """
        
        r = cls.fromwalker(filewalkerbit.FileWalkerBit(path), **kwArgs)
        r.cameFromTTC = True
        return r
    
    @classmethod
    def fromvalidatedpath(cls, path, **kwArgs):
        """
        """
        
        r = cls.fromvalidatedwalker(
          filewalkerbit.FileWalkerBit(path),
          **kwArgs)
        
        if r:
            r.cameFromTTC = True
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild("Family")
        else:
            logger = logger.getChild("Family")
        
        ttclen = w.length()
        
        logger.debug((
          'V0001',
          (ttclen,),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.critical((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        s = w.unpack("4s")
        
        if s != b'ttcf':
            logger.critical((
              'E0062',
              tuple(s),
              "Expected 'ttcf' tag, but got 0x%02X%02X%02X%02X instead."))
            
            return None
        
        if w.length() < 4:
            logger.critical((
              'V0292',
              (),
              "Insufficient bytes for version."))
            
            return None
        
        version = w.unpack("L")
        
        if version == 0x10000:
            logger.info(('I0061', (), "TTC version is 1.0."))
            isVersion2 = False
        
        elif version == 0x20000:
            logger.info(('I0062', (), "TTC version is 2.0."))
            isVersion2 = True
        
        else:
            logger.critical((
              'E0063',
              (version,),
              "Unknown version: 0x%08X."))
            
            return None
        
        if w.length() < 4:
            logger.critical((
              'V0293',
              (),
              "Insufficient bytes for offset count."))
            
            return None
        
        count = w.unpack("L")
        
        if w.length() < 4 * count:
            logger.critical((
              'E0060',
              (),
              "Not enough offsets for count."))
            
            return None
        
        else:
            logger.info((
              'I0060',
              (count,),
              "Offset count is %d."))
        
        r = cls(version=version)
        fw = fontedit.Editor.fromvalidatedwalker
        kwArgs.pop('fromTTC', None)
        
        for i, offset in enumerate(w.group("L", count)):
            if offset >= w.length():
                logger.critical((
                  'E0061',
                  (i,),
                  "Offset [%d] is past EOF."))
                
                return None
            
            if 'subloggerNameFunc' in kwArgs:
                s = kwArgs['subloggerNameFunc'](i, **kwArgs)
            else:
                s = "[%d]" % (i,)
                        
            itemLogger = logger.getChild(s)
            wSub = w.subWalker(0)
            wSub.skip(offset)
            r.append(fw(wSub, logger=itemLogger, fromTTC=True, **kwArgs))

        # DSIG: despite what the spec indicates, BOTH Version 1 and Version 2
        # TTCs may have a DSIG, tucked in following the OffsetTable but before
        # the first font's dirTables. We read the 4 bytes immediately following
        # the OffsetTable. If that is 'DSIG', then we have a DSIG, and there
        # should be 2 non-zero 4-byte values for Length and Offset.
        
        dsigTag = w.unpack("4s")
        
        if dsigTag == b'DSIG':
            dsigLength, dsigOffset = w.group("L", 2)
            isOK = True
            
            if dsigLength == 0:
                logger.error((
                  'V0517',
                  (),
                  "DSIG indicated in header, but length is 0."))
                
                isOK = False
            
            if dsigOffset == 0:
                logger.error((
                  'V0518',
                  (),
                  "DSIG indicated in header, but offset is 0."))
                
                isOK = False
            
            if dsigOffset + dsigLength > ttclen:
                logger.error((
                  'V0519',
                  (),
                  "DSIG offset + length exceeds file length."))
                
                isOK = False

            if isOK:
                r.hasDSIG = True
                logger.info(('V0520', (), "DSIG present."))

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FamilyEditor from the specified walker, which
        should point to the start of a TTC.
        """
        
        s = w.unpack("4s")
        
        if s != b'ttcf':
            raise ValueError("Unknown TTC tag: %s" % (s,))
        
        version = w.unpack("L")
        
        if version == 0x10000:
            isVersion2 = False
        elif version == 0x20000:
            isVersion2 = True
        else:
            raise ValueError("Unknown TTC version: 0x%08X" % (version,))
        
        r = cls(version=version)
        fw = fontedit.Editor.fromwalker
        kwArgs.pop('fromTTC', None)
        
        for offset in w.group("L", w.unpack("L")):
            
            # All interior offsets within the table directories of the
            # contained fonts are relative to the start of the TTC, and not to
            # the start of the individual font's header, so the "sub" walker we
            # pass down needs to anchor at the same place the original walker
            # anchors.
            
            wSub = w.subWalker(0)
            wSub.skip(offset)
            r.append(fw(wSub, fromTTC=True, **kwArgs))
        
        dsigTag = w.unpack("4s")
        
        if dsigTag == b'DSIG':
            r.hasDSIG = True
            dsigLength, dsigOffset = w.group("L", 2)
        
        return r

    def makeLoggerName(self, i):
        """
        Default method to generate/retrieve a logger name for item validation.
        Scheme is to return the subfamily name if available; otherwise simply
        the item's index.
        """
        
        if self[i] is not None and self[i].reallyHas(b'name'):
            return self[i].name.getSubfamilyName()
        else:
            return "[%d]" % (i,)

    def writeFont(self, path, **kwArgs):
        """
        """
        
        f = open(path, "wb")
        f.write(self.binaryString(**kwArgs))
        f.close()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
