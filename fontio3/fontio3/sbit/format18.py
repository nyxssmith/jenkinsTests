#
# format18.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 18 embedded color emoji.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.sbit import bigglyphmetrics
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class Format18(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing format 1 embedded bitmaps. These are simple
    collections of the following attributes:
    
        image       A Bitmap object representing the actual image.
        
        metrics     A BigGlyphMetrics object.
    
    >>> _testingValues[1].pprint()
    Image data:
             0 |   0101 0101 0101 0101  0101 0101 0101 0101 |................|
            10 |   0101 0101 0101 01                        |.......         |
    Metrics:
      Height: 7
      Width: 8
      Horizontal left sidebearing: 1
      Horizontal origin-to-top: 0
      Horizontal advance: 10
      Vertical origin-to-left: -3
      Vertical top sidebearing: -1
      Vertical advance: 9
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
            attr_label = "Image data",
            attr_pprintfunc = (
              lambda p, obj, label, **k:
              pp.PP.hexDump(p, obj, label))))
    
    attrSorted = ('image', 'metrics')
    imageFormat = 18  # class constant
    
    #
    # Methods
    #
    
    def binarySize(self):
        """
        Returns the byte size of the binary string, without having to actually
        construct it. This is useful in the analysis phase of sbit writing.
        
        >>> _testingValues[1].binarySize()
        35
        """
        
        return len(self.image) + 12  # 4 for ULONG, 8 for metrics
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format18 object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0708 0100 0AFD FF09  0000 0017 0101 0101 |................|
              10 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              20 | 0101 01                                  |...             |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        self.metrics.buildBinary(w, **kwArgs)
        w.add("L", len(self.image))
        w.addString(self.image)

    @classmethod
    def fromscaler(cls, scaler, glyphIndex, bitDepth, **kwArgs):
        """
        Initializes a Format18 object for glyphIndex using a scaler. The scaler
        should at minimum support a 'getBitmap' function, returning an object
        with properties/methods of a ScalerInterface GlyphBitmap and should
        have already set the font, size, and any other necessary scaler
        attributes.

        The following kwArgs are supported:
        
            flags   A dict of flags and values to be passed in to
                    scaler.setFlags, e.g.: scaler.setFlags(flags.keys()[n],
                    flags[flags.keys()[n]])
        """

        raise NotImplementedError()
    
    @classmethod
    def fromscalerdata(cls, glyphbitmap, bitDepth):
        """
        Initializes a Format18 from glyphbitmap, which should be an object
        similar to ScalerInterface's 'GlyphBitmap', having 'metrics' and 'bits'
        attributes.
        """
    
        raise NotImplementedError()
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Format18. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test.sbit')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format18.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.sbit.format18 - DEBUG - Walker has 35 remaining bytes.
        test.sbit.format18.bigglyphmetrics - DEBUG - Walker has 35 remaining bytes.
        
        >>> fvb(s[:-1], logger=logger)
        test.sbit.format18 - DEBUG - Walker has 34 remaining bytes.
        test.sbit.format18.bigglyphmetrics - DEBUG - Walker has 34 remaining bytes.
        test.sbit.format18 - ERROR - Insufficient data
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format18')
        else:
            logger = logger.getChild('format18')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
        bm = fvw(w, logger=logger, **kwArgs)
        
        if bm is None:
            return None
        
        if w.length() < 4:
            logger.error(('V0219', (), "Insufficient data"))
            return None
        
        needLength = w.unpack("L")
        
        if w.length() < needLength:
            logger.error(('V0219', (), "Insufficient data"))
            return None
        
        b = w.chunk(needLength)
        return cls(metrics=bm, image=b)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format18 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format18.frombytes(
        ...   obj.binaryString())
        True
        """
        
        fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
        bm = fw(w, **kwArgs)
        b = w.chunk(w.unpack("L"))
        return cls(metrics=bm, image=b)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Format18(),
        
        Format18(
          metrics = bigglyphmetrics.BigGlyphMetrics(7, 8, 1, 0, 10, -3, -1, 9),
          image = b'\x01' * 23))  # not real PNG data

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
