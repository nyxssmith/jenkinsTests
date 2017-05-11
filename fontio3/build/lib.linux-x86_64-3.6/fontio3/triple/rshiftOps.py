#
# rshiftOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by rshift() on Triple objects.
"""

# Other imports
from fontio3.triple import collection, divOps, triple

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

def _rshift_CC_CC(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (CC) by the values in t2 (CC).
    
    ### C(_rshift_CC_CC(T(20, 35, 5), T(2, 100008, 2)))
    Singles: [0, 1], Ranges: [(5, 8, 1)]
    ### C(_rshift_CC_CC(T(-150, 0, 25), T(-1000, 1000, 4)))
    Ranges: [(-8, 1, 3), (-10, 2, 3), (-150, 0, 25)]
    ### C(_rshift_CC_CC(T(-290, -55, 5), T(1, None, 2)))
    Singles: [-37, -36, -34, -32, -31], Ranges: [(-29, 0, 1), (-145, -25, 5), (-143, -28, 5)]
    ### C(_rshift_CC_CC(T(1200, 2000, 25), T(-15, None, 4)))
    Singles: [0, 2, 3], Ranges: [(37, 62, 1), (600, 1000, 25), (612, 1012, 25)]
    ### C(_rshift_CC_CC(T(8, 9, 1), T(1, 3, 1)))
    Singles: [2, 4]
    """
    
    t1Neg, t1Pos = t1.signedParts()
    ignore, t2Pos = t2.signedParts()
    
    if t2Pos is not None:
        if t1Pos is not None:
            shift = t2Pos.start
            last = t1Pos.stop - t1Pos.skip
            
            while (True if t2Pos.stop is None else (shift < t2Pos.stop)):
                divisor = 2 ** shift
                
                for t in t1Pos.div(divisor):
                    yield t
                
                if last >> shift == 0:
                    break
                
                shift += t2Pos.skip
        
        if t1Neg is not None:
            shift = t2Pos.start
            first = t1Neg.start
            
            while (True if t2Pos.stop is None else (shift < t2Pos.stop)):
                divisor = 2 ** shift
                
                for t in t1Neg.div(divisor):
                    yield t
                
                if first >> shift == -1:
                    break
                
                shift += t2Pos.skip

