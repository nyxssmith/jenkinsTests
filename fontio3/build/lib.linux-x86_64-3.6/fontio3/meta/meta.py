#
# meta.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'meta' tables.
"""

# Other imports
from fontio3.fontdata import binary, mapmeta
from fontio3.meta import codelist, metautils

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    """
    Validate the meta object.

    >>> e = utilities.fakeEditor(5)
    >>> o2 = OS_2_v4.OS_2()
    >>> o2.unicodeRanges.hasBasicLatin = True
    >>> o2.unicodeRanges.hasArabic = True
    >>> e[b'OS/2'] = o2
    >>> e.cmap = cmap.Cmap({(3, 0, 0): {0xF100:10}})
    >>> l = utilities.makeDoctestLogger("meta")
    >>> slng = codelist.Codelist(['Latn', 'Hans', 'Quux'])
    >>> dlng = codelist.Codelist(['en-Latn-US', 'zh-cmn-Hant', 'foo-bar-baz'])
    >>> obj = Meta({'dlng':dlng, 'slng':slng})
    >>> _validate(obj, editor=e, logger=l)
    meta - WARNING - 'dlng' contains entry 'foo-bar-baz' which is not a well-formed ...
    meta - WARNING - Script 'Quux' listed in 'slng' not found in IANA registry (as of ...
    meta - WARNING - 'Hant' listed in 'dlng' but not found in 'slng'
    meta - WARNING - Script 'Hans' in 'slng' but corresponding OS/2 ...
    meta - WARNING - OS/2 Unicode Range indicates hasArabic but none of the Script tags ('Arab', 'Aran') is listed in 'slng'
    meta - WARNING - Symbol font semantics but 'Zsym' not in 'slng'
    False

    >>> obj = Meta()
    >>> _validate(obj, editor=e, logger=l)
    meta - WARNING - The table is completely empty (no metadata tags)
    False

    >>> obj = Meta({'dlng':dlng})
    >>> _validate(obj, editor=e, logger=l)
    meta - WARNING - 'dlng' present but 'slng' is missing or empty.
    meta - WARNING - 'dlng' contains entry 'foo-bar-baz' which is not a well-formed ScriptLangTag
    meta - WARNING - 'Hant' listed in 'dlng' but not found in 'slng'
    meta - WARNING - 'Latn' listed in 'dlng' but not found in 'slng'
    False

    >>> dlng = codelist.Codelist([u'', u'Grek'])
    >>> obj = Meta({'dlng':dlng, 'slng':dlng})
    >>> _validate(obj, editor=e, logger=l)
    meta - WARNING - 'dlng' contains an empty entry
    meta - WARNING - 'slng' contains an empty entry
    meta - WARNING - Script 'Grek' in 'slng' but corresponding OS/2 Unicode Range bit hasGreekAndCoptic not set
    meta - WARNING - OS/2 Unicode Range indicates hasBasicLatin but 'Latn' Script is not listed in 'slng'
    meta - WARNING - OS/2 Unicode Range indicates hasArabic but none of the Script tags ('Arab', 'Aran') is listed in 'slng'
    meta - WARNING - Symbol font semantics but 'Zsym' not in 'slng'
    False

    >>> del(e['OS/2'])
    >>> _validate(obj, editor=e, logger=l)
    meta - WARNING - 'dlng' contains an empty entry
    meta - WARNING - 'slng' contains an empty entry
    meta - WARNING - OS/2 table not present or damaged; cannot compare 'slng' tags to Unicode Range settings
    False
    """
    
    isOK = True
    logger = kwArgs.get('logger')
    editor = kwArgs.get('editor')

    if not obj:
        isOK = False
        logger.warning((
            'V0972',
            (),
            "The table is completely empty (no metadata tags)"))

    dlngs = obj['dlng'].asScriptSet() if 'dlng' in obj else (set(), set())
    slngs = obj['slng'].asScriptSet() if 'slng' in obj else (set(), set())
    valid = metautils.IANA_VALID_SCRIPT_TAGS

    if dlngs[1] and not slngs[1]:
        isOK = False
        
        logger.warning((
            'V0964',
            (),
            "'dlng' present but 'slng' is missing or empty."))

    # dlng and slng contain well-formed ScriptLangTags
    for tag, tobj in (("dlng", dlngs[0]), ("slng", slngs[0])):
        if tobj:
            for lngtag in sorted(tobj):
                if lngtag.strip() == '':
                    isOK = False
                    logger.warning((
                      'Vxxxx',
                      (tag,),
                      "'%s' contains an empty entry"))
                if lngtag and metautils.scriptfromscriptlangtag(lngtag) is None:
                    isOK = False
                    
                    logger.warning((
                        'V0965',
                        (tag, lngtag),
                        "'%s' contains entry '%s' which is not a "
                        "well-formed ScriptLangTag"))

    # dlng and slng are in IANA registry
    for tag, tobj in (("dlng", dlngs[1]), ("slng", slngs[1])):
        extra = tobj - valid
        
        if extra:
            isOK = False
            
            for ex in sorted(extra):
                logger.warning((
                    'V0966',
                    (ex, tag, metautils.REGISTRY_DATE),
                    "Script '%s' listed in '%s' not found in IANA "
                    "registry (as of %s)"))

    # dlng is a subset of slng if present
    extra = dlngs[1] - slngs[1]
    
    if extra:
        isOK = False
        
        for ex in sorted(extra):
            logger.warning((
                'V0967',
                (ex,),
                "'%s' listed in 'dlng' but not found in 'slng'"))

    # slng reflects OS/2 settings if present
    if 'slng' in obj:
        if editor.reallyHas(b'OS/2'):
            os2tbl = editor[b'OS/2']
            uranges = os2tbl.unicodeRanges

            # scripts in 'slng' must have corresponding UR bit set
            for slangtag in sorted(slngs[1]):
                urtuple = metautils.IANA_TO_FONTIO_UNIRANGE_MAP.get(slangtag, tuple())
                
                for ur in urtuple:
                    for urv in ur.split("|"):
                        if urv in uranges._MASKSORT and not getattr(uranges, urv, False):
                            isOK = False
                            
                            logger.warning((
                                'V0968',
                                (slangtag, urv),
                                "Script '%s' in 'slng' but corresponding "
                                "OS/2 Unicode Range bit %s not set"))

            # bit set in UR must have corresponding script tags in 'slng'
            for ur in uranges._MASKSORT:
                if getattr(uranges, ur, False):
                    tagtuple = metautils.FONTIO_UNIRANGE_TO_IANA_MAP.get(ur, tuple())
                    
                    if len(tagtuple) == 0:
                        pass
                    
                    elif len(tagtuple) == 1:
                        if not tagtuple[0] in slngs[1]:
                            isOK = False
                            
                            logger.warning((
                                'V0969',
                                (ur, tagtuple[0]),
                                "OS/2 Unicode Range indicates %s but '%s' "
                                "Script is not listed in 'slng'"))
                    else:
                        if not any([t in slngs[1] for t in tagtuple]):
                            isOK = False
                            
                            logger.warning((
                                'V0969',
                                (ur, tagtuple),
                                "OS/2 Unicode Range indicates %s but none "
                                "of the Script tags %s is listed in 'slng'"))

            # Symbol semantics -> Zsym in 'slng'
            panoseSymbol = os2tbl.panoseArray.family == 5
            cmapTbl = editor.get('cmap', None)
            cmapSymbol = cmapTbl and editor.cmap.findKeys(platform=3, script=0)
            
            if panoseSymbol or cmapSymbol:
                if 'Zsym' not in slngs[1]:
                    isOK = False
                    
                    logger.warning((
                        'V0971',
                        (),
                        "Symbol font semantics but 'Zsym' not in 'slng'"))

        else:
            logger.warning((
                'V0970',
                (),
                "OS/2 table not present or damaged; cannot compare 'slng' "
                "tags to Unicode Range settings"))

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#
if 0:
    def __________________(): pass

class Meta(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Meta objects represent 'meta' tables and map 4-character tags to arbitrary
    data. The tags 'slng' and 'dlng' are expected to map to comma-separated
    strings of 'ScriptLangTag' values, which are a modification of IANA BCP-47
    Language-Tags and indicate scripts.
    """

    mapSpec = dict(
        item_followsprotocol=True,
        map_validatefunc_partial=_validate)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Meta object to the specified writer.

        >>> obj = Meta()
        >>> obj['dlng'] = codelist.Codelist(['ab', 'c', 'def'])
        >>> obj['XxXx'] = binary.Binary.frombytes(b"some binary data")
        >>> utilities.hexdump(obj.binaryString())
               0 | 0000 0001 0000 0000  0000 0028 0000 0002 |...........(....|
              10 | 5878 5878 0000 0028  0000 0010 646C 6E67 |XxXx........dlng|
              20 | 0000 0038 0000 000A  736F 6D65 2062 696E |........some bin|
              30 | 6172 7920 6461 7461  6162 2C20 632C 2064 |ary dataab, c, d|
              40 | 6566                                     |ef              |

        >>> obj2 = Meta.frombytes(obj.binaryString())
        >>> obj == obj2
        True
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("2L", 1, 0)  # version, flags
        firstDataStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, firstDataStake)
        w.add("L", len(self))
        entryStakes = {}
        lengthStakes = {}

        for tag in sorted(self):
            w.add("4s", tag.encode('ascii'))
            entryStakes[tag] = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, entryStakes[tag])
            lengthStakes[tag] = w.addDeferredValue("L")

        fdStaked = False
        
        for tag in sorted(self):
            if not fdStaked:
                w.stakeCurrentWithValue(firstDataStake)
                fdStaked = True
            
            startLen = w.byteLength
            self[tag].buildBinary(w, stakeValue=entryStakes[tag], **kwArgs)
            w.setDeferredValue(lengthStakes[tag], "L", int(w.byteLength - startLen))

        if not fdStaked:
            w.stakeCurrentWithValue(firstDataStake)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Meta object from the specified walker, doing
        validation with supplied logger.

        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = Meta()
        >>> obj['dlng'] = codelist.Codelist(['ab', 'c', 'def'])
        >>> obj['XxXx'] = binary.Binary.frombytes(b"some binary data")
        >>> bs = obj.binaryString()
        >>> obj2 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 66 remaining bytes.
        test.meta - INFO - Table contains 'XxXx' tag
        test.meta - INFO - Table contains 'dlng' tag
        test.meta.codelist - DEBUG - Walker has 10 remaining bytes.
        test.meta.codelist - INFO - List contains 3 items
        >>> obj == obj2
        True
        >>> bs = utilities.fromhex(_testingData[0])
        >>> obj3 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 72 remaining bytes.
        test.meta - WARNING - Data for 'Abcd' tag overlaps data for 'Bcde' tag
        test.meta - WARNING - Gap between data for 'Bcde' and 'Cdef' tags
        test.meta - WARNING - Gap between data for 'Cdef' and 'Defg' tags
        test.meta - INFO - Table contains 'Abcd' tag
        test.meta - INFO - Table contains 'Bcde' tag
        test.meta - INFO - Table contains 'Cdef' tag
        test.meta - ERROR - The offset + length for tag Cdef is out of bounds

        >>> bs = utilities.fromhex(_testingData[0])[0:12]
        >>> obj4 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 12 remaining bytes.
        test.meta - ERROR - Insufficient bytes

        >>> bs = utilities.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
        >>> obj5 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 16 remaining bytes.
        test.meta - ERROR - Expected version 1, but got version 0

        >>> bs = utilities.fromhex("00 00 00 01 01 02 03 04 00 00 00 00 00 00 00 00")
        >>> obj6 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 16 remaining bytes.
        test.meta - WARNING - Flags should be zero, but are 16909060
        test.meta - WARNING - The data section start 0 does not match the expected value 16
        >>> bs = utilities.fromhex(_testingData[0])[:-18]
        >>> obj7 = Meta.fromvalidatedbytes(bs, logger=logger)
        test.meta - DEBUG - Walker has 54 remaining bytes.
        test.meta - ERROR - Insufficient bytes
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('meta')
        else:
            logger = logger.getChild('meta')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None

        baseOffset = w.getOffset(relative=True)
        totalTableAvailLen = w.length()
        version, flags, dataSectionOffset, count = w.unpack("4L")

        if version != 1:
            logger.error((
              'V0002',
              (version,),
              "Expected version 1, but got version %d"))

            return None

        if flags:
            logger.warning((
              'V0980',
              (flags,),
              "Flags should be zero, but are %d"))

        expectedDataOffset = 16 + 12 * count

        if dataSectionOffset != (expectedDataOffset):
            logger.warning((
              'V0981',
              (dataSectionOffset, expectedDataOffset),
              "The data section start %d does not match the expected value %d"))

            return None

        if w.length() < 12 * count:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None

        indexRecs = w.group("4s2L", count)
        wData = w.subWalker(baseOffset)
        r = cls()

        # Check for overlaps/gaps between data (this is not expressly prohibited
        # by the spec, so just warn for now).
        oltRecs = sorted(((ir[1], ir[2], ir[0]) for ir in indexRecs))
        
        for i in range(len(oltRecs)-1):
            rec = oltRecs[i]
            recNext = oltRecs[i+1]

            if rec[0] + rec[1] < recNext[0]:
                logger.warning((
                  'V0982',
                  (str(rec[2], 'ascii'), str(recNext[2], 'ascii')),
                  "Gap between data for '%s' and '%s' tags"))

            if rec[0] + rec[1] > recNext[0]:
                logger.warning((
                  'V0983',
                  (str(rec[2], 'ascii'), str(recNext[2], 'ascii')),
                  "Data for '%s' tag overlaps data for '%s' tag"))

        for tag, offset, length in indexRecs:
            tag = str(tag, 'ascii')
            
            logger.info((
              'Vxxxx',
              (tag,),
              "Table contains '%s' tag"))

            if offset < expectedDataOffset:
                logger.error((
                  'V0984',
                  (tag,),
                  "The offset for tag %s is too low (before the expected "
                  "table-wide dataOffset)"))

                return None

            if offset + length > totalTableAvailLen:
                logger.error((
                  'V0985',
                  (tag,),
                  "The offset + length for tag %s is out of bounds"))

                return None

            wSub = wData.subWalker(offset, relative=True, newLimit=length)

            if tag in {'dlng', 'slng'}:
                f = codelist.Codelist.fromvalidatedwalker
            else:
                f = binary.Binary.fromvalidatedwalker

            r[tag] = f(wSub, logger=logger, **kwArgs)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Meta object from the specified walker.

        >>> obj = Meta()
        >>> obj['dlng'] = codelist.Codelist(['ab', 'c', 'def'])
        >>> obj['XxXx'] = binary.Binary.frombytes(b"some binary data")
        >>> bs = obj.binaryString()
        >>> bigString = b'Z' * 100 + bs
        >>> w = walkerbit.StringWalker(bigString)
        >>> ignore = w.group("B", 100)
        >>> obj2 = Meta.fromwalker(w)
        >>> obj == obj2
        True
        """

        baseOffset = w.getOffset(relative=True)
        version = w.unpack("L")

        if version != 1:
            raise ValueError("Unknown 'meta' version: %d" % (version,))

        flags, dataSectionOffset, count = w.unpack("3L")
        indexRecs = w.group("4s2L", count)
        wData = w.subWalker(baseOffset)
        r = cls()

        for tag, offset, length in indexRecs:
            tag = str(tag, 'ascii')
            wSub = wData.subWalker(offset, relative=True, newLimit=length)

            if tag in {'dlng', 'slng'}:
                f = codelist.Codelist.fromwalker
            else:
                f = binary.Binary.fromwalker

            r[tag] = f(wSub, **kwArgs)

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.cmap import cmap
    from fontio3.OS_2 import OS_2_v4
    from fontio3.utilities import walkerbit

    _testingData = (
        "00 00 00 01 00 00 00 00 00 00 00 40 00 00 00 04 41 62 63 64 00 "
        "00 00 40 00 00 00 05 42 63 64 65 00 00 00 42 00 00 00 05 43 64 "
        "65 66 00 00 00 48 00 00 00 05 44 65 66 67 00 00 00 FF 00 00 00 "
        "05 DE AD BE EF DE AD BE EF",)

def _test():
    import doctest

    doctest.testmod(optionflags=doctest.ELLIPSIS)

if __name__ == "__main__":
    if __debug__:
        _test()

