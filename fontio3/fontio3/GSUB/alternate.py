#
# alternate.py
#
# Copyright © 2007-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 3 (Alternate Substitution) subtables for a GSUB table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GSUB import alternate_glyphset
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Constants
#

GS = alternate_glyphset.Alternate_GlyphSet

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    for inGlyph, outSet in obj.items():
        if len(outSet) == 1:
            if inGlyph == next(iter(outSet)):
                logger.warning((
                  'V0424',
                  (inGlyph,),
                  "Glyph %d has, as its only alternate, itself."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Alternate(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Alternate substitution subtables for a GSUB table. These are dicts whose
    keys are glyph indices and whose values are GS objects.
    
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> _testingValues[0].pprint(namer=nm)
    
    >>> _testingValues[1].pprint(namer=nm)
    xyz5 (glyph 4):
      xyz9 (glyph 8)
      afii60002 (glyph 97)
    
    >>> _testingValues[2].pprint(namer=nm)
    xyz26 (glyph 25):
      xyz16 (glyph 15)
      xyz17 (glyph 16)
      xyz18 (glyph 17)
    xyz27 (glyph 26):
      xyz16 (glyph 15)
      xyz17 (glyph 16)
      xyz18 (glyph 17)
    xyz28 (glyph 27):
      xyz31 (glyph 30)
      xyz41 (glyph 40)
    
    >>> print(sorted(_testingValues[2].gatheredOutputGlyphs()))
    [15, 16, 17, 30, 40]
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_maxcontextfunc = (lambda d: 1),
        map_validatefunc_partial = _validate)
    
    kind = ('GSUB', 3)
    kindString = "Alternate substitution table"
    
    #
    # Methods
    #
    
    def asAAT(self, **kwArgs):
        """
        Returns a list of AAT 'morx' subtable objects that represent all the
        possible outcomes of this Alternate object.
        
        >>> v = _testingValues[2].asAAT()
        >>> len(v)
        3
        
        >>> v[0].pprint()
        25: 15
        26: 15
        27: 30
        Mask value: 00000001
        Coverage:
          Subtable kind: 4
        
        >>> v[1].pprint()
        25: 16
        26: 16
        27: 40
        Mask value: 00000001
        Coverage:
          Subtable kind: 4
        
        >>> v[2].pprint()
        25: 17
        26: 17
        Mask value: 00000001
        Coverage:
          Subtable kind: 4
        """
        
        if not self:
            return []
        
        from fontio3.morx import noncontextual
        
        count = max(len(v) for v in self.values())
        rv = [noncontextual.Noncontextual() for i in range(count)]
    
        for g, v in self.items():
            for i, n in enumerate(sorted(v)):
                rv[i][g] = n
    
        return rv
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Alternate object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0006 0000 0001  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 000E 0001 0008  0002 0008 0061 0001 |.............a..|
              10 | 0001 0004                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 001A 0003 000C  000C 0014 0003 000F |................|
              10 | 0010 0011 0002 001E  0028 0001 0003 0019 |.........(......|
              20 | 001A 001B                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        covTable = coverage.Coverage.fromglyphset(self)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        sortedKeys = sorted(self)
        w.add("H", len(self))
        pool = {}  # unique obj -> stake
        stakes = []
        
        for inGlyph in sortedKeys:
            obj = self[inGlyph]
            imm = obj.asImmutable()
            
            if imm in pool:
                stakes.append(pool[imm][0])
            
            else:
                stake = w.getNewStake()
                pool[imm] = (stake, obj)
                stakes.append(stake)
        
        for stake in stakes:
            w.addUnresolvedOffset("H", stakeValue, stake)
        
        kwArgs.pop('countFirst', None)
        
        for t in sorted(pool.values()):
            t[1].buildBinary(w, stakeValue=t[0], countFirst=True, **kwArgs)
        
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
        25:
          15
          16
          17
        26:
          15
          16
          17
        27:
          30
          40
        >>> id(obj) in memo
        True
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for gIn, tOut in self.items():
            for gOut in tOut:
                r[gIn].add(gOut)
        
        memo[id(self)] = r
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new Alternate constructed from the specified FontWorkerSource,
        with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> l = Alternate.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.alternate - WARNING - line 4 -- incorrect number of tokens, expected 2 or more, found 1
        FW_test.alternate - WARNING - line 5 -- glyph 'X' not found
        FW_test.alternate - WARNING - line 5 -- glyph 'Y' not found
        FW_test.alternate - WARNING - line 5 -- glyph 'Z' not found
        >>> l.pprint()
        2:
          3
        5:
          7
          11
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("alternate")
        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber
        r = cls()

        for line in fws:
            if line.lower() in terminalStrings:
                return r
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if len(tokens) < 2:
                    logger.warning(('V0957', (fws.lineNumber, len(tokens)), 
                        "line %d -- incorrect number of tokens, "
                        "expected 2 or more, found %d"))
                    
                    continue

                glyphsOK=True
                glyphIndices = [namer.glyphIndexFromString(t) for t in tokens]
                
                for i in range(len(tokens)):
                    if glyphIndices[i] is None:
                        logger.warning(('V0956', (fws.lineNumber, tokens[i]),
                            "line %d -- glyph '%s' not found"))
                        
                        glyphsOK=False
                
                if glyphsOK:
                    key = glyphIndices[0]
                    
                    if key in r:
                        logger.warning((
                          'V0963',
                          (fws.lineNumber, tokens[0]),
                          "line %d -- ignoring duplicated entry for '%s'"))
                    
                    else:
                        value = alternate_glyphset.Alternate_GlyphSet(glyphIndices[1:])
                        r[key] = value

        logger.error((
            'V0958',
            (startingLineNumber, terminalString),
            'line %d -- did not find matching \'%s\''))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Alternate object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[2].binaryString()
        >>> logger = utilities.makeDoctestLogger("alternate_test")
        >>> fvb = Alternate.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        alternate_test.alternate - DEBUG - Walker has 36 bytes remaining.
        alternate_test.alternate.coverage - DEBUG - Walker has 10 remaining bytes.
        alternate_test.alternate.coverage - DEBUG - Format is 1, count is 3
        alternate_test.alternate.coverage - DEBUG - Raw data are [25, 26, 27]
        alternate_test.alternate.glyph 25.glyphset - DEBUG - Logger has 24 bytes remaining.
        alternate_test.alternate.glyph 25.glyphset - DEBUG - Count is 3
        alternate_test.alternate.glyph 25.glyphset - DEBUG - Data are (15, 16, 17)
        alternate_test.alternate.glyph 27.glyphset - DEBUG - Logger has 16 bytes remaining.
        alternate_test.alternate.glyph 27.glyphset - DEBUG - Count is 2
        alternate_test.alternate.glyph 27.glyphset - DEBUG - Data are (30, 40)
        
        >>> fvb(s[:4], logger=logger)
        alternate_test.alternate - DEBUG - Walker has 4 bytes remaining.
        alternate_test.alternate - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("alternate")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, covOffset, count = w.unpack("3H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Was expecting format 1, but got format %d."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        if count != len(covTable):
            logger.error((
              'V0427',
              (count, len(covTable)),
              "The AlternateSetCount (%d) does not match the length "
              "of the Coverage (%d)."))
            
            return None
        
        if not count:
            logger.warning(('V0444', (), "The AlternateSetCount is zero."))
        
        if w.length() < 2 * count:
            logger.error((
              'V0428',
              (),
              "The AlternateSet offsets are missing or incomplete."))
            
            return None
        
        it = zip(sorted(covTable), w.group("H", count))
        r = cls()
        pool = {}
        kwArgs.pop('countFirst', None)
        
        for inGlyph, offset in it:
            if offset not in pool:
                obj = GS.fromvalidatedwalker(
                  w.subWalker(offset),
                  countFirst = True,
                  logger = logger.getChild("glyph %d" % (inGlyph,)),
                  **kwArgs)
                
                if obj is None:
                    return None
                
                pool[offset] = obj
            
            r[inGlyph] = pool[offset]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Alternate object from the specified walker.
        
        >>> for i in range(3):
        ...   obj = _testingValues[i]
        ...   print(obj == Alternate.frombytes(obj.binaryString()))
        True
        True
        True
        """
        
        format, covOffset, count = w.unpack("3H")
        
        if format != 1:
            raise ValueError("Unknown format for Alternate subtable: %s" % (format,))
        
        covTable = coverage.Coverage.fromwalker(w.subWalker(covOffset))
        
        if count != len(covTable):
            raise ValueError("Count mismatch in Alternate subtable!")
        
        it = zip(sorted(covTable), w.group("H", count))
        r = cls()
        pool = {}
        
        for inGlyph, offset in it:
            if offset not in pool:
                pool[offset] = GS.fromwalker(w.subWalker(offset), countFirst=True)
            
            r[inGlyph] = pool[offset]
        
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
        
        >>> gt = alternate_glyphset.Alternate_GlyphSet([37, 35, 50])
        >>> obj = Alternate({5: gt})
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
        
        When no chooserFunc is provided, the min() function is used:
        
        >>> r, count = obj.runOne(ga, 2)
        >>> count
        1
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 4
          originalOffset: 1
        2:
          Value: 35
          originalOffset: 2
        3:
          Value: 6
          originalOffset: 3
        4:
          Value: 7
          originalOffset: 4
        
        A chooserFunc may be explicitly provided:
        
        >>> r, count = obj.runOne(ga, 2, chooserFunc=max)
        >>> count
        1
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 4
          originalOffset: 1
        2:
          Value: 50
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
        alts = self[inGlyph]
        chooser = kwArgs.get('chooserFunc', min)
        
        r[startIndex] = runningglyphs.Glyph(
          chooser(alts),
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

        for inGlyph, outTuple in sorted(self.items()):
            outTupleStr = "\t".join([bnfgi(g) for g in sorted(outTuple)])
            s.write("%s\t%s\n" % (bnfgi(inGlyph), outTupleStr))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    gstv = alternate_glyphset._testingValues
    
    _testingValues = (
        Alternate(),
        Alternate({4: gstv[0]}),
        Alternate({25: gstv[1], 26: gstv[1], 27: gstv[2]}))
    
    del gstv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 2,
        'A1': 3,
        'B': 5,
        'B1': 7,
        'B2': 11,
        'C': 13
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        A	A1
        B	B1	B2
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        A	A1
        B	B1	B2
        C
        X	Y	Z
        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
