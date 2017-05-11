#
# powOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by pow_() on Triple objects. Remember that these
operations occur piecewise on individual values. Thus, Triple(1, 5, 2) raised
to the power 2 yields two values, 1 and 9, and NOT the values of multiplying
the Triple by itself (1, 3 and 9).

So remember: t ** k is NOT the same as multiplying t by itself k times!
"""

# System imports
import math

# Other imports
from fontio3.triple import collection, triple, utilities

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

if 0:
    def __________________(): pass

def _minim(t):
    """
    Given a Triple t, this method returns the hypothetical member whose
    absolute value is closest to zero. The "hypothetical" member is of a Triple
    whose skip and phase are the same as t's, but whose start and stop are
    open.
    
    ### _minim(T(-100, None, 7))
    -2
    ### _minim(T(3, 13, 2))
    1
    """
    
    n1 = t.phase  # guaranteed non-negative
    n2 = n1 - t.skip  # guaranteed negative
    return (n1 if abs(n1) <= abs(n2) else n2)

def _pow_any_CC(t1, t2):
    """
    Returns an iterator over Triples representing t1 (any kind) raised to the
    power t2 (CC).
    
    ### C(_pow_any_CC(T(1, 9, 2), T(1, 3, 1))).asList()
    [(1, 11, 2), (25, 33, 8), (49, 57, 8)]
    ### C(_pow_any_CC(T(5, None, 3), T(1, 9, 1))).asList()
    [(27, *, 3), (25, *, 3), (5, *, 3)]
    ### C(_pow_any_CC(T(None, 1, 4), T(2, 6, 2))).asList()
    [(9, *, 1)]
    ### C(_pow_any_CC(T(None, None, 11, 7), T(1, 4, 1))).asList()
    [(*, *, 1, phase=0)]
    """
    
    for k in t2:
        for t in _powConstant(t1, k):
            yield t

def _pow_CC_CO(t1, t2):
    """
    Returns an iterator over Triples representing t1 (CC) raised to the power
    t2 (CO).
    
    ### C(_pow_CC_CO(T(3, 19, 2), T(2, None, 5))).asList()
    [(9, *, 1)]
    ### C(_pow_CC_CO(T(-3, 19, 11), T(2, None, 5))).asList()
    [(*, *, 1, phase=0)]
    ### C(_pow_CC_CO(T(-5, 9, 7), T(2, None, 4))).asList()
    [(4, *, 1)]
    """
    
    if t1.start >= 0 or (t2.skip % 2 == 0 and t2.phase % 2 == 0):
        n = min(abs(t1.start), abs(t1.stop - t1.skip))
        yield T(int(math.floor(n ** t2.start)), None, 1)
    else:
        yield T(None, None, 1)

def _pow_CC_OC(t1, t2):
    """
    Returns an iterator over Triples representing t1 (CC) raised to the power
    t2 (OC).
    
    ### C(_pow_CC_OC(T(2, 10, 2), T(None, -100, 2))).asList()
    [(0, 1, 1)]
    ### C(_pow_CC_OC(T(1, 9, 2), T(None, -100, 2))).asList()
    [(0, 2, 1)]
    """
    
    t2Neg, t2Pos = t2.signedParts()
    
    if t2Neg.skip % 2 == 1 or t2Neg.phase % 2 == 0:  # has even negative powers
        for t in _powConstant_CC_neg_even(t1, -2):  # any negative even number will do
            yield t
    
    if t2Neg.skip % 2 == 1 or t2Neg.phase % 2 == 1:  # has odd negative powers
        for t in _powConstant_CC_neg_odd(t1, -1):  # any negative odd number will do
            yield t
    
    if t2Pos is not None:
        for t in _pow_any_CC(t1, t2Pos):
            yield t

def _pow_CC_OO(t1, t2):
    """
    Returns an iterator over Triples representing t1 (CC) raised to the power
    t2 (OO).
    
    ### C(_pow_CC_OO(T(1, 11, 2), T(None, None, 2, 0))).asList()
    [(0, *, 1)]
    ### C(_pow_CC_OO(T(1, 11, 2), T(None, None, 2, 1))).asList()
    [(0, *, 1)]
    ### C(_pow_CC_OO(T(-20, 0, 2), T(None, None, 2, 0))).asList()
    [(0, *, 1)]
    ### C(_pow_CC_OO(T(-20, 0, 2), T(None, None, 2, 1))).asList()
    [(*, *, 1, phase=0)]
    """
    
    if t2.phase % 2 == 0 and t2.skip % 2 == 0 or t1.start >= 0:
        yield T(0, None, 1)
    else:
        yield T(None, None, 1)

def _pow_COOCOO_COOCOO(t1, t2):
    """
    Returns an iterator over Triples representing t1 (any of the open types)
    raised to the power t2 (any of the open types).
    
    ### C(_pow_COOCOO_COOCOO(T(4, None, 5), T(3, None, 7))).asList()
    [(64, *, 1)]
    ### C(_pow_COOCOO_COOCOO(T(4, None, 5), T(-3, None, 7))).asList()
    [(0, 1, 1), (256, *, 1)]
    ### C(_pow_COOCOO_COOCOO(T(-5, None, 3), T(None, 6, 4))).asList()
    [(0, *, 1)]
    ### C(_pow_COOCOO_COOCOO(T(-5, None, 3), T(None, 7, 5))).asList()
    [(*, *, 1, phase=0)]
    ### C(_pow_COOCOO_COOCOO(T(-5, None, 3), T(None, 2, 3))).asList()
    [(-1, 2, 1)]
    """
    
    t1Neg, t1Pos = t1.signedParts()  # CO implies t1Pos guaranteed to exist
    t2Neg, t2Pos = t2.signedParts()  # OC implies t2Neg guaranteed to exist
    evenPowersOnly = t2.phase % 2 == 0 and t2.skip % 2 == 0
    
    if t1Neg is not None:
        if t2Neg is not None:
            if evenPowersOnly:
                yield T(0, (2 if -1 in t1Neg else 1), 1)
            else:
                yield T(-1, 0, 1)
        
        if t2Pos is not None:
            if evenPowersOnly:
                yield T((t1Neg.stop - t1Neg.skip) ** t2Pos.start, None, 1)
            else:
                yield T(None, None, 1)
    
    if t1Pos is not None:
        if t2Neg is not None:
            yield T(0, (2 if 1 in t1Pos else 1), 1)
        
        if t2Pos is not None:
            yield T(t1Pos.start ** t2Pos.start, None, 1)

def _powConstant(t, k):
    """
    Returns an iterator over Triples representing t raised to the specified
    constant power.
    
    If t is open-ended, a superset of the actual answer is returned.
    
    ### C(_powConstant(T(None, 14, 6), 0)).asList()
    [(1, 2, 1)]
    ### C(_powConstant(T(None, 14, 6), 1)).asList()
    [(*, 14, 6)]
    """
    
    if k == 0:
        yield T(1, 2, 1)
    
    elif k == 1:
        yield t
    
    else:
        key = (t.start is None, t.stop is None, k < 0, k % 2)
        
        for aTriple in _powConstant_dispatchTable[key](t, k):
            yield aTriple

def _powConstant_CC_pos_any(t, k):
    """
    ### C(_powConstant_CC_pos_any(T(1, 11, 2), 1)).asList()
    [(1, 11, 2)]
    ### C(_powConstant_CC_pos_any(T(1, 11, 2), 2)).asList()
    [(1, 17, 8), (25, 33, 8), (49, 57, 8), (81, 89, 8)]
    """
    
    for aTriple in utilities.tripleIteratorFromIterable(set(n ** k for n in t)):
        yield aTriple

def _powConstant_CC_neg_even(t, k):
    """
    ### C(_powConstant_CC_neg_even(T(0, 1, 1), -2)).asList()
    []
    ### C(_powConstant_CC_neg_even(T(-1, 6, 7), -2)).asList()
    [(1, 2, 1)]
    ### C(_powConstant_CC_neg_even(T(4, 6, 4), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_CC_neg_even(T(1, 11, 2), -2)).asList()
    [(0, 2, 1)]
    ### C(_powConstant_CC_neg_even(T(-20, -5, 5), -2)).asList()
    [(0, 1, 1)]
    """
    
    if len(t) == 1:
        n = t.start
        
        if abs(n) == 1:
            yield T(1, 2, 1)
        elif n:
            yield T(0, 1, 1)
        # nothing is yielded if 0 is the only member of the Triple
    
    else:
        yield T(0, (2 if 1 in t or -1 in t else 1), 1)

def _powConstant_CC_neg_odd(t, k):
    """
    ### C(_powConstant_CC_neg_odd(T(-100, -10, 5), -3)).asList()
    [(-1, 0, 1)]
    ### C(_powConstant_CC_neg_odd(T(10, 100, 5), -3)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_CC_neg_odd(T(1, 11, 2), -3)).asList()
    [(0, 2, 1)]
    ### C(_powConstant_CC_neg_odd(T(-100, 100, 1), -1)).asList()
    [(-1, 2, 1)]
    """
    
    s = set()
    
    if t.start < 0:
        s.add(-1)
    
    if 1 in t:
        s.add(1)
    
    if (t.stop - t.skip) > 1:
        s.add(0)
    
    return utilities.tripleIteratorFromIterable(s)

def _powConstant_CO_pos_even(t, k):
    """
    ### C(_powConstant_CO_pos_even(T(-100, None, 7), 2)).asList()
    [(4, *, 1)]
    ### C(_powConstant_CO_pos_even(T(0, None, 7), 2)).asList()
    [(0, *, 1)]
    ### C(_powConstant_CO_pos_even(T(100, None, 7), 2)).asList()
    [(10000, *, 1)]
    """
    
    yield T(max(t.start, _minim(t)) ** k, None, 1)

def _powConstant_CO_pos_odd(t, k):
    """
    ### C(_powConstant_CO_pos_odd(T(-10, None, 7), 3)).asList()
    [(-1000, *, 1)]
    ### C(_powConstant_CO_pos_odd(T(0, None, 7), 3)).asList()
    [(0, *, 1)]
    ### C(_powConstant_CO_pos_odd(T(10, None, 7), 3)).asList()
    [(1000, *, 1)]
    """
    
    yield T(t.start ** k, None, 1)

def _powConstant_COOCOO_neg_even(t, k):
    """
    ### C(_powConstant_COOCOO_neg_even(T(-100, None, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(0, None, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(100, None, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(1, None, 2), -2)).asList()
    [(0, 2, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, -100, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, 7, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, 100, 7), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, 3, 2), -2)).asList()
    [(0, 2, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, None, 7, 5), -2)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_COOCOO_neg_even(T(None, None, 5, 4), -2)).asList()
    [(0, 2, 1)]
    """
    
    yield T(0, (2 if 1 in t or -1 in t else 1), 1)

def _powConstant_CO_neg_odd(t, k):
    """
    ### C(_powConstant_CO_neg_odd(T(-100, None, 7), -1)).asList()
    [(-1, 1, 1)]
    ### C(_powConstant_CO_neg_odd(T(-104, None, 7), -1)).asList()
    [(-1, 2, 1)]
    ### C(_powConstant_CO_neg_odd(T(0, None, 7), -1)).asList()
    [(0, 1, 1)]
    ### C(_powConstant_CO_neg_odd(T(1, None, 7), -1)).asList()
    [(0, 2, 1)]
    """
    
    start = (-1 if t.start < 0 else 0)
    stop = (2 if 1 in t else 1)
    yield T(start, stop, 1)

def _powConstant_OC_pos_even(t, k):
    """
    ### C(_powConstant_OC_pos_even(T(None, -43, 7), 2)).asList()
    [(2500, *, 1)]
    ### C(_powConstant_OC_pos_even(T(None, 7, 7), 2)).asList()
    [(0, *, 1)]
    ### C(_powConstant_OC_pos_even(T(None, 150, 7), 2)).asList()
    [(9, *, 1)]
    """
    
    yield T(min(t.stop - t.skip, _minim(t)) ** k, None, 1)

def _powConstant_OC_pos_odd(t, k):
    """
    ### C(_powConstant_OC_pos_odd(T(None, -2, 5), 3)).asList()
    [(*, -342, 1)]
    ### C(_powConstant_OC_pos_odd(T(None, 7, 7), 3)).asList()
    [(*, 1, 1)]
    ### C(_powConstant_OC_pos_odd(T(None, 7, 5), 3)).asList()
    [(*, 9, 1)]
    """
    
    last = t.stop - t.skip
    yield T(None, (last ** k) + 1, 1)

def _powConstant_OC_neg_odd(t, k):
    """
    ### C(_powConstant_OC_neg_odd(T(None, -100, 7), -3)).asList()
    [(-1, 0, 1)]
    ### C(_powConstant_OC_neg_odd(T(None, 6, 5), -3)).asList()
    [(-1, 3, 2)]
    ### C(_powConstant_OC_neg_odd(T(None, 100, 7), -3)).asList()
    [(-1, 1, 1)]
    ### C(_powConstant_OC_neg_odd(T(None, 11, 5), -3)).asList()
    [(-1, 2, 1)]
    """
    
    s = set([-1])
    
    if (t.stop - t.skip) > 1:
        s.add(0)
    
    if 1 in t:
        s.add(1)
    
    return utilities.tripleIteratorFromIterable(s)

def _powConstant_OO_pos_even(t, k):
    """
    ### C(_powConstant_OO_pos_even(T(None, None, 8, 5), 2)).asList()
    [(9, *, 1)]
    ### C(_powConstant_OO_pos_even(T(None, None, 1, 0), 2)).asList()
    [(0, *, 1)]
    """
    
    yield T(_minim(t) ** k, None, 1)

def _powConstant_OO_pos_odd(t, k):
    """
    ### C(_powConstant_OO_pos_odd(T(None, None, 8, 5), 3)).asList()
    [(*, *, 1, phase=0)]
    ### C(_powConstant_OO_pos_odd(T(None, None, 1, 0), 3)).asList()
    [(*, *, 1, phase=0)]
    """
    
    yield T(None, None, 1, 0)

def _powConstant_OO_neg_odd(t, k):
    """
    ### C(_powConstant_OO_neg_odd(T(None, None, 8, 5), -3)).asList()
    [(-1, 1, 1)]
    ### C(_powConstant_OO_neg_odd(T(None, None, 1, 0), -3)).asList()
    [(-1, 2, 1)]
    """
    
    yield T(-1, (2 if 1 in t else 1), 1)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_powConstant_dispatchTable = {
  (False, False, False, 0): _powConstant_CC_pos_any,
  (False, False, False, 1): _powConstant_CC_pos_any,
  (False, False, True, 0): _powConstant_CC_neg_even,
  (False, False, True, 1): _powConstant_CC_neg_odd,
  (False, True, False, 0): _powConstant_CO_pos_even,
  (False, True, False, 1): _powConstant_CO_pos_odd,
  (False, True, True, 0): _powConstant_COOCOO_neg_even,
  (False, True, True, 1): _powConstant_CO_neg_odd,
  (True, False, False, 0): _powConstant_OC_pos_even,
  (True, False, False, 1): _powConstant_OC_pos_odd,
  (True, False, True, 0): _powConstant_COOCOO_neg_even,
  (True, False, True, 1): _powConstant_OC_neg_odd,
  (True, True, False, 0): _powConstant_OO_pos_even,
  (True, True, False, 1): _powConstant_OO_pos_odd,
  (True, True, True, 0): _powConstant_COOCOO_neg_even,
  (True, True, True, 1): _powConstant_OO_neg_odd}

_pow_dispatchTable = {
  ((False, False), (False, False)): _pow_any_CC,
  ((False, False), (False, True)): _pow_CC_CO,
  ((False, False), (True, False)): _pow_CC_OC,
  ((False, False), (True, True)): _pow_CC_OO,
  ((False, True), (False, False)): _pow_any_CC,
  ((False, True), (False, True)): _pow_COOCOO_COOCOO,
  ((False, True), (True, False)): _pow_COOCOO_COOCOO,
  ((False, True), (True, True)): _pow_COOCOO_COOCOO,
  ((True, False), (False, False)): _pow_any_CC,
  ((True, False), (False, True)): _pow_COOCOO_COOCOO,
  ((True, False), (True, False)): _pow_COOCOO_COOCOO,
  ((True, False), (True, True)): _pow_COOCOO_COOCOO,
  ((True, True), (False, False)): _pow_any_CC,
  ((True, True), (False, True)): _pow_COOCOO_COOCOO,
  ((True, True), (True, False)): _pow_COOCOO_COOCOO,
  ((True, True), (True, True)): _pow_COOCOO_COOCOO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def powOp(t1, t2):
    """
    Returns a list of Triples representing the t1 raised to the power of t2. No
    attempt is made to optimize the return result, since Collections should be
    used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        r = _pow_dispatchTable[(kind1, kind2)](t1, t2)
    
    except AttributeError:
        r = _powConstant(t1, t2)
    
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

