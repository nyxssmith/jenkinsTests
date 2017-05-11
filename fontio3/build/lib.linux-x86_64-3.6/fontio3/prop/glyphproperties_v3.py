#
# glyphproperties_v3.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definition of glyph properties for version 3.0 'prop' tables. The only addition
in version 3.0 is support for more directionality classes.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.prop import directionalityclass, glyphproperties_v2
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_directionality(obj, **kwArgs):
    logger = kwArgs['logger']
    
    isOK = valassist.isNumber_integer_unsigned(
      obj,
      label = "directionality",
      logger = logger,
      numBits = 5)
    
    if not isOK:
        return False
    
    return True

def _validate_floater(obj, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    glyphIndex = kwArgs['glyphIndex']
    
    if e is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate floater because the Editor is missing."))
        
        return False
    
    h = e.get(b'hmtx', {})
    v = e.get(b'vmtx', {})
    
    if not (h or v):
        logger.error((
          'V0553',
          (),
          "Unable to validate floater because the Editor does not have "
          "either a 'hmtx' or a 'vmtx' table."))
        
        return False
    
    if h:
        hMetrics = h.get(glyphIndex, None)
        
        if hMetrics is None:
            logger.error((
              'V0553',
              (),
              "Unable to validate floater because the specified glyph index "
              "is not present in the Hmtx object."))
            
            return False
        
        elif hMetrics.advance:
            if obj:
                logger.error((
                  'V0778',
                  (glyphIndex, hMetrics.advance),
                  "Glyph %d has nonzero horizontal advance %d, but floater "
                  "flag is True. Floaters must have zero advance."))
                
                return False
    
    if v:
        vMetrics = v.get(glyphIndex, None)
        
        if vMetrics is None:
            logger.error((
              'V0553',
              (),
              "Unable to validate floater because the specified glyph index "
              "is not present in the Vmtx object."))
            
            return False
        
        elif vMetrics.advance:
            if obj:
                logger.error((
                  'V0778',
                  (glyphIndex, vMetrics.advance),
                  "Glyph %d has nonzero vertical advance %d, but floater "
                  "flag is True. Floaters must have zero advance."))
                
                return False
    
    return True

def _validate_mirrorGlyph(obj, **kwArgs):
    if obj is None:
        return True
    
    glyphIndex = kwArgs['glyphIndex']
    delta = obj - glyphIndex
    
    if not (-8 <= delta < 8):
        kwArgs['logger'].error((
          'V0777',
          (glyphIndex,),
          "Mirror for glyph %d is more than 8 indices away."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GlyphProperties(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Glyph properties for AAT 'prop' tables. These are collections of attributes
    as follows:
    
        directionality      An integer representing the directionality class
                            value for the glyph.
        
        floater             True if the glyph has zero advance.
        
        hangsLeftTop        True if the glyph "hangs" into the left margin for
                            horizontal text, or the top margin for vertical.
        
        hangsRightBottom    True if the glyph "hangs" into the right margin for
                            horizontal text, or the bottom margin for vertical.
        
        attachesRight       True if the glyph always attaches to the glyph
                            appearing physically to the right of it. This was
                            added in version 2.0.
        
        mirrorGlyph         If the properties are for a bracketing glyph with
                            a mirrored counterpart, this attribute contains the
                            glyph index of that counterpart. Otherwise (the
                            default case) the attribute is None.
    
    >>> s = utilities.fromhex("FD 8B")
    >>> GlyphProperties.frombytes(s, glyphIndex=100).pprint()
    Glyph is floater: True
    Glyph is left/top hanger: True
    Glyph is right/bottom hanger: True
    Mirror bracketing glyph: 97
    Attaches on right: True
    Directionality class: Other neutrals
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = glyphproperties_v1._fakeEditor()
    >>> obj = GlyphProperties(mirrorGlyph=39)
    >>> obj.isValid(editor=e, logger=logger, glyphIndex=35)
    True
    >>> obj.isValid(editor=e, logger=logger, glyphIndex=350)
    val.mirrorGlyph - ERROR - Mirror for glyph 350 is more than 8 indices away.
    False
    
    >>> obj = GlyphProperties(floater=True)
    >>> obj.isValid(editor=e, logger=logger, glyphIndex=35)
    val.floater - ERROR - Glyph 35 has nonzero horizontal advance 600, but floater flag is True. Floaters must have zero advance.
    False
    
    >>> obj = GlyphProperties(directionality=21)
    >>> obj.isValid(editor=e, logger=logger, glyphIndex=35)
    True
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        attachesRight = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Attaches on right",
            attr_showonlyiftrue = True),
        
        floater = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Glyph is floater",
            attr_showonlyiftrue = True,
            attr_validatefunc_partial = _validate_floater),
        
        hangsLeftTop = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Glyph is left/top hanger",
            attr_showonlyiftrue = True),
        
        hangsRightBottom = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Glyph is right/bottom hanger",
            attr_showonlyiftrue = True),
        
        mirrorGlyph = dict(
            attr_isoutputglyph = True,
            attr_label = "Mirror bracketing glyph",
            attr_renumberdirect = True,
            attr_showonlyiftrue = True,
            attr_usenamerforstr = True,
            attr_validatefunc_partial = _validate_mirrorGlyph),
        
        directionality = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Directionality class",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(
                directionalityclass.names[x],
                label = label,
                **k)),
            attr_validatefunc_partial = _validate_directionality))
    
    attrSorted = (
      'floater',
      'hangsLeftTop',
      'hangsRightBottom',
      'mirrorGlyph',
      'attachesRight',
      'directionality')
    
    version = 3  # class constant
    
    #
    # Methods
    #
    
    def asNumber(self, **kwArgs):
        """
        Returns a 16-bit unsigned value representing the GlyphProperties, as
        encoded in the binary table. A keyword argument named 'glyphIndex'
        must be provided if self.mirrorGlyph is not None.
        """
        
        n = 0
        
        if self.floater:
            n = 0x8000
        
        if self.hangsLeftTop:
            n |= 0x4000
        
        if self.hangsRightBottom:
            n |= 0x2000
        
        if self.attachesRight:
            n |= 0x0080
        
        if self.mirrorGlyph is not None:
            n |= 0x1000
            delta = self.mirrorGlyph - kwArgs['glyphIndex']
            
            if not (-8 <= delta < 8):
                raise ValueError(
                  "Offset to mirror glyph does not fit in 4 bits!")
            
            n |= (delta % 16) << 8
        
        return n + self.directionality
    
    def asVersion2(self, **kwArgs):
        """
        Returns a version 2 GlyphProperties object from the data in self.
        """
        
        return glyphproperties_v2.GlyphProperties(
          floater = self.floater,
          hangsLeftTop = self.hangsLeftTop,
          hangsRightBottom = self.hangsRightBottom,
          mirrorGlyph = self.mirrorGlyph,
          attachesRight = self.attachesRight,
          directionality = self.directionality,
          **kwArgs)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GlyphProperties object to the specified
        LinkedWriter. No staking is done. A keyword argument named 'glyphIndex'
        must be provided.
        
        >>> c = GlyphProperties(floater=True, directionality=11)
        >>> utilities.hexdump(c.binaryString())
               0 | 800B                                     |..              |
        
        >>> c.mirrorGlyph = 98
        >>> c.pprint(namer=namer.testingNamer())
        Glyph is floater: True
        Mirror bracketing glyph: afii60003
        Directionality class: Other neutrals
        
        >>> utilities.hexdump(c.binaryString(glyphIndex=101))
               0 | 9D0B                                     |..              |
        """
        
        w.add("H", self.asNumber(**kwArgs))
    
    @classmethod
    def fromnumber(cls, mask, **kwArgs):
        """
        Constructs and returns a new GlyphProperties object from the specified
        value. There is one required keyword argument:
        
            glyphIndex      The index of the glyph being created. This is used
                            in case a mirror glyph is contained in the data.
        
        >>> c = GlyphProperties(attachesRight=True, directionality=11)
        >>> bs = c.binaryString()
        >>> n = 256 * bs[0] + bs[1]
        >>> c == GlyphProperties.fromnumber(n)
        True
        
        >>> c.mirrorGlyph = 98
        >>> bs = c.binaryString(glyphIndex=101)
        >>> n = 256 * bs[0] + bs[1]
        >>> c == GlyphProperties.fromnumber(n, glyphIndex=101)
        True
        """
        
        if mask & 0x1000:
            n = (mask & 0xF00) >> 8
            
            if n > 7:
                n -= 16
            
            mirGlyph = kwArgs['glyphIndex'] + n
        
        else:
            mirGlyph = None
        
        return cls(
          floater = bool(mask & 0x8000),
          hangsLeftTop = bool(mask & 0x4000),
          hangsRightBottom = bool(mask & 0x2000),
          mirrorGlyph = mirGlyph,
          attachesRight = bool(mask & 0x0080),
          directionality = mask & 0x1F)
    
    @classmethod
    def fromvalidatednumber(cls, mask, **kwArgs):
        """
        Creates and returns a new GlyphProperties object from the specified
        value, doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        
        if mask & 0x0060:
            logger.warning((
              'V0779',
              (),
              "One or more of the 0x0060 bits are set. These should be zero."))
        
        if mask & 0x1000:
            n = (mask & 0x0F00) >> 8
            
            if n > 7:
                n -= 16
            
            mirGlyph = kwArgs['glyphIndex'] + n
        
        else:
            if mask & 0x0F00:
                logger.warning((
                  'V0780',
                  (),
                  "There is a nonzero offset to a mirror glyph, but the "
                  "0x1000 bit is not on."))
            
            mirGlyph = None
        
        return cls(
          floater = bool(mask & 0x8000),
          hangsLeftTop = bool(mask & 0x4000),
          hangsRightBottom = bool(mask & 0x2000),
          mirrorGlyph = mirGlyph,
          attachesRight = bool(mask & 0x0080),
          directionality = mask & 0x1F)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphProperties object from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = GlyphProperties.fromvalidatedbytes
        >>> origObj = GlyphProperties(
        ...   mirrorGlyph = 39,
        ...   attachesRight = True,
        ...   directionality = 4)
        >>> s = origObj.binaryString(glyphIndex=35)
        >>> obj = fvb(s, glyphIndex=35, logger=logger)
        fvw.glyphproperties_v2 - DEBUG - Walker has 2 remaining bytes.
        >>> obj == origObj
        True
        
        >>> ba = bytearray(s)
        >>> ba[1] |= 0x60
        >>> obj = fvb(bytes(ba), glyphIndex=35, logger=logger)
        fvw.glyphproperties_v2 - DEBUG - Walker has 2 remaining bytes.
        fvw.glyphproperties_v2 - WARNING - One or more of the 0x0060 bits are set. These should be zero.
        
        >>> ba = bytearray(s)
        >>> ba[0] &= 0xEF
        >>> obj = fvb(bytes(ba), glyphIndex=35, logger=logger)
        fvw.glyphproperties_v2 - DEBUG - Walker has 2 remaining bytes.
        fvw.glyphproperties_v2 - WARNING - There is a nonzero offset to a mirror glyph, but the 0x1000 bit is not on.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("glyphproperties_v2")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls.fromvalidatednumber(w.unpack("H"), logger=logger, **kwArgs)
    
    @classmethod
    def fromversion2(cls, v2Obj, **kwArgs):
        """
        Returns a new version 3 GlyphProperties object from the specified
        version 2 GlyphProperties object.
        """
        
        delKeys = {
          'attachesRight',
          'directionality',
          'floater',
          'hangsLeftTop',
          'hangsRightBottom',
          'mirrorGlyph'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        return cls(
          floater = v2Obj.floater,
          hangsLeftTop = v2Obj.hangsLeftTop,
          hangsRightBottom = v2Obj.hangsRightBottom,
          mirrorGlyph = v2Obj.mirrorGlyph,
          attachesRight = v2Obj.attachesRight,
          directionality = int(v2Obj.directionality),
          **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Constructs and returns a new GlyphProperties object from the specified
        walker. There is one required keyword argument:
        
            glyphIndex      The index of the glyph being created. This is used
                            in case a mirror glyph is contained in the data.
        
        >>> c = GlyphProperties(floater=True, directionality=11)
        >>> c == GlyphProperties.frombytes(c.binaryString())
        True
        
        >>> c.mirrorGlyph = 98
        >>> c == GlyphProperties.frombytes(
        ...   c.binaryString(glyphIndex=101),
        ...   glyphIndex = 101)
        True
        """
        
        return cls.fromnumber(w.unpack("H"), **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.prop import glyphproperties_v1
    from fontio3.utilities import namer

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
