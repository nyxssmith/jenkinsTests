#
# metautils.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utility functions and data for the 'meta' table.
"""

# System imports
import re
import urllib.request, urllib.error, urllib.parse

# -----------------------------------------------------------------------------

#
# Constants
#

FONTIO_UNIRANGE_TO_IANA_MAP = {
    'hasBasicLatin': ('Latn',),
    'hasLatin1Supplement': ('Latn',),
    'hasLatinExtendedA': ('Latn',),
    'hasLatinExtendedB': ('Latn',),
    'hasIPA': ('Latn',),
    'hasIPAPhonetics': ('Latn',),
    # 'hasModifierLetters': (,),
    # 'hasCombiningDiacriticalMarks': (,),
    'hasBasicGreek': ('Grek',),
    'hasGreek': ('Grek',),
    'hasGreekSymbolsAndCoptic': ('Grek', 'Copt'),
    'hasGreekAndCoptic': ('Grek', 'Copt'),
    'hasCoptic': ('Copt',),
    'hasCyrillic': ('Cyrl',),
    'hasArmenian': ('Armn',),
    'hasBasicHebrew': ('Hebr',),
    'hasHebrewExtended': ('Hebr',),
    'hasHebrew': ('Hebr',),
    'hasVai': ('Vaii',),
    'hasBasicArabic': ('Arab', 'Aran'),
    'hasArabicExtended': ('Arab', 'Aran'),
    'hasArabic': ('Arab', 'Aran'),
    'hasNKo': ('Nkoo',),
    'hasDevanagari': ('Deva',),
    'hasBengali': ('Beng',),
    'hasGurmukhi': ('Guru',),
    'hasGujarati': ('Gujr',),
    'hasOriya': ('Orya',),
    'hasTamil': ('Taml',),
    'hasTelugu': ('Telu',),
    'hasKannada': ('Knda',),
    'hasMalayalam': ('Mlym',),
    'hasThai': ('Thai',),
    'hasLao': ('Laoo',),
    'hasBasicGeorgian': ('Geor', 'Geok'),
    'hasGeorgianExtended': ('Geor', 'Geok'),
    'hasGeorgian': ('Geor', 'Geok'),
    'hasBalinese': ('Bali',),
    'hasHangulJamo': ('Hang',),
    'hasLatinExtendedAdditional': ('Latn',),
    'hasGreekExtended': ('Grek',),
    # 'hasPunctuation': (,),
    # 'hasSuperscriptsAndSubscripts': (,),
    # 'hasCurrency': (,),
    # 'hasSymbolCombiningDiacritics': (,),
    # 'hasLetterlike': (,),
    # 'hasNumberForms': (,),
    # 'hasArrows': (,),
    # 'hasMathematical': (,),
    # 'hasMiscellaneousTechnical': (,),
    # 'hasControlPictures': (,),
    # 'hasOCR': (,),
    # 'hasEnclosed': (,),
    # 'hasBoxDrawing': (,),
    # 'hasBlockElements': (,),
    # 'hasGeometricShapes': (,),
    # 'hasMiscellaneousSymbols': (,),
    # 'hasDingbats': (,),
    # 'hasCJKPunctuation': (,),
    'hasHiragana': ('Hira', 'Hrkt', 'Japn'),
    'hasKatakana': ('Kana', 'Krkt', 'Japn'),
    'hasBopomofo': ('Bopo',),
    # 'hasHangulCompatibilityJamo': (,),
    'hasPhagsPa': ('Phag',),
    # 'hasCJKMiscellaneous': (,),
    # 'hasCJKEnclosed': (,),
    # 'hasCJKCompatibility': (,),
    'hasHangulSyllables': ('Hang', 'Kore'),
    # 'hasNonPlaneZero': (,),
    'hasPhoenician': ('Phnx',),
    'hasCJKIdeographs': ('Hani', 'Hans', 'Hant', 'Jpan', 'Kore'),
    # 'hasPlaneZeroPrivate': (,),
    # 'hasCJKStrokes': (,),
    'hasAlphabeticPresentationForms': ('Latn', 'Hebr'),
    'hasArabicPresentationFormsA': ('Arab',),
    # 'hasCombiningHalfMarks': (,),
    # 'hasVerticalForms': (,),
    'hasSmallFormVariants': ('Latn',),
    'hasArabicPresentationFormsB': ('Arab',),
    'hasHalfAndFullWidthForms': ('Hira', 'Kana'),
    # 'hasSpecials': (,),
    'hasTibetan': ('Tibt',),
    'hasSyriac': ('Syrc', 'Syre', 'Syrj', 'Syrn'),
    'hasThaana': ('Thaa',),
    'hasSinhala': ('Sinh',),
    'hasMyanmar': ('Mymr',),
    'hasEthiopic': ('Ethi',),
    'hasCherokee': ('Cher',),
    'hasUnifiedCanadianAboriginalSyllabics': ('Cans',),
    'hasOgham': ('Ogam',),
    'hasRunic': ('Runr',),
    'hasKhmer': ('Khmr',),
    'hasMongolian': ('Mong',),
    'hasBraille': ('Brai',),
    'hasYi': ('Yiii',),
    'hasTagalogEtAl': ('Buhd', 'Hano', 'Tagb', 'Tglg'),
    'hasOldItalic': ('Ital',),
    'hasGothic': ('Goth',),
    'hasDeseret': ('Dsrt',),
    # 'hasMusical': (,),
    'hasMathematicalAlphanumerics': ('Zmth',),
    # 'hasPlane1516Private': (,),
    # 'hasVariations': (,),
    # 'hasTags': (,),
    'hasLimbu': ('Limb',),
    'hasTaiLe': ('Tale',),
    'hasNewTaiLue': ('Talu',),
    'hasBuginese': ('Bugi',),
    'hasGlagolitic': ('Glag',),
    'hasTifinagh': ('Tfng',),
    # 'hasYijingHexagrams': (,),
    'hasSylotiNagri': ('Sylo',),
    'hasLinearB': ('Linb',),
    # 'hasAncientGreekNumbers': (,),
    'hasUgaritic': ('Ugar',),
    'hasOldPersian': ('Xpeo',),
    'hasShavian': ('Shaw',),
    'hasOsmanya': ('Osma',),
    'hasCypriot': ('Cprt',),
    'hasKharoshthi': ('Khar',),
    # 'hasTaiXuanJingSymbols': (,),
    'hasCuneiform': ('Xsux',),
    # 'hasCountingRodNumerals': (,),
    'hasSundanese': ('Sund',),
    'hasLepcha': ('Lepc',),
    'hasOlChiki': ('Olck',),
    'hasSaurashtra': ('Saur',),
    'hasKayahLi': ('Kali',),
    'hasRejang': ('Rjng',),
    'hasCham': ('Cham',),
    # 'hasAncientSymbols': (,),
    # 'hasPhaistosDisc': (,),
    'hasCarianLycianLydian': ('Cari', 'Lyci', 'Lydi'),
    # 'hasDominoMahjong': (,),
    }

IANA_TO_FONTIO_UNIRANGE_MAP = {
    # 'Adlm': (,),  # Adlam
    # 'Afak': (,),  # Afaka
    # 'Aghb': (,),  # Caucasian Albanian
    # 'Ahom': (,),  # Tai Ahom
    'Arab': ('hasArabic|hasBasicArabic',),  # Arabic
    'Aran': ('hasArabic|hasBasicArabic',),  # Arabic (Nastaliq variant)
    # 'Armi': (,),  # Imperial Aramaic
    'Armn': ('hasArmenian',),  # Armenian
    # 'Avst': (,),  # Avestan
    'Bali': ('hasBalinese',),  # Balinese
    # 'Bamu': (,),  # Bamum
    # 'Bass': (,),  # Bassa Vah
    # 'Batk': (,),  # Batak
    'Beng': ('hasBengali',),  # Bengali
    # 'Blis': (,),  # Blissymbols
    'Bopo': ('hasBopomofo',),  # Bopomofo
    # 'Brah': (,),  # Brahmi
    'Brai': ('hasBraille',),  # Braille
    'Bugi': ('hasBuginese',),  # Buginese
    'Buhd': ('hasTagalogEtAl',),  # Buhid
    # 'Cakm': (,),  # Chakma
    'Cans': ('hasUnifiedCanadianAboriginalSyllabics',),  # UCAS
    'Cari': ('hasCarianLycianLydian',),  # Carian
    'Cham': ('hasCham',),  # Cham
    'Cher': ('hasCherokee',),  # Cherokee
    # 'Cirt': (,),  # Cirth
    'Copt': ('hasCoptic|hasGreekAndCoptic|hasGreekSymbolsAndCoptic',),  # Coptic
    'Cprt': ('hasCypriot',),  # Cypriot
    'Cyrl': ('hasCyrillic',),  # Cyrillic
    # 'Cyrs': (,),  # Cyrillic (Old Church Slavonic variant)
    'Deva': ('hasDevanagari',),  # Nagari
    'Dsrt': ('hasDeseret',),  # Mormon
    # 'Dupl': (,),  # Duployan stenography
    # 'Egyd': (,),  # Egyptian demotic
    # 'Egyh': (,),  # Egyptian hieratic
    # 'Egyp': (,),  # Egyptian hieroglyphs
    # 'Elba': (,),  # Elbasan
    'Ethi': ('hasEthiopic',),  # Ge'ez
    'Geok': ('hasBasicGeorgian|hasGeorgian',),  # Khutsuri (Asomtavruli and Nuskhuri)
    'Geor': ('hasBasicGeorgian|hasGeorgian',),  # Georgian (Mkhedruli)
    'Glag': ('hasGlagolitic',),  # Glagolitic
    'Goth': ('hasGothic',),  # Gothic
    # 'Gran': (,),  # Grantha
    'Grek': ('hasBasicGreek|hasGreek|hasGreekAndCoptic',),  # Greek
    'Gujr': ('hasGujarati',),  # Gujarati
    'Guru': ('hasGurmukhi',),  # Gurmukhi
    'Hang': ('hasHangulSyllables',),  # Hangeul
    'Hani': ('hasCJKIdeographs',),  # Hanja
    'Hano': ('hasTagalogEtAl',),  # Hanunoo
    'Hans': ('hasCJKIdeographs',),  # Han (Simplified variant)
    'Hant': ('hasCJKIdeographs',),  # Han (Traditional variant)
    # 'Hatr': (,),  # Hatran
    'Hebr': ('hasBasicHebrew|hasHebrew',),  # Hebrew
    'Hira': ('hasHiragana',),  # Hiragana
    # 'Hluw': (,),  # Hittite Hieroglyphs
    # 'Hmng': (,),  # Pahawh Hmong
    'Hrkt': ('hasHiragana', 'hasKatakana'),  # Japanese Syll.
    # 'Hung': (,),  # Hungarian Runic
    # 'Inds': (,),  # Harappan
    'Ital': ('hasOldItalic',),  # Old Italic (Etruscan, Oscan, etc.)
    # 'Java': (,),  # Javanese
    'Jpan': ('hasCJKIdeographs', 'hasHiragana', 'hasKatakana'),  # Japanese all
    # 'Jurc': (,),  # Jurchen
    'Kali': ('hasKayahLi',),  # Kayah Li
    'Kana': ('hasKatakana',),  # Katakana
    'Khar': ('hasKharoshthi',),  # Kharoshthi
    'Khmr': ('hasKhmer',),  # Khmer
    # 'Khoj': (,),  # Khojki
    # 'Kitl': (,),  # Khitan large script
    # 'Kits': (,),  # Khitan small script
    'Knda': ('hasKannada',),  # Kannada
    'Kore': ('hasCJKIdeographs', 'hasHangulSyllables'),  # Korean ('Hang' + 'Hani')
    # 'Kpel': (,),  # Kpelle
    # 'Kthi': (,),  # Kaithi
    # 'Lana': (,),  # Lanna
    'Laoo': ('hasLao',),  # Lao
    # 'Latf': (,),  # Latin (Fraktur variant)
    # 'Latg': (,),  # Latin (Gaelic variant)
    'Latn': ('hasBasicLatin',),  # Latin
    'Lepc': ('hasLepcha',),  # Rong
    'Limb': ('hasLimbu',),  # Limbu
    # 'Lina': (,),  # Linear A
    'Linb': ('hasLinearB',),  # Linear B
    # 'Lisu': (,),  # Fraser
    # 'Loma': (,),  # Loma
    'Lyci': ('hasCarianLycianLydian',),  # Lycian
    'Lydi': ('hasCarianLycianLydian',),  # Lydian
    # 'Mahj': (,),  # Mahajani
    # 'Mand': (,),  # Mandaean
    # 'Mani': (,),  # Manichaean
    # 'Marc': (,),  # Marchen
    # 'Maya': (,),  # Mayan hieroglyphs
    # 'Mend': (,),  # Mende Kikakui
    # 'Merc': (,),  # Meroitic Cursive
    # 'Mero': (,),  # Meroitic Hieroglyphs
    'Mlym': ('hasMalayalam',),  # Malayalam
    # 'Modi': (,),  # Modi
    'Mong': ('hasMongolian',),  # Mongolian
    # 'Moon': (,),  # Moon type
    # 'Mroo': (,),  # Mru
    # 'Mtei': (,),  # Meetei
    # 'Mult': (,),  # Multani
    'Mymr': ('hasMyanmar',),  # Burmese
    # 'Narb': (,),  # Ancient North Arabian
    # 'Nbat': (,),  # Nabataean
    # 'Nkgb': (,),  # Naxi Geba
    'Nkoo': ('hasNKo',),  # N'Ko
    # 'Nshu': (,),  # Nushu
    'Ogam': ('hasOgham',),  # Ogham
    'Olck': ('hasOlChiki',),  # Santali
    # 'Orkh': (,),  # Orkhon Runic
    'Orya': ('hasOriya',),  # Oriya
    # 'Osge': (,),  # Osage
    'Osma': ('hasOsmanya',),  # Osmanya
    # 'Palm': (,),  # Palmyrene
    # 'Pauc': (,),  # Pau Cin Hau
    # 'Perm': (,),  # Old Permic
    'Phag': ('hasPhagsPa',),  # Phags-pa
    # 'Phli': (,),  # Inscriptional Pahlavi
    # 'Phlp': (,),  # Psalter Pahlavi
    # 'Phlv': (,),  # Book Pahlavi
    'Phnx': ('hasPhoenician',),  # Phoenician
    # 'Plrd': (,),  # Pollard
    # 'Prti': (,),  # Inscriptional Parthian
    # 'Qaaa..Qabx': (,),  # Private use
    'Rjng': ('hasRejang',),  # Kaganga
    # 'Roro': (,),  # Rongorongo
    'Runr': ('hasRunic',),  # Runic
    # 'Samr': (,),  # Samaritan
    # 'Sara': (,),  # Sarati
    # 'Sarb': (,),  # Old South Arabian
    'Saur': ('hasSaurashtra',),  # Saurashtra
    # 'Sgnw': (,),  # SignWriting
    'Shaw': ('hasShavian',),  # Shaw
    # 'Shrd': (,),  # Sarada
    # 'Sidd': (,),  # Siddhamatrka
    # 'Sind': (,),  # Sindhi
    'Sinh': ('hasSinhala',),  # Sinhala
    # 'Sora': (,),  # Sora Sompeng
    'Sund': ('hasSundanese',),  # Sundanese
    'Sylo': ('hasSylotiNagri',),  # Syloti Nagri
    'Syrc': ('hasSyriac',),  # Syriac
    'Syre': ('hasSyriac',),  # Syriac (Estrangelo variant)
    'Syrj': ('hasSyriac',),  # Syriac (Western variant)
    'Syrn': ('hasSyriac',),  # Syriac (Eastern variant)
    'Tagb': ('hasTagalogEtAl',),  # Tagbanwa
    # 'Takr': (,),  # Tankri
    'Tale': ('hasTaiLe',),  # Tai Le
    'Talu': ('hasNewTaiLue',),  # New Tai Lue
    'Taml': ('hasTamil',),  # Tamil
    # 'Tang': (,),  # Tangut
    # 'Tavt': (,),  # Tai Viet
    'Telu': ('hasTelugu',),  # Telugu
    # 'Teng': (,),  # Tengwar
    'Tfng': ('hasTifinagh',),  # Berber
    'Tglg': ('hasTagalogEtAl',),  # Alibata
    'Thaa': ('hasThaana',),  # Thaana
    'Thai': ('hasThai',),  # Thai
    'Tibt': ('hasTibetan',),  # Tibetan
    # 'Tirh': (,),  # Tirhuta
    'Ugar': ('hasUgaritic',),  # Ugaritic
    'Vaii': ('hasVai',),  # Vai
    # 'Visp': (,),  # Visible Speech
    # 'Wara': (,),  # Varang Kshiti
    # 'Wole': (,),  # Woleai
    'Xpeo': ('hasOldPersian',),  # Old Persian
    'Xsux': ('hasCuneiform',),  # Sumero-Akkadian cuneiform
    'Yiii': ('hasYi',),  # Yi
    # 'Zinh': (,),  # Code for inherited script
    'Zmth': ('hasMathematicalAlphanumerics',),  # Mathematical notation
    # 'Zsym': (,),  # Symbols
    # 'Zxxx': (,),  # Code for unwritten documents
    # 'Zyyy': (,),  # Code for undetermined script
    # 'Zzzz': (,),  # Code for uncoded script
    }

REGISTRY_DATE = '2016-02-10'

IANA_VALID_SCRIPT_TAGS = {
  'Adlm', 'Afak', 'Aghb', 'Ahom', 'Arab', 'Aran', 'Armi', 'Armn', 'Avst',
  'Bali', 'Bamu', 'Bass', 'Batk', 'Beng', 'Bhks', 'Blis', 'Bopo', 'Brah',
  'Brai', 'Bugi', 'Buhd', 'Cakm', 'Cans', 'Cari', 'Cham', 'Cher', 'Cirt',
  'Copt', 'Cprt', 'Cyrl', 'Cyrs', 'Deva', 'Dsrt', 'Dupl', 'Egyd', 'Egyh',
  'Egyp', 'Elba', 'Ethi', 'Geok', 'Geor', 'Glag', 'Goth', 'Gran', 'Grek',
  'Gujr', 'Guru', 'Hanb', 'Hang', 'Hani', 'Hano', 'Hans', 'Hant', 'Hatr',
  'Hebr', 'Hira', 'Hluw', 'Hmng', 'Hrkt', 'Hung', 'Inds', 'Ital', 'Jamo',
  'Java', 'Jpan', 'Jurc', 'Kali', 'Kana', 'Khar', 'Khmr', 'Khoj', 'Kitl',
  'Kits', 'Knda', 'Kore', 'Kpel', 'Kthi', 'Lana', 'Laoo', 'Latf', 'Latg',
  'Latn', 'Leke', 'Lepc', 'Limb', 'Lina', 'Linb', 'Lisu', 'Loma', 'Lyci',
  'Lydi', 'Mahj', 'Mand', 'Mani', 'Marc', 'Maya', 'Mend', 'Merc', 'Mero',
  'Mlym', 'Modi', 'Mong', 'Moon', 'Mroo', 'Mtei', 'Mult', 'Mymr', 'Narb',
  'Nbat', 'Newa', 'Nkgb', 'Nkoo', 'Nshu', 'Ogam', 'Olck', 'Orkh', 'Orya',
  'Osge', 'Osma', 'Palm', 'Pauc', 'Perm', 'Phag', 'Phli', 'Phlp', 'Phlv',
  'Phnx', 'Piqd', 'Plrd', 'Prti', 'Qaaa', 'Qaab', 'Qaac', 'Qaad', 'Qaae',
  'Qaaf', 'Qaag', 'Qaah', 'Qaai', 'Qaaj', 'Qaak', 'Qaal', 'Qaam', 'Qaan',
  'Qaao', 'Qaap', 'Qaaq', 'Qaar', 'Qaas', 'Qaat', 'Qaau', 'Qaav', 'Qaaw',
  'Qaax', 'Qaay', 'Qaaz', 'Qaba', 'Qabb', 'Qabc', 'Qabd', 'Qabe', 'Qabf',
  'Qabg', 'Qabh', 'Qabi', 'Qabj', 'Qabk', 'Qabl', 'Qabm', 'Qabn', 'Qabo',
  'Qabp', 'Qabq', 'Qabr', 'Qabs', 'Qabt', 'Qabu', 'Qabv', 'Qabw', 'Qabx',
  'Rjng', 'Roro', 'Runr', 'Samr', 'Sara', 'Sarb', 'Saur', 'Sgnw', 'Shaw',
  'Shrd', 'Sidd', 'Sind', 'Sinh', 'Sora', 'Sund', 'Sylo', 'Syrc', 'Syre',
  'Syrj', 'Syrn', 'Tagb', 'Takr', 'Tale', 'Talu', 'Taml', 'Tang', 'Tavt',
  'Telu', 'Teng', 'Tfng', 'Tglg', 'Thaa', 'Thai', 'Tibt', 'Tirh', 'Ugar',
  'Vaii', 'Visp', 'Wara', 'Wole', 'Xpeo', 'Xsux', 'Yiii', 'Zmth', 'Zsye',
  'Zsym'}

SCRIPTLANGTAG_PATTERN_STRING = r'^(((?P<language>([A-Za-z]{2,3}-)(?P<extlang>([A-Za-z]{3})-)?|([A-Za-z]{4})-|([A-Za-z]{5,8})-)?((?P<script>[A-Za-z]{4}))(-(?P<region>[A-Za-z]{2}|[0-9]{3}))?(-(?P<variant>[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*(-(?P<extension>[0-9A-WY-Za-wy-z](-[A-Za-z0-9]{2,8})+))*(-(?P<privateUse>x(-[A-Za-z0-9]{1,8})+))?))$'

SCRIPTLANGTAG_PATTERN = re.compile(SCRIPTLANGTAG_PATTERN_STRING)

# -----------------------------------------------------------------------------

#
# Functions
#


def scriptfromscriptlangtag(slt):
    """
    Extract the Script component of a ScriptLangTag using a regex or none if
    invalid pattern/Script not present.
    
    >>> scriptfromscriptlangtag('en-Latn')
    'Latn'
    >>> scriptfromscriptlangtag('foo-bar-baz')
    """
    
    pmatch = SCRIPTLANGTAG_PATTERN.match(slt)
    
    if pmatch and 'script' in pmatch.groupdict():
        return pmatch.group('script')
    else:
        return None

def generatevalidscriptset():
    """
    Generate a REGISTRY_DATE and IANA_VALID_SCRIPT_TAGS Python code, suitable
    for copy/paste above.
    
    >>> generatevalidscriptset()
    REGISTRY_DATE = ...
    """
    
    sdict = parseregistry(typefilter=['script'])
    sset = set(sdict['script'])
    sset -= {'Qaaa..Qabx', 'Zinh', 'Zyyy', 'Zxxx', 'Zzzz'}

    privates = set()
    
    for let3 in range(ord('a'), ord('c')):
        for let4 in range(ord('a'), ord('z')+1):
            chr3 = chr(let3)
            chr4 = chr(let4)
            
            if chr3 == 'b' and chr4 in ['y', 'z']:
                pass
            else:
                privates.update(['Qa%s%s' % (chr3, chr4)])

    sset.update(privates)
    ssetstr = ", ".join(["'" + s + "'" for s in sorted(sset)])
    print("REGISTRY_DATE = '%s'\n" % (sdict['date']))
    print("IANA_VALID_SCRIPT_TAGS = {\n%s}" % (ssetstr,))

def parseregistry(typefilter=None, usedescription=False):
    """
    Download and parse the IANA language subtag registry CSV file from
    http://www.iana.org/assignments/language-subtag-registry/language-subtag-
    registry

    This is meant to be called offline (not at runtime) for building the
    IANA_VALID_SCRIPT_TAGS constant above.
    """

    regurl = "/".join([
      'http:/',
      'www.iana.org',
      'assignments',
      'language-subtag-registry',
      'language-subtag-registry'])

    regtxt = str(urllib.request.urlopen(regurl).read(), 'utf-8')
    blocks = regtxt.split("%%")
    tagdict = {'date': blocks.pop(0).split(":")[1].strip()}

    for block in blocks:
        entries = block.strip().split('\n')
        entrydict = {}
        
        for entry in entries:
            if ': ' in entry:
                key, val = entry.split(': ')
                entrydict[key] = val

        taglist = tagdict.get(entrydict['Type'], set())

        if 'Tag' in entrydict:
            tagval = entrydict.get('Tag')
        else:
            tagval = entrydict.get('Subtag')

        if usedescription:
            tagval += " - " + entrydict.get('Description', "")

        if typefilter is None or entrydict['Type'] in typefilter:
            taglist.update((tagval,))
            tagdict[entrydict['Type']] = taglist
    
    return tagdict

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)

if __name__ == "__main__":
    if __debug__:
        _test()

