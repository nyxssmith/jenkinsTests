#
# subtable_glyph_coverage_sets.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#
import logging

from fontio3.fontdata import seqmeta
from fontio3.statetables.subtable_glyph_coverage_set import (
    SubtableGlyphCoverageSet,
    getBytesPerSubtableCoverageArray)
from fontio3.utilities import hexdump, makeDoctestLogger
from fontio3.utilities.walkerbit import StringWalkerBit
from fontio3.utilities.writer import LinkedWriter


class SubTableGlyphCoverageSets(list, metaclass=seqmeta.FontDataMetaclass):

    #
    # Class definition variables
    #

    seqSpec = dict(
        item_pprintlabelfunc=(lambda x: "Subtable %d Glyph Coverage Set" % (x + 1,)),
        item_followsprotocol=True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SubtableGlyphCoverageSets object to the
        specified LinkedWriter.

        The keyword arguments are:
            stakeValue      The stake value to be used at the start of this
                            output.
            fontGlyphCount  Number of glyphs in the font.
            isKerx          If true, use 0xFFFFFFFF to indicate no coverage
                            for a given subtable, otherwise use 0.

        >>> glyphSets = [{1, 2, 3, 42}, {}, {0,1,2,3,4,5,6,7,32,33,34,35}, {}]
        >>> s = SubTableGlyphCoverageSets([SubtableGlyphCoverageSet(x) for x in glyphSets])
        >>> fontGlyphCount = 43
        >>> w = LinkedWriter()
        >>> stakeValue = w.getNewStake()
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'stakeValue': stakeValue}
        >>> s.buildBinary(w, **kwArgs)
        >>> hexdump(w.binaryString())
               0 | 0000 0010 0000 0000  0000 0018 0000 0000 |................|
              10 | 0E00 0000 0004 0000  FF00 0000 0F00 0000 |................|
        >>> w2 = LinkedWriter()
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount}
        >>> s.buildBinary(w2, **kwArgs)
        >>> hexdump(w2.binaryString())
               0 | 0000 0010 0000 0000  0000 0018 0000 0000 |................|
              10 | 0E00 0000 0004 0000  FF00 0000 0F00 0000 |................|
        >>> w3 = LinkedWriter()
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'isKerx': True}
        >>> s.buildBinary(w3, **kwArgs)
        >>> hexdump(w3.binaryString())
               0 | 0000 0010 FFFF FFFF  0000 0018 FFFF FFFF |................|
              10 | 0E00 0000 0004 0000  FF00 0000 0F00 0000 |................|
        """
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        if 'isKerx' in kwArgs:
            isKerx = kwArgs.pop('isKerx')
        else:
            isKerx = False

        offsetStakes = {
            i: w.getNewStake()
            for i, subtableGlyphCoverageSet in enumerate(self)
            if subtableGlyphCoverageSet}

        for i, subtableGlyphCoverageSet in enumerate(self):
            if subtableGlyphCoverageSet:
                w.addUnresolvedOffset("L", stakeValue, offsetStakes[i])
            else:
                if isKerx:
                    w.add("L", 0xFFFFFFFF)  # kerx
                else:
                    w.add("L", 0)  # morx

        for i, subtableGlyphCoverageSet in enumerate(self):
            if not subtableGlyphCoverageSet:
                continue

            subtableGlyphCoverageSet.buildBinary(
                w, stakeValue=offsetStakes[i], **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, numSubtables, **kwArgs):
        """
        Creates and returns a new SubtableGlyphCoverageSets object from the
        specified walker, doing source validation.

        >>> hex_data = "00 00 00 10 00 00 00 00 00 00 00 18 00 00 00 00 0E 00 00 00 00 04 00 00 FF 00 00 00 0F 00 00 00"
        >>> wb = StringWalkerBit(bytes.fromhex(hex_data))
        >>> fontGlyphCount = 43
        >>> numSubtables = 4
        >>> logger = makeDoctestLogger("fvw")
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'numSubtables': numSubtables, 'logger': logger}
        >>> SubTableGlyphCoverageSets.fromvalidatedwalker(w=wb, **kwArgs)
        fvw.SubtableGlyphCoverageSets - DEBUG - Walker has 32 remaining bytes.
        fvw.SubtableGlyphCoverageSets.subtable 0 - DEBUG - Walker has 16 remaining bytes.
        fvw.SubtableGlyphCoverageSets.subtable 0 - DEBUG - Walker has 8 remaining bytes.
        fvw.SubtableGlyphCoverageSets.subtable 2 - DEBUG - Walker has 8 remaining bytes.
        fvw.SubtableGlyphCoverageSets.subtable 2 - DEBUG - Walker has 0 remaining bytes.
        fvw.SubtableGlyphCoverageSets - DEBUG - Walker has 0 remaining bytes.
        SubTableGlyphCoverageSets([SubtableGlyphCoverageSet({1, 2, 3, 42}), SubtableGlyphCoverageSet(set()), SubtableGlyphCoverageSet({0, 1, 2, 3, 4, 5, 6, 7, 32, 33, 34, 35}), SubtableGlyphCoverageSet(set())])
        >>> hex_data2 = "00 00 00 10 00 00 00"
        >>> wb2 = StringWalkerBit(bytes.fromhex(hex_data2))
        >>> SubTableGlyphCoverageSets.fromvalidatedwalker(w=wb2, **kwArgs)
        fvw.SubtableGlyphCoverageSets - DEBUG - Walker has 7 remaining bytes.
        fvw.SubtableGlyphCoverageSets - ERROR - Insufficient bytes -- need 16, have 7.
        """

        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('SubtableGlyphCoverageSets')

        logger.debug((
            'V0001',
            (w.length(),),
            "Walker has %d remaining bytes."))

        r = cls()
        w2 = w.subWalker(0, relative=True)
        w3 = w2.subWalker(0)

        bytesNeeded = numSubtables * 4
        bytesAvailable = w3.length()
        if bytesAvailable < bytesNeeded:
            logger.error(('V0004', (bytesNeeded, bytesAvailable),
                          "Insufficient bytes -- need %d, have %d."))
            return None

        subtableOffsets = w3.group('L', numSubtables)
        maxOffset = 0
        for subtableIndex, offset in enumerate(subtableOffsets):
            coverageSet = SubtableGlyphCoverageSet()
            if offset not in {0, 0xFFFFFFFF}:
                w3 = w2.subWalker(offset)
                coverageSet = SubtableGlyphCoverageSet.fromvalidatedwalker(
                    w3,
                    logger=logger.getChild("subtable %d" % (subtableIndex,)),
                    **kwArgs)
                maxOffset = max(maxOffset, offset)
            r.append(coverageSet)

        # skip to the end of the last coverage set
        if maxOffset != 0:
            w.skip(maxOffset + getBytesPerSubtableCoverageArray(**kwArgs))
        # print('w.length() = %d' % w.length())

        logger.debug((
            'V0001',
            (w.length(),),
            "Walker has %d remaining bytes."))
        return r

    @classmethod
    def fromwalker(cls, w, numSubtables, **kwArgs):
        """
        Creates and returns a SubtableGlyphCoverageSet object from the
        specified walker.
        >>> hex_data = "00 00 00 10 00 00 00 00 00 00 00 18 00 00 00 00 0E 00 00 00 00 04 00 00 FF 00 00 00 0F 00 00 00"
        >>> wb = StringWalkerBit(bytes.fromhex(hex_data))
        >>> fontGlyphCount = 43
        >>> numSubtables = 4
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'numSubtables': numSubtables}
        >>> SubTableGlyphCoverageSets.fromwalker(w=wb, **kwArgs)
        SubTableGlyphCoverageSets([SubtableGlyphCoverageSet({1, 2, 3, 42}), SubtableGlyphCoverageSet(set()), SubtableGlyphCoverageSet({0, 1, 2, 3, 4, 5, 6, 7, 32, 33, 34, 35}), SubtableGlyphCoverageSet(set())])
        """
        r = cls()
        w2 = w.subWalker(0, relative=True)
        w3 = w2.subWalker(0)
        subtableOffsets = w3.group('L', numSubtables)
        maxOffset = 0
        for offset in subtableOffsets:
            coverageSet = SubtableGlyphCoverageSet()
            if offset not in {0, 0xFFFFFFFF}:
                w3 = w2.subWalker(offset)
                coverageSet = SubtableGlyphCoverageSet.fromwalker(w3, **kwArgs)
                maxOffset = max(maxOffset, offset)
            r.append(coverageSet)

        # skip to the end of the last coverage set
        if maxOffset != 0:
            w.skip(maxOffset + getBytesPerSubtableCoverageArray(**kwArgs))
        # print('w.length() = %d' % w.length())

        return r


def _test():
    import doctest

    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
