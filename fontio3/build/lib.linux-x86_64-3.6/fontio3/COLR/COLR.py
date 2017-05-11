#
# COLR.py
#
# Copyright © 2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the 'COLR' table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.COLR import layertuple

# -----------------------------------------------------------------------------
#
# Functions
#

def _validate(d, **kwArgs):
    editor = kwArgs['editor']
    logger = kwArgs.get('logger').getChild('COLR')

    if not editor.reallyHas(b'CPAL'):
        logger.error((
            'Vxxxx',
            (),
            "COLR table present but CPAL table is missing or damaged."))
        return False

    cpalTbl = editor.CPAL

    if editor.reallyHas(b'glyf'):
        gTbl = editor.glyf
    elif editor.reallyHas(b'CFF '):
        gTbl = editor[b'CFF ']
    else:
        logger.error((
          'Vxxxx',
          (),
          "COLR table present but 'glyf' or 'CFF ' table missing or damaged."))
        return False

    isOK = True
    for k,lt in d.items():
        for v in lt:
            if v.glyphIndex in gTbl:
                logger.info((
                  'Vxxxx',
                  (k, v.glyphIndex,),
                  "COLR entry %d: glyphIndex %d is present in the glyph data table."))
            else:
                isOK = False
                logger.error((
                  'Vxxxx',
                  (k, v.glyphIndex,),
                  "COLR entry %d: glyphIndex %d is out-of-range for the glyph "
                  "data table."))

            if v.paletteIndex in cpalTbl[0]:
                logger.info((
                  'Vxxxx',
                  (k, v.paletteIndex,),
                  "COLR entry %d: paletteIndex %d is present in the CPAL table."))
            else:
                isOK = False
                logger.error((
                  'Vxxxx',
                  (k, v.paletteIndex,),
                  "COLR entry %d: paletteIndex %d is out-of-range of the CPAL "
                  "palette(s)."))
              
    return isOK


# -----------------------------------------------------------------------------

#
# Classes
#


