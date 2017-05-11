#
# format2.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 embedded bitmaps.
"""

# Other imports
from fontio3 import bitmap
from fontio3.fontdata import simplemeta
from fontio3.sbit import smallglyphmetrics

# -----------------------------------------------------------------------------

#
# Classes
#

class Format2(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing format 2 embedded bitmaps. These are simple
    collections of the following attributes:
    
        image       A Bitmap object representing the actual image.
        
        metrics     A SmallGlyphMetrics object.
    
    >>> _testingValues[1].pprint()
    Image:
         +++++++
         1234567
      -1 X.....X
      -2 .X...X.
      -3 ..X.X..
      -4 X..X...
      -5 ..X.X..
      -6 .X...X.
      -7 X.....X
      Bit depth: 1
      Y-coordinate of topmost gridline: 0
      X-coordinate of leftmost gridline: 1
    Metrics:
      Horizontal: True
      Height: 7
      Width: 7
      Origin-to-left: 1
      Origin-to-top: 0
      Advance: 10
    
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
      Horizontal: True
      Height: 3
      Width: 3
      Origin-to-left: 1
      Origin-to-top: 3
      Advance: 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        metrics = dict(
            attr_followsprotocol = True,
            attr_initfunc = smallglyphmetrics.SmallGlyphMetrics,
            attr_label = "Metrics"),
        
        image = dict(
            attr_followsprotocol = True,
            attr_label = "Image"))
    
    attrSorted = ('image', 'metrics')
    
    imageFormat = 2  # class constant
    
    #
    # Methods
    #
    
    def binarySize(self):
        """
        Returns the byte size of the binary string, without having to actually
        construct it. This is useful in the analysis phase of sbit writing.
        """
        
        m = self.metrics
        return ((m.height * m.width + 7) // 8) + 5
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format2 object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0707 0100 0A82 88A4  8288 A080           |............    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0303 0103 0574 7414  7470                |.....tt.tp      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        self.metrics.buildBinary(w, **kwArgs)
        bd = self.image.bitDepth
        
        for row in self.image:
            w.addBitsGroup(row, bd, False)
        
        w.alignToByteMultiple(1)
    
    @classmethod
    def fromformat8(cls, fmt8Obj, strike):
        """
        Creates and returns a new Format2 object by converting the composite
        representation into simple form.
        """
        
        return cls(
          metrics = fmt8Obj.metrics,
          image = fmt8Obj.getBitmap(strike))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format2. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format2.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, isHorizontal=True, bitDepth=1)
        test.sbit.format2 - DEBUG - Walker has 12 remaining bytes.
        test.sbit.format2.smallglyphmetrics - DEBUG - Walker has 12 remaining bytes.
        
        >>> obj = fvb(s[:-1], logger=logger, isHorizontal=True, bitDepth=1)
        test.sbit.format2 - DEBUG - Walker has 11 remaining bytes.
        test.sbit.format2.smallglyphmetrics - DEBUG - Walker has 11 remaining bytes.
        test.sbit.format2 - ERROR - Insufficient data for bitmap
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format2')
        else:
            logger = logger.getChild('format2')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        assert 'isHorizontal' in kwArgs
        assert 'bitDepth' in kwArgs
        
        sm = smallglyphmetrics.SmallGlyphMetrics.fromvalidatedwalker(
          w,
          logger=logger,
          **kwArgs)
        
        if sm is None:
            return None
        
        bitDepth = kwArgs['bitDepth']
        
        if w.bitLength() < (bitDepth * sm.width * sm.height):
            logger.error((
              'V0220',
              (),
              "Insufficient data for bitmap"))
            
            return None
        
        v = [None] * sm.height
        
        for row in range(sm.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, sm.width))
        
        b = bitmap.Bitmap(
          v,
          lo_x = sm.bearingX,
          hi_y = sm.bearingY,
          bitDepth = bitDepth)
        
        return cls(metrics=sm, image=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format2 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format2.frombytes(
        ...   obj.binaryString(),
        ...   isHorizontal = obj.metrics.isHorizontal,
        ...   bitDepth = obj.image.bitDepth)
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Format2.frombytes(
        ...   obj.binaryString(),
        ...   isHorizontal = obj.metrics.isHorizontal,
        ...   bitDepth = obj.image.bitDepth)
        True
        """
        
        assert 'isHorizontal' in kwArgs
        assert 'bitDepth' in kwArgs
        
        sm = smallglyphmetrics.SmallGlyphMetrics.fromwalker(w, **kwArgs)
        bitDepth = kwArgs['bitDepth']
        v = [None] * sm.height
        
        for row in range(sm.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, sm.width))
        
        b = bitmap.Bitmap(
          v,
          lo_x = sm.bearingX,
          hi_y = sm.bearingY,
          bitDepth = bitDepth)
        
        return cls(metrics=sm, image=b)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Format2(),
        
        Format2(
          metrics = smallglyphmetrics.SmallGlyphMetrics(True, 7, 7, 1, 0, 10),
          
          image = bitmap.Bitmap(
            [
              [1, 0, 0, 0, 0, 0, 1],
              [0, 1, 0, 0, 0, 1, 0],
              [0, 0, 1, 0, 1, 0, 0],
              [1, 0, 0, 1, 0, 0, 0],
              [0, 0, 1, 0, 1, 0, 0],
              [0, 1, 0, 0, 0, 1, 0],
              [1, 0, 0, 0, 0, 0, 1]],
            
            lo_x = 1,
            hi_y = 0,
            bitDepth = 1)),
        
        Format2(
          metrics = smallglyphmetrics.SmallGlyphMetrics(True, 3, 3, 1, 3, 5),
          
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
