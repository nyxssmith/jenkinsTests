#
# scriptutilities.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities for checking script & language tag registration and updating list of
registered tags from Microsoft OpenType spec.
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

LAST_SCRAPE_DATE = '2016-04-06'

OT_VALID_SCRIPT_TAGS = {
    b'adlm', b'ahom', b'hluw', b'arab', b'armn', b'avst', b'bali', b'bamu',
    b'bass', b'batk', b'beng', b'bng2', b'bhks', b'bopo', b'brah', b'brai',
    b'bugi', b'buhd', b'byzm', b'cans', b'cari', b'aghb', b'cakm', b'cham',
    b'cher', b'hani', b'copt', b'cprt', b'cyrl', b'DFLT', b'dsrt', b'deva',
    b'dev2', b'dupl', b'egyp', b'elba', b'ethi', b'geor', b'glag', b'goth',
    b'gran', b'grek', b'gujr', b'gjr2', b'guru', b'gur2', b'hang', b'jamo',
    b'hano', b'hatr', b'hebr', b'kana', b'armi', b'phli', b'prti', b'java',
    b'kthi', b'knda', b'knd2', b'kana', b'kali', b'khar', b'khmr', b'khoj',
    b'sind', b'lao ', b'latn', b'lepc', b'limb', b'lina', b'linb', b'lisu',
    b'lyci', b'lydi', b'mahj', b'marc', b'mlym', b'mlm2', b'mand', b'mani',
    b'math', b'mtei', b'mend', b'merc', b'mero', b'plrd', b'modi', b'mong',
    b'mroo', b'mult', b'musc', b'mymr', b'mym2', b'nbat', b'newa', b'talu',
    b'nko ', b'orya', b'ory2', b'ogam', b'olck', b'ital', b'hung', b'narb',
    b'perm', b'xpeo', b'sarb', b'orkh', b'osge', b'osma', b'hmng', b'palm',
    b'pauc', b'phag', b'phnx', b'phlp', b'rjng', b'runr', b'samr', b'saur',
    b'shrd', b'shaw', b'sidd', b'sgnw', b'sinh', b'sora', b'xsux', b'sund',
    b'sylo', b'syrc', b'tglg', b'tagb', b'tale', b'lana', b'tavt', b'takr',
    b'taml', b'tml2', b'tang', b'telu', b'tel2', b'thaa', b'thai', b'tibt',
    b'tfng', b'tirh', b'ugar', b'vai ', b'wara', b'yi  '}

