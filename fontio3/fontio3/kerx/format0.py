#
# format0.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for simple pairwise kerning (in 'kerx' tables).
"""

# System imports
import functools
import logging
import operator
import warnings

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.kerx import coverage, glyphpair
from fontio3.utilities import bsh, valassist
from fontio3.statetables import subtable_glyph_coverage_set


# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    r = True
    
    if editor is None:
        return True
    
    if editor.reallyHas(b'head'):
        upem = editor.head.unitsPerEm
    
    else:
        logger.warning((
          'V0603',
          (),
          "No 'head' table is present, so validation will assume a "
          "units-per-em value of 1000."))
        
        upem = 1000  # if there's no 'head' table, it's probably a CFF font
    
    f = functools.partial(valassist.isFormat_h, label="kerning value")
    
    for key in sorted(obj):
        value = obj[key]
        itemLogger = logger.getChild("[%s]" % (key,))
        
        if not f(value, logger=itemLogger):
            r = False
        
        elif not value:
            itemLogger.warning((
              'V0141',
              (key,),
              "The kerning value for %s is zero."))
        
        elif abs(value) >= upem:
            itemLogger.warning((
              'V0604',
              (value,),
              "The kerning value of %s seems excessive."))
        
    return r

def _validate_tupleIndex(obj, **kwArgs):
    if obj is None:
        return True
    
    if not valassist.isNumber_integer_unsigned(obj, numBits=16, **kwArgs):
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format0(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing format 0 'kern' tables. These are dicts mapping
    GlyphPair objects to FUnit values. There are two attributes:
    
        coverage        A Coverage object.
        
        tupleIndex      If the coverage indicates variation data are present,
                        this will be a tuple index for variation kerning.
    
    Note that older versions of the the online Apple documenation for this
    format specified 4 16-bit values per record. This is incorrect, and John
    Jenkins has stated he will fix it (private email 13-May-2016).
    
    >>> _testingValues[1].pprint()
    GlyphPair((14, 23)): -25
    GlyphPair((14, 96)): -30
    GlyphPair((18, 38)): 12
    Header information:
      Horizontal
      With-stream
      No variation kerning
      Process forward
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    (xyz15, afii60001): -30
    (xyz15, xyz24): -25
    (xyz19, xyz39): 12
    Header information:
      Horizontal
      With-stream
      No variation kerning
      Process forward
    
    >>> obj = _testingValues[1].__deepcopy__()
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = _fakeEditor(0x1000)
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj[glyphpair.GlyphPair([5000, -20])] = 0
    >>> obj[glyphpair.GlyphPair([19, 20])] = 10000
    >>> obj.isValid(logger=logger, editor=e)
    val.[(19, 20)] - WARNING - The kerning value of 10000 seems excessive.
    val.[(5000, -20)] - WARNING - The kerning value for (5000, -20) is zero.
    val.[(5000, -20)].[0] - ERROR - Glyph index 5000 too large.
    val.[(5000, -20)].[1] - ERROR - The glyph index -20 cannot be used in an unsigned field.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_keyfollowsprotocol = True,
        item_scaledirectvalues = True,
        item_usenamerforstr = True,
        map_compactremovesfalses = True,
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        coverage = dict(
            attr_followsprotocol = True,
            attr_label = "Header information"),
        
        tupleIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Variations tuple index",
            attr_showonlyiffuncobj = (lambda t,obj: obj.coverage.variation),
            attr_validatefunc = _validate_tupleIndex),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    attrSorted = ('coverage', 'tupleIndex', 'glyphCoverageSet')

    format = 0  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter. The following keyword options are supported:
        
            addSentinel     Default is False. If True, a (0xFFFF, 0xFFFF, 0)
                            entry will be added after the last real entry.
        
        >>> obj = _testingValues[1]
        >>> h = utilities.hexdump
        >>> h(obj.binaryString())
               0 | 0000 0003 0000 000C  0000 0001 0000 0006 |................|
              10 | 000E 0017 FFE7 000E  0060 FFE2 0012 0026 |.........`.....&|
              20 | 000C                                     |..              |
        
        >>> h(obj.binaryString(addSentinel=True))
               0 | 0000 0003 0000 000C  0000 0001 0000 0006 |................|
              10 | 000E 0017 FFE7 000E  0060 FFE2 0012 0026 |.........`.....&|
              20 | 000C FFFF FFFF 0000                      |........        |
        """
        
        w.addString(bsh.binsearchheader(len(self), 6, use32Bits=True))
        it = sorted(self.items(), key=operator.itemgetter(0))
        
        for (g1, g2), value in it:
            w.add("2Hh", g1, g2, value)
        
        if kwArgs.get('addSentinel', False):
            w.add("3h", -1, -1, 0)  # sentinel at end, not counted in nUnits
    
    @classmethod
    def fromformat2(cls, f2):
        """
        Creates and returns a new Format0 object derived from the specified
        Format2 object.
        """
        
        assert f2.format == 2
        r = cls({}, coverage=f2.coverage, tupleIndex=f2.tupleIndex)
        invLeft = utilities.invertDictFull(f2.leftClassDef, asSets=True)
        invRight = utilities.invertDictFull(f2.rightClassDef, asSets=True)
        
        for key2, value2 in f2.items():
            leftClass, rightClass = key2
            for leftGlyph in invLeft.get(leftClass, []):
                for rightGlyph in invRight.get(rightClass, []):
                    r[GlyphPair([leftGlyph, rightGlyph])] = value2
        
        return r
    
    @classmethod
    def fromgpospairs(cls, pgObj, **kwArgs):
        """
        Creates and returns a new Format0 object from the specified PairGlyphs
        object. If there are any keys whose associated Values cannot be
        converted, they will be shown in a ValueError raised by this method.
        
        The following keyword arguments are used:
        
            coverage        A Coverage object. If not provided, a default
                            Coverage will be created and used.
            
            tupleIndex      The variations tuple index. Default is 0.
        """
        
        if 'coverage' not in kwArgs:
            kwArgs['coverage'] = coverage.Coverage()
        
        if 'tupleIndex' not in kwArgs:
            kwArgs['tupleIndex'] = 0
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        couldNotProcess = set()
        horizontal = not kwArgs['coverage'].vertical
        GP = glyphpair.GlyphPair
        
        for gposKey, gposValue in pgObj.items():
            fmt0Key = GP(gposKey)
            gposFirst = gposValue.first
            gposMask1 = (0 if gposFirst is None else gposFirst.getMask())
            gposSecond = gposValue.second
            gposMask2 = (0 if gposSecond is None else gposSecond.getMask())
            delta = 0
            
            # We only process effects that move the glyphs internally. That
            # means any Values that use anything other than an advance shift
            # on the first glyph or an origin shift on the second are not
            # processed, and their keys will be added to couldNotProcess.
            
            if horizontal:
                if gposMask1 == 4:  # xAdvance
                    delta += gposFirst.xAdvance
                
                elif gposMask1:
                    couldNotProcess.add(gposKey)
                    continue
                
                if gposMask2 == 1:  # xPlacement
                    delta += gposSecond.xPlacement
                
                elif gposMask2:
                    couldNotProcess.add(gposKey)
                    continue
            
            else:
                if gposMask1 == 8:  # yAdvance
                    delta += gposFirst.yAdvance
                
                elif gposMask1:
                    couldNotProcess.add(gposKey)
                    continue
                
                if gposMask2 == 2:  # yPlacement
                    delta += gposSecond.yPlacement
                
                elif gposMask2:
                    couldNotProcess.add(gposKey)
                    continue
            
            if delta:
                r[fmt0Key] = delta
        
        if couldNotProcess:
            v = sorted(couldNotProcess)
            raise ValueError("Could not process these GPOS keys: %s" % (v,))
        
        return r
    
    @classmethod
    def fromkern_format0(cls, k0, **kwArgs):
        """
        Creates and returns a Format0 object from the data in the specified
        fontio3.kern.format0.Format0 object.
        
        >>> Format0.fromkern_format0(_k0()[1]).pprint()
        GlyphPair((14, 23)): -25
        GlyphPair((14, 96)): -30
        GlyphPair((18, 38)): 12
        Header information:
          Horizontal
          With-stream
          No variation kerning
          Process forward
        """
        
        r = cls(
          {},
          coverage = coverage.Coverage.fromkern_coverage(k0.coverage),
          tupleIndex = 0)
        
        GP = glyphpair.GlyphPair
        
        for t, n in k0.items():
            r[GP(t)] = n
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format0 object from the specified walker, doing
        source validation. The walker should start at the subtable header. The
        following keyword arguments are suggested (if they are not present, the
        default values for coverage and tupleIndex will be used, which won't
        usually be what's wanted).
        
        NOTE: see the docstring for the Format0 class for a discussion of
        record formats.
        
            coverage    A Coverage object.
            logger      A logger to which messages will be posted.
            tupleIndex  The variations tuple index.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format0")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("L12x")
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        if count:
            if w.length() < 6 * count:
                logger.error(('V0004', (), "Insufficient bytes for array."))
                return None
            
            data = w.group("2Hh", count)
            GP = glyphpair.GlyphPair
            
            for *t, value in data:
                key = GP(t)
                
                if key in r:
                    if value == r[key]:
                        logger.warning((
                          'V0770',
                          (key,),
                          "A duplicate key %s was found."))
                    
                    else:
                        logger.error((
                          'V0771',
                          (key, value, r[key]),
                          "A duplicate key %s was found with value %d, "
                          "but that key was previously added with value %d."))
                        
                        return None
                
                r[key] = value
            
            # Skip the sentinel, if one is present (it's ambiguous)
            
            if w.length() >= 6:
                sentinel = w.unpack("3h", advance=False)
                
                if sentinel == (-1, -1, 0):
                    w.skip(6)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format0 object from the specified walker, which
        should start at the subtable header. The following keyword arguments
        are suggested (if they are not present, the default values for coverage
        and tupleIndex will be used, which won't usually be what's wanted).
        
            coverage    A Coverage object.
            tupleIndex  The variations tuple index.
        
        NOTE: see the docstring for the Format0 class for a discussion of
        record formats.
        
        >>> obj = _testingValues[1]
        >>> obj == Format0.frombytes(
        ...   obj.binaryString(),
        ...   coverage = coverage.Coverage())
        True
        """
        
        count = w.unpack("L12x")
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        if count:
            data = w.group("2Hh", count)
            GP = glyphpair.GlyphPair
            dups = set()
        
            for *t, value in data:
                key = GP(t)
            
                if key in r:
                    dups.add(key)
            
                # We don't put an "else" here to allow the last present entry to
                # "win", in the case where there are duplicate keys.
            
                r[key] = value
        
            if dups:
                warnings.warn(
                  "Duplicate keys in format0 data: %s" % (sorted(dups),))
        
            # Skip the sentinel, if one is present (it's ambiguous)
        
            if w.length() >= 6:
                sentinel = w.unpack("3h", advance=False)
            
                if sentinel == (-1, -1, 0):
                    w.skip(6)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    def _fakeEditor(n):
        from fontio3.head import head
        
        e = utilities.fakeEditor(n)
        e.head = head.Head()
        return e
    
    def _k0():
        from fontio3.kern import format0
        
        return format0._testingValues
    
    _gptv = glyphpair._testingValues
    
    _testingValues = (
        Format0(),
        
        Format0({
          _gptv[0]: -25,
          _gptv[1]: -30,
          _gptv[2]: 12},
          coverage = coverage.Coverage()))
    
    del _gptv
    
#    _testingValues[1].setNamer(namer.testingNamer())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
