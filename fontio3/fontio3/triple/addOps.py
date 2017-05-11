#
# addOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by add() on Triple objects.
"""

# Other imports
from fontio3.triple import collection, triple
from fontio3.fontmath import rational

# -----------------------------------------------------------------------------

#
# Private functions
#

def _add_CC_CC(t1, t2):
    """
    Returns an iterator of the sum of Triples t1 (CC) and t2 (CC).
    
    >>> T = triple.Triple
    >>> C = collection.Collection
    >>> C(_add_CC_CC(T(1, 11, 2), T(1, 1, 1))).asList()
    [(1, 11, 2)]
    >>> C(_add_CC_CC(T(1, 11, 2), T(1, 2, 1))).asList()
    [(2, 12, 2)]
    >>> C(_add_CC_CC(T(1, 1, 1), T(1, 11, 2))).asList()
    [(1, 11, 2)]
    >>> C(_add_CC_CC(T(1, 2, 1), T(1, 11, 2))).asList()
    [(2, 12, 2)]
    >>> C(_add_CC_CC(T(1, 11, 2), T(100, 150, 1))).asList()
    [(101, 159, 1)]
    >>> C(_add_CC_CC(T(5, 32, 3), T(-45, 0, 3))).asList()
    [(-40, 29, 3)]
    >>> C(_add_CC_CC(T(1, 56, 5), T(702, 772, 7))).asList()
    [(710, 800, 5), (731, 821, 5), (717, 807, 5), (703, 793, 5), (724, 814, 5)]
    >>> C(_add_CC_CC(T(1, 10, 3), T(100, 1070, 97))).asList()
    [(101, 1071, 97), (104, 1074, 97), (107, 1077, 97)]
    >>> C(_add_CC_CC(T(1, 17, 4), T(300, 640, 34))).asList()
    [(309, 649, 34), (313, 653, 34), (301, 641, 34), (305, 645, 34)]
    """
    
    Triple = triple.Triple
    selfLen = len(t1)
    otherLen = len(t2)
    
    if selfLen == 0:
        yield t2
    
    elif otherLen == 0:
        yield t1
    
    elif selfLen <= otherLen:
        for n in t1:
            yield Triple(t2.start + n, t2.stop + n, t2.skip)
    
    else:
        for n in t2:
            yield Triple(t1.start + n, t1.stop + n, t1.skip)
    
#     elif selfLen == 1:
#         yield Triple(t2.start + t1.start, t2.stop + t1.start, t2.skip)
#     
#     elif otherLen == 1:
#         yield Triple(t1.start + t2.start, t1.stop + t2.start, t1.skip)
#     
#     else:
#         if t1.skip > t2.skip:
#             t1, t2 = t2, t1
#         
#         if t1.skip == 1:
#             yield Triple(t1.start + t2.start, t1.stop + t2.stop - t2.skip, 1)
#         
#         elif t1.skip == t2.skip:
#             yield Triple(t1.start + t2.start, t1.stop + t2.stop - t1.skip, t1.skip)
#         
#         else:
#             if (t1.start + (t1.skip * t2.skip) // gcfSkip) <= t1.stop:
#                 d = {}
#                 base = t1.start + t2.start
#                 count = saveCount = min(otherLen, t1.skip // gcfSkip)
#                 
#                 while count:
#                     count -= 1
#                     d[base % t1.skip] = [base]
#                     base += t2.skip
#                 
#                 base = (t1.stop - t1.skip) + (t2.stop - t2.skip)
#                 count = saveCount
#                 
#                 while count:
#                     count -= 1
#                     d[base % t1.skip].append(base + t1.skip)
#                     base -= t2.skip
#                 
#                 for vSub in d.itervalues():
#                     if len(vSub) == 2:
#                         yield Triple(vSub[0], vSub[1], t1.skip)
#                     else:
#                         yield Triple(vSub[0], vSub[0] + t1.skip, t1.skip)
#             
#             elif selfLen < otherLen:
#                 for n in xrange(t1.start, t1.stop, t1.skip):
#                     yield Triple(t2.start + n, t2.stop + n, t2.skip)
#             
#             else:
#                 for n in xrange(t2.start, t2.stop, t2.skip):
#                     yield Triple(t1.start + n, t1.stop + n, t1.skip)

def _add_CC_CO(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (CC) and t2 (CO).
    
    >>> T = triple.Triple
    >>> list(_add_CC_CO(T(1, 1, 1), T(6, None, 4), 1))
    [(6, *, 4)]
    >>> list(_add_CC_CO(T(1, 2, 2), T(6, None, 4), 1))
    [(7, *, 4)]
    >>> list(_add_CC_CO(T(2, 18, 4), T(10, None, 3), 1))
    [(20, *, 1), (16, 22, 3), (12, 21, 3)]
    >>> list(_add_CC_CO(T(2, 10, 4), T(10, None, 3), 1))
    [(12, *, 3), (16, *, 3)]
    """
    
    Triple = triple.Triple
    
    if t1._cachedLen < 2:
        yield (_addConstant(t2, t1.start) if t1._cachedLen else t2)
    
    else:
        lowFull = min(t1.skip, t2.skip)
        low = lowFull // gcfSkip
        
        if t1._cachedLen >= low:
            for obj in _add_CO_CO(t2, Triple(t1.start, None, t1.skip), gcfSkip):
                yield obj
        else:
            for n in t1:
                yield _addConstant(t2, n)

