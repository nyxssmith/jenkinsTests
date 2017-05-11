#
# contour_cubic.py
#
# Copyright © 2004-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single contours, which are simply sequences of PointWithOnOff
objects.
"""

# System imports
import itertools
import operator

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.fontmath import (
  cspline,
  line,
  mathutilities,
  point,
  pointwithonoff,
  rectangle)

# -----------------------------------------------------------------------------

#
# Exception Classes
#

class InvalidContourError(Exception):
    """
    Raised when an invalid contour is detected.
    """
    
    pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Contour_cubic(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single CFF contours. These are lists of PointWithOnOff
    objects.
    
    Note that Contour_cubic objects do not have fromwalker() or buildBinary()
    methods; those functions are handled at a higher level, given the
    convoluted nature of the 'CFF ' table.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = (lambda p, obj, label: p.simple(obj, label=label)),
        item_pprintlabelfunc = (lambda i: "Point %d" % (i,)))
    
    #
    # Methods
    #
    
    def bounds(self):
        """
        Returns a Rectangle with the extrema based on the curves; this is
        (usually) different from what you'd get by calling extrema().
        """
        
        r = None
        
        for c in self.splineIterator():
            b = c.bounds()
            r = (b if r is None else r.unioned(b))
        
        return r
    
    def containsContour(self, other):
        """
        Returns True if self contains other. For this to be the case, the
        following conditions must apply:
        
            1.  No spline in other intersects any spline in self. Note this
                even includes single point intersections!
            
            2.  The bounds of other are smaller than the bounds of self.
            
            3.  The two contours have different chiralities.
            
            4.  At least one on-curve point in other is contained by self.

        >>> _testingValues[2].containsContour(_testingValues[3])
        True
        >>> _testingValues[3].containsContour(_testingValues[2])
        False
        >>> _testingValues[2].containsContour(_testingValues[2])
        False
        >>> _testingValues[3].containsContour(_testingValues[3])
        False
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(100, 500),
        ...   P(200, 800),
        ...   P(250, 1000),
        ...   P(300, 800)])
        >>> c2 = Contour_cubic([
        ...   P(100, 500),
        ...   P(200, 800),
        ...   P(250, 1000)])
        >>> c2.containsContour(c)
        False
        >>> c.containsContour(c2)
        False
        """
        
        if other.bounds().area() >= self.bounds().area():
            return False
        
        if other.isClockwise() == self.isClockwise():
            return False
        
        selfSplines = list(self.splineIterator())
        otherSplines = list(other.splineIterator())
        
        for selfPiece in selfSplines:
            for otherPiece in otherSplines:
                if selfPiece.intersection(otherPiece):
                    return False
        
        try:
            pt = next(p for p in other if not p.onCurve)
        except StopIteration:
            pt = other.normalized()[0]
        
        return self.containsPoint(pt)
    
    def containsPoint(self, p):
        """
        Returns True if p is an interior point, False if it is on the edge or
        exterior.
        
        >>> P = point.Point
        >>> _testingValues[3].containsPoint(P(850, 900))
        True
        >>> _testingValues[3].containsPoint(P(700, 950))
        False
        """
        
        dSum = {False: 0, True: 0}
        
        for spln in self.splineIterator():
            d = spln.transitions(p.x, p.x + 1000000, p.y, True)
            dSum[False] += d[False]
            dSum[True] += d[True]
        
        return bool((dSum[False] - dSum[True]) % 2)
    
    def corners(self, includeOffCurve=False):
        """
        Returns a tuple with 8 indices into self, as follows (note some may
        repeat):
        
                [0]     topmost then leftmost
                [1]     topmost then rightmost
                [2]     leftmost then topmost
                [3]     leftmost then bottommost
                [4]     bottommost then leftmost
                [5]     bottommost then rightmost
                [6]     rightmost then topmost
                [7]     rightmost then bottommost
            
        Note that an empty Contour will return a list of None values.
        
        >>> print(_testingValues[3].corners())
        [3, 3, 0, 0, 0, 2, 2, 2]
        
        >>> print(_testingValues[3].corners(includeOffCurve=True))
        [3, 3, 0, 0, 1, 1, 2, 2]
        
        >>> print(_testingValues[1].corners())
        [None, None, None, None, None, None, None, None]
        """
        
        if not self:
            return [None] * 8
        
        if includeOffCurve:
            iv = list(range(len(self)))
        else:
            iv = [i for i, p in enumerate(self) if p.onCurve]
        
        if not iv:
            return [None] * 8
        
        xMin = min(self[i].x for i in iv)
        xMax = max(self[i].x for i in iv)
        yMin = min(self[i].y for i in iv)
        yMax = max(self[i].y for i in iv)
        f1 = operator.itemgetter(1)
        vT = [(i, self[i].x) for i in iv if self[i].y == yMax]
        vT.sort(key=f1)
        vB = [(i, self[i].x) for i in iv if self[i].y == yMin]
        vB.sort(key=f1)
        vL = [(i, self[i].y) for i in iv if self[i].x == xMin]
        vL.sort(key=f1)
        vR = [(i, self[i].y) for i in iv if self[i].x == xMax]
        vR.sort(key=f1)
        
        return [
          vT[0][0],
          vT[-1][0],
          vL[-1][0],
          vL[0][0],
          vB[0][0],
          vB[-1][0],
          vR[-1][0],
          vR[0][0]]
    
    def extrema(self, excludeOffCurve=False):
        """
        Returns a Rectangle with the extrema based on the actual coordinates;
        this is different from the bounds, which are calculated based on the
        actual curves.
        
        Note that you can check whether one or more extreme points are off-
        curve by comparing the results of this method with True and False as
        the flags -- if the resulting Rectangles differ, then at least one of
        the extreme points is off-curve.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> print(c.extrema())
        Traceback (most recent call last):
            ...
        InvalidContourError: contour has no on-curve points.
        
        >>> c = Contour_cubic([
        ...   P(200, -300, onCurve=True),
        ...   P(0, 100, onCurve=False),
        ...   P(400, 400, onCurve=True),
        ...   P(700, 0, onCurve=True)])
        >>> print(c.extrema())
        Minimum X = 0, Minimum Y = -300, Maximum X = 700, Maximum Y = 400
        """
        
        r = None
        
        for c in self.splineIterator():
            ex = c.extrema(excludeOffCurve=excludeOffCurve)
            r = (ex if r is None else r.unioned(ex))
        
        return r
    
    def intersects(self, other, delta=1.0e-5):
        """
        Returns True if self and other intersect edges at any point. Note that
        one contour completely inside another is not an intersection for the
        purposes of this method; the edges have to touch. Also note that points
        may touch and it doesn't count as an intersection; for this method to
        return True, there must be at least one actual crossing somewhere.
        
        >>> _testingValues[0].intersects(_testingValues[2])
        False
        
        >>> shifted = Contour_cubic([p.moved(20, 20) for p in _testingValues[0]])
        >>> _testingValues[0].pprint()
        Point 0: (20, 10), on-curve
        Point 1: (20, 490), on-curve
        Point 2: (380, 490), on-curve
        Point 3: (380, 10), on-curve
        >>> shifted.pprint()
        Point 0: (40, 30), on-curve
        Point 1: (40, 510), on-curve
        Point 2: (400, 510), on-curve
        Point 3: (400, 30), on-curve
        >>> _testingValues[0].intersects(shifted)
        True
        """
        
        splineGroup1 = list(self.splineIterator())
        extremaGroup1 = [obj.extrema() for obj in splineGroup1]
        splineGroup2 = list(other.splineIterator())
        extremaGroup2 = [obj.extrema() for obj in splineGroup2]
        foundOverlap = False
        CE = mathutilities.closeEnough
        
        for curve1, rect1 in zip(splineGroup1, extremaGroup1):
            for curve2, rect2 in zip(splineGroup2, extremaGroup2):
                # only bother with intersection check if extrema overlap
                
                if (
                  rect1.isEmpty() or
                  rect2.isEmpty() or
                  max(rect1.overlapDegrees(rect2)) > 0):
                    
                    for sectObj in curve1.intersection(curve2, delta):
                        if not isinstance(sectObj, point.Point):
                            foundOverlap = True
                            break
                        
                        t = curve1.parametricValueFromPoint(sectObj)
                        u = curve2.parametricValueFromPoint(sectObj)
                        
                        if (
                          (t is not None) and
                          (u is not None) and
                          not ((CE(t, 0) or CE(t, 1)) and (CE(u, 0) or CE(u, 1)))):
                            
                            foundOverlap = True
                            break
                
                if foundOverlap:
                    break
            
            if foundOverlap:
                break
        
        return foundOverlap
    
    def isClockwise(self):
        """
        Returns True if the contour is clockwise.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(100, 500),
        ...   P(300, 800),
        ...   P(200, 100)])
        >>> c.isClockwise()
        True
        >>> c.reverse()
        >>> c.isClockwise()
        False
        """
        
        return self.polygonArea() < 0
    
    def normalized(self):
        """
        Returns a copy of self that has the first point on-curve.
        """
        
        v = list(self)
        
        if v and (not v[0].onCurve):
            onCurvePoints = [i for i, p in enumerate(v) if p.onCurve]
            
            if len(onCurvePoints):
                firstOn = min(onCurvePoints)
                v = v[firstOn:] + v[:firstOn]
            
            else:
                raise InvalidContourError("contour has no on-curve points.")
        
        return type(self)(v)
    
    def polygonArea(self):
        """
        Returns the signed area of the polygon comprising all the points in
        the contour. This area will be negative if the contour is clockwise,
        and positive if it is counter-clockwise.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(100, 900),
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> c.polygonArea()
        -640000.0
        >>> c.reverse()
        >>> c.polygonArea()
        640000.0
        """
        
        it = itertools.cycle(self)
        next(it)
        cumul = 0
        
        for p1, p2 in zip(self, it):
            cumul += p1.x * p2.y
            cumul -= p2.x * p1.y
        
        return cumul / 2
    
    def splineIterator(self):
        """
        Returns an iterator over CSpline objects for the contour.
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(620, 610),
        ...   P(620, 1090),
        ...   P(980, 1090),
        ...   P(980, 610)])
        >>> for obj in c.splineIterator(): print(obj)
        Line from (620, 610) to (620, 1090)
        Line from (620, 1090) to (980, 1090)
        Line from (980, 1090) to (980, 610)
        Line from (980, 610) to (620, 610)
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_cubic([
        ...   P(100, 900),
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> for obj in c.splineIterator(): print(obj)
        Line from (100, 900) to (900, 900)
        Line from (900, 900) to (900, 100)
        Line from (900, 100) to (100, 100)
        Line from (100, 100) to (100, 900)
        
        >>> c = Contour_cubic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> for obj in c.splineIterator(): print(obj)
        Traceback (most recent call last):
            ...
        InvalidContourError: contour has no on-curve points.
        """
        
        n = self.normalized()
        i = 0
        v = n + n
        C = cspline.CSpline
        P = point.Point
        
        while i < len(n):  # yes, n, not v
            p1, p2 = v[i:i+2]
            assert p1.onCurve
            
            if p2.onCurve:
                yield C(P(p1), None, None, P(p2))
                i += 1
            
            else:
                yield C(P(p1), P(p2), P(v[i+2]), P(v[i+3]))
                i += 3

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.fontmath import matrix
    
    pv = pointwithonoff._testingValues
    
    _testingValues = (
        Contour_cubic(pv[4:8]),
        Contour_cubic(),
        Contour_cubic(pv[8:12]),
        Contour_cubic(pv[12:16]),
        Contour_cubic(pv[0:4]),
        Contour_cubic((pv[8],) + pv[8:12]),
        Contour_cubic(pv[4:6] + (pv[4],) + pv[6:8]),
        Contour_cubic((pv[1],) + pv[4:6] + (pv[2],) + pv[6:8]),
        Contour_cubic((pv[4],) + (pv[6],) + (pv[5],) + (pv[7],))  # self-intersects
        )
    
    del pv
def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
