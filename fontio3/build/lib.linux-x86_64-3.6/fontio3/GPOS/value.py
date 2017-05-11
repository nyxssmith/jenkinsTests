#
# value.py
#
# Copyright © 2007-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Value objects, which are the basic building blocks for GPOS tables.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.opentype import device, living_variations
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    d = obj.__dict__
    Device = device.Device
    LivingDeltas = living_variations.LivingDeltas
    
    for key in ('xPlaDevice', 'yPlaDevice', 'xAdvDevice', 'yAdvDevice'):
        dev = d[key]
        
        if dev is not None and not isinstance(dev, Device):
            logger.error((
              'V0318',
              (key,),
              "The '%s' value is neither None nor a Device object."))
            
            return False
    
    for key in ('xPlaVariation', 'yPlaVariation', 'xAdvVariation', 'yAdvVariation'):
        dev = d[key]
        
        if dev is not None and not isinstance(dev, LivingDeltas):
            logger.error((
              'V0318',
              (key,),
              "The '%s' value is neither None nor a LivingDeltas object"))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Value(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Value objects represent adjustments to the position or metrics of a glyph.
    They are simple collections of 12 attributes, most (or indeed all) of
    which may be unspecified:
    
        xAdvance        A modification (expressed in FUnits) to the advance
                        width of the glyph in the x-direction.
        
        xAdvDevice      A Device object to modify the xAdvance value at certain
                        PPEM values. Note that these are specified in pixels,
                        not FUnits.
        
        xPlacement      A modification (expressed in FUnit) to the origin of
                        the glyph in the x-direction.
        
        xPlaDevice      A Device object to modify the xPlacement value at
                        certain PPEM values. Note that these are specified in
                        pixels, not FUnits.
        
        yAdvance        A modification (expressed in FUnits) to the advance
                        width of the glyph in the y-direction.
        
        yAdvDevice      A Device object to modify the yAdvance value at certain
                        PPEM values. Note that these are specified in pixels,
                        not FUnits.
        
        yPlacement      A modification (expressed in FUnit) to the origin of
                        the glyph in the y-direction.
        
        yPlaDevice      A Device object to modify the yPlacement value at
                        certain PPEM values. Note that these are specified in
                        pixels, not FUnits.
                        
        xAdvVariation   A LivingDeltas object to modify the xAdvance value
                        in variable fonts.
                        
        xPlaVariation   A LivingDeltas object to modify the xPlacement value
                        in variable fonts.
                        
        yAdvVariation   A LivingDeltas object to modify the yAdvance value
                        in variable fonts.
                        
        yPlaVariation   A LivingDeltas object to modify the yPlacement value
                        in variable fonts.


    >>> _testingValues[0].pprint()
    FUnit adjustment to origin's x-coordinate: -10
    >>> _testingValues[2].pprint()
    FUnit adjustment to origin's x-coordinate: 30
    Device for vertical advance:
      Tweak at 12 ppem: -2
      Tweak at 14 ppem: -1
      Tweak at 18 ppem: 1
    
    >>> logger = utilities.makeDoctestLogger("xx")
    >>> e = utilities.fakeEditor(0x10000)
    >>> v = Value()
    >>> v.xPlaDevice = 4
    >>> v.isValid(logger=logger, editor=e)
    xx - ERROR - The 'xPlaDevice' value is neither None nor a Device object.
    xx.xPlaDevice - WARNING - Object is not None and not deep, and no converter function is provided.
    False
    
    >>> bool(Value()), bool(_testingValues[0])
    (False, True)
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        xPlacement = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "FUnit adjustment to origin's x-coordinate",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'yPlacement',
            attr_validatefunc = valassist.isFormat_h),
        
        yPlacement = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "FUnit adjustment to origin's y-coordinate",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'xPlacement',
            attr_validatefunc = valassist.isFormat_h),
        
        xAdvance = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "FUnit adjustment to horizontal advance",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'yAdvance',
            attr_validatefunc = valassist.isFormat_h),
        
        yAdvance = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "FUnit adjustment to vertical advance",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_showonlyiftrue = True,
            attr_transformcounterpart = 'xAdvance',
            attr_validatefunc = valassist.isFormat_h),
         
        xPlaDevice = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Device for origin's x-coordinate",
            attr_representsx = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
         
        yPlaDevice = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Device for origin's y-coordinate",
            attr_representsy = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
         
        xAdvDevice = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Device for horizontal advance",
            attr_representsx = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
         
        yAdvDevice = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Device for vertical advance",
            attr_representsy = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
         
        xPlaVariation = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Variation for origin's x-coordinate",
            attr_representsx = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True,
            attr_islivingdeltas=True),
         
        yPlaVariation = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Variation for origin's y-coordinate",
            attr_representsy = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True,
            attr_islivingdeltas=True),
         
        xAdvVariation = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Variation for horizontal advance",
            attr_representsx = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True,
            attr_islivingdeltas=True),
         
        yAdvVariation = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Variation for vertical advance",
            attr_representsy = True,
            attr_showonlyiftrue = True,
            attr_strneedsparens = True,
            attr_islivingdeltas=True))
    
    attrSorted = (
      'xPlacement',
      'yPlacement',
      'xAdvance',
      'yAdvance',
      'xPlaDevice',
      'yPlaDevice',
      'xAdvDevice',
      'yAdvDevice',
      'xPlaVariation',
      'yPlaVariation',
      'xAdvVariation',
      'yAdvVariation')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. There are three
        keyword arguments:
        
            devicePool      A dict mapping device IDs to the Device objects.
                            This is optional; if not specified, a local pool
                            will be used. The devices will only be actually
                            added if devicePool is not specified; if it is
                            specified, a higher-level client is responsible for
                            this.
            
            posBase         A stake representing the base from which device
                            offsets will be computed. This is required.
            
            valueFormat     The mask representing which values are to be
                            included. This is optional; if not specified, the
                            getMask() method will be called to determine it.
                            
            otIVS           A tuple of (ivsBinaryString, LivingDelta-to-DeltaSetIndex 
                            Map). The ivsBinaryString is not used here, but is
                            elsewhere in the chain. The LivingDelta Map is
                            used to translate the values's *Variation values
                            into (outer, inner) Variation Indexes and
                            construct a special Device record for writing as a
                            VariationIndex.
        
        >>> w = writer.LinkedWriter()
        >>> for obj in _testingValues:
        ...     w.stakeCurrentWithValue("test stake")
        ...     w.add("l", -1)
        ...     obj.buildBinary(w, posBase="test stake", valueFormat=255)
        ...     utilities.hexdump(w.binaryString())
        ...     w.reset()
               0 | FFFF FFFF FFF6 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000                                |....            |
               0 | FFFF FFFF 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0014 000C 0012  0001 8C04           |............    |
               0 | FFFF FFFF 001E 0000  0000 0000 0000 0000 |................|
              10 | 0000 0014 000C 0012  0001 8C04           |............    |
               0 | FFFF FFFF 0000 0000  0000 0000 0020 0014 |............. ..|
              10 | 0000 0000 000C 0014  0002 BDF0 0020 3000 |............. 0.|
              20 | 000C 0012 0001 8C04                      |........        |
        """
        
        devicePool = kwArgs.pop('devicePool', None)
        
        if devicePool is None:
            devicePool = {}
            doLocal = True
        else:
            doLocal = False
        
        if 'valueFormat' in kwArgs:
            valueFormat = kwArgs['valueFormat']
        else:
            valueFormat = self.getMask()

        ivsBs, ld2dsimap = kwArgs.get('otIVS', (None, None))

        if ld2dsimap:
            valueFormat = ((valueFormat << 4) + valueFormat) & 0xF0F

        posBase = kwArgs['posBase']
        d = self.__dict__
        
        for i, key in enumerate(self.getSortedAttrNames()):
            if (1 << i) & valueFormat:
                obj = d[key]
            
                if i < 4:
                    w.add("h", obj)
            
                elif i >= 8 and obj is not None:
                    # Variation (LivingDeltas); convert to special Device obj
                    dstuple = ld2dsimap[obj]
                    objID = (dstuple[0] << 16) + dstuple[1]
                    if objID not in devicePool:
                        varidxrec = device.Device(
                          dict(enumerate(dstuple)),
                          isVariable=True)
                        devicePool[objID] = (varidxrec, w.getNewStake())

                    w.addUnresolvedOffset("H", posBase, devicePool[objID][1])
            
                elif obj is None:
                    w.add("H", 0)
            
                else:
                    objID = id(obj)
                
                    if objID not in devicePool:
                        devicePool[objID] = (obj, w.getNewStake())
                
                    w.addUnresolvedOffset("H", posBase, devicePool[objID][1])
                
        if doLocal:
            # we decorate-sort to ensure a repeatable, canonical ordering
            it = sorted(
              (sorted(obj.asImmutable()[1]), obj, stake)
              for obj, stake in devicePool.values())
            
            for t in it:
                t[1].buildBinary(w, stakeValue=t[2], **kwArgs)
        
# I've commented out the following two lines, because they do NOTHING!
#         else:
#             kwArgs['devicePool'] = devicePool
#     
#     def effects(self, **kwArgs):
#         """
#         Returns a pair of tuples, X and Y. The tuples will be of length one if
#         the effects of this Value object are limited to changes to the origin;
#         otherwise they will be of length two, with the second element being
#         applied to the following glyph.
#         
#         If the Value has all zeroes, a single None is returned.
#         
#         Device shifts are not currently supported.
#         
#         >>> Value(xPlacement=-25).effects()
#         ((-25,), (0,))
#         
#         >>> Value(yAdvance=40).effects()
#         ((0, 0), (0, 40))
#         
#         >>> Value().effects() is None
#         True
#         """
#         
#         if self.xAdvance or self.yAdvance:
#             vLen = 2
#         elif self.xPlacement or self.yPlacement:
#             vLen = 1
#         else:
#             return None
#         
#         vX = [0] * vLen
#         vY = [0] * vLen
#         
#         if self.xPlacement:
#             vX[0] = self.xPlacement
#         
#         if self.yPlacement:
#             vY[0] = self.yPlacement
#         
#         if self.xAdvance:
#             vX[1] = self.xAdvance
#         
#         if self.yAdvance:
#             vY[1] = self.yAdvance
#         
#         return tuple(vX), tuple(vY)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Value object from the specified walker, with
        validation of the input source. The following keyword arguments are
        supported:
        
            logger          A logger to which messages will be logged.
        
            posBase         A StringWalker whose base is used for offsets to
                            Device objects. If not specified, the w argument is
                            used.
            
            valueFormat     A mask value specifying which fields are actually
                            present.
        
            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.
        
        >>> d = device.Device({12: -2, 14: -1, 18: 1})
        >>> v = Value(xAdvance=600, xPlaDevice=d)
        >>> w = writer.LinkedWriter()
        >>> w.stakeCurrentWithValue("test stake")
        >>> v.buildBinary(w, posBase="test stake")
        >>> logger = utilities.makeDoctestLogger("test")
        >>> v == Value.fromvalidatedbytes(
        ...   w.binaryString(),
        ...   valueFormat = v.getMask(),
        ...   logger = logger)
        test.value - DEBUG - Walker has 12 remaining bytes.
        test.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
        test.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        test.value.xPlaDevice.device - DEBUG - Data are (35844,)
        True
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild("value")
        else:
            logger = logger.getChild("value")

        otcommondeltas = kwArgs.get('otcommondeltas', None)

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        valueFormat = kwArgs['valueFormat']
        posBase = kwArgs.get('posBase', w)
        isPresentList = [bool((1 << i) & valueFormat) for i in range(8)]
        pool = {}
        r = cls()
        rd = r.__dict__
        
        all_attrs = cls.getSortedAttrNames()
        org_attrs = all_attrs[0:8]
        dev_attrs = org_attrs[4:]
        var_attrs = all_attrs[8:]
        for i, key in enumerate(org_attrs):
            rdkey = key
            if isPresentList[i]:
                if w.length() < 2:
                    logger.error((
                      'V0317',
                      (key,),
                      "Insufficient bytes for the '%s' value."))
                    
                    return None
                
                if i < 4:
                    rd[key] = w.unpack("h")
                
                else:
                    offset = w.unpack("H")
                    
                    if offset:
                        if offset not in pool:
                            subLogger = logger.getChild(key)
                            
                            d = device.Device.fromvalidatedwalker(
                              posBase.subWalker(offset),
                              logger = subLogger)
                            
                            if isinstance(d, tuple):
                                rdkey = var_attrs[dev_attrs.index(key)] # change key

                                if otcommondeltas is not None:
                                    if d in otcommondeltas:
                                        ld = otcommondeltas.get(d)
                                        vLogger = logger.getChild(rdkey)
                                        vLogger.debug((
                                          'Vxxxx',
                                          (ld,),
                                          "LivingDeltas %s"))

                                        pool[offset] = ld

                                    else:
                                        logger.error((
                                          'Vxxxx',
                                          (d,),
                                          "VariationIndex %s not present in the OpenType "
                                          "common itemVariationStore (GDEF)."))

                                        return None

                                else:
                                    logger.error((
                                      'Vxxxx',
                                      (),
                                      "VariationIndex present in device table but "
                                      "the OpenType common itemVariationStore (GDEF) "
                                      "is not present or is unreadable."))
                                      
                                    return None
                            
                            elif isinstance(d, device.Device):
                                pool[offset] = d
                            
                            elif d is None:
                                return None
                        
                        rd[rdkey] = pool[offset]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Value object from the specified walker. There
        are two keyword arguments:
        
            posBase         A StringWalker whose base is used for offsets to
                            Device objects. If not specified, the w argument is
                            used.
            
            valueFormat     A mask value specifying which fields are actually
                            present.

            otcommondeltas  A dictionary of (outer, inner): LivingDeltas.
                            Required for Variable fonts.
        
        >>> d = device.Device({12: -2, 14: -1, 18: 1})
        >>> v = Value(xAdvance=600, xPlaDevice=d)
        >>> w = writer.LinkedWriter()
        >>> w.stakeCurrentWithValue("test stake")
        >>> v.buildBinary(w, posBase="test stake")
        >>> v == Value.frombytes(w.binaryString(), valueFormat=v.getMask())
        True
        """

        otcommondeltas = kwArgs.get('otcommondeltas', None)

        valueFormat = kwArgs['valueFormat']
        posBase = kwArgs.get('posBase', w)
        isPresentList = [bool((1 << i) & valueFormat) for i in range(8)]
        pool = {}
        r = cls()
        rd = r.__dict__
        
        all_attrs = cls.getSortedAttrNames()
        org_attrs = all_attrs[0:8]
        dev_attrs = org_attrs[4:]
        var_attrs = all_attrs[8:]
        for i, key in enumerate(org_attrs):
            rdkey = key
            if isPresentList[i]:
                if i < 4:
                    rd[key] = w.unpack("h")
                
                else:
                    offset = w.unpack("H")
                    
                    if offset:
                        if offset not in pool:
                            d = device.Device.fromwalker(
                              posBase.subWalker(offset))

                            if isinstance(d, tuple):

                                if otcommondeltas is not None:
                                    rdkey = var_attrs[dev_attrs.index(key)]
                                    ld = otcommondeltas.get(d)
                                    if ld is None:
                                        return None
                                    pool[offset] = ld

                            elif isinstance(d, device.Device):
                                pool[offset] = d

                            elif d is None:
                                return None
                        
                        rd[rdkey] = pool[offset]
        
        return r
    
    def getMask(self):
        """
        Returns a mask value representing the actual state of data currently
        present.
        
        >>> v = Value()
        >>> v.getMask()
        0
        >>> v.xAdvance = 5
        >>> v.getMask()
        4
        >>> v.xPlaVariation = "FakeVariationValue"
        >>> v.getMask()
        20
        """
        
        d = self.__dict__

        vAll = [bool(d[key]) for key in self.getSortedAttrNames()]
        hasVariations = any(vAll[8:])
        if hasVariations:
            v = vAll[0:4] + vAll[8:]
        else:
            v = vAll[0:8]

        return functools.reduce(lambda x, y: (x << 1) | y, reversed(v))

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write Value as Font Worker-style source. kwArg 'lbl' is required
        (label for the value; may be a tab-separated pair or single
        glyphname/id). kwArg 'prefix' is optional; used from pairvalues
        to designate left/right and should include trailing space.
        """
        attr_order = (
          ('xPlacement', 'x placement'),
          ('yPlacement', 'y placement'),
          ('xAdvance', 'x advance'),
          ('yAdvance', 'y advance'),
          )

        prefix = kwArgs.get('prefix', "")
        lbl = kwArgs.get('lbl')

        for fiotag, fwtag in attr_order:
            v = self.__dict__[fiotag]
            if v:
                s.write("%s%s\t%s\t%d\n" % (prefix, fwtag, lbl, v))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer
    
    _testingValues = (
        Value(xPlacement=-10),
        Value(yAdvDevice=device._testingValues[0]),
        Value(xPlacement=30, yAdvDevice=device._testingValues[0]),
        
        Value(
          xPlaDevice = device._testingValues[0],
          yPlaDevice = device._testingValues[1]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
