#
# PCLT.py
#
# Copyright © 2009-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entire 'PCLT' tables.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta

from fontio3.PCLT import (
  charactercomplement,
  posture,
  serifcontrast,
  serifstyle,
  strokeweight,
  structure,
  vendor2,
  vendorcode,
  width,
  widthtype)

from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private methods
#

def _pprint_single(p, x, label, **kwArgs):
    p.simple(x, label=label, **kwArgs)

def _validate_pitch(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate pitch, because no 'cmap' table is present."))
        
        return False
    
    uMap = editor.cmap.getUnicodeMap()
    
    if 0x0020 not in uMap:
        logger.error((
          'V0796',
          (),
          "There is no space character in the Unicode cmap, so "
          "the pitch cannot be validated."))
        
        return False
    
    spaceGlyphIndex = uMap[0x0020]
    
    if not editor.reallyHas(b'hmtx'):
        logger.error((
          'V0553',
          (),
          "Unable to validate pitch, because no 'hmtx' table is present."))
        
        return False
    
    spaceWidth = editor.hmtx[spaceGlyphIndex].advance
    
    if obj != spaceWidth:
        logger.error((
          'E2201',
          (spaceWidth, obj),
          "The space has a width of %d, but the pitch is %d."))
        
        return False
    
    return True

def _validate_symbolSet(obj, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        n = int(obj[:-1])
        ok = True
    except:
        ok = False
    
    if not ok:
        logger.error((
          'V0794',
          (obj,),
          "The first part of the symbol set code '%s' is not a valid number."))
        
        return False
    
    if not valassist.isNumber_integer_unsigned(
      n,
      numBits = 11,
      label = "symbol set number",
      logger = logger):
        
        return False
    
    n = ord(obj[-1]) - 64
    
    if not valassist.isNumber_integer_unsigned(
      n,
      numBits = 6,
      label = "symbol set ID",
      logger = logger):
      
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PCLT(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire PCLT tables. These are collections of
    attributes.
    
    >>> _testingValues[1].pprint()
    Native (created by font vendor): False
    Vendor: Monotype
    Font number: 5526016
    Pitch (width of space): 569
    x-Height: 1062
    Structure: Solid (normal, black)
    Width: Normal
    Posture: Upright
    Vendor2: Monotype
    Type family: 939
    Cap-height: 1466
    Symbol set: 0@
    Type face: Albany
    Character Complement:
      ASCII (supports several standard interpretations)
      Desktop Publishing extensions
      Latin 1 extensions
      Macintosh extensions
      Unicode order
    File name: ALBR00
    Stroke weight: Book, text, regular, etc.
    Width type: Normal
    Serif style: Sans-serif Square
    Contrast/Monoline: Sans-serif/Monoline
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        native = dict(
            attr_initfunc = (lambda: True),
            attr_label = "Native (created by font vendor)"),
        
        vendorCode = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: vendorcode.VendorCode(ord(b'M'))),  # Monotype
            attr_label = "Vendor",
            attr_pprintfunc = _pprint_single),
        
        fontNumber = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Font number",
            
            attr_validatefunc = functools.partial(
              valassist.isNumber_integer_unsigned,
              numBits = 24,
              label = "font number")),
        
        pitch = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Pitch (width of space)",
            attr_scaledirect = True,
            attr_validatefunc = _validate_pitch),
        
        xHeight = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "x-Height",
            attr_scaledirect = True),
        
        structure = dict(
            attr_followsprotocol = True,
            attr_initfunc = structure.Structure,
            attr_label = "Structure",
            attr_pprintfunc = _pprint_single),
        
        width = dict(
            attr_followsprotocol = True,
            attr_initfunc = width.Width,
            attr_label = "Width",
            attr_pprintfunc = _pprint_single),
        
        posture = dict(
            attr_followsprotocol = True,
            attr_initfunc = posture.Posture,
            attr_label = "Posture",
            attr_pprintfunc = _pprint_single),
        
        vendor2 = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: vendor2.Vendor2(4)),  # Monotype
            attr_label = "Vendor2",
            attr_pprintfunc = _pprint_single),
        
        typeFamily = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Type family",
            
            attr_validatefunc = functools.partial(
              valassist.isNumber_integer_unsigned,
              numBits = 12,
              label = "type family")),
        
        capHeight = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Cap-height",
            attr_scaledirect = True),
        
        symbolSet = dict(
            attr_initfunc = (lambda: b"0U"),  # ASCII
            attr_label = "Symbol set",
            attr_validatefunc = _validate_symbolSet),
        
        typeFace = dict(
            attr_initfunc = (lambda: ' ' * 16),
            attr_label = "Type face",
            
            attr_validatefunc = functools.partial(
              valassist.isString,
              maxSize = 16,
              label = "type face")),
        
        characterComplement = dict(
            attr_followsprotocol = True,
            attr_initfunc = charactercomplement.CharacterComplement,
            attr_label = "Character Complement"),
        
        fileName = dict(
            attr_initfunc = (lambda: ' ' * 6),
            attr_label = "File name",
            
            attr_validatefunc = functools.partial(
              valassist.isString,
              minSize = 6,
              maxSize = 6,
              label = "file name")),
        
        strokeWeight = dict(
            attr_followsprotocol = True,
            attr_initfunc = strokeweight.StrokeWeight,
            attr_label = "Stroke weight",
            attr_pprintfunc = _pprint_single),
        
        widthType = dict(
            attr_followsprotocol = True,
            attr_initfunc = widthtype.WidthType,
            attr_label = "Width type",
            attr_pprintfunc = _pprint_single),
        
        serifStyle = dict(
            attr_followsprotocol = True,
            attr_initfunc = serifstyle.SerifStyle,
            attr_label = "Serif style",
            attr_pprintfunc = _pprint_single),
        
        serifContrast = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: serifcontrast.SerifContrast(1)),
            attr_label = "Contrast/Monoline",
            attr_pprintfunc = _pprint_single))
    
    attrSorted = (
      'native',
      'vendorCode',
      'fontNumber',
      'pitch',
      'xHeight',
      'structure',
      'width',
      'posture',
      'vendor2',
      'typeFamily',
      'capHeight',
      'symbolSet',
      'typeFace',
      'characterComplement',
      'fileName',
      'strokeWeight',
      'widthType',
      'serifStyle',
      'serifContrast')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PCLT object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = PCLT.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.PCLT - DEBUG - Walker has 54 remaining bytes.
        
        >>> fvb(s[:-1] + b'a', logger=logger)
        fvw.PCLT - DEBUG - Walker has 54 remaining bytes.
        fvw.PCLT - ERROR - Last byte should be zero (reserved), but is not.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("PCLT")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4 + w.calcsize("L6H16s"):
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x10000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00010000 but got 0x%08X instead."))
            
            return None
        
        part1 = w.unpack("L6H16s")
        
        if part1[3] & 0xFC00:
            logger.error((
              'E2205',
              (),
              "High-order six bits of style word must be zero."))
            
            return None
        
        cc = charactercomplement.CharacterComplement.fromvalidatedwalker(
          w,
          logger = logger)
        
        if cc is None:
            return None
        
        if w.length() < w.calcsize("6sbbBx"):
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        part2 = w.unpack("6s2b2B")
        
        if part2[4]:
            logger.error((
              'E2202',
              (),
              "Last byte should be zero (reserved), but is not."))
            
            return None
        
        ss1 = str((part1[6] & 0xFFE0) >> 11)
        eu = utilities.ensureUnicode
        tb = utilities.truncateBytes
        ss2 = eu((part1[6] & 0x001F) + 64)
        
        return cls(
          native = bool(part1[0] & 0x80000000),
          vendorCode = vendorcode.VendorCode((part1[0] & 0x7F000000) >> 24),
          fontNumber = part1[0] & 0x00FFFFFF,
          pitch = part1[1],
          xHeight = part1[2],
          structure = structure.Structure((part1[3] & 0x03E0) >> 5),
          width = width.Width((part1[3] & 0x001C) >> 2),
          posture = posture.Posture(part1[3] & 0x0003),
          vendor2 = vendor2.Vendor2((part1[4] & 0xF000) >> 12),
          typeFamily = part1[4] & 0x0FFF,
          capHeight = part1[5],
          symbolSet = ss1 + ss2,
          typeFace = eu(tb(part1[7])).rstrip(),
          characterComplement = cc,
          fileName = eu(part2[0]),
          strokeWeight = strokeweight.StrokeWeight(part2[1]),
          widthType = widthtype.WidthType(part2[2]),
          serifStyle = serifstyle.SerifStyle(part2[3] & 0x3F),
          serifContrast = serifcontrast.SerifContrast((part2[3] & 0xC0) >> 6))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PCLT object from the specified walker.
        
        >>> _testingValues[1] == PCLT.frombytes(_testingValues[1].binaryString())
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x00010000:
            raise ValueError("PCLT Version not supported: 0x%08X" % (version,))
        
        part1 = w.unpack("L6H16s")
        cc = charactercomplement.CharacterComplement.fromwalker(w)
        part2 = w.unpack("6sbbBx")
        ss1 = str((part1[6] & 0xFFE0) >> 11)
        eu = utilities.ensureUnicode
        tb = utilities.truncateBytes
        ss2 = eu((part1[6] & 0x001F) + 64)
        
        return cls(
          native = bool(part1[0] & 0x80000000),
          vendorCode = vendorcode.VendorCode((part1[0] & 0x7F000000) >> 24),
          fontNumber = part1[0] & 0x00FFFFFF,
          pitch = part1[1],
          xHeight = part1[2],
          structure = structure.Structure((part1[3] & 0x03E0) >> 5),
          width = width.Width((part1[3] & 0x001C) >> 2),
          posture = posture.Posture(part1[3] & 0x0003),
          vendor2 = vendor2.Vendor2((part1[4] & 0xF000) >> 12),
          typeFamily = part1[4] & 0x0FFF,
          capHeight = part1[5],
          symbolSet = ss1 + ss2,
          typeFace = eu(tb(part1[7])).rstrip(),
          characterComplement = cc,
          fileName = eu(part2[0]),
          strokeWeight = strokeweight.StrokeWeight(part2[1]),
          widthType = widthtype.WidthType(part2[2]),
          serifStyle = serifstyle.SerifStyle(part2[3] & 0x3F),
          serifContrast = serifcontrast.SerifContrast((part2[3] & 0xC0) >> 6))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PCLT object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 4D54 5200  0239 0426 0000 43AB |....MTR..9.&..C.|
              10 | 05BA 0000 416C 6261  6E79 2020 2020 2020 |....Albany      |
              20 | 2020 2020 FFFF FFFF  36FF FFFE 414C 4252 |    ....6...ALBR|
              30 | 3030 0000 4000                           |00..@.          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        eb = utilities.ensureBytes
        
        # version
        w.add("L", 0x00010000)
        
        # native, vendorCode, fontNumber
        n = (0x80000000 if self.native else 0)
        n += (self.vendorCode << 24)
        n += self.fontNumber
        w.add("L", n)
        
        # pitch, xHeight
        w.add("2H", self.pitch, self.xHeight)
        
        # structure, width, posture
        w.add("H", (self.structure << 5) + (self.width << 2) + self.posture)
        
        # vendor2, typeFamily
        w.add("H", (self.vendor2 << 12) + self.typeFamily)
        
        # capHeight
        w.add("H", self.capHeight)
        
        # symbolSet
        s = self.symbolSet
        w.add("H", (int(s[:-1]) << 11) + (ord(s[-1]) - 64))
        
        # typeFace
        tf = (self.typeFace + (" "*16))[0:16]
        w.addString( eb(tf) )
        
        # characterComplement
        self.characterComplement.buildBinary(w)
        
        # fileName
        fn = (self.fileName + (" "*6))[0:6]
        w.addString( eb(fn) )
        
        # strokeWeight, serifContrast, widthType
        w.add("2b", self.strokeWeight, self.widthType)
        
        # serifStyle, padding
        w.add("Bx", (self.serifContrast << 6) + self.serifStyle)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _cv = charactercomplement._testingValues
    
    _testingValues = (
        PCLT(),
        
        PCLT(
          native = False,
          vendorCode = vendorcode.VendorCode(77),
          fontNumber = 5526016,
          pitch = 569,
          xHeight = 1062,
          structure = structure.Structure(0),
          width = width.Width(0),
          posture = posture.Posture(0),
          vendor2 = vendor2.Vendor2(4),
          typeFamily = 939,
          capHeight = 1466,
          symbolSet = '0@',
          typeFace = 'Albany',
          characterComplement = _cv[2],
          fileName = 'ALBR00',
          strokeWeight = strokeweight.StrokeWeight(0),
          widthType = widthtype.WidthType(0),
          serifStyle = serifstyle.SerifStyle(0),
          serifContrast = serifcontrast.SerifContrast(1)))
    
    del _cv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
