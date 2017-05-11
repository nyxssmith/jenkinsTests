#
# markrecord.py -- definition of an OpenType MarkRecord
#
# Copyright © 2009-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of the MarkRecord class, used to support mark-related positioning.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.GPOS import anchor
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_markAnchor(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.error((
          'V0342',
          (),
          "The markAnchor value is missing or has no effect."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MarkRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single MarkRecord, comprising a markClass and a
    markAnchor.
    
    >>> _testingValues[0].pprint()
    Mark Class: 3
    Mark Anchor:
      x-coordinate: -40
      y-coordinate: 18
    
    >>> _testingValues[1].pprint()
    Mark Class: 1
    Mark Anchor:
      x-coordinate: 10
      y-coordinate: 20
      Device for x:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    ivtest.markAnchor - ERROR - The markAnchor value is missing or has no effect.
    ivtest.markClass - ERROR - The markClass value -1 cannot be used in an unsigned field.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markClass = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Mark Class",
            attr_validatefunc = functools.partial(
              valassist.isNumber_integer_unsigned,
              numBits = 16,
              label = "markClass value")),
        
        markAnchor = dict(
            attr_followsprotocol = True,
            attr_label = "Mark Anchor",
            attr_validatefunc_partial = _validate_markAnchor))
    
    attrSorted = ('markClass', 'markAnchor')
    
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
        >>> wTest.add("h", -1)  # fake mark array contents
        >>> _testingValues[0].buildBinary(wTest, posBase="test stake")
        >>> utilities.hexdump(wTest.binaryString())
               0 | FFFF 0003 0006 0001  FFD8 0012           |............    |
        
        >>> wTest.reset()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> wTest.add("l", -1)  # fake mark array contents
        >>> _testingValues[1].buildBinary(wTest, posBase="test stake")
        >>> utilities.hexdump(wTest.binaryString())
               0 | FFFF FFFF 0001 0008  0003 000A 0014 000A |................|
              10 | 0000 000C 0012 0001  8C04                |..........      |
        
        >>> wTest.reset()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> wTest.add("h", -1)  # fake mark array contents
        >>> _testingValues[2].buildBinary(wTest, posBase="test stake")
        >>> utilities.hexdump(wTest.binaryString())
               0 | FFFF 0002 0006 0002  FFD8 0012 0006      |..............  |
        """
        
        posBase = kwArgs['posBase']  # stake for mark array base
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
        
        w.add("H", self.markClass)
        
        if self.markAnchor is None:
            raise ValueError("Missing mark anchor!")
        
        immut = self.markAnchor.asImmutable()
        
        if immut not in anchorPool:
            anchorPool[immut] = (self.markAnchor, w.getNewStake())
            orderedKeys.append(immut)
        
        w.addUnresolvedOffset("H", posBase, anchorPool[immut][1])
        
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
        Creates and returns a new MarkRecord from the specified walker, doing
        source validation. The following keyword arguments are supported:
        
            logger      A logger to which messages will be posted.
            
            posBase     The walker representing the MarkArray's start. This
                        is required.
        
        >>> wTest = writer.LinkedWriter()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> _testingValues[1].buildBinary(wTest, posBase="test stake")
        >>> s = wTest.binaryString()
        >>> logger = utilities.makeDoctestLogger("markrecord_test")
        >>> fvb = MarkRecord.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, posBase=walkerbit.StringWalker(s))
        markrecord_test.markrecord - DEBUG - Walker has 22 bytes remaining.
        markrecord_test.markrecord.anchor_device - DEBUG - Walker has 18 remaining bytes.
        markrecord_test.markrecord.anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        markrecord_test.markrecord.anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        markrecord_test.markrecord.anchor_device.x.device - DEBUG - Data are (35844,)
        
        >>> fvb(s[:3], logger=logger, posBase=walkerbit.StringWalker(s))
        markrecord_test.markrecord - DEBUG - Walker has 3 bytes remaining.
        markrecord_test.markrecord - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("markrecord")
        otcd = kwArgs.get("otcommondeltas")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        posBase = kwArgs.pop('posBase')
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        mc, maOffset = w.unpack("2H")
        
        a = anchor.Anchor_validated(
          posBase.subWalker(maOffset),
          logger = logger,
          glyphIndex = kwArgs.get('glyphIndex', None),
          otcommondeltas = otcd)
        
        if a is None:
            return None
        
        return cls(markClass=mc, markAnchor=a)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkRecord from the specified walker. One
        keyword argument is used:
        
            posBase     The walker representing the MarkArray's start
        
        >>> wTest = writer.LinkedWriter()
        >>> wTest.stakeCurrentWithValue("test stake")
        >>> _testingValues[1].buildBinary(wTest, posBase="test stake")
        >>> bs = wTest.binaryString()
        >>> walk = walkerbit.StringWalker(bs)
        >>> mr = MarkRecord.fromwalker(walk, posBase=walk.subWalker(0))
        >>> mr == _testingValues[1]
        True
        """
        
        otcd = kwArgs.get('otcommondeltas')
        
        posBase = kwArgs['posBase']  # walker based at start of mark array
        mc, maOffset = w.unpack("2H")
        
        a = anchor.Anchor(
          posBase.subWalker(maOffset),
          glyphIndex = kwArgs.get('glyphIndex', None),
          otcommondeltas=otcd)
        
        return cls(markClass=mc, markAnchor=a)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.GPOS import anchor_coord, anchor_device, anchor_point
    from fontio3.opentype import device
    from fontio3.utilities import walkerbit, writer
    
    _testingValues = (
        MarkRecord(3, anchor_coord._testingValues[0]),
        MarkRecord(1, anchor_device._testingValues[0]),
        MarkRecord(2, anchor_point._testingValues[0]),
        MarkRecord(-1, None))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
