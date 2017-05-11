#
# chaincoverage.py
#
# Copyright © 2009-2010, 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 3 GSUB chaining contextual substitution tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import pschaincoverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ChainCoverage(pschaincoverage.PSChainCoverage):
    """
    Objects containing format 3 chaining contextual GSUB lookups.
    
    These are dicts mapping a single Key to a PSLookupGroup. (Note that in the
    future, if OpenType permits a format for multiple entries instead of a
    single entry, the existing dict will suffice).
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (({xyz19, xyz30, xyz4}, {xyz30, xyz91}), ({xyz3, xyz7},), ({xyz53, xyz54}, {xyz54, xyz55, xyz56})):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single substitution table):
            xyz3: xyz42
            xyz7: xyz44
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
    
    kind = ('GSUB', 6)
    kindString = "Chaining contextual (coverage) substitution table"
    
    #
    # Methods
    #
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectsSummary() instead.")
    
    def effectsSummary(self, **kwArgs):
        """
        Returns an EffectsSummary object. If present, notes will be made in a
        provided memo kwArgs to allow elision of reprocessing, which should
        eliminate the combinatoric explosion.
        
        >>> obj = _testingValues[0]
        >>> memo = {}
        >>> es = obj.effectsSummary(memo=memo)
        >>> es.pprint()
        2:
          41
        6:
          43
        >>> len(memo)  # will have obj *and* the single substitution subtable
        2
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for key, lkGroup in self.items():
            for lkRec in lkGroup:
                onlyWant = key[1][lkRec.sequenceIndex]
                
                for sub in lkRec.lookup:
                    if id(sub) not in memo:
                        memo[id(sub)] = sub.effectsSummary(**kwArgs)
                    
                    r.updateSets(memo[id(sub)], onlyWant=onlyWant)
        
        memo[id(self)] = r
        return r
    
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
        >>> obj.pprint()
        Key((CoverageTuple((CoverageSet(frozenset({18, 3, 29})), CoverageSet(frozenset({90, 29})))), CoverageTuple((CoverageSet(frozenset({2, 6})),)), CoverageTuple((CoverageSet(frozenset({52, 53})), CoverageSet(frozenset({53, 54, 55})))))):
          Effect #1:
            Sequence index: 0
            Lookup:
              Subtable 0 (Single substitution table):
                2: 41
                6: 43
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        
        >>> ga = runningglyphs.GlyphList.fromiterable([3, 77, 90, 6, 52, 77, 55])
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
          Value: 3
          originalOffset: 0
        1:
          Value: 77
          originalOffset: 1
        2:
          Value: 90
          originalOffset: 2
        3:
          Value: 43
          originalOffset: 3
        4:
          Value: 52
          originalOffset: 4
        5:
          Value: 77
          originalOffset: 5
        6:
          Value: 55
          originalOffset: 6
        """
        
        # We pop the igsFunc because the lookups we're going to call to do the
        # effects might have different flags.
        
        igsFunc = kwArgs.pop('igsFunc')
        igs = igsFunc(glyphArray, **kwArgs)
        useLLOrder = kwArgs.get('useLLOrder', True)
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
            if firstGlyph not in key[1][0]:
                continue
            
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
            
            r = glyphArray.fromiterable(glyphArray)  # preserves offsets
            
            if useLLOrder:
                v = [(obj, obj.lookup.sequence) for obj in self[key]]
                it = [t[0] for t in sorted(v, key=operator.itemgetter(1))]
            
            else:
                it = self[key]
            
            count = vBackMap[startIndexNI + inLen - 1] - vBackMap[startIndexNI] + 1
            
            for effIndex, eff in enumerate(it):
                rNew, subCount = eff.lookup.runOne_GSUB(
                  r,
                  startIndex = vBackMap[startIndexNI + eff.sequenceIndex],
                  **kwArgs)
                
                if not subCount:
                    continue
                
                # The effect's Lookup did something. This might affect the igs
                # so they need to be recalculated, and the vNonIgs and vBackMap
                # then also need to be redone.
                
                if effIndex < (len(it) - 1):
                    igs = igsFunc(rNew, **kwArgs)
                
                    v = [
                      (g, i)
                      for i, g in enumerate(rNew)
                      if (not igs[i])]
        
                    vNonIgs = [x[0] for x in v]
                    vBackMap = [x[1] for x in v]
                    assert startIndexNI == vBackMap.index(startIndex)
                
                delta = len(rNew) - len(r)
                count += delta
                r = rNew
            
            return (r, count)
        
        return (glyphArray, 0)
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    def _makeTV():
        from fontio3.GSUB import single
        
        from fontio3.opentype import (
          coverageset,
          lookup,
          pschaincoverage_coveragetuple,
          pschaincoverage_key,
          pslookupgroup,
          pslookuprecord)
        
        single_obj = single.Single({2: 41, 6: 43})
        lookup_obj = lookup.Lookup([single_obj], sequence=0)
        pslookuprecord_obj = pslookuprecord.PSLookupRecord(0, lookup_obj)
        pslookupgroup_obj = pslookupgroup.PSLookupGroup([pslookuprecord_obj])
        
        tBack = pschaincoverage_coveragetuple.CoverageTuple([
          coverageset.CoverageSet([3, 18, 29]),
          coverageset.CoverageSet([29, 90])])
        
        tIn = pschaincoverage_coveragetuple.CoverageTuple([
          coverageset.CoverageSet([2, 6])])
        
        tLook = pschaincoverage_coveragetuple.CoverageTuple([
          coverageset.CoverageSet([52, 53]),
          coverageset.CoverageSet([53, 54, 55])])
        
        key_obj = pschaincoverage_key.Key([tBack, tIn, tLook])
        return ChainCoverage({key_obj: pslookupgroup_obj})
    
    _testingValues = (
        _makeTV(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
