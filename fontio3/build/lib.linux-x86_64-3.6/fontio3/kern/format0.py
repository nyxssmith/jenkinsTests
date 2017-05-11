#
# format0.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for simple pairwise kerning (in 'kern' tables).
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.kern import coverage_v1, glyphpair
from fontio3.utilities import bsh, valassist

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
    
    if (not kwArgs.get('forApple', False)) and editor.reallyHas(b'cmap'):
        # do check for unencoded glyphs (MS-specific)
        uMap = editor.cmap.getUnicodeMap()
        
        if uMap is not None:
            rMap = uMap.getReverseMapTuple()
            badGlyphs = set()
            
            for leftGlyph, rightGlyph in obj:
                if leftGlyph not in rMap:
                    badGlyphs.add(leftGlyph)
                
                if rightGlyph not in rMap:
                    badGlyphs.add(rightGlyph)
            
            if badGlyphs:
                logger.error((
                  'V0613',
                  (sorted(badGlyphs),),
                  "For a Microsoft font, all glyphs in a format 0 'kern' "
                  "subtable must have Unicodes. These glyphs do not: %s"))
                  
                r = False
    
    if editor.reallyHas(b'head'):
        upem = editor.head.unitsPerEm
    
    else:
        logger.warning((
          'V0603',
          (),
          "No 'head' table is present, so validation will assume a "
          "units-per-em value of 1000."))
        
        upem = 1000  # if there's no 'head' table, it's probably a CFF font
    
    f = functools.partial(valassist.isNumber_integer_signed, numBits=16)
    
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
              (key, value),
              "The kerning value for %s (%s) seems excessive."))
        
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
    
        coverage        A Coverage object, either version 0 or version 1.
        
        tupleIndex      If the coverage is version 1, this will be a tuple
                        index for variation kerning, if the coverage.variation
                        flag is set. Otherwise it is None (and it is always
                        None for version 0 coverages).
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    (xyz15, afii60001): -30
    (xyz15, xyz24): -25
    (xyz19, xyz39): 12
    Header information:
      Vertical text: False
      Cross-stream: False
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
            attr_label = "Variations tuple index",
            attr_initfunc = (lambda: 0),
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate_tupleIndex))
    
    format = 0  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format0 object to the specified
        LinkedWriter.
        
        >>> obj = _testingValues[1]
        >>> h = utilities.hexdump
        >>> h(obj.binaryString())
               0 | 0003 000C 0001 0006  000E 0017 FFE7 000E |................|
              10 | 0060 FFE2 0012 0026  000C                |.`.....&..      |
        
        >>> h(obj.binaryString(addSentinel=True))
               0 | 0003 000C 0001 0006  000E 0017 FFE7 000E |................|
              10 | 0060 FFE2 0012 0026  000C FFFF FFFF 0000 |.`.....&........|
        """
        
        w.addString(bsh.binsearchheader(len(self), 6))
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
        GP = glyphpair.GlyphPair
        
        for key2, value2 in f2.items():
            leftClass, rightClass = key2
            for leftGlyph in invLeft.get(leftClass, []):
                for rightGlyph in invRight.get(rightClass, []):
                    r[GP([leftGlyph, rightGlyph])] = value2
        
        return r
    
    @classmethod
    def fromgpospairs(cls, pgObj, **kwArgs):
        """
        Creates and returns a new Format0 object from the specified PairGlyphs
        object. If there are any keys whose associated Values cannot be
        converted, they will be shown in a ValueError raised by this method.
        
        The following keyword arguments are used:
        
            coverage        A version 1 Coverage object. If not provided, a
                            default Coverage will be created and used.
            
            keepZeroes      Some Lookups use a pair-glyph subtable containing
                            glyph pairs with no movement. Since a match in an
                            earlier subtable should prevent processing of that
                            pair in subsequent subtable, we need to keep these
                            values. See the PFC "GPOS to Flat Kern" script for
                            an example.
                            
                            Default is False.
            
            tupleIndex      The variations tuple index. Default is 0.
        """
        
        if 'coverage' not in kwArgs:
            kwArgs['coverage'] = coverage_v1.Coverage()
        
        if 'tupleIndex' not in kwArgs:
            kwArgs['tupleIndex'] = 0
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        couldNotProcess = set()
        horizontal = not kwArgs['coverage'].vertical
        keepZeroes = kwArgs.get('keepZeroes', False)
        
        for gposKey, gposValue in pgObj.items():
            fmt0Key = glyphpair.GlyphPair(gposKey)
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
            
            if delta or keepZeroes:
                r[fmt0Key] = delta
        
        if couldNotProcess:
            v = sorted(couldNotProcess)
            raise ValueError("Could not process these GPOS keys: %s" % (v,))
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format0 object from the specified walker, which
        should start at the subtable header. This method does extensive
        validation via the logging module (the client should have done a
        logging.basicConfig call prior to calling this method, unless a logger
        is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format0.fromvalidatedbytes
        >>> obj = fvb(s[0:3], logger=logger)
        test.format0 - DEBUG - Walker has 3 remaining bytes.
        test.format0 - ERROR - Insufficient bytes.

        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.format0 - DEBUG - Walker has 20 remaining bytes.
        test.format0 - INFO - There are 2 kerning pairs.
        test.format0.[0].glyphpair - DEBUG - Walker has 12 remaining bytes.
        test.format0.[1].glyphpair - DEBUG - Walker has 6 remaining bytes.
        test.format0 - WARNING - Value for pair (14, 96) is 0
        
        >>> s = utilities.fromhex(
        ...   "00 03 00 0C 00 01 00 06 00 05 00 10 FF E7 00 05 "
        ...   "00 10 FF E7 00 05 00 10 FF E9") 
        >>> obj = fvb(s, logger=logger)
        test.format0 - DEBUG - Walker has 26 remaining bytes.
        test.format0 - INFO - There are 3 kerning pairs.
        test.format0.[0].glyphpair - DEBUG - Walker has 18 remaining bytes.
        test.format0.[1].glyphpair - DEBUG - Walker has 12 remaining bytes.
        test.format0 - WARNING - Duplicate entry for pair (5, 16) with value -25
        test.format0.[2].glyphpair - DEBUG - Walker has 6 remaining bytes.
        test.format0 - ERROR - Duplicate entry for pair (5, 16) with different value -23 (-25)
        """
        
        kwArgs.pop('fontGlyphCount', None)
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format0")
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        nPairs, searchRange, entrySelector, rangeShift = w.unpack("4H")
        bTest = bsh.BSH(nUnits=nPairs, unitSize=6)

        """
        The parent 'kern' table stores a 'length' record for each
        subtable. In 'kern' table version 0, this field is defined as a
        USHORT and will thus overflow when nPairs is > 10920 (14 bytes
        of header + (6 * 10920) = 65534). Although most systems can deal
        with the font correctly (provided that the actual byte length
        corresponds with nPairs), we still detect and warn about the
        condition as some applications do not correctly deal with the
        mismatch.
        """
        if nPairs > 10920:
            logger.warning((
              'V0920',
              (),
              "Subtable declares more than 10920 pairs."))
        
        srmod = bTest.searchRange % 65536
        if searchRange != srmod:
            logger.error((
              'E1602',
              (searchRange, srmod),
              "Subtable searchRange %d is incorrect; should be %d."))
            
            return None
        
        esmod = bTest.entrySelector % 65536
        if entrySelector != esmod:
            logger.error((
              'E1600',
              (entrySelector, esmod),
              "Subtable entrySelector %d is incorrect; should be %d."))
            
            return None
        
        rsmod = bTest.rangeShift % 65536
        if rangeShift != rsmod:
            logger.error((
              'E1601',
              (rangeShift, rsmod),
              "Subtable rangeShift %d is incorrect; should be %d."))
            
            return None
        
        if w.length() < 6 * nPairs:
            logger.error(('V0136', (), "Insufficient bytes for pair data."))
            return None
        
        logger.info(('V0137', (nPairs,), "There are %d kerning pairs."))
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        okToReturn = True
        GP = glyphpair.GlyphPair.fromvalidatedwalker
        sortCheck = [None] * nPairs
        
        for i in range(nPairs):
            key = GP(w, logger=logger.getChild("[%d]" % (i,)), **kwArgs)
            
            if key is None:
                return None
            
            sortCheck[i] = key
            value = w.unpack("h")
            
            if key in r:
                if value == r[key]:
                    logger.warning((
                      'V0139',
                      (key, value),
                      "Duplicate entry for pair %s with value %d"))
                
                else:
                    logger.error((
                      'V0140',
                      (key, value, r[key]),
                      "Duplicate entry for pair %s with different "
                      "value %d (%d)"))
                    
                    okToReturn = False
                    
            if value == 0:
                logger.warning(('V0141', (key,), "Value for pair %s is 0"))
            
            else:
                r[key] = value
        
        if sortCheck != sorted(sortCheck):
            logger.error(('V0138', (), "Kerning pairs are not sorted."))
            okToReturn = False
        
        # Skip the sentinel, if one is present (spec is ambiguous)
        
        if w.length() >= 6:  # last subtable might just zero-pad, so check this
            sentinel = w.unpack("3h", advance=False)
            
            if sentinel == (-1, -1, 0):
                w.skip(6)
            
            # check for non-zero pad? i.e. sentinel[2] != 0?
        
        return (r if okToReturn else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format0 object from the specified walker, which
        should start at the subtable header.
        
        >>> obj = _testingValues[1]
        >>> obj == Format0.frombytes(
        ...   obj.binaryString(),
        ...   coverage = coverage_v1.Coverage())
        True
        """
        
        nPairs = w.unpack("H6x")
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        fw = glyphpair.GlyphPair.fromwalker
        
        while nPairs:
            key = fw(w)
            r[key] = w.unpack("h")
            nPairs -= 1
        
        if w.length() >= 6:  # last subtable might just zero-pad, so check this
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
    from fontio3.kern import coverage_v0
    from fontio3.utilities import namer
    
    _gptv = glyphpair._testingValues
    
    _testingValues = (
        Format0(),
        
        Format0({
          _gptv[0]: -25,
          _gptv[1]: -30,
          _gptv[2]: 12},
          coverage = coverage_v1.Coverage()),

        Format0({
          _gptv[3]: -25,
          _gptv[1]: 0},
          coverage = coverage_v0.Coverage()),
        
        Format0({
          _gptv[0]: -25,
          _gptv[1]: -30,
          _gptv[2]: 12},
          coverage = coverage_v0.Coverage()))
    
    _testingValues[1].setNamer(namer.testingNamer())
    del _gptv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
