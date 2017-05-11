#
# grouptable.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for group tables.
"""

# System imports
import itertools

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GroupTable(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    """
    
    kind = 0
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GroupTable object to the specified
        LinkedWriter.
        
        >>> obj = GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> utilities.hexdump(obj.binaryString())
               0 | 0005 0004 0003 0006  0000 0007 0001 0008 |................|
              10 | 0003 000F 0002                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        counts = []
        
        for k, g in itertools.groupby(self):
            counts.append((k, len(list(g))))
        
        w.add("H", len(counts))
        startGlyph = 0
        
        for key, count in counts:
            w.add("2H", startGlyph + count - 1, key)
            startGlyph += count
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> fvb = GroupTable.fromvalidatedbytes
        >>> obj = GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> bs = obj.binaryString()
        >>> obj2 = fvb(bs, logger=logger)
        test.grouptable - DEBUG - Walker has 22 remaining bytes.
        test.grouptable - DEBUG - Count is 5, raw data is ((4, 3), (6, 0), (7, 1), (8, 3), (15, 2))
        >>> obj == obj2
        True
        
        We flip the order of the final two groups:
        
        >>> bsBad = bs[:-8] + bs[-4:] + bs[-8:-4]
        >>> fvb(bsBad, logger=logger)
        test.grouptable - DEBUG - Walker has 22 remaining bytes.
        test.grouptable - DEBUG - Count is 5, raw data is ((4, 3), (6, 0), (7, 1), (15, 2), (8, 3))
        test.grouptable - ERROR - Groups not sorted by end glyph index.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('grouptable')
        else:
            logger = logger.getChild('grouptable')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        numRanges = w.unpack("H")
        
        if w.length() < 4 * numRanges:
            logger.error(('V0004', (), "Insufficient data for ranges."))
            return None
        
        rangeData = w.group("2H", numRanges)
        
        logger.debug((
          'Vxxxx',
          (numRanges, rangeData),
          "Count is %d, raw data is %s"))
        
        sortTest = [t[0] for t in rangeData]
        
        if sortTest != sorted(sortTest):
            logger.error((
              'Vxxxx',
              (),
              "Groups not sorted by end glyph index."))
            
            return None
        
        v = []
        currGlyph = 0
        
        for endGlyph, groupID in rangeData:
            count = endGlyph - currGlyph + 1
            v.extend([groupID] * count)
            currGlyph = endGlyph + 1
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GroupTable object from the specified walker.
        
        >>> obj = GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> bs = obj.binaryString()
        >>> obj2 = GroupTable.frombytes(bs)
        >>> obj == obj2
        True
        """
        
        rangeData = w.group("2H", w.unpack("H"))
        v = []
        currGlyph = 0
        
        for endGlyph, groupID in rangeData:
            if endGlyph < currGlyph:
                raise ValueError("Ranges not sorted!")
            
            count = endGlyph - currGlyph + 1
            v.extend([groupID] * count)
            currGlyph = endGlyph + 1
        
        return cls(v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