def _add_CC_OC(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (CC) and t2 (OC).
    
    >>> T = triple.Triple
    >>> list(_add_CC_OC(T(1, 1, 1), T(None, 13, 3), 1))
    [(*, 13, 3)]
    >>> list(_add_CC_OC(T(4, 5, 1), T(None, 13, 3), 1))
    [(*, 17, 3)]
    >>> list(_add_CC_OC(T(2, 18, 4), T(None, 10, 3), 1))
    [(*, 14, 1), (14, 20, 3), (15, 24, 3)]
    """
    
    Triple = triple.Triple
    
    if t1._cachedLen < 2:
        yield (_addConstant(t2, t1.start) if t1._cachedLen else t2)
    
    else:
        lowFull = min(t1.skip, t2.skip)
        low = lowFull // gcfSkip
        
        if t1._cachedLen >= low:
            for obj in _add_OC_OC(t2, Triple(None, t1.stop, t1.skip), gcfSkip):
                yield obj
        else:
            for n in t1:
                yield _addConstant(t2, n)

def _add_CO_CO(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (CO) and t2 (CO).
    
    >>> T = triple.Triple
    >>> list(_add_CO_CO(T(2, None, 1), T(2, None, 3), 1))
    [(4, *, 1)]
    >>> list(_add_CO_CO(T(3, None, 10), T(-8, None, 14), 2))
    [(51, *, 2), (37, 57, 10), (23, 53, 10), (9, 59, 10), (-5, 55, 10)]
    >>> list(_add_CO_CO(T(6, None, 12), T(2, None, 20), 4))
    [(48, *, 4), (28, 52, 12), (8, 56, 12)]
    >>> list(_add_CO_CO(T(-10, None, 3), T(-50, None, 5), 1))
    [(-50, *, 1), (-55, -49, 3), (-60, -48, 3)]
    """
    
    Triple = triple.Triple
    highFull, lowFull = max(t1.skip, t2.skip), min(t1.skip, t2.skip)
    low = lowFull // gcfSkip
    fullStart = t1.start + t2.start + (highFull * (low - 1))
    yield Triple(fullStart, None, gcfSkip)
    
    for i in range(1, low):
        newStart = fullStart - i * highFull
        q, r = divmod(fullStart - newStart, lowFull)
        newStop = newStart + (1 + q - (not r)) * lowFull
        yield Triple(newStart, newStop, lowFull)

def _add_CO_OC(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (CO) and t2 (OC).
    
    >>> T = triple.Triple
    >>> list(_add_CO_OC(T(11, None, 6, 5), T(None, 917, 9), 3))
    [(*, *, 3, phase=1)]
    >>> list(_add_CO_OC(T(13, None, 5, 4), T(None, 14, 3), 1))
    [(*, *, 1, phase=0)]
    >>> list(_add_CO_OC(T(44, None, 9, 5), T(None, 3, 12), 3))
    [(*, *, 3, phase=2)]
    """
    
    Triple = triple.Triple
    newSelf = Triple(None, t1.stop, t1.skip, t1.phase)
    return _add_OO_COOCOO(newSelf, t2, gcfSkip)

def _add_OC_OC(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (OC) and t2 (OC).
    
    >>> T = triple.Triple
    >>> list(_add_OC_OC(T(None, 2, 1), T(None, 15, 3), 1))
    [(*, 14, 1)]
    >>> list(_add_OC_OC(T(None, 16, 12), T(None, 31, 20), 4))
    [(*, -21, 4), (-17, 7, 12), (-21, 27, 12)]
    >>> list(_add_OC_OC(T(None, 3, 8), T(None, 4, 8), 8))
    [(*, -1, 8)]
    """
    
    Triple = triple.Triple
    highFull, lowFull = max(t1.skip, t2.skip), min(t1.skip, t2.skip)
    low = lowFull // gcfSkip
    fullLast = (t1.stop - t1.skip) + (t2.stop - t2.skip) + (highFull * (1 - low))
    yield Triple(None, fullLast + gcfSkip, gcfSkip)
    
    for i in range(1, low):
        thisLast = fullLast + i * highFull
        q, r = divmod(thisLast - fullLast, lowFull)
        thisFirst = thisLast - lowFull * (q - (not r))
        yield Triple(thisFirst, thisLast + lowFull, lowFull)

def _add_OO_CC(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (OO) and t2 (CC).
    
    >>> T = triple.Triple
    >>> list(_add_OO_CC(T(None, None, 9, 5), T(3, 15, 12), 3))
    [(*, *, 9, phase=8)]
    >>> list(_add_OO_CC(T(None, None, 9, 5), T(3, 27, 12), 3))
    [(*, *, 9, phase=8), (*, *, 9, phase=2)]
    >>> list(_add_OO_CC(T(None, None, 9, 5), T(3, 39, 12), 3))
    [(*, *, 3, phase=2)]
    >>> list(_add_OO_CC(T(None, None, 19, phase=16), T(1, 9, 2), 1))
    [(*, *, 19, phase=17), (*, *, 19, phase=0), (*, *, 19, phase=2), (*, *, 19, phase=4)]
    """
    
    Triple = triple.Triple
    
    if len(t2) >= (t1.skip // gcfSkip):
        yield Triple(None, None, gcfSkip, (t1.phase + t2.phase) % gcfSkip)
    else:
        for n in range(t2.start, t2.stop, t2.skip):
            yield Triple(None, None, t1.skip, (t1.phase + n) % t1.skip)

def _add_OO_COOCOO(t1, t2, gcfSkip):
    """
    Returns an iterator of the sum of t1 (OO) and t2 (one of CO, OC, or OO).
    
    >>> T = triple.Triple
    >>> list(_add_OO_COOCOO(T(None, None, 6, 5), T(None, None, 9, 8), 3))
    [(*, *, 3, phase=1)]
    >>> list(_add_OO_COOCOO(T(None, None, 5, 4), T(None, 14, 3), 1))
    [(*, *, 1, phase=0)]
    >>> list(_add_OO_COOCOO(T(None, None, 9, 5), T(3, None, 12), 3))
    [(*, *, 3, phase=2)]
    """
    
    yield triple.Triple(None, None, gcfSkip, (t1.phase + t2.phase) % gcfSkip)

def _addConstant(t1, k):
    """
    Returns a new Triple with the results of a constant addition of k to t1.
    
    >>> T = triple.Triple
    >>> _addConstant(T(None, None, 5, 2), 8)
    (*, *, 5, phase=0)
    >>> _addConstant(T(None, 13, 5), 6)
    (*, 19, 5)
    >>> _addConstant(T(-12, None, 7), 100)
    (88, *, 7)
    >>> _addConstant(T(1, 11, 2), 5)
    (6, 16, 2)
    """
    
    Triple = triple.Triple
    
    if t1.start is None:
        if t1.stop is None:
            return Triple(None, None, t1.skip, (t1.phase + k) % t1.skip)
        
        return Triple(None, t1.stop + k, t1.skip)
    
    if t1.stop is None:
        return Triple(t1.start + k, None, t1.skip)
    
    return Triple(t1.start + k, t1.stop + k, t1.skip)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_add_dispatchTable = {
  ((False, False), (False, True)): _add_CC_CO,
  ((False, False), (True, False)): _add_CC_OC,
  ((False, True), (False, True)): _add_CO_CO,
  ((False, True), (True, False)): _add_CO_OC,
  ((True, False), (True, False)): _add_OC_OC,
  ((True, True), (False, False)): _add_OO_CC,
  ((True, True), (False, True)): _add_OO_COOCOO,
  ((True, True), (True, False)): _add_OO_COOCOO,
  ((True, True), (True, True)): _add_OO_COOCOO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def addOp(t1, t2):
    """
    Returns an iterator of Triples representing the sum of the input Triples.
    No particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        gcf = rational.gcf(t1.skip, t2.skip)
        t = (kind1, kind2)
        
        if t == ((False, False), (False, False)):
            r = _add_CC_CC(t1, t2)
        elif t in _add_dispatchTable:
            r = _add_dispatchTable[t](t1, t2, gcf)
        else:
            r = _add_dispatchTable[(kind2, kind1)](t2, t1, gcf)
    
    except AttributeError:
        r = iter([_addConstant(t1, t2)])
    
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

