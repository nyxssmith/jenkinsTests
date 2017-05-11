#
# coverage_v1.py
#
# Copyright © 2010-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for coverage fields for version 1 kerning tables.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Coverage(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing coverage flags for version 1 kerning tables. These are
    simple objects with the following attributes:
    
        crossStream     A Boolean indicating whether the data in this subtable
                        are to be applied cross-stream (i.e. vertically for
                        horizontal text, and vice versa) or not. Default is
                        False.
        
        variation       A Boolean indicating whether the data in this subtable
                        apply to a specific variation tuple. This only applies
                        to TrueType variation fonts, and a value of True means
                        the tupleIndex associated with the subtable has
                        significance. Default is False
        
        vertical        A Boolean indicating whether the data in this subtable
                        apply to vertical text or horizontal text. Default is
                        False (i.e. horizontal text is the default).
    
    >>> _testingValues[0].pprint()
    Vertical text: False
    Cross-stream: False
    
    >>> _testingValues[1].pprint()
    Vertical text: True
    Cross-stream: False
    Variation kerning is present
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 1
    
    maskSpec = dict(
        vertical = dict(
            mask_isbool = True,
            mask_label = "Vertical text",
            mask_rightmostbitindex = 7),
        
        crossStream = dict(
            mask_isbool = True,
            mask_label = "Cross-stream",
            mask_rightmostbitindex = 6),
        
        variation = dict(
            mask_isbool = True,
            mask_label = "Variation kerning is present",
            mask_rightmostbitindex = 5,
            mask_showonlyiftrue = True))
    
    maskSorted = ('vertical', 'crossStream', 'variation')
    format = 1

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Coverage(),
        Coverage(vertical=True, variation=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
