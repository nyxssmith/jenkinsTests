#
# behavior_v0.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'gasp' table Version 0 behavior masks.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Behavior(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects describing rasterizer behavior.
    
    >>> _testingValues[0].pprint()
    Grid-fit
    
    >>> utilities.hexdump(_testingValues[0].binaryString())
           0 | 0001                                     |..              |
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 0000                                     |..              |
    
    >>> fb = Behavior.frombytes
    >>> _testingValues[0] == fb(_testingValues[0].binaryString())
    True
    
    >>> _testingValues[1] == fb(_testingValues[1].binaryString())
    True
    
    >>> _testingValues[1] == fb(_testingValues[1].binaryString())
    True
    
    >>> logger = utilities.makeDoctestLogger("ValTest")
    >>> tmp = Behavior.fromvalidatednumber(8, logger=logger)
    ValTest.behavior - WARNING - All reserved bits should be set to 0, but some are 1.
    """
    
    #
    # Class definition variables
    #

    maskByteLength = 2
    maskSorted = ('gridFit', 'doGray')
    
    maskControls = dict(
        loggername = "behavior",
        validatecode_notsettozero = 'E1000')
    
    maskSpec = dict(
        gridFit = dict(
            mask_isbool = True,
            mask_label = "Grid-fit",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),
        
        doGray = dict(
            mask_isbool = True,
            mask_label = "Do gray",
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Behavior(gridFit=True),
        Behavior())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
