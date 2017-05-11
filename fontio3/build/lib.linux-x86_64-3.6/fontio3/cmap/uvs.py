#
# uvs.py
#
# Copyright © 2011, 2013, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 14 Unicode Variation Selector mappings. Note that format 14
is substantially different than the other subtable formats; the data defined
here is present as an attribute on the top-level ``Cmap`` object, and not as an
entry in the ``Cmap`` dict.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.cmap import uvs_entry
from fontio3.fontdata import mapmeta
from fontio3.utilities import span2

# -----------------------------------------------------------------------------

#
# Private functions
#

def _vs_pprint(key):
    if key <= 0xFE0F:
        return "VS%d (U+%04X)" % (key - 0xFDFF, key)
    
    return "VS%d (U+%06X)" % (key - 0xE00EF, key)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class UVS(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing mappings for Unicode variations. These are dicts mapping
    Unicode selector scalars (``U+FE00`` through ``U+FE0F``, and ``U+E0100``
    through ``U+E01EF``) to :py:class:`~fontio3.cmap.uvs_entry.UVS_Entry``
    objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    VS2 (U+FE01):
      U+614E: xyz24
      U+6226: afii60002
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    VS4 (U+FE03):
      Default mappings:
        U+4E01
        U+4E08
    VS17 (U+0E0100):
      U+89EE: xyz42
      Default mappings:
        U+5225
        U+022F43
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = _vs_pprint,
        item_pprintlabelpresort = True)
    
    #
    # Methods
    #
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        if endOfWalker < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        format, size = w.unpack("HL")
        
        if format != 14:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return False
        
        if endOfWalker != size:
            logger.warning((
              'V0011',
              (int(size), int(endOfWalker)),
              "Size field value (0x%08X) is not expected (0x%08X)."))
        
        return True
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (see below)
        :return: None
        :raises ValueError: if no eligible subtable format can accommodate
            the data present in ``self``
        
        The following ``kwArgs`` are supported:
        
        ``stakeValue``
            A stake that will be placed at the start of the binary data laid
            down by this method. One will be synthesized if not provided.
            See :py:class:`~fontio3.utilities.writer.LinkedWriter` for a
            description of stakes and how they're used.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000E 0000 0023 0000  0001 00FE 0100 0000 |.....#..........|
              10 | 0000 0000 1500 0000  0200 614E 0017 0062 |..........aN...b|
              20 | 2600 61                                  |&.a             |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 000E 0000 0041 0000  0002 00FE 0300 0000 |.....A..........|
              10 | 2000 0000 000E 0100  0000 002C 0000 0038 | ..........,...8|
              20 | 0000 0002 004E 0100  004E 0800 0000 0002 |.....N...N......|
              30 | 0052 2500 022F 4300  0000 0001 0089 EE00 |.R%../C.........|
              40 | 29                                       |)               |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        startLength = w.byteLength
        w.add("H", 14)  # format
        lengthStake = w.addDeferredValue("L")
        w.add("L", len(self))
        defStakes = {}
        nonDefStakes = {}
        
        for vs in sorted(self):
            w.add("T", vs)
            d = self[vs]
            
            if d.default:
                defStakes[vs] = w.getNewStake()
                w.addUnresolvedOffset("L", stakeValue, defStakes[vs])
            else:
                w.add("L", 0)
            
            if len(d):
                nonDefStakes[vs] = w.getNewStake()
                w.addUnresolvedOffset("L", stakeValue, nonDefStakes[vs])
            else:
                w.add("L", 0)
        
        for vs in sorted(self):
            d = self[vs]
            
            if vs in defStakes:
                w.stakeCurrentWithValue(defStakes[vs])
                s = span2.Span(d.default)
                count = 0
                countStake = w.addDeferredValue("L")
                
                for first, last in s.ranges():
                    spanCount = last - first + 1
                    
                    while spanCount:
                        pieceCount = min(256, spanCount)
                        w.add("TB", first, pieceCount - 1)
                        count += 1
                        first += pieceCount
                        spanCount -= pieceCount
                
                w.setDeferredValue(countStake, "L", count)
            
            if vs in nonDefStakes:
                w.stakeCurrentWithValue(nonDefStakes[vs])
                w.add("L", len(d))
                w.addGroup("TH", sorted(d.items(), key=operator.itemgetter(0)))
        
        #w.alignToByteMultiple(2)
        w.setDeferredValue(lengthStake, "L", int(w.byteLength - startLength))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``UVS`` instance from the specified walker, performing
        validation on the correctness of the binary data.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (see below)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        The following ``kwArgs`` are supported:
        
        ``logger``
            A logger to which validation information will be posted.
        
        >>> logger = utilities.makeDoctestLogger('test.cmap')
        >>> fh = utilities.fromhex
        >>> s = b""
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 0 remaining bytes.
        test.cmap.format14 - ERROR - Insufficient bytes.
        
        >>> s = fh("00 0F 00 00 00 06")
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 6 remaining bytes.
        test.cmap.format14 - ERROR - Invalid format (0x000F).
        
        >>> s = fh("00 0E 00 00 00 19")
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 6 remaining bytes.
        test.cmap.format14 - WARNING - Size field value (0x00000019) is not expected (0x00000006).
        test.cmap.format14 - ERROR - Insufficient bytes for count.
        
        >>> s = fh("00 0E 00 00 00 0A 00 00 00 00")
        >>> obj = UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 10 remaining bytes.
        
        >>> s = fh("00 0E 00 00 00 0A 00 00 00 01")
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 10 remaining bytes.
        test.cmap.format14 - ERROR - Insufficient bytes for groups.
        
        >>> s = fh("00 0E 00 00 00 20 00 00 00 02 00 FE 04 00 00 00 "
        ...        "00 00 00 00 00 00 FE 02 00 00 00 00 00 00 00 00")
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 32 remaining bytes.
        test.cmap.format14 - ERROR - Groups not sorted by variation selector.
        
        >>> s = fh("00 0E 00 00 00 15 00 00 00 01 00 FE 44 00 00 00 "
        ...        "00 00 00 00 00")
        >>> UVS.fromvalidatedbytes(s, logger=logger)
        test.cmap.format14 - DEBUG - Walker has 21 remaining bytes.
        test.cmap.format14 - ERROR - U+00FE44 is not a valid variation selector.
        
        xxx more tests here
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format14')
        else:
            logger = logger.getChild('format14')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        okToProceed = cls._validate_header(w, logger, endOfWalker)
        
        if not okToProceed:
            return None
        
        r = cls()
        
        if w.length() < 2:
            logger.error(('V0058', (), "Insufficient bytes for count."))
            return None
        
        groupCount = w.unpack("L")
        
        if w.length() < 11 * groupCount:
            logger.error(('V0059', (), "Insufficient bytes for groups."))
            return None
        
        groups = list(w.group("T2L", groupCount))
        
        if (
          (len(groups) > 1) and
          (groups != sorted(groups, key=operator.itemgetter(0)))):
            
            logger.error((
              'V0061',
              (),
              "Groups not sorted by variation selector."))
            
            okToProceed = False
        
        for varSelector, defOffset, nonDefOffset in groups:
            if not (
              (0xFE00 <= varSelector < 0xFE10) or
              (0xE0100 <= varSelector < 0xE01F0)):
                
                logger.error((
                  'V0060',
                  (varSelector,),
                  "U+%06X is not a valid variation selector."))
                
                okToProceed = False
            
            d = uvs_entry.UVS_Entry()
            
            if defOffset:
                if defOffset >= endOfWalker:
                    logger.error((
                      'V0062',
                      (defOffset, endOfWalker, varSelector),
                      "Default offset 0x%08X exceeds subtable end 0x%08X "
                      "for UVS %06X."))
                    
                    okToProceed = False
                
                else:
                    wDef = w.subWalker(defOffset)
                    
                    if wDef.length() < 4:
                        logger.error((
                          'V0063',
                          (varSelector,),
                          "Insufficient bytes for default count for "
                          "UVS %06X."))
                        
                        okToProceed = False
                    
                    else:
                        numRecs = wDef.unpack("L")
                        
                        if wDef.length() < numRecs * 4:
                            logger.error((
                              'V0064',
                              (varSelector,),
                              "Insufficient bytes for default groups for "
                              "UVS %06X."))
                            
                            okToProceed = False
                        
                        defGroups = list(wDef.group("TB", numRecs))
                        
                        if numRecs > 1:
                            s = sorted(defGroups, key=operator.itemgetter(0))
                            
                            if defGroups != s:
                                logger.error((
                                  'V0065',
                                  (varSelector,),
                                  "Default groups not sorted by Unicode for "
                                  "UVS %06X."))
                                
                                okToProceed = False
                            
                            it = zip(
                              defGroups,
                              itertools.islice(defGroups, 1, None))
                            
                            if not all(t1[0] + t1[1] < t2[0] for t1, t2 in it):
                                logger.error((
                                  'V0066',
                                  (varSelector,),
                                  "Default groups have overlaps for "
                                  "UVS %06X."))
                                
                                okToProceed = False
                        
                        for start, extraCount in defGroups:
                            d.default.update(
                              range(start, start + extraCount + 1))
            
            if nonDefOffset:
                if nonDefOffset >= endOfWalker:
                    logger.error((
                      'V0067',
                      (nonDefOffset, endOfWalker, varSelector),
                      "Non-default offset 0x%08X exceeds subtable end "
                      "0x%08X for UVS %06X."))
                    
                    okToProceed = False
                
                else:
                    wNonDef = w.subWalker(nonDefOffset)
                    
                    if wNonDef.length() < 4:
                        logger.error((
                          'V0068',
                          (varSelector,),
                          "Insufficient bytes for non-default count for "
                          "UVS %06X."))
                        
                        okToProceed = False
                    
                    else:
                        numRecs = wNonDef.unpack("L")
                        
                        if wNonDef.length() < numRecs * 5:
                            logger.error((
                              'V0069',
                              (varSelector,),
                              "Insufficient bytes for non-default groups for "
                              "UVS %06X."))
                            
                            okToProceed = False
                        
                        nonDefGroups = list(wNonDef.group("TH", numRecs))
                        
                        if numRecs > 1:
                            s = sorted(
                              nonDefGroups,
                              key = operator.itemgetter(0))
                            
                            if nonDefGroups != s:
                                logger.error((
                                  'V0070',
                                  (varSelector,),
                                  "Non-default groups not sorted by Unicode "
                                  "for UVS %06X."))
                                
                                okToProceed = False
                            
                            if numRecs > len(set(t[0] for t in nonDefGroups)):
                                logger.error((
                                  'V0071',
                                  (varSelector,),
                                  "Non-default groups have duplicate Unicodes "
                                  "for UVS %06X."))
                                
                                okToProceed = False
                        
                        for c, glyph in nonDefGroups:
                            d[c] = glyph
            
            if d:
                r[varSelector] = d
        
        return (r if okToProceed else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``UVS`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> obj = _testingValues[1]
        >>> obj == UVS.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == UVS.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 14
        r = cls()
        g = w.group("T2L", w.unpack("4xL"))
        
        for varSelector, defOffset, nonDefOffset in g:
            d = uvs_entry.UVS_Entry()
            
            if defOffset:
                wDef = w.subWalker(defOffset)
                
                for start, extraCount in wDef.group("TB", wDef.unpack("L")):
                    d.default.update(range(start, start + extraCount + 1))
            
            if nonDefOffset:
                wNonDef = w.subWalker(nonDefOffset)
                
                for c, glyph in wNonDef.group("TH", wNonDef.unpack("L")):
                    d[c] = glyph
            
            if d:
                r[varSelector] = d
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _uetv = uvs_entry._testingValues
    
    _testingValues = (
        UVS(),
        
        UVS({0xFE01: _uetv[1]}),
        
        UVS({0xFE03: _uetv[2], 0xE0100: _uetv[3]}))
    
    del _uetv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
