#
# OS_2_v5.py
#
# Copyright © 2010-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Version 5 OS/2 tables.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta

from fontio3.OS_2 import (
  codepageranges_v2,
  familyclass_v0,
  OS_2_v4,
  panose,
  panose_fam2_v2,
  selection_v4,
  typeflags_v3,
  unicoderanges_v4,
  vendors_v0)

# -----------------------------------------------------------------------------

#
# Private constants
#

_weightClassNames = (
  "Thin",
  "Ultra-light",
  "Light",
  "Regular",
  "Medium",
  "Demi-bold",
  "Bold",
  "Ultra-bold",
  "Heavy")

_widthClassNames = (
  "Ultra-condensed",
  "Extra-condensed",
  "Condensed",
  "Semi-condensed",
  "Normal",
  "Semi-expanded",
  "Expanded",
  "Extra-expanded",
  "Ultra-expanded")

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_usWeightClass(p, value, label, **kwArgs):
    """
    >>> p = pp.PP()
    >>> _pprint_usWeightClass(p, 300, "Weight class")
    Weight class: Light (value 300)
    
    >>> _pprint_usWeightClass(p, 350, "Weight class")
    Weight class: Between Light and Regular (value 350)
    
    >>> _pprint_usWeightClass(p, 30, "Weight class")
    Weight class: Thinner than 'Thin' (value 30)
    
    >>> _pprint_usWeightClass(p, 3000, "Weight class")
    Weight class: Heavier than 'Heavy' (value 3000)
    """
    
    if value < 100:
        s = "Thinner than 'Thin' (value %d)" % (value,)
    elif value > 900:
        s = "Heavier than 'Heavy' (value %d)" % (value,)
    else:
        n = (value - 100) // 100
        
        if value % 100:
            t = (_weightClassNames[n], _weightClassNames[n+1], value)
            s = "Between %s and %s (value %d)" % t
        
        else:
            s = "%s (value %d)" % (_weightClassNames[n], value)
    
    p.simple(s, label=label)

def _pprint_usWidthClass(p, value, label, **kwArgs):
    """
    >>> p = pp.PP()
    >>> _pprint_usWidthClass(p, 7, "Width class")
    Width class: Expanded
    
    >>> _pprint_usWidthClass(p, 11, "Width class")
    Traceback (most recent call last):
      ...
    ValueError: Unknown width class value: 11
    """
    
    if value not in frozenset(range(1, 10)):
        raise ValueError("Unknown width class value: %s" % (value,))
    
    p.simple(_widthClassNames[value - 1], label=label)

def _recalc_fsSelection(oldValue, **kwArgs):
    newValue = oldValue.__copy__()
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'head'):
        raise NoHead()
    
    headFlags = e.head.macStyle
    
    # sync bold and italic
    newValue.bold = headFlags.bold
    newValue.italic = headFlags.italic
    
    # do regular check
    if oldValue.regular:
        newValue.bold = newValue.italic = False
    
    return newValue != oldValue, newValue

def _recalc_sxHeight(oldValue, **kwArgs):
    newValue = 0
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'cmap'):
        raise NoCmap()
    
    m = e.cmap.getUnicodeMap() or {0}

    gtbl = None
    if b'glyf' in e:
        gtbl = e.glyf
    if b'CFF ' in e:
        gtbl = e[b'CFF ']
    
    if gtbl is None or 0x78 not in m:
        return newValue != oldValue, newValue

    gl = gtbl[m[0x78]]
    
    if gl:
        newValue = gl.bounds.yMax
    
    return newValue != oldValue, newValue

def _recalc_sCapHeight(oldValue, **kwArgs):
    newValue = 0
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'cmap'):
        raise NoCmap()
    
    m = e.cmap.getUnicodeMap() or {0}

    gtbl = None
    if b'glyf' in e:
        gtbl = e.glyf
    if b'CFF ' in e:
        gtbl = e[b'CFF ']
    
    if gtbl is None or 0x48 not in m:
        return newValue != oldValue, newValue

    gl = gtbl[m[0x48]]
    
    if gl:
        newValue = gl.bounds.yMax
    
    return newValue != oldValue, newValue

def _recalc_usBreakChar(oldValue, **kwArgs):
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'cmap'):
        raise NoCmap()
    
    m = e.cmap.getUnicodeMap()
    
    if not m:
        m = e.cmap.getSymbolMap() or {0}
    
    if oldValue in m:
        return False, oldValue
    
    return True, min(m)

def _recalc_usFirstCharIndex(oldValue, **kwArgs):
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'cmap'):
        raise NoCmap()
    
    m = e.cmap.getUnicodeMap()
    
    if not m:
        m = e.cmap.getSymbolMap() or [0]
    
    newValue = min(0xFFFF, min(m))
    return newValue != oldValue, newValue

