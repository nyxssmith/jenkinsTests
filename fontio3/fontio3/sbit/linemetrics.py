#
# linemetrics.py
#
# Copyright © 2006-2016, Monotype Imaging Inc. All Rights Reserved.
#

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _fZero():
    return 0

def _merge_ascent(selfValue, otherValue, **kwArgs):
    if kwArgs.get('onlyMinMax', True):
        return (False, selfValue)
    
    newValue = max(selfValue, otherValue)
    return (newValue != selfValue, newValue)

def _merge_check(selfValue, otherValue, **kwArgs):
    if selfValue == otherValue:
        return (False, selfValue)
    
    if 'logger' in kwArgs:
        kwArgs['logger'].error((
          'V0213',
          (),
          "Cannot merge horizontal and vertical line metrics."))
        
        return (False, selfValue)
    
    raise ValueError("Cannot merge horizontal and vertical line metrics!")

def _merge_descent(selfValue, otherValue, **kwArgs):
    if kwArgs.get('onlyMinMax', True):
        return (False, selfValue)
    
    newValue = min(selfValue, otherValue)
    return (newValue != selfValue, newValue)

def _merge_max(selfValue, otherValue, **kwArgs):
    newValue = max(selfValue, otherValue)
    return (newValue != selfValue, newValue)

def _merge_min(selfValue, otherValue, **kwArgs):
    newValue = min(selfValue, otherValue)
    return (newValue != selfValue, newValue)

def _recalc(obj, **kwArgs):
    """
    This function recalculates the 5 derivable attribute values via a passed-in
    bigMetricsIterator. Note this means that, since the strike defines its two
    line metrics objects as following protocol, they must also have
    attr_recalculatedeep set to False, and the partial recalc function for the
    whole strike then is responsible for setting things up to pass this
    iterator to the recalculated() call here.
    """
    
    r = obj.__copy__()
    assert 'bigMetricsIterator' in kwArgs
    it = kwArgs['bigMetricsIterator']
    m = next(it)
    r.widthMax = m.width
    
    if obj.isHorizontal:
        r.minOriginSB = m.horiBearingX
        r.minAdvanceSB = m.horiAdvance - (m.horiBearingX + m.width)
        r.maxBeforeBL = m.horiBearingY
        r.minAfterBL = m.horiBearingY - m.height
    
    else:
        r.minOriginSB = m.vertBearingY
        r.minAdvanceSB = m.vertAdvance - (m.vertBearingY + m.height)
        r.maxBeforeBL = m.vertBearingX
        r.minAfterBL = m.vertBearingX - m.width
    
    for m in it:
        r.widthMax = max(r.widthMax, m.width)
        
        if obj.isHorizontal:
            n1 = m.horiBearingX
            n2 = m.horiAdvance - (m.horiBearingX + m.width)
            n3 = m.horiBearingY
            n4 = m.horiBearingY - m.height
        
        else:
            n1 = m.vertBearingY
            n2 = m.vertAdvance - (m.vertBearingY + m.height)
            n3 = m.vertBearingX
            n4 = m.vertBearingX - m.width
        
        r.minOriginSB = min(r.minOriginSB, n1)
        r.minAdvanceSB = min(r.minAdvanceSB, n2)
        r.maxBeforeBL = max(r.maxBeforeBL, n3)
        r.minAfterBL = min(r.minAfterBL, n4)
        
    return (r != obj, r)

