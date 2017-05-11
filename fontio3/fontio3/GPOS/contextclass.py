#
# contextclass.py
#
# Copyright © 2009-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 GPOS contextual positioning tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GPOS import effect
from fontio3.opentype import pscontextclass, runningglyphs
    
# -----------------------------------------------------------------------------

#
# Classes
#

class ContextClass(pscontextclass.PSContextClass):
    """
    Objects containing format 2 contextual GPOS lookups.
    
    These are dicts mapping Keys to PSLookupGroups.
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Key((1, 2, 3), ruleOrder=0):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single positioning table):
            20:
              FUnit adjustment to origin's x-coordinate: -25
            25:
              FUnit adjustment to origin's x-coordinate: -29
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 0
      Effect #2:
        Sequence index: 2
        Lookup:
          Subtable 0 (Single positioning table):
            26:
              FUnit adjustment to origin's x-coordinate: 25
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 0
    Class definition table:
      20: 1
      25: 1
      26: 3
      80: 2
      81: 2
    """
    
    #
    # Class constants
    #
    
    kind = ('GPOS', 7)
    kindString = "Contextual (class) positioning table"
    
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
        20 (0, -25)
        25 (0, -29)
        26 (25, 0)
        """
        
        cache = kwArgs.pop('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        revMap = utilities.invertDictFull(self.classDef, asSets=True)
        c0Glyphs = None
        
        for key, lkGroup in self.items():
            rCumul = {}
            
            for lkRec in lkGroup:
                cls = key[lkRec.sequenceIndex]
                lk = lkRec.lookup
                
                if cls:
                    gSet = revMap[cls]
                
                else:
                    if c0Glyphs is None:
                        count = utilities.getFontGlyphCount(**kwArgs)
                        c0Glyphs = set(range(count))
                        
                        for remove in revMap.values():
                            c0Glyphs -= remove
                    
                    gSet = c0Glyphs
                
                for subtable in lk:
                    rSub = subtable.effectExtrema(
                      forHorizontal,
                      cache = cache,
                      **kwArgs)
                    
                    for glyph in gSet:
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
        Key((1, 2, 3), ruleOrder=0):
          Effect #1:
            Sequence index: 0
            Lookup:
              Subtable 0 (Single positioning table):
                20:
                  FUnit adjustment to origin's x-coordinate: -25
                25:
                  FUnit adjustment to origin's x-coordinate: -29
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
          Effect #2:
            Sequence index: 2
            Lookup:
              Subtable 0 (Single positioning table):
                26:
                  FUnit adjustment to origin's x-coordinate: 25
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        Class definition table:
          20: 1
          25: 1
          26: 3
          80: 2
          81: 2
        >>> ga = runningglyphs.GlyphList.fromiterable([14, 25, 77, 80, 77, 26])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, True, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> (r, count)
        (None, 0)
        
        >>> r, count = obj.runOne(ga, 1, igsFunc=igsFunc)
        >>> count
        5
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 14, originalOffset = 0 
        glyph 25, originalOffset = 1 xPlacementDelta = -29
        glyph 77, originalOffset = 2 
        glyph 80, originalOffset = 3 
        glyph 77, originalOffset = 4 
        glyph 26, originalOffset = 5 xPlacementDelta = 25
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
        cd = self.classDef
        
        for key in self:  # custom order, remember...
            if cd.get(firstGlyph, 0) != key[0]:
                continue
            
            if len(key) > len(vNonIgs):
                continue
            
            if not all(a == cd.get(b, 0) for a, b in zip(key, vNonIgs)):
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
            
            count = vBackMap[len(key) - 1] - vBackMap[0] + 1
            
            for eff in it:
                rNew, subCount = eff.lookup.runOne_GPOS(
                  glyphArray,
                  startIndex = vBackMap[eff.sequenceIndex],
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
        """
        The test case here recognizes the glyph sequence 1-2-3, and adjusts the
        positioning of classes 1 and 3.
        """
        
        from fontio3 import hmtx, utilities
        from fontio3.GPOS import single, value
        
        from fontio3.opentype import (
          classdef,
          lookup,
          pscontextclass_key,
          pslookupgroup,
          pslookuprecord)
        
        v1 = value.Value(xPlacement=-25)
        v2 = value.Value(xPlacement=-29)
        s1 = single.Single({20: v1, 25: v2})
        lk1 = lookup.Lookup([s1])
        psr1 = pslookuprecord.PSLookupRecord(0, lk1)
        s2 = single.Single({26: value.Value(xPlacement=25)})
        lk2 = lookup.Lookup([s2])
        psr2 = pslookuprecord.PSLookupRecord(2, lk2)
        psg = pslookupgroup.PSLookupGroup([psr1, psr2])
        key = pscontextclass_key.Key([1, 2, 3])
        cd = classdef.ClassDef({20: 1, 25: 1, 80: 2, 81: 2, 26: 3})
        r = ContextClass({key: psg}, classDef=cd)
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[20] = hmtx.MtxEntry(910, 42)
        e.hmtx[25] = hmtx.MtxEntry(900, 50)
        e.hmtx[26] = hmtx.MtxEntry(970, 40)
        e.hmtx[80] = hmtx.MtxEntry(1020, 55)
        e.hmtx[81] = hmtx.MtxEntry(1090, 85)
        
        return r, e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
