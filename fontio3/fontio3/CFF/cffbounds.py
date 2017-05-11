#
# cffbounds.py
#
# Copyright © 2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CFF bounding boxes.
"""

# System imports
import itertools
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

class CFFBounds(rectangle.Rectangle):
    """
    Objects representing bounding rectangles for CFF glyphs. These are
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
        
        >>> h = utilities.hexdumpString
        >>> print(h(_testingValues[0].binaryString()), end='')
               0 |000A FFEC 005A 0064                      |.....Z.d        |
        
        >>> print(h(_testingValues[1].binaryString()), end='')
               0 |0000 0000 0000 0000                      |........        |
        """
        
        w.addGroup("h", self.asList())
    
    @classmethod
    def fromcontours(cls, iterable, **kwArgs):
        """
        Creates and returns a CFFBounds computed from the specified iterable of
        single contours, which should comprise point-like objects with 'x' and
        'y' attributes. There is one optional argument, useful in computing the
        bounding box for a composite glyph:
        
            mxIter      If specified, should be an iterable over matrix.Matrix
                        objects. The objects will be applied to each member of
                        iterable, seriatim.
        
        >>> cffcontours = _getMods()
        >>> print(CFFBounds.fromcontours(cffcontours._testingValues[2]))
        Minimum X = 5, Minimum Y = 5, Maximum X = 10, Maximum Y = 10
        
        >>> print(CFFBounds.fromcontours(cffcontours._testingValues[1]))
        Minimum X = 5, Minimum Y = 5, Maximum X = 10, Maximum Y = 10
        
        >>> print((CFFBounds.fromcontours(cffcontours._testingValues[3])))
        Minimum X = 5, Minimum Y = 5, Maximum X = 100, Maximum Y = 100
        
        Note that the matrices passed in (if present) already have the issue of
        shift-before-scale or scale-before-shift implicitly resolved by their
        very construction:
        
        >>> m1 = matrix.Matrix.forScale(-0.5, 2)
        >>> m2 = matrix.Matrix.forShift(40, 70)
        >>> m2 = m2.multiply(
        ...   matrix.Matrix.forScale(1.5, 1.0))  # shift before scale
        >>> print(
        ...   CFFBounds.fromcontours(
        ...     cffcontours._testingValues[1],
        ...     mxIter=[m1, m2]))
        Minimum X = -5, Minimum Y = 10, Maximum X = 75, Maximum Y = 80
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
            # 20160401: added int(round()) of values since CFF can be
            # fractional but other font coordinates are integer only. JH.
            xMin = int(round(min(min(map(xGetter, iter(c))) for c in v if c)))
            xMax = int(round(max(max(map(xGetter, iter(c))) for c in v if c)))
            yMin = int(round(min(min(map(yGetter, iter(c))) for c in v if c)))
            yMax = int(round(max(max(map(yGetter, iter(c))) for c in v if c)))
        
        except ValueError:
            xMin = yMin = xMax = yMax = 0
        
        return cls(xMin, yMin, xMax, yMax)
    

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.fontmath import matrix
    
    def _getMods():
        from fontio3.CFF import cffcontours
        return cffcontours
    
    _testingValues = (
        CFFBounds(10, -20, 90, 100),
        CFFBounds(),
        CFFBounds(5, 5, 120, 80))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