OT_VALID_LANG_TAGS = {
    b'ABA ', b'ABK ', b'ACH ', b'ACR ', b'ADY ', b'AFK ', b'AFR ', b'AGW ',
    b'AIO ', b'AKA ', b'ALS ', b'ALT ', b'AMH ', b'ANG ', b'APPH', b'ARA ',
    b'ARG ', b'ARI ', b'ARK ', b'ASM ', b'AST ', b'ATH ', b'AVR ', b'AWA ',
    b'AYM ', b'AZB ', b'AZE ', b'BAD ', b'BAD0', b'BAG ', b'BAL ', b'BAN ',
    b'BAR ', b'BAU ', b'BBC ', b'BBR ', b'BCH ', b'BCR ', b'BDY ', b'BEL ',
    b'BEM ', b'BEN ', b'BGC ', b'BGQ ', b'BGR ', b'BHI ', b'BHO ', b'BIK ',
    b'BIL ', b'BIS ', b'BJJ ', b'BKF ', b'BLI ', b'BLK ', b'BLN ', b'BLT ',
    b'BMB ', b'BML ', b'BOS ', b'BPY ', b'BRE ', b'BRH ', b'BRI ', b'BRM ',
    b'BRX ', b'BSH ', b'BTI ', b'BTS ', b'BUG ', b'CAK ', b'CAT ', b'CBK ',
    b'CEB ', b'CHE ', b'CHG ', b'CHH ', b'CHI ', b'CHK ', b'CHK0', b'CHO ',
    b'CHP ', b'CHR ', b'CHA ', b'CHU ', b'CHY ', b'CGG ', b'CMR ', b'COP ',
    b'COR ', b'COS ', b'CPP ', b'CRE ', b'CRR ', b'CRT ', b'CSB ', b'CSL ',
    b'CSY ', b'CTG ', b'CUK ', b'DAN ', b'DAR ', b'DAX ', b'DCR ', b'DEU ',
    b'DGO ', b'DGR ', b'DHG ', b'DHV ', b'DIQ ', b'DIV ', b'DJR ', b'DJR0',
    b'DNG ', b'DNJ ', b'DNK ', b'DRI ', b'DUJ ', b'DUN ', b'DZN ', b'EBI ',
    b'ECR ', b'EDO ', b'EFI ', b'ELL ', b'EMK ', b'ENG ', b'ERZ ', b'ESP ',
    b'ESU ', b'ETI ', b'EUQ ', b'EVK ', b'EVN ', b'EWE ', b'FAN ', b'FAN0',
    b'FAR ', b'FAT ', b'FIN ', b'FJI ', b'FLE ', b'FNE ', b'FON ', b'FOS ',
    b'FRA ', b'FRC ', b'FRI ', b'FRL ', b'FRP ', b'FTA ', b'FUL ', b'FUV ',
    b'GAD ', b'GAE ', b'GAG ', b'GAL ', b'GAR ', b'GAW ', b'GEZ ', b'GIH ',
    b'GIL ', b'GIL0', b'GKP ', b'GLK ', b'GMZ ', b'GNN ', b'GOG ', b'GON ',
    b'GRN ', b'GRO ', b'GUA ', b'GUC ', b'GUF ', b'GUJ ', b'GUZ ', b'HAI ',
    b'HAL ', b'HAR ', b'HAU ', b'HAW ', b'HAY ', b'HAZ ', b'HBN ', b'HER ',
    b'HIL ', b'HIN ', b'HMA ', b'HMN ', b'HMO ', b'HND ', b'HO  ', b'HRI ',
    b'HRV ', b'HUN ', b'HYE ', b'HYE0', b'IBA ', b'IBB ', b'IBO ', b'IJO ',
    b'IDO ', b'ILE ', b'ILO ', b'INA ', b'IND ', b'ING ', b'INU ', b'IPK ',
    b'IPPH', b'IRI ', b'IRT ', b'ISL ', b'ISM ', b'ITA ', b'IWR ', b'JAM ',
    b'JAN ', b'JAV ', b'JBO ', b'JII ', b'JUD ', b'JUL ', b'KAB ', b'KAB0',
    b'KAC ', b'KAL ', b'KAN ', b'KAR ', b'KAT ', b'KAZ ', b'KDE ', b'KEA ',
    b'KEB ', b'KEK ', b'KGE ', b'KHA ', b'KHK ', b'KHM ', b'KHS ', b'KHT ',
    b'KHV ', b'KHW ', b'KIK ', b'KIR ', b'KIS ', b'KIU ', b'KJD ', b'KJP ',
    b'KKN ', b'KLM ', b'KMB ', b'KMN ', b'KMO ', b'KMS ', b'KNR ', b'KOD ',
    b'KOH ', b'KOK ', b'KON ', b'KOM ', b'KON0', b'KOP ', b'KOR ', b'KOS ',
    b'KOZ ', b'KPL ', b'KRI ', b'KRK ', b'KRL ', b'KRM ', b'KRN ', b'KRT ',
    b'KSH ', b'KSH0', b'KSI ', b'KSM ', b'KSW ', b'KUA ', b'KUI ', b'KUL ',
    b'KUM ', b'KUR ', b'KUU ', b'KUY ', b'KYK ', b'KYU ', b'LAD ', b'LAH ',
    b'LAK ', b'LAM ', b'LAO ', b'LAT ', b'LAZ ', b'LCR ', b'LDK ', b'LEZ ',
    b'LIJ ', b'LIM ', b'LIN ', b'LIS ', b'LJP ', b'LKI ', b'LMA ', b'LMB ',
    b'LMO ', b'LMW ', b'LOM ', b'LRC ', b'LSB ', b'LSM ', b'LTH ', b'LTZ ',
    b'LUA ', b'LUB ', b'LUG ', b'LUH ', b'LUO ', b'LVI ', b'MAD ', b'MAG ',
    b'MAH ', b'MAJ ', b'MAK ', b'MAL ', b'MAM ', b'MAN ', b'MAP ', b'MAR ',
    b'MAW ', b'MBN ', b'MCH ', b'MCR ', b'MDE ', b'MDR ', b'MEN ', b'MER ',
    b'MFE ', b'MIN ', b'MIZ ', b'MKD ', b'MKR ', b'MKW ', b'MLE ', b'MLG ',
    b'MLN ', b'MLR ', b'MLY ', b'MND ', b'MNG ', b'MNI ', b'MNK ', b'MNX ',
    b'MOH ', b'MOK ', b'MOL ', b'MON ', b'MOR ', b'MOS ', b'MRI ', b'MTH ',
    b'MTS ', b'MUN ', b'MUS ', b'MWL ', b'MWW ', b'MYN ', b'MZN ', b'NAG ',
    b'NAH ', b'NAN ', b'NAP ', b'NAS ', b'NAU ', b'NAV ', b'NCR ', b'NDB ',
    b'NDC ', b'NDG ', b'NDS ', b'NEP ', b'NEW ', b'NGA ', b'NGR ', b'NHC ',
    b'NIS ', b'NIU ', b'NKL ', b'NKO ', b'NLD ', b'NOE ', b'NOG ', b'NOR ',
    b'NOV ', b'NSM ', b'NSO ', b'NTA ', b'NTO ', b'NYM ', b'NYN ', b'OCI ',
    b'OCR ', b'OJB ', b'ORI ', b'ORO ', b'OSS ', b'PAA ', b'PAG ', b'PAL ',
    b'PAM ', b'PAN ', b'PAP ', b'PAP0', b'PAS ', b'PAU ', b'PCC ', b'PCD ',
    b'PDC ', b'PGR ', b'PHK ', b'PIH ', b'PIL ', b'PLG ', b'PLK ', b'PMS ',
    b'PNB ', b'POH ', b'PON ', b'PRO ', b'PTG ', b'PWO ', b'QIN ', b'QUC ',
    b'QUH ', b'QUZ ', b'QVI ', b'QWH ', b'RAJ ', b'RAR ', b'RBU ', b'RCR ',
    b'REJ ', b'RIA ', b'RIF ', b'RIT ', b'RKW ', b'RMS ', b'RMY ', b'ROM ',
    b'ROY ', b'RSY ', b'RTM ', b'RUA ', b'RUN ', b'RUP ', b'RUS ', b'SAD ',
    b'SAN ', b'SAS ', b'SAT ', b'SAY ', b'SCN ', b'SCO ', b'SEK ', b'SEL ',
    b'SGA ', b'SGO ', b'SGS ', b'SHI ', b'SHN ', b'SIB ', b'SID ', b'SIG ',
    b'SKS ', b'SKY ', b'SLA ', b'SLV ', b'SML ', b'SMO ', b'SNA ', b'SNA0',
    b'SND ', b'SNH ', b'SNK ', b'SOG ', b'SOP ', b'SOT ', b'SQI ', b'SRB ',
    b'SRD ', b'SRK ', b'SRR ', b'SSL ', b'SSM ', b'STQ ', b'SUK ', b'SUN ',
    b'SUR ', b'SVA ', b'SVE ', b'SWA ', b'SWK ', b'SWZ ', b'SXT ', b'SXU ',
    b'SYL ', b'SYR ', b'SZL ', b'TAB ', b'TAJ ', b'TAM ', b'TAT ', b'TCR ',
    b'TDD ', b'TEL ', b'TET ', b'TGL ', b'TGN ', b'TGR ', b'TGY ', b'THA ',
    b'THT ', b'TIB ', b'TIV ', b'TKM ', b'TMH ', b'TMN ', b'TNA ', b'TNE ',
    b'TNG ', b'TOD ', b'TOD0', b'TPI ', b'TRK ', b'TSG ', b'TUA ', b'TUL ',
    b'TUV ', b'TVL ', b'TWI ', b'TYZ ', b'TZM ', b'TZO ', b'UDM ', b'UKR ',
    b'UMB ', b'URD ', b'USB ', b'UYG ', b'UZB ', b'VEC ', b'VEN ', b'VIT ',
    b'VOL ', b'VRO ', b'WA  ', b'WAG ', b'WAR ', b'WCR ', b'WEL ', b'WLN ',
    b'WLF ', b'XBD ', b'XHS ', b'XJB ', b'XOG ', b'XPE ', b'YAK ', b'YAO ',
    b'YAP ', b'YBA ', b'YCR ', b'YIC ', b'YIM ', b'ZEA ', b'ZGH ', b'ZHA ',
    b'ZHH ', b'ZHP ', b'ZHS ', b'ZHT ', b'ZND ', b'ZUL ', b'ZZA '}

