#
# deltas_dict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for deltas (x and y) associated with particular AxialCoordinates
objects.
"""

# System imports
import functools
import itertools
import operator

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.gvar import axial_coordinates, deltas
    
# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(d, **kwArgs):
    if not d:
        return True
    
    logger = kwArgs['logger']
    v = [tuple(float(x) for x in t) for t in d]
    tSignum = lambda t: tuple((x > 0) - (x < 0) for x in t)
    v2 = sorted(v, key=tSignum)
    ig = operator.itemgetter
    count = len(v2[0])
    
    for k, g in itertools.groupby(iter(v2), tSignum):
        v3 = list(g)
        
        if len(v3) == 1:
            continue
        
        colsToCheck = []
        
        for i in range(count):
            if len({t[i] for t in v3}) > 1:
                colsToCheck.append(i)
        
        if len(colsToCheck) < 2:
            continue
        
        checkSet = {tuple(sorted(v3, key=ig(i))) for i in colsToCheck}
        
        if len(checkSet) > 1:
            logger.error((
              'Vxxxx',
              (v,),
              "The AxialCoordinates keys (%s) are not well ordered."))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class DeltasDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping AxialCoordinates objects to Deltas objects. These represent
    all the deltas for a single point of a single glyph.
    
    >>> ao = ('wght', 'wdth')
    >>> AC = axial_coordinate.AxialCoordinate
    >>> ACS = axial_coordinates.AxialCoordinates
    >>> key1 = ACS((AC(1.0/3), AC(-0.25)), axisOrder=ao)
    >>> key2 = ACS((AC(0.0), AC(0.5)), axisOrder=ao)
    >>> val1 = deltas.Deltas(250, -30)
    >>> val2 = deltas.Deltas(-40, -40)
    >>> obj = DeltasDict({key1: val1, key2: val2})
    >>> obj.pprint()
    (wght 0.0, wdth 0.5):
      Delta X: -40
      Delta Y: -40
    (wght 0.333, wdth -0.25):
      Delta X: 250
      Delta Y: -30
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_keyfollowsprotocol = True,
        item_pprintlabelfunc = str,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def interpolateDelta(self, coord):
        """
        Given a normalized (-1..1) coordinate, return a Deltas object that
        represents the needed shifts. This follows the algorithm documented in
        the most recent Apple 'gvar' document:
        
        https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6gvar.html
        
        Note that we do not stop after finding the first match; this is needed
        to account for intermediates (among other effects).
        
        Note also that coord must be normalized; this method has no access to
        the Fvar object to do normalization.
        
        >>> ao = ('wght', 'wdth')
        >>> AC = axial_coordinate.AxialCoordinate
        >>> ACS = axial_coordinates.AxialCoordinates
        >>> key1 = ACS((AC(1.0), AC(-1.0)), axisOrder=ao)
        >>> key2 = ACS((AC(0.0), AC(1.0)), axisOrder=ao)
        >>> val1 = deltas.Deltas(250, -30)
        >>> val2 = deltas.Deltas(-40, -40)
        >>> obj = DeltasDict({key1: val1, key2: val2})
        
        Coordinates that are actually present simply return their associated
        deltas directly:
        
        >>> print(obj.interpolateDelta((1.0, -1.0)))
        (250, -30)
        
        Coordinates that are between two keys return the interpolation:
        
        >>> print(obj.interpolateDelta((0.5, -0.25)))
        (31, -4)
        """
        
        dx = dy = None
        
        for keyCoord, dlt in self.items():
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
            
            if factor:
                if dx is None:
                    dx = dy = 0
                
                dx += factor * dlt.x
                dy += factor * dlt.y
        
        if dx is None:
            return None
        
        return deltas.Deltas(int(round(dx)), int(round(dy)))
        
        
#         dx = dy = None
#         
#         for keyCoord, dlt in self.items():
#             ed = dlt.effectiveDomain
#             axisFactors = []
#             
#             if ed is not None:
#                 if all(
#                   ((c >= ed.edge1[i]) and (c <= ed.edge2[i]))
#                   for i, c in enumerate(coord)):
#                     
#                     it = zip(coord, keyCoord, ed.edge1, ed.edge2)
#                     
#                     for c, cPeak, cMin, cMax in it:
#                         if not cPeak:
#                             continue
#                         
#                         if c == cPeak:
#                             axisFactors.append(1.0)
#                         elif c < cPeak:
#                             axisFactors.append((c - cMin) / (cPeak - cMin))
#                         else:
#                             axisFactors.append((cMax - c) / (cMax - cPeak))
#             
#             else:
#                 important = []
#                 it = enumerate(zip(keyCoord, coord))
#                 
#                 for i, (keyValue, coordValue) in it:
#                     if (not keyValue):
#                         # we ignore a zero key coord for purposes of
#                         # determining whether or not this tuple applies (i.e.
#                         # whether its column index gets added to the important
#                         # list)
#                         continue
#                 
#                     if (not coordValue):
#                         # if the key coord is nonzero but the client-specified
#                         # coordinate is zero, then the scalar product will be
#                         # zero and this tuple will have no effect, so break out
#                         # of the column loop.
#                         del important[:]
#                         break
#                 
#                     if (keyValue > 0) != (coordValue > 0):
#                         del important[:]
#                         break
#                 
#                     if abs(coordValue) > abs(keyValue):
#                         del important[:]
#                         break
#                 
#                     important.append(i)
#                 
#                 if important:
#                     axisFactors = [coord[i] / keyCoord[i] for i in important]
#             
#             if axisFactors:
#                 fullFactor = functools.reduce(operator.mul, axisFactors)
#                 dScaled = dlt.magnified(fullFactor, fullFactor)
#                 
#                 if dx is None:
#                     dx, dy = dScaled.x, dScaled.y
#                 
#                 else:
#                     dx += dScaled.x
#                     dy += dScaled.y
#         
#         if dx is None:
#             return None
#         
#         return deltas.Deltas(int(round(dx)), int(round(dy)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.gvar import axial_coordinate

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

