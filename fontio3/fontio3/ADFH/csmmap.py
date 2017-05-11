#
# csmmap.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for maps from glyph index to CSMEntry.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.ADFH import csmentry
from fontio3.fontdata import mapmeta
from fontio3.utilities import pp, span2

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs.pop('logger')
    r = True
    
    # gather together all glyphs that refer to a given entry, so we only need
    # to put one message out for the whole lot, instead of per-glyph messages.
    
    idToImmut = {}
    immutToObjSpan = {}
    
    for glyphIndex, csmEntry in obj.items():
        entryID = id(csmEntry)
        
        if entryID not in idToImmut:
            idToImmut[entryID] = csmEntry.asImmutable()
        
        immut = idToImmut[entryID]
        
        if immut not in immutToObjSpan:
            immutToObjSpan[immut] = (csmEntry, span2.Span())
        
        immutToObjSpan[immut][1].add(glyphIndex)
    
    for csmEntry, s in immutToObjSpan.values():
        subLogger = logger.getChild("glyphs %s" % (s,))
        r = csmEntry.isValid(logger=subLogger, **kwArgs) and r
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CSMMap(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping glyph indices to CSMEntry objects.
    
    >>> _testingValues[1].pprint()
    [0-1399]:
      Entry #1:
        Lower limit of size range (inclusive): 12
        Inside cutoff: 0.25
        Outside cutoff: -2.0
        Gamma: -0.25
      Entry #2:
        Lower limit of size range (inclusive): 20
        Inside cutoff: 0.75
        Outside cutoff: -1.0
        Gamma: -0.25
    [1400-1402]:
      Entry #1:
        Lower limit of size range (inclusive): 18
        Inside cutoff: -0.5
        Outside cutoff: 0.25
        Gamma: 0.5
    [1403-1999]:
      Entry #1:
        Lower limit of size range (inclusive): 12
        Inside cutoff: 0.25
        Outside cutoff: -2.0
        Gamma: -0.25
      Entry #2:
        Lower limit of size range (inclusive): 20
        Inside cutoff: 0.75
        Outside cutoff: -1.0
        Gamma: -0.25
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
      item_followsprotocol = True,
      item_renumberdirectkeys = True,
      item_subloggernamefunc = (lambda n: "glyph %d" % (n,)),
      map_pprintfunc = pp.PP.mapping_grouped_deep,
      map_validatefunc = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CSMMap to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0003 002E 0577 0000  057A 001E 07CF 0000 |.....w...z......|
              10 | 0002 000C 0000 4000  FFFE 0000 FFFF C000 |......@.........|
              20 | 0014 0000 C000 FFFF  0000 FFFF C000 0001 |................|
              30 | 0012 FFFF 8000 0000  4000 0000 8000      |........@.....  |
        """
        
        i = 0
        d = {} 
        objList = []
        mc = operator.methodcaller('asImmutable')
        
        for k, g in itertools.groupby((self[k] for k in sorted(self)), key=mc):
            v = list(g)
            
            if k not in d:
                d[k] = (v[0], w.getNewStake(), [])
                objList.append((v[0], d[k][1]))
            
            d[k][-1].append(i + len(v))
            i += len(v)
        
        ranges = sorted(
          (stop, t[1])
          for immut, t in d.items()
          for stop in t[-1])
        
        w.add("H", len(ranges))
        byteLengthStake = w.addDeferredValue("H")
        csmEntriesStake = w.getNewStake()
        
        for stop, stake in ranges:
            w.add("H", stop - 1)
            w.addUnresolvedOffset("H", csmEntriesStake, stake)
        
        startOffset = w.byteLength
        w.stakeCurrentWithValue(csmEntriesStake)
        
        for obj, stake in objList:
            obj.buildBinary(w, stakeValue=stake)
        
        w.setDeferredValue(byteLengthStake, "H", w.byteLength - startOffset)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a CSMMap object from the specified walker, doing
        source validation.
        
        >>> logger = utilities.makeDoctestLogger("csmmap_test")
        >>> s = _testingValues[1].binaryString()
        >>> fvb = CSMMap.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        csmmap_test.csmmap - DEBUG - Walker has 62 remaining bytes.
        csmmap_test.csmmap.glyph 0 thru glyph 1399.csmentry - DEBUG - Walker has 46 remaining bytes.
        csmmap_test.csmmap.glyph 0 thru glyph 1399.csmentry.entry 0.csmrecord - DEBUG - Walker has 44 remaining bytes.
        csmmap_test.csmmap.glyph 0 thru glyph 1399.csmentry.entry 1.csmrecord - DEBUG - Walker has 30 remaining bytes.
        csmmap_test.csmmap.glyph 1400 thru glyph 1402.csmentry - DEBUG - Walker has 16 remaining bytes.
        csmmap_test.csmmap.glyph 1400 thru glyph 1402.csmentry.entry 0.csmrecord - DEBUG - Walker has 14 remaining bytes.
        
        >>> fvb(s[:3], logger=logger)
        csmmap_test.csmmap - DEBUG - Walker has 3 remaining bytes.
        csmmap_test.csmmap - ERROR - Insufficient bytes.
        
        >>> fvb(s[:5], logger=logger)
        csmmap_test.csmmap - DEBUG - Walker has 5 remaining bytes.
        csmmap_test.csmmap - ERROR - The CSMRangeArray is missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("csmmap")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count, byteSize = w.unpack("2H")
        
        if w.length() < 4 * count:
            logger.error((
              'V0575',
              (),
              "The CSMRangeArray is missing or incomplete."))
            
            return None
        
        recs = w.group("2H", count)
        wEntryBase = w.subWalker(0, relative=True)
        pool = {}
        r = cls()
        startGlyph = 0
        f = csmentry.CSMEntry.fromvalidatedwalker
        
        for endGlyphIndex, offset in recs:
            if offset not in pool:
                subLogger = logger.getChild(
                  "glyph %d thru glyph %d" % (startGlyph, endGlyphIndex))
                
                obj = f(wEntryBase.subWalker(offset), logger=subLogger)
                
                if obj is None:
                    return None
                
                pool[offset] = obj
            
            obj = pool[offset]
            
            for i in range(startGlyph, endGlyphIndex + 1):
                r[i] = obj
            
            startGlyph = endGlyphIndex + 1
        
        if w.length() < byteSize:
            logger.error((
              'V0576',
              (byteSize,),
              "The byteSize is %d, but there are not that many bytes left."))
            
            return None
        
        w.skip(byteSize)
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a CSMMap object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == CSMMap.frombytes(obj.binaryString())
        True
        """
        
        count, byteSize = w.unpack("2H")
        recs = w.group("2H", count)
        wEntryBase = w.subWalker(0, relative=True)
        pool = {}
        r = cls()
        startGlyph = 0
        f = csmentry.CSMEntry.fromwalker
        
        for endGlyphIndex, offset in recs:
            if offset not in pool:
                pool[offset] = f(wEntryBase.subWalker(offset))
            
            obj = pool[offset]
            
            for i in range(startGlyph, endGlyphIndex + 1):
                r[i] = obj
            
            startGlyph = endGlyphIndex + 1
        
        w.skip(byteSize)
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _ev = csmentry._testingValues
    _tv1 = CSMMap((i, _ev[1]) for i in range(2000))
    _tv1[1400] = _tv1[1401] = _tv1[1402] = _ev[2]
    
    _testingValues = (
        CSMMap(),
        _tv1)
    
    del _ev

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
