#
# caretvalue_variation.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
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

class CaretValue_Variation(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing caret values with variation indices. These are very
    similar (actually: binary identical) to device tables, but instead of
    describing device-specific values, they store LivingDeltas which describe
    variations.
    
    >>> c = _testingValues[0]
    >>> c >= 500
    True
    >>> c.variationRecord
    'FakeLivingDelta1'
    """
    
    #
    # Class definition variables
    #
    
    valueSpec = dict(
        value_pprintlabel = "Caret value in FUnits",
        value_scales = True,
        value_validatefunc = valassist.isFormat_h)
    
    attrSpec = dict(
        variationRecord = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = None,
            attr_islivingdeltas = True,
            attr_label = "Variation Record"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter. There are two
        keyword arguments:

            otIVS           A tuple of (ivsBinaryString, LivingDelta-to-DeltaSetIndexMap). 
                            The ivsBinaryString is not used here, but is
                            elsewhere in the chain. The LivingDelta Map is
                            used to translate the object's variationRecord
                            into an (outer, inner) Variation Index and
                            construct a special Device record for writing as a
                            VariationIndex.

            devicePool      If specified should be a dict of (outer,inner) :
                            Device records for the device pool. If not
                            specified, a local pool will be used and the
                            Device binary will be written locally. Note that
                            "Device" is somewhat anachronistic: it's actually
                            VariationIndex data, but since it's essentially
                            the same as Device data, we're recycling...

        >>> fakeIVS = ("fakeBinaryString", {"FakeLivingDelta1":(0,5)})
        >>> utilities.hexdump(_testingValues[0].binaryString(otIVS=fakeIVS))
               0 | 0003 01F4 0006 0000  0005 8000           |............    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        ivsBs, ld2dsimap = kwArgs['otIVS']

        devicePool = kwArgs.pop('devicePool', None)
        
        if devicePool is None:
            devicePool = {}
            doLocal = True
        else:
            doLocal = False

        dstuple = ld2dsimap[self.variationRecord]

        if dstuple not in devicePool:
            varidxrec = device.Device(
              {k:v for k,v in enumerate(dstuple)},
              isVariable=True)
            devicePool[dstuple] = (varidxrec, w.getNewStake())
        
        w.add("Hh", 3, self)
        w.addUnresolvedOffset("H", stakeValue, devicePool[dstuple][1])
        
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

        >>> fakeIVS = ("fakeBinaryString", {"FakeLivingDelta1":(0,5)})
        >>> logger = utilities.makeDoctestLogger('testD')
        >>> s = _testingValues[0].binaryString(otIVS=fakeIVS)
        >>> fvb = CaretValue_Variation.fromvalidatedbytes
        >>> fvb(s[:1], logger=logger)
        testD.variation - DEBUG - Walker has 1 remaining bytes.
        testD.variation - ERROR - Insufficient bytes.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        testD.variation - DEBUG - Walker has 12 remaining bytes.
        testD.variation - ERROR - Expected format 3 for CaretValue_Variation.
        
        In the following, note the error is posted to testD.variation.device,
        which is in the Device.fromvalidatedwalker part of the code:
        
        >>> fvb(s[:8], logger=logger)
        testD.variation - DEBUG - Walker has 8 remaining bytes.
        testD.variation.device - DEBUG - Walker has 2 remaining bytes.
        testD.variation.device - ERROR - Insufficient bytes.

        >>> fvb(s, logger=logger)
        testD.variation - DEBUG - Walker has 12 remaining bytes.
        testD.variation.device - DEBUG - Walker has 6 remaining bytes.
        testD.variation.device - DEBUG - VariationIndex (0, 5)
        testD.variation - ERROR - CaretValue with VariationIndex present but the OpenType common itemVariationStore (GDEF) is not present or is unreadable.

        >>> fvb(s, otcommondeltas={}, logger=logger)
        testD.variation - DEBUG - Walker has 12 remaining bytes.
        testD.variation.device - DEBUG - Walker has 6 remaining bytes.
        testD.variation.device - DEBUG - VariationIndex (0, 5)
        testD.variation - ERROR - VariationIndex (0, 5) not present in OpenType common itemVariationStore (GDEF).

        >>> otcd = {(0,5): "FakeLivingDelta1"}
        >>> obj = fvb(s, otcommondeltas=otcd, logger=logger)
        testD.variation - DEBUG - Walker has 12 remaining bytes.
        testD.variation.device - DEBUG - Walker has 6 remaining bytes.
        testD.variation.device - DEBUG - VariationIndex (0, 5)
        testD.variation - DEBUG - LivingDeltas FakeLivingDelta1
        >>> int(obj) == 500
        True
        >>> obj.variationRecord == 'FakeLivingDelta1'
        True
        
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('variation')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        otcommondeltas = kwArgs.get('otcommondeltas', None)
        
        format, n, offset = w.unpack("HhH")
        
        if format != 3:
            logger.error((
              'V0099',
              (),
              "Expected format 3 for CaretValue_Variation."))
            
            return None
        
        wSub = w.subWalker(offset)
        # Device from*walker code actually parses out the (outer, inner) info and
        # returns as a plain tuple.
        vtuple = device.Device.fromvalidatedwalker(wSub, logger=logger, **kwArgs)
        
        if vtuple is None:
            return None
        
        if otcommondeltas is not None:
            if vtuple in otcommondeltas:
                ld = otcommondeltas[vtuple]
                logger.debug(('Vxxxx', (ld,), "LivingDeltas %s"))
                
            else:
                logger.error((
                  'Vxxxx',
                  (vtuple,),
                  "VariationIndex %s not present in OpenType common "
                  "itemVariationStore (GDEF)."))
                return None
                
        else:
            logger.error((
              'Vxxxx',
              (),
              "CaretValue with VariationIndex present but the OpenType common "
              "itemVariationStore (GDEF) is not present or is unreadable."))
            return None
        
        return cls(n, variationRecord=ld)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CaretValue_Variation object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> fakeIVS = ("fakeBinaryString", {"FakeLivingDelta1":(0,5)})
        >>> otcd = {(0,5): "FakeLivingDelta1"}
        >>> fb = CaretValue_Variation.frombytes
        >>> bs = obj.binaryString(otIVS=fakeIVS)
        >>> obj == fb(bs, otcommondeltas=otcd)
        True
        """
        
        otcommondeltas = kwArgs['otcommondeltas']
        
        format = w.unpack("H")
        assert format == 3, "Can't create CaretValue_Variation with non-format-3!"
        n = w.unpack("h")
        vtuple = device.Device.fromwalker(w.subWalker(w.unpack("H")))
        ld = otcommondeltas.get(vtuple)
        
        if ld is None:
            return None

        return cls(n, variationRecord=ld)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walkerbit
    
    _testingValues = (
        CaretValue_Variation(500, variationRecord="FakeLivingDelta1"),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
