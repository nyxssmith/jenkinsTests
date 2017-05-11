#
# condition.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Condition Tables as found in GSUB v1.1 (OpenType 1.8) or later.
"""

# System imports
from collections import namedtuple
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

_C = namedtuple("_C", ["axisTag", "filterMin", "filterMax"])

class Condition(_C, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing Condition Tables. These are named tuples
    with three elements:
        [0] axisTag     4-character axis tag that the condition corresponds to
                        the fvar table's axisOrder

        [1] filterMin   minimum value on the axis to satisfy this condition

        [2] filterMax   maximum value on the axis to satisfy this condition
    """

    format = 1  # for now...if more are added, split into different files.

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureVariations Table object to the
        specified LinkedWriter.
        
        A single kwArg, axisOrder (representing the fvar table's axis Order),
        is required.
        
        >>> bs = _testingValues[0].binaryString(axisOrder=('wght',))
        Traceback (most recent call last):
            ...
        ValueError: tuple.index(x): x not in tuple
        
        >>> bs = _testingValues[1].binaryString(axisOrder=('wght',))
        >>> utilities.hexdump(bs)
               0 | 0001 0000 0010 4000                      |......@.        |
        """

        ao = kwArgs['axisOrder']
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", Condition.format)
        ai = ao.index(self[0])
        w.add("H", ai)                           # axisIndex
        w.add("h", int(round(self[1] * 16384)))  # filterMin - F2DOT14
        w.add("h", int(round(self[2] * 16384)))  # filterMax - F2DOT14

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Condition object from the specified walker,
        doing source validation. Requires one kwArg, 'axisOrder', which should
        be the axisOrder from the fvar table. This is used to expand the
        axisIndex into a 4-character tag.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = "0001 0000 1234 5678"
        >>> b = utilities.fromhex(s)
        >>> fvb = Condition.fromvalidatedbytes
        >>> obj = fvb(b, logger=logger, axisOrder=('wght', 'wdth'))
        test.condition - DEBUG - Walker has 8 remaining bytes.
        test.condition - INFO - AxisTag 'wght'
        test.condition - INFO - Min: 0.284424, Max: 1.351074

        >>> obj = fvb(b[0:4], logger=logger, axisOrder=('wght',))
        test.condition - DEBUG - Walker has 4 remaining bytes.
        test.condition - ERROR - Insufficient bytes.
        
        >>> s = "0005 0000 7890 1234"
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, logger=logger, axisOrder=('wght',))
        test.condition - DEBUG - Walker has 8 remaining bytes.
        test.condition - ERROR - Unknown Condition format 5; ignoring
        >>> obj is None
        True
        
        >>> s = "0001 0009 2345 6789"
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, logger=logger, axisOrder=('wght', 'wdth'))
        test.condition - DEBUG - Walker has 8 remaining bytes.
        test.condition - ERROR - AxisIndex 9 is out-of-range for the supplied axisOrder
        """

        logger = kwArgs.get('logger', None)

        if logger is None:
            logger = logging.getLogger()

        logger = logger.getChild("condition")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        fmt, ai, minRaw, maxRaw = w.unpack("2H2h")
        
        if fmt != Condition.format:
            logger.error((
              'Vxxxx',
              (fmt,),
              "Unknown Condition format %d; ignoring"))
            return None

        ao = kwArgs.get('axisOrder', ())
        if 0 <= ai < len(ao):
            axisTag = ao[ai]
            logger.info((
              'Vxxxx',
              (axisTag,),
              "AxisTag '%s'"))
        else:
            logger.error((
              'Vxxxx',
              (ai,),
              "AxisIndex %d is out-of-range for the supplied axisOrder"))
            return None

        filterMin = minRaw / 16384
        filterMax = maxRaw / 16384

        logger.info((
          'Vxxxx',
          (filterMin, filterMax),
          "Min: %02f, Max: %02f"))

        r = cls(axisTag=axisTag, filterMin=filterMin, filterMax=filterMax)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Condition object from the specified
        walker. Requires one kwArg, 'axisOrder', which should
        be the axisOrder from the fvar table. This is used to expand the
        axisIndex into a 4-character tag.
        
        Unknown formats are to be ignored (return None); should NOT raise an
        exception on these per spec.

        >>> s = "0001 0000 0A00 3456"
        >>> b = utilities.fromhex(s)
        >>> fb = Condition.frombytes
        >>> obj = fb(b, axisOrder=('wght',))
        >>> obj.axisTag
        'wght'
        >>> obj.filterMin
        0.15625
        >>> obj.filterMax
        0.8177490234375
        
        >>> s = "0005 0000 00A0 3456"  # unknown format
        >>> b = utilities.fromhex(s)
        >>> obj = fb(b, axisOrder=('wdth',))
        >>> obj is None
        True
        """

        fmt, ai, minRaw, maxRaw = w.unpack("2H2h")

        if fmt != Condition.format:
            return None

        axisTag = kwArgs['axisOrder'][ai]
        filterMin = minRaw / 16384
        filterMax = maxRaw / 16384

        r = cls(axisTag=axisTag, filterMin=filterMin, filterMax=filterMax)

        return r


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:

    _testingValues = (
        Condition(axisTag='', filterMin=0, filterMax=0),
        Condition(axisTag='wght', filterMin = 0.001, filterMax = 1.0),
        Condition(axisTag='wdth', filterMin = -1.0, filterMax = 1.0))
        

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
