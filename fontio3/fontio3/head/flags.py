#
# flags.py
#
# Copyright © 2004-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'head' table flags.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Flags(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing font-wide flags as contained in the 'head' table.
    
    >>> _testingValues[2].pprint()
    Baseline is at y=0: False
    Left sidebearing is at x=0: False
    Glyph hints depend on PPEM: True
    PPEM forced to integral value: False
    Advance widths depend on PPEM: True
    Vertical baseline is at x=0: True
    Font requires layout for linguistically correct layout: False
    Font has default layout features: False
    Font requires reordering: True
    Font does rearrangement: False
    Font uses MicroType Lossless compression: False
    Converted font requiring compatible metrics: True
    Font optimized for ClearType: False
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj = Flags.fromvalidatednumber(0xC000, logger=logger)
    test.flags - WARNING - All reserved bits should be set to 0, but some are 1.
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        loggername = "flags",
        validatecode_notsettozero = "V0197")
    
    maskSorted = (
      'baselineAtY0',
      'sidebearingAtX0',
      'opticalScalingViaHints',
      'forcePPEMToInteger',
      'opticalAdvanceViaHints',
      'verticalBaselineAtX0',
      'layoutRequired',
      'hasDefaultLayoutFeatures',
      'requiresReordering',
      'requiresRearrangement',
      'isMicrotypeLossless',
      'isConverted',
      'isClearType')
    
    maskSpec = dict(
        baselineAtY0 = dict(
            mask_isbool = True,
            mask_label = "Baseline is at y=0",
            mask_rightmostbitindex = 0),
        
        sidebearingAtX0 = dict(
            mask_isbool = True,
            mask_label = "Left sidebearing is at x=0",
            mask_rightmostbitindex = 1),
        
        opticalScalingViaHints = dict(
            mask_isbool = True,
            mask_label = "Glyph hints depend on PPEM",
            mask_rightmostbitindex = 2),
        
        forcePPEMToInteger = dict(
            mask_isbool = True,
            mask_label = "PPEM forced to integral value",
            mask_rightmostbitindex = 3),
        
        opticalAdvanceViaHints = dict(
            mask_isbool = True,
            mask_label = "Advance widths depend on PPEM",
            mask_rightmostbitindex = 4),
        
        verticalBaselineAtX0 = dict(
            mask_isbool = True,
            mask_label = "Vertical baseline is at x=0",
            mask_rightmostbitindex = 5),
        
        # bit 6 is not used
        
        layoutRequired = dict(
            mask_isbool = True,
            mask_label = "Font requires layout for linguistically correct layout",
            mask_rightmostbitindex = 7),
        
        hasDefaultLayoutFeatures = dict(
            mask_isbool = True,
            mask_label = "Font has default layout features",
            mask_rightmostbitindex = 8),
        
        requiresReordering = dict(
            mask_isbool = True,
            mask_label = "Font requires reordering",
            mask_rightmostbitindex = 9),
        
        requiresRearrangement = dict(
            mask_isbool = True,
            mask_label = "Font does rearrangement",
            mask_rightmostbitindex = 10),
        
        isMicrotypeLossless = dict(
            mask_isbool = True,
            mask_label = "Font uses MicroType Lossless compression",
            mask_rightmostbitindex = 11),
        
        isConverted = dict(
            mask_isbool = True,
            mask_label = "Converted font requiring compatible metrics",
            mask_rightmostbitindex = 12),
        
        isClearType = dict(
            mask_isbool = True,
            mask_label = "Font optimized for ClearType",
            mask_rightmostbitindex = 13))
        
        # bits 14 and 15 are not used

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Flags(),
        Flags(baselineAtY0=True, sidebearingAtX0=True, isClearType=True),
        Flags.fromnumber(0x1234))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
