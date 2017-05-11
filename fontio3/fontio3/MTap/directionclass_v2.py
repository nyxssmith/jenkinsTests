#
# directionclass_v2.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to direction class values in version 2 'MTap' tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Classes
#

class DirectionClass(int, metaclass=enummeta.FontDataMetaclass):
    """
    Integer values representing glyph class enumerated values.
    
    >>> print(_testingValues[0])
    No direction (0)
    
    >>> print(_testingValues[3])
    Right to Left (3)
    
    >>> print(_testingValues[9])
    Left to Right, Upwards (9)
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_annotatevalue = True,
        enum_stringsdict = {
          0: "No direction",
          1: "Left to Right",
          2: "No direction",
          3: "Right to Left",
          4: "No direction",
          5: "Left to Right, Downwards",
          6: "Downwards",
          7: "Right to Left, Downwards",
          8: "No direction",
          9: "Left to Right, Upwards",
         10: "Upwards",
         11: "Right to Left, Upwards"})
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the DirectionClass object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 02                                       |.               |
        """
        
        w.add("B", self)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a DirectionClass object from the specified walker.
        
        >>> fb = DirectionClass.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        """
        
        return cls(w.unpack("B"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        DirectionClass(0),
        DirectionClass(1),
        DirectionClass(2),
        DirectionClass(3),
        DirectionClass(4),
        DirectionClass(5),
        DirectionClass(6),
        DirectionClass(7),
        DirectionClass(8),
        DirectionClass(9),
        DirectionClass(10),
        DirectionClass(11),
        DirectionClass())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
