#
# smallglyphmetrics.py
#
# Copyright © 2006-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for small metrics (which include values for just one orientation).
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

class SmallGlyphMetrics(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing collections of metrics for a bitmap in a single
    orientation. These are simple collections of the following attributes:
        
        advance         Unsigned advance width of the bitmap.
        
        bearingX        Signed distance from the origin to the left edge of the
                        bitmap.
        
        bearingY        Signed distance from the origin to the top edge of the
                        bitmap.
        
        height          Unsigned height of the bitmap (i.e. the number of rows
                        it occupies).
        
        isHorizontal    True if these metrics are for horizontal text; False if
                        they are for vertical text.
        
        width           Unsigned width of the bitmap (i.e. the number of
                        columns it occupies).
    
    >>> _testingValues[1].pprint()
    Horizontal: True
    Height: 7
    Width: 5
    Origin-to-left: 1
    Origin-to-top: 5
    Advance: 9
    
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
        isHorizontal = dict(
            attr_initfunc = (lambda: True),
            attr_label = "Horizontal"),
        
        height = dict(
            attr_initfunc = _fZero,
            attr_label = "Height",
            attr_representsy = True,
            attr_validatefunc = _fPos(
              'V0208',
              "Height value %d is out of range")),
        
        width = dict(
            attr_initfunc = _fZero,
            attr_label = "Width",
            attr_representsx = True,
            attr_validatefunc = _fPos(
              'V0209',
              "Width value %d is out of range")),
        
        bearingX = dict(
            attr_initfunc = _fZero,
            attr_label = "Origin-to-left",
            attr_representsx = True,
            attr_validatefunc = _fSigned(
              'V0210',
              "BearingX value is out of range")),
        
        bearingY = dict(
            attr_initfunc = _fZero,
            attr_label = "Origin-to-top",
            attr_representsy = True,
            attr_validatefunc = _fSigned(
              'V0211',
              "BearingY value is out of range")),
        
        advance = dict(
            attr_initfunc = _fZero,
            attr_label = "Advance",
            attr_validatefunc = _fPos(
              'V0212',
              "Advance value %d is out of range")))
    
    attrSorted = (
      'isHorizontal',
      'height',
      'width',
      'bearingX',
      'bearingY',
      'advance')
    
    isSmall = True  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SmallGlyphMetrics to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0705 0105 09                             |.....           |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0705 FEFF 07                             |.....           |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        w.add(
          "2B2bB",
          self.height,
          self.width,
          self.bearingX,
          self.bearingY,
          self.advance)
    
    @classmethod
    def frombigmetrics(cls, big, wantHorizontal):
        """
        Use this class method if you have an existing BigGlyphMetrics object
        and you need a SmallGlyphMetrics object of the specified orientation
        synthesized from it.
        
        >>> big = _getBigTV()[1]
        >>> SmallGlyphMetrics.frombigmetrics(big, True).pprint()
        Horizontal: True
        Height: 7
        Width: 5
        Origin-to-left: 1
        Origin-to-top: 5
        Advance: 9
        
        >>> SmallGlyphMetrics.frombigmetrics(big, False).pprint()
        Horizontal: False
        Height: 7
        Width: 5
        Origin-to-left: -2
        Origin-to-top: -1
        Advance: 7
        """
        
        if wantHorizontal:
            return cls(
              isHorizontal = True,
              height = big.height,
              width = big.width,
              bearingX = big.horiBearingX,
              bearingY = big.horiBearingY,
              advance = big.horiAdvance)
        
        return cls(
          isHorizontal = False,
          height = big.height,
          width = big.width,
          bearingX = big.vertBearingX,
          bearingY = big.vertBearingY,
          advance = big.vertAdvance)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new SmallGlyphMetrics object.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger("test2")
        >>> s = _testingValues[1].binaryString()
        >>> obj = SmallGlyphMetrics.fromvalidatedbytes(s, logger=logger)
        test2.smallglyphmetrics - DEBUG - Walker has 5 remaining bytes.
        
        >>> obj = SmallGlyphMetrics.fromvalidatedbytes(s[:-1], logger=logger)
        test2.smallglyphmetrics - DEBUG - Walker has 4 remaining bytes.
        test2.smallglyphmetrics - ERROR - Insufficient bytes
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('smallglyphmetrics')
        else:
            logger = logger.getChild('smallglyphmetrics')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 5:
            logger.error(('V0199', (), "Insufficient bytes"))
            return None
        
        return cls(kwArgs.get('isHorizontal', True), *w.unpack("2B2bB"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SmallGlyphMetrics from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> d = {'isHorizontal': True}
        >>> obj == SmallGlyphMetrics.frombytes(obj.binaryString(), **d)
        True
        
        >>> obj = _testingValues[2]
        >>> d = {'isHorizontal': False}
        >>> obj == SmallGlyphMetrics.frombytes(obj.binaryString(), **d)
        True
        """
        
        return cls(kwArgs.get('isHorizontal', True), *w.unpack("2B2bB"))
    
    def lineMetricsFields(self, wantHorizontal):
        """
        Returns a tuple of values (widthMax, minOriginSB, minAdvanceSB,
        maxBeforeBL, minAfterBL) suitable for use by a LineMetrics object's
        updateFields() method.

        If the orientation is not available a ValueError is raised. A client
        calling this method should then convert the small metrics object into a
        big metrics object and then call the resulting object's
        lineMetricsFields method.
        
        >>> _testingValues[3].lineMetricsFields(True)
        (5, 1, 1, 4, -3)
        
        >>> _testingValues[4].lineMetricsFields(False)
        (5, -1, 3, -3, -8)
        
        >>> _testingValues[3].lineMetricsFields(False)
        Traceback (most recent call last):
          ...
        ValueError
        """
        
        if wantHorizontal != self.isHorizontal:
            raise ValueError()
        
        if wantHorizontal:
            return (
              self.width,
              self.bearingX,
              self.advance - (self.bearingX + self.width),
              self.bearingY,
              self.bearingY - self.height)
        
        return (
          self.width,
          self.bearingY,
          self.advance - (self.bearingY + self.height),
          self.bearingX,
          self.bearingX - self.width)

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
    
    def _getBigTV():
        from fontio3.sbit import bigglyphmetrics
        return bigglyphmetrics._testingValues
    
    _testingValues = (
        SmallGlyphMetrics(),
        SmallGlyphMetrics(True, 7, 5, 1, 5, 9),
        SmallGlyphMetrics(False, 7, 5, -2, -1, 7),
        SmallGlyphMetrics(True, 7, 5, 1, 4, 7),
        SmallGlyphMetrics(False, 7, 5, -3, -1, 9))

if __name__ == "__main__":
    _test()
