#
# CPAL_v1.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the 'CPAL' table, version 1.
"""

# System imports
import logging

# Other imports
from fontio3.CPAL import palette, palettetype
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class _PaletteTypeDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True)

if 0:
    def __________________(): pass

class CPAL(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Top-level CPAL v1 objects. These are maps of palette indices to Palettes.
    There are four attributes:
        version             Table Version (==1)
        paletteTypes        map of paletteID to PaletteType (mask)
        paletteLabels       map of paletteID to name.namerecs for palette labels
        paletteEntryLabels  map of paletteID to name.namerecs for entry labels

    >>> _testingValues[0].pprint()
    Palette 0:
      0: Red = 0, Green = 0, Blue = 0, Alpha = 0
      1: Red = 51, Green = 34, Blue = 17, Alpha = 68
    PaletteEntryLabels: {}
    PaletteLabels: {}
    PaletteTypes:
      0:
        Light Background
    Version: 1
    """

    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Palette %d" % (i,)),
        item_pprintlabelpresort = True)

    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Version"),
        
        paletteTypes = dict(
            attr_followsprotocol = True,
            attr_initfunc = _PaletteTypeDict,
            attr_label = "PaletteTypes"),
        
        paletteLabels = dict(
            attr_initfunc = (lambda: {}),
            attr_label = "PaletteLabels"),
        
        paletteEntryLabels = dict(
            attr_initfunc = (lambda: {}),
            attr_label = "PaletteEntryLabels"))

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CPAL object to the specified LinkedWriter.

        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002 0002 0004  0000 001C 0000 0002 |................|
              10 | 0000 0000 0000 0000  0000 0000 1122 3344 |............."3D|
              20 | 0000 0000 0000 0000  1122 3344           |........."3D    |
        """
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", 1)  # version
        pi = sorted(self)
        np = len(self)
        npe = max([max(p.keys()) for p in list(self.values())]) + 1
        w.add("H", npe)  # numPalettesEntries
        w.add("H", np)  # numPalette
        w.add("H", np * npe)  # numColorRecords (un-compacted)
        stakeOffsetFirstColorRecord = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stakeOffsetFirstColorRecord)

        for i in pi:
            w.add("H", i * npe)  # colorRecordIndices

        if self.paletteTypes:
            stakeOffsetPaletteTypeArray = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stakeOffsetPaletteTypeArray)
        
        else:
            w.add("L", 0)

        if self.paletteLabels:
            stakeOffsetPaletteLabelArray = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stakeOffsetPaletteLabelArray)
        
        else:
            w.add("L", 0)

        if self.paletteEntryLabels:
            stakeOffsetPaletteEntryLabelArray = w.getNewStake()
            
            w.addUnresolvedOffset(
              "L",
              stakeValue,
              stakeOffsetPaletteEntryLabelArray)
        
        else:
            w.add("L", 0)

        # ColorRecords (as collected in Palettes)
        w.stakeCurrentWithValue(stakeOffsetFirstColorRecord)
        
        for i, p in sorted(self.items()):
            p.buildBinary(w, numPalettesEntries=npe, **kwArgs)

        # PaletteTypeArray
        if self.paletteTypes:
            w.stakeCurrentWithValue(stakeOffsetPaletteTypeArray)
            
            for i in range(np):
                ptype = self.paletteTypes.get(i, palettetype.PaletteType())
                ptype.buildBinary(w, **kwArgs)

        # PaletteLabelArray
        if self.paletteLabels:
            w.stakeCurrentWithValue(stakeOffsetPaletteLabelArray)
            
            for i in range(np):
                plabelid = self.paletteLabels.get(i, 0xFFFF)
                w.add("H", plabelid)

        # PaletteEntryLabelArray
        if self.paletteEntryLabels:
            w.stakeCurrentWithValue(stakeOffsetPaletteEntryLabelArray)
            
            for i in range(npe):
                pelabelid = self.paletteEntryLabels.get(i, 0xFFFF)
                w.add("H", pelabelid)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CPAL object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword argument).

        >>> logger = utilities.makeDoctestLogger("test")
        >>> bs = _testingValues[0].binaryString()
        >>> obj = CPAL.fromvalidatedbytes(bs, logger=logger)
        test.CPAL - DEBUG - Walker has 38 remaining bytes.
        test.CPAL - INFO - 1 Palettes with 2 entries each.
        test.CPAL.palette - DEBUG - Walker has 12 remaining bytes.
        test.CPAL.palette.colorrecord - DEBUG - Walker has 12 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(0, 0, 0, 0)
        test.CPAL.palette.colorrecord - DEBUG - Walker has 8 remaining bytes.
        test.CPAL.palette.colorrecord - INFO - ColorRecord RGBA(51, 34, 17, 68)
        test.CPAL - INFO - Has PaletteTypes
        >>> bs == obj.binaryString()
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

        if w.length() < 26:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        version, npe, np, ncr, ofcr = w.unpack("4HL")

        if version != 1:
            logger.error((
              'V0002',
              (version,),
              "Expected version 1, but got %d"))

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

        # Extras in Version 1
        opta, opla, opela = w.unpack("3L")

        # Palettes
        fvw = palette.Palette.fromvalidatedwalker
        
        for pi in range(np):
            wp = w.subWalker(ofcr + (crindices[pi] * 4))
            r[pi] = fvw(wp, numPalettesEntries=npe, logger=logger, **kwArgs)

        # PaletteTypeArray
        if opta:
            logger.info(('Vxxxx', (), "Has PaletteTypes"))
            fvn = palettetype.PaletteType.fromvalidatednumber
            wpt = w.subWalker(opta)
            
            for p in range(np):
                rawtype = wpt.unpack("L")
                r.paletteTypes[p] = fvn(rawtype, logger=logger, **kwArgs)

        # PaletteLabelsArray
        if opla:
            logger.info(('Vxxxx', (), "Has PaletteLabels"))
            wpl = w.subWalker(opla)
            
            for p in range(np):
                plid = wpl.unpack("H")
                r.paletteLabels[p] = plid

        # PaletteEntryLabelsArray
        if opela:
            logger.info(('Vxxxx', (), "Has PaletteEntryLabels"))
            wpel = w.subWalker(opela)
            
            for e in range(npe):
                pelid = wpel.unpack("H")
                r.paletteEntryLabels[e] = pelid

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

        # Extras in Version 1
        opta, opla, opela = w.unpack("3L")

        # Palettes
        fw = palette.Palette.fromwalker
        
        for pi in range(np):
            wp = w.subWalker(ofcr + (crindices[pi] * 4))
            r[pi] = fw(wp, numPalettesEntries=npe, **kwArgs)

        # PaletteTypeArray
        if opta:
            fn = palettetype.PaletteType.fromnumber
            wpt = w.subWalker(opta)
            
            for p in range(np):
                rawtype = wpt.unpack("L")
                r.paletteTypes[p] = fn(rawtype, **kwArgs)

        # PaletteLabelsArray
        if opla:
            wpl = w.subWalker(opla)
            
            for p in range(np):
                plid = wpl.unpack("H")
                r.paletteLabels[p] = plid

        # PaletteEntryLabelsArray
        if opela:
            wpel = w.subWalker(opela)
            
            for e in range(npe):
                pelid = wpel.unpack("H")
                r.paletteEntryLabels[e] = pelid

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _pt1 = palettetype.PaletteType.fromnumber(1)

    _testingValues = (
        CPAL({0: palette._testingValues[0]}, paletteTypes=_PaletteTypeDict({0: _pt1})),
        CPAL({0: palette._testingValues[1], 1: palette._testingValues[0]}),
    )


def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

