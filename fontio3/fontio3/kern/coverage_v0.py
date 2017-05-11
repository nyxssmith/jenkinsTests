#
# coverage_v0.py
#
# Copyright © 2010-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for coverage fields for version 0 kerning tables.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Coverage(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing coverage flags for version 0 kerning tables. These are
    simple objects with the following attributes:
    
        crossStream     A Boolean indicating whether the data in this subtable
                        are to be applied cross-stream (i.e. vertically for
                        horizontal text, and vice versa) or not. Default is
                        False.
        
        minimum         A Boolean indicating whether the data in this subtable
                        represent minimum values instead of kerning values. A
                        subtable with minimum values will usually be placed
                        last in the 'kern' table, and the minimum values can be
                        used to prevent over-kerning that might have arisen
                        based on cumulative effects from previous subtables.
                        Default is False.
                        
                        Note that minimum processing is deprecated, and is not
                        used any more. It is no longer present in the version 1
                        Coverage object (q.v.)
        
        override        A Boolean indicating whether the data in this subtable
                        should be treated as overrides or as normal cumulative
                        values. If True, then any kerning values successfully
                        looked up in this table will replace any existing
                        cumulative value, instead of being added to it. Default
                        is False.
        
        vertical        A Boolean indicating whether the data in this subtable
                        apply to vertical text or horizontal text. Default is
                        False (i.e. horizontal text is the default).
    
    >>> _testingValues[0].pprint()
    Vertical text: False
    
    >>> _testingValues[1].pprint()
    Vertical text: False
    Table has minimum data, not kerning data
    Kerning is cross-stream
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 1
    
    maskSpec = dict(
        vertical = dict(
            mask_initfunc = (lambda: False),
            mask_isantibool = True,
            mask_label = "Vertical text",
            mask_rightmostbitindex = 0),
        
        minimum = dict(
            mask_isbool = True,
            mask_label = "Table has minimum data, not kerning data",
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True),
        
        crossStream = dict(
            mask_isbool = True,
            mask_label = "Kerning is cross-stream",
            mask_rightmostbitindex = 2,
            mask_showonlyiftrue = True),
        
        override = dict(
            mask_isbool = True,
            mask_label = "Table values override, don't accumulate",
            mask_rightmostbitindex = 3,
            mask_showonlyiftrue = True))
    
    maskSorted = ('vertical', 'minimum', 'crossStream', 'override')
    format = 0

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
        Coverage(minimum=True, crossStream=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
