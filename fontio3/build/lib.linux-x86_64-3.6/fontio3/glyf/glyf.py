#
# glyf.py
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entire 'glyf' tables in TrueType fonts. Some effort has been made
to make the performance acceptable for even very large fonts.
"""

# System imports
import collections
import functools
import itertools
import logging

# Other imports
from fontio3 import loca
from fontio3.fontdata import deferreddictmeta
from fontio3.glyf import ttbounds, ttcompositeglyph, ttsimpleglyph

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ddFactory(key, d):
    offset, byteLength = d['loca'][key]
    w = d['wGlyf'].subWalker(offset, relative=True, newLimit=byteLength)
    
    if w.stillGoing():
        if d['doValidation']:
            logger = d['logger'].getChild("[%d]" % (key,))
            
            if w.length() < 2:
                logger.error((
                  'V0001',
                  (),
                  "Insufficient bytes"))
                
                return None
            
            numContours = w.unpack("h", advance=False)
            
            if numContours == -1:
                f = ttcompositeglyph.TTCompositeGlyph.fromvalidatedwalker
            else:
                f = ttsimpleglyph.TTSimpleGlyph.fromvalidatedwalker
            
            return f(w, logger=logger)
        
        else:
            numContours = w.unpack("h", advance=False)
            
            if numContours == -1:
                return ttcompositeglyph.TTCompositeGlyph.fromwalker(w)
            
            return ttsimpleglyph.TTSimpleGlyph.fromwalker(w)
    
    return ttsimpleglyph.TTSimpleGlyph()

def _doFinal4(pdMod, startPoint):
    """
    Returns a tuple of (deltaX, deltaY) pairs for the 4 phantom points.
    """
    
    return tuple(
      pdMod.get(p, (0, 0))
      for p in range(startPoint, startPoint + 4))

def _recalc_all(glyfObj, **kwArgs):
    allGlyphSet = set(glyfObj)
    r = glyfObj.__copy__()
    anyChanged = False
    
    # first make sure all the non-composite glyphs have updated bboxes
    for i, obj in glyfObj.items():
        if not obj.isComposite:
            newObj = obj.recalculated(**kwArgs)
            allGlyphSet.remove(i)
            
            if newObj != obj:
                r[i] = newObj
                anyChanged = True
    
    # process the composites in shallow-to-deep order
    while allGlyphSet:
        toRemove = set()
        
        for i in allGlyphSet:
            obj = glyfObj[i]
            refs = set(c.glyphIndex for c in obj.components)
            
            if not (refs & allGlyphSet):
                newObj = obj.recalculated(**kwArgs)
                toRemove.add(i)
                
                if newObj != obj:
                    r[i] = newObj
                    anyChanged = True
        
        allGlyphSet -= toRemove
    
    return (anyChanged, (r if anyChanged else glyfObj))

def _validateMissing(glyfObj, **kwArgs):
    logger = kwArgs['logger']
    
    if not len(glyfObj):
        logger.error((
          'V0946',
          (),
          "The 'glyf' table is completely empty."))
        
        return False
    
    if (0 not in glyfObj) or (glyfObj[0] is None):
        logger.error((
          'V0947',
          (),
          "Glyph 0 (the missing glyph) is missing or bad."))
        
        return False
    
    if (not glyfObj[0].isComposite) and (not glyfObj[0].contours):
        logger.warning((
          'V0948',
          (),
          "Glyph 0 has no contours."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Glyf(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    """
    
    #
    # Class definition variables
    #
    
    deferredDictSpec = dict(
        dict_recalculatefunc = _recalc_all,
        dict_validatefunc_partial = _validateMissing,
        item_createfunc = _ddFactory,
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda i: "glyph %d" % (i,)),
        item_usenamerforstr = True)
    
    #
    # Methods
    #
    
    @staticmethod
    def _getVariation_composite(glyphObj, pdMod, **kwArgs):
        e = kwArgs['editor']

        coords = kwArgs.pop('coords')

        forcedObj = ttsimpleglyph.TTSimpleGlyph() # empty

        for cidx, c in enumerate(glyphObj.components):
            cmpIdx = c.glyphIndex
            cmpMtx = c.transformationMatrix
            cmpVarObj, cmpF4 = e.glyf.getVariation(cmpIdx, coords, **kwArgs)
            dx, dy = pdMod.get(cidx, (0,0))
            m = type(c.transformationMatrix).forShift(dx, dy)
            cmpTrans = cmpVarObj.transformed(cmpMtx.multiplied(m))
            for tc in cmpTrans.contours:
                forcedObj.contours.append(tc)

        return forcedObj, _doFinal4(pdMod, len(glyphObj.components))


    @staticmethod
    def _getVariation_simple(glyphObj, pdMod, **kwArgs):
        ptCount = glyphObj.pointCount(**kwArgs)
        from fontio3.gvar import deltas
        deltaFunc = deltas.Deltas
        deltaZero = deltaFunc(0, 0)
        walkPoint = 0
        
        for c in glyphObj.contours:
            pointsFull = set(range(walkPoint, walkPoint + len(c)))
            basePoint = walkPoint
            walkPoint += len(c)
            pointsInContour = {n for n in pointsFull if n in pdMod}
            
            if not pointsInContour:
                for p in pointsFull:
                    pdMod[p] = deltaZero
                
                continue
            
            sortedInContour = sorted(pointsInContour)
            
            vDeltas = [
              (list(pdMod[p]) if p in pointsInContour else [0, 0])
              for p in sorted(pointsFull)]
            
            dPrevNext = {}
            
            for p in pointsFull - pointsInContour:
                if p < sortedInContour[0]:
                    pPrev = sortedInContour[-1]
                else:
                    pPrev = max(q for q in pointsInContour if q < p)
                
                if p > sortedInContour[-1]:
                    pNext = sortedInContour[0]
                else:
                    pNext = min(q for q in pointsInContour if q > p)
                
                dPrevNext[p] = (pPrev, pNext)
            
            for xy in (0, 1):
                for p in pointsFull - pointsInContour:
                    xyCoord = c[p-basePoint][xy]
                    pPrev, pNext = dPrevNext[p]
                    xyPrev = c[pPrev-basePoint][xy]
                    xyNext = c[pNext-basePoint][xy]
                    
                    if xyPrev > xyNext:
                        xyNext, xyPrev = xyPrev, xyNext
                        pNext, pPrev = pPrev, pNext
                    
                    if xyPrev <= xyCoord <= xyNext:
                        # it lies between; do interpolation
                        portion = (xyCoord - xyPrev) / (xyNext - xyPrev)
                        totalDist = vDeltas[pNext-basePoint][xy] - vDeltas[pPrev-basePoint][xy]
                        vDeltas[p-basePoint][xy] = vDeltas[pPrev-basePoint][xy] + portion * totalDist
                    
                    elif abs(xyPrev-xyCoord) < abs(xyNext-xyCoord):
                        # it lies outside; shift by xyPrev's shift
                        vDeltas[p-basePoint][xy] = vDeltas[pPrev-basePoint][xy]
                    
                    else:
                        # it lies outside; shift by xyNext's shift
                        vDeltas[p-basePoint][xy] = vDeltas[pNext-basePoint][xy]
            
            for p in pointsFull:
                pdMod[p] = deltaFunc(*vDeltas[p-basePoint])
        
        ptIndex = 0
        
        for c in glyphObj.contours:
            for indexInContour, p in enumerate(c):
                dlt = pdMod[ptIndex]
                dlt = [int(round(dlt[0])), int(round(dlt[1]))]
                c[indexInContour] = p.moved(*dlt)
                ptIndex += 1
        
        return glyphObj, _doFinal4(pdMod, ptCount)

