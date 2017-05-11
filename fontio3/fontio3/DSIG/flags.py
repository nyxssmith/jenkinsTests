#
# flags.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'DSIG' table flags.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Flags(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing flags as contained in the 'DSIG' table header.
    
    >>> _testingValues[1].pprint()
    Counter-signatures disallowed: True

    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj = Flags.fromvalidatednumber(0x0009, logger=logger)
    test.flags - WARNING - All reserved bits should be set to 0, but some are 1.
    """
    
    #
    # Class definition variables
    #

    maskByteLength = 2
    
    maskControls = dict(
        loggername = "flags",
        validatecode_notsettozero = "V0197",
        )
    
    maskSorted = (
      'cannotBeResigned',
      )
    
    maskSpec = dict(
        cannotBeResigned = dict(
            mask_isbool = True,
            mask_label = "Counter-signatures disallowed",
            mask_rightmostbitindex = 0),
    )
        
        # all other bits are reserved

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
        Flags(cannotBeResigned=True),
        Flags.fromnumber(0x1234),
        )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
