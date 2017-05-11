#
# divOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by div() on Triple objects.
"""

# Other imports
from fontio3.fontmath import rational
from fontio3.triple import collection, triple

# -----------------------------------------------------------------------------

#
# Constants
#

T = triple.Triple
C = collection.Collection

# -----------------------------------------------------------------------------

#
# Private functions
#

def _div_CC_CC(t1, t2):
    """
    Returns an iterator of Triples representing the division of t1 (CC) by t2
    (CC).
    
    ### C(_div_CC_CC(T(25, 55, 5), T(3, 9, 3)))
    Singles: [10, 11, 13, 15, 16], Ranges: [(4, 9, 1)]
    """
    
    return C(_div_CC_CC_gen(t1, t2)).tripleIterator()

def _div_CC_CC_gen(t1, t2):
    for divisor in t2:
        for obj in _divConstant(t1, divisor):
            yield obj
        
        if divisor >= t1.stop:
            break

def _div_CC_CO(t1, t2):
    """
    Returns an iterator of Triples representing the division of t1 (CC) by t2
    (CO).
    
    ### C(_div_CC_CO(T(10, 100, 5), T(-14, None, 4)))
    Singles: [6, 8, 14], Ranges: [(-16, 5, 1), (9, 15, 2), (-45, -15, 5), (5, 50, 5), (-48, -13, 5), (7, 52, 5)]
    """
    
    n = max(abs(t1.start), abs(t1.stop - t1.skip))
    clipStart = t2.findMember(True, False, -n)
    
    if clipStart is None:
        clipStart = t2.start
    
    clipLast = t2.findMember(False, False, n)
    return _div_CC_CC(t1, T(clipStart, clipLast + t2.skip, t2.skip))

def _div_CC_OC(t1, t2):
    n = max(abs(t1.start), abs(t1.stop - t1.skip))
    clipStart = t2.findMember(True, False, -n)
    clipLast = t2.findMember(False, False, n)
    
    if clipLast is None:
        clipLast = t2.stop - t2.skip
    
    return _div_CC_CC(t1, T(clipStart, clipLast + t2.skip, t2.skip))

def _div_CC_OO(t1, t2):
    n = max(abs(t1.start), abs(t1.stop - t1.skip))
    clipStart = t2.findMember(True, False, -n)
    
    if clipStart is None:
        clipStart = t2.start
    
    clipLast = t2.findMember(False, False, n)
    
    if clipLast is None:
        clipLast = t2.stop - t2.skip
    
    return _div_CC_CC(t1, T(clipStart, clipLast + t2.skip, t2.skip))

def _div_CO_CC(t1, t2):
    for n in t2:
        for obj in _divConstant(t1, n):
            yield obj

def _div_CO_CO(t1, t2):
    yield T((None if t1.start < 0 or t2.start < 0 else 0), None, 1)

def _div_CO_OC(t1, t2):
    t1Neg, t1Pos = t1.signedParts()  # t1Neg, t1Pos guaranteed to be (CC or None, CO)
    t2Neg, t2Pos = t2.signedParts()  # t2Neg, t2Pos guaranteed to be (OC, CC or None)
    
    if t1Neg is not None:
        for obj in _div_CC_OC(t1Neg, t2Neg):
            yield obj
        
        if t2Pos is not None:
            for obj in _div_CC_CC(t1Neg, t2Pos):
                yield obj
    
    if t2Pos is not None:
        for obj in _div_CO_CC(t1Pos, t2Pos):
            yield obj
    
    yield T(None, (1 if t1Pos.start else 0), 1)

def _div_OC_CC(t1, t2):
    for n in t2:
        for obj in _divConstant(t1, n):
            yield obj

def _div_OC_CO(t1, t2):
    t1Neg, t1Pos = t1.signedParts()  # t1Neg, t1Pos guaranteed to be (OC, CC or None)
    t2Neg, t2Pos = t2.signedParts()  # t2Neg, t2Pos guaranteed to be (CC or None, CO)
    
    if t1Pos is not None:
        for obj in _div_CC_CO(t1Pos, t2Pos):
            yield obj
        
        if t2Neg is not None:
            for obj in _div_CC_CC(t1Pos, t2Neg):
                yield obj
    
    if t2Neg is not None:
        for obj in _div_OC_CC(t1Neg, t2Neg):
            yield obj
    
    yield T(None, 0, 1)

def _div_OC_OC(t1, t2):
    t1Last = t1.stop - t1.skip
    t2Last = t2.stop - t2.skip
    yield T((None if t1Last < 0 or t2Last < 0 else 0), None, 1)

def _divConstant(t, k):
    """
    Returns an iterator of Triples resulting from the division of the specified
    Triple by the specified constant.
    
    ### C(_divConstant(T(15, None, 4), -1))
    Ranges: [(*, -11, 4)]
    ### C(_divConstant(T(150, 45000, 50), 64))
    Ranges: [(2, 703, 1)]
    ### C(_divConstant(T(None, None, 7, 2), 5))
    Ranges: [(*, *, 7, phase=0), (*, *, 7, phase=1), (*, *, 7, phase=3), (*, *, 7, phase=4), (*, *, 7, phase=6)]
    ### C(_divConstant(T(None, None, 12, 2), 8))
    Ranges: [(*, *, 3, phase=0), (*, *, 3, phase=1)]
    ### C(_divConstant(T(None, 122, 12, 2), 8))
    Ranges: [(*, 15, 3), (*, 16, 3)]
    ### C(_divConstant(T(50, None, 12, 2), 8))
    Ranges: [(6, *, 3), (7, *, 3)]
    ### C(_divConstant(T(50, 110, 12), 8))
    Singles: [7, 10], Ranges: [(6, 15, 3)]
    ### C(_divConstant(T(3, None, 5), 0))
    Traceback (most recent call last):
      ...
    ZeroDivisionError: _divConstant called with zero constant!
    """
    
    if k == 0:
        raise ZeroDivisionError("_divConstant called with zero constant!")
    
    if k < 0:
        t = -t
        k = -k
    
    if k == 1:
        yield t
    
    elif k >= t.skip:
        newStart = (None if t.start is None else t.start // k)
        newStop = (None if t.stop is None else 1 + (t.stop - t.skip) // k)
        yield T(newStart, newStop, 1)
    
    else:
        gcf = rational.gcf(t.skip, k)
        phaseSkip = t.skip // gcf
        
        if t.start is None and t.stop is None:
            for i in T(t.phase, t.phase + phaseSkip * k, t.skip):
                yield T(None, None, phaseSkip, i // k)
        
        elif t.start is None:
            for i in T(t.stop - phaseSkip * k, t.stop, t.skip):
                yield T(None, i // k + phaseSkip, phaseSkip)
        
        elif t.stop is None:
            for i in T(t.start, t.start + phaseSkip * k, t.skip):
                yield T(i // k, None, phaseSkip)
        
        else:
            start = t.start
            loopStop = min(t.stop, t.start + phaseSkip * k)
            
            while start < loopStop:
                startDiv = start // k
                thisLast = t.stop - t.skip
                thisLastDiv = thisLast // k
                
                while thisLastDiv % phaseSkip != startDiv % phaseSkip:
                    thisLast -= t.skip
                    thisLastDiv = thisLast // k
                
                yield T(startDiv, thisLastDiv + phaseSkip, phaseSkip)
                start += t.skip

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_div_dispatchTable = {
  ((False, False), (False, False)): _div_CC_CC,
  ((False, False), (False, True)): _div_CC_CO,
  ((False, False), (True, False)): _div_CC_OC,
  ((False, False), (True, True)): _div_CC_OO,
  ((False, True), (False, False)): _div_CO_CC,
  ((False, True), (False, True)): _div_CO_CO,
  ((False, True), (True, False)): _div_CO_OC,
  ((True, False), (False, False)): _div_OC_CC,
  ((True, False), (False, True)): _div_OC_CO,
  ((True, False), (True, False)): _div_OC_OC}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def divOp(t1, t2):
    """
    Returns an iterator of Triples representing the integer division of t1 by
    t2. No particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        t = (kind1, kind2)
        
        if t in _div_dispatchTable:
            r = _div_dispatchTable[(kind1, kind2)](t1, t2)
        else:
            r = iter([T(None, None, 1)])
    
    except AttributeError:
        r = _divConstant(t1, t2)
    
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

