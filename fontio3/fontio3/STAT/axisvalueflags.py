#
# axisvalueflags.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Axis Value flags.
"""

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class AxisValueFlags(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing Axis Value flags in the STAT table.

    >>> _testingValues[0].pprint()
    Older Sibling Font Attribute: False
    Elidable Axis Value Name: False
    >>> _testingValues[1].pprint()
    Older Sibling Font Attribute: True
    Elidable Axis Value Name: False
    >>> logger = utilities.makeDoctestLogger("test")
    >>> obj = AxisValueFlags.fromvalidatednumber(0x1234, logger=logger)
    test.axisvalueflags - WARNING - All reserved bits should be set to 0, but some are 1.
    """

    #
    # Class definition variables
    #

    maskByteLength = 2

    maskControls = dict(
        loggername = "axisvalueflags",
        validatecode_notsettozero = "V0197")

    maskSorted = (
      'olderSiblingFontAttribute',
      'elidableAxisValueName')

    maskSpec = dict(
        olderSiblingFontAttribute = dict(
            mask_isbool = True,
            mask_label = "Older Sibling Font Attribute",
            mask_rightmostbitindex = 0),

        elidableAxisValueName = dict(
            mask_isbool = True,
            mask_label = "Elidable Axis Value Name",
            mask_rightmostbitindex = 1))

        # bits 3 - 15 are not used

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = (
        AxisValueFlags(),
        AxisValueFlags(olderSiblingFontAttribute=True),
        AxisValueFlags(elidableAxisValueName=True),
        AxisValueFlags.fromnumber(0x1234))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
