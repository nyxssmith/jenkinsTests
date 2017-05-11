#
# anchorentry.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the anchor-point variant of entry record for format 4 'kerx'
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

class AnchorEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing an alignment action based on anchor points for a
    format 4 'kerx' table. These are simple objects with two attributes:
    
        markedAnchor
        currentAnchor
    
    The current anchor is moved into alignment with the marked anchor. Note the
    point values referred to here are list indices into the per-glyph lists of
    anchor point positions maintained by the 'ankr' table.
    
    A fontdata note: the glyphs to which these anchors refer are not directly
    referred to here; rather, they are the result of processing of the state
    table. So if anchors are to be renumbered, the client may have to do quite a
    bit of work to ascertain which glyphs are being referred to. The format 4
    analyzer code can help here.
    
    >>> _testingValues[1].pprint()
    Marked glyph's anchor: 4
    Current glyph's anchor: 3
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markedAnchor = dict(
            attr_label = "Marked glyph's anchor"),
        
        currentAnchor = dict(
            attr_label = "Current glyph's anchor"))
    
    attrSorted = ('markedAnchor', 'currentAnchor')
    kind = 1
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the AnchorEntry object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0004 0003                                |....            |
        """
        
        w.add("2H", self.markedAnchor, self.currentAnchor)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new AnchorEntry object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> bs = utilities.fromhex("00 04 00 03")
        >>> fvb = AnchorEntry.fromvalidatedbytes
        >>> obj = fvb(bs, logger=logger)
        fvw.anchorentry - DEBUG - Walker has 4 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(bs[:-1], logger=logger)
        fvw.anchorentry - DEBUG - Walker has 3 remaining bytes.
        fvw.anchorentry - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("anchorentry")
        
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
        Creates and returns a new AnchorEntry objectfrom the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == AnchorEntry.frombytes(obj.binaryString())
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
        AnchorEntry(),
        AnchorEntry(4, 3))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
