#
# historygroup.py
#
# Copyright © 2008, 2011, 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for unordered collections of HistoryEntry-class objects.
"""

# Other imports
from fontio3.hints.history import historyentry
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Public functions
#

def combineDicts(d1, d2):
    """
    Combines d2 into d1, given input dicts whose values are either None or
    HistoryGroup objects.
    
    >>> vHG = [HistoryGroup.fromargs(_makeFakeHistoryEntry_push("Fred", 19, i)) for i in range(4, 8)]
    >>> d1 = {10: vHG[0], 14: vHG[1], 16: None}
    >>> d2 = {10: None, 14: vHG[2], 16: vHG[3]}
    >>> combineDicts(d1, d2)
    >>> pp.PP().mapping_deep_smart(d1, lambda x: len(x) > 1)
    10: Extra index 4 in PUSH opcode index 19 in Fred
    14:
      Extra index 5 in PUSH opcode index 19 in Fred
      Extra index 6 in PUSH opcode index 19 in Fred
    16: Extra index 7 in PUSH opcode index 19 in Fred
    """
    
    for k, h2 in d2.items():
        if h2 is not None:
            h1 = d1.get(k, None)
            
            if h1 is None:
                d1[k] = h2
            elif h1 is not h2:
                try:
                    h1.combine(h2)
                except AttributeError:
                    d1[k] = HistoryGroup.fromargs(h1)
                    d1[k].combine(h2)

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryGroup(set):
    """
    Objects representing unordered collections of HistoryEntry objects.
    HistoryGroup objects will never contain other HistoryGroup objects; they
    are flat collections.

    Ambiguities are resolved by quints, so two equal but distinct HistoryEntry
    objects will not both be added to a HistoryGroup.
    
    HistoryGroup objects contain HistoryEntry objects, which are immutable, so
    HistoryGroups are direct subclasses of Python's set type.
    """
    
    #
    # Class methods
    #
    
    @classmethod
    def fromargs(cls, *args):
        """
        This classmethod is useful as a constructor when the caller has
        individual arguments and doesn't want to have to create a list just to
        pass in an iterable to __init__.
        
        >>> he1 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> he2 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> HistoryGroup.fromargs(he1, he2).pprint()
        Extra index 5 in PUSH opcode index 12 in Fred
        Implicit zero for RP2 used at opcode index 9 in George
        """
        
        return cls(args)
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable=None):
        """
        Initializes the group with the specified arguments, each of which
        should be a descendent of HistoryEntry. Note that any groups in the
        args are pulled apart before being added to this new group. This means
        a group will never contain other groups, only their contents.
        
        >>> he1 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> he2 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> g1 = HistoryGroup([he1, he2])
        >>> g1.pprint()
        Extra index 5 in PUSH opcode index 12 in Fred
        Implicit zero for RP2 used at opcode index 9 in George
        >>> he3 = _makeFakeHistoryEntry_storage("George", 18, 20)
        >>> g2 = HistoryGroup([he3, g1])
        >>> g2.pprint()
        Extra index 5 in PUSH opcode index 12 in Fred
        Implicit zero for RP2 used at opcode index 9 in George
        Implicit zero for storage location 20 used at opcode index 18 in George
        """
        
        if iterable is not None:
            for entry in iterable:
                self.combine(entry)
    
    #
    # Special methods
    #
    
    def __copy__(self):
        r = HistoryGroup()
        r.update(self)  # all HE objs are immutable
        return r
    
    def __deepcopy__(self, memo=None):
        r = HistoryGroup()
        r.update(self)  # all HE objs are immutable
        return r
    
    #
    # Public methods
    #
    
    def iterSorted(self):
        """
        Returns a generator over the HistoryEntry objects in canonical order.
        
        >>> he1 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> he2 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> g = HistoryGroup.fromargs(he1, he2)
        >>> [obj.kind for obj in g.iterSorted()]
        ['push', 'refPt']
        """
        
        return iter(sorted(self, key=historyentry.HistoryEntry.quint))
    
    def combine(self, other):
        """
        Combines other (which may be either a single HistoryEntry-class object,
        or else a HistoryGroup) into self.
        
        >>> he1 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> g1 = HistoryGroup.fromargs(he1)
        >>> he2 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> g2 = HistoryGroup.fromargs(he2)
        >>> he3 = _makeFakeHistoryEntry_storage("George", 18, 20)
        >>> g2.combine(he3)
        >>> g2.pprint()
        Implicit zero for RP2 used at opcode index 9 in George
        Implicit zero for storage location 20 used at opcode index 18 in George
        >>> g1.combine(g2)
        >>> g1.pprint()
        Extra index 5 in PUSH opcode index 12 in Fred
        Implicit zero for RP2 used at opcode index 9 in George
        Implicit zero for storage location 20 used at opcode index 18 in George
        """
        
        try:
            self.update(other)
        except TypeError:
            self.add(other)
    
    def merged(self, other): return HistoryGroup(self | other)
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> HistoryGroup().pprint()
        Empty collection of history entries
        >>> he1 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> he2 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> he3 = _makeFakeHistoryEntry_storage("George", 18, 20)
        >>> HistoryGroup.fromargs(he1, he2, he3).pprint()
        Extra index 5 in PUSH opcode index 12 in Fred
        Implicit zero for RP2 used at opcode index 9 in George
        Implicit zero for storage location 20 used at opcode index 18 in George
        """
        
        p = pp.PP(**kwArgs)
        
        if self:
            if len(self) == 1:
                p.deep(next(iter(self)))
            else:
                p.sequence_deep(self.iterSorted())
        
        else:
            p("Empty collection of history entries")
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Pretty-prints the difference in the two objects.
        
        >>> he11 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> he12 = _makeFakeHistoryEntry_push("Fred", 12, 6)
        >>> he2 = _makeFakeHistoryEntry_refPt("George", 9, 2)
        >>> he3 = _makeFakeHistoryEntry_storage("George", 18, 20)
        >>> g1 = HistoryGroup.fromargs(he11, he2, he3)
        >>> g2 = HistoryGroup.fromargs(he12, he2, he3)
        >>> f = utilities.debugStream()
        >>> g1.pprint_changes(None, stream=f)
        >>> v = f.getvalue().splitlines()
        >>> v = v[0:1] + sorted(v[1:])
        >>> for line in v:
        ...   print(line)
        All new records:
          Extra index 5 in PUSH opcode index 12 in Fred
          Implicit zero for RP2 used at opcode index 9 in George
          Implicit zero for storage location 20 used at opcode index 18 in George
        >>> f.close()
        
        >>> f = utilities.debugStream()
        >>> g1.pprint_changes(g2)
        Added records:
          Extra index 5 in PUSH opcode index 12 in Fred
        Deleted records:
          Extra index 6 in PUSH opcode index 12 in Fred
        """
        
        p = pp.PP(**kwArgs)
        
        if not prior:
            p.setlike_deep(self, label="All new records")
        else:
            p.diff_setlike_deep(self, prior)
    
    def quint(self):
        v = list(obj.quint() for obj in self)
        v.sort()
        return ('group', tuple(v))

# -----------------------------------------------------------------------------

#
# Debugging support code
#

if 0:
    def __________________(): pass

if __debug__:
    # Other imports
    from fontio3.hints.history import push, refpt, storage
    
    # Other imports
    class _Fake(object):
        def __init__(self, s): self.infoString = s
        
    def _makeFakeHintObj(infoString, fakeID=99):
        return (fakeID, _Fake(infoString))
    
    def _makeFakeHistoryEntry_push(infoString, PC, extra):
        return push.HistoryEntry_push(_makeFakeHintObj(infoString), PC, extra)
    
    def _makeFakeHistoryEntry_refPt(infoString, PC, which):
        return refpt.HistoryEntry_refPt(_makeFakeHintObj(infoString), PC, which)
    
    def _makeFakeHistoryEntry_storage(infoString, PC, which):
        return storage.HistoryEntry_storage(_makeFakeHintObj(infoString), PC, which)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

