#
# point.py
#
# Copyright © 2007-2007, 2011-2012, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for two-dimensional geometric points.
"""

# System imports
import collections
import math

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.fontmath import matrix

# -----------------------------------------------------------------------------

#
# Classes
#

class Point(
  collections.namedtuple("NT", "x y"),
  metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing geometric, two-dimensional points. These are named
    tuples whose two components are 'x' and 'y'.
    
    >>> obj = Point(3, -4)
    >>> print(obj.y)
    -4
    
    >>> print(obj)
    (3, -4)
    
    >>> toOrigin = matrix.Matrix.forShift(-1, -1)
    >>> scaleIt = matrix.Matrix.forScale(2, 3)
    >>> fromOrigin = matrix.Matrix.forShift(1, 1)
    >>> m = toOrigin.multiply(scaleIt).multiply(fromOrigin)
    >>> print(obj.transformed(m))
    (5, -14)
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_representsxyalternating = True,
        item_scaledirect = True,
        seq_fixedlength = 2,
        seq_makefunc = (lambda v, a, **k: type(v)(*a, **k)))
    
    #
    # Special methods
    #
    
    def __abs__(self):
        """
        Returns a new Point which lies in the first quadrant.
        
        >>> print(abs(Point(-3, -4)))
        (3, 4)
        """
        
        return type(self)(abs(self.x), abs(self.y), **self.__dict__)
    
    def __add__(self, other):
        """
        Returns a new Point representing the (vector) sum of the two input
        points. It is also permitted for other to be a constant, in which case
        it will be added to both coordinates.
        
        >>> print(Point(1, 2) + Point(-5, 5))
        (-4, 7)
        >>> print(Point(1, 2) + 3)
        (4, 5)
        """
        
        try:
            r = type(self)(self.x + other.x, self.y + other.y, **self.__dict__)
        except AttributeError:
            r = type(self)(self.x + other, self.y + other, **self.__dict__)
        
        return r
    
    def __floordiv__(self, other):
        """
        Returns a new Point representing the seriatim floor division of self by
        other; note that other may be a constant.
        
        >>> print(Point(3, -7) // Point(2, -4))
        (1, 1)
        >>> print(Point(5, 13) // 8)
        (0, 1)
        """
        
        try:
            r = type(self)(
              self.x // other.x,
              self.y // other.y,
              **self.__dict__)
        
        except AttributeError:
            r = type(self)(self.x // other, self.y // other, **self.__dict__)
        
        return r
    
    def __mul__(self, other):
        """
        Returns a new Point representing the seriatim multiplication of self by
        other; note that other may be a constant.
        
        >>> print(Point(2, -3) * Point(-7, -2))
        (-14, 6)
        >>> print(Point(2, -3) * 4)
        (8, -12)
        """
        
        try:
            r = type(self)(self.x * other.x, self.y * other.y, **self.__dict__)
        except AttributeError:
            r = type(self)(self.x * other, self.y * other, **self.__dict__)
        
        return r
    
    def __neg__(self):
        """
        Returns a new Point representing the reflection about the origin of the
        specified point.
        
        >>> print(-Point(3, -4))
        (-3, 4)
        """
        
        return type(self)(-self.x, -self.y, **self.__dict__)
    
    def __radd__(self, other): return self.__add__(other)
    def __rmul__(self, other): return self.__mul__(other)
    def __rsub__(self, other): return other + self.__neg__()
    def __rfloordiv__(self, other): return self.__floordiv__(other)
    def __rtruediv__(self, other): return self.__truediv__(other)
    
    def __str__(self):
        """
        Returns a unified string representing the whole Point.
        
        >>> print(Point(2.5, -1.25))
        (2.5, -1.25)
        """
        
        return "(%s, %s)" % (self.x, self.y)
    
    def __sub__(self, other):
        """
        Returns a new Point representing the seriatim difference of self minus
        other; note that other may be a constant.
        
        >>> print(Point(1, 3) - Point(0, 9))
        (1, -6)
        >>> print(Point(1, 3) - 12)
        (-11, -9)
        """
        
        try:
            r = type(self)(self.x - other.x, self.y - other.y, **self.__dict__)
        except AttributeError:
            r = type(self)(self.x - other, self.y - other, **self.__dict__)
        
        return r
    
    def __truediv__(self, other):
        """
        Returns a new Point representing the seriatim full division of self by
        other; note that other may be a constant.
        
        >>> print(Point(3, -7) / Point(2, -4))
        (1.5, 1.75)
        >>> print(Point(5, 13) / 8)
        (0.625, 1.625)
        """
        
        try:
            r = type(self)(self.x / other.x, self.y / other.y, **self.__dict__)
        except AttributeError:
            r = type(self)(self.x / other, self.y / other, **self.__dict__)
        
        return r
    
    #
    # Public methods
    #
    
    def distanceFrom(self, other):
        """
        Returns the distance between the two Points.
        
        >>> print(Point(4, 5).distanceFrom(Point(1, 1)))
        5.0
        """
        
        return math.sqrt(sum((other[i] - self[i]) ** 2 for i in range(2)))
    
    def distanceFromOrigin(self):
        """
        Returns the distance of self from the origin.
        
        >>> print(Point(3, 4).distanceFromOrigin())
        5.0
        """
        
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def equalEnough(self, other, delta=1.0e-5):
        """
        Returns True if the coordinates of self differ from the coordinates of
        other by no more than delta. Note this does not compare the (possibly
        diagonal) distance between self and other; if that is needed, it should
        be done directly by the client.
        
        >>> Point(3, -4).equalEnough(Point(1, 1))
        False
        >>> Point(3, -4).equalEnough(Point(1, 1), delta=10.0)
        True
        """
        
        delta = abs(delta)
        
        return (
          abs(self.x - other.x) <= delta and
          abs(self.y - other.y) <= delta)
    
    def magnified(self, xScale=1.0, yScale=1.0):
        """
        Returns a new Point scaled by the specified factors about the origin.
        
        The name "magnified" is used to prevent conflicts with the standard
        metaclass "scaled()" method; their signatures are different, so this
        conflict is to be avoided.
        
        >>> print(Point(3, -4).magnified(1.5, -0.75))
        (4.5, 3.0)
        """
        
        return type(self)(self.x * xScale, self.y * yScale, **self.__dict__)
    
    def magnifiedAbout(self, about, xScale=1.0, yScale=1.0):
        """
        Returns a new Point scaled by the specified factors about the specified
        point.
        
        The name "magnified" is used to prevent conflicts with the standard
        metaclass "scaled()" method; their signatures are different, so this
        conflict is to be avoided.
        
        >>> print(Point(3, -4).magnifiedAbout(Point(1, 1), xScale=2, yScale=3))
        (5, -14)
        """
        
        M = matrix.Matrix
        shiftToOrigin = M.forShift(*(-about))
        scaleIt = M.forScale(xScale, yScale)
        shiftBack = M.forShift(*about)
        tMatrix = shiftToOrigin.multiply(scaleIt).multiply(shiftBack)
        return type(self)(*tMatrix.mapPoint(self), **self.__dict__)
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new Point moved by the specified deltas.
        
        >>> print(Point(-2, 4).moved(3, -5))
        (1, -1)
        """
        
        return type(self)(self.x + deltaX, self.y + deltaY, **self.__dict__)
    
    def rotated(self, angleInDegrees=0.0):
        """
        Returns a new Point rotated by the specified angle, counter-clockwise,
        about the origin.
        
        >>> print(Point(3, -4).rotated(90))
        (4.0, 3.0)
        """
        
        return self.rotatedAbout(Point(0, 0), angleInDegrees)
    
    def rotatedAbout(self, about, angleInDegrees=0.0):
        """
        Returns a new Point rotated by the specified angle, counter-clockwise,
        about the specified Point.
        
        >>> print(Point(3, -4).rotatedAbout(Point(1, 1), 90))
        (6.0, 3.0)
        """
        
        M = matrix.Matrix
        shiftToOrigin = M.forShift(*(-about))
        turnIt = M.forRotation(angleInDegrees)
        shiftBack = M.forShift(*about)
        tMatrix = shiftToOrigin.multiply(turnIt).multiply(shiftBack)
        return type(self)(*tMatrix.mapPoint(self), **self.__dict__)
    
    def zeroEnough(self, delta=1.0e-5):
        """
        Return True if both coordinates of self differ from zero by no more
        than delta.
        
        >>> Point(0, 0.1).zeroEnough()
        False
        >>> Point(0, 0.1).zeroEnough(0.25)
        True
        """
        
        delta = abs(delta)
        return abs(self.x) <= delta and abs(self.y) <= delta

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
