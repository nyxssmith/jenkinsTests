#
# featuresetting.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for (feature, setting) values with meaningful displayed values.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Constants
#

registeredNames = {
    (0, 0): "No features disabled",
    (0, 1): "All features disabled",
    
    (1, 0): "Required ligatures on",
    (1, 1): "Required ligatures off",
    (1, 2): "Common ligatures on",
    (1, 3): "Common ligatures off",
    (1, 4): "Rare ligatures on",
    (1, 5): "Rare ligatures off",
    (1, 6): "Logo ligatures on",
    (1, 7): "Logo ligatures off",
    (1, 8): "Rebus ligatures on",
    (1, 9): "Rebus ligatures off",
    (1, 10): "Diphthong ligatures on",
    (1, 11): "Diphthong ligatures off",
    (1, 12): "Squared ligatures on",
    (1, 13): "Squared ligatures off",
    (1, 14): "Squared abbreviated ligatures on",
    (1, 15): "Squared abbreviated ligatures off",
    (1, 16): "Symbol ligatures on",
    (1, 17): "Symbol ligatures off",
    (1, 18): "Contextual ligatures on",
    (1, 19): "Contextual ligatures off",
    (1, 20): "Historical ligatures on",
    (1, 21): "Historical ligatures off",
    
    (2, 0): "Cursive connection off",
    (2, 1): "Partial cursive connection",
    (2, 2): "Full cursive connection",
    
    (3, 0): "Normal upper/lower case (deprecated)",
    (3, 1): "All caps (deprecated)",
    (3, 2): "All lower case (deprecated)",
    (3, 3): "Small caps (deprecated)",
    (3, 4): "Initial caps (deprecated)",
    (3, 5): "Initial and small caps (deprecated)",
    
    (4, 0): "Vertical substitution on",
    (4, 1): "Vertical substitution off",
    
    (5, 0): "Linguistic rearrangement on",
    (5, 1): "Linguistic rearrangement off",
    
    (6, 0): "Monospaced numerals",
    (6, 1): "Proportional numerals",
    (6, 2): "Third-width numerals",
    (6, 3): "Quarter-width numerals",
    
    # (7, x) is Apple-reserved
    
    (8, 0): "Word-initial swashes on",
    (8, 1): "Word-initial swashes off",
    (8, 2): "Word-finial swashes on",
    (8, 3): "Word-finial swashes off",
    (8, 4): "Line-initial swashes on",
    (8, 5): "Line-initial swashes off",
    (8, 6): "Line-finial swashes on",
    (8, 7): "Line-finial swashes off",
    (8, 8): "Non-finial swashes on",
    (8, 9): "Non-finial swashes off",
    
    (9, 0): "Show diacritics",
    (9, 1): "Hide diacritics",
    (9, 2): "Decompose diacritics",
    
    (10, 0): "Normal vertical position",
    (10, 1): "Superiors",
    (10, 2): "Inferiors",
    (10, 3): "Ordinals",
    (10, 4): "Scientific inferiors",
    
    (11, 0): "No fractions",
    (11, 1): "Nut fractions",
    (11, 2): "Diagonal fractions",
    
    # (12, x) is Apple-reserved
    
    (13, 0): "Prevent overlap",
    (13, 1): "Allow overlap",
    
    (14, 0): "Two hyphens to em-dash",
    (14, 1): "Two hyphens normal",
    (14, 2): "Hyphen to en-dash",
    (14, 3): "Hyphen normal",
    (14, 4): "Un-slashed zero",
    (14, 5): "Slashed zero",
    (14, 6): "?! to interrobang",
    (14, 7): "?! normal",
    (14, 8): "Smart quotes on",
    (14, 9): "Smart quotes off",
    (14, 10): "Three periods to ellipsis",
    (14, 11): "Three periods normal",
    
    (15, 0): "Hyphen to minus",
    (15, 1): "Hyphen normal",
    (15, 2): "Asterisk to multiply",
    (15, 3): "Asterisk normal",
    (15, 4): "Virgule to divide",
    (15, 5): "Virgule normal",
    (15, 6): "Inequality ligatures on",
    (15, 7): "Inequality ligatures off",
    (15, 8): "Exponents on",
    (15, 9): "Exponents off",
    (15, 10): "Mathematical Greek on",
    (15, 11): "Mathematical Greek off",
    
    (16, 0): "No ornaments",
    (16, 1): "Dingbats",
    (16, 2): "Pi characters",
    (16, 3): "Fleurons",
    (16, 4): "Decorative borders",
    (16, 5): "International symbols",
    (16, 6): "Math symbols",
    
    (19, 0): "No style options",
    (19, 1): "Display text",
    (19, 2): "Engraved text",
    (19, 3): "Illuminated caps",
    (19, 4): "Titling caps",
    (19, 5): "Tall caps",
    
    (20, 0): "Traditional characters",
    (20, 1): "Simplified characters",
    (20, 2): "JIS 1978 characters",
    (20, 3): "JIS 1983 characters",
    (20, 4): "JIS 1990 characters",
    (20, 5): "Traditional alternatives (one)",
    (20, 6): "Traditional alternatives (two)",
    (20, 7): "Traditional alternatives (three)",
    (20, 8): "Traditional alternatives (four)",
    (20, 9): "Traditional alternatives (five)",
    (20, 10): "Expert characters",
    (20, 11): "JIS 2004 characters",
    (20, 12): "Hojo characters",
    (20, 13): "NLC characters",
    (20, 14): "Traditional names characters",
    
    (21, 0): "Lower-case numerals",
    (21, 1): "Upper-case numerals",
    
    (22, 0): "Proportional text",
    (22, 1): "Monospaced text",
    (22, 2): "Half-width text",
    (22, 3): "Third-width text",
    (22, 4): "Quarter-width text",
    (22, 5): "Alternate proportional text",
    (22, 6): "Alternate half-width text",
    
    (23, 0): "No transliteration",
    (23, 1): "Hanja to hangul",
    (23, 2): "Hiragana to katakana",
    (23, 3): "Katakana to hiragana",
    (23, 4): "Kana to romaji",
    (23, 5): "Romaji to hiragana",
    (23, 6): "Romaji to katakana",
    (23, 7): "Hanja to hangul alternatives (one)",
    (23, 8): "Hanja to hangul alternatives (two)",
    (23, 9): "Hanja to hangul alternatives (three)",
    
    (24, 0): "No annotation",
    (24, 1): "Box annotation",
    (24, 2): "Rounded box annotation",
    (24, 3): "Circle annotation",
    (24, 4): "Inverted circle annotation",
    (24, 5): "Parenthesis annotation",
    (24, 6): "Period annotation",
    (24, 7): "Roman numeral annotation",
    (24, 8): "Diamond annotation",
    (24, 9): "Inverted box annotation",
    (24, 10): "Inverted rounded box annotation",
    
    (25, 0): "Full-width kana",
    (25, 1): "Proportional kana",
    
    (26, 0): "Full-width ideographs",
    (26, 1): "Proportional ideographs",
    (26, 2): "Half-width ideographs",
    
    (27, 0): "Canonical Unicode composition on",
    (27, 1): "Canonical Unicode composition off",
    (27, 2): "Compatibility Unicode composition on",
    (27, 3): "Compatibility Unicode composition off",
    (27, 4): "Transcoding Unicode composition on",
    (27, 5): "Transcoding Unicode composition off",
    
    (28, 0): "No Ruby (deprecated)",
    (28, 1): "Ruby (deprecated)",
    (28, 2): "Ruby kana on",
    (28, 3): "Ruby kana off",
    
    (29, 0): "No CJK alternate symbols",
    (29, 1): "CJK alternate symbols (one)",
    (29, 2): "CJK alternate symbols (two)",
    (29, 3): "CJK alternate symbols (three)",
    (29, 4): "CJK alternate symbols (four)",
    (29, 5): "CJK alternate symbols (five)",
    
    (30, 0): "No ideographic alternates",
    (30, 1): "Ideographic alternates (one)",
    (30, 2): "Ideographic alternates (two)",
    (30, 3): "Ideographic alternates (three)",
    (30, 4): "Ideographic alternates (four)",
    (30, 5): "Ideographic alternates (five)",
    
    (31, 0): "CJK vertical Latin centered",
    (31, 1): "CJK vertical Latin horiz. baseline",
    
    (32, 0): "No CJK Italic Latin (deprecated)",
    (32, 1): "CJK Italic Latin (deprecated)",
    (32, 2): "CJK Italic Latin on",
    (32, 3): "CJK Italic Latin off",
    
    (33, 0): "Case-sensitive layout on",
    (33, 1): "Case-sensitive layout off",
    (33, 2): "Case-sensitive spacing on",
    (33, 3): "Case-sensitive spacing off",
    
    (34, 0): "Alternate horizontal kana on",
    (34, 1): "Alternate horizontal kana off",
    (34, 2): "Alternate vertical kana on",
    (34, 3): "Alternate vertical kana off",
    
    (35, 0): "No stylistic alternates",
  # (35, 1): this does not exist; Apple appear to be mixing exclusive and non!
    (35, 2): "Stylistic alternates (one) on",
    (35, 3): "Stylistic alternates (one) off",
    (35, 4): "Stylistic alternates (two) on",
    (35, 5): "Stylistic alternates (two) off",
    (35, 6): "Stylistic alternates (three) on",
    (35, 7): "Stylistic alternates (three) off",
    (35, 8): "Stylistic alternates (four) on",
    (35, 9): "Stylistic alternates (four) off",
    (35, 10): "Stylistic alternates (five) on",
    (35, 11): "Stylistic alternates (five) off",
    (35, 12): "Stylistic alternates (six) on",
    (35, 13): "Stylistic alternates (six) off",
    (35, 14): "Stylistic alternates (seven) on",
    (35, 15): "Stylistic alternates (seven) off",
    (35, 16): "Stylistic alternates (eight) on",
    (35, 17): "Stylistic alternates (eight) off",
    (35, 18): "Stylistic alternates (nine) on",
    (35, 19): "Stylistic alternates (nine) off",
    (35, 20): "Stylistic alternates (ten) on",
    (35, 21): "Stylistic alternates (ten) off",
    (35, 22): "Stylistic alternates (eleven) on",
    (35, 23): "Stylistic alternates (eleven) off",
    (35, 24): "Stylistic alternates (twelve) on",
    (35, 25): "Stylistic alternates (twelve) off",
    (35, 26): "Stylistic alternates (thirteen) on",
    (35, 27): "Stylistic alternates (thirteen) off",
    (35, 28): "Stylistic alternates (fourteen) on",
    (35, 29): "Stylistic alternates (fourteen) off",
    (35, 30): "Stylistic alternates (fifteen) on",
    (35, 31): "Stylistic alternates (fifteen) off",
    (35, 32): "Stylistic alternates (sixteen) on",
    (35, 33): "Stylistic alternates (sixteen) off",
    (35, 34): "Stylistic alternates (seventeen) on",
    (35, 35): "Stylistic alternates (seventeen) off",
    (35, 36): "Stylistic alternates (eighteen) on",
    (35, 37): "Stylistic alternates (eighteen) off",
    (35, 38): "Stylistic alternates (nineteen) on",
    (35, 39): "Stylistic alternates (nineteen) off",
    (35, 40): "Stylistic alternates (twenty) on",
    (35, 41): "Stylistic alternates (twenty) off",
    
    (36, 0): "Contextual alternates on",
    (36, 1): "Contextual alternates off",
    (36, 2): "Swash alternates on",
    (36, 3): "Swash alternates off",
    (36, 4): "Contextual swash alternates on",
    (36, 5): "Contextual swash alternates off",
    
    (37, 0): "Default lower-case",
    (37, 1): "Lower-case small caps",
    (37, 2): "Lower-case petite caps",
    
    (38, 0): "Default upper-case",
    (38, 1): "Upper-case small caps",
    (38, 2): "Upper-case petite caps",
    
    (103, 0): "Half-width CJK Latin",
    (103, 1): "Proportional CJK Latin",
    (103, 2): "Default CJK Latin",
    (103, 3): "Full-width CJK Latin"
    }

