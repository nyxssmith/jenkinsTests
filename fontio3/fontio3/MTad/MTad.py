#
# MTad.py
#
# Copyright © 2008-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'MTad' tables.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.MTad import anchorrecord

# -----------------------------------------------------------------------------

#
# Classes
#

class MTad(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'MTad' tables. These are tuples of
    AnchorRecord objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "AnchorRecord %d" % (i,)),
        seq_mergeappend = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTad object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002 0000 000C  0000 005E 0001 0001 |...........^....|
              10 | 0045 FFF0 0005 0001  0002 000C FFE2 0003 |.E..............|
              20 | 0023 00FA 0032 0001  000E 0013 0012 0004 |.#...2..........|
              30 | 0044 FFC9 FFD4 0006  0000 000C 0009 0002 |.D..............|
              40 | 0013 0000 FF9F 000B  0027 FFE4 0024 0001 |.........'...$..|
              50 | 003C 00AA 010A 0002  0018 0384 FE3E 0002 |.<...........>..|
              60 | 0001 0045 FFF0 0005  0001 0002 000C FFE2 |...E............|
              70 | 0003 0023 00FA 0032  0001 000E 0013 0012 |...#...2........|
              80 | 0004 0044 FFC9 FFD4  0006 0000 000C 0009 |...D............|
              90 | 0002 0013 0000 FF9F  000B 0027 FFE4 0024 |...........'...$|
              A0 | 0001 003C 00AA 010A  0002 0018 0384 FE3E |...<...........>|
              B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
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
        Creates and returns a MTad object from the specified walker.
        
        >>> fb = MTad.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        version = w.unpack("H")
        
        if version != 1:
            raise ValueError("Unknown 'MTad' version: %d" % (version,))
        
        offsets = w.group("L", w.unpack("H"))
        fw = anchorrecord.AnchorRecord.fromwalker
        return cls(fw(w.subWalker(offset)) for offset in offsets)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _ar = anchorrecord._testingValues
    
    _testingValues = (
        MTad(),
        MTad([_ar[1], _ar[2]]))
    
    del _ar

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
