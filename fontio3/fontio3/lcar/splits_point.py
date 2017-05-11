#
# splits_point.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the point flavor of ligature caret values.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Splits_Point(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing the split points, in point form, for a ligature. These
    are tuples of point indices.
    
    >>> sp = Splits_Point([2, 4, 18])
    >>> print(sp)
    (2, 4, 18)
    >>> md = {120: {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0}}
    >>> print(sp.pointsRenumbered(md, glyphIndex=120)) # keepMissing is True
    (3, 1, 18)
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintfunc = (
          lambda p, x, label:
          p.simple("Point %d" % (x,), label=label)),
        item_renumberpointsdirect = True,
        seq_fixedlength = True,
        seq_maxcontextfunc = (lambda t: len(t)))
    
    dataFormat = 1  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Splits_Point object to the specified
        LinkedWriter.
        
        >>> sd = Splits_Point([2, 4, 18])
        >>> utilities.hexdump(sd.binaryString())
               0 | 0003 0002 0004 0012                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        w.addGroup("H", self)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Splits_Point object from the specified
        walker. There are no keyword arguments.
        
        >>> sd = Splits_Point([2, 4, 18])
        >>> sd == Splits_Point.frombytes(sd.binaryString())
        True
        """
        
        return cls(w.group("H", w.unpack("H")))

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
