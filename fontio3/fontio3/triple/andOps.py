#
# andOps.py
#
# Copyright © 2008, 2010, 2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by and() on Triple objects.
"""

# Other imports
from fontio3.fontmath import rational
from fontio3.triple import triple, utilities
from fontio3.utilities import binlist, sampleGenerator
from functools import reduce

# -----------------------------------------------------------------------------

#
# Private functions
#

def _and_CC_CC(t1, t2):
    """
    Returns an iterator of the bitwise-AND of t1 (CC) and t2 (CC).
    
    >>> T = triple.Triple
    >>> list(_and_CC_CC(T(1, 11, 2), T(10, 15, 5)))
    [(0, 1, 1), (2, 14, 6)]
    """
    
    if len(t1) < len(t2):
        s = set(a & b for a in t1 for b in t2)
    else:
        s = set(a & b for a in t2 for b in t1)
    
    return utilities.tripleIteratorFromIterable(s)

def _and_CC_COOC(t1, t2):
    """
    Returns an iterator of the bitwise-AND of t1 (CC) and t2 (CO or OC).
    """
    
    for n in t1:
        for obj in _andConstant(t2, n):
            yield obj

def _and_OO_CC(t1, t2):
    """
    Returns an iterator of the bitwise-AND of t1 (OO) and t2 (CC).
    """
    
    for n in t2:
        for obj in _andConstant(t1, n):
            yield obj

def _and_COOCOO_COOCOO(t1, t2):
    """
    Returns an iterator of the bitwise-AND of t1 (OO) and t2 (CO, OC or OO).
    
    >>> T = triple.Triple
    >>> list(_and_COOCOO_COOCOO(T(None, None, 7, 1), T(None, None, 5, 3)))
    [(*, *, 1, phase=0)]
    >>> list(_and_COOCOO_COOCOO(T(None, None, 16, 5), T(None, None, 8, 2)))
    [(*, *, 16, phase=0)]
    >>> list(_and_COOCOO_COOCOO(T(None, None, 32, 11), T(None, None, 8, 6)))
    [(*, *, 32, phase=2), (*, *, 32, phase=10)]
    >>> list(_and_COOCOO_COOCOO(T(None, None, 24, 13), T(None, None, 9, 7)))
    [(*, *, 8, phase=0), (*, *, 8, phase=1), (*, *, 8, phase=4), (*, *, 8, phase=5)]
    """
    
    Triple = triple.Triple
    mask1 = _lowMask(t1.skip)
    mask2 = _lowMask(t2.skip)
    
    if mask1:
        n = len(mask1)
        mask1 = binlist(t1.phase, n)[-n:]
    
    if mask2:
        n = len(mask2)
        mask2 = binlist(t2.phase, n)[-n:]
    
    len1, len2 = len(mask1), len(mask2)
    
    if len1 == 0 and len2 == 0:
        yield Triple(None, None, 1)
    
    elif len1 == len2:
        finalMask = [n & mask2[i] for i, n in enumerate(mask1)]
        yield Triple(None, None, 2 ** len1, reduce(_f, finalMask))
    
    else:
        if len1 < len2:
            shortMask, longMask = mask1, mask2
            shortLen, longLen = len1, len2
        else:
            shortMask, longMask = mask2, mask1
            shortLen, longLen = len2, len1
        
        diffLen = longLen - shortLen
        finalLow = [n & shortMask[i] for i, n in enumerate(longMask[diffLen:])]
        
        for finalHigh in sampleGenerator([list(range(n + 1)) for n in longMask[:diffLen]], 0):
            finalMask = finalHigh + finalLow
            yield Triple(None, None, 2 ** len(finalMask), reduce(_f, finalMask))

def _andConstant(t, k):
    """
    Returns an iterator of Triples with the results of a constant logical-ANDed
    with t.
    
    >>> T = triple.Triple
    >>> list(_andConstant(T(1, 100, 1), 0))
    [(0, 1, 1)]
    >>> list(_andConstant(T(0, None, 12), 4))
    [(0, 8, 4)]
    >>> list(_andConstant(T(14, 770, 7), 5))
    [(1, 7, 3), (0, 10, 5)]
    >>> list(_andConstant(T(None, None, 7, 2), -3))
    [(*, *, 28, phase=0), (*, *, 28, phase=9), (*, *, 28, phase=16), (*, *, 28, phase=21)]
    >>> list(_andConstant(T(None, 303, 7), -3))
    [(*, 308, 28), (*, 317, 28), (*, 324, 28), (*, 301, 28)]
    >>> list(_andConstant(T(51, None, 7), -3))
    [(56, *, 28), (65, *, 28), (72, *, 28), (49, *, 28)]
    >>> list(_andConstant(T(16, 37, 7), -3))
    [(28, 56, 28), (16, 44, 28), (21, 49, 28)]
    """
    
    Triple = triple.Triple
    
    if k == 0:
        yield Triple(0, 1, 1)
    
    elif k == -1:
        yield t
    
    elif k < 0:
        # because binlist only works with non-negative numbers, create an
        # equivalent positive value for k which will result in the same output
        bl = binlist(-k-1)
        pow2 = 2 ** len(bl)
        cycle = pow2 // rational.gcf(pow2, t.skip)
        bigCycle = cycle * t.skip
        
        if t.start is None and t.stop is None:
            for start in range(t.phase, t.phase + bigCycle, t.skip):
                yield Triple(None, None, bigCycle, start & k)
        
        elif t.start is None:
            last = t.stop - t.skip
            d = dict((n % bigCycle, n) for n in range(last, last - bigCycle, -t.skip))
            
            for start in range(t.phase, t.phase + bigCycle, t.skip):
                yield Triple(None, (d[start] & k) + bigCycle, bigCycle, start & k)
        
        elif t.stop is None:
            d = dict((n % bigCycle, n) for n in range(t.start, t.start + bigCycle, t.skip))
            
            for start in range(t.phase, t.phase + bigCycle, t.skip):
                yield Triple(d[start] & k, None, bigCycle, start & k)
        
        else:
            last = t.stop - t.skip
            dStarts = {}
            
            for n in range(t.start, t.start + bigCycle, t.skip):
                if n > last:
                    break
                
                dStarts[n % bigCycle] = n & k
            
            dStops = {}
            
            for n in range(last, last - bigCycle, -t.skip):
                if n < t.start:
                    break
                
                dStops[n % bigCycle] = (n & k) + bigCycle
            
            for start in range(t.phase, t.phase + bigCycle, t.skip):
                if start in dStarts:
                    actualStart = dStarts[start]
                    stop = dStops.get(start, actualStart + bigCycle)
                    yield Triple(actualStart, stop, bigCycle)
    
    else:
        bl = binlist(k)
        pow2 = 2 ** len(bl)
        cycle = pow2 // rational.gcf(pow2, t.skip)
        
        if t.start is None:
            if t.stop is None:
                start = t.phase
                stop = start + cycle * t.skip
            
            else:
                stop = t.stop
                start = stop - cycle * t.skip
        
        elif t.stop is None:
            start = t.start
            stop = start + cycle * t.skip
        
        else:
            start = t.start
            stop = min(t.stop, start + cycle * t.skip)
        
        s = set(n & k for n in range(start, stop, t.skip))
        
        for t in utilities.tripleIteratorFromIterable(s):
            yield t

def _f(x, y): return 2 * x + y

def _lowMask(n):
    """
    For a positive value n returns a list containing some number of zeroes,
    where the specific number matches the number in the low-order bits of n.
    
    >>> _lowMask(16)
    [0, 0, 0, 0]
    >>> _lowMask(10)
    [0]
    >>> _lowMask(9)
    []
    """
    
    assert n > 0, "Must pass positive value to _lowMask!"
    it = reversed(binlist(n))
    count = 0
    
    while not next(it):
        count += 1
    
    return [0] * count

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_and_dispatchTable = {
  ((False, False), (False, False)): _and_CC_CC,
  ((False, False), (False, True)): _and_CC_COOC,
  ((False, False), (True, False)): _and_CC_COOC,
  ((False, True), (False, True)): _and_COOCOO_COOCOO,
  ((False, True), (True, False)): _and_COOCOO_COOCOO,
  ((True, False), (True, False)): _and_COOCOO_COOCOO,
  ((True, True), (False, False)): _and_OO_CC,
  ((True, True), (False, True)): _and_COOCOO_COOCOO,
  ((True, True), (True, False)): _and_COOCOO_COOCOO,
  ((True, True), (True, True)): _and_COOCOO_COOCOO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def andOp(t1, t2):
    """
    Returns a list of Triples representing the bitwise-AND of the input
    Triples. No particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        
        if (kind1, kind2) in _and_dispatchTable:
            r = _and_dispatchTable[(kind1, kind2)](t1, t2)
        else:
            r = _and_dispatchTable[(kind2, kind1)](t2, t1)
    
    except AttributeError:
        r = _andConstant(t1, t2)
    
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

