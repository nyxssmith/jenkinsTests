#
# span3.py
#
# Copyright © 2014, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Spans redone as simple tuples.
"""

# System imports
import collections
import itertools

# Other imports
# from fontio3 import utilities

# -----------------------------------------------------------------------------

#
# Functions
#

# def _canonicalize(it):
#     """
#     Given an iterable comprising (start, end) pairs, return a new tuple in
#     canonicalized form.
#     
#     >>> _canonicalize(((4, 6), (-12, -4), (5, 8), (0, 3)))
#     ((-12, -4), (0, 8))
#     """
#     
#     d = collections.defaultdict(set)
#     
#     for t in it:
#         d[(t[0] is None, t[1] is None)].add(t)
#     
#     if d[(True, True)]:
#         return ((None, None),)
#     
#     sLeft = d[(True, False)]
#     leftFence = (max(t[1] for t in sLeft) if sLeft else None)
#     
#     sRight = d[(False, True)]
#     rightFence = (max(t[0] for t in sRight) if sRight else None)
#     
#     sMiddle = d[(False, False)]
#     
#     # The following logic extends the fences where appropriate.
#     
#     if (leftFence is not None) and (rightFence is not None):
#         stillGoing = True
#         
#         while stillGoing:
#             for t in list(sMiddle):
#                 first, last = t
#                 
#                 if first <= leftFence and last > leftFence:
#                     leftFence = last
#                     
#                     if first < rightFence and last >= rightFence:
#                         rightFence = first
#                     
#                     sMiddle.discard(t)
#                     break
#                 
#                 if first < rightFence and last >= rightFence:
#                     rightFence = first
#                     sMiddle.discard(t)
#                     break
#             
#             else:
#                 stillGoing = False
#     
#     elif leftFence is not None:
#         stillGoing = True
#         
#         while stillGoing:
#             for t in list(sMiddle):
#                 first, last = t
#                 
#                 if first <= leftFence and last > leftFence:
#                     leftFence = last
#                     sMiddle.discard(t)
#                     break
#             
#             else:
#                 stillGoing = False
#     
#     elif rightFence is not None:
#         stillGoing = True
#         
#         while stillGoing:
#             for t in list(sMiddle):
#                 first, last = t
#                 
#                 if first < rightFence and last >= rightFence:
#                     rightFence = first
#                     sMiddle.discard(t)
#                     break
#             
#             else:
#                 stillGoing = False
#     
#     if (leftFence is not None) and (rightFence is not None) and (leftFence >= rightFence):
#         return ((None, None),)
#     
#     # Reconcile the middle pieces, which are now strictly separated from the
#     # fences (if any).
#     
#     vMiddle = []
#     
#     if sMiddle:
#         it = iter(sorted(sMiddle))
#         inProgress = next(it)
#     
#         for p in it:
#             if p[0] <= inProgress[1] + 1 and p[1] > inProgress[1]:
#                 inProgress = (inProgress[0], p[1])
#             
#             elif p[1] <= inProgress[1]:
#                 continue
#         
#             else:
#                 vMiddle.append(inProgress)
#                 inProgress = p
#     
#         vMiddle.append(inProgress)
#         
#     
#     
# #     stillGoing = True
# #     f = _pairIntersected_FFFF
# #     
# #     while stillGoing:
# #         for p1, p2 in itertools.combinations(list(sMiddle), 2):
# # #             if p1[1] < p2[0] or p2[1] < p1[0]:
# # #                 return ()
# # #     
# # #             return (max(p1[0], p2[0]), min(p1[1], p2[1]))
# #             
# #             
# #             
# #             
# #             
# #             
# #             
# #             
# #             
# #             if f(p1, p2):
# #                 p = (min(p1[0], p2[0]), max(p1[1], p2[1]))
# #                 sMiddle.discard(p1)
# #                 sMiddle.discard(p2)
# #                 sMiddle.add(p)
# #                 break
# #         
# #         else:
# #             stillGoing = False
# #     
# #     workSet = {n for first, last in sMiddle for n in range(first, last + 1)}
# #     it = utilities.monotonicGroupsGenerator(sorted(workSet))
#     
#     # Put the pieces together
#     
#     v = ([] if leftFence is None else [(None, leftFence)])
#     v.extend(vMiddle)
#     
#     if rightFence is not None:
#         v.append((rightFence, None))
#     
#     return tuple(v)

