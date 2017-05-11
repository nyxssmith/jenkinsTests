#
# macstyle.py
#
# Copyright © 2004-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the Mac style bits in the 'head' table.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class MacStyle(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing the Mac style bits in the 'head' table.
    
    >>> _testingValues[1].pprint(label="Mac Style")
    Mac Style: Bold Italic
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj = MacStyle.fromvalidatednumber(0x8000, logger=logger)
    test.macstyle - WARNING - All reserved bits should be set to 0, but some are 1.
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        combinedstringfunc = (lambda sv: (' '.join(sv) if sv else "Plain")),
        loggername = "macstyle",
        validatecode_notsettozero = "V0196")
    
    maskSorted = (
      'bold', 'italic', 'underline', 'outline', 'shadow', 'condensed',
      'extended')
    
    maskSpec = dict(
        bold = dict(
            mask_isbool = True,
            mask_label = "Bold",
            mask_rightmostbitindex = 0),
        
        italic = dict(
            mask_isbool = True,
            mask_label = "Italic",
            mask_rightmostbitindex = 1),
        
        underline = dict(
            mask_isbool = True,
            mask_label = "Underline",
            mask_rightmostbitindex = 2),
        
        outline = dict(
            mask_isbool = True,
            mask_label = "Outline",
            mask_rightmostbitindex = 3),
        
        shadow = dict(
            mask_isbool = True,
            mask_label = "Shadow",
            mask_rightmostbitindex = 4),
        
        condensed = dict(
            mask_isbool = True,
            mask_label = "Condensed",
            mask_rightmostbitindex = 5),
        
        extended = dict(
            mask_isbool = True,
            mask_label = "Extended",
            mask_rightmostbitindex = 6))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        MacStyle(),
        MacStyle(bold=True, italic=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
