#
# ttcontours.py
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of TrueType contours (both full and stroke).
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta
from fontio3.glyf import ttcontour, ttpoint
from fontio3.utilities import writer

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
    isOK = True
    
    for c in obj:
        if (len(c) == 2) and (not all(p.onCurve for p in c)):
            logger.error((
              'V0988',
              (),
              "At least one contour is length 2 and has off-curve points."))
            
            return False
    
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

        vqo = it.VerifyQuadOutline(itc)
        hasIntersections = vqo[0]
        hasCorrectWinding = vqo[1]
        hasOnCurveAtExtrema = vqo[2]

        # NOTE: currently we don't have a non-intersectionlib way to do
        # the winding direction or on-curve at extrema tests, so they're only
        # performed if we have intersectionlib.

        if not hasCorrectWinding:
            wrongContours = ", ".join([str(ci) for ci in vqo[7]])
            if len(vqo[7]) > 1:
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
            if c1.intersects(c2):
                hasIntersections = True
                break
    
    if hasIntersections:
        logger.warning((
          'W1110',
          (),
          "Glyph has intersecting components."))
          
    if obj.highBit and kwArgs['editor'].head.glyphDataFormat != 0x9654:
        logger.error((
          'V0184',
          (),
          "Reserved bit in flags is not zero."))
        isOK = False
    
    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TTContours(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing multiple TrueType contours. These are lists of
    TTContour objects. There is one attribute:
    
        highBit     If True, the 0x80 bit is set in one or more points. This is
                    used, for example, to identify an outline glyph in a stroke
                    font for iType.
    
    >>> _testingValues[1].pprint()
    Contour 0:
      Point 0: (620, 610), on-curve
      Point 1: (620, 1090), on-curve
      Point 2: (980, 1090), on-curve
      Point 3: (980, 610), on-curve
    Contour 1:
      Point 0: (750, 750), on-curve
      Point 1: (850, 700), off-curve
      Point 2: (950, 750), on-curve
      Point 3: (850, 1000), on-curve
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Contour %d" % (i,)),
        item_subloggernamefunc = (lambda i: "contour %d" % (i,)),
        seq_compactremovesfalses = True,
        seq_validatefunc_partial = _validate)
    
    attrSpec = dict(
        highBit = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: False),
            attr_label = "High bit",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    @staticmethod
    def _combineRepeats(v):
        """
        Takes a vector of one-byte strings (flags) and coalesces repeats.
    
        Note that this method does its work in-place within the specified
        vector.
        
        >>> v = [0x11, 0x11, 0x11, 0x01, 0x11]
        >>> TTContours._combineRepeats(v)
        >>> v
        [25, 2, 1, 17]
        """
        
        prevValue = v[0]
        i = 1
        
        while i < len(v):
            if v[i] == prevValue:
                v[i-1] |= 0x08
                j = i + 1
                
                while j < len(v):
                    if v[j] != v[i]:
                        break
                    j += 1
                
                v[i] = j - i    # number of additional repeats
                v[i+1:j] = []
            
            else:
                prevValue = v[i]
            
            i += 1
    
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
    def _parseFlags(w, numPoints):
        v = []
        
        while numPoints > 0:
            f = w.unpack("B")
            
            if f & 0x08:
                repeatCount = w.unpack("B") + 1
                v.extend([f] * repeatCount)
                numPoints -= repeatCount
            
            else:
                v.append(f)
                numPoints -= 1
        
        return v
    
    @staticmethod
    def _parseFlags_validated(w, numPoints, logger):
        v = []
        
        while numPoints > 0:
            if w.length() < 1:
                logger.error((
                  'V0181',
                  (),
                  "Not enough flags for specified number of points."))
                
                return None
            
            f = w.unpack("B")
            
            if f & 0x08:
                if w.length() < 1:
                    logger.error((
                      'V0182',
                      (),
                      "No repeat count after repeat bit."))
                    
                    return None
                
                repeatCount = w.unpack("B") + 1
                
                if repeatCount > numPoints:
                    logger.error((
                      'V0183',
                      (),
                      "Repeat count exceeds number of remaining points."))
                    
                    return None
                
                v.extend([f] * repeatCount)
                numPoints -= repeatCount
            
            else:
                v.append(f)
                numPoints -= 1
        
        return v
    
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
        >>> print(TTContours._remapIndexList(v, d))
        [(1, 4), (1, 5), (1, 6), (1, 7), (0, 0), (0, 1), (0, 2), (0, 3)]
        
        >>> print(TTContours._remapIndexList(v, {1: 7, 7: 2, 2: 1}))
        [(0, 0), (0, 2), (1, 7), (0, 3), (1, 4), (1, 5), (1, 6), (0, 1)]
        """
        
        r = list(v)
        
        for oldIndex, newIndex in pointMap.items():
            r[newIndex] = v[oldIndex]
        
        return r
    
    @classmethod
    def _unpackPoints(cls, w, numPoints):
        flags = cls._parseFlags(w, numPoints)
        x = 0
        y = 0
        xCoords = [0] * len(flags)
        yCoords = list(xCoords)
        onCurve = [False] * len(flags)
        highBit = False
        
        for i, flag in enumerate(flags):
            if flag & 0x01:
                onCurve[i] = True
            
            if flag & 0x80:
                highBit = True
            
            if flag & 0x02:
                delta = (w.unpack("B") if flag & 0x10 else -w.unpack("B"))
            elif flag & 0x10:
                delta = 0
            else:
                delta = w.unpack("h")
            
            x += delta
            xCoords[i] = x
        
        for i, flag in enumerate(flags):
            if flag & 0x04:
                delta = (w.unpack("B") if flag & 0x20 else -w.unpack("B"))
            elif flag & 0x20:
                delta = 0
            else:
                delta = w.unpack("h")
            
            y += delta
            yCoords[i] = y
        
        v = [
          ttpoint.TTPoint((t[0], t[1]), onCurve=t[2])
          for t in zip(xCoords, yCoords, onCurve)]
        
        return v, highBit
    
    @classmethod
    def _unpackPoints_validated(cls, w, numPoints, logger):
        flags = cls._parseFlags_validated(w, numPoints, logger)
        
        if flags is None:
            return None
        
        x = 0
        y = 0
        xCoords = [0] * len(flags)
        yCoords = list(xCoords)
        onCurve = [False] * len(flags)
        highBit = False
        
        for i, flag in enumerate(flags):
            if flag & 0x40:
                logger.warning((
                  'V0184',
                  (),
                  "Reserved bit in flags is not zero."))
            
            if flag & 0x01:
                onCurve[i] = True
            
            if flag & 0x80:
                highBit = True
            
            if flag & 0x02:
                if w.length() < 1:
                    logger.error((
                      'V0185',
                      (),
                      "Insufficient bytes for x-delta."))
                    
                    return None
                
                delta = (w.unpack("B") if flag & 0x10 else -w.unpack("B"))
            
            elif flag & 0x10:
                delta = 0
            
            else:
                if w.length() < 2:
                    logger.error((
                      'V0185',
                      (),
                      "Insufficient bytes for x-delta."))
                    
                    return None
                
                delta = w.unpack("h")
            
            x += delta
            xCoords[i] = x
        
        for i, flag in enumerate(flags):
            if flag & 0x04:
                if w.length() < 1:
                    logger.error((
                      'V0186',
                      (),
                      "Insufficient bytes for y-delta."))
                    
                    return None
                
                delta = (w.unpack("B") if flag & 0x20 else -w.unpack("B"))
            
            elif flag & 0x20:
                delta = 0
            
            else:
                if w.length() < 2:
                    logger.error((
                      'V0186',
                      (),
                      "Insufficient bytes for y-delta."))
                    
                    return None
                
                delta = w.unpack("h")
            
            y += delta
            yCoords[i] = y
        
        v = [
          ttpoint.TTPoint((t[0], t[1]), onCurve=t[2])
          for t in zip(xCoords, yCoords, onCurve)]
        
        return v, highBit
    
    def _validateIndexList(self, v):
        """
        Given a reordered index list, checks each contour for contiguity and
        raises a ValueError if any discontiguities are found.
        
        >>> v = _testingValues[1]._makeIndexList()
        >>> d = {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3}
        >>> _testingValues[1]._validateIndexList(
        ...   TTContours._remapIndexList(v, d))
        
        >>> _testingValues[1]._validateIndexList(
        ...   TTContours._remapIndexList(v, {1: 7, 7: 2, 2: 1}))
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
        Adds the binary data to the specified LinkedWriter. Note that this is
        the flags, xCoordinates, and yCoordinates portions of a simple glyph.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 3711 2111 1401 680A  01E0 FE20           |7.!...h....     |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0111 2111 2716 3727  026C 0168 E664 6464 |..!.'.7'.l.h.ddd|
              10 | 0262 01E0 FE20 8C32  32FA                |.b... .22.      |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 3711 2111 1311 2111  2716 3727 1401 68F0 |7.!...!.'.7'..h.|
              10 | 0168 E664 6464 0A01  E0FE 2002 5801 E0FE |.h.ddd.... .X...|
              20 | 208C 3232 FA                             | .22.           |
        """
        
        numPoints = sum(len(c) for c in self)
        vFlags = [0] * numPoints
        xw = writer.LinkedWriter()
        yw = writer.LinkedWriter()
        lastX = 0
        lastY = 0
        
        for i, p in enumerate(self.pointIterator()):
            f = (1 if p.onCurve else 0)
            
            if self.highBit:
                f += 0x80
            
            deltaX = p.x - lastX
            deltaY = p.y - lastY
            
            if deltaX:
                a = abs(deltaX)
                
                if a < 256:
                    f += 0x02
                    
                    if deltaX >= 0:
                        f += 0x10
                    
                    xw.add("B", a)
                
                else:
                    xw.add("h", deltaX)
            
            else:
                f += 0x10
            
            if deltaY:
                a = abs(deltaY)
                
                if a < 256:
                    f += 0x04
                    
                    if deltaY >= 0:
                        f += 0x20
                    
                    yw.add("B", a)
                
                else:
                    yw.add("h", deltaY)
            
            else:
                f += 0x20
            
            lastX = p.x
            lastY = p.y
            vFlags[i] = f
        
        self._combineRepeats(vFlags)  # works in-place
        w.addGroup("B", vFlags)
        w.addString(xw.binaryString())
        w.addString(yw.binaryString())
    
    @classmethod
    def fromcontourgroups(cls, cgObjs, **kwArgs):
        """
        Creates and returns a new TTContours object by "flattening" the given
        TTContourGroup objects. The cgObjs argument should be a sequence of
        zero or more TTContourGroup objects.
        
        >>> cgObjs = _makeCGTest()
        >>> TTContours.fromcontourgroups(cgObjs).pprint()
        Contour 0:
          Point 0: (100, 100), on-curve
          Point 1: (100, 1100), on-curve
          Point 2: (1900, 1100), on-curve
          Point 3: (1900, 100), on-curve
        Contour 1:
          Point 0: (200, 200), on-curve
          Point 1: (1400, 200), on-curve
          Point 2: (1400, 1000), on-curve
          Point 3: (200, 1000), on-curve
        Contour 2:
          Point 0: (300, 300), on-curve
          Point 1: (300, 900), on-curve
          Point 2: (1000, 900), on-curve
          Point 3: (1000, 300), on-curve
        Contour 3:
          Point 0: (400, 400), on-curve
          Point 1: (500, 400), on-curve
          Point 2: (500, 500), on-curve
          Point 3: (400, 500), on-curve
        Contour 4:
          Point 0: (1100, 300), on-curve
          Point 1: (1100, 900), on-curve
          Point 2: (1300, 900), on-curve
          Point 3: (1300, 300), on-curve
        Contour 5:
          Point 0: (1500, 200), on-curve
          Point 1: (1800, 200), on-curve
          Point 2: (1800, 1000), on-curve
          Point 3: (1500, 1000), on-curve
        Contour 6:
          Point 0: (1550, 700), on-curve
          Point 1: (1550, 900), on-curve
          Point 2: (1650, 900), on-curve
          Point 3: (1650, 700), on-curve
        Contour 7:
          Point 0: (1650, 300), on-curve
          Point 1: (1650, 500), on-curve
          Point 2: (1750, 500), on-curve
          Point 3: (1750, 300), on-curve
        Contour 8:
          Point 0: (2000, 500), on-curve
          Point 1: (2000, 600), on-curve
          Point 2: (2100, 600), on-curve
          Point 3: (2100, 500), on-curve
        """
        
        v = []
        f = ttcontour.TTContour
        
        for cgObj in cgObjs:
            v.append(f(cgObj))
            kids = getattr(cgObj, 'children', [])
            
            if kids:
                v.extend(cls.fromcontourgroups(kids, **kwArgs))
        
        return cls(v, **utilities.filterKWArgs(cls, kwArgs))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTContours. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[0].binaryString()
        >>> TTContours.fromvalidatedbytes(
        ...   s, logger=logger, endPoints=[3]).pprint()
        test.ttcontours - DEBUG - Walker has 12 remaining bytes.
        Contour 0:
          Point 0: (20, 10), on-curve
          Point 1: (20, 490), on-curve
          Point 2: (380, 490), on-curve
          Point 3: (380, 10), on-curve
        
        >>> obj = TTContours.fromvalidatedbytes(
        ...   s[:-1], logger=logger, endPoints=[3])
        test.ttcontours - DEBUG - Walker has 11 remaining bytes.
        test.ttcontours - ERROR - Insufficient bytes for y-delta.
        
        >>> obj = TTContours.frombytes(s, logger=logger, endPoints=[3])
        >>> obj.highBit = True
        >>> fe = utilities.fakeEditor(1, head=True)
        >>> obj.isValid(editor=fe, logger=logger)
        test - ERROR - Reserved bit in flags is not zero.
        False
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ttcontours')
        else:
            logger = logger.getChild('ttcontours')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        ep = kwArgs['endPoints']
        t = cls._unpackPoints_validated(w, ep[-1] + 1, logger)
        
        if t is None:
            return None
        
        points, highBit = t
        v = []
        startPoint = 0
        
        for endPoint in ep:
            v.append(ttcontour.TTContour(points[startPoint:endPoint+1]))
            startPoint = endPoint + 1
        
        return cls(v, highBit=highBit)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TTContours object from the specified walker,
        which should be located at the start of the flags in a TrueType glyph
        description.
        
        There is one required keyword argument:
        
            endPoints       A sequence of indices for the endpoints of each
                            contour.
        
        >>> tv = _testingValues
        >>> fb = TTContours.frombytes
        >>> tv[0] == fb(tv[0].binaryString(), endPoints=[3])
        True
        >>> tv[1] == fb(tv[1].binaryString(), endPoints=[3, 7])
        True
        >>> tv[2] == fb(tv[2].binaryString(), endPoints=[3, 7, 11])
        True
        """
        
        ep = kwArgs['endPoints']
        points, highBit = cls._unpackPoints(w, ep[-1] + 1)
        v = []
        startPoint = 0
        
        for endPoint in ep:
            v.append(ttcontour.TTContour(points[startPoint:endPoint+1]))
            startPoint = endPoint + 1
        
        return cls(v, highBit=highBit)
    
    def pointIterator(self):
        """
        Returns an iterator which yields individual TTPoint objects, without
        respect to TTContour boundaries.
        
        >>> for p in _testingValues[0].pointIterator(): print(p.x)
        20
        20
        380
        380
        """
        
        for c in self:
            for p in c:
                yield p
    
    def pointsRenumbered(self, mapData, **kwArgs):
        """
        The complex nature of nesting in TrueType non-composite glyphs makes
        necessary this custom method to renumber points.
        
        >>> _testingValues[1].pprint()
        Contour 0:
          Point 0: (620, 610), on-curve
          Point 1: (620, 1090), on-curve
          Point 2: (980, 1090), on-curve
          Point 3: (980, 610), on-curve
        Contour 1:
          Point 0: (750, 750), on-curve
          Point 1: (850, 700), off-curve
          Point 2: (950, 750), on-curve
          Point 3: (850, 1000), on-curve
        
        This example shows a single contour being reversed:
        
        >>> md = {50: {0: 3, 1: 2, 2: 1, 3: 0}}
        >>> _testingValues[1].pointsRenumbered(md, glyphIndex=50).pprint()
        Contour 0:
          Point 0: (980, 610), on-curve
          Point 1: (980, 1090), on-curve
          Point 2: (620, 1090), on-curve
          Point 3: (620, 610), on-curve
        Contour 1:
          Point 0: (750, 750), on-curve
          Point 1: (850, 700), off-curve
          Point 2: (950, 750), on-curve
          Point 3: (850, 1000), on-curve
        
        This example shows two contours being interchanged:
        
        >>> md = {50: {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3}}
        >>> _testingValues[1].pointsRenumbered(md, glyphIndex=50).pprint()
        Contour 0:
          Point 0: (750, 750), on-curve
          Point 1: (850, 700), off-curve
          Point 2: (950, 750), on-curve
          Point 3: (850, 1000), on-curve
        Contour 1:
          Point 0: (620, 610), on-curve
          Point 1: (620, 1090), on-curve
          Point 2: (980, 1090), on-curve
          Point 3: (980, 610), on-curve
        """
        
        glyphIndex = kwArgs['glyphIndex']
        
        if glyphIndex in mapData:
            v = self._makeIndexList()
            v = self._remapIndexList(v, mapData[glyphIndex])
            self._validateIndexList(v)
            r = []
            flatList = list(self.pointIterator())
        
        for oldContourIndex, g in itertools.groupby(v, operator.itemgetter(0)):
            oldIndices = [obj[1] for obj in g]
            
            if oldIndices == list(
              range(oldIndices[0], oldIndices[0] + len(oldIndices))):
                r.append(self[oldContourIndex])
            
            else:
                r.append(ttcontour.TTContour(flatList[i] for i in oldIndices))
        
        return TTContours(r)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeCGTest():
        from fontio3.glyf import ttcontourgroups
        
        return ttcontourgroups.TTContourGroups.fromttcontours(
          ttcontourgroups._makeTestContours())
    
    c = ttcontour._testingValues
    
    _testingValues = (
        TTContours([c[0]]),
        TTContours([c[2], c[3]]),
        TTContours([c[0], c[2], c[3]]))
    
    del c

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
