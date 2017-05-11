#
# OS_2_v0.py
#
# Copyright © 2010-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for original Version 0 OS/2 tables, as defined by Microsoft. Note this
differs from Apple's definition of Version 0; see OS_2_v0_mac.py for that
format.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3 import utilities

from fontio3.OS_2 import (
  familyclass_v0,
  OS_2_v0_mac,
  panose,
  panose_fam2_v0,
  selection_v0,
  typeflags_v0,
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

_xAvgCharWidthFactors = {
  ord('a'): 64,
  ord('b'): 14,
  ord('c'): 27,
  ord('d'): 35,
  ord('e'): 100,
  ord('f'): 20,
  ord('g'): 14,
  ord('h'): 42,
  ord('i'): 63,
  ord('j'): 3,
  ord('k'): 6,
  ord('l'): 35,
  ord('m'): 20,
  ord('n'): 56,
  ord('o'): 56,
  ord('p'): 17,
  ord('q'): 4,
  ord('r'): 49,
  ord('s'): 56,
  ord('t'): 71,
  ord('u'): 31,
  ord('v'): 10,
  ord('w'): 18,
  ord('x'): 3,
  ord('y'): 18,
  ord('z'): 2,
  ord(' '): 166}

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

def _recalc_xAvgCharWidth(oldValue, **kwArgs):
    editor = kwArgs['editor']
    
    if editor is None:
        raise NoEditor()
    
    if not editor.reallyHas(b'hmtx'):
        raise NoHmtx()
    
    if not editor.reallyHas(b'cmap'):
        raise NoCmap()
    
    mtx = editor.hmtx
    uMap = editor.cmap.getUnicodeMap()
    cumulWeight = 0
    weighted = []
    
    for uniScalar, weight in _xAvgCharWidthFactors.items():
        if uniScalar in uMap:
            cumulWeight += weight
            weighted.append(mtx[uMap[uniScalar]].advance * weight)
    
    if cumulWeight:
        s = sum(weighted)
        newValue = int(s / cumulWeight)
        newValueRound = int(round(s / cumulWeight))
    
    else:
        s = sum(obj.advance for obj in mtx.values())
        newValue = int(s / len(mtx))
        newValueRound = int(round(s / len(mtx)))
    
    if kwArgs.get('forApple', False):
        newValue = newValueRound
    
    elif (newValue != newValueRound) and ('logger' in kwArgs):
        kwArgs['logger'].warning((
          'V0606',
          (newValue, newValueRound),
          "The recalculated xAvgCharWidth value (%d) is one less than the "
          "rounded value (%d). The smaller value will be used for "
          "compatibility with Windows, but consider using a newer version "
          "of the OS/2 table."))
    
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
    Objects representing OS/2 tables, version 0 (as defined by Microsoft).
    
    >>> _testingValues[1].pprint()
    OS/2 Version: 0 (Windows)
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
      Proportion: Expanded
      Contrast: Any
      Stroke Variation: Any
      Arm Style: Any
      Letterform: Any
      Midline: Any
      x-Height: Any
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
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "OS/2 Version",
            attr_pprintfunc = (lambda p,n,label,**k: p.simple("0 (Windows)", label))),
        
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
            attr_initfunc = typeflags_v0.TypeFlags,
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
            attr_pprintfunc = (lambda p,n,label,**k: p.simple(familyclass_v0.labels[n], label=label)),
            attr_validatefunc = _validate_sFamilyClass),
        
        panoseArray = dict(
            attr_followsprotocol = True,
            attr_initfunc = panose_fam2_v0.Panose_fam2,
            attr_label = "PANOSE specification"),
        
        achVendID = dict(
            attr_initfunc = (lambda: b'MONO'),
            attr_label = "Font vendor",
            attr_pprintfunc = (lambda p,n,label,**k: p.simple(vendors_v0.labels[n], label=label))),
        
        fsSelection = dict(
            attr_followsprotocol = True,
            attr_initfunc = selection_v0.Selection,
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
            attr_validatefunc = _validate_usWinDescent))
    
    attrSorted = (
        'version', 'xAvgCharWidth', 'usWeightClass', 'usWidthClass', 'fsType',
        'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset',
        'ySubscriptYOffset', 'ySuperscriptXSize', 'ySuperscriptYSize',
        'ySuperscriptXOffset', 'ySuperscriptYOffset', 'yStrikeoutSize',
        'yStrikeoutPosition', 'sFamilyClass', 'panoseArray', 'achVendID',
        'fsSelection', 'usFirstCharIndex', 'usLastCharIndex', 'sTypoAscender',
        'sTypoDescender', 'sTypoLineGap', 'usWinAscent', 'usWinDescent')
    
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
        
        if w.length() < 78:
            logger.error(('E2127', (), "Insufficient bytes"))
            return None
        
        ver = w.unpack("H")
        
        if ver != 0:
            logger.error(('V0002', (), "Expected version 0"))
            return None
        
        v = [ver]
        okToReturn = True
        v.extend(w.unpack("H2h"))
        obj = typeflags_v0.TypeFlags.fromvalidatedwalker(w, **kwArgs)
        
        if obj is None:
            okToReturn = False
        
        v.append(obj)
        v.extend(w.unpack("10hH"))
        obj = panose.Panose_validated(w, os2panver=0, **kwArgs)
        
        if obj is None:
            okToReturn = False
        
        v.append(obj)
        v.append(w.unpack("16x4s"))
        obj = selection_v0.Selection.fromvalidatedwalker(w, **kwArgs)
        
        if obj is None:
            okToReturn = False
        
        v.append(obj)
        v.extend(w.unpack("2H3h2H"))
        return (cls(*v) if okToReturn else None)
    
    @classmethod
    def fromversion0mac(cls, v0MacObj, **kwArgs):
        """
        Returns a new OS_2 object from the specified version 0 (Mac) object.
        """
        
        # no recalculation is needed for this conversion
        return cls(
          xAvgCharWidth = v0MacObj.xAvgCharWidth,
          usWeightClass = v0MacObj.usWeightClass,
          usWidthClass = v0MacObj.usWidthClass,
          fsType = v0MacObj.fsType,
          ySubscriptXSize = v0MacObj.ySubscriptXSize,
          ySubscriptYSize = v0MacObj.ySubscriptYSize,
          ySubscriptXOffset = v0MacObj.ySubscriptXOffset,
          ySubscriptYOffset = v0MacObj.ySubscriptYOffset,
          ySuperscriptXSize = v0MacObj.ySuperscriptXSize,
          ySuperscriptYSize = v0MacObj.ySuperscriptYSize,
          ySuperscriptXOffset = v0MacObj.ySuperscriptXOffset,
          ySuperscriptYOffset = v0MacObj.ySuperscriptYOffset,
          yStrikeoutSize = v0MacObj.yStrikeoutSize,
          yStrikeoutPosition = v0MacObj.yStrikeoutPosition,
          sFamilyClass = v0MacObj.sFamilyClass,
          panoseArray = v0MacObj.panoseArray,
          achVendID = v0MacObj.achVendID,
          fsSelection = v0MacObj.fsSelection,
          usFirstCharIndex = v0MacObj.usFirstCharIndex,
          usLastCharIndex = v0MacObj.usLastCharIndex)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new OS_2 object from the specified walker.
        
        >>> _testingValues[0] == OS_2.frombytes(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == OS_2.frombytes(_testingValues[1].binaryString())
        True
        """
        
        ver = w.unpack("H")
        assert ver == 0  # caller must be using the right class
        v = [ver]
        v.extend(w.unpack("H2h"))
        v.append(typeflags_v0.TypeFlags.fromwalker(w, **kwArgs))
        v.extend(w.unpack("10hH"))
        v.append(panose.Panose(w, os2panver=0, **kwArgs))
        # 4 longs of zeroes ignored for unicode ranges, not used in v1
        w.skip(16)
        v.append(w.unpack("4s"))
        v.append(selection_v0.Selection.fromwalker(w, **kwArgs))
        v.extend(w.unpack("2H3h2H"))
        return cls(*v)
    
    #
    # Public methods
    #
    
    def asVersion0Mac(self, **kwArgs):
        """
        Returns a Version 0 (Mac) OS_2 object from self.
        """
        
        return OS_2_v0_mac.OS_2(
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
          achVendID = self.achVendID,
          fsSelection = self.fsSelection,
          usFirstCharIndex = self.usFirstCharIndex,
          usLastCharIndex = self.usLastCharIndex)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the OS_2 object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000 0190 0005  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0200 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 4D4F 4E4F 0000 |..........MONO..|
              40 | 0020 0020 0000 0000  0000 0000 0000      |. . ..........  |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0258 0258 0008  0004 0000 0000 0000 |...X.X..........|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 020E 0005 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 4D4F 4E4F 0010 |..........MONO..|
              40 | 0020 0020 0578 FCE0  0000 0000 0000      |. . .x........  |
        """
        
        w.add("Hh2H",
          self.version, self.xAvgCharWidth, self.usWeightClass,
          self.usWidthClass)
        
        self.fsType.buildBinary(w, **kwArgs)
        
        w.add("10hH",
          self.ySubscriptXSize, self.ySubscriptYSize, self.ySubscriptXOffset,
          self.ySubscriptYOffset, self.ySuperscriptXSize,
          self.ySuperscriptYSize, self.ySuperscriptXOffset,
          self.ySuperscriptYOffset, self.yStrikeoutSize,
          self.yStrikeoutPosition, self.sFamilyClass)
        
        self.panoseArray.buildBinary(w, **kwArgs)
        w.add("16x4s", self.achVendID)
        self.fsSelection.buildBinary(w, **kwArgs)
        
        w.add("2H3h2H",
          self.usFirstCharIndex, self.usLastCharIndex, self.sTypoAscender,
          self.sTypoDescender, self.sTypoLineGap, self.usWinAscent,
          self.usWinDescent)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import pp
    
    _testingValues = (
        OS_2(),
        
        OS_2(
          xAvgCharWidth = 600,
          usWeightClass = 600,
          usWidthClass = 8,
          fsType = typeflags_v0.TypeFlags.fromnumber(4),
          panoseArray = panose_fam2_v0.Panose_fam2(serif="Flared", proportion="Expanded"),
          fsSelection = selection_v0.Selection(strikeout=True),
          sTypoAscender = 1400,
          sTypoDescender = -800))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
