#
# groups20.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ADFH 2.0 groups (MAZ/BAZ).
"""

# Other imports
import itertools
import logging
import warnings

# Other imports
from fontio3 import utilities
from fontio3.ADFH import grouprecord
from fontio3.fontdata import mapmeta
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class Groups(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing BAZ group information for version 2.0 'ADFH' tables.
    These are dicts mapping glyph indices to GroupRecord objects. Note that
    missing keys or keys explicitly mapping to None will be treated as MAZ
    glyphs, and will not be present in the binary data.
    
    >>> _testingValues[2].pprint()
    [300-359]:
      Index of first CVT value: 4
      Number of y-lines: 12
      Adjust strokes right-to-left: True
    [1200-1249, 1400-1419]:
      Index of first CVT value: 12
      Number of y-lines: 30
      Adjust strokes right-to-left: False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        map_pprintfunc = pp.PP.mapping_grouped_deep)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Groups object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 04B0 04E1 0000  0578 058B 0000 0001 |.........x......|
              10 | 000C 001E 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0003 012C 0167 0000  04B0 04E1 0001 0578 |...,.g.........x|
              10 | 058B 0001 0002 0004  000C 0001 0000 000C |................|
              20 | 001E 0000 0000                           |......          |
        """
        
        countStake = w.addDeferredValue("H")
        itBig = (i for i in sorted(self) if self[i] is not None)
        groupCount = 0
        pool = {}
        poolList = []
        
        for start, stop, delta in utilities.monotonicGroupsGenerator(itBig):
            it = (self[i] for i in range(start, stop))
            
            for k, g in itertools.groupby(it):
                groupCount += 1
                v = list(g)
                last = start + len(v) - 1
                immut = v[0].asImmutable()
                
                if immut not in pool:
                    pool[immut] = len(poolList)
                    poolList.append(v[0])
                
                w.add("3H", start, last, pool[immut])
                start = last + 1
        
        w.setDeferredValue(countStake, "H", groupCount)
        
        if poolList:
            w.add("H", len(poolList))
            
            for obj in poolList:
                obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def from15(cls, g):
        """
        Returns a Groups from a version 1.5 Groups. It maps all the glyphs to
        the same object.
        """
        
        rec = grouprecord.GroupRecord()  # use defaults for initial rec
        return cls(zip(g, itertools.repeat(rec)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Groups object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("groups20_fvw")
        >>> fvb = Groups.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        groups20_fvw.groups20 - DEBUG - Walker has 24 remaining bytes.
        groups20_fvw.groups20.group 0.grouprecord - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        groups20_fvw.groups20 - DEBUG - Walker has 1 remaining bytes.
        groups20_fvw.groups20 - ERROR - Insufficient bytes.
        
        >>> fvb(s[:5], logger=logger)
        groups20_fvw.groups20 - DEBUG - Walker has 5 remaining bytes.
        groups20_fvw.groups20 - ERROR - The group index records are missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("groups20")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        groupIndexCount = w.unpack("H")
        
        if w.length() < 6 * groupIndexCount:
            logger.error((
              'V0589',
              (),
              "The group index records are missing or incomplete."))
            
            return None
        
        groupIndices = w.group("3H", groupIndexCount)
        fvw = grouprecord.GroupRecord.fromvalidatedwalker
        
        if any(x[2] != 0xFFFF for x in groupIndices):
            if w.length() < 2:
                logger.error((
                  'V0596',
                  (),
                  "The group count is missing or incomplete."))
                
                return None
            
            groupCount = w.unpack("H")
            groupRecords = [None] * groupCount
            
            for i in range(groupCount):
                groupRecords[i] = fvw(
                  w,
                  logger = logger.getChild("group %d" % (i,)))
            
            if any(x is None for x in groupRecords):
                return None
        
        else:
            groupRecords = []
            groupCount = 0
            
        usedData = set()
        okToProceed = True
        r = cls()
        
        for start, end, index in groupIndices:
            if index != 0xFFFF and index >= groupCount:
                logger.error((
                  'V0597',
                  (start, end, index),
                  "The group from glyph %d through glyph %d refers to "
                  "group number %d, which does not exist."))
                
                okToProceed = False
                break
            
            usedData.add(index)
            rec = (None if index == 0xFFFF else groupRecords[index])
            r.update(zip(range(start, end + 1), itertools.repeat(rec)))
        
        if not okToProceed:
            return None
        
        if groupCount:
            unusedGroups = set(range(groupCount)) - usedData
            
            if unusedGroups:
                logger.warning((
                  'V0598',
                  (sorted(unusedGroups),),
                  "The following group(s) were never referenced: %s"))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Groups object from the specified walker.
        
        >>> fb = Groups.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        r = cls()
        groupIndices = w.group("3H", w.unpack("H"))
        grfw = grouprecord.GroupRecord.fromwalker
        
        if any(x[2] != 0xFFFF for x in groupIndices):
            groupRecords = list(grfw(w) for i in range(w.unpack("H")))
        else:
            groupRecords = []
        
        usedData = set()
        
        for start, end, index in groupIndices:
            usedData.add(index)
            rec = (None if index == 0xFFFF else groupRecords[index])
            r.update(zip(range(start, end + 1), itertools.repeat(rec)))
        
        unusedData = set(range(len(groupRecords))) - usedData
        
        if unusedData:
            warnings.warn("Warning: 'ADFH' binary data has unused groups!")
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _grv = grouprecord._testingValues
    _g1 = Groups()
    _g2 = Groups()
    
    for i in itertools.chain(iter(range(1200, 1250)), iter(range(1400, 1420))):
        _g1[i] = _g2[i] = _grv[1]
    
    for i in range(300, 360):
        _g2[i] = _grv[2]
    
    _testingValues = (
        Groups(),
        _g1,
        _g2)
    
    del _grv, _g1, _g2, i

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
