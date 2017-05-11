#
# MVAR.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MVAR table.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.MVAR import valuemap
from fontio3.opentype import version as otversion
from fontio3.opentype import living_variations

# -----------------------------------------------------------------------------

#
# Private Constants
#

_V1_0_VALUE_RECORD_SIZE = 8


# -----------------------------------------------------------------------------

#
# Private methods
#

def _validate(obj, **kwArgs):
    """
    isValid() validation for the top-level MVAR
    """

    editor = kwArgs['editor']
    logger = kwArgs['logger']

    isOK = True

    # check regionAxisCounts of LivingDeltas are all same, and same as fvar
    ax_cnts = set([len(list(v)[0][0]) for v in list(obj.valueMap.values())])
    
    if len(obj.valueMap) == 0:
        axisCount = 0
    else:
        axisCount = list(ax_cnts)[0]
    
    if axisCount and len(ax_cnts) != 1:
        logger.error((
          'Vxxxx',
          (),
          "MVAR regionAxisCounts are not all the same for each ValueRecord"))

        return False

    if editor.reallyHas(b'fvar'):
        fvarTbl = editor.fvar
        fvarAxisCount = len(fvarTbl)
        if fvarAxisCount != axisCount:
            logger.error((
              'V1092',
              (axisCount, fvarAxisCount),
              "The MVAR regionAxisCount %d does not match the fvar axisCount %d"))
            isOK = False

        else:
            logger.info((
              'V1092',
              (),
              "The MVAR regionAxisCount matches the fvar axiscount"))

    else:
        logger.error((
          'V1092',
          (),
          "Cannot validate the MVAR regionAxisCount against the fvar "
          "axisCount because the fvar table is missing or damaged"))
        isOK = False

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

