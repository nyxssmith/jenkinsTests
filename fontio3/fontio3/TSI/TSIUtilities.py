#
# TSIUtilities.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Functions
#

def stripComments(s, inComment=False):
    """
    Replaces comments with whitespace (of the same length, so offsets aren't
    interfered with).
    
    >>> s = "ab /* comment */cd"
    >>> print(s)
    ab /* comment */cd
    >>> print((stripComments(s)[0]))
    ab              cd
    
    If the caller knows that a comment state already holds, the inComment
    parameter can indicate this:
    
    >>> s = "def*/ ghi"
    >>> print(s)
    def*/ ghi
    >>> print((stripComments(s, True)[0]))
          ghi
    """
    
    ranges = []
    
    if inComment:
        state = 'inComment'
        first = 0
    
    else:
        state = 'ground'
        first = None
    
    for i, c in enumerate(s):
        if state == 'ground':
            if c == '/':
                first = i
                state = 'sawSlash'
        
        elif state == 'sawSlash':
            if c == '*':
                state = 'inComment'
            elif c != '/':
                state = 'ground'
        
        elif state == 'inComment':
            if c == '*':
                state = 'sawStar'
        
        elif state == 'sawStar':
            if c == '/':
                ranges.append((first, i))
                state = 'ground'
            
            elif c != '*':
                state = 'inComment'
    
    if state == 'inComment':
        ranges.append((first, len(s)))
    
    sv = list(s)
    
    for first, last in ranges:
        count = last - first + 1
        sv[first:last+1] = list(' ' * count)
    
    return ''.join(sv), (state == 'inComment')

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

_StSt = collections.namedtuple(
  "_StSt",
  ['start', 'stop'])

class StartStop(_StSt):
    """
    Pairs of (start, stop) string index values, used to delimit a particular
    kind of value in a hint.
    """
    
    def __repr__(self):
        return repr(tuple(self))
    
    def __str__(self):
        return str(tuple(self))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class LocInfo(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping StartStop objects to strings identifying kinds of fields.
    Note that the start and stop values should be for the full string.
    """
    
    mapSpec = dict(
        item_pprintlabelpresort = True)

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

