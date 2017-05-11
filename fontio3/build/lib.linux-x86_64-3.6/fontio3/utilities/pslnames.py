#
# pslnames.py
#
# Copyright © 2004-2011, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Names for platform, script and language. These were originally in name.py, but
since they're used in cmaps also, they were moved here to a common module.
"""

# System imports
import collections
import logging

# Other imports
from fontio3 import utilities

# -----------------------------------------------------------------------------

#
# Constants
#

unknown = lambda: "(unknown)"

platformNames = collections.defaultdict(unknown, {
    0: "Unicode",
    1: "Mac",
    2: "ISO (deprecated)",
    3: "MS",
    4: "Custom"})

platform0Names = collections.defaultdict(unknown, {
    0: "1.0 semantics",
    1: "1.1 semantics",
    2: "ISO 10646:1993 semantics",
    3: "2.0, BMP only",
    4: "2.0, Full Repertoire",
    5: "Variation Sequences",
    6: "Full Repertoire"})

platform1Names = collections.defaultdict(unknown, {
    0: "Roman",
    1: "Japanese",
    2: "Traditional Chinese",
    3: "Korean",
    4: "Arabic",
    5: "Hebrew",
    6: "Greek",
    7: "Russian",
    8: "RSymbol",
    9: "Devanagari",
    10: "Gurmukhi",
    11: "Gujarati",
    12: "Oriya",
    13: "Bengali",
    14: "Tamil",
    15: "Telugu",
    16: "Kannada",
    17: "Malayalam",
    18: "Sinhalese",
    19: "Burmese",
    20: "Khmer",
    21: "Thai",
    22: "Laotian",
    23: "Georgian",
    24: "Armenian",
    25: "Simplified Chinese",
    26: "Tibetan",
    27: "Mongolian",
    28: "Geez",
    29: "Slavic",
    30: "Vietnamese",
    31: "Sindhi",
    32: "(Uninterpreted)"})

# ISO is now deprecated
platform2Names = collections.defaultdict(unknown, {
    0: "7-bit ASCII",
    1: "ISO 10646",
    2: "ISO 8859-1"})
    
platform3Names = collections.defaultdict(unknown, {
    0: "Symbol",
    1: "BMP",
    2: "ShiftJIS",
    3: "PRC",
    4: "Big5",
    5: "Wansung",
    6: "Johab",
    7: "Reserved",
    8: "Reserved",
    9: "Reserved",
    10: "Unicode"})

platform1Languages = collections.defaultdict(unknown, {
    0: "English",
    1: "French",
    2: "German",
    3: "Italian",
    4: "Dutch",
    5: "Swedish",
    6: "Spanish",
    7: "Danish",
    8: "Portuguese",
    9: "Norwegian",
    10: "Hebrew",
    11: "Japanese",
    12: "Arabic (Saudi)",
    13: "Finnish",
    14: "Greek",
    15: "Icelandic",
    16: "Maltese",
    17: "Turkish",
    18: "Croatian",
    19: "Traditional Chinese",
    20: "Urdu",
    21: "Hindi",
    22: "Thai",
    23: "Korean",
    24: "Lithuanian",
    25: "Polish",
    26: "Hungarian",
    27: "Estonian",
    28: "Latvian",
    29: "Sami",
    30: "Faroese",
    31: "Farsi",
    32: "Russian",
    33: "Simplified Chinese",
    34: "Flemish",
    35: "Irish Gaelic",
    36: "Albanian",
    37: "Romanian",
    38: "Czech",
    39: "Slovak",
    40: "Slovenian",
    41: "Yiddish",
    42: "Serbian Cyrillic",
    43: "Macedonian",
    44: "Bulgarian",
    45: "Ukrainian",
    46: "Belarussian",
    47: "Uzbek Cyrillic",
    48: "Kazakh",
    49: "Azeri Cyrillic",
    50: "Azerbaijani Armenian",
    51: "Armenian",
    52: "Georgian",
    53: "Moldavian",
    54: "Kirghiz",
    55: "Tajiki",
    56: "Turkmen",
    57: "Mongolian",
    58: "Mongolian Cyrillic",
    59: "Pashto",
    60: "Kurdish",
    61: "Kashmiri",
    62: "Sindhi",
    63: "Tibetan",
    64: "Nepali",
    65: "Sanskrit",
    66: "Marathi",
    67: "Bengali",
    68: "Assamese",
    69: "Gujarati",
    70: "Punjabi",
    71: "Oriya",
    72: "Malayalam",
    73: "Kannada",
    74: "Tamil",
    75: "Telugu",
    76: "Sinhalese",
    77: "Burmese",
    78: "Khmer",
    79: "Lao",
    80: "Vietnamese",
    81: "Indonesian",
    82: "Tagalog",
    83: "Malay Roman",
    84: "Malay Arabic",
    85: "Amharic",
    86: "Tigrinya",
    87: "Oromo",
    88: "Somali",
    89: "Swahili",
    90: "Kinyarwanda",
    91: "Rundi",
    92: "Nyanja",
    93: "Malagasy",
    94: "Esperanto",
    128: "Welsh",
    129: "Basque",
    130: "Catalan",
    131: "Latin",
    132: "Quechua",
    133: "Guarani",
    134: "Aymara",
    135: "Tatar",
    136: "Uighur",
    137: "Dzongkha",
    138: "Javanese Roman",
    139: "Sundanese Roman",
    140: "Galician",
    141: "Afrikaans",
    142: "Breton",
    143: "Inuktitut",
    144: "Scottish Gaelic",
    145: "Manx Gaelic",
    146: "Irish Gaelic Script",
    147: "Tongan",
    148: "Greek Polytonic",
    149: "Greenlandic",
    150: "Azeri Roman",
    65535: "(no language)"})

platform3Languages = collections.defaultdict(unknown, {
    0x0401: "Arabic (Saudi Arabia)",
    0x0402: "Bulgarian",
    0x0403: "Catalan",
    0x0404: "Chinese (Taiwan)",
    0x0405: "Czech",
    0x0406: "Danish",
    0x0407: "German (Germany)",
    0x0408: "Greek",
    0x0409: "English (U.S.)",
    0x040A: "Spanish (Traditional Sort)",
    0x040B: "Finnish",
    0x040C: "French (France)",
    0x040D: "Hebrew",
    0x040E: "Hungarian",
    0x040F: "Icelandic",
    0x0410: "Italian (Italy)",
    0x0411: "Japanese",
    0x0412: "Korean",
    0x0413: "Dutch (Netherlands)",
    0x0414: "Norwegian",
    0x0415: "Polish",
    0x0416: "Portuguese (Brazil)",
    0x0417: "Romansh",
    0x0418: "Romanian",
    0x0419: "Russian",
    0x041A: "Croatian",
    0x041B: "Slovak",
    0x041C: "Albanian",
    0x041D: "Swedish",
    0x041E: "Thai",
    0x041F: "Turkish",
    0x0420: "Urdu",
    0x0421: "Indonesian",
    0x0422: "Ukrainian",
    0x0423: "Belarusian",
    0x0424: "Slovenian",
    0x0425: "Estonian",
    0x0426: "Latvian",
    0x0427: "Lithuanian",
    0x0428: "Tajik (Cyrillic)",
    0x0429: "Farsi",
    0x042A: "Vietnamese",
    0x042B: "Armenian",
    0x042C: "Azeri (Latin)",
    0x042D: "Basque",
    0x042E: "Upper Sorbian",
    0x042F: "Macedonian",
    0x0432: "Setswana",
    0x0434: "isiXhosa",
    0x0435: "isiZulu",
    0x0436: "Afrikaans",
    0x0437: "Georgian",
    0x0438: "Faroese",
    0x0439: "Hindi",
    0x043A: "Maltese",
    0x043B: "Sami (Northern, Norway)",
    0x043E: "Malay (Malaysia)",
    0x043F: "Kazakh",
    0x0440: "Kyrgyz",
    0x0441: "Kiswahili",
    0x0442: "Turkmen",
    0x0443: "Uzbek (Latin)",
    0x0444: "Tatar",
    0x0445: "Bengali (India)",
    0x0446: "Punjabi",
    0x0447: "Gujarati",
    0x0448: "Odiya",
    0x0449: "Tamil",
    0x044A: "Telugu",
    0x044B: "Kannada",
    0x044C: "Malayalam",
    0x044D: "Assamese",
    0x044E: "Marathi",
    0x044F: "Sanskrit",
    0x0450: "Mongolian (Cyrillic)",
    0x0451: "Tibetan",
    0x0452: "Welsh",
    0x0453: "Khmer",
    0x0454: "Lao",
    0x0456: "Galician",
    0x0457: "Konkani",
    0x045A: "Syriac",
    0x045B: "Sinhala",
    0x045D: "Inuktitut",
    0x045E: "Amharic",
    0x0462: "Frisian",
    0x0463: "Pashto",
    0x0464: "Filipino",
    0x0465: "Divehi",
    0x0468: "Hausa (Latin)",
    0x046A: "Yoruba",
    0x046B: "Quechua (Bolivia)",
    0x046C: "Sesotho sa Leboa",
    0x046D: "Bashkir",
    0x046E: "Luxembourgish",
    0x046F: "Greenlandic",
    0x0470: "Igbo",
    0x0478: "Yi",
    0x047A: "Mapudungun",
    0x047C: "Mohawk",
    0x047E: "Breton",
    0x0480: "Uighur",
    0x0481: "Maori",
    0x0482: "Occitan",
    0x0483: "Corsican",
    0x0484: "Alsatian",
    0x0485: "Yakut",
    0x0486: "K'iche",
    0x0488: "Wolof",
    0x048C: "Dari",
    0x0801: "Arabic (Iraq)",
    0x0804: "Chinese (People's Republic of China)",
    0x0807: "German (Switzerland)",
    0x0809: "English (United Kingdom)",
    0x080A: "Spanish (Mexico)",
    0x080C: "French (Belgium)",
    0x0810: "Italian (Switzerland)",
    0x0813: "Dutch (Belgium)",
    0x0814: "Norwegian (Nynorsk)",
    0x0816: "Portuguese (Portugal)",
    0x081A: "Serbian (Latin, Serbia)",
    0x081D: "Swedish (Finland)",
    0x082C: "Azeri (Cyrillic)",
    0x082E: "Lower Sorbian",
    0x083B: "Sami (Northern, Sweden)",
    0x083C: "Irish",
    0x083E: "Malay (Brunei Darussalam)",
    0x0843: "Uzbek (Cyrillic)",
    0x0845: "Bengali (Bangladesh)",
    0x0850: "Mongolian (Traditional)",
    0x085D: "Inuktitut (Latin)",
    0x085F: "Tamazight (Latin)",
    0x086B: "Quechua (Ecuador)",
    0x0C01: "Arabic (Egypt)",
    0x0C04: "Chinese (Hong Kong S.A.R.)",
    0x0C07: "German (Austria)",
    0x0C09: "English (Australia)",
    0x0C0A: "Spanish (Modern Sort)",
    0x0C0C: "French (Canada)",
    0x0C1A: "Serbian (Cyrillic, Serbia)",
    0x0C3B: "Sami (Northern, Finland)",
    0x0C6B: "Quechua (Peru)",
    0x1001: "Arabic (Libya)",
    0x1004: "Chinese (Singapore)",
    0x1007: "German (Luxembourg)",
    0x1009: "English (Canada)",
    0x100A: "Spanish (Guatemala)",
    0x100C: "French (Switzerland)",
    0x101A: "Croatian (Latin)",
    0x103B: "Sami (Lule, Norway)",
    0x1401: "Arabic (Algeria)",
    0x1404: "Chinese (Macao S.A.R.)",
    0x1407: "German (Liechtenstein)",
    0x1409: "English (New Zealand)",
    0x140A: "Spanish (Costa Rica)",
    0x140C: "French (Luxembourg)",
    0x141A: "Bosnian (Latin)",
    0x143B: "Sami (Lule, Sweden)",
    0x1801: "Arabic (Morocco)",
    0x1809: "English (Ireland)",
    0x180A: "Spanish (Panama)",
    0x180C: "French (Monaco)",
    0x181A: "Serbian (Latin, Bosnia and Herzegovina)",
    0x183B: "Sami (Southern, Norway)",
    0x1C01: "Arabic (Tunisia)",
    0x1C09: "English (South Africa)",
    0x1C0A: "Spanish (Dominican Republic)",
    0x1C1A: "Serbian (Cyrillic, Bosnia and Herzegovina)",
    0x1C3B: "Sami (Southern, Sweden)",
    0x2001: "Arabic (Oman)",
    0x2009: "English (Jamaica)",
    0x200A: "Spanish (Venezuela)",
    0x201A: "Bosnian (Cyrillic)",
    0x203B: "Sami (Skoit)",
    0x2401: "Arabic (Yemen)",
    0x2409: "English (Caribbean)",
    0x240A: "Spanish (Colombia)",
    0x243B: "Sami (Inari)",
    0x2801: "Arabic (Syria)",
    0x2809: "English (Belize)",
    0x280A: "Spanish (Peru)",
    0x2C01: "Arabic (Jordan)",
    0x2C09: "English (Trinidad and Tobago)",
    0x2C0A: "Spanish (Argentina)",
    0x3001: "Arabic (Lebanon)",
    0x3009: "English (Zimbabwe)",
    0x300A: "Spanish (Ecuador)",
    0x3401: "Arabic (Kuwait)",
    0x3409: "English (Philippines)",
    0x340A: "Spanish (Chile)",
    0x3801: "Arabic (U.A.E.)",
    0x380A: "Spanish (Uruguay)",
    0x3C01: "Arabic (Bahrain)",
    0x3C0A: "Spanish (Paraguay)",
    0x4001: "Arabic (Qatar)",
    0x4009: "English (India)",
    0x400A: "Spanish (Bolivia)",
    0x4409: "English (Malaysia)",
    0x440A: "Spanish (El Salvador)",
    0x4809: "English (Singapore)",
    0x480A: "Spanish (Honduras)",
    0x4C0A: "Spanish (Nicaragua)",
    0x500A: "Spanish (Puerto Rico)",
    0x540A: "Spanish (United States)"})

# -----------------------------------------------------------------------------

#
# Public functions
#

def isValid(platform, script, language, **kwArgs):
    """
    If one or more of the specified values either do not exist, or do not
    exist in that particular combination, then the logger is used to post
    an error to that effect.
    
    The following keyword arguments are used:
    
        languageCode        If the language is unrecognized or contextually
                            invalid, then this error code will be posted. If no
                            code is provided, the default ('G0021') will be
                            used.
        
        logger              A logger to be used. If none is provided a default
                            logger will be used.
        
        platformCode        If the platform is unrecognized or contextually
                            invalid, then this error code will be posted. If no
                            code is provided, the default ('G0019') will be
                            used.
        
        scriptCode          If the script/platform-specific value is
                            unrecognized or contextually invalid, then this
                            error code will be posted. If no code is provided,
                            the default ('G0020') will be used.
    
    >>> logger = utilities.makeDoctestLogger("test")
    >>> isValid(1, 0, 0, logger=logger)
    True
    
    >>> isValid(12, 0, 0, logger=logger)
    test.pslnames - ERROR - The platform code 12 is not recognized.
    False
    
    >>> isValid(3, 61, 0, logger=logger)
    test.pslnames - ERROR - The script code 61 is not recognized for platform 3
    False
    
    >>> isValid(3, 1, 0x45F, logger=logger)
    test.pslnames - ERROR - The language code 1119 (0x045F) is not recognized for script 1 of platform 3
    False
    """
    
    logger = kwArgs.get('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('pslnames')
    else:
        logger = logger.getChild('pslnames')
    
    r = True
    
    if platform not in platformNames:
        logger.error((
          kwArgs.get('platformCode', 'G0019'),
          (platform,),
          "The platform code %d is not recognized."))
        
        return False
    
    if platform == 4:
        # There is no checking for custom platform(s)
        return r
    
    sDicts = (
      platform0Names,
      platform1Names,
      platform2Names,
      platform3Names)
    
    if script not in sDicts[platform]:
        logger.error((
          kwArgs.get('scriptCode', 'G0020'),
          (script, platform),
          "The script code %d is not recognized for platform %d"))
        
        return False
    
    if platform == 0 or platform == 2:
        # Unicode and ISO platforms don't use language codes
        return r
    
    lDict = (platform1Languages if platform == 1 else platform3Languages)
    
    if language not in lDict:
        logger.error((
          kwArgs.get('languageCode', 'G0021'),
          (language, language, script, platform),
          "The language code %d (0x%04X) is not recognized for script %d of platform %d"))
        
        r = False
    
    return r

def labelForKey(t, addRecap=True, adjustForCmap=False, **kwArgs):
    """
    Returns a string which sensibly describes the particular platform, script
    and language tuple. If addRecap is True, the numeric triple will be added
    at the end of the returned string, preceded by a space. If adjustForCmap
    is True then one will be subtracted from the langauge for Mac-specific
    encodings.
    
    The following keyword arguments are used:
    
        terse       If True, the descriptive "Platform:", "Specific kind:", and
                    "Language:" strings will be omitted from the final output.
                    Specifying this flag will force addRecap to be turned off.
                    Default is False.
    
    >>> print(labelForKey((3, 1, 0)))
    Platform: MS, Specific kind: BMP (3, 1, 0)
    >>> print(labelForKey((1, 4, 84), addRecap=False))
    Platform: Mac, Specific kind: Arabic, Language: Malay Arabic
    >>> print(labelForKey((6, 5, 1)))
    Platform: (unknown) (6, 5, 1)
    
    >>> print(labelForKey((1, 0, 0)))
    Platform: Mac, Specific kind: Roman, Language: English (1, 0, 0)
    >>> print(labelForKey((1, 0, 0), adjustForCmap=True))
    Platform: Mac, Specific kind: Roman, Language: not specified (1, 0, 0)
    >>> print(labelForKey((1, 0, 0), terse=True))
    Mac/Roman/English
    >>> print(labelForKey((3, 1, 0x045E), terse=True))
    MS/BMP/Amharic
    >>> print(labelForKey((3, 1, "zh-Hant-HK"), terse=True))
    MS/BMP/'zh-Hant-HK'
    """
    
    terse = kwArgs.get('terse', False)
    
    if terse:
        addRecap = False
    
    platform, script, language = t
    sv = [platformNames[platform]]  # it's a defaultdict, so this is OK
    
    if platform == 0:
        sv.append(platform0Names[script])
    
    elif platform == 1:
        sv.append(platform1Names[script])
        
        if adjustForCmap:
            language -= 1
        
        if language == -1:
            sv.append("not specified")
        else:
            sv.append(platform1Languages[language])
    
    elif platform == 2:
        sv.append(platform2Names[script])
    
    elif platform == 3:
        sv.append(platform3Names[script])
        
        if isinstance(language, str):
            sv.append(repr(language))
        elif language:
            sv.append(platform3Languages[language])
    
    if len(sv) == 1:
        fmt = ("%s" if terse else "Platform: %s")
    elif len(sv) == 2:
        fmt = ("%s/%s" if terse else "Platform: %s, Specific kind: %s")
    else:
        fmt = ("%s/%s/%s" if terse else "Platform: %s, Specific kind: %s, Language: %s")
    
    sv = [fmt % tuple(sv)]
    
    if addRecap:
        sv.append(str(t))
    
    return ' '.join(sv)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
