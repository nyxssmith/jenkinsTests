#
# classtable.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from glyph to class for 'kern' tables.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class ClassTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing class mappings as used in format 1 'kern' tables.
    These are dicts mapping glyph indices to class name strings.
    
    >>> _testingValues[1].pprint()
    90: Vowel
    94: End of line
    96: Vowel
    97: Vowel
    98: Consonant
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60001: Vowel
    afii60002: Vowel
    afii60003: Consonant
    xyz91: Vowel
    xyz95: End of line
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(200)
    >>> obj = ClassTable({800: "My class", 801: 802})
    >>> obj.isValid(logger=logger, editor=e)
    val.[800] - ERROR - Glyph index 800 too large.
    val.[801] - ERROR - Glyph index 801 too large.
    val.[801] - ERROR - The class name 802 is not a Unicode string.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatefunc = functools.partial(
          valassist.isString,
          label = "class name"))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ClassTable object to the specified writer.
        The following keyword arguments are used:
        
            classDict       A dict mapping class names to their corresponding
                            numeric values. This is required.
        
        >>> cd = {s: i for i, s in enumerate(_testNames())}
        >>> utilities.hexdump(_testingValues[1].binaryString(classDict=cd))
               0 | 005A 0009 0401 0101  0301 0404 0500      |.Z............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        minGlyph = min(self)
        maxGlyph = max(self)
        count = maxGlyph - minGlyph + 1
        cd = kwArgs['classDict']
        w.add("2H", minGlyph, count)
        
        v = [
          (cd[self[i]] if i in self else 1)
          for i in range(minGlyph, maxGlyph + 1)]
        
        w.addGroup("B", v)
        w.alignToByteMultiple(2)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable object from the specified walker,
        doing source validation. The following keyword arguments are used:
        
            classNames      A sequence whose indices are class index numbers
                            and whose values are the associated class name
                            strings. This is required.
            
            fontGlyphCount  The number of glyphs in the font. This is required.
            
            logger          A Logger to which messages will be posted.
        
        >>> cn = _testNames()
        >>> cd = {s: i for i, s in enumerate(cn)}
        >>> s = _testingValues[1].binaryString(classDict=cd)
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = ClassTable.fromvalidatedbytes
        >>> d = {'logger': logger, 'classNames': cn, 'fontGlyphCount': 900}
        >>> obj = fvb(s, **d)
        fvw.classtable - DEBUG - Walker has 14 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:2], **d)
        fvw.classtable - DEBUG - Walker has 2 remaining bytes.
        fvw.classtable - ERROR - Insufficient bytes.
        
        >>> fvb(utilities.fromhex("E5 00 00 09") + s[4:], **d)
        fvw.classtable - DEBUG - Walker has 14 remaining bytes.
        fvw.classtable - ERROR - The first glyph index (58624) plus the glyph count (9) exceeds the total number of glyphs in the font (900).
        
        >>> fvb(s[:6], **d)
        fvw.classtable - DEBUG - Walker has 6 remaining bytes.
        fvw.classtable - ERROR - The class values are missing or incomplete.
        """
        
        cm = kwArgs['classNames']
        fgc = kwArgs['fontGlyphCount']
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("classtable")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        firstGlyph, nGlyphs = w.unpack("2H")
        
        if firstGlyph + nGlyphs >= fgc:
            logger.error((
              'V0631',
              (firstGlyph, nGlyphs, fgc),
              "The first glyph index (%d) plus the glyph count (%d) exceeds "
              "the total number of glyphs in the font (%d)."))
            
            return None
        
        if w.length() < nGlyphs:
            logger.error((
              'V0632',
              (),
              "The class values are missing or incomplete."))
            
            return None
        
        data = w.group("B", nGlyphs)
        r = cls()
        
        if data[0] == 1 or data[-1] == 1:
            logger.warning((
              'V0633',
              (),
              "The class values start and/or end with the out-out-bounds "
              "value. This wastes space."))
        
        for i, x in enumerate(data):
            if x == 1:
                continue  # don't need explicit out-of-bounds entries
            
            r[firstGlyph + i] = cm[x]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable object from the specified walker.
        The following keyword arguments are used:
        
            classNames      A sequence whose indices are class index numbers
                            and whose values are the associated class name
                            strings. This is required.
        
        >>> obj = _testingValues[1]
        >>> v = _testNames()
        >>> cd = {s: i for i, s in enumerate(v)}
        >>> obj == ClassTable.frombytes(
        ...   obj.binaryString(classDict=cd),
        ...   classNames = v)
        True
        """
        
        cm = kwArgs['classNames']
        firstGlyph, nGlyphs = w.unpack("2H")
        r = cls()
        
        for i, x in enumerate(w.group("B", nGlyphs)):
            if x == 1:
                continue  # don't need explicit out-of-bounds entries
            
            r[firstGlyph + i] = cm[x]
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    def _testNames():
        return [
          "End of text",
          "Out of bounds",
          "Deleted glyph",
          "End of line",
          "Vowel",
          "Consonant"]
    
    v = _testNames()
    
    _testingValues = (
        ClassTable(),
        
        ClassTable({
          i + 90: v[k]
          for i, k in enumerate([4,1,1,1,3,1,4,4,5])
          if k != 1}))
    
    del v

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
