#
# classtable.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from glyph to class for 'mort' tables (specifically the
state table portions; noncontextual mappings are handled separately).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pf(p, value, label, **kwArgs):
    if value != "Out of bounds":
        p.simple(value, label=label, **kwArgs)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    allValues = set(obj.values())
    
    if (not obj) or (allValues == {"Out of bounds"}):
        logger.warning((
          'V0670',
          (),
          "Class table empty or only maps to 'Out of bounds'."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ClassTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing class mappings as used in 'mort' subtables. These are
    dicts mapping glyph indices to class name strings.
    
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
    
    >>> logger = utilities.makeDoctestLogger("classtable")
    >>> e = utilities.fakeEditor(97)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    classtable - WARNING - Class table empty or only maps to 'Out of bounds'.
    True
    
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    classtable.[97] - ERROR - Glyph index 97 too large.
    classtable.[98] - ERROR - Glyph index 98 too large.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintfunc = _pf,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ClassTable object to the specified writer.
        The following keyword arguments are used:
        
            classDict       A dict mapping class names to their corresponding
                            numeric values. This is required.
        
        >>> h = utilities.hexdump
        >>> cd = {s: i for i, s in enumerate(_testNames())}
        >>> h(_testingValues[1].binaryString(classDict=cd))
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
        f = self.get
        it = range(minGlyph, maxGlyph + 1)
        w.addGroup("B", (cd[f(i, "Out of bounds")] for i in it))
        w.alignToByteMultiple(2)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable object from the specified walker.
        The following keyword arguments are used:
        
            classNames      A sequence whose indices are class index numbers
                            and whose values are the associated class name
                            strings. This is required.
            
            logger          A logger to which messages will be posted.
        
        >>> v = _testNames()
        >>> cd = {s: i for i, s in enumerate(_testNames())}
        >>> s = _testingValues[1].binaryString(classDict=cd)
        >>> logger = utilities.makeDoctestLogger("classtable_fvw")
        >>> fvb = ClassTable.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, classNames=v)
        classtable_fvw.classtable - DEBUG - Walker has 14 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:3], logger=logger, classNames=v)
        classtable_fvw.classtable - DEBUG - Walker has 3 remaining bytes.
        classtable_fvw.classtable - ERROR - Insufficient bytes.
        
        >>> fvb(s[:7], logger=logger, classNames=v)
        classtable_fvw.classtable - DEBUG - Walker has 7 remaining bytes.
        classtable_fvw.classtable - ERROR - The class table records are missing or incomplete.
        """
        
        cn = kwArgs['classNames']
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
        
        if w.length() < nGlyphs:
            logger.error((
              'V0669',
              (),
              "The class table records are missing or incomplete."))
            
            return None
        
        return cls({
          firstGlyph + i: cn[x]
          for i, x in enumerate(w.group("B", nGlyphs))
          if x != 1})
    
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
        >>> cd = {s: i for i, s in enumerate(_testNames())}
        >>> obj == ClassTable.frombytes(
        ...   obj.binaryString(classDict=cd),
        ...   classNames = v)
        True
        """
        
        cm = kwArgs['classNames']
        firstGlyph, nGlyphs = w.unpack("2H")
        
        return cls({
          firstGlyph + i: cm[x]
          for i, x in enumerate(w.group("B", nGlyphs))
          if x != 1})

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
          for i, k in enumerate([4, 1, 1, 1, 3, 1, 4, 4, 5])
          if k != 1}))
    
    del v

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
