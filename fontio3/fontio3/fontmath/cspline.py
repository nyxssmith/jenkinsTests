#
# cspline.py
#
# Copyright © 2013, 2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for cubic b-splines.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.fontmath import line, mathutilities, point, rectangle

# -----------------------------------------------------------------------------

#
# Classes
#

class CSpline(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing cubic b-splines. These are simple collections of 4
    attributes, representing the start and end points and the two control
    points.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        start = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0)),
            attr_label = "Start point"),
        
        control0 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0)),
            attr_label = "First control point"),
        
        control1 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0)),
            attr_label = "Second control point"),
        
        end = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: point.Point(0, 0)),
            attr_label = "End point"))
    
    attrSorted = ('start', 'control0', 'control1', 'end')
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a nice string representation of the CSpline object.
        
        >>> for obj in _testingValues: print(obj)
        Curve from (1, 2) to (10, 7) with controls points (2, 6) and (5, 5)
        Curve from (1, 1) to (19, 1) with controls points (17, 9) and (3, 8)
        Line from (1, 1) to (5, 5)
        Curve from (4, 5.25) to (19, 13.25) with controls points (7, 6.25) and (12, 6.25)
        Curve from (1, 1) to (4, 1) with controls points (2, 10) and (3, -10)
        Curve from (1, 1) to (7, 12) with coincident control points at (4, 3)
        Point at (4, -3)
        """
        
        if self.start.equalEnough(self.end):
            return "Point at %s" % (self.start,)
        
        if self.isLine():
            return "Line from %s to %s" % (self.start, self.end)
        
        if self.control0.equalEnough(self.control1):
            return (
              "Curve from %s to %s with coincident control points at %s" %
              (self.start, self.end, self.control0))
        
        return (
          "Curve from %s to %s with controls points %s and %s" %
          (self.start, self.end, self.control0, self.control1))
    
    def _coefficients(self):
        """
        Returns a tuple with 8 elements, being the numeric factors in the
        expansion of self into the form:
        
            x(t) = At^3 + Bt^2 + Ct + D
            y(t) = Et^3 + Ft^2 + Gt + H
        
        That is, the tuple (A, B, C, D, E, F, G, H) is returned.
        
        >>> print(_testingValues[0]._coefficients())
        (0, 6, 3, 1, 8, -15, 12, 2)
        
        >>> print(_testingValues[1]._coefficients())
        (60, -90, 48, 1, 3, -27, 24, 1)
        
        >>> print(_testingValues[3]._coefficients())
        (0, 6, 9, 4, 8.0, -3.0, 3.0, 5.25)
        """
        
        return self._pointsToParameters(
          self.start.x,
          self.control0.x,
          self.control1.x,
          self.end.x,
          self.start.y,
          self.control0.y,
          self.control1.y,
          self.end.y)
    
    @staticmethod
    def _parametersToPoints(A, B, C, D, E, F, G, H):
        a = D
        b = (C + 3 * a) / 3
        c = (B + 6 * b - 3 * a) / 3
        d = A + a - 3 * b + 3 * c
        e = H
        f = (G + 3 * e) / 3
        g = (F + 6 * f - 3 * e) / 3
        h = E + e - 3 * f + 3 * g
        
        return (a, b, c, d, e, f, g, h)
    
    @staticmethod
    def _pointsToParameters(a, b, c, d, e, f, g, h):
        A = 3 * b - 3 * c + d - a
        B = 3 * a + 3 * c - 6 * b
        C = 3 * b - 3 * a
        D = a
        E = 3 * f - 3 * g + h - e
        F = 3 * e + 3 * g - 6 * f
        G = 3 * f - 3 * e
        H = e
        
        return (A, B, C, D, E, F, G, H)
    
    def area(self):
        """
        Analytical solution for the area bounded by the curve and the line
        connecting self.start and self.end. Note this is sign-sensitive, so the
        area might not be the value you might expect.
        
        >>> round(_testingValues[0].area(), 10)
        8.7
        >>> _testingValues[4].area()
        -1.5
        >>> _testingValues[2].area()
        12.0
        """
        
        width = self.end.x - self.start.x
        trapezoidArea = width * (self.start.y + self.end.y) / 2
        
        if self.isLine():
            return trapezoidArea
        
        A, B, C, D, E, F, G, H = self._coefficients()
        tY = (H, G, F, E)
        tX = (D, C, B, A)
        txDeriv = mathutilities.polyderiv(tX)
        tProd = mathutilities.polymul(tY, txDeriv)
        return sum(mathutilities.polyinteg(tProd)) - trapezoidArea
    
    def bounds(self):
        """
        Returns a Rectangle representing the actual bounds, based on the curve
        itself.
        
        >>> print(_testingValues[0].bounds())
        Minimum X = 1, Minimum Y = 2, Maximum X = 10, Maximum Y = 7
        
        >>> print(_testingValues[1].bounds())
        Minimum X = 1, Minimum Y = 1, Maximum X = 19, Maximum Y = 6.631236180096162
        
        >>> print(_testingValues[2].bounds())
        Minimum X = 1, Minimum Y = 1, Maximum X = 5, Maximum Y = 5
        """
        
        if self.isLine():
            return line.Line(self.start, self.end).bounds()
        
        extremaRect = self.extrema(True)
        a = self.start.x
        b = self.control0.x
        c = self.control1.x
        d = self.end.x
        e = self.start.y
        f = self.control0.y
        g = self.control1.y
        h = self.end.y
        ZE = mathutilities.zeroEnough
        CES = mathutilities.closeEnoughSpan
        
        # xZeroes are where dx/dt goes to zero (i.e. vertical tangents)
        xZeroes = mathutilities.quadratic(
          3 * (-a + 3 * b - 3 * c + d),
          2 * (3 * a - 6 * b + 3 * c),
          (-3 * a + 3 * b))
        
        xZeroes = [n for n in xZeroes if ZE(n.imag) if CES(n)]
        
        # yZeroes are where dy/dt goes to zero (i.e. horizontal tangents)
        yZeroes = mathutilities.quadratic(
          3 * (-e + 3 * f - 3 * g + h),
          2 * (3 * e - 6 * f + 3 * g),
          (-3 * e + 3 * f))
        
        yZeroes = [n for n in yZeroes if ZE(n.imag) if CES(n)]
        
        pX = [
          self.pointFromParametricValue(root)
          for root in xZeroes]
        
        pY = [
          self.pointFromParametricValue(root)
          for root in yZeroes
          if root not in xZeroes]
        
        vXMin = [extremaRect.xMin] + [p.x for p in pX]
        vXMax = [extremaRect.xMax] + [p.x for p in pX]
        vYMin = [extremaRect.yMin] + [p.y for p in pY]
        vYMax = [extremaRect.yMax] + [p.y for p in pY]
        
        return rectangle.Rectangle(
          min(vXMin),
          min(vYMin),
          max(vXMax),
          max(vYMax))
    
    def distanceToPoint(self, p):
        """
        Returns an unsigned distance from the point to the nearest position on
        the curve. This will perforce be a point normal to the curve, but as
        there may be several such, the distance returned will be the smallest.
        
        >>> P = point.Point
        >>> print(_testingValues[0].distanceToPoint(P(5, 3)))
        2.4471964319857658
        
        >>> print(_testingValues[1].distanceToPoint(P(10, 10)))
        3.3691151093862604
        
        >>> print(_testingValues[2].distanceToPoint(P(6,6)))
        0.0
        """
        
        if self.isLine():
            L = line.Line(self.start, self.end)
            return L.distanceToPoint(p)
        
        a = self.start.x
        b = self.control0.x
        c = self.control1.x
        d = self.end.x
        e = self.start.y
        f = self.control0.y
        g = self.control1.y
        h = self.end.y
        A = 3 * b - 3 * c + d - a
        B = 3 * a + 3 * c - 6 * b
        C = 3 * b - 3 * a
        D = 3 * f - 3 * g + h - e
        E = 3 * e + 3 * g - 6 * f
        F = 3 * f - 3 * e
        G = a - p.x
        H = e - p.y
        
        def sumPrime(t):
            return (
              6 * (A * A + D * D) * (t ** 5) +
              10 * (A * B + D * E) * (t ** 4) +
              4 * (B * B + E * E + 2 * A * C + 2 * D * F) * (t ** 3) +
              6 * (A * G + B * C + D * H + E * F) * (t * t) +
              2 * (C * C + F * F + 2 * B * G + 2 * E * H) * t +
              2 * (C * G + F * H))
        
        def sumDoublePrime(t):
            return (
              30 * (A * A + D * D) * (t ** 4) +
              40 * (A * B + D * E) * (t ** 3) +
              12 * (B * B + E * E + 2 * A * C + 2 * D * F) * (t * t) +
              12 * (A * G + B * C + D * H + E * F) * t +
              2 * (C * C + F * F + 2 * B * G + 2 * E * H))
        
        tReal = mathutilities.newton(sumPrime, sumDoublePrime, 0.5)
        
        # Now we remove this root from the quintic, leaving a quartic that can
        # be solved directly.
        
        factors = (
          2 * (C * G + F * H),
          2 * (C * C + F * F + 2 * B * G + 2 * E * H),
          6 * (A * G + B * C + D * H + E * F),
          4 * (B * B + E * E + 2 * A * C + 2 * D * F),
          10 * (A * B + D * E),
          6 * (A * A + D * D))
        
        reducedFactors = mathutilities.polyreduce(factors, tReal)
        roots = (tReal,) + mathutilities.quartic(*reversed(reducedFactors))
        ZE = mathutilities.zeroEnough
        
        v = [
          p.distanceFrom(self.pointFromParametricValue(root))
          for root in roots
          if ZE(root.imag)]
        
        return utilities.safeMin(v)
    
    def extrema(self, excludeOffCurve=False):
        """
        Returns a Rectangle representing the extrema (based on the actual point
        coordinates, and not the curve itself).
        
        >>> print(_testingValues[0].extrema())
        Minimum X = 1, Minimum Y = 2, Maximum X = 10, Maximum Y = 7
        
        >>> print(_testingValues[2].extrema())
        Minimum X = 1, Minimum Y = 1, Maximum X = 5, Maximum Y = 5
        """
        
        if self.isLine():
            return line.Line(self.start, self.end).extrema()
        
        if excludeOffCurve:
            ps = [self.start, self.end]
        else:
            ps = [self.start, self.control0, self.control1, self.end]
        
        return rectangle.Rectangle(
          min(p.x for p in ps),
          min(p.y for p in ps),
          max(p.x for p in ps),
          max(p.y for p in ps))
    
    def intersection(self, other, delta=1.0e-5):
        """
        Returns a tuple of objects representing the intersection of the two
        CSpline objects, usually Points but possibly a CSpline; empty if there
        is no intersection.
        
        We use Newton's method here to solve the nonlinear system:
        
            self_x(t) - other_x(u) = 0
            self_y(t) - other_y(u) = 0
        
        There is an admittedly ad hoc decision here to look at 25 different
        (t, u) pairs as starting values to find local solutions. This method
        has (so far) found all solutions for intersections I've thrown at it,
        including one case with 5 intersections, but this heuristic code should
        be rigorously tested.
        
        Also, the resulting t- and u-values are rounded to six places.
        
        >>> for obj in _testingValues[0].intersection(_testingValues[3]):
        ...     obj.pprint()
        Start point:
          0: 4.0
          1: 5.25
        First control point:
          0: 5.5
          1: 5.75
        Second control point:
          0: 7.5
          1: 6.0
        End point:
          0: 10.0
          1: 7.0
          
        >>> P = point.Point
        >>> a = CSpline(P(0, 0), P(3, 3), P(4, 4), P(6, 6))
        >>> for obj in _testingValues[2].intersection(a):
        ...   print(str(obj))
        Line from (1, 1) to (5, 5)

        >>> for obj in _testingValues[2].intersection(_testingValues[2]):
        ...   print(str(obj))
        Line from (1, 1) to (5, 5)
        
        >>> c = CSpline(P(0, 0), P(-1, 0), P(0, 0), P(0, 0))
        >>> print(_testingValues[2].intersection(c))
        ()
        """
        
        # Before we start working on potential point intersections, do a check
        # to see if the entire cubics overlap, or if they're both lines.
        
        selfLine = self.isLine()
        otherLine = other.isLine()
        
        if selfLine or otherLine:
            if selfLine and otherLine:
                L1 = line.Line(self.start, self.end)
                L2 = line.Line(other.start, other.end)
                sect = L1.intersection(L2, delta)
                
                if sect is None:
                    return ()
                
                return (sect,)
            
            if selfLine and (self.control0 is None and self.control1 is None):
                L1 = line.Line(self.start, self.end)
                
                self = type(self)(
                  self.start,
                  L1.midpoint(),
                  L1.midpoint(),
                  self.end)
            
            if otherLine and (other.control0 is None and other.control1 is None):
                L1 = line.Line(other.start, other.end)
                
                other = type(other)(
                  other.start,
                  L1.midpoint(),
                  L1.midpoint(),
                  other.end)
        
        pvsSelf = [0.0, 0.25, 0.5, 0.75, 1.0]
        pts = [self.pointFromParametricValue(n) for n in pvsSelf]
        pvsOther = [other.parametricValueFromPoint(pt) for pt in pts]
        ZE = mathutilities.zeroEnough
        
        if None not in pvsOther:
            diffs = [i - j for i, j in zip(pvsSelf, pvsOther)]
            
            if ZE(max(diffs) - min(diffs)):
                d = diffs[0]
                
                if not (ZE(d) or ZE(d - 1) or (0 < d < 1)):
                    return ()
                
                elif ZE(d):
                    return (self.__deepcopy__(),)
                
                elif d < 0:
                    return (self.piece(0, 1 + d)[0],)
                
                return (self.piece(d, 1)[0],)
        
        # If we get here, there is no overlap, so proceed with the actual
        # calculations.
        
        A, B, C, D, E, F, G, H = self._coefficients()
        S, T, U, V, W, X, Y, Z = other._coefficients()
        
        def func(v):  # maps a (u, v) pair to a distance in x and y
            t, u = v
            
            x = (
              A * (t ** 3)
              + B * t * t
              + C * t
              + D
              - S * (u ** 3)
              - T * u * u
              - U * u
              - V)
            
            y = (
              E * (t ** 3)
              + F * t * t
              + G * t
              + H
              - W * (u ** 3)
              - X * u * u
              - Y * u
              - Z)
    
            return [x, y]

        def Jacobian(t, u):
            e1 = 3 * A * t * t + 2 * B * t + C
            e2 = -3 * S * u * u - 2 * T * u - U
            e3 = 3 * E * t * t + 2 * F * t + G
            e4 = -3 * W * u * u - 2 * X * u - Y
            return [[e1, e2], [e3, e4]]
        
        def matInv(m):
            det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
            
            return [
              [m[1][1] / det, -m[0][1] / det],
              [-m[1][0] / det, m[0][0] / det]]
        
        def matMul(m, v):
            e1 = m[0][0] * v[0] + m[0][1] * v[1]
            e2 = m[1][0] * v[0] + m[1][1] * v[1]
            return [e1, e2]
        
        solutions = set()
        zeroDivCount = 0
        giveUpCount = 0
        
        for n1 in range(5):
            for n2 in range(5):
                n = [n1 / 4, n2 / 4]
                nPrior = [-1, -1]
                iterCount = 0
                okToProceed = True
                
                while (not ZE(n[0] - nPrior[0])) or (not ZE(n[1] - nPrior[1])):
                    try:
                        nDelta = matMul(matInv(Jacobian(*n)), func(n))
                    
                    except ZeroDivisionError:
                        zeroDivCount += 1
                        okToProceed = False
                    
                    if not okToProceed:
                        break
                    
                    nPrior = list(n)
                    n[0] -= nDelta[0]
                    n[1] -= nDelta[1]
                    iterCount += 1
                
                    if iterCount > 10:
                        giveUpCount += 1
                        okToProceed = False
                        break
                
                if okToProceed:
                    if not (ZE(n[0]) or ZE(n[0] - 1) or (0 < n[0] < 1)):
                        continue
                
                    if not (ZE(n[1]) or ZE(n[1] - 1) or (0 < n[1] < 1)):
                        continue
                
                    checkIt = func(n)
                
                    if (not ZE(checkIt[0])) or (not ZE(checkIt[1])):
                        continue
                
                    n = (round(n[0], 6), round(n[1], 6))
                    solutions.add(n)
        
        return tuple(
          self.pointFromParametricValue(obj[0])
          for obj in solutions)
    
    def isLine(self):
        """
        Returns True if the two control points are colinear with the start and
        end points (or are both None), False otherwise.
        
        >>> _testingValues[1].isLine()
        False
        
        >>> _testingValues[2].isLine()
        True
        """
        
        if self.control0 is None and self.control1 is None:
            return True
        
        L = line.Line(self.start, self.end)
        
        if L.parametricValueFromPoint(self.control0) is None:
            return False
        
        return L.parametricValueFromPoint(self.control1) is not None
    
    def magnified(self, xScale=1, yScale=1):
        """
        Returns a new CSpline scaled as specified about the origin.
        """
        
        if self.isLine():
            return type(self)(
              self.start.magnified(xScale, yScale),
              None,
              None,
              self.end.magnified(xScale, yScale))
        
        return type(self)(
          self.start.magnified(xScale, yScale),
          self.control0.magnified(xScale, yScale),
          self.control1.magnified(xScale, yScale),
          self.end.magnified(xScale, yScale))
    
    def magnifiedAbout(self, about, xScale=1, yScale=1):
        """
        Returns a new CSpline scaled as specified about the specified point.
        """
        
        if self.isLine():
            return type(self)(
              self.start.magnifiedAbout(about, xScale, yScale),
              None,
              None,
              self.end.magnifiedAbout(about, xScale, yScale))
        
        return type(self)(
          self.start.magnifiedAbout(about, xScale, yScale),
          self.control0.magnifiedAbout(about, xScale, yScale),
          self.control1.magnifiedAbout(about, xScale, yScale),
          self.end.magnifiedAbout(about, xScale, yScale))
    
    def moved(self, deltaX=0, deltaY=0):
        """
        Returns a new CSpline moved by the specified amount.
        """
        
        if self.isLine():
            return type(self)(
              self.start.moved(deltaX, deltaY),
              None,
              None,
              self.end.moved(deltaX, deltaY))
        
        return type(self)(
          self.start.moved(deltaX, deltaY),
          self.control0.moved(deltaX, deltaY),
          self.control1.moved(deltaX, deltaY),
          self.end.moved(deltaX, deltaY))
    
    def parametricValueFromPoint(self, p):
        """
        Returns the parametric t-value for the specified point p, or None if p
        does not lie on the spline.
        
        >>> obj = _testingValues[0]
        >>> print(obj.parametricValueFromPoint(point.Point(1, 2)))
        0
        
        >>> print(obj.parametricValueFromPoint(point.Point(10, 7)))
        1
        
        >>> print(obj.parametricValueFromPoint(point.Point(4, 5.25)))
        0.5
        
        >>> print(obj.parametricValueFromPoint(point.Point(4, -5.25)))
        None
        """
        
        if self.isLine():
            L = line.Line(self.start, self.end)
            return L.parametricValueFromPoint(p)
        
        a = self.start.x
        b = self.control0.x
        c = self.control1.x
        d = self.end.x
        
        roots = mathutilities.cubic(
          (-a + 3 * b - 3 * c + d),
          (3 * a - 6 * b + 3 * c),
          (-3 * a + 3 * b),
          (a - p.x))
        
        # Check that the y-value for real roots is sufficiently close
        
        for root in roots:
            if not mathutilities.zeroEnough(root.imag):
                continue
            
            pTest = self.pointFromParametricValue(root)
            
            if mathutilities.closeEnough(p.y, pTest.y):
                return root
        
        return None
    
    def piece(self, t1, t2):
        """
        Create and return a new CSpline object which maps t1 to t2 in the
        original to 0 to 1 in the new.
        
        Returns two things: the new CSpline, and an anonymous function which
        maps an old t-value to a new u-value.
        
        >>> origObj = _testingValues[0]
        >>> origObj.pprint()
        Start point:
          0: 1
          1: 2
        First control point:
          0: 2
          1: 6
        Second control point:
          0: 5
          1: 5
        End point:
          0: 10
          1: 7
        >>> newObj, f = origObj.piece(0.25, 0.75)
        >>> newObj.pprint()
        Start point:
          0: 2.125
          1: 4.1875
        First control point:
          0: 3.125
          1: 5.1875
        Second control point:
          0: 4.625
          1: 5.4375
        End point:
          0: 6.625
          1: 5.9375
        >>> print(origObj.pointFromParametricValue(0.25))
        (2.125, 4.1875)
        >>> print(newObj.pointFromParametricValue(0))
        (2.125, 4.1875)
        >>> print(origObj.pointFromParametricValue(0.75))
        (6.625, 5.9375)
        >>> print(newObj.pointFromParametricValue(1))
        (6.625, 5.9375)
        """
        
        if self.isLine():
            return line.Line(self.start, self.end).piece(t1, t2)
        
        A, B, C, D, E, F, G, H = self._coefficients()
        
        if t1 > t2:
            t1, t2 = t2, t1
        
        a = t2 - t1
        b = t1
        A2 = A * (a ** 3)
        B2 = 3 * A * a * a * b + B * a * a
        C2 = 3 * A * a * b * b + 2 * B * a * b + C * a
        D2 = A * (b ** 3) + B * b * b + C * b + D
        E2 = E * (a ** 3)
        F2 = 3 * E * a * a * b + F * a * a
        G2 = 3 * E * a * b * b + 2 * F * a * b + G * a
        H2 = E * (b ** 3) + F * b * b + G * b + H
        pVec = self._parametersToPoints(A2, B2, C2, D2, E2, F2, G2, H2)
        
        newSpline = type(self)(
          point.Point(pVec[0], pVec[4]),
          point.Point(pVec[1], pVec[5]),
          point.Point(pVec[2], pVec[6]),
          point.Point(pVec[3], pVec[7]))
        
        return newSpline, lambda x: ((x - t1) / (t2 - t1))
    
    def pointFromParametricValue(self, t):
        """
        Returns a Point representing the specified parametric value.
        
        >>> obj = _testingValues[0]
        >>> print(obj.pointFromParametricValue(0))
        (1, 2)
        
        >>> print(obj.pointFromParametricValue(1))
        (10, 7)
        
        >>> print(obj.pointFromParametricValue(0.5))
        (4.0, 5.25)
        
        >>> print(obj.pointFromParametricValue(0.25))
        (2.125, 4.1875)
        
        >>> print(obj.pointFromParametricValue(1.5))
        (19.0, 13.25)
        
        >>> print(obj.pointFromParametricValue(-0.75))
        (2.125, -18.8125)
        """
        
        if self.isLine():
            L = line.Line(self.start, self.end)
            return L.pointFromParametricValue(t)
        
        if t == 0:
            return self.start
        
        if t == 1:
            return self.end
        
        a = self.start.x
        b = self.control0.x
        c = self.control1.x
        d = self.end.x
        e = self.start.y
        f = self.control0.y
        g = self.control1.y
        h = self.end.y
        
        x = (
          (-a + 3 * b - 3 * c + d) * (t ** 3) +
          (3 * a - 6 * b + 3 * c) * (t ** 2) +
          (-3 * a + 3 * b) * t +
          a)
        
        y = (
          (-e + 3 * f - 3 * g + h) * (t ** 3) +
          (3 * e - 6 * f + 3 * g) * (t ** 2) +
          (-3 * e + 3 * f) * t +
          e)
        
        return point.Point(x, y)
    
    def rotated(self, angleInDegrees=0):
        """
        Returns a new CSpline rotated as specified about the origin.
        """
        
        if self.isLine():
            return type(self)(
              self.start.rotated(angleInDegrees),
              None,
              None,
              self.end.rotated(angleInDegrees))
        
        return type(self)(
          self.start.rotated(angleInDegrees),
          self.control0.rotated(angleInDegrees),
          self.control1.rotated(angleInDegrees),
          self.end.rotated(angleInDegrees))
    
    def rotatedAbout(self, about, angleInDegrees=0):
        """
        Returns a new CSpline rotated as specified about the specified point.
        """
        
        if self.isLine():
            return type(self)(
              self.start.rotatedAbout(about, angleInDegrees),
              None,
              None,
              self.end.rotatedAbout(about, angleInDegrees))
        
        return type(self)(
          self.start.rotatedAbout(about, angleInDegrees),
          self.control0.rotatedAbout(about, angleInDegrees),
          self.control1.rotatedAbout(about, angleInDegrees),
          self.end.rotatedAbout(about, angleInDegrees))
    
    def slopeFromParametricValue(self, t):
        """
        Returns the slope of the curve at the parametric value t.
        
        >>> obj = _testingValues[0]
        >>> print(obj.slopeFromParametricValue(0))
        4.0
        >>> print(obj.slopeFromParametricValue(1))
        0.4
        """
        
        ZE = mathutilities.zeroEnough
        
        if self.isLine():
            # The slope is constant in this case
            p1, p2 = self.start, self.end
            
            if ZE(p2.x - p1.x):
                return float("+inf")
            
            return (p2.y - p1.y) / (p2.x - p1.x)
        
        # Let a, b, c, d be the x-coordinates, in order.
        # Then x = a(1-t)^3 + 3bt(1-t)^2 + 3ct^2(1-t) + dt^3
        # So x = 
        #   (-a + 3b - 3c + d)t^3 +
        #   (3a - 6b + 3c)t^2 +
        #   (-3a + 3b)t +
        #   a
        #
        # Similarly, for e, f, g, h as the y-analogs, we get:
        # y =
        #   (-e + 3f - 3g + h)t^3 +
        #   (3e - 6f + 3g)t^2 +
        #   (-3e + 3f)t +
        #   e
        #
        # The slope is then the ratio of (dy / dt) / (dx / dt).
        
        a = self.start.x
        b = self.control0.x
        c = self.control1.x
        d = self.end.x
        
        denom = (
          3 * (-a + 3 * b - 3 * c + d) * (t ** 2) +
          2 * (3 * a - 6 * b + 3 * c) * t +
          (-3 * a + 3 * b))
        
        if ZE(denom):
            return float("+inf")
        
        e = self.start.y
        f = self.control0.y
        g = self.control1.y
        h = self.end.y
        
        numer = (
          3 * (-e + 3 * f - 3 * g + h) * (t ** 2) +
          2 * (3 * e - 6 * f + 3 * g) * t +
          (-3 * e + 3 * f))
        
        return numer / denom
    
    def transitions(self, xStart, xStop, yCoord, leftToRight):
        """
        Finds the intersection of self and the horizontal line segment defined
        by xStart, xStop, and yCoord, then for each point in the intersection
        determines whether the curve passes by left-to-right or right-to-left
        when looked at in the specified leftToRight orientation. See the
        doctest examples below for a sense of how this works; basically, a dict
        is returned with True mapping to seen left-to-right transitions, and
        False mapping to seen right-to-left transitions.
        
        >>> obj = _testingValues[0]
        >>> print(obj.transitions(0, 10, 3, True))
        {False: 1, True: 0}
        >>> print(obj.transitions(0, 10, 3, False))
        {False: 0, True: 1}
        
        >>> obj = _testingValues[4]
        >>> print(obj.transitions(0, 5, 2, True))
        {False: 1, True: 1}
        >>> print(obj.transitions(0, 5, 1, True))
        {False: 2, True: 1}
        """
        
        ray = type(self)(
          start = point.Point(xStart, yCoord),
          control0 = None,
          control1 = None,
          end = point.Point(xStop, yCoord))
        
        sects = self.intersection(ray)
        r = {False: 0, True: 0}
        CE = mathutilities.closeEnough
        
        for p in sorted(sects, reverse=(not leftToRight)):
            if not isinstance(p, point.Point):
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

if __debug__:
    P = point.Point
    
    _testingValues = (
        CSpline(P(1, 2), P(2, 6), P(5, 5), P(10, 7)),
        CSpline(P(1, 1), P(17, 9), P(3, 8), P(19, 1)),
        
        # the following is actually a line
        
        CSpline(P(1, 1), P(3, 3), P(4, 4), P(5, 5)),
        
        # the following is the [0] entry shifted by 0.5t (i.e. u = t - 0.5)
        
        CSpline(P(4, 5.25), P(7, 6.25), P(12, 6.25), P(19, 13.25)),
        
        # the following is pseudo-sine-wavish
        
        CSpline(P(1, 1), P(2, 10), P(3, -10), P(4, 1)),
        
        # the following has the two control points coincident
        
        CSpline(P(1, 1), P(4, 3), P(4, 3), P(7, 12)),
        
        # the following is degenerate, being only a single point
        
        CSpline(P(4, -3), P(4, -3), P(4, -3), P(4, -3)))
    
    del P

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
