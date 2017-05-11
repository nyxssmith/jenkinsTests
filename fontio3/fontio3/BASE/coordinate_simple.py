#
# coordinate_simple.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Items relating to simple coordinate values for OpenType BASE tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    try:
        n = int(round(obj))
    except:
        n = None
    
    # Note that if the value n is None (i.e. conversion or rounding failed)
    # the error is not raised here. Since this function is a partial, the
    # valuemeta isValid() checks will still be done, and the error will be
    # raised there instead.
    
    if n is not None and e is not None and e.reallyHas(b'head'):
        upem = e.head.unitsPerEm
        
        if abs(n) >= 2 * upem:
            logger.warning((
              'V0637',
              (n,),
              "The FUnit value %d is more than two ems away "
              "from the origin, which seems unlikely."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Coordinate_simple(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing the simplest coordinate value, a single integer in
    FUnits. This will be interpreted as X or Y depending on whether the object
    containing it is part of the horizontal or vertical baseline data.
    
    >>> _testingValues[2].pprint()
    Coordinate: 85
    
    >>> print(_testingValues[3])
    -20
    
    >>> logger = utilities.makeDoctestLogger("coordinate_simple_test")
    >>> e = _fakeEditor()
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    coordinate_simple_test - WARNING - The FUnit value -20000 is more than two ems away from the origin, which seems unlikely.
    True
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Coordinate",
        value_scales = True,
        value_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Coordinate_simple object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 0055                                |...U            |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0001 FFEC                                |....            |
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
        Creates and returns a new Coordinate_simple object from the specified
        walker, doing source validation.
        
        >>> s = _testingValues[2].binaryString()
        >>> logger = utilities.makeDoctestLogger("coordinate_simple_fvw")
        >>> fvb = Coordinate_simple.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        coordinate_simple_fvw.coordinate_simple - DEBUG - Walker has 4 remaining bytes.
        >>> obj == 85
        True
        
        >>> fvb(s[:2], logger=logger)
        coordinate_simple_fvw.coordinate_simple - DEBUG - Walker has 2 remaining bytes.
        coordinate_simple_fvw.coordinate_simple - ERROR - Insufficient bytes.
        
        >>> fvb(s[2:4] + s[2:4], logger=logger)
        coordinate_simple_fvw.coordinate_simple - DEBUG - Walker has 4 remaining bytes.
        coordinate_simple_fvw.coordinate_simple - ERROR - Expected format 1 but got 85 instead.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("coordinate_simple")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0001', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1 but got %d instead."))
            
            return None
        
        return cls(w.unpack("h"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Coordinate_simple object from the specified
        walker.
        
        >>> for i in range(4):
        ...     obj = _testingValues[i]
        ...     print(obj == Coordinate_simple.frombytes(obj.binaryString()))
        True
        True
        True
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError(
              "Unknown format for Coordinate_simple: %d" % (format,))
        
        return cls(w.unpack("h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _fakeEditor():
        from fontio3.head import head
        
        e = utilities.fakeEditor(0x10000)
        e.head = head.Head()
        return e
    
    _testingValues = (
        Coordinate_simple(),
        Coordinate_simple(0),
        Coordinate_simple(85),
        Coordinate_simple(-20),
        # bad values start here
        Coordinate_simple(-20000))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
