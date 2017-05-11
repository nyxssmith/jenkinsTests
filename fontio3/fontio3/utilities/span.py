#
# span.py -- Support for manipulating ranges of integer indices
#
# Copyright © 2004-2007, 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for objects which manipulate ranges of integer indices.
"""

# System imports
import re

# -----------------------------------------------------------------------------

#
# Classes
#

class Span(object):
    """
    Objects for manipulating ranges of integer indices; most commonly used for
    managing glyph index collections.
    """

    #
    # Constants
    #

    patGroup = re.compile(r"([0-9]+|\*)\s*-\s*([0-9]+|\*)")
    patSingle = re.compile(r"([0-9]+)")
    patHexGroup = re.compile(r"([0-9A-Fa-f]+|\*)\s*-\s*([0-9A-Fa-f]+|\*)")
    patHexSingle = re.compile(r"([0-9A-Fa-f]+)")
    
    #
    # Initialization and class methods
    #

    def __init__(self, iterable=None):
        """
        Creates an empty Span. If an iterable is specified its values will be
        used to initially fill the Span.

        Conceptually a span is a collection of ranges (first, last) of numbers.
        Note that unlike Python ranges the last is included in the span. Thus,
        a span of (4, 9) would have to be represented by a Python range(4, 10).

        Spans are permitted to be "open-ended" at one or both ends. This means
        the span includes all numbers above or below a specified value. This
        quality is represented in a returned range by the use of None. Thus, a
        span of (None, 6) indicates the span includes all numbers less than or
        equal to 6.
        
        >>> Span([1, 2, 3, 5]).asPairsList()
        [(1, 3), (5, 5)]
        >>> Span().asPairsList()
        []
        >>> Span([1, 2, 2, 2, 2, 2]).asPairsList()
        [(1, 2)]
        >>> Span(x*x for x in (3, 5, 7)).asPairsList()
        [(9, 9), (25, 25), (49, 49)]
        """
        
        if iterable is not None:
            self.spans = [(x, x) for x in iterable]
            self._canonicalize()
        
        else:
            self.spans = []
        
        self.stringOutputInHex = False
    
    @classmethod
    def fromstringhex(cls, s):
        r = cls()
        r.addFromStringHex(s)
        return r
    
    #
    # Special methods
    #
    
    def __eq__(self, other):
        """
        Compare a Span for equality with either another Span (or BoundSpan), or
        a list.
        
        >>> s = Span([1, 2, 3, 5])
        >>> s == s
        True
        >>> s == [(1, 3), (5, 5)]
        True
        >>> s == [1, 2, 3, 5]
        True
        >>> s == [1, 2, 5]
        False
        """
        
        if isinstance(other, Span):
            return self.spans == other.spans
        elif isinstance(other, list):
            if all(isinstance(x, tuple) and len(x) == 2 for x in other):
                return self.spans == other
            else:
                return self.spans == Span(other).spans
        else:
            return False
    
    def __getitem__(self, n):
        """
        Returns the nth range in the Span. This is a pair (first, last) of
        numbers.
        
        >>> s = Span([1, 2, 3, 5])
        >>> s[0]
        (1, 3)
        >>> s[-1]
        (5, 5)
        """
        
        return self.spans[n]
    
    def __iter__(self):
        """
        Returns an iterator over the ranges in the Span. Each call yields a
        (first, last) pair.
        
        >>> s = Span([1, 2, 3, 5])
        >>> list(s)
        [(1, 3), (5, 5)]
        """
        
        return iter(self.spans)
    
    def __len__(self):
        """
        Returns the number of ranges in the Span.
        
        >>> s = Span([1, 2, 3, 5])
        >>> len(s)
        2
        """
        
        return len(self.spans)
    
    def __ne__(self, other): return not (self == other)
    
    def __str__(self):
        """
        Returns a compact string representation of the Span. This uses a dash
        between the first and last values of each range. Each range is
        separated by a comma. Open-ended ranges are denoted using an asterisk.
        
        If the entire Span is open, a single asterisk (only) is returned.
        
        If the Span contains no members, the string "(empty)" is returned.
        
        The numeric values are output in decimal by default unless
        self.stringOutputInHex is set to True, in which case they're output in
        hex.
        
        >>> s = Span([1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.addRange(25, 30)
        >>> str(s)
        '1-3, 5, 25-30'
        >>> s.invert()
        >>> str(s)
        '*-0, 4, 6-24, 31-*'
        >>> s.stringOutputInHex = True
        >>> str(s)
        '*-0x0, 0x4, 0x6-0x18, 0x1F-*'
        >>> str(Span())
        '(empty)'
        """
        
        if self.stringOutputInHex:
            fmts = ["*-0x%X", "0x%X-*", "0x%X", "0x%X-0x%X"]
        else:
            fmts = ["*-%d", "%d-*", "%d", "%d-%d"]
        
        if self.spans:
            sv = []
            
            for start, end in self.spans:
                if (start is None) and (end is None):
                    sv.append("*")
                elif start is None:
                    sv.append(fmts[0] % end)
                elif end is None:
                    sv.append(fmts[1] % start)
                elif start == end:
                    sv.append(fmts[2] % start)
                else:
                    sv.append(fmts[3] % (start, end))
            
            return ', '.join(sv)
        
        else:
            return "(empty)"

    #
    # Private methods
    #
    
    def _canonicalize(self):
        """
        Makes self.spans into canonical form, where there is at most one
        open-ended beginning span, at most one open-ended ending span, and
        sorted internal spans that don't intersect any open-ended spans.

        This code has now been optimized so it doesn't try to create separate
        entries for each value in each range. That means it can be used to
        canonicalize quite enormous Spans.
        """
        
        if len(self.spans) > 1:
            if (None, None) in self.spans:
                self.spans[:] = [(None, None)]
            
            else:
                leftFence = rightFence = None
                pool = []
                
                for low, high in self.spans:
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
                    
                    # consolidate overlapping or adjacent entries
                    index = 0
                    
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
                    if pool and leftFence is not None:
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
                if \
                  leftFence is not None and \
                  rightFence is not None and \
                  leftFence >= rightFence - 1:
                    self.spans[:] = [(None, None)]
                
                else:
                    self.spans[:] = []
                    
                    if leftFence is not None:
                        self.spans.append((None, leftFence))
                    
                    self.spans.extend(pool)
                    
                    if rightFence is not None:
                        self.spans.append((rightFence, None))
    
    #
    # Public methods
    #
    
    def addFromString(self, s):
        """
        Parses the string, which will contain single decimal numbers or ranges
        (which are two decimal numbers with an intervening hyphen) and adds the
        results to the span. The caller may use the asterisk to denote an
        open-ended range. To denote a completely inclusive Span, the caller
        should specify the string "*-*" (note this is slightly different from
        what __str__ returns. Such is life.)
        
        >>> s = Span([1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.addFromString("8-11, 15-29, 200-*")
        >>> str(s)
        '1-3, 5, 8-11, 15-29, 200-*'
        >>> s.addFromString("0-19")
        >>> str(s)
        '0-29, 200-*'
        """
        
        v = []
        makeAll = False
        
        for start, end in self.patGroup.findall(s):
            if (start == '*') and (end == '*'):
                makeAll = True
                break
            
            if start == '*':
                start = None
            else:
                start = int(start)
            
            if end == '*':
                end = None
            else:
                end = int(end)
            
            v.append((start, end))
        
        for start in self.patSingle.findall(s):
            start = int(start)
            v.append((start, start))
        
        if makeAll:
            self.spans = [(None, None)]
        
        else:
            self.spans.extend(v)
            self._canonicalize()
    
    def addFromStringHex(self, s):
        """
        Parses the string, which will contain single hexidecimal numbers or
        ranges (which are two hexidecimal numbers with an intervening hyphen)
        and adds the results to the span. The caller may use the asterisk to
        denote an open-ended range. To denote a completely inclusive Span, the
        caller should specify the string "*-*" (note this is slightly different
        from what __str__ returns. Such is life.)

        Case does not matter for the digits A-F. Any leading "0x" or "0X" or
        "$" or trailing 'h' or 'H' will be stripped.
        
        >>> s = Span()
        >>> str(s)
        '(empty)'
        >>> s.addFromStringHex("4E00-4fff 6000-6200")
        >>> s.stringOutputInHex = True
        >>> str(s)
        '0x4E00-0x4FFF, 0x6000-0x6200'
        >>> s.addFromStringHex("4f50H - *")
        >>> str(s) 
        '0x4E00-*'
        >>> s.addFromStringHex("0x2000    - $2100")
        >>> str(s)
        '0x2000-0x2100, 0x4E00-*'
        """
        
        s = s.replace('0x', '').replace('0X', '').replace('$', '').replace('H', '').replace('h', '')
        v = []
        makeAll = False
        
        for start, end in self.patHexGroup.findall(s):
            if (start == '*') and (end == '*'):
                makeAll = True
                break
            
            if start == '*':
                start = None
            else:
                start = int(start, 16)
            
            if end == '*':
                end = None
            else:
                end = int(end, 16)
            
            v.append((start, end))
        
        for start in self.patHexSingle.findall(s):
            start = int(start, 16)
            v.append((start, start))
        
        if makeAll:
            self.spans = [(None, None)]
        
        else:
            self.spans.extend(v)
            self._canonicalize()
    
    def addList(self, iterable):
        """
        Adds all the numbers in the specified iterable to the Span. Note that
        the name of this method is for historical reasons; any iterable,
        including lists, may be specified.
        
        >>> s = Span([1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.addList([10, 11])
        >>> str(s)
        '1-3, 5, 10-11'
        >>> s.addList(x * x for x in (20, 22))
        >>> str(s)
        '1-3, 5, 10-11, 400, 484'
        """
        
        self.spans.extend([(x, x) for x in iterable])
        self._canonicalize()

    def addRange(self, newStart, newEnd):
        """
        Adds the indices from newStart through newEnd to the Span. A value of
        None indicates an open side on that end.
        
        >>> s = Span()
        >>> s.addRange(40, 50)
        >>> str(s)
        '40-50'
        >>> s.addRange(None, 5)
        >>> str(s)
        '*-5, 40-50'
        >>> s.addRange(100, None)
        >>> str(s)
        '*-5, 40-50, 100-*'
        >>> s.addRange(None, None)
        >>> str(s)
        '*'
        """
        
        if newStart is not None and newEnd is not None and newStart > newEnd:
            newStart, newEnd = newEnd, newStart
        
        self.spans.append((newStart, newEnd))
        self._canonicalize()
    
    def addRanges(self, iterable):
        """
        Adds all the pairs in the specified iterable to the span.
        
        >>> s = Span()
        >>> s.addRanges((n, n+10) for n in (200, 350, 650))
        >>> str(s)
        '200-210, 350-360, 650-660'
        >>> s.addRanges([(None, 20), (150, None)])
        >>> str(s)
        '*-20, 150-*'
        """
        
        clean = []
        
        for start, end in iterable:
            if start is not None and end is not None and start > end:
                start, end = end, start
            
            clean.append((start, end))
        
        self.spans.extend(clean)
        self._canonicalize()
    
    def asDict(self):
        """
        Returns a tuple of three items: the end of the open-ended low range (or
        None); the start of the open-ended high range (or None); and a
        dictionary whose keys are the individual integers from the union of all
        non-open spans and whose values are unimportant (set to None).
        
        >>> s = Span()
        >>> s.asDict()
        (None, None, {})
        >>> s.addRange(10, 11)
        >>> s.asDict()
        (None, None, {10: None, 11: None})
        >>> s.addRange(None, 3)
        >>> s.asDict()
        (3, None, {10: None, 11: None})
        >>> s.addRange(50, None)
        >>> s.asDict()
        (3, 50, {10: None, 11: None})
        """
        
        startLowOpen, startHighOpen, v = self.asList()
        return startLowOpen, startHighOpen, dict.fromkeys(v)
    
    def asList(self):
        """
        Returns a tuple of three items: the end of the open-ended low range (or
        None); the start of the open-ended high range (or None); and the span
        as a sorted list of individual integers.
        
        >>> s = Span()
        >>> s.asList()
        (None, None, [])
        >>> s.addRange(10, 11)
        >>> s.asList()
        (None, None, [10, 11])
        >>> s.addRange(None, 3)
        >>> s.asList()
        (3, None, [10, 11])
        >>> s.addRange(50, None)
        >>> s.asList()
        (3, 50, [10, 11])
        """
        
        if self.isFull():
            return 0, 1, []
        
        else:
            v = []
            startLowOpen = startHighOpen = None
            
            for low, high in self.spans:
                if low is not None and high is not None:
                    v.extend(list(range(low, high + 1)))
                elif low is None:
                    startLowOpen = high
                else:
                    startHighOpen = low
            
            v.sort()
            return startLowOpen, startHighOpen, v
    
    def asPairsList(self):
        """
        Returns a list of (first, last) pairs.
        
        >>> Span(x * x for x in range(4)).asPairsList()
        [(0, 1), (4, 4), (9, 9)]
        """
        
        return list(self.spans)
        
    def asSet(self):
        """
        Returns a tuple of three items: the start of the open-ended low range
        (or None); the start of the open-ended high range (or None); and a set
        whose values are the individual integers from the union of all non-open
        spans.
        
        >>> s = Span()
        >>> s.asSet()
        (None, None, set())
        >>> s.addRange(10, 11)
        >>> s.asSet()
        (None, None, {10, 11})
        >>> s.addRange(None, 3)
        >>> s.asSet()
        (3, None, {10, 11})
        >>> s.addRange(50, None)
        >>> s.asSet()
        (3, 50, {10, 11})
        """
        
        startLowOpen, startHighOpen, v = self.asList()
        return startLowOpen, startHighOpen, set(v)
    
    def clear(self):
        """
        Removes all ranges from the Span.
        
        >>> s = Span([1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.clear()
        >>> str(s)
        '(empty)'
        """
        
        self.spans = []
    
    def clipRange(self, firstValid, lastValid):
        """
        Removes any indices outside the inclusive range firstValid..lastValid.
        A value of None indicates open-ended clipping (i.e. no clipping on that
        end).
        
        >>> s = Span()
        >>> s.addRange(10, 20)
        >>> s.addRange(50, 100)
        >>> str(s)
        '10-20, 50-100'
        >>> s.clipRange(15, 80)
        >>> str(s)
        '15-20, 50-80'
        >>> s.clipRange(60, None)
        >>> str(s)
        '60-80'
        """
        
        clipSpan = Span()
        clipSpan.addRange(firstValid, lastValid)
        self.intersectSpan(clipSpan)
    
    def contains(self, n):
        """
        Returns True if n is present in the Span.
        
        >>> s = Span([1, 2, 3, 5, 7, 8, 9])
        >>> str(s)
        '1-3, 5, 7-9'
        >>> s.contains(3)
        True
        >>> s.contains(4)
        False
        """
        
        if not self.spans:
            return False
        
        first, lastPlusOne = 0, len(self.spans)
        
        if self.spans[0] == (None, None):
            return True
        
        if self.spans[0][0] is None:
            if n <= self.spans[0][1]:
                return True
            else:
                first += 1
        
        if self.spans[-1][1] is None:
            if n >= self.spans[-1][0]:
                return True
            else:
                lastPlusOne -= 1
        
        for rangeFirst, rangeLast in self.spans[first:lastPlusOne]:
            if rangeFirst <= n <= rangeLast:
                return True
        
        return False
    
    def copy(self, **kwArgs):
        """
        Returns a copy.
        
        >>> s = Span([3, 4])
        >>> id(s) != id(s.copy())
        True
        >>> s == s.copy()
        True
        """
        
        theCopy = Span()
        theCopy.spans = list(self.spans)
        return theCopy
    
    def count(self):
        """
        Returns a count of the total number of individual elements (not
        ranges!) in the span, or None if either end is open.

        For a count of ranges use len().
        
        >>> s = Span()
        >>> s.count()
        0
        >>> s.addRange(20, 30)
        >>> s.count()
        11
        >>> s.addRange(50, None)
        >>> str(s.count())
        'None'
        """
        
        if self.spans:
            if (self.spans[0][0] is None) or (self.spans[-1][1] is None):
                return None
        
        n = 0
        
        for start, end in self.spans:
            n += (end - start + 1)
        
        return n
    
    def deleteRange(self, delStart, delEnd):
        """
        Deletes the indices from delStart through delEnd from the Span.
        
        >>> s = Span([1, 2, 3, 5, 6, 7, 8])
        >>> str(s)
        '1-3, 5-8'
        >>> s.deleteRange(3, 6)
        >>> str(s)
        '1-2, 7-8'
        >>> s.deleteRange(2, None)
        >>> str(s)
        '1'
        """
        
        # deleting a range is just intersecting with the inverse of that range
        delSpan = Span()
        delSpan.addRange(delStart, delEnd)
        delSpan.invert()
        self.intersectSpan(delSpan)
    
    def deleteSpan(self, other):
        """
        Deletes the values in other from self.
        
        >>> s = Span([1, 2, 3, 5, 6, 7, 8, 40, 50])
        >>> print(s)
        1-3, 5-8, 40, 50
        >>> s2 = Span([2, 5, 6, 10, 11, 39, 40, 41])
        >>> print(s2)
        2, 5-6, 10-11, 39-41
        >>> s.deleteSpan(s2)
        >>> print(s)
        1, 3, 7-8, 50
        """
        
        otherCopy = other.copy()
        otherCopy.invert()
        self.intersectSpan(otherCopy)
    
    def fullIterator(self):
        """
        Returns an generator which returns individual values from self. Raises
        ValueError if either end is open.
        
        >>> s = Span([1, 2, 3, 5])
        >>> list(s)
        [(1, 3), (5, 5)]
        >>> list(s.fullIterator())
        [1, 2, 3, 5]
        >>> s.addRange(20, None)
        >>> list(s)
        [(1, 3), (5, 5), (20, None)]
        >>> list(s.fullIterator())
        Traceback (most recent call last):
          ...
        ValueError
        """
        
        if len(self.spans):
            if (self.spans[0][0] is None) or (self.spans[-1][1] is None):
                raise ValueError
        
        for start, end in self.spans:
            for x in range(start, end + 1):
                yield x
    
    def index(self, n):
        """
        Returns the (start, end) pair containing n, if present. Otherwise
        returns None.
        
        >>> s = Span([1, 2, 3, 5, 6, 9, 10])
        >>> str(s)
        '1-3, 5-6, 9-10'
        >>> s.index(3)
        (1, 3)
        >>> s.index(9)
        (9, 10)
        >>> str(s.index(11))
        'None'
        """
        
        if not self.spans:
            return None
        
        first, lastPlusOne = 0, len(self.spans)
        
        if self.spans[0] == (None, None):
            return self.spans[0]
        
        if self.spans[0][0] is None:
            if n <= self.spans[0][1]:
                return self.spans[0]
            else:
                first += 1
        
        if self.spans[-1][1] is None:
            if n >= self.spans[-1][0]:
                return self.spans[-1]
            else:
                lastPlusOne -= 1
        
        for rangeFirst, rangeLast in self.spans[first:lastPlusOne]:
            if rangeFirst <= n <= rangeLast:
                return (rangeFirst, rangeLast)
        
        return None
    
    intersectRange = clipRange
    
    def intersectSpan(self, other):
        """
        Modifies self by interesecting with other.
        
        >>> s1 = Span([1, 2, 3, 5, 6, 7, 8])
        >>> str(s1)
        '1-3, 5-8'
        >>> s2 = Span([4, 6, 8, 10])
        >>> str(s2)
        '4, 6, 8, 10'
        >>> s1.intersectSpan(s2)
        >>> str(s1)
        '6, 8'
        >>> s1 = Span() 
        >>> s1.addRanges([(None, 40), (50, 70), (100, None)])
        >>> s2 = Span()
        >>> s2.addRanges([(30, 60), (90, None)])
        >>> str(s1)
        '*-40, 50-70, 100-*'
        >>> str(s2)
        '30-60, 90-*'
        >>> s1.intersectSpan(s2)
        >>> str(s1)
        '30-40, 50-60, 100-*'
        """
        
        if other.isFull():
            pass
        elif self.isFull():
            self.spans[:] = other.spans
        else:
            s2 = other.copy()
            self.invert()
            s2.invert()
            self.unionSpan(s2)
            self.invert()
    
    def invert(self):
        """
        Inverts the span, so what was excluded is now included and vice versa.
        This works correctly for open-ended Span as well as closed Spans.
        
        >>> s = Span([1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.invert()
        >>> str(s)
        '*-0, 4, 6-*'
        >>> s = Span()
        >>> s.addRanges([(None, 40), (50, 60), (70, None)])
        >>> str(s)
        '*-40, 50-60, 70-*'
        >>> s.invert()
        >>> str(s)
        '41-49, 61-69'
        """
        
        if self.spans == [(None, None)]:
            self.spans[:] = []
        elif not self.spans:
            self.spans[:] = [(None, None)]
        else:
            v = []
            index = 0
            
            while index < len(self.spans) - 1:
                high1 = self.spans[index][1]
                low2 = self.spans[index + 1][0]
                v.append((high1 + 1, low2 - 1))
                index += 1
            
            if self.spans[0][0] is not None:
                v.insert(0, (None, self.spans[0][0] - 1))
            
            if self.spans[-1][1] is not None:
                v.append((self.spans[-1][1] + 1, None))
            
            self.spans[:] = v
        
        # no canonicalization call needed!
    
    def isFull(self):
        """
        Returns True if the span is all-inclusive.
        
        >>> s = Span()
        >>> s.isFull()
        False
        >>> s.invert()
        >>> s.isFull()
        True
        """
        
        return self.spans == [(None, None)]
    
    def unionSpan(self, other):
        """
        Modifies self by unioning with other.
        
        >>> s1 = Span([1, 2, 3, 5, 6, 7, 8])
        >>> str(s1)
        '1-3, 5-8'
        >>> s2 = Span([4, 6, 8, 10])
        >>> str(s2)
        '4, 6, 8, 10'
        >>> s1.unionSpan(s2)
        >>> str(s1)
        '1-8, 10'
        >>> s1 = Span() 
        >>> s1.addRanges([(None, 40), (50, 70), (100, None)])
        >>> s2 = Span()
        >>> s2.addRanges([(30, 60), (90, None)])
        >>> str(s1)
        '*-40, 50-70, 100-*'
        >>> str(s2)
        '30-60, 90-*'
        >>> s1.unionSpan(s2)
        >>> str(s1)
        '*-70, 90-*'
        """
        
        self.spans.extend(other.spans)
        self._canonicalize()

# -----------------------------------------------------------------------------

class SpanFromPairs(Span):
    """
    SpanFromPairs objects are just Spans which get initialized by a sequence of
    (first, last) values, instead of individual values as is the case with Span
    objects.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, pairsSeq):
        """
        Initializes the object with the pairs in the specified sequence. It's
        OK if there are overlaps or abutments, since we explicitly perform a
        canonicalization.
        
        >>> str(SpanFromPairs([(None, 40), (50, 60), (70, None)]))
        '*-40, 50-60, 70-*'
        """
        
        super(SpanFromPairs, self).__init__()
        self.spans = list(pairsSeq)
        self._canonicalize()

# -----------------------------------------------------------------------------

class BoundSpan(Span):
    """
    Like Span, but with explicit upper and lower bounds. Any attempt to add
    content to the BoundSpan will automatically be clipped to the specified
    limits. This means BoundSpans may never be open-ended.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, low, high, iterable=None):
        """
        Initializes the BoundSpan with the specified low and high values.
        
        >>> s = BoundSpan(3, 99, [2, 3, 5, 6, 7, 99, 100, 101])
        >>> str(s)
        '3, 5-7, 99'
        """
        
        super(BoundSpan, self).__init__(iterable)
        self.low = low
        self.high = high
        self._clipCheck()       # the iterable might've had bad values
    
    #
    # Private methods
    #
    
    def _clipCheck(self):
        """
        Because of recursion problems it's easier to have all public methods of
        BoundSpan call this after they call the superclass methods.
        """
        
        s = Span()
        s.spans = list(self.spans)
        s.clipRange(self.low, self.high)
        self.spans[:] = s.spans
    
    #
    # Public methods
    #
    
    def addFromString(self, s):
        """
        Does superclass addFromString and then clips to the bounds.
        
        >>> s = BoundSpan(0, 25, [1, 2, 3, 5])
        >>> str(s)
        '1-3, 5'
        >>> s.addFromString("8-11, 15-29, 200-*")
        >>> str(s)
        '1-3, 5, 8-11, 15-25'
        >>> s.addFromString("0-19")
        >>> str(s)
        '0-25'
        """
        
        super(BoundSpan, self).addFromString(s)
        self._clipCheck()
    
    def addFromStringHex(self, s):
        """
        Does superclass addFromStringHex and then clips to the bounds.
        
        >>> s = BoundSpan(0x1000, 0x6100)
        >>> str(s)
        '(empty)'
        >>> s.addFromStringHex("4E00 - 4fff,  6000-6200")
        >>> s.stringOutputInHex = True 
        >>> str(s)
        '0x4E00-0x4FFF, 0x6000-0x6100'
        >>> s.addFromStringHex("0x0900-1100")
        >>> str(s)
        '0x1000-0x1100, 0x4E00-0x4FFF, 0x6000-0x6100'
        """
        
        super(BoundSpan, self).addFromStringHex(s)
        self._clipCheck()
    
    def addList(self, seq):
        """
        Does superclass addList and then clips to the bounds.
        
        >>> s = BoundSpan(100, 300, [122, 123])
        >>> str(s)
        '122-123'
        >>> s.addList(x * x for x in range(9, 30))
        >>> str(s)
        '100, 121-123, 144, 169, 196, 225, 256, 289'
        """
        
        super(BoundSpan, self).addList(seq)
        self._clipCheck()
    
    def addRange(self, newStart, newEnd):
        """
        Does superclass addRange and then clips to the bounds.
        
        >>> s = BoundSpan(200, 400)
        >>> str(s)     
        '(empty)'
        >>> s.addRange(100, 300)
        >>> str(s)
        '200-300'
        >>> s.addRange(320, None)
        >>> str(s)
        '200-300, 320-400'
        """
        
        super(BoundSpan, self).addRange(newStart, newEnd)
        self._clipCheck()
    
    def addRanges(self, iterable):
        """
        Does superclass addRanges and then clips to the bounds.
        
        >>> s = BoundSpan(100, 200)
        >>> s.addRanges((n, n+10) for n in range(50, 150, 25))
        >>> str(s)
        '100-110, 125-135'
        """
        
        super(BoundSpan, self).addRanges(iterable)
        self._clipCheck()

    def copy(self, **kwArgs):
        """
        Returns a copy, possibly adjusting the bounds constraints. Valid
        keyword arguments are:
        
            newLow      Override (and possibly clip) to new low value
            newHigh     Override (and possibly clip) to new high value
        
        >>> s = BoundSpan(0, 100000)
        >>> str(s)
        '(empty)'
        >>> s.addRange(100, 5000)
        >>> str(s)
        '100-5000'
        >>> s2 = s.copy(newHigh=700)
        >>> str(s2)
        '100-700'
        """
        
        newLow = kwArgs.get('newLow', self.low)
        newHigh = kwArgs.get('newHigh', self.high)
        theCopy = BoundSpan(newLow, newHigh)
        theCopy.spans = list(self.spans)
        theCopy._clipCheck()
        
        return theCopy
    
    def deleteRange(self, delStart, delEnd):
        """
        Does superclass deleteRange and then clips to the bounds.
        
        >>> s = BoundSpan(200, 400)
        >>> s.addRange(100, 300)
        >>> str(s)
        '200-300'
        >>> s.deleteRange(250, 500)
        >>> str(s)
        '200-249'
        """
        
        # deleting a range is just intersecting with the inverse of that range
        delSpan = BoundSpan(self.low, self.high)
        delSpan.addRange(delStart, delEnd)
        delSpan.invert()
        self.intersectSpan(delSpan)
        # no clip check is needed, since it can only shrink
        
    def invert(self):
        """
        Does superclass invert and then clips to the bounds.
        
        >>> s = BoundSpan(100, 400)
        >>> s.addRange(200, 300)
        >>> str(s)
        '200-300'
        >>> s.invert()
        >>> str(s)
        '100-199, 301-400'
        """
        
        super(BoundSpan, self).invert()
        self._clipCheck()
    
    def isFull(self):
        """
        Returns True if the current value of the BoundSpan exactly covers its
        limits (as specified when the BoundSpan was created).
        
        >>> s = BoundSpan(100, 300)
        >>> s.addRange(0, 1000)
        >>> str(s)
        '100-300'
        >>> s.isFull()
        True
        >>> s.deleteRange(255, 255)
        >>> str(s)
        '100-254, 256-300'
        >>> s.isFull()
        False
        """
        
        return len(self.spans) == 1 and self.spans[0] == (self.low, self.high)
    
    def unionSpan(self, other):
        """
        Does superclass unionSpan and then clips to the bounds.
        
        >>> s1 = BoundSpan(0, 100, [98, 99])
        >>> s2 = BoundSpan(100, 200, [100, 101])
        >>> str(s1)
        '98-99'
        >>> str(s2)
        '100-101'
        >>> s1.unionSpan(s2)
        >>> str(s1)
        '98-100'
        """
        
        super(BoundSpan, self).unionSpan(other)
        self._clipCheck()

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
