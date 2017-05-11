#
# CPAL_v0.py
#
# Copyright © 2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the 'CPAL' table, version 0.
"""

# System imports
import logging

# Other imports
from fontio3.CPAL import palette
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class CPAL(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Top-level CPAL v0 objects. These are maps of palette indices to Palettes.
    There is one attribute, the version.

    >>> _testingValues[1].pprint()
    Palette 0:
      0: Red = 51, Green = 34, Blue = 17, Alpha = 68
    Palette 1:
      0: Red = 0, Green = 0, Blue = 0, Alpha = 0
      1: Red = 51, Green = 34, Blue = 17, Alpha = 68
    Version: 0
    """

    mapSpec = dict(
        item_followsprotocol=True,
        item_pprintlabelfunc=(lambda i: "Palette %d" % (i,)),
        item_pprintlabelpresort=True)

    attrSpec = dict(
        version=dict(
            attr_initfunc=(lambda: 0),
            attr_label="Version"))

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CPAL object to the specified LinkedWriter.

        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0002 0002 0004  0000 0010 0000 0002 |................|
              10 | 1122 3344 0000 0000  0000 0000 1122 3344 |."3D........."3D|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", 0)  # version
        pi = sorted(self)
        npe = max([max(p.keys()) for p in list(self.values())]) + 1
        w.add("H", npe)  # numPalettesEntries
        w.add("H", len(self))  # numPalette
        w.add("H", len(self) * npe)  # numColorRecords (un-compacted)
        stakeOffsetFirstColorRecord = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stakeOffsetFirstColorRecord)
        
        for i in pi:
            w.add("H", i * npe)  # colorRecordIndices
        
        # ColorRecords (as collected in Palettes)
        w.stakeCurrentWithValue(stakeOffsetFirstColorRecord)
        
        for i, p in sorted(self.items()):
            p.buildBinary(w, numPalettesEntries=npe, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CPAL object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword argument).

        >>> logger = utilities.makeDoctestLogger("test")
        >>> bs = _testingValues[1].binaryString()
        >>> obj = CPAL.fromvalidatedbytes(bs, logger=logger)
        test.CPAL - DEBUG - Walker has 32 remaining bytes.
        test.CPAL - INFO - 2 Palettes with 2 entries each.
        test.CPAL.palette - DEBUG - Walker has 16 remaining bytes.
        test.CPAL.palette.colorrecord - DEBUG - Walker has 16 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(51, 34, 17, 68)
        test.CPAL.palette.colorrecord - DEBUG - Walker has 12 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(0, 0, 0, 0)
        test.CPAL.palette - DEBUG - Walker has 8 remaining bytes.
        test.CPAL.palette.colorrecord - DEBUG - Walker has 8 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(0, 0, 0, 0)
        test.CPAL.palette.colorrecord - DEBUG - Walker has 4 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(51, 34, 17, 68)
        >>> obj[1] == _testingValues[1][1]  # Note: uneven palettes; objects !=
        True
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('CPAL')
        else:
            logger = logger.getChild('CPAL')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 14:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        version, npe, np, ncr, ofcr = w.unpack("4HL")

        if version != 0:
            logger.error((
              'V0002',
              (version,),
              "Expected version zero, but got %d"))
            
            return None

        if np < 1:
            logger.error((
              'V0929',
              (),
              "Must be at least one palette defined."))
            
            return None

        if npe < 1:
            logger.error((
              'V0930',
              (),
              "Must be at least one palette entry defined."))
            
            return None

        if ncr > 0xFFFE:
            logger.error((
              'V0931',
              (),
              "Cannot define more than 0xFFFE colorRecords."))
            
            return None

        logger.info((
          'Vxxxx',
          (np, npe),
          "%d Palettes with %d entries each."))

        r = cls(version=version)
        crindices = w.group("H", np)
        fvw = palette.Palette.fromvalidatedwalker
        
        for pi in range(np):
            wp = w.subWalker(ofcr + (crindices[pi] * 4))
            r[pi] = fvw(wp, numPalettesEntries=npe, logger=logger, **kwArgs)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CPAL object from the specified walker.

        >>> s = _testingValues[0].binaryString()
        >>> obj = CPAL.frombytes(s)
        >>> obj == _testingValues[0]
        True
        """

        version, npe, np, ncr, ofcr = w.unpack("4HL")
        r = cls(version=version)
        crindices = w.group("H", np)
        fw = palette.Palette.fromwalker
        
        for pi in range(np):
            wp = w.subWalker(ofcr + (crindices[pi] * 4))
            r[pi] = fw(wp, numPalettesEntries=npe, **kwArgs)

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = (
        CPAL({0: palette._testingValues[0]}),
        CPAL({0: palette._testingValues[1], 1: palette._testingValues[0]}),
    )


def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

