#
# anchor_coord.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for anchored locations, specified solely via FUnit values.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontmath import point
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Anchor_Coord(point.Point):
    """
    Objects representing anchored locations, via FUnit values only.
    
    >>> _testingValues[0].pprint()
    x-coordinate: -40
    y-coordinate: 18
    
    >>> _testingValues[0].anchorKind
    'coord'
    
    >>> _testingValues[3].x
    -180
    
    >>> logger = utilities.makeDoctestLogger("anchor_coord_val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Anchor_Coord(4.5, -40000).isValid(logger=logger, editor=e)
    anchor_coord_val.[0] - ERROR - The value 4.5 is not an integer.
    anchor_coord_val.[1] - ERROR - The signed value -40000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintlabelfunc = (lambda n: ("x-coordinate", "y-coordinate")[n]),
        item_roundfunc = utilities.truncateRound,
        item_validatefunc = valassist.isFormat_h)
    
    anchorKind = 'coord'
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> atc = _testingValues[0]
        >>> utilities.hexdump(atc.binaryString())
               0 | 0001 FFD8 0012                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H2h", 1, *self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Coord object, including validation of the input
        source.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> e = utilities.fakeEditor(0x10000)
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Anchor_Coord.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, editor=e)
        test.anchor_coord - DEBUG - Walker has 6 remaining bytes.
        
        >>> fvb(s[:5], logger=logger, editor=e)
        test.anchor_coord - DEBUG - Walker has 5 remaining bytes.
        test.anchor_coord - ERROR - Insufficient bytes.
        
        >>> fvb(s[2:6] + s[0:2], logger=logger, editor=e)
        test.anchor_coord - DEBUG - Walker has 6 remaining bytes.
        test.anchor_coord - ERROR - Was expecting format 1, but got 65496 instead.
        """
        
        logger = kwArgs.get('logger', logging.getLogger())
        logger = logger.getChild('anchor_coord')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Was expecting format 1, but got %d instead."))
            
            return None
        
        return cls(*w.unpack("2h"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Coord object from the specified walker.
        
        >>> atc = _testingValues[0]
        >>> atc == Anchor_Coord.frombytes(atc.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError("Unknown format for Anchor_Coord: %d" % (format,))
        
        return cls(*w.unpack("2h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        Anchor_Coord(-40, 18),
        Anchor_Coord(0, 0),
        Anchor_Coord(0, 40),
        Anchor_Coord(-180, 0))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
