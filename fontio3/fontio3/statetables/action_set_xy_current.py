#
# action_set_xy_current.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for actions which set the current glyph's x and/or y coordinates to
some value.
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

class Action_Set_XY_Current(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Actions that set the current glyph's position in one or both axes. The
    coordinates are specified in FUnits, and there is no device table.
    
    Note that a value of None means to not set the coordinate; it will remain
    whatever it was.
    
    >>> print(Action_Set_XY_Current(), end='')
    
    >>> print(Action_Set_XY_Current(x=25))
    X-position (FUnits) = 25
    
    >>> print(Action_Set_XY_Current(y=0))
    Y-position (FUnits) = 0
    
    >>> print(Action_Set_XY_Current(5, 5))
    X-position (FUnits) = 5, Y-position (FUnits) = 5
    """
    
    #
    # Class definition variables
    #
    
    soifFunc = functools.partial(operator.is_not, None)
    
    attrSpec = dict(
        x = dict(
            attr_label = "X-position (FUnits)",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiffunc = soifFunc,
            attr_transformcounterpart = 'y'),
        
        y = dict(
            attr_label = "Y-position (FUnits)",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiffunc = soifFunc,
            attr_transformcounterpart = 'x'))
    
    del soifFunc
    
    kind = "set_xy_current"
    
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
