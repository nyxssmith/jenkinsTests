#
# state.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for an entire state (one row in a state table).
"""

# System imports
import collections
import functools
import itertools

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.statetables import actioncell

# -----------------------------------------------------------------------------

#
# Classes
#

class _DD(collections.defaultdict):
    def __missing__(self, key):
        r = self[key] = actioncell.ActionCell()
        return r

class State(_DD, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows (states) in a state array. These are
    defaultdicts mapping class strings to ActionCell objects. The default
    factory function just creates an empty ActionCell (which has a newState of
    "Start of text" and an empty actions list). There is one attribute:
    
        name        A string with a name for the state. This string is used
                    to specify new states in the ActionCell, and is the key
                    in the higher-level StateDict object.
    
    >>> _testingValues[0]["f"].pprint()
    New state: Saw f
    Actions:
      Action #1:
        X-shift (FUnits): -25
      Action #2:
        No advance; glyph will be reprocessed
    
    >>> _testingValues[0]["q"].pprint()
    New state: Start of text
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda s: "Class %r" % (s,)),
        map_makefunc = (lambda s,*a,**k: type(s)(_DD, *a, **k)))
    
    attrSpec = dict(
        name = dict(
            attr_label = "State name"))
    
    attrSorted = ()
    
    #
    # Public methods
    #
    
    def iteractions(self):
        """
        Returns an iterator over all actions present in the entire StateDict.
        """
        
        it = (iter(obj.actions) for obj in self.values() if obj.actions)
        return itertools.chain.from_iterable(it)
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        return functools.reduce(set.union, (obj.marksUsed() for obj in self.values()))
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _av = actioncell._testingValues
    
    _testingValues = (
        State({"f": _av[0]}),)
    
    del _av

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
