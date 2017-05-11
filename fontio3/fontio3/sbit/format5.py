#
# format5.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 5 embedded bitmaps.
"""

# Other imports
from fontio3 import bitmap
from fontio3.fontdata import simplemeta
from fontio3.sbit import bigglyphmetrics

# -----------------------------------------------------------------------------

#
# Classes
#

class Format5(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing format 5 embedded bitmaps. These are simple collections of
    the following attributes:
    
        image       A Bitmap object representing the actual image.
        
        metrics     A BigGlyphMetrics object.
    
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
      Height: 7
      Width: 7
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
    
    imageFormat = 5  # class constant
    
    #
    # Methods
    #
    
    def binarySize(self):
        """
        Returns the byte size of the binary string, without having to actually
        construct it. This is useful in the analysis phase of sbit writing.
        """
        
        m = self.metrics
        return (m.height * m.width + 7) // 8
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format5 object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 8288 A482 88A0 80                        |.......         |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 7474 1474 70                             |tt.tp           |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        bd = self.image.bitDepth
        
        for row in self.image:
            w.addBitsGroup(row, bd, False)
        
        w.alignToByteMultiple(1)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format5. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format5.fromvalidatedbytes
        >>> obj = fvb(
        ...   s,
        ...   logger = logger,
        ...   bigMetrics = _testingValues[1].metrics,
        ...   bitDepth = 1)
        test.sbit.format5 - DEBUG - Walker has 7 remaining bytes.
        
        >>> obj = fvb(
        ...   s[:-1],
        ...   logger = logger,
        ...   bigMetrics = _testingValues[1].metrics,
        ...   bitDepth = 1)
        test.sbit.format5 - DEBUG - Walker has 6 remaining bytes.
        test.sbit.format5 - ERROR - Insufficient data for bitmap
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format5')
        else:
            logger = logger.getChild('format5')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        assert 'bitDepth' in kwArgs
        assert 'bigMetrics' in kwArgs
        
        m = kwArgs['bigMetrics']
        bitDepth = kwArgs['bitDepth']
        
        if w.bitLength() < (bitDepth * m.width * m.height):
            logger.error((
              'V0221',
              (),
              "Insufficient data for bitmap"))
            
            return None
        
        v = [None] * m.height
        
        for row in range(m.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, m.width))
        
        b = bitmap.Bitmap(
          v,
          lo_x = m.horiBearingX,
          hi_y = m.horiBearingY,
          bitDepth = bitDepth)
        
        return cls(metrics=m, image=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format5 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format5.frombytes(
        ...   obj.binaryString(),
        ...   bigMetrics = obj.metrics,
        ...   bitDepth = obj.image.bitDepth)
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Format5.frombytes(
        ...   obj.binaryString(),
        ...   bigMetrics = obj.metrics,
        ...   bitDepth = obj.image.bitDepth)
        True
        """
        
        assert 'bigMetrics' in kwArgs
        assert 'bitDepth' in kwArgs
        
        m = kwArgs['bigMetrics']
        bitDepth = kwArgs['bitDepth']
        v = [None] * m.height
        
        for row in range(m.height):
            v[row] = list(w.unpackBitsGroup(bitDepth, m.width))
        
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
        Format5(),
        
        Format5(
          metrics = bigglyphmetrics.BigGlyphMetrics(7, 7, 1, 0, 10, -3, -1, 9),
          
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
        
        Format5(
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
