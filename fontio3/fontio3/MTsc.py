#
# MTsc.py
#
# Copyright © 2007-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'MTsc' (class name strings) table.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class MTsc(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing lists of class names. The MTsf.Record objects store
    the actual strings, not indices into the MTsc list. This allows live
    editing, and means this MTsc list is rewritten at MTsf buildBinary() time.
    
    >>> _testingValues[1].pprint()
    Class 0: 'wxyz'
    Class 1: 'abcdef'
    Class 2: 'fred'
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintfunc = (lambda p,x,label: p.simple(ascii(x)[1:], label=label)),
        item_pprintlabelfunc = (lambda i: "Class %d" % (i,)),
        item_strusesrepr = True)
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a MTsc object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == MTsc.frombytes(obj.binaryString())
        True
        """
        
        version = w.unpack("H")
        
        if version != 1:
            raise ValueError("Unknown MTsc version: %d" % (version,))
        
        offsets = w.group("L", w.unpack("H"))
        return cls(w.subWalker(offset).pascalString() for offset in offsets)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTsc object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0003 0000 0010  0000 0015 0000 001C |................|
              10 | 0477 7879 7A06 6162  6364 6566 0466 7265 |.wxyz.abcdef.fre|
              20 | 64                                       |d               |
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
            w.stakeCurrentWithValue(stake)
            
            if not isinstance(obj, bytes):
                obj = bytes(obj, 'ascii')
            
            w.add("B", len(obj))
            w.addString(obj)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        MTsc(),
        MTsc([b'wxyz', b'abcdef', b'fred']))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
