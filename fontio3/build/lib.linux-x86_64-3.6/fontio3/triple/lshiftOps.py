#
# lshiftOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by lshift() on Triple objects.
"""

# Other imports
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

if 0:
    def __________________(): pass

def _lshift_CC_CC(t1, t2):
    """
    Returns an iterator over Triples representing the logical left-shift of t1
    (CC) by the values in t2 (CC).
    
    >>> C(_lshift_CC_CC(T(1, 11, 2), T(3, 6, 1))).asList()
    [(8, 88, 16), (16, 176, 32), (32, 352, 64)]
    """
    
    for n in t2:
        for t in t1.mul(2 ** n):
            yield t

def _lshift_CC_CO(t1, t2):
    """
    Returns an iterator over Triples representing the logical left-shift of t1
    (CC) by the values in t2 (CO). Only the non-negative values in t2 are used.
    
    Without meta-Triples (see the docstring for mulOps._mul_OO_OO), there can
    be no finite representation of the output of this method. So for the time
    being, an open-ended Triple of the appropriate sign, skip and phase is
    used.
    
    >>> C(_lshift_CC_CO(T(-3, 11, 7), T(-19, None, 1))).asList()
    [(*, *, 1, phase=0)]
    >>> C(_lshift_CC_CO(T(3, 11, 2), T(3, None, 3))).asList()
    [(24, *, 8)]
    """
    
    ignore, t2Pos = t2.signedParts()
    
    if t2Pos is not None:
        newSkip = 2 ** t2Pos.start
        newStart = (None if t1.start < 0 else t1.start * newSkip)
        yield T(newStart, None, newSkip)

def _lshift_CC_OC(t1, t2):
    """
    Returns an iterator over Triples representing the logical left-shift of t1
    (CC) by the values in t2 (OC). Only the non-negative values in t2 are used,
    and since it is open on the right, it's possible no values at all will be
    generated.
    
    >>> C(_lshift_CC_OC(T(1, 11, 2), T(None, 5, 2))).asList()
    [(2, 22, 4), (8, 88, 16)]
    >>> C(_lshift_CC_OC(T(1, 11, 2), T(None, -10, 4))).asList()
    []
    """
    
    ignore, t2Pos = t2.signedParts()
    
    if t2Pos is not None:
        return _lshift_CC_CC(t1, t2Pos)
    
    return iter([])  # is there a better way of representing an empty iterator?

def _lshift_OC_CO(t1, t2):
    """
    Returns an iterator over Triples representing the logical left-shift of t1
    (OC) by the values in t2 (CO). Only the non-negative values in t2 are used.
    
    Without meta-Triples (see the docstring for mulOps._mul_OO_OO), there can
    be no finite representation of the output of this method. So for the time
    being, an open-ended Triple of the appropriate sign, skip and phase is
    used.
    
    >>> C(_lshift_OC_CO(T(None, 12, 5), T(-17, None, 9))).asList()
    [(*, *, 2, phase=0)]
    """
    
    ignore, t2Pos = t2.signedParts()
    newSkip = 2 ** t2Pos.start
    yield T(None, None, newSkip)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_lshift_dispatchTable = {
  ((False, False), (False, False)): _lshift_CC_CC,
  ((False, False), (False, True)): _lshift_CC_CO,
  ((False, False), (True, False)): _lshift_CC_OC,
  ((False, False), (True, True)): _lshift_CC_CO,
  ((False, True), (False, False)): _lshift_CC_CC,
  ((False, True), (False, True)): _lshift_CC_CO,
  ((False, True), (True, False)): _lshift_CC_OC,
  ((False, True), (True, True)): _lshift_CC_CO,
  ((True, False), (False, False)): _lshift_CC_CC,
  ((True, False), (False, True)): _lshift_OC_CO,
  ((True, False), (True, False)): _lshift_CC_OC,
  ((True, False), (True, True)): _lshift_OC_CO,
  ((True, True), (False, False)): _lshift_CC_CC,
  ((True, True), (False, True)): _lshift_OC_CO,
  ((True, True), (True, False)): _lshift_CC_OC,
  ((True, True), (True, True)): _lshift_OC_CO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def lshiftOp(t1, t2):
    """
    Returns an iterator of Triples representing t1 left-shifted by t2 bits. No
    particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Note that in some cases the Triples returned by the iterator will actually
    be a superset of the "correct" set of answers. This is due to the absence
    of meta-Triples, which may be added at some point in the future.
    
    >>> C(lshiftOp(T(5, 17, 4), 2)).asList()
    [(20, 68, 16)]
    >>> C(lshiftOp(T(1, 11, 2), T(3, 6, 1))).asList()
    [(8, 88, 16), (16, 176, 32), (32, 352, 64)]
    >>> C(lshiftOp(T(3, 11, 2), T(3, None, 3))).asList()
    [(24, *, 8)]
    >>> C(lshiftOp(T(1, 11, 2), T(None, 5, 2))).asList()
    [(2, 22, 4), (8, 88, 16)]
    >>> C(lshiftOp(T(3, 11, 2), T(None, None, 3, 1))).asList()
    [(6, *, 2)]
    >>> C(lshiftOp(T(-5, None, 2), T(3, 6, 1))).asList()
    [(-40, *, 16), (-80, *, 32), (-160, *, 64)]
    >>> C(lshiftOp(T(-5, None, 2), T(-6, None, 4))).asList()
    [(*, *, 4, phase=0)]
    >>> C(lshiftOp(T(-5, None, 2), T(None, 10, 4))).asList()
    [(-20, *, 8), (-320, *, 128)]
    >>> C(lshiftOp(T(-5, None, 2), T(None, None, 4))).asList()
    [(*, *, 1, phase=0)]
    >>> C(lshiftOp(T(None, 4, 5), T(1, 9, 2))).asList()
    [(*, 8, 10), (*, 32, 40)]
    >>> C(lshiftOp(T(None, 12, 5), T(-17, None, 9))).asList()
    [(*, *, 2, phase=0)]
    >>> C(lshiftOp(T(None, 12, 5), T(None, 5, 2))).asList()
    [(*, 24, 10), (*, 96, 40)]
    >>> C(lshiftOp(T(None, 12, 5), T(None, None, 9, 3))).asList()
    [(*, *, 8, phase=0)]
    >>> C(lshiftOp(T(None, None, 4, 3), T(1, 7, 2))).asList()
    [(*, *, 8, phase=6), (*, *, 32, phase=24), (*, *, 128, phase=96)]
    >>> C(lshiftOp(T(None, None, 4, 3), T(-3, None, 2))).asList()
    [(*, *, 2, phase=0)]
    >>> C(lshiftOp(T(None, None, 4, 3), T(None, -3, 2))).asList()
    []
    >>> C(lshiftOp(T(None, None, 4, 3), T(None, None, 2, 1))).asList()
    [(*, *, 2, phase=0)]
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        return _lshift_dispatchTable[(kind1, kind2)](t1, t2)
    except AttributeError:
        return t1.mul(2 ** t2)

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

