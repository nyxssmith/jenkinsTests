#
# name.py
#
# Copyright © 2004-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'name' tables in TrueType and OpenType fonts.
"""

# System imports
import collections
import itertools
import operator
import re

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.name import name_key
from fontio3.utilities import pslnames, findAvailableIndex

# -----------------------------------------------------------------------------

#
# Private constants
#

_nameIDs = {
     0: "Copyright",
     1: "Family",
     2: "Subfamily",
     3: "Unique ID",
     4: "Full Name",
     5: "Version",
     6: "Postscript",
     7: "Trademark",
     8: "Manufacturer",
     9: "Designer",
    10: "Description",
    11: "URL Vendor",
    12: "URL Designer",
    13: "License Description",
    14: "License Info URL",
    15: "Reserved; Set to zero",
    16: "Typographic Family name",
    17: "Typographic Subfamily name",
    18: "Compatible Full (Mac only)",
    19: "Sample Text",
    20: "Postscript CID",
    21: "WWS Family",
    22: "WWS Subfamily",
    23: "Light Background Palette",
    24: "Dark Background Palette"}

_patBold = re.compile(r"\b(bold|black|heavy|dark|[sdh]emibold)", re.I)
_patItalic = re.compile(r"\b(italic|oblique|slant)", re.I)
_patNegative = re.compile(r"\b(negative|inver)", re.I)
_patOutline = re.compile(r"\boutline", re.I)
_patStrikeout = re.compile(r"\bstrike", re.I)
_patUnderscore = re.compile(r"\b(underscore|underline)", re.I)
_patVersion = re.compile(r"([0-9]+)\.([0-9]+)")

# -----------------------------------------------------------------------------

#
# Private functions
#

def _lbf(k):
    sv = [pslnames.labelForKey(k[0:3], terse=True)]
    nameID = k[3]
    
    if nameID in _nameIDs:
        sv.append(_nameIDs[nameID])
    else:
        sv.append("Name ID %d" % (nameID,))
    
    sv.append(str(k))
    return ' '.join(sv)

def _recalc(oldTable, **kwArgs):
    if not any(k[-1] == 19 for k in oldTable):
        return False, oldTable
    
    newTable = type(oldTable)({
      k: v
      for k, v in oldTable.items()
      if k[-1] != 19})
    
    return True, newTable

def _validate(d, **kwArgs):
    logger = kwArgs.pop('logger')
    r = _validate_keys(d, logger, **kwArgs)
    r = _validate_psNames(d, logger, **kwArgs) and r
    r = _validate_reservedNameIDs(d, logger, **kwArgs) and r
    r = _validate_sampleString(d, logger, **kwArgs) and r
    r = _validate_versionString(d, logger, **kwArgs) and r
    r = _validate_consistency(d, logger, **kwArgs) and r
    return r

def _validate_consistency(d, logger, **kwArgs):
    e = kwArgs['editor']
    os2 = e.get(b'OS/2')
    
    if os2 is not None:
        fss = os2.fsSelection
        dFromName = d.subFamilyNameToBits()
        
        if fss.bold != dFromName['bold'] or fss.italic != dFromName['italic']:
            logger.warning((
              'W2000',
              (),
              "Subfamily name does not match OS/2 fsSelector bits."))
            
            return False

    else:
        logger.warning((
            'W0050',
            (),
            "Cannot perform name.subfamilyName-to-OS/2.fsSelection "
            "test because the OS/2 table is missing or empty"))

    return True

def _validate_keys(d, logger, **kwArgs):
    r = True
    kwArgs['languageCode'] = "E2001"
    kwArgs['scriptCode'] = "E2005"
    piv = pslnames.isValid
    
    for key in d:
        subLogger = logger.getChild(str(tuple(key)))
        r = piv(key[0], key[1], key[2], logger=subLogger, **kwArgs) and r
    
    if not {k for k in d if k[0] == 1}:
        logger.warning((
          'E2003',
          (),
          "There are no Mac-platform names defined."))
    
    if not {k for k in d if k[0] == 3}:
        logger.warning((
          'E2004',
          (),
          "There are no Windows-platform names defined."))
    
    return r

def _validate_psNames(d, logger, **kwArgs):
    r = True
    excludeds = {' ', '(', ')', '[', ']', '{', '}', '<', '>', '/', '%'}
    excludeds_b = {b' ', b'(', b')', b'[', b']', b'{', b'}', b'<', b'>', b'/', b'%'}
    allPSNames = set()
    
    for k, s in d.items():
        if k[3] == 6:
            allPSNames.add(k)
            isBad = False
            isStr = isinstance(s, str)
            
            if isStr:
                try:
                    b = s.encode('ascii')
                except UnicodeEncodeError:
                    isBad = True
            
            else:
                isBad = (min(s) < 33) or (max(s) > 127)
            
            if not isBad:
                if set(s) & (excludeds if isStr else excludeds_b):
                    isBad = True
            
            if isBad:
                logger.error((
                  'E2006',
                  (k,),
                  "Postscript name %s has illegal character(s)."))
                
                r = False
            
            if len(s) > 63:
                logger.error((
                  'E2007',
                  (k,),
                  "Postscript name %s is >63 characters long."))
                
                r = False
    
    if {1, 3} - {k[0] for k in allPSNames}:
        logger.error((
          'E2008',
          (),
          "Postscript name not present for both Mac and Windows."))
        
        r = False
    
    if len({d[k] for k in allPSNames}) > 1:
        logger.error((
          'E2009',
          (),
          "Postscript names are inconsistent."))
        
        r = False
    
    return r

def _validate_reservedNameIDs(d, logger, **kwArgs):
    if any(i < 256 for i in ({k[3] for k in d} - set(_nameIDs))):
        logger.error((
          'E2010',
          (),
          "One or more records using reserved name IDs."))
        
        return False
    
    return True

def _validate_sampleString(d, logger, **kwArgs):
    ssKeys = {k for k in d if k[3] == 19}
    
    if not ssKeys:
        return True
    
    e = kwArgs['editor']
    r = True
    
    if e.reallyHas(b'cmap'):
        u = e.cmap.getUnicodeMap()
        
        for k in ssKeys:
            s = d[k]
            
            if any(ord(c) not in u for c in s):
                logger.error((
                  'E2015',
                  (k,),
                  "The sample string %s contains unmapped Unicodes."))
                
                r = False
    
    return r

def _validate_versionString(d, logger, **kwArgs):
    vKeys = {k for k in d if k[3] == 5}
    r = True
    badFormat = False
    
    if not vKeys or not {k for k in vKeys if k[0] == 3}:
        logger.error((
          'E2014',
          (),
          "No MS version name entry found."))
        
        r = False
    
    for k in vKeys:
        v = _patVersion.findall(d[k])
        
        if not v:
            badFormat = True
        
        for t in v:
            if int(t[0]) > 65535 or int(t[1]) > 65535:
                badFormat = True
    
    if badFormat:
        logger.error((
          'E2013',
          (),
          "Version string not formatted correctly."))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Name(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing 'name' tables from a TrueType (or OpenType) font.
    These are dicts mapping (platformID, platformSpecificID, languageID,
    nameID) tuples to Unicode strings. Note that strings are always maintained
    internally in Unicode; encoding and decoding happens as needed in the
    fromwalker() and buildBinary() methods.
    
    >>> _testingValues[1].pprint()
    Mac/Roman/English Family (1, 0, 0, 1): ABCÑ
    Mac/Traditional Chinese/Traditional Chinese Subfamily (1, 2, 19, 2): 安大衛
    
    >>> _testingValues[2].pprint()
    MS/BMP/'en' Family (3, 1, 'en', 1): ABC
    MS/BMP/'en' Subfamily (3, 1, 'en', 2): DEFG
    MS/BMP/'zh-Hant-HK' Family (3, 1, 'zh-Hant-HK', 1): 安大衛
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_ensurekeytype = name_key.Name_Key,
        item_keyfollowsprotocol = True,
        item_pprintlabelfunc = _lbf,
        item_pprintlabelpresort = True,
        map_recalculatefunc_partial = _recalc,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #

    def _makeNonUnicode(self, t):
        """
        Given a tuple (representing a key in self) returns a bytes object
        representing that name. Note that names which were unable to be
        encoded as Unicode originally will simply round-trip here, as there is
        logic to check whether self[t] is a string or a bytes object.
        """
        
        u = self[t]
        
        if isinstance(u, bytes):
            # Plain strings (which resulted from a failure of decoding during
            # fromwalker()) are passed through without change.
            return u
        
        plat, scrp, lang = t[:3]
        s = None
        
        if plat == 0 or plat == 3:  # Unicode or Microsoft
            enc = "utf-16be"
        
        elif plat == 1:  # Macintosh
            if scrp == 0:  # Roman
                if lang in frozenset([24, 25, 26, 27, 28, 36, 38, 39, 40]):
                    enc = "mac-centeuro"
                elif lang == 15:
                    enc = "mac-iceland"
                elif lang == 17:
                    enc = "mac-turkish"
                elif lang == 18:
                    enc = "mac-croatian"
                elif lang == 37:
                    enc = "mac-romanian"
                else:
                    enc = "mac-roman"
            
            elif scrp == 1:  # Japanese
                sjmap = {"©": b'\xFD', "™": b'\xFE', "…": b'\xFF'}
                sv = []
                
                for k, g in itertools.groupby(u, sjmap.__contains__):
                    if k:
                        for c in g:
                            sv.append(sjmap[c])
                    else:
                        sv.append(''.join(g).encode("shift-jis"))
                
                s = b''.join(sv)
            
            elif scrp == 2:  # Traditional Chinese
                enc = "big5"
            
            elif scrp == 3:  # Korean
                sv = []
                
                skmap = {
                 "₩": b'\x81',
                 "—": b'\x82',
                 "©": b'\x83',
                 "™": b'\xFE',
                 "…": b'\xFF'}
                
                for k, g in itertools.groupby(u, skmap.__contains__):
                    if k:
                        for c in g:
                            sv.append(skmap[c])
                    else:
                        sv.append(''.join(g).encode("euc_kr"))
                
                s = b''.join(sv)
            
            elif scrp == 7:  # Russian
                enc = "mac-cyrillic"
            
            elif scrp == 25:  # Simplified Chinese
                enc = "gb2312"
            
            elif scrp == 29:  # Slavic
                enc = "mac-centeuro"
            
            else:
                # should never get here, as long as fromwalker and buildBinary are in sync
                raise ValueError("Unsupported script for Mac platform: %d" % (scrp,))
        
        if s is None:
            s = u.encode(enc)
        
        return s
    
    @staticmethod
    def _rawToUnicode(plat, scrp, lang, rawBytes):
        r"""
        Converts the specified raw bytes into a Unicode string, given the
        specified platform, script, and language. Returns a pair: the Unicode
        string (or the raw bytes unconverted if the conversion failed), and a
        Boolean indicating success in conversion.
        
        >>> Name._rawToUnicode(1, 0, 0, b'ABC')
        ('ABC', True)
        
        >>> fh = utilities.fromhex
        >>> Name._rawToUnicode(1, 3, 23, fh("A3"))
        (b'\xa3', False)
        """
        
        r = None
        
        if plat == 0:  # Unicode
            enc = "utf-16be"
        
        elif plat == 1:  # Macintosh
            if scrp == 0:  # Roman
                if lang in frozenset([24, 25, 26, 27, 28, 36, 38, 39, 40]):
                    enc = "mac-centeuro"
                elif lang == 15:
                    enc = "mac-iceland"
                elif lang == 17:
                    enc = "mac-turkish"
                elif lang == 18:
                    enc = "mac-croatian"
                elif lang == 37:
                    enc = "mac-romanian"
                else:
                    enc = "mac-roman"
            
            elif scrp == 1:  # Japanese
                enc = "shift-jis"
                sjmap = {b'\xFD': "©", b'\xFE': "™", b'\xFF': "…"}
                uv = []
                
                for k, g in itertools.groupby(rawBytes, sjmap.__contains__):
                    if k:
                        for c in g:
                            uv.append(sjmap[c])
                    
                    else:
                        try:
                            uv.append(str(bytes(g), enc))
                        
                        except UnicodeDecodeError:
                            r = (rawBytes, False)
                            break
                
                else:
                    r = (''.join(uv), True)
            
            elif scrp == 2:  # Traditional Chinese
                enc = "big5"
            
            elif scrp == 3:  # Korean
                enc = "euc_kr"
                uv = []
                
                skmap = {
                  b'\x81': "₩",
                  b'\x82': "—",
                  b'\x83': "©",
                  b'\xFE': "™",
                  b'\xFF': "…"}
                
                for k, g in itertools.groupby(rawBytes, skmap.__contains__):
                    if k:
                        for c in g:
                            uv.append(skmap[c])
                    
                    else:
                        try:
                            uv.append(str(bytes(g), enc))
                        
                        except UnicodeDecodeError:
                            r = (rawBytes, False)
                            break
                
                else:
                    r = (''.join(uv), True)
            
            elif scrp == 7:  # Russian
                enc = "mac-cyrillic"
            
            elif scrp == 25:  # Simplified Chinese
                enc = "gb2312"
            
            elif scrp == 29:  # Slavic
                enc = "mac-centeuro"
            
            else:
                r = (rawBytes, False)
        
        elif plat == 3:  # Microsoft
            enc = "utf-16be"
        
        else:
            r = (rawBytes, False)
        
        if r is None:
            try:
                r = (str(rawBytes, enc), True)
            
            except UnicodeDecodeError:
                r = (rawBytes, False)  # just a bytes object
        
        return r
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Name object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0002 001E 0001  0000 0000 0001 0004 |................|
              10 | 0000 0001 0002 0013  0002 0006 0004 4142 |..............AB|
              20 | 4384 A677 A46A BDC3                      |C..w.j..        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 0003 0034 0003  0001 8000 0001 0006 |.....4..........|
              10 | 0000 0003 0001 8000  0002 0008 0006 0003 |................|
              20 | 0001 8001 0001 0006  000E 0002 0004 0014 |................|
              30 | 0014 0018 0041 0042  0043 0044 0045 0046 |.....A.B.C.D.E.F|
              40 | 0047 5B89 5927 885B  0065 006E 007A 0068 |.G[.Y'.[.e.n.z.h|
              50 | 002D 0048 0061 006E  0074 002D 0048 004B |.-.H.a.n.t.-.H.K|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # If any string language codes are used, it will have to be format 1.
        langTags = set(t[2] for t in self if isinstance(t[2], str))
        langTagToCode = dict(zip(sorted(langTags), range(0x8000, 0x8000 + len(langTags))))
        format = (1 if langTags else 0)
        
        w.add("2H", format, len(self))
        dataStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, dataStake)
        stringStakes = {}
        
        for t in sorted(self):
            s = self._makeNonUnicode(t)
            
            if t[2] in langTagToCode:
                t = (t[0], t[1], langTagToCode[t[2]], t[3])
            
            w.add("5H", *(t + (len(s),)))
            stake = stringStakes.setdefault(s, w.getNewStake())
            w.addUnresolvedOffset("H", dataStake, stake)
        
        if format == 1:
            w.add("H", len(langTags))
            
            for s in sorted(langTags):
                b = s.encode('utf-16be')
                w.add("H", len(b))
                stake = stringStakes.setdefault(b, w.getNewStake())
                w.addUnresolvedOffset("H", dataStake, stake)
        
        w.stakeCurrentWithValue(dataStake)
        
        # sort on stake for canonical ordering
        for s, stake in sorted(stringStakes.items(), key=operator.itemgetter(1)):
            w.stakeCurrentWithValue(stake)
            w.addString(s)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Name object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = _testingValues[1].binaryString()
        >>> obj = Name.fromvalidatedbytes(s, logger=logger)
        test.name - DEBUG - Walker has 40 remaining bytes.
        test.name - INFO - Format is 0 (original).
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = Name.fromvalidatedbytes(s, logger=logger)
        test.name - DEBUG - Walker has 96 remaining bytes.
        test.name - INFO - Format is 1 (language-tag).
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('name')
        else:
            logger = logger.getChild('name')
        
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, count, stringOffset = w.unpack("3H")
        
        if format == 0:
            logger.info(('V0159', (), "Format is 0 (original)."))
        elif format == 1:
            logger.info(('V0160', (), "Format is 1 (language-tag)."))
        else:
            logger.error(('E2000', (format,), "Unknown format 0x%04X."))
            return None
        
        r = cls()
        
        if count == 0:
            if w.length():
                logger.warning(('V0162', (), "Number of name records is zero, but content remains."))
            else:
                logger.warning(('V0161', (), "Number of name records is zero."))
            
            return r
        
        wData = w.subWalker(stringOffset)
        
        if w.length() < 12 * count:
            logger.error(('V0163', (), "Insufficient bytes for name record array."))
            return None
        
        groups = list(w.group("6H", count))
        okToReturn = True
        
        if groups != sorted(groups):
            logger.error(('E2002', (), "Name records are not sorted."))
            okToReturn = False
        
        for plat, scrp, lang, name, length, offset in groups:
            
            # Note we do not validate the actual values here; that's done in
            # isValid() instead.
            
            if plat in {0, 3} and (length % 2):
                logger.error((
                  'E2012',
                  (plat, scrp, lang, name),
                  "Unicode string length odd for (%d, %d, %d, %d) entry."))
                
                okToReturn = False
                continue
            
            try:
                rawBytes = wData.piece(length, offset, relative=False)
            
            except IndexError:
                logger.error((
                  'V0164',  # same as E2011, effectively
                  (plat, scrp, lang, name),
                  "Insufficient string bytes for (%d, %d, %d, %d) entry."))
                
                okToReturn = False
                continue
            
            key = name_key.Name_Key((plat, scrp, lang, name))
            s, succeeded = cls._rawToUnicode(plat, scrp, lang, rawBytes)
            r[key] = s
            
            if not succeeded:
                logger.warning((
                  'V0166',
                  key,
                  "Could not convert (%d, %d, %d, %d) string to Unicode."))
        
        if format == 1:
            langTags = []
            
            if w.length() < 2:
                logger.error(('V0167', (), "Insufficient bytes for langTag count."))
                return None
            
            count = w.unpack("H")
            
            if not count:
                logger.warning(('V0168', (), "The langTag count is zero."))
            
            else:
                if w.length() < 4 * count:
                    logger.error(('V0169', (), "insufficient bytes for langTag records."))
                    return None
                
                groups = w.group("2H", count)
                
                for i, (ltLen, ltOffset) in enumerate(groups):
                    try:
                        rawBytes = wData.piece(ltLen, ltOffset, relative=False)
                    
                    except IndexError:
                        logger.error(('V0170', (i,), "Insufficient bytes for langTag record [%d]."))
                        okToReturn = False
                        continue
                    
                    langTags.append(str(rawBytes, 'utf-16be'))
                
                toDel = set()
                toAdd = {}
                
                for key in r:
                    if key[2] >= 0x8000:
                        ltIndex = key[2] - 0x8000
                        
                        if ltIndex >= len(langTags):
                            logger.error(('V0171', (key,), "LangTag index for key %s out of range."))
                            okToReturn = False
                            continue
                        
                        newKey = name_key.Name_Key(
                          (key[0], key[1], langTags[ltIndex], key[3]))
                        
                        toAdd[newKey] = r[key]
                        toDel.add(key)
                
                r.update(toAdd)
                
                for key in toDel:
                    del r[key]
        
        return (r if okToReturn else None)
        
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Name object from the data in the specified walker.
        
        >>> _testingValues[1] == Name.frombytes(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == Name.frombytes(_testingValues[2].binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format not in {0, 1}:
            raise ValueError("Unknown 'name' table format: %d" % (format,))
        
        count = w.unpack("H")
        wData = w.subWalker(w.unpack("H"))
        r = cls()
        
        for plat, scrp, lang, name, length, offset in w.group("6H", count):
            rawBytes = wData.piece(length, offset, relative=False)
            key = name_key.Name_Key((plat, scrp, lang, name))
            r[key] = cls._rawToUnicode(plat, scrp, lang, rawBytes)[0]
        
        if format == 1:
            langTags = []
            
            for ltLen, ltOffset in w.group("2H", w.unpack("H")):
                rawBytes = wData.piece(ltLen, ltOffset, relative=False)
                langTags.append(str(rawBytes, 'utf-16be'))
            
            toDel = set()
            toAdd = {}
            
            for key in r:
                if key[2] >= 0x8000:
                    
                    newKey = name_key.Name_Key(
                      (key[0], key[1], langTags[key[2] - 0x8000], key[3]))
                    
                    toAdd[newKey] = r[key]
                    toDel.add(key)
            
            r.update(toAdd)
            
            for key in toDel:
                del r[key]
        
        return r
    
    def getFamilyName(self): return self.getNameFromID(1)
    def getFullName(self): return self.getNameFromID(4)
    
    def getNameFromID(self, nameID, default="Unknown"):
        """
        Find the best available name associated with a given nameID. The order
        in which names are returned is thus:
        
            (3, 1, 1033, nameID)
            (3, 0, 1033, nameID)
            (1, 0, 0, nameID)
            First one found iterating over keys with nameID as [-1] element
        
        >>> n = Name({(3, 0, 1033, 10): "ABC"})
        >>> n.getNameFromID(10)
        'ABC'
        >>> n[(3, 1, 1033, 10)] = "XYZ"
        >>> n.getNameFromID(10)
        'XYZ'
        >>> n.getNameFromID(11)
        'Unknown'
        >>> n.getNameFromID(11, default="No name")
        'No name'
        """
        
        if (3, 1, 1033, nameID) in self:
            return self[(3, 1, 1033, nameID)]
        
        if (3, 0, 1033, nameID) in self:
            return self[(3, 0, 1033, nameID)]
        
        if (1, 0, 0, nameID) in self:
            return self[(1, 0, 0, nameID)]
        
        for k in self:
            if k[-1] == nameID:
                return self[k]

        return default


    def getNextPrivateID(self, **kwArgs):
        """
        Return the next lowest unused nameID >= 256
        
        Note, this can theoretically return > 32767 which is technically
        out-of-spec, but we're leaving that to the caller to check.
        
        >>> x = _testingValues[1]
        >>> x.getNextPrivateID()
        256
        >>> x[(1, 0, 0, 256)] = "test"
        >>> x[(1, 0, 0, 259)] = "test"
        >>> x[(3, 1, 0, 256)] = "test"
        >>> x[(3, 1, 0, 257)] = "test"
        >>> x[(3, 1, 0, 258)] = "test"
        >>> x.getNextPrivateID()
        260
        """
        
        all_platforms = kwArgs.get('allPlatforms', False)
        min_set = list(range(256))
        used = list(set([k[3] for k in self]))

        return findAvailableIndex(min_set + used)


    def getSubfamilyName(self): return self.getNameFromID(2)
        
    def hasNameID(self, nameID):
        """
        Checks whether there is a 'nameID' entry, independent of
        platform/encoding/language. Unlike .getNameFromID(), this merely
        checks for the first one found iterating over keys with nameID
        as [-1] element.
        
        >>> n = Name({(3, 0, 1033, 10): "ABC"})
        >>> n.hasNameID(10)
        True
        >>> n.hasNameID(0)
        False
        """
        
        for k in self:
            if k[-1] == nameID:
                return True

        return False
    
    def subFamilyNameToBits(self):
        """
        Takes the subFamily name string (in English only, sadly) and analyzes
        it to determine whether it has bold, italic, etc. Returns a dict whose
        keys are these normalized style names and whose values are booleans.
        """
        
        d = collections.defaultdict(lambda: False)
        sfName = self.get((3, 1, 1033, 2), "")
        
        if _patBold.findall(sfName):
            d['bold'] = True
        
        if _patItalic.findall(sfName):
            d['italic'] = True
        
        if _patUnderscore.findall(sfName):
            d['underscore'] = True
        
        if _patOutline.findall(sfName):
            d['outline'] = True
        
        if _patStrikeout.findall(sfName):
            d['strikeout'] = True
        
        if _patNegative.findall(sfName):
            d['negative'] = True
        
        return d

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Name(),
        
        Name({
          (1, 0, 0, 1): "ABCÑ",  # N-tilde, maps to MacRoman 0x84
          (1, 2, 19, 2): "安大衛"}),  # An Dawei, my Chinese name
        
        Name({
          (3, 1, "en", 1): "ABC",
          (3, 1, "en", 2): "DEFG",
          (3, 1, "zh-Hant-HK", 1): "安大衛"}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
