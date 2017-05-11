#
# action_shift_xy_marked.py
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

class Action_Shift_XY_Marked(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Actions that shift the current glyph by some amount in X and/or Y. The
    shift distances are specified in FUnits, and there is no device table.
    
    >>> print(Action_Shift_XY_Marked(x=25, mark="First pushed"))
    X-shift (FUnits) = 25, At glyph with mark = 'First pushed'
    
    >>> print(Action_Shift_XY_Marked(y=-50, mark="Push 1"))
    Y-shift (FUnits) = -50, At glyph with mark = 'Push 1'
    
    >>> print(Action_Shift_XY_Marked(5, 5, 'zz'))
    X-shift (FUnits) = 5, Y-shift (FUnits) = 5, At glyph with mark = 'zz'
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
            attr_transformcounterpart = 'x'),
        
        mark = dict(
            attr_label = "At glyph with mark",
            attr_strusesrepr = True))
    
    attrSorted = ('x', 'y', 'mark')
    kind = "shift_xy_marked"
    
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
