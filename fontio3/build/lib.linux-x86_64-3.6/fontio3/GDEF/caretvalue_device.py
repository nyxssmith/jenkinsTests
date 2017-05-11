#
# caretvalue_device.py
#
# Copyright © 2005-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to ligature caret positioning.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import valuemeta
from fontio3.opentype import device
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class CaretValue_Device(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing the most complex kind of caret value: a single, signed
    value in FUnits with an associated Device object.
    
    >>> c = _testingValues[0]
    >>> c.pprint()
    Caret value in FUnits: 500
    Device record:
      Tweak at 12 ppem: -2
      Tweak at 13 ppem: -1
      Tweak at 16 ppem: 1
      Tweak at 17 ppem: 2
    >>> c < 700  # treat it as a regular number
    True
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Caret value in FUnits",
        value_scales = True,
        value_validatefunc = valassist.isFormat_h)
    
    attrSpec = dict(
        deviceRecord = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = device.Device,
            attr_label = "Device record"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter. There is one
        keyword argument:
        
            devicePool      If specified should be a dict for the device pool.
                            If not specified, a local pool will be used and the
                            Device binary will be written locally.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 01F4 0006 000C  0011 0002 EF00 1200 |................|
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
        
        deviceID = id(self.deviceRecord)
        
        if deviceID not in devicePool:
            devicePool[deviceID] = (self.deviceRecord, w.getNewStake())
        
        w.add("Hh", 3, self)
        w.addUnresolvedOffset("H", stakeValue, devicePool[deviceID][1])
        
        if doLocal:
            for obj, devStake in devicePool.values():
                obj.buildBinary(w, stakeValue=devStake, **kwArgs)
        
        else:
            kwArgs['devicePool'] = devicePool
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new CaretValue_Device.
        However, it also does extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('testD')
        >>> s = _testingValues[0].binaryString()
        >>> fvb = CaretValue_Device.fromvalidatedbytes
        >>> fvb(s[:1], logger=logger)
        testD.device - DEBUG - Walker has 1 remaining bytes.
        testD.device - ERROR - Insufficient bytes.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        testD.device - DEBUG - Walker has 16 remaining bytes.
        testD.device - ERROR - Expected format 3 for CaretValue_Device.
        
        In the following, note the error is posted to testD.device.device,
        which is in the Device.fromvalidatedwalker part of the code:
        
        >>> fvb(s[:8], logger=logger)
        testD.device - DEBUG - Walker has 8 remaining bytes.
        testD.device.device - DEBUG - Walker has 2 remaining bytes.
        testD.device.device - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('device')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, n, offset = w.unpack("HhH")
        
        if format != 3:
            logger.error((
              'V0099',
              (),
              "Expected format 3 for CaretValue_Device."))
            
            return None
        
        wSub = w.subWalker(offset)
        d = device.Device.fromvalidatedwalker(wSub, logger=logger, **kwArgs)
        
        if d is None:
            return None
        
        return cls(n, deviceRecord=d)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CaretValue_Device object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == CaretValue_Device.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 3, "Can't create CaretValue_Device with non-format-3!"
        n = w.unpack("h")
        d = device.Device.fromwalker(w.subWalker(w.unpack("H")))
        return cls(n, deviceRecord=d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    d1 = device.Device({12: -2, 13: -1, 16: 1, 17: 2})
    
    _testingValues = (
        CaretValue_Device(500, deviceRecord=d1),)
    
    del d1

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
