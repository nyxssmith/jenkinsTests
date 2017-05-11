#
# contextglyph.py
#
# Copyright © 2009-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 GPOS contextual positioning tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GPOS import effect
from fontio3.opentype import pscontextglyph, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ContextGlyph(pscontextglyph.PSContextGlyph):
    """
    These are identical to PSContextGlyphs, with the addition of the kind and
    kindString class constants.
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Key((12, 15, 12), ruleOrder=1):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single positioning table):
            12:
              FUnit adjustment to origin's x-coordinate: -15
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
            12:
              FUnit adjustment to origin's x-coordinate: 15
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 0
    Key((25, 80, 26), ruleOrder=0):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single positioning table):
            25:
              FUnit adjustment to origin's x-coordinate: -25
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
    """
    
    #
    # Class constants
    #
    
    kind = ('GPOS', 7)
    kindString = "Contextual (glyph) positioning table"
    
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
        12 (15, -15)
        25 (0, -25)
        26 (25, 0)
        
        >>> d = obj.effectExtrema(forHorizontal=True, editor=ed)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        """
        
        cache = kwArgs.pop('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        
        for key, lkGroup in self.items():
            rCumul = {}
            
            for lkRec in lkGroup:
                glyph = key[lkRec.sequenceIndex]
                lk = lkRec.lookup
                
                for subtable in lk:
                    rSub = subtable.effectExtrema(
                      forHorizontal,
                      cache = cache,
                      **kwArgs)
                    
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
        glyph 25, originalOffset = 1 xPlacementDelta = -25
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
        
        for key in self:  # custom order, remember...
            if firstGlyph != key[0]:
                continue
            
            if len(key) > len(vNonIgs):
                continue
            
            if not all(a == b for a, b in zip(key, vNonIgs)):
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
        The test case here recognizes the glyph sequence 25-80-26, and adjusts
        the positioning of glyphs 25 and 26.
        """
        
        from fontio3 import hmtx
        from fontio3.GPOS import single, value
        
        from fontio3.opentype import (
          lookup,
          pscontextglyph_key,
          pslookupgroup,
          pslookuprecord)
        
        s1 = single.Single({25: value.Value(xPlacement=-25)})
        s2 = single.Single({26: value.Value(xPlacement=25)})
        s3 = single.Single({12: value.Value(xPlacement=-15)})
        s4 = single.Single({12: value.Value(xPlacement=15)})
        
        lk1 = lookup.Lookup([s1])
        lk2 = lookup.Lookup([s2])
        lk3 = lookup.Lookup([s3])
        lk4 = lookup.Lookup([s4])
        
        psr1 = pslookuprecord.PSLookupRecord(0, lk1)
        psr2 = pslookuprecord.PSLookupRecord(2, lk2)
        psr3 = pslookuprecord.PSLookupRecord(0, lk3)
        psr4 = pslookuprecord.PSLookupRecord(2, lk4)
        
        psg1 = pslookupgroup.PSLookupGroup([psr1, psr2])
        psg2 = pslookupgroup.PSLookupGroup([psr3, psr4])
        key1 = pscontextglyph_key.Key([25, 80, 26], ruleOrder=0)
        key2 = pscontextglyph_key.Key([12, 15, 12], ruleOrder=1)
        
        r = ContextGlyph({key1: psg1, key2: psg2})
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
        e.hmtx[12] = hmtx.MtxEntry(700, 50)
        e.hmtx[15] = hmtx.MtxEntry(690, 50)
        e.hmtx[25] = hmtx.MtxEntry(900, 50)
        e.hmtx[26] = hmtx.MtxEntry(970, 40)
        e.hmtx[80] = hmtx.MtxEntry(1020, 55)
        
        return r, e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
