#
# basisOps.py
#
# Copyright © 2008, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used to manipulate Triple objects as if they had basis values.
"""

# Other imports
from fontio3.triple import collection, triple
from fontio3.fontmath import rational

# -----------------------------------------------------------------------------

#
# Public functions
#

def convert(t, oldBasis, newBasis, round=True):
    """
    Returns an iterator of Triples representing t converted from oldBasis to
    newBasis. No particular attempt is made to optimize the return result,
    since TripleCollections should be used to do the needed optimizations.

    If round is True values will be rounded (0.5 rounds up). If round is False
    values will be integer-division truncated.
    
    >>> T, C = (triple.Triple, collection.Collection)
    >>> C(convert(T(1, 11, 2), 4, 4, True)).asList()
    [(1, 11, 2)]
    >>> C(convert(T(1, 11, 2), 4, 4, False)).asList()
    [(1, 11, 2)]
    >>> C(convert(T(1, 11, 2), 4, 16, True)).asList()
    [(4, 44, 8)]
    >>> C(convert(T(1, 11, 2), 4, 16, False)).asList()
    [(4, 44, 8)]
    >>> C(convert(T(1, 17, 2), 16, 4, True)).asList()
    [(0, 5, 1)]
    >>> C(convert(T(1, 17, 2), 16, 4, False)).asList()
    [(0, 4, 1)]
    >>> C(convert(T(2, 29, 3), 9, 12, True)).asList()
    [(3, 39, 4)]
    >>> C(convert(T(2, 29, 3), 9, 12, False)).asList()
    [(2, 38, 4)]
    """
    
    if oldBasis == newBasis:
        yield t
    
    else:
        gcf = rational.gcf(oldBasis, newBasis)
        lcm = (oldBasis * newBasis) // gcf
        
        if gcf == oldBasis:
            for tProduct in t.mul(newBasis // oldBasis):
                yield tProduct
        
        elif gcf == newBasis:
            divisor = oldBasis // newBasis
            
            if round:
                for tDividend in t.add(divisor // 2):
                    for tQuotient in tDividend.div(divisor):
                        yield tQuotient
            
            else:
                for tQuotient in t.div(divisor):
                    yield tQuotient
        
        else:
            for tScaled in t.mul(lcm // oldBasis):
                for tResult in convert(tScaled, lcm, newBasis, round):
                    yield tResult

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

