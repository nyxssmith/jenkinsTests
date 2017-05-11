#
# absOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by abs() on Triple objects.
"""

# Other imports
from fontio3.triple import triple

# -----------------------------------------------------------------------------

#
# Private functions
#

def _abs_CC(t):
    """
    Returns an iterator of the absolute value of Triple t (CC).
    
    >>> Triple = triple.Triple
    >>> list(_abs_CC(Triple(4, 104, 25)))
    [(4, 104, 25)]
    >>> list(_abs_CC(Triple(-126, 2, 16)))
    [(14, 142, 16)]
    >>> list(_abs_CC(Triple(-126, 162, 16)))
    [(14, 142, 16), (2, 162, 16)]
    >>> list(_abs_CC(Triple(-26, 26, 4)))
    [(2, 30, 4)]
    """
    
    if t.start >= 0:
        yield t
    
    else:
        Triple = triple.Triple
        tNew = Triple(t.skip - t.phase, t.skip - t.start, t.skip)
        
        if t.stop - t.skip < 0:
            yield tNew
        elif t.skip == 2 * t.phase:
            yield Triple(t.phase, max(tNew.stop, t.stop), t.skip)
        else:
            yield tNew
            yield Triple(t.phase, t.stop, t.skip)

def _abs_CO(t):
    """
    Returns an iterator of the absolute value of Triple t (CO).
    
    >>> Triple = triple.Triple
    >>> list(_abs_CO(Triple(1, None, 8)))
    [(1, *, 8)]
    >>> list(_abs_CO(Triple(-19, None, 4)))
    [(3, 23, 4), (1, *, 4)]
    >>> list(_abs_CO(Triple(-21, None, 6)))
    [(3, *, 6)]
    """
    
    if t.start >= 0:
        yield t
    
    else:
        Triple = triple.Triple
        
        if t.skip == 2 * t.phase:
            yield Triple(t.phase, None, t.skip)
        else:
            yield Triple(t.skip - t.phase, t.skip - t.start, t.skip)
            yield Triple(t.phase, t.stop, t.skip)

def _abs_OC(t):
    """
    Returns an iterator of the absolute value of Triple t (OC).
    
    >>> Triple = triple.Triple
    >>> list(_abs_OC(Triple(None, -8, 5)))
    [(13, *, 5)]
    >>> list(_abs_OC(Triple(None, 23, 8)))
    [(7, 23, 8), (1, *, 8)]
    """
    
    Triple = triple.Triple
    lastVal = t.stop - t.skip
    
    if lastVal < 0:
        yield Triple(-lastVal, None, t.skip)
    else:
        yield Triple(t.phase, t.stop, t.skip)
        yield Triple(t.skip - t.phase, None, t.skip)

def _abs_OO(t):
    """
    Returns an iterator of the absolute value of Triple t (OO).
    
    >>> Triple = triple.Triple
    >>> list(_abs_OO(Triple(None, None, 3, 0)))
    [(0, *, 3)]
    >>> list(_abs_OO(Triple(None, None, 5, 1)))
    [(1, *, 5), (4, *, 5)]
    """
    
    Triple = triple.Triple
    tNew = Triple(t.phase, None, t.skip)
    
    if t.phase == 0 or t.skip == 2 * t.phase:
        yield tNew
    else:
        yield tNew
        yield Triple(t.skip - t.phase, None, t.skip)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_abs_dispatchTable = {
  (False, False): _abs_CC,
  (False, True): _abs_CO,
  (True, False): _abs_OC,
  (True, True): _abs_OO}

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def absOp(t):
    """
    Returns an iterator of Triples representing the absolute value of the input
    Triple. No particular attempt is made to optimize the return result, since
    TripleCollections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    key = (t.start is None, t.stop is None)
    return _abs_dispatchTable[key](t)

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

