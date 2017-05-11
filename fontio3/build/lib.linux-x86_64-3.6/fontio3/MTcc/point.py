#
# point.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to a single cursive connection point.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Point(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single cursive connection point.
    
    The data format is:
        connectionType (UInt16, actually Boolean)
        pointIndex (UInt16)
        xCoordinate (SInt16)
        yCoordinate (SInt16)
    
    >>> _testingValues[0].pprint()
    Connection type: False
    Point index: (no data)
    X-coordinate: 0
    Y-coordinate: 0
    
    >>> _testingValues[1].pprint()
    Connection type: True
    Point index: 69
    X-coordinate: -16
    Y-coordinate: 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        connectionType = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Connection type"),
        
        pointIndex = dict(
            attr_label = "Point index",
            attr_renumberpointsdirect = True),
        
        xCoordinate = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "X-coordinate",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'yCoordinate'),
        
        yCoordinate = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Y-coordinate",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'xCoordinate'))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Point object from the specified walker.
        
        >>> _testingValues[0] == Point.frombytes(_testingValues[0].binaryString())
        True
        >>> _testingValues[1] == Point.frombytes(_testingValues[1].binaryString())
        True
        >>> _testingValues[2] == Point.frombytes(_testingValues[2].binaryString())
        True
        >>> _testingValues[3] == Point.frombytes(_testingValues[3].binaryString())
        True
        >>> _testingValues[4] == Point.frombytes(_testingValues[4].binaryString())
        True
        """
        
        ct = bool(w.unpack("H"))
        pt = w.unpack("H")
        
        if pt == 0xFFFF:
            pt = None
        
        x, y = w.unpack("2h")
        return cls(ct, pt, x, y)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Point object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 FFFF 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0045 FFF0 0005                      |...E....        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0000 000C 001E FFE2                      |........        |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0001 0004 0000 FFA6                      |........        |
        
        >>> utilities.hexdump(_testingValues[4].binaryString())
               0 | 0000 FFFF FF9C 0064                      |.......d        |
        """
        
        w.add("2H2h",
          int(bool(self.connectionType)),  # int(bool(...)) ensures 0 or 1
          (0xFFFF if self.pointIndex is None else self.pointIndex),
          self.xCoordinate,
          self.yCoordinate)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Point(),
        Point(True, 69, -16, 5),
        Point(False, 12, 30, -30),
        Point(True, 4, 0, -90),
        Point(False, None, -100, 100))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
