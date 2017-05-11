#
# anchor.py
#
# Copyright © 2008-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Anchor objects (part of the 'MTad' table).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Anchor(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single anchor within a single point.
    
    The data format is:
        anchorType (SInt16)
        pointIndex (UInt16)
        xCoordinate (SInt16)
        yCoordinate (SInt16)
    
    >>> _testingValues[1].pprint()
    Anchor type: 1
    Point index: 69
    X-coordinate: -16
    Y-coordinate: 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        anchorType = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Anchor type"),
        
        pointIndex = dict(
            attr_initfunc = (lambda: 0),
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
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Anchor object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0045 FFF0 0005                      |...E....        |
        """
        
        w.add("hH2h",
          self.anchorType,
          self.pointIndex,
          self.xCoordinate,
          self.yCoordinate)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns an Anchor object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("anchor")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*w.unpack("hH2h"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an Anchor object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Anchor.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("hH2h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Anchor(),
        Anchor(1, 69, -16, 5),
        Anchor(1, 2, 12, -30),
        Anchor(3, 35, 250, 50),
        Anchor(1, 14, 19, 18),
        Anchor(4, 68, -55, -44),
        Anchor(6, 0, 12, 9),
        Anchor(2, 19, 0, -97),
        Anchor(11, 39, -28, 36),
        Anchor(1, 60, 170, 266),
        Anchor(2, 24, 900, -450))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
