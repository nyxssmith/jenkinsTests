#
# codepageranges_v2.py
#
# Copyright © 2004-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for representations of MS code page data for OS/2 tables, versions 2
through the present.
"""

# System imports
import itertools
import unicodedata

# Other imports
from fontio3 import utilitiesbackend
from fontio3.fontdata import maskmeta
from fontio3.OS_2 import codepageranges_v1
from fontio3.utilities import span2

# -----------------------------------------------------------------------------

#
# Private constants
#

_bitData = {  # bit number -> (python encoding string, is16Bit)
  0: ('cp1252', False, 'has1252'),
  1: ('cp1250', False, 'has1250'),
  2: ('cp1251', False, 'has1251'),
  3: ('cp1253', False, 'has1253'),
  4: ('cp1254', False, 'has1254'),
  5: ('cp1255', False, 'has1255'),
  6: ('cp1256', False, 'has1256'),
  7: ('cp1257', False, 'has1257'),
  8: ('cp1258', False, 'has1258'),
  16: ('cp874', False, 'has874'),
  17: ('cp932', True, 'has932'),
  18: ('gb2312', True, 'has936'),
  19: ('cp949', True, 'has949'),
  20: ('cp950', True, 'has950'),
  21: ('johab', True, 'has1361'),
  29: ('mac-roman', False, 'hasMacRoman'),
  # bit 30, OEM Character Set cannot be validated without external info
  # bit 31, Symbol is handled via code, not data
  48: ('cp869', False, 'has869'),
  49: ('cp866', False, 'has866'),
  50: ('cp865', False, 'has865'),
  51: ('cp864', False, 'has864'),
  52: ('cp863', False, 'has863'),
  53: ('cp862', False, 'has862'),
  54: ('cp861', False, 'has861'),
  55: ('cp860', False, 'has860'),
  56: ('cp857', False, 'has857'),
  57: ('cp855', False, 'has855'),
  58: ('cp852', False, 'has852'),
  59: ('cp775', False, 'has775'),
  60: ('cp737', False, 'has737'),
  # bit 61, cp708 (ASMO 708) is not available in a Python encoding
  62: ('cp850', False, 'has850'),
  63: ('cp437', False, 'has437')}

_b8BitSmall = codepageranges_v1._b8BitSmall
_b16BitBig = codepageranges_v1._b16BitBig

# -----------------------------------------------------------------------------

#
# Private functions
#

def _getUSpan(key, onlyPrintables=False):
    """
    Given a bit number as the key, returns a Span with the Unicodes in the full
    version of that code page. If onlyPrintable is True, the Unicodes with
    property 'Cc' (i.e. control characters) will be filtered out of the result.
    
    >>> _printUSpan(_getUSpan(0))  # Latin 1
    U+0000 through U+007F
    U+00A0 through U+00FF
    U+0152 through U+0153
    U+0160 through U+0161
    U+0178
    U+017D through U+017E
    U+0192
    U+02C6
    U+02DC
    U+2013 through U+2014
    U+2018 through U+201A
    U+201C through U+201E
    U+2020 through U+2022
    U+2026
    U+2030
    U+2039 through U+203A
    U+20AC
    U+2122
    
    >>> _printUSpan(_getUSpan(0, True))  # Latin 1, printables only
    U+0020 through U+007E
    U+00A0 through U+00FF
    U+0152 through U+0153
    U+0160 through U+0161
    U+0178
    U+017D through U+017E
    U+0192
    U+02C6
    U+02DC
    U+2013 through U+2014
    U+2018 through U+201A
    U+201C through U+201E
    U+2020 through U+2022
    U+2026
    U+2030
    U+2039 through U+203A
    U+20AC
    U+2122
    """
    
    enc, is16Bit, name = _bitData[key]
    r = span2.Span(ord(c) for c in str(bytes(range(256)), enc, errors='ignore'))
    r.update({ord(c) for c in str(_b16BitBig, enc, errors='ignore')})
    
    if onlyPrintables:
        uc = unicodedata.category
        f = (lambda c: uc(chr(c)) == 'Cc')
        r = span2.Span(itertools.filterfalse(f, r))
    
    return r

def _recalc_all(obj, **kwArgs):
    """
    Recalculates all the flag bits.
    
    Keyword arguments supported are:
    
        base1252        A Boolean which, if True, means the cpthreshold value
                        will be interpreted only with respect to those parts of
                        the code page's repertoire that do not overlap any part
                        of the CP1252 code page. If False, then the comparison
                        is on the whole set by itself. Default is True.
                    
                        Note that this flag has no effect for the CP1252 code
                        page itself, which is always just tested against the
                        cpthreshold value.
    
        cpthreshold     An integral value indicating what portion of a
                        particular code page's repertoire needs to be present
                        in unicodeSpan for that code page to be flagged as
                        present. The values are interpreted as follows (default
                        is 95):
                    
                        0       Any one of the code page's members must be
                                present.
                        
                        1-99    Interpreted as a percentage of the code
                                page's repertoire that must be present.
                        
                        100     100% of the code page's members must be
                                present in unicodeSpan.
        
        unicodeSpan     A Span object with the present Unicodes. If not
                        specified, the Span will be constructed from the editor
                        via the cmap.Cmap.getUnicodeMap() method.
    """
    
    if 'unicodeSpan' in kwArgs:
        uSpan = kwArgs['unicodeSpan']
    
    else:
        e = kwArgs['editor']
        
        if e is None:
            raise codepageranges_v1.NoEditor()
        
        if not e.reallyHas(b'cmap'):
            raise codepageranges_v1.NoCmap()
        
        uSpan = span2.Span(e.cmap.getUnicodeMap())
        
        has30 = bool(e.cmap.findKeys(3, 0))
    
    cpthreshold = kwArgs.get('cpthreshold', 95)
    base1252 = kwArgs.get('base1252', True)
    newObj = obj.__copy__()
    d = newObj.__dict__
    
    for key in set(_bitData) | {31}:
        if key == 31:
            d['hasSymbol'] = has30
        
        else:
            name = _bitData[key][2]
            uSpanEnc = _getUSpan(key, onlyPrintables=True)
            
            if base1252 and (key != 0):
                uSpanEnc -= _getUSpan(0, onlyPrintables=True)
            
            if uSpanEnc:
                diff = uSpanEnc - uSpan
                uCount = len(uSpanEnc)
                dCount = len(diff)
                
                if cpthreshold == 100:
                    d[name] = not diff
                
                elif cpthreshold == 0:
                    d[name] = dCount != uCount
                
                else:
                    presentRatio = float(uCount - dCount) / float(uCount)
                    d[name] = presentRatio >= (cpthreshold / 100.0)
    
    return (newObj != obj), newObj

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if 'unicodeSpan' in kwArgs:
        uSpan = kwArgs['unicodeSpan']
    
    else:
        e = kwArgs['editor']
        
        if e is None or not e.reallyHas(b'cmap'):
            logger.error((
              'V0553',
              (),
              "Unable to validate CodePageRanges because the Editor and/or "
              "the Cmap are not available."))
            
            return False
        
        uSpan = span2.Span(e.cmap.getUnicodeMap())
    
    d = obj.__dict__
    
    for key in set(_bitData):  # symbol is validated separately
        printablesMissing = _getUSpan(key, True) - uSpan
        
        if printablesMissing:
            # there are missing printables from the range
            if d[obj.rangeIDToName[key]]:
                logger.warning((
                  'W2101',
                  (_bitData[key][0],
                   ["U+%04X" % (n,) for n in sorted(printablesMissing)]),
                  "Code page %s is missing printables %s"))
        
        elif not d[obj.rangeIDToName[key]]:
            # all printables are present, but code page is off
            logger.warning((
              'W2100',
              (_bitData[key][0],),
              "Code page %s has all printables, but is set to False"))
    
    return True

def _validate_symbol(flag, **kwArgs):
    """
    PLEASE SEE Jira VALIDATE-159, FONTIO-80 and 
    http://www.microsoft.com/typography/otspec/OS2.htm#cpr
    """
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None or not editor.reallyHas(b'cmap'):
        logger.error((
          'V0553',
          (),
          "Unable to validate symbols because the Editor and/or "
          "the Cmap are not available."))
        
        return False
    
    r = True
    
    has30 = bool(editor.cmap.findKeys(3, 0))
    
    hasMappings = bool(
      set(editor.cmap.getUnicodeMap()) &
      set(range(0xF000, 0xF100))
      )
    
    if has30:
        if not(flag):
            logger.error((
              'E2126',
              (),
              "Symbol code page bit not set, but there is a Symbol (3,0) cmap "
              "subtable present."))

            r = False

    else:
        if flag:
            logger.warning((
              'V0973',
              (),
              "Unicode font with Symbol Code Page bit (#31) set."))

    return r
    
def _validate_oem(flag, **kwArgs):
    logger = kwArgs['logger']
    
    if flag:
        logger.warning((
          'V0793',
          (),
          "OEM Character Set codepagerange bit is set (cannot be validated)."))
          
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CodePageRanges(object, metaclass=maskmeta.FontDataMetaclass):
    """
    Objects representing Windows code page ranges, as contained in the OS/2
    table. These are masklike collections of Boolean attributes, one per code
    page.
    
    >>> CodePageRanges.fromnumber(0x6000000100000000).pprint(label="Code pages")
    Code pages:
      Latin 1 (CP 1252)
      Mac Roman
      OEM Character Set
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 8
    
    maskSorted = (
      'has1252', 'has1250', 'has1251', 'has1253', 'has1254', 'has1255',
      'has1256', 'has1257', 'has1258', 'has874', 'has932', 'has936', 'has949',
      'has950', 'has1361', 'hasMacRoman', 'hasOEM', 'hasSymbol', 'has869', 
      'has866', 'has865', 'has864', 'has863', 'has862', 'has861', 'has860', 
      'has857', 'has855', 'has852', 'has775', 'has737', 'has708', 'has850', 
      'has437')
    
    v = list(maskSorted)
    v.remove('hasOEM')
    v.remove('hasSymbol')
    v.remove('has708')
    rangeIDToName = dict(zip(sorted(_bitData), v))
    del v
    
    def msLongwordSwap64(n, **kwArgs):
        # Converts from this:
        # 31 ... 0 63 ... 32
        # to this:
        # 63 ... 0
        i1to2 = (n &  0xFFFFFFFF) << 32
        i2to1 = (n & (0xFFFFFFFF << 32)) >> 32
        return i1to2 + i2to1

    maskControls = dict(
        loggername = "codepageranges",
        recalculatefunc_partial = _recalc_all,
        validatecode_notsettozero = "E2116",
        validatefunc_partial = _validate,
        inputconvolutionfunc = msLongwordSwap64,
        outputconvolutionfunc = msLongwordSwap64)
    
    maskSpec = dict(
        has1252 = dict(
            mask_isbool = True,
            mask_label = "Latin 1 (CP 1252)",
            mask_rightmostbitindex = 0,
            mask_showonlyiftrue = True),
        
        has1250 = dict(
            mask_isbool = True,
            mask_label = "Latin 2: Eastern Europe (CP 1250)",
            mask_rightmostbitindex = 1,
            mask_showonlyiftrue = True),
        
        has1251 = dict(
            mask_isbool = True,
            mask_label = "Cyrillic (CP 1251)",
            mask_rightmostbitindex = 2,
            mask_showonlyiftrue = True),
        
        has1253 = dict(
            mask_isbool = True,
            mask_label = "Greek (CP 1253)",
            mask_rightmostbitindex = 3,
            mask_showonlyiftrue = True),
        
        has1254 = dict(
            mask_isbool = True,
            mask_label = "Turkish (CP 1254)",
            mask_rightmostbitindex = 4,
            mask_showonlyiftrue = True),
        
        has1255 = dict(
            mask_isbool = True,
            mask_label = "Hebrew (CP 1255)",
            mask_rightmostbitindex = 5,
            mask_showonlyiftrue = True),
        
        has1256 = dict(
            mask_isbool = True,
            mask_label = "Arabic (CP 1256)",
            mask_rightmostbitindex = 6,
            mask_showonlyiftrue = True),
        
        has1257 = dict(
            mask_isbool = True,
            mask_label = "Windows Baltic (CP 1257)",
            mask_rightmostbitindex = 7,
            mask_showonlyiftrue = True),
        
        has1258 = dict(
            mask_isbool = True,
            mask_label = "Vietnamese (CP 1258)",
            mask_rightmostbitindex = 8,
            mask_showonlyiftrue = True),
        
        has874 = dict(
            mask_isbool = True,
            mask_label = "Thai (CP 874)",
            mask_rightmostbitindex = 16,
            mask_showonlyiftrue = True),
        
        has932 = dict(
            mask_isbool = True,
            mask_label = "JIS/Japan (CP 932)",
            mask_rightmostbitindex = 17,
            mask_showonlyiftrue = True),
        
        has936 = dict(
            mask_isbool = True,
            mask_label = "Simplified Chinese (CP 936)",
            mask_rightmostbitindex = 18,
            mask_showonlyiftrue = True),
        
        has949 = dict(
            mask_isbool = True,
            mask_label = "Korean Wansung (CP 949)",
            mask_rightmostbitindex = 19,
            mask_showonlyiftrue = True),
        
        has950 = dict(
            mask_isbool = True,
            mask_label = "Traditional Chinese (CP 950)",
            mask_rightmostbitindex = 20,
            mask_showonlyiftrue = True),
        
        has1361 = dict(
            mask_isbool = True,
            mask_label = "Korean Johab (CP 1361)",
            mask_rightmostbitindex = 21,
            mask_showonlyiftrue = True),
        
        hasMacRoman = dict(
            mask_isbool = True,
            mask_label = "Mac Roman",
            mask_rightmostbitindex = 29,
            mask_showonlyiftrue = True),
        
        hasOEM = dict(
            mask_isbool = True,
            mask_label = "OEM Character Set",
            mask_rightmostbitindex = 30,
            mask_showonlyiftrue = True,
            mask_validatefunc = _validate_oem),
        
        hasSymbol = dict(
            mask_isbool = True,
            mask_label = "Symbols",
            mask_rightmostbitindex = 31,
            mask_showonlyiftrue = True,
            mask_validatefunc = _validate_symbol),
        
        has869 = dict(
            mask_isbool = True,
            mask_label = "IBM Greek (CP 869)",
            mask_rightmostbitindex = 48,
            mask_showonlyiftrue = True),
        
        has866 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Russian (CP 866)",
            mask_rightmostbitindex = 49,
            mask_showonlyiftrue = True),
        
        has865 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Nordic (CP 865)",
            mask_rightmostbitindex = 50,
            mask_showonlyiftrue = True),
        
        has864 = dict(
            mask_isbool = True,
            mask_label = "Arabic (CP 864)",
            mask_rightmostbitindex = 51,
            mask_showonlyiftrue = True),
        
        has863 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Canadian French (CP 863)",
            mask_rightmostbitindex = 52,
            mask_showonlyiftrue = True),
        
        has862 = dict(
            mask_isbool = True,
            mask_label = "Hebrew (SP 862)",
            mask_rightmostbitindex = 53,
            mask_showonlyiftrue = True),
        
        has861 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Icelandic (CP 861)",
            mask_rightmostbitindex = 54,
            mask_showonlyiftrue = True),
        
        has860 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Portuguese (CP 860)",
            mask_rightmostbitindex = 55,
            mask_showonlyiftrue = True),
        
        has857 = dict(
            mask_isbool = True,
            mask_label = "IBM Turkish (CP 857)",
            mask_rightmostbitindex = 56,
            mask_showonlyiftrue = True),
        
        has855 = dict(
            mask_isbool = True,
            mask_label = "IBM Cyrillic (CP 855)",
            mask_rightmostbitindex = 57,
            mask_showonlyiftrue = True),
        
        has852 = dict(
            mask_isbool = True,
            mask_label = "Latin 2 (CP 852)",
            mask_rightmostbitindex = 58,
            mask_showonlyiftrue = True),
        
        has775 = dict(
            mask_isbool = True,
            mask_label = "MS-DOS Baltic (CP 775)",
            mask_rightmostbitindex = 59,
            mask_showonlyiftrue = True),
        
        has737 = dict(
            mask_isbool = True,
            mask_label = "Greek (CP 737; formerly 437 G)",
            mask_rightmostbitindex = 60,
            mask_showonlyiftrue = True),
        
        has708 = dict(
            mask_isbool = True,
            mask_label = "Arabic (CP 708)",
            # ASMO 708 is not recalculated by _recalc_all (yet)
            mask_rightmostbitindex = 61,
            mask_showonlyiftrue = True),
        
        has850 = dict(
            mask_isbool = True,
            mask_label = "WE/Latin 1 (CP 850)",
            mask_rightmostbitindex = 62,
            mask_showonlyiftrue = True),
        
        has437 = dict(
            mask_isbool = True,
            mask_label = "US (CP 437)",
            mask_rightmostbitindex = 63,
            mask_showonlyiftrue = True))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromversion1(cls, v1Obj, **kwArgs):
        """
        Returns a new version 2 CodePageRanges object from the specified
        version 1 CodePageRanges object. There is one keyword argument:
        
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
          has1252 = v1Obj.has1252,
          has1250 = v1Obj.has1250,
          has1251 = v1Obj.has1251,
          has1253 = v1Obj.has1253,
          has1254 = v1Obj.has1254,
          has1255 = v1Obj.has1255,
          has1256 = v1Obj.has1256,
          has1257 = v1Obj.has1257,
          has874 = v1Obj.has874,
          has932 = v1Obj.has932,
          has936 = v1Obj.has936,
          has949 = v1Obj.has949,
          has950 = v1Obj.has950,
          has1361 = v1Obj.has1361,
          hasMacRoman = v1Obj.hasMacRoman,
          hasOEM = v1Obj.hasOEM,
          hasSymbol = v1Obj.hasSymbol,
          has869 = v1Obj.has869,
          has866 = v1Obj.has866,
          has865 = v1Obj.has865,
          has864 = v1Obj.has864,
          has863 = v1Obj.has863,
          has862 = v1Obj.has862,
          has861 = v1Obj.has861,
          has860 = v1Obj.has860,
          has857 = v1Obj.has857,
          has855 = v1Obj.has855,
          has852 = v1Obj.has852,
          has775 = v1Obj.has775,
          has737 = v1Obj.has737,
          has708 = v1Obj.has708,
          has850 = v1Obj.has850,
          has437 = v1Obj.has437)
        
        if kwArgs.get('deferRecalculation', True):
            return r
        
        return r.recalculated(**kwArgs)
    
    #
    # Public methods
    #
    
    def asVersion1(self, **kwArgs):
        """
        Returns a version 1 CodePageRanges object from the data in self. There
        is one keyword argument:
        
            deferRecalculation  If True (the default), the fields will be
                                copied but no recalculation is done. The client
                                should do a recalculation, in this case. If
                                False, a recalculated() object will be
                                returned; in this case, the client should be
                                sure to pass in the needed keyword arguments
                                (usually editor and unicodeSpan, and perhaps
                                base1252 and threshold as well).
        """
        
        r = codepageranges_v1.CodePageRanges(
          has1252 = self.has1252,
          has1250 = self.has1250,
          has1251 = self.has1251,
          has1253 = self.has1253,
          has1254 = self.has1254,
          has1255 = self.has1255,
          has1256 = self.has1256,
          has1257 = self.has1257,
          has874 = self.has874,
          has932 = self.has932,
          has936 = self.has936,
          has949 = self.has949,
          has950 = self.has950,
          has1361 = self.has1361,
          hasMacRoman = self.hasMacRoman,
          hasOEM = self.hasOEM,
          hasSymbol = self.hasSymbol,
          has869 = self.has869,
          has866 = self.has866,
          has865 = self.has865,
          has864 = self.has864,
          has863 = self.has863,
          has862 = self.has862,
          has861 = self.has861,
          has860 = self.has860,
          has857 = self.has857,
          has855 = self.has855,
          has852 = self.has852,
          has775 = self.has775,
          has737 = self.has737,
          has708 = self.has708,
          has850 = self.has850,
          has437 = self.has437)
        
        if kwArgs.get('deferRecalculation', True):
            return r
        
        return r.recalculated(**kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _printUSpan(s):
        for first, last in s.ranges():
            if first == last:
                print("U+%04X" % (first,))
            else:
                print("U+%04X through U+%04X" % (first, last))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
