#
# action_mark_current.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for actions which mark the current glyph with a name (which is used by
some later action).
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Action_Mark_Current(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Actions that mark the current glyph location with a label.
    
    >>> print(Action_Mark_Current())
    Mark current with label = 'mark'
    
    >>> print(Action_Mark_Current("fred"))
    Mark current with label = 'fred'
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markLabel = dict(
            attr_initfunc = (lambda: "mark"),
            attr_label = "Mark current with label",
            attr_strusesrepr = True))
    
    kind = "mark_current"
    
    #
    # Public methods
    #
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        return set()

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
