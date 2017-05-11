#
# coordinate_device.py
#
# Copyright © 2010-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Items relating to device-modified coordinate values for OpenType BASE tables.

IMPORTANT NOTE: The OpenType spec (as of version 1.6) does not specify where
the offset to the Device record is calculated from. This code assumes the
offset is from the start of the BaseCoordFormat3 table itself; if this proves
inaccurate, this code will have to be modified.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta
from fontio3.opentype import device

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    try:
        n = int(round(obj))
    except:
        n = None
    
    # Note that if the value n is None (i.e. conversion or rounding failed)
    # the error is not raised here. Since this function is a partial, the
    # valuemeta isValid() checks will still be done, and the error will be
    # raised there instead.
    
    if n is not None and e is not None and e.reallyHas(b'head'):
        upem = e.head.unitsPerEm
        
        if abs(n) >= 2 * upem:
            logger.warning((
              'V0637',
              (n,),
              "The FUnit value %d is more than two ems away "
              "from the origin, which seems unlikely."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Coordinate_device(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing a coordinate value, a single integer in FUnits. This
    will be interpreted as X or Y depending on whether the object containing it
    is part of the horizontal or vertical baseline data.
    
    There is also one attribute:
    
        device      A Device object to be used to tweak the coordinate.
    
    >>> _testingValues[0].pprint()
    Coordinate: 25
    Device table:
      Tweak at 12 ppem: -2
      Tweak at 14 ppem: -1
      Tweak at 18 ppem: 1
    
    >>> logger = utilities.makeDoctestLogger("coordinate_device_test")
    >>> e = _fakeEditor()
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    coordinate_device_test - WARNING - The FUnit value -20000 is more than two ems away from the origin, which seems unlikely.
    True
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Coordinate",
        value_scales = True,
        value_validatefunc_partial = _validate)
    
    attrSpec = dict(
        device = dict(
            attr_followsprotocol = True,
            attr_initfunc = device.Device,
            attr_label = "Device table"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Coordinate_device object to the specified
        LinkedWriter. There is one optional keyword argument:
        
            devicePool      A dict mapping immutable versions of Devices to the
                            (Device, stake) pairs. If specified, the caller (or
                            a higher caller) is responsible for writing out the
                            pool when done. If not specified, a local pool will
                            be used and will be written here.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 0019 0006 000C  0012 0001 8C04      |..............  |
        
        >>> pool = {}
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, devicePool=pool)
        >>> _testingValues[1].buildBinary(w, devicePool=pool)
        >>> _testingValues[2].buildBinary(w, devicePool=pool)
        >>> for immut, (obj, stake) in sorted(
        ...   pool.items(),
        ...   key=(lambda x: sorted(x[0][1]))):
        ...     obj.buildBinary(w, stakeValue=stake)
        >>> utilities.hexdump(w.binaryString())
               0 | 0003 0019 001E 0003  FFF6 000C 0003 000F |................|
              10 | 0012 000C 0014 0002  BDF0 0020 3000 000C |........... 0...|
              20 | 0012 0001 8C04                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("Hh", 3, self)
        
        if 'devicePool' in kwArgs:
            pool = kwArgs['devicePool']
            immut = self.device.asImmutable(**kwArgs)
            
            if immut not in pool:
                pool[immut] = (self.device, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, pool[immut][1])
        
        else:
            stake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, stake)
            self.device.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Coordinate_device object from the specified
        walker, doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("coordinate_device_fvw")
        >>> fvb = Coordinate_device.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        coordinate_device_fvw.coordinate_device - DEBUG - Walker has 14 remaining bytes.
        coordinate_device_fvw.coordinate_device.device - DEBUG - Walker has 8 remaining bytes.
        coordinate_device_fvw.coordinate_device.device - DEBUG - StartSize=12, endSize=18, format=1
        coordinate_device_fvw.coordinate_device.device - DEBUG - Data are (35844,)
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:3], logger=logger)
        coordinate_device_fvw.coordinate_device - DEBUG - Walker has 3 remaining bytes.
        coordinate_device_fvw.coordinate_device - ERROR - Insufficient bytes.
        
        >>> fvb(s[2:4] * 2 + s[4:], logger=logger)
        coordinate_device_fvw.coordinate_device - DEBUG - Walker has 14 remaining bytes.
        coordinate_device_fvw.coordinate_device - ERROR - Expected format 3, but got 25 instead.
        
        >>> fvb(s[0:4]+utilities.fromhex("FF FF"), logger=logger)
        coordinate_device_fvw.coordinate_device - DEBUG - Walker has 6 remaining bytes.
        coordinate_device_fvw.coordinate_device - ERROR - The device offset of 65535 is beyond the available length 6.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("coordinate_device")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        wBase = w.subWalker(0, relative=True)  # needed for device base
        format, shift, devOffset = w.unpack("HhH")
        
        if format != 3:
            logger.error((
              'V0002',
              (format,),
              "Expected format 3, but got %d instead."))
            
            return None
        
        if devOffset >= wBase.length():
            logger.error((
              'V0639',
              (devOffset, wBase.length()),
              "The device offset of %d is beyond the available length %d."))
            
            return None
        
        dev = device.Device.fromvalidatedwalker(
          wBase.subWalker(devOffset),
          logger = logger,
          **kwArgs)
        
        if dev is None:
            return None
        
        return cls(shift, device=dev)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Coordinate_device object from the specified
        walker.
        
        >>> for i in range(3):
        ...     obj = _testingValues[i]
        ...     print(obj == Coordinate_device.frombytes(obj.binaryString()))
        True
        True
        True
        """
        
        wBase = w.subWalker(0, relative=True)
        format = w.unpack("H")
        
        if format != 3:
            raise ValueError(
              "Unknown format for Coordinate_device: %d" % (format,))
        
        n = w.unpack("h")
        
        dev = device.Device.fromwalker(
          wBase.subWalker(w.unpack("H")),
          **kwArgs)
        
        return cls(n, device=dev)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import operator
    from fontio3 import utilities
    from fontio3.utilities import writer
    
    def _fakeEditor():
        from fontio3.head import head
        
        e = utilities.fakeEditor(0x10000)
        e.head = head.Head()
        return e
    
    _dv = device._testingValues
    
    _testingValues = (
        Coordinate_device(25, device=_dv[0]),
        Coordinate_device(-10, device=_dv[1]),
        Coordinate_device(15, device=_dv[0]),
        # bad values start here
        Coordinate_device(-20000, device=_dv[0]))
    
    del _dv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
