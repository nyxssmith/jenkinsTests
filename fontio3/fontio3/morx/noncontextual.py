#
# noncontextual.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 4 (noncontextual, or swash) 'mort' subtables.
"""

# Other imports
from fontio3 import utilities
from fontio3.morx import coverage
from fontio3.utilities import lookup
from fontio3.statetables import subtable_glyph_coverage_set

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_mask(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0667',
          (),
          "Swash table is empty and will have no effect."))
    
    idempotents = set(k for k, v in obj.items() if k == v)
    
    if idempotents:
        logger.warning((
          'V0668',
          (sorted(idempotents),),
          "The following glyphs map to themselves: %s"))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Noncontextual(lookup.Lookup_OutGlyph):
    """
    Objects representing format 4 (noncontextual, or swash) 'mort' subtables.
    These are dicts mapping input glyphs to output glyphs. There are two
    attributes:
    
        coverage        A Coverage object (q.v.)
        
        maskValue       The arbitrarily long integer value with the subFeature
                        mask bits for this subtable.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz16: afii60002
    xyz17: afii60003
    Mask value: 08000000
    Coverage:
      Subtable kind: 4
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz23: xyz41
    xyz26: xyz20
    xyz81: U+0163
    Mask value: 0004000000000000
    Coverage:
      Subtable kind: 4
    
    >>> logger = utilities.makeDoctestLogger("swash")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    swash - WARNING - Swash table is empty and will have no effect.
    True
    
    >>> obj = _testingValues[1].__deepcopy__()
    >>> obj.update({24: 24, 19: 19, 80: 80})
    >>> obj.isValid(logger=logger, editor=e)
    swash - WARNING - The following glyphs map to themselves: [19, 24, 80]
    True
    
    >>> s = _testingValues[2].binaryString()
    >>> logger = utilities.makeDoctestLogger("swash_fvw")
    >>> fvb = Noncontextual.fromvalidatedbytes
    >>> d = {
    ...   'logger': logger,
    ...   'coverage': _testingValues[2].coverage,
    ...   'maskValue': _testingValues[2].maskValue}
    >>> obj = fvb(s, **d)
    swash_fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
    swash_fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
    >>> obj == _testingValues[2]
    True
    
    >>> fvb(s[:3], **d)
    swash_fvw.lookup_aat - DEBUG - Walker has 3 remaining bytes.
    swash_fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 1 remaining bytes.
    swash_fvw.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.
    
    >>> fvb(s[:13], **d)
    swash_fvw.lookup_aat - DEBUG - Walker has 13 remaining bytes.
    swash_fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 11 remaining bytes.
    swash_fvw.lookup_aat - ERROR - The data for the format 6 Lookup are missing or incomplete.
    
    >>> obj = _testingValues[1]
    >>> cv = obj.coverage.__deepcopy__()
    >>> ms = obj.maskValue
    >>> obj == Noncontextual.frombytes(
    ...   obj.binaryString(),
    ...   coverage = cv,
    ...   maskValue = ms)
    True
    
    >>> obj = _testingValues[2]
    >>> cv = obj.coverage.__deepcopy__()
    >>> ms = obj.maskValue
    >>> obj == Noncontextual.frombytes(
    ...   obj.binaryString(),
    ...   coverage = cv,
    ...   maskValue = ms)
    True
    
    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 0008 000F 0002 0061  0062                |.......a.b      |
    
    >>> utilities.hexdump(_testingValues[2].binaryString())
           0 | 0006 0004 0003 0008  0001 0004 0016 0028 |...............(|
          10 | 0019 0013 0050 0063  FFFF FFFF           |.....P.c....    |
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectvalues = True,
        item_valueisoutputglyph = True,
        map_maxcontextfunc = (lambda obj: 2),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        maskValue = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 1),
            attr_label = "Mask value",
            attr_pprintfunc = _pprint_mask),
        
        coverage = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: coverage.Coverage(kind=4)),
            attr_label = "Coverage"),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    
    attrSorted = ('maskValue', 'coverage', 'glyphCoverageSet')
    kind = 4  # class constant
    
    #
    # Methods
    #
    
    @classmethod
    def fromgsubsingle(cls, singleObj, **kwArgs):
        """
        Creates and returns a new Noncontextual object from the specified GSUB
        Single object.
        """
        
        return cls(singleObj, **utilities.filterKWArgs(cls, kwArgs))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Noncontextual object from the specified
        walker, doing data validation.
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        d = lookup.Lookup.fromvalidatedwalker(w, **kwArgs)
        
        if d is None:
            return None
        
        r.update(d)
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Noncontextual object from the specified
        walker.
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        r.update(lookup.Lookup.fromwalker(w, **kwArgs))
        return r
    
    def run(self, glyphArray, **kwArgs):
        """
        Given an input sequence of either glyph indices or (sequence index,
        glyph index) pairs, process them and return a new sequence of (original
        sequence index, output glyph) pairs. The following keyword arguments
        are used:
        
            startIndex      Index in glyphArray where processing is to start.
                            Note that the output sequence will always have the
                            same length as the input sequence; this parameter
                            only controls where substitution starts. Default is
                            0.
        
        >>> print(_testingValues[1].run([14, 15, 16, 17]))
        [(0, 14), (1, 97), (2, 98), (3, 17)]
        >>> print(_testingValues[1].run([14, 15, 16, 17], startIndex=2))
        [(0, 14), (1, 15), (2, 98), (3, 17)]
        """
        
        if not glyphArray:
            return []
        
        if not isinstance(glyphArray[0], tuple):
            r = list(enumerate(glyphArray))
        else:
            r = list(glyphArray)
        
        for i in range(kwArgs.get('startIndex', 0), len(r)):
            if r[i][1] in self:
                r[i] = (r[i][0], self[r[i][1]])
        
        return r

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Noncontextual_allowFakeGlyphs(Noncontextual):
    """
    This class is essentially the same as the regular Noncontextual class, but
    it permits fake glyphs as keys or values.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_allowfakeglyphkeys = True,
        item_allowfakeglyphvalues = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Noncontextual(),
        Noncontextual({15: 97, 16: 98}, maskValue=0x08000000),
        Noncontextual({22: 40, 25: 19, 80: 99}, maskValue=0x0004000000000000))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
