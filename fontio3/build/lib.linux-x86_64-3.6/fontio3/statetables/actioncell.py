#
# actioncell.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support single cell entries in a state array.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class ActionCell(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single cell in a two-dimensional state array. These
    are simple objects with two attributes:
    
        newState    A string label representing the next state to be entered
                    after this cell is processed.
        
        actions     None if there are no actions, or else an ActionList object.
    
    >>> _testingValues[0].pprint()
    New state: Saw f
    Actions:
      Action #1:
        X-shift (FUnits): -25
      Action #2:
        No advance; glyph will be reprocessed
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "New state"),
        
        actions = dict(
            attr_followsprotocol = True,
            attr_label = "Actions",
            attr_showonlyiftrue = True))
            
    
    attrSorted = ('newState', 'actions')
    
    #
    # Public methods
    #
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        if self.actions:
            return self.actions.marksUsed()
        
        return set()
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.statetables import actionlist
    
    _av = actionlist._testingValues
    
    _testingValues = (
        ActionCell("Saw f", _av[2]),)
    
    del _av

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
