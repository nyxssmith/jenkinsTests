#
# chainglyph.py
#
# Copyright © 2009-2010, 2012-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 GSUB chaining contextual substitution tables.
"""

# System imports
import collections
import operator

# Other imports
from fontio3 import utilities
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import pschainglyph, runningglyphs

# -----------------------------------------------------------------------------

#
# Classes
#

class ChainGlyph(pschainglyph.PSChainGlyph):
    """
    These are objects representing chained contextual (glyph) mappings. They
    are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    ((xyz13, xyz9), (xyz3,), (xyz6, xyz9, xyz10, xyz31)), Relative order = 0:
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single substitution table):
            xyz3: xyz42
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
    kindString = "Chaining contextual (glyph) substitution table"
    
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
        >>> len(memo)  # will have obj *and* the single substitution subtable
        2
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for key, lkGroup in self.items():
            for lkRec in lkGroup:
                onlyWant = {key[1][lkRec.sequenceIndex]}
                
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
        Key((GlyphTuple((12, 8)), GlyphTuple((2,)), GlyphTuple((5, 8, 9, 30))), ruleOrder=0):
          Effect #1:
            Sequence index: 0
            Lookup:
              Subtable 0 (Single substitution table):
                2: 41
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        
        >>> ga = runningglyphs.GlyphList.fromiterable([19, 12, 77, 8, 2, 5, 8, 77, 9, 30])
        >>> igsFunc = lambda *a, **k: [False, False, True, False, False, False, False, True, False, False]
        >>> r, count = obj.runOne(ga, 0, igsFunc=igsFunc)
        >>> count
        0
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 4, igsFunc=igsFunc)
        >>> count
        1
        >>> r.pprint()
        0:
          Value: 19
          originalOffset: 0
        1:
          Value: 12
          originalOffset: 1
        2:
          Value: 77
          originalOffset: 2
        3:
          Value: 8
          originalOffset: 3
        4:
          Value: 41
          originalOffset: 4
        5:
          Value: 5
          originalOffset: 5
        6:
          Value: 8
          originalOffset: 6
        7:
          Value: 77
          originalOffset: 7
        8:
          Value: 9
          originalOffset: 8
        9:
          Value: 30
          originalOffset: 9
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
          lookup,
          pschainglyph_glyphtuple,
          pschainglyph_key,
          pslookupgroup,
          pslookuprecord)
        
        single_obj = single.Single({2: 41})
        lookup_obj = lookup.Lookup([single_obj], sequence=0)
        pslookuprecord_obj = pslookuprecord.PSLookupRecord(0, lookup_obj)
        pslookupgroup_obj = pslookupgroup.PSLookupGroup([pslookuprecord_obj])
        tBack = pschainglyph_glyphtuple.GlyphTuple([12, 8])
        tIn = pschainglyph_glyphtuple.GlyphTuple([2])
        tLook = pschainglyph_glyphtuple.GlyphTuple([5, 8, 9, 30])
        key_obj = pschainglyph_key.Key([tBack, tIn, tLook])
        return ChainGlyph({key_obj: pslookupgroup_obj})
    
    _testingValues = (
        _makeTV(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
