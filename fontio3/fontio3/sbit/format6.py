#
# format6.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 6 embedded bitmaps.
"""

# Other imports
from fontio3 import bitmap, utilities
from fontio3.fontdata import simplemeta
from fontio3.sbit import bigglyphmetrics
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Classes
#

class Format6(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing format 6 embedded bitmaps. These are simple
    collections of the following attributes:
    
        image       A Bitmap object representing the actual image.
        
        metrics     A BigGlyphMetrics object.
    
    >>> _testingValues[1].pprint()
    Image:
         ++++++++
         12345678
      -1 X......X
      -2 .X....X.
      -3 ..X..X..
      -4 ...XX...
      -5 ...XX...
      -6 ..X..X..
      -7 .X....X.
      Bit depth: 1
      Y-coordinate of topmost gridline: 0
      X-coordinate of leftmost gridline: 1
    Metrics:
      Height: 7
      Width: 8
      Horizontal left sidebearing: 1
      Horizontal origin-to-top: 0
      Horizontal advance: 10
      Vertical origin-to-left: -3
      Vertical top sidebearing: -1
      Vertical advance: 9
    
    >>> _testingValues[2].pprint()
    Image:
         +++
         123
      +2 747
      +1 414
      +0 747
      Bit depth: 4
      Y-coordinate of topmost gridline: 3
      X-coordinate of leftmost gridline: 1
    Metrics:
      Height: 3
      Width: 3
      Horizontal left sidebearing: 1
      Horizontal origin-to-top: 3
      Horizontal advance: 5
      Vertical origin-to-left: -1
      Vertical top sidebearing: -1
      Vertical advance: 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        metrics = dict(
            attr_followsprotocol = True,
            attr_initfunc = bigglyphmetrics.BigGlyphMetrics,
            attr_label = "Metrics"),
        
        image = dict(
            attr_followsprotocol = True,
            attr_label = "Image"))
    
    attrSorted = ('image', 'metrics')
    
    imageFormat = 6  # class constant
    
    #
    # Methods
    #
    
    def binarySize(self):
        """
        Returns the byte size of the binary string, without having to actually
        construct it. This is useful in the analysis phase of sbit writing.
        """
        
        m = self.metrics
        return m.height * ((m.width + 7) // 8) + 8
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format6 object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0708 0100 0AFD FF09  8142 2418 1824 42   |.........B$..$B |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0303 0103 05FF FF05  7470 4140 7470      |........tpA@tp  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        m = self.metrics
        m.buildBinary(w, **kwArgs)
        bd = self.image.bitDepth
        
        for row in self.image:
            w.addBitsGroup(row, bd, False)
            w.alignToByteMultiple(1)

    @classmethod
    def fromscaler(cls, scaler, glyphIndex, bitDepth, **kwArgs):
        """
        Initializes a Format6 object for glyphIndex using a scaler. The scaler
        should at minimum support a 'getBitmap' function, returning an object
        with properties/methods of a ScalerInterface GlyphBitmap and should
        have already set the font, size, and any other necessary scaler
        attributes.

        The following kwArgs are supported:
        
            flags   A dict of flags and values to be passed into
                    scaler.setFlags, e.g.: scaler.setFlags(flags.keys()[n],
                    flags[flags.keys()[n]])
        """

        return cls.fromscalerdata(scaler.getBitmap(glyphIndex), bitDepth)
    
    @classmethod
    def fromscalerdata(cls, glyphbitmap, bitDepth):
        """
        Initializes a Format6 from glyphbitmap, which should be an object
        similar to ScalerInterface's 'GlyphBitmap', having 'metrics' and 'bits'
        attributes.
        """
    
        mtx = glyphbitmap.metrics
        
        m = bigglyphmetrics.BigGlyphMetrics(
          height = mtx.height,
          width = mtx.width,
          horiBearingX = mtx.lo_x,
          horiBearingY = mtx.hi_y + 1, # convert from pixel to edge
          horiAdvance = mtx.i_dx)

        w = walker.StringWalker(glyphbitmap.bits)

        v = [
          utilities.explodeRow(w.chunk(mtx.bpl), bitDepth, m.width)
          for _ in range(m.height)]

        b = bitmap.Bitmap(
          v,
          lo_x = m.horiBearingX,
          hi_y = m.horiBearingY,
          bitDepth = bitDepth)

        r = cls(image=b, metrics=m)

        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format6. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format6.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, bitDepth=1)
        test.sbit.format6 - DEBUG - Walker has 15 remaining bytes.
        test.sbit.format6.bigglyphmetrics - DEBUG - Walker has 15 remaining bytes.
        
        >>> obj = fvb(s[:-1], logger=logger, bitDepth=1)
        test.sbit.format6 - DEBUG - Walker has 14 remaining bytes.
        test.sbit.format6.bigglyphmetrics - DEBUG - Walker has 14 remaining bytes.
        test.sbit.format6 - ERROR - Insufficient data for bitmap
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format6')
        else:
            logger = logger.getChild('format6')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        assert 'bitDepth' in kwArgs
        
        m = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker(
          w,
          logger=logger,
          **kwArgs)
        
        if m is None:
            return None
        
        bitDepth = kwArgs['bitDepth']
        bpr = (bitDepth * m.width + 7) // 8
        
        if w.length() < (bpr * m.height):
            logger.error((
              'V0222',
              (),
              "Insufficient data for bitmap"))
            
            return None
        
        v = [None] * m.height
        
        for row in range(m.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, m.width))
            w.align(1)
        
        b = bitmap.Bitmap(
          v,
          lo_x = m.horiBearingX,
          hi_y = m.horiBearingY,
          bitDepth = bitDepth)
        
        return cls(metrics=m, image=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format6 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format6.frombytes(
        ...   obj.binaryString(),
        ...   bitDepth = obj.image.bitDepth)
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Format6.frombytes(
        ...   obj.binaryString(),
        ...   bitDepth = obj.image.bitDepth)
        True
        """
        
        assert 'bitDepth' in kwArgs
        
        m = bigglyphmetrics.BigGlyphMetrics.fromwalker(w, **kwArgs)
        bitDepth = kwArgs['bitDepth']
        v = [None] * m.height
        
        for row in range(m.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, m.width))
            w.align(1)
        
        b = bitmap.Bitmap(
          v,
          lo_x = m.horiBearingX,
          hi_y = m.horiBearingY,
          bitDepth = bitDepth)
        
        return cls(metrics=m, image=b)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Format6(),
        
        Format6(
          metrics = bigglyphmetrics.BigGlyphMetrics(7, 8, 1, 0, 10, -3, -1, 9),
          
          image = bitmap.Bitmap(
            [
              [1, 0, 0, 0, 0, 0, 0, 1],
              [0, 1, 0, 0, 0, 0, 1, 0],
              [0, 0, 1, 0, 0, 1, 0, 0],
              [0, 0, 0, 1, 1, 0, 0, 0],
              [0, 0, 0, 1, 1, 0, 0, 0],
              [0, 0, 1, 0, 0, 1, 0, 0],
              [0, 1, 0, 0, 0, 0, 1, 0]],
            
            lo_x = 1,
            hi_y = 0,
            bitDepth = 1)),
        
        Format6(
          metrics = bigglyphmetrics.BigGlyphMetrics(3, 3, 1, 3, 5, -1, -1, 5),
          
          image = bitmap.Bitmap(
            [
              [7, 4, 7],
              [4, 1, 4],
              [7, 4, 7]],
            
            lo_x = 1,
            hi_y = 3,
            bitDepth = 4)))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
