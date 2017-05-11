#
# glyphrecord.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single glyph in a Strike.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Constants
#

VALID_IMAGE_TYPES = frozenset({
  'jpg ',
  'pdf ',
  'png ',
  'tiff'})

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single glyph in a Strike. These are simple
    collections of attributes:
    
        data                A binary string with the raw data. We currently
                            make no attempt to interpret this; it's just a
                            chunk of bytes.
        
        graphicType         A 4-byte string identifying the kind of graphic.
                            While this is limited (currently to 'jpg ', 'pdf ',
                            'png ', and 'tiff'), it may expand in the future,
                            so rather than making it an enumeration, it's just
                            a string.
        
        originOffsetX       The x-value of the origin.
        
        originOffsetY       The y-value of the origin.
    """
    
    attrSpec = dict(
        data = dict(),
        
        graphicType = dict(),
        
        originOffsetX = dict(
            attr_representsx = True,
            attr_transformcounterpart = 'originOffsetY'),
        
        originOffsetY = dict(
            attr_representsy = True,
            attr_transformcounterpart = 'originOffsetX'))
    
    attrSorted = ('originOffsetX', 'originOffsetY', 'graphicType', 'data')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the GlyphRecord to the specified writer.
        
        >>> obj = GlyphRecord(15, -35, 'tiff', b"Some data here")
        >>> utilities.hexdump(obj.binaryString())
               0 | 000F FFDD 7469 6666  536F 6D65 2064 6174 |....tiffSome dat|
              10 | 6120 6865 7265                           |a here          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add(
          '2h4s',
          self.originOffsetX,
          self.originOffsetY,
          self.graphicType.encode('ascii'))
        
        w.addString(self.data)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphRecord object from the specified walker,
        doing validation.
        
        >>> logger = utilities.makeDoctestLogger("glyphrecord")
        >>> fvb = GlyphRecord.fromvalidatedbytes
        >>> bs1 = utilities.fromhex("00 0F FF DD 74 69 66 66 41 42 43")
        >>> obj = fvb(bs1, logger=logger)
        glyphrecord.glyphrecord - DEBUG - Walker has 11 remaining bytes.
        
        >>> fvb(bs1[:3], logger=logger)
        glyphrecord.glyphrecord - DEBUG - Walker has 3 remaining bytes.
        glyphrecord.glyphrecord - ERROR - Insufficient bytes.
        
        >>> obj = fvb(bs1[:8], logger=logger)
        glyphrecord.glyphrecord - DEBUG - Walker has 8 remaining bytes.
        glyphrecord.glyphrecord - WARNING - Image data is zero-length
        
        >>> bs2 = utilities.fromhex("00 0F FF DD 78 69 66 66 41 42 43")
        >>> fvb(bs2, logger=logger)
        glyphrecord.glyphrecord - DEBUG - Walker has 11 remaining bytes.
        glyphrecord.glyphrecord - ERROR - Image type 'xiff' is not valid for an 'sbix' table.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('glyphrecord')
        else:
            logger = logger.getChild('glyphrecord')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        ooX, ooY, gType = w.unpack("2h4s")
        gType = str(gType, 'ascii')
        
        if gType not in VALID_IMAGE_TYPES:
            logger.error((
              'V1015',
              (gType,),
              "Image type '%s' is not valid for an 'sbix' table."))
            
            return None
        
        if not w.length():
            logger.warning((
              'V1016',
              (),
              "Image data is zero-length"))
        
        data = w.rest()
        return cls(ooX, ooY, gType, data)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphRecord object from the specified walker.
        
        >>> bs1 = utilities.fromhex("00 0F FF DD 74 69 66 66 41 42 43")
        >>> GlyphRecord.frombytes(bs1).pprint()
        originOffsetX: 15
        originOffsetY: -35
        graphicType: tiff
        data: b'ABC'
        
        >>> bs2 = utilities.fromhex("00 00 00 10 70 6E 67 20 44 45 46 47")
        >>> GlyphRecord.frombytes(bs2).pprint()
        originOffsetX: 0
        originOffsetY: 16
        graphicType: png 
        data: b'DEFG'
        """
        
        ooX, ooY, gType = w.unpack("2h4s")
        gType = str(gType, 'ascii')
        data = w.rest()
        return cls(ooX, ooY, gType, data)

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

