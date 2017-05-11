#
# span2.py
#
# Copyright © 2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Alternative implementation of spans that are always bounded, and use sets as
the primary store. This drastically speeds up Boolean operations on the Span.
"""

# System imports
import re

# Other imports
from fontio3 import utilities
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Span(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing collections of non-negative integers. These are sets
    for ease of manipulation, with special string and pprint functions to make
    their output compact.
    
    Note that unlike the utilities.span module, the spans defined here are
    never open-ended.
    
    >>> Span({3, 4, 5, 6, 7, 14, 30, 31, 32}).pprint(label="The Span")
    The Span:
      3-7, 14, 30-32
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
      set_pprintfunc = (lambda p,obj: p(str(obj))))
    
    attrSpec = dict(
        showInHex = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: False),
            attr_label = "Show values in hex"))
    
    attrSorted = ()
    
    #
    # Class constants
    #
    
    patDecimal = re.compile(r"([0-9]+|\-)")
    patHex = re.compile(r"([0-9A-Fa-f]+|\-)")
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of the object. If the object's
        showInHex attribute is True then the output will use hex.
        
        >>> obj = Span.fromstring("2190-3285, 4000-6000")
        >>> print(obj)
        2190-3285, 4000-6000
        >>> obj.showInHex = True
        >>> print(obj)
        88E-CD5, FA0-1770
        """
        
        sv = []
        
        if self.showInHex:
            for t in self.ranges():
                first, last = t
                sv.append(("%X" % (first,) if first == last else "%X-%X" % t))
        
        else:
            for t in self.ranges():
                first, last = t
                sv.append((str(first) if first == last else "%d-%d" % t))
        
        return ', '.join(sv)
    
    def addFromHexString(self, s):
        """
        Parses the string, which will contain single hex numbers or ranges
        (which are two hex numbers with an intervening hyphen) and adds the
        results to the span.
        
        ValueErrors will be raised if the string is ill-formed.
        
        >>> obj = Span({}, showInHex=True)
        >>> obj.addFromHexString("D, 10-1B, 27-50")
        >>> print(obj)
        D, 10-1B, 27-50
        >>> obj.addFromHexString("E-F")
        >>> print(obj)
        D-1B, 27-50
        >>> obj.addFromHexString("CC")
        >>> print(obj)
        D-1B, 27-50, CC
        
        >>> obj.addFromHexString("-9")
        Traceback (most recent call last):
          ...
        ValueError: String cannot start with a hyphen!
        
        >>> obj.addFromHexString("9-")
        Traceback (most recent call last):
          ...
        ValueError: String cannot end with a hyphen!
        
        >>> obj.addFromHexString("5--9")
        Traceback (most recent call last):
          ...
        ValueError: String has adjacent hyphens!
        """
        
        v = self.patHex.findall(s)
        i = 0
        current = None
        
        while i < len(v):
            s = v[i]
            
            if s == '-':
                if current is None:
                    raise ValueError("String cannot start with a hyphen!")
                
                if i == len(v) - 1:
                    raise ValueError("String cannot end with a hyphen!")
                
                s = v[i + 1]
                
                if s == '-':
                    raise ValueError("String has adjacent hyphens!")
                
                self.update(range(current, int(s, 16) + 1))
                current = None
                i += 2
            
            else:
                if current is not None:
                    self.add(current)
                
                current = int(s, 16)
                i += 1
        
        if current is not None:
            self.add(current)
    
    def addFromString(self, s):
        """
        Parses the string, which will contain single decimal numbers or ranges
        (which are two decimal numbers with an intervening hyphen) and adds the
        results to the span.
        
        ValueErrors will be raised if the string is ill-formed.
        
        >>> obj = Span()
        >>> obj.addFromString("13, 16-27, 39-80")
        >>> print(obj)
        13, 16-27, 39-80
        >>> obj.addFromString("14-15")
        >>> print(obj)
        13-27, 39-80
        >>> obj.addFromString("99")
        >>> print(obj)
        13-27, 39-80, 99
        
        >>> obj.addFromString("-9")
        Traceback (most recent call last):
          ...
        ValueError: String cannot start with a hyphen!
        
        >>> obj.addFromString("9-")
        Traceback (most recent call last):
          ...
        ValueError: String cannot end with a hyphen!
        
        >>> obj.addFromString("5--9")
        Traceback (most recent call last):
          ...
        ValueError: String has adjacent hyphens!
        """
        
        v = self.patDecimal.findall(s)
        i = 0
        current = None
        
        while i < len(v):
            s = v[i]
            
            if s == '-':
                if current is None:
                    raise ValueError("String cannot start with a hyphen!")
                
                if i == len(v) - 1:
                    raise ValueError("String cannot end with a hyphen!")
                
                s = v[i + 1]
                
                if s == '-':
                    raise ValueError("String has adjacent hyphens!")
                
                self.update(range(current, int(s) + 1))
                current = None
                i += 2
            
            else:
                if current is not None:
                    self.add(current)
                
                current = int(s)
                i += 1
        
        if current is not None:
            self.add(current)
    
    @classmethod
    def fromhexstring(cls, s, **kwArgs):
        """
        Creates and returns a new Span from the specified string, which should
        have its values expressed in hex. Note that showInHex will be set to
        True in the resulting Span if the caller did not explicitly set its
        value in kwArgs.
        
        >>> print(Span.fromhexstring("100-1FF"))
        100-1FF
        
        >>> print(Span.fromhexstring("100-1FF", showInHex=False))
        256-511
        """
        
        if 'showInHex' not in kwArgs:
            kwArgs['showInHex'] = True
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        r.addFromHexString(s)
        return r
    
    @classmethod
    def fromranges(cls, iterable, **kwArgs):
        """
        Creates and returns a new Span from the specified iterable, which
        should yield (first, last) pairs.
        
        >>> print(Span.fromranges([(4, 50), (100, 200), (900, 1200)]))
        4-50, 100-200, 900-1200
        
        Duplication is fine:
        
        >>> print(Span.fromranges([(4, 50), (60, 90), (15, 85)]))
        4-90
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        for first, last in iterable:
            r.update(range(first, last + 1))
        
        return r
    
    @classmethod
    def fromstring(cls, s, **kwArgs):
        """
        Creates and returns a new Span from the specified string, which should
        have its values expressed in decimal. Note that showInHex will be set
        to False in the resulting Span if the caller did not explicitly set its
        value in kwArgs.
        
        >>> print(Span.fromstring("256-511"))
        256-511
        
        >>> print(Span.fromstring("256-511", showInHex=True))
        100-1FF
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        r.addFromString(s)
        return r
    
    def inverted(self, lowest, highest):
        """
        Returns a new Span object containing all values it doesn't currently
        contain.
        
        >>> obj = Span.fromranges([(30, 49), (75, 123), (190, 208)])
        >>> print(obj)
        30-49, 75-123, 190-208
        
        >>> print(obj.inverted(0, 999))
        0-29, 50-74, 124-189, 209-999
        """
        
        return type(self)(
          set(range(lowest, highest + 1)) - self,
          **self.__dict__)
    
    def ranges(self):
        """
        Returns a generator over (first, last) pairs for the current contents
        of the Span.
        
        >>> print(list(Span({2, 3, 4, 12, 15, 16}).ranges()))
        [(2, 4), (12, 12), (15, 16)]
        
        >>> print(list(Span().ranges()))
        []
        """
        
        it = utilities.monotonicGroupsGenerator(sorted(self))
        
        for start, stop, ignore in it:
            yield (start, stop - 1)

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
    _test()