def _canonicalize(it):
    """
    Given an iterable comprising (start, end) pairs, return a new tuple in
    canonicalized form.
    
    >>> _canonicalize(((4, 6), (-12, -4), (5, 8), (0, 3)))
    ((-12, -4), (0, 8))
    """
    
    s = set(it)
    
    if (None, None) in s:
        return ((None, None),)
    
    if len(s) == 1:
        return tuple(s)
    
    leftFence = rightFence = None
    pool = []
    
    for low, high in s:
        if low is None:
            if leftFence is None or high > leftFence:
                leftFence = high
        
        elif high is None:
            if rightFence is None or low < rightFence:
                rightFence = low
        
        else:
            pool.append((low, high))
    
    if pool:
        pool.sort()
        index = 0
        
        # consolidate overlapping or adjacent entries
        
        while index < len(pool) - 1:
            low1, high1 = pool[index]
            low2, high2 = pool[index + 1]
            
            if low2 > high1 + 1:
                pass
            
            elif high2 > high1:
                pool[index] = (low1, high2)
                del pool[index + 1]
                index -= 1
            
            else:
                del pool[index + 1]
                index -= 1
            
            index += 1
        
        # remove or modify entries at any open ends
        
        if pool and (leftFence is not None):
            index = 0
            
            while index < len(pool):
                low, high = pool[index]
                
                if high <= leftFence:
                    del pool[index]
                    index -= 1
                
                elif low > leftFence + 1:
                    break
                
                else:
                    leftFence = high
                    del pool[index]
                    index -= 1
                
                index += 1
        
        if pool and rightFence is not None:
            index = len(pool) - 1
            
            while pool and index >= 0:
                low, high = pool[index]
                
                if low >= rightFence:
                    del pool[index]
                
                elif high < rightFence - 1:
                    break
                
                else:
                    rightFence = low
                    del pool[index]
                
                index -= 1
    
    # we're now ready to write the canonical list back
    
    if (
      (leftFence is not None) and
      (rightFence is not None) and
      (leftFence >= rightFence - 1)):
        
        v = [(None, None)]
    
    else:
        v = []
        
        if leftFence is not None:
            v.append((None, leftFence))
        
        v.extend(pool)
        
        if rightFence is not None:
            v.append((rightFence, None))
    
    return tuple(v)

def _pairIntersected(p1, p2):
    t = (p1[0] is None, p1[1] is None, p2[0] is None, p2[1] is None)
    return _pairIntersected_dispatch[t](p1, p2)

def _pairIntersected_FFFF(p1, p2):
    """
    >>> _pairIntersected_FFFF((5, 10), (40, 70))
    ()
    >>> _pairIntersected_FFFF((5, 10), (-90, -70))
    ()
    >>> _pairIntersected_FFFF((5, 10), (7, 20))
    (7, 10)
    >>> _pairIntersected_FFFF((5, 10), (4, 8))
    (5, 8)
    >>> _pairIntersected_FFFF((5, 10), (0, 100))
    (5, 10)
    >>> _pairIntersected_FFFF((5, 10), (6, 7))
    (6, 7)
    """
    
    if p1[1] < p2[0] or p2[1] < p1[0]:
        return ()
    
    return (max(p1[0], p2[0]), min(p1[1], p2[1]))

def _pairIntersected_FFFT(p1, p2):
    """
    >>> _pairIntersected_FFFT((5, 10), (40, None))
    ()
    >>> _pairIntersected_FFFT((5, 10), (8, None))
    (8, 10)
    >>> _pairIntersected_FFFT((5, 10), (2, None))
    (5, 10)
    """
    
    return (() if p1[1] < p2[0] else (max(p1[0], p2[0]), p1[1]))

def _pairIntersected_FFTF(p1, p2):
    """
    >>> _pairIntersected_FFTF((5, 10), (None, 2))
    ()
    >>> _pairIntersected_FFTF((5, 10), (None, 8))
    (5, 8)
    >>> _pairIntersected_FFTF((5, 10), (None, 40))
    (5, 10)
    """
    
    return (() if p1[0] > p2[1] else (p1[0], min(p1[1], p2[1])))

def _pairIntersected_FTFT(p1, p2):
    """
    >>> _pairIntersected_FTFT((5, None), (0, None))
    (5, None)
    >>> _pairIntersected_FTFT((5, None), (10, None))
    (10, None)
    """
    
    return (max(p1[0], p2[0]), None)

def _pairIntersected_FTTF(p1, p2):
    """
    >>> _pairIntersected_FTTF((5, None), (None, 2))
    ()
    >>> _pairIntersected_FTTF((5, None), (None, 8))
    (5, 8)
    >>> _pairIntersected_FTTF((5, None), (None, 40))
    (5, 40)
    """
    
    return (() if p1[0] > p2[1] else (p1[0], p2[1]))

def _pairIntersected_TFTF(p1, p2):
    """
    >>> _pairIntersected_TFTF((None, 5), (None, 2))
    (None, 2)
    >>> _pairIntersected_TFTF((None, 5), (None, 40))
    (None, 5)
    """
    
    return (None, min(p1[1], p2[1]))

