#
# ttcomponentflags.py
#
# Copyright © 2009-2011, 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for component flags in a composite TrueType glyph.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class TTComponentFlags(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing flags for a single component of a composite glyph.
    Note that these are the flags as seen in raw binary TrueType data, and are
    principally used for packing and unpacking the binary data. The actual
    flags used by Python objects are slightly refined from these, and can be
    seen in the TTComponent class.
    
    >>> _testingValues[0].pprint()
    
    >>> _testingValues[1].pprint()
    Round XY to grid
    
    >>> _testingValues[2].pprint()
    Args 1 and 2 are words
    Round XY to grid
    More components follow
    Has 2x2 scale matrix
    Has hints
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        loggername = "ttcomponentflags")
    
    maskSorted = (
      'argsAreWords', 'argsAreXYValues', 'roundToGrid', 'hasSimpleScale',
      'moreComponents', 'hasXYScale', 'hasMatrix', 'hasHints', 'useMyMetrics',
      'overlapCompound', 'scaledComponentOffset', 'unscaledComponentOffset')
    
    maskSpec = dict(
        argsAreWords = dict(
            mask_isbool = True,
            mask_label = "Args 1 and 2 are words",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),
        
        argsAreXYValues = dict(
            mask_isbool = True,
            mask_label = "Args 1 and 2 are XY values",
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True),
        
        roundToGrid = dict(
            mask_isbool = True,
            mask_label = "Round XY to grid",
            mask_rightmostbitindex = 2,
            mask_showonlyiftrue = True),
        
        hasSimpleScale = dict(
            mask_isbool = True,
            mask_label = "Has simple XY scale",
            mask_rightmostbitindex = 3,
            mask_showonlyiftrue = True),
        
        obsoleteBit4 = dict(
            mask_isbool = True,
            mask_label = "(obsolete bit 4)",
            mask_rightmostbitindex = 4,
            mask_showonlyiftrue = True),

        moreComponents = dict(
            mask_isbool = True,
            mask_label = "More components follow",
            mask_rightmostbitindex = 5,
            mask_showonlyiftrue = True),
        
        hasXYScale = dict(
            mask_isbool = True,
            mask_label = "Has separate XY scales",
            mask_rightmostbitindex = 6,
            mask_showonlyiftrue = True),
        
        hasMatrix = dict(
            mask_isbool = True,
            mask_label = "Has 2x2 scale matrix",
            mask_rightmostbitindex = 7,
            mask_showonlyiftrue = True),
        
        hasHints = dict(
            mask_isbool = True,
            mask_label = "Has hints",
            mask_rightmostbitindex = 8,
            mask_showonlyiftrue = True),
        
        useMyMetrics = dict(
            mask_isbool = True,
            mask_label = "Use my metrics",
            mask_rightmostbitindex = 9,
            mask_showonlyiftrue = True),
        
        overlapCompound = dict(
            mask_isbool = True,
            mask_label = "Contours overlap",
            mask_rightmostbitindex = 10,
            mask_showonlyiftrue = True),
        
        scaledComponentOffset = dict(
            mask_isbool = True,
            mask_label = "Scaled offsets (Apple)",
            mask_rightmostbitindex = 11,
            mask_showonlyiftrue = True),
        
        unscaledComponentOffset = dict(
            mask_isbool = True,
            mask_label = "Unscaled offsets (Microsoft)",
            mask_rightmostbitindex = 12,
            mask_showonlyiftrue = True),
        
        unusedBit13 = dict(
            mask_isbool = True,
            mask_label = "Unused bit 13",
            mask_rightmostbitindex = 13,
            mask_showonlyiftrue = True),
        
        unusedBit14 = dict(
            mask_isbool = True,
            mask_label = "Unused bit 14",
            mask_rightmostbitindex = 14,
            mask_showonlyiftrue = True),
        
        unusedBit15 = dict(
            mask_isbool = True,
            mask_label = "Unused bit 15",
            mask_rightmostbitindex = 15,
            mask_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        TTComponentFlags(),
        TTComponentFlags(roundToGrid=True),
        TTComponentFlags(
          hasHints = True,
          hasMatrix = True,
          moreComponents = True,
          roundToGrid = True,
          argsAreWords = True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
