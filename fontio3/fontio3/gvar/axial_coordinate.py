#
# axial_coordinate.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single floating-point values, in the -2..2 range, used as entries
in an AxialCoordinates object. These are essentially values along one axis.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import valuemeta
    
# -----------------------------------------------------------------------------

#
# Classes
#

class AxialCoordinate(float, metaclass=valuemeta.FontDataMetaclass):
    """
    Single floating-point values, used in AxialCoordinates objects. Note that
    they have a custom __str__() method to display to three places only,
    althoug the actual data value is always preserved.
    """
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representing the value. This string will be rounded to
        three places, but its internal value remains unchanged.
        
        >>> print((AxialCoordinate(1/3)))
        0.333
        """
        
        return str(round(self, 3))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for self to the specified writer.
        
        >>> h = utilities.hexdump
        >>> v = [-2.0, -1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5]
        >>> for n in v:
        ...   h(AxialCoordinate(n).binaryString())
               0 | 8000                                     |..              |
               0 | A000                                     |..              |
               0 | C000                                     |..              |
               0 | E000                                     |..              |
               0 | 0000                                     |..              |
               0 | 2000                                     | .              |
               0 | 4000                                     |@.              |
               0 | 6000                                     |`.              |
        
        Note that a value outside the valid range will raise a ValueError:
        
        >>> h(AxialCoordinate(2.0).binaryString())
        Traceback (most recent call last):
          ...
        ValueError: Cannot represent the AxialCoordinate as a shortFrac!
        """
        
        if not -2.0 <= self < 2.0:
            raise ValueError(
              "Cannot represent the AxialCoordinate as a shortFrac!")
        
        w.add("h", int(round(self * 16384)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinate object from the data in the
        specified walker, doing validation. If a logger is not provided, one
        will be made.
        
        >>> bs = utilities.fromhex("40 00")
        >>> obj = AxialCoordinate.fromvalidatedbytes(bs)
        coord - DEBUG - Walker has 2 remaining bytes.
        coord - DEBUG - Coordinate value is 16384
        
        >>> obj == 1.0
        True
        
        >>> AxialCoordinate.fromvalidatedbytes(bs[:1])
        coord - DEBUG - Walker has 1 remaining bytes.
        coord - ERROR - Insufficient bytes.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('coord')
        else:
            logger = utilities.makeDoctestLogger('coord')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        raw = w.unpack("h")
        
        logger.debug((
          'Vxxxx',
          (raw,),
          "Coordinate value is %d"))
        
        return cls(raw / 16384)  # we've imported division from __future__
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinate object from the data in the
        specified walker.
        
        >>> bs = utilities.fromhex("40 00")
        >>> obj = AxialCoordinate.frombytes(bs)
        >>> print(obj)
        1.0
        >>> utilities.hexdump(obj.binaryString())
               0 | 4000                                     |@.              |
        
        >>> bs = utilities.fromhex("E0 00")
        >>> obj = AxialCoordinate.frombytes(bs)
        >>> print(obj)
        -0.5
        >>> utilities.hexdump(obj.binaryString())
               0 | E000                                     |..              |
        """
        
        return cls(w.unpack("h") / 16384)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

