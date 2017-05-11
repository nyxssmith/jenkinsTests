#
# triangle.py
#
# Copyright © 2006, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for triangles.
"""

# System imports
import math

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import line, mathutilities, point

# -----------------------------------------------------------------------------

#
# Classes
#

class Triangle(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing triangles. These are simple objects with three
    attributes, p1, p2, and p3, representing the vertices.
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
            attr_initfunc = (lambda: point.Point(0, 0))),
        
        p3 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0))))
    
    #
    # Special methods
    #
    
    def __str__(self):
        """
        Returns a string representation of the Triangle.
        
        >>> P = point.Point
        >>> print(Triangle(P(3, 5), P(0, 1), P(-1, 3)))
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        """
        
        return (
          "Triangle with vertices %s, %s, and %s" %
          (self.p1, self.p2, self.p3))
    
    #
    # Public methods
    #
    
    def area(self):
        """
        Returns the area of the Triangle. Since we know the three sides we use
        Heron's formula.
        
        >>> P = point.Point
        >>> Triangle(P(3, 5), P(0, 1), P(-1, 3)).area()
        5.0
        >>> print(Triangle(P(-10, 0), P(0, 0.000001), P(10, 0)).area())
        9.973764735866506e-06
        """
        
        Line = line.Line
        line12 = Line(self.p1, self.p2)
        line23 = Line(self.p2, self.p3)
        line31 = Line(self.p3, self.p1)
        a = line12.length()
        b = line23.length()
        c = line31.length()
        s = (a + b + c) / 2
        radicand = s * (s - a) * (s - b) * (s - c)
        
        if radicand >= 0:
            return math.sqrt(radicand)
        
        return 0
    
    def center(self):
        """
        Returns a Point representing the center of the Triangle.
        
        >>> P = point.Point
        >>> print(Triangle(P(3, 5), P(0, 1), P(-1, 3)).center())
        (0.6666666666666667, 3.0)
        >>> print(Triangle(P(-10, 0), P(0, 0.000001), P(10, 0)).center())
        (0.0, 5e-07)
        """
        
        if self.isDegenerate():
            minX = min(self.p1.x, self.p2.x, self.p3.x)
            minY = min(self.p1.y, self.p2.y, self.p3.y)
            maxX = max(self.p1.x, self.p2.x, self.p3.x)
            maxY = max(self.p1.y, self.p2.y, self.p3.y)
            
            L = line.Line(
              point.Point(minX, minY),
              point.Point(maxX, maxY))
            
            return L.midpoint()
        
        Line = line.Line
        line12 = Line(self.p1, self.p2)
        line23 = Line(self.p2, self.p3)
        testLine1 = Line(self.p3, line12.midpoint())
        testLine2 = Line(self.p1, line23.midpoint())
        return testLine1.intersection(testLine2)
    
    def isDegenerate(self, delta=1.0e-5):
        """
        Returns True if the Triangle is degenerate (that is, if its area is
        essentially zero).
        
        >>> P = point.Point
        >>> Triangle(P(3, 5), P(0, 1), P(-1, 3)).isDegenerate()
        False
        >>> Triangle(P(3, 5), P(3.00000001, 5), P(-1, 3)).isDegenerate()
        True
        """
        
        return mathutilities.zeroEnough(self.area(), delta=delta)
    
    def isRightTriangle(self):
        """
        Returns True if the Triangle is a right triangle. Will always return
        False for a degenerate Triangle.
        
        >>> P = point.Point
        >>> Triangle(P(3, 5), P(0, 1), P(-1, 3)).isRightTriangle()
        True
        >>> Triangle(P(0, 0), P(3, 5), P(-3, 5)).isRightTriangle()
        False
        >>> Triangle(P(-10, 0), P(0, 0.0000001), P(10, 0)).isRightTriangle()
        False
        """
        
        if self.isDegenerate():
            return False
        
        Line = line.Line
        line12 = Line(self.p1, self.p2)
        line23 = Line(self.p2, self.p3)
        line31 = Line(self.p3, self.p1)
        
        return any([
          line12.perpendicularTo(line23),
          line23.perpendicularTo(line31),
          line31.perpendicularTo(line12)])
    
    def magnified(self, xScale=1, yScale=1):
        """
        Returns a new Triangle scaled as specified about the origin.
        
        >>> P = point.Point
        >>> T = Triangle(P(3, 5), P(0, 1), P(-1, 3))
        >>> print(T)
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        >>> print(T.magnified(2.5, -0.5))
        Triangle with vertices (7.5, -2.5), (0.0, -0.5), and (-2.5, -1.5)
        """
        
        return type(self)(
          self.p1.magnified(xScale, yScale),
          self.p2.magnified(xScale, yScale),
          self.p3.magnified(xScale, yScale))
    
    def magnifiedAbout(self, about, xScale=1, yScale=1):
        """
        Returns a new Triangle scaled as specified about a specified point.
        
        >>> P = point.Point
        >>> T = Triangle(P(3, 5), P(0, 1), P(-1, 3))
        >>> print(T)
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        >>> print(T.magnifiedAbout(P(1, -1), xScale=1.75, yScale=-0.5))
        Triangle with vertices (4.5, -4.0), (-0.75, -2.0), and (-2.5, -3.0)
        """
        
        return type(self)(
          self.p1.magnifiedAbout(about, xScale, yScale),
          self.p2.magnifiedAbout(about, xScale, yScale),
          self.p3.magnifiedAbout(about, xScale, yScale))
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new Triangle moved by the specified amount.
        
        >>> P = point.Point
        >>> T = Triangle(P(3, 5), P(0, 1), P(-1, 3))
        >>> print(T)
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        >>> print(T.moved(-4, 4))
        Triangle with vertices (-1, 9), (-4, 5), and (-5, 7)
        """
        
        return type(self)(
          self.p1.moved(deltaX, deltaY),
          self.p2.moved(deltaX, deltaY),
          self.p3.moved(deltaX, deltaY))
        
    def perimeter(self):
        """
        Returns the perimeter of the Triangle.
        
        >>> P = point.Point
        >>> Triangle(P(3, 5), P(0, 1), P(-1, 3)).perimeter()
        11.70820393249937
        """
        
        Line = line.Line
        
        return (
          Line(self.p1, self.p2).length() +
          Line(self.p2, self.p3).length() +
          Line(self.p3, self.p1).length())
    
    def rotated(self, angleInDegrees=0):
        """
        Returns a new Triangle rotated by the specified angle (measured
        counter-clockwise) about the origin.
        
        >>> P = point.Point
        >>> T = Triangle(P(3, 5), P(0, 1), P(-1, 3))
        >>> print(T)
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        >>> print(T.rotated(90))
        Triangle with vertices (-5.0, 3.0), (-1.0, 0.0), and (-3.0, -1.0)
        """
        
        return type(self)(
          self.p1.rotated(angleInDegrees),
          self.p2.rotated(angleInDegrees),
          self.p3.rotated(angleInDegrees))
    
    def rotatedAbout(self, about, angleInDegrees=0):
        """
        Returns a new Triangle rotated by the specified angle (measured
        counter-clockwise) about the specified point.
        
        >>> P = point.Point
        >>> T = Triangle(P(3, 5), P(0, 1), P(-1, 3))
        >>> print(T)
        Triangle with vertices (3, 5), (0, 1), and (-1, 3)
        >>> print(T.rotatedAbout(P(-3, 3), 90))
        Triangle with vertices (-5.0, 9.0), (-1.0, 6.0), and (-3.0, 5.0)
        """
        
        return type(self)(
          self.p1.rotatedAbout(about, angleInDegrees),
          self.p2.rotatedAbout(about, angleInDegrees),
          self.p3.rotatedAbout(about, angleInDegrees))

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
