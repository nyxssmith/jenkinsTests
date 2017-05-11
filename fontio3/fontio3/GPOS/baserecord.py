#
# baserecord.py -- definition of an OpenType BaseRecord
#
# Copyright © 2009-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of the BaseRecord class, used to support mark-related positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.GPOS import anchor

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not any(obj):
        logger.warning((
          'V0338',
          (),
          "All the anchors in the BaseRecord are empty, so the BaseRecord "
          "has no effect and may be removed."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BaseRecord(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a single BaseRecord. These are lists whose indices are
    markClasses and whose entries are either None or else objects of one of the
    Anchor variant classes.
    
    >>> _testingValues[0].pprint()
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
    
    >>> _testingValues[1].pprint()
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
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    ivtest.[3] - WARNING - Point 6 in glyph 40 has coordinates (950, 750), but the Anchor data in this object are (-40, 18).
    True
    
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    ivtest - WARNING - All the anchors in the BaseRecord are empty, so the BaseRecord has no effect and may be removed.
    True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Class %d" % (i,)),
        seq_validatefunc_partial = _validate)
    
    _childLogName = "baserecord"
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. There are three
        keyword arguments:
        
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
            
            posBase         The stake for the base array.
        
        >>> wTest = writer.LinkedWriter()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> wTest.add("l", -1)  # fake base array contents
        >>> _testingValues[0].buildBinary(wTest, posBase="test stake")
        >>> utilities.hexdump(wTest.binaryString())
               0 | FFFF FFFF 0000 000C  0012 001C 0001 FFD8 |................|
              10 | 0012 0003 000A 0014  0012 0000 0002 FFD8 |................|
              20 | 0012 0006 000C 0012  0001 8C04           |............    |
        """
        
        posBase = kwArgs['posBase']  # stake for base array base
        devicePool = kwArgs.get('devicePool', None)
        anchorPool = kwArgs.get('anchorPool', None)
        assert (devicePool is None) == (anchorPool is None)
        orderedKeys = kwArgs.get('orderedKeys', [])
        
        if anchorPool is None:
            anchorPool = {}
            devicePool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        for obj in self:
            if obj is not None:
                immut = obj.asImmutable()
                
                if immut not in anchorPool:
                    anchorPool[immut] = (obj, w.getNewStake())
                    orderedKeys.append(immut)
                
                w.addUnresolvedOffset("H", posBase, anchorPool[immut][1])
            
            else:
                w.add("H", 0)
        
        # if we're local, resolve the references
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
        Creates and returns a new BaseRecord from the specified walker, doing
        source validation.
        
        >>> br1 = _testingValues[0]
        >>> wTest = writer.LinkedWriter()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> br1.buildBinary(wTest, posBase="test stake")
        >>> s = wTest.binaryString()
        >>> logger = utilities.makeDoctestLogger("baserecord_test")
        >>> fvb = BaseRecord.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, classCount=4, glyphIndex=40)
        baserecord_test.baserecord - DEBUG - Walker has 40 bytes remaining.
        baserecord_test.baserecord.[1].anchor_coord - DEBUG - Walker has 32 remaining bytes.
        baserecord_test.baserecord.[2].anchor_device - DEBUG - Walker has 26 remaining bytes.
        baserecord_test.baserecord.[2].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        baserecord_test.baserecord.[2].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        baserecord_test.baserecord.[2].anchor_device.x.device - DEBUG - Data are (35844,)
        baserecord_test.baserecord.[3].anchor_point - DEBUG - Walker has 16 remaining bytes.
        
        >>> obj = fvb(s[:5], logger=logger, classCount=4, glyphIndex=40)
        baserecord_test.baserecord - DEBUG - Walker has 5 bytes remaining.
        baserecord_test.baserecord - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild(cls._childLogName)
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        posBase = kwArgs.pop('posBase', w)
        count = kwArgs.pop('classCount')
        
        if w.length() < 2 * count:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        offsets = w.group("H", count)
        fvw = anchor.Anchor_validated
        v = [None] * count
        
        for i, offset in enumerate(offsets):
            if offset:
                subLogger = logger.getChild("[%d]" % (i,))
                
                obj = fvw(
                  posBase.subWalker(offset),
                  logger = subLogger,
                  **kwArgs)
                
                if obj is None:
                    return None
                
                v[i] = obj
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new BaseRecord from the specified walker. Two
        keyword arguments are used:
        
            classCount      The number of markClasses.
            posBase         The walker representing the BaseArray's start.
        
        >>> br1 = _testingValues[0]
        >>> wTest = writer.LinkedWriter()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> br1.buildBinary(wTest, posBase="test stake")
        >>> bs = wTest.binaryString()
        >>> walk = walkerbit.StringWalker(bs)
        >>> br2 = BaseRecord.fromwalker(
        ...   walk,
        ...   classCount = 4,
        ...   posBase = walk.subWalker(0),
        ...   glyphIndex = 40)
        >>> br1 == br2
        True
        """
        
        posBase = kwArgs.pop('posBase')
        count = kwArgs.pop('classCount')
        offsets = w.group("H", count)
        func = anchor.Anchor
        
        return cls(
          (func(posBase.subWalker(offset), **kwArgs) if offset else None)
          for offset in offsets)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.GPOS import anchor_coord, anchor_device, anchor_point
    from fontio3.utilities import walkerbit, writer
    
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e
    
    cv = anchor_coord._testingValues
    dv = anchor_device._testingValues
    pv = anchor_point._testingValues
    
    _testingValues = (
        BaseRecord([None, cv[0], dv[0], pv[0]]),
        BaseRecord([dv[0], None, None, cv[0]]),
        BaseRecord([None, None, None, None]))
    
    del cv, dv, pv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
