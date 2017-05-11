#
# contextanalyzer.py
#
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing 'mort' contextual subtables to build up Python-style
dictionaries mapping marked and current glyph sets to output glyphs for each
entry index in the subtable.
"""

# Other imports
from fontio3.statetables import stutils

# -----------------------------------------------------------------------------

#
# Classes
#

class Analyzer:
    """
    Objects performing contextual analysis for 'mort' type 1 subtables.
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
        self.numClasses, oCT, oSA, oET, oST = self.w.unpack("5H")
        self.offsets = (oSA, oST)
        
        wCT, wSA, wET, wST = stutils.offsetsToSubWalkers(
          self.w,
          oCT,
          oSA,
          oET,
          oST)
        
        self._findNumStates(
          wET.subWalker(0, relative=True),
          oSA,
          self.numClasses)
        
        self._makeClassMap(wCT)
        self.stateArray = wSA.group("B" * self.numClasses, self.numStates)
        self.entryTable = wET.unpackRest("4H", strict=False)
        self.substTable = wST.unpackRest("H")
    
    def _buildInputs_validated(self, logger):
        self.w.reset()
        stBaseOffset = self.w.getOffset()
        
        if self.w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        t = self.w.unpack("5H")
        self.numClasses, oCT, oSA, oET, oST = t
        
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
        
        self.offsets = (oSA, oST)
        wCT, wSA, wET, wST = stutils.offsetsToSubWalkers(self.w, *t[1:])
        self.entryTable = wET.unpackRest("4H", strict=False)
        
        if not self.entryTable:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
            return False
        
        maxOffset = max(t[0] for t in self.entryTable) - oSA
        self.numStates = 1 + (maxOffset // self.numClasses)
        
        okToProceed = self._makeClassMap_validated(
          wCT,
          logger = logger.getChild("classmap"))
        
        if not okToProceed:
            return False
        
        if wSA.length() < self.numClasses * self.numStates:
            logger.error((
              'V0676',
              (),
              "The state array is missing or incomplete."))
            
            return False
        
        self.stateArray = wSA.group("B" * self.numClasses, self.numStates)
        maxEntryIndex = max(n for row in self.stateArray for n in row)
        
        if maxEntryIndex >= len(self.entryTable):
            logger.error((
              'V0724',
              (stateNames[stateIndex], classNames[classIndex]),
              "At least one state array cell contains an entry index that "
              "is out of range."))
            
            return False
        
        self.substTable = wST.unpackRest("H")
        
        if not self.substTable:
            logger.error((
              'V0679',
              (),
              "The substitution table is missing or incomplete."))
            
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
        #print("State index", stateIndex, "and marked set", markSet)
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
                newStateOffset, flags, markOffset, currOffset = (
                  self.entryTable[entryIndex])
                
                n = newStateOffset - self.offsets[0]
                newStateIndex = n // self.numClasses
                
                if markOffset:
                    assert markSet
                    d = self.entryIndexToMarkDict.setdefault(entryIndex, {})
                    newMarkSet = set()
                    
                    for glyphIndex in markSet:
                        n = (glyphIndex + markOffset) % 65536
                        substIndex = ((n * 2) - self.offsets[1]) // 2
                        
                        try:
                            d[glyphIndex] = self.substTable[substIndex]
                        except IndexError:
                            self.analysis.add(t)
                            continue
                        
                        newMarkSet.add(d[glyphIndex])
                
                else:
                    newMarkSet = set(markSet)
                
                if currOffset:
                    assert currSet
                    d = self.entryIndexToCurrDict.setdefault(entryIndex, {})
                    newCurrSet = set()
                    
                    for glyphIndex in currSet:
                        n = (glyphIndex + currOffset) % 65536
                        substIndex = ((n * 2) - self.offsets[1]) // 2
                        
                        try:
                            d[glyphIndex] = self.substTable[substIndex]
                        except IndexError:
                            self.analysis.add(t)
                            continue
                        
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
    
    def _findNumStates(self, w, stateArrayBaseOffset, numClasses):
        v = w.unpackRest("4H")
        maxOffset = max(offset for offset, *rest in v) - stateArrayBaseOffset
        self.numStates = 1 + (maxOffset // numClasses)
    
    def _makeClassMap(self, w):
        firstGlyph, count = w.unpack("2H")
        group = w.group("B", count)
        
        self.classMap = {
          i: c
          for i, c in enumerate(group, start=firstGlyph)
          if c != 1}
        
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: v for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = {0xFFFF}
        
        self.emptyClasses = (
          set(range(4, self.numClasses)) - set(self.classToGlyphs))
    
    def _makeClassMap_validated(self, w, logger):
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        firstGlyph, count = w.unpack("2H")
        
        if w.length() < count:
            logger.error((
              'V0669',
              (),
              "The class table records are missing or incomplete."))
            
            return False
        
        group = w.group("B", count)
        
        self.classMap = {
          i: c
          for i, c in enumerate(group, start=firstGlyph)
          if c != 1}
        
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: v for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = {0xFFFF}
        
        self.emptyClasses = (
          set(range(4, self.numClasses)) - set(self.classToGlyphs))
        
        return True
    
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
        "00 07",
        "00 0A",  # offset to class table
        "00 16",  # offset to state array
        "00 32",  # offset to entry table
        "00 6A",  # offset to subst table
        
        # Class table starts here (0x0C bytes)
        "00 49",  # first glyph is 73
        "00 07",  # count is 7
        "04 01 01 05 01 01 06 00",  # f is class 4, i is class 5, l is class 6
        
        # State array starts here (0x1C bytes)
        "00 00 00 00 01 00 00",  # state 0 (Start of text)
        "00 00 00 00 01 00 00",  # state 1 (Start of line)
        "00 00 00 00 02 03 04",  # state 2 (Saw f)
        "00 00 00 00 01 05 06",  # state 3 (Saw ff)
        
        # Entry table starts here (0x40 bytes)
        "00 16 00 00 00 00 00 00",  # entry 0 (->SOT)
        "00 24 80 00 00 00 00 00",  # entry 1 (->Saw f, mark)
        "00 2B 00 00 FF EC FF ED",  # entry 2 (->Saw ff, marked->ff, current->DEL)
        "00 16 00 00 FF EE FF EA",  # entry 3 (->SOT, marked->fi, current->DEL)
        "00 16 00 00 FF EF FF E7",  # entry 4 (->SOT, marked->fl, current->DEL)
        "00 16 00 00 FE EF FF EA",  # entry 5 (->SOT, marked->ffi, current->DEL)
        "00 16 00 00 FE F0 FF E7",  # entry 6 (->SOT, marked->ffl, current->DEL)
        
        # Substitution table starts here (0x0C bytes)
        "01 4A",  # glyph 330 is ff
        "FF FF",  # deleted glyph code
        "00 C0",  # glyph 192 is fi
        "00 C1",  # glyph 192 is fl
        "01 4B",  # glyph 331 is ffi
        "01 4C",  # glyph 332 is ffl
        "00 00"   # pad to longword alignment
        ]
    
    _binData = utilities.fromhex(' '.join(_sv))
    del _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
