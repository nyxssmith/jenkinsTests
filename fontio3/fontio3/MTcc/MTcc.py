#
# MTcc.py
#
# Copyright © 2008-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'MTcc' tables.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.MTcc import record

# -----------------------------------------------------------------------------

#
# Classes
#

class MTcc(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'MTcc' tables. These are tuples of
    Record objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Record %d" % (i,)),
        seq_mergeappend = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTcc object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0001 0000 0008  0001 0045 FFF0 0005 |...........E....|
              10 | 0000 000C 001E FFE2  0001 0004 0000 FFA6 |................|
              20 | 0000 FFFF FF9C 0064                      |.......d        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", 1, len(self))
        stakes = [w.getNewStake() for obj in self]
        
        for stake in stakes:
            w.addUnresolvedOffset("L", stakeValue, stake)
        
        for obj, stake in zip(self, stakes):
            obj.buildBinary(w, stakeValue=stake)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a MTcc object from the specified walker.
        
        >>> fb = MTcc.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        version = w.unpack("H")
        
        if version != 1:
            raise ValueError("Unknown 'MTcc' version: %d" % (version,))
        
        offsets = w.group("L", w.unpack("H"))
        fw = record.Record.fromwalker
        return cls(fw(w.subWalker(offset)) for offset in offsets)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _ar = record._testingValues
    
    _testingValues = (
        MTcc(),
        MTcc([_ar[1]]))
    
    del _ar

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
