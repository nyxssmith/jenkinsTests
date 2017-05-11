#
# behavior.py
#
# Copyright © 2009-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'gasp' table Version 1 behavior masks.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Private Functions
#

def _validate(obj, **kwArgs):
    """
    Validate the mask. 
    
    Normally this would be completely handled by default validation routines,
    checking for reserved bits and whatnot, but for the specific case of v1
    Behaviors, we do a check for the case of only v0-level Behaviors set to
    True and issue an *error* if so...which we also wouldn't normally do, but
    because of a significant change in 'gasp' table handling in Windows 8.1
    DWrite, we want to flag it and make it easily noticeable. The reason is: in
    the newer DWrite, the state (on OR off!) of the v1 flags (GASP_SYMMETRIC_*)
    override the v0 flags. Thus if you have, for example, GASP_GRIDFIT (v0) set
    to True, but GASP_SYMMETRIC_GRIDFIT (v1) set to False, NO grid-fitting of
    any sort will occur, because the False state of GASP_SYMMETRIC_GRIDFIT
    overrides the True state of GASP_GRIDFIT.
    """
    
    logger = kwArgs['logger']

    if obj.gridFit and not obj.symmetricGridFit:
        logger.error((
          'V0992',
          (),
          "v0 Grid Fit flag (GASP_GRIDFIT) set without corresponding "
          "v1 Symmetric Grid Fit flag (GASP_SYMMETRIC_GRIDFIT)."))
    
    if obj.doGray and not obj.symmetricSmoothing:
        logger.error((
          'V0992',
          (),
          "v0 Smoothing flag (GASP_DOGRAY) set without corresponding "
          "v1 Symmetric Smoothing flag (GASP_SYMMETRIC_SMOOTHING)."))
          
    return True # they *are* valid settings...

# -----------------------------------------------------------------------------

#
# Classes
#

class Behavior(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects describing rasterizer behavior.
    
    >>> _testingValues[0].pprint()
    Grid-fit
    
    >>> _testingValues[1].pprint()
    Symmetric grid-fit
    Symmetric smoothing
    
    >>> utilities.hexdump(_testingValues[0].binaryString())
           0 | 0001                                     |..              |
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 000C                                     |..              |
    
    >>> utilities.hexdump(_testingValues[2].binaryString())
           0 | 0000                                     |..              |
    
    >>> fb = Behavior.frombytes
    >>> _testingValues[0] == fb(_testingValues[0].binaryString())
    True
    
    >>> _testingValues[1] == fb(_testingValues[1].binaryString())
    True
    
    >>> _testingValues[2] == fb(_testingValues[2].binaryString())
    True
    
    >>> logger = utilities.makeDoctestLogger("ValTest")
    >>> tmp = Behavior.fromvalidatednumber(8234, logger=logger)
    ValTest.behavior - WARNING - All reserved bits should be set to 0, but some are 1.
    
    Note that merging unequal Behaviors will raise a ValueError:
    
    >>> _testingValues[0].merged(_testingValues[1])
    Traceback (most recent call last):
      ...
    ValueError: Attempt to merge unequal values!
    """
    
    #
    # Class definition variables
    #

    maskByteLength = 2
    
    maskSorted = (
      'gridFit',
      'doGray',
      'symmetricGridFit',
      'symmetricSmoothing')
    
    maskControls = dict(
        loggername = "behavior",
        validatecode_notsettozero = 'E1000',
        validatefunc_partial = _validate)
    
    maskSpec = dict(
        gridFit = dict(
            mask_isbool = True,
            mask_label = "Grid-fit",
            mask_mergecheckequality = True,
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),
        
        doGray = dict(
            mask_isbool = True,
            mask_label = "Do gray",
            mask_mergecheckequality = True,
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True),
        
        symmetricGridFit = dict(
            mask_isbool = True,
            mask_label = "Symmetric grid-fit",
            mask_mergecheckequality = True,
            mask_rightmostbitindex = 2,
            mask_showonlyiftrue = True),
        
        symmetricSmoothing = dict(
            mask_isbool = True,
            mask_label = "Symmetric smoothing",
            mask_mergecheckequality = True,
            mask_rightmostbitindex = 3,
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
        Behavior(symmetricGridFit=True, symmetricSmoothing=True),
        Behavior())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