def _validate(obj, **kwArgs):
    
    # The EBSC table needs to validate without having a bigMetricsIterator,
    # so we test for the presence of that and return immediately if not there.
    
    if kwArgs.get('bigMetricsIterator', None) is None:
        return True
    
    logger = kwArgs['logger']
    correctObj = obj.recalculated(**kwArgs)
    r = True
    
    if obj.widthMax != correctObj.widthMax:
        logger.error((
          'V0214',
          (correctObj.widthMax, obj.widthMax),
          "The widthMax should be %d (is %d)"))
        
        r = False
    
    if obj.minOriginSB != correctObj.minOriginSB:
        logger.error((
          'V0215',
          (correctObj.minOriginSB, obj.minOriginSB),
          "The minOriginSB should be %d (is %d)"))
        
        r = False
    
    if obj.minAdvanceSB != correctObj.minAdvanceSB:
        logger.error((
          'V0216',
          (correctObj.minAdvanceSB, obj.minAdvanceSB),
          "The minAdvanceSB should be %d (is %d)"))
        
        r = False
    
    if obj.maxBeforeBL != correctObj.maxBeforeBL:
        logger.error((
          'V0217',
          (correctObj.maxBeforeBL, obj.maxBeforeBL),
          "The maxBeforeBL should be %d (is %d)"))
        
        r = False
    
    if obj.minAfterBL != correctObj.minAfterBL:
        logger.error((
          'V0218',
          (correctObj.minAfterBL, obj.minAfterBL),
          "The minAfterBL should be %d (is %d)"))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class LineMetrics(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects containing line metrics information for a single strike. These
    metrics are specific to either horizontal or vertical orientation, but not
    both.
    
    These are simple collections of the following attributes:
    
        isHorizontal            True if this object represents line metrics for
                                horizontal text, False if for vertical.
    
        ascent                  For horizontal text, the signed vertical
                                distance from the baseline to the line top. For
                                vertical text, the signed distance from the
                                baseline to the right boundary.
        
        descent                 For horizontal text, the signed vertical
                                distance from the baseline to the line bottom.
                                For vertical text, the signed distance from the
                                baseline to the left boundary.
        
        widthMax                Maximum pixel width of all the glyphs in the
                                strike.
        
        caretSlopeNumerator     Signed rise of the caret slope (set to 1 for 
                                non-italic fonts).
        
        caretSlopeDenominator   Signed run of the caret slope (set to 0 for
                                non-italic fonts).
        
        caretOffset             Signed extra offset to move the slanted caret.
        
        minOriginSB             For horizontal text, the signed minimum of the
                                horiBearingX values of all the glyphs in the
                                strike. For vertical text, the signed minimum
                                of the vertBearingY values of all the glyphs in
                                the strike.
        
        minAdvanceSB            For horizontal text, the signed minimum of
                                (horiAdvance-horiBearingX+width) for all glyphs
                                in the strike. For vertical text, the signed
                                minimum of (vertAdvance-vertBearingY+height)
                                for all glyphs in the strike.
        
        maxBeforeBL             For horizontal text, the signed maximum of
                                horiBearingY for all glyphs in the strike. For
                                vertical text, the signed maximum of
                                vertBearingX for all glyphs in the strike.
        
        minAfterBL              For horizontal text, the signed minimum of
                                (horiBearingY-height) for all glyphs in the
                                strike. For vertical text, the signed minimum
                                of (vertBearingX-width) for all glyphs in the
                                strike.
    
    >>> _testingValues[1].pprint()
    Horizontal: True
    Ascent: 12
    Descent: -3
    Maximum pixel width: 16
    Caret slope numerator: 1
    Caret slope denominator: 0
    Caret offset: 0
    Minimum sidebearing on origin side: 1
    Minimum sidebearing on non-origin side: 1
    Maximum positive cross-stream extent: 1
    Minimum negative cross-stream extent: -2
    
    >>> obj = _testingValues[1].__copy__()
    >>> obj.widthMax = 17
    >>> obj.minOriginSB = 0
    >>> obj.minAfterBL = -1
    >>> _testingValues[1].merged(obj).pprint_changes(_testingValues[1])
    Maximum pixel width changed from 16 to 17
    Minimum sidebearing on origin side changed from 1 to 0
    
    >>> it = iter(_bigTV()[1:3])
    >>> o2 = _testingValues[1].recalculated(bigMetricsIterator=it)
    >>> o2.pprint()
    Horizontal: True
    Ascent: 12
    Descent: -3
    Maximum pixel width: 5
    Caret slope numerator: 1
    Caret slope denominator: 0
    Caret offset: 0
    Minimum sidebearing on origin side: 1
    Minimum sidebearing on non-origin side: 1
    Maximum positive cross-stream extent: 5
    Minimum negative cross-stream extent: -3
    
    >>> o2.widthMax = 4
    >>> it = iter(_bigTV()[1:3])
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> o2.isValid(logger=logger,bigMetricsIterator=it)
    t2 - ERROR - The widthMax should be 5 (is 4)
    False
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        isHorizontal = dict(
            attr_initfunc = (lambda: True),
            attr_label = "Horizontal",
            attr_mergefunc = _merge_check),
        
        ascent = dict(
            attr_initfunc = _fZero,
            attr_label = "Ascent",
            attr_mergefunc = _merge_ascent),
        
        descent = dict(
            attr_initfunc = _fZero,
            attr_label = "Descent",
            attr_mergefunc = _merge_descent),
        
        widthMax = dict(
            attr_initfunc = _fZero,
            attr_label = "Maximum pixel width",
            attr_mergefunc = _merge_max),
        
        caretSlopeNumerator = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Caret slope numerator"),
        
        caretSlopeDenominator = dict(
            attr_initfunc = _fZero,
            attr_label = "Caret slope denominator"),
        
        caretOffset = dict(
            attr_initfunc = _fZero,
            attr_label = "Caret offset"),
        
        minOriginSB = dict(
            attr_initfunc = _fZero,
            attr_label = "Minimum sidebearing on origin side",
            attr_mergefunc = _merge_min),
        
        minAdvanceSB = dict(
            attr_initfunc = _fZero,
            attr_label = "Minimum sidebearing on non-origin side",
            attr_mergefunc = _merge_min),
        
        maxBeforeBL = dict(
            attr_initfunc = _fZero,
            attr_label = "Maximum positive cross-stream extent",
            attr_mergefunc = _merge_max),
        
        minAfterBL = dict(
            attr_initfunc = _fZero,
            attr_label = "Minimum negative cross-stream extent",
            attr_mergefunc = _merge_min))
    
    attrSorted = (
      'isHorizontal',
      'ascent',
      'descent',
      'widthMax',
      'caretSlopeNumerator',
      'caretSlopeDenominator',
      'caretOffset',
      'minOriginSB',
      'minAdvanceSB',
      'maxBeforeBL',
      'minAfterBL')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the LineMetrics object to the specified
        writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add(
          "2bB7bxx",
          self.ascent,
          self.descent,
          self.widthMax,
          self.caretSlopeNumerator,
          self.caretSlopeDenominator,
          self.caretOffset,
          self.minOriginSB,
          self.minAdvanceSB,
          self.maxBeforeBL,
          self.minAfterBL)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new LineMetrics object.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = _testingValues[1].binaryString()
        >>> obj = LineMetrics.fromvalidatedbytes(s, logger=logger)
        test.horizontal linemetrics - DEBUG - Walker has 12 remaining bytes.
        
        >>> obj = LineMetrics.fromvalidatedbytes(s[:-1], logger=logger)
        test.horizontal linemetrics - DEBUG - Walker has 11 remaining bytes.
        test.horizontal linemetrics - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        h = kwArgs.get('isHorizontal', True)
        s = ("horizontal linemetrics" if h else "vertical linemetrics")
        logger = logger.getChild(s)
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.unpack("2bB7b2x")
        return cls(*((h,) + t))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a LineMetrics object from the specified walker.
        The following keyword argument is supported:
        
            isHorizontal    True if this LineMetrics is for horizontal text,
                            and False if it's for vertical text. Default is
                            True.
        """
        
        h = kwArgs.get('isHorizontal', True)
        t = w.unpack("2bB7b2x")
        return cls(*((h,) + t))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _bigTV():
        from fontio3.sbit import bigglyphmetrics
        
        return bigglyphmetrics._testingValues
    
    _testingValues = (
        LineMetrics(),
        
        LineMetrics(
          ascent = 12,
          descent = -3,
          widthMax = 16,
          minOriginSB = 1,
          minAdvanceSB = 1,
          maxBeforeBL = 1,
          minAfterBL = -2))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
