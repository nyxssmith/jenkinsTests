#
# featureutilities.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities for checking feature tag registration/description and updating list
of feature tags/descriptions from Microsoft OpenType spec.
"""

# Future imports


# System imports
from datetime import datetime
from html.parser import HTMLParser
import urllib.request, urllib.error, urllib.parse

# other imports
from fontio3 import utilities

# -----------------------------------------------------------------------------

#
# Constants
#

LAST_SCRAPE_DATE = '2017-04-04'

OT_FEATURE_DESCRIPTIONS = {
    b'aalt': 'Access All Alternates',
    b'abvf': 'Above-base Forms',
    b'abvm': 'Above-base Mark Positioning',
    b'abvs': 'Above-base Substitutions',
    b'afrc': 'Alternative Fractions',
    b'akhn': 'Akhands',
    b'blwf': 'Below-base Forms',
    b'blwm': 'Below-base Mark Positioning',
    b'blws': 'Below-base Substitutions',
    b'c2pc': 'Petite Capitals From Capitals',
    b'c2sc': 'Small Capitals From Capitals',
    b'calt': 'Contextual Alternates',
    b'case': 'Case-Sensitive Forms',
    b'ccmp': 'Glyph Composition / Decomposition',
    b'cfar': 'Conjunct Form After Ro',
    b'cjct': 'Conjunct Forms',
    b'clig': 'Contextual Ligatures',
    b'cpct': 'Centered CJK Punctuation',
    b'cpsp': 'Capital Spacing',
    b'cswh': 'Contextual Swash',
    b'curs': 'Cursive Positioning',
    b'cv01': 'Character Variants 1',
    b'cv02': 'Character Variants 2',
    b'cv03': 'Character Variants 3',
    b'cv04': 'Character Variants 4',
    b'cv05': 'Character Variants 5',
    b'cv06': 'Character Variants 6',
    b'cv07': 'Character Variants 7',
    b'cv08': 'Character Variants 8',
    b'cv09': 'Character Variants 9',
    b'cv10': 'Character Variants 10',
    b'cv11': 'Character Variants 11',
    b'cv12': 'Character Variants 12',
    b'cv13': 'Character Variants 13',
    b'cv14': 'Character Variants 14',
    b'cv15': 'Character Variants 15',
    b'cv16': 'Character Variants 16',
    b'cv17': 'Character Variants 17',
    b'cv18': 'Character Variants 18',
    b'cv19': 'Character Variants 19',
    b'cv20': 'Character Variants 20',
    b'cv21': 'Character Variants 21',
    b'cv22': 'Character Variants 22',
    b'cv23': 'Character Variants 23',
    b'cv24': 'Character Variants 24',
    b'cv25': 'Character Variants 25',
    b'cv26': 'Character Variants 26',
    b'cv27': 'Character Variants 27',
    b'cv28': 'Character Variants 28',
    b'cv29': 'Character Variants 29',
    b'cv30': 'Character Variants 30',
    b'cv31': 'Character Variants 31',
    b'cv32': 'Character Variants 32',
    b'cv33': 'Character Variants 33',
    b'cv34': 'Character Variants 34',
    b'cv35': 'Character Variants 35',
    b'cv36': 'Character Variants 36',
    b'cv37': 'Character Variants 37',
    b'cv38': 'Character Variants 38',
    b'cv39': 'Character Variants 39',
    b'cv40': 'Character Variants 40',
    b'cv41': 'Character Variants 41',
    b'cv42': 'Character Variants 42',
    b'cv43': 'Character Variants 43',
    b'cv44': 'Character Variants 44',
    b'cv45': 'Character Variants 45',
    b'cv46': 'Character Variants 46',
    b'cv47': 'Character Variants 47',
    b'cv48': 'Character Variants 48',
    b'cv49': 'Character Variants 49',
    b'cv50': 'Character Variants 50',
    b'cv51': 'Character Variants 51',
    b'cv52': 'Character Variants 52',
    b'cv53': 'Character Variants 53',
    b'cv54': 'Character Variants 54',
    b'cv55': 'Character Variants 55',
    b'cv56': 'Character Variants 56',
    b'cv57': 'Character Variants 57',
    b'cv58': 'Character Variants 58',
    b'cv59': 'Character Variants 59',
    b'cv60': 'Character Variants 60',
    b'cv61': 'Character Variants 61',
    b'cv62': 'Character Variants 62',
    b'cv63': 'Character Variants 63',
    b'cv64': 'Character Variants 64',
    b'cv65': 'Character Variants 65',
    b'cv66': 'Character Variants 66',
    b'cv67': 'Character Variants 67',
    b'cv68': 'Character Variants 68',
    b'cv69': 'Character Variants 69',
    b'cv70': 'Character Variants 70',
    b'cv71': 'Character Variants 71',
    b'cv72': 'Character Variants 72',
    b'cv73': 'Character Variants 73',
    b'cv74': 'Character Variants 74',
    b'cv75': 'Character Variants 75',
    b'cv76': 'Character Variants 76',
    b'cv77': 'Character Variants 77',
    b'cv78': 'Character Variants 78',
    b'cv79': 'Character Variants 79',
    b'cv80': 'Character Variants 80',
    b'cv81': 'Character Variants 81',
    b'cv82': 'Character Variants 82',
    b'cv83': 'Character Variants 83',
    b'cv84': 'Character Variants 84',
    b'cv85': 'Character Variants 85',
    b'cv86': 'Character Variants 86',
    b'cv87': 'Character Variants 87',
    b'cv88': 'Character Variants 88',
    b'cv89': 'Character Variants 89',
    b'cv90': 'Character Variants 90',
    b'cv91': 'Character Variants 91',
    b'cv92': 'Character Variants 92',
    b'cv93': 'Character Variants 93',
    b'cv94': 'Character Variants 94',
    b'cv95': 'Character Variants 95',
    b'cv96': 'Character Variants 96',
    b'cv97': 'Character Variants 97',
    b'cv98': 'Character Variants 98',
    b'cv99': 'Character Variants 99',
    b'dist': 'Distances',
    b'dlig': 'Discretionary Ligatures',
    b'dnom': 'Denominators',
    b'dtls': 'Dotless Forms',
    b'expt': 'Expert Forms',
    b'falt': 'Final Glyph on Line Alternates',
    b'fin2': 'Terminal Forms #2',
    b'fin3': 'Terminal Forms #3',
    b'fina': 'Terminal Forms',
    b'flac': 'Flattened accent forms',
    b'frac': 'Fractions',
    b'fwid': 'Full Widths',
    b'half': 'Half Forms',
    b'haln': 'Halant Forms',
    b'halt': 'Alternate Half Widths',
    b'hist': 'Historical Forms',
    b'hkna': 'Horizontal Kana Alternates',
    b'hlig': 'Historical Ligatures',
    b'hngl': 'Hangul',
    b'hojo': 'Hojo Kanji Forms (JIS X 0212-1990 Kanji Forms)',
    b'hwid': 'Half Widths',
    b'init': 'Initial Forms',
    b'isol': 'Isolated Forms',
    b'ital': 'Italics',
    b'jalt': 'Justification Alternates',
    b'jp04': 'JIS2004 Forms',
    b'jp78': 'JIS78 Forms',
    b'jp83': 'JIS83 Forms',
    b'jp90': 'JIS90 Forms',
    b'kern': 'Kerning',
    b'lfbd': 'Left Bounds',
    b'liga': 'Standard Ligatures',
    b'ljmo': 'Leading Jamo Forms',
    b'lnum': 'Lining Figures',
    b'locl': 'Localized Forms',
    b'ltra': 'Left-to-right alternates',
    b'ltrm': 'Left-to-right mirrored forms',
    b'mark': 'Mark Positioning',
    b'med2': 'Medial Forms #2',
    b'medi': 'Medial Forms',
    b'mgrk': 'Mathematical Greek',
    b'mkmk': 'Mark to Mark Positioning',
    b'mset': 'Mark Positioning via Substitution',
    b'nalt': 'Alternate Annotation Forms',
    b'nlck': 'NLC Kanji Forms',
    b'nukt': 'Nukta Forms',
    b'numr': 'Numerators',
    b'onum': 'Oldstyle Figures',
    b'opbd': 'Optical Bounds',
    b'ordn': 'Ordinals',
    b'ornm': 'Ornaments',
    b'palt': 'Proportional Alternate Widths',
    b'pcap': 'Petite Capitals',
    b'pkna': 'Proportional Kana',
    b'pnum': 'Proportional Figures',
    b'pref': 'Pre-Base Forms',
    b'pres': 'Pre-base Substitutions',
    b'pstf': 'Post-base Forms',
    b'psts': 'Post-base Substitutions',
    b'pwid': 'Proportional Widths',
    b'qwid': 'Quarter Widths',
    b'rand': 'Randomize',
    b'rclt': 'Required Contextual Alternates',
    b'rkrf': 'Rakar Forms',
    b'rlig': 'Required Ligatures',
    b'rphf': 'Reph Forms',
    b'rtbd': 'Right Bounds',
    b'rtla': 'Right-to-left alternates',
    b'rtlm': 'Right-to-left mirrored forms',
    b'ruby': 'Ruby Notation Forms',
    b'rvrn': 'Required Variation Alternates',
    b'salt': 'Stylistic Alternates',
    b'sinf': 'Scientific Inferiors',
    b'size': 'Optical size',
    b'smcp': 'Small Capitals',
    b'smpl': 'Simplified Forms',
    b'ss01': 'Stylistic Set 1',
    b'ss02': 'Stylistic Set 2',
    b'ss03': 'Stylistic Set 3',
    b'ss04': 'Stylistic Set 4',
    b'ss05': 'Stylistic Set 5',
    b'ss06': 'Stylistic Set 6',
    b'ss07': 'Stylistic Set 7',
    b'ss08': 'Stylistic Set 8',
    b'ss09': 'Stylistic Set 9',
    b'ss10': 'Stylistic Set 10',
    b'ss11': 'Stylistic Set 11',
    b'ss12': 'Stylistic Set 12',
    b'ss13': 'Stylistic Set 13',
    b'ss14': 'Stylistic Set 14',
    b'ss15': 'Stylistic Set 15',
    b'ss16': 'Stylistic Set 16',
    b'ss17': 'Stylistic Set 17',
    b'ss18': 'Stylistic Set 18',
    b'ss19': 'Stylistic Set 19',
    b'ss20': 'Stylistic Set 20',
    b'ssty': 'Math script style alternates',
    b'stch': 'Stretching Glyph Decomposition',
    b'subs': 'Subscript',
    b'sups': 'Superscript',
    b'swsh': 'Swash',
    b'titl': 'Titling',
    b'tjmo': 'Trailing Jamo Forms',
    b'tnam': 'Traditional Name Forms',
    b'tnum': 'Tabular Figures',
    b'trad': 'Traditional Forms',
    b'twid': 'Third Widths',
    b'unic': 'Unicase',
    b'valt': 'Alternate Vertical Metrics',
    b'vatu': 'Vattu Variants',
    b'vert': 'Vertical Writing',
    b'vhal': 'Alternate Vertical Half Metrics',
    b'vjmo': 'Vowel Jamo Forms',
    b'vkna': 'Vertical Kana Alternates',
    b'vkrn': 'Vertical Kerning',
    b'vpal': 'Proportional Alternate Vertical Metrics',
    b'vrt2': 'Vertical Alternates and Rotation',
    b'vrtr': 'Vertical Alternates for Rotation',
    b'zero': 'Slashed Zero',
}

URL_FEATURETAG_REG = 'http://www.microsoft.com/typography/otspec/featurelist.htm'

# -----------------------------------------------------------------------------

#
# Classes
#

class MyHTMLParser(HTMLParser):

    def __init__(self): # pragma: no cover
        HTMLParser.__init__(self)
        self._ftag = None
        self._td_count = 0
        self._td_depth = 0
        self.feature_tags = dict()

    def handle_starttag(self, tag, attrs): # pragma: no cover
        if tag == 'tr':
            self._td_count = 0
            self._td_depth = 0
        elif tag == 'td':
            self._td_count += 1
            self._td_depth += 1

    def handle_endtag(self, tag): # pragma: no cover
        if tag == 'td':
            self._td_depth -= 1

    def handle_data(self, data): # pragma: no cover
        clean_data = data.strip()
        if self._td_count == 1 and self._td_depth == 1 and len(clean_data) == 4:
            self._ftag = clean_data

        if self._td_count == 2 and self._td_depth == 1 and len(clean_data):
            if self._ftag not in self.feature_tags:
                self.feature_tags[self._ftag] = clean_data

# -----------------------------------------------------------------------------

#
# Functions
#

def generatevalidfeatureset(): # pragma: no cover
    """
    Print LAST_SCRAPE_DATE and OT_FEATURE_DESCRIPTIONS in form suitable for
    copy/paste into this file, for updating fontio3 when feature tag
    registries are updated.
    """
    
    dstr = datetime.now().strftime("%Y-%m-%d")
    print("LAST_SCRAPE_DATE = '%s'\n" % (dstr,))

    feattags = parseregistry(URL_FEATURETAG_REG)

    # Special case for cv01-cv99 range (the only one currently in featurelist.htm)
    # since it's part of the spec, and it is not likely to be removed, we don't
    # try to parse it; just add it after the fact here.
    for cvi in range(1,100):
        feattags["cv%02d" % (cvi,)] = "Character Variants %d" % (cvi,)

    print("OT_FEATURE_DESCRIPTIONS = {")
    for ft, fd in sorted(feattags.items()):
        print("    b'%s': '%s'," % (ft, fd))
    print("}")

def parseregistry(url): # pragma: no cover
    """
    Scrape OpenType Feature tags from registry page at supplied url.
    """
    
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'Monotype Font Tools Crawler'})
    
    page = urllib.request.urlopen(request)
    html = page.read()
    page.close()
    parser = MyHTMLParser()
    parser.feed(str(html, 'utf-8'))
    return parser.feature_tags

def isValidFeatureTag(tag, **kwArgs):
    """
    Validate whether a supplied tag is in our set of valid feature tags, writing
    results to a logger supplied in kwArgs.
    
    >>> l = utilities.makeDoctestLogger("featureutilities")

    >>> isValidFeatureTag(b'\x0Eabc', logger=l)
    featureutilities - ERROR - Feature tag '\u000Eabc' is not a legal OpenType feature tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    >>> isValidFeatureTag(b'hi', logger=l)
    featureutilities - ERROR - Feature tag 'hi' is not a legal OpenType feature tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    >>> isValidFeatureTag(b'foo ', logger=l)
    featureutilities - WARNING - Feature tag 'foo ' is a legal tag, but does not appear in the OpenType Feature Tag registry as of 2017-04-04.
    False

    >>> isValidFeatureTag(b'aalt', logger=l)
    featureutilities - INFO - Feature tag 'aalt' is a legal tag and appears in the OpenType Feature Tag registry.
    True

    >>> isValidFeatureTag('\u00FFabc')
    False

    >>> isValidFeatureTag('\u1032abc', logger=l)
    featureutilities - ERROR - Feature tag 'ဲabc' is not a legal OpenType feature tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    # This one can be problematic due to formatting irregularities in MS's HTML
    >>> OT_FEATURE_DESCRIPTIONS[b'curs']
    'Cursive Positioning'
    
    >>> isValidFeatureTag(b'afrc')
    True
    """
    
    logger = kwArgs.get('logger', None)
    
    if isinstance(tag, str):
        try:
            tag = tag.encode('ascii')
        
        except UnicodeEncodeError:
            if logger is not None:
                logger.error((
                  'V1010',
                  (tag,),
                  "Feature tag '%s' is not a legal OpenType feature tag (must "
                  "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
    
    isLegal = len(tag) == 4 and all(0x20 <= x <= 0x7E for x in tag)
    isRegistered = tag in OT_FEATURE_DESCRIPTIONS

    if logger is not None:        
        if not isLegal:
            logger.error((
              'V1010',
              (str(tag, 'ascii'),),
              "Feature tag '%s' is not a legal OpenType feature tag (must "
              "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
        
        if not isRegistered:
            logger.warning((
              'V1011',
              (str(tag, 'ascii'), LAST_SCRAPE_DATE),
              "Feature tag '%s' is a legal tag, but does not appear in the "
              "OpenType Feature Tag registry as of %s."))
            
            return False
            
        logger.info((
          'V1012',
          (str(tag, 'ascii'),),
          "Feature tag '%s' is a legal tag and appears in the OpenType "
          "Feature Tag registry."))
        
        return True
        
    return isLegal and isRegistered

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
