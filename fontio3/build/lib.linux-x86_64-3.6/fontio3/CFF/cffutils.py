#
# cffutils.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utility data and functions for CFF.
"""

from fontio3.utilitiesbackend import utPack

# -----------------------------------------------------------------------------

#
# Constants
#

topDictOperators = {
    0: ('version', 'SID'),
    1: ('notice', 'SID'),
    (12, 0): ('copyright', 'SID'),
    2: ('fullName', 'SID'),
    3: ('familyName', 'SID'),
    4: ('weight', 'SID'),
    (12, 1): ('isFixedPitch', 'boolean'),
    (12, 2): ('italicAngle', 'number'),
    (12, 3): ('underlinePosition', 'number'),
    (12, 4): ('underlineThickness', 'number'),
    (12, 5): ('paintType', 'number'),
    (12, 6): ('charstringType', 'number'),
    (12, 7): ('fontMatrix', 'array'),
    13: ('uniqueID', 'number'),
    5: ('fontBBox', 'array'),
    (12, 8): ('strokeWidth', 'number'),
    14: ('xuid', 'array'),
    15: ('charset', 'number'),
    16: ('encoding', 'number'),
    17: ('charStrings', 'number'),
    18: ('private', 'number2'),
    (12, 20): ('syntheticBase', 'number'),
    (12, 21): ('postScript', 'SID'),
    (12, 22): ('baseFontName', 'SID'),
    (12, 23): ('baseFontBlend', 'delta'),
    (12, 30): ('ros', 'SIDSIDnumber'),
    (12, 31): ('cidFontVersion', 'number'),
    (12, 32): ('cidFontRevision', 'number'),
    (12, 33): ('cidFontType', 'number'),
    (12, 34): ('cidCount', 'number'),
    (12, 35): ('uidBase', 'number'),
    (12, 36): ('fdArray', 'number'),
    (12, 37): ('fdSelect', 'number'),
    (12, 38): ('fontName', 'SID')}
    
topDictLabelDict = {v[0]: (k, v[1]) for k,v in list(topDictOperators.items())}

privateDictOperators = {
    6: ('BlueValues', 'delta'),
    7: ('OtherBlues', 'delta'),
    8: ('FamilyBlues', 'delta'),
    9: ('FamilyOtherBlues', 'delta'),
    (12, 9): ('BlueScale', 'number'),
    (12, 10): ('BlueShift', 'number'),
    (12, 11): ('BlueFuzz', 'number'),
    10: ('StdHW', 'number'),
    11: ('StdVW', 'number'),
    (12, 12): ('StemSnapH', 'delta'),
    (12, 13): ('StemSnapV', 'delta'),
    (12, 14): ('ForceBold', 'boolean'),
    (12, 17): ('LanguageGroup', 'number'),
    (12, 18): ('ExpansionFactor', 'number'),
    (12, 19): ('initialRandomSeed', 'number'),
    19: ('Subrs', 'number'),
    20: ('defaultWidthX', 'number'),
    21: ('nominalWidthX', 'number')}
    
privateDictLabelDict = {v[0]: (k, v[1]) for k,v in list(privateDictOperators.items())}

stdStrings = ('.notdef', 'space', 'exclam', 'quotedbl', 'numbersign', 'dollar',
    'percent', 'ampersand', 'quoteright', 'parenleft', 'parenright',
    'asterisk', 'plus', 'comma', 'hyphen', 'period', 'slash', 'zero', 'one',
    'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'colon',
    'semicolon', 'less', 'equal', 'greater', 'question', 'at', 'A', 'B', 'C',
    'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
    'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'bracketleft', 'backslash',
    'bracketright', 'asciicircum', 'underscore', 'quoteleft', 'a', 'b', 'c',
    'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
    's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'braceleft', 'bar', 'braceright',
    'asciitilde', 'exclamdown', 'cent', 'sterling', 'fraction', 'yen',
    'florin', 'section', 'currency', 'quotesingle', 'quotedblleft',
    'guillemotleft', 'guilsinglleft', 'guilsinglright', 'fi', 'fl', 'endash',
    'dagger', 'daggerdbl', 'periodcentered', 'paragraph', 'bullet',
    'quotesinglbase', 'quotedblbase', 'quotedblright', 'guillemotright',
    'ellipsis', 'perthousand', 'questiondown', 'grave', 'acute', 'circumflex',
    'tilde', 'macron', 'breve', 'dotaccent', 'dieresis', 'ring', 'cedilla',
    'hungarumlaut', 'ogonek', 'caron', 'emdash', 'AE', 'ordfeminine', 'Lslash',
    'Oslash', 'OE', 'ordmasculine', 'ae', 'dotlessi', 'lslash', 'oslash', 'oe',
    'germandbls', 'onesuperior', 'logicalnot', 'mu', 'trademark', 'Eth',
    'onehalf', 'plusminus', 'Thorn', 'onequarter', 'divide', 'brokenbar',
    'degree', 'thorn', 'threequarters', 'twosuperior', 'registered', 'minus',
    'eth', 'multiply', 'threesuperior', 'copyright', 'Aacute', 'Acircumflex',
    'Adieresis', 'Agrave', 'Aring', 'Atilde', 'Ccedilla', 'Eacute',
    'Ecircumflex', 'Edieresis', 'Egrave', 'Iacute', 'Icircumflex', 'Idieresis',
    'Igrave', 'Ntilde', 'Oacute', 'Ocircumflex', 'Odieresis', 'Ograve',
    'Otilde', 'Scaron', 'Uacute', 'Ucircumflex', 'Udieresis', 'Ugrave',
    'Yacute', 'Ydieresis', 'Zcaron', 'aacute', 'acircumflex', 'adieresis',
    'agrave', 'aring', 'atilde', 'ccedilla', 'eacute', 'ecircumflex',
    'edieresis', 'egrave', 'iacute', 'icircumflex', 'idieresis', 'igrave',
    'ntilde', 'oacute', 'ocircumflex', 'odieresis', 'ograve', 'otilde',
    'scaron', 'uacute', 'ucircumflex', 'udieresis', 'ugrave', 'yacute',
    'ydieresis', 'zcaron', 'exclamsmall', 'Hungarumlautsmall',
    'dollaroldstyle', 'dollarsuperior', 'ampersandsmall', 'Acutesmall',
    'parenleftsuperior', 'parenrightsuperior', 'twodotenleader',
    'onedotenleader', 'zerooldstyle', 'oneoldstyle', 'twooldstyle',
    'threeoldstyle', 'fouroldstyle', 'fiveoldstyle', 'sixoldstyle',
    'sevenoldstyle', 'eightoldstyle', 'nineoldstyle', 'commasuperior',
    'threequartersemdash', 'periodsuperior', 'questionsmall', 'asuperior',
    'bsuperior', 'centsuperior', 'dsuperior', 'esuperior', 'isuperior',
    'lsuperior', 'msuperior', 'nsuperior', 'osuperior', 'rsuperior',
    'ssuperior', 'tsuperior', 'ff', 'ffi', 'ffl', 'parenleftinferior',
    'parenrightinferior', 'Circumflexsmall', 'hyphensuperior', 'Gravesmall',
    'Asmall', 'Bsmall', 'Csmall', 'Dsmall', 'Esmall', 'Fsmall', 'Gsmall',
    'Hsmall', 'Ismall', 'Jsmall', 'Ksmall', 'Lsmall', 'Msmall', 'Nsmall',
    'Osmall', 'Psmall', 'Qsmall', 'Rsmall', 'Ssmall', 'Tsmall', 'Usmall',
    'Vsmall', 'Wsmall', 'Xsmall', 'Ysmall', 'Zsmall', 'colonmonetary',
    'onefitted', 'rupiah', 'Tildesmall', 'exclamdownsmall', 'centoldstyle',
    'Lslashsmall', 'Scaronsmall', 'Zcaronsmall', 'Dieresissmall', 'Brevesmall',
    'Caronsmall', 'Dotaccentsmall', 'Macronsmall', 'figuredash',
    'hypheninferior', 'Ogoneksmall', 'Ringsmall', 'Cedillasmall',
    'questiondownsmall', 'oneeighth', 'threeeighths', 'fiveeighths',
    'seveneighths', 'onethird', 'twothirds', 'zerosuperior', 'foursuperior',
    'fivesuperior', 'sixsuperior', 'sevensuperior', 'eightsuperior',
    'ninesuperior', 'zeroinferior', 'oneinferior', 'twoinferior',
    'threeinferior', 'fourinferior', 'fiveinferior', 'sixinferior',
    'seveninferior', 'eightinferior', 'nineinferior', 'centinferior',
    'dollarinferior', 'periodinferior', 'commainferior', 'Agravesmall',
    'Aacutesmall', 'Acircumflexsmall', 'Atildesmall', 'Adieresissmall',
    'Aringsmall', 'AEsmall', 'Ccedillasmall', 'Egravesmall', 'Eacutesmall',
    'Ecircumflexsmall', 'Edieresissmall', 'Igravesmall', 'Iacutesmall',
    'Icircumflexsmall', 'Idieresissmall', 'Ethsmall', 'Ntildesmall',
    'Ogravesmall', 'Oacutesmall', 'Ocircumflexsmall', 'Otildesmall',
    'Odieresissmall', 'OEsmall', 'Oslashsmall', 'Ugravesmall', 'Uacutesmall',
    'Ucircumflexsmall', 'Udieresissmall', 'Yacutesmall', 'Thornsmall',
    'Ydieresissmall', '001.000', '001.001', '001.002', '001.003', 'Black',
    'Bold', 'Book', 'Light', 'Medium', 'Regular', 'Roman', 'Semibold')

nStdStrings = len(stdStrings)

dStdStrings = {el:i for i,el in enumerate(stdStrings)}


# -----------------------------------------------------------------------------

#
# Functions
#

def resolvesid(sid, fontstrings, **kwArgs):
    """
    Resolve an SID number to a Python string using stdStrings and
    supplied fontstrings.
    
    >>> t = resolvesid(5, [])
    >>> resolvestring(t, []) == 5
    True
    >>> fs = ['test1', 'test2', 'test3']
    >>> t = resolvesid(nStdStrings + 1, fs)
    >>> resolvestring(t, fs) == nStdStrings+1
    True
    """
    if sid < nStdStrings:
        return stdStrings[sid]
    else:
        fsid = sid - nStdStrings
        if fontstrings is not None and fsid < len(fontstrings):
            return fontstrings[fsid]
        else:
            return "UnknownSID%d" % (fsid,)


def resolvestring(s, fontstrings, **kwArgs):
    """
    Resolve a Python string to a SID using the supplied fontstrings.
    Note that fontstrings may be modified (appended) if 's' is not in
    either stdStrings or fontstrings.
    
    >>> fs = []
    >>> n = resolvestring('foo', fs)
    >>> resolvesid(n, fs) == 'foo'
    True
    """
    sid = dStdStrings.get(s, None)
    
    if sid is None:
        if s not in fontstrings: fontstrings.append(s)
        sid = nStdStrings + fontstrings.index(s)
        
    return sid

def pack_t2_number(n, w, **kwArgs):

        """
        Pack (add) 'n' to writer 'w' using Type2 Charstring Number Encoding.
        """

        dbg = kwArgs.get('debug', False)
 
        if isinstance(n, float):
            if dbg: print(("packing float %f" % (n,)))
            w.add("Bl", 255, int(n*65536.0))
            return

        if -107 <= n <= 107:
            if dbg: print(("packing 1-byte int %d" % (n,)))
            w.add("B", n+139) 

        elif 108 <= n <= 1131:
            if dbg: print(("packing 2-byte int %d" % (n,)))
            ns = n - 108
            b0 = (ns/256) + 247
            b1 = (ns%256)
            w.add("BB", b0, b1)
    
        elif -1131 <= n <= -108:
            if dbg: print(("packing negative 2-byte int %d" % (n,)))
            ns = -(n + 108)
            b0 = (ns/256) + 251
            b1 = (ns%256)
            w.add("BB", b0, b1)  

        elif -32768 <= n <= 32767:
            if dbg: print(("packing 3-byte int %d" % (n,)))
            w.add("Bh", 28, n)        


# -----------------------------------------------------------------------------

#
# Classes
#

class WriteIndexValue(object):
    """
    A callable class which returns packed binary string for a number. The size
    (format) of the number is dependent upon self.format. An instance is used
    for writer.addUnresolvedOffset where we are building the offset stakes
    before we know the actual lengths of the values in the INDEX.
    
    The instance's .maxoffset should be updated prior to .buildBinary being called.    
    """
    def __init__(self):
        self.maxoffset = 16777217 # default to largest, 4 bytes

    def __call__(self, n):
        if self.maxoffset < 256: return utPack("B", n)
        elif self.maxoffset < 65536: return utPack("H", n)
        elif self.maxoffset < 16777216: return utPack("T", n)
        else: return utPack("I", n)
        
    def numBytes(self):
        if self.maxoffset < 256: return 1
        elif self.maxoffset < 65536: return 2
        elif self.maxoffset < 16777216: return 3
        else: return 4

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

