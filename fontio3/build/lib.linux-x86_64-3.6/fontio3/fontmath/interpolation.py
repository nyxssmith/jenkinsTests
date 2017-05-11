#
# interpolation.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for interpolation as done in variations fonts (i.e. 'gvar' data).
"""

# System imports
import collections
import itertools
#import sys

# -----------------------------------------------------------------------------

#
# Functions
#

def closeEnoughIn(d, key, delta=1.0e-5):
    """
    """
    
    return any(closeEnoughTuple(key, k, delta) for k in d)

def closeEnoughTuple(t1, t2, delta=1.0e-5):
    """
    Checks the two tuples for essential equality.
    
    >>> t1 = (4.001, -3.999)
    >>> t2 = (4, -4)
    >>> closeEnoughTuple(t1, t2)
    False
    >>> closeEnoughTuple(t1, t2, delta=0.01)
    True
    """
    
    delta = abs(delta)
    return all(abs(n1 - n2) <= delta for n1, n2 in zip(t1, t2))

def interp(trial, coords, deltas, **kwArgs):
    """
    This assumes trial is contained within coords, and that coords span R-space
    with ordinality len(trial). Also, coords[0] should be the origin. The delta
    array should conform to coords.
    
    >>> coords = [(0, 0), (0, 1), (1, 1)]
    >>> deltas = [(0, 0), (0, 100), (100, 100)]
    >>> interp((0.25, 0.5), coords, deltas)
    (25.0, 50.0)
    
    >>> deltas[1] = (0, 50)
    >>> interp((0.25, 0.5), coords, deltas)
    (25.0, 37.5)
    
    >>> coords = [(0, 0, 0), (1, 0.5, 0.5), (0, 1, 0), (0.25, 0, 1)]
    >>> deltas = [(0, 0), (100, 40), (-30, -30), (10, 60)]
    >>> interp((0.75, 0.5, 0.4275), coords, deltas)
    (70.125, 29.025)
    
    >>> coords = [(0, 0, 0), (1, 0.5, 0.5), (0, 1, 0), (0.25, 0, 1)]
    >>> deltas = [(0, 0), (100, 40), (-30, -30), (10, 60)]
    >>> interp((0.75, 0.5, 0.25), coords, deltas)
    (71.25, 26.25)
    
    >>> coords = [(0,), (0.25,), (1,)]
    >>> deltas = [(0, 0), (0, 80), (0, 100)]
    >>> interp((0.125,), coords, deltas)
    (0.0, 40.0)
    """
    
    cToD = dict(list(zip(coords, deltas)))
    
    for i in range(len(trial)):
        if closeEnoughIn(cToD, trial):
            return cToD[nearestKnot(cToD, trial)]
        
        cToD = moveOneStep(cToD, trial, i)
    
    if closeEnoughIn(cToD, trial):
        return cToD[nearestKnot(cToD, trial)]
    
    return None

def moveOneStep(coordsToDeltas, trial, trialIndex):
    """
    Move one step along the stepwise-linear interpolation process.
    
    >>> coords = [(0, 0, 0), (1, 0.5, 0.5), (0, 1, 0), (0.25, 0, 1)]
    >>> deltas = [(0, 0), (100, 40), (-30, -30), (10, 60)]
    >>> ctd = dict(list(zip(coords, deltas)))
    >>> trial = (0.75, 0.5, 0.25)
    >>> obj = moveOneStep(ctd, trial, 0)
    >>> for c in sorted(obj):
    ...   print(c, obj[c])
    (0.75, 0.3333333333333333, 0.6666666666666667) (69.99999999999999, 46.66666666666667)
    (0.75, 0.375, 0.375) (75.0, 30.0)
    (0.75, 0.625, 0.375) (67.5, 22.5)
    
    >>> obj = moveOneStep(obj, trial, 1)
    >>> for c in sorted(obj):
    ...   print(c, obj[c])
    (0.75, 0.5, 0.375) (71.25, 26.25)
    (0.75, 0.5, 0.5) (68.57142857142857, 32.85714285714286)
    
    >>> obj = moveOneStep(obj, trial, 2)
    >>> for c in sorted(obj):
    ...   print(c, obj[c])
    (0.75, 0.5, 0.25) (71.25, 26.25)
    """
    
    r = {}
    trialScalar = trial[trialIndex]
    scalarToSet = collections.defaultdict(set)
    
    for c in coordsToDeltas:
        scalarToSet[c[trialIndex]].add(c)
    
    scalarMax = max(scalarToSet)
    scalarMin = min(scalarToSet)
    
    if trialScalar > scalarMax:
        trialScalar = scalarMax
    
    if trialScalar < scalarMin:
        trialScalar = scalarMin
    
    newTrial = list(trial)
    newTrial[trialIndex] = trialScalar
    newTrial = tuple(newTrial)
    
    if closeEnoughIn(coordsToDeltas, newTrial):
        r[trial] = coordsToDeltas[nearestKnot(coordsToDeltas, newTrial)]
        return r
    
    if trialScalar in scalarToSet:
        for c in scalarToSet[trialScalar]:
            r[c] = coordsToDeltas[c]
        
        del scalarToSet[trialScalar]
        
        if not scalarToSet:
            return r
    
    # At this point we know trialScalar itself is not in the dataset
    
    lowPart = set()
    highPart = set()
    
    for n, cSet in scalarToSet.items():
        if n < trialScalar:
            lowPart.update(cSet)
        else:
            highPart.update(cSet)
    
    if not lowPart and highPart:
        raise ValueError("Unexpected data shape!")
    
    for c1, c2 in itertools.product(lowPart, highPart):
        #print(c1, c2, file=sys.stderr)
        t = (trialScalar - c1[trialIndex]) / (c2[trialIndex] - c1[trialIndex])
        c = [(1-t)*n1 + t*n2 for n1, n2 in zip(c1, c2)]
        c[trialIndex] = trialScalar  # get rid of rounding fluff...
        c = tuple(c)
        
        if c not in r:
            dlt1 = coordsToDeltas[c1]
            dlt2 = coordsToDeltas[c2]
            r[c] = tuple((1-t)*n1 + t*n2 for n1, n2 in zip(dlt1, dlt2))
    
    return r

def nearestKnot(d, trial):
    allKnots = sorted(d)
    isClose = [closeEnoughTuple(trial, x) for x in allKnots]
    
    if not any(isClose):
        return None
    
    return allKnots[isClose.index(True)]

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