class MVAR(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing an MVAR table. These are simple objects that contain
    ValueRecords that in turn contain metric values.

    >>> l = utilities.makeDoctestLogger("MVAR")
    >>> e = utilities.fakeEditor(5)
    >>> obj = MVAR()
    >>> obj.isValid(editor=e, logger=l)
    MVAR - ERROR - Cannot validate the MVAR regionAxisCount against the fvar axisCount because the fvar table is missing or damaged
    MVAR.valueMap - WARNING - No Value Records defined!
    False

    >>> e.fvar = fvar.Fvar()
    >>> obj.isValid(editor=e, logger=l)
    MVAR - INFO - The MVAR regionAxisCount matches the fvar axiscount
    MVAR.valueMap - WARNING - No Value Records defined!
    True

    >>> lr1 = LivingRegion.fromdict({b'wght': (-1.0, -1.0, 0.0)})
    >>> ldm1 = LivingDeltasMember((lr1, -150))
    >>> ld1 = LivingDeltas({ldm1})
    >>> ivs = IVS({(0, 0): ld1})
    >>> vm = valuemap.ValueMap({'test': ld1})
    >>> obj = MVAR(valueMap=vm, axisCount=1)
    >>> obj.isValid(editor=e, logger=l)
    MVAR - ERROR - The MVAR regionAxisCount 1 does not match the fvar axisCount 0
    MVAR.valueMap - WARNING - 'test' is not a registered value tag.
    MVAR.valueMap - INFO - 1 Value Records.
    False
    """

    #
    # Class definition variables
    #

    objSpec = dict(
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = otversion.Version,
            attr_label = "Version"),

        valueMap = dict(
            attr_label = "Value Map",
            attr_followsprotocol = True,
            attr_initfunc = valuemap.ValueMap))

    attrSorted = ('version', 'valueMap')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MVAR object to the specified LinkedWriter.

        The following keyword arguments are recognized:

            axisOrder   an iterable of axis tags (e.g. fvar.axisOrder) (required).

        >>> lr1 = LivingRegion.fromdict({b'wght': (-1.0, -1.0, 0.0)})
        >>> lr2 = LivingRegion.fromdict({b'wght': (0.5, 0.75, 1.0)})
        >>> lr3 = LivingRegion.fromdict({b'wght': (0.0, 0.25, 0.5)})
        >>> ldm1 = LivingDeltasMember((lr1, -150))
        >>> ldm2 = LivingDeltasMember((lr2, 100))
        >>> ldm3 = LivingDeltasMember((lr1, 150))
        >>> ldm4 = LivingDeltasMember((lr3, -75))
        >>> ld1 = LivingDeltas({ldm1})
        >>> ld2 = LivingDeltas({ldm2, ldm3})
        >>> ld3 = LivingDeltas({ldm4})
        >>> ivs = IVS({(0, 0): ld1, (0, 1): ld2, (1, 0): ld3})
        >>> vm = valuemap.ValueMap({'test': ld1, 'foo ': ld2, 'bar ': ld3})
        >>> obj = MVAR(valueMap=vm, axisCount=2)
        >>> bs = obj.binaryString(axisOrder=(b'wght',))
        >>> len(bs)
        110

           0 | 0001 0000 0000 0008  0003 0024 6261 7220 |...........$bar |
          10 | 0002 0000 666F 6F20  0000 0000 7465 7374 |....foo ....test|
          20 | 0001 0000 0001 0000  0034 0003 0000 0014 |.........4......|
          30 | 0000 0021 0000 002B  0001 0001 0002 0000 |...!...+........|
          40 | 0002 0096 6400 0100  0100 0100 00FF 6A00 |....d.........j.|
          50 | 0100 0000 0100 01B5  0001 0003 C000 C000 |................|
          60 | 0000 0000 1000 2000  2000 3000 4000      |...... . .0.@.  |

        >>> obj = MVAR()
        >>> bs = obj.binaryString(axisOrder=None)
        >>> utilities.hexdump(bs)
               0 | 0001 0000 0000 0008  0000 0000           |............    |
        """

        axisOrder = kwArgs.pop('axisOrder')

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)

        else:
            stakeValue = w.stakeCurrent()

        self.version.buildBinary(w, **kwArgs)

        w.add("H", 0)  # OT 1.8.1
        w.add("H", _V1_0_VALUE_RECORD_SIZE)
        valueCount = len(self.valueMap)
        w.add("H", valueCount)

        if valueCount:
            ivsBsFn = living_variations.IVS.binaryStringFromDeltas
            deltas = self.gatheredLivingDeltas(**kwArgs)
            ivsBs, ldmap = ivsBsFn(deltas, axisOrder=axisOrder, **kwArgs)

            stake_IVS = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, stake_IVS)

            self.valueMap.buildBinary(w, ldmap=ldmap, **kwArgs)

            w.stakeCurrentWithValue(stake_IVS)
            w.addString(ivsBs)
            
        else:
            w.add("H", 0) # NULL offsetToIVS


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MVAR object from the specified walker, doing
        validation.

        The following keyword arguments are recognized:

            axisOrder   an iterable of axis tags (e.g. fvar.axisOrder) (required).

            logger      a logging.logger-compatible object

        >>> logger = utilities.makeDoctestLogger('test')
        >>> axorder=('wght',)
        >>> s = ("0001 0000 0001 0008  0003 0024 6261 7220"
        ...      "0002 0000 666F 6F20  0000 0000 7465 7374"
        ...      "0001 0000 0001 0000  0034 0003 0000 0014"
        ...      "0000 0021 0000 002B  0001 0001 0002 0000"
        ...      "0002 0096 6400 0100  0100 0100 00FF 6A00"
        ...      "0100 0000 0100 01B5  0001 0003 C000 C000"
        ...      "0000 0000 1000 2000  2000 3000 4000")
        >>> b = utilities.fromhex(s)
        >>> fvb = MVAR.fromvalidatedbytes
        >>> obj = fvb(b, axisOrder=axorder, logger=logger)
        test.MVAR - DEBUG - Walker has 110 remaining bytes.
        test.MVAR.version - DEBUG - Walker has 110 remaining bytes.
        test.MVAR - INFO - 3 ValueRecords declared
        test.MVAR - WARNING - Reserved field is not set to zero.
        test.MVAR.IVS - DEBUG - Walker has 74 remaining bytes.
        test.MVAR.IVS - INFO - Format 1
        test.MVAR.IVS - DEBUG - Data count is 3
        test.MVAR.IVS - DEBUG - Axis count is 1
        test.MVAR.IVS - DEBUG - Region count is 3
        test.MVAR.IVS - DEBUG - Delta (0, 0)
        test.MVAR.IVS - DEBUG - Delta (1, 0)
        test.MVAR.IVS - DEBUG - Delta (2, 0)
        test.MVAR.valuemap - DEBUG - Walker has 98 remaining bytes.
        test.MVAR.valuemap - DEBUG - Tag: b'bar ': (2, 0)
        test.MVAR.valuemap - DEBUG - Tag: b'foo ': (0, 0)
        test.MVAR.valuemap - DEBUG - Tag: b'test': (1, 0)
        
        >>> obj = fvb(b[:5], axisOrder=axorder, logger=logger)
        test.MVAR - DEBUG - Walker has 5 remaining bytes.
        test.MVAR - ERROR - Insufficient bytes.

        >>> bad = b[0:7] + b'\x07' + b[8:]
        >>> logger.logger.setLevel("WARNING")
        >>> obj = fvb(bad, axisOrder=axorder, logger=logger)
        test.MVAR - ERROR - Unexpected valueRecordSize 7 (expected 8)

        >>> bad = b[0:9] + utilities.fromhex("00") + b[10:]
        >>> obj = fvb(bad, axisOrder=axorder, logger=logger)
        test.MVAR - WARNING - valueRecordCount is zero!
        test.MVAR - WARNING - Reserved field is not set to zero.
        
        >>> bad = b[0:10] + utilities.fromhex("0000") + b[12:]
        >>> obj = fvb(bad, axisOrder=axorder, logger=logger)
        test.MVAR - WARNING - Reserved field is not set to zero.
        test.MVAR - ERROR - non-zero valueRecordCount but no IVS!
        
        >>> bad = b[0:10] + utilities.fromhex("FFFF") + b[12:]
        >>> obj = fvb(bad, axisOrder=axorder, logger=logger)
        test.MVAR - WARNING - Reserved field is not set to zero.
        test.MVAR - ERROR - offsetToItemVariationStore extends past end of table!
        
        >>> bad = b[:-16]
        >>> obj = fvb(bad, axisOrder=axorder, logger=logger)
        test.MVAR - WARNING - Reserved field is not set to zero.
        test.MVAR.IVS - ERROR - Region offset extends past end of table!
        test.MVAR - ERROR - Item Variation Store missing or empty!

        >>> axorder=('wght', 'wdth')
        >>> obj = fvb(b, axisOrder=axorder, logger=logger)
        test.MVAR - WARNING - Reserved field is not set to zero.
        test.MVAR.IVS - ERROR - Axis count 1 does not match size of axisOrder 2!
        test.MVAR - ERROR - Item Variation Store missing or empty!
        """

        axisOrder = kwArgs.pop('axisOrder', [])

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('MVAR')
        else:
            logger = logger.getChild('MVAR')

        t_length = w.length()

        logger.debug((
          'V0001',
          (t_length,),
          "Walker has %d remaining bytes."))

        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        version = otversion.Version.fromvalidatedwalker(w, logger=logger)
        reserved, valueRecordSize, valueRecordCount = w.unpack("3H")

        if valueRecordSize != _V1_0_VALUE_RECORD_SIZE:
            logger.error((
              'V1093',
              (valueRecordSize, _V1_0_VALUE_RECORD_SIZE),
              "Unexpected valueRecordSize %d (expected %d)"))

            return None

        if valueRecordCount > 0:
            logger.info((
              'V1094',
              (valueRecordCount,),
              "%d ValueRecords declared"))

        else:
            logger.warning((
              'V1094',
              (),
              "valueRecordCount is zero!"))

        if reserved != 0:  # formerly axisCount
            logger.warning((
              'V1098',
              (),
              "Reserved field is not set to zero."))

        offsetToIVS = w.unpack("H")

        if offsetToIVS == 0 and valueRecordCount:
            logger.error((
              'Vxxxx',
              (),
              "non-zero valueRecordCount but no IVS!"))
              
            return None

        if offsetToIVS >= t_length:
            logger.error((
              'V0004',
              (),
              "offsetToItemVariationStore extends past end of table!"))
            return None
            
        elif offsetToIVS:
            wIvs = w.subWalker(offsetToIVS)
            IVSfvw = living_variations.IVS.fromvalidatedwalker
            ivs = IVSfvw(wIvs,
                         axisOrder=axisOrder,
                         logger=logger,
                         **kwArgs)

            if not ivs:
                logger.error((
                  'Vxxxx',
                  (),
                  "Item Variation Store missing or empty!"))

                return None

        if w.length() < (valueRecordSize * valueRecordCount):
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for the number of ValueRecords"))

            return None

        if w.length():
            fvw = valuemap.ValueMap.fromvalidatedwalker        
            vmap = fvw(w, recordCount=valueRecordCount, logger=logger, ivs=ivs, **kwArgs)
        else:
            vmap = valuemap.ValueMap()

        r = cls(version=version,
                valueMap=vmap)

        return r


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MVAR object from the specified walker.

        >>> s = ("0001 0000 0000 0008  0003 0024 6261 7220"
        ...      "0002 0000 666F 6F20  0000 0000 7465 7374"
        ...      "0001 0000 0001 0000  0034 0003 0000 0014"
        ...      "0000 0021 0000 002B  0001 0001 0002 0000"
        ...      "0002 0096 6400 0100  0100 0100 00FF 6A00"
        ...      "0100 0000 0100 01B5  0001 0003 C000 C000"
        ...      "0000 0000 1000 2000  2000 3000 4000")
        >>> b = utilities.fromhex(s)
        >>> obj = MVAR.frombytes(b, axisOrder=('wght',))
        >>> obj.valueMap['bar '].pprint()
        A delta of -75 applies in region 'wght': (start 0.0, peak 0.25, end 0.5)
        """

        version = otversion.Version.fromwalker(w)
        reserved, valueRecordSize, valueRecordCount, offsetToIVS = w.unpack("4H")
        wIvs = w.subWalker(offsetToIVS)
        IVSfw = living_variations.IVS.fromwalker

        if offsetToIVS:
            ivs = IVSfw(wIvs, **kwArgs)

        if w.length():
            fw = valuemap.ValueMap.fromwalker
            vmap = fw(w, recordCount=valueRecordCount, ivs=ivs, **kwArgs)
        else:
            vmap = {}

        r = cls(version=version, valueMap=vmap)

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.fvar import fvar
    from fontio3.opentype.living_variations import (LivingDeltas,
                                                    LivingRegion,
                                                    IVS,
                                                    LivingDeltasMember)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


