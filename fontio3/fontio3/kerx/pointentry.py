#
# pointentry.py
#
# Copyright © 2011, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the control-point variant of entry record for format 4 'kerx'
subtables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class PointEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing an alignment action based on control points for a
    format 4 'kerx' table. These are simple objects with two attributes:
    
        markedPoint
        currentPoint
    
    The current point is moved into alignment with the marked point.
    
    A fontdata note: the glyphs to which these points refer are not directly
    referred to here; rather, they are the result of processing of the state
    table. So if points are to be renumbered, the client may have to do quite a
    bit of work to ascertain which glyphs are being referred to. The format 4
    analyzer code can help here.
    
    >>> _testingValues[1].pprint()
    Marked glyph's point: 2
    Current glyph's point: 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markedPoint = dict(
            attr_label = "Marked glyph's point",
            attr_renumberpointsdirect = True),
        
        currentPoint = dict(
            attr_label = "Current glyph's point",
            attr_renumberpointsdirect = True))
    
    attrSorted = ('markedPoint', 'currentPoint')
    kind = 0
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PointEntry object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0005                                |....            |
        """
        
        w.add("2H", self.markedPoint, self.currentPoint)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PointEntry object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> bs = utilities.fromhex("00 02 00 05")
        >>> fvb = PointEntry.fromvalidatedbytes
        >>> obj = fvb(bs, logger=logger)
        fvw.pointentry - DEBUG - Walker has 4 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(bs[:-1], logger=logger)
        fvw.pointentry - DEBUG - Walker has 3 remaining bytes.
        fvw.pointentry - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pointentry")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(*w.unpack("2H"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PointEntry object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == PointEntry.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("2H"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        PointEntry(),
        PointEntry(2, 5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
