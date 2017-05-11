#
# single.py
#
# Copyright © 2007-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 1 (Single Substitution) subtables for a GSUB table.
"""

# System imports
import logging
import io as StringIO

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    noChanges = set()
    mapToMissing = set()
    
    for inGlyph, outGlyph in obj.items():
        if inGlyph == outGlyph:
            noChanges.add(inGlyph)
        
        if outGlyph == 0:
            mapToMissing.add(inGlyph)
    
    if noChanges:
        logger.warning((
          'V0417',
          (sorted(noChanges),),
          "These glyphs map to themselves: %s"))
    
    if mapToMissing:
        logger.warning((
          'V0418',
          (sorted(mapToMissing),),
          "These glyphs map to glyph zero: %s"))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Single(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Single substitution subtables for a GSUB table. These are dicts whose keys
    and values are both glyph indices.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz5: xyz11
    xyz7: xyz13
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz5: xyz11
    xyz6: afii60002
    xyz7: xyz19
    
    >>> logger = utilities.makeDoctestLogger("single_iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Single({4: 7, 8: 0, 15: 15, 16: 16}).isValid(logger=logger, editor=e)
    single_iv - WARNING - These glyphs map to themselves: [15, 16]
    single_iv - WARNING - These glyphs map to glyph zero: [8]
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_renumberdirectvalues = True,
        item_usenamerforstr = True,
        item_valueisoutputglyph = True,
        map_maxcontextfunc = (lambda d: 2),
        map_validatefunc_partial = _validate)
    
    kind = ('GSUB', 1)
    kindString = "Single substitution table"
    
    #
    # Methods
    #
    
    def asAAT(self, **kwArgs):
        """
        Returns a list of AAT 'morx' subtable objects that have the same effect
        as this Single object.
        
        >>> v = _testingValues[2].asAAT()
        >>> len(v)
        1
        >>> utilities.hexdump(v[0].binaryString())
               0 | 0008 0004 0003 000A  0061 0012           |.........a..    |
        """
        
        if not self:
            return []
        
        from fontio3.morx import noncontextual
        
        return [noncontextual.Noncontextual(self)]
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Single object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0006 0000 0001  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0006 0006 0001  0002 0004 0006      |..............  |
        
        >>> utilities.hexdump(_testingValues[2].binaryString()) 
               0 | 0002 000C 0003 000A  0061 0012 0001 0003 |.........a......|
              10 | 0004 0005 0006                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        deltas = set(outGlyph - inGlyph for inGlyph, outGlyph in self.items())
        covTable = coverage.Coverage.fromglyphset(self)
        covStake = w.getNewStake()
        
        if (not self) or len(deltas) == 1:
            w.add("H", 1)  # format 1
            w.addUnresolvedOffset("H", stakeValue, covStake)
            w.add("H", ((deltas.pop() % 65536) if self else 0))
        
        else:
            w.add("H", 2)  # format 2
            w.addUnresolvedOffset("H", stakeValue, covStake)
            w.add("H", len(self))
            
            for inGlyph in sorted(self):
                w.add("H", self[inGlyph])
        
        covTable.buildBinary(w, stakeValue=covStake, **kwArgs)
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectsSummary() instead.")
    
    def effectsSummary(self, **kwArgs):
        """
        Returns an EffectsSummary object. If present, notes will be made in a
        provided memo kwArgs to allow elision of reprocessing, which should
        eliminate the combinatoric explosion.
        
        >>> obj = _testingValues[2]
        >>> memo = {}
        >>> es = obj.effectsSummary(memo=memo)
        >>> es.pprint()
        4:
          10
        5:
          97
        6:
          18
        >>> id(obj) in memo
        True
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for gIn, gOut in self.items():
            r[gIn].add(gOut)
        
        memo[id(self)] = r
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new Single constructed from the specified FontWorkerSource,
        with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_fws.goto(1) # go back to start of file
        >>> s = Single.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> s.pprint()
        2: 5
        3: 7
        >>> s = Single.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.single - WARNING - line 3 -- glyph 'X' not found
        FW_test.single - WARNING - line 5 -- glyph 'Z' not found
        FW_test.single - WARNING - line 6 -- glyph 'T' not found
        FW_test.single - WARNING - line 6 -- glyph 'U' not found
        FW_test.single - WARNING - line 7 -- incorrect number of tokens, expected 2, found 1
        FW_test.single - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> s.pprint()
        2: 5
        3: 7
        """
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('single')

        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber

        r = cls()

        for line in fws:
            if line.lower() in terminalStrings:
                return r
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                if len(tokens) != 2:
                    logger.warning(('V0957', (fws.lineNumber, len(tokens)), 
                        'line %d -- incorrect number of tokens, expected 2, found %d'))
                    continue

                glyphsOK=True
                glyphIndices = [namer.glyphIndexFromString(t) for t in tokens]
                for i in range(2):
                    if glyphIndices[i] is None:
                        logger.warning(('V0956', (fws.lineNumber, tokens[i]),
                            "line %d -- glyph '%s' not found"))
                        glyphsOK=False

                if glyphsOK:
                    if glyphIndices[0] in r:
                        logger.warning((
                          'Vxxxx',
                          (fws.lineNumber, tokens[0]),
                          "line %d -- ignoring duplicated entry for '%s'"))
                    else:
                        r[glyphIndices[0]] = glyphIndices[1]

        logger.warning((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Single object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("single_test")
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Single.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        single_test.single - DEBUG - Walker has 14 bytes remaining.
        single_test.single.coverage - DEBUG - Walker has 8 remaining bytes.
        single_test.single.coverage - DEBUG - Format is 1, count is 2
        single_test.single.coverage - DEBUG - Raw data are [4, 6]
        
        >>> fvb(s[:4], logger=logger)
        single_test.single - DEBUG - Walker has 4 bytes remaining.
        single_test.single - ERROR - Insufficient bytes.
        
        >>> fvb(utilities.fromhex("00 05") + s[2:], logger=logger)
        single_test.single - DEBUG - Walker has 14 bytes remaining.
        single_test.single - ERROR - Format is 5 but should be either 1 or 2.
        
        >>> obj = fvb(
        ...   s[:4] + utilities.fromhex("00 00") + s[6:],
        ...   logger=logger)
        single_test.single - DEBUG - Walker has 14 bytes remaining.
        single_test.single.coverage - DEBUG - Walker has 8 remaining bytes.
        single_test.single.coverage - DEBUG - Format is 1, count is 2
        single_test.single.coverage - DEBUG - Raw data are [4, 6]
        single_test.single - WARNING - The DeltaGlyphID is zero.
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(
        ...   s[:4] + utilities.fromhex("00 01") + s[6:],
        ...   logger=logger)
        single_test.single - DEBUG - Walker has 22 bytes remaining.
        single_test.single.coverage - DEBUG - Walker has 10 remaining bytes.
        single_test.single.coverage - DEBUG - Format is 1, count is 3
        single_test.single.coverage - DEBUG - Raw data are [4, 5, 6]
        single_test.single - ERROR - The GlyphCount 1 does not match the length of the Coverage 3.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("single")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, covOffset, n = w.unpack("3H")
        
        if format != 1 and format != 2:
            logger.error((
              'V0002',
              (format,),
              "Format is %d but should be either 1 or 2."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        r = cls()
        
        if format == 1:
            if not n:
                logger.warning(('V0416', (), "The DeltaGlyphID is zero."))
            
            delta = n  # yes, unsigned (see below)
            
            for inGlyph in covTable:
                r[inGlyph] = (inGlyph + delta) % 65536
        
        else:
            if not n:
                logger.warning(('V0441', (), "The GlyphCount is zero."))
            
            if w.length() < 2 * n:
                logger.error((
                  'V0414',
                  (),
                  "The Substitutes array is missing or incomplete."))
                
                return None
            
            if len(covTable) != n:
                logger.error((
                  'V0415',
                  (n, len(covTable)),
                  "The GlyphCount %d does not match the length of "
                  "the Coverage %d."))
                
                return None
            
            outGlyphs = w.group("H", n)
            it = zip(sorted(covTable), outGlyphs)
            
            for inGlyph, outGlyph in it:
                r[inGlyph] = outGlyph
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Single object from the specified walker.
        
        >>> for i in range(3):
        ...   obj = _testingValues[i]
        ...   print(obj == Single.frombytes(obj.binaryString()))
        True
        True
        True
        """
        
        format, covOffset = w.unpack("2H")
        covTable = coverage.Coverage.fromwalker(w.subWalker(covOffset))
        r = cls()
        
        if format == 1:
            delta = w.unpack("H")  # yes, unsigned (see below)
            
            for inGlyph in covTable:
                r[inGlyph] = (inGlyph + delta) % 65536
        
        elif format == 2:
            outGlyphs = w.group("H", w.unpack("H"))
            it = zip(sorted(covTable), outGlyphs)
            
            for inGlyph, outGlyph in it:
                r[inGlyph] = outGlyph
        
        else:
            raise ValueError("Unknown Single format: %s" % (format,))
        
        return r
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single glyph in a glyph array. This method is
        called by the Lookup object's run() method (and possibly by actions
        within contextual or related subtables).
        
        This method returns a pair: the new output GlyphList, and a count of
        the number of glyph indices involved (or zero, if no action happened).
        
        Note that the igsFunc is not used in this method.
        
        >>> obj = Single({4: 10, 5: 97, 6: 18})
        >>> ga = runningglyphs.GlyphList.fromiterable([3, 4, 5, 6, 7])
        >>> ga.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 4
          originalOffset: 1
        2:
          Value: 5
          originalOffset: 2
        3:
          Value: 6
          originalOffset: 3
        4:
          Value: 7
          originalOffset: 4
        
        >>> r, count = obj.runOne(ga, 0)
        >>> count
        0
        
        When no match is found, the same (input) glyphArray is returned:
        
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 1)
        >>> count
        1
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 10
          originalOffset: 1
        2:
          Value: 5
          originalOffset: 2
        3:
          Value: 6
          originalOffset: 3
        4:
          Value: 7
          originalOffset: 4
        """
        
        inGlyph = glyphArray[startIndex]
        
        if inGlyph not in self:
            return (glyphArray, 0)
        
        r = glyphArray.fromiterable(glyphArray)  # preserves offsets
        
        r[startIndex] = runningglyphs.Glyph(
          self[inGlyph],
          originalOffset = inGlyph.originalOffset,
          shaperClass = inGlyph.shaperClass)
        
        return (r, 1)

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for inGlyph, outGlyph in sorted(self.items()):
            s.write("%s\t%s\n" % (bnfgi(inGlyph), bnfgi(outGlyph)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from io import StringIO
    
    from fontio3 import utilities
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer
    
    _testingValues = (
        Single(),
        Single({4: 10, 6: 12}),  # format 1
        Single({4: 10, 5: 97, 6: 18}))  # format 2

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 2,
        'B': 3,
        'C': 5,
        'D': 7,
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        A	C
        B	D
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        A	C
        X	A
        B	D
        C	Z
        T	U
        foo
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
