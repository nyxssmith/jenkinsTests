#
# action_reprocess_current.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for actions which prevent advancing to the next glyph in the glyph
array.
"""

# Other imports
from fontio3.fontdata import minimalmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Action_Reprocess_Current(object, metaclass=minimalmeta.FontDataMetaclass):
    """
    Actions that tell the state engine to not advance to the next glyph after
    finishing all actions on this glyph. This translates into the "noAdvance"
    bit in AAT state flags.
    
    >>> print(Action_Reprocess_Current())
    No advance; glyph will be reprocessed
    
    >>> Action_Reprocess_Current().pprint()
    No advance; glyph will be reprocessed
    """
    
    #
    # Class definition variables
    #
    
    minSpec = dict(
        minimal_string = "No advance; glyph will be reprocessed")
    
    kind = "reprocess_current"
    
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
