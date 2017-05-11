#
# matrix.py
#
# Copyright © 2007, 2011-2012, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities for manipulating transformation matrices.
"""

# System imports
import math

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.fontmath import matrix_row

# -----------------------------------------------------------------------------

#
# Classes
#

class Matrix(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing 3x3 matrices. These are lists of three lists of
    numeric values.
    
    >>> m = Matrix()
    >>> print(m)
    No changes
    
    >>> m = Matrix.forShift(25, -50)
    >>> m.pprint()
    Shift X by 25.0 and Y by -50.0
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_deepconverterfunc = matrix_row.Matrix_row,
        item_followsprotocol = True,
        seq_fixedlength = 3,
        seq_pprintfunc = (lambda p,x,**k: p.simple(str(x), **k)))
    
    #
    # Methods
    #
    
    def __init__(self, *args, **kwArgs):
        """
        Initializes the Matrix as specified, unless there are no parameters, in
        which case the identity matrix will be used.
        
        >>> m = Matrix([[1, 0, 0]])
        Traceback (most recent call last):
            ...
        ValueError: Matrix must have 3 rows.
        """

        if args:
            v = [matrix_row.Matrix_row(x) for x in args[0]]
            
        else:
            v = identityMatrix.__deepcopy__()
        
        if len(v) != 3:
            raise ValueError("Matrix must have 3 rows.")

        self[:] = v
    
    def __str__(self):
        """
        Returns a string representation of the Matrix object that is relatively
        simple and easy for non-mathematicians to understand.
        
        >>> mScale = Matrix.forScale(1.75, -0.5)
        >>> mShift = Matrix.forShift(80, 300)
        >>> print(Matrix())
        No changes
        
        >>> print(mScale)
        Scale X by 1.75 and Y by -0.5
        
        >>> print(mShift)
        Shift X by 80.0 and Y by 300.0
        
        >>> print(mShift.multiply(mScale))
        Shift X by 80.0 and Y by 300.0, and then scale X by 1.75 and Y by -0.5
        
        >>> obj = mScale.multiply(mShift)
        >>> obj.kwArgs = {'shiftBeforeScale': False}
        >>> print(obj)
        Scale X by 1.75 and Y by -0.5, and then shift X by 80 and Y by 300
        
        >>> print(Matrix.forRotation(90))
        [[0.0, 1.0, 0], [-1.0, 0.0, 0], [0, 0, 1]]
        """
        
        if self == identityMatrix:
            return "No changes"
        
        if any([self[0][1], self[0][2], self[1][0], self[1][2]]):
            return str([list(self[0]), list(self[1]), list(self[2])])
        
        sbs = getattr(self, 'kwArgs', {}).get('shiftBeforeScale', True)
        shift, scale = self.toShiftAndScale(sbs)
        hasXShift = bool(shift[2][0])
        hasYShift = bool(shift[2][1])
        hasShift = hasXShift or hasYShift
        hasXScale = scale[0][0] != 1.0
        hasYScale = scale[1][1] != 1.0
        hasScale = hasXScale or hasYScale
        sv = []
        
        if hasShift and hasScale:
            if sbs:
                sv.append(
                  self._nicePiece(
                    "Shift",
                    hasXShift,
                    hasYShift,
                    shift[2][0],
                    shift[2][1]))
                
                sv.append(
                  self._nicePiece(
                    "scale",
                    hasXScale,
                    hasYScale,
                    scale[0][0],
                    scale[1][1]))
            
            else:
                sv.append(
                  self._nicePiece(
                    "Scale",
                    hasXScale,
                    hasYScale,
                    scale[0][0],
                    scale[1][1]))
                
                sv.append(
                  self._nicePiece(
                    "shift",
                    hasXShift,
                    hasYShift,
                    shift[2][0],
                    shift[2][1]))
        
        elif hasShift:
            sv.append(
              self._nicePiece(
                "Shift",
                hasXShift,
                hasYShift,
                shift[2][0],
                shift[2][1]))
        
        else:
            sv.append(
              self._nicePiece(
                "Scale",
                hasXScale,
                hasYScale,
                scale[0][0],
                scale[1][1]))
        
        return ", and then ".join(sv)
    
    @staticmethod
    def _nicePiece(kind, doX, doY, x, y):
        if doX and doY:
            s = "%s X by %s and Y by %s" % (kind, x, y)
        elif doX:
            s = "%s X by %s" % (kind, x)
        else:
            s = "%s Y by %s" % (kind, y)
        
        return s
    
    def determinant(self):
        """
        Returns the determinant of self. This will always be a floating-point
        number, even if the matrix is made up of integers.
        
        >>> m = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> m.determinant()
        0.0
        """
        
        m1 = self[0][0] * (self[1][1] * self[2][2] - self[1][2] * self[2][1])
        m2 = self[0][1] * (self[1][0] * self[2][2] - self[1][2] * self[2][0])
        m3 = self[0][2] * (self[1][0] * self[2][1] - self[1][1] * self[2][0])
        return float(m1 + m3 - m2)
    
    @classmethod
    def forRotation(cls, angleInDegrees):
        """
        Returns a Matrix object representing a transformation involving just a
        rotation by the specified angle in a counter-clockwise direction.
        
        >>> print(Matrix.forRotation(360))
        No changes
        
        >>> print(Matrix.forRotation(90))
        [[0.0, 1.0, 0], [-1.0, 0.0, 0], [0, 0, 1]]
        
        >>> print(Matrix.forRotation(180))
        Scale X by -1.0 and Y by -1.0
        
        >>> print(Matrix.forRotation(270))
        [[0.0, -1.0, 0], [1.0, 0.0, 0], [0, 0, 1]]
        
        >>> m = Matrix.forRotation(45)
        >>> for v in m:
        ...   for n in v:
        ...     print(round(n, 8))
        0.70710678
        0.70710678
        0
        -0.70710678
        0.70710678
        0
        0
        0
        1
        """
        
        angleInDegrees %= 360
        
        if angleInDegrees == 0:
            s, c = 0.0, 1.0
        elif angleInDegrees == 90:
            s, c = 1.0, 0.0
        elif angleInDegrees == 180:
            s, c = 0.0, -1.0
        elif angleInDegrees == 270:
            s, c = -1.0, 0.0
        else:
            angleInRadians = angleInDegrees * math.pi / 180
            s, c = math.sin(angleInRadians), math.cos(angleInRadians)
        
        return cls([[c, s, 0], [-s, c, 0], [0, 0, 1]])
    
    @classmethod
    def forScale(cls, xScale, yScale):
        """
        Returns a Matrix object representing a transformation involving just
        the two specified scale factors.
        
        >>> print(Matrix.forScale(1, 2))
        Scale Y by 2
        """
        
        return cls([[xScale, 0, 0], [0, yScale, 0], [0, 0, 1]])
    
    @classmethod
    def forShift(cls, xMove, yMove):
        """
        Returns a Matrix object representing a transformation involving just
        the two specified shift amounts.
        
        >>> print(Matrix.forShift(1, 2))
        Shift X by 1.0 and Y by 2.0
        """
        
        return cls([[1, 0, 0], [0, 1, 0], [xMove, yMove, 1]])
    
    def inverse(self):
        """
        Returns a new Matrix representing the inverse of self, or None if the
        matrix cannot be inverted.
        
        >>> m = Matrix([[2, 0, 0], [0, 1, 0], [10, 5, 1]])
        >>> print(list(m.inverse()))
        [Matrix_row([0.5, 0.0, 0.0]), Matrix_row([0.0, 1.0, 0.0]), Matrix_row([-5.0, -5.0, 1.0])]
        >>> print(m.inverse())
        Shift X by -10.0 and Y by -5.0, and then scale X by 0.5
        >>> m = Matrix([[0.0000005, 0, 0], [0, 0.0000005, 0], [0, 0, 1.0]])
        >>> m.inverse()
        """
        
        det = self.determinant()
        
        if abs(det) < 1.0e-6:
            return None
        
        m = self.minor()
        m[0][1] = -m[0][1]
        m[1][0] = -m[1][0]
        m[1][2] = -m[1][2]
        m[2][1] = -m[2][1]
        t = m.transpose()
        return Matrix([[t[r][c] / det for c in range(3)] for r in range(3)])
    
    inverted = inverse
        
    def is2by2Equivalent(self):
        """
        Returns a boolean indicating whether our matrix is equivalent to a 2x2,
        e.g.: [[a, b, 0],
               [d, e, 0],
               [0, 0, 1]]
        
        >>> Matrix([[3, 1, 0], [-2, -2, 0], [0, 0, 1]]).is2by2Equivalent()
        True
        >>> Matrix([[3, 1, 0.5], [-2, -2, 0], [0, 0, 1]]).is2by2Equivalent()
        False
        >>> Matrix([[3, 1, 0], [-2, -2, 0.5], [0, 0, 1]]).is2by2Equivalent()
        False
        """
        
        if self[0][2]:
            return False
        
        if self[1][2]:
            return False
        
        return self[2] == [0, 0, 1]
    
    def mapPoint(self, p):
        """
        Given a point-like object (a sequence of two values), applies the
        matrix to the point and returns the resulting point as a list of two
        values.
        
        >>> m = Matrix([[2, 0, 0], [0, 1, 0], [10, 5, 1]])
        >>> print(m.mapPoint([-10, 20]))
        [-10, 25]
        """
        
        x, y = p[0], p[1]
        xNew = x * self[0][0] + y * self[1][0] + self[2][0]
        yNew = x * self[0][1] + y * self[1][1] + self[2][1]
        return [xNew, yNew]
    
    def minor(self):
        """
        Returns a new Matrix representing the minor of self.
        
        >>> m = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> print(m.minor())
        [[-3, -6, -3], [-6, -12, -6], [-3, -6, -3]]
        """
        
        m00 = self[1][1] * self[2][2] - self[1][2] * self[2][1]
        m01 = self[1][0] * self[2][2] - self[1][2] * self[2][0]
        m02 = self[1][0] * self[2][1] - self[1][1] * self[2][0]
        m10 = self[0][1] * self[2][2] - self[0][2] * self[2][1]
        m11 = self[0][0] * self[2][2] - self[0][2] * self[2][0]
        m12 = self[0][0] * self[2][1] - self[0][1] * self[2][0]
        m20 = self[0][1] * self[1][2] - self[0][2] * self[1][1]
        m21 = self[0][0] * self[1][2] - self[0][2] * self[1][0]
        m22 = self[0][0] * self[1][1] - self[0][1] * self[1][0]
        return Matrix([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]])
    
    def multiplied(self, other):
        """
        Returns a new Matrix representing self times other (in that order).
        
        >>> m1 = Matrix([[0.5, 0, 0], [0, 1, 0], [-5, -5, 1]])
        >>> m2 = Matrix([[3, 0, 0], [0, 3, 0], [0, 30, 1]])
        >>> print(list(m1.multiplied(m2)))
        [Matrix_row([1.5, 0.0, 0.0]), Matrix_row([0, 3, 0]), Matrix_row([-15, 15, 1])]
        >>> print(m1.multiplied(m2))
        Shift X by -10.0 and Y by 5.0, and then scale X by 1.5 and Y by 3
        """
        
        m = []
        
        for row in range(3):
            for col in range(3):
                sum = 0
                
                for n in range(3):
                    sum += self[row][n] * other[n][col]
                
                m.append(sum)
        
        return Matrix([m[0:3], m[3:6], m[6:9]])
    
    multiply = multiplied
    
    def toShiftAndScale(self, shiftBeforeScale=True):
        """
        Decomposes self into two separate Matrix objects, one for shift and one
        for scale. If shiftBeforeScale is True, self is decomposed such that
        the shift matrix is multiplied by the scale to yield self; otherwise,
        self is decomposed such that the scale matrix is multiplied by the
        shift to yield self.

        Returns a pair (shift, scale) in that order, irrespective of the state
        of the shiftBeforeScale boolean.
        
        >>> m = Matrix([[3, 0, 0], [0, 2, 0], [30, 40, 1]])
        >>> ss = m.toShiftAndScale(False)
        >>> print(ss[0])  # always the shift
        Shift X by 30.0 and Y by 40.0
        >>> print(ss[1])  # always the scale
        Scale X by 3 and Y by 2
        
        >>> ss = m.toShiftAndScale(True)
        >>> print(ss[0])  # always the shift
        Shift X by 10.0 and Y by 20.0
        >>> print(ss[1])  # always the scale
        Scale X by 3 and Y by 2
        
        >>> mx = Matrix([[3, 0.5, 0.5], [0.5, 3, 0], [0, 0, 1]])
        >>> sx = mx.toShiftAndScale()
        >>> sx[0][0]
        Matrix_row([1, 0, 0])
        """
        
        a, b, c, d = self[0][0], self[0][1], self[1][0], self[1][1]
        mScale = Matrix([[a, b, 0], [c, d, 0], [0, 0, 1]])
        
        if shiftBeforeScale:
            if b == 0 and c == 0:  # the most common case by far
                dx = self[2][0] / a
                dy = self[2][1] / d
            
            else:
                disc = a * d - b * c
                dx = (d * self[2][0] - c * self[2][1]) / disc
                dy = (self[2][0] - a * dx) / c
            
            mShift = Matrix.forShift(dx, dy)
        
        else:
            mShift = Matrix.forShift(self[2][0], self[2][1])
        
        return mShift, mScale
    
    def transpose(self):
        """
        Returns a new Matrix representing the transposition of self.
        
        >>> m = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        >>> print(m.transpose())
        [[1, 4, 7], [2, 5, 8], [3, 6, 9]]
        """
        
        return Matrix([[self[c][r] for c in range(3)] for r in range(3)])
    
    transposed = transpose

# -----------------------------------------------------------------------------

#
# Constants
#

identityMatrix = Matrix([
    matrix_row.Matrix_row([1.0, 0.0, 0.0]),
    matrix_row.Matrix_row([0.0, 1.0, 0.0]),
    matrix_row.Matrix_row([0.0, 0.0, 1.0])])

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
    _test()
