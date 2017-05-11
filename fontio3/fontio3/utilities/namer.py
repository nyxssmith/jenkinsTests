#
# namer.py
#
# Copyright © 2009-2010, 2012-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for converting between glyph indices, ``'post'``, ``'CFF '``, or
``'Zapf'`` names, Unicodes, and Unicode names. Also support for obtaining
VTT-style Character Group Names.
"""

# System imports
import unicodedata

# Other imports
from fontio3 import utilities, utilitiesbackend

from fontio3.utilities.groupnames import (
  _defaultNameToGroup,
  _defaultUnicodeToGroup)

# -----------------------------------------------------------------------------

#
# Constants
#

PFX_UNI = ('u ', 'u+', '0x', '\\u')
PFX_GID = ('# ', '\#')

# -----------------------------------------------------------------------------

#
# Classes
#

class Namer:
    """
    A Namer is an object that can convert between various designations for a
    particular glyph index.
        
    :param editor: An Editor-class object
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
    These keyword arguments are supported:
    
    ``annotate``
        Default is False. If True, whatever name is returned will have a
        parenthetical note with the glyph index (unless it's simply a
        string version of the glyph index being returned).
    
    ``remapAFII``
        Default is False. If True, and a ``'post'`` name is present but starts
        with the string ``'afii'``, then an alternate name will be used
        instead.
                        
    ``useFontWorkerName``
        Default is False. If True, glyph name will be returned as first
        available of: ``'post'`` name, ``'CFF '`` name, ``u HHHH`` (Unicode),
        or ``# NNNNN`` (glyph id).
    
    ``useUnicodeName``
        Default is False. If True, the Unicode name will be used if
        available, and if the ``'post'`` and/or ``'Zapf'`` names are not
        available.
    """
    
    #
    # Methods
    #
    
    def __init__(self, editor, **kwArgs):
        self.annotate = kwArgs.get('annotate', False)
        self.remapAFII = kwArgs.get('remapAFII', False)
        self.useFontWorkerName = kwArgs.get('useFontWorkerName', False)
        self.useUnicodeName = kwArgs.get('useUnicodeName', False)
        self.editor = editor
        self._initialized = False
    
    def _makeMaps(self):
        """
        Creates the ``'post'`` and Unicode maps, if not already done.
        
        >>> d = {'remapAFII': False, 'useUnicodeName': False, 'annotate': False}
        >>> nNone = Namer(None, **d)
        >>> nNone._makeMaps()
        """
        
        #>>> a = fontedit.Editor()
        #>>> currentDir = os.getcwd()
        #>>> pathFont1 = os.path.join( currentDir,'qe','testfontdata','AdPro.ttf')
        #>>> pathFont2 = os.path.join( currentDir,'qe','testfontdata','BlackmoorStd.otf')
        #>>> pathFont3 = os.path.join( currentDir,'qe','testfontdata','NotoSansGujarati_VTT.ttf')
        #>>> pathFont4 = os.path.join( currentDir,'qe','testfontdata','Zapfino.ttf')
        #>>> b1 = a.frompath(pathFont1)
        #>>> b2 = a.frompath(pathFont2)
        #>>> b3 = a.frompath(pathFont3)
        #>>> b4 = a.frompath(pathFont4)
        #>>> nAdProttf = Namer(b1, **d)
        #>>> nAdProttf._makeMaps()
        #>>> nBlackmoorotf = Namer(b2, **d)
        #>>> nBlackmoorotf._makeMaps()
        #>>> nNotoSansGujaratittf = Namer(b3, **d)
        #>>> nNotoSansGujaratittf._makeMaps()
        #>>> nZapfinottf = Namer(b4, **d)
        #>>> nZapfinottf._makeMaps()        
        
        if not self._initialized:
            keySet = (set(self.editor) if self.editor else set())
            
            if b'post' in keySet:
                self._glyphToPost = self.editor.post or {}
            else:
                self._glyphToPost = {}
                
            if b'CFF ' in keySet:
                self._cffCharset = self.editor[b'CFF '].glyphNames or {}
            else:
                self._cffCharset = {}
            
            if self._glyphToPost:
                self._nameToGlyph = self._glyphToPost.getReverseMap()  
            elif self._cffCharset:
                self._nameToGlyph = self._cffCharset.getReverseMap()
            else:
                self._nameToGlyph = {}

            if self.editor and self.editor.reallyHas(b'cmap'):
                uMap = self.editor.cmap.getUnicodeMap()
                self._unicodeToGlyph = uMap
                self._glyphToUnicode = uMap.getReverseMap()
            
            else:
                self._glyphToUnicode = {}
            
            if b'TSI5' in keySet:
                self._TSI5Table = self.editor.TSI5 or {}
            else:
                self._TSI5Table = {}

            if b'Zapf' in keySet:
                self._zapfTable = self.editor.Zapf or {}
            else:
                self._zapfTable = {}
            
            self._initialized = True
    
    def bestGroupForGlyphIndex(self, glyphIndex, **kwArgs):
        """
        Returns a VTT-style Character Group name (string) for glyphIndex.
        
        :param int glyphIndex: The glyph needing a name
        :param kwArgs: Optional keyword arguments (none currently used)
        :return: The group name
        :rtype: str
        
        Preferred order of obtaining names:
        
        - TSI5 table if present
        - glyphname-to-group mapping (from groupnames.py)
        - unicode-to-group mapping (groupnames.py)

        >>> d = {'remapAFII': False, 'useUnicodeName': False, 'annotate': False}
        >>> f = testingNamer(**d).bestGroupForGlyphIndex
        >>> f(10), f(77), f(95), f(99), f(300)
        ('CustomGroupName', 'LowerCase', 'LowerCase', 'LowerCase', 'AnyGroup')
        """
    
        if glyphIndex is None:
            return None
        
        self._makeMaps()

        if glyphIndex in self._TSI5Table:
            return self._TSI5Table[glyphIndex]

        glyphname = self.bestNameForGlyphIndex(glyphIndex)
        
        if glyphname in _defaultNameToGroup:
            return _defaultNameToGroup[glyphname]

        u = self._glyphToUnicode.get(glyphIndex, None)
        
        if u in _defaultUnicodeToGroup:
            return _defaultUnicodeToGroup[u]

        return 'AnyGroup'
    
    def bestNameForGlyphIndex(self, glyphIndex, **kwArgs):
        """
        Finds the best name for a glyph.
        
        :param int glyphIndex: The glyph needing a name
        :param kwArgs: Optional keyword arguments (none currently used)
        :return: The best name for the specified glyph
        :rtype: str
        
        The name will be obtained from the first source found in the following
        prioritized list:
        
        - ``'Zapf'`` name
        - ``'post'`` name
        - Unicode name (if enabled and Unicode is present)
        - U+nnnn or U+nnnnnn name (if Unicode is present)
        - The glyph index as a string
        
        >>> d = {'remapAFII': False, 'useUnicodeName': False, 'annotate': False}
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> f(10), f(77), f(95), f(99), f(300)
        ('xyz11', 'xyz78', 'afii60000', 'U+0163', '300')
        
        >>> d['useUnicodeName'] = True
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> f(10), f(77), f(95), f(99)
        ('xyz11', 'xyz78', 'afii60000', 'LATIN SMALL LETTER T WITH CEDILLA')
        
        >>> d['remapAFII'] = True
        >>> d['useUnicodeName'] = False
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> f(10), f(77), f(95), f(99)
        ('xyz11', 'xyz78', 'U+015F', 'U+0163')
        
        >>> d['useUnicodeName'] = True
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> f(10), f(77), f(95), f(99)
        ('xyz11', 'xyz78', 'LATIN SMALL LETTER S WITH CEDILLA', 'LATIN SMALL LETTER T WITH CEDILLA')
        
        >>> d = {'remapAFII': False, 'useUnicodeName': False, 'annotate': True}
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(10), f(77), f(95), f(99), f(300)): print(s)
        xyz11 (glyph 10)
        xyz78 (glyph 77)
        afii60000 (glyph 95)
        U+0163 (glyph 99)
        300
        
        >>> d['useUnicodeName'] = True
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(10), f(77), f(95), f(99)): print(s)
        xyz11 (glyph 10)
        xyz78 (glyph 77)
        afii60000 (glyph 95)
        LATIN SMALL LETTER T WITH CEDILLA (glyph 99)
        
        >>> d['remapAFII'] = True
        >>> d['useUnicodeName'] = False
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(10), f(77), f(95), f(99)): print(s)
        xyz11 (glyph 10)
        xyz78 (glyph 77)
        U+015F (glyph 95)
        U+0163 (glyph 99)
        
        >>> d['useUnicodeName'] = True
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(10), f(77), f(95), f(99)): print(s)
        xyz11 (glyph 10)
        xyz78 (glyph 77)
        LATIN SMALL LETTER S WITH CEDILLA (glyph 95)
        LATIN SMALL LETTER T WITH CEDILLA (glyph 99)

        >>> d = {'useFontWorkerName': True}
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(10), f(95), f(99), f(500)): print(s)
        xyz11
        afii60000
        u 0163
        # 500

        >>> f = CFFtestingNamer().bestNameForGlyphIndex
        >>> for s in (f(5), f(10)): print(s)        
        cff5
        cff10

        >>> f = CFFtestingNamer(annotate=True, useUnicodeName=True).bestNameForGlyphIndex
        >>> for s in (f(49), f(50)): print(s)
        cff49 (glyph 49)
        LATIN CAPITAL LETTER R (glyph 50)
        
        >>> f = CFFtestingNamer().bestNameForGlyphIndex
        >>> f(None)
        
        >>> d['useUnicodeName'] = False
        >>> f = testingNamer(**d).bestNameForGlyphIndex
        >>> for s in (f(65535), f(65536), f(65537), f(65534), f(65533)): print(s)
        # 65535
        # 65536
        # 65537
        # 65534
        # 65533
        >>> d = {'remapAFII': False, 'useUnicodeName': False, 'annotate': False}
        """
        
        #>>> a = fontedit.Editor()
        #>>> currentDir = os.getcwd()
        #>>> pathFont4 = os.path.join( currentDir,'qe','testfontdata','Zapfino.ttf')
        #>>> b4 = a.frompath(pathFont4)
        #>>> nZapfinottf = Namer(b4, **d)
        #>>> nZapfinottf.bestNameForGlyphIndex(79)
        #'S.4'
        #>>> d['useUnicodeName']= True
        #>>> nZapfinottf = Namer(b4, **d)
        #>>> nZapfinottf.bestNameForGlyphIndex(34)
        #'H.3'
        #>>> d['useFontWorkerName']= True
        #>>> nZapfinottf = Namer(b4, **d)
        #>>> nZapfinottf.bestNameForGlyphIndex(65339)
        #'# 65339'
        
        if glyphIndex is None:
            return None
        
        if self.useFontWorkerName:
            self.annotate = False
            self.remapAFII = False
            self.useUnicodeName = False
            
        self._makeMaps()
        uNameFromZapf = None
        annotation = (" (glyph %d)" % (glyphIndex,) if self.annotate else "")
        
        if glyphIndex in self._zapfTable:
            kn = self._zapfTable[glyphIndex].kindNames
            
            if kn:
                s = kn.bestName()
                
                if s is not None:
                    return "%s%s" % (s, annotation)
                    
        if glyphIndex in self._cffCharset:
            b = self._cffCharset[glyphIndex]
            s = str(utilities.ensureUnicode(b))

            if not (self.remapAFII and s.startswith('afii')):
                return "%s%s" % (s, annotation)
        
        if glyphIndex in self._glyphToPost:
            s = self._glyphToPost[glyphIndex]
            
            if not (self.remapAFII and s.startswith('afii')):
                return "%s%s" % (s, annotation)
        
        if glyphIndex not in self._glyphToUnicode:
            if self.useFontWorkerName:
                return "# %d" % (glyphIndex,)

            return str(glyphIndex)
        
        u = self._glyphToUnicode[glyphIndex]
        
        if self.useUnicodeName:
            try:
                s = unicodedata.name(chr(u), None)
            
            except ValueError:  # unichr(0x10001) fails in narrow builds...
                bs = utilitiesbackend.utPack('L', u)
                s = unicodedata.name(str(bs, 'utf-32be'), None)
            
            if s is not None:
                return "%s%s" % (s, annotation)

        if self.useFontWorkerName:
            if u <= 0xFFFF:
                return "u %04X" % (u,)
            
            return "u %X" % (u,)
        
        if u <= 0xFFFF:
            return "U+%04X%s" % (u, annotation)
        
        return "U+%06X%s" % (u, annotation)
    
    def glyphIndexFromString(self, s, **kwArgs):
        """
        Get a glyph index corresponding to a string.
        
        :param str s: The name of the glyph
        :param kwArgs: Optional keyword arguments (none currently used)
        :return: The glyph index, or None
        :rtype: int or None
        
        >>> d = {}
        >>> n = testingNamer(**d)
        >>> n.glyphIndexFromString('xyz2')
        1
        >>> n.glyphIndexFromString('# 123')  # out-of-range; None
        >>> n.glyphIndexFromString('u 0105')
        5
        >>> n.glyphIndexFromString('7725')
        """
        
        self._makeMaps()
        
        # try glyph name first
        if s in self._nameToGlyph:
            return self._nameToGlyph[s]
        
        # try as glyph id
        if s[:2] in PFX_GID:
            try:
                i = int(s[2:])
            except ValueError:
                return None
            
            if self.editor:
                if 0 <= i < self.editor.maxp.numGlyphs:
                    return i
            
            return None
        
        # try as Unicode
        if s[:2].lower() in PFX_UNI:
            try:
                u = int(s[2:], 16)
            except ValueError:
                return None

            return self._unicodeToGlyph.get(u, None)
            
        # that's all, folks...
        return None

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def testingNamer(**kwArgs):
        """
        Returns a Namer object without an editor backing it. Its
        characteristics are as follows:
        
        - Supports glyphs 0 through 99 (except 77; see below)
        - Unicodes are glyph codes plus 0x100
        - Postnames are "xyz1" through "xyz95" and "afii60000"
          through "afii60003"
        - Glyph 99 has no post name
        - Glyph 77 has no Unicode
        """
        
        n = Namer(None, **kwArgs)
        p = {}
        u = {}
        fmt1 = "xyz%d"
        fmt2 = "afii6000%d"
        
        for g in range(100):
            if g != 77:
                u[g] = g + 0x100
            
            if g < 95:
                p[g] = fmt1 % (g + 1,)
            elif g < 99:
                p[g] = fmt2 % (g - 95)
        
        n._glyphToPost = p
        n._glyphToUnicode = u
        n._unicodeToGlyph = {v:k for k,v in list(u.items())}
        n._zapfTable = {}
        n._cffCharset = {}
        n._nameToGlyph = {v:k for k,v in list(p.items())}
        n._TSI5Table = {10:'CustomGroupName', 77:'LowerCase'}
        n._initialized = True
        return n
        
    def CFFtestingNamer(**kwArgs):
        """
        Returns a namer object without an editor backing it for testing the
        glyphnames-from-CFF scenario, without breaking the existing tests (CFF
        fonts are presumed to only derive glyph names from the ``'CFF '`` table,
        not from the ``'post'`` table, and the namer logic supports this
        assumption).
        """
        
        n = Namer(None, **kwArgs)
        n._cffCharset = {k:"cff%d" % (k,) for k in range(50)}
        n._glyphToPost = {k:"post%d" % (k,) for k in range(50)}
        n._glyphToUnicode = {k:k+32 for k in range(100)}
        n._zapfTable = {}
        n._initialized = True
        return n

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
