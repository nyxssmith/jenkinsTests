#
# actionlist.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for lists of actions of various kinds.
"""

# System imports
import functools

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class ActionList(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Lists of actions of various kinds.
    
    >>> _testingValues[1].pprint()
    Action #1:
      Mark current with label: 'first mark'
    
    >>> _testingValues[2].pprint()
    Action #1:
      X-shift (FUnits): -25
    Action #2:
      No advance; glyph will be reprocessed
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Action #%d" % (i + 1,)))
    
    #
    # Public methods
    #
    
    def kinds(self):
        """
        Returns a set with all the 'kind' strings from all actions contained in
        the list.
        
        >>> sorted(_testingValues[2].kinds())
        ['reprocess_current', 'shift_xy_current']
        """
        
        return set(obj.kind for obj in self)
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        return functools.reduce(set.union, (obj.marksUsed() for obj in self))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    from fontio3.statetables import (
      action_mark_current,
      action_reprocess_current,
      action_shift_xy_current)
    
    _tv1 = [
      action_mark_current.Action_Mark_Current("first mark")]
    
    _tv2 = [
      action_shift_xy_current.Action_Shift_XY_Current(-25, 0),
      action_reprocess_current.Action_Reprocess_Current()]
    
    _testingValues = (
        ActionList(),
        ActionList(_tv1),
        ActionList(_tv2))
    
    del _tv1, _tv2

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
