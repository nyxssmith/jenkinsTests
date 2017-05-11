#
# reverse.py
#
# Copyright © 2007-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 8 (Reverse chaining contextual) subtables for a GSUB table.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.GSUB import reverse_coveragetuple, reverse_key
from fontio3.GSUB.effects import EffectsSummary

from fontio3.opentype import (
  coverageset,
  glyphtuple,
  pschaincoverage_coveragetuple,
  runningglyphs)

# -----------------------------------------------------------------------------

#
# Constants
#

CoverageTuple = reverse_coveragetuple.CoverageTuple
Key = reverse_key.Key

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    if len(obj) != 1:
        logger.error((
          'V0452',
          (),
          "The Reverse lookup may only have a single entry."))
        
        r = False
    
    else:
        k, v = next(iter(obj.items()))
        
        if len(k[1]) != len(v):
            logger.error((
              'V0453',
              (),
              "The length of the input sequence must match the length "
              "of the substitution glyphs."))
            
            r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#
    
if 0:
    def __________________(): pass

class Reverse(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 1 reverse chaining contextual single substitution
    subtables (coverage-based).
    
    These are dicts mapping a single Key to a GlyphTuple. The [1] element of
    the key must have the same number of entries as the GlyphTuple, since this
    format does not use the PSLookupGroup construct at all.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (({xyz21, xyz22}, {xyz31, xyz32}), {xyz51, xyz52, xyz54, xyz57, xyz58}, ({afii60001, afii60002, xyz95}, {xyz21, xyz31, xyz41})):
      0: xyz61
      1: xyz62
      2: xyz64
      3: xyz67
      4: xyz68
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresortfunc = (lambda obj: obj[1]),
        item_renumberdeepkeys = True,
        item_usenamerforstr = True,
        map_maxcontextfunc = (
          lambda d:
            utilities.safeMax(len(k[0]) for k in d) + 1 +
            utilities.safeMax(len(k[2]) for k in d)),
        map_validatefunc_partial = _validate)
    
    kind = ('GSUB', 8)
    kindString = "Reverse chaining table"
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Reverse object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 001C 0002 003C  002A 0002 0044 0032 |.......<.*...D.2|
              10 | 0005 003C 003D 003F  0042 0043 0001 0005 |...<.=.?.B.C....|
              20 | 0032 0033 0035 0038  0039 0001 0002 0014 |.2.3.5.8.9......|
              30 | 0015 0001 0003 0014  001E 0028 0001 0002 |...........(....|
              40 | 001E 001F 0001 0003  005E 0060 0061      |.........^.`.a  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        pool = {}
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        
        for key in self:
            for it in (reversed(key[0]), iter(key[2])):
                v = list(it)
                w.add("H", len(v))
                
                for c in v:
                    immut = tuple(sorted(c))
                    
                    if immut not in pool:
                        pool[immut] = (c, w.getNewStake())
                    
                    w.addUnresolvedOffset("H", stakeValue, pool[immut][1])
        
        for value in self.values():
            w.add("H", len(value))
            w.addGroup("H", value)
        
        key[1].buildBinary(w, stakeValue=covStake)
        
        for immut, (obj, stake) in sorted(pool.items()):
            obj.buildBinary(w, stakeValue=stake)
    
    def effectsSummary(self, **kwArgs):
        """
        Returns an EffectsSummary object. If present, notes will be made in a
        provided memo kwArgs to allow elision of reprocessing, which should
        eliminate the combinatoric explosion.
        
        >>> obj = _testingValues[0]
        >>> memo = {}
        >>> es = obj.effectsSummary(memo=memo)
        >>> es.pprint()
        50:
          60
        51:
          61
        53:
          63
        56:
          66
        57:
          67
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for key, tOut in self.items():
            for gIn, gOut in zip(sorted(key[1]), tOut):
                r[gIn].add(gOut)
        
        memo[id(self)] = r
        return r

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new Reverse from the specified FontWorkerSource,
        doing source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_fws.goto(1) # go back to start of file
        >>> obj = Reverse.fromValidatedFontWorkerSource(
        ...   _test_FW_fws,
        ...   logger=logger,
        ...   namer = _test_FW_namer)
        >>> obj.pprint()
        Key((CoverageTuple((CoverageSet(frozenset({2, 3})),)), CoverageSet(frozenset({8})), CoverageTuple((CoverageSet(frozenset({5})),)))):
          0: 9

        >>> _test_FW_fws2.goto(1) # go back to start of file
        >>> obj = Reverse.fromValidatedFontWorkerSource(
        ...  _test_FW_fws2,
        ...  logger=logger,
        ...  namer = _test_FW_namer)
        FW_test.reverse - WARNING - line 3 -- glyph 'foo' not found
        FW_test.reverse - WARNING - line 3 -- glyph 'bar' not found
        FW_test.reverse - ERROR - Must define at least one backtrackcoverage or lookaheadcoverage for reversechaining lookup type.
        >>> obj is None
        True
        """
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("reverse")

        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber

        CoverageTuple = pschaincoverage_coveragetuple.CoverageTuple
        Key = reverse_key.Key
        fFWS = coverageset.CoverageSet.fromValidatedFontWorkerSource

        backtrackcvgsets = []
        singlesubin = []
        singlesubout = []
        lookaheadcvgsets = []

        r = cls()

        for line in fws:
            if line.lower() in terminalStrings:
                if len(backtrackcvgsets) == 0 and len(lookaheadcvgsets) == 0:
                    logger.error((
                        'Vxxxx',
                        (),
                        "Must define at least one backtrackcoverage "
                        "or lookaheadcoverage for reversechaining "
                        "lookup type."))

                    return None

                if len(singlesubin) == 0:
                    logger.error((
                        'Vxxxx',
                        (),
                        "Single substitution is empty."))

                    return None

                # sort output to match order of input
                ssinsorted, ssoutsorted = list(zip(*sorted(zip(singlesubin, singlesubout))))

                ss = coverageset.CoverageSet(ssinsorted)
                k = Key(
                    CoverageTuple(backtrackcvgsets),
                    ss,
                    CoverageTuple(lookaheadcvgsets))
                v = glyphtuple.GlyphTuple(ssoutsorted)
                r[k] = v

                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                if tokens[0].lower() == 'backtrackcoverage definition begin':
                    # key[0]
                    backtrackcvgsets.append(fFWS(fws, **kwArgs))

                elif tokens[0].lower() == 'lookaheadcoverage definition begin':
                    # key[2]
                    lookaheadcvgsets.append(fFWS(fws, **kwArgs))

                elif len(tokens) == 2:
                    glyphsOK = True
                    glyphIndices = [namer.glyphIndexFromString(t) for t in tokens]

                    for i in range(2):
                        if glyphIndices[i] is None:
                            logger.warning(('V0956', (fws.lineNumber, tokens[i]),
                                "line %d -- glyph '%s' not found"))
                            glyphsOK = False

                    if glyphsOK:
                        singlesubin.append(glyphIndices[0])
                        singlesubout.append(glyphIndices[1])

        logger.error((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Reverse object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("reverse_test")
        >>> fvb = Reverse.fromvalidatedbytes
        >>> s = _testingValues[0].binaryString()
        >>> obj = fvb(s, logger=logger)
        reverse_test.reverse - DEBUG - Walker has 78 bytes remaining.
        reverse_test.reverse.input.coverageset - DEBUG - Walker has 50 remaining bytes.
        reverse_test.reverse.input.coverageset - DEBUG - Format is 1, count is 5
        reverse_test.reverse.input.coverageset - DEBUG - Raw data are [50, 51, 53, 56, 57]
        reverse_test.reverse.backtrack index 0.coverageset - DEBUG - Walker has 18 remaining bytes.
        reverse_test.reverse.backtrack index 0.coverageset - DEBUG - Format is 1, count is 2
        reverse_test.reverse.backtrack index 0.coverageset - DEBUG - Raw data are [30, 31]
        reverse_test.reverse.backtrack index 1.coverageset - DEBUG - Walker has 36 remaining bytes.
        reverse_test.reverse.backtrack index 1.coverageset - DEBUG - Format is 1, count is 2
        reverse_test.reverse.backtrack index 1.coverageset - DEBUG - Raw data are [20, 21]
        reverse_test.reverse.lookahead index 0.coverageset - DEBUG - Walker has 10 remaining bytes.
        reverse_test.reverse.lookahead index 0.coverageset - DEBUG - Format is 1, count is 3
        reverse_test.reverse.lookahead index 0.coverageset - DEBUG - Raw data are [94, 96, 97]
        reverse_test.reverse.lookahead index 1.coverageset - DEBUG - Walker has 28 remaining bytes.
        reverse_test.reverse.lookahead index 1.coverageset - DEBUG - Format is 1, count is 3
        reverse_test.reverse.lookahead index 1.coverageset - DEBUG - Raw data are [20, 30, 40]

        >>> fvb(s[:5], logger=logger)
        reverse_test.reverse - DEBUG - Walker has 5 bytes remaining.
        reverse_test.reverse - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("reverse")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, inOffset, backCount = w.unpack("3H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got format %d."))
            
            return None
        
        fvw = coverageset.CoverageSet.fromvalidatedwalker
        
        kIn = fvw(
          w.subWalker(inOffset),
          logger = logger.getChild("input"),
          **kwArgs)
        
        if kIn is None:
            return None
        
        if w.length() < 2 * backCount:
            logger.error((
              'V0446',
              (),
              "The Backtrack offsets are missing or incomplete."))
            
            return None
        
        backOffsets = w.group("H", backCount)
        v = [None] * backCount
        
        for i, offset in enumerate(backOffsets):
            obj = fvw(w.subWalker(offset),
              logger = logger.getChild("backtrack index %d" % (i,)),
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        kBack = CoverageTuple(reversed(v))
        
        if w.length() < 2:
            logger.error((
              'V0447',
              (),
              "The Lookahead count is missing or incomplete."))
            
            return None
        
        lookCount = w.unpack("H")
        
        if w.length() < 2 * lookCount:
            logger.error((
              'V0448',
              (),
              "The Lookahead offsets are missing or incomplete."))
            
            return None
        
        lookOffsets = w.group("H", lookCount)
        v = [None] * lookCount
        
        for i, offset in enumerate(lookOffsets):
            obj = fvw(w.subWalker(offset),
              logger = logger.getChild("lookahead index %d" % (i,)),
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        kLook = CoverageTuple(v)
        key = Key([kBack, kIn, kLook])
        
        if w.length() < 2:
            logger.error((
              'V0449',
              (),
              "The Substitute count is missing or incomplete."))
            
            return None
        
        substCount = w.unpack("H")
        
        if w.length() < 2 * substCount:
            logger.error((
              'V0450',
              (),
              "The Substitute array is missing or incomplete."))
            
            return None
        
        if substCount != len(kIn):
            logger.error((
              'V0451',
              (),
              "The Substitute count does not match the length of the "
              "input Coverage."))
            
            return None
        
        group = glyphtuple.GlyphTuple(w.group("H", substCount))
        return cls({key: group})
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Reverse object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == Reverse.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        assert format == 1
        f = coverageset.CoverageSet.fromwalker
        kIn = f(w.subWalker(w.unpack("H")))
        backOffsets = w.group("H", w.unpack("H"))
        
        kBack = CoverageTuple(reversed([
          f(w.subWalker(offset))
          for offset in backOffsets]))
        
        lookOffsets = w.group("H", w.unpack("H"))
        kLook = CoverageTuple(f(w.subWalker(offset)) for offset in lookOffsets)
        key = Key([kBack, kIn, kLook])
        group = glyphtuple.GlyphTuple(w.group("H", w.unpack("H")))
        return cls({key: group})

    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single (initial) glyph in a glyph array. This
        method is called by the Lookup object's run() method (and possibly by
        actions within contextual or related subtables).
        
        This method returns a pair: the new output GlyphList, and a count of
        the number of glyph indices involved (or zero, if no action happened).
        
        Note that igs is used in this method.
        
        >>> obj = _testingValues[0]
        >>> ga = runningglyphs.GlyphList.fromiterable([20, 77, 30, 57, 94, 77, 20])
        >>> igsFunc = lambda *a, **k: [False, True, False, False, False, True, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> count
        0
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 3, igsFunc=igsFunc)
        >>> count
        1
        >>> r.pprint()
        0:
          Value: 20
          originalOffset: 0
        1:
          Value: 77
          originalOffset: 1
        2:
          Value: 30
          originalOffset: 2
        3:
          Value: 67
          originalOffset: 3
        4:
          Value: 94
          originalOffset: 4
        5:
          Value: 77
          originalOffset: 5
        6:
          Value: 20
          originalOffset: 6
        """
        
        igsFunc = kwArgs['igsFunc']
        igs = igsFunc(glyphArray, **kwArgs)
        firstGlyph = glyphArray[startIndex]
        
        # Find all non-ignorables (not just starting with startIndex, since we
        # potentially need backtrack here too...)
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray)
          if (not igs[i])]
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        startIndexNI = vBackMap.index(startIndex)
        
        for key in self:
            if firstGlyph not in key[1]:
                continue
            
            backLen, inLen, lookLen = len(key[0]), 1, len(key[2])
            totalLen = backLen + inLen + lookLen
            
            if backLen > startIndexNI:
                continue
            
            if (inLen + lookLen) > (len(vNonIgs) - startIndexNI):
                continue
            
            pieceStart = startIndexNI - backLen
            piece = vNonIgs[pieceStart:pieceStart+totalLen]
            
            if not all(a in b for a, b in zip(piece, key[0] + (key[1],) + key[2])):
                continue
            
            # If we get here the key is a match
            
            r = glyphArray.fromiterable(glyphArray)  # preserves offsets
            it = list(zip(sorted(key[1]), self[key]))
            d = {gIn: gOut for gIn, gOut in it}
            
            r[startIndex] = runningglyphs.Glyph(
                d[firstGlyph],
                originalOffset = glyphArray[startIndex].originalOffset)
            
            return (r, 1)
        
        return (glyphArray, 0)

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        # backtrackcoverage
        k = list(self.keys())[0]
        
        if k[0]:
            for btc in k[0]:
                s.write("\nbacktrackcoverage definition begin\n")
                
                for g in sorted(btc):
                    s.write("%s\n" % (bnfgi(g),))
                
                s.write("coverage definition end\n")

        # lookaheadcoverage
        if k[2]:
            for lac in k[2]:
                s.write("\nlookaheadcoverage definition begin\n")
                
                for g in sorted(lac):
                    s.write("%s\n" % (bnfgi(g),))
                
                s.write("coverage definition end\n")

        # single substitution lookup (input coverage -> output coverage)
        in_cvg = k[1]
        out_cvg = self[k]
        s.write("\n")
        
        for i, inGlyph in enumerate(sorted(in_cvg)):
            outGlyph = out_cvg[i]
            s.write("%s\t%s\n" % (bnfgi(inGlyph), bnfgi(outGlyph)))
        
        s.write("")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from io import StringIO

    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource

    ktv = reverse_key._testingValues
    GT = glyphtuple.GlyphTuple

    _testingValues = (
        Reverse({ktv[0]: GT([60, 61, 63, 66, 67])}),)

    del ktv, GT

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 2,
        'B': 3,
        'C': 5,
        'D': 7,
        'E': 8,
        'F': 9,
    }
    _test_FW_namer._initialized = True

    _test_FW_fws = FontWorkerSource(StringIO(
        """
        backtrackcoverage definition begin
        A
        B
        coverage definition end

        lookaheadcoverage definition begin
        C
        coverage definition end

        E	F

        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        E	F
        foo	bar

        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
