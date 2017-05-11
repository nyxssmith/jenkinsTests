#
# anchor_variation.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
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

class Anchor_Variation(anchor_coord.Anchor_Coord):
    """
    Objects representing anchored locations, via FUnit values and two
    associated Variation objects, one for x and one for y. These are just like
    Anchor_Device objects, but instead of Device data they include Variation
    information.
    
    >>> _testingValues[0].pprint()
    x-coordinate: 29
    y-coordinate: 35
    Variation for x:
      A delta of -100 applies in region 'wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0)

    >>> _testingValues[0].anchorKind
    'variation'
    
    >>> logger = utilities.makeDoctestLogger("anchor_variation_val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    anchor_variation_val.[0] - ERROR - The value -4.5 is not an integer.
    anchor_variation_val.[1] - ERROR - The signed value 40000 does not fit in 16 bits.
    False
    """
    
    #
    # Class definition variables
    #
    
    # Since we inherit from Anchor_Coord, we
    # only need to define the extra attributes.
    
    attrSpec = dict(
        xVariation = dict(
            attr_followsprotocol = True,
            attr_label = "Variation for x",
            attr_representsx = True,
            attr_showonlyiftrue = True,
            attr_islivingdeltas=True),
        
        yVariation = dict(
            attr_followsprotocol = True,
            attr_label = "Variation for y",
            attr_representsy = True,
            attr_showonlyiftrue = True,
            attr_islivingdeltas=True))
    
    anchorKind = 'variation'
    
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
                            
            otIVS           
        
        >>> otIVS = ("", {testLD1: (0,1), testLD2: (0,3)})
        >>> utilities.hexdump(_testingValues[0].binaryString(otIVS=otIVS))
               0 | 0003 001D 0023 000A  0000 0000 0001 8000 |.....#..........|
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

        ivsBs, ld2dsimap = kwArgs.get('otIVS', (None, None))

        
        w.add("H2h", 3, *self)
        
        for obj in (self.xVariation, self.yVariation):
            if obj:
                dstuple = ld2dsimap[obj]

                if dstuple not in devicePool:
                    varidxrec = device.Device(
                      dict(enumerate(dstuple)),
                      isVariable=True)
                    devicePool[dstuple] = (varidxrec, w.getNewStake())

                w.addUnresolvedOffset("H", stakeValue, devicePool[dstuple][1])

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
        Returns a new Anchor_Variation object, including validation of the input
        source. The following keyword arguments are
        supported:
        
            logger          A logger to which messages will be logged.
        
            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.

        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> e = utilities.fakeEditor(0x10000)
        >>> s = ("0003 000A 0014 000A 0010 0000 0001 8000 0000 0002 8000")
        >>> b = utilities.fromhex(s)
        >>> fvb = Anchor_Variation.fromvalidatedbytes
        >>> otcd = {(0,1): testLD1, (0,2): testLD2}
        >>> obj = fvb(b, logger=logger, editor=e, otcommondeltas=otcd)
        test.anchor_variation - DEBUG - Walker has 22 remaining bytes.
        test.anchor_variation.x.device - DEBUG - Walker has 12 remaining bytes.
        test.anchor_variation.x.device - DEBUG - VariationIndex (0, 1)
        test.anchor_variation.x - DEBUG - LivingDeltas ('wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0), -100)
        test.anchor_variation.y.device - DEBUG - Walker has 6 remaining bytes.
        test.anchor_variation.y.device - DEBUG - VariationIndex (0, 2)
        test.anchor_variation.y - DEBUG - LivingDeltas ('wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0), 40)
        
        >>> obj = fvb(b[0:8], logger=logger, editor=e, otcommondeltas=otcd)
        test.anchor_variation - DEBUG - Walker has 8 remaining bytes.
        test.anchor_variation - ERROR - Insufficient bytes.
        
        >>> s = ("0004 000A 0014 000A 0010 0000 0001 8000 0000 0005 8000")
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, logger=logger, editor=e, otcommondeltas=otcd)
        test.anchor_variation - DEBUG - Walker has 22 remaining bytes.
        test.anchor_variation - ERROR - Was expecting format 3, but got 4 instead.

        >>> b = utilities.fromhex("0003") + b[2:]
        >>> obj = fvb(b, logger=logger, editor=e, otcommondeltas=otcd)
        test.anchor_variation - DEBUG - Walker has 22 remaining bytes.
        test.anchor_variation.x.device - DEBUG - Walker has 12 remaining bytes.
        test.anchor_variation.x.device - DEBUG - VariationIndex (0, 1)
        test.anchor_variation.x - DEBUG - LivingDeltas ('wdth': (start -1.0, peak 0.25, end 0.75), 'wght': (start -0.75, peak 0.0, end 1.0), -100)
        test.anchor_variation.y.device - DEBUG - Walker has 6 remaining bytes.
        test.anchor_variation.y.device - DEBUG - VariationIndex (0, 5)
        test.anchor_variation.y - ERROR - Variation Index (0, 5) not present in the OpenType common itemVariationStore (GDEF).
        """
        
        logger = kwArgs.get('logger', None)
        otcommondeltas = kwArgs.get('otcommondeltas')
        
        if logger is None:
            logger = logging.getLogger().getChild('anchor_variation')
        else:
            logger = logger.getChild('anchor_variation')
        
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
        xVarOffset, yVarOffset = w.unpack("2H")
        fvw = device.Device.fromvalidatedwalker
        
        if xVarOffset:
            subLogger = logger.getChild("x")
            dlt = fvw(w.subWalker(xVarOffset), logger=subLogger)
            if dlt:
                ld = otcommondeltas.get(dlt)
                if ld:
                    subLogger.debug((
                      'Vxxxx',
                      (ld,),
                      "LivingDeltas %s"))
                    argDict['xVariation'] = ld

                else:
                    subLogger.error((
                      'Vxxxx',
                      (dlt,),
                      "Variation Index %s not present in the OpenType "
                      "common itemVariationStore (GDEF)."))
                      
            else:
                sublogger.debug((
                  'Vxxxx',
                  (xVarOffset,),
                  "Invalid Variable data at 0x%04X"))

        if yVarOffset:
            subLogger = logger.getChild("y")
            dlt = fvw(w.subWalker(yVarOffset), logger=subLogger)
            if dlt:
                ld = otcommondeltas.get(dlt)
                if ld:
                    subLogger.debug((
                      'Vxxxx',
                      (ld,),
                      "LivingDeltas %s"))
                    argDict['yVariation'] = ld

                else:
                    subLogger.error((
                      'Vxxxx',
                      (dlt,),
                      "Variation Index %s not present in the OpenType "
                      "common itemVariationStore (GDEF)."))
            else:
                subLogger.debug((
                  'Vxxxx',
                  (yVarOffset,),
                  "Invalid Variable data at 0x%04X"))

        return cls(x, y, **argDict)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Variation object from the specified walker. The
        following keyword arguments are supported:

            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.

        >>> atv = _testingValues[0]
        >>> otIVS = ("", {testLD1: (0,1), testLD2: (0,2)})
        >>> otcd = {(0,1): testLD1, (0,2): testLD2}
        >>> bs = atv.binaryString(otIVS=otIVS)
        >>> atv == Anchor_Variation.frombytes(bs, otcommondeltas=otcd)
        True

        >>> e = utilities.fakeEditor(0x10000)
        >>> s = ("0003 000A 0014 000A 0010 0000 0001 8000 0000 0002 8000")
        >>> b = utilities.fromhex(s)
        >>> fb = Anchor_Variation.frombytes
        >>> obj = fb(b, editor=e, otcommondeltas=otcd)
        >>> list(obj.xVariation)[0][1]
        -100
        >>> list(obj.yVariation)[0][1]
        40

        >>> s = ("0005 000A 0014 000A 0000 0000 0001 8000")
        >>> b = utilities.fromhex(s)
        >>> obj = fb(b, editor=e, otcommondeltas=otcd)
        Traceback (most recent call last):
            ...
        ValueError: Unknown format for Anchor_Variation: 5
        """
        
        otcommondeltas = kwArgs.get('otcommondeltas')
        
        format = w.unpack("H")
        
        if format != 3:
            raise ValueError(
              "Unknown format for Anchor_Variation: %d" %
              (format,))
        
        argDict = {}
        x, y = w.unpack("2h")
        xVarOffset, yVarOffset = w.unpack("2H")
        
        if xVarOffset:
            dsi = device.Device.fromwalker(w.subWalker(xVarOffset))
            ld = otcommondeltas.get(dsi)
            argDict['xVariation'] = ld
        
        if yVarOffset:
            dsi = device.Device.fromwalker(w.subWalker(yVarOffset))
            ld = otcommondeltas.get(dsi)
            argDict['yVariation'] = ld
        
        return cls(x, y, **argDict)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype.living_variations import LivingRegion, LivingDeltas, LivingDeltasMember
    
    axdict = {'wght': (-0.75, 0.0, 1.0), 'wdth': (-1.0, 0.25, 0.75)}
    testkey = LivingRegion.fromdict(axdict)
    testLD1 = LivingDeltas({LivingDeltasMember((testkey, -100))})
    testLD2 = LivingDeltas({LivingDeltasMember((testkey, 40))})

    _testingValues = (
        Anchor_Variation(29, 35, xVariation=testLD1),
        Anchor_Variation(-25, 120, yVariation=testLD2),
        Anchor_Variation(0, 50, xVariation=testLD1),
        
        # bad values start here
        
        Anchor_Variation(-4.5, 40000, xVariation=testLD1, yVariation=None))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
