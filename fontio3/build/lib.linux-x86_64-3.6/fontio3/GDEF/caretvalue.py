#
# caretvalue.py
#
# Copyright © 2005-2012, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to ligature caret positioning.
"""

# System imports
import logging

# Other imports
from fontio3.GDEF import (caretvalue_coord,
                          caretvalue_device,
                          caretvalue_point,
                          caretvalue_variation)

# -----------------------------------------------------------------------------

#
# Constants
#

FD_NONVARIABLE = {1: caretvalue_coord.CaretValue_Coord,
                  2: caretvalue_point.CaretValue_Point,
                  3: caretvalue_device.CaretValue_Device}

FD_VARIABLE = dict(FD_NONVARIABLE)
FD_VARIABLE[3] = caretvalue_variation.CaretValue_Variation


# -----------------------------------------------------------------------------

#
# Functions
#

def CaretValue(w, **kwArgs):
    """
    Factory function to create one of the three (four) kinds of CaretValue.

    >>> b = utilities.fromhex("0001 0005")
    >>> w = walkerbit.StringWalker(b)
    >>> CaretValue(w)
    CaretValue_Coord(5)

    >>> b = utilities.fromhex("0002 0008")
    >>> w = walkerbit.StringWalker(b)
    >>> CaretValue(w)
    CaretValue_Point(8)

    >>> b = utilities.fromhex("0003 01F4 0006 000C  0011 0002 EF00 1200")
    >>> w = walkerbit.StringWalker(b)
    >>> obj = CaretValue(w)
    >>> int(obj), sorted(obj.deviceRecord.items())
    (500, [(12, -2), (13, -1), (16, 1), (17, 2)])
    >>> obj.deviceRecord.isVariable == False
    True

    >>> otcd = {(0,5): "FakeLivingDelta1"}
    >>> b = utilities.fromhex("0003 0010 0006 0000 0005 8000")
    >>> w = walkerbit.StringWalker(b)
    >>> CaretValue(w, otcommondeltas=otcd)
    CaretValue_Variation(16, variationRecord='FakeLivingDelta1')
    """
    
    format = w.unpack("H", advance=False)

    dfact = FD_VARIABLE if 'otcommondeltas' in kwArgs else FD_NONVARIABLE
    
    if format not in dfact:
        raise ValueError("Unknown CaretValue format: %d" % format)

    return dfact[format].fromwalker(w, **kwArgs)


def CaretValue_validated(w, **kwArgs):
    """
    Factory function to create one of the three (four) validated kinds of CaretValue.
    
    >>> logger = utilities.makeDoctestLogger('test')
    >>> w = walkerbit.StringWalker(b'AA')
    >>> CaretValue_validated(w, logger=logger)
    test.caretvalue - ERROR - Unknown format 0x4141.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild('caretvalue')
    
    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    format = w.unpack("H", advance=False)

    dfact = FD_VARIABLE if 'otcommondeltas' in kwArgs else FD_NONVARIABLE
    
    if format not in dfact:
        logger.error(('E4004', (format,), "Unknown format 0x%04X."))
        return None

    return dfact[format].fromvalidatedwalker(w, logger=logger, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    _testingValues = (
      caretvalue_coord._testingValues +
      caretvalue_point._testingValues +
      caretvalue_device._testingValues +
      caretvalue_variation._testingValues)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
