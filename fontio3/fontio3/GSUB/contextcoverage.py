#
# contextcoverage.py
#
# Copyright © 2009-2010, 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 3 GSUB contextual substitution tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import pscontextcoverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ContextCoverage(pscontextcoverage.PSContextCoverage):
    """
    Objects containing format 3 contextual GSUB lookups.
    
    These are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    ({xyz10, xyz11, xyz3}, {xyz3, xyz6}):
      Effect #1:
        Sequence index: 1
        Lookup:
          Subtable 0 (Single substitution table):
            xyz3: xyz42
            xyz6: xyz43
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
    
    kind = ('GSUB', 5)
    kindString = "Contextual (coverage) substitution table"
    
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
        5:
          42
        >>> len(memo)  # will have obj *and* the single substitution subtable
        2
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for key, lkGroup in self.items():
            for lkRec in lkGroup:
                onlyWant = key[lkRec.sequenceIndex]
                
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
        Key((CoverageSet(frozenset({9, 2, 10})), CoverageSet(frozenset({2, 5})))):
          Effect #1:
            Sequence index: 1
            Lookup:
              Subtable 0 (Single substitution table):
                2: 41
                5: 42
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        
        >>> ga = runningglyphs.GlyphList.fromiterable([6, 10, 77, 5])
        >>> igsFunc = lambda *a, **k: [False, False, True, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> count
        0
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc)
        >>> count
        3
        >>> r.pprint()
        0:
          Value: 6
          originalOffset: 0
        1:
          Value: 10
          originalOffset: 1
        2:
          Value: 77
          originalOffset: 2
        3:
          Value: 42
          originalOffset: 3
        """
        
        # We pop the igsFunc because the lookups we're going to call to do the
        # effects might have different flags.
        
        igsFunc = kwArgs.pop('igsFunc')
        igs = igsFunc(glyphArray, **kwArgs)
        useLLOrder = kwArgs.get('useLLOrder', True)
        firstGlyph = glyphArray[startIndex]
        
        # To make comparisons in the loop easier, we use the igs data to
        # extract just the non-ignorables starting with startIndex into a
        # separate list called vNonIgs.
        
        v = [
          (g, i)
          for i, g in enumerate(glyphArray[startIndex:], start=startIndex)
          if (not igs[i])]
        
        vNonIgs = [x[0] for x in v]
        vBackMap = [x[1] for x in v]
        
        for key in self:  # custom order, remember...
            if firstGlyph not in key[0]:
                continue
            
            if len(key) > len(vNonIgs):
                continue
            
            if not all(b in a for a, b in zip(key, vNonIgs)):
                continue
            
            # If we get here the key is a match
            
            r = glyphArray.fromiterable(glyphArray)  # preserves offsets
            
            if useLLOrder:
                v = [(obj, obj.lookup.sequence) for obj in self[key]]
                it = [t[0] for t in sorted(v, key=operator.itemgetter(1))]
            
            else:
                it = self[key]
            
            count = vBackMap[len(key) - 1] - vBackMap[0] + 1
            
            for effIndex, eff in enumerate(it):
                rNew, subCount = eff.lookup.runOne_GSUB(
                  r,
                  startIndex = vBackMap[eff.sequenceIndex],
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
                      for i, g in enumerate(rNew[startIndex:], start=startIndex)
                      if (not igs[i])]
        
                    vNonIgs = [x[0] for x in v]
                    vBackMap = [x[1] for x in v]
                
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
          pscontextcoverage_key,
          pslookupgroup,
          pslookuprecord)
        
        single_obj = single.Single({2: 41, 5: 42})
        lookup_obj = lookup.Lookup([single_obj], sequence=0)
        pslookuprecord_obj = pslookuprecord.PSLookupRecord(1, lookup_obj)
        pslookupgroup_obj = pslookupgroup.PSLookupGroup([pslookuprecord_obj])
        coverageset_obj_1 = coverageset.CoverageSet([2, 9, 10])
        coverageset_obj_2 = coverageset.CoverageSet([2, 5])
        
        key_obj = pscontextcoverage_key.Key([
          coverageset_obj_1,
          coverageset_obj_2])
        
        return ContextCoverage({key_obj: pslookupgroup_obj})
    
    _testingValues = (
        _makeTV(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
