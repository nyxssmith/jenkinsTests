#
# historylist.py
#
# Copyright © 2007-2009, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Package file for fontio3.hints.history package.
"""

# System imports
import itertools

# Other imports
from fontio3 import utilities
from fontio3.hints.history import historygroup
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryList(list):
    """
    HistoryList objects are the primary objects used by clients like HintsNew. They
    are sequences of HistoryEntry objects, representing how values were placed
    into some parallel list.
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
        """
        
        return cls(args)
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable=None):
        """
        Initializes the object with the HistoryEntry-class objects provided by
        the iterable.
        """
        
        if iterable is not None:
            self.extend(iterable)
    
    #
    # Special methods
    #
    
    def __copy__(self): return HistoryList(self)
    def __deepcopy__(self, memo=None): return HistoryList(self)
    
    #
    # Public methods
    #
    
    def combine(self, other):
        """
        Merges other into self. For entries that differ, a HistoryEntry_group
        is created and put into that location.
        
        >>> e_push1 = _makeFakeHistoryEntry_push("Fred", 12, 4)
        >>> e_push2 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> e_refPt = _makeFakeHistoryEntry_refPt("George", 15, 1)
        >>> h = HistoryList.fromargs(e_push1, e_refPt)
        >>> h2 = HistoryList.fromargs(e_push2, e_refPt)
        >>> h.combine(h2)
        >>> h.pprint()
        0:
          Extra index 4 in PUSH opcode index 12 in Fred
          Extra index 5 in PUSH opcode index 12 in Fred
        1: Implicit zero for RP1 used at opcode index 15 in George
        """
        
        if len(self) != len(other):
            raise utilities.MergeSyncFailure("Lengths of merged objects must match!")
        
        for i, entry1 in enumerate(self):
            entry2 = other[i]
            
            if (entry1 is not entry2) and (entry1 != entry2):
                self[i] = historygroup.HistoryGroup.fromargs(entry1, entry2)
    
    merge = combine
    
    def merged(self, other):
        """
        Returns a new HistoryList object for the two specified objects, where
        entries at the same index are merged into a single HistoryEntry_group
        object if they differ.
        """
        
        if len(self) != len(other):
            raise utilities.MergeSyncFailure("Lengths of merged objects must match!")
        
        def gen():
            for entry1, entry2 in zip(iter(self), iter(other)):
                if (entry1 is entry2) or (entry1 == entry2):
                    yield entry1
                else:
                    yield historygroup.HistoryGroup.fromargs(entry1, entry2)
        
        return HistoryList(gen())
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> e_push1 = _makeFakeHistoryEntry_push("Fred", 12, 4)
        >>> e_push2 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> e_refPt = _makeFakeHistoryEntry_refPt("George", 15, 1)
        >>> HistoryList.fromargs(e_push1, e_push2, e_refPt).pprint()
        0: Extra index 4 in PUSH opcode index 12 in Fred
        1: Extra index 5 in PUSH opcode index 12 in Fred
        2: Implicit zero for RP1 used at opcode index 15 in George
        """
        
        p = pp.PP(**kwArgs)
        f = lambda obj: isinstance(obj, historygroup.HistoryGroup)
        p.sequence_deep_tag_smart(self, f)
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Pretty-prints the difference between the two objects.
        
        >>> e_push1 = _makeFakeHistoryEntry_push("Fred", 12, 4)
        >>> e_push2 = _makeFakeHistoryEntry_push("Fred", 12, 5)
        >>> e_refPt = _makeFakeHistoryEntry_refPt("George", 15, 1)
        >>> h = HistoryList.fromargs(e_push1, e_push2)
        >>> h2 = h.__copy__()
        >>> h2.append(e_refPt)
        >>> del h2[0]
        >>> h2.pprint_changes(h, label="Overall changes")
        Overall changes:
          Appended at end:
            Implicit zero for RP1 used at opcode index 15 in George
          Deleted from the start:
            Extra index 4 in PUSH opcode index 12 in Fred
        """
        
        p = pp.PP(**kwArgs)
        
        if not prior:
            f = lambda obj: isinstance(obj, historygroup.HistoryGroup)
            p.sequence_deep_tag_smart(self, f)
        else:
            p.diff_sequence_deep(self, prior)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    # Other imports
    from fontio3.hints.history import push, refpt
    
    class _Fake(object):
        def __init__(self, s): self.infoString = s
        
    def _makeFakeHintObj(infoString, fakeID=99):
        return (fakeID, _Fake(infoString))
    
    def _makeFakeHistoryEntry_push(infoString, PC, extra):
        return push.HistoryEntry_push(_makeFakeHintObj(infoString), PC, extra)
    
    def _makeFakeHistoryEntry_refPt(infoString, PC, which):
        return refpt.HistoryEntry_refPt(_makeFakeHintObj(infoString), PC, which)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