class COLR(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Top-level COLR objects. These are maps of reference (base) glyph to
    LayerTuples. There is one attribute:

        version     Table version number

    >>> _testingValues[0].pprint()
    1:
      0: glyphIndex = 21, paletteIndex = 45
      1: glyphIndex = 8, paletteIndex = 16
    2:
      0: glyphIndex = 8, paletteIndex = 16
      1: glyphIndex = 21, paletteIndex = 45
      2: glyphIndex = 8, paletteIndex = 16
    Version: 0
    """

    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol=True,
        item_renumberdirectkeys=True,
        map_validatefunc_partial=_validate)
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Version"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the COLR object to the specified LinkedWriter.

        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0002 0000 000E  0000 001A 0005 0001 |................|
              10 | 0000 0002 0002 0002  0003 0015 002D 0008 |.............-..|
              20 | 0010 0008 0010 0015  002D 0008 0010      |.........-....  |
       """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("H", self.version)

        allrecs = sorted(self.items())
        w.add("H", len(allrecs))  # numBaseGlyphRecords

        stakeOffsetBaseGlyphRecord = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stakeOffsetBaseGlyphRecord)

        stakeOffsetLayerRecord = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, stakeOffsetLayerRecord)

        layerct = sum([len(r[1]) for r in allrecs])
        w.add("H", layerct)  # numLayerRecords

        # Base Glyph recs
        w.stakeCurrentWithValue(stakeOffsetBaseGlyphRecord)
        layeridx = 0
        
        for rec in allrecs:
            gid = rec[0]
            ltuple = rec[1]
            nLayers = len(ltuple)
            w.add("H", gid)
            w.add("H", layeridx)  # firstLayerIndex
            w.add("H", nLayers)
            layeridx += nLayers

        # now Layer Records
        w.stakeCurrentWithValue(stakeOffsetLayerRecord)
        
        for rec in allrecs:
            for lyt in rec[1]:
                lyt.buildBinary(w, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new COLR object. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' kwArg).

        >>> logger = utilities.makeDoctestLogger("test")
        >>> bs = _testingValues[0].binaryString()
        >>> fvb = _testingValues[0].fromvalidatedbytes
        >>> obj = fvb(bs, logger=logger)
        test.COLR - DEBUG - Walker has 46 remaining bytes.
        test.COLR - INFO - Base Glyph 1 layers: first 0, count 2
        test.COLR.layertuple - DEBUG - Walker has 20 remaining bytes.
        test.COLR.layertuple.layer - DEBUG - Walker has 20 remaining bytes.
        test.COLR.layertuple.layer - INFO - Glyph 21: palette index 45
        test.COLR.layertuple.layer - DEBUG - Walker has 16 remaining bytes.
        test.COLR.layertuple.layer - INFO - Glyph 8: palette index 16
        test.COLR - INFO - Base Glyph 2 layers: first 2, count 3
        test.COLR.layertuple - DEBUG - Walker has 12 remaining bytes.
        test.COLR.layertuple.layer - DEBUG - Walker has 12 remaining bytes.
        test.COLR.layertuple.layer - INFO - Glyph 8: palette index 16
        test.COLR.layertuple.layer - DEBUG - Walker has 8 remaining bytes.
        test.COLR.layertuple.layer - INFO - Glyph 21: palette index 45
        test.COLR.layertuple.layer - DEBUG - Walker has 4 remaining bytes.
        test.COLR.layertuple.layer - INFO - Glyph 8: palette index 16
        >>> obj == _testingValues[0]
        True
        """
        
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('COLR')
        else:
            logger = logger.getChild('COLR')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 14:  # size of header, in bytes
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        # Get the header information.
        version, bgcount, bgoffset, loffset, lcount = w.unpack("2H2LH")

        if version != 0:
            logger.warning((
              'V0002',
              (version,),
              "Unknown version %d; parsing as v0."))

        if bgcount == 0:
            logger.warning(('V0924', (), "BaseGlyph record count is zero"))

        if lcount == 0:
            logger.warning(('V0925', (), "Layer record count is zero"))

        r = cls(version=version)

        wbg = w.subWalker(bgoffset)
        
        if wbg.length() < 6 * bgcount:
            logger.error((
              'V0004',
              (bgcount,),
              "Insufficient bytes for Base Glyph count of %d."))
            
            return None

        bgentries = wbg.group("3H", bgcount)

        wl = w.subWalker(loffset)
        
        if wl.length() < 4 * lcount:
            logger.error((
              'V0004',
              (lcount,),
              "Insufficient bytes for Layer count of %d"))
            
            return None

        fvw = layertuple.LayerTuple.fromvalidatedwalker
        
        for bge in bgentries:
            gid = bge[0]
            firstidx = bge[1]
            numLayers = bge[2]
            
            logger.info((
              'V1004',
              (gid, firstidx, numLayers),
              "Base Glyph %d layers: first %d, count %d"))
            
            wlt = w.subWalker(loffset + (firstidx * 4))
            r[gid] = fvw(wlt, numLayers=numLayers, logger=logger, **kwArgs)

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new COLR object from the specified walker.
        >>> s = _testingValues[0].binaryString()
        >>> obj = COLR.frombytes(s)
        >>> _testingValues[0] == obj
        True
        """
        
        # Get the header information.
        version, bgcount, bgoffset, loffset, lcount = w.unpack("2H2LH")
        r = cls(version=version)
        bgentries = w.group("3H", bgcount)
        fw = layertuple.LayerTuple.fromwalker
        
        for bge in bgentries:
            gid = bge[0]
            firstidx = bge[1]
            numLayers = bge[2]
            wlt = w.subWalker(loffset + (firstidx * 4))
            r[gid] = fw(wlt, numLayers=numLayers, **kwArgs)

        return r

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = (
        COLR({
          1: layertuple._testingValues[0],
          2: layertuple._testingValues[1]}),
        COLR(),)


def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

