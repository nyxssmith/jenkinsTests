#
# deltasetindexmap.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Delta Set Index Maps in the HVAR table.
"""

# System imports
from functools import partial
import logging
from math import ceil, floor, log2

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class DeltaSetIndexMap(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping glyph indices to (outerIndex, innerIndex) values.
    """

    #
    # Class definition variables
    #

    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_pprintlabelpresort = True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ValueMap object to the specified
        LinkedWriter.

        >>> obj = DeltaSetIndexMap({0: (0xFFFF, 0), 1: (0, 0xFFFF)})
        >>> utilities.hexdump(obj.binaryString())
               0 | 003F 0002 FFFF 0000  0000 FFFF           |.?..........    |

        >>> obj = DeltaSetIndexMap({0: (0, 117), 1: (3, 1)})
        >>> utilities.hexdump(obj.binaryString())
               0 | 0016 0002 0075 0181                      |.....u..        |

        >>> obj = DeltaSetIndexMap({0: (1, 1), 1: (0x2000, 2)})
        >>> utilities.hexdump(obj.binaryString())
               0 | 0031 0002 0000 0005  0000 8002           |.1..........    |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)

        else:
            stakeValue = w.stakeCurrent()

        outers, inners = zip(*self.values())
        innerBitCount = floor(log2(max(inners) or 1)) + 1

        entrySize = 1
        for o,i in self.values():
            v = ceil(floor(log2(o or 1) + 1) / 8)
            entrySize = max(entrySize, 2**v)

        entryFormat = ((entrySize - 1) << 4) | innerBitCount -1

        w.add("H", entryFormat)
        w.add("H", len(self))

        wFn = {1: partial(w.add, "B"),
               2: partial(w.add, "H"),
               3: partial(w.add, "T"),
               4: partial(w.add, "L")}.get(entrySize)
               
        for k, v in sorted(self.items()):
            entryVal = (v[0] << innerBitCount) | v[1]
            wFn(entryVal)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.

        kwArg 'logger' is required.

        # reciprocal of buildBinary test 1
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("00 3F 00 02 FF FF 00 00 00 00 FF FF")
        >>> b = utilities.fromhex(s)
        >>> obj = DeltaSetIndexMap.fromvalidatedbytes(b, logger=logger)
        test.deltasetindexmap - DEBUG - Walker has 12 remaining bytes.
        test.deltasetindexmap - DEBUG - entryFormat = 0x3F
        test.deltasetindexmap - DEBUG - mapCount = 2
        test.deltasetindexmap - DEBUG - innerBitCount = 16
        test.deltasetindexmap - DEBUG - mapEntrySize = 4 bytes
        test.deltasetindexmap - DEBUG - Entry 0 (65535, 0); rawData = 0xFFFF0000
        test.deltasetindexmap - DEBUG - Entry 1 (0, 65535); rawData = 0xFFFF

        # reciprocal of buildBinary test 2
        >>> b = utilities.fromhex("00 16 00 02 00 75 01 81")
        >>> obj = DeltaSetIndexMap.fromvalidatedbytes(b, logger=logger)
        test.deltasetindexmap - DEBUG - Walker has 8 remaining bytes.
        test.deltasetindexmap - DEBUG - entryFormat = 0x16
        test.deltasetindexmap - DEBUG - mapCount = 2
        test.deltasetindexmap - DEBUG - innerBitCount = 7
        test.deltasetindexmap - DEBUG - mapEntrySize = 2 bytes
        test.deltasetindexmap - DEBUG - Entry 0 (0, 117); rawData = 0x75
        test.deltasetindexmap - DEBUG - Entry 1 (3, 1); rawData = 0x181

        >>> s = ("00 14 00 02 1F 3B 1F 3C")
        >>> b = utilities.fromhex(s)
        >>> obj = DeltaSetIndexMap.fromvalidatedbytes(b, logger=logger)
        test.deltasetindexmap - DEBUG - Walker has 8 remaining bytes.
        test.deltasetindexmap - DEBUG - entryFormat = 0x14
        test.deltasetindexmap - DEBUG - mapCount = 2
        test.deltasetindexmap - DEBUG - innerBitCount = 5
        test.deltasetindexmap - DEBUG - mapEntrySize = 2 bytes
        test.deltasetindexmap - DEBUG - Entry 0 (249, 27); rawData = 0x1F3B
        test.deltasetindexmap - DEBUG - Entry 1 (249, 28); rawData = 0x1F3C

        >>> logger.logger.setLevel("WARNING")
        >>> s = ("FF F0 00 05 01 02 03 04 05")
        >>> b = utilities.fromhex(s)
        >>> obj = DeltaSetIndexMap.fromvalidatedbytes(b, logger=logger)
        test.deltasetindexmap - ERROR - Reserved bits in entryFormatMask are not set to zero
        test.deltasetindexmap - ERROR - Insufficient bytes.

        >>> obj = DeltaSetIndexMap.fromvalidatedbytes(b'AB', logger=logger)
        test.deltasetindexmap - ERROR - Insufficient bytes.
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('deltasetindexmap')
        else:
            logger = logger.getChild('deltasetindexmap')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            return None

        entryFormatRaw, mapCount = w.unpack("2H")

        logger.debug(('Vxxxx', (entryFormatRaw,), "entryFormat = 0x%X"))
        logger.debug(('Vxxxx', (mapCount,), "mapCount = %d"))

        innerBitCount = (entryFormatRaw & 0x000F) + 1
        mapEntrySize = ((entryFormatRaw & 0x0030) >> 4) + 1
        reserved = entryFormatRaw & 0xFFC0

        logger.debug(('Vxxxx', (innerBitCount,), "innerBitCount = %d"))
        logger.debug(('Vxxxx', (mapEntrySize,), "mapEntrySize = %d bytes"))

        if reserved != 0:
            logger.error((
              'V1099',
              (),
              "Reserved bits in entryFormatMask are not set to zero"))
            # return None?

        if w.length() < mapEntrySize * mapCount:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))
            return None

        entryFormat = {1: "B", 2: "H", 3: "T", 4: "L"}.get(mapEntrySize)

        d = {}
        for g in range(mapCount):
            rawEntry = w.unpack(entryFormat)
            outer = rawEntry >> innerBitCount
            inner = rawEntry & ((1 << innerBitCount) -1)
            logger.debug((
              'Vxxxx',
              (g, outer, inner, rawEntry),
              "Entry %d (%d, %d); rawData = 0x%X"))

            d[g] = (outer, inner)

        return cls(d)


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new DeltaSetIndexMap object from the specified walker.

        >>> s = ("00 14 00 02 1F 3B 1F 3C")
        >>> b = utilities.fromhex(s)
        >>> obj = DeltaSetIndexMap.frombytes(b)
        >>> obj.pprint()
        0: (249, 27)
        1: (249, 28)
        """

        entryFormatRaw, mapCount = w.unpack("2H")
        innerBitCount = (entryFormatRaw & 0x000F) + 1
        mapEntrySize = ((entryFormatRaw & 0x0030) >> 4) + 1
        reserved = entryFormatRaw & 0xFFC0
        entryFormat = {1: "B", 2: "H", 3: "T", 4: "L"}.get(mapEntrySize)

        d = {}
        for g in range(mapCount):
            rawEntry = w.unpack(entryFormat)
            d[g] = (rawEntry >> innerBitCount, rawEntry & ((1 << innerBitCount) -1))

        return cls(d)


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


