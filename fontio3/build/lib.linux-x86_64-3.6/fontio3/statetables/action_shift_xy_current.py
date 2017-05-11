#
# action_shift_xy_current.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for actions which move the current glyph by some x and/or y
displacement.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Action_Shift_XY_Current(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Actions that shift the current glyph by some amount in X and/or Y. The
    shift distances are specified in FUnits, and there is no device table.
    
    >>> print(Action_Shift_XY_Current(), end='')
    
    >>> print(Action_Shift_XY_Current(x=25))
    X-shift (FUnits) = 25
    
    >>> print(Action_Shift_XY_Current(y=-50))
    Y-shift (FUnits) = -50
    
    >>> print(Action_Shift_XY_Current(5, 5))
    X-shift (FUnits) = 5, Y-shift (FUnits) = 5
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        x = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "X-shift (FUnits)",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'y'),
        
        y = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Y-shift (FUnits)",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'x'))
    
    kind = "shift_xy_current"
    
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
