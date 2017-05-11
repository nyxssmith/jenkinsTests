#
# chaincoverage.py
#
# Copyright © 2009-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 3 GPOS chaining contextual positioning tables.
"""

# System imports
import operator

# Other imports
from fontio3 import utilities
from fontio3.GPOS import effect
from fontio3.opentype import pschaincoverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ChainCoverage(pschaincoverage.PSChainCoverage):
    """
    Objects containing format 3 chaining contextual GPOS lookups.
    
    These are dicts mapping a single Key to a PSLookupGroup. (Note that in the
    future, if OpenType permits a format for multiple entries instead of a
    single entry, the existing dict will suffice).
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Key((CoverageTuple((CoverageSet(frozenset({20, 22})), CoverageSet(frozenset({23})))), CoverageTuple((CoverageSet(frozenset({80, 81, 82})),)), CoverageTuple((CoverageSet(frozenset({22})), CoverageSet(frozenset({40, 20})))))):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single positioning table):
            80:
              FUnit adjustment to origin's x-coordinate: -25
            81:
              FUnit adjustment to origin's x-coordinate: -29
            82:
              FUnit adjustment to origin's x-coordinate: -25
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 0
    """
    
    #
    # Class constants
    #
    
    kind = ('GPOS', 8)
    kindString = "Chaining contextual (coverage) positioning table"
    
    #
    # Methods
    #
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectExtrema() instead.")
    
    def effectExtrema(self, forHorizontal=True, **kwArgs):
        """
        Returns a dict, indexed by glyph, of pairs of values. If
        forHorizontal is True, these values will be the yMaxDelta and
        yMinDelta; if False, they will be the xMaxDelta and xMinDelta. These
        values can then be used to test against the font's ascent/descent
        values in order to show VDMA-like output, or to be accumulated across
        all the features that are performed for a given script and lang/sys.
        
        Note that either or both of these values may be None; this can arise
        for cases like mark-to-mark, where potentially infinite stacking of
        marks can occur.
        
        The following keyword arguments are used:
            
            cache               A dict mapping object IDs to result dicts.
                                This is used during processing to speed up
                                analysis of deeply nested subtables, so the
                                effectExtrema() call need only be made once per
                                subtable.
            
            editor              The Editor object containing this subtable.
        
        >>> obj, ed = _makeTest()
        >>> d = obj.effectExtrema(forHorizontal=False, editor=ed)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        80 (0, -25)
        81 (0, -29)
        82 (0, -25)
        """
        
        cache = kwArgs.pop('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        
        for key, lkGroup in self.items():
            rCumul = {}
            
            for lkRec in lkGroup:
                cov = key[1][lkRec.sequenceIndex]
                lk = lkRec.lookup
                
                for subtable in lk:
                    rSub = subtable.effectExtrema(
                      forHorizontal,
                      cache = cache,
                      **kwArgs)
                    
                    for glyph in cov:
                        if glyph in rSub:
                            if glyph not in rCumul:
                                rCumul[glyph] = rSub[glyph]
                        
                            else:
                                if rCumul[glyph][0] is None or rSub[glyph][0] is None:
                                    new0 = None
                                else:
                                    new0 = rCumul[glyph][0] + rSub[glyph][0]
                            
                                if rCumul[glyph][1] is None or rSub[glyph][1] is None:
                                    new1 = None
                                else:
                                    new1 = rCumul[glyph][1] + rSub[glyph][1]
                            
                                rCumul[glyph] = (new0, new1)
            
            for glyph, (valHi, valLo) in rCumul.items():
                if glyph not in r:
                    r[glyph] = (valHi, valLo)
                
                else:
                    oldHi, oldLo = r[glyph]
                    
                    if oldHi is None or valHi is None:
                        newHi = None
                    else:
                        newHi = max(oldHi, valHi)
                    
                    if oldLo is None or valLo is None:
                        newLo = None
                    else:
                        newLo = min(oldLo, valLo)
                    
                    r[glyph] = (newHi, newLo)
        
        cache[id(self)] = r
        return r
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        
        >>> obj, ed = _makeTest()
        >>> obj.pprint()
        Key((CoverageTuple((CoverageSet(frozenset({20, 22})), CoverageSet(frozenset({23})))), CoverageTuple((CoverageSet(frozenset({80, 81, 82})),)), CoverageTuple((CoverageSet(frozenset({22})), CoverageSet(frozenset({40, 20})))))):
          Effect #1:
            Sequence index: 0
            Lookup:
              Subtable 0 (Single positioning table):
                80:
                  FUnit adjustment to origin's x-coordinate: -25
                81:
                  FUnit adjustment to origin's x-coordinate: -29
                82:
                  FUnit adjustment to origin's x-coordinate: -25
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        >>> ga = runningglyphs.GlyphList.fromiterable([14, 20, 77, 23, 80, 77, 22, 40])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, False, True, False, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> (r, count)
        (None, 0)
        
        >>> r, count = obj.runOne(ga, 4, igsFunc=igsFunc)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 14, originalOffset = 0 
        glyph 20, originalOffset = 1 
        glyph 77, originalOffset = 2 
        glyph 23, originalOffset = 3 
        glyph 80, originalOffset = 4 xPlacementDelta = -25
        glyph 77, originalOffset = 5 
        glyph 22, originalOffset = 6 
        glyph 40, originalOffset = 7 
        """
        
        # We pop the igsFunc because the lookups we're going to call to do the
        # effects might have different flags.
        
        igsFunc = kwArgs.pop('igsFunc')
        igs = igsFunc(glyphArray, **kwArgs)
        useLLOrder = kwArgs.get('useLLOrder', True)
        
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
            backLen, inLen, lookLen = [len(x) for x in key]
            totalLen = backLen + inLen + lookLen
            
            if backLen > startIndexNI:
                continue
            
            if (inLen + lookLen) > (len(vNonIgs) - startIndexNI):
                continue
            
            pieceStart = startIndexNI - backLen
            piece = vNonIgs[pieceStart:pieceStart+totalLen]
            
            if not all(a in b for a, b in zip(piece, sum(key, ()))):
                continue
            
            # If we get here the key is a match
            
            E = effect.Effect
            
            if 'cumulEffects' in kwArgs:
                r = kwArgs.pop('cumulEffects')
            else:
                r = [E() for g in glyphArray]
            
            if useLLOrder:
                v = [(obj, obj.lookup.sequence) for obj in self[key]]
                it = [t[0] for t in sorted(v, key=operator.itemgetter(1))]
            
            else:
                it = self[key]
            
            count = vBackMap[startIndexNI + inLen - 1] - vBackMap[startIndexNI] + 1
            
            for eff in it:
                rNew, subCount = eff.lookup.runOne_GPOS(
                  glyphArray,
                  startIndex = vBackMap[startIndexNI + eff.sequenceIndex],
                  cumulEffects = r,
                  **kwArgs)
                
                if subCount:
                    r = rNew
            
            return (r, count)
        
        return (None, 0)
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeTest():
        from fontio3 import hmtx, utilities
        from fontio3.GPOS import single, value
        
        from fontio3.opentype import (
          coverageset,
          lookup,
          pschaincoverage_coveragetuple,
          pschaincoverage_key,
          pslookupgroup,
          pslookuprecord)
        
        v1 = value.Value(xPlacement=-25)
        v2 = value.Value(xPlacement=-29)
        s1 = single.Single({80: v1, 81: v2, 82: v1})
        lk1 = lookup.Lookup([s1])
        psr1 = pslookuprecord.PSLookupRecord(0, lk1)
        psg = pslookupgroup.PSLookupGroup([psr1])
        
        cs1 = coverageset.CoverageSet([20, 22])
        cs2 = coverageset.CoverageSet([23])
        cs3 = coverageset.CoverageSet([80, 81, 82])
        cs4 = coverageset.CoverageSet([22])
        cs5 = coverageset.CoverageSet([20, 40])
        ct1 = pschaincoverage_coveragetuple.CoverageTuple([cs1, cs2])
        ct2 = pschaincoverage_coveragetuple.CoverageTuple([cs3])
        ct3 = pschaincoverage_coveragetuple.CoverageTuple([cs4, cs5])
        key = pschaincoverage_key.Key([ct1, ct2, ct3])
        
        r = ChainCoverage({key: psg})
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[20] = hmtx.MtxEntry(910, 42)
        e.hmtx[22] = hmtx.MtxEntry(900, 50)
        e.hmtx[23] = hmtx.MtxEntry(970, 40)
        e.hmtx[40] = hmtx.MtxEntry(890, 8)
        e.hmtx[80] = hmtx.MtxEntry(1020, 55)
        e.hmtx[81] = hmtx.MtxEntry(1090, 85)
        e.hmtx[82] = hmtx.MtxEntry(1020, 55)
        
        return r, e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
