#
# contour_quadratic.py
#
# Copyright © 2004-2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single TrueType contours.
"""

# System imports
import itertools
import math
import operator

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.fontmath import (
  bspline,
  line,
  mathutilities,
  point,
  pointwithonoff,
  rectangle)

# -----------------------------------------------------------------------------

#
# Private constants
#

_directions = {
  (-1, -1): "ne",
  (-1, 0): "e",
  (-1, 1): "se",
  (0, -1): "n",
  (0, 1): "s",
  (1, -1): "nw",
  (1, 0): "w",
  (1, 1): "sw"}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    # check for coincident adjacent points
    
    sawDups = sawBadDups = False
    
    for k, g in itertools.groupby(obj, key=tuple):
        v = list(g)
        
        if len(v) > 1:
            sawDups = True
        
        if len(set(x.onCurve for x in v)) > 1:
            sawBadDups = True
    
    if sawBadDups:
        logger.error((
          'V0295',
          (),
          "Contour has duplicate adjacent points of differing "
          "on-curve states."))
        
        r = False
    
    elif sawDups:
        logger.warning((
          'W1111',
          (),
          "Contour has duplicate adjacent points."))
    
    # check for coincident non-adjacent points and zero-length contours
    
    d = {}
    sawDups = sawBadDups = False
    
    for i, p in enumerate(obj):
        d.setdefault(tuple(p), set()).add(i)
    
    if len(d) == 1:
        logger.warning((
          'W1113',
          (),
          "Contour is degenerate (only a single (x, y) location)."))
    
    for k, s in d.items():
        if len(s) > 1:
            for a, b in itertools.permutations(s, 2):
                if abs(a - b) > 1:
                    sawDups = True
                    
                    if obj[a].onCurve != obj[b].onCurve:
                        sawBadDups = True
    
    if sawBadDups:
        logger.error((
          'V0297',
          (),
          "Contour has duplicate non-adjacent points of differing "
          "on-curve states."))
        
        r = False
    
    elif sawDups:
        logger.warning((
          'V0296',
          (),
          "Contour has duplicate non-adjacent points."))
    
    # check for on-curve points on the extrema
    
    extRectWith = obj.extrema(False)
    extRectWithout = obj.extrema(True)
    
    if extRectWith != extRectWithout:
        logger.warning((
          'W1112',
          (),
          "Not all extrema are marked with on-curve points."))
    
    # check for internally-intersecting contours
    
    allSplines = list(obj.splineIterator())
    allExtrema = [x.extrema() for x in allSplines]
    it = zip(allSplines, allExtrema)
    foundOverlap = False
    CE = mathutilities.closeEnough
    
    for (curve1, rect1), (curve2, rect2) in itertools.combinations(it, 2):
        # only bother with intersection check if extrema overlap
        
        if (
          rect1.isEmpty() or
          rect2.isEmpty() or
          max(rect1.overlapDegrees(rect2)) > 0):
            
            for sectObj in curve1.intersection(curve2):
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
        logger.warning((
          'E1111',
          (),
          "Contour intersects itself."))
    
    # check for co-linear off-curve points
    
    for curve in allSplines:
        if curve.offCurve is not None:
            L = line.Line(curve.onCurve1, curve.onCurve2)
            t = L.parametricValueFromPoint(curve.offCurve)
            
            if t is not None:
                logger.warning((
                  'V0309',
                  (curve.offCurve,),
                  "The off-curve point %s is co-linear with its two "
                  "adjacent on-curve points."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Contour_quadratic(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single TrueType contours. These are lists of
    PointWithOnOff objects.
    
    Note that Contour_quadratic objects do not have fromwalker() or
    buildBinary() methods; those functions are handled at a higher level, given
    the convoluted nature of the TrueType 'glyf' table.
    
    There is no support here (as yet) for stroke fonts.
    
    >>> _testingValues[0].pprint()
    Point 0: (20, 10), on-curve
    Point 1: (20, 490), on-curve
    Point 2: (380, 490), on-curve
    Point 3: (380, 10), on-curve
    
    >>> _testingValues[0].scaled(1.5).pprint()
    Point 0: (30, 15), on-curve
    Point 1: (30, 735), on-curve
    Point 2: (570, 735), on-curve
    Point 3: (570, 15), on-curve
    
    >>> m = matrix.Matrix.forShift(-50, -120)
    >>> m = m.multiply(matrix.Matrix.forRotation(90))  # counterclockwise
    >>> m = m.multiply(matrix.Matrix.forShift(50, 120))
    >>> _testingValues[0].transformed(m).pprint()
    Point 0: (160, 90), on-curve
    Point 1: (-320, 90), on-curve
    Point 2: (-320, 450), on-curve
    Point 3: (160, 450), on-curve
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    test - WARNING - Not all extrema are marked with on-curve points.
    True
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    test - ERROR - Contour has duplicate adjacent points of differing on-curve states.
    test - WARNING - Not all extrema are marked with on-curve points.
    False
    
    >>> _testingValues[5].isValid(logger=logger, editor=e)
    test - WARNING - Contour has duplicate adjacent points.
    True
    
    >>> _testingValues[6].isValid(logger=logger, editor=e)
    test - WARNING - Contour has duplicate non-adjacent points.
    test - WARNING - Contour intersects itself.
    True
    
    >>> _testingValues[7].isValid(logger=logger, editor=e)
    test - ERROR - Contour has duplicate non-adjacent points of differing on-curve states.
    False
    
    >>> _testingValues[8].isValid(logger=logger, editor=e)
    test - WARNING - Contour intersects itself.
    True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = (lambda p,obj,label: p.simple(obj, label=label)),
        item_pprintlabelfunc = (lambda i: "Point %d" % (i,)),
        seq_indexispointindex = True,
        seq_validatefunc_partial = _validate)
    
    #
    # Public methods
    #
    
    def bounds(self):
        """
        Returns a Rectangle with the extrema based on the curves; this is
        different from the extrema, which are calculated based solely on the
        coordinates.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_quadratic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> print(c.bounds())
        Minimum X = 100.0, Minimum Y = 100.0, Maximum X = 900.0, Maximum Y = 900.0
        
        >>> c = Contour_quadratic([
        ...   P(200, -300, onCurve=True),
        ...   P(0, 100, onCurve=False),
        ...   P(400, 400, onCurve=True),
        ...   P(700, 0, onCurve=True)])
        >>> print(c.bounds())
        Minimum X = 133.33333333333334, Minimum Y = -300, Maximum X = 700, Maximum Y = 400
        """
        
        r = None
        
        for b in self.splineIterator():
            ex = b.bounds()
            r = (ex if r is None else r.unioned(ex))
        
        return (r if r is None else rectangle.Rectangle(*r.asList()))
    
#     def centroid(self):
#         """
#         Computes and returns a Point representing the centroid of self. Note
#         that clients should ensure self is not self-intersecting first.
#         
#         The algorithm here is as follows:
#         
#             1.  Use splineIterator() to build a list of simple pieces.
#             
#             2.  Make a polygon out of these simple pieces and determine its
#                 area and centroid.
#             
#             3.  Find the areas of all the parabolic segments.
#             
#             4.  Find the centroid using sum(C[i].x * A[i]) / sum(A[i]),
#                 where C are the individual centroids and A are the areas. Note
#                 that some of the areas are likely to be negative (where the
#                 off-curve point lies inside the polygon from step 2 above).
#         
#         This code is likely to be somewhat slow, and so is a candidate for
#         moving to the fastmath C interface.
#         """
#         
#         # algorithm step 1
#         
#         simplePieces = list(self.splineIterator())
#         
#         # algorithm step 2
#         
#         it = itertools.cycle(simplePieces)
#         next(it)
#         polyArea = 0
#         
#         for obj1, obj2 in zip(simplePieces, it):
#             p1 = obj1.onCurve1
#             p2 = obj2.onCurve1  # yes, 1
#             polyArea += p1.x * p2.y
#             polyArea -= p2.x * p1.y
#         
#         polyArea /= 2
#         
#         if polyArea < 0:
#             # negative means clockwise
#             isCW = True
#             polyArea = -polyArea
#         
#         else:
#             # positive means counter-clockwise
#             isCW = False
#         
#         # algorithm step 3
#         
#         for piece in simplePieces:
#             if piece.offCurve is None:
#                 continue
#             
#             # For clockwise contours, if the off-curve point is to the left of
#             # the line from onCurve1 to onCurve2 then this area is positive;
#             # if it's to the right then the area is negative. This is flipped
#             # for counter-clockwise contours.
#             
#             pieceRawArea = piece.area()
#             pOn1 = (piece.onCurve1 if isCW else piece.onCurve2)
#             pOn2 = (piece.onCurve2 if isCW else piece.onCurve1)
#             pOff = piece.offCurve
#             angle1 = math.atan2(pOn2.y - pOn1.y, pOn2.x - pOn1.x)
#             angle2 = math.atan2(pOff.y - pOn1.y, pOff.x - pOn1.x)
#             
#             if angle2 < angle1:
#                 pieceRawArea = -pieceRawArea
#         
#         # algorithm step 4
#         
#         return None  # xxx
    
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
        >>> _testingValues[2].containsContour(_testingValues[2])
        False
        >>> _testingValues[3].containsContour(_testingValues[3])
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
        >>> _testingValues[3].containsPoint(P(800, 950))
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
    
    def describe(self):
        """
        Returns a general direction-based description of the normalized version
        of self.
        
        >>> print(_testingValues[0].describe())
        ('e', 's', 'w', 'n')
        >>> print(_testingValues[3].describe())
        ('sw', 'e', 'nw')
        """
        
        self = self.normalized(topLeftFirst=True)
        
        # For every pair of on-curve points, add a direction indication.
        retVal = ["start"]
        
        for i, first in enumerate(self):
            if first.onCurve:
                for j in range(i + 1, len(self)):
                    if self[j].onCurve:
                        otherIndex = j
                        break
                
                else:
                    # since we normalized, point [0] is guaranteed on-curve
                    otherIndex = 0
                
                second = self[otherIndex]
                
                t = (
                  (first.x > second.x) - (first.x < second.x),
                  (first.y > second.y) - (first.y < second.y))
                
                direction = _directions[t]
                
                if direction != retVal[-1]:
                    retVal.append(direction)
        
        return tuple(retVal[1:])
    
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
        >>> c = Contour_quadratic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> print(c.extrema())
        Minimum X = 100.0, Minimum Y = 100.0, Maximum X = 900.0, Maximum Y = 900.0
        
        >>> c = Contour_quadratic([
        ...   P(200, -300, onCurve=True),
        ...   P(0, 100, onCurve=False),
        ...   P(400, 400, onCurve=True),
        ...   P(700, 0, onCurve=True)])
        >>> print(c.extrema())
        Minimum X = 0, Minimum Y = -300, Maximum X = 700, Maximum Y = 400
        """
        
        r = None
        
        for b in self.splineIterator():
            ex = b.extrema(excludeOffCurve=excludeOffCurve)
            r = (ex if r is None else r.unioned(ex))
        
        return (r if r is None else rectangle.Rectangle(*r.asList()))
    
    def intersects(self, other):
        """
        Returns True if self and other intersect edges at any point. Note that
        one contour completely inside another is not an intersection for the
        purposes of this method; the edges have to touch. Also note that points
        may touch and it doesn't count as an intersection; for this method to
        return True, there must be at least one actual crossing somewhere.
        
        >>> _testingValues[0].intersects(_testingValues[2])
        False
        
        >>> shifted = Contour_quadratic([p.moved(20, 20) for p in _testingValues[0]])
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
                    
                    for sectObj in curve1.intersection(curve2):
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
        >>> c = Contour_quadratic([
        ...   P(100, 900),
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> c.isClockwise()
        True
        >>> c.reverse()
        >>> c.isClockwise()
        False
        """
        
        return self.polygonArea() < 0
    
    def normalized(self, **kwArgs):
        """
        Returns a copy of self with explicit on-curve points added where they
        are only implied. Adjacent points with the same coordinates will be
        reduced down to a single point, as will the special cases of two on-
        curve points that are the same separated by a different off-curve
        point. The returned object is guaranteed to have its [0] element be
        on-curve.
        
        There are also optional effects controlled via these keyword arguments:
        
            oldToNew            Default None. If an empty dict is passed in via
                                this keyword argument, it will be filled with a
                                map from old index to new index; remember there
                                may be extra points, so values() may be sparse.
            
            topLeftFirst        Default False. If True, the returned object
                                will have its topmost, then leftmost on-curve
                                point in the [0] element.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_quadratic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> c.pprint()
        Point 0: (100, 900), off-curve
        Point 1: (900, 900), off-curve
        Point 2: (900, 100), off-curve
        Point 3: (100, 100), off-curve
        >>> d = {}
        >>> c.normalized(oldToNew=d).pprint()
        Point 0: (500.0, 900.0), on-curve
        Point 1: (900, 900), off-curve
        Point 2: (900.0, 500.0), on-curve
        Point 3: (900, 100), off-curve
        Point 4: (500.0, 100.0), on-curve
        Point 5: (100, 100), off-curve
        Point 6: (100.0, 500.0), on-curve
        Point 7: (100, 900), off-curve
        >>> print(sorted(d.items()))
        [(0, 7), (1, 1), (2, 3), (3, 5)]
        
        >>> c = Contour_quadratic([
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False),
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False)])
        >>> c.pprint()
        Point 0: (900, 100), off-curve
        Point 1: (100, 100), off-curve
        Point 2: (100, 900), off-curve
        Point 3: (900, 900), off-curve
        >>> d = {}
        >>> c.normalized(oldToNew=d, topLeftFirst=True).pprint()
        Point 0: (500.0, 900.0), on-curve
        Point 1: (900, 900), off-curve
        Point 2: (900.0, 500.0), on-curve
        Point 3: (900, 100), off-curve
        Point 4: (500.0, 100.0), on-curve
        Point 5: (100, 100), off-curve
        Point 6: (100.0, 500.0), on-curve
        Point 7: (100, 900), off-curve
        >>> print(sorted(d.items()))
        [(0, 3), (1, 5), (2, 7), (3, 1)]
        
        >>> c = Contour_quadratic([
        ...   P(100, 900),
        ...   P(100, 900),  # duplicate point
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> c.normalized().pprint()
        Point 0: (100, 900), on-curve
        Point 1: (900, 900), on-curve
        Point 2: (900, 100), on-curve
        Point 3: (100, 100), on-curve
        
        >>> c = Contour_quadratic([
        ...   P(100, 900),
        ...   P(100, 901, onCurve=False),
        ...   P(100, 900),
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> c.normalized().pprint()
        Point 0: (100, 900), on-curve
        Point 1: (900, 900), on-curve
        Point 2: (900, 100), on-curve
        Point 3: (100, 100), on-curve
        """
        
        if len(self) == 0:
            return self.__copy__()
        
        it = itertools.cycle(self)
        next(it)
        it2 = itertools.cycle(self)
        next(it2)
        next(it2)
        v = []  # entries are (origIndex, value)
        firstOn = None
        specialSkip = False
        thisPtIndex = 0
        
        for thisPt, nextPt, afterNextPt in zip(self, it, it2):
            if specialSkip:
                specialSkip = False
                thisPtIndex += 1
                continue
            
            if tuple(thisPt) == tuple(nextPt):
                thisPtIndex += 1
                continue
            
            if thisPt.onCurve:
                if (
                  (not nextPt.onCurve) and
                  (afterNextPt.onCurve) and
                  (tuple(thisPt) == tuple(afterNextPt))):
                  
                    specialSkip = True
                    thisPtIndex += 1
                    continue
                
                if firstOn is None:
                    firstOn = len(v)
            
            v.append((thisPtIndex, thisPt))
            thisPtIndex += 1
            
            if (not thisPt.onCurve) and (not nextPt.onCurve):
                p = (thisPt + nextPt) / 2
                p.onCurve = True
                
                if firstOn is None:
                    firstOn = len(v)
                
                v.append((None, p))
        
        # If topLeftFirst is set, do that
        if kwArgs.get('topLeftFirst', False):
            tempObj = type(self)(obj[1] for obj in v)
            tlIndex = tempObj.corners()[0]
            
            if tlIndex:
                v = v[tlIndex:] + v[:tlIndex]
        
        # Otherwise, if the first point isn't on-curve, fix that
        elif firstOn:
            v = v[firstOn:] + v[:firstOn]
        
        # Fill in oldToNew, if it was asked for
        d = kwArgs.get('oldToNew')
        
        if d is not None:
            for i, (origIndex, pt) in enumerate(v):
                if origIndex is not None:
                    d[origIndex] = i
        
        return type(self)(obj[1] for obj in v)
    
    def polygonArea(self):
        """
        Returns the signed area of the polygon comprising all the points in
        the contour. This area will be negative if the contour is clockwise,
        and positive if it is counter-clockwise.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_quadratic([
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
        Returns an iterator over BSpline objects for all the curves or
        straight-line sections of the contour.
        
        >>> P = pointwithonoff.PointWithOnOff
        >>> c = Contour_quadratic([
        ...   P(100, 900),
        ...   P(900, 900),
        ...   P(900, 100),
        ...   P(100, 100)])
        >>> for obj in c.splineIterator(): print(obj)
        Line from (100, 900) to (900, 900)
        Line from (900, 900) to (900, 100)
        Line from (900, 100) to (100, 100)
        Line from (100, 100) to (100, 900)
        
        >>> c = Contour_quadratic([
        ...   P(100, 900, onCurve=False),
        ...   P(900, 900, onCurve=False),
        ...   P(900, 100, onCurve=False),
        ...   P(100, 100, onCurve=False)])
        >>> for obj in c.splineIterator(): print(obj)
        Curve from (500.0, 900.0) to (900.0, 500.0) with off-curve point (900, 900)
        Curve from (900.0, 500.0) to (500.0, 100.0) with off-curve point (900, 100)
        Curve from (500.0, 100.0) to (100.0, 500.0) with off-curve point (100, 100)
        Curve from (100.0, 500.0) to (500.0, 900.0) with off-curve point (100, 900)
        """
        
        n = self.normalized()
        i = 0
        v = n + n
        B = bspline.BSpline
        P = point.Point
        
        while i < len(n):  # yes, n, not v
            p1, p2 = v[i:i+2]
            
            if p1.onCurve and p2.onCurve:
                yield B(P(p1), P(p2), None)
                i += 1
            
            else:
                
                # Since the contour was normalized, we know v[i] is on-curve,
                # so at this point v[i+1] must be off-curve, and v[i+2] must
                # be on-curve again.
                
                yield B(P(p1), P(v[i+2]), P(p2))
                i += 2

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
        Contour_quadratic(pv[4:8]),
        Contour_quadratic(),
        Contour_quadratic(pv[8:12]),
        Contour_quadratic(pv[12:16]),
        Contour_quadratic(pv[0:4]),
        Contour_quadratic((pv[8],) + pv[8:12]),
        Contour_quadratic(pv[4:6] + (pv[4],) + pv[6:8]),
        Contour_quadratic((pv[1],) + pv[4:6] + (pv[2],) + pv[6:8]),
        Contour_quadratic((pv[4],) + (pv[6],) + (pv[5],) + (pv[7],))  # self-intersects
        )
    
    del pv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
