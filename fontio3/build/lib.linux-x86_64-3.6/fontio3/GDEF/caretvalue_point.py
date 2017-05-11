#
# caretvalue_point.py
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

class CaretValue_Point(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing a caret value as a point index in a glyph.
    
    >>> c = _testingValues[1]
    >>> c.pprint()
    Caret value point index: 12
    >>> c > 3
    True
    >>> c.pointsRenumbered({900: {12: 20}}, glyphIndex=900).pprint()
    Caret value point index: 20
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_ispointindex = True,
        value_pprintlabel = "Caret value point index",
        value_validatefunc = valassist.isFormat_H)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 000C                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("Hh", 2, self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CaretValue_Point. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('testP')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = CaretValue_Point.fromvalidatedbytes
        >>> fvb(s[:1], logger=logger)
        testP.point - DEBUG - Walker has 1 remaining bytes.
        testP.point - ERROR - Insufficient bytes.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        testP.point - DEBUG - Walker has 4 remaining bytes.
        testP.point - ERROR - Expected format 2 for CaretValue_Point.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('point')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, n = w.unpack("2H")
        
        if format != 2:
            logger.error((
              'V0099',
              (),
              "Expected format 2 for CaretValue_Point."))
            
            return None
        
        return cls(n)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CaretValue_Point object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == CaretValue_Point.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == CaretValue_Point.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 2, "Cannot create CaretValue_Point with non-format-2!"
        return cls(w.unpack("H"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    _testingValues = (
        CaretValue_Point(0),
        CaretValue_Point(12))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
