#
# anchor_device.py
#
# Copyright © 2007-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Common anchor objects for OpenType tables.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import anchor_coord
from fontio3.opentype import device

# -----------------------------------------------------------------------------

#
# Classes
#

class Anchor_Device(anchor_coord.Anchor_Coord):
    """
    Objects representing anchored locations, via FUnit values and two
    associated Device objects, one for x and one for y.
    
    >>> _testingValues[0].pprint()
    x-coordinate: 10
    y-coordinate: 20
    Device for x:
      Tweak at 12 ppem: -2
      Tweak at 14 ppem: -1
      Tweak at 18 ppem: 1
    
    >>> _testingValues[0].anchorKind
    'device'
    
    >>> logger = utilities.makeDoctestLogger("anchor_device_val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    anchor_device_val.[0] - ERROR - The value -4.5 is not an integer.
    anchor_device_val.[1] - ERROR - The signed value 40000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    # Since we inherit from Anchor_Coord, we
    # only need to define the extra attributes.
    
    attrSpec = dict(
        xDevice = dict(
            attr_followsprotocol = True,
            attr_label = "Device for x",
            attr_representsx = True,
            attr_showonlyiftrue = True),
        
        yDevice = dict(
            attr_followsprotocol = True,
            attr_label = "Device for y",
            attr_representsy = True,
            attr_showonlyiftrue = True))
    
    anchorKind = 'device'
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. There is one
        keyword argument:
        
            devicePool      A dict mapping device IDs to Device objects. This
                            is optional; if not specified a local pool will be
                            used and will be written after the main content. If
                            a devicePool is specified, the writing will be left
                            up to the higher-level caller.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 000A 0014 000A  0000 000C 0012 0001 |................|
              10 | 8C04                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        devicePool = kwArgs.pop('devicePool', None)
        
        if devicePool is None:
            devicePool = {}
            doLocal = True
        else:
            doLocal = False
        
        w.add("H2h", 3, *self)
        
        for obj in (self.xDevice, self.yDevice):
            if obj:
                devID = id(obj)
                
                if devID not in devicePool:
                    devicePool[devID] = (obj, w.getNewStake())
                
                w.addUnresolvedOffset("H", stakeValue, devicePool[devID][1])
            
            else:
                w.add("H", 0)
        
        if doLocal:
            # we decorate-sort to ensure a repeatable, canonical ordering
            
            it = sorted(
              (obj.asImmutable(), obj, stake)
              for obj, stake in devicePool.values())
            
            for t in it:
                t[1].buildBinary(w, stakeValue=t[2], **kwArgs)
        
        else:
            kwArgs['devicePool'] = devicePool
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Device object, including validation of the input
        source.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> e = utilities.fakeEditor(0x10000)
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Anchor_Device.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, editor=e)
        test.anchor_device - DEBUG - Walker has 18 remaining bytes.
        test.anchor_device.x.device - DEBUG - Walker has 8 remaining bytes.
        test.anchor_device.x.device - DEBUG - StartSize=12, endSize=18, format=1
        test.anchor_device.x.device - DEBUG - Data are (35844,)
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('anchor_device')
        else:
            logger = logger.getChild('anchor_device')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 3:
            logger.error((
              'V0002',
              (format,),
              "Was expecting format 3, but got %d instead."))
            
            return None
        
        argDict = {}
        x, y = w.unpack("2h")
        xDevOffset, yDevOffset = w.unpack("2H")
        fvw = device.Device.fromvalidatedwalker
        
        if xDevOffset:
            subLogger = logger.getChild("x")
            argDict['xDevice'] = fvw(w.subWalker(xDevOffset), logger=subLogger)
        
        if yDevOffset:
            subLogger = logger.getChild("y")
            argDict['yDevice'] = fvw(w.subWalker(yDevOffset), logger=subLogger)
        
        return cls(x, y, **argDict)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Device object from the specified walker.
        
        >>> atd = _testingValues[0]
        >>> atd == Anchor_Device.frombytes(atd.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 3:
            raise ValueError(
              "Unknown format for Anchor_Device: %d" %
              (format,))
        
        argDict = {}
        x, y = w.unpack("2h")
        xDevOffset, yDevOffset = w.unpack("2H")
        
        if xDevOffset:
            argDict['xDevice'] = device.Device.fromwalker(
              w.subWalker(xDevOffset))
        
        if yDevOffset:
            argDict['yDevice'] = device.Device.fromwalker(
              w.subWalker(yDevOffset))
        
        return cls(x, y, **argDict)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Anchor_Device(10, 20, xDevice=device._testingValues[0]),
        Anchor_Device(-25, 120, yDevice=device._testingValues[1]),
        Anchor_Device(0, 50, xDevice=device._testingValues[2]),
        
        # bad values start here
        
        Anchor_Device(-4.5, 40000, xDevice=None, yDevice=None))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
