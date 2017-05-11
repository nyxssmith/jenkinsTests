#
# modOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by mod() on Triple objects.
"""

# Other imports
from fontio3.fontmath import rational
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

def _mod_CC_CC(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (CC) modulus
    all values in t2 (CC).
    
    ### list(_mod_CC_CC(T(1, 11, 2), T(4, 16, 3)))
    [(0, 4, 2), (1, 11, 2)]
    """
    
    return utilities.tripleIteratorFromIterable(_mod_CC_CC_gen(t1, t2))

def _mod_CC_CC_gen(t1, t2):
    t2Neg, t2Pos = t2.signedParts()
    
    for n1 in t1:
        if t2Pos:
            for n2 in t2Pos:
                yield n1 % n2
        if t2Neg:
            for n2 in t2Neg:
                yield (n1 % n2) % -n2

def _mod_CC_CO(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (CC) modulus
    all values in t2 (CO).
    
    ### list(_mod_CC_CO(T(202, 230, 4), T(196, None, 14)))
    [(0, 20, 4), (2, 34, 4), (202, 230, 4)]
    ### list(_mod_CC_CO(T(202, 230, 4), T(14196, None, 14)))
    [(202, 230, 4)]
    """
    
    absLarge = max(abs(t1.start), abs(t1.stop - t1.skip))
    newLast = t2.findMember(False, False, absLarge)
    newStart = t2.findMember(True, False, -absLarge)
    
    if newStart is None:
        newStart = t2.start
        assert newStart <= newLast, "internal error"
    
    tNew = T(newStart, newLast + t2.skip, t2.skip)
    
    if 0 in tNew:
        tNeg, tPos = tNew.signedParts()
        
        if tNeg is not None:
            for t in _mod_CC_CC(t1, tNeg):
                yield t
        
        for t in _mod_CC_CC(t1, T(tPos.start + tPos.skip, tPos.stop, tPos.skip)):
            yield t
    
    else:
        for t in _mod_CC_CC(t1, tNew):
            yield t

def _mod_CC_OC(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (CC) modulus
    all values in t2 (OC).
    
    ### list(_mod_CC_OC(T(7, 35, 2), T(None, -115, 4)))
    [(7, 35, 2)]
    ### list(_mod_CC_OC(T(7, 35, 2), T(None, 11, 4)))
    [(0, 18, 2), (1, 35, 2)]
    """
    
    absLarge = max(abs(t1.start), abs(t1.stop - t1.skip))
    newStart = t2.findMember(True, False, -absLarge)
    newLast = t2.findMember(False, False, absLarge)
    
    if newLast is None:
        newLast = t2.stop - t2.skip
        assert newStart <= newLast, "internal error"
    
    tNew = T(newStart, newLast + t2.skip, t2.skip)
    
    if 0 in tNew:
        tNeg, tPos = tNew.signedParts()
        
        if tNeg is not None:
            for t in _mod_CC_CC(t1, tNeg):
                yield t
        
        for t in _mod_CC_CC(t1, T(tPos.start + tPos.skip, tPos.stop, tPos.skip)):
            yield t
    
    else:
        for t in _mod_CC_CC(t1, tNew):
            yield t

def _mod_CC_OO(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (CC) modulus
    all values in t2 (OO).
    
    ### C(_mod_CC_OO(T(202, 230, 4), T(None, None, 14, 0))).asList()
    [(0, 104, 4), (2, 114, 4), (202, 230, 4)]
    """
    
    absLarge = max(abs(t1.start), abs(t1.stop - t1.skip))
    newStart = t2.findMember(True, False, -absLarge)
    newLast = t2.findMember(False, False, absLarge)
    tNew = T(newStart, newLast + t2.skip, t2.skip)
    
    if 0 in tNew:
        tNeg, tPos = tNew.signedParts()
        
        if tNeg is not None:
            for t in _mod_CC_CC(t1, tNeg):
                yield t
        
        for t in _mod_CC_CC(t1, T(tPos.start + tPos.skip, tPos.stop, tPos.skip)):
            yield t
    
    else:
        for t in _mod_CC_CC(t1, tNew):
            yield t

def _mod_CO_CC(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (CO) modulus
    all values in t2 (CC).
    
    ### list(_mod_CO_CC(T(12, None, 6), T(4, 46, 21)))
    [(0, 4, 2), (0, 25, 1)]
    """
    
    if 0 in t2:
        tNeg, tPos = t2.signedParts()
        
        if tNeg is not None:
            for n in tNeg:
                for t in _modConstant(t1, n):
                    yield t
        
        for n in T(tPos.start + tPos.skip, tPos.stop, tPos.skip):
            for t in _modConstant(t1, n):
                yield t
    
    else:
        for n in t2:
            for t in _modConstant(t1, n):
                yield t

def _mod_OC_CC(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (OC) modulus
    all values in t2 (CC).
    
    ### list(_mod_OC_CC(T(None, 35, 6), T(8, 35, 9)))
    [(1, 9, 2), (0, 17, 1), (1, 27, 2)]
    """
    
    if 0 in t2:
        tNeg, tPos = t2.signedParts()
        
        if tPos is not None:
            for n in tPos:
                for t in _modConstant(t1, n):
                    yield t
        
        for n in T(tNeg.start + tNeg.skip, tNeg.stop, tNeg.skip):
            for t in _modConstant(t1, n):
                yield t
    
    else:
        for n in t2:
            for t in _modConstant(t1, n):
                yield t

def _mod_OO_CC(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (OO) modulus
    all values in t2 (CC).
    
    ### list(_mod_OO_CC(T(None, None, 5, 0), T(35, 105, 7)))
    [(0, 98, 1)]
    ### list(_mod_OO_CC(T(None, None, 5, 0), T(35, 42, 7)))
    [(0, 35, 5)]
    ### list(_mod_OO_CC(T(None, None, 5, 3), T(35, 56, 7)))
    [(0, 49, 1)]
    """
    
    gcf = rational.gcf(t1.skip, t2.skip)
    
    if (t2.stop - t2.start) < (t1.skip * t2.skip // gcf):
        # not enough for a full cycle, so do indiv values
        s = set()
        
        for n in t2:
            s.update(_modConstant_set(t1, n))
        
        for obj in utilities.tripleIteratorFromIterable(s):
            yield obj
    
    else:
        # enough for a full cycle
        tTemp = next(_mod_OO_OO(t1, T(None, None, t2.skip, t2.phase)))
        newStop = (t2.stop - t2.skip - 1) + tTemp.skip
        yield T(tTemp.start, newStop, tTemp.skip)

def _mod_OO_OO(t1, t2):
    """
    Returns an iterator over Triples representing all values in t1 (OO) modulus
    all values in t2 (OO).
    
    ### list(_mod_OO_OO(T(None, None, 5, 0), T(None, None, 7, 0)))
    [(0, *, 1)]
    ### list(_mod_OO_OO(T(None, None, 6, 2), T(None, None, 4, 0)))
    [(0, *, 2)]
    ### list(_mod_OO_OO(T(None, None, 24, 11), T(None, None, 9, 6)))
    [(2, *, 3)]
    """
    
    gcf = rational.gcf(t1.skip, t2.skip)
    
    if gcf == 1:
        yield T(0, None, 1)
    elif t2.phase == 0:
        yield T(t1.phase % gcf, None, gcf)
    else:
        newSkip = rational.gcf(gcf, t2.phase)
        yield T(t1.phase % newSkip, None, newSkip)

def _modConstant(t, k):
    """
    Returns an iterator over Triples representing the modulus of the specified
    Triple t by the specified constant k.
    
    ### list(_modConstant(T(None, None, 6, 5), 4))
    [(1, 5, 2)]
    ### list(_modConstant(T(14, 29, 5), 7))
    [(0, 2, 2), (3, 7, 2)]
    """
    
    return utilities.tripleIteratorFromIterable(_modConstant_set(t, k))

def _modConstant_set(t, k):
    """
    Returns an iterator over Triples representing the modulus of the specified
    Triple t by the specified constant k.
    
    ### sorted(_modConstant_set(T(None, None, 6, 5), 4))
    [1, 3]
    ### sorted(_modConstant_set(T(14, 29, 5), 7))
    [0, 3, 5]
    """
    
    s = set()
    lcm = rational.lcm(t.skip, k)
    
    if t.start is None or t.stop is None:
        for n in range(t.phase, t.phase + lcm, t.skip):
            s.add(n % k)
    else:
        for n in range(t.start, min(t.start + lcm, t.stop), t.skip):
            s.add(n % k)
    
    return s

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_mod_dispatchTable = {
  ((False, False), (False, False)): _mod_CC_CC,
  ((False, False), (False, True)): _mod_CC_CO,
  ((False, False), (True, False)): _mod_CC_OC,
  ((False, False), (True, True)): _mod_CC_OO,
  ((False, True), (False, False)): _mod_CO_CC,
  ((False, True), (False, True)): _mod_OO_OO,
  ((False, True), (True, False)): _mod_OO_OO,
  ((False, True), (True, True)): _mod_OO_OO,
  ((True, False), (False, False)): _mod_OC_CC,
  ((True, False), (False, True)): _mod_OO_OO,
  ((True, False), (True, False)): _mod_OO_OO,
  ((True, False), (True, True)): _mod_OO_OO,
  ((True, True), (False, False)): _mod_OO_CC,
  ((True, True), (False, True)): _mod_OO_OO,
  ((True, True), (True, False)): _mod_OO_OO,
  ((True, True), (True, True)): _mod_OO_OO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def modOp(t1, t2):
    """
    Returns an iterator of Triples representing the modulus of t1 by t2. No
    particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        if 0 in t2:
            raise ZeroDivisionError("Cannot take modulus with zero!")
        
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        return _mod_dispatchTable[(kind1, kind2)](t1, t2)
    
    except TypeError:
        if t2 == 0:
            raise ZeroDivisionError("Cannot take modulus with zero!")
        
        return _modConstant(t1, t2)

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

