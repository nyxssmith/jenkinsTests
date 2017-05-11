#
# HVAR.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the HVAR table.
"""

# System imports
import itertools

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.HVAR import deltasetindexmap, livingdeltas_dict
from fontio3.opentype import version as otversion
from fontio3.opentype import living_variations

# -----------------------------------------------------------------------------

#
# Private methods
#

def _validate(obj, **kwArgs):
    """
    isValid() validation for the top-level HVAR
    """

    editor = kwArgs['editor']
    logger = kwArgs['logger']

    isOK = True

    # TO DO: write content validations

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

class HVAR(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing an HVAR table. These are simple objects that contain
    Advance, LSB, and RSB DeltaSetIndexMaps as well as an itemVariationStore.

    >>> d = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    >>> key = LivingRegion.fromdict(d)
    >>> ld0 = LivingDeltas({LivingDeltasMember((key, -180))})
    >>> ld1 = LivingDeltas({LivingDeltasMember((key, 40))})
    >>> awmap = livingdeltas_dict.LivingDeltasDict({0:ld0, 1: ld1})
    >>> obj = HVAR(advances=awmap)
    >>> obj.pprint()
    Version:
      Major version: 1
      Minor version: 0
    Advance Width Deltas:
      0:
        A delta of -180 applies in region 'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
      1:
        A delta of 40 applies in region 'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)
    Left Sidebearing Deltas: (no data)
    Right Sidebearing Deltas: (no data)
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

        advances = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: livingdeltas_dict.LivingDeltasDict(),
            attr_label = "Advance Width Deltas"),

        leftsidebearings = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: None,
            attr_label = "Left Sidebearing Deltas"),

        rightsidebearings = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: None,
            attr_label = "Right Sidebearing Deltas"),
        )

    attrSorted = ('version',
                  'advances',
                  'leftsidebearings',
                  'rightsidebearings')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the HVAR object to the specified LinkedWriter.

        The following keyword arguments are recognized:

            axisOrder   an iterable of axis tags (e.g. fvar.axisOrder) (required).

        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString(axisOrder=('wght', 'wdth')))
               0 | 0001 0000 0000 0014  0000 003C 0000 0000 |...........<....|
              10 | 0000 0000 0001 0000  0018 0001 0000 000C |................|
              20 | 0002 0001 0001 0000  FF4C 0028 0002 0001 |.........L.(....|
              30 | D000 0000 4000 C000  1000 3000 0010 0002 |....@.....0.....|
              40 | 0000 0001                                |....            |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)

        else:
            stakeValue = w.stakeCurrent()

        self.version.buildBinary(w, **kwArgs)

        stake_IVS = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stake_IVS)

        # get our IVS binary string & Delta-Set map into them
        # from our width, LSB, and RSB values (if present).
        advVals = [t[1] for t in sorted(self.advances.items())]

#         if self.leftsidebearings:
#             lsbVals = [t[1] for t in sorted(self.leftsidebearings.items())]
#         else:
#             lsbVals = []
# 
#         if self.rightsidebearings:
#             rsbVals = [t[1] for t in sorted(self.rightsidebearings.items())]
#         else:
#             rsbVals = []

        # convert Living Deltas back to a binary string + LivingDelta-to-DeltaSetIndexMap
        #valIter = itertools.chain(advVals, lsbVals, rsbVals)
        valIter = self.gatheredLivingDeltas(**kwArgs)
        ivsBsFn = living_variations.IVS.binaryStringFromDeltas
        ivsBs, LDtoDSMap = ivsBsFn(valIter, **kwArgs)

        # Currently: always write advances with explicit map data. try to
        # minimize length, though, using technique similar to hmtx table:
        runcount = 0
        testVal = advVals[-1]
        for i in range(len(advVals) - 2, -1, -1):
            if advVals[i] != testVal:
                break
            runcount += 1

        shortlen = len(advVals) - runcount
        stake_AWM = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stake_AWM)
        advMap = {g: LDtoDSMap[advVals[g]] for g in range(shortlen)}
        advDSMap = deltasetindexmap.DeltaSetIndexMap(advMap)

        if self.leftsidebearings:
            count = len(self.leftsidebearings)
            stake_LSBM = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stake_LSBM)
            lsbMap = {g: LDtoDSMap[self.leftsidebearings[g]] for g in range(count)}
            lsbDSMap = deltasetindexmap.DeltaSetIndexMap(lsbMap)
        else:
            w.add("L", 0)

        if self.rightsidebearings:
            count = len(self.rightsidebearings)
            stake_RSBM = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stake_RSBM)
            rsbMap = {g: LDtoDSMap[self.rightsidebearings[g]] for g in range(count)}
            rsbDSMap = deltasetindexmap.DeltaSetIndexMap(rsbMap)
        else:
            w.add("L", 0)

        # stake and write the IVS data
        w.stakeCurrentWithValue(stake_IVS)
        w.addString(ivsBs)

        # stake and write the Advances DSIMap
        w.stakeCurrentWithValue(stake_AWM)
        advDSMap.buildBinary(w, **kwArgs)

        if self.leftsidebearings:
            # stake and write the map
            w.stakeCurrentWithValue(stake_LSBM)
            lsbDSMap.buildBinary(w, **kwArgs)

        if self.rightsidebearings:
            w.stakeCurrentWithValue(stake_RSBM)
            rsbDSMap.buildBinary(w, **kwArgs)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new HVAR object from the specified walker, doing
        validation.

        The following keyword arguments are recognized:

            axisOrder       an iterable of axis tags (e.g. fvar.axisOrder) (required).

            fontGlyphCount  the number of glyphs in the font.

            logger          a logging.logger-compatible object

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = (
        ...  "0001 0000 0000 0014  0000 003C 0000 0000"
        ...  "0000 0000 0001 0000  0018 0001 0000 000C"
        ...  "0002 0001 0001 0000  FF4C 0028 0002 0001"
        ...  "D000 0000 4000 C000  1000 3000 0000 0002"
        ...  "0001")
        >>> b = utilities.fromhex(s)
        >>> fvb = HVAR.fromvalidatedbytes
        >>> obj = fvb(b, logger=logger, axisOrder=('wght','wdth'), fontGlyphCount=2)
        test.HVAR - DEBUG - Walker has 66 remaining bytes.
        test.HVAR.version - DEBUG - Walker has 66 remaining bytes.
        test.HVAR.IVS - DEBUG - Walker has 46 remaining bytes.
        test.HVAR.IVS - INFO - Format 1
        test.HVAR.IVS - DEBUG - Data count is 1
        test.HVAR.IVS - DEBUG - Axis count is 2
        test.HVAR.IVS - DEBUG - Region count is 1
        test.HVAR.IVS - DEBUG - Delta (0, 0)
        test.HVAR.IVS - DEBUG - Delta (0, 1)
        test.HVAR - DEBUG - Advance Width Delta-Set Index Map present
        test.HVAR.deltasetindexmap - DEBUG - Walker has 6 remaining bytes.
        test.HVAR.deltasetindexmap - DEBUG - entryFormat = 0x0
        test.HVAR.deltasetindexmap - DEBUG - mapCount = 2
        test.HVAR.deltasetindexmap - DEBUG - innerBitCount = 1
        test.HVAR.deltasetindexmap - DEBUG - mapEntrySize = 1 bytes
        test.HVAR.deltasetindexmap - DEBUG - Entry 0 (0, 0); rawData = 0x0
        test.HVAR.deltasetindexmap - DEBUG - Entry 1 (0, 1); rawData = 0x1
        test.HVAR - DEBUG - Advances glyph 0 DeltaSetIndex (0, 0)
        test.HVAR - DEBUG - Advances glyph 1 DeltaSetIndex (0, 1)
        
        >> sorted(obj)
        [(0, 0), (0, 1)]
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('HVAR')
        else:
            logger = logger.getChild('HVAR')

        axisOrder = kwArgs.pop('axisOrder')
        fontGlyphCount = utilities.getFontGlyphCount(**kwArgs)

        t_length = w.length()

        logger.debug((
          'V0001',
          (t_length,),
          "Walker has %d remaining bytes."))

        if t_length < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        version = otversion.Version.fromvalidatedwalker(w, logger=logger)

        if version.major != 1:
            logger.error((
              'V1101',
              (version.major,),
              "Unexpected table major version %d (expected 1)"))

            return None

        if version.minor != 0:
            logger.warning((
              'V1101',
              (version.minor,),
              "Unexpected table minor version %d (expected 0)"))
            # still proceed processing; minor version change should not change structure

        r = cls(version=version)

        oIVS, oAWM, oLSBM, oRSBM = w.unpack("4L")

        ivs = {}
        if oIVS:
            maxLen = int(w.length() - oIVS)
            wIvs = w.subWalker(oIVS)
            IVSfvw = living_variations.IVS.fromvalidatedwalker
            ivs = IVSfvw(wIvs, axisOrder=axisOrder, logger=logger, **kwArgs)

        if not ivs:
            logger.error((
              'V1100',
              (),
              "Item Variation Store missing or empty"))

            return None

        DSIMfvw = deltasetindexmap.DeltaSetIndexMap.fromvalidatedwalker

        # Advance width data is required, but an explicit Delta-Set Index Map
        # for it isn't. If the Delta-Set map isn't present, default to (0,
        # glyphIndex) as keys into the IVS to obtain the LivingDeltas.
        if oAWM:
            logger.debug(('Vxxxx', (), "Advance Width Delta-Set Index Map present"))
            wAwm = w.subWalker(oAWM)
            gidToDSMap = DSIMfvw(wAwm, logger=logger, **kwArgs)
        else:
            gidToDSMap = {g:(0, g) for g in range(fontGlyphCount)}

        defDSVal = sorted(gidToDSMap.items())[-1][1]

        lds = {}
        for g in range(fontGlyphCount):
            dskey = gidToDSMap.get(g, defDSVal)

            if dskey in ivs:
                logger.debug(('Vxxxx', (g, dskey), "Advances glyph %d DeltaSetIndex %s"))
            else:
                logger.error((
                  'Vxxxx',
                  (dskey, g),
                  "Advances: DeltaSetIndex %s for glyph %d not found "
                  "in Item Variation Store!"))

                return None

            lds[g] = ivs[dskey]

        r.advances = livingdeltas_dict.LivingDeltasDict(lds)

        # LSB & RSB are optional and if present they have an explicit Delta-Set
        # Index Map. So if offsets are NULL, there is no map.
        if oLSBM:
            logger.debug(('Vxxxx', (), "LSB Delta-Set Index Map present"))
            wLsbm = w.subWalker(oLSBM)
            gidToDSMap = DSIMfvw(wLsbm, logger=logger, **kwArgs)
            defDSVal = sorted(gidToDSMap.items())[-1][1]
            lds = {g:ivs[gidToDSMap.get(g, defDSVal)] for g in range(fontGlyphCount)}
            r.leftsidebearings = livingdeltas_dict.LivingDeltasDict(lds)

        if oRSBM:
            logger.debug(('Vxxxx', (), "RSB Delta-Set Index Map present"))
            wRsbm = w.subWalker(oRSBM)
            defDSVal = sorted(gidToDSMap.items())[-1][1]
            lds = {g:ivs[gidToDSMap.get(g, defDSVal)] for g in range(fontGlyphCount)}
            r.rightsidebearings = livingdeltas_dict.LivingDeltasDict(lds)

        return r



    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new HVAR object from the specified walker.

        The following keyword arguments are recognized:

            axisOrder       an iterable of axis tags (e.g. fvar.axisOrder) (required).

            fontGlyphCount  the number of glyphs in the font.

        """

        axisOrder = kwArgs.pop('axisOrder')
        fontGlyphCount = utilities.getFontGlyphCount(**kwArgs)

        version = otversion.Version.fromwalker(w)

        r = cls(version=version)

        oIVS, oAWM, oLSBM, oRSBM = w.unpack("4L")

        wIvs = w.subWalker(oIVS)
        IVSfw = living_variations.IVS.fromwalker
        ivs = IVSfw(wIvs, axisOrder=axisOrder, **kwArgs)

        DSIMfw = deltasetindexmap.DeltaSetIndexMap.fromwalker

        # Advance width data is required, but an explicit Delta-Set Index Map
        # for it isn't. If the Delta-Set map isn't present, default to (0,
        # glyphIndex) as keys into the IVS to obtain the LivingDeltas.
        if oAWM:
            wAwm = w.subWalker(oAWM)
            gidToDSMap = DSIMfw(wAwm, **kwArgs)
        else:
            gidToDSMap = {g:(0, g) for g in range(fontGlyphCount)}

        defDSVal = sorted(gidToDSMap.items())[-1][1]
        lds = {g:ivs[gidToDSMap.get(g, defDSVal)] for g in range(fontGlyphCount)}

        r.advances = livingdeltas_dict.LivingDeltasDict(lds)

        # LSB & RSB are optional and if present they have an explicit Delta-Set
        # Index Map. So if offsets are NULL, there is no map.
        if oLSBM:
            wLsbm = w.subWalker(oLSBM)
            gidToDSMap = DSIMfw(wLsbm, **kwArgs)
            defDSVal = sorted(gidToDSMap.items())[-1][1]
            lds = {g:ivs[gidToDSMap.get(g, defDSVal)] for g in range(fontGlyphCount)}
            r.leftsidebearings = livingdeltas_dict.LivingDeltasDict(lds)

        if oRSBM:
            wRsbm = w.subWalker(oRSBM)
            gidToDSMap = DSIMfw(wLsbm, **kwArgs)
            defDSVal = sorted(gidToDSMap.items())[-1][1]
            lds = {g:ivs[gidToDSMap.get(g, defDSVal)] for g in range(fontGlyphCount)}
            r.rightsidebearings = livingdeltas_dict.LivingDeltasDict(lds)

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype.living_variations import (LivingDeltas,
                                                    IVS,
                                                    LivingRegion,
                                                    LivingDeltasMember)

    d = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    key = LivingRegion.fromdict(d)
    ld0 = LivingDeltas({LivingDeltasMember((key, -180))})
    ld1 = LivingDeltas({LivingDeltasMember((key, 40))})
    awmap = livingdeltas_dict.LivingDeltasDict({0:ld0, 1: ld1})
    _testingValues =(
      HVAR(),
      HVAR(advances=awmap))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


