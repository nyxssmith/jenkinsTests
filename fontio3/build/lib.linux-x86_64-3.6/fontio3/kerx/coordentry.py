#
# coordentry.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the coordinate variant of entry record for format 4 'kerx'
subtables.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class CoordEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing an alignment action based on coordinates for a
    format 4 'kerx' table. These are simple objects with four attributes:
    
        markedX
        markedY
        currentX
        currentY
    
    The current point is moved into alignment with the marked point.
    
    >>> _testingValues[1].pprint()
    Marked glyph's X-coordinate: 200
    Marked glyph's Y-coordinate: -130
    Current glyph's X-coordinate: 50
    Current glyph's Y-coordinate: 190
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markedX = dict(
            attr_label = "Marked glyph's X-coordinate",
            attr_renumberdirect = True,
            attr_representsx = True,
            attr_transformcounterpart = 'markedY',
            attr_validatefunc = functools.partial(
              valassist.isFormat_h,
              label = "marked x-coordinate")),
        
        markedY = dict(
            attr_label = "Marked glyph's Y-coordinate",
            attr_renumberdirect = True,
            attr_representsy = True,
            attr_transformcounterpart = 'markedX',
            attr_validatefunc = functools.partial(
              valassist.isFormat_h,
              label = "marked y-coordinate")),
        
        currentX = dict(
            attr_label = "Current glyph's X-coordinate",
            attr_renumberdirect = True,
            attr_representsx = True,
            attr_transformcounterpart = 'currentY',
            attr_validatefunc = functools.partial(
              valassist.isFormat_h,
              label = "current x-coordinate")),
        
        currentY = dict(
            attr_label = "Current glyph's Y-coordinate",
            attr_renumberdirect = True,
            attr_representsy = True,
            attr_transformcounterpart = 'currentX',
            attr_validatefunc = functools.partial(
              valassist.isFormat_h,
              label = "current y-coordinate")))
    
    attrSorted = ('markedX', 'markedY', 'currentX', 'currentY')
    kind = 2
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CoordEntry object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 00C8 FF7E 0032 00BE                      |...~.2..        |
        """
        
        w.add("4h", self.markedX, self.markedY, self.currentX, self.currentY)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CoordEntry object from the specified walker,
        doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("coordentry")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*w.unpack("4h"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CoordEntry object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == CoordEntry.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("4h"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        CoordEntry(),
        CoordEntry(200, -130, 50, 190))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
