#
# cffcontours.py
#
# Copyright © 2013-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of Cubic_contour objects.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.fontmath import rectangle

try:
    import intersectionlib
    useIntLibOK = True
except ImportError:
    useIntLibOK = False

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    hasIntersections = False

    if useIntLibOK:
        it = intersectionlib.IntersectionTester()
        PD = {
            True: it.ON_CURVE,
            False: it.OFF_CURVE}
        itc = []
        for c in obj:
            cc = []
            for p in c:
                cc.append( tuple((float(p.x), float(p.y), PD.get(p.onCurve))) )
            if len(c) > 2:
                cc.append( cc[0] )  # close non-degenerate contours
            itc.append(tuple(cc))

        vco = it.VerifyCubicOutline(itc)
        hasIntersections = vco[0]
        hasCorrectWinding = vco[1]
        hasOnCurveAtExtrema = vco[2]

        # NOTE: currently we don't have a non-intersectionlib way to do
        # the winding direction or on-curve at extrema tests, so they're only
        # performed if we have intersectionlib.

        if not hasCorrectWinding:
            wrongContours = ", ".join([str(ci) for ci in vco[7]])
            if len(vco[7]) > 1:
                wstring = "s %s do " % (wrongContours,)
            else:
                wstring = " %s does " % (wrongContours,)

            logger.warning((
              'V1006',
              (wstring,),
              "Contour%s not have correct winding direction."))

        if not hasOnCurveAtExtrema:
            logger.warning((
              'W1112',
              (),
              "Not all extrema are marked with on-curve points."))

    else:
        for c1, c2 in itertools.combinations(obj, 2):
            if c1.intersects(c2, delta=5.0e-2):
                hasIntersections = True
                break

    if hasIntersections:
        logger.warning((
          'W1110',
          (),
          "Glyph has intersecting components."))

    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CFFContours(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing multiple CFF contours. These are lists of
    Cubic_contour objects. There are no attributes:

    >>> _testingValues[1].pprint()
    Contour 0:
      Point 0: (5, 5), on-curve
      Point 1: (10, 5), on-curve
      Point 2: (10, 10), on-curve
      Point 3: (5, 10), on-curve
    Contour 1:
      Point 0: (5, 5), on-curve
      Point 1: (7, 7), off-curve
      Point 2: (9, 9), off-curve
      Point 3: (10, 10), on-curve
    """

    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Contour %d" % (i,)),
        item_subloggernamefunc = (lambda i: "contour %d" % (i,)),
        seq_validatefunc_partial = _validate)

    #
    # Methods
    #

    def bounds(self, **kwArgs):
        xMin = 32767
        xMax = -32768
        yMin = xMin
        yMax = xMax
        for c in self:
            bc = c.extrema()
            if bc:
                xMin = min(xMin, bc.xMin)
                xMax = max(xMax, bc.xMax)
                yMin = min(yMin, bc.yMin)
                yMax = max(yMax, bc.yMax)
        return rectangle.Rectangle(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

    def _makeIndexList(self):
        """
        Returns a list of (contourIndex, entirePointIndex) for the object.

        >>> _testingValues[1]._makeIndexList()
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (1, 6), (1, 7)]
        """

        totalLen = sum(len(c) for c in self)
        r = [None] * totalLen
        start = 0

        for contourIndex, c in enumerate(self):
            for pointIndex in range(start, start + len(c)):
                r[pointIndex] = (contourIndex, pointIndex)

            start += len(c)

        return r

    @staticmethod
    def _remapIndexList(v, pointMap):
        """
        Given a list of (contourIndex, pointIndex) pairs, creates and returns a
        new list resulting from the specified pointMap, which is a dict of
        oldPointIndex -> newPointIndex.

        >>> v = _testingValues[1]._makeIndexList()
        >>> print(v)
        [(0, 0), (0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (1, 6), (1, 7)]

        >>> d = {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3}
        >>> print((CFFContours._remapIndexList(v, d)))
        [(1, 4), (1, 5), (1, 6), (1, 7), (0, 0), (0, 1), (0, 2), (0, 3)]

        >>> print((CFFContours._remapIndexList(v, {1: 7, 7: 2, 2: 1})))
        [(0, 0), (0, 2), (1, 7), (0, 3), (1, 4), (1, 5), (1, 6), (0, 1)]
        """

        r = list(v)

        for oldIndex, newIndex in pointMap.items():
            r[newIndex] = v[oldIndex]

        return r

    def _validateIndexList(self, v):
        """
        Given a reordered index list, checks each contour for contiguity and
        raises a ValueError if any discontiguities are found.

        >>> v = _testingValues[1]._makeIndexList()
        >>> d = {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3}
        >>> _testingValues[1]._validateIndexList(
        ...   CFFContours._remapIndexList(v, d))

        >>> _testingValues[1]._validateIndexList(
        ...   CFFContours._remapIndexList(v, {1: 7, 7: 2, 2: 1}))
        Traceback (most recent call last):
          ...
        ValueError: Discontiguous grouping after point renumbering!
        """

        keysFound = set()

        for k, g in itertools.groupby(v, operator.itemgetter(0)):
            if (k in keysFound) or (len(list(g)) != len(self[k])):
                raise ValueError(
                  "Discontiguous grouping after point renumbering!")

            keysFound.add(k)

        if len(keysFound) != len(self):
            raise ValueError(
              "One or more contours deleted by point renumbering!")

    def buildBinary(self, w, **kwArgs):
        """
        Not yet implemented.
        """
        raise NotImplementedError()



    def pointIterator(self):
        """
        Returns an iterator which yields individual PointWithOnOff objects, without
        respect to Contour_cubic boundaries.

        >>> for p in _testingValues[0].pointIterator(): print((p.x))
        5
        10
        10
        5
        """

        for c in self:
            for p in c:
                yield p


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.fontmath import contour_cubic
    from fontio3.fontmath import pointwithonoff

    c1 = contour_cubic.Contour_cubic()
    c1.append( pointwithonoff.PointWithOnOff( (5,5), onCurve=True ))
    c1.append( pointwithonoff.PointWithOnOff( (10,5), onCurve=True ))
    c1.append( pointwithonoff.PointWithOnOff( (10,10), onCurve=True ))
    c1.append( pointwithonoff.PointWithOnOff( (5,10), onCurve=True ))

    c2 = contour_cubic.Contour_cubic()
    c2.append( pointwithonoff.PointWithOnOff( (5,5), onCurve=True ))
    c2.append( pointwithonoff.PointWithOnOff( (7,7), onCurve=False ))
    c2.append( pointwithonoff.PointWithOnOff( (9,9), onCurve=False ))
    c2.append( pointwithonoff.PointWithOnOff( (10,10), onCurve=True ))

    c3 = contour_cubic.Contour_cubic()
    c3.append(pointwithonoff.PointWithOnOff((100,100), onCurve=True))

    _testingValues = (
        CFFContours([c1]),
        CFFContours([c1, c2]),
        CFFContours([c2]),
        CFFContours([c2, c3]))

    del c1, c2, c3

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

