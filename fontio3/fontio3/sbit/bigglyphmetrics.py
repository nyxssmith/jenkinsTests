#
# bigglyphmetrics.py
#
# Copyright © 2006-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for big metrics (which include both horizontal and vertical values).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _fPos(code, s):
    def fPos_closure(n, **k):
        logger = k['logger']
        
        if not (0 <= n < 256):
            logger.error((code, (n,), s))
            return False
        
        return True
    
    return fPos_closure

def _fSigned(code, s):
    def fSigned_closure(n, **k):
        logger = k['logger']
        
        if not (-128 <= n < 128):
            logger.error((code, (n,), s))
            return False
        
        return True
    
    return fSigned_closure

def _fZero():
    return 0

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BigGlyphMetrics(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing collections of horizontal and vertical metrics for a
    bitmap. These are simple collections of the following attributes:
        
        height          Unsigned height of the bitmap (i.e. the number of rows
                        it occupies).
        
        horiAdvance     Unsigned advance width of the horizontal bitmap.
        
        horiBearingX    Signed distance from the horizontal origin to the left
                        edge of the bitmap.
        
        horiBearingY    Signed distance from the horizontal origin to the top
                        edge of the bitmap.
        
        vertAdvance     Unsigned advance width (that is, advance height) of
                        the vertical bitmap.
        
        vertBearingX    Signed distance from the vertical origin to the left
                        edge of the bitmap.
        
        vertBearingY    Signed distance from the vertical origin to the top
                        edge of the bitmap.
        
        width           Unsigned width of the bitmap (i.e. the number of
                        columns it occupies).
    
    >>> _testingValues[1].pprint()
    Height: 7
    Width: 5
    Horizontal left sidebearing: 1
    Horizontal origin-to-top: 5
    Horizontal advance: 9
    Vertical origin-to-left: -2
    Vertical top sidebearing: -1
    Vertical advance: 7
    
    >>> obj = _testingValues[1].__copy__()
    >>> obj.height = -4
    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj.isValid(logger=logger)
    test.height - ERROR - Height value -4 is out of range
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        height = dict(
            attr_initfunc = _fZero,
            attr_label = "Height",
            attr_representsy = True,
            attr_validatefunc = _fPos(
              'V0200',
              "Height value %d is out of range")),
        
        width = dict(
            attr_initfunc = _fZero,
            attr_label = "Width",
            attr_representsx = True,
            attr_validatefunc = _fPos(
              'V0201',
              "Width value %d is out of range")),
        
        horiBearingX = dict(
            attr_initfunc = _fZero,
            attr_label = "Horizontal left sidebearing",
            attr_representsx = True,
            attr_validatefunc = _fSigned(
              'V0204',
              "Horizontal bearingX value is out of range")),
        
        horiBearingY = dict(
            attr_initfunc = _fZero,
            attr_label = "Horizontal origin-to-top",
            attr_representsy = True,
            attr_validatefunc = _fSigned(
              'V0205',
              "Horizontal bearingY value is out of range")),
        
        horiAdvance = dict(
            attr_initfunc = _fZero,
            attr_label = "Horizontal advance",
            attr_representsx = True,
            attr_validatefunc = _fPos(
              'V0202',
              "Horizontal advance value %d is out of range")),
        
        vertBearingX = dict(
            attr_initfunc = _fZero,
            attr_label = "Vertical origin-to-left",
            attr_representsx = True,
            attr_validatefunc = _fSigned(
              'V0206',
              "Vertical bearingX value is out of range")),
        
        vertBearingY = dict(
            attr_initfunc = _fZero,
            attr_label = "Vertical top sidebearing",
            attr_representsy = True,
            attr_validatefunc = _fSigned(
              'V0207',
              "Vertical bearingY value is out of range")),
        
        vertAdvance = dict(
            attr_initfunc = _fZero,
            attr_label = "Vertical advance",
            attr_representsy = True,
            attr_validatefunc = _fPos(
              'V0203',
              "Vertical advance value %d is out of range")))
    
    attrSorted = (
      'height',
      'width',
      'horiBearingX',
      'horiBearingY',
      'horiAdvance',
      'vertBearingX',
      'vertBearingY',
      'vertAdvance')
    
    isSmall = False  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the BigGlyphMetrics to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0705 0105 09FE FF07                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        w.add(
          "2B2bB2bB",
          self.height,
          self.width,
          self.horiBearingX,
          self.horiBearingY,
          self.horiAdvance,
          self.vertBearingX,
          self.vertBearingY,
          self.vertAdvance)
    
    @classmethod
    def fromsmallmetrics(cls, small):
        """
        Use this class method if you have an existing SmallGlyphMetrics object
        and you need a BigGlyphMetrics object synthesized from it. This will
        create a "best-guess" for the metrics of the non-included orientation.
        
        >>> _stv = _getSmallTV()
        >>> BigGlyphMetrics.fromsmallmetrics(_stv[1]).pprint()
        Height: 7
        Width: 5
        Horizontal left sidebearing: 1
        Horizontal origin-to-top: 5
        Horizontal advance: 9
        Vertical origin-to-left: -2
        Vertical top sidebearing: -1
        Vertical advance: 9
        
        >>> BigGlyphMetrics.fromsmallmetrics(_stv[2]).pprint()
        Height: 7
        Width: 5
        Horizontal left sidebearing: 1
        Horizontal origin-to-top: 3
        Horizontal advance: 7
        Vertical origin-to-left: -2
        Vertical top sidebearing: -1
        Vertical advance: 7
        """
        
        if small.isHorizontal:
            return cls(
              height = small.height,
              width = small.width,
              horiBearingX = small.bearingX,
              horiBearingY = small.bearingY,
              horiAdvance = small.advance,
              vertBearingX = -(small.width // 2),
              vertBearingY = -1,
              vertAdvance = small.height + 2)
        
        return cls(
          height = small.height,
          width = small.width,
          horiBearingX = 1,
          horiBearingY = small.height // 2,
          horiAdvance = small.width + 2,
          vertBearingX = small.bearingX,
          vertBearingY = small.bearingY,
          vertAdvance = small.advance)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new BigGlyphMetrics object.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger("test2")
        >>> s = _testingValues[1].binaryString()
        >>> obj = BigGlyphMetrics.fromvalidatedbytes(s, logger=logger)
        test2.bigglyphmetrics - DEBUG - Walker has 8 remaining bytes.
        
        >>> obj = BigGlyphMetrics.fromvalidatedbytes(s[:-1], logger=logger)
        test2.bigglyphmetrics - DEBUG - Walker has 7 remaining bytes.
        test2.bigglyphmetrics - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('bigglyphmetrics')
        else:
            logger = logger.getChild('bigglyphmetrics')
        
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0199', (), "Insufficient bytes"))
            return None
        
        return cls(*w.unpack("2B2bB2bB"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new BigGlyphMetrics from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == BigGlyphMetrics.frombytes(obj.binaryString())
        True
        """
        
        return cls(*w.unpack("2B2bB2bB"))
    
    def lineMetricsFields(self, wantHorizontal):
        """
        Returns a tuple of values (widthMax, minOriginSB, minAdvanceSB,
        maxBeforeBL, minAfterBL) suitable for use by a LineMetrics object's
        updateFields() method.
        
        >>> _testingValues[2].lineMetricsFields(True)
        (5, 1, 11, 4, -3)
        
        >>> _testingValues[2].lineMetricsFields(False)
        (5, -1, 17, -3, -8)
        """
        
        if wantHorizontal:
            return (
              self.width,
              self.horiBearingX,
              self.horiAdvance - self.horiBearingX + self.width,
              self.horiBearingY,
              self.horiBearingY - self.height)
        
        return (
          self.width,
          self.vertBearingY,
          self.vertAdvance - self.vertBearingY + self.height,
          self.vertBearingX,
          self.vertBearingX - self.width)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __debug__:
    from fontio3 import utilities
    
    def _getSmallTV():
        from fontio3.sbit import smallglyphmetrics
        return smallglyphmetrics._testingValues
    
    _testingValues = (
        BigGlyphMetrics(),
        
        BigGlyphMetrics(7, 5, 1, 5, 9, -2, -1, 7),
        
        BigGlyphMetrics(
          width = 5,
          height = 7,
          horiBearingX = 1,
          horiBearingY = 4,
          horiAdvance = 7,
          vertAdvance = 9,
          vertBearingX = -3,
          vertBearingY = -1))

if __name__ == "__main__":
    _test()
