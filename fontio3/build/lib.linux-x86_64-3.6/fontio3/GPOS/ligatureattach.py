#
# ligatureattach.py -- OpenType GPOS type 5 LigatureAttach objects
#
# Copyright © 2009-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType LigatureAttach objects (used in Mark-to-Ligature GPOS
lookups).
"""

# System imports
import functools
import logging
import itertools

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.GPOS import componentrecord

# -----------------------------------------------------------------------------

#
# Classes
#

class LigatureAttach(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects containing base attachment information for each component of a
    ligature. These are lists of ComponentRecord objects.
    
    >>> _testingValues[0].pprint()
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
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Ligature Component #%d" % (i + 1,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 0000 0012 0000  0018 0020 0000 0000 |........... ....|
              10 | 002A 0001 FFD8 0012  0002 FFD8 0012 0006 |.*..............|
              20 | 0003 000A 0014 0010  0000 0001 0000 0000 |................|
              30 | 000C 0012 0001 8C04                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        devicePool = kwArgs.pop('devicePool', None)
        anchorPool = kwArgs.pop('anchorPool', None)
        assert (devicePool is None) == (anchorPool is None)
        orderedKeys = kwArgs.pop('orderedKeys', [])
        kwArgs.pop('posBase', None)
        
        if anchorPool is None:
            anchorPool = {}
            devicePool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        for obj in self:
            assert obj is not None
            
            obj.buildBinary(
              w,
              posBase = stakeValue,
              anchorPool = anchorPool,
              devicePool = devicePool,
              orderedKeys = orderedKeys,
              **kwArgs)
        
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
        Creates and returns a LigatureAttach objects from the specified
        walker, doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("ligatureattach_test")
        >>> fvb = LigatureAttach.fromvalidatedbytes
        >>> obj = fvb(s, classCount=4, glyphIndex=40, logger=logger)
        ligatureattach_test.ligatureattach - DEBUG - Walker has 56 bytes remaining.
        ligatureattach_test.ligatureattach.ligature component 0.componentrecord - DEBUG - Walker has 54 bytes remaining.
        ligatureattach_test.ligatureattach.ligature component 0.componentrecord.[1].anchor_coord - DEBUG - Walker has 38 remaining bytes.
        ligatureattach_test.ligatureattach.ligature component 0.componentrecord.[3].anchor_point - DEBUG - Walker has 32 remaining bytes.
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord - DEBUG - Walker has 46 bytes remaining.
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord.[0].anchor_device - DEBUG - Walker has 24 remaining bytes.
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord.[0].anchor_device.x.device - DEBUG - Data are (35844,)
        ligatureattach_test.ligatureattach.ligature component 1.componentrecord.[3].anchor_coord - DEBUG - Walker has 14 remaining bytes.
        
        >>> fvb(s[:1], classCount=4, glyphIndex=40, logger=logger)
        ligatureattach_test.ligatureattach - DEBUG - Walker has 1 bytes remaining.
        ligatureattach_test.ligatureattach - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("ligatureattach")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        posBase = w.subWalker(0)
        count = w.unpack("H")
        fvw = componentrecord.ComponentRecord.fromvalidatedwalker
        r = cls([None] * count)
        kwArgs.pop('posBase', None)
        
        for i in range(count):
            subLogger = logger.getChild("ligature component %d" % (i,))
            obj = fvw(w, posBase=posBase, logger=subLogger, **kwArgs)
            
            if obj is None:
                return None
            
            r[i] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a LigatureAttach from the specified walker.
        
        >>> lat = _testingValues[0]
        >>> s = lat.binaryString()
        >>> lat == LigatureAttach.frombytes(s, classCount=4, glyphIndex=40)
        True
        """
        
        posBase = w.subWalker(0)
        count = w.unpack("H")
        f = componentrecord.ComponentRecord.fromwalker
        kwArgs.pop('posBase', None)
        func = functools.partial(f, posBase=posBase, **kwArgs)
        return cls(map(func, itertools.repeat(w, count)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    c = componentrecord._testingValues
    
    _testingValues = (
        LigatureAttach([c[0], c[1]]),
        LigatureAttach([c[2], c[3]]),
        LigatureAttach([c[1], c[4]]))
    
    del c

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