URL_SCRIPTTAG_REG = 'http://www.microsoft.com/typography/otspec/scripttags.htm'

URL_LANGTAG_REG = 'http://www.microsoft.com/typography/otspec/languagetags.htm'

# -----------------------------------------------------------------------------

#
# Classes
#

class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self._td_count = 0
        self._td_depth = 0
        self.opentype_tags = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self._td_count = 0
            self._td_depth = 0
        elif tag == 'td':
            self._td_count += 1
            self._td_depth += 1

    def handle_endtag(self, tag):
        if tag == 'td':
            self._td_depth -= 1

    def handle_data(self, data):
        if self._td_count == 2 and self._td_depth == 1:
            text = (data.strip() + '    ')[:4]
            self.opentype_tags.append(text)

# -----------------------------------------------------------------------------

#
# Functions
#

def generatevalidscriptset():
    """
    Print LAST_SCRAPE_DATE,  OT_VALID_SCRIPT_TAGS, and OT_VALID_LANG_TAGS in
    form suitable for copy/paste into this file, for updating fontio3 when
    script tag registries are updated.
    """
    
    dstr = datetime.now().strftime("%Y-%m-%d")
    print("LAST_SCRAPE_DATE = '%s'\n" % (dstr,))

    scrtags = parseregistry(URL_SCRIPTTAG_REG)
    tstr = ', '.join("%s" % (t.encode('ascii'),) for t in scrtags)
    print("OT_VALID_SCRIPT_TAGS = {%s}\n" % (tstr,))
    
    langtags = parseregistry(URL_LANGTAG_REG)
    tstr = ', '.join("%s" % (t.encode('ascii'),) for t in langtags)
    print("OT_VALID_LANG_TAGS = {%s}" % (tstr,))

