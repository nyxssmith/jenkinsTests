#
# markarray.py -- definition of an OpenType MarkArray
#
# Copyright © 2009-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of the MarkArray class, used to support mark-related positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GPOS import markrecord
from fontio3.opentype import coverage

# -----------------------------------------------------------------------------

#
# Classes
#

class MarkArray(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects associating glyphs with markClasses and anchors. These are dicts
    mapping glyph indices to MarkRecord objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    afii60002:
      Mark Class: 1
      Mark Anchor:
        x-coordinate: 10
        y-coordinate: 20
        Device for x:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
    xyz16:
      Mark Class: 3
      Mark Anchor:
        x-coordinate: -40
        y-coordinate: 18
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatekwargsfunc = (lambda x,k: {'glyphIndex': k}),
        map_maxcontextfunc = (lambda d: 1))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. Keyword arguments:
        
            anchorPool      If specified should be a dict for the anchor pool.
                            In this case, the devicePool must also be
                            specified, and the higher-level caller is
                            responsible for adding both the anchors and devices
                            to the writer.
                            
                            If not specified, a local pool will be used and the
                            anchors and devices will be written here.
            
            devicePool      If specified should be a dict for the device pool.
                            In this case, the anchorPool must also be
                            specified, and the higher-level caller is
                            responsible for adding both the anchors and devices
                            to the writer.
                            
                            If not specified, a local pool will be used and the
                            anchors and devices will be written here.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 0003 000A 0001  0010 0001 FFD8 0012 |................|
              10 | 0003 000A 0014 000A  0000 000C 0012 0001 |................|
              20 | 8C04                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        anchorPool = kwArgs.get('anchorPool', None)
        devicePool = kwArgs.get('devicePool', None)
        assert (anchorPool is None) == (devicePool is None)
        orderedKeys = kwArgs.get('orderedKeys', [])
        
        if anchorPool is None:
            anchorPool = {}
            devicePool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        revTable = {}
        coverage.Coverage.fromglyphset(self, backMap=revTable)
        w.add("H", len(self))
        
        for covIndex in range(len(self)):
            rec = self[revTable[covIndex]]
            
            rec.buildBinary(
              w,
              anchorPool = anchorPool,
              devicePool = devicePool,
              posBase = stakeValue,
              orderedKeys = orderedKeys)
        
        # Resolve the references
        if doLocal:
            for key in orderedKeys:
                obj, objStake = anchorPool[key]
                obj.buildBinary(w, stakeValue=objStake, devicePool=devicePool)
            
            it = sorted(
              (obj.asImmutable(), obj, stake)
              for obj, stake in devicePool.values())
            
            for immut, obj, objStake in it:
                obj.buildBinary(w, stakeValue=objStake)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkArray from the specified walker, doing
        source validation.
        
        >>> ma = _testingValues[0]
        >>> c = coverage.Coverage.fromglyphset(ma)
        >>> s = ma.binaryString(coverage=c)
        >>> logger = utilities.makeDoctestLogger("markarray_test")
        >>> fvb = MarkArray.fromvalidatedbytes
        >>> obj = fvb(s, coverage=c, logger=logger)
        markarray_test.markarray - DEBUG - Walker has 34 remaining bytes.
        markarray_test.markarray.glyph 15.markrecord - DEBUG - Walker has 32 bytes remaining.
        markarray_test.markarray.glyph 15.markrecord.anchor_coord - DEBUG - Walker has 24 remaining bytes.
        markarray_test.markarray.glyph 97.markrecord - DEBUG - Walker has 28 bytes remaining.
        markarray_test.markarray.glyph 97.markrecord.anchor_device - DEBUG - Walker has 18 remaining bytes.
        markarray_test.markarray.glyph 97.markrecord.anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        markarray_test.markarray.glyph 97.markrecord.anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        markarray_test.markarray.glyph 97.markrecord.anchor_device.x.device - DEBUG - Data are (35844,)
        
        >>> fvb(s[:1], coverage=c, logger=logger)
        markarray_test.markarray - DEBUG - Walker has 1 remaining bytes.
        markarray_test.markarray - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("markarray")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        covTable = kwArgs['coverage']
        revTable = dict(zip(covTable.values(), covTable.keys()))
        r = cls()
        posBase = w.subWalker(0)
        count = w.unpack("H")
        fvw = markrecord.MarkRecord.fromvalidatedwalker
        kwArgs.pop('glyphIndex', None)
        kwArgs.pop('posBase', None)
        
        for i in range(count):
            if i not in revTable:
                logger.error((
                  'V0944',
                  (i,),
                  "Coverage index %d has data, but is not in the Coverage."))
                
                return None
            
            glyph = revTable[i]
            subLogger = logger.getChild("glyph %d" % (glyph,))
            
            obj = fvw(
              w,
              posBase = posBase,
              glyphIndex = glyph,
              logger = subLogger,
              **kwArgs)
            
            if obj is None:
                return None
            
            r[glyph] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkArray from the specified walker. One
        keyword argument is used:
        
            coverage    A Coverage object (from the MarkBasePosFormat1
                        subtable header).
        
        >>> ma = _testingValues[0]
        >>> c = coverage.Coverage.fromglyphset(ma)
        >>> ma == MarkArray.frombytes(ma.binaryString(coverage=c), coverage=c)
        True
        """
        
        covTable = kwArgs['coverage']
        revTable = dict(zip(covTable.values(), covTable.keys()))
        r = cls()
        posBase = w.subWalker(0)
        fw = markrecord.MarkRecord.fromwalker
        kwArgs.pop('glyphIndex', None)
        kwArgs.pop('posBase', None)
        
        for i in range(w.unpack("H")):
            glyph = revTable[i]
            r[glyph] = fw(w, posBase=posBase, glyphIndex=glyph, **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        MarkArray({
          15: markrecord._testingValues[0],
          97: markrecord._testingValues[1]}),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