patternedNames = {
    17: (
      lambda s:
      (("Character alternative %d" % (s,)) if s else "No alternates")),
    
    18: (lambda s: "Design complexity level %d" % (s + 1,)),
    
    39: (lambda s: "Ltag index %d" % (s - 1,))}  # yes, -1

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        f = int(obj[0])
        s = int(obj[1])
    
    except:
        return True  # actual error raised in seqmeta.M_isValid
    
    if f in patternedNames:
        return True
    
    if (f, s) not in registeredNames:
        logger.warning((
          'V0671',
          (f, s),
          "The combination of feature %d and setting %d is not present "
          "in the Apple Font Feature Registry."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureSetting(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a feature/setting combination, as used in 'mort' and
    'morx' tables. These are tuples of two values.
    
    >>> _testingValues[0].pprint()
    Superiors (10, 1)
    
    >>> _testingValues[1].pprint()
    No alternates (17, 0)
    
    >>> _testingValues[2].pprint()
    Character alternative 4 (17, 4)
    
    >>> logger = utilities.makeDoctestLogger("featuresetting")
    >>> e = utilities.fakeEditor(0x1000)
    >>> FeatureSetting([67, 89]).isValid(logger=logger, editor=e)
    featuresetting - WARNING - The combination of feature 67 and setting 89 is not present in the Apple Font Feature Registry.
    True
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        seq_fixedlength = 2,
        seq_pprintfunc = (lambda p,obj,**k: p(str(obj))),
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of the FeatureSetting.
        
        >>> print(_testingValues[0])
        Superiors (10, 1)
        
        >>> print(_testingValues[1])
        No alternates (17, 0)
        
        >>> print(_testingValues[2])
        Character alternative 4 (17, 4)
        """
        
        if self in registeredNames:
            s = registeredNames[self]
        elif self[0] in patternedNames:
            s = patternedNames[self[0]](self[1])
        else:
            s = "Feature"
        
        return "%s (%d, %d)" % (s, self[0], self[1])
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureSetting to the specified writer.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 000A 0001                                |....            |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0011 0000                                |....            |
        
        >>> h(_testingValues[2].binaryString())
               0 | 0011 0004                                |....            |
        """
        
        w.addGroup("H", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureSetting from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("featuresetting_fvw")
        >>> fvb = FeatureSetting.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        featuresetting_fvw.featuresetting - DEBUG - Walker has 4 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:3], logger=logger)
        featuresetting_fvw.featuresetting - DEBUG - Walker has 3 remaining bytes.
        featuresetting_fvw.featuresetting - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("featuresetting")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(w.unpack("2H"))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureSetting from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == FeatureSetting.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == FeatureSetting.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == FeatureSetting.frombytes(obj.binaryString())
        True
        """
        
        return cls(w.unpack("2H"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        FeatureSetting((10, 1)),
        FeatureSetting((17, 0)),
        FeatureSetting((17, 4)),
        
        # FeatureSettings forming a mutually-exclusive grouping
        FeatureSetting((2, 0)),     # cursive off
        FeatureSetting((2, 1)),     # cursive partial
        FeatureSetting((2, 2)),     # cursive full
        
        # FeatureSettings forming on/off pairs
        FeatureSetting((1, 2)),     # common ligs on
        FeatureSetting((1, 3)),     # common ligs off
        FeatureSetting((1, 4)),     # rare ligs on
        FeatureSetting((1, 5)))     # rare ligs off

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
