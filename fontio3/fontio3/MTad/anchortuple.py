#
# anchortuple.py
#
# Copyright © 2008-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AnchorTuples (collections of 10 Anchors) for the 'MTad' table.
"""

# System imports
import itertools

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.MTad import anchor

# -----------------------------------------------------------------------------

#
# Classes
#

class AnchorTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Tuples of exactly 10 Anchors. The data format is just the 10 Anchors with
    no preceding count.
    
    >>> _testingValues[0].pprint()
    Anchor 0:
      Anchor type: 1
      Point index: 69
      X-coordinate: -16
      Y-coordinate: 5
    Anchor 1:
      Anchor type: 1
      Point index: 2
      X-coordinate: 12
      Y-coordinate: -30
    Anchor 2:
      Anchor type: 3
      Point index: 35
      X-coordinate: 250
      Y-coordinate: 50
    Anchor 3:
      Anchor type: 1
      Point index: 14
      X-coordinate: 19
      Y-coordinate: 18
    Anchor 4:
      Anchor type: 4
      Point index: 68
      X-coordinate: -55
      Y-coordinate: -44
    Anchor 5:
      Anchor type: 6
      Point index: 0
      X-coordinate: 12
      Y-coordinate: 9
    Anchor 6:
      Anchor type: 2
      Point index: 19
      X-coordinate: 0
      Y-coordinate: -97
    Anchor 7:
      Anchor type: 11
      Point index: 39
      X-coordinate: -28
      Y-coordinate: 36
    Anchor 8:
      Anchor type: 1
      Point index: 60
      X-coordinate: 170
      Y-coordinate: 266
    Anchor 9:
      Anchor type: 2
      Point index: 24
      X-coordinate: 900
      Y-coordinate: -450
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Anchor %d" % (i,)),
        seq_fixedlength = 10)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AnchorTuple object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0045 FFF0 0005  0001 0002 000C FFE2 |...E............|
              10 | 0003 0023 00FA 0032  0001 000E 0013 0012 |...#...2........|
              20 | 0004 0044 FFC9 FFD4  0006 0000 000C 0009 |...D............|
              30 | 0002 0013 0000 FF9F  000B 0027 FFE4 0024 |...........'...$|
              40 | 0001 003C 00AA 010A  0002 0018 0384 FE3E |...<...........>|
        """
        
        for obj in self:
            obj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an AnchorTuple object from the specified walker.
        
        >>> fb = AnchorTuple.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        fw = anchor.Anchor.fromwalker
        return cls(map(fw, itertools.repeat(w, 10)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _av = anchor._testingValues
    
    _testingValues = (
        AnchorTuple(_av[1:11]),
        AnchorTuple(anchor.Anchor() for i in range(10)))
    
    del _av

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
