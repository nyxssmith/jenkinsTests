#
# utilities.py
#
# Copyright © 2008, 2010, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Helper functions used by Triple objects.
"""

# System imports
import collections
import itertools

# Other imports
from fontio3.triple import triple
from fontio3.utilities import span3

# -----------------------------------------------------------------------------

#
# Public functions
#

def cmpInf(a, b):
    """
    Like cmp(a, b) but either a or b or both may also be the strings "+inf" and
    "-inf" for positive and negative infinity, respectively.
    
    ### v = ["-inf", -1, 0, 1, "+inf"]
    ### for a in v:
    ...   for b in v:
    ...     print "cmpInf(%s, %s) is %d" % (repr(a), repr(b), cmpInf(a, b))
    ... 
    cmpInf('-inf', '-inf') is 0
    cmpInf('-inf', -1) is -1
    cmpInf('-inf', 0) is -1
    cmpInf('-inf', 1) is -1
    cmpInf('-inf', '+inf') is -1
    cmpInf(-1, '-inf') is 1
    cmpInf(-1, -1) is 0
    cmpInf(-1, 0) is -1
    cmpInf(-1, 1) is -1
    cmpInf(-1, '+inf') is -1
    cmpInf(0, '-inf') is 1
    cmpInf(0, -1) is 1
    cmpInf(0, 0) is 0
    cmpInf(0, 1) is -1
    cmpInf(0, '+inf') is -1
    cmpInf(1, '-inf') is 1
    cmpInf(1, -1) is 1
    cmpInf(1, 0) is 1
    cmpInf(1, 1) is 0
    cmpInf(1, '+inf') is -1
    cmpInf('+inf', '-inf') is 1
    cmpInf('+inf', -1) is 1
    cmpInf('+inf', 0) is 1
    cmpInf('+inf', 1) is 1
    cmpInf('+inf', '+inf') is 0
    """
    
    if a == "+inf":
        return (0 if b == "+inf" else 1)
    
    if a == "-inf":
        return (0 if b == "-inf" else -1)
    
    if b == "+inf":
        return -1
    
    return (1 if b == "-inf" else ((a > b) - (a < b)))

def tripleIteratorFromIterable(it, *args):
    """
    Returns a generator for Triples that exactly cover the values in the
    specified iterable, with no overlap or duplication.
    
    ### list(tripleIteratorFromIterable([2, 3, 5, 11, 12, 14, 20]))
    [(2, 29, 9), (3, 21, 9), (5, 23, 9)]
    ### list(tripleIteratorFromIterable([0, 1, 4, 5]))
    [(0, 2, 1), (4, 6, 1)]
    ### list(tripleIteratorFromIterable(range(10000)))
    [(0, 10000, 1)]
    ### list(tripleIteratorFromIterable(range(0, 510, 51), 51))
    [(0, 510, 51)]
    """
    
    s = set(it)
    d = {}
    
    while s:
        chosen, outSet = tripleIteratorFromIterable_chunk(s)
        d[chosen] = outSet
        s -= outSet
    
    # Move values to connected places, if possible
    
    toCheck = {
      (n, (sk, md))
      for (sk, md), s in d.items()
      for n in s
      if (n - sk) not in s}
    
    toDo = []
    
    for n, (sk, md) in toCheck:
        for t, s in d.items():
            if t == (sk, md):
                continue
            
            if n - t[0] in s:
                toDo.append((n, (sk, md), t))
    
    for n, k1, k2 in toDo:
        d[k2].add(n)
        d[k1].discard(n)
    
    # Emit the Triples
    
    T = triple.Triple
    FS = span3.Span.fromsingles
    
    for k in sorted(d):
        sk, md = k
        sp = FS((n - md) // sk for n in d[k])
        
        for first, last in sp:
            yield T(first * sk + md, (last + 1) * sk + md, sk)

def tripleIteratorFromIterable_chunk(it):
    """
    """
    
    v = sorted(it)
    d = collections.defaultdict(set)
    
    for i in range(len(v) - 1):
        a, b = v[i:i+2]
        n = b - a
        d[(n, a % n)].update({a, a + n})
    
#     it1 = iter(v)
#     it2 = iter(v)
#     ignore = next(it2)
#     
#     for a, b in itertools.izip(it1, it2):
#         n = b - a
#         d[(n, a % n)].update({a, a + n})
    
    ranked = sorted((len(d[n]), n) for n in d if n[0] != 1)
    
    if ranked:
        chosen = ranked[-1][1]
    else:
        chosen = (1, 0)
    
    s = d[chosen]
    
    for n in v:
        if (n not in s) and ((n % chosen[0]) == chosen[1]):
            s.add(n)
    
    return (chosen, s)

# def tripleIteratorFromIterable(iterable, *suggestedSkips):
#     """
#     Given a (finite) iterable of single values, returns an iterator of Triples which
#     exactly cover the values with no duplicates. In the worst case this will be
#     a list of single-element Triples.
#     
#     If suggestedSkips are present they will be added to the trial skips.
#     
#     The need to specify the class explicitly arises from problems with circular
#     imports, given the lack of a macro facility in Python that would otherwise
#     permit easy creation of single modules from multiple source files.
#     
#     ### T = triple.Triple
#     ### list(tripleIteratorFromIterable([2, 3, 5, 11, 12, 14, 20]))
#     [(2, 29, 9), (3, 21, 9), (5, 23, 9)]
#     ### list(tripleIteratorFromIterable([0, 1, 4, 5]))
#     [(0, 2, 1), (4, 6, 1)]
#     ### list(tripleIteratorFromIterable(range(10000)))
#     [(0, 10000, 1)]
#     ### list(tripleIteratorFromIterable(range(0, 510, 51), 51))
#     [(0, 510, 51)]
#     """
#     
#     v = frozenset(iterable)  # do the set to remove duplicates
#     best = [len(v) + 1]
#     trials = list(suggestedSkips) + range(1, 17) + [32, 64, 256, 1024, 16384]
#     
#     for trial in trials:
#         d = collections.defaultdict(list)
#         
#         for n in v:
#             phase = n % trial
#             d[phase].append((n - phase) // trial)
#         
#         theSpans = dict((phase, span.Span(d[phase])) for phase in sorted(d.iterkeys()))
#         partLens = [len(x) for x in theSpans.itervalues()]
#         total = sum(partLens)
#         
#         if total < best[0]:
#             best[:] = [total, len(partLens), trial]
#             dSaved = theSpans
#         elif total == best[0] and len(partLens) < best[1]:
#             best[1:] = [len(partLens), trial]
#             dSaved = theSpans
#         
#         if best[:2] == [1, 1]:
#             break
#     
#     skip = best[-1]
#     
#     for phase, s in dSaved.iteritems():
#         for first, last in s:
#             start = first * skip + phase
#             stop = (last + 1) * skip + phase
#             yield triple.Triple(start, stop, skip)

def tripleListFromIterable(iterable, *suggestedSkips):
    """
    Given a (finite) iterable of single values, returns a list of Triples which
    exactly cover the values with no duplicates. In the worst case this will be
    a list of single-element Triples.
    
    The need to specify the class explicitly arises from problems with circular
    imports, given the lack of a macro facility in Python that would otherwise
    permit easy creation of single modules from multiple source files.
    
    ### T = triple.Triple
    ### tripleListFromIterable([2, 3, 5, 11, 12, 14, 20])
    [(2, 29, 9), (3, 21, 9), (5, 23, 9)]
    ### tripleListFromIterable([0, 1, 4, 5])
    [(0, 2, 1), (4, 6, 1)]
    ### tripleListFromIterable(range(10000))
    [(0, 10000, 1)]
    """
    
    return list(tripleIteratorFromIterable(iterable, *suggestedSkips))

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

