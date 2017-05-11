#
# pscontextcoverage.py
#
# Copyright © 2009-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 3 (coverage) contextual tables, both GPOS and GSUB.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
    coverageset,
    pscontextcoverage_key,
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
            
            if n != int(n) or n < 0 or n >= len(key):
                logger.error((
                  'V0363',
                  (effectIndex, key, len(key) - 1, n),
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

class PSContextCoverage(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 3 contextual lookups. Note that these work for
    both GPOS and GSUB tables.
    
    These are dicts mapping a single Key to a PSLookupGroup. (Note that in the
    future, if OpenType permits a format for multiple entries instead of a
    single entry, the existing dict will suffice.)
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    ({xyz21, xyz22}, {xyz31, xyz32}, {afii60001, afii60002, xyz95}):
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
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdeepkeys = True,
        item_usenamerforstr = True,
        map_compactiblefunc = (lambda d, k, **kw: False),
        #map_compactremovesfalses = True,
        map_maxcontextfunc = (lambda d: utilities.safeMax(len(k) for k in d)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PSContextCoverage to the specified
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
               0 | 0003 0003 0002 0014  001C 0024 0000 000B |...........$....|
              10 | 0001 0019 0001 0002  0014 0015 0001 0002 |................|
              20 | 001E 001F 0001 0003  005E 0060 0061      |.........^.`.a  |
        
        >>> PSContextCoverage().binaryString()
        Traceback (most recent call last):
          ...
        ValueError: Cannot write empty PSContextCoverages!
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if not len(self):
            raise ValueError("Cannot write empty PSContextCoverages!")
        
        w.add("H", 3)
        ctStakes = []
        
        # Note the strong assumption that Python correctly walks the iterators
        # over keys and values in the same way in the following two loops.
        
        for i, key in enumerate(self):
            if i == 0:
                w.add("2H", len(key), len(self[key]))
            
            for ctIndex, covTable in enumerate(key):
                ctStakes.append(w.getNewStake())
                w.addUnresolvedOffset("H", stakeValue, ctStakes[-1])
        
        for value in self.values():
            value.buildBinary(w, **kwArgs)
        
        for ctIndex, covTable in enumerate(key):
            w.stakeCurrentWithValue(ctStakes[ctIndex])
            covTable.buildBinary(w)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PSContextCoverage from the specified
        FontWorkerSource, with source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSContextCoverage.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger = logger,
        ...   editor={})
        FW_test.pscontextcoverage - WARNING - line 14 -- unexpected token: foo
        FW_test.pscontextcoverage - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Key((CoverageSet(frozenset({2})), CoverageSet(frozenset({5})), CoverageSet(frozenset({11})))):
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
        logger = logger.getChild("pscontextcoverage")
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber

        Key = pscontextcoverage_key.Key
        CoverageSet = coverageset.CoverageSet

        coverageList = []
        lookupGroups = {}
        fVFWS = CoverageSet.fromValidatedFontWorkerSource
        
        for line in fws:
            if line.lower() in terminalStrings:
                return cls(lookupGroups)
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() == 'coverage definition begin':
                    coverageSet = fVFWS(fws, logger=logger, **kwArgs)
                    coverageList.append(coverageSet)
                
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
                    
                    key = Key(coverageList)
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
        Creates and returns a new PSContextCoverage object from the specified
        walker, doing source validation. The following keyword arguments are
        supported:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromvalidatedwalker(). The fixup call takes
                        one argument: the Lookup being set into it.
            
            logger      A logger to which messages will be posted.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {ltv[1].asImmutable(): 11, ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> logger = utilities.makeDoctestLogger("pscontextcoverage_test")
        >>> fvb = PSContextCoverage.fromvalidatedbytes
        >>> obj = fvb(s, fixupList=FL, logger=logger)
        pscontextcoverage_test.pscontextcoverage - DEBUG - Walker has 46 bytes remaining.
        pscontextcoverage_test.pscontextcoverage - DEBUG - Format is 3
        pscontextcoverage_test.pscontextcoverage - DEBUG - Coverage count is 3
        pscontextcoverage_test.pscontextcoverage - DEBUG - Action count is 2
        pscontextcoverage_test.pscontextcoverage - DEBUG - Coverage offsets are (20, 28, 36)
        pscontextcoverage_test.pscontextcoverage.coverage 0.coverageset - DEBUG - Walker has 26 remaining bytes.
        pscontextcoverage_test.pscontextcoverage.coverage 0.coverageset - DEBUG - Format is 1, count is 2
        pscontextcoverage_test.pscontextcoverage.coverage 0.coverageset - DEBUG - Raw data are [20, 21]
        pscontextcoverage_test.pscontextcoverage.coverage 1.coverageset - DEBUG - Walker has 18 remaining bytes.
        pscontextcoverage_test.pscontextcoverage.coverage 1.coverageset - DEBUG - Format is 1, count is 2
        pscontextcoverage_test.pscontextcoverage.coverage 1.coverageset - DEBUG - Raw data are [30, 31]
        pscontextcoverage_test.pscontextcoverage.coverage 2.coverageset - DEBUG - Walker has 10 remaining bytes.
        pscontextcoverage_test.pscontextcoverage.coverage 2.coverageset - DEBUG - Format is 1, count is 3
        pscontextcoverage_test.pscontextcoverage.coverage 2.coverageset - DEBUG - Raw data are [94, 96, 97]
        pscontextcoverage_test.pscontextcoverage.pslookupgroup - DEBUG - Walker has 34 bytes remaining.
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 34 remaining bytes.
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 11
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Walker has 30 remaining bytes.
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Sequence index is 1
        pscontextcoverage_test.pscontextcoverage.pslookupgroup.[1].pslookuprecord - DEBUG - Lookup index is 25
        
        >>> fvb(s[:5], fixupList=FL, logger=logger)
        pscontextcoverage_test.pscontextcoverage - DEBUG - Walker has 5 bytes remaining.
        pscontextcoverage_test.pscontextcoverage - ERROR - Insufficient bytes.
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pscontextcoverage")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 3:
            logger.error((
              'V0002',
              (format,),
              "Expected format 3, but got format %d instead."))
            
            return None
        
        logger.debug(('Vxxxx', (), "Format is 3"))
        covCount, posCount = w.unpack("2H")
        logger.debug(('Vxxxx', (covCount,), "Coverage count is %d"))
        logger.debug(('Vxxxx', (posCount,), "Action count is %d"))
        
        if w.length() < 2 * covCount:
            logger.error((
              'V0362',
              (),
              "The offsets to the Coverages are missing or incomplete."))
            
            return None
        
        covOffsets = w.group("H", covCount)
        logger.debug(('Vxxxx', (covOffsets,), "Coverage offsets are %s"))
        fvw = coverageset.CoverageSet.fromvalidatedwalker
        v = [None] * covCount
        
        for i, offset in enumerate(covOffsets):
            cov = fvw(
              w.subWalker(offset),
              logger = logger.getChild("coverage %d" % (i,)))
            
            if cov is None:
                return None
            
            v[i] = cov
        
        key = pscontextcoverage_key.Key(v)
        
        group = pslookupgroup.PSLookupGroup.fromvalidatedwalker(
          w,
          count = posCount,
          fixupList = fixupList,
          logger = logger)
        
        if group is None:
            return None
        
        return cls({key: group})
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSContextCoverage from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromwalker(). The fixup call takes one
                        argument: the Lookup being set into it.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {ltv[1].asImmutable(): 11, ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> obj = PSContextCoverage.frombytes(s, fixupList=FL)
        >>> d = {11: ltv[1], 25: ltv[2]}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == _testingValues[0]
        True
        """
        
        format = w.unpack("H")
        assert format == 3
        covCount, posCount = w.unpack("2H")
        covOffsets = w.group("H", covCount)
        f = coverageset.CoverageSet.fromwalker
        
        key = pscontextcoverage_key.Key(
          f(w.subWalker(offset))
          for offset in covOffsets)
        
        fixupList = kwArgs['fixupList']
        
        group = pslookupgroup.PSLookupGroup.fromwalker(
          w,
          count = posCount,
          fixupList = fixupList)
        
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
            lookupList = self[k]

            for i, cvg in enumerate(k):
                s.write("coverage definition begin\t%d\n" % (i,))
                for g in sorted(cvg):
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
    from fontio3.utilities import namer, writer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    gv = pslookupgroup._testingValues
    kv = pscontextcoverage_key._testingValues
    
    _testingValues = (
        PSContextCoverage({kv[0]: gv[1]}),)
    
    del gv, kv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'F': 2,
        'period': 5,
        'quoteleft': 11,
    }
    _test_FW_namer._initialized = True
    
    def _make_test_FW_lookupDict():
        from fontio3.GPOS import single, value
        
        S = single.Single
        V = value.Value
        
        return {
            'testSingle1': S({3:V(xAdvance=678)}),
            'testSingle2': S({3:V(xAdvance=901)})}
    
    _test_FW_lookupDict = _make_test_FW_lookupDict()

    _test_FW_fws = FontWorkerSource(StringIO(
        """
        coverage definition begin	0
        F
        coverage definition end
        
        coverage definition begin	1
        period
        coverage definition end
        
        coverage definition begin	2
        quoteleft
        coverage definition end
        
        coverage	1,testSingle1	1,testSingle2

        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        coverage definition begin	0
        F
        coverage definition end
        
        coverage definition begin	1
        period
        coverage definition end
        
        coverage definition begin	2
        quoteleft
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
