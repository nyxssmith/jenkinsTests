#
# splits_distance.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the distance flavor of ligature caret values.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Splits_Distance(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing the split points, in FUnit form, for a ligature. These
    are tuples of FUnit values.
    
    >>> sd = Splits_Distance([250, 700, 800])
    >>> print(sd)
    (250, 700, 800)
    >>> print(sd.scaled(1.5))
    (375, 1050, 1200)
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintfunc = (
          lambda p, x, label:
          p.simple("%d FUnits" % (x,), label=label)),
        item_scaledirect = True,  # they're FUnit values
        seq_fixedlength = True,
        seq_maxcontextfunc = (lambda t: len(t)))
    
    dataFormat = 0  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Splits_Distance object to the specified
        LinkedWriter.
        
        >>> sd = Splits_Distance([250, 700, 800])
        >>> utilities.hexdump(sd.binaryString())
               0 | 0003 00FA 02BC 0320                      |.......         |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        w.addGroup("h", self)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Splits_Distance object from the specified
        walker. There are no keyword arguments.
        
        >>> sd = Splits_Distance([250, 700, 800])
        >>> sd == Splits_Distance.frombytes(sd.binaryString())
        True
        """
        
        return cls(w.group("h", w.unpack("H")))

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