#     def _getVariation_simple(glyphObj, pdMod, **kwArgs):
#         ptCount = glyphObj.pointCount(**kwArgs)
#         from fontio3.gvar import deltas
#         deltaFunc = deltas.Deltas
#         deltaZero = deltaFunc(0, 0)
#         walkPoint = 0
#         
#         for c in glyphObj.contours:
#             pointsFull = set(range(walkPoint, walkPoint + len(c)))
#             basePoint = walkPoint
#             walkPoint += len(c)
#             pointsInContour = {n for n in pointsFull if n in pdMod}
#             
#             if not pointsInContour:
#                 for p in pointsFull:
#                     pdMod[p] = deltaZero
#                 
#                 continue
#             
#             vDeltas = [
#               (list(pdMod[p]) if p in pointsInContour else [0, 0])
#               for p in sorted(pointsFull)]
#             
#             for xy in (0, 1):
#                 d = collections.defaultdict(set)
#                 
#                 for p in pointsInContour:
#                     d[c[p-basePoint][xy]].add(pdMod[p][xy])
#                 
#                 # Check cases where the same coordinate has multiple deltas.
#                 
#                 badCoords = {fd for fd, s in d.items() if len(s) > 1}
#                 
#                 if badCoords:
#                     if 'logger' in kwArgs:
#                         kwArgs['logger'].warning((
#                           'Vxxxx',
#                           ('xy'[xy], sorted(badCoords)),
#                           "These %s-coordinates map to multiple deltas: %s"))
#                     
#                     for fd in badCoords:
#                         s = d[fd]
#                         avg = sum(s) / len(s)
#                         d[fd] = {avg}
#                 
#                 for fd in d:
#                     d[fd] = next(iter(d[fd]))
#                 
#                 # Now do the interpolation
#                 
#                 for p in pointsFull - pointsInContour:
#                     pCoord = c[p-basePoint][xy]
#                     
#                     # now find bracketing coords
#                     
#                     if pCoord in d:
#                         dlt = d[pCoord]
#                     
#                     else:
#                         below = sorted(fd for fd in d if pCoord > fd)
#                         above = sorted(fd for fd in d if pCoord < fd)
#                         
#                         if below and above:
#                             a = above[0]
#                             b = below[-1]
#                             portion = (pCoord - b) / (a - b)
#                             dlt = d[b] + portion * (d[a] - d[b])
#                         
#                         elif below:
#                             dlt = d[below[-1]]
#                         
#                         else:
#                             dlt = d[above[0]]
#                     
#                     vDeltas[p-basePoint][xy] = dlt
#             
#             for p in pointsFull:
#                 pdMod[p] = deltaFunc(*vDeltas[p-basePoint])
#         
#         ptIndex = 0
#         
#         for c in glyphObj.contours:
#             for indexInContour, p in enumerate(c):
#                 dlt = pdMod[ptIndex]
#                 dlt = [int(round(dlt[0])), int(round(dlt[1]))]
#                 c[indexInContour] = p.moved(*dlt)
#                 ptIndex += 1
#         
#         return glyphObj, _doFinal4(pdMod, ptCount)
    
    def _validateChanges(self):
        """
        If any objects are composite glyphs, their references to component
        glyph indices are checked to make sure they're in range. The client
        must have already called _validateTightness().
        """
        
        badGlyphs = set()
        
        for glyphIndex, obj in self.items():
            if obj.isComposite:
                for component in obj.components:
                    if component.glyphIndex not in self:
                        badGlyphs.add(glyphIndex)
                        break
        
        if badGlyphs:
            s = sorted(badGlyphs)
            raise IndexError(
              "These composite glyphs refer to nonexistent glyphs: %s" % (s,))
    
    def _validateTightness(self):
        """
        Checks to make sure the keys are tight (that is, there are no numeric
        gaps and they start at zero). If they are not tight, an IndexError is
        raised.
        """
        
        minGlyphIndex = min(self)
        
        if minGlyphIndex:
            raise IndexError("The dictionary does not start at glyph zero!")
        
        maxGlyphIndex = max(self)
        
        if maxGlyphIndex != len(self) - 1:
            raise IndexError("There are gaps in the keys!")
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Glyf object to the specified LinkedWriter.
        
        Keyword arguments:
        
            forApple                If True, then composite glyphs will use the
                                    Apple interpretation (shift-then-scale).
                                    The default is False, which means to use
                                    the MS interpretation (scale-then-shift).
            
            forceLongAlignment      If True then all glyphs will be padded so
                                    they occupy a multiple-of-4 number of
                                    bytes.
        
            locaCallback            If the client is interested in getting the
                                    'loca' table constructed during this
                                    method's execution, then a callback should
                                    be provided. If present, this callback will
                                    be called with the new Loca object as the
                                    sole parameter.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            self._validateTightness()
            umk = self.unmadeKeys()
            ceCopy = self.copyCreationExtras()
            cecLoca = ceCopy.get('loca')
            cecBase = ceCopy.get('wGlyf')
            walkOffset = 0
            locaObj = loca.Loca(itertools.repeat(None, len(self)))
            forApple = kwArgs.get('forApple', False)
            forceLong = kwArgs.get('forceLongAlignment', False)
            
            for i in range(len(self)):
                startOffset = w.byteLength
                
                if i in umk:
                    offset, byteLength = cecLoca[i]
                    cecBase.reset()
                    
                    wRaw = cecBase.subWalker(
                      offset,
                      relative = True,
                      newLimit = byteLength)
                    
                    w.addString(wRaw.rest())
                
                else:
                    self[i].buildBinary(w, scaledOffsets=forApple)
                
                if forceLong:
                    w.alignToByteMultiple(4)
                
                thisByteLength = w.byteLength - startOffset
                locaObj[i] = (walkOffset, thisByteLength)
                walkOffset += thisByteLength
            
            if 'locaCallback' in kwArgs:
                kwArgs['locaCallback'](locaObj)
    
    def ensureConsistentGlyphSet(self, proposedSet, **kwArgs):
        """
        Given a proposed set of glyph indices representing a subset of the full
        set of glyph indices present in self, returns an updated set which has
        been modified for consistency. For instance, if self has glyph 100
        which is a composite of glyphs 201 and 202, and the proposed set only
        has glyphs 100 and 202, then a conflict exists. It can be resolved in
        one of two ways: by adding 201 back to the set, or by removing 100 from
        the set. Which of these options is chosen depends on the state of the
        fixByAdding keyword argument (see below).
        
        If a client is building an oldToNew dict for use in a glyphsRenumbered
        call where keepMissing is to be set to False, then this method should
        be called first to make the set of glyphs consistent.
        
        The following keyword arguments are supported:
        
            fixByAdding         Default True. If True, missing component glyphs
                                for composite glyphs present in proposedSet
                                will be added back. If False, composite glyphs
                                missing at least one component will be removed
                                from the returned result.
            
            orphanCheck         Default False. If True, then any non-composite
                                glyph that was used only as a component in one
                                or more composite glyphs will be removed if no
                                composite glyph remains which refers to it. If
                                False, orphans will be left in.
        """
        
        workingSet = set(proposedSet)
        fba = kwArgs.pop('fixByAdding', True)
        fakeEditor = {b'glyf': self}
        compositesToRemove = set()
        stillGoing = True
        
        while stillGoing:
            for i, d in self.items():
                if i not in workingSet:
                    continue
            
                if (not d) or (not d.isComposite):
                    continue
            
                # It's a composite glyph
            
                pieces = set()
                d.allReferencedGlyphs(pieces, editor=fakeEditor)
            
                if pieces == (pieces & workingSet):
                    continue  # nothing is missing, so just continue
            
                # One or more components is not present
            
                if fba:
                    workingSet.update(pieces)
                else:
                    compositesToRemove.add(i)
            
            if compositesToRemove:
                workingSet -= compositesToRemove
                compositesToRemove.clear()
            
            else:
                stillGoing = False
        
        if kwArgs.pop('orphanCheck', False):
            
            # First build a dict mapping non-composite component glyph IDs to
            # sets of composite glyphs that refer to them in self.
            
            backMap = collections.defaultdict(set)
            
            for i, d in self.items():
                if (not d) or (not d.isComposite):
                    continue
                
                for c in d.components:
                    ci = c.glyphIndex
                    cd = self[ci]
                    
                    if cd and (not cd.isComposite):
                        backMap[ci].add(i)
            
            # For each glyph that is a key in backMap, if that glyph is both
            # present in workingSet, and none of the backMapped composites are
            # present in workingSet, then remove that glyph from workingSet.
            
            componentsToRemove = set()
            
            for componentGlyphIndex, compositeSet in backMap.items():
                if componentGlyphIndex not in workingSet:
                    continue
                
                if any(gi in workingSet for gi in compositeSet):
                    continue
                
                componentsToRemove.add(componentGlyphIndex)
            
            # Finally, remove the orphans.
            
            workingSet -= componentsToRemove
        
        return workingSet
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Glyf object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('glyf')
        else:
            logger = logger.getChild('glyf')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        kwArgs.pop('doValidation', None)
        return cls.fromwalker(w, doValidation=True, logger=logger, **kwArgs)
        
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        locaObj = kwArgs['locaObj']
        
        if locaObj is not None:
            otki = iter(range(len(locaObj)))
            
            ce = dict(
              oneTimeKeyIterator = otki,
              loca = locaObj,
              wGlyf = w,
              doValidation = kwArgs.get('doValidation', False),
              logger = kwArgs.get('logger', None))
            
            return cls(creationExtras=ce)
        
        return None
    
    def getVariation(self, glyphIndex, coords, **kwArgs):
        """
        For a TT variant font (i.e. one with 'fvar' and 'gvar' tables) return a
        variation of the specified glyph index that matches the specified
        coordinates. This returned value is a pair (glyphObject, final4), where
        final4 is itself a tuple of 4 pairs contining the (deltaX, deltaY)
        values for the 4 phantom points.
        
        The following keyword arguments are used:
        
            editor      The Editor object. This is used to get the Fvar and
                        Gvar objects.
        """
        
        e = kwArgs['editor']
        
        if not e.reallyHas('gvar'):
            return (self[glyphIndex], _doFinal4({}, 0))
        
        gvarObj = e.gvar
        
        if len(coords) != len(gvarObj.axisOrder):
            raise ValueError("Coordinate has unexpected number of axes!")
        
        pd = gvarObj.glyphData.get(glyphIndex, None)
        
        if pd is None:
            return (self[glyphIndex], _doFinal4({}, 0))
        
        glyphObj = self[glyphIndex].__deepcopy__()
        
        if glyphObj.isComposite:
            pdMod = pd.deltasForCoord_composite(coords)
            r = self._getVariation_composite(glyphObj, pdMod, coords=coords, **kwArgs)
        
        else:
            pdMod = pd.deltasForCoord_simple(coords, glyphObj)
            r = self._getVariation_simple(glyphObj, pdMod, **kwArgs)
        
        r[0].hintBytes = b''
        r[0].bounds = ttbounds.TTBounds.fromcontours(r[0].contours)
        return r

    def getXYtoPointMap(self, id, **kwArgs):
        """
        Returns a dict mapping (xcoordinate, ycoordinate) tuples to
        point indices for id. Note that this resolves composites to
        simple glyphs so can be called on any glyph.
        
        The kwArg 'editor' should be passed in, since it is used for
        decomposing composites.
        """
        d = self[id]
        if d.isComposite:
            d = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(d, **kwArgs)

        pts = (tuple(p) for c in d.contours for p in c)
        return {p:i for i,p in enumerate(pts)}
    
    def singleIterator(self, glyphIndex, **kwArgs):
        """
        Returns a generator over tuples. These tuples represent splines or line
        segments. Rather than using classes for the points, this method just
        returns everything in simplest possible terms: tuples, Booleans, and
        ints.
        
        A line segment will have the form (False, x1, y1, x2, y2). A spline
        will have the form (True, onX1, onY1, offX, offY, onX2, onY2). Note
        that the objects returned by this generator will always be one of
        these two forms, which means this code will do a certain amount of
        normalizing (putting implicit on-curve points in, for instance).
        """
        
        obj = self[glyphIndex]
        
        if obj.isComposite:
            obj = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(obj, **kwArgs)
        
        if obj:
            for contourObj in obj.contours:
                n = contourObj.normalized()
                i = 0
                v = n + n
            
                while i < len(n):  # yes, n, not v
                    p1, p2 = v[i:i+2]
                
                    if p1.onCurve and p2.onCurve:
                        yield tuple((
                          False,
                          float(p1.x), float(p1.y),
                          float(p2.x), float(p2.y)))
                        
                        i += 1
                
                    else:
                        on2 = v[i+2]
                        
                        yield tuple((
                          True,
                          float(p1.x), float(p1.y),
                          float(p2.x), float(p2.y),  # p2 is the off-curve pt
                          float(on2.x), float(on2.y)))
                        
                        i += 2
    
    def unionBounds(self):
        """
        Returns a TTBounds object with the union bounds for all glyphs in the
        Glyf object.
        """
        
        TTB = ttbounds.TTBounds
        
        return functools.reduce(
          TTB.unioned,
          (obj.bounds for obj in self.values() if obj),
          TTB(xMin=32767, xMax=-32767, yMin=32767, yMax=-32767))

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
