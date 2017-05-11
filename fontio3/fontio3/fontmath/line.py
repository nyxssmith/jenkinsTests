#
# line.py
#
# Copyright © 2006-2014, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for lines.
"""

# System imports
import math

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import mathutilities, matrix, point, rectangle

# -----------------------------------------------------------------------------

#
# Classes
#

class Line(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing finite line segments. These are simple objects with
    two attributes: p1 and p2, both of which are Point objects.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        p1 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0))),
        
        p2 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0))))
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a nicely formatted string representing the Line.
        
        >>> P = point.Point
        >>> print(Line(P(3, 8), P(-1, 15.5)))
        Line from (3, 8) to (-1, 15.5)
        >>> print(Line(P(3, 8), P(3, 8)))
        Degenerate line at (3, 8)
        """
        
        if self.isDegenerate():
            return "Degenerate line at %s" % (self.p1,)
        
        return "Line from %s to %s" % (self.p1, self.p2)
    
    def bounds(self):
        """
        >>> P = point.Point
        >>> L1 = Line(P(1, 1), P(1, 9))
        >>> print(L1.bounds())
        Minimum X = 1, Minimum Y = 1, Maximum X = 1, Maximum Y = 9
        """
        
        xMin = min(self.p1.x, self.p2.x)
        yMin = min(self.p1.y, self.p2.y)
        xMax = max(self.p1.x, self.p2.x)
        yMax = max(self.p1.y, self.p2.y)
        return rectangle.Rectangle(xMin, yMin, xMax, yMax)
    
    def distanceToPoint(self, p):
        """
        Returns an unsigned distance from the line to the point. This will be
        the smallest possible distance (i.e. the distance along the normal to
        the line's slope).
        
        >>> P = point.Point
        >>> L1 = Line(P(1, 1), P(1, 9))
        >>> print(L1.distanceToPoint(P(1, 5)))
        0.0
        >>> print(L1.distanceToPoint(P(5, 5)))
        4.0
        >>> print(L1.distanceToPoint(P(-5, 15)))
        6.0
        >>> L3 = Line(P(0,0),P(0,0))
        >>> print(L3.distanceToPoint(P(0, 0)))
        0.0
        >>> L2 = Line(P(3, 1), P(1, -6))
        >>> print(L2.distanceToPoint(P(0, 0)))
        2.609850715025092
        """
        
        if self.isDegenerate():
            return p.distanceFrom(self.p1)
        
        t = self.parametricValueFromProjectedPoint(p)
        pOnLine = self.pointFromParametricValue(t)
        return p.distanceFrom(pOnLine)
    
    def equalEnough(self, other, delta=1.0e-5):
        """
        Returns True if self's two points are within delta of other's two
        points.
        
        >>> P = point.Point
        >>> L1 = Line(P(3, -2), P(4, 4))
        >>> L2 = Line(P(3.001, -1.999), P(4, 4.001))
        >>> L1.equalEnough(L2)
        False
        >>> L1.equalEnough(L2, delta=0.01)
        True
        """
        
        way1 = (
          self.p1.equalEnough(other.p1, delta) and
          self.p2.equalEnough(other.p2, delta))
        
        way2 = (
          self.p1.equalEnough(other.p2, delta) and
          self.p2.equalEnough(other.p1, delta))
        
        return way1 or way2
    
    extrema = bounds  # no difference for lines
    
    def intersection(self, other, delta=1.0e-5):
        """
        Determines if self and other intersect, and returns an object
        representing that intersection. This could be None if they do not
        intersect, a Point object if they intersect in a single point, or a
        Line object if they are fully or partly coincident.
        
        >>> P = point.Point
        
        Simple point intersection cases:
        
        >>> print(Line(P(0, 0), P(0, 8)).intersection(Line(P(0, 4), P(8, 4))))
        (0.0, 4.0)
        >>> print(Line(P(2, 1), P(5, 4)).intersection(Line(P(3, 3), P(11, 3))))
        (4.0, 3.0)
        
        Non-parallel, out-of-bounds intersection case:
        
        >>> L1 = Line(P(2, 2), P(5, 5))
        >>> L2 = Line(P(20000, 2), P(20004, 5))
        >>> print(L1.intersection(L2))
        None
        
        Parallel line cases, disjoint and otherwise:
        
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(1, 2), P(5, 6))))
        None
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(2, 2), P(6, 6))))
        Line from (2.0, 2.0) to (5, 5)
        >>> print(Line(P(0, 0), P(1000000, 1000000)).intersection(Line(P(999999, 999999), P(2000000, 2000000))))
        (999999, 999999)
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(6, 6), P(8, 8))))
        None
        
        Degenerate line cases:
        >>> print(Line(P(4, 4), P(4, 4)).intersection(Line(P(0, 0), P(5, 5))))
        (4, 4)
        >>> print(Line(P(4, 4), P(4, 4)).intersection(Line(P(1, 0), P(5, 5))))
        None
        >>> print(Line(P(4, 4), P(4, 4)).intersection(Line(P(4, 4), P(4, 4.0000001))))
        (4, 4)
        >>> print(Line(P(4, 4), P(4, 4)).intersection(Line(P(70000, 70000), P(70000, 70000))))
        None
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(3, 3), P(3, 3))))
        (3, 3)
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(8, 8), P(8, 8))))
        None
        >>> print(Line(P(1, 1), P(5, 5)).intersection(Line(P(2, 3), P(2, 3))))
        None
        """
        
        CE = mathutilities.closeEnough
        CES = mathutilities.closeEnoughSpan
        IIP = mathutilities.intIfPossible
        
        if self.isDegenerate(delta):
            if other.isDegenerate(delta):
                if mathutilities.closeEnoughXY(self.p1, other.p1, delta):
                    return self.p1.__copy__()
                
                return None
            
            t = other.parametricValueFromPoint(self.p1)
            
            if t is None:
                return t
            
            return self.p1.__copy__()
        
        elif other.isDegenerate(delta):
            t = self.parametricValueFromPoint(other.p1)
            
            if (t is None) or (not CES(t)):
                return None
            
            return other.p1.__copy__()
        
        if CE(self.slope(), other.slope()):
            # lines are either parallel or coincident
            t1 = self.parametricValueFromPoint(other.p1)
            
            if t1 is None:
                return None
            
            # lines are coincident, although the segments may not overlap
            t2 = self.parametricValueFromPoint(other.p2)
            
            if max(t1, t2) < 0 or min(t1, t2) > 1:
                return None
            
            t1 = IIP(max(0, t1))
            t2 = IIP(min(1, t2))
            
            if CE(t1, t2):
                return other.p1
            
            return type(self)(
              self.pointFromParametricValue(t1),
              self.pointFromParametricValue(t2))
        
        # the slopes differ, so solve the equations
        factorMatrix = matrix.Matrix((
          (self.p2.x - self.p1.x, other.p1.x - other.p2.x, 0),
          (self.p2.y - self.p1.y, other.p1.y - other.p2.y, 0),
          (0, 0, 1)))
        
        fmInverse = factorMatrix.inverse()
        assert fmInverse is not None
        
        constMatrix = matrix.Matrix((
          (other.p1.x - self.p1.x, 0, 0),
          (other.p1.y - self.p1.y, 0, 0),
          (0, 0, 1)))
        
        prod = fmInverse.multiply(constMatrix)
        t = IIP(prod[0][0])
        u = IIP(prod[1][0])
        
        if CES(t) and CES(u):
            return self.pointFromParametricValue(t)
        
        return None  # no intersection within the actual length
    
    def isDegenerate(self, delta=1.0e-5):
        """
        Returns True if the two points making up the Line are equal enough,
        using the specified delta.
        
        >>> P = point.Point
        >>> Line(P(5, 2), P(5.001, 2)).isDegenerate()
        False
        >>> Line(P(5, 2), P(5.001, 2)).isDegenerate(delta=0.01)
        True
        """
        
        return self.p1.equalEnough(self.p2, delta=delta)
    
    def length(self):
        """
        Returns the length of the Line.
        
        >>> P = point.Point
        >>> Line(P(0, 0), P(3, 4)).length()
        5.0
        
        Degenerate lines have zero length:
        
        >>> Line(P(2, -3), P(2, -3)).length()
        0
        """
        
        if self.isDegenerate():
            return 0
        
        return math.sqrt(
          ((self.p2.x - self.p1.x) ** 2) +
          ((self.p2.y - self.p1.y) ** 2))
    
    def magnified(self, xScale=1, yScale=1):
        """
        Returns a new Line scaled as specified about the origin.
        
        >>> P = point.Point
        >>> L = Line(P(3, -2), P(4, 4))
        >>> print(L.magnified(1.75, -0.5))
        Line from (5.25, 1.0) to (7.0, -2.0)
        """
        
        return type(self)(
          self.p1.magnified(xScale, yScale),
          self.p2.magnified(xScale, yScale))
    
    def magnifiedAbout(self, about, xScale=1, yScale=1):
        """
        Returns a new Line scaled as specified about a specified point.
        
        >>> P = point.Point
        >>> L = Line(P(3, -2), P(4, 4))
        >>> print(L.magnifiedAbout(P(1, -1), xScale=1.75, yScale=-0.5))
        Line from (4.5, -0.5) to (6.25, -3.5)
        """
        
        return type(self)(
          self.p1.magnifiedAbout(about, xScale, yScale),
          self.p2.magnifiedAbout(about, xScale, yScale))
    
    def midpoint(self):
        """
        Returns a Point representing the midpoint of the Line.
        
        >>> P = point.Point
        >>> print(Line(P(3, -2), P(4, 4)).midpoint())
        (3.5, 1.0)
        """
        
        return (self.p1 + self.p2) / 2
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new Line moved by the specified amount.
        
        >>> P = point.Point
        >>> L = Line(P(3, -2), P(4, 4))
        >>> print(L)
        Line from (3, -2) to (4, 4)
        >>> print(L.moved(-5, 10))
        Line from (-2, 8) to (-1, 14)
        """
        
        return type(self)(
          self.p1.moved(deltaX, deltaY),
          self.p2.moved(deltaX, deltaY))
    
    def normalized(self, length=1):
        """
        Returns a new Line whose first point is the same as self's, but whose
        second point is moved such that the length of the new Line is as
        specified. The new Line's second point will be in the same direction
        relative to the first point as the original Line's was.
        
        If self is degenerate it cannot be normalized to a non-zero length, so
        a copy of self will be returned if length is zero and None will be
        returned otherwise.
        
        Specifying a length of zero will return a degenerate line both of whose
        points are the same as self.p1.
        
        >>> P = point.Point
        >>> print(Line(P(0, 0), P(10, 0)).normalized())
        Line from (0, 0) to (1.0, 0.0)
        >>> print(Line(P(0, 0), P(0, 10)).normalized())
        Line from (0, 0) to (0, 1)
        >>> print(Line(P(0, 0), P(0, -10)).normalized())
        Line from (0, 0) to (0, -1)
        >>> print(Line(P(1, -1), P(-2, -6)).normalized())
        Line from (1, -1) to (0.48550424457247343, -1.8574929257125443)
        >>> print(Line(P(0, 0), P(10, 0)).normalized(length=5))
        Line from (0, 0) to (5.0, 0.0)
        
        Degenerate cases:
        
        >>> LDeg = Line(P(2, -3), P(2, -3))
        >>> LDeg.normalized() is None
        True
        >>> LDeg.normalized(0) == LDeg
        True
        >>> LDeg.normalized(0) is LDeg
        False
        """
        
        p = self.p1
        
        if not length:
            return type(self)(p, p)
        
        slope = self.slope()
        
        if slope is None:
            return (None if length else self.__copy__())
        
        if abs(slope) == float("+inf"):
            # line is vertical
            sign = (-1 if self.p2.y < p.y else 1)
            return type(self)(p, point.Point(p.x, p.y + sign * length))
        
        sign = (-1 if self.p2.x < p.x else 1)
        x = p.x + sign * math.sqrt(length ** 2 / (1 + slope ** 2))
        y = p.y + slope * (x - p.x)
        return type(self)(p, point.Point(x, y))
    
    def parametricValueFromProjectedPoint(self, p):
        """
        Given a Point, not necessarily on the line, find the t-value
        representing the projection of that point onto the line. The returned
        t-value is not necessarily in the [0, 1] range.
        
        If self is degenerate, zero is returned.
        
        >>> P = point.Point
        >>> Line(P(0, 0), P(10, 0)).parametricValueFromProjectedPoint(P(2, 6))
        0.2
        >>> Line(P(0, 0), P(0, 10)).parametricValueFromProjectedPoint(P(2, 6))
        0.6
        >>> Line(P(1, 1), P(5, 4)).parametricValueFromProjectedPoint(P(2, 4))
        0.52
        >>> Line(P(1, 1), P(5, 4)).parametricValueFromProjectedPoint(P(25, 4))
        4.2
        
        Degenerate lines always return 0, regardless of the point:
        
        >>> Line(P(2, -3), P(2, -3)).parametricValueFromProjectedPoint(P(0, 0))
        0.0
        """
        
        m = self.slope()
        
        if m is None:
            return 0.0
        
        if abs(m) == float("+inf"):
            # line is vertical
            return self.parametricValueFromPoint(point.Point(self.p1.x, p.y))
        
        if mathutilities.zeroEnough(m):
            # line is horizontal
            return self.parametricValueFromPoint(point.Point(p.x, self.p1.y))
        
        # line is neither vertical nor horizontal
        numer = self.p1.y - p.y - (m * self.p1.x) - ((1 / m) * p.x)
        denom = -m - (1 / m)
        x = numer / denom
        return (x - self.p1.x) / (self.p2.x - self.p1.x)
    
    def parametricValueFromPoint(self, p):
        """
        Given a Point, returns the t value that satisfies the parametric
        equation: (1-t)p1 + (t)p2 == p. Returns None if p does not intersect
        self.
        
        >>> P = point.Point
        >>> L = Line(P(1, 1), P(3, 3))
        >>> print(L.parametricValueFromPoint(P(1, 1)))
        0.0
        >>> print(L.parametricValueFromPoint(P(2, 2)))
        0.5
        >>> print(L.parametricValueFromPoint(P(2, 3)))
        None
        
        >>> L = Line(P(1, 1), P(3, 1))  # horizontal
        >>> print(L.parametricValueFromPoint(P(2, 1)))
        0.5
        >>> print(L.parametricValueFromPoint(P(2, 2)))
        None
        
        >>> L = Line(P(1, 1), P(1, 3))  # vertical
        >>> print(L.parametricValueFromPoint(P(1, 2)))
        0.5
        >>> print(L.parametricValueFromPoint(P(2, 2)))
        None
        
        >>> L = Line(P(1, 1), P(1, 1))  # degenerate (point)
        >>> print(L.parametricValueFromPoint(P(1, 1)))
        0.0
        >>> print(L.parametricValueFromPoint(P(2, 2)))
        None
        """
        
        ce = mathutilities.closeEnough
        p1 = self.p1
        p2 = self.p2
        
        if ce(p1.x, p2.x):
            tx = None
        else:
            tx = (p.x - p1.x) / (p2.x - p1.x)
        
        if ce(p1.y, p2.y):
            ty = None
        else:
            ty = (p.y - p1.y) / (p2.y - p1.y)
        
        if tx is None and ty is None:
            # degenerate case: self is a Point
            return (0.0 if p1.equalEnough(p) else None)
        
        elif tx is None:
            return (ty if ce(p.x, p1.x) else None)
        
        elif ty is None:
            return (tx if ce(p.y, p1.y) else None)
        
        return (tx if ce(tx, ty) else None)
    
    def perpendicularTo(self, other):
        """
        Returns True if the two Lines are orthogonal, False otherwise.
        
        >>> P = point.Point
        >>> Line(P(0, 0), P(1, 0)).perpendicularTo(Line(P(0, 0), P(0, 1)))
        True
        >>> Line(P(1, 1), P(2, 2)).perpendicularTo(Line(P(-6, 5), P(-7, 6)))
        True
        >>> Line(P(1, 1), P(2, 3)).perpendicularTo(Line(P(-6, 5), P(-7, 6)))
        False
        >>> Line(P(0, 0), P(0, 5)).perpendicularTo(Line(P(-5, 0), P(5, 0)))
        True
        >>> Line(P(0, 5), P(0, 0)).perpendicularTo(Line(P(-5, 0), P(5, 0)))
        True
        >>> Line(P(4, 4), P(4, 4)).perpendicularTo(Line(P(-5, 0), P(5, 1)))
        Traceback (most recent call last):
          ...
        ValueError: Cannot determine perpendicularity for degenerate lines!
        """
        
        selfSlope = self.slope()
        otherSlope = other.slope()
        
        if selfSlope is None or otherSlope is None:
            raise ValueError(
              "Cannot determine perpendicularity for degenerate lines!")
        
        try:
            r = mathutilities.closeEnough(selfSlope, -1 / otherSlope)
        except ZeroDivisionError:
            r = abs(selfSlope) == float("+inf")
        
        return r
    
    def piece(self, t1, t2):
        """
        Creates a new Line object which maps t1 to t2 in the original to 0 to 1
        in the new.
        
        Returns two things: the new Line, and an anonymous function which
        maps an old t-value to a new u-value.
        
        >>> P = point.Point
        >>> L = Line(P(1, 1), P(5, 9))
        >>> print(L)
        Line from (1, 1) to (5, 9)
        >>> L2, func = L.piece(0.25, 0.75)
        >>> print(L2)
        Line from (2.0, 3.0) to (4.0, 7.0)
        >>> func(0.25), func(0.5), func(0.75)
        (0.0, 0.5, 1.0)
        """
        
        L = type(self)(
          self.pointFromParametricValue(t1),
          self.pointFromParametricValue(t2))
        
        return L, lambda x: ((x - t1) / (t2 - t1))
    
    def pointFromParametricValue(self, t):
        """
        Given a parametric value, returns a Point on self at that value.
        
        >>> P = point.Point
        >>> L = Line(P(1, 1), P(5, 9))
        >>> print(L.pointFromParametricValue(0.0))
        (1.0, 1.0)
        >>> print(L.pointFromParametricValue(1.0))
        (5.0, 9.0)
        >>> print(L.pointFromParametricValue(-2.0))
        (-7.0, -15.0)
        >>> print(L.pointFromParametricValue(0.5))
        (3.0, 5.0)
        """
        
        return (self.p1 * (1 - t)) + (self.p2 * t)
    
    def rotated(self, angleInDegrees=0):
        """
        Returns a new Line rotated by the specified angle (measured counter-
        clockwise) about the origin.
        
        >>> P = point.Point
        >>> L = Line(P(3, -2), P(4, 4))
        >>> print(L.rotated(90))
        Line from (2.0, 3.0) to (-4.0, 4.0)
        """
        
        return type(self)(
          self.p1.rotated(angleInDegrees),
          self.p2.rotated(angleInDegrees))
    
    def rotatedAbout(self, about, angleInDegrees=0):
        """
        Returns a new Line rotated by the specified angle (measured counter-
        clockwise) about the specified point.
        
        >>> P = point.Point
        >>> L = Line(P(3, -2), P(4, 4))
        >>> print(L.rotatedAbout(P(-3, 3), 90))
        Line from (2.0, 9.0) to (-4.0, 10.0)
        """
        
        return type(self)(
          self.p1.rotatedAbout(about, angleInDegrees),
          self.p2.rotatedAbout(about, angleInDegrees))
    
    def slope(self):
        """
        Returns the slope of the Line (potentially a signed infinity, where the
        sign reflects a movement from self.p1 to self.p2).
        
        If the Line is degenerate, the slope will be returned as None, but no
        error will be raised.
        
        >>> P = point.Point
        >>> print(Line(P(2, 4), P(1, 2)).slope())
        2.0
        >>> print(Line(P(1, 2), P(2, 4)).slope())
        2.0
        >>> print(Line(P(2, 4), P(2, 2)).slope())
        -inf
        >>> print(Line(P(2, -4), P(2, 2)).slope())
        inf
        >>> print(Line(P(2, -4), P(2, -4)).slope())
        None
        """
        
        if self.isDegenerate():
            return None
        
        if mathutilities.closeEnough(self.p1.x, self.p2.x):
            if self.p2.y >= self.p1.y:
                return float("+inf")
            
            return float("-inf")
        
        return (self.p2.y - self.p1.y) / (self.p2.x - self.p1.x)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
