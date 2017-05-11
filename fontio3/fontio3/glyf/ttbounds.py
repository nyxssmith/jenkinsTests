#
# ttbounds.py
#
# Copyright © 2004-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType bounding boxes.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontmath import rectangle

# -----------------------------------------------------------------------------

#
# Private constants
#

_xGetter = operator.attrgetter('x')
_yGetter = operator.attrgetter('y')

# -----------------------------------------------------------------------------

#
# Classes
#

class TTBounds(rectangle.Rectangle):
    """
    Objects representing bounding rectangles for TrueType glyphs. These are
    simple objects with 4 signed integer attributes: xMin, yMin, xMax, and yMax
    (in that order).
    
    >>> _testingValues[0].pprint()
    Minimum X: 10
    Minimum Y: -20
    Maximum X: 90
    Maximum Y: 100
    
    >>> _testingValues[0].scaled(1.5).pprint()
    Minimum X: 15
    Minimum Y: -30
    Maximum X: 135
    Maximum Y: 150
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        xMin = dict(attr_roundfunc = utilities.truncateRound),
        yMin = dict(attr_roundfunc = utilities.truncateRound),
        xMax = dict(attr_roundfunc = utilities.ceilingRound),
        yMax = dict(attr_roundfunc = utilities.ceilingRound))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 000A FFEC 005A 0064                      |.....Z.d        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0000 0000 0000                      |........        |
        """
        
        w.addGroup("h", self.asList())
    
    @classmethod
    def fromcontour(cls, c, **kwArgs):
        """
        Creates and returns a TTBounds from the specified contour, which should
        be a sequence of point-like objects with 'x' and 'y' attributes. There
        is one optional argument:
        
            mx      If specified, should be a matrix.Matrix. The matrix will be
                    applied to the contour before the bounds are taken.
        
        >>> ttcontour = _getMods()[0]
        >>> print(TTBounds.fromcontour(ttcontour._testingValues[0]))
        Minimum X = 20, Minimum Y = 10, Maximum X = 380, Maximum Y = 490
        
        >>> m = matrix.Matrix.forScale(0.5, -1.5)
        >>> print(TTBounds.fromcontour(ttcontour._testingValues[0], mx=m))
        Minimum X = 10, Minimum Y = -735, Maximum X = 190, Maximum Y = -15
        
        >>> print(TTBounds.fromcontour([]))
        Minimum X = 0, Minimum Y = 0, Maximum X = 0, Maximum Y = 0
        """
        
        m = kwArgs.get('mx', None)
        
        if m is not None:
            c = c.transformed(m)
        
        try:
            xGetter = _xGetter
            yGetter = _yGetter
            xMin = min(map(xGetter, iter(c)))
            xMax = max(map(xGetter, iter(c)))
            yMin = min(map(yGetter, iter(c)))
            yMax = max(map(yGetter, iter(c)))
        
        except ValueError:
            xMin = yMin = xMax = yMax = 0
        
        return cls(xMin, yMin, xMax, yMax)
    
    @classmethod
    def fromcontours(cls, iterable, **kwArgs):
        """
        Creates and returns a TTBounds computed from the specified iterable of
        single contours, which should comprise point-like objects with 'x' and
        'y' attributes. There is one optional argument, useful in computing the
        bounding box for a composite glyph:
        
            mxIter      If specified, should be an iterable over matrix.Matrix
                        objects. The objects will be applied to each member of
                        iterable, seriatim.
        
        >>> ttcontours = _getMods()[1]
        >>> print(TTBounds.fromcontours(ttcontours._testingValues[2]))
        Minimum X = 20, Minimum Y = 10, Maximum X = 980, Maximum Y = 1090
        
        >>> print(TTBounds.fromcontours(ttcontours._testingValues[1]))
        Minimum X = 620, Minimum Y = 610, Maximum X = 980, Maximum Y = 1090
        
        Note that the matrices passed in (if present) already have the issue of
        shift-before-scale or scale-before-shift implicitly resolved by their
        very construction:
        
        >>> m1 = matrix.Matrix.forScale(-0.5, 2)
        >>> m2 = matrix.Matrix.forShift(40, 70)
        >>> m2 = m2.multiply(
        ...   matrix.Matrix.forScale(1.5, 1.0))  # shift before scale
        >>> print(
        ...   TTBounds.fromcontours(
        ...     ttcontours._testingValues[1],
        ...     mxIter=[m1, m2]))
        Minimum X = -490, Minimum Y = 770, Maximum X = 1485, Maximum Y = 2180
        
        >>> print(TTBounds.fromcontours([[], [], []]))
        Minimum X = 0, Minimum Y = 0, Maximum X = 0, Maximum Y = 0
        """
        
        if iterable is None or len(iterable) == 0:
            return None
        
        mxIt = kwArgs.get('mxIter', None)
        
        if mxIt is not None:
            v = [c.transformed(m) for c, m in zip(iterable, mxIt)]
        else:
            v = list(iterable)
        
        try:
            xGetter = _xGetter
            yGetter = _yGetter
            xMin = min(min(map(xGetter, iter(c))) for c in v if c)
            xMax = max(max(map(xGetter, iter(c))) for c in v if c)
            yMin = min(min(map(yGetter, iter(c))) for c in v if c)
            yMax = max(max(map(yGetter, iter(c))) for c in v if c)
        
        except ValueError:
            xMin = yMin = xMax = yMax = 0
        
        return cls(xMin, yMin, xMax, yMax)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTBounds. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[0].binaryString()
        >>> TTBounds.fromvalidatedbytes(s, logger=logger).pprint()
        test.ttbounds - DEBUG - Walker has 8 remaining bytes.
        Minimum X: 10
        Minimum Y: -20
        Maximum X: 90
        Maximum Y: 100
        
        >>> obj = TTBounds.fromvalidatedbytes(s[:-1], logger=logger)
        test.ttbounds - DEBUG - Walker has 7 remaining bytes.
        test.ttbounds - ERROR - Insufficient bytes.
        
        >>> s = utilities.fromhex("0C 00 00 14 05 00 0A A0")
        >>> obj = TTBounds.fromvalidatedbytes(s, logger=logger)
        test.ttbounds - DEBUG - Walker has 8 remaining bytes.
        test.ttbounds - ERROR - xMin 3072 is greater than xMax 1280.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ttbounds')
        else:
            logger = logger.getChild('ttbounds')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.group("h", 4)
        
        if t[0] > t[2]:
            logger.error((
              'V0179',
              (t[0], t[2]),
              "xMin %d is greater than xMax %d."))
            
            return None
        
        if t[1] > t[3]:
            logger.error((
              'V0180',
              (t[1], t[3]),
              "yMin %d is greater than yMax %d."))
            
            return None
        
        return cls(*t)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TTBounds from the specified walker.
        
        >>> tv = _testingValues
        >>> tv[0] == TTBounds.frombytes(tv[0].binaryString())
        True
        >>> tv[1] == TTBounds.frombytes(tv[1].binaryString())
        True
        """
        
        return cls(*w.group("h", 4))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.fontmath import matrix
    
    def _getMods():
        from fontio3.glyf import ttcontour, ttcontours
        return ttcontour, ttcontours
    
    _testingValues = (
        TTBounds(10, -20, 90, 100),
        TTBounds(),
        TTBounds(5, 5, 120, 80))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