def _rshift_CO_CC(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (CO) by the values in t2 (CC).
    
    ### C(_rshift_CO_CC(T(-25, None, 5), T(1, 7, 2)))
    Ranges: [(-10, *, 5), (-4, *, 5), (-13, *, 5), (-2, *, 5), (-1, *, 5)]
    """
    
    ignore, t2Pos = t2.signedParts()
    
    for n in t2Pos:
        divisor = 2 ** n
        
        for t in t1.div(divisor):
            yield t

def _rshift_CO_CO(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (CO) by the values in t2 (CO).
    
    This method returns a superset of the actual answer; perhaps with the
    advent of meta-Triples we could actually express the result exactly.
    
    ### C(_rshift_CO_CO(T(-13, None, 5), T(-7, None, 9)))
    Ranges: [(-4, *, 1)]
    """
    
    ignore, t2Pos = t2.signedParts()
    yield T(t1.start >> t2Pos.start, None, 1)

def _rshift_CO_OC(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (CO) by the values in t2 (CC).
    
    ### C(_rshift_CO_OC(T(-25, None, 5), T(None, 7, 2)))
    Ranges: [(-10, *, 5), (-4, *, 5), (-13, *, 5), (-2, *, 5), (-1, *, 5)]
    ### C(_rshift_CO_OC(T(-25, None, 5), T(None, 0, 3)))
    Empty Collection
    """
    
    ignore, t2Pos = t2.signedParts()
    
    if t2Pos is not None:
        return _rshift_CO_CC(t1, t2Pos)
    
    return iter([])

def _rshift_CO_OO(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (CO) by the values in t2 (OO).
    
    This method returns a superset of the actual answer; perhaps with the
    advent of meta-Triples we could actually express the result exactly.
    
    ### C(_rshift_CO_OO(T(3, None, 5), T(None, None, 3, 1)))
    Ranges: [(0, *, 1)]
    ### C(_rshift_CO_OO(T(-3, None, 5), T(None, None, 3, 1)))
    Ranges: [(-1, *, 1)]
    """
    
    yield T((-1 if t1.start < 0 else 0), None, 1)

def _rshift_OC_CO(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (OC) by the values in t2 (CO).
    
    This method returns a superset of the actual answer; perhaps with the
    advent of meta-Triples we could actually express the result exactly.
    
    ### C(_rshift_OC_CO(T(None, -2, 9), T(-5, None, 2)))
    Ranges: [(*, 0, 1)]
    ### C(_rshift_OC_CO(T(None, 80, 9), T(-5, None, 2)))
    Ranges: [(*, 36, 1)]
    """
    
    last = t1.stop - t1.skip
    yield T(None, (0 if last < 0 else 1 + (last >> t2.phase)), 1)

def _rshift_OC_OO(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (OC) by the values in t2 (CO).
    
    This method returns a superset of the actual answer; perhaps with the
    advent of meta-Triples we could actually express the result exactly.
    
    ### C(_rshift_OC_OO(T(None, 80, 9), T(None, None, 2, 1)))
    Ranges: [(*, 36, 1)]
    """
    
    ignore, t2Pos = t2.signedParts()
    return _rshift_OC_CO(t1, t2Pos)

def _rshift_OO_CC(t1, t2):
    """
    Returns an iterator over Triples representing the logical right-shift of t1
    (OO) by the values in t2 (OO).
    
    This method returns a superset of the actual answer; perhaps with the
    advent of meta-Triples we could actually express the result exactly.
    
    ### C(_rshift_OO_CC(T(None, None, 3, 2), T(1, 11, 2)))
    Ranges: [(*, *, 1, phase=0)]
    """
    
    yield T(None, None, 1, 0)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_rshift_dispatchTable = {
  ((False, False), (False, False)): _rshift_CC_CC,
  ((False, False), (False, True)): _rshift_CC_CC,     # CC_CO handled by CC_CC
  ((False, False), (True, False)): _rshift_CC_CC,     # CC_OC handled by CC_CC
  ((False, False), (True, True)): _rshift_CC_CC,      # CC_OO handled by CC_CC
  ((False, True), (False, False)): _rshift_CO_CC,
  ((False, True), (False, True)): _rshift_CO_CO,
  ((False, True), (True, False)): _rshift_CO_OC,
  ((False, True), (True, True)): _rshift_CO_OO,
  ((True, False), (False, False)): _rshift_CO_CC,     # OC_CC handled by CO_CC
  ((True, False), (False, True)): _rshift_OC_CO,
  ((True, False), (True, False)): _rshift_CO_OC,      # OC_OC handled by CO_OC
  ((True, False), (True, True)): _rshift_OC_OO,
  ((True, True), (False, False)): _rshift_OO_CC,
  ((True, True), (False, True)): _rshift_OO_CC,       # OO_CO handled by OO_CC
  ((True, True), (True, False)): _rshift_OO_CC,       # OO_OC handled by OO_CC
  ((True, True), (True, True)): _rshift_OO_CC}        # OO_OO handled by OO_CC

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def rshiftOp(t1, t2):
    """
    Returns an iterator of Triples representing t1 right-shifted by t2 bits. No
    particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Note that in some cases the Triples returned by the iterator will actually
    be a superset of the "correct" set of answers. This is due to the absence
    of meta-Triples, which may be added at some point in the future.
    
    ### C(rshiftOp(T(20, 200, 5), 3))
    Ranges: [(2, 25, 1)]
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        return _rshift_dispatchTable[(kind1, kind2)](t1, t2)
    except AttributeError:
        return divOps.divOp(t1, 2 ** t2)

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

