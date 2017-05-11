#
# chainglyph.py
#
# Copyright © 2009-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved
#

"""
Support for format 1 GPOS chaining contextual positioning tables.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GPOS import effect
from fontio3.opentype import pschainglyph, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ChainGlyph(pschainglyph.PSChainGlyph):
    """
    These are objects representing chained contextual (glyph) mappings. They
    are dicts mapping Keys to PSLookupGroups.
    
    >>> obj, ed = _makeTest()
    >>> obj.pprint()
    Key((GlyphTuple((25,)), GlyphTuple((80,)), GlyphTuple((26,))), ruleOrder=0):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single positioning table):
            80:
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
    kindString = "Chaining contextual (glyph) positioning table"
    
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
        """
        
        cache = kwArgs.pop('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        
        for key, lkGroup in self.items():
            rCumul = {}
            
            for lkRec in lkGroup:
                glyph = key[1][lkRec.sequenceIndex]
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
        >>> obj.pprint()
        Key((GlyphTuple((25,)), GlyphTuple((80,)), GlyphTuple((26,))), ruleOrder=0):
          Effect #1:
            Sequence index: 0
            Lookup:
              Subtable 0 (Single positioning table):
                80:
                  FUnit adjustment to origin's x-coordinate: -25
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        >>> ga = runningglyphs.GlyphList.fromiterable([14, 25, 77, 80, 77, 26])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, True, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> (r, count)
        (None, 0)
        
        >>> r, count = obj.runOne(ga, 3, igsFunc=igsFunc)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 14, originalOffset = 0 
        glyph 25, originalOffset = 1 
        glyph 77, originalOffset = 2 
        glyph 80, originalOffset = 3 xPlacementDelta = -25
        glyph 77, originalOffset = 4 
        glyph 26, originalOffset = 5 
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
            if firstGlyph != key[1][0]:
                continue
            
            backLen, inLen, lookLen = [len(x) for x in key]
            totalLen = backLen + inLen + lookLen
            
            if backLen > startIndexNI:
                continue
            
            if (inLen + lookLen) > (len(vNonIgs) - startIndexNI):
                continue
            
            pieceStart = startIndexNI - backLen
            piece = vNonIgs[pieceStart:pieceStart+totalLen]
            
            if not all(a == b for a, b in zip(piece, sum(key, ()))):
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
        """
        The test case here recognizes the glyph sequence 25-80-26, where 25 is
        the backtrack and 26 the lookahead. The position of glyph 80 is
        adjusted.
        """
        
        from fontio3 import hmtx, utilities
        from fontio3.GPOS import single, value
        
        from fontio3.opentype import (
          lookup,
          pschainglyph_glyphtuple,
          pschainglyph_key,
          pslookupgroup,
          pslookuprecord)
        
        s1 = single.Single({80: value.Value(xPlacement=-25)})
        lk1 = lookup.Lookup([s1])
        psr1 = pslookuprecord.PSLookupRecord(0, lk1)
        psg1 = pslookupgroup.PSLookupGroup([psr1])
        backPart = pschainglyph_glyphtuple.GlyphTuple([25])
        inPart = pschainglyph_glyphtuple.GlyphTuple([80])
        lookPart = pschainglyph_glyphtuple.GlyphTuple([26])
        key1 = pschainglyph_key.Key([backPart, inPart, lookPart])
        r = ChainGlyph({key1: psg1})
        e = utilities.fakeEditor(0x10000)
        e.hmtx = hmtx.Hmtx()
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
