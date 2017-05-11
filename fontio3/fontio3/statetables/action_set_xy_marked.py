#
# action_set_xy_marked.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for actions which set a marked glyph's x and/or y coordinates to some
value.
"""

# System imports
import functools
import operator

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Action_Set_XY_Marked(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Actions that set a marked glyph's position in one or both axes. The
    coordinates are specified in FUnits, and there is no device table.
    
    Note that a value of None means to not set the coordinate; it will remain
    whatever it was.
    
    >>> print(Action_Set_XY_Marked(x=25, mark="First pushed"))
    Set x-position (FUnits) = 25, At glyph with mark = 'First pushed'
    
    >>> print(Action_Set_XY_Marked(y=0, mark='Push 1'))
    Set y-position (FUnits) = 0, At glyph with mark = 'Push 1'
    
    >>> print(Action_Set_XY_Marked(5, 5, 'zz'))
    Set x-position (FUnits) = 5, Set y-position (FUnits) = 5, At glyph with mark = 'zz'
    """
    
    #
    # Class definition variables
    #
    
    soifFunc = functools.partial(operator.is_not, None)
    
    attrSpec = dict(
        x = dict(
            attr_label = "Set x-position (FUnits)",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiffunc = soifFunc,
            attr_transformcounterpart = 'y'),
        
        y = dict(
            attr_label = "Set y-position (FUnits)",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiffunc = soifFunc,
            attr_transformcounterpart = 'x'),
        
        mark = dict(
            attr_label = "At glyph with mark",
            attr_strusesrepr = True))
    
    attrSorted = ('x', 'y', 'mark')
    del soifFunc
    kind = "set_xy_marked"
    
    #
    # Public methods
    #
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        return {self.mark}

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
