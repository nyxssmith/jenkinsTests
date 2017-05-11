#
# xorOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by xor() on Triple objects.
"""

# Other imports
from fontio3 import utilities
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

if 0:
    def __________________(): pass

def _xor_CC_CC(t1, t2):
    """
    Returns an iterator over Triples representing the result of performing a
    logical-XOR on the values in the two Triples.
    """
    
    if len(t1) > len(t2):
        t1, t2 = t2, t1
    
    for k in t1:
        for t in _xorConstant(t2, k):
            yield t

def _xorConstant(t, k):
    """
    Returns an iterator over Triples representing the result of performing an
    XOR of all the values in t with the constant k.
    """
    
    if k == 0:
        yield t
    
    elif k == -1:
        yield ~t
    
    else:
        tNeg, tPos = t.signedParts()
        
        if k > 0:
            if tNeg is not None:
                for aTriple in _xorConstant_sub(~tNeg, k):
                    yield ~aTriple
            
            if tPos is not None:
                for aTriple in _xorConstant_sub(tPos, k):
                    yield aTriple
        
        else:  # k < 0
            if tNeg is not None:
                for aTriple in _xorConstant_sub(~tNeg, ~k):
                    yield aTriple
            
            if tPos is not None:
                for aTriple in _xorConstant_sub(tPos, ~k):
                    yield ~aTriple

def _xorConstant_sub(t, k):
    """
    Subroutine to assist _xorConstant. The Triple t and the constant k must
    both be positive.
    
    ### C(_xorConstant_sub(T(4, None, 5), 6)).asList()
    [(2, *, 40), (8, *, 40), (15, *, 40), (21, *, 40), (27, *, 40), (30, *, 40), (33, *, 40), (36, *, 40)]
    ### C(_xorConstant_sub(T(4, 79, 5), 6)).asList()
    [(30, 54, 6), (55, 73, 6), (2, 14, 6), (15, 39, 6), (70, 82, 6)]
    """
    
    assert t.start >= 0 and k > 0, "_xorConstant_sub invariant failed!"
    bl = utilities.binlist(k)
    pow2 = 2 ** len(bl)
    cycle = pow2 // rational.gcf(pow2, t.skip)
    cs = cycle * t.skip
    
    if t.stop is None:
        for start in range(t.start, t.start + cs, t.skip):
            yield T(start ^ k, None, cs)
    
    else:
        tLast = t.stop - t.skip
        
        for start in range(t.start, t.start + cs, t.skip):
            xStart = start ^ k
            j = (tLast - start) // cs
            
            if j >= 0:
                xStop = xStart + (1 + j) * cs
                yield T(xStart, xStop, cs)

# -----------------------------------------------------------------------------

#
# Dispatch table
#

_xor_dispatchTable = {
  ((False, False), (False, False)): _xor_CC_CC
  }

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def xorOp(t1, t2):
    """
    Returns a list of Triples representing the values in t1 XOR'ed with the
    values in t2. No attempt is made to optimize the return result, since
    Collections should be used to do the needed optimizations.
    
    Doctests are present in the specific helper functions.
    """
    
    try:
        kind1 = (t1.start is None, t1.stop is None)
        kind2 = (t2.start is None, t2.stop is None)
        return _xor_dispatchTable[(kind1, kind2)](t1, t2)
    except AttributeError:
        return _xorConstant(t1, t2)

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

