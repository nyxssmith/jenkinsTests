#
# pp.py -- Pretty-printing support for fontio3
#
# Copyright © 2008-2011, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a pretty-printing abstraction that's more useful for fontio3
than the Python-provided one.
"""

# System imports
import collections
import copy
import difflib
import itertools
import operator
import sys
import textwrap

# Other imports
from fontio3 import utilities
from fontio3.utilities import span

# -----------------------------------------------------------------------------

#
# Private functions
#

def _encolon(s):
    """
    If the specified string already ends with a colon then the string itself is
    returned. Otherwise a new string made up of the specified string with an
    appended colon is returned.
    
    >>> _encolon("abc")
    'abc:'
    >>> _encolon("ab:")
    'ab:'
    """
    
    return (s if s.endswith(':') else s + ':')

def _hexline(s):
    """
    Formats a single line of from 1 to 16 bytes for hexdump.
    
    >>> _hexline(b"A")
    '41                                       |A               |'
    >>> _hexline(b"ABCDEFGH")
    '4142 4344 4546 4748                      |ABCDEFGH        |'
    >>> _hexline(b"ABCDEFG")
    '4142 4344 4546 47                        |ABCDEFG         |'
    """
    
    sv = (["%0.2X" % x for x in s] + ["  "] * 15)[:16]
    c = (''.join(('.', chr(x))[32 <= x < 127] for x in s) + " " * 15)[:16]
    return "%s%s %s%s %s%s %s%s  %s%s %s%s %s%s %s%s |%s|" % tuple(sv + [c])

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def analyze_diff_mapping(currObj, priorObj):
    """
    Analyzes the differences in the two mappings and returns three sets whose
    values are keys: added, deleted and changed.
    
    >>> d1 = {'a': 2, 'c': 5, 'd': 9, 'e': -3}
    >>> d2 = {'a': 3, 'b': 8, 'e': -3}
    >>> analyze_diff_mapping(d2, d1) == ({'b'}, {'c', 'd'}, {'a'})
    True
    """
    
    added = set()
    changed = set()
    
    for key in currObj:
        if key in priorObj:
            currValue = currObj[key]
            priorValue = priorObj[key]
            
            if currValue is not priorValue and currValue != priorValue:
                changed.add(key)
        
        else:
            added.add(key)
    
    deleted = set(key for key in priorObj if key not in currObj)
    
    return added, deleted, changed

def analyze_diff_sequence(currObj, priorObj, decorator=None):
    """
    Analyzes the differences in the two sequences and returns a dict
    characterizing those differences.
    
    If the sequence is made up of mutable objects, the caller should also pass
    in a decorator function. This must be called with a single argument (the
    item from the sequence), and must return an immutable object that is
    logically equivalent (e.g. a hash).
    
    >>> v1 = [3, 8]
    >>> v2 = list(range(1, 11))
    >>> PP().mapping(analyze_diff_sequence(v2, v1))
    'insert': [(0, 0, 0, 2), (1, 1, 3, 7), (2, 2, 8, 10)]
    >>> PP().mapping(analyze_diff_sequence(v1, v2))
    'delete': [(0, 2, 0, 0), (3, 7, 1, 1), (8, 10, 2, 2)]
    >>> PP().mapping(analyze_diff_sequence([1, 2, 3, 4, 5], [1, 17, 5]))
    'replace': [(1, 2, 1, 4)]
    >>> v1 = [{1: 3}, {2: 4, 3: 6}, {4: 19}]
    >>> v2 = [{1: 3}, {2: 5, 3: 6}, {8: 8}, {4: 19}]
    >>> PP().mapping(analyze_diff_sequence(v2, v1))
    Traceback (most recent call last):
      [...]
    TypeError: unhashable type: 'dict'
    >>> PP().mapping(analyze_diff_sequence(v2, v1, decorator=lambda x: tuple(x.items())))
    'replace': [(1, 2, 1, 3)]
    """
    
    if decorator is not None:
        currObj = [decorator(obj) for obj in currObj]
        priorObj = [decorator(obj) for obj in priorObj]
    
    sm = difflib.SequenceMatcher(a=priorObj, b=currObj)
    d = collections.defaultdict(list)
    
    for t in sm.get_opcodes():
        k = t[0]
        
        if k != 'equal':
            d[k].append(t[1:])
    
    return d

def analyze_diff_setlike(currObj, priorObj):
    """
    Analyzes the differences in the two set-like objects and returns two sets
    whose values are objects: added and deleted.
    
    >>> analyze_diff_setlike(set([1, 2, 4, 8]), set([2, 3, 4, 5]))
    ({8, 1}, {3, 5})
    """
    
    return currObj - priorObj, priorObj - currObj

def isDictlike(obj):
    try:
        obj.get(0, None)
        return True
    except:
        return False

def isListlike(obj):
    try:
        obj + [0]
        return True
    except:
        return False

def isSetlike(obj):
    try:
        obj - frozenset([1])
        return True
    except:
        return False

def isStringlike(obj):
    try:
        obj + 'a'
        return True
    except:
        return False

def isTuplelike(obj):
    try:
        obj + (0,)
        return True
    except:
        return False

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PP(object):
    """
    Pretty-printing support objects. Instances of this class are used in pprint
    methods throughout fontio3 to ease the process.
    """
    
    #
    # Constants
    #
    
    _initDict = {
      'indent': 0,
      'indentDelta': 2,
      'label': None,
      'maxWidth': None,
      'noDataString': "(no data)"}
    
    #
    # Initialization method
    #
    
    def __init__(self, **kwArgs):
        """
        Initializes the object with some set (possibly empty) of keyword
        arguments, which include:
        
            indent          How many spaces to indent on left (default 0)
            indentDelta     Extra spaces per new indent (default 2)
            label           Header label, only printed once (default None)
            maxWidth        Line-length limit (unlimited if None, the default)
            noDataString    String used for deep Nones (default "(no data)")
            stream          Stream to receive output (default sys.stdout)
        
        If there is a keyword argument named 'p' its contents are used.
        
        >>> p = PP()
        >>> p.indent, p.indentDelta, p.label
        (0, 2, None)
        >>> p = PP(indentDelta=5, label="One-shot")
        >>> p.indent, p.indentDelta, p.label
        (0, 5, 'One-shot')
        >>> p2 = PP(p=p)
        >>> p2.indent, p2.indentDelta, p2.label
        (0, 5, 'One-shot')
        """
        
        if 'p' in kwArgs:
            self.__dict__ = kwArgs['p'].__dict__
        
        else:
            d = self.__dict__ = self._initDict.copy()
            d['stream'] = sys.stdout
            d.update(kwArgs)
            d['_sp'] = " " * self.indent
            
            if 'keys' in d:
                del d['keys']
    
    #
    # Special methods
    #
    
    def __call__(self, obj, **kwArgs):
        r"""
        Instances of PP are callable, and clients should call them to do a
        standard pprint of a line.
        
        >>> p = PP()
        >>> p(15)
        15
        >>> p("Fred")
        Fred
        >>> p = PP(indent=5, label="Values")
        >>> p(15)
             Values:
               15
        >>> p("Fred")
               Fred
        >>> p("Line 1\nLine 2\n\nLine 4")
               Line 1
               Line 2
        <BLANKLINE>
               Line 4
        
        >>> PP(maxWidth=70)("abc defg " * 100)
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg abc defg abc defg abc defg abc defg abc defg
        abc defg abc defg abc defg abc defg abc defg abc defg abc defg abc
        defg abc defg abc defg
        
        >>> PP(label="\u00D6le")("The Gl\u00F6gg is good.")
        Öle:
          The Glögg is good.
        
        >>> PP(label="\u00D6le")("The Gl\u00F6gg is good.", useRepr=True)
        Öle:
          'The Glögg is good.'
        """
        
        sr = (repr if kwArgs.get('useRepr', False) else str)
        
        if self.maxWidth is None:
            if self.label is not None:
                print("%s%s" % (self._sp, _encolon(self.label)), file=self.stream)
                self.label = None
                self._bumpIndent(1)
            
            for separatedLine in sr(obj).splitlines():
                print("%s%s" % (self._sp, separatedLine), file=self.stream)
        
        else:
            if self.label is not None:
                s = "%s%s" % (self._sp, _encolon(self.label))
                v = textwrap.wrap(
                  s, width=self.maxWidth, initial_indent=self._sp, subsequent_indent=self._sp)
                
                for piece in v:
                    print(piece, file=self.stream)
                
                self.label = None
                self._bumpIndent(1)
            
            for separatedLine in sr(obj).splitlines():
                if not separatedLine:
                    v = ['']
                
                else:
                    v = textwrap.wrap(
                      separatedLine,
                      width=self.maxWidth,
                      initial_indent=self._sp,
                      subsequent_indent=self._sp + (" " * kwArgs.get('extraSubsequentIndent', 0)))
                
                for piece in v:
                    print(piece, file=self.stream)
    
    #
    # Private methods
    #
    
    def _bumpIndent(self, nestLevel):
        self.indent += nestLevel * self.indentDelta
        self._sp = " " * self.indent
    
    def _diff_sequence_common(self, currObj, priorObj, d, func):
        for i1, i2, j1, j2 in d['insert']:
            v = currObj[j1:j2]
            
            if i1 == 0:
                func(v, label="Inserted at the start")
            elif i1 < len(priorObj):
                func(v, label="Inserted before index %d" % (i1,))
            else:
                func(v, label="Appended at end")
        
        for i1, i2, j1, j2 in d['delete']:
            v = priorObj[i1:i2]
            
            if i1 == 0:
                func(v, label="Deleted from the start")
            elif i2 == len(priorObj):
                func(v, label="Deleted from the end")
            else:
                func(v, label="Deleted from old index %d" % (i1,))
        
        for i1, i2, j1, j2 in d['replace']:
            func(currObj[j1:j2], label="This sequence at new index %d" % (j1,))
            func(priorObj[i1:i2], label="replaced this sequence at old index %d" % (i1,))
    
    def _limitedDict(self):  # for older pprint() methods
        return {
          'indent': self.indent,
          'indentDelta': self.indentDelta,
          'stream': self.stream}
    
    def _makeDict(self, nestLevel):
        if nestLevel == -1:
            return {
              'indent': 0,
              'indentDelta': self.indentDelta,
              'stream': self.stream,
              'maxWidth': self.maxWidth}
        
        return {
          'indent': self.indent + nestLevel * self.indentDelta,
          'indentDelta': self.indentDelta,
          'stream': self.stream,
          'maxWidth': self.maxWidth}
    
    def _ndc(self, obj, **kwArgs):
        sr = (repr if kwArgs.get('useRepr', False) else str)
        return (self.noDataString if obj is None else sr(obj))
    
    #
    # Public methods
    #
    
    def deep(self, obj, label=None, **kwArgs):
        """
        Pretty-print an object that itself has a pprint method.
        
        >>> p = PP(label="Top label")
        >>> p.deep(X(5), label="Bottom label 1")
        Top label:
          Bottom label 1:
            The list [0, 1, 2, 3, 4]
        >>> p.deep(X(3), label="Bottom label 2")
          Bottom label 2:
            The list [0, 1, 2]
        >>> p.deep(X(4))
          The list [0, 1, 2, 3]
        >>> p.deep(None, label="Bottom label 3")
          Bottom label 3:
            (no data)
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        if obj is not None:
            obj.pprint(p=self, **kwArgs)
        else:
            self(self.noDataString)
    
    def diff(self, currObj, priorObj, label, **kwArgs):
        """
        Pretty-print the difference in the two values. Note that the client is
        responsible for calling this method only when there is a difference,
        since this method does not test for equality (as that might be
        potentially very expensive for some objects).
        
        >>> PP().diff(12, -15, "x")
        x changed from -15 to 12
        >>> PP(label="Summary of differences").diff('abc', 'abd', "The input string", useRepr=True)
        Summary of differences:
          The input string changed from 'abd' to 'abc'
        >>> PP().diff(19, None, "x")
        x changed from (no data) to 19
        """
        
        f = self._ndc
        currObj = f(currObj, **kwArgs)
        priorObj = f(priorObj, **kwArgs)
        self("%s changed from %s to %s" % (label, priorObj, currObj))
    
    def diff_deep(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two objects, using currObj's own
        pprint_changes method.
        
        >>> x1, x2 = X(5), X(2)
        >>> PP().diff_deep(x1, None)
        Prior was empty, current is:
          The list [0, 1, 2, 3, 4]
        >>> PP().diff_deep(x1, None, label="Changes")
        Changes:
          Prior was empty, current is:
            The list [0, 1, 2, 3, 4]
        >>> PP().diff_deep(None, x2)
        Current is empty, prior was:
          The list [0, 1]
        >>> PP().diff_deep(None, x2, label="Changes")
        Changes:
          Current is empty, prior was:
            The list [0, 1]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        if currObj is not None and priorObj is not None:
            currObj.pprint_changes(priorObj, p=self, **kwArgs)
        elif currObj is not None:
            self("Prior was empty, current is:")
            self.makeIndentedPP().deep(currObj, **kwArgs)
        elif priorObj is not None:
            self("Current is empty, prior was:")
            self.makeIndentedPP().deep(priorObj, **kwArgs)
        else:
            self(self.noDataString)
    
    def diff_mapping(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two mappings.
    
        >>> d1 = {'a': 2, 'c': 5, 'd': 9, 'e': -3}
        >>> d2 = {'a': 3, 'b': 8, 'e': -3}
        >>> PP().diff_mapping(d2, d1)
        Added records:
          'b': 8
        Deleted records:
          'c': 5
          'd': 9
        Changed records:
          'a': from 2 to 3
        >>> PP().diff_mapping(d1, d2)
        Added records:
          'c': 5
          'd': 9
        Deleted records:
          'b': 8
        Changed records:
          'a': from 3 to 2
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        added, deleted, changed = analyze_diff_mapping(currObj, priorObj)
        
        if added:
            g = ((k, currObj[k]) for k in sorted(added))
            self.pair_iterator(g, label="Added records", **kwArgs)
        
        if deleted:
            g = ((k, priorObj[k]) for k in sorted(deleted))
            self.pair_iterator(g, label="Deleted records", **kwArgs)
        
        if changed:
            f = (repr if kwArgs.get('useRepr', False) else str)
            g = ((k, "from %s to %s" % (f(priorObj[k]), f(currObj[k]))) for k in sorted(changed))
            self.pair_iterator(g, label="Changed records", useRepr=False)
    
    def diff_mapping_deep(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two mappings.
        
        >>> d1 = {'a': X(3), 'b': X(4), 'c': X(2), 'd': X(5)}
        >>> d2 = {'b': X(4), 'c': X(3), 'e': X(6)}
        >>> PP().diff_mapping_deep(d2, d1)
        Added records:
          'e':
            The list [0, 1, 2, 3, 4, 5]
        Deleted records:
          'a':
            The list [0, 1, 2]
          'd':
            The list [0, 1, 2, 3, 4]
        Changed records:
          'c' changed from:
            The list [0, 1]
          to:
            The list [0, 1, 2]
        >>> PP().diff_mapping_deep(d1, d2)
        Added records:
          'a':
            The list [0, 1, 2]
          'd':
            The list [0, 1, 2, 3, 4]
        Deleted records:
          'e':
            The list [0, 1, 2, 3, 4, 5]
        Changed records:
          'c' changed from:
            The list [0, 1, 2]
          to:
            The list [0, 1]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        added, deleted, changed = analyze_diff_mapping(currObj, priorObj)
        
        if added:
            g = ((k, currObj[k]) for k in sorted(added))
            self.pair_iterator_deep(g, label="Added records", **kwArgs)
        
        if deleted:
            g = ((k, priorObj[k]) for k in sorted(deleted))
            self.pair_iterator_deep(g, label="Deleted records", **kwArgs)
        
        if changed:
            self("Changed records:")
            indent1 = self.makeIndentedPP()
            
            for k in sorted(changed):
                indent1.deep(priorObj[k], label="%s changed from" % (repr(k),), **kwArgs)
                indent1.deep(currObj[k], label="to", **kwArgs)
    
    def diff_sequence(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two sequences.
        
        >>> v1 = ['c', 'h']
        >>> v2 = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
        >>> PP().diff_sequence(v2, v1, useRepr=True)
        Inserted at the start:
          'a'
          'b'
        Inserted before index 1:
          'd'
          'e'
          'f'
          'g'
        Appended at end:
          'i'
          'j'
        >>> PP().diff_sequence(v1, v2, useRepr=True)
        Deleted from the start:
          'a'
          'b'
        Deleted from old index 3:
          'd'
          'e'
          'f'
          'g'
        Deleted from the end:
          'i'
          'j'
        >>> PP().diff_sequence([1, 2, 3, 4, 5], [1, 17, 5])
        This sequence at new index 1:
          2
          3
          4
        replaced this sequence at old index 1:
          17
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        d = analyze_diff_sequence(currObj, priorObj, decorator=kwArgs.get('decorator', None))
        f = self.sequence
        
        for i1, i2, j1, j2 in d['insert']:
            v = currObj[j1:j2]
            
            if i1 == 0:
                f(v, label="Inserted at the start", **kwArgs)
            elif i1 < len(priorObj):
                f(v, label="Inserted before index %d" % (i1,), **kwArgs)
            else:
                f(v, label="Appended at end", **kwArgs)
        
        for i1, i2, j1, j2 in d['delete']:
            v = priorObj[i1:i2]
            
            if i1 == 0:
                f(v, label="Deleted from the start", **kwArgs)
            elif i2 == len(priorObj):
                f(v, label="Deleted from the end", **kwArgs)
            else:
                f(v, label="Deleted from old index %d" % (i1,), **kwArgs)
        
        for i1, i2, j1, j2 in d['replace']:
            f(currObj[j1:j2], label="This sequence at new index %d" % (j1,), **kwArgs)
            f(priorObj[i1:i2], label="replaced this sequence at old index %d" % (i1,), **kwArgs)
    
    def diff_sequence_deep(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two sequences. Note that the objects
        making up the sequences must be hashable and support comparison for
        equality.
        
        >>> v1 = [X(3), X(8)]
        >>> v2 = [X(i) for i in range(1, 11)]
        >>> PP().diff_sequence_deep(v2, v1)
        Inserted at the start:
          The list [0]
          The list [0, 1]
        Inserted before index 1:
          The list [0, 1, 2, 3]
          The list [0, 1, 2, 3, 4]
          The list [0, 1, 2, 3, 4, 5]
          The list [0, 1, 2, 3, 4, 5, 6]
        Appended at end:
          The list [0, 1, 2, 3, 4, 5, 6, 7, 8]
          The list [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> PP().diff_sequence_deep(v1, v2)
        Deleted from the start:
          The list [0]
          The list [0, 1]
        Deleted from old index 3:
          The list [0, 1, 2, 3]
          The list [0, 1, 2, 3, 4]
          The list [0, 1, 2, 3, 4, 5]
          The list [0, 1, 2, 3, 4, 5, 6]
        Deleted from the end:
          The list [0, 1, 2, 3, 4, 5, 6, 7, 8]
          The list [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> PP().diff_sequence_deep(v1, [v2[2]] + v2[4:6] + [v2[8]])
        This sequence at new index 1:
          The list [0, 1, 2, 3, 4, 5, 6, 7]
        replaced this sequence at old index 1:
          The list [0, 1, 2, 3, 4]
          The list [0, 1, 2, 3, 4, 5]
          The list [0, 1, 2, 3, 4, 5, 6, 7, 8]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        d = analyze_diff_sequence(currObj, priorObj, decorator=kwArgs.get('decorator', None))
        f = self.sequence_deep
        
        for i1, i2, j1, j2 in d['insert']:
            v = currObj[j1:j2]
            
            if i1 == 0:
                f(v, label="Inserted at the start", **kwArgs)
            elif i1 < len(priorObj):
                f(v, label="Inserted before index %d" % (i1,), **kwArgs)
            else:
                f(v, label="Appended at end", **kwArgs)
        
        for i1, i2, j1, j2 in d['delete']:
            v = priorObj[i1:i2]
            
            if i1 == 0:
                f(v, label="Deleted from the start", **kwArgs)
            elif i2 == len(priorObj):
                f(v, label="Deleted from the end", **kwArgs)
            else:
                f(v, label="Deleted from old index %d" % (i1,), **kwArgs)
        
        for i1, i2, j1, j2 in d['replace']:
            f(currObj[j1:j2], label="This sequence at new index %d" % (j1,), **kwArgs)
            f(priorObj[i1:i2], label="replaced this sequence at old index %d" % (i1,), **kwArgs)
    
    def diff_setlike(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two set-like objects. There is no
        guarantee about the order in which the differences are shown.
        
        >>> PP().diff_setlike(set([1, 2, 4, 8]), set([2, 3, 4, 5]))
        Added records:
          8
          1
        Deleted records:
          3
          5
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        added, deleted = analyze_diff_setlike(currObj, priorObj)
        
        if added:
            self.setlike(added, label="Added records", **kwArgs)
        
        if deleted:
            self.setlike(deleted, label="Deleted records", **kwArgs)
    
    def diff_setlike_deep(self, currObj, priorObj, label=None, **kwArgs):
        """
        Pretty-print the difference in the two set-like objects, where these
        objects have their own pprint() methods. There is no guarantee about
        the order in which the differences are shown.
        
        >>> PP().diff_setlike_deep(set(X(i) for i in [1, 2, 4, 8]), set(X(i) for i in [2, 3, 4, 5]))
        Added records:
          The list [0]
          The list [0, 1, 2, 3, 4, 5, 6, 7]
        Deleted records:
          The list [0, 1, 2]
          The list [0, 1, 2, 3, 4]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        added, deleted = analyze_diff_setlike(currObj, priorObj)
        
        if added:
            self.setlike_deep(added, label="Added records", **kwArgs)
        
        if deleted:
            self.setlike_deep(deleted, label="Deleted records", **kwArgs)
    
    def fixed(self, n, label=None):
        """
        Pretty-prints the specified value, which is interpreted as a 16.16
        fixed value. Note that n must be positive; a negative value will have
        the high bit set. See the doctests below for clarification.
        
        >>> p = PP(label="Some fixed values")
        >>> p.fixed(0x00020000, label="Positive two")
        Some fixed values:
          Positive two: 2.0
        >>> p.fixed(0xFFFE0000, label="Negative two")
          Negative two: -2.0
        >>> p.fixed(0x00014000, label="One and a quarter")
          One and a quarter: 1.25
        >>> p.fixed(-0x00010000, label="Uh oh")
        Traceback (most recent call last):
          ...
        AssertionError: Cannot pass negative values to fixed()!
        >>> p.fixed(0x200000000, label="Uh oh")
        Traceback (most recent call last):
          ...
        AssertionError: Value out of range!
        """
        
        assert n >= 0, "Cannot pass negative values to fixed()!"
        assert n < 0x100000000, "Value out of range!"
        
        if n >= 0x80000000:
            self.simple((n - 0x100000000) / 65536.0, label=label)
        else:
            self.simple(n / 65536.0, label=label)
    
    def generic(self, obj, label=""):
        if label:
            label = _encolon(label) + " "
        
        if obj is None:
            self("%s%s" % (label, self.noDataString))
            return
        
        elif hasattr(obj, 'pprint'):
            self("%sa pprint-aware object:" % (label,))
            p2 = self.makeIndentedPP()
            
            try:
                obj.pprint(**p2.__dict__)
            except TypeError:  # old-style pprint() method
                obj.pprint(**p2._limitedDict())
            
            return
        
        elif isStringlike(obj):
            self("%s%s" % (label, repr(obj)))
        
        elif isListlike(obj) or isTuplelike(obj):
            if obj:
                if label:
                    self("%s(a sequence)" % (label,))
                else:
                    self("a sequence:")
                
                p2 = self.makeIndentedPP()
                
                for i, item in enumerate(obj):
                    p2.generic(item, "%d" % (i,))
            
            else:
                self("%san empty sequence" % (label,))
        
        elif isDictlike(obj):
            if obj:
                if label:
                    self("%s(a mapping)" % (label,))
                else:
                    self("a mapping:")
                
                p2 = self.makeIndentedPP()
                
                for key in sorted(obj):
                    p2.generic(obj[key], "%s" % (repr(key),))
            
            else:
                self("%san empty mapping" % (label,))
        
        elif isSetlike(obj):
            if obj:
                self("%sa set:" % (label,))
                p2 = self.makeIndentedPP()
                
                for item in obj:
                    p2.generic(item)
            
            else:
                self("%san empty set" % (label,))
        
        else:
            self("%s%s" % (label, repr(obj)))
    
    def hexDump(self, obj, label=None):
        """
        Pretty-print a hex dump of the object (which is first converted, if
        necessary, to a string).
        
        >>> p = PP(label="Top label")
        >>> p.hexDump("In a hole in the ground there lived a hobbit.")
        Top label:
                 0 |   496E 2061 2068 6F6C  6520 696E 2074 6865 |In a hole in the|
                10 |   2067 726F 756E 6420  7468 6572 6520 6C69 | ground there li|
                20 |   7665 6420 6120 686F  6262 6974 2E        |ved a hobbit.   |
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        try:
            s = bytes(obj, 'ascii')
        except TypeError:
            s = obj
        
        startOffset = 0
        origLen = len(s)
        
        while startOffset < origLen:
            self.no_newline("%8X |" % (startOffset,))
            chunkLen = min(16, origLen - startOffset)
            self(_hexline(s[startOffset:startOffset+chunkLen]))
            startOffset += 16
    
    def makeIndentedPP(self):
        r = copy.copy(self)
        r._bumpIndent(1)
        return r
    
    def mapping(self, m, label=None, **kwArgs):
        """
        Pretty-print a mapping (e.g. a dict) whose values do not have their own
        pprint methods. The keys are sorted.
        
        >>> p = PP(label="Top label")
        >>> p.mapping({'george': 5, 'fred': 'A sentence this is.'}, label="Bottom label 1", useRepr=True)
        Top label:
          Bottom label 1:
            'fred': 'A sentence this is.'
            'george': 5
        >>> p.mapping(dict.fromkeys(['c', 'a', 'b'], -1), label="Bottom label 2")
          Bottom label 2:
            'a': -1
            'b': -1
            'c': -1
        >>> p.mapping({3: 5})
          3: 5
        """
        
        g = ((k, m[k]) for k in sorted(m))
        self.pair_iterator(g, label=label, **kwArgs)
    
    def mapping_deep(self, m, label=None, **kwArgs):
        """
        Pretty-print a mapping (e.g. a dict) whose values have their own pprint
        methods. The keys are sorted.
        
        >>> v = [X(n) for n in range(4, 9)]
        >>> p = PP(label="Top label", noDataString="ZILCH")
        >>> d = {'fred': v[3], 'george': v[0], 'david': None}
        >>> p.mapping_deep(d, "Bottom label")
        Top label:
          Bottom label:
            'david': ZILCH
            'fred':
              The list [0, 1, 2, 3, 4, 5, 6]
            'george':
              The list [0, 1, 2, 3]
        """
        
        g = ((k, m[k]) for k in sorted(m))
        self.pair_iterator_deep(g, label=label, **kwArgs)
    
    def mapping_deep_smart(self, m, isMultilineFunc, label=None, **kwArgs):
        """
        Pretty-print a mapping (e.g. a dict) whose values have their own pprint
        methods. The keys are sorted. Before each
        object's pprint method is called, the isMultilineFunc predicate
        function is called on that object. If the return value is true, the
        display is as for mapping_deep (i.e. the key on one line and the
        object's pprint output indented below it). If the return value is
        false, the key and pprint output appear on the same line.
        
        >>> v = [X(n) for n in range(4, 9)]
        >>> p = PP(label="Top label")
        >>> d = {'fred': v[3], 'george': v[0], 'david': None}
        >>> p.mapping_deep_smart(d, lambda x: False, "Bottom label 1")
        Top label:
          Bottom label 1:
            'david': (no data)
            'fred': The list [0, 1, 2, 3, 4, 5, 6]
            'george': The list [0, 1, 2, 3]
        >>> p.mapping_deep_smart(d, lambda x: True, "Bottom label 2")
          Bottom label 2:
            'david': (no data)
            'fred':
              The list [0, 1, 2, 3, 4, 5, 6]
            'george':
              The list [0, 1, 2, 3]
        >>> p = PP(label="Top label 2")
        >>> p.mapping_deep_smart(d, lambda x: False)
        Top label 2:
          'david': (no data)
          'fred': The list [0, 1, 2, 3, 4, 5, 6]
          'george': The list [0, 1, 2, 3]
        >>> p = PP(label="Top label 3")
        >>> p.mapping_deep_smart(d, lambda x: True)
        Top label 3:
          'david': (no data)
          'fred':
            The list [0, 1, 2, 3, 4, 5, 6]
          'george':
            The list [0, 1, 2, 3]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        pNormal = type(self)(**self._makeDict(1 if self.label is None else 2))
        pCompact = type(self)(**self._makeDict(-1))
        
        for k in sorted(m):
            obj = m[k]
            t = (repr(k),)
            
            if obj is None:
                self("%s: %s" % (repr(k), self.noDataString))
            elif isMultilineFunc(obj):
                self("%s:" % t)
                obj.pprint(p=pNormal, **kwArgs)
            else:
                self.no_newline("%s:" % t)
                obj.pprint(p=pCompact, **kwArgs)
    
    def mapping_grouped(self, obj, label=None, **kwArgs):
        """
        Pretty-print a mapping where adjacent equal elements are grouped. Note
        that for a mapping to use this method, its keys *must* be integers.
        Gaps are OK, but there should be no non-integral keys.
        
        >>> d = {0:1, 1:1, 2:1, 3:2, 4:1, 5:1, 6:None, 7:None, 9:4, 10:4, 12:4}
        >>> PP(label="Top label", noDataString="(deleted)").mapping_grouped(d, label="Bottom label")
        Top label:
          Bottom label:
            [0-2]: 1
            [3]: 2
            [4-5]: 1
            [6-7]: (deleted)
            [9-10, 12]: 4
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        gen = ((k, obj[k]) for k in sorted(obj))  # sorted iterators would be nice...
        nds = self.noDataString
        f = (repr if kwArgs.get('useRepr', False) else str)
        
        for k, g in itertools.groupby(gen, lambda x: x[1]):
            sp = span.Span(x[0] for x in g)
            s = str(sp)
            x = obj[sp[0][0]]
            
            if x is None:
                self("[%s]: %s" % (s, nds))
            else:
                self("[%s]: %s" % (s, f(x)))
    
    def mapping_grouped_deep(self, obj, label=None, **kwArgs):
        """
        Pretty-print a mapping where adjacent equal elements are grouped. Each
        non-None element of the mapping has its own pprint() method. Note that
        for a mapping to use this method, its keys *must* be integers. Gaps are
        OK, but there should be no non-integral keys.
        
        >>> d = {14:X(3), 15:X(3), 16:X(3), 17:None, 18:None, 19:X(5), 20:X(4), 22:X(4)}
        >>> p = PP(label="Top label", noDataString="(object has been deleted)")
        >>> p.mapping_grouped_deep(d, label="Bottom label")
        Top label:
          Bottom label:
            [14-16]:
              The list [0, 1, 2]
            [17-18]: (object has been deleted)
            [19]:
              The list [0, 1, 2, 3, 4]
            [20, 22]:
              The list [0, 1, 2, 3]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        gen = ((k, obj[k]) for k in sorted(obj))  # sorted iterators would be nice...
        nds = self.noDataString
        p = type(self)(**self._makeDict(1 if self.label is None else 2))
        
        for k, g in itertools.groupby(gen, operator.itemgetter(1)):
            sp = span.Span(x[0] for x in g)
            s = str(sp)
            x = obj[sp[0][0]]
                
            if x is None:
                self("[%s]: %s" % (s, nds))
            else:
                self("[%s]:" % (s,))
                x.pprint(p=p, **kwArgs)
    
    def no_newline(self, obj):
        """
        Like a __call__ call, but doesn't include a return at the end.
        """
        
        if self.label is not None:
            print("%s%s:" % (self._sp, self.label), file=self.stream)
            self.label = None
            self._bumpIndent(1)
        
        self.stream.write("%s%s " % (self._sp, obj))
    
    def pair_iterator(self, it, label=None, **kwArgs):
        """
        Pretty-print a mapping (expressed as an iterator of (key, value) pairs)
        whose values do not have their own pprint methods. Note the key
        ordering is up to the iterator or generator providing the pairs.
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        f = (repr if kwArgs.get('useRepr', False) else str)
        
        for k, obj in it:
            self("%s: %s" % (repr(k), f(obj)))
    
    def pair_iterator_deep(self, it, label=None, **kwArgs):
        """
        Pretty-print a mapping (expressed as an iterator of (key, object)
        pairs), where the objects have their own pprint methods. Note the key
        ordering is up to the iterator or generator providing the pairs.
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        p = type(self)(**self._makeDict(1 if self.label is None else 2))
        
        for k, obj in it:
            if obj is not None:
                self("%s:" % (repr(k),))
                obj.pprint(p=p, **kwArgs)
            else:
                self("%s: %s" % (repr(k), self.noDataString))
    
    def sequence(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are not shown.
        
        >>> p = PP(label="Top label")
        >>> p.sequence(['a', 15, {14: -1}], label="Bottom label 1", useRepr=True)
        Top label:
          Bottom label 1:
            'a'
            15
            {14: -1}
        >>> p.sequence([-1, 'zed'], label="Bottom label 2", useRepr=True)
          Bottom label 2:
            -1
            'zed'
        
        >>> p = PP()
        >>> p.sequence('abc')
        a
        b
        c
        >>> p.sequence('abc', combiner = ", ")
        a, b, c
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        sr = (repr if kwArgs.get('useRepr', False) else str)
        combiner = kwArgs.get('combiner', None)
        
        if combiner is None:
            for obj in seq:
                self(sr(obj))
        
        else:
            self(sr(combiner.join(seq)))
    
    def sequence_deep(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are not shown.
        
        >>> p = PP(label="Top label", noDataString="Vast emptiness...")
        >>> p.sequence_deep([X(4), None, X(2)], label="Bottom label")
        Top label:
          Bottom label:
            The list [0, 1, 2, 3]
            Vast emptiness...
            The list [0, 1]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        d = self.__dict__
        nds = self.noDataString
        
        for obj in seq:
            if obj is not None:
                obj.pprint(p=self, **kwArgs)
            else:
                self(nds)
    
    def sequence_deep_tag(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are also shown.
        
        >>> p = PP(label="Top label")
        >>> p.sequence_deep_tag([X(4), None, X(2)])
        Top label:
          0:
            The list [0, 1, 2, 3]
          1: (no data)
          2:
            The list [0, 1]
        >>> p = PP(label="Top label")
        >>> p.sequence_deep_tag([X(4), None, X(2)], label="Bottom label")
        Top label:
          Bottom label:
            0:
              The list [0, 1, 2, 3]
            1: (no data)
            2:
              The list [0, 1]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        p = type(self)(**self._makeDict(1 if self.label is None else 2))
        nds = self.noDataString
        
        for i, obj in enumerate(seq):
            if obj is not None:
                self("%d:" % (i,))
                obj.pprint(p=p, **kwArgs)
            else:
                self("%d: %s" % (i, nds))
    
    def sequence_deep_tag_smart(self, seq, isMultilineFunc, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are also shown. Before each
        object's pprint method is called, the isMultilineFunc predicate
        function is called on that object. If the return value is true, the
        display is as for sequence_deep_tag (i.e. the index on one line and the
        object's pprint output indented below it). If the return value is
        false, the index and pprint output appear on the same line.
        
        >>> p = PP(label="Top label", noDataString="(nada)")
        >>> p.sequence_deep_tag_smart([X(4), None, X(2)], lambda x: True, label="Bottom label 1")
        Top label:
          Bottom label 1:
            0:
              The list [0, 1, 2, 3]
            1: (nada)
            2:
              The list [0, 1]
        >>> p.sequence_deep_tag_smart([X(4), None, X(2)], lambda x: False, label="Bottom label 2")
          Bottom label 2:
            0: The list [0, 1, 2, 3]
            1: (nada)
            2: The list [0, 1]
        >>> p = PP(label="Top label 2", noDataString="(nada)")
        >>> p.sequence_deep_tag_smart([X(4), None, X(2)], lambda x: True)
        Top label 2:
          0:
            The list [0, 1, 2, 3]
          1: (nada)
          2:
            The list [0, 1]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        pNormal = type(self)(**self._makeDict(1 if self.label is None else 2))
        pCompact = type(self)(**self._makeDict(-1))
        nds = self.noDataString
        
        for i, obj in enumerate(seq):
            if obj is None:
                self("%d: %s" % (i, nds))
            elif isMultilineFunc(obj):
                self("%d:" % (i,))
                obj.pprint(p=pNormal, **kwArgs)
            else:
                self.no_newline("%d:" % (i,))
                obj.pprint(p=pCompact, **kwArgs)
    
    def sequence_grouped(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence where adjacent equal elements are grouped.
        
        >>> p = PP(label="Top label", noDataString="--void--")
        >>> v = [1, 1, 1, 3, None, None, "fred", "fred", "fred"]
        >>> p.sequence_grouped(v, label="Bottom label")
        Top label:
          Bottom label:
            [0-2]: 1
            [3]: 3
            [4-5]: --void--
            [6-8]: fred
        >>> p.sequence_grouped(v, label="Bottom label", useRepr=True)
          Bottom label:
            [0-2]: 1
            [3]: 3
            [4-5]: --void--
            [6-8]: 'fred'
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        currIndex = 0
        nds = self.noDataString
        f = (repr if kwArgs.get('useRepr', False) else str)
        
        for k, g in itertools.groupby(seq):
            count = len(list(g))  # it staggers me there's no itertools function for len(iterator)
            k = (nds if k is None else f(k))
            
            if count == 1:
                self("[%d]: %s" % (currIndex, k))
            else:
                self("[%d-%d]: %s" % (currIndex, currIndex + count - 1, k))
            
            currIndex += count
    
    def sequence_grouped_deep(self, seq, label=None, **kwArgs):
        """
        Pretty-print a deep sequence where adjacent equal elements are grouped.
        
        Note the objects in seq should either be None or else all responsive to
        the same __eq__ method.
        
        >>> p = PP(label="Top label")
        >>> v = [X(4), X(4), X(4), None, None, X(3), X(4), X(4)]
        >>> p.sequence_grouped_deep(v, label="Bottom label")
        Top label:
          Bottom label:
            [0-2]:
              The list [0, 1, 2, 3]
            [3-4]: (no data)
            [5]:
              The list [0, 1, 2]
            [6-7]:
              The list [0, 1, 2, 3]
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        p = type(self)(**self._makeDict(1 if self.label is None else 2))
        nds = self.noDataString
        currIndex = 0
        
        for k, g in itertools.groupby(seq):
            count = len(list(g))  # see comment in sequence_grouped
            
            if count == 1:
                if k is None:
                    self("[%d]: %s" % (currIndex, nds))
                else:
                    self("[%d]:" % (currIndex,))
                    seq[currIndex].pprint(p=p, **kwArgs)
            else:
                if k is None:
                    self("[%d-%d]: %s" % (currIndex, currIndex + count - 1, nds))
                else:
                    self("[%d-%d]:" % (currIndex, currIndex + count - 1))
                    seq[currIndex].pprint(p=p, **kwArgs)
            
            currIndex += count
    
    def sequence_tag(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are also shown.
        
        >>> p = PP(label="Top label")
        >>> p.sequence_tag(['a', 15, {14: -1}], label="Bottom label 1", useRepr=True)
        Top label:
          Bottom label 1:
            0: 'a'
            1: 15
            2: {14: -1}
        >>> p.sequence_tag([-1, 'zed'], label="Bottom label 2", useRepr=True)
          Bottom label 2:
            0: -1
            1: 'zed'
        """
        
        if label:
            self(_encolon(label))
            self = self.makeIndentedPP()
        
        f = (repr if kwArgs.get('useRepr', False) else str)
        
        for i, obj in enumerate(seq):
            self("%d: %s" % (i, f(obj)))
    
    def sequence_tag_long(self, seq, label=None, **kwArgs):
        """
        Pretty-print a sequence (e.g. a list) whose values do not have their
        own pprint methods. The list indices are shown for the entry at the
        start of each line.
        
                  1111111111222222222233333333334444444444
        01234567890123456789012345678901234567890123456789
        >>> PP(maxWidth=50).sequence_tag_long(list(range(20, 150)))
        [0] 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34
        [15] 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49
        [30] 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64
        [45] 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79
        [60] 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94
        [75] 95 96 97 98 99 100 101 102 103 104 105 106
        [87] 107 108 109 110 111 112 113 114 115 116 117
        [98] 118 119 120 121 122 123 124 125 126 127 128
        [109] 129 130 131 132 133 134 135 136 137 138 139
        [120] 140 141 142 143 144 145 146 147 148 149
        >>> PP(maxWidth=50).sequence_tag_long(list(range(20, 150)), label="The values")
        The values:
          [0] 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34
          [15] 35 36 37 38 39 40 41 42 43 44 45 46 47 48
          [29] 49 50 51 52 53 54 55 56 57 58 59 60 61 62
          [43] 63 64 65 66 67 68 69 70 71 72 73 74 75 76
          [57] 77 78 79 80 81 82 83 84 85 86 87 88 89 90
          [71] 91 92 93 94 95 96 97 98 99 100 101 102 103
          [84] 104 105 106 107 108 109 110 111 112 113 114
          [95] 115 116 117 118 119 120 121 122 123 124 125
          [106] 126 127 128 129 130 131 132 133 134 135
          [116] 136 137 138 139 140 141 142 143 144 145
          [126] 146 147 148 149
        """
        
        if self.maxWidth is None:
            self.simple(seq, label, **kwArgs)
        
        else:
            if label:
                self(_encolon(label))
                self = self.makeIndentedPP()
            
            sv = []
            posn = self.indent
            i = 0
            f = (repr if kwArgs.get('useRepr', False) else str)
            
            while i < len(seq):
                obj = seq[i]
                
                if posn == self.indent:
                    s = "[%d]" % (i,)
                    sv.append(s)
                    posn += len(s)
                    thisLineStart = i
                
                s = " %s" % (f(obj),)
                
                if posn + len(s) > self.maxWidth:
                    # need to end this line and start a new one
                    if i == thisLineStart:
                        raise ValueError("maxWidth too narrow for even one entry!")
                    
                    sv.append(" " * (self.maxWidth - posn + 1))
                    posn = self.indent
                
                else:
                    sv.append(s)
                    posn += len(s)
                    i += 1
            
            self(''.join(sv))  # maxWidth will magically break where we need it to
    
    def setlike(self, obj, label=None, **kwArgs):
        """
        Pretty-prints the set-like object. There are no guarantees about the
        order in which the items of the setlike object are displayed.
        
        >>> PP().setlike(set([1, 19, 50]), label="A set-like object")
        A set-like object:
          1
          50
          19
        """
        
        self.sequence(iter(obj), label=label, **kwArgs)
    
    def setlike_deep(self, obj, label=None, **kwArgs):
        """
        Pretty-prints the set-like object, whose elements are themselves shown
        via their own pprint() methods. There are no guarantees about the order
        in which the items of the setlike object are displayed.
        
        >>> PP().setlike_deep(set([X(3), X(5), X(2)]), label="A deep set-like object")
        A deep set-like object:
          The list [0, 1, 2]
          The list [0, 1]
          The list [0, 1, 2, 3, 4]
        """
        
        self.sequence_deep(iter(obj), label=label, **kwArgs)
    
    def simple(self, obj, label=None, **kwArgs):
        """
        Displays a simple one-line value. If a label is specified, and a
        maxWidth, and if the total line would be larger than the maxWidth, then
        the label is printed on a separate line and the output is indented one
        level.
        
        >>> PP().simple(123)
        123
        >>> PP().simple(123, "Value")
        Value: 123
        >>> PP().simple(None)
        (no data)
        >>> PP().simple(None, "x")
        x: (no data)
        >>> PP().simple('chicken', 'Dinner')
        Dinner: chicken
        >>> PP().simple('chicken', 'Dinner', useRepr=True)
        Dinner: 'chicken'
        >>> PP(maxWidth=50).simple(list(range(5)), "A list")
        A list: [0, 1, 2, 3, 4]
        >>> PP(maxWidth=50).simple(list(range(50)), "A list")
        A list:
          [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
          14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
          26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
          38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]
        
        >>> PP(maxWidth=50).simple(list(range(50)), "A list", multilineExtraIndent=0)
        A list: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
                33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
                43, 44, 45, 46, 47, 48, 49]
        
        >>> PP(maxWidth=50).simple(list(range(50)), "A list", multilineExtraIndent=1)
        A list: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                 13, 14, 15, 16, 17, 18, 19, 20, 21, 22,
                 23, 24, 25, 26, 27, 28, 29, 30, 31, 32,
                 33, 34, 35, 36, 37, 38, 39, 40, 41, 42,
                 43, 44, 45, 46, 47, 48, 49]
        
        >>> PP(indent=4, maxWidth=50).simple(list(range(50)), "A list", multilineExtraIndent=0)
            A list: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                    12, 13, 14, 15, 16, 17, 18, 19, 20,
                    21, 22, 23, 24, 25, 26, 27, 28, 29,
                    30, 31, 32, 33, 34, 35, 36, 37, 38,
                    39, 40, 41, 42, 43, 44, 45, 46, 47,
                    48, 49]
        
        >>> PP(indent=4, maxWidth=50).simple(list(range(50)), "A list", multilineExtraIndent=1)
            A list: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                     12, 13, 14, 15, 16, 17, 18, 19, 20,
                     21, 22, 23, 24, 25, 26, 27, 28, 29,
                     30, 31, 32, 33, 34, 35, 36, 37, 38,
                     39, 40, 41, 42, 43, 44, 45, 46, 47,
                     48, 49]
        
        >>> PP().simple("Gl\xF6gg")
        Glögg
        
        >>> PP().simple("Gl\xF6gg", useRepr=True)
        'Glögg'
        """
        
        s = self._ndc(obj, **kwArgs)
        
        if label is None:
            self(s)
        
        else:
            label = _encolon(label)
            
            if self.maxWidth is None:
                self("%s %s" % (label, s))
            
            else:
                totalLen = len(self._sp) + len(label) + 1 + len(s)
                
                if totalLen <= self.maxWidth:
                    self("%s %s" % (label, s))
                
                else:
                    multilineExtraIndent = kwArgs.get('multilineExtraIndent', None)
                    
                    if multilineExtraIndent is not None:
                        multilineExtraIndent += (len(label) + 1)
                        self("%s %s" % (label, s), extraSubsequentIndent=multilineExtraIndent)
                    
                    else:
                        self(label)
                        self.makeIndentedPP()(s)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    class X(object):
        def __init__(self, n):
            self.v = list(range(n))
        def __eq__(self, other): return self is other or (other is not None and self.v == other.v)
        def __ne__(self, other): return self is not other and (other is None or self.v != other.v)
        def __hash__(self): return hash(tuple(self.v))
        def pprint(self, **kwArgs):
            p = PP(**kwArgs)
            p("The list %s" % (self.v,))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
