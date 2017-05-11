#
# head.py
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the TrueType 'head' table.
"""

# System imports
import datetime
import logging
import time

# Other imports
from fontio3 import utilities

from fontio3.fontdata import simplemeta
from fontio3.head import flags, macstyle

# -----------------------------------------------------------------------------

#
# Constants
#

fontDirectionHintStrings = {
    0: "Fully mixed-directional glyphs",
    1: "Only strongly left-to-right glyphs",
    2: "Strongly left-to-right and neutral glyphs",
   -1: "Only strongly right-to-left glyphs",
   -2: "Strongly right-to-left and neutral glyphs"}

EPOCH = datetime.datetime(1904, 1, 1, 0, 0, 0, 0, datetime.timezone.utc)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _getTime():
    """
    Returns an integer with the number of seconds since 1/1/1904. Note that
    integer overflow won't likely be a problem, because by 2038 (when the clock
    turns over) we'll likely be using Python 3.0 or later, and int in those
    implementations is arbitrary precision.
    
    As per the newly amended 'head' definition in the Open Font Format, this
    is now always done as UTC times.
    """
    
    timeDelta = datetime.datetime.now(datetime.timezone.utc) - EPOCH
    return int(timeDelta.total_seconds())

def _merge_glyphDataFormat(selfGDF, otherGDF, **kwArgs):
    replace = (otherGDF == 0x9655 or (otherGDF == 0x9654 and selfGDF == 0x9655))

    if (selfGDF != otherGDF) and replace:
        return True, otherGDF
    
    return False, selfGDF

def _merge_unitsPerEm(selfUPEM, otherUPEM, **kwArgs):
    if selfUPEM != otherUPEM:
        raise ValueError("Merging 'head' tables requires same unitsPerEm!")
    
    return (False, selfUPEM)

def _num_secs_OK(timeInSeconds):
    """
    TrueType modified and created dates are 64-bit signed integers representing
    the number of seconds since midnight, January 1, 1904. This allows a
    massive range of billions of years into the future or past. Python's date
    range is somewhat more limited, so we have this check so we don't overflow.
    This still allows a very reasonable range of dates from midnight January 1,
    1 to 23:59:59.999999 December 31, 9999.
    
        datetime(1904,1,1) + timedelta(seconds=255485145600) overflows date max
        datetime(1904,1,1) + timedelta(seconds=-60052752001) overflows date min
    """

    return (-60052752001 < timeInSeconds < 255485145600)

def _pprint_time(p, timeInSeconds, label, **kwArgs):
    if _num_secs_OK(timeInSeconds):
        p.simple(
          str(EPOCH + datetime.timedelta(seconds=timeInSeconds)),
          label = label)
    
    else:
        p.simple("0x%x" % (timeInSeconds,), label=label)

def _recalc(obj, **kwArgs):
    editor = kwArgs['editor']
    r = obj.__deepcopy__()
    
    if editor is not None:
        if editor.reallyHas(b'glyf'):
            glyphTbl = editor.glyf
        elif editor.reallyHas(b'CFF '):
            glyphTbl = editor['CFF ']
        else:
            glyphTbl = None
        
        if glyphTbl is not None:
            # Force recalc instead of using stored bounds (which may be incorrect).
            r.xMin = 32767
            r.xMax = -32767
            r.yMin = 32767
            r.yMax = -32767
            for gl in list(glyphTbl.values()):
                if gl:
                    glr = gl.recalculated(editor=editor)
                    if glr.bounds:
                        r.xMin = min(r.xMin, glr.bounds.xMin)
                        r.xMax = max(r.xMax, glr.bounds.xMax)
                        r.yMin = min(r.yMin, glr.bounds.yMin)
                        r.yMax = max(r.yMax, glr.bounds.yMax)
    
    return r != obj, r

def _validate(tbl, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'head' table because the editor is "
          "missing or empty."))
        
        return False
    
    tblExpected = tbl.recalculated(**kwArgs)
    r = True

    if not (editor.reallyHas(b'glyf') or editor.reallyHas(b'CFF ')):
        logger.warning((
          'V0298',
          (),
          "Font-wide bounding box not tested because "
          "neither a 'glyf' nor a 'CFF ' table is present"))
    
    else:
        for attr in ('xMin', 'xMax', 'yMin', 'yMax'):
            actual = getattr(tbl, attr)
            calculated = getattr(tblExpected, attr)
            
            if abs(calculated) > abs(actual):
                logger.error((
                  'E1326',
                  (attr, calculated, actual),
                  "The calculated value for %s (%d) exceeds the "
                  "actual value %d"))
                
                r = False
            
            elif abs(calculated) < abs(actual):
                logger.warning((
                  'Vxxxx',
                  (attr, calculated, actual),
                  "The calculated value for %s (%d) does not match the "
                  "actual value %d"))
                
                r = False
            
            else:
                logger.info((
                  'P1326',
                  (attr,),
                  "The %s value matches the calculated value"))
    
    if tbl.xMin > tbl.xMax:
        logger.error((
          'E1327',
          (tbl.xMin, tbl.xMax),
          "xMin (%d) is greater than xMax (%d)"))
        
        r = False
    
    if tbl.yMin > tbl.yMax:
        logger.error((
          'E1330',
          (tbl.yMin, tbl.yMax),
          "yMin (%d) is greater than yMax (%d)"))
        
        r = False

    mtbl = [b'hdmx', b'LTSH']
    
    if tbl.flags.opticalAdvanceViaHints:
        msgP = ('P1305', 'P1306')
        msgW = ('W1302', 'W1303')
        
        for i, t in enumerate(mtbl):
            if t in editor:
                logger.info((
                  msgP[i],
                  (t,),
                  "Non-linear scaling flag (bit 4) is set, "
                  "and %s table is present"))
            
            else:
                logger.warning((
                  msgW[i],
                  (t,),
                  "Non-linear scaling flag (bit 4) is set, "
                  "but %s table is not present"))
    
    else:
        msgP = ('P1303', 'P1304')
        msgE = ('E1303', 'E1304')
        
        for i, t in enumerate(mtbl):
            if t in editor:
                logger.error((
                  msgE[i],
                  (t,),
                  "Non-linear scaling flag (bit 4) is clear, "
                  "but %s table is present"))
                
                r = False
            
            else:
                logger.info((
                  msgP[i],
                  (t,),
                  "Non-linear scaling flag (bit 4) is clear, "
                  "and %s table is not present"))


    macStyle = tbl.macStyle
    
    if editor.reallyHas(b'name'):
        # gather up some names that we expect to be present
        subfamilyName = ""
        versionName = ""
        
        for idp, ide, idl in ((1, 0, 0), (3, 1, 1033), (3, 0, 1033)):
            if not subfamilyName and ((idp, ide, idl, 2) in editor.name):
                subfamilyName = editor.name[(idp, ide, idl, 2)]
            
            if not versionName and ((idp, ide, idl, 5) in editor.name):
                versionName = editor.name[(idp, ide, idl, 5)]
            
            if subfamilyName and versionName:
                break

        # macStyle.bold vs. subfamily name
        isOK = True
        sfd = editor.name.subFamilyNameToBits()

        if sfd['bold']:
            isOK = macStyle.bold
        else:
            isOK = not(macStyle.bold)

        if isOK:
            logger.info((
              'P1316',
              (),
              "The macStyle bold bit is consistent with the name "
              "table's subfamily string."))
        
        else:
            logger.error((
              'E1311',
              (macStyle.bold, subfamilyName),
              "The macStyle bold bit (%s) is not consistent with "
              "the name table's subfamily string '%s'."))

        # macStyle.italic vs subfamily name
        isOK = True
        if sfd['italic']:
            isOK = macStyle.italic
        else:
            isOK = not(macStyle.italic)
        
        if isOK:
            logger.info((
              'P1320',
              (),
              "The macStyle italic bit is consistent with the name "
              "table's subfamily string."))
        else:
            logger.error((
              'E1314',
              (macStyle.italic, subfamilyName),
              "The macStyle italic bit (%s) is not consistent with "
              "the name table's subfamily string '%s'."))


        # fontRevision <---> name.version
        fontRevAsString = ("%5.2f" % (tbl.fontRevision/65536,)).strip()
        expectedVersionString = "Version %s" % fontRevAsString
        
        if expectedVersionString not in versionName:
            logger.warning((
              'W1314',
              (fontRevAsString, versionName),
              "fontRevision (%s) is not consistent with the "
              "name table version string '%s'"))
        
        else:
            logger.info((
              'P1330',
              (),
              "fontRevision is consistent with the name table version string"))

    if editor.reallyHas(b'OS/2'):
        os2 = editor[b'OS/2']
        
        if os2 is None:
            logger.warning((
              'W0050',
              (),
              "Cannot perform head.macStyle-to-OS/2.fsSelection test "
              "due to an error in the OS/2 table"))
            
            r = False

        else:
            os2fssel = os2.fsSelection
            
            for attr in ('bold', 'italic'):
                vh = getattr(macStyle, attr)
                vo = getattr(os2fssel, attr)
                
                if vh == vo:
                    logger.info((
                      'P1314',
                      (attr, attr),
                      "The macstyle %s bit matches the "
                      "OS/2 fsSelection %s bit"))
                
                else:
                    logger.error((
                      'E1312',
                      (attr, vh, attr, vo),
                      "The macStyle %s bit is %s but the "
                      "OS/2 fsSelection %s bit is %s"))
                    
                    r = False

    elif not kwArgs.get('forApple', False):
        logger.warning((
          'W0050',
          (),
          "Cannot perform head.macStyle-to-OS/2.fsSelection test "
          "because the OS/2 table is missing"))

    if editor.reallyHas(b'post') and editor.post.header:
        if bool(editor.post.header.italicAngle) != tbl.macStyle.italic:
            logger.error((
              'E1316',
              (tbl.macStyle.italic, editor.post.header.italicAngle),
              "The macStyle italic bit is %s but post.italicAngle is %5.1f"))
            
            r = False
        
        else:
            logger.info((
              'P1319',
              (),
              "The macStyle italic bit is consistent with the "
              "post table italic angle"))
                
    if tbl.modified <= tbl.created:
        logger.warning((
          'V0244',
          (),
          "The modified date is earlier than the created date"))

    return r

def _validate_created(value, **kwArgs):
    delKeys = {'code_invalid', 'code_unlikely', 'code_valid'}
    
    for delKey in delKeys:
        kwArgs.pop(delKey, None)
    
    return _validate_date(
      value,
      "created",
      code_invalid = 'E1300',
      code_unlikely = 'W1301',
      code_valid = 'P1300',
      **kwArgs)

def _validate_date(value, label, **kwArgs):
    logger = kwArgs['logger']

    if (value == 0) or not (_num_secs_OK(value)):
        logger.error((
          kwArgs['code_invalid'],
          (label, value),
          "The %s value '0x%x' is not valid"))
        
        if (value != 0) and (value % 0x100000000 == 0):
            logger.warning((
              'V0301',
              (label,),
              "The %s value may be in the wrong Endian order"))
        
        return False
    
    pyDate = EPOCH + datetime.timedelta(seconds=value)

    if (pyDate.year < 1985) or (value > _getTime()):
        logger.warning((
          kwArgs['code_unlikely'],
          (label, pyDate),
          "The %s date/time '%s' is an unlikely value"))
    
    else:
        logger.info((
          kwArgs['code_valid'],
          (label, pyDate),
          "The %s date/time '%s' appears to be valid"))

    return True

def _validate_flags(obj, **kwArgs):
    logger = kwArgs['logger']

    if not obj.sidebearingAtX0:
        logger.warning((
          'V0934',
          (),
          "Bit 1 (left sidebearing point at x=0) is not set"))
    
    return True

def _validate_fontDirectionHint(value, **kwArgs):
    logger = kwArgs['logger']
    
    if not (-2 <= value <= 2):
        logger.error((
          'E1306',
          (value,),
          "The fontDirectionHint value (%d) is not in the range -2..2"))
        
        return False
    
    logger.info((
      'P1308',
      (value,),
      "The fontDirectionHint value (%d) is in the range -2..2"))

    if (not kwArgs.get('forApple', False)) and (value != 2):
        
        # For MS purposes, other values are deprecated; see
        # http://www.microsoft.com/typography/otspec/head.htm
        # For Apple purposes, other values are OK
        
        logger.warning((
          'V0245',
          (value,),
          "The fontDirectionHint value (%d) is not 2"))
    
    return True

def _validate_glyphDataFormat(value, **kwArgs):
    logger = kwArgs['logger']
    
    # This only covers TT where the value must == 0; is there any other way to
    # detect a (legitimate) stik font besides glyphDataFormat? -- Yes, by the
    # presence of at least one bit 7 on in a simple glyph's flags -- this
    # indicates an outline glyph in an otherwise stik font. However, if the
    # stik font contains no outline glyphs at all, then the glyphDataFormat is
    # the only way to tell.
    
    if value:
        logger.error((
          'E1307',
          (value,),
          "The glyphDataFormat (%d) is not 0"))
        
        return False
    
    logger.info(('P1309', (), "The glyphDataFormat is 0"))
    return True

def _validate_indexToLocFormat(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate the indexToLocFormat value because "
          "the editor is missing or empty."))
        
        return False

    # value ignored in CFF, so check that first (AND return if so):
    if b'CFF ' in editor:
        logger.info((
          'P1310',
          (value,),
          "The indexToLocFormat value (%d) is ignored in a CFF font"))
        
        return True

    # must be 0 or 1 for TrueType...
    if not editor.reallyHas(b'maxp'):
        logger.error((
          'V0553',
          (),
          "Unable to validate the indexToLocFormat value because "
          "the 'maxp' table is missing or empty."))
        
        return False
    
    glyphcount = editor.maxp.numGlyphs + 1
    
    if value:
        expLocaInfo = (glyphcount * 4, "long")
    else:
        expLocaInfo = (glyphcount * 2, "short")
    
    if value not in {0, 1}:
        logger.error((
          'E1309',
          (value,),
          "The indexToLocFormat value (%d) is not 0 or 1"))
        
        return False
    
    logger.info((
        'P1312',
        (value, expLocaInfo[1]),
        "The indexToLocFormat value is %d (%s offsets)"))

    # and 'loca' length must correspond to the value
    if not editor.reallyHas(b'loca'):
        logger.error((
          'V0553',
          (),
          "Unable to validate the indexToLocFormat value because "
          "the 'loca' table is missing."))
        
        return False
    
    rawLoca = editor.getRawTable(b'loca')
    
    if (rawLoca is not None) and (expLocaInfo[0] != len(rawLoca)):
        logger.error((
          'E1308',
          (value,),
          "The indexToLocFormat value (%d) is not consistent "
          "with loca length"))
        
        return False
    
    locaTbl = editor.loca
    if value == 1 and not locaTbl.needsLongOffsets():
        logger.warning((
          'V1067',
          (),
          "The indexToLoc format value indicates long offsets, but short "
          "offsets could be used to reduce the size of the 'loca' table."))
    
    logger.info((
        'P1311',
        (value,),
        "The indexToLocFormat value (%d) is consistent with loca length"))

    return True

def _validate_lowestRecPPEM(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']

    if value == 0:
        logger.error((
          'E1310',
          (),
          "The lowestRecPPEM value is zero"))
        
        return False
    
    if value <= 6:
        # From MS Font Validator for TrueType fonts. Skipped for CFF.
        if not b'CFF ' in editor:
            logger.warning((
              'W1305',
              (value,),
              "The lowestRecPPEM value (%d) may be unreasonably small"))
    
    elif value >= 36:
        # From MS Font Validator
        logger.warning((
          'W1304',
          (value,),
          "The lowestRecPPEM value (%d) may be unreasonably large"))
    
    else:
        logger.info((
          'P1313',
          (value,),
          "The lowestRecPPEM value (%d) is in a reasonable range"))
    
    return True

def _validate_magicNumber(value, **kwArgs):
    logger = kwArgs['logger']
    
    if value == 0x5f0f3cf5:
        logger.info((
          'P1321',
          (),
          "The magic number is 0x5f0f3cf5"))
        
        return True
    
    logger.error((
      'E1319',
      (value,),
      "The magic number (0x%08x) is not 0x5f0f3cf5"))
    
    return False

def _validate_modified(value, **kwArgs):
    delKeys = {'code_invalid', 'code_unlikely', 'code_valid'}
    
    for delKey in delKeys:
        kwArgs.pop(delKey, None)
    
    return _validate_date(
      value,
      "modified",
      code_invalid = 'E1320',
      code_unlikely = 'W1311',
      code_valid = 'P1310',
      **kwArgs)

def _validate_unitsPerEm(value, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    LTEMax = (value <= 16384)
    GTEWinMin = (value >= 16)
    GTEAplMin = (value >= 64)
    PowerOfTwo = ( (value != 0) and not (value & (value - 1)) )
    Upem1000 = (value == 1000)
    IsCFF = b'CFF ' in editor

    if not LTEMax:
        logger.error((
          'E1323',
          (value,),
          "The unitsPerEm value (%d) is greater than 16384"))
        
        return False

    if not GTEWinMin:
        logger.error((
          'E1324',
          (value,),
          "The unitsPerEm value (%d) is less than the Windows minimum of 16"))
        
        return False
    
    if not GTEAplMin:
        logger.warning((
          'W1312',
          (value,),
          "The unitsPerEm value (%d) is less than the Apple minimum of 64"))
    
    if IsCFF:
        if not Upem1000:
            logger.warning((
              'W1313',
              (value,),
              "The unitsPerEm value (%d) is not 1000."))
    else:
        if not PowerOfTwo:
            logger.warning((
              'W1313',
              (value,),
              "The unitsPerEm value (%d) is not a power of two"))
    
    if GTEAplMin and PowerOfTwo:
        logger.info((
          'P1325',
          (value,),
          "The unitsPerEm value (%d) is a power of two in "
          "the range 64..16384"))
    
    return True

def _validate_version(value, **kwArgs):
    logger = kwArgs['logger']
    
    if value == 0x00010000:
        logger.info((
          'P1324',
          (),
          "The table version number is 0x00010000"))
        
        return True
    
    logger.error((
      'E1322',
      (value,),
      "The table version (0x%08x) is not 0x00010000"))
    
    return False

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Head(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'head' tables.
    
    >>> _testingValues[1].pprint()
    Table version: 1.0
    Font revision: 0
    Flags:
      Baseline is at y=0: False
      Left sidebearing is at x=0: False
      Glyph hints depend on PPEM: True
      PPEM forced to integral value: False
      Advance widths depend on PPEM: True
      Vertical baseline is at x=0: True
      Font requires layout for linguistically correct layout: False
      Font has default layout features: False
      Font requires reordering: True
      Font does rearrangement: False
      Font uses MicroType Lossless compression: False
      Converted font requiring compatible metrics: True
      Font optimized for ClearType: False
    Font Units-per-em: 2048
    Font created: 1954-03-27 14:30:00+00:00
    Font modified: 1954-03-27 14:30:00+00:00
    Font bounding box xMin: -50
    Font bounding box yMin: -290
    Font bounding box xMax: 2000
    Font bounding box yMax: 1800
    Mac style: Bold Italic
    Lowest recommended PPEM: 9
    Font direction: Fully mixed-directional glyphs
    Format of 'loca' table: 0
    Glyph data format: 0x0000
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 0x00010000),
            attr_label = "Table version",
            attr_validatefunc = _validate_version,
            attr_pprintfunc = (
              lambda p, i, label, **k:
              p.simple(i / 65536.0, label=label))),
        
        fontRevision = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Font revision"),
        
        checkSumAdjustment = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Checksum adjustment",
            attr_pprintfunc = (lambda p,i,label,**k: None)),  # doesn't pprint
        
        magicNumber = dict(
            attr_initfunc = (lambda: 0x5F0F3CF5),
            attr_label = "TrueType magic number",
            attr_validatefunc = _validate_magicNumber,
            attr_pprintfunc = (lambda p,i,label,**k: None)),  # doesn't pprint
        
        flags = dict(
            attr_followsprotocol = True,
            attr_initfunc = flags.Flags,
            attr_label = "Flags",
            attr_validatefunc = _validate_flags),
        
        unitsPerEm = dict(
            attr_initfunc = (lambda: 2048),
            attr_inputcheckfunc = (lambda x: 16 <= x <= 16384),
            attr_label = "Font Units-per-em",
            attr_mergefunc = _merge_unitsPerEm,
            attr_validatefunc = _validate_unitsPerEm),
        
        created = dict(
            attr_initfunc = _getTime,
            attr_label = "Font created",
            attr_pprintfunc = _pprint_time,
            attr_validatefunc = _validate_created),
        
        modified = dict(
            attr_initfunc = _getTime,
            attr_label = "Font modified",
            attr_pprintfunc = _pprint_time,
            attr_validatefunc = _validate_modified,
            attr_recalculatefunc = (lambda x, **k: (True, _getTime()))),
        
        xMin = dict(
            attr_initfunc = (lambda: 30000),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Font bounding box xMin",
            attr_mergefunc = (lambda a, b, **k: (b < a, min(a, b))),
            attr_representsx = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'yMin'),
        
        yMin = dict(
            attr_initfunc = (lambda: 30000),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Font bounding box yMin",
            attr_mergefunc = (lambda a, b, **k: (b < a, min(a, b))),
            attr_representsy = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'xMin'),
        
        xMax = dict(
            attr_initfunc = (lambda: -30000),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Font bounding box xMax",
            attr_mergefunc = (lambda a, b, **k: (b > a, max(a, b))),
            attr_representsx = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'yMax'),
        
        yMax = dict(
            attr_initfunc = (lambda: -30000),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Font bounding box yMax",
            attr_mergefunc = (lambda a, b, **k: (b > a, max(a, b))),
            attr_representsy = True,
            attr_scaledirect = True,
            attr_transformcounterpart = 'xMax'),
        
        macStyle = dict(
            attr_followsprotocol = True,
            attr_initfunc = macstyle.MacStyle,
            attr_label = "Mac style",
            attr_pprintfunc = (
              lambda p, n, label, **k:
              p.simple(str(n), label=label))),
        
        lowestRecPPEM = dict(
            attr_initfunc = (lambda: 9),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Lowest recommended PPEM",
            attr_validatefunc = _validate_lowestRecPPEM),
        
        fontDirectionHint = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = (lambda x: -2 <= x <= 2),
            attr_label = "Font direction",
            attr_validatefunc = _validate_fontDirectionHint,
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(fontDirectionHintStrings[x], label=label))),
        
        indexToLocFormat = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Format of 'loca' table",
            attr_validatefunc = _validate_indexToLocFormat),
        
        glyphDataFormat = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Glyph data format",
            attr_mergefunc = _merge_glyphDataFormat,
            attr_validatefunc = _validate_glyphDataFormat,
            attr_pprintfunc = (
              lambda p, i, label, **k:
              p.simple("0x%04X" % (i,), label=label))))
    
    attrSorted = (
      'version',
      'fontRevision',
      'checkSumAdjustment',
      'magicNumber',
      'flags',
      'unitsPerEm',
      'created',
      'modified',
      'xMin',
      'yMin',
      'xMax',
      'yMax',
      'macStyle',
      'lowestRecPPEM',
      'fontDirectionHint',
      'indexToLocFormat',
      'glyphDataFormat')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Head object to the specified LinkedWriter.
        The supported keyword arguments (all optional) are:
        
            stakeValue      The stake representing the start of this Head
                            record.
            
            useIndexMap     If not None, the checkSumAdjustment will be added
                            as an unresolved index value to be filled in later
                            (tag1 = the string value of this useIndexMap
                            argument, tag2 = "head").
        
        >>> h = Head()
        >>> h.created = h.modified = 0xC60416DC
        >>> utilities.hexdump(h.binaryString())
               0 | 0001 0000 0000 0000  0000 0000 5F0F 3CF5 |............_.<.|
              10 | 0000 0800 0000 0000  C604 16DC 0000 0000 |................|
              20 | C604 16DC 7530 7530  8AD0 8AD0 0000 0009 |....u0u0........|
              30 | 0000 0000 0000                           |......          |
        
        >>> utilities.hexdump(h.binaryString(useIndexMap="headAdj"))
               0 | 0001 0000 0000 0000  0000 0000 5F0F 3CF5 |............_.<.|
              10 | 0000 0800 0000 0000  C604 16DC 0000 0000 |................|
              20 | C604 16DC 7530 7530  8AD0 8AD0 0000 0009 |....u0u0........|
              30 | 0000 0000 0000                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2L", self.version, self.fontRevision)
        sUIM = kwArgs.get('useIndexMap', None)
        
        if sUIM is True:
            sUIM = "headAdj"  # for backwards compatibility
        
        if sUIM is not None:
            w.addUnresolvedIndex("L", sUIM, 'head')
            w.addIndexMap(sUIM, {'head': 0})  # replaced in Editor.buildBinary()
        
        else:
            w.add("L", self.checkSumAdjustment)
        
        w.add("L", self.magicNumber)
        
        self.flags.buildBinary(w, **kwArgs)
        
        w.add("H2Q4h",
          self.unitsPerEm,
          int(self.created),
          int(self.modified),
          self.xMin,
          self.yMin,
          self.xMax,
          self.yMax)
        
        self.macStyle.buildBinary(w, **kwArgs)
        
        w.add("Hh2H",
          self.lowestRecPPEM,
          self.fontDirectionHint,
          self.indexToLocFormat,
          self.glyphDataFormat)
    
    @classmethod
    def fromeditor(cls, editor):
        """
        Returns a new Head instance using certain fields from the
        specified Editor. Use this class method instead of the old minimalDict
        function.
        """
        
        r = cls()
        baseHead = editor.head
        r.fontRevision = baseHead.fontRevision
        r.macStyle = baseHead.macStyle
        r.glyphDataFormat = baseHead.glyphDataFormat
        r.unitsPerEm = baseHead.unitsPerEm
        b = editor.glyf[0].bounds
        r.xMin = b.xMin
        r.yMin = b.yMin
        r.xMax = b.xMax
        r.yMax = b.yMax
        r.flags = baseHead.flags
        r.lowestRecPPEM = baseHead.lowestRecPPEM
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Head. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> obj = Head.fromvalidatedbytes(s, logger=logger)
        test.head - DEBUG - Walker has 54 remaining bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('head')
        else:
            logger = logger.getChild('head')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() != 54:
            logger.error(('V0198', (), "Table is not exactly 54 bytes."))
            return None
        
        t1 = w.unpack("4L")
        fl = flags.Flags.fromvalidatedwalker(w, logger=logger, **kwArgs)
        t2 = w.unpack("H2Q4h")
        ms = macstyle.MacStyle.fromvalidatedwalker(w, logger=logger, **kwArgs)
        t3 = w.unpack("Hh2H")
        return cls(*(t1 + (fl,) + t2 + (ms,) + t3))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Head instance initialized via the specified walker.
        
        >>> h = Head()
        >>> h == Head.frombytes(h.binaryString())
        True
        """
        
        t1 = w.unpack("4L")
        fl = flags.Flags.fromwalker(w, **kwArgs)
        t2 = w.unpack("H2Q4h")
        ms = macstyle.MacStyle.fromwalker(w, **kwArgs)
        t3 = w.unpack("Hh2H")
        return cls(*(t1 + (fl,) + t2 + (ms,) + t3))
    
    def isAAFont(self):
        """
        Returns True if the font is stik and has AA hints.
        """
        
        return self.glyphDataFormat == 0x9655
    
    def isStrokeFont(self):
        """
        Returns True if the glyphDataFormat indicates this is a stik font.
        """
        
        return self.glyphDataFormat == 0x9654
    
    def updateBBox(self, glyfTable):
        """
        Updates the bounding box based on the specified glyf table.
        
        This method should be called when new glyphs are added or existing
        glyphs are changed.
        """
        
        ub = glyfTable.unionBounds()
        self.xMin = ub.xMin
        self.yMin = ub.yMin
        self.xMax = ub.xMax
        self.yMax = ub.yMax
    
    def updateModifiedToNow(self):
        """
        Updates the modified date to the present moment.
        """
        
        self.modified = _getTime()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Head(),
        
        Head(
          flags = flags._testingValues[2],
          created = 0x5E7E0DE8,
          modified = 0x5E7E0DE8,
          xMin = -50,
          yMin = -290,
          xMax = 2000,
          yMax = 1800,
          macStyle = macstyle._testingValues[1]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
