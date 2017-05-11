#
# contextclass.py
#
# Copyright © 2009-2010, 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 GSUB contextual substitution tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import pscontextclass, runningglyphs
    
# -----------------------------------------------------------------------------

#
# Classes
#

class ContextClass(pscontextclass.PSContextClass):
    """
    Objects containing format 2 contextual GSUB lookups.
    
    These are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Key((1, 2, 1, 3), ruleOrder=0):
      Effect #1:
        Sequence index: 1
        Lookup:
          Subtable 0 (Single substitution table):
            xyz3: xyz42
            xyz9: xyz43
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 0
    Class definition table:
      xyz13: 3
      xyz20: 1
      xyz3: 2
      xyz9: 2
    """
    
    #
    # Class constants
    #
    
    kind = ('GSUB', 5)
    kindString = "Contextual (class) substitution table"
    
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
        8:
          42
        >>> len(memo)  # will have obj *and* the single substitution subtable
        2
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        revMap = utilities.invertDictFull(self.classDef, asSets=True)
        
        for key, lkGroup in self.items():
            for lkRec in lkGroup:
                ci = key[lkRec.sequenceIndex]
                
                if ci:
                    onlyWant = revMap[ci]
                else:
                    onlyWant = self.coverageExtras
                
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
        Key((1, 2, 1, 3), ruleOrder=0):
          Effect #1:
            Sequence index: 1
            Lookup:
              Subtable 0 (Single substitution table):
                2: 41
                8: 42
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        Class definition table:
          2: 2
          8: 2
          12: 3
          19: 1
        
        >>> ga = runningglyphs.GlyphList.fromiterable([4, 19, 77, 8, 19, 12, 5])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, False, False, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> count
        0
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc)
        >>> count
        5
        >>> r.pprint()
        0:
          Value: 4
          originalOffset: 0
        1:
          Value: 19
          originalOffset: 1
        2:
          Value: 77
          originalOffset: 2
        3:
          Value: 42
          originalOffset: 3
        4:
          Value: 19
          originalOffset: 4
        5:
          Value: 12
          originalOffset: 5
        6:
          Value: 5
          originalOffset: 6
        """
        
        # We pop the igsFunc because the lookups we're going to call to do the
        # effects might have different flags.
        
        igsFunc = kwArgs.pop('igsFunc')
        igs = igsFunc(glyphArray, **kwArgs)
        useLLOrder = kwArgs.get('useLLOrder', True)
        firstGlyph = glyphArray[startIndex]
        cd = self.classDef
        
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
            if cd.get(firstGlyph, 0) != key[0]:
                continue
            
            if len(key) > len(vNonIgs):
                continue
            
            if not all(a == cd.get(b, 0) for a, b in zip(key, vNonIgs)):
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
          classdef,
          lookup,
          pscontextclass_key,
          pslookupgroup,
          pslookuprecord)
        
        single_obj = single.Single({2: 41, 8: 42})
        lookup_obj = lookup.Lookup([single_obj], sequence=0)
        pslookuprecord_obj = pslookuprecord.PSLookupRecord(1, lookup_obj)
        pslookupgroup_obj = pslookupgroup.PSLookupGroup([pslookuprecord_obj])
        key_obj = pscontextclass_key.Key([1, 2, 1, 3])
        classdef_obj = classdef.ClassDef({19: 1, 2: 2, 8: 2, 12: 3})
        
        return ContextClass(
          {key_obj: pslookupgroup_obj},
          classDef=classdef_obj)
    
    _testingValues = (
        _makeTV(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
