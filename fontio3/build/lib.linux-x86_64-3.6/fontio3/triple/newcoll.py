#
# newcoll.py
#
# Copyright © 2009, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
New-style collection objects that subsume behavior of both Triples and
Collections.
"""

# System imports
import itertools
import operator

# Other imports
from fontio3.fontmath import rational
from functools import reduce

# -----------------------------------------------------------------------------

#
# Private functions
#

def _mergePairIntoPhaseList(start, stop, v):
    """
    The range (start, stop) is integrated into the existing contents (if any)
    of the list v.
    
    Returns True if any changes were made to v; False otherwise.
    
    >>> v = []
    >>> _mergePairIntoPhaseList(10, 20, v)
    True
    >>> v
    [(10, 20)]
    >>> _mergePairIntoPhaseList(14, 18, v)
    False
    >>> _mergePairIntoPhaseList(None, 15, v)
    True
    >>> v
    [(None, 20)]
    >>> _mergePairIntoPhaseList(100, None, v)
    True
    >>> v
    [(None, 20), (100, None)]
    >>> _mergePairIntoPhaseList(None, None, v)
    True
    >>> v
    [(None, None)]
    """
    
    madeChange = False
    
    if not v:
        v.append((start, stop))
        madeChange = True
    elif start is None and stop is None:
        madeChange = v != [(None, None)]
        v[:] = [(None, None)]
    elif start is None:
        madeChange = _mergePairIntoPhaseList_O_C(stop, v)
    elif stop is None:
        madeChange = _mergePairIntoPhaseList_C_O(start, v)
    else:
        madeChange = _mergePairIntoPhaseList_C_C(start, stop, v)
    
    return madeChange

def _mergePairIntoPhaseList_C_C(start, stop, v):
    """
    Merges a closed pair into v.
    
    >>> v = [(10, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(30, 50, v)
    >>> v
    [(10, 20), (30, 50)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(0, 5, v)
    >>> v
    [(0, 5), (10, 20), (30, 50)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(25, 27, v)
    >>> v
    [(0, 5), (10, 20), (25, 27), (30, 50)]
    >>> v = [(None, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(30, 40, v)
    >>> v
    [(None, 20), (30, 40)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(5, 15, v)
    >>> v
    [(None, 20), (30, 40)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(10, 25, v)
    >>> v
    [(None, 25), (30, 40)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(25, 30, v)
    >>> v
    [(None, 40)]
    >>> v = [(10, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(5, 7, v)
    >>> v
    [(5, 7), (10, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(15, 17, v)
    >>> v
    [(5, 7), (10, 20)]
    >>> v = [(None, 20), (50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(5, 15, v)
    >>> v
    [(None, 20), (50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(75, 200, v)
    >>> v
    [(None, 20), (50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(25, 30, v)
    >>> v
    [(None, 20), (25, 30), (50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(45, 50, v)
    >>> v
    [(None, 20), (25, 30), (45, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(27, 47, v)
    >>> v
    [(None, 20), (25, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_C(20, 25, v)
    >>> v
    [(None, None)]
    """
    
    madeChange = True
    i = 0
    
    while i < len(v):
        thisStart, thisStop = v[i]
        
        if thisStart is None:
            if stop <= thisStop:
                madeChange = False
                break  # already covered
            elif start <= thisStop:
                madeChange = _mergePairIntoPhaseList_O_C(stop, v)
                break
            else:
                i += 1
        
        elif thisStop is None:
            if start >= thisStart:
                madeChange = False
                pass  # already covered
            elif stop >= thisStart:
                madeChange = _mergePairIntoPhaseList_C_O(start, v)
            else:
                v.insert(i, (start, stop))
            
            break
        
        else:
            if start < thisStart:
                if stop < thisStart:
                    v.insert(i, (start, stop))
                    break
                elif stop <= thisStop:
                    v[i] = (start, thisStop)
                    break
                else:
                    del v[i]  # and continue with same i
            
            elif start <= thisStop:
                if stop <= thisStop:
                    madeChange = False
                    break  # already covered
                else:
                    start = thisStart
                    del v[i]  # and continue with same i
            
            else:
                i += 1
    
    else:
        v.append((start, stop))  # whether or not v is empty
    
    return madeChange

def _mergePairIntoPhaseList_C_O(start, v):
    """
    Merges a new open-right pair with the specified start into v.
    
    >>> v = [(50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(75, v)
    >>> v
    [(50, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(35, v)
    >>> v
    [(35, None)]
    >>> v = [(10, 20), (30, None)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(25, v)
    >>> v
    [(10, 20), (25, None)]
    >>> v = [(None, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(25, v)
    >>> v
    [(None, 20), (25, None)]
    >>> v = [(None, 20)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(15, v)
    >>> v
    [(None, None)]
    >>> v = [(10, 20), (30, 50)]            
    >>> madeChange = _mergePairIntoPhaseList_C_O(60, v)
    >>> v
    [(10, 20), (30, 50), (60, None)]
    >>> v = [(10, 20), (30, 50)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(40, v)
    >>> v
    [(10, 20), (30, None)]
    >>> v = [(10, 20), (30, 50)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(15, v)
    >>> v
    [(10, None)]
    >>> v = [(None, 20), (30, 50)]
    >>> madeChange = _mergePairIntoPhaseList_C_O(10, v)
    >>> v
    [(None, None)]
    """
    
    madeChange = True
    
    while v:
        thisStart, thisStop = v[-1]
        
        if thisStop is None:
            if thisStart <= start:
                madeChange = False
                break  # already covered
            else:
                del v[-1]
        
        elif thisStart is None:
            if start <= thisStop:
                v[:] = [(None, None)]
            else:
                v.append((start, None))
            
            break
        
        else:
            if thisStart >= start:
                del v[-1]
            elif thisStop >= start:
                v[-1] = (thisStart, None)
                break
            else:
                v.append((start, None))
    
    else:
        if not v:
            v.append((start, None))
    
    return madeChange

def _mergePairIntoPhaseList_O_C(stop, v):
    """
    Merges a new open-left pair with the specified stop into v.
    
    >>> v = [(None, 10)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(5, v)
    >>> v
    [(None, 10)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(15, v)
    >>> v
    [(None, 15)]
    >>> v = [(None, 10), (20, 30)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(15, v)
    >>> v
    [(None, 15), (20, 30)]
    >>> v = [(20, None)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(15, v)
    >>> v
    [(None, 15), (20, None)]
    >>> v = [(20, None)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(25, v)
    >>> v
    [(None, None)]
    >>> v = [(20, 30), (50, 75)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(10, v)
    >>> v
    [(None, 10), (20, 30), (50, 75)]
    >>> v = [(20, 30), (50, 75)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(25, v)
    >>> v
    [(None, 30), (50, 75)]
    >>> v = [(20, 30), (50, 75)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(60, v)
    >>> v
    [(None, 75)]
    >>> v = [(20, 30), (50, None)]
    >>> madeChange = _mergePairIntoPhaseList_O_C(60, v)
    >>> v
    [(None, None)]
    """
    
    madeChange = True
    
    while v:
        thisStart, thisStop = v[0]
        
        if thisStart is None:
            if thisStop >= stop:
                madeChange = False
                break  # already covered
            else:
                del v[0]
        
        elif thisStop is None:
            if stop >= thisStart:
                v[:] = [(None, None)]
            else:
                v.insert(0, (None, stop))
            
            break
        
        else:
            if thisStop <= stop:
                del v[0]
            elif thisStart <= stop:
                v[0] = (None, thisStop)
                break
            else:
                v.insert(0, (None, stop))
                break
    
    else:
        if not v:
            v.append((None, stop))
    
    return madeChange

def _phaseListContainsValue(v, n):
    """
    Returns True if the specified value is covered by the phaseList.
    
    >>> f = _phaseListContainsValue
    >>> f([(None, None)], 10)
    True
    >>> f([(None, 20)], 5), f([(None, 20)], 30)
    (True, False)
    >>> f([(20, None)], 5), f([(20, None)], 30)
    (False, True)
    >>> v = [(10, 30), (45, 75)]
    >>> f(v, 5), f(v, 15), f(v, 40), f(v, 65), f(v, 80)
    (False, True, False, True, False)
    """
    
    for start, stop in v:
        if start is None and stop is None:
            return True
        elif start is None:
            if n < stop:
                return True
        elif stop is None:
            if n >= start:
                return True
        else:
            if start <= n < stop:
                return True
    
    return False

def _removePairFromPhaseList(start, stop, v):
    """
    The range (start, stop) is removed from the existing contents of the list
    v, which must not be empty.
    
    Returns True if any changes were made to v; False otherwise.
    
    >>> v = [(None, None)]
    >>> _removePairFromPhaseList(20, 50, v)
    True
    >>> v
    [(None, 20), (50, None)]
    """
    
    assert v
    
    if start is None and stop is None:
        v[:] = []
        madeChange = True
    elif start is None:
        madeChange = _removePairFromPhaseList_O_C(stop, v)
    elif stop is None:
        madeChange = _removePairFromPhaseList_C_O(start, v)
    else:
        madeChange = _removePairFromPhaseList_C_C(start, stop, v)
    
    return madeChange

def _removePairFromPhaseList_C_C(start, stop, v):
    """
    Removes the closed range from v. This function may leave v completely
    empty.
    
    Returns True if any changes were made to v, False otherwise.
    
    >>> v = [(None, None)]
    >>> madeChange = _removePairFromPhaseList_C_C(20, 50, v)
    >>> print(madeChange, v)
    True [(None, 20), (50, None)]
    >>> print(_removePairFromPhaseList_C_C(25, 45, v))
    False
    >>> madeChange = _removePairFromPhaseList(70, None, v)
    >>> print(madeChange, v)
    True [(None, 20), (50, 70)]
    >>> madeChange = _removePairFromPhaseList(None, -40, v)
    >>> print(madeChange, v)
    True [(-40, 20), (50, 70)]
    >>> madeChange = _removePairFromPhaseList(None, None, v)
    >>> print(madeChange, v)
    True []
    """
    
    madeChange = False
    i = 0
    
    while i < len(v):
        thisStart, thisStop = v[i]
        
        if thisStart is None and thisStop is None:
            v[:] = [(None, start), (stop, None)]
            madeChange = True
            break
        
        elif thisStart is None:
            if stop < thisStop:
                v[i:i+1] = [(None, start), (stop, thisStop)]
                madeChange = True
                break
            
            elif start < thisStop:
                v[i] = (None, start)
                madeChange = True
                i += 1
            
            else:
                i += 1
        
        elif thisStop is None:
            if stop > thisStart:
                if start <= thisStart:
                    v[i] = (stop, None)
                else:
                    v[i:] = [(thisStart, start), (stop, None)]
                
                madeChange = True
            
            break
        
        elif thisStart < start:
            if thisStop <= start:
                i += 1
            elif thisStop <= stop:
                v[i] = (thisStart, start)
                madeChange = True
                i += 1
            else:
                v[i:i+1] = [(thisStart, start), (stop, thisStop)]
                madeChange = True
                break
        
        elif thisStart <= stop:
            madeChange = True
            
            if thisStop <= stop:
                del v[i]
            else:
                v[i] = (stop, thisStop)
                break
        
        else:
            break
    
    return madeChange

def _removePairFromPhaseList_C_O(start, v):
    """
    Removes the open-right range with the specified start from v. This function
    may leave v completely empty.
    
    Returns True if any changes were made to v, False otherwise.
    
    >>> v = [(None, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(20, v)
    >>> print(madeChange, v)
    True [(None, 20)]
    
    >>> v = [(None, 20)]
    >>> madeChange = _removePairFromPhaseList_C_O(10, v)
    >>> print(madeChange, v)
    True []
    >>> v = [(None, 20)]
    >>> madeChange = _removePairFromPhaseList_C_O(50, v)
    >>> print(madeChange, v)
    False [(None, 20)]
    >>> v = [(None, 20), (30, 60), (90, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(50, v)
    >>> print(madeChange, v)
    True [(None, 20), (30, 50)]
    
    >>> v = [(20, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(10, v)
    >>> print(madeChange, v)
    True []
    >>> v = [(20, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(40, v)
    >>> print(madeChange, v)
    True [(20, 40)]
    >>> v = [(5, 15), (20, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(40, v)
    >>> print(madeChange, v)
    True [(5, 15), (20, 40)]
    
    >>> v = [(20, 50), (100, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(5, v)
    >>> print(madeChange, v)
    True []
    >>> v = [(0, 50), (100, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(5, v)
    >>> print(madeChange, v)
    True [(0, 5)]
    >>> v = [(0, 2), (100, None)]
    >>> madeChange = _removePairFromPhaseList_C_O(5, v)
    >>> print(madeChange, v)
    True [(0, 2)]
    """
    
    madeChange = False
    i = 0
    
    while i < len(v):
        thisStart, thisStop = v[i]
        
        if thisStart is None and thisStop is None:
            v[:] = [(None, start)]
            madeChange = True
            break
        
        elif thisStart is None:
            if start <= thisStop:
                v[:] = []
                madeChange = True
                break
            else:
                i += 1
        
        elif thisStop is None:
            if start <= thisStart:
                del v[i]
            else:
                v[i] = (thisStart, start)
            
            madeChange = True
            break
        
        elif start >= thisStop:
            i += 1
        
        else:
            if start > thisStart:
                v[i] = (thisStart, start)
                del v[i+1:]
            else:
                del v[i:]
            
            madeChange = True
            break
    
    return madeChange

def _removePairFromPhaseList_O_C(stop, v):
    """
    Removes the open-left range with the specified stop from v. This function
    may leave v completely empty.
    
    Returns True if any changes were made to v, False otherwise.
    
    >>> v = [(None, None)]
    >>> madeChange = _removePairFromPhaseList_O_C(20, v)
    >>> print(madeChange, v)
    True [(20, None)]
    
    >>> v = [(None, 10)]
    >>> madeChange = _removePairFromPhaseList_O_C(4, v)
    >>> print(madeChange, v)
    True [(4, 10)]
    >>> v = [(None, 10)]
    >>> madeChange = _removePairFromPhaseList_O_C(10, v)
    >>> print(madeChange, v)
    True []
    >>> v = [(None, 10), (20, 50)]
    >>> madeChange = _removePairFromPhaseList_O_C(30, v)
    >>> print(madeChange, v)
    True [(30, 50)]
    
    >>> v = [(40, None)]
    >>> madeChange = _removePairFromPhaseList_O_C(10, v)
    >>> print(madeChange, v)
    False [(40, None)]
    >>> madeChange = _removePairFromPhaseList_O_C(90, v)
    >>> print(madeChange, v)
    True [(90, None)]
    >>> v = [(None, 20), (30, 50), (90, None)]
    >>> madeChange = _removePairFromPhaseList_O_C(200, v)
    >>> print(madeChange, v)
    True [(200, None)]
    
    >>> v = [(40, 80)]
    >>> madeChange = _removePairFromPhaseList_O_C(30, v)
    >>> print(madeChange, v)
    False [(40, 80)]
    >>> madeChange = _removePairFromPhaseList_O_C(60, v)
    >>> print(madeChange, v)
    True [(60, 80)]
    >>> madeChange = _removePairFromPhaseList_O_C(100, v)
    >>> print(madeChange, v)
    True []
    """
    
    madeChange = False
    
    while v:
        thisStart, thisStop = v[0]
        
        if thisStart is None and thisStop is None:
            v[:] = [(stop, None)]
            madeChange = True
            break
        
        elif thisStart is None:
            madeChange = True
            
            if stop < thisStop:
                v[0] = (stop, thisStop)
                break
            
            else:
                del v[0]
                
                if stop == thisStop:
                    break
        
        elif thisStop is None:
            if stop > thisStart:
                v[0] = (stop, None)
                madeChange = True
            
            break
        
        elif thisStop <= stop:
            del v[0]
            madeChange = True
        
        elif thisStart < stop:
            v[0] = (stop, thisStop)
            madeChange = True
            break
        
        else:
            break
    
    return madeChange

def _tupleFunc_noSkip(*args):
    return (args[0], args[1], args[3])

def _tupleFunc_simple(*args):
    return args

def _tuplesWithScaledSkip(t, newSkip):
    """
    Given a tuple (start, stop, oldSkip, phase) and a newSkip, which must
    be a multiple of oldSkip, returns a list of (newStart, newStop, newSkip,
    newPhase) tuples completely spanning the original data.
    
    >>> _tuplesWithScaledSkip((None, None, 2, 1), 6)
    [(None, None, 6, 1), (None, None, 6, 3), (None, None, 6, 5)]
    >>> _tuplesWithScaledSkip((15, None, 2, 1), 6)
    [(15, None, 6, 3), (17, None, 6, 5), (19, None, 6, 1)]
    >>> _tuplesWithScaledSkip((None, 15, 2, 1), 6)
    [(None, 19, 6, 1), (None, 17, 6, 5), (None, 15, 6, 3)]
    >>> _tuplesWithScaledSkip((1, 11, 2, 1), 6)
    [(1, 13, 6, 1), (3, 15, 6, 3), (5, 11, 6, 5)]
    >>> _tuplesWithScaledSkip((4, 6, 2, 0), 6)
    [(4, 10, 6, 4)]
    """
    
    start, stop, skip, phase = t
    assert newSkip % skip == 0
    v = []
    count = newSkip // skip
    
    if count == 1:
        v.append(t)
    
    elif start is None and stop is None:
        for i in range(count):
            v.append((None, None, newSkip, phase + i * skip))
    
    elif start is None:
        lastValue = stop - skip
        
        for i in range(count):
            n = newSkip + lastValue - i * skip
            v.append((None, n, newSkip, n % newSkip))
    
    elif stop is None:
        firstValue = start
        
        for i in range(count):
            n = firstValue + i * skip
            v.append((n, None, newSkip, n % newSkip))
    
    elif newSkip > max(abs(start), abs(stop - skip)):
        v = [(i, i + newSkip, newSkip, i % newSkip) for i in range(start, stop, skip)]
    
    else:
        bias = stop + newSkip - skip
        
        for i in range(count):
            firstValue = start + i * skip
            n = (bias - firstValue) // newSkip
            newStop = firstValue + n * newSkip
            
            if newStop > firstValue:
                v.append((firstValue, newStop, newSkip, firstValue % newSkip))
    
    return v
    
# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class NewColl(object):
    """
    NewColls are groups of (start, stop) pairs with a fixed skip over the
    entire collection. This differs from old-style Collections which allow
    different skips internally. Imposing the same skip greatly simplifies the
    logic for NewColls.
    """
    
    #
    # Initialization and class methods
    #
    
    def __init__(self, skip=1):
        """
        Initializes an empty NewColl. If you have a source of pairs or
        old-style Triples, use one of the classmethods instead.
        
        >>> NewColl()
        1, {}
        >>> NewColl(4)
        4, {}
        """
        
        self.skip = skip
        self.phaseDict = {}
        self._cachedLen = -1
    
    @classmethod
    def frompairs(cls, iterable, skip=1):
        """
        Returns a new NewColl with the specified skip. It is initialized by
        (start, stop) or (start, stop, phase) tuples provided by the specified
        iterator, all of which must share the same specified skip.

        Note that the (start, stop, phase) form is really only required if
        start and stop are both None; the phase is computed in other cases.
        
        >>> NewColl.frompairs([(1, 11), (20, None)], 2)
        2, {0: [(20, None)], 1: [(1, 11)]}
        >>> NewColl.frompairs([(None, None, 4), (None, 17, 2)], 5)
        5, {2: [(None, 17)], 4: [(None, None)]}
        """
        
        r = cls(skip)
        
        for t in iterable:
            r.addPair(*t)  # mostly 2-element; dbl-opens get phase as third
        
        return r
    
    @classmethod
    def frompairswithskip(cls, seq):
        """
        Returns a new NewColl initialized by (start, stop, skip, phase) tuples
        from the specified sequence. It is OK if these tuples have different
        skips; the least common multiple of all of them is computed and is used
        as the skip for the NewColl.
        
        Note that seq must be a sequence and not just an iterable, because all
        of the skip values in it need to be analyzed for lcm computation before
        they are then looped over.
        
        >>> NewColl.frompairswithskip([(1, 11, 2, 1), (14, None, 3, 2)])
        6, {1: [(1, 13)], 2: [(14, None)], 3: [(3, 15)], 5: [(5, 11), (17, None)]}
        """
        
        newSkip = reduce(rational.lcm, (obj[2] for obj in seq))
        r = cls(newSkip)
        f = operator.itemgetter(0, 1, 3)
        
        for t in seq:
            for tNew in _tuplesWithScaledSkip(t, newSkip):
                r.addPair(*f(tNew))
        
        return r
    
    #
    # Special methods
    #
    
    def __abs__(self):
        """
        Returns a new NewColl with the absolute value of self.
        
        >>> p = NewColl.frompairs
        
        *** Open on both ends ***
        >>> abs(p([(None, None, 2)], 7))
        7, {2: [(2, None)], 5: [(5, None)]}
        >>> abs(p([(None, None, 3)], 6))
        6, {3: [(3, None)]}
        
        *** Open on the left ***
        >>> abs(p([(None, -31)], 4))
        4, {3: [(35, None)]}
        >>> abs(p([(None, 19)], 7))
        7, {2: [(2, None)], 5: [(5, 19)]}
        >>> abs(p([(None, 3)], 3))
        3, {0: [(0, None)]}
        
        *** Open on the right ***
        >>> abs(p([(1, None)], 8))
        8, {1: [(1, None)]}
        >>> abs(p([(-19, None)], 4))
        4, {1: [(1, None)], 3: [(3, 23)]}
        >>> abs(p([(-21, None)], 6))
        6, {3: [(3, None)]}
        
        *** Closed on both ends ***
        >>> abs(p([(4, 104)], 25))
        25, {4: [(4, 104)]}
        >>> abs(p([(-126, 2)], 16))
        16, {14: [(14, 142)]}
        >>> abs(p([(-126, 162)], 16))
        16, {2: [(2, 162)], 14: [(14, 142)]}
        >>> abs(p([(-26, 26)], 4))
        4, {2: [(2, 30)]}
        >>> abs(p([(-99, -79)], 5))
        5, {4: [(84, 104)]}
        """
        
        v = []
        
        for t in self.phasedPairs(True):
            start, stop, skip, phase = t
            
            if start is None and stop is None:
                v.append((phase, None, skip, phase))
                
                if phase and (skip != 2 * phase):
                    n = skip - phase
                    v.append((n, None, skip, n))
            
            elif start is None:
                lastVal = stop - skip
                
                if lastVal < 0:
                    n = -lastVal
                    v.append((n, None, skip, n % skip))
                else:
                    v.append((phase, stop, skip, phase))
                    n = skip - phase
                    v.append((n, None, skip, n % skip))
            
            elif stop is None:
                if start >= 0:
                    v.append(t)
                else:
                    v.append((phase, None, skip, phase))
                    
                    if skip != 2 * phase:
                        n = skip - phase
                        v.append((n, skip - start, skip, n % skip))
            
            elif start >= 0:
                v.append(t)
            
            elif stop < skip:
                n = skip - stop
                v.append((n, skip - start, skip, n % skip))
            
            elif skip == 2 * phase:
                v.append((phase, max(skip - start, stop), skip, phase))
            
            else:
                n = skip - phase
                v.append((n, skip - start, skip, n % skip))
                v.append((phase, stop, skip, phase))
        
        return self.frompairswithskip(v)
    
    def __add__(self, other):
        """
        Returns a new NewColl with the sum of the two specified NewColls. Note
        this is the mathematical sum, and is distinct from the union (q.v.)
        
        >>> p = NewColl.frompairs
        >>> p([(1, 11)], 2) + p([(14, 28)], 2)
        2, {1: [(15, 37)]}
        >>> p([(1, 11)], 2) + p([(None, None, 1)], 2)
        2, {0: [(None, None)]}
        """
        
        self, other = self._commonSkip(other)
        v = []
        
        for start1, stop1, skip1, phase1 in self.phasedPairs(True):
            for start2, stop2, skip2, phase2 in other.phasedPairs(True):
                newStart = (None if start1 is None or start2 is None else start1 + start2)
                newStop = (None if stop1 is None or stop2 is None else stop1 + stop2 - skip1)
                newPhase = (phase1 + phase2) % skip1
                v.append((newStart, newStop, skip1, newPhase))
        
        return self.frompairswithskip(v)
    
    def __contains__(self, value):
        """
        Returns True if value is covered by self. As a special case, if value
        is None then True is returned if there exist any open-ended pairs in
        self.
        
        >>> None in NewColl.frompairs([(1, 11)], 2)
        False
        >>> None in NewColl.frompairswithskip([(1, 11, 2, 1), (14, None, 3, 2)])
        True
        >>> 20 in NewColl.frompairswithskip([(1, 11, 2, 1), (14, None, 3, 2)])
        True
        >>> 21 in NewColl.frompairswithskip([(1, 11, 2, 1), (14, None, 3, 2)])
        False
        """
        
        self._cachedLengthCheck()
        
        if value is None:
            return self._cachedLen is None
        
        phase = value % self.skip
        return _phaseListContainsValue(self.phaseDict.get(phase, []), value)
    
    def __copy__(self):
        """
        Returns a shallow copy.
        
        >>> c = NewColl.frompairs([(1, 11)], 2)
        >>> c2 = c.__copy__()
        >>> c is c2, c.phaseDict is c2.phaseDict
        (False, True)
        """
        
        r = type(self)(self.skip)
        r.phaseDict = self.phaseDict
        r._cachedLen = self._cachedLen
        return r
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy.
        
        >>> c = NewColl.frompairs([(1, 11)], 2)
        >>> c2 = c.__deepcopy__()
        >>> c is c2, c.phaseDict is c2.phaseDict
        (False, False)
        """
        
        r = type(self)(self.skip)
        r.phaseDict = dict((phase, list(v)) for phase, v in self.phaseDict.items())
        r._cachedLen = self._cachedLen
        return r
    
    def __eq__(self, other):
        """
        Returns True if self equals other. If the skip for self differs from
        the skip for other, the two will be converted to a common skip before
        comparison.
        
        >>> NewColl.frompairs([(1, 11)], 2) == NewColl.frompairs([(1, 11)], 2)
        True
        >>> NewColl.frompairs([(1, 11)], 2) == NewColl.frompairs([(1, 11)], 5)
        False
        >>> NewColl.frompairs([(1, 6)], 5) == NewColl.frompairs([(1, 2)], 1)
        True
        >>> NewColl.frompairs([(1, 6)], 5) == 1
        True
        """
        
        self, other = self._commonSkip(other)
        
        # The following comparison relies on the fact that there is only one
        # canonical representation for a given NewColl's phaseDict (finally!)
        
        return self.phaseDict == other.phaseDict
    
    def __int__(self):
        """
        Returns an integer if self has only one value. Otherwise raises a
        ValueError.
        
        >>> int(NewColl.frompairs([(1, 21)], 20))
        1
        >>> int(NewColl.frompairs([(1, 11)], 2))
        Traceback (most recent call last):
          ...
        ValueError: Collection does not have exactly one value!
        """
        
        self._cachedLengthCheck()
        
        if self._cachedLen != 1:
            raise ValueError("Collection does not have exactly one value!")
        
        return int(list(self.phaseDict.values())[0][0][0])
    
    def __iter__(self):
        """
        Returns an iterator over values. Raises ValueError if there are any
        open-ended pairs in the NewColl.
        
        Note the values returned by this iterator are not necessarily sorted.
        
        >>> sorted(NewColl.frompairs([(1, 11)], 2))
        [1, 3, 5, 7, 9]
        >>> sorted(NewColl.frompairs([(2, 8), (1, 7), (3, 9)], 3))
        [1, 2, 3, 4, 5, 6]
        >>> sorted(NewColl.frompairs([(None, 5)], 3))
        Traceback (most recent call last):
          ...
        ValueError: Cannot iterate infinite-length collections!
        """
        
        self._cachedLengthCheck()
        
        if self._cachedLen is None:
            raise ValueError("Cannot iterate infinite-length collections!")
        
        its = []
        
        for v in self.phaseDict.values():
            for start, stop in v:
                its.append(iter(range(start, stop, self.skip)))
        
        return itertools.chain(*its)
    
    def __len__(self):
        """
        Returns the length (i.e. number of distinct values) in self. If there
        are any open-ended pairs in self, a ValueError is raised. If you wish
        to avoid this ValueError, check for None in self beforehand.
        
        >>> c = NewColl(4)
        >>> len(c)
        0
        >>> c.addPair(1, 17)
        >>> len(c)
        4
        >>> c.addPair(40, 80)
        >>> len(c)
        14
        >>> c.addPair(5, 405)  # 3 dups to existing, so we're only adding 97 new values
        >>> len(c)
        111
        >>> c.addPair(None, None, 3)
        >>> len(c)
        Traceback (most recent call last):
          ...
        ValueError: Open-ended has infinite length!
        """
        
        self._cachedLengthCheck()
        
        if self._cachedLen is None:
            raise ValueError("Open-ended has infinite length!")
            
        return self._cachedLen
    
    def __mul__(self, other):
        """
        Returns a new NewColl representing the product of the two inputs. Note
        that by the nature of NewColls, multiplication is inexact, producing a
        lower and upper limit. If a client wishes a more exact (and potentially
        much, much larger and slower) representation, the public exactMul
        method should be used.

        >>> C = NewColl.frompairs
        >>> C([(1, 11)], 2) * C([(-5, 5)], 1)
        1, {0: [(-45, 37)]}
        """
        
        if not isinstance(other, NewColl):
            return self.scaled(other)
        
        vSelfNeg, vSelfPos = self.signedPhasedPairs(True)
        vOtherNeg, vOtherPos = other.signedPhasedPairs(True)
        
        if (not (vSelfNeg or vSelfPos)) or (not (vOtherNeg or vOtherPos)):
            return type(self)(1)
        
        f = self.frompairswithskip
        selfNeg = (f(vSelfNeg) if vSelfNeg else None)
        selfPos = (f(vSelfPos) if vSelfPos else None)
        otherNeg = (f(vOtherNeg) if vOtherNeg else None)
        otherPos = (f(vOtherPos) if vOtherPos else None)
        walk = []
        
        if selfNeg is not None and otherNeg is not None:
            a, b = selfNeg.extrema()
            c, d = otherNeg.extrema()
            x = (None if b is None or d is None else b * d)
            y = (None if a is None or c is None else a * c)
            walk.append((x, y))
        
        if selfNeg is not None and otherPos is not None:
            a, b = selfNeg.extrema()
            c, d = otherPos.extrema()
            x = (None if a is None or d is None else a * d)
            y = (None if b is None or c is None else b * c)
            walk.append((x, y))
        
        if selfPos is not None and otherNeg is not None:
            a, b = selfPos.extrema()
            c, d = otherNeg.extrema()
            x = (None if b is None or c is None else b * c)
            y = (None if a is None or d is None else a * d)
            walk.append((x, y))
        
        if selfPos is not None and otherPos is not None:
            a, b = selfPos.extrema()
            c, d = otherPos.extrema()
            x = (None if a is None or c is None else a * c)
            y = (None if b is None or d is None else b * d)
            walk.append((x, y))
        
        first, last = walk[0]  # at least one is guaranteed to exist
        
        for x, y in walk[1:]:
            if first is not None:
                first = (None if x is None else min(x, first))
            
            if last is not None:
                last = (None if y is None else max(y, last))
        
        if last is not None:
            last += 1
        
        return self.frompairs([(first, last)], 1)
    
    def __ne__(self, other): return not (self == other)
    
    def __neg__(self):
        """
        Returns a new NewColl with the negation of all the values in self.
        
        >>> -NewColl.frompairs([(1, 11)], 2)
        2, {1: [(-9, 1)]}
        >>> -NewColl.frompairs([(None, -20), (-10, 25), (50, None)], 5)
        5, {0: [(None, -45), (-20, 15), (25, None)]}
        >>> -NewColl.frompairs([(None, None, 2)], 5)
        5, {3: [(None, None)]}
        """
        
        v = []
        skip = self.skip
        
        for start, stop, phase in self.phasedPairs():
            if start is None and stop is None:
                v.append((None, None, (-phase) % skip))
            elif start is None:
                v.append((skip - stop, None))
            elif stop is None:
                v.append((None, skip - start))
            else:
                v.append((skip - stop, skip - start))
        
        return self.frompairs(v, self.skip)
    
    def __repr__(self):
        """
        Returns a string representation of self.
        
        >>> NewColl.frompairs([(1, 11), (20, None)], 2)
        2, {0: [(20, None)], 1: [(1, 11)]}
        """
        
        sv = ["%d: %s" % (key, self.phaseDict[key]) for key in sorted(self.phaseDict)]
        return "%d, {%s}" % (self.skip, ', '.join(sv))
    
    def __sub__(self, other):
        """
        Returns a new NewColl with the results of self minus other.
        
        >>> p = NewColl.frompairs
        >>> p([(1, 11)], 2) - p([(1, 11)], 2)
        2, {0: [(-8, 10)]}
        >>> p([(1, 11)], 2) - p([(None, 5)], 6)
        6, {0: [(6, None)], 2: [(2, None)], 4: [(4, None)]}
        """
        
        self, other = self._commonSkip(other)
        return self + (-other)
    
    #
    # Private methods
    #
    
    def _cachedLengthCheck(self):
        """
        Makes sure self._cachedLen is up-to-date.
        
        >>> c = NewColl.frompairs([(1, 11)], 2)
        >>> c._cachedLen
        -1
        >>> c._cachedLengthCheck()
        >>> c._cachedLen
        5
        """
        
        if self._cachedLen == -1:
            n = 0
            
            for v in self.phaseDict.values():
                for start, stop in v:
                    if start is None or stop is None:
                        self._cachedLen = None
                        return
                    
                    n += stop - start  # no overlaps within phaseDict, so safe
            
            self._cachedLen = n // self.skip  # save division for last
    
    def _commonSkip(self, other):
        """
        Returns (self, other) if their skip values are the same. Otherwise,
        returns a pair of NewColls matching self and other but with the same
        skip (this will be the lowest common multple).
        
        >>> c2_1 = NewColl.frompairs([(1, 11)], 2)
        >>> c2_2 = NewColl.frompairs([(3, 19)], 2)
        >>> c2_1._commonSkip(c2_2)
        (2, {1: [(1, 11)]}, 2, {1: [(3, 19)]})
        >>> c6 = NewColl.frompairs([(3, 27)], 6)
        >>> c2_1._commonSkip(c6)
        (6, {1: [(1, 13)], 3: [(3, 15)], 5: [(5, 11)]}, 6, {3: [(3, 27)]})
        >>> c4 = NewColl.frompairs([(1, 21)], 4)
        >>> c4._commonSkip(c6)
        (12, {1: [(1, 25)], 5: [(5, 29)], 9: [(9, 21)]}, 12, {3: [(3, 27)], 9: [(9, 33)]})
        """
        
        try:
            if self.skip != other.skip:
                lcm = rational.lcm(self.skip, other.skip)
                
                if self.skip != lcm:
                    self = self.convertedToSkip(lcm)
                
                if other.skip != lcm:
                    other = other.convertedToSkip(lcm)
        
        except AttributeError:
            other = self.frompairs([(other, other + self.skip)], self.skip)
        
        return self, other
    
    def _startStopCheck(self, start, stop, phase):
        """
        Validates inputs and returns them, raising ValueErrors where
        appropriate.
        
        >>> c = NewColl(5)
        >>> c._startStopCheck(None, None, 3)
        (None, None, 3)
        >>> c._startStopCheck(None, None, 5)
        Traceback (most recent call last):
          ...
        ValueError: Phase must be less than skip!
        >>> c._startStopCheck(None, None, None)
        Traceback (most recent call last):
          ...
        ValueError: Must specify a phase for double-open ranges!
        >>> c._startStopCheck(None, 11, None)
        (None, 11, 1)
        >>> c._startStopCheck(None, 11, 3)
        Traceback (most recent call last):
          ...
        ValueError: Phase does not match stop!
        >>> c._startStopCheck(-7, None, None)
        (-7, None, 3)
        >>> c._startStopCheck(-7, None, 2)
        Traceback (most recent call last):
          ...
        ValueError: Phase does not match start!
        >>> c._startStopCheck(1, 11, None)
        (1, 11, 1)
        >>> c._startStopCheck(1, 14, None)
        (1, 11, 1)
        >>> c._startStopCheck(1, 11, 2)
        Traceback (most recent call last):
          ...
        ValueError: Phase does not match start!
        >>> c._startStopCheck(6, 1, None)
        Traceback (most recent call last):
          ...
        ValueError: Stop must be greater than start!
        """
        
        if start is None and stop is None:
            if phase is None and self.skip == 1:
                phase = 0
            
            if phase is None:
                raise ValueError("Must specify a phase for double-open ranges!")
        
        elif start is None:
            if phase is None:
                phase = stop % self.skip
            
            if phase != stop % self.skip:
                raise ValueError("Phase does not match stop!")
        
        elif stop is None:
            if phase is None:
                phase = start % self.skip
            
            if phase != start % self.skip:
                raise ValueError("Phase does not match start!")
        
        else:
            if stop <= start:
                raise ValueError("Stop must be greater than start!")
            
            if phase is None:
                phase = start % self.skip
            
            if phase != start % self.skip:
                raise ValueError("Phase does not match start!")
            
            stop -= (stop - start) % self.skip
        
        if phase >= self.skip:
            raise ValueError("Phase must be less than skip!")
        
        return start, stop, phase
    
    #
    # Public methods
    #
    
    def addPair(self, start, stop, phase=None):
        """
        Adds a new pair to self. Note this method never changes self.skip.
        
        >>> c = NewColl(4)
        >>> c
        4, {}
        >>> c.addPair(1, 17)
        >>> c
        4, {1: [(1, 17)]}
        >>> c.addPair(40, 80)
        >>> c
        4, {0: [(40, 80)], 1: [(1, 17)]}
        >>> c.addPair(5, 405)
        >>> c
        4, {0: [(40, 80)], 1: [(1, 405)]}
        >>> c.addPair(None, None, 3)
        >>> c
        4, {0: [(40, 80)], 1: [(1, 405)], 3: [(None, None)]}
        """
        
        start, stop, phase = self._startStopCheck(start, stop, phase)
        madeChange = False
        v = self.phaseDict.setdefault(phase, [])
        
        if v != [(None, None)]:
            madeChange = _mergePairIntoPhaseList(start, stop, v)
        
        if madeChange:
            self._cachedLen = -1
    
    def convertedToSkip(self, newSkip):
        """
        Returns a new NewColl exactly matching self, but with the specified new
        skip value. A ValueError is raised if newSkip is not a multiple of
        self.skip.
        
        >>> NewColl.frompairs([(1, 11)], 2).convertedToSkip(6)
        6, {1: [(1, 13)], 3: [(3, 15)], 5: [(5, 11)]}
        >>> NewColl.frompairs([(1, 11)], 2).convertedToSkip(5)
        Traceback (most recent call last):
          ...
        ValueError: You can only convert to skips that are multiples of the existing skip!
        """
        
        if newSkip == self.skip:
            return self.__deepcopy__()
        
        if newSkip % self.skip:
            raise ValueError("You can only convert to skips that are multiples of the existing skip!")
        
        f = _tuplesWithScaledSkip
        v = self.phasedPairs(True)
        return self.frompairswithskip([t for oldTuple in v for t in f(oldTuple, newSkip)])
    
    def deletePair(self, start, stop, phase=None):
        """
        Removes any values in the specified range from self. It's OK if no
        values actually end up getting removed.
        
        >>> c = NewColl.frompairs([(None, 10), (25, 55), (90, None)], 5)
        >>> c.deletePair(-50, -25)
        >>> c
        5, {0: [(None, -50), (-25, 10), (25, 55), (90, None)]}
        >>> c.deletePair(0, 100)
        >>> c
        5, {0: [(None, -50), (-25, 0), (100, None)]}
        >>> c.deletePair(-45, -25)
        >>> c
        5, {0: [(None, -50), (-25, 0), (100, None)]}
        """
        
        start, stop, phase = self._startStopCheck(start, stop, phase)
        madeChange = False
        v = self.phaseDict.get(phase, [])
        
        if v:
            madeChange = _removePairFromPhaseList(start, stop, v)
        
        if madeChange:
            self._cachedLen = -1
            
            if not v:
                del self.phaseDict[phase]
    
    def difference(self, other):
        """
        Returns a new NewColl containing all values in self not also in other.
        
        >>> c1 = NewColl.frompairs([(1, 11)], 2)
        >>> c2 = NewColl.frompairs([(-5, 5)], 2)
        >>> c1.difference(c2)
        2, {1: [(5, 11)]}
        >>> c2.difference(c1)
        2, {1: [(-5, 1)]}
        >>> c3 = NewColl.frompairs([(3, 27)], 6)
        >>> c1.difference(c3)
        6, {1: [(1, 13)], 5: [(5, 11)]}
        >>> c3.difference(c1)
        6, {3: [(15, 27)]}
        """
        
        self, other = self._commonSkip(other)
        r = self.__deepcopy__()
        
        for t in self.intersection(other).phasedPairs():
            r.deletePair(*t)
        
        return r
    
    def exactMul(self, other):
        """
        Returns a NewColl containing the exact answer for self * other, unless
        either one is open-ended, in which case a ValueError is raised. Note
        that default multiplication (i.e. the __mul__ method) is inexact for
        NewColls, but may be significantly faster too.

        >>> C = NewColl.frompairs
        >>> C([(1, 11)], 2).exactMul(C([(-5, 5)], 1))
        1, {0: [(-45, -44), (-36, -34), (-28, -26), (-25, -24), (-21, -19), (-18, -17), (-15, -13), (-12, -11), (-10, -8), (-7, 8), (9, 11), (12, 13), (14, 16), (18, 19), (20, 22), (27, 29), (36, 37)]}
        """

        if not isinstance(other, NewColl):
            return self.scaled(other)

        self._cachedLengthCheck()
        other._cachedLengthCheck()

        if self._cachedLen is None or other._cachedLen is None:
            raise ValueError("Cannot use exactMul with open NewColls!")

        s = (i * j for i in self for j in other)
        return self.frompairs(((n, n+1) for n in s), 1)

    def extrema(self):
        """
        Returns a pair of values, representing the smallest and largest values
        actually contained in the NewColl (note this is the largest value, not
        the stop value!) Either or both of the returned values may be None if
        the NewColl is open on that end.
        
        If the NewColl is empty, the string 'no data' is returned.
        
        >>> print(NewColl.frompairs([(6, 20), (1, 11)], 2).extrema())
        (1, 18)
        >>> print(NewColl.frompairs([(6, 10), (1, None)], 2).extrema())
        (1, None)
        >>> print(NewColl.frompairs([(None, 10), (1, 11)], 2).extrema())
        (None, 9)
        >>> print(NewColl.frompairs([(None, 10), (100, None)], 2).extrema())
        (None, None)
        >>> print(NewColl(4).extrema())
        no data
        """
        
        self._cachedLengthCheck()
        vals = list(self.phaseDict.values())
        
        if vals:
            firsts = [v[0][0] for v in vals]
            stops = [v[-1][1] for v in vals]
            smallest = (None if any(x is None for x in firsts) else min(firsts))
            
            if any(x is None for x in stops):
                return (smallest, None)
            
            return (smallest, max(stops) - self.skip)
        
        return 'no data'
    
    def intersection(self, other):
        """
        Returns a new NewColl with the intersection of the two specified
        NewColls.
        
        >>> p = NewColl.frompairs
        >>> p([(1, 11)], 2).intersection(p([(3, 63)], 6))
        6, {3: [(3, 15)]}
        """
        
        return self.inverse().union(other.inverse()).inverse()
    
    def inverse(self):
        """
        Returns a new NewColl with the same skip as self but covering all
        values not covered in self.
        
        >>> NewColl.frompairs([(1, 11)], 2).inverse()
        2, {0: [(None, None)], 1: [(None, 1), (11, None)]}
        >>> NewColl.frompairs([(1, 11)], 2).inverse().inverse()
        2, {1: [(1, 11)]}
        >>> NewColl.frompairs([(None, None, 0)], 1).inverse()
        1, {}
        >>> NewColl.frompairs([(None, 20), (35, 55), (90, None)], 5).inverse()
        5, {0: [(20, 35), (55, 90)], 1: [(None, None)], 2: [(None, None)], 3: [(None, None)], 4: [(None, None)]}
        """
        
        vCumul = []
        
        for phase in range(self.skip):
            v = self.phaseDict.get(phase, [])
            
            if v:
                if len(v) == 1:
                    start, stop = v[0]
                    
                    if start is None and stop is None:
                        pass
                    elif start is None:
                        vCumul.append((stop, None))
                    elif stop is None:
                        vCumul.append((None, start))
                    else:
                        vCumul.append((None, start))
                        vCumul.append((stop, None))
                
                else:
                    for i in range(len(v) - 1):
                        vCumul.append((v[i][1], v[i+1][0]))
            
            else:
                vCumul.append((None, None, phase))
        
        return self.frompairs(vCumul, self.skip)
    
    def phasedPairs(self, includeSkip=False):
        """
        Returns a list of either (start, stop, phase) tuples (if includeSkip is
        False) or (start, stop, skip, phase) tuples (if includeSkip is True).
        
        >>> c = NewColl.frompairs([(1, 13), (3, 27), (5, 11)], 6)
        >>> c.phasedPairs()
        [(1, 13, 1), (3, 27, 3), (5, 11, 5)]
        >>> c.phasedPairs(True)
        [(1, 13, 6, 1), (3, 27, 6, 3), (5, 11, 6, 5)]
        """
        
        it = list(self.phaseDict.items())
        
        if includeSkip:
            return [(start, stop, self.skip, phase) for phase, v in it for start, stop in v]
        
        return [(start, stop, phase) for phase, v in it for start, stop in v]
    
    def scaled(self, scaleFactor):
        """
        Returns a new NewColl whose values are those in self multiplied by the
        constant scaleFactor, which must be an integer.
        
        >>> NewColl.frompairs([(1, 11)], 2).scaled(3)
        6, {3: [(3, 33)]}
        >>> NewColl.frompairs([(None, 15), (18, 22), (30, None)], 2).scaled(3)
        6, {0: [(54, 66), (90, None)], 3: [(None, 45)]}
        >>> NewColl.frompairs([(None, 15), (18, 22), (30, None)], 2).scaled(-3)
        6, {0: [(None, -84), (-60, -48)], 3: [(-39, None)]}
        >>> NewColl.frompairs([(None, 15), (18, 22), (30, None)], 2).scaled(0)
        1, {0: [(0, 1)]}
        """
        
        v = []
        
        if scaleFactor < 0:
            scale = -scaleFactor
            needToNegate = True
        else:
            scale = scaleFactor
            needToNegate = False
        
        if scale:
            for start, stop, phase in self.phasedPairs():
                newStart = (None if start is None else start * scale)
                newStop = (None if stop is None else stop * scale)
                v.append((newStart, newStop, self.skip * scale, phase * scale))
        
        else:
            v.append((0, 1, 1, 0))
        
        r = self.frompairswithskip(v)
        return (-r if needToNegate else r)
    
    def signedPhasedPairs(self, includeSkip=False):
        """
        Returns two lists of either (start, stop, phase) tuples (if includeSkip
        is False) or (start, stop, skip, phase) tuples (if includeSkip is
        True). The first returned list contains only tuples covering strictly
        negative values. The second returned list contains only zeroes and
        positives.
        
        >>> NewColl.frompairs([(1, 11)], 2).signedPhasedPairs()
        ([], [(1, 11, 1)])
        >>> NewColl.frompairs([(1, 11)], 2).signedPhasedPairs(True)
        ([], [(1, 11, 2, 1)])
        >>> NewColl.frompairs([(-100, -50)], 2).signedPhasedPairs()
        ([(-100, -50, 0)], [])
        >>> NewColl.frompairs([(-100, 50)], 2).signedPhasedPairs()
        ([(-100, 0, 0)], [(0, 50, 0)])
        >>> NewColl.frompairs([(None, -53)], 10).signedPhasedPairs()
        ([(None, -53, 7)], [])
        >>> NewColl.frompairs([(None, 6)], 10).signedPhasedPairs()
        ([(None, 6, 6)], [])
        >>> NewColl.frompairs([(None, 200)], 10).signedPhasedPairs()
        ([(None, 0, 0)], [(0, 200, 0)])
        >>> NewColl.frompairs([(200, None)], 10).signedPhasedPairs()
        ([], [(200, None, 0)])
        >>> NewColl.frompairs([(0, None)], 10).signedPhasedPairs()
        ([], [(0, None, 0)])
        >>> NewColl.frompairs([(-165, None)], 10).signedPhasedPairs()
        ([(-165, 5, 5)], [(5, None, 5)])
        >>> NewColl.frompairs([(None, None, 1)], 3).signedPhasedPairs()
        ([(None, 1, 1)], [(1, None, 1)])
        """
        
        vNeg = []
        vPos = []
        skip = self.skip
        f = (_tupleFunc_simple if includeSkip else _tupleFunc_noSkip)
        
        for phase, v in list(self.phaseDict.items()):
            for start, stop in v:
                if start is None and stop is None:
                    vNeg.append(f(None, phase, skip, phase))
                    vPos.append(f(phase, None, skip, phase))
                
                elif start is None:
                    if stop >= skip:
                        vNeg.append(f(None, phase, skip, phase))
                        vPos.append(f(phase, stop, skip, phase))
                    else:
                        vNeg.append(f(None, stop, skip, phase))
                
                elif stop is None:
                    if start < 0:
                        vNeg.append(f(start, phase, skip, phase))
                        vPos.append(f(phase, None, skip, phase))
                    else:
                        vPos.append(f(start, None, skip, phase))
                
                elif start >= 0:
                    vPos.append(f(start, stop, skip, phase))
                
                elif stop < skip:
                    vNeg.append(f(start, stop, skip, phase))
                
                else:
                    vNeg.append(f(start, phase, skip, phase))
                    vPos.append(f(phase, stop, skip, phase))
        
        return vNeg, vPos
    
    def union(self, other):
        """
        Returns a new NewColl with the union of the two specified NewColls.
        
        >>> NewColl.frompairs([(1, 11)], 2).union(NewColl.frompairs([(9, 41)], 2))
        2, {1: [(1, 41)]}
        >>> NewColl.frompairs([(1, 11)], 2).union(NewColl.frompairs([(3, 27)], 6))
        6, {1: [(1, 13)], 3: [(3, 27)], 5: [(5, 11)]}
        >>> NewColl.frompairs([(None, 20)], 10).union(NewColl.frompairs([(0, None)], 10))
        10, {0: [(None, None)]}
        """
        
        self, other = self._commonSkip(other)
        r = self.__deepcopy__()
        
        for start, stop, phase in other.phasedPairs():
            r.addPair(start, stop, phase)
        
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

