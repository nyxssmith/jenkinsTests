#
# ligaturearray.py -- definition of an OpenType LigatureArray
#
# Copyright © 2009-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definition of the LigatureArray class, used to support mark-related
positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GPOS import ligatureattach

# -----------------------------------------------------------------------------

class LigatureArray(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects associating ligature glyphs with all possible anchor points. These
    are dicts mapping glyph indices to LigatureAttach objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    U+0163:
      Ligature Component #1:
        Class 0:
          x-coordinate: 0
          y-coordinate: 40
        Class 1:
          x-coordinate: -25
          y-coordinate: 120
          Device for y:
            Tweak at 12 ppem: -5
            Tweak at 13 ppem: -3
            Tweak at 14 ppem: -1
            Tweak at 18 ppem: 2
            Tweak at 20 ppem: 3
        Class 2:
          x-coordinate: -180
          y-coordinate: 0
        Class 3:
          x-coordinate: 0
          y-coordinate: 0
          Contour point index: 4
          Glyph index: 99
      Ligature Component #2:
        Class 0:
          x-coordinate: 0
          y-coordinate: 50
          Device for x:
            Tweak at 12 ppem: -9
            Tweak at 16 ppem: 20
        Class 1:
          x-coordinate: 0
          y-coordinate: 50
          Device for x:
            Tweak at 12 ppem: -9
            Tweak at 16 ppem: 20
        Class 2:
          (no data)
        Class 3:
          (no data)
    xyz17:
      Ligature Component #1:
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
          x-coordinate: 0
          y-coordinate: 0
      Ligature Component #2:
        Class 0:
          x-coordinate: 0
          y-coordinate: 48
          Contour point index: 0
          Glyph index: 16
        Class 1:
          (no data)
        Class 2:
          x-coordinate: -10
          y-coordinate: 0
          Contour point index: 9
          Glyph index: 16
        Class 3:
          x-coordinate: -10
          y-coordinate: 0
          Contour point index: 9
          Glyph index: 16
    xyz41:
      Ligature Component #1:
        Class 0:
          (no data)
        Class 1:
          x-coordinate: -40
          y-coordinate: 18
        Class 2:
          (no data)
        Class 3:
          x-coordinate: -40
          y-coordinate: 18
          Contour point index: 6
          Glyph index: 40
      Ligature Component #2:
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
          x-coordinate: 0
          y-coordinate: 0
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatekwargsfunc = (lambda x,k: {'glyphIndex': k}),
        map_maxcontextfunc = (lambda d: 1))  # this is GPOS
    
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
               0 | 0003 0008 001A 002C  0002 0036 0000 0000 |.......,...6....|
              10 | 0040 0046 0000 004E  004E 0002 0000 0044 |.@.F...N.N.....D|
              20 | 0000 004A 0024 0000  0000 002E 0002 0040 |...J.$.........@|
              30 | 0046 0050 0056 005E  005E 0000 0000 0003 |.F.P.V.^.^......|
              40 | 000A 0014 006E 0000  0001 0000 0000 0002 |.....n..........|
              50 | 0000 0030 0000 0002  FFF6 0000 0009 0001 |...0............|
              60 | FFD8 0012 0002 FFD8  0012 0006 0001 0000 |................|
              70 | 0028 0003 FFE7 0078  0000 002E 0001 FF4C |.(.....x.......L|
              80 | 0000 0002 0000 0000  0004 0003 0000 0032 |...............2|
              90 | 000A 0000 000C 0010  0003 F700 0000 1400 |................|
              A0 | 000C 0014 0002 BDF0  0020 3000 000C 0012 |......... 0.....|
              B0 | 0001 8C04                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        kad = kwArgs.copy()
        anchorPool = kad.pop('anchorPool', None)
        devicePool = kad.pop('devicePool', None)
        assert (anchorPool is None) == (devicePool is None)
        orderedKeys = kwArgs.pop('orderedKeys', [])
        
        if anchorPool is None:
            anchorPool = {}
            devicePool = {}
            doLocal = True
        else:
            doLocal = False
        
        w.add("H", len(self))
        localPool = {}
        
        for covIndex, glyphIndex in enumerate(sorted(self)):
            latID = id(self[glyphIndex])
            
            if latID not in localPool:
                localPool[latID] = (self[glyphIndex], w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, localPool[latID][1])
        
        kad['anchorPool'] = anchorPool
        kad['devicePool'] = devicePool
        kad['orderedKeys'] = orderedKeys
        
        for obj, stake in localPool.values():
            obj.buildBinary(w, stakeValue=stake, **kad)
        
        # Resolve the references
        if doLocal:
            for key in orderedKeys:
                obj, objStake = anchorPool[key]
                obj.buildBinary(w, stakeValue=objStake, devicePool=devicePool)
            
            it = sorted(
              (sorted(obj.asImmutable()[1]), obj, stake)
              for obj, stake in devicePool.values())
            
            for immut, obj, objStake in it:
                obj.buildBinary(w, stakeValue=objStake)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LigatureArray object from the specified
        walker, doing source validation. The following keyword arguments are
        supported:
        
            classCount      Passed through to lower constructors.
            
            coverage        A Coverage object (from the MarkLigPosFormat1
                            subtable header).
            
            logger          A logger to which messages will be posted.
        
        >>> lat = _testingValues[0]
        >>> c = coverage.Coverage.fromglyphset(lat)
        >>> s = lat.binaryString()
        >>> logger = utilities.makeDoctestLogger("ligaturearray_test")
        >>> fvb = LigatureArray.fromvalidatedbytes
        >>> obj = fvb(s, coverage=c, classCount=4, logger=logger)
        ligaturearray_test.ligaturearray - DEBUG - Walker has 180 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach - DEBUG - Walker has 172 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 170 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord.[0].anchor_device - DEBUG - Walker has 118 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord.[0].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord.[0].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord.[0].anchor_device.x.device - DEBUG - Data are (35844,)
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 0.componentrecord.[3].anchor_coord - DEBUG - Walker has 108 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 162 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 1.componentrecord.[0].anchor_point - DEBUG - Walker has 102 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 1.componentrecord.[2].anchor_point - DEBUG - Walker has 94 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 16.ligatureattach.ligature component 1.componentrecord.[3].anchor_point - DEBUG - Walker has 94 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach - DEBUG - Walker has 154 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 152 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord.[1].anchor_coord - DEBUG - Walker has 86 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 0.componentrecord.[3].anchor_point - DEBUG - Walker has 80 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 144 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[0].anchor_device - DEBUG - Walker has 118 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Data are (35844,)
        ligaturearray_test.ligaturearray.glyph 40.ligatureattach.ligature component 1.componentrecord.[3].anchor_coord - DEBUG - Walker has 108 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach - DEBUG - Walker has 136 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 134 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[0].anchor_coord - DEBUG - Walker has 72 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[1].anchor_device - DEBUG - Walker has 66 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[1].anchor_device.y.device - DEBUG - Walker has 20 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[1].anchor_device.y.device - DEBUG - StartSize=12, endSize=20, format=2
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[1].anchor_device.y.device - DEBUG - Data are (48624, 32, 12288)
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[2].anchor_coord - DEBUG - Walker has 56 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 0.componentrecord.[3].anchor_point - DEBUG - Walker has 50 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 126 bytes remaining.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[0].anchor_device - DEBUG - Walker has 42 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Walker has 32 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - StartSize=12, endSize=16, format=3
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Data are (63232, 0, 5120)
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[1].anchor_device - DEBUG - Walker has 42 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[1].anchor_device.x.device - DEBUG - Walker has 32 remaining bytes.
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[1].anchor_device.x.device - DEBUG - StartSize=12, endSize=16, format=3
        ligaturearray_test.ligaturearray.glyph 99.ligatureattach.ligature component 1.componentrecord.[1].anchor_device.x.device - DEBUG - Data are (63232, 0, 5120)
        
        >>> fvb(s[:1], coverage=c, classCount=4, logger=logger)
        ligaturearray_test.ligaturearray - DEBUG - Walker has 1 remaining bytes.
        ligaturearray_test.ligaturearray - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("ligaturearray")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        assert 'classCount' in kwArgs
        sortedKeys = sorted(kwArgs['coverage'])
        offsetCount = w.unpack("H")
        
        if offsetCount != len(sortedKeys):
            logger.error((
              'V0345',
              (len(sortedKeys), offsetCount),
              "The Coverage has %d indices, but the LigatureCount is %d."))
            
            return None
        
        if w.length() < 2 * offsetCount:
            logger.error((
              'V0346',
              (),
              "Insufficient bytes for the LigatureAttach offsets."))
            
            return None
        
        r = cls()
        fvw = ligatureattach.LigatureAttach.fromvalidatedwalker
        kwArgs.pop('glyphIndex', None)
        
        for i, offset in enumerate(w.group("H", offsetCount)):
            wSub = w.subWalker(offset)
            glyph = sortedKeys[i]
            subLogger = logger.getChild("glyph %d" % (glyph,))
            obj = fvw(wSub, glyphIndex=glyph, logger=subLogger, **kwArgs)
            
            if obj is None:
                return None
            
            r[glyph] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LigatureArray object from the specified
        walker. One keyword argument is used:
        
            coverage    A Coverage object (from the MarkLigPosFormat1
                        subtable header).
        
        In addition, the classCount (number of mark classes) is passed down to
        the other constructors, but is not used directly in this method.
        
        >>> lat = _testingValues[0]
        >>> covTable = coverage.Coverage.fromglyphset(lat)
        >>> s = lat.binaryString()
        >>> lat == LigatureArray.frombytes(s, coverage=covTable, classCount=4)
        True
        """
        
        assert 'classCount' in kwArgs
        sortedKeys = sorted(kwArgs['coverage'])
        offsetCount = w.unpack("H")
        
        if offsetCount != len(sortedKeys):
            raise ValueError(
              "LigatureArray coverage count does not equal offsets count!")
        
        r = cls()
        fw = ligatureattach.LigatureAttach.fromwalker
        kwArgs.pop('glyphIndex', None)
        
        for i, offset in enumerate(w.group("H", offsetCount)):
            wSub = w.subWalker(offset)
            glyph = sortedKeys[i]
            r[glyph] = fw(wSub, glyphIndex=glyph, **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype import coverage
    from fontio3.utilities import namer
    
    la = ligatureattach._testingValues
    
    _testingValues = (
        LigatureArray({40: la[0], 99: la[1], 16: la[2]}),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
