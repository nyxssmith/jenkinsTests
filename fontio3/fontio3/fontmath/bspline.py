#
# bspline.py
#
# Copyright © 2006, 2011-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for quadratic b-splines.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.fontmath import line, mathutilities, point, rectangle, triangle

# -----------------------------------------------------------------------------

#
# Classes
#

class BSpline(object, metaclass=simplemeta.FontDataMetaclass):
    """
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        onCurve1 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0))),
        
        offCurve = dict(
            attr_followsprotocol = True),
        
        onCurve2 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0))))
    
    attrSorted = ('onCurve1', 'onCurve2', 'offCurve')
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a nice string representation of the spline. This also works for
        degenerate splines.
        
        >>> P = point.Point
        >>> print(BSpline(P(4, -3), P(4, -3), None))
        Point at (4, -3)
        
        >>> print(BSpline(P(1, 3), P(5, 0), None))
        Line from (1, 3) to (5, 0)
        
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)))
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        """
        
        on1 = self.onCurve1
        on2 = self.onCurve2
        
        if self.offCurve is None:
            if on1.equalEnough(on2):
                return "Point at %s" % (on1,)
            
            return "Line from %s to %s" % (on1, on2)
        
        return (
          "Curve from %s to %s with off-curve point %s" %
          (on1, on2, self.offCurve))
    
    def _intersection_curve(self, other):
        """
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> c = BSpline(P(2, 3), P(4, 4), P(0, 1))
        >>> b._intersection_curve(c)
        (Point(x=4, y=4), Point(x=4, y=4))
        """
        ZE = mathutilities.zeroEnough
        CES = mathutilities.closeEnoughSpan
        A = self.onCurve1.x + self.onCurve2.x - (2 * self.offCurve.x)
        assert not ZE(A)
        B = 2 * (self.offCurve.x - self.onCurve1.x)
        C = self.onCurve1.x
        D = other.onCurve1.x + other.onCurve2.x - (2 * other.offCurve.x)
        E = 2 * (other.offCurve.x - other.onCurve1.x)
        F = other.onCurve1.x
        G = self.onCurve1.y + self.onCurve2.y - (2 * self.offCurve.y)
        assert not ZE(G)
        H = 2 * (self.offCurve.y - self.onCurve1.y)
        denom = B * G - A * H
        assert not ZE(denom)
        I = self.onCurve1.y
        J = other.onCurve1.y + other.onCurve2.y - (2 * other.offCurve.y)
        K = 2 * (other.offCurve.y - other.onCurve1.y)
        L = other.onCurve1.y
        
        # This is the full case, where we have to solve the following pair of
        # equations:
        #
        #   At^2 + Bt + C = Du^2 + Eu + F
        #   Gt^2 + Ht + I = Ju^2 + Ku + L
        #
        # Since we know both A and G are nonzero, we can multiply the first
        # equation by G and the second one by A, and then subtract the two
        # equations. Simplifying, we get this equation representing t in terms
        # of u:
        #
        #   t = (DG-AJ)/(BG-AH) u^2 +
        #       (EG-AK)/(BG-AH) u   +
        #       ((FG-AL)+(AI-CG))/(BG-AH)
        #
        # To simplify, we define the following three values:
        #
        #   M = (DG-AJ)/(BG-AH)
        #   N = (EG-AK)/(BG-AH)
        #   P = ((FG-AL)+(AI-CG))/(BG-AH)
        #
        # This results in the simpler equation:
        #
        #   t = Mu^2 + Nu + P
        #
        # This is then substituted back into the y-equation:
        #
        #   Gt^2 + Ht + I = Ju^2 + Ku + L
        #
        # Resulting in the final quartic:
        #
        #   (GM^2)u^4 +
        #   (2GMN)u^3 +
        #   (GN^2 + 2GMP + HM - J)u^2+
        #   (2GNP + HN - K)u +
        #   (GP^2 + HP + I - L) = 0
        
        M = (D * G - A * J) / denom
        N = (E * G - A * K) / denom
        P = ((F * G - A * L) + (A * I - C * G)) / denom
        
        roots = mathutilities.quartic(
          G * M * M,
          2 * G * M * N,
          G * N * N + 2 * G * M * P + H * M - J,
          2 * G * N * P + H * N - K,
          G * P * P + H * P + I - L)
        
        v = []
        
        for u in roots:
            if not ZE(u.imag):
                continue
            
            u = u.real
            
            if CES(u):
                # a possible solution
                t = M * u * u + N * u + P
                
                if CES(t):
                    # an actual solution
                    v.append(other.pointFromParametricValue(u))
        
        return tuple(v)
    
    def _intersection_curve_xspecial(self, other):
        ZE = mathutilities.zeroEnough
        CES = mathutilities.closeEnoughSpan
        A = self.onCurve1.x + self.onCurve2.x - (2 * self.offCurve.x)
        assert ZE(A)
        B = 2 * (self.offCurve.x - self.onCurve1.x)
        C = self.onCurve1.x
        D = other.onCurve1.x + other.onCurve2.x - (2 * other.offCurve.x)
        E = 2 * (other.offCurve.x - other.onCurve1.x)
        F = other.onCurve1.x
        G = self.onCurve1.y + self.onCurve2.y - (2 * self.offCurve.y)
        assert not ZE(G)
        H = 2 * (self.offCurve.y - self.onCurve1.y)
        I = self.onCurve1.y
        J = other.onCurve1.y + other.onCurve2.y - (2 * other.offCurve.y)
        K = 2 * (other.offCurve.y - other.onCurve1.y)
        L = other.onCurve1.y
        
        # Since A is zero, we have the following simplified equation:
        #
        #   Bt + C = Du^2 + Eu + F
        #
        # This gives us a solution for t in terms of u:
        #
        #   t = (Du^2 + Eu + (F - C)) / B
        #
        # To simplify, we define the following three values:
        #
        #   M = D / B
        #   N = E / B
        #   P = (F - C) / B
        #
        # This results in the simpler equation:
        #
        #   t = Mu^2 + Nu + P
        #
        # This is then substituted back into the y-equation:
        #
        #   Gt^2 + Ht + I = Ju^2 + Ku + L
        #
        # Resulting in the final quartic:
        #
        #   (GM^2)u^4 +
        #   (2GMN)u^3 +
        #   (GN^2 + 2GMP + HM - J)u^2+
        #   (2GNP + HN - K)u +
        #   (GP^2 + HP + I - L) = 0
        
        M = D / B
        N = E / B
        P = (F - C) / B
        
        roots = mathutilities.quartic(
          G * M * M,
          2 * G * M * N,
          G * N * N + 2 * G * M * P + H * M - J,
          2 * G * N * P + H * N - K,
          G * P * P + H * P + I - L)
        
        v = []
        
        for u in roots:
            if not ZE(u.imag):
                continue
            
            u = u.real
            
            if CES(u):
                # a possible solution
                t = M * u * u + N * u + P
                
                if CES(t):
                    # an actual solution
                    v.append(other.pointFromParametricValue(u))
        
        return tuple(v)
    
    def _intersection_curve_yspecial(self, other):
        ZE = mathutilities.zeroEnough
        CES = mathutilities.closeEnoughSpan
        A = self.onCurve1.x + self.onCurve2.x - (2 * self.offCurve.x)
        assert not ZE(A)
        B = 2 * (self.offCurve.x - self.onCurve1.x)
        C = self.onCurve1.x
        D = other.onCurve1.x + other.onCurve2.x - (2 * other.offCurve.x)
        E = 2 * (other.offCurve.x - other.onCurve1.x)
        F = other.onCurve1.x
        G = self.onCurve1.y + self.onCurve2.y - (2 * self.offCurve.y)
        assert ZE(G)
        H = 2 * (self.offCurve.y - self.onCurve1.y)
        I = self.onCurve1.y
        J = other.onCurve1.y + other.onCurve2.y - (2 * other.offCurve.y)
        K = 2 * (other.offCurve.y - other.onCurve1.y)
        L = other.onCurve1.y
        
        # Since G is zero, we have the following simplified equation:
        #
        #   Ht + I = Ju^2 + Ku + L
        #
        # This gives us a solution for t in terms of u:
        #
        #   t = (Ju^2 + Ku + (L - I)) / H
        #
        # To simplify, we define the following three values:
        #
        #   M = J / H
        #   N = K / H
        #   P = (L - I) / H
        #
        # This results in the simpler equation:
        #
        #   t = Mu^2 + Nu + P
        #
        # This is then substituted back into the x-equation:
        #
        #   At^2 + Bt + C = Du^2 + Eu + F
        #
        # Resulting in the final quartic:
        #
        #   (AM^2)u^4 +
        #   (2AMN)u^3 +
        #   (AN^2 + 2AMP + BM - D)u^2+
        #   (2ANP + BN - E)u +
        #   (AP^2 + BP + C - F) = 0
        
        M = J / H
        N = K / H
        P = (L - I) / H
        
        roots = mathutilities.quartic(
          A * M * M,
          2 * A * M * N,
          A * N * N + 2 * A * M * P + B * M - D,
          2 * A * N * P + B * N - E,
          A * P * P + B * P + C - F)
        
        v = []
        
        for u in roots:
            if not ZE(u.imag):
                continue
            
            u = u.real
            
            if CES(u):
                # a possible solution
                t = M * u * u + N * u + P
                
                if CES(t):
                    # an actual solution
                    v.append(other.pointFromParametricValue(u))
        
        return tuple(v)
    
    def _intersection_line(self, theLine):
        """
        Utility function handling the line-curve intersection cases. Note that
        self.offCurve must not be None (that will have been filtered out in
        the higher-level code).
       
        >>> P = point.Point
        >>> a = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> b = line.Line(P(2, -3), P(4, -3))
        >>> c = line.Line(P(4, -3), P(4, -3))
        >>> d = line.Line(P(4, -3), P(6, 4))
        >>> e = line.Line(P(2, 0), P(4, 0))
        >>> a._intersection_line(c)
        ()
        
        >>> a._intersection_line(b)
        (Point(x=2.0, y=-3.0),)
        
        >>> a._intersection_line(d)      
        ()
        
        >>> a._intersection_line(e)      
        ()
        """
        
        assert self.offCurve is not None
        ZE = mathutilities.zeroEnough
        CES = mathutilities.closeEnoughSpan
        
        # Set up the coefficients for the x-equation:
        #     At + B = Cu^2 + Du + E
        # and the y-equation:
        #     Ft + G = Hu^2 + Iu + J
        
        A = theLine.p2.x - theLine.p1.x
        B = theLine.p1.x
        C = self.onCurve1.x + self.onCurve2.x - 2 * self.offCurve.x
        D = 2 * (self.offCurve.x - self.onCurve1.x)
        E = self.onCurve1.x
        
        F = theLine.p2.y - theLine.p1.y
        G = theLine.p1.y
        H = self.onCurve1.y + self.onCurve2.y - 2 * self.offCurve.y
        I = 2 * (self.offCurve.y - self.onCurve1.y)
        J = self.onCurve1.y
        
        if ZE(A) and ZE(F):
            
            # If both A and F are zero, the curve is degenerate (the two on-
            # curve points are essentially coincident). In this case, there is
            # only a single point intersection possible if either of the on-
            # curve points lies on the line.
            
            t = theLine.parametricValueFromPoint(self.onCurve1)
            return (() if t is None else (self.onCurve1.__copy__(),))
        
        if ZE(A):
        
            # If A is zero and F is not, we solve the simpler quadratic:
            #     Cu^2 + Du + (E-B) = 0
            # and then plug that u-value into the y-equation to get t.
            
            root1, root2 = mathutilities.quadratic(C, D, E - B)
            
            if not ZE(root1.imag):
                return ()
            
            v = []
            
            for u in (root1, root2):
                if CES(u):
                    # a possible solution
                    t = (H * u * u + I * u + J - G) / F
                    
                    if CES(t):
                        # an actual solution
                        v.append(theLine.pointFromParametricValue(t))
            
            return tuple(v)
        
        if ZE(F):
        
            # If F is zero and A is not, we solve the simpler quadratic:
            #     Hu^2 + Iu + (J-G) = 0
            # and then plug that u-value into the y-equation to get t.
            
            root1, root2 = mathutilities.quadratic(H, I, J - G)
            
            if not ZE(root1.imag):
                return ()
            
            v = []
            
            for u in (root1, root2):
                if CES(u):
                    # a possible solution
                    t = (C * u * u + D * u + E - B) / A
                    
                    if CES(t):
                        # an actual solution
                        v.append(theLine.pointFromParametricValue(t))
            
            return tuple(v)
        
        # If we get here, both A and F are nonzero, so we solve the full
        # quadratic:
        #
        #    (CF-AH)u^2 + (DF-AI)u + (EF+AG-AJ-BF) = 0
        #
        # and then plug that u-value into the y-equation to get t.
        
        root1, root2 = mathutilities.quadratic(
          C * F - A * H,
          D * F - A * I,
          E * F + A * G - A * J - B * F)
        
        if not ZE(root1.imag):
            return ()
        
        v = []
        
        for u in (root1, root2):
            if CES(u):
                # a possible solution
                t = (C * u * u + D * u + E - B) / A
                
                if CES(t):
                    # an actual solution
                    v.append(theLine.pointFromParametricValue(t))
        
        return tuple(v)
    
    def area(self):
        """
        Analytical solution for the area bounded by the parabolic section and
        the straight line.
        
        >>> P = point.Point
        >>> round(BSpline(P(2, -3), P(4, 4), P(0, 1)).area(), 10)
        20.6666666667
        >>> P = point.Point
        
        >>> print(BSpline(P(2, -3), P(4, 4), None).area())
        0
        
        >>> print(BSpline(P(2, -3), P(4, 4), P(4, 4)).area())
        Traceback (most recent call last):
          ...
        ZeroDivisionError: division by zero
        
        >>> print(BSpline(P(2, -3), P(2, -3), P(3, 4)).area())
        0
        """
        
        if self.offCurve is None:
            return 0
        
        if self.onCurve1.equalEnough(self.onCurve2):
            return 0
        
        normalized = self.moved(-self.onCurve1.x, -self.onCurve1.y)
        x1, y1 = normalized.offCurve.x, normalized.offCurve.y
        x2, y2 = normalized.onCurve2.x, normalized.onCurve2.y
        slopeDenom = x2 * (y2 - 2 * y1) - y2 * (x2 - 2 * x1)
        # assert slopeDenom, "Zero slope denominator in BSpline.area!"
        tangentT = (y2 * x1 - x2 * y1) / slopeDenom
        tangentPoint = normalized.pointFromParametricValue(tangentT)
        
        t = triangle.Triangle(
          self.onCurve1,
          tangentPoint,
          self.onCurve2)
        
        return 4 * t.area() / 3
    
    def bounds(self):
        """
        Returns a Rectangle representing the actual curve bounds. This might be
        different than the extrema.
        
        >>> P = point.Point
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)).extrema())
        Minimum X = 0, Minimum Y = -3, Maximum X = 4, Maximum Y = 4
        
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)).bounds())
        Minimum X = 1.3333333333333335, Minimum Y = -3, Maximum X = 4, Maximum Y = 4
        
        >>> print(BSpline(P(2, -3), P(4, 4), None).bounds())
        Minimum X = 2, Minimum Y = -3, Maximum X = 4, Maximum Y = 4
        
        >>> print(BSpline(P(4, 4), P(4, 4), P(2, 4)).bounds())
        Minimum X = 4, Minimum Y = 4, Maximum X = 4, Maximum Y = 4
        
        >>> print(BSpline(P(2, 3.1), P(2, 3.11), P(2,3.105)).bounds())
        Minimum X = 2, Minimum Y = 3.1, Maximum X = 2, Maximum Y = 3.11
        
        >>> print(BSpline(P(10, 5.1), P(12, 3.11), P(-2,1.105)).bounds())
        Minimum X = 4.461538461538462, Minimum Y = 2.439995833333333, Maximum X = 12, Maximum Y = 5.1
        """
        
        # We determine the bounds in x by differentiating the curve and finding
        # out where the slope zeroes out. Let a = self.onCurve1.x,
        # b = self.onCurve2.x, and c = self.offCurve.x. The equation for the
        # curve in x is:
        #
        # x = a(1-t)^2 + 2ct(1-t) + bt^2
        #
        # Refactoring this into terms involving t, we get:
        #
        # x = (a+b-2c)t^2 + (2c-2a)t + a
        #
        # Differentiating this with respect to t gets us:
        #
        # x' = 2(a+b-2c)t + (2c-2a)
        #
        # When x' is zero the curve is vertical. Solving, we get:
        #
        # t = (a-c)/(a+b-2c)
        #
        # If the denominator is zero then there are no vertical tangents. If t
        # is not in [0,1] then there are no vertical tangents. In both of these
        # cases the endpoints will provide the bounds.
        #
        # If, on the other hand, t exists and is in [0,1] then we need to plug
        # that value for t back into the original equation to get the
        # corresponding value of x.
        #
        # The same logic applies, mutatis mutandis, to y.
        
        extremaRect = self.extrema(True)
        
        if self.offCurve is None:
            return extremaRect
        
        if self.onCurve1.equalEnough(self.onCurve2):
            return extremaRect
        
        xMin, yMin, xMax, yMax = extremaRect.asList()
        a = self.onCurve1.x
        b = self.onCurve2.x
        c = self.offCurve.x
        denom = a + b - (2 * c)
        
        if denom:
            t = (a - c) / denom
            
            if mathutilities.closeEnoughSpan(t):
                p = self.pointFromParametricValue(t)
                xMin = min(xMin, p.x)
                xMax = max(xMax, p.x)
        
        a = self.onCurve1.y
        b = self.onCurve2.y
        c = self.offCurve.y
        denom = a + b - (2 * c)
        
        if denom:
            t = (a - c) / denom
            
            if mathutilities.closeEnoughSpan(t):
                p = self.pointFromParametricValue(t)
                yMin = min(yMin, p.y)
                yMax = max(yMax, p.y)
        
        return rectangle.Rectangle(xMin, yMin, xMax, yMax)
    
    def distanceToPoint(self, p):
        """
        Returns an unsigned distance from the point to the nearest position on
        the curve.
        
        >>> P = point.Point
        >>> obj = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(obj.distanceToPoint(P(3, 3)))
        0.10068277482538779
        >>> print(BSpline(P(2, -3), P(4, 4), None).distanceToPoint(P(2,-3)))
        0.0
        >>> print(BSpline(P(4, 4), P(4, 4), P(2, 4)).distanceToPoint(P(2,-3)))
        7.280109889280518
        """
        
        if self.onCurve1.equalEnough(self.onCurve2):
            return p.distanceFrom(self.onCurve1)
        
        if self.offCurve is None:
            return line.Line(self.onCurve1, self.onCurve2).distanceToPoint(p)
        
        a = self.onCurve1.x
        b = self.onCurve2.x
        c = self.offCurve.x
        d = self.onCurve1.y
        e = self.onCurve2.y
        f = self.offCurve.y
        A = a + b - 2 * c
        B = c - a
        C = d + e - 2 * f
        D = f - d
        E = a - p.x
        F = d - p.y
        
        roots = mathutilities.cubic(
          4 * (A * A + C * C),
          12 * (A * B + C * D),
          4 * (2 * B * B + 2 * D * D + A * E + C * F),
          4 * (B * E + D * F))
        
        ZE = mathutilities.zeroEnough
        
        v = [
          p.distanceFrom(self.pointFromParametricValue(root))
          for root in roots
          if ZE(root.imag)]
        
        return utilities.safeMin(v)
    
    def extrema(self, excludeOffCurve=False):
        """
        Returns a Rectangle representing the extrema (based on the actual
        coordinates, and not the curve itself). Normally the off-curve point is
        included in the calculations; to exclude it, set the excludeOffCurve
        flag to True.
        
        Note that you can check whether one or more extreme points are off-
        curve by comparing the results of this method with True and False as
        the flags -- if the resulting Rectangles differ, then at least one of
        the extreme points is off-curve.
        
        >>> P = point.Point
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)).extrema())
        Minimum X = 0, Minimum Y = -3, Maximum X = 4, Maximum Y = 4
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)).extrema(True))
        Minimum X = 2, Minimum Y = -3, Maximum X = 4, Maximum Y = 4
        """
        
        if self.offCurve is None or self.onCurve1.equalEnough(self.onCurve2):
            return rectangle.Rectangle.frompoints(self.onCurve1, self.onCurve2)
        
        if excludeOffCurve:
            return rectangle.Rectangle(
              min(self.onCurve1.x, self.onCurve2.x),
              min(self.onCurve1.y, self.onCurve2.y),
              max(self.onCurve1.x, self.onCurve2.x),
              max(self.onCurve1.y, self.onCurve2.y))
        
        return rectangle.Rectangle(
          min(self.onCurve1.x, self.onCurve2.x, self.offCurve.x),
          min(self.onCurve1.y, self.onCurve2.y, self.offCurve.y),
          max(self.onCurve1.x, self.onCurve2.x, self.offCurve.x),
          max(self.onCurve1.y, self.onCurve2.y, self.offCurve.y))
    
    def intersection(self, other):
        """
        Returns a tuple of objects representing the intersection of the two
        BSplines.
        
        >>> P = point.Point
        >>> b1 = BSpline(P(2, -3), P(4, 4), None)
        >>> b2 = BSpline(P(1, 0), P(4, -1), None)
        >>> for obj in b1.intersection(b2): print(obj)
        (2.6956521739130435, -0.5652173913043479)
        >>> for obj in b1.intersection(b2.moved(10)): print(obj)
        
        >>> b3 = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> for obj in b3.intersection(b2): print(obj)
        (1.345578690319357, -0.11519289677311899)
        
        >>> for obj in b2.intersection(b3): print(obj)
        (1.345578690319357, -0.11519289677311899)
        
        >>> for obj in b3.intersection(b2.moved(10)): print(obj)
        
        >>> for obj in b3.intersection(b1.moved(-1)): print(obj)
        (2.6484772346100725, 2.7696703211352536)
        (1.4424318562990182, -1.4514885029534366)
        
        >>> b4 = BSpline(P(-2, 0), P(2, 0), P(0, 2))
        >>> for obj in b4.intersection(b3): print(obj)
        (1.4334792522721553, 0.4862843083263152)
        
        >>> b5 = BSpline(P(0, 3), P(0, -3), P(3, 0))
        >>> for obj in b5.intersection(b3): print(obj)
        (1.448865608003318, 0.553901030852897)
        (1.3583316809062103, -0.92195982264009)
        
        >>> b6 = BSpline(P(2, -3), P(2, -3), None)
        >>> b7 = BSpline(P(1, 0), P(4, -1), None)
        >>> b8 = BSpline(P(0, 0), P(10, 10), P(5,5))
        >>> b9 = BSpline(P(2.1, 1), P(20, 20), P(5,5))
        >>> b6.intersection(b7)
        ()
        >>> b7.intersection(b6)
        ()
        >>> b8.intersection(b9)
        ()
        """
        
        if self.onCurve1.equalEnough(self.onCurve2):
            t = other.parametricValueFromPoint(self.onCurve1)
            return (() if t is None else (self.onCurve1,))
        
        if other.onCurve1.equalEnough(other.onCurve2):
            t = self.parametricValueFromPoint(other.onCurve1)
            return (() if t is None else (other.onCurve1,))
        
        self = self.normalized()
        other = other.normalized()
        CEXY = mathutilities.closeEnoughXY
        
        if self.offCurve is None and other.offCurve is None:
            # actually a line intersection case
            L1 = line.Line(self.onCurve1, self.onCurve2)
            L2 = line.Line(other.onCurve1, other.onCurve2)
            isect = L1.intersection(L2)
            return (() if isect is None else (isect,))
        
        if self.offCurve is None or other.offCurve is None:
            
            # one is a line and one is a curve. check endpoints first.
            
            if (
              CEXY(self.onCurve1, other.onCurve1) or
              CEXY(self.onCurve1, other.onCurve2)):
                
                return (self.onCurve1.__copy__(),)
            
            if (
              CEXY(self.onCurve2, other.onCurve1) or
              CEXY(self.onCurve2, other.onCurve2)):
                
                return (self.onCurve2.__copy__(),)
            
            if self.offCurve is None:
                # self is line and other is curve; from 0-2 intersection points
                return other._intersection_line(
                  line.Line(self.onCurve1, self.onCurve2))
            
            # other is line and self is curve; from 0-2 intersection points
            return self._intersection_line(
              line.Line(other.onCurve1, other.onCurve2))
        
        if CEXY(self.offCurve, other.offCurve):
            # If the two off-curve points coincide, then we check to see if
            # other's start and end points lie on self. If they do, the curves
            # overlap.
            
            tStart = self.parametricValueFromPoint(other.onCurve1)
            
            if tStart is not None:
                tEnd = self.parametricValueFromPoint(other.onCurve2)
                
                if tEnd is not None:
                    return (self.piece(
                      max(0, tStart),
                      min(1, tEnd))[0],)  # don't need the function
        
        if CEXY(self.onCurve1, other.onCurve1) or CEXY(self.onCurve1, other.onCurve2):
            return (self.onCurve1.__copy__(),)
        
        if CEXY(self.onCurve2, other.onCurve1) or CEXY(self.onCurve2, other.onCurve2):
            return (self.onCurve2.__copy__(),)
        
        # At this point we know it's a full curve/curve intersection, so the
        # possible results are 0-2 points
        
        ZE = mathutilities.zeroEnough
        A = self.onCurve1.x + self.onCurve2.x - (2 * self.offCurve.x)
        B = 2 * (self.offCurve.x - self.onCurve1.x)
        G = self.onCurve1.y + self.onCurve2.y - (2 * self.offCurve.y)
        H = 2 * (self.offCurve.y - self.onCurve1.y)
        
        assert not (ZE(A) and ZE(G))  # linear case already handled
        
        if ZE(A):
            return self._intersection_curve_xspecial(other)
        
        if ZE(G):
            return self._intersection_curve_yspecial(other)
        
        if ZE(B * G - A * H):
            return other.intersection(self)
        
        return self._intersection_curve(other)
    
    def magnified(self, xScale=1, yScale=1):
        """
        Returns a new BSpline scaled as specified about the origin.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.magnified(-2.5, 0.75))
        Curve from (-5.0, -2.25) to (-10.0, 3.0) with off-curve point (-0.0, 0.75)
        >>> c = BSpline(P(2, -3), P(4, 4), None)
        >>> print(c.magnified(5, -5))
        Line from (10, 15) to (20, -20)
        """
        
        if self.offCurve is None:
            return type(self)(
              self.onCurve1.magnified(xScale, yScale),
              self.onCurve2.magnified(xScale, yScale),
              None)
        
        return type(self)(
          self.onCurve1.magnified(xScale, yScale),
          self.onCurve2.magnified(xScale, yScale),
          self.offCurve.magnified(xScale, yScale))
    
    def magnifiedAbout(self, about, xScale=1, yScale=1):
        """
        Returns a new BSpline scaled as specified about a specified point.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.magnifiedAbout(P(1, -1), -2.5, 0.75))
        Curve from (-1.5, -2.5) to (-6.5, 2.75) with off-curve point (3.5, 0.5)
        >>> c = BSpline(P(2, -3), P(4, 4), None)
        >>> print(c.magnifiedAbout(P(-1,3), 5, -5))
        Line from (14, 33) to (24, -2)
        """
        
        if self.offCurve is None:
            return type(self)(
              self.onCurve1.magnifiedAbout(about, xScale, yScale),
              self.onCurve2.magnifiedAbout(about, xScale, yScale),
              None)
        
        return type(self)(
          self.onCurve1.magnifiedAbout(about, xScale, yScale),
          self.onCurve2.magnifiedAbout(about, xScale, yScale),
          self.offCurve.magnifiedAbout(about, xScale, yScale))
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new BSpline moved by the specified amount.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.moved(-2, 3))
        Curve from (0, 0) to (2, 7) with off-curve point (-2, 4)
        """
        
        if self.offCurve is None:
            return type(self)(
              self.onCurve1.moved(deltaX, deltaY),
              self.onCurve2.moved(deltaX, deltaY),
              None)
        
        return type(self)(
          self.onCurve1.moved(deltaX, deltaY),
          self.onCurve2.moved(deltaX, deltaY),
          self.offCurve.moved(deltaX, deltaY))
    
    def normal(self):
        """
        Returns a new BSpline of unit length, starting from the point on the
        curve corresponding to a t-value of 0.5, and moving in a direction
        orthogonal to the tangent at that point, outwards (i.e. away from the
        line from self.onCurve1 to self.onCurve2).
        
        >>> P = point.Point
        >>> print(BSpline(P(2, -3), P(4, 4), P(0, 1)).normal())
        Line from (1.5, 0.75) to (0.5384760523591766, 1.0247211278973771)
        """
        
        startPt = self.pointFromParametricValue(0.5)
        refLine = line.Line(self.onCurve1, self.onCurve2)
        tProj = refLine.parametricValueFromProjectedPoint(startPt)
        tProjPt = refLine.pointFromParametricValue(tProj)
        unnormEndPt = (startPt * 2) - tProjPt
        unnormLine = line.Line(startPt, unnormEndPt)
        return unnormLine.normalized()
    
    def normalized(self):
        """
        If self.offCurve is None, or if self.offCurve is not None and lies
        legitimately off the line from self.onCurve1 to self.onCurve2, then
        self is returned. Otherwise, a new BSpline is created with the off-
        curve point set appropriately.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.normalized())
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        
        >>> b = BSpline(P(0, 0), P(10, 10), P(5, 5))
        >>> print(b)
        Curve from (0, 0) to (10, 10) with off-curve point (5, 5)
        >>> print(b.normalized())
        Line from (0, 0) to (10, 10)
        
        We also need to normalize the cases where the off-curve point is
        co-linear with the two on-curve points, but has a parametric value
        less than zero or greater than one:
        
        >>> print(BSpline(P(5, 5), P(10, 10), P(0, 0)).normalized())
        Line from (0, 0) to (10, 10)
        >>> print(BSpline(P(0,0), P(10, 10), P(5,5)).normalized())
        Line from (0, 0) to (10, 10)
        >>> print(BSpline(P(0,0), P(10, 10), P(9.0001,10.0001)).normalized())
        Curve from (0, 0) to (10, 10) with off-curve point (9.0001, 10.0001)
        """
        
        if self.offCurve is None or self.onCurve1.equalEnough(self.onCurve2):
            return self
        
        L = line.Line(self.onCurve1, self.onCurve2)
        t = L.parametricValueFromPoint(self.offCurve)
        
        if t is None:
            return self
        
        # If we get here, the supposed off-curve point is actually colinear
        # with the two on-curve points, so it's a straight line and needs to
        # reflect that fact.
        
        if mathutilities.closeEnoughSpan(t):
            return type(self)(self.onCurve1, self.onCurve2, None)
        
        if t < 0:
            return type(self)(self.offCurve, self.onCurve2, None)
        
        return type(self)(self.onCurve1, self.offCurve, None)
    
    def parametricValueFromPoint(self, p):
        """
        Given a Point p, find the parametric value t which corresponds to the
        point along the curve. Returns None if the point does not lie on the
        curve.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b.parametricValueFromPoint(b.pointFromParametricValue(0)))
        0
        >>> print(b.parametricValueFromPoint(b.pointFromParametricValue(1)))
        1
        >>> print(b.parametricValueFromPoint(b.pointFromParametricValue(0.5)))
        0.5
        
        >>> m = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b.parametricValueFromPoint(b.pointFromParametricValue(0)))
        0
        
        >>> b = BSpline(P(5, 5), P(10, 10), None)
        >>> print(b.parametricValueFromPoint(P(0, 0)))
        -1.0
        """
        
        if self.offCurve is None:
            theLine = line.Line(self.onCurve1, self.onCurve2)
            return theLine.parametricValueFromPoint(p)
        
        a = self.onCurve1.x + self.onCurve2.x - 2 * self.offCurve.x
        b = 2 * (self.offCurve.x - self.onCurve1.x)
        c = self.onCurve1.x - p.x
        
        if a:
            tx1, tx2 = mathutilities.quadratic(a, b, c)
        elif b:
            tx1 = tx2 = -c / b
        else:
            """           
            >>> d = BSpline(P(1, 5), P(1, 10), P(1,-5))
            >>> print(d.parametricValueFromPoint(P(0, 0)))
            None
            >>> e = BSpline(P(-9, 5), P(1, 10), P(-1,-5))
            >>> print(e.parametricValueFromPoint(P(0, 0)))
            None
            """
            return (None if c else 0)
        
        if tx1.imag:
            return None
        
        a = self.onCurve1.y + self.onCurve2.y - 2 * self.offCurve.y
        b = 2 * (self.offCurve.y - self.onCurve1.y)
        c = self.onCurve1.y - p.y
        
        if a:
            ty1, ty2 = mathutilities.quadratic(a, b, c)
        elif b:
            ty1 = ty2 = -c / b
        else:
            """
            >>> c = BSpline(P(5, 1), P(10, 1), P(-5,1))
            >>> print(c.parametricValueFromPoint(P(0, 0)))
            None
            """
            return (None if c else 0)
        
        CE = mathutilities.closeEnough
        
        if CE(tx1, ty1) or CE(tx1, ty2):
            return tx1
        
        if CE(tx2, ty1) or CE(tx2, ty2):
            return tx2
        
        return None
    
    def piece(self, t1, t2):
        """
        Create a new b-spline mapping the original parametric values in the
        range t1 to t2 into new values from 0 to 1.

        Returns two things: the new b-spline, and an anonymous function which
        maps an old t-value (i.e. a value in the range from t1 through t2) onto
        a new u-value from 0 through 1.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> bNew, f = b.piece(0.25, 0.75)
        >>> print(bNew)
        Curve from (1.375, -1.0625) to (2.375, 2.4375) with off-curve point (1.125, 0.8125)
        >>> for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        ...   tNew = f(t)
        ...   print(b.pointFromParametricValue(t), bNew.pointFromParametricValue(tNew))
        (2.0, -3.0) (2.0, -3.0)
        (1.375, -1.0625) (1.375, -1.0625)
        (1.5, 0.75) (1.5, 0.75)
        (2.375, 2.4375) (2.375, 2.4375)
        (4.0, 4.0) (4.0, 4.0)
        >>> c = BSpline(P(2, -3), P(4, 4), None)
        >>> c.piece(0,10)[0].pprint()
        onCurve1:
          0: 2.0
          1: -3.0
        onCurve2:
          0: 22.0
          1: 67.0
        offCurve: (no data)
        
        >>> c.piece(100,-10)[0].pprint()
        onCurve1:
          0: -18.0
          1: -73.0
        onCurve2:
          0: 202.0
          1: 697.0
        offCurve: (no data)
        """
        
        if t1 > t2:
            t1, t2 = t2, t1
        
        newP0 = self.pointFromParametricValue(t1)
        newP2 = self.pointFromParametricValue(t2)
        
        if self.offCurve is None:
            # linear case
            newSpline = BSpline(newP0, newP2)
        
        else:
            # quadratic case
            newP1 = self.pointFromParametricValue((t1 + t2) / 2)
            newP1x = 2 * (newP1.x - 0.25 * (newP0.x + newP2.x))
            newP1y = 2 * (newP1.y - 0.25 * (newP0.y + newP2.y))
            newSpline = BSpline(newP0, newP2, point.Point(newP1x, newP1y))
        
        return newSpline, lambda x: ((x - t1) / (t2 - t1))
    
    def pointFromParametricValue(self, t):
        """
        Given a parametric value t, where t=0 maps to self.onCurve1 and t=1
        maps to self.onCurve2, returns a Point representing that value.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b.pointFromParametricValue(0))
        (2, -3)
        >>> print(b.pointFromParametricValue(1))
        (4, 4)
        >>> print(b.pointFromParametricValue(0.5))
        (1.5, 0.75)
        """
        
        if self.offCurve is None:
            # linear case
            x = (t * self.onCurve2.x) + ((1.0 - t) * self.onCurve1.x)
            y = (t * self.onCurve2.y) + ((1.0 - t) * self.onCurve1.y)
        
        else:
            # quadratic case
            factor0 = (1 - t) ** 2
            factor1 = 2 * t * (1 - t)
            factor2 = t * t
            
            x = (
              (factor0 * self.onCurve1.x) +
              (factor1 * self.offCurve.x) +
              (factor2 * self.onCurve2.x))
            
            y = (
              (factor0 * self.onCurve1.y) +
              (factor1 * self.offCurve.y) +
              (factor2 * self.onCurve2.y))
        
        return point.Point(x, y)
    
    def rotated(self, angleInDegrees=0):
        """
        Returns a new BSpline scaled as specified about the origin.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.rotated(90))
        Curve from (3.0, 2.0) to (-4.0, 4.0) with off-curve point (-1.0, 0.0)
        """
        
        if self.offCurve is None:
            return type(self)(
              self.onCurve1.rotated(angleInDegrees),
              self.onCurve2.rotated(angleInDegrees),
              None)
        
        return type(self)(
          self.onCurve1.rotated(angleInDegrees),
          self.onCurve2.rotated(angleInDegrees),
          self.offCurve.rotated(angleInDegrees))
    
    def rotatedAbout(self, about, angleInDegrees=0):
        """
        Returns a new BSpline scaled as specified about a specified point.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b)
        Curve from (2, -3) to (4, 4) with off-curve point (0, 1)
        >>> print(b.rotatedAbout(P(1, -1), 90))
        Curve from (3.0, 0.0) to (-4.0, 2.0) with off-curve point (-1.0, -2.0)
        """
        
        if self.offCurve is None:
            return type(self)(
              self.onCurve1.rotatedAbout(about, angleInDegrees),
              self.onCurve2.rotatedAbout(about, angleInDegrees),
              None)
        
        return type(self)(
          self.onCurve1.rotatedAbout(about, angleInDegrees),
          self.onCurve2.rotatedAbout(about, angleInDegrees),
          self.offCurve.rotatedAbout(about, angleInDegrees))
    
    def slopeFromParametricValue(self, t):
        """
        Returns the slope of the curve at parametric value t.
        
        >>> P = point.Point
        >>> b = BSpline(P(2, -3), P(4, 4), P(0, 1))
        >>> print(b.slopeFromParametricValue(0))
        -2.0
        >>> print(b.slopeFromParametricValue(0.5))
        3.5
        >>> print(b.slopeFromParametricValue(1))
        0.75
        """
        
        # The slope is dy/dx, which can be expressed parametrically by:
        #
        # dy/dx = dy/dt divided by dx/dt
        #
        # Let a=onCurve1.x, b=offCurve.x, and c=onCurve2.x. The parametric
        # equation for x in terms of t is:
        #
        # x = a(1-t)^2 + 2bt(1-t) + ct^2
        #
        # Expanding and differentiating with respect to t, we get:
        #
        # dx/dt = 2(a+c-2b)t + 2(b-a)
        #
        # Using d, e, and f for analogous equations in y, we get:
        #
        # dy/dt = 2(d+f-2e)t + 2(e-d)
        #
        # Dividing dy/dt by dx/dt gives us the result.
        
        if self.offCurve is None:
            return line.Line(self.onCurve1, self.onCurve2).slope()
        
        a = self.onCurve1.x
        b = self.offCurve.x
        c = self.onCurve2.x
        denom = (a + c - 2 * b) * t + (b - a)
        
        if mathutilities.zeroEnough(denom):
            return float("+inf")
        
        d = self.onCurve1.y
        e = self.offCurve.y
        f = self.onCurve2.y
        numer = (d + f - 2 * e) * t + (e - d)
        
        return numer / denom
    
    def transitions(self, xStart, xStop, yCoord, leftToRight):
        """
        Finds the intersection of self and the horizontal line segment defined
        by xStart, xStop, and yCoord, then for each point in the intersection
        determines whether the curve passes by left-to-right or right-to-left
        when looked at in the specified leftToRight orientation. See the
        doctest examples below for a sense of how this works.
        
        >>> P = point.Point
        >>> b = BSpline(P(0, 0), P(10, 0), P(5, 20))
        >>> print(b.transitions(0, 10, 4, True))
        {False: 1, True: 1}
        
        >>> print(b.transitions(0, 10, 4, False))
        {False: 1, True: 1}
        
        >>> print(b.transitions(5, 10, 4, True))
        {False: 0, True: 1}
        
        >>> print(b.transitions(5, 10, 4, False))
        {False: 1, True: 0}
        
        >>> print(b.transitions(0, 5, 4, True))
        {False: 1, True: 0}
        
        >>> print(b.transitions(0, 5, 4, False))
        {False: 0, True: 1}
        
        Note that tangent points are not considered intersections for the
        purposes of this method:
        
        >>> b = BSpline(P(0, 0), P(7, -1), P(7, 1))
        >>> print(b.transitions(0, 7, 1/3, True))
        {False: 0, True: 0}
        """
        
        ray = type(self)(
          onCurve1 = point.Point(xStart, yCoord),
          onCurve2 = point.Point(xStop, yCoord),
          offCurve = None)
        
        sects = self.intersection(ray)
        r = {False: 0, True: 0}
        CE = mathutilities.closeEnough
        
        for p in sorted(sects, reverse=(not leftToRight)):
            if isinstance(p, line.Line):
                continue
            
            t = self.parametricValueFromPoint(p)
            p2 = self.pointFromParametricValue(t - 0.001)
            p3 = self.pointFromParametricValue(t + 0.001)
            
            if CE(p2.y, p3.y):
                continue
            
            if p2.y > p3.y:
                r[leftToRight] += 1
            else:
                r[not leftToRight] += 1
        
        return r

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
