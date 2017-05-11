#
# anchorrecord.py
#
# Copyright © 2008-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AnchorRecords (which are tuples of AnchorTuples).
"""

# System imports
import itertools

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.MTad import anchortuple

# -----------------------------------------------------------------------------

#
# Classes
#

class AnchorRecord(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Tuples of AnchorTuples.
    
    The data format is:
        count (UInt16)
        This is followed by count AnchorTuples (q.v.)
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "AnchorTuple %d" % (i,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AnchorRecord object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0001 0045 FFF0  0005 0001 0002 000C |.....E..........|
              10 | FFE2 0003 0023 00FA  0032 0001 000E 0013 |.....#...2......|
              20 | 0012 0004 0044 FFC9  FFD4 0006 0000 000C |.....D..........|
              30 | 0009 0002 0013 0000  FF9F 000B 0027 FFE4 |.............'..|
              40 | 0024 0001 003C 00AA  010A 0002 0018 0384 |.$...<..........|
              50 | FE3E                                     |.>              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a AnchorRecord object from the specified walker.
        
        >>> fb = AnchorRecord.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        count = w.unpack("H")
        fw = anchortuple.AnchorTuple.fromwalker
        return cls(map(fw, itertools.repeat(w, count)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _at = anchortuple._testingValues
    
    _testingValues = (
        AnchorRecord(),
        AnchorRecord([_at[0]]),
        AnchorRecord([_at[0], _at[1]]))
    
    del _at

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
