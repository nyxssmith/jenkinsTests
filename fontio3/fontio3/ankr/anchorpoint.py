#
# anchorpoint.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to a single anchor point for a single glyph.
"""

# System imports
import logging

# Other imports
from fontio3.fontmath import point
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class AnchorPoint(point.Point):
    """
    Objects representing single anchor points within a glyph. These are just
    fontio3.fontmath.point.Point objects with validation, from...(), and
    buildBinary() methods added.
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(1000)
    >>> AnchorPoint(100, -100).isValid(logger=logger, editor=e)
    True
    >>> AnchorPoint(100000, -100).isValid(logger=logger, editor=e)
    val.[0] - ERROR - The signed value 100000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_validatefunc = valassist.isFormat_h,
        seq_pprintfunc = (lambda p, obj, **k: p.simple("(%d, %d)" % obj)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AnchorPoint to the specified writer.
        
        >>> obj = AnchorPoint(100, -100)
        >>> utilities.hexdump(obj.binaryString())
               0 | 0064 FF9C                                |.d..            |
        """
        
        w.add("2h", self.x, self.y)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AnchorPoint object from the specified walker,
        doing source validation.
        
        >>> bs = utilities.fromhex("00 64 FF 9C")
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> print(AnchorPoint.fromvalidatedbytes(bs, logger=logger))
        fvw.anchorpoint - DEBUG - Walker has 4 remaining bytes.
        (100, -100)
        
        >>> AnchorPoint.fromvalidatedbytes(bs[:-1], logger=logger)
        fvw.anchorpoint - DEBUG - Walker has 3 remaining bytes.
        fvw.anchorpoint - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("anchorpoint")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        return cls(*w.group("h", 2))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AnchorPoint object from the specified walker.
        
        >>> bs = utilities.fromhex("00 64 FF 9C")
        >>> print(AnchorPoint.frombytes(bs))
        (100, -100)
        """
        
        return cls(*w.group("h", 2))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        AnchorPoint(0, 0),
        AnchorPoint(100, 0),
        AnchorPoint(-200, 0),
        AnchorPoint(0, 150),
        AnchorPoint(0, -250),
        AnchorPoint(100, 150),
        AnchorPoint(100, -250),
        AnchorPoint(-200, 150),
        AnchorPoint(-200, -250))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
