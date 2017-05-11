#
# coordinate_variation.py
#
# Copyright © 2010-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Items relating to variation-modified coordinate values for OpenType BASE tables.

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

class Coordinate_variation(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing a coordinate value, a single integer in FUnits. This
    will be interpreted as X or Y depending on whether the object containing it
    is part of the horizontal or vertical baseline data.
    
    There is also one attribute:
    
        variation      A LivingDeltas object to be used to tweak the
                       coordinate in variation space.
    
    >>> int(_testingValues[0])
    25
    >>> list(_testingValues[0].variation)[0][1]
    -180

    >>> logger = utilities.makeDoctestLogger("coordinate_variation_test")
    >>> e = _fakeEditor()
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    coordinate_variation_test - WARNING - The FUnit value -20000 is more than two ems away from the origin, which seems unlikely.
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
        variation = dict(
            attr_followsprotocol = True,
            attr_label = "Variation",
            attr_islivingdeltas = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Coordinate_variation object to the specified
        LinkedWriter. There is one optional keyword argument:
        
            devicePool      A dict mapping immutable versions of Devices to the
                            (Device, stake) pairs. If specified, the caller (or
                            a higher caller) is responsible for writing out the
                            pool when done. If not specified, a local pool will
                            be used and will be written here.
                            
            otIVS           
                
        >>> w = writer.LinkedWriter()
        >>> otIVS = ("", {"FakeLivingDeltas1": (1, 55)})
        >>> obj = Coordinate_variation(32, variation="FakeLivingDeltas1")
        >>> bs = obj.binaryString(otIVS=otIVS)
        >>> utilities.hexdump(bs)
               0 | 0003 0020 0006 0001  0037 8000           |... .....7..    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        ivsBs, ld2dsimap = kwArgs.get('otIVS', (None, None))

        w.add("Hh", 3, self)
        
        if 'devicePool' in kwArgs:
            pool = kwArgs['devicePool']

            dstuple = ld2dsimap[self.variation]

            if dstuple not in pool:
                varidxrec = device.Device(
                  dict(enumerate(dstuple)),
                  isVariable=True)
                pool[dstuple] = (varidxrec, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, pool[dstuple][1])
        
        else:
            stake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, stake)
            dstuple = ld2dsimap[self.variation]
            varidxrec = device.Device(
              dict(enumerate(dstuple)),
              isVariable=True)
            varidxrec.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Coordinate_variation object from the
        specified walker, doing source validation. The following keyword
        arguments are supported:
        
            logger          A logger to which messages will be logged.
        
            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.

        >>> s = utilities.fromhex("0003 0040 0006 0000 0001 8000")
        >>> otcd = {(0,1): testLD1, (0,2): testLD2}
        >>> logger = utilities.makeDoctestLogger("coordinate_variation_fvw")
        >>> fvb = Coordinate_variation.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, otcommondeltas=otcd)
        coordinate_variation_fvw.coordinate_variation - DEBUG - Walker has 12 remaining bytes.
        coordinate_variation_fvw.coordinate_variation.device - DEBUG - Walker has 6 remaining bytes.
        coordinate_variation_fvw.coordinate_variation.device - DEBUG - VariationIndex (0, 1)
        coordinate_variation_fvw.coordinate_variation - DEBUG - LivingDeltas ('wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0), -180)
        """
        
        logger = kwArgs.pop('logger')
        otcommondeltas = kwArgs.get('otcommondeltas')

        if logger is None:
            logger = logging.getLogger().getChild('coordinate_variation')
        else:
            logger = logger.getChild('coordinate_variation')
        
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
        
        dlt = device.Device.fromvalidatedwalker(
          wBase.subWalker(devOffset),
          logger = logger,
          **kwArgs)

        if dlt:
            ld = otcommondeltas.get(dlt)
            if ld:
                logger.debug((
                  'Vxxxx',
                  (ld,),
                  "LivingDeltas %s"))
            else:
                logger.error((
                  'Vxxxx',
                  (dlt,),
                  "Variation Index %s not present in the OpenType "
                  "common itemVariationStore (GDEF)."))
                  
                return None

        else:
            logger.debug((
              'Vxxxx',
              (devOffset,),
              "Invalid Variable data at 0x%04X"))

        return cls(shift, variation=ld)

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Coordinate_variation object from the specified
        walker. The following keyword arguments are supported:

            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.
        
        >>> bs = utilities.fromhex("0003 000A 0006 0000 0002 8000")
        >>> fvb = Coordinate_variation.frombytes
        >>> otcd = {(0,2): testLD2}
        >>> obj = fvb(bs, otcommondeltas=otcd)
        >>> int(obj)
        10
        >>> list(obj.variation)[0][1]
        10
        """

        otcommondeltas = kwArgs['otcommondeltas']
        
        wBase = w.subWalker(0, relative=True)
        format = w.unpack("H")
        
        if format != 3:
            raise ValueError(
              "Unknown format for Coordinate_variation: %d" % (format,))
        
        n = w.unpack("h")
        
        dlt = device.Device.fromwalker(
          wBase.subWalker(w.unpack("H")),
          **kwArgs)
          
        ld = otcommondeltas[dlt]
        
        return cls(n, variation=ld)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import operator
    from fontio3 import utilities
    from fontio3.opentype import living_variations
    from fontio3.utilities import writer
    
    def _fakeEditor():
        from fontio3.head import head
        
        e = utilities.fakeEditor(0x10000)
        e.head = head.Head()
        return e

    LR = living_variations.LivingRegion
    LD = living_variations.LivingDeltas
    LDM = living_variations.LivingDeltasMember

    d = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    key = LR.fromdict(d)
    testLD1 = LD({LDM((key, -180))})
    testLD2 = LD({LDM((key, 10))})

    _testingValues = (
        Coordinate_variation(25, variation=testLD1),
        Coordinate_variation(-10, variation=testLD2),
        Coordinate_variation(15, variation=testLD2),
        # bad values start here
        Coordinate_variation(-20000, variation=testLD1))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
