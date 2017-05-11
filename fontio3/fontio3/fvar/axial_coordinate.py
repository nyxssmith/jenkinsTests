#
# axial_coordinate.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single floating-point values used as entries in AxisInfo and
InstanceInfo objects. These are essentially values along one axis.
"""

# Other imports
from fontio3.fontdata import valuemeta
from fontio3.fontmath import mathutilities

# -----------------------------------------------------------------------------

#
# Classes
#

class AxialCoordinate(float, metaclass=valuemeta.FontDataMetaclass):
    """
    Single floating-point values, used in AxisInfo and InstanceInfo objects.
    Note that they have a custom __str__() method to display to three places
    only, although the actual data value is always preserved.
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

    # noinspection PyUnusedLocal
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for self to the specified writer.

        >>> h = utilities.hexdump
        >>> v = [-2.0, -1.5, -1.0, -0.5, 0, 0.5, 1.0, 1.5]
        >>> for n in v:
        ...   h(AxialCoordinate(n).binaryString())
               0 | FFFE 0000                                |....            |
               0 | FFFE 8000                                |....            |
               0 | FFFF 0000                                |....            |
               0 | FFFF 8000                                |....            |
               0 | 0000 0000                                |....            |
               0 | 0000 8000                                |....            |
               0 | 0001 0000                                |....            |
               0 | 0001 8000                                |....            |
        """

        w.add('L', mathutilities.floatToFixed(self, forceUnsigned=True))

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinate object from the data in the
        specified walker, doing source validation.

        >>> bs = utilities.fromhex("00 01 00 00")
        >>> obj = AxialCoordinate.fromvalidatedbytes(bs)
        AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> print(obj)
        1.0
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000                                |....            |

        >>> bs = utilities.fromhex("FF FF 80 00")
        >>> obj = AxialCoordinate.fromvalidatedbytes(bs)
        AxialCoordinate - DEBUG - Walker has 4 remaining bytes.
        >>> print(obj)
        -0.5
        >>> utilities.hexdump(obj.binaryString())
               0 | FFFF 8000                                |....            |
        
        >>> bs = utilities.fromhex("00 00 01")
        >>> AxialCoordinate.fromvalidatedbytes(bs)
        AxialCoordinate - DEBUG - Walker has 3 remaining bytes.
        AxialCoordinate - ERROR - Insufficient bytes (3) for AxialCoordinate (minimum 4)
        """

        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('AxialCoordinate')
        else:
            logger = utilities.makeDoctestLogger('AxialCoordinate')

        remaining_length = w.length()
        
        logger.debug((
          'V0001',
          (remaining_length,),
          "Walker has %d remaining bytes."))

        bytes_needed = 4
        
        if remaining_length < bytes_needed:
            logger.error((
              'V0004',
              (remaining_length, bytes_needed),
              "Insufficient bytes (%d) for AxialCoordinate (minimum %d)"))
            
            return None

        return cls(mathutilities.fixedToFloat(w.unpack("L")))

    # noinspection PyUnusedLocal
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AxialCoordinate object from the data in the
        specified walker.

        >>> bs = utilities.fromhex("00 01 00 00")
        >>> obj = AxialCoordinate.frombytes(bs)
        >>> print(obj)
        1.0
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000                                |....            |

        >>> bs = utilities.fromhex("FF FF 80 00")
        >>> obj = AxialCoordinate.frombytes(bs)
        >>> print(obj)
        -0.5
        >>> utilities.hexdump(obj.binaryString())
               0 | FFFF 8000                                |....            |
        """

        return cls(mathutilities.fixedToFloat(w.unpack("L")))

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