def _recalc_usLastCharIndex(oldValue, **kwArgs):
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'cmap'):
        raise NoCmap()
    
    m = e.cmap.getUnicodeMap()
    
    if not m:
        m = e.cmap.getSymbolMap() or [0]
    
    newValue = min(0xFFFF, max(m))
    return newValue != oldValue, newValue

def _recalc_usMaxContext(oldValue, **kwArgs):
    e = kwArgs['editor']
    
    if e is None:
        raise NoEditor()
    
    newValue = e.gatheredMaxContext()
    return newValue != oldValue, newValue

def _recalc_xAvgCharWidth(oldValue, **kwArgs):
    editor = kwArgs['editor']
    
    if editor is None:
        raise NoEditor()
    
    if not editor.reallyHas(b'hmtx'):
        raise NoHmtx()
    
    mtx = editor.hmtx
    v = [obj.advance for obj in mtx.values() if obj.advance]
    
    if not v:
        return 0
    
    newValue = int(sum(v) / len(v))
    return newValue != oldValue, newValue

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj.fsSelection.bold and (obj.usWeightClass < 500):
        logger.warning((
          'W2103',
          (obj.fsSelection.bold, obj.usWeightClass),
          "The fsSelection.bold bit (%s) is inconsistent "
          "with the usWeightClass %d"))
    
    panoseEnumInvs = obj.panoseArray.getEnumInverseMaps()
    
    if 'weight' in panoseEnumInvs:
        panoseAsWeightClass = (
          panoseEnumInvs['weight'][obj.panoseArray.weight] * 89 + 100)
        
        pwdifference = abs(obj.usWeightClass - panoseAsWeightClass)
    
        if pwdifference >= 200:
            logger.warning((
              'W2116',
              (obj.usWeightClass, obj.panoseArray.weight),
              "The usWeightClass %d is inconsistent "
              "with the PANOSE weight %s"))

    if not obj.fsSelection.italic:
        if obj.ySuperscriptXOffset != 0:
            logger.warning((
                'V0340',
                (),
                "The ySuperscriptXOffset is non-zero, but the font is not "
                "styled as italic."))
        
        if obj.ySubscriptXOffset != 0:
            logger.warning((
                'V0340',
                (),
                "The ySubscriptXOffset is non-zero, but the font is not "
                "styled as italic."))
    
    return True

