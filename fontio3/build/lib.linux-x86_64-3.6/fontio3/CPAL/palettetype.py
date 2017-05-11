#
# palettetype.py
#
# Copyright © 20015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for v1 CPAL paletteType masks.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class PaletteType(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects describing palette type.

    >>> _testingValues[0].pprint()
    Light Background

    >>> h = utilities.hexdumpString
    >>> print(h(_testingValues[0].binaryString()), end='')
           0 |0000 0001                                |....            |

    >>> print(h(_testingValues[1].binaryString()), end='')
           0 |0000 0000                                |....            |

    >>> fb = PaletteType.frombytes
    >>> _testingValues[0] == fb(_testingValues[0].binaryString())
    True

    >>> _testingValues[1] == fb(_testingValues[1].binaryString())
    True

    >>> _testingValues[1] == fb(_testingValues[1].binaryString())
    True

    >>> logger = utilities.makeDoctestLogger("test")
    >>> tmp = PaletteType.fromvalidatednumber(8, logger=logger)
    test.palettetype - WARNING - All reserved bits should be set to 0, but some are 1.
    """

    maskByteLength = 4
    maskSorted = ('lightBackground', 'darkBackground')

    maskControls = dict(
        loggername = "palettetype",
        validatecode_notsettozero = 'E1000')

    maskSpec = dict(
        lightBackground = dict(
            mask_isbool = True,
            mask_label = "Light Background",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),

        darkBackground = dict(
            mask_isbool = True,
            mask_label = "Dark Background",
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
        PaletteType(lightBackground=True),
        PaletteType())

def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