_pairIntersected_dispatch = {
  (False, False, False, False): _pairIntersected_FFFF,
  (False, False, False, True): _pairIntersected_FFFT,
  (False, False, True, False): _pairIntersected_FFTF,
  (False, False, True, True): (lambda p1, p2: p1),
  (False, True, False, False): (lambda p1, p2: _pairIntersected_FFFT(p2, p1)),
  (False, True, False, True): _pairIntersected_FTFT,
  (False, True, True, False): _pairIntersected_FTTF,
  (False, True, True, True): (lambda p1, p2: p1),
  (True, False, False, False): (lambda p1, p2: _pairIntersected_FFTF(p2, p1)),
  (True, False, False, True): (lambda p1, p2: _pairIntersected_FTTF(p2, p1)),
  (True, False, True, False): _pairIntersected_TFTF,
  (True, False, True, True): (lambda p1, p2: p1),
  (True, True, False, False): (lambda p1, p2: p2),
  (True, True, False, True): (lambda p1, p2: p2),
  (True, True, True, False): (lambda p1, p2: p2),
  (True, True, True, True): (lambda p1, p2: p1)}

def disjointlyIntersectedGroup(iterable, **kwArgs):
    """
    Given an iterable over Span objects, if all the objects are disjoint, then
    return an empty list. Otherwise, return a list of (originalIndex, newSpan)
    representing the disjoint intersection.
    
    >>> obj1 = Span(((None, 30),))
    >>> obj2 = Span(((100, None),))
    >>> disjointlyIntersectedGroup([obj1, obj2])
    []
    
    >>> obj3 = Span(((10, 45),))
    >>> disjointlyIntersectedGroup([obj1, obj2, obj3])
    [(0, ((10, 30),)), (0, ((None, 9),)), (1, ((100, None),)), (2, ((31, 45),))]
    
    >>> s0 = Span(((35, 64),))
    >>> s1 = Span(((None, 64),))
    >>> s2 = Span(((35, None),))
    >>> sorted(disjointlyIntersectedGroup([s0, s1, s2]), key=str)
    [(1, ((None, 34),)), (2, ((35, 64),)), (2, ((65, None),))]
    
    >>> s0 = Span(((35, 35),))
    >>> s1 = Span(((35, 64),))
    >>> s2 = Span(((36, 64),))
    >>> s3 = Span(((65, None),))
    >>> sorted(disjointlyIntersectedGroup([s0, s1, s2, s3], greedy=True), key=str)
    [(1, ((35, 64),)), (3, ((65, None),))]
    >>> sorted(disjointlyIntersectedGroup([s0, s1, s2, s3], greedy=False), key=str)
    [(0, ((35, 35),)), (1, ((36, 64),)), (3, ((65, None),))]
    """
    
    if kwArgs.pop('debug', False):
        import pdb; pdb.set_trace()
    
    v = list(enumerate(iterable))
    tryAgain = True
    madeChange = False
    
    while tryAgain:
        for t1, t2 in itertools.combinations(list(v), 2):
            i1, s1 = t1
            i2, s2 = t2
            pairDI = s1.disjointlyIntersected(s2, **kwArgs)
            
            if not pairDI:
                continue
            
            madeChange = True
            d = {0: i1, 1: i2}
            v = [t for t in v if t[0] not in {i1, i2}]
            v.extend((d[n], s) for n, s in pairDI if s)
            break
        
        else:
            tryAgain = False
    
    if not madeChange:
        return []
    
    return sorted(v, key=(lambda k: (k[0], str(k[1]))))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Span(tuple):
    """
    """
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a readable string representation.
        
        >>> print(Span(((None, -40), (-12, 19), (23, 23), (25, None))))
        -40 and under, -12..19, 23, or 25 and over
        >>> print(Span(((None, None),)))
        (all)
        >>> print(Span())
        (empty)
        """
        
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
        >>> s
        ((0, 5), (9, 14))
        >>> s.addedFromPairs(((-4, 3), (8, 17), (100, None)))
        ((-4, 5), (8, 17), (100, None))
        """
        
        itBoth = itertools.chain(iter(self), it)
        return type(self)(_canonicalize(itBoth))
    
    def addedFromSingles(self, it):
        """
        Returns a new Span with the individual values from the specified
        iterator added.
        
        >>> s = Span(((0, 5), (9, 14)))
        >>> s
        ((0, 5), (9, 14))
        >>> s.addedFromSingles((3, 7, 14, 15, 16))
        ((0, 5), (7, 7), (9, 16))
        """
        
        itBoth = itertools.chain(iter(self), ((n, n) for n in it))
        return type(self)(_canonicalize(itBoth))
    
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
        
        if not self:
            return False
        
        if self[0] == (None, None):
            return True
        
        start = 0
        stop = len(self)
        
        if self[0][0] is None:
            if n <= self[0][1]:
                return True
            
            start += 1
        
        if self[-1][1] is None:
            if n >= self[-1][0]:
                return True
            
            stop -= 1
        
        return any(obj[0] <= n <= obj[1] for obj in self[start:stop])
    
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
        
        if not self:
            return 0
        
        if self[0][0] is None or self[-1][1] is None:
            return None
        
        return sum(b - a + 1 for a, b in self)
    
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
        
        return cls(_canonicalize((n, n) for n in it))
    
