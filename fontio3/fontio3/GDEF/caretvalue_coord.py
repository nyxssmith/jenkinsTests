#
# caretvalue_coord.py
#
# Copyright © 2005-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to ligature caret positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class CaretValue_Coord(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing the simplest kind of caret value: a single, signed
    value in FUnits.
    
    >>> c = _testingValues[1]
    >>> c.pprint()
    Simple caret value in FUnits: 500
    >>> c < 800
    True
    >>> c.scaled(0.5).pprint()
    Simple caret value in FUnits: 250
    
    >>> logger = utilities.makeDoctestLogger("caretvalue_coord_val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> CaretValue_Coord(40000).isValid(logger=logger, editor=e)
    caretvalue_coord_val - ERROR - The signed value 40000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Simple caret value in FUnits",
        value_scales = True,
        value_validatefunc = valassist.isFormat_h)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 01F4                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 FD76                                |...v            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("Hh", 1, self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CaretValue_Coord. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('testC')
        >>> s = _testingValues[2].binaryString()
        >>> fvb = CaretValue_Coord.fromvalidatedbytes
        >>> fvb(s[:1], logger=logger)
        testC.coordinate - DEBUG - Walker has 1 remaining bytes.
        testC.coordinate - ERROR - Insufficient bytes.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        testC.coordinate - DEBUG - Walker has 4 remaining bytes.
        testC.coordinate - ERROR - Expected format 1 for CaretValue_Coord.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('coordinate')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, n = w.unpack("Hh")
        
        if format != 1:
            logger.error((
              'V0099',
              (),
              "Expected format 1 for CaretValue_Coord."))
            
            return None
        
        return cls(n)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CaretValue_Coord object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == CaretValue_Coord.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == CaretValue_Coord.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == CaretValue_Coord.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 1, "Cannot create CaretValue_Coord with non-format-1!"
        return cls(w.unpack("h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        CaretValue_Coord(0),
        CaretValue_Coord(500),
        CaretValue_Coord(-650))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