def parseregistry(url):
    """
    Scrape OpenType tags from registry page at supplied url.
    """
    
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'Monotype Font Tools Crawler'})
    
    page = urllib.request.urlopen(request)
    html = page.read()
    page.close()
    parser = MyHTMLParser()
    parser.feed(str(html, 'utf-8'))
    return parser.opentype_tags

def isValidScriptTag(tag, **kwArgs):
    """
    Validate whether a supplied tag is in our set of valid script tags, writing
    results to a logger supplied in kwArgs.
    
    >>> l = utilities.makeDoctestLogger("scriptutilities")
    >>> isValidScriptTag('arab', logger=l)
    scriptutilities - INFO - Script tag 'arab' is a legal tag and appears in the OpenType Script Tag registry.
    True

    >>> isValidScriptTag('foobar', logger=l)
    scriptutilities - ERROR - Script tag 'foobar' is not a legal OpenType script tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False
    
    >>> isValidScriptTag('\x83abc', logger=l)
    scriptutilities - ERROR - Script tag '\x83abc' is not a legal OpenType script tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    >>> isValidScriptTag(' a 2', logger=l)
    scriptutilities - WARNING - Script tag ' a 2' is a legal tag, but does not appear in the OpenType Script Tag registry as of 2016-04-06.
    False
    
    >>> isValidScriptTag(b'latn')
    True
    """
    
    logger = kwArgs.get('logger', None)
    
    if isinstance(tag, str):
        try:
            tag = tag.encode('ascii')
        
        except UnicodeEncodeError:
            logger.error((
              'V1010',
              (tag,),
              "Script tag '%s' is not a legal OpenType script tag (must "
              "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
    
    isLegal = len(tag) == 4 and all(0x20 <= x <= 0x7E for x in tag)
    isRegistered = tag in OT_VALID_SCRIPT_TAGS

    if logger is not None:        
        if not isLegal:
            logger.error((
              'V1010',
              (str(tag, 'ascii'),),
              "Script tag '%s' is not a legal OpenType script tag (must "
              "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
        
        if not isRegistered:
            logger.warning((
              'V1011',
              (str(tag, 'ascii'), LAST_SCRAPE_DATE),
              "Script tag '%s' is a legal tag, but does not appear in the "
              "OpenType Script Tag registry as of %s."))
            
            return False
            
        logger.info((
          'V1012',
          (str(tag, 'ascii'),),
          "Script tag '%s' is a legal tag and appears in the OpenType "
          "Script Tag registry."))
        
        return True
        
    return isLegal and isRegistered

def isValidLangTag(tag, **kwArgs):
    """
    Validate whether a supplied tag is in our set of valid language tags, writing
    results to a logger supplied in kwArgs.
    
    >>> l = utilities.makeDoctestLogger("scriptutilities")
    >>> isValidLangTag('ARA ', logger=l)
    scriptutilities - INFO - Language tag 'ARA ' is a legal tag and appears in the OpenType Language Tag registry.
    True

    >>> isValidLangTag('foobar', logger=l)
    scriptutilities - ERROR - Language tag 'foobar' is not a legal OpenType language tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    >>> isValidLangTag('\x83abc', logger=l)
    scriptutilities - ERROR - Language tag '\x83abc' is not a legal OpenType language tag (must be exactly 4 ASCII characters in range 0x20..0x7E).
    False

    >>> isValidLangTag(' a 2', logger=l)
    scriptutilities - WARNING - Language tag ' a 2' is a legal tag, but does not appear in the OpenType Language Tag registry as of 2016-04-06.
    False
    
    >>> isValidLangTag('ROM ')
    True
    """
    
    logger = kwArgs.get('logger', None)
    
    if isinstance(tag, str):
        try:
            tag = tag.encode('ascii')
        
        except UnicodeEncodeError:
            logger.error((
              'V1010',
              (tag,),
              "Language tag '%s' is not a legal OpenType language tag (must "
              "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
    
    isLegal = len(tag) == 4 and all(0x20 <= x <= 0x7E for x in tag)
    isRegistered = tag in OT_VALID_LANG_TAGS

    if logger is not None:        
        if not isLegal:
            logger.error((
              'V1010',
              (str(tag, 'ascii'),),
              "Language tag '%s' is not a legal OpenType language tag (must "
              "be exactly 4 ASCII characters in range 0x20..0x7E)."))
            
            return False
        
        if not isRegistered:
            logger.warning((
              'V1011',
              (str(tag, 'ascii'), LAST_SCRAPE_DATE),
              "Language tag '%s' is a legal tag, but does not appear in the "
              "OpenType Language Tag registry as of %s."))
            
            return False
            
        logger.info((
          'V1012',
          (str(tag, 'ascii'),),
          "Language tag '%s' is a legal tag and appears in the OpenType "
          "Language Tag registry."))
        
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