#     def intersected(self, other):
#         """
#         Returns a new Span with the results of the intersection.
#         
#         >>> s1 = Span.fromsingles((1, 2, 3, 5, 6, 7, 8))
#         >>> s2 = Span.fromsingles((4, 6, 8, 10))
#         >>> s1.intersected(s2)
#         ((6, 6), (8, 8))
#         """
#         
#         if other == ((None, None),):
#             return self
#         
#         if self == ((None, None),):
#             return other
#         
#         return self.inverted().addedFromPairs(other.inverted()).inverted()
    
    def intersected(self, other):
        """
        Returns a new Span with the results of the intersection.
        
        >>> s1 = Span.fromsingles((1, 2, 3, 5, 6, 7, 8))
        >>> s2 = Span.fromsingles((4, 6, 8, 10))
        >>> s1.intersected(s2)
        ((6, 6), (8, 8))
        """
        
        if other == ((None, None),):
            return self
        
        if not other:
            return type(self)()
        
        v = [_pairIntersected(p1, p2) for p1, p2 in itertools.product(self, other)]
        return type(self)(_canonicalize(t for t in v if t))
    
    def inverted(self):
        """
        Inverts the span, so what was excluded is now included and vice versa.
        This works correctly for open-ended Span as well as closed Spans.
        
        >>> Span.fromsingles([1, 2, 3, 5]).inverted()
        ((None, 0), (4, 4), (6, None))
        
        >>> Span.fromsingles([1, 2, 3, 5]).inverted().inverted()
        ((1, 3), (5, 5))
        
        >>> Span().inverted()
        ((None, None),)
        """
        
        if not self:
            return type(self)(((None, None),))
        
        if self == ((None, None),):
            return type(self)()
        
        v = ([(None, self[0][0] - 1)] if self[0][0] is not None else [])
        index = 0
        
        while index < len(self) - 1:
            high1 = self[index][1]
            low2 = self[index + 1][0]
            v.append((high1 + 1, low2 - 1))
            index += 1
        
#         if self[0][0] is not None:
#             v.insert(0, (None, self[0][0] - 1))
        
        if self[-1][1] is not None:
            v.append((self[-1][1] + 1, None))
        
        return type(self)(v)  # already canonicalized
    
#     def inverted(self):
#         """
#         Faster inversion?
#         
#         >>> Span.fromsingles([1, 2, 3, 5]).inverted()
#         ((None, 0), (4, 4), (6, None))
#         
#         >>> Span.fromsingles([1, 2, 3, 5]).inverted().inverted()
#         ((1, 3), (5, 5))
#         
#         >>> Span().inverted()
#         ((None, None),)
#         """
#         
#         if not self:
#             return type(self)(((None, None),))
#         
#         L = self[0][0]
#         R = self[-1][1]
#         
#         if L is None:
#             v = [(a[1]+1, b[0]-1) for a, b in zip(self, self[1:])]
#             
#             if R is not None:
#                 v.append((R + 1, None))
#         
#         elif R is None:
#             v = [(None, L - 1)]
#             v.extend((a[1]+1, b[0]-1) for a, b in zip(self, self[1:]))
#         
#         else:
#             v = [(None, L - 1)]
#             v.extend((a[1]+1, b[0]-1) for a, b in zip(self, self[1:]))
#             v.append((R + 1, None))
#         
#         return type(self)(v)
#         
#         
# #         it1 = iter(self)
# #         it2 = iter(self)
# #         ignore = next(it2)
# #         itMiddle = ((a[1]+1, b[0]-1) for a, b in zip(it1, it2))
# #         
# #         if self[0][0] is None:
# #             if self[-1][1] is None:
# #                 itLeft = iter([])
# #                 itRight = iter([])
# #             
# #             else:
# #                 itLeft = iter([])
# #                 itRight = iter([(self[-1][1] + 1, None)])
# #         
# #         elif self[-1][1] is None:
# #             itLeft = iter([(None, self[0][0] - 1)])
# #             itRight = iter([])
# #         
# #         else:
# #             itLeft = iter([(None, self[0][0] - 1)])
# #             itRight = iter([(self[-1][1] + 1, None)])
# #         
# #         return type(self)(itertools.chain(itLeft, itMiddle, itRight))
    
    def isFull(self):
        return self == ((None, None),)
    
    unioned = addedFromPairs

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
