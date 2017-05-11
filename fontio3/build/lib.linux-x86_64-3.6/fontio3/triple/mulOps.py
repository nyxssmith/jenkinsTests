#
# mulOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by mul() on Triple objects.
"""

# Other imports
from fontio3.fontmath import rational
from fontio3.triple import triple

# -----------------------------------------------------------------------------

#
# Constants
#

T = triple.Triple

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

def _mul_CC_CC(t1, t2):
    """
    Returns an iterator of Triples representing the product of t1 (CC) and t2
    (CC).
    
    >>> list(_mul_CC_CC(T(1, 11, 2), T(2, 11, 3)))
    [(2, 22, 4), (5, 55, 10), (8, 88, 16)]
    """
    
    if len(t1) < len(t2):
        for n in t1:
            yield _mulConstant(t2, n)
    else:
        for n in t2:
            yield _mulConstant(t1, n)

def _mul_CC_COOC(t1, t2):
    """
    Returns an iterator of Triples representing the product of t1 (CC) and t2
    (CO or OC).
    
    >>> list(_mul_CC_COOC(T(1, 9, 2), T(3, None, 7)))
    [(3, *, 7), (9, *, 21), (15, *, 35), (21, *, 49)]
    """
    
    for n in t1:
        yield _mulConstant(t2, n)

def _mul_CO_CO(t1, t2):
    """
    Returns an iterator of Triples representing the product of t1 (CO) and t2
    (CO).
    
    >>> list(_mul_CO_CO(T(18, None, 3), T(5, None, 5)))
    [(90, *, 15)]
    >>> list(_mul_CO_CO(T(4, None, 3), T(-6, None, 9)))
    [(*, *, 3, phase=0)]
    """
    
    gcf1 = (rational.gcf(t1.skip, t1.phase) if t1.phase else t1.skip)
    gcf2 = (rational.gcf(t2.skip, t2.phase) if t2.phase else t2.skip)
    newStart = (None if t1.start < 0 or t2.start < 0 else t1.start * t2.start)
    yield T(newStart, None, gcf1 * gcf2)

def _mul_CO_OC(t1, t2):
    """
    Returns an iterator of Triples representing the product of t1 (CO) and t2
    (OC).
    
    >>> list(_mul_CO_OC(T(4, None, 3), T(None, 15, 9)))
    [(*, *, 3, phase=0)]
    >>> list(_mul_CO_OC(T(21, None, 7), T(None, 0, 4)))
    [(*, -56, 28)]
    """
    
    gcf1 = (rational.gcf(t1.skip, t1.phase) if t1.phase else t1.skip)
    gcf2 = (rational.gcf(t2.skip, t2.phase) if t2.phase else t2.skip)
    newSkip = gcf1 * gcf2
    
    if t1.start >= 0 and (t2.stop - t2.skip) < 0:
        newStop = t1.start * (t2.stop - t2.skip) + newSkip
    else:
        newStop = None
    
    yield T(None, newStop, newSkip)

def _mul_OC_OC(t1, t2):
    """
    Returns a list representing the product of t1 (OC) and t2 (OC).
    
    >>> list(_mul_OC_OC(T(None, 0, 5), T(None, 0, 7)))
    [(35, *, 35)]
    >>> list(_mul_OC_OC(T(None, 0, 5), T(None, 6, 3)))
    [(*, *, 15, phase=0)]
    """
    
    gcf1 = (rational.gcf(t1.skip, t1.phase) if t1.phase else t1.skip)
    gcf2 = (rational.gcf(t2.skip, t2.phase) if t2.phase else t2.skip)
    newSkip = gcf1 * gcf2
    selfLast = t1.stop - t1.skip
    otherLast = t2.stop - t2.skip
    newStart = (None if selfLast > 0 or otherLast > 0 else selfLast * otherLast)
    yield T(newStart, None, gcf1 * gcf2)

def _mul_OO_CC(t1, t2):
    """
    Returns an iterator of Triples representing the product of t1 (OO) and t2
    (CC). No attempt is made to remove potential duplicate entries (for
    instance, an entry in the returned list with a skip of 4 might entirely
    duplicate one with a skip of 2).
    
    >>> list(_mul_OO_CC(T(None, None, 5, 2), T(1, 9, 2)))
    [(*, *, 5, phase=2), (*, *, 15, phase=6), (*, *, 25, phase=10), (*, *, 35, phase=14)]
    """
    
    for n in t2:
        yield _mulConstant(t1, n)

def _mul_OO_CO(t1, t2):
    """
    Returns a list representing the product of t1 (OO) and t2 (CO).
    Because of the prime fallout problem, the results of this method are
    usually supersets of the actual answers, which await meta-Triples (see
    the docstring for the _mul_OO_OO method).
    
    >>> list(_mul_OO_CO(T(None, None, 5, 0), T(0, None, 4)))
    [(*, *, 20, phase=0)]
    """
    
    a, b, c, d = t1.phase, t1.skip, t2.start, t2.skip
    
    if a == 0:
        if c == 0:
            # (bi)(dj) case
            yield T(None, None, b * d, 0)
        
        else:
            gcf = rational.gcf(abs(c), d)
            cNew = c // gcf
            dNew = d // gcf
            
            if (1 - cNew) % dNew == 0 or (-1 - cNew) % dNew == 0:
                yield T(None, None, b * gcf, 0)
            else:
                yield T(None, None, b, 0)
    
    elif c == 0:
        yield T(None, None, d, 0)
    
    else:
        yield T(None, None, 1, 0)

def _mul_OO_OC(t1, t2):
    """
    Returns a list representing the product of t1 (OO) and t2 (OC).
    Because of the prime fallout problem, the results of this method are
    usually supersets of the actual answers, which await meta-Triples (see
    the docstring for the _mul_OO_OO method).
    
    >>> list(_mul_OO_OC(T(None, None, 5, 0), T(None, 0, 4)))
    [(*, *, 20, phase=0)]
    >>> list(_mul_OO_OC(T(None, None, 5, 0), T(None, 10, 4)))
    [(*, *, 10, phase=0)]
    >>> list(_mul_OO_OC(T(None, None, 5, 2), T(None, 0, 3)))
    [(*, *, 1, phase=0)]
    """
    
    a, b, c, d = t1.phase, t1.skip, t2.stop - t2.skip, t2.skip
    
    if a == 0:
        if c == 0:
            # (bi)(-dj) case, d>0, j>=0, i any integer
            # this becomes (-bd)(ij), and if j=1, this spans all values
            yield T(None, None, b * d, 0)
        
        else:
            # (bi)(c-dj) case, d>0, j>=0, i any integer
            gcf = rational.gcf(abs(c), d)
            cNew = c // gcf
            dNew = d // gcf
            
            if (1 - cNew) % dNew == 0 or (-1 - cNew) % dNew == 0:
                yield T(None, None, b * gcf, 0)
            else:
                yield T(None, None, b, 0)  # fallback case
    
    elif c == 0:
        yield T(None, None, d, 0)  # fallback case
    
    else:
        yield T(None, None, 1, 0)  # full fallback case

def _mul_OO_OO(t1, t2):
    """
    Given two doubly-open Triples (None, None, a, b) and (None, None, c,
    d), the actual product is the union of the following two meta-Triples:
    
        (None, None, (bc, None, ac), (bd, None, ad))
        (None, None, (ac-bc, None, ac), ((a-b)(c-d), None, ac-ad))
    
    However, there is currently no support for meta-Triples (i.e. Triples
    whose starts, stops, skips and/or phases are themselves Triples). This
    limitation could be addressed at some point in the future.
    
    For the time being this method usually returns (None, None, 1, 0),
    which is at least a superset of the actual answer. There are some
    special cases handled here, such as both Triples having a phase of
    zero, or one having a phase of zero and certain t2 conditions
    holding for the t2, where a real answer is returned.
    
    >>> list(_mul_OO_OO(T(None, None, 2, 0), T(None, None, 4, 0)))
    [(*, *, 8, phase=0)]
    >>> list(_mul_OO_OO(T(None, None, 2, 0), T(None, None, 4, 1)))
    [(*, *, 2, phase=0)]
    >>> list(_mul_OO_OO(T(None, None, 4, 2), T(None, None, 2, 0)))
    [(*, *, 4, phase=0)]
    >>> list(_mul_OO_OO(T(None, None, 2, 0), T(None, None, 7, 3)))
    [(*, *, 1, phase=0)]
    """
    
    finalCase = False
    
    if t1.phase == 0:
        if t2.phase == 0:
            yield T(None, None, t1.skip * t2.skip, 0)
        
        else:
            b = t1.skip * t2.phase
            c = t1.skip * t2.skip
            newSkip = rational.gcf(b, c)
            b //= newSkip
            c //= newSkip
            
            if (1 - b) % c == 0 or (-1 - b) % c == 0:
                yield T(None, None, newSkip, 0)
            else:
                yield T(None, None, 1, 0)  # fallback case
    
    elif t2.phase == 0:
        b = t2.skip * t1.phase
        c = t2.skip * t1.skip
        newSkip = rational.gcf(b, c)
        b //= newSkip
        c //= newSkip
        
        if (1 - b) % c == 0 or (-1 - b) % c == 0:
            yield T(None, None, newSkip, 0)
        else:
            finalCase = True
    
    else:
        finalCase = True
    
    if finalCase:
        # We have (a+bi) times (c+di)
        # This breaks into ac + f * (xi + yj + zij)
        a, b, c, d = t1.phase, t1.skip, t2.phase, t2.skip
        x, y, z = b * c, a * d, b * d
        f = rational.gcf(rational.gcf(x, y), z)
        x //= f
        y //= f
        z //= f
        
        if abs(x) == 1 or abs(y) == 1:
            yield T(None, None, f, (a * c) % f)
        elif (1 - y) % z == 0 or (-1 - y) % z == 0 or (1 - x) % z == 0 or (-1 - x) % z == 0:
            yield T(None, None, f, (a * c) % f)
        else:
            yield T(None, None, 1, 0)  # fallback case

def _mulConstant(t1, k):
    """
    Returns a Triple representing the product of t1 and the specified
    constant.
    
    >>> _mulConstant(T(None, None, 7, 2), 4)
    (*, *, 28, phase=8)
    >>> _mulConstant(T(None, 12, 7), 3)
    (*, 36, 21)
    >>> _mulConstant(T(2, None, 11), 5)
    (10, *, 55)
    >>> _mulConstant(T(3, 17, 7), 8)
    (24, 136, 56)
    >>> _mulConstant(T(None, None, 7, 2), -3)
    (*, *, 21, phase=15)
    >>> _mulConstant(T(None, 24, 19), -2)
    (-10, *, 38)
    >>> _mulConstant(T(4, None, 19), -2)
    (*, 30, 38)
    >>> _mulConstant(T(-10, 20, 3), -4)
    (-68, 52, 12)
    >>> _mulConstant(T(None, None, 5, 2), 0)
    (0, 1, 1)
    """
    
    if k > 0:
        if t1.start is None:
            if t1.stop is None:
                return T(None, None, t1.skip * k, t1.phase * k)
            
            return T(None, t1.stop * k, t1.skip * k)
        
        elif t1.stop is None:
            return T(t1.start * k, None, t1.skip * k)
        
        return T(t1.start * k, t1.stop * k, t1.skip * k)
    
    elif k < 0:
        newSkip = t1.skip * -k
        
        if t1.start is None:
            if t1.stop is None:
                return T(None, None, newSkip, (k * (t1.phase - t1.skip)) % newSkip)
            
            return T((t1.stop - t1.skip) * k, None, newSkip)
        
        elif t1.stop is None:
            return T(None, t1.start * k + newSkip, newSkip)
        
        return T((t1.stop - t1.skip) * k, t1.start * k + newSkip, newSkip)
    
    return T(0, 1, 1)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_mul_dispatchTable = {
  ((False, False), (False, False)): _mul_CC_CC,
  ((False, False), (False, True)): _mul_CC_COOC,
  ((False, False), (True, False)): _mul_CC_COOC,
  ((False, True), (False, True)): _mul_CO_CO,
  ((False, True), (True, False)): _mul_CO_OC,
  ((True, False), (True, False)): _mul_OC_OC,
  ((True, True), (False, False)): _mul_OO_CC,
  ((True, True), (False, True)): _mul_OO_CO,
  ((True, True), (True, False)): _mul_OO_OC,
  ((True, True), (True, True)): _mul_OO_OO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def mulOp(t1, t2):
    """
    Returns a list of Triples representing the product of the input Triples. No
    particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        
        if (kind1, kind2) in _mul_dispatchTable:
            r = _mul_dispatchTable[(kind1, kind2)](t1, t2)
        else:
            r =  _mul_dispatchTable[(kind2, kind1)](t2, t1)
    
    except AttributeError:
        r = iter([_mulConstant(t1, t2)])
    
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

