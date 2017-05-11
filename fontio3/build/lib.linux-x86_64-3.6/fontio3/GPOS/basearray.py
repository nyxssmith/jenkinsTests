#
# basearray.py -- definition of an OpenType BaseArray
#
# Copyright © 2009-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of the BaseArray class, used to support mark-related
positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GPOS import baserecord
from fontio3.opentype import coverage

# -----------------------------------------------------------------------------

#
# Classes
#

class BaseArray(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects associating base glyphs with all possible anchor points. These are
    dicts mapping glyph indices to BaseRecord objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    afii60003:
      Class 0:
        x-coordinate: 10
        y-coordinate: 20
        Device for x:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      Class 1:
        (no data)
      Class 2:
        (no data)
      Class 3:
        x-coordinate: -40
        y-coordinate: 18
    xyz41:
      Class 0:
        (no data)
      Class 1:
        x-coordinate: -40
        y-coordinate: 18
      Class 2:
        x-coordinate: 10
        y-coordinate: 20
        Device for x:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      Class 3:
        x-coordinate: -40
        y-coordinate: 18
        Contour point index: 6
        Glyph index: 40
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> _testingValues[0].isValid(logger=logger, editor=_fakeEditor())
    ivtest.[40].[3] - WARNING - Point 6 in glyph 40 has coordinates (950, 750), but the Anchor data in this object are (-40, 18).
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatekwargsfunc = (lambda x, k: {'glyphIndex': k}),
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
               0 | 0002 0000 0012 0018  0022 0018 0000 0000 |........."......|
              10 | 0012 0001 FFD8 0012  0003 000A 0014 0012 |................|
              20 | 0000 0002 FFD8 0012  0006 000C 0012 0001 |................|
              30 | 8C04                                     |..              |
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
        # We ignore the output from the following; we only want the side-effect
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
        Creates and returns a new BaseArray from the specified walker, doing
        source validation. The following keyword arguments are used:
        
            classCount  Number of classes per BaseRecord. This is not used
                        directly in this method, but is passed through to the
                        BaseRecord fromvalidatedwalker() call.
            
            coverage    A Coverage object (from the MarkBasePosFormat1
                        subtable header).
            
            logger      A logger to which messages will be posted.
        
        >>> bat = _testingValues[0]
        >>> c = coverage.Coverage.fromglyphset(bat)
        >>> s = bat.binaryString(coverage=c)
        >>> logger = utilities.makeDoctestLogger("basearray_test")
        >>> fvb = BaseArray.fromvalidatedbytes
        >>> obj = fvb(s, coverage=c, classCount=4, logger=logger)
        basearray_test.basearray - DEBUG - Walker has 50 remaining bytes.
        basearray_test.basearray.glyph 40.baserecord - DEBUG - Walker has 48 bytes remaining.
        basearray_test.basearray.glyph 40.baserecord.[1].anchor_coord - DEBUG - Walker has 32 remaining bytes.
        basearray_test.basearray.glyph 40.baserecord.[2].anchor_device - DEBUG - Walker has 26 remaining bytes.
        basearray_test.basearray.glyph 40.baserecord.[2].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        basearray_test.basearray.glyph 40.baserecord.[2].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        basearray_test.basearray.glyph 40.baserecord.[2].anchor_device.x.device - DEBUG - Data are (35844,)
        basearray_test.basearray.glyph 40.baserecord.[3].anchor_point - DEBUG - Walker has 16 remaining bytes.
        basearray_test.basearray.glyph 98.baserecord - DEBUG - Walker has 40 bytes remaining.
        basearray_test.basearray.glyph 98.baserecord.[0].anchor_device - DEBUG - Walker has 26 remaining bytes.
        basearray_test.basearray.glyph 98.baserecord.[0].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        basearray_test.basearray.glyph 98.baserecord.[0].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        basearray_test.basearray.glyph 98.baserecord.[0].anchor_device.x.device - DEBUG - Data are (35844,)
        basearray_test.basearray.glyph 98.baserecord.[3].anchor_coord - DEBUG - Walker has 32 remaining bytes.
        
        >>> fvb(s[:1], coverage=c, classCount=4, logger=logger)
        basearray_test.basearray - DEBUG - Walker has 1 remaining bytes.
        basearray_test.basearray - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("basearray")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        covTable = kwArgs.pop('coverage')
        assert 'classCount' in kwArgs
        # The revTable dict maps coverage indices to glyphs
        revTable = dict(zip(covTable.values(), covTable.keys()))
        r = cls()
        posBase = w.subWalker(0)
        fvw = baserecord.BaseRecord.fromvalidatedwalker
        count = w.unpack("H")
        kwArgs.pop('posBase', None)
        kwArgs.pop('glyphIndex', None)
        
        for i in range(count):
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
        Creates and returns a new BaseArray from the specified walker. Two
        keyword arguments are used:
        
            classCount  Number of classes per BaseRecord. This is not used
                        directly in this method, but is passed through to the
                        BaseRecord fromwalker() call.
        
            coverage    A Coverage object (from the MarkBasePosFormat1
                        subtable header).
        
        >>> bat = _testingValues[0]
        >>> c = coverage.Coverage.fromglyphset(bat)
        >>> bs = bat.binaryString(coverage=c)
        >>> bat == BaseArray.frombytes(bs, coverage=c, classCount=4)
        True
        """
        
        covTable = kwArgs.pop('coverage')
        assert 'classCount' in kwArgs
        # The revTable dict maps coverage indices to glyphs
        revTable = dict(zip(covTable.values(), covTable.keys()))
        r = cls()
        posBase = w.subWalker(0)
        func = baserecord.BaseRecord.fromwalker
        kwArgs.pop('posBase', None)
        kwArgs.pop('glyphIndex', None)
        
        for i in range(w.unpack("H")):
            glyph = revTable[i]
            r[glyph] = func(w, posBase=posBase, glyphIndex=glyph, **kwArgs)
        
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
    
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e
    
    _testingValues = (
        BaseArray({
          40: baserecord._testingValues[0],
          98: baserecord._testingValues[1]}),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
