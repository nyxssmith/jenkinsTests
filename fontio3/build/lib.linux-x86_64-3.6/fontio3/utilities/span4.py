#
# span4.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved
#

"""
Thin front-end to superfast C implementation of Spans.
"""

# Other imports
from fontio3 import cspanbackend

# -----------------------------------------------------------------------------

#
# Classes
#

class Span(object):
    """
    """
    
    #
    # Methods
    #
    
    def __bool__(self):
        """
        """
        
        return cspanbackend.cspanBool(self.capsule)
    
    def __eq__(self, other):
        """
        Returns True if self and other are equal. Note the assumption of
        canonicalization is used implicitly in the underlying implementation!
        
        >>> obj1 = Span(((10, 30), (40, None)))
        >>> obj2 = Span(((11, 30),))
        >>> obj1 == obj2
        False
        >>> obj3 = obj2.addedFromPairs(((10, 10), (40, None)))
        >>> obj1 == obj3
        True
        """
        
        return cspanbackend.cspanEqual(self.capsule, other.capsule)
    
    def __init__(self, iterable=None):
        """
        Initialize the Span to the specified sequence of pairs.
        
        >>> obj = Span(((None, 40), (65, 90)))
        >>> print(obj)
        40 and under, or 65..90
        
        >>> print(Span())
        (empty)
        """
        
        self.capsule = cspanbackend.cspanNewContext(tuple(iterable or ()))
    
    def __repr__(self):
        return repr(self.asTuple())
    
    def __str__(self):
        """
        """
        
        self = self.asTuple()
        
        if not self:
            return "(empty)"
        
        if (
          (len(self) == 2) and
          (self[0][0] is None) and
          (self[1][1] is None) and
          (self[0][1] == (self[1][0] - 2))):
          
            return "not %d" % (self[0][1] + 1,)
        
        fmts = ["%s%d and under", "%s%d and over", "%s%d", "%s%d..%d"]
        sv = []
        
        for i, (start, end) in enumerate(self):
            if (len(self) > 1) and (i == (len(self) - 1)):
                s = 'or '
            else:
                s = ''
            
            if (start is None) and (end is None):
                sv.append("(all)")
            
            elif start is None:
                sv.append(fmts[0] % (s, end))
            
            elif end is None:
                sv.append(fmts[1] % (s, start))
            
            elif start == end:
                sv.append(fmts[2] % (s, start))
            
            else:
                sv.append(fmts[3] % (s, start, end))
        
        return ', '.join(sv)
    
    def addedFromPairs(self, it):
        """
        Returns a new Span with the pairs from the specified iterator added.
        
        >>> s = Span(((0, 5), (9, 14)))
        >>> print(s)
        0..5, or 9..14
        >>> print(s.addedFromPairs(((-4, 3), (8, 17), (100, None))))
        -4..5, 8..17, or 100 and over
        """
        
        r = type(self).__new__(type(self))  # bypass __init__
        r.capsule = cspanbackend.cspanAddedFromPairs(self.capsule, tuple(it))
        return r
    
    def addedFromSingles(self, it):
        """
        Returns a new Span with the individual values from the specified
        iterator added.
        
        >>> s = Span(((0, 5), (9, 14)))
        >>> print(s)
        0..5, or 9..14
        >>> print(s.addedFromSingles((3, 7, 14, 15, 16)))
        0..5, 7, or 9..16
        """
        
        r = type(self).__new__(type(self))  # bypass __init__
        r.capsule = cspanbackend.cspanAddedFromSingles(self.capsule, tuple(it))
        return r
        
    def asTuple(self):
        """
        """
        
        return cspanbackend.cspanAsTuple(self.capsule)
    
    def containsValue(self, n):
        """
        Returns True if n is contained. Note we provide this explicit method,
        as opposed to overriding __contains__; this is for speed.
        
        >>> Span().containsValue(3)
        False
        >>> Span(((None, None),)).containsValue(3)
        True
        >>> s = Span(((None, 12), (19, 35), (50, None)))
        >>> v = [-1, 15, 20, 40, 60]
        >>> [s.containsValue(n) for n in v]
        [True, False, True, False, True]
        """
        
        return cspanbackend.cspanContainsValue(self.capsule, n)
    
    def count(self):
        """
        Returns the number of individual values, or None if open-ended.
        
        >>> Span(((4, 12), (100, 100))).count()
        10
        >>> Span().count()
        0
        >>> print(Span(((None, -4),)).count())
        None
        """
        
        return cspanbackend.cspanCount(self.capsule)
    
    def disjointlyIntersected(self, other, **kwArgs):
        """
        Given two Spans, returns a list of (index, newSpan) tuples. These
        represent the intersection, broken into disjoint Spans. If self and/or
        other have to be split apart, the index in each tuple indicates whether
        this newSpan comes from self (0) or other (1).
        
        There are 4 general cases. The first case is where self and other do
        not intersect; as a special case, this just returns the empty list:
        
        >>> obj1 = Span(((None, 40), (60, 90)))
        >>> obj2 = Span(((130, None),))
        >>> obj1.disjointlyIntersected(obj2)
        []
        
        The second case is where other is a subset of self:
        
        >>> obj1 = Span(((10, 100),))
        >>> obj2 = Span(((50, 65), (75, 80)))
        >>> obj1.disjointlyIntersected(obj2)
        [(0, ((10, 100),))]
        
        Note that a sub-case here is where the two are equal:
        
        >>> obj1.disjointlyIntersected(obj1)
        [(0, ((10, 100),))]
        
        The "greedy" keyword argument (default True) controls whether maximum
        coalescing happens. If we set it to False, note the effect:
        
        >>> for obj in obj1.disjointlyIntersected(obj2, greedy=False):
        ...     print(obj)
        (0, ((10, 49), (66, 74), (81, 100)))
        (1, ((50, 65), (75, 80)))
        
        The third case is where self is a subset of other:
        
        >>> obj2.disjointlyIntersected(obj1)
        [(1, ((10, 100),))]
        
        The fourth case is where self and other overlap:
        
        >>> obj1 = Span(((None, 50),))
        >>> obj2 = Span(((20, None),))
        >>> obj1.disjointlyIntersected(obj2)
        [(0, ((None, 19),)), (0, ((20, 50),)), (1, ((51, None),))]
        """
        
        greedy = kwArgs.pop('greedy', True)
        rawSect = self.intersected(other)
        
        # case 1: no intersection (greedy is ignored here)
        if not rawSect:
            return []
        
        # case 2: other is a subset of self (or they're equal)
        if rawSect == other:
            if greedy:
                return [(0, self)]
            
            selfMinusOther = self.intersected(other.inverted())
            return [(0, selfMinusOther), (1, other)]
        
        # case 3: self is a subset of other
        if rawSect == self:
            if greedy:
                return [(1, other)]
            
            otherMinusSelf = other.intersected(self.inverted())
            return [(0, self), (1, otherMinusSelf)]
        
        # case 4: self and other overlap (greedy is ignored here)
        rawInv = rawSect.inverted()
        selfMinus = self.intersected(rawInv)
        otherMinus = other.intersected(rawInv)
        return [(0, selfMinus), (0, rawSect), (1, otherMinus)]
    
    @classmethod
    def fromsingles(cls, it):
        """
        Given an iterator over single values, return a Span.
        
        >>> Span.fromsingles((5, 1, 3, 4, -9, -7, -8))
        ((-9, -7), (1, 1), (3, 5))
        """
        
        return cls(tuple((n, n) for n in it))
    
    def intersected(self, other):
        """
        Returns the intersection as a new object.
        
        >>> print(Span(((None, None),)).intersected(Span(((13, 29),))))
        13..29
        >>> print(Span(((None, 30),)).intersected(Span(((10, 20),))))
        10..20
        >>> print(Span(((None, 30),)).intersected(Span(((10, 40),))))
        10..30
        >>> print(Span(((None, 30),)).intersected(Span(((70, 80),))))
        (empty)
        >>> print(Span(((1, 20),)).intersected(Span(((13, 55),))))
        13..20
        """
        
        r = type(self).__new__(type(self))  # bypass __init__
        r.capsule = cspanbackend.cspanIntersected(self.capsule, other.capsule)
        return r
    
    def inverted(self):
        """
        Returns the inverse as a new object.
        
        >>> print(Span(((30, 49),)).inverted())
        29 and under, or 50 and over
        
        >>> print(Span(((None, 15), (30, 50))).inverted())
        16..29, or 51 and over
        
        >>> print(Span(((5, 15), (30, 50))).inverted())
        4 and under, 16..29, or 51 and over
        
        >>> print(Span(((None, 15), (30, None))).inverted())
        16..29
        
        >>> print(Span(((5, 15), (30, None))).inverted())
        4 and under, or 16..29
        
        >>> print(Span().inverted())
        (all)
        
        >>> print(Span(((None, None),)).inverted())
        (empty)
        """
        
        r = type(self).__new__(type(self))  # bypass __init__
        r.capsule = cspanbackend.cspanInverted(self.capsule)
        return r
    
    def unioned(self, other):
        """
        Returns the union as a new object.
        
        >>> obj1 = Span(((10, 40), (60, 90)))
        >>> obj2 = Span(((30, 70),))
        >>> print(obj1.unioned(obj2))
        10..90
        
        >>> print(obj1.inverted().unioned(obj2))
        9 and under, 30..70, or 91 and over
        
        >>> obj3 = Span(((None, 50),))
        >>> obj4 = Span(((10, None),))
        >>> print(obj3.unioned(obj4))
        (all)
        """
        
        r = type(self).__new__(type(self))  # bypass __init__
        r.capsule = cspanbackend.cspanUnioned(self.capsule, other.capsule)
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
