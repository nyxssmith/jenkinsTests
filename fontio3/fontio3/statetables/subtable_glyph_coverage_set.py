#
# subtable_glyph_coverage_set.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#
import logging

from fontio3.fontdata import setmeta
from fontio3.utilities import getFontGlyphCount, hexdump, makeDoctestLogger
from fontio3.utilities.walkerbit import StringWalkerBit
from fontio3.utilities.writer import LinkedWriter


def getBytesPerSubtableCoverageArray(**kwArgs):
    """
    Returns the number of bytes for a subtable glyph coverage array based
    on the number of glyphs in the font, includes padding bytes if needed
    to ensure a four-byte boundary.
    >>> kwArgs = {'fontGlyphCount': 27}
    >>> getBytesPerSubtableCoverageArray(**kwArgs)
    4
    """
    numGlyphs = getFontGlyphCount(**kwArgs)
    # Each coverage bitfield is (numGlyphs + CHAR_BIT - 1) / CHAR_BIT bytes
    # in size...
    bytesPerSubtable = (numGlyphs + 7) // 8
    # ...padded to a four-byte boundary.
    bytesPerSubtable = ((bytesPerSubtable + 3) // 4) * 4
    return bytesPerSubtable


class SubtableGlyphCoverageSet(set, metaclass=setmeta.FontDataMetaclass):
    #
    # Class definition variables
    #

    setSpec = dict(
        item_renumberdirect=True,
        set_showpresorted=True)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SubtableGlyphCoverageSet object to the
        specified LinkedWriter.

        The keyword arguments are:
            stakeValue      The stake value to be used at the start of this
                            output.
            fontGlyphCount  Number of glyphs in the font.
        >>> s = SubtableGlyphCoverageSet({1, 2, 3, 42})
        >>> fontGlyphCount = 43
        >>> w = LinkedWriter()
        >>> stakeValue = w.getNewStake()
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'stakeValue': stakeValue}
        >>> s.buildBinary(w, **kwArgs)
        >>> hexdump(w.binaryString())
               0 | 0E00 0000 0004 0000                      |........        |
        """
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        # else:
        #     stakeValue = w.stakeCurrent()

        numGlyphs = getFontGlyphCount(**kwArgs)
        bytesPerSubtable = getBytesPerSubtableCoverageArray(**kwArgs)
        data = [0] * bytesPerSubtable
        for glyph_index in range(numGlyphs):
            if glyph_index in self:
                data[glyph_index // 8] |= (1 << (glyph_index & 0x07))
        w.addGroup('B', data)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SubtableGlyphCoverageSet object from the
        specified walker, doing source validation.

        >>> wb = StringWalkerBit(bytes.fromhex("0E 00 00 00 00 04 00 00"))
        >>> fontGlyphCount = 43
        >>> logger = makeDoctestLogger("fvw")
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount, 'logger': logger}
        >>> SubtableGlyphCoverageSet.fromvalidatedwalker(w=wb, **kwArgs)
        fvw - DEBUG - Walker has 8 remaining bytes.
        fvw - DEBUG - Walker has 0 remaining bytes.
        SubtableGlyphCoverageSet({1, 2, 3, 42})
        >>> wb2 = StringWalkerBit(bytes.fromhex("0E 00 00 00 00"))
        >>> SubtableGlyphCoverageSet.fromvalidatedwalker(w=wb2, **kwArgs)
        fvw - DEBUG - Walker has 5 remaining bytes.
        fvw - ERROR - Insufficient bytes -- need 8, have 5.
        """

        logger = kwArgs.pop('logger', logging.getLogger())
        logger.debug((
            'V0001',
            (w.length(),),
            "Walker has %d remaining bytes."))
        r = cls()
        numGlyphs = getFontGlyphCount(**kwArgs)
        bytesPerSubtable = getBytesPerSubtableCoverageArray(**kwArgs)

        bytesAvailable = w.length()
        bytesNeeded = bytesPerSubtable
        if bytesAvailable < bytesNeeded:
            logger.error(('V0004', (bytesNeeded, bytesAvailable),
                          "Insufficient bytes -- need %d, have %d."))
            return None

        data = w.group('B', bytesPerSubtable)
        for glyph_index in range(numGlyphs):
            # To determine if a particular glyph is covered by the subtable,
            # calculate coverageBitfield[glyph/CHAR_BIT] & (1 << (glyph & (CHAR_BIT-1))).
            # If this is non-zero, the glyph is covered.
            if data[glyph_index // 8] & (1 << (glyph_index & 0x07)) != 0:
                r.add(glyph_index)
        logger.debug((
            'V0001',
            (w.length(),),
            "Walker has %d remaining bytes."))
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a SubtableGlyphCoverageSet object from the
        specified walker.
        >>> wb = StringWalkerBit(bytes.fromhex("0E 00 00 00 00 04 00 00"))
        >>> fontGlyphCount = 43
        >>> kwArgs = {'fontGlyphCount': fontGlyphCount}
        >>> SubtableGlyphCoverageSet.fromwalker(w=wb, **kwArgs)
        SubtableGlyphCoverageSet({1, 2, 3, 42})
        """
        r = cls()
        numGlyphs = getFontGlyphCount(**kwArgs)
        bytesPerSubtable = getBytesPerSubtableCoverageArray(**kwArgs)
        data = w.group('B', bytesPerSubtable)
        for glyph_index in range(numGlyphs):
            # To determine if a particular glyph is covered by the subtable,
            # calculate coverageBitfield[glyph/CHAR_BIT] & (1 << (glyph & (CHAR_BIT-1))).
            # If this is non-zero, the glyph is covered.
            if data[glyph_index // 8] & (1 << (glyph_index & 0x07)) != 0:
                r.add(glyph_index)
        return r


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
