#
# point_dict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for DeltasDict objects associated with particular point indices for a
given glyph.
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.fontmath import interpolation
from fontio3.gvar import deltas
    
# -----------------------------------------------------------------------------

#
# Classes
#

class PointDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping point indices to DeltasDict objects. These have all the
    delta information for a single glyph.
    
    As with GlyphDict objects, this class is a helper and has no buildBinary()
    or fromwalker() methods.
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Point %d" % (i,)),
        item_pprintlabelpresort = True,
        item_renumberpointsdirectkeys = True)
    
    #
    # Methods
    #
    
    def deltasForCoord_composite(self, coord):
        """
        Returns a dict mapping point indices to Deltas, with no actual
        interpolation (since the "points" in this case are actually indices
        into the component array).
        """
        
        r = {}
        
        for pointIndex, ddObj in self.items():
            dlt = ddObj.interpolateDelta(coord)
            
            if dlt is not None:
                r[pointIndex] = dlt
        
        return r
    
    def deltasForCoord_simple(self, coord, glyphObj):
        """
        """
        
        allPts = [p for c in glyphObj.contours for p in c]
        r = {p: [0, 0] for p in range(len(allPts)+4)}
        d = self.makeInvertDict()  # {coord: {pt: dlt, pt: dlt...}, ...}
        
        for keyCoord, keySubDict in d.items():
            kDeltas = {}
            
            # This loop can go over all points at once
            
            for p, dlt in keySubDict.items():
                factor = 1
                ed = dlt.effectiveDomain
                it = enumerate(zip(keyCoord, coord))
                
                for i, (peakValue, coordValue) in it:
                    if not factor:
                        break
                    
                    if ed is not None:
                        ed1 = min(ed.edge1[i], ed.edge2[i])
                        ed2 = max(ed.edge1[i], ed.edge2[i])
                    
                    if not peakValue:
                        continue
                
                    if (
                      (not coordValue) or 
                      (coordValue < 0 and peakValue > 0) or 
                      (coordValue > 0 and peakValue < 0) or
                      ((ed is None) and (abs(coordValue) > abs(peakValue)))):
                  
                        factor = 0
                
                    elif ed is None:
                        factor *= (coordValue / peakValue)
                
                    elif (coordValue < ed1) or (coordValue > ed2):
                        factor = 0
                
                    elif coordValue < peakValue:
                        if peakValue != ed1:
                            factor *= (coordValue - ed1) / (peakValue - ed1)
                
                    elif ed2 != peakValue:
                        factor *= (ed2 - coordValue) / (ed2 - peakValue)
                
                kDeltas[p] = [factor * dlt.x, factor * dlt.y]
            
            # Now need to interpolate for all keys missing from kDeltas
            # Note we don't need to interpolate phantoms (single points)
            #
            # Note that unlike above, this loop needs to respect contours
            
            hadActualDeltas = set(kDeltas)
            walkPoint = 0
            
            for c in glyphObj.contours:
                pointsFull = set(range(walkPoint, walkPoint + len(c)))
                basePoint = walkPoint
                walkPoint += len(c)
                pointsPresent = hadActualDeltas & pointsFull
                
                if not pointsPresent:
                    continue
                
                pointsMissing = pointsFull - pointsPresent
                sortedPresent = sorted(pointsPresent)
                dPrevNext = {}
            
                for p in pointsMissing:
                    if p < sortedPresent[0]:
                        pPrev = sortedPresent[-1]
                    else:
                        pPrev = max(q for q in pointsPresent if q < p)
                
                    if p > sortedPresent[-1]:
                        pNext = sortedPresent[0]
                    else:
                        pNext = min(q for q in pointsPresent if q > p)
                
                    dPrevNext[p] = (pPrev, pNext)
            
                for p in pointsMissing:
                    if p not in kDeltas:
                        kDeltas[p] = [0, 0]
                
                    for xy in (0, 1):
                        xyCoord = c[p-basePoint][xy]
                        pPrev, pNext = dPrevNext[p]
                        xyPrev = c[pPrev-basePoint][xy]
                        xyNext = c[pNext-basePoint][xy]
                    
                        if xyPrev > xyNext:
                            xyNext, xyPrev = xyPrev, xyNext
                            pNext, pPrev = pPrev, pNext
                    
                        if xyPrev <= xyCoord <= xyNext:
                            # it lies between; do interpolation
                            if xyNext == xyPrev:
                                kDeltas[p][xy] = (kDeltas[pPrev][xy] + kDeltas[pNext][xy]) / 2
                            
                            else:
                                portion = (xyCoord - xyPrev) / (xyNext - xyPrev)
                                totalDist = kDeltas[pNext][xy] - kDeltas[pPrev][xy]
                                kDeltas[p][xy] = kDeltas[pPrev][xy] + portion * totalDist
                    
                        elif abs(xyPrev-xyCoord) < abs(xyNext-xyCoord):
                            # it lies outside; shift by xyPrev's shift
                            kDeltas[p][xy] = kDeltas[pPrev][xy]
                    
                        else:
                            # it lies outside; shift by xyNext's shift
                            kDeltas[p][xy] = kDeltas[pNext][xy]
            
            for p, dlt in kDeltas.items():
                if p not in r:  # handle Zycon glyph 34 and similar cases
                    continue
                
                r[p][0] += dlt[0]
                r[p][1] += dlt[1]
        
        D = deltas.Deltas
        r = {p: D(int(round(v[0])), int(round(v[1]))) for p, v in r.items()}
        return r
    
    def findCommonPoints(self):
        """
        Analyzes the topology of points and associated coords, and returns a
        set of common points that could be used, or None if no common points
        are found.
        """
        
        dCoordToPoints = collections.defaultdict(set)
        
        for pointIndex, dd in self.items():
            for coord in dd:
                dCoordToPoints[coord].add(pointIndex)
        
        dPointSetToCoordSet = collections.defaultdict(set)
        
        for coord, ptSet in dCoordToPoints.items():
            dPointSetToCoordSet[frozenset(ptSet)].add(coord)
        
        # If any set length is greater than one, then choose the largest and
        # use it; otherwise return None.
        
        if not dPointSetToCoordSet:
            return None
        
        largest = max(len(s) for s in dPointSetToCoordSet.values())
        
        if largest < 2:
            return None
        
        for ptSet, coordSet in dPointSetToCoordSet.items():
            if len(coordSet) == largest:
                return ptSet
        
        return None  # this line should never be reached
    
    def makeInvertDict(self):
        """
        Makes and returns a simple dict of dicts. Normally, a PointDict object
        maps point indices to DeltasDict objects. This method inverts that,
        returning a dict of AxialCoordinate objects mapping to subdicts, which
        in turn map points to Deltas objects.
        """
        
        r = {}
        
        for pointIndex, ddObj in self.items():
            for coord, deltasObj in ddObj.items():
                r.setdefault(coord, {})[pointIndex] = deltasObj
        
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

