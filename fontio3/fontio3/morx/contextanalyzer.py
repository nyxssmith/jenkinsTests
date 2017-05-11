#
# contextanalyzer.py
#
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing 'morx' contextual subtables to build up Python-style
dictionaries mapping marked and current glyph sets to output glyphs for each
entry index in the subtable.
"""

# Other imports
from fontio3.statetables import stutils
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Classes
#

class Analyzer:
    """
    Objects performing contextual analysis for 'morx' type 2 subtables.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, w):
        self.w = w
        self.analysis = None
    
    #
    # Private methods and functions
    #
    
    def _buildInputs(self):
        self.w.reset()
        t = self.w.unpack("5L")
        self.numClasses, oCT, oSA, oET, oGT = t
        wCT, wSA, wET, wGT = stutils.offsetsToSubWalkers(self.w, *t[1:])
        self.entryTable = wET.unpackRest("4H", strict=False)
        
        self.numStates = max(
          int(wSA.length()) // (2 * self.numClasses),
          1 + max(t[0] for t in self.entryTable))
        
        self.classMap = lookup.Lookup.fromwalker(wCT)
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: v for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = {0xFFFF}
        
        self.emptyClasses = (
          set(range(4, self.numClasses)) - set(self.classToGlyphs))
        
        self.stateArray = wSA.group("H" * self.numClasses, self.numStates)
        
        numLookups = 1 + max(
          n
          for t in self.entryTable
          for n in t[2:4]
          if n != 0xFFFF)
        
        self.glyphLookups = [None] * numLookups
        offsets = wGT.group("L", numLookups)
        
        for i, offset in enumerate(offsets):
            wSub = wGT.subWalker(offset)
            self.glyphLookups[i] = lookup.Lookup_OutGlyph.fromwalker(wSub)
    
    def _buildInputs_validated(self, logger):
        self.w.reset()
        stBaseOffset = self.w.getOffset()
        
        if self.w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        t = self.w.unpack("5L")
        self.numClasses, oCT, oSA, oET, oGT = t
        
        if self.numClasses < 4:
            logger.error((
              'V0634',
              (self.numClasses,),
              "The number of classes in a state table must be at least "
              "four, but is only %d."))
            
            return False
        
        firstValid = self.w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + self.w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in t[1:]):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return False
        
        wCT, wSA, wET, wGT = stutils.offsetsToSubWalkers(self.w, *t[1:])
        self.entryTable = wET.unpackRest("4H", strict=False)
        
        if not self.entryTable:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
            return False
        
        if len(self.entryTable) != len(set(self.entryTable)):
            logger.error((
              'Vxxxx',
              (),
              "The entry table has duplicate rows; this usually means "
              "a copy/paste error or some other problem."))
            
            return False
        
        self.numStates = max(
          int(wSA.length()) // (2 * self.numClasses),
          1 + max(t[0] for t in self.entryTable))
        
        if self.numStates < 2:
            logger.error((
              'V0725',
              (),
              "The number of states in the state table is less than two. "
              "The two fixed states must always be present."))
            
            return None
        
        self.classMap = lookup.Lookup.fromvalidatedwalker(
          wCT,
          logger = logger.getChild("classmap"))
        
        if not self.classMap:
            return False
        
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: v for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = {0xFFFF}
        
        self.emptyClasses = (
          set(range(4, self.numClasses)) - set(self.classToGlyphs))
        
        if wSA.length() < 2 * self.numClasses * self.numStates:
            logger.error((
              'V0676',
              (),
              "The state array is missing or incomplete."))
            
            return False
        
        self.stateArray = wSA.group("H" * self.numClasses, self.numStates)
        maxEntryIndex = max(n for row in self.stateArray for n in row)
        
        if maxEntryIndex >= len(self.entryTable):
            logger.error((
              'V0724',
              (stateNames[stateIndex], classNames[classIndex]),
              "At least one state array cell contains an entry index that "
              "is out of range."))
            
            return False
        
        numLookups = 1 + max(
          n
          for t in self.entryTable
          for n in t[2:4]
          if n != 0xFFFF)
        
        if wGT.length() < 4 * numLookups:
            logger.error((
              'V0728',
              (),
              "The offset header to the per-glyph lookup tables is "
              "missing or incomplete."))
            
            return False
        
        self.glyphLookups = [None] * numLookups
        offsets = wGT.group("L", numLookups)
        f = lookup.Lookup_OutGlyph.fromvalidatedwalker
        
        for i, offset in enumerate(offsets):
            wSub = wGT.subWalker(offset)
            
            self.glyphLookups[i] = f(
              wSub,
              logger = logger.getChild("per-glyph %d" % (i,)))
            
            if self.glyphLookups[i] is None:
                return False
        
        return True
    
    def _doAnalysis(self):
        self._buildInputs()
        self.analysis = set()  # (stateIndex, classIndex, markSet, currSet)
        self.entryIndexToMarkDict = {}  # entryIndex->dict(inGlyph->outGlyph)
        self.entryIndexToCurrDict = {}  # entryIndex->dict(inGlyph->outGlyph)
        self._fillStateRecs(0, set())
        self._fillStateRecs(1, set())
    
    def _doAnalysis_validated(self, logger):
        okToProceed = self._buildInputs_validated(logger)
        
        if not okToProceed:
            return False
        
        self.analysis = set()  # (stateIndex, classIndex, markSet, currSet)
        self.entryIndexToMarkDict = {}  # entryIndex->dict(inGlyph->outGlyph)
        self.entryIndexToCurrDict = {}  # entryIndex->dict(inGlyph->outGlyph)
        self._fillStateRecs(0, set())
        self._fillStateRecs(1, set())
        return True
    
    def _fillStateRecs(self, stateIndex, markSet):
        thisState = self.stateArray[stateIndex]
        newToDo = set()
        
        for classIndex, entryIndex in enumerate(thisState):
            if classIndex in self.emptyClasses:
                continue
            
            if classIndex in {0, 1, 3}:
                currSet = set()
            else:
                currSet = self.classToGlyphs[classIndex]
            
            t = (stateIndex, classIndex, frozenset(markSet), frozenset(currSet))
            
            if t not in self.analysis:
                newStateIndex, flags, markIndex, currIndex = (
                  self.entryTable[entryIndex])
                
                if markIndex != 0xFFFF:
                    assert markSet
                    d = self.entryIndexToMarkDict.setdefault(entryIndex, {})
                    newMarkSet = set()
                    glyphLookup = self.glyphLookups[markIndex]
                    
                    for glyphIndex in markSet:
                        d[glyphIndex] = glyphLookup.get(glyphIndex, 0xFFFF)
                        newMarkSet.add(d[glyphIndex])
                
                else:
                    newMarkSet = set(markSet)
                
                if currIndex != 0xFFFF:
                    assert currSet
                    d = self.entryIndexToCurrDict.setdefault(entryIndex, {})
                    newCurrSet = set()
                    glyphLookup = self.glyphLookups[currIndex]
                    
                    for glyphIndex in currSet:
                        d[glyphIndex] = glyphLookup.get(glyphIndex, 0xFFFF)
                        newCurrSet.add(d[glyphIndex])
                
                else:
                    newCurrSet = set(currSet)
                
                if newStateIndex > 1:
                    if flags & 0x8000:
                        if classIndex == 2 and newStateIndex == stateIndex:
                            
                            # If this case arises, the deleted glyph is being
                            # marked and then passed to this same state. This
                            # is a font bug; the mark bit should not be set in
                            # this case. This logic prevents the recursion from
                            # continuing down in this case.
                            
                            pass
                        
                        else:
                            newToDo.add((newStateIndex, frozenset(newCurrSet)))
                    
                    else:
                        newToDo.add((newStateIndex, frozenset(newMarkSet)))
                
                self.analysis.add(t)
        
        # now do the recursive calls back to this method
        for newStateIndex, newMarkSet in newToDo:
            self._fillStateRecs(newStateIndex, newMarkSet)
    
    #
    # Public methods
    #
    
    def analyze(self, **kwArgs):
        """
        Creates and returns the analysis for the object. This analysis is a
        pair (entryIndexToMarkDict, entryIndexToCurrDict); see the doctest
        below for what the output looks like.
        
        >>> w = walkerbit.StringWalker(_binData)
        >>> m, c = Analyzer(w).analyze()
        >>> p = pp.PP()
        >>> p.generic(m)
        a mapping:
          2: (a mapping)
            73: 330
          3: (a mapping)
            73: 192
          4: (a mapping)
            73: 193
          5: (a mapping)
            330: 331
          6: (a mapping)
            330: 332
        
        >>> p.generic(c)
        a mapping:
          2: (a mapping)
            73: 65535
          3: (a mapping)
            76: 65535
          4: (a mapping)
            79: 65535
          5: (a mapping)
            76: 65535
          6: (a mapping)
            79: 65535
        """
        
        if self.analysis is None:
            if 'logger' in kwArgs:
                if not self._doAnalysis_validated(kwArgs['logger']):
                    self.entryIndexToMarkDict = None
                    self.entryIndexToCurrDict = None
            
            else:
                self._doAnalysis()
        
        return self.entryIndexToMarkDict, self.entryIndexToCurrDict

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import pp, walkerbit
    
    _sv = [
        "00 00 00 07",  # numClasses
        "00 00 00 14",  # offset to class table
        "00 00 00 2C",  # offset to state array
        "00 00 00 64",  # offset to entry table
        "00 00 00 9C",  # offset to glyph table
        
        # Class table starts here (offset = 0x0014 bytes)
        "00 06 00 04 00 03 00 08 00 01 00 04",  # format 6 lookup
        "00 49 00 04",  # glyph 73 (f) maps to class 4
        "00 4C 00 05",  # glyph 76 (i) maps to class 5
        "00 4F 00 06",  # glyph 79 (l) maps to class 6
        
        # State array starts here (offset = 0x002C bytes)
        "00 00 00 00 00 00 00 00 00 01 00 00 00 00",  # state 0 (Start of text)
        "00 00 00 00 00 00 00 00 00 01 00 00 00 00",  # state 1 (Start of line)
        "00 00 00 00 00 00 00 00 00 02 00 03 00 04",  # state 2 (Saw f)
        "00 00 00 00 00 00 00 00 00 01 00 05 00 06",  # state 3 (Saw ff)
        
        # Entry table starts here (offset = 0x0064 bytes)
        "00 00 00 00 FF FF FF FF",  # entry 0 (->SOT)
        "00 02 80 00 FF FF FF FF",  # entry 1 (->Saw f, mark)
        "00 03 00 00 00 00 00 01",  # entry 2 (->Saw ff, mkd->ff, cur->DEL)
        "00 00 00 00 00 02 00 01",  # entry 3 (->SOT, mkd->fi, cur->DEL)
        "00 00 00 00 00 03 00 01",  # entry 4 (->SOT, mkd->fl, cur->DEL)
        "00 00 00 00 00 04 00 01",  # entry 5 (->SOT, mkd->ffi, cur->DEL)
        "00 00 00 00 00 05 00 01",  # entry 6 (->SOT, mkd->ffi, cur->DEL)
        
        # Glyph table header starts here (offset = 0x009C bytes)
        "00 00 00 18",  # offset from glyph table to lookup 0
        "00 00 00 20",  # offset from glyph table to lookup 1
        "00 00 00 34",  # offset from glyph table to lookup 2
        "00 00 00 3C",  # offset from glyph table to lookup 3
        "00 00 00 44",  # offset from glyph table to lookup 4
        "00 00 00 4C",  # offset from glyph table to lookup 5
        
        # (glyph table contents start here)
        
        # lookup 0 (f->ff)
        "00 08 00 49 00 01 01 4A",
        
        # lookup 1 (f->DEL, i->DEL, l->DEL)
        "00 08 00 49 00 07 FF FF FF FF FF FF FF FF FF FF FF FF FF FF",
        
        # lookup 2 (f->fi)
        "00 08 00 49 00 01 00 C0",
        
        # lookup 3 (f->fl)
        "00 08 00 49 00 01 00 C1",
        
        # lookup 4 (ff->ffi)
        "00 08 01 4A 00 01 01 4B",
        
        # lookup 5 (ff->ffl)
        "00 08 01 4A 00 01 01 4C",
        ]
    
    _binData = utilities.fromhex(' '.join(_sv))
    del _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
