#
# pschaincoverage.py
#
# Copyright © 2009-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 3 (coverage) chaining contextual tables, both GPOS and GSUB.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
  coverageset,
  pschaincoverage_coveragetuple,
  pschaincoverage_key,
  pslookupgroup,
  pslookuprecord)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    # Do a length check to guarantee no sequenceIndex refers to a value outside
    # the range actually present in the associated Key.
    
    for key, group in obj.items():
        for effectIndex, effect in enumerate(group):
            n = effect.sequenceIndex
            
            if n != int(n) or n < 0 or n >= len(key[1]):
                logger.error((
                  'V0397',
                  (effectIndex, key, len(key[1]) - 1, n),
                  "Effect %d of key %s should have a sequenceIndex from 0 "
                  "through %d, but the value is %s."))
                
                r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PSChainCoverage(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 3 chaining contextual subtables.
    
    These are dicts mapping a single Key to a PSLookupGroup. (Note that in the
    future, if OpenType permits a format for multiple entries instead of a
    single entry, the existing dict will suffice).
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (({xyz21, xyz22}, {xyz31, xyz32}), ({xyz31, xyz32}, {afii60001, afii60002, xyz95}), ({afii60001, afii60002, xyz95}, {xyz21, xyz31, xyz41})):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Pair (glyph) positioning table):
            (xyz11, xyz21):
              First adjustment:
                FUnit adjustment to origin's x-coordinate: 30
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
              Second adjustment:
                Device for origin's x-coordinate:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
                Device for origin's y-coordinate:
                  Tweak at 12 ppem: -5
                  Tweak at 13 ppem: -3
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 2
                  Tweak at 20 ppem: 3
            (xyz9, xyz16):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            (xyz9, xyz21):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: True
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 1
      Effect #2:
        Sequence index: 1
        Lookup:
          Subtable 0 (Pair (class) positioning table):
            (First class 1, Second class 1):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            (First class 2, Second class 0):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
            (First class 2, Second class 1):
              First adjustment:
                FUnit adjustment to origin's x-coordinate: 30
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
              Second adjustment:
                Device for origin's x-coordinate:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
                Device for origin's y-coordinate:
                  Tweak at 12 ppem: -5
                  Tweak at 13 ppem: -3
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 2
                  Tweak at 20 ppem: 3
            Class definition table for first glyph:
              xyz16: 1
              xyz6: 1
              xyz7: 1
              xyz8: 2
            Class definition table for second glyph:
              xyz21: 1
              xyz22: 1
              xyz23: 1
          Lookup flags:
            Right-to-left for Cursive: True
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 2
    
    >>> _testingValues[0].gatheredMaxContext()
    6
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_keyfollowsprotocol = True,
        item_pprintlabelpresortfunc = operator.itemgetter(1),
        item_renumberdeepkeys = True,
        item_usenamerforstr = True,
        map_compactiblefunc = (lambda d, k, **kw: False),
        #map_compactremovesfalses = True,
        map_maxcontextfunc = (
          lambda d:
          sum(utilities.safeMax(len(k[i]) for k in d) for i in range(3))),
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PSChainCoverage to the specified
        LinkedWriter.
        
        NOTE! There will be unresolved lookup list indices in the LinkedWriter
        after this method is finished. The caller (or somewhere higher up) is
        responsible for adding an index map to the LinkedWriter with the tag
        "lookupList" before the LinkedWriter's binaryString() method is called.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> w.addIndexMap(
        ...   "lookupList_GPOS",
        ...   { ltv[1].asImmutable(): 11,
        ...     ltv[2].asImmutable(): 25})
        >>> utilities.hexdump(w.binaryString())
               0 | 0003 0002 0030 001E  0002 0030 0038 0002 |.....0.....0.8..|
              10 | 0038 0026 0002 0000  000B 0001 0019 0001 |.8.&............|
              20 | 0002 0014 0015 0001  0003 0014 001E 0028 |...............(|
              30 | 0001 0002 001E 001F  0001 0003 005E 0060 |.............^.`|
              40 | 0061                                     |.a              |
        
        >>> PSChainCoverage().binaryString()
        Traceback (most recent call last):
          ...
        ValueError: Cannot write empty PSChainCoverages!
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if not len(self):
            raise ValueError("Cannot write empty PSChainCoverages!")
        
        w.add("H", 3)  # format
        pool = {}  # immutable for Coverage -> (coverage, stake)
        
        # Note the strong assumption that Python correctly walks the iterators
        # over keys and values in the same way in the following two loops.
        
        for key in self:
            for it in (reversed(key[0]), iter(key[1]), iter(key[2])):
                v = list(it)
                w.add("H", len(v))
                
                for c in v:
                    immut = tuple(sorted(c))
                    
                    if immut not in pool:
                        pool[immut] = (c, w.getNewStake())
                    
                    w.addUnresolvedOffset("H", stakeValue, pool[immut][1])
        
        for value in self.values():
            w.add("H", len(value))
            value.buildBinary(w, **kwArgs)
        
        for immut, (obj, stake) in sorted(pool.items()):
            obj.buildBinary(w, stakeValue=stake)
    
    def compacted(self, **kwArgs):
        """
        Returns a compacted version of the object. This first does canonical
        compacting, and then walks the Key to make sure there are no "emptied
        out" entries (perhaps as a result of glyph renumbering).
        """
        
        r = mapmeta.M_compacted(self, **kwArgs)
        
        if not r:
            return None
        
        k = next(iter(r))
        
        for ct in k:
            for cs in ct:
                if not cs:
                    return None
        
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PSChainCoverage from the specified
        FontWorkerSource, doing source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSChainCoverage.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger = logger,
        ...   editor = {})
        FW_test.pschaincoverage - WARNING - line 16 -- unexpected token: foo
        FW_test.pschaincoverage - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Key((CoverageTuple((CoverageSet(frozenset({2})),)), CoverageTuple((CoverageSet(frozenset({5, 7})),)), CoverageTuple((CoverageSet(frozenset({11, 13})),)))):
          Effect #1:
            Sequence index: 0
            Lookup:
              3:
                FUnit adjustment to horizontal advance: 678
          Effect #2:
            Sequence index: 0
            Lookup:
              3:
                FUnit adjustment to horizontal advance: 901
        """
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pschaincoverage")

        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber

        CoverageTuple = pschaincoverage_coveragetuple.CoverageTuple
        Key = pschaincoverage_key.Key
        fVFWS = coverageset.CoverageSet.fromValidatedFontWorkerSource

        # initial lists; will be converted to CoverageTuple later
        backtracks = []
        inputs = []
        lookaheads = []

        lookupGroups = {}

        for line in fws:
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                # NOTE: added '.lower()' to token parsing as FontWorker seems to
                # write 'Backtrackcoverage', 'Inputcoverage', and
                # 'LookAheadcoverage', unlike other lookups which are all
                # lowercase.

                if tokens[0].lower() in terminalStrings:
                    return cls(lookupGroups)

                if tokens[0].lower() == 'backtrackcoverage definition begin':
                    backtracks.append(fVFWS(fws, logger=logger, **kwArgs))

                elif tokens[0].lower() == 'inputcoverage definition begin':
                    inputs.append(fVFWS(fws, logger=logger, **kwArgs))

                elif tokens[0].lower() == 'lookaheadcoverage definition begin':
                    lookaheads.append(fVFWS(fws, logger=logger, **kwArgs))

                elif tokens[0].lower() == 'coverage':
                    lookupList = []

                    for effect in tokens[1:]:
                        effectTokens = [x.strip() for x in effect.split(',')]
                        sequenceIndex = int(effectTokens[0]) - 1
                        lookupName = effectTokens[1]

                        lookupList.append(
                          pslookuprecord.PSLookupRecord(
                            sequenceIndex,
                            lookup.Lookup.fromValidatedFontWorkerSource(
                                fws,
                                lookupName,
                                logger=logger,
                                **kwArgs)))

                    key = Key((
                      CoverageTuple(reversed(backtracks)),
                      CoverageTuple(inputs),
                      CoverageTuple(lookaheads)))

                    lookupGroup = pslookupgroup.PSLookupGroup(lookupList)
                    lookupGroups[key] = lookupGroup

                else:
                    logger.warning((
                      'V0960',
                      (fws.lineNumber, tokens[0]),
                      'line %d -- unexpected token: %s'))

        logger.warning((
          'V0958',
          (startingLineNumber, "/".join(terminalStrings)),
          "line %d -- did not find matching '%s'"))

        return cls(lookupGroups)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSChainCoverage object from the specified
        walker, doing source validation.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {
        ...   ltv[1].asImmutable(): 11,
        ...   ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> fvb = PSChainCoverage.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("pschaincoverage_test")
        >>> obj = fvb(s, fixupList=FL, logger=logger)
        pschaincoverage_test.pschaincoverage - DEBUG - Walker has 66 remaining bytes.
        pschaincoverage_test.pschaincoverage - DEBUG - Format is 3
        pschaincoverage_test.pschaincoverage - DEBUG - Backtrack count is 2
        pschaincoverage_test.pschaincoverage - DEBUG - Backtrack offsets (reversed) are (30, 48)
        pschaincoverage_test.pschaincoverage.backtrack coverage 0.coverageset - DEBUG - Walker has 18 remaining bytes.
        pschaincoverage_test.pschaincoverage.backtrack coverage 0.coverageset - DEBUG - Format is 1, count is 2
        pschaincoverage_test.pschaincoverage.backtrack coverage 0.coverageset - DEBUG - Raw data are [30, 31]
        pschaincoverage_test.pschaincoverage.backtrack coverage 1.coverageset - DEBUG - Walker has 36 remaining bytes.
        pschaincoverage_test.pschaincoverage.backtrack coverage 1.coverageset - DEBUG - Format is 1, count is 2
        pschaincoverage_test.pschaincoverage.backtrack coverage 1.coverageset - DEBUG - Raw data are [20, 21]
        pschaincoverage_test.pschaincoverage - DEBUG - Input count is 2
        pschaincoverage_test.pschaincoverage - DEBUG - Input offsets are (48, 56)
        pschaincoverage_test.pschaincoverage.input coverage 0.coverageset - DEBUG - Walker has 18 remaining bytes.
        pschaincoverage_test.pschaincoverage.input coverage 0.coverageset - DEBUG - Format is 1, count is 2
        pschaincoverage_test.pschaincoverage.input coverage 0.coverageset - DEBUG - Raw data are [30, 31]
        pschaincoverage_test.pschaincoverage.input coverage 1.coverageset - DEBUG - Walker has 10 remaining bytes.
        pschaincoverage_test.pschaincoverage.input coverage 1.coverageset - DEBUG - Format is 1, count is 3
        pschaincoverage_test.pschaincoverage.input coverage 1.coverageset - DEBUG - Raw data are [94, 96, 97]
        pschaincoverage_test.pschaincoverage - DEBUG - Lookahead count is 2
        pschaincoverage_test.pschaincoverage - DEBUG - Lookahead offsets are (56, 38)
        pschaincoverage_test.pschaincoverage.lookahead coverage 0.coverageset - DEBUG - Walker has 10 remaining bytes.
        pschaincoverage_test.pschaincoverage.lookahead coverage 0.coverageset - DEBUG - Format is 1, count is 3
        pschaincoverage_test.pschaincoverage.lookahead coverage 0.coverageset - DEBUG - Raw data are [94, 96, 97]
        pschaincoverage_test.pschaincoverage.lookahead coverage 1.coverageset - DEBUG - Walker has 28 remaining bytes.
        pschaincoverage_test.pschaincoverage.lookahead coverage 1.coverageset - DEBUG - Format is 1, count is 3
        pschaincoverage_test.pschaincoverage.lookahead coverage 1.coverageset - DEBUG - Raw data are [20, 30, 40]
        pschaincoverage_test.pschaincoverage - DEBUG - Action count is 2
        pschaincoverage_test.pschaincoverage.pslookupgroup - DEBUG - Walker has 44 bytes remaining.
        pschaincoverage_test.pschaincoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 44 remaining bytes.
        pschaincoverage_test.pschaincoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pschaincoverage_test.pschaincoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 11
        pschaincoverage_test.pschaincoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Walker has 40 remaining bytes.
        pschaincoverage_test.pschaincoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Sequence index is 1
        pschaincoverage_test.pschaincoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Lookup index is 25

        >>> fvb(s[:25], fixupList=FL, logger=logger)
        pschaincoverage_test.pschaincoverage - DEBUG - Walker has 25 remaining bytes.
        pschaincoverage_test.pschaincoverage - DEBUG - Format is 3
        pschaincoverage_test.pschaincoverage - DEBUG - Backtrack count is 2
        pschaincoverage_test.pschaincoverage - DEBUG - Backtrack offsets (reversed) are (30, 48)
        pschaincoverage_test.pschaincoverage.backtrack coverage 0.coverageset - DEBUG - Walker has 0 remaining bytes.
        pschaincoverage_test.pschaincoverage.backtrack coverage 0.coverageset - ERROR - Insufficient bytes.
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pschaincoverage")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, backCount = w.unpack("2H")
        
        if format != 3:
            logger.error((
              'V0002',
              (format,),
              "Expected format 3, but got format %d."))
            
            return None

        else:
            logger.debug(('Vxxxx', (), "Format is 3"))

        logger.debug(('Vxxxx', (backCount,), "Backtrack count is %d"))

        if w.length() < 2 * backCount:
            logger.error((
              'V0391',
              (),
              "The Backtrack Coverage offsets are missing or incomplete."))
            
            return None
        
        backOffsets = w.group("H", backCount)

        logger.debug((
          'Vxxxx',
          (tuple(reversed(backOffsets)),),
          "Backtrack offsets (reversed) are %s"))

        v = [None] * backCount
        CoverageTuple = pschaincoverage_coveragetuple.CoverageTuple
        Key = pschaincoverage_key.Key
        fvw = coverageset.CoverageSet.fromvalidatedwalker
        
        for i, offset in enumerate(backOffsets):
            subLogger = logger.getChild("backtrack coverage %d" % (i,))
            obj = fvw(w.subWalker(offset), logger=subLogger)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        kBack = CoverageTuple(reversed(v))
        
        if w.length() < 2:
            logger.error((
              'V0392',
              (),
              "The InputGlyphCount is missing or incomplete."))
            
            return None
        
        inCount = w.unpack("H")
        logger.debug(('Vxxxx', (inCount,), "Input count is %d"))

        if w.length() < 2 * inCount:
            logger.error((
              'V0393',
              (),
              "The Input Coverage offsets are missing or incomplete."))
            
            return None
        
        inOffsets = w.group("H", inCount)
        logger.debug(('Vxxxx', (inOffsets,), "Input offsets are %s"))
        v = [None] * inCount
        
        for i, offset in enumerate(inOffsets):
            subLogger = logger.getChild("input coverage %d" % (i,))
            obj = fvw(w.subWalker(offset), logger=subLogger)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        kIn = CoverageTuple(v)
        
        if w.length() < 2:
            logger.error((
              'V0394',
              (),
              "The LookaheadGlyphCount is missing or incomplete."))
            
            return None
        
        lookCount = w.unpack("H")
        logger.debug(('Vxxxx', (lookCount,), "Lookahead count is %d"))

        if w.length() < 2 * lookCount:
            logger.error((
              'V0395',
              (),
              "The Lookahead Coverage offsets are missing or incomplete."))
            
            return None
        
        lookOffsets = w.group("H", lookCount)
        logger.debug(('Vxxxx', (lookOffsets,), "Lookahead offsets are %s"))
        v = [None] * lookCount
        
        for i, offset in enumerate(lookOffsets):
            subLogger = logger.getChild("lookahead coverage %d" % (i,))
            obj = fvw(w.subWalker(offset), logger=subLogger)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        kLook = CoverageTuple(v)
        key = Key([kBack, kIn, kLook])
        
        if w.length() < 2:
            logger.error((
              'V0396',
              (),
              "The count of lookup records is missing or incomplete."))
            
            return None
        
        count = w.unpack("H")
        logger.debug(('Vxxxx', (count,), "Action count is %d"))

        group = pslookupgroup.PSLookupGroup.fromvalidatedwalker(
          w,
          count = count,
          fixupList = fixupList,
          logger = logger,
          **kwArgs)
        
        return cls({key: group})
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSChainCoverage from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this call is made, usually by the
                        top-level GPOS construction logic. The fixup call takes
                        one argument, the Lookup being set into it.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {
        ...   ltv[1].asImmutable(): 11,
        ...   ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> obj = PSChainCoverage.frombytes(s, fixupList=FL)
        >>> d = {11: ltv[1], 25: ltv[2]}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == _testingValues[0]
        True
        """
        
        assert 'fixupList' in kwArgs
        format = w.unpack("H")
        assert format == 3
        f = coverageset.CoverageSet.fromwalker
        backOffsets = w.group("H", w.unpack("H"))
        CoverageTuple = pschaincoverage_coveragetuple.CoverageTuple
        Key = pschaincoverage_key.Key

        kBack = CoverageTuple(
          reversed([
            f(w.subWalker(offset))
            for offset in backOffsets]))

        inOffsets = w.group("H", w.unpack("H"))
        kIn = CoverageTuple(f(w.subWalker(offset)) for offset in inOffsets)
        lookOffsets = w.group("H", w.unpack("H"))
        kLook = CoverageTuple(f(w.subWalker(offset)) for offset in lookOffsets)
        key = Key([kBack, kIn, kLook])
        count = w.unpack("H")

        group = pslookupgroup.PSLookupGroup.fromwalker(
          w,
          count = count,
          fixupList = kwArgs['fixupList'])

        return cls({key: group})


    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise uses Font
        Worker glyph index labeling ("# <id>").
        """

        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for k in iter(self):
            coverageBacktrack = k[0]
            coverageInput = k[1]
            coverageLookahead = k[2]
            lookupList = self[k]

            if coverageBacktrack:
                for cbi in reversed(coverageBacktrack):  # N.B.!!
                    s.write("backtrackcoverage definition begin\n")
                    for g in sorted(cbi):
                        s.write("%s\n" % (bnfgi(g),))
                    s.write("coverage definition end\n\n")

            if coverageInput:
                for cii in coverageInput:
                    s.write("inputcoverage definition begin\n")
                    for g in sorted(cii):
                        s.write("%s\n" % (bnfgi(g),))
                    s.write("coverage definition end\n\n")

            if coverageLookahead:
                for cli in coverageLookahead:
                    s.write("lookaheadcoverage definition begin\n")
                    for g in sorted(cli):
                        s.write("%s\n" % (bnfgi(g),))
                    s.write("coverage definition end\n\n")

            s.write("coverage")
            for lkp in lookupList:
                s.write("\t%d,%d" % (lkp.sequenceIndex + 1, lkp.lookup.sequence))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import lookup
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer, writer
    from io import StringIO

    gv = pslookupgroup._testingValues
    kv = pschaincoverage_key._testingValues

    _testingValues = (
        PSChainCoverage({kv[0]: gv[1]}),)
    
    del gv, kv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'F': 2,
        'period': 5,
        'comma': 7,
        'quoteleft': 11,
        'quotesingle': 13
    }
    _test_FW_namer._initialized = True

    def _make_test_FW_lookupDict():
        from fontio3.GPOS import single, value

        S = single.Single
        V = value.Value

        return {
          'testSingle1': S({3: V(xAdvance=678)}),
          'testSingle2': S({3: V(xAdvance=901)})}

    _test_FW_lookupDict = _make_test_FW_lookupDict()

    _test_FW_fws = FontWorkerSource(StringIO(
        """
        backtrackcoverage definition begin
        F
        coverage definition end

        inputcoverage definition begin
        period
        comma
        coverage definition end

        lookaheadcoverage definition begin
        quoteleft
        quotesingle
        coverage definition end

        coverage	1,testSingle1	1,testSingle2

        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        backtrackcoverage definition begin
        F
        coverage definition end

        inputcoverage definition begin
        period
        comma
        coverage definition end

        lookaheadcoverage definition begin
        quoteleft
        quotesingle
        coverage definition end

        foo
        coverage	1,testSingle1	1,testSingle2

        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