def _validate_sCapHeight(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    numGlyphs = utilities.getFontGlyphCount(**kwArgs)
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate sCapHeight because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    if value < 0:
        logger.error((
          'Vxxxx',
          (value,),
          "sCapHeight (%d) is less than zero!"))

        return False
    
    umap = editor.cmap.getUnicodeMap()
    gidofH = umap.get(0x0048)

    if gidofH is not None:
        if not 0 <= gidofH < numGlyphs:
            logger.error((
              'Vxxxx',
              (gidofH,),
              "sCapHeight value could not be validated because the glyph "
              "corresponding to 'H' (%d) is out of range for the font."))
            
            return False
        
        if editor.reallyHas(b'glyf'):
            gObj = editor.glyf[gidofH]
        
        elif editor.reallyHas(b'CFF '):
            gObj = editor[b'CFF '][gidofH]
        
        else:
            logger.warning((
              'Vxxxx',
              (value,),
              "No 'glyf' or 'CFF ' table present; could not validate "
              "sCapHeight value (%d)"))
            
            return True

        if gObj and gObj.bounds:
            actual = gObj.bounds.yMax
        else:
            actual = None
        
        if value != actual:
            logger.warning((
              'Vxxxx',
              (value, actual),
              "sCapHeight value (%d) does not match yMax of 'H' (%s)"))
              
    else:
        logger.warning((
          'Vxxxx',
          (value,),
          "sCapHeight value (%d) could not be validated because no "
          "glyph for 'H' is present in the font."))
          
    return True

def _validate_sFamilyClass(value, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        inRange = 0 <= value < 0x10000
    except:
        inRange = False
    
    if not inRange:
        logger.error((
          'G0009',
          (),
          "The sFamilyClass value is non-numeric or out of range."))
        
        return False
    
    hi, lo = divmod(value, 256)
    r = True
    
    if hi in {6, 11, 13, 14}:
        logger.error((
          'E2119',
          (hi,),
          "The sFamilyClass class ID %d is reserved."))
        
        r = False
    
    elif hi > 14:
        logger.error((
          'E2120',
          (hi,),
          "The sFamilyClass class ID %d is undefined."))
        
        r = False
    
    if value not in familyclass_v0.labels:
        logger.error((
          'E2121',
          (lo, hi),
          "The sFamilyClass subclass %d is not defined for class %d"))
        
        r = False
    
    return r

def _validate_sxHeight(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    numGlyphs = utilities.getFontGlyphCount(**kwArgs)
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate sxHeight because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    if value < 0:
        logger.error((
          'Vxxxx',
          (value,),
          "sxHeight (%d) is less than zero!"))

        return False
    
    umap = editor.cmap.getUnicodeMap()
    gidofx = umap.get(0x0078)

    if gidofx is not None:
        if not 0 <= gidofx < numGlyphs:
            logger.error((
              'Vxxxx',
              (gidofx,),
              "sxHeight value could not be validated because the glyph "
              "corresponding to 'x' (%d) is out of range for the font."))
            
            return False
        
        if editor.reallyHas(b'glyf'):
            gObj = editor.glyf[gidofx]
        
        elif editor.reallyHas(b'CFF '):
            gObj = editor[b'CFF '][gidofx]
        
        else:
            logger.warning((
              'Vxxxx',
              (value,),
              "No 'glyf' or 'CFF ' table present; could not validate "
              "sxHeight value (%d)"))
            
            return True

        if gObj and gObj.bounds:
            actual = gObj.bounds.yMax
        else:
            actual = None
        
        if value != actual:
            logger.warning((
              'Vxxxx',
              (value, actual),
              "sxHeight value (%d) does not match yMax of 'x' (%s)"))
              
    else:
        logger.warning((
          'Vxxxx',
          (value,),
          "sxHeight value (%d) could not be validated because no "
          "glyph for 'x' is present in the font."))
          
    return True

def _validate_twip(value, **kwArgs):
    n = round(value * 20)
    
    if n < 0 or n > 0xFFFF:
        logger.error((
          'V0923',
          (value,),
          "The value %s (in TWIPs) cannot be represented in an unsigned "
          "16-bit value."))
        
        return False
    
    return True

def _validate_usBreakChar(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate usBreakChar because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    m = editor.cmap.getUnicodeMap()
    
    if not m:
        m = editor.cmap.getSymbolMap() or set()
    
    if (not value) or (value not in m):
        logger.error((
          'E2128',
          (value,),
          "The usBreakChar value of 0x%04X is not valid."))
        
        return False
    
    return True

def _validate_usDefaultChar(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate usDefaultChar because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    m = editor.cmap.getUnicodeMap()
    
    if not m:
        m = editor.cmap.getSymbolMap() or set()
    
    if value and (value not in m):
        logger.error((
          'E2129',
          (value,),
          "The usDefaultChar value of 0x%04X is not valid."))
        
        return False
    
    return True

def _validate_usFirstCharIndex(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if (editor is None) or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate usFirstCharIndex because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    uMap = editor.cmap.getUnicodeMap()
    
    if not uMap:
        uMap = editor.cmap.getSymbolMap() or [0]
    
    actualMin = min(0xFFFF, min(uMap))
    
    if value != actualMin:
        logger.error((
          'E2130',
          (actualMin, value),
          "The usFirstCharIndex should be 0x%04X, but is 0x%04X"))
        
        return False
    
    return True

def _validate_usLastCharIndex(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None or (not editor.reallyHas(b'cmap')):
        logger.error((
          'V0553',
          (),
          "Unable to validate usLastCharIndex because the Editor and/or "
          "Cmap are missing or empty."))
        
        return False
    
    uMap = editor.cmap.getUnicodeMap()
    
    if not uMap:
        uMap = editor.cmap.getSymbolMap() or [0]
    
    actualMax = min(0xFFFF, max(uMap))
    
    if value != actualMax:
        logger.error((
          'E2131',
          (actualMax, value),
          "The usLastCharIndex should be 0x%04X, but is 0x%04X"))
        
        return False
    
    return True

def _validate_usMaxContext(value, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        changed, correctValue = _recalc_usMaxContext(value, **kwArgs)
    except ValueError:
        changed = None
    
    if changed is None:
        logger.warning((
          'V0553',
          (),
          "Could not validate usMaxContext because table(s) are missing"))
    
    elif changed:
        logger.error((
          'V0831',
          (correctValue, value),
          "The usMaxContext should be %d, but is %d"))
        
        return False
    
    return True

def _validate_usWeightClass(value, **kwArgs):
    logger = kwArgs['logger']
    q, r = divmod(value, 100)

    # 20160408: re-vamp to address VALIDATE-211

    if r == 0 and 1 <= q <= 9:  # simple multiple of 100 in range 100-999
        logger.info((
          'V1055',
          (value,),
          "The usWeightClass value %d is valid"))

    elif r == 50 and 2 <= q <= 9:  # multiple of 50 in range 250-999
        logger.warning((
          'V1056',
          (value,),
          "The usWeightClass value %d is valid, but is "
          "not a multiple of 100"))

    else:
        logger.error((
          'E2133',
          (value,),
          "The usWeightClass value %d is not valid"))
        
        return False
    
    return True

def _validate_usWidthClass(value, **kwArgs):
    logger = kwArgs['logger']
    
    if (value < 1) or (value > 9):
        logger.error((
          'E2134',
          (value,),
          "The usWidthClass value %d is not valid"))
        
        return False
    
    return True

def _validate_usWinAscent(value, **kwArgs):
    logger = kwArgs['logger']
    headTbl = kwArgs['editor'].head
    
    if value == 0:
        logger.error((
          'V0821',
          (),
          "The usWinAscent value is zero."))
        
        return False

    if headTbl.yMax > value:
        logger.warning((
          'V0918',
          (headTbl.yMax, value),
          "The font-wide head.yMax %d exceeds the usWinAscent %d. Clipping may occur."))
    
    return True

def _validate_usWinDescent(value, **kwArgs):
    logger = kwArgs['logger']
    headTbl = kwArgs['editor'].head
    
    if value == 0:
        logger.error((
          'V0821',
          (),
          "The usWinDescent value is zero."))
        
        return False

    if abs(headTbl.yMin) > value:
        logger.warning((
          'V0919',
          (headTbl.yMin, value),
          "The font-wide head.yMin %d exceeds the usWinDescent %d. Clipping may occur."))
    
    return True

def _validate_xAvgCharWidth(value, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        changed, correctValue = _recalc_xAvgCharWidth(value, **kwArgs)
    except ValueError:
        changed = None
    
    if changed is None:
        logger.warning((
          'W2104',
          (),
          "Could not validate xAvgCharWidth because table(s) are missing"))
    
    elif changed:
        logger.error((
          'E2135',
          (correctValue, value),
          "The xAvgCharWidth should be %d, but is %d"))
        
        return False
    
    return True

def _validate_yStrikeoutPosition(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= e.head.unitsPerEm:
        logger.warning((
          'W2107',
          (value,),
          "The yStrikeoutPosition value of %d is unlikely. I guess."))
    
    return True

def _validate_yStrikeoutSize(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= (e.head.unitsPerEm // 4):
        logger.warning((
          'W2108',
          (value,),
          "The yStrikeoutSize value of %d seems iffy."))
    
    return True

def _validate_ySubscriptXOffset(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if abs(value) >= e.head.unitsPerEm:
        logger.warning((
          'V0341',
          (value,),
          "The ySubscriptXOffset value of %d is unlikely."))
    
    else:
        logger.info((
          'V0339',
          (value,),
          "The ySubscriptXOffset value is %d"))

    return True

def _validate_ySubscriptXSize(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= e.head.unitsPerEm:
        logger.warning((
          'W2109',
          (value,),
          "The ySubscriptXSize value of %d is, like, totally wack."))
    
    return True

def _validate_ySubscriptYOffset(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if abs(value) >= e.head.unitsPerEm:
        logger.warning((
          'V0341',
          (value,),
          "The ySubscriptYOffset value of %d is unlikely."))
    
    else:
        logger.info((
          'V0339',
          (value,),
          "The ySubscriptYOffset value is %d"))

    return True

def _validate_ySubscriptYSize(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= e.head.unitsPerEm:
        logger.warning((
          'W2111',
          (value,),
          "The ySubscriptYSize value of %d has bad karma."))
    
    return True

def _validate_ySuperscriptXOffset(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if abs(value) >= e.head.unitsPerEm:
        logger.warning((
          'V0341',
          (value,),
          "The ySuperscriptXOffset value of %d is unlikely."))
    
    else:
        logger.info((
          'V0339',
          (value,),
          "The ySuperscriptXOffset value is %d"))

    return True

def _validate_ySuperscriptXSize(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= e.head.unitsPerEm:
        logger.warning((
          'W2112',
          (value,),
          "The ySuperscriptXSize value of %d is, like, totally wack."))
    
    return True

def _validate_ySuperscriptYOffset(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if abs(value) >= e.head.unitsPerEm:
        logger.warning((
          'V0341',
          (value,),
          "The ySuperscriptYOffset value of %d is unlikely."))
    
    else:
        logger.info((
          'V0339',
          (value,),
          "The ySuperscriptYOffset value is %d"))

    return True

def _validate_ySuperscriptYSize(value, **kwArgs):
    logger = kwArgs['logger']
    e = kwArgs['editor']
    
    if e is None or (not e.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate yStrikeoutPosition, because the Editor and/or "
          "Head table are missing or empty."))
        
        return False
    
    if value < 0 or value >= e.head.unitsPerEm:
        logger.warning((
          'W2114',
          (value,),
          "The ySuperscriptYSize value of %d has bad karma."))
    
    return True


# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class NoCmap(ValueError): pass
class NoEditor(ValueError): pass
class NoHead(ValueError): pass
class NoHmtx(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class OS_2(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Version 5 OS/2 tables.
    
    >>> _testingValues[1].pprint()
    OS/2 Version: 5
    Average weighted escapement: 600
    Weight class: Demi-bold (value 600)
    Width class: Extra-expanded
    Type Flags:
      Embedding Level: Preview & Print Embedding
    Subscript horizontal font size: 0
    Subscript vertical font size: 0
    Subscript x-offset: 0
    Subscript y-offset: 0
    Superscript horizontal font size: 0
    Superscript vertical font size: 0
    Superscript x-offset: 0
    Superscript y-offset: 0
    Strikeout size: 0
    Strikeout position: 0
    IBM font family class and subclass: No Classification
    PANOSE specification:
      Family Type: Latin Text
      Serif Type: Flared
      Weight: Any
      Proportion: Extended
      Contrast: Any
      Stroke Variation: Any
      Arm Style: Any
      Letterform: Any
      Midline: Any
      x-Height: Any
    Unicode coverage:
      hasBasicLatin
      hasLatin1Supplement
    Font vendor: Monotype
    Selection Flags:
      Strikeout
    Minimum Unicode: 32
    Maximum Unicode: 32
    Typographic ascender: 1400
    Typographic descender: -800
    Typographic line gap: 0
    Windows ascender: 0
    Windows descender: 0
    Code Page Character Ranges:
      Latin 1 (CP 1252)
      Hebrew (CP 1255)
    x-Height: 0
    Cap-Height: 0
    Missing character: 0
    Break character: 32
    Maximum target glyph context: 4
    Lowest PPEM set by designer: 4.5
    Highest PPEM set by designer: 325.75
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 5),
            attr_label = "OS/2 Version"),
        
        xAvgCharWidth = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Average weighted escapement",
            attr_recalculatefunc = _recalc_xAvgCharWidth,
            attr_representsx = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_xAvgCharWidth),
        
        usWeightClass = dict(
            attr_initfunc = (lambda: 400),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Weight class",
            attr_pprintfunc = _pprint_usWeightClass,
            attr_validatefunc = _validate_usWeightClass),
        
        usWidthClass = dict(
            attr_initfunc = (lambda: 5),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Width class",
            attr_pprintfunc = _pprint_usWidthClass,
            attr_validatefunc = _validate_usWidthClass),
        
        fsType = dict(
            attr_followsprotocol = True,
            attr_initfunc = typeflags_v3.TypeFlags,
            attr_label = "Type Flags"),
        
        ySubscriptXSize = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Subscript horizontal font size",
            attr_scaledirect = True,
            attr_validatefunc = _validate_ySubscriptXSize),
        
        ySubscriptYSize = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Subscript vertical font size",
            attr_scaledirect = True,
            attr_validatefunc = _validate_ySubscriptYSize),
        
        ySubscriptXOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Subscript x-offset",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_ySubscriptXOffset),
        
        ySubscriptYOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Subscript y-offset",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_ySubscriptYOffset),
        
        ySuperscriptXSize = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Superscript horizontal font size",
            attr_scaledirect = True,
            attr_validatefunc = _validate_ySuperscriptXSize),
        
        ySuperscriptYSize = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Superscript vertical font size",
            attr_scaledirect = True,
            attr_validatefunc = _validate_ySuperscriptYSize),
        
        ySuperscriptXOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Superscript x-offset",
            attr_representsx = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_ySuperscriptXOffset),
        
        ySuperscriptYOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Superscript y-offset",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_ySuperscriptYOffset),
        
        yStrikeoutSize = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Strikeout size",
            attr_scaledirect = True,
            attr_representsy = True,
            attr_validatefunc_partial = _validate_yStrikeoutSize),
        
        yStrikeoutPosition = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Strikeout position",
            attr_representsy = True,
            attr_scaledirect = True,
            attr_validatefunc_partial = _validate_yStrikeoutPosition),
        
        sFamilyClass = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "IBM font family class and subclass",
            attr_pprintfunc = (
              lambda p, n, label, **k:
              p.simple(familyclass_v0.labels[n], label=label)),
            attr_validatefunc = _validate_sFamilyClass),
        
        panoseArray = dict(
            attr_followsprotocol = True,
            attr_initfunc = panose_fam2_v2.Panose_fam2,
            attr_label = "PANOSE specification"),
        
        unicodeRanges = dict(
            attr_followsprotocol = True,
            attr_initfunc = unicoderanges_v4.UnicodeRanges,
            attr_label = "Unicode coverage"),
        
        achVendID = dict(
            attr_initfunc = (lambda: b'MONO'),
            attr_label = "Font vendor",
            attr_pprintfunc = (
              lambda p, n, label, **k:
              p.simple(vendors_v0.labels[n], label=label))),
        
        fsSelection = dict(
            attr_followsprotocol = True,
            attr_initfunc = selection_v4.Selection,
            attr_label = "Selection Flags",
            attr_recalculatefunc = _recalc_fsSelection),
        
        usFirstCharIndex = dict(
            attr_initfunc = (lambda: 0x0020),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Minimum Unicode",
            attr_recalculatefunc = _recalc_usFirstCharIndex,
            attr_validatefunc = _validate_usFirstCharIndex),
        
        usLastCharIndex = dict(
            attr_initfunc = (lambda: 0x0020),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Maximum Unicode",
            attr_recalculatefunc = _recalc_usLastCharIndex,
            attr_validatefunc = _validate_usLastCharIndex),
        
        sTypoAscender = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Typographic ascender",
            attr_scaledirect = True,
            attr_representsy = True),
        
        sTypoDescender = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Typographic descender",
            attr_scaledirect = True,
            attr_representsy = True),
        
        sTypoLineGap = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Typographic line gap",
            attr_scaledirect = True,
            attr_representsy = True),
        
        usWinAscent = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Windows ascender",
            attr_scaledirect = True,
            attr_representsy = True,
            attr_validatefunc = _validate_usWinAscent),
        
        usWinDescent = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Windows descender",
            attr_scaledirect = True,
            attr_representsy = True,
            attr_validatefunc = _validate_usWinDescent),
        
        codePageRanges = dict(
            attr_followsprotocol = True,
            attr_initfunc = codepageranges_v2.CodePageRanges,
            attr_label = "Code Page Character Ranges"),
        
        sxHeight = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "x-Height",
            attr_scaledirect = True,
            attr_representsy = True,
            attr_validatefunc_partial = _validate_sxHeight),
        
        sCapHeight = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Cap-Height",
            attr_scaledirect = True,
            attr_representsy = True,
            attr_validatefunc_partial = _validate_sCapHeight),
        
        usDefaultChar = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Missing character",
            attr_validatefunc = _validate_usDefaultChar),
        
        usBreakChar = dict(
            attr_initfunc = (lambda: 0x0020),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Break character",
            attr_recalculatefunc = _recalc_usBreakChar,
            attr_validatefunc = _validate_usBreakChar),
        
        usMaxContext = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Maximum target glyph context",
            attr_recalculatefunc = _recalc_usMaxContext,
            attr_validatefunc = _validate_usMaxContext),
        
        usLowerOpticalPointSize = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Lowest PPEM set by designer",
            attr_validatefunc = _validate_twip),
        
        usUpperOpticalPointSize = dict(
            attr_initfunc = (lambda: 3276.75),
            attr_label = "Highest PPEM set by designer",
            attr_validatefunc = _validate_twip))
    
    attrSorted = (
        'version',
        'xAvgCharWidth',
        'usWeightClass',
        'usWidthClass',
        'fsType',
        'ySubscriptXSize',
        'ySubscriptYSize',
        'ySubscriptXOffset',
        'ySubscriptYOffset',
        'ySuperscriptXSize',
        'ySuperscriptYSize',
        'ySuperscriptXOffset',
        'ySuperscriptYOffset',
        'yStrikeoutSize',
        'yStrikeoutPosition',
        'sFamilyClass',
        'panoseArray',
        'unicodeRanges',
        'achVendID',
        'fsSelection',
        'usFirstCharIndex',
        'usLastCharIndex',
        'sTypoAscender',
        'sTypoDescender',
        'sTypoLineGap',
        'usWinAscent',
        'usWinDescent',
        'codePageRanges',
        'sxHeight',
        'sCapHeight',
        'usDefaultChar',
        'usBreakChar',
        'usMaxContext',
        'usLowerOpticalPointSize',
        'usUpperOpticalPointSize')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new OS_2. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        """
        
        logger = kwArgs.get('logger', None)
        assert logger is not None  # we're only called via factory
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 100:
            logger.error(('E2127', (), "Insufficient bytes"))
            return None
        
        ver = w.unpack("H")
        
        if ver != 5:
            logger.error(('V0002', (), "Expected version 5"))
            return None
        
        v = [ver]
        okToReturn = True
        v.extend(w.unpack("H2h"))
        v.append(typeflags_v3.TypeFlags.fromvalidatedwalker(w, **kwArgs))
        
        if v[-1] is None:
            okToReturn = False
        
        v.extend(w.unpack("10hH"))
        v.append(panose.Panose_validated(w, **kwArgs))
        
        if v[-1] is None:
            okToReturn = False
        
        v.append(
          unicoderanges_v4.UnicodeRanges.fromvalidatedwalker(w, **kwArgs))
        
        if v[-1] is None:
            okToReturn = False
        
        v.append(w.unpack("4s"))
        v.append(selection_v4.Selection.fromvalidatedwalker(w, **kwArgs))
        
        if v[-1] is None:
            okToReturn = False
        
        v.extend(w.unpack("2H3h2H"))
        
        v.append(
          codepageranges_v2.CodePageRanges.fromvalidatedwalker(w, **kwArgs))
        
        if v[-1] is None:
            okToReturn = False
        
        v.extend(w.unpack("2h3H"))
        v.extend(n / 20 for n in w.unpack("2H"))
        return (cls(*v) if okToReturn else None)
    
    @classmethod
    def fromversion4(cls, v4Obj, **kwArgs):
        """
        Returns a new version 5 OS_2 object from the specified version 4
        object. There is one keyword argument:
        
            deferRecalculation  If True (the default), the fields will be
                                copied but no recalculation is done. The client
                                should do a recalculation, in this case. If
                                False, a recalculated() object will be
                                returned; in this case, the client should be
                                sure to pass in the needed keyword arguments
                                (usually editor and unicodeSpan, and perhaps
                                base1252 and threshold as well).
        """
        
        r = cls(
          xAvgCharWidth = v4Obj.xAvgCharWidth,
          usWeightClass = v4Obj.usWeightClass,
          usWidthClass = v4Obj.usWidthClass,
          fsType = v4Obj.fsType,
          ySubscriptXSize = v4Obj.ySubscriptXSize,
          ySubscriptYSize = v4Obj.ySubscriptYSize,
          ySubscriptXOffset = v4Obj.ySubscriptXOffset,
          ySubscriptYOffset = v4Obj.ySubscriptYOffset,
          ySuperscriptXSize = v4Obj.ySuperscriptXSize,
          ySuperscriptYSize = v4Obj.ySuperscriptYSize,
          ySuperscriptXOffset = v4Obj.ySuperscriptXOffset,
          ySuperscriptYOffset = v4Obj.ySuperscriptYOffset,
          yStrikeoutSize = v4Obj.yStrikeoutSize,
          yStrikeoutPosition = v4Obj.yStrikeoutPosition,
          sFamilyClass = v4Obj.sFamilyClass,
          panoseArray = v4Obj.panoseArray,
          unicodeRanges = v4Obj.unicodeRanges,
          achVendID = v4Obj.achVendID,
          fsSelection = v4Obj.fsSelection,
          usFirstCharIndex = v4Obj.usFirstCharIndex,
          usLastCharIndex = v4Obj.usLastCharIndex,
          sTypoAscender = v4Obj.sTypoAscender,
          sTypoDescender = v4Obj.sTypoDescender,
          sTypoLineGap = v4Obj.sTypoLineGap,
          usWinAscent = v4Obj.usWinAscent,
          usWinDescent = v4Obj.usWinDescent,
          codePageRanges = v4Obj.codePageRanges,
          sxHeight = v4Obj.sxHeight,
          sCapHeight = v4Obj.sCapHeight,
          usDefaultChar = v4Obj.usDefaultChar,
          usBreakChar = v4Obj.usBreakChar,
          usMaxContext = v4Obj.usMaxContext,
          usLowerOpticalPointSize = 0.0,
          usUpperOpticalPointSize = 3276.75)
        
        if kwArgs.get('deferRecalculation', True):
            return r
        
        return r.recalculated(**kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new OS_2 object from the specified walker.
        
        >>> fb = OS_2.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        ver = w.unpack("H")
        assert ver == 5  # caller must be using the right class
        v = [ver]
        v.extend(w.unpack("H2h"))
        v.append(typeflags_v3.TypeFlags.fromwalker(w, **kwArgs))
        v.extend(w.unpack("10hH"))
        v.append(panose.Panose(w, **kwArgs))
        v.append(unicoderanges_v4.UnicodeRanges.fromwalker(w, **kwArgs))
        v.append(w.unpack("4s"))
        v.append(selection_v4.Selection.fromwalker(w, **kwArgs))
        v.extend(w.unpack("2H3h2H"))
        v.append(codepageranges_v2.CodePageRanges.fromwalker(w, **kwArgs))
        v.extend(w.unpack("2h3H"))
        v.extend(n / 20 for n in w.unpack("2H"))
        return cls(*v)
    
    #
    # Public methods
    #
    
    def asVersion4(self, **kwArgs):
        """
        Returns a Version 4 OS_2 object from self.
        """
        
        return OS_2_v4.OS_2(
          xAvgCharWidth = self.xAvgCharWidth,
          usWeightClass = self.usWeightClass,
          usWidthClass = self.usWidthClass,
          fsType = self.fsType,
          ySubscriptXSize = self.ySubscriptXSize,
          ySubscriptYSize = self.ySubscriptYSize,
          ySubscriptXOffset = self.ySubscriptXOffset,
          ySubscriptYOffset = self.ySubscriptYOffset,
          ySuperscriptXSize = self.ySuperscriptXSize,
          ySuperscriptYSize = self.ySuperscriptYSize,
          ySuperscriptXOffset = self.ySuperscriptXOffset,
          ySuperscriptYOffset = self.ySuperscriptYOffset,
          yStrikeoutSize = self.yStrikeoutSize,
          yStrikeoutPosition = self.yStrikeoutPosition,
          sFamilyClass = self.sFamilyClass,
          panoseArray = self.panoseArray,
          unicodeRanges = self.unicodeRanges,
          achVendID = self.achVendID,
          fsSelection = self.fsSelection,
          usFirstCharIndex = self.usFirstCharIndex,
          usLastCharIndex = self.usLastCharIndex,
          sTypoAscender = self.sTypoAscender,
          sTypoDescender = self.sTypoDescender,
          sTypoLineGap = self.sTypoLineGap,
          usWinAscent = self.usWinAscent,
          usWinDescent = self.usWinDescent,
          codePageRanges = self.codePageRanges,
          sxHeight = self.sxHeight,
          sCapHeight = self.sCapHeight,
          usDefaultChar = self.usDefaultChar,
          usBreakChar = self.usBreakChar,
          usMaxContext = self.usMaxContext)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the OS_2 object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0005 0000 0190 0005  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0200 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 4D4F 4E4F 0000 |..........MONO..|
              40 | 0020 0020 0000 0000  0000 0000 0000 0000 |. . ............|
              50 | 0000 0000 0000 0000  0000 0000 0020 0000 |............. ..|
              60 | 0000 FFFF                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0005 0258 0258 0008  0004 0000 0000 0000 |...X.X..........|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 020E 0005 0000 0000  0000 0000 0003 0000 |................|
              30 | 0000 0000 0000 0000  0000 4D4F 4E4F 0010 |..........MONO..|
              40 | 0020 0020 0578 FCE0  0000 0000 0000 0000 |. . .x..........|
              50 | 0021 0000 0000 0000  0000 0000 0020 0004 |.!........... ..|
              60 | 005A 1973                                |.Z.s            |
        """
        
        w.add("Hh2H",
          self.version,
          self.xAvgCharWidth,
          self.usWeightClass,
          self.usWidthClass)
        
        self.fsType.buildBinary(w, **kwArgs)
        
        w.add("10hH",
          self.ySubscriptXSize,
          self.ySubscriptYSize,
          self.ySubscriptXOffset,
          self.ySubscriptYOffset,
          self.ySuperscriptXSize,
          self.ySuperscriptYSize,
          self.ySuperscriptXOffset,
          self.ySuperscriptYOffset,
          self.yStrikeoutSize,
          self.yStrikeoutPosition,
          self.sFamilyClass)
        
        self.panoseArray.buildBinary(w, **kwArgs)
        self.unicodeRanges.buildBinary(w, **kwArgs)
        w.add("4s", self.achVendID)
        self.fsSelection.buildBinary(w, **kwArgs)
        
        w.add("2H3h2H",
          self.usFirstCharIndex,
          self.usLastCharIndex,
          self.sTypoAscender,
          self.sTypoDescender,
          self.sTypoLineGap,
          self.usWinAscent,
          self.usWinDescent)
        
        self.codePageRanges.buildBinary(w, **kwArgs)
        
        w.add("2h5H",
          self.sxHeight,
          self.sCapHeight,
          self.usDefaultChar,
          self.usBreakChar,
          self.usMaxContext,
          round(self.usLowerOpticalPointSize * 20),
          round(self.usUpperOpticalPointSize * 20))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import pp
    
    _testingValues = (
        OS_2(),
        
        OS_2(
          xAvgCharWidth = 600,
          usWeightClass = 600,
          usWidthClass = 8,
          fsType = typeflags_v3.TypeFlags.fromnumber(4),
          
          panoseArray = panose_fam2_v2.Panose_fam2(
            serif = "Flared",
            proportion = "Extended"),
          
          unicodeRanges = unicoderanges_v4.UnicodeRanges(
            hasBasicLatin = True,
            hasLatin1Supplement = True),
          
          fsSelection = selection_v4.Selection(strikeout=True),
          sTypoAscender = 1400,
          sTypoDescender = -800,
          
          codePageRanges = codepageranges_v2.CodePageRanges(
            has1252 = True,
            has1255 = True),
          
          usMaxContext = 4,
          usLowerOpticalPointSize = 4.5,
          usUpperOpticalPointSize = 325.75))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
