#
# ligatureanalyzer.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing 'mort' ligature subtables.
"""

# System imports
import itertools

# Other imports
from fontio3 import utilities
from fontio3.statetables import stutils

# -----------------------------------------------------------------------------

#
# Classes
#

class Analyzer:
    """
    Objects performing ligature analysis for 'mort' type 2 subtables.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, w):
        self.w = w
        self.analysis = None
    
    #
    # Private methods
    #
    
    def _buildInputs(self):
        self.w.reset()
        t = self.w.unpack("7H")
        self.numClasses, oCT, oSA, oET, oLA, oCP, oLG = t
        self.offsets = t[1:]
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          self.w,
          *self.offsets)
        
        self._findNumStates(wET.subWalker(0, relative=True), oSA)
        self._makeClassMap(wCT)
        self.stateArray = wSA.group("B" * self.numClasses, self.numStates)
        self.entryTable = wET.unpackRest("2H", strict=False)
        self.ligActions = wLA.unpackRest("L", strict=False)
        self.ligActionIsLast = [bool(n & 0x80000000) for n in self.ligActions]
        self.compOffsets = wCP.unpackRest("H")
        self.ligatures = wLG.unpackRest("H")
    
    def _buildInputs_validated(self, logger):
        self.w.reset()
        stBaseOffset = self.w.getOffset()
        
        if self.w.length() < 14:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        t = self.w.unpack("7H")
        self.numClasses, oCT, oSA, oET, oLA, oCP, oLG = t
        self.offsets = t[1:]
        
        if self.numClasses < 4:
            logger.error((
              'V0634',
              (self.numClasses,),
              "The number of classes in a state table must be at least "
              "four, but is only %d."))
            
            return False
        
        firstValid = self.w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + self.w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in self.offsets):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return False
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          self.w,
          *self.offsets)
        
        self.entryTable = wET.unpackRest("2H", strict=False)
        
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
              (),
              "At least one state array cell contains an entry index that "
              "is out of range."))
            
            return False
        
        self.ligActions = wLA.unpackRest("L", strict=False)
        
        if not self.ligActions:
            logger.error((
              'V0690',
              (),
              "The ligature action list is missing or incomplete."))
            
            return False
        
        self.ligActionIsLast = [bool(n & 0x80000000) for n in self.ligActions]
        self.compOffsets = wCP.unpackRest("H")
        
        if not self.compOffsets:
            logger.error((
              'V0691',
              (),
              "The component offset table is missing or incomplete."))
            
            return False
        
        self.ligatures = wLG.unpackRest("H")
        
        if not self.ligatures:
            logger.error((
              'V0692',
              (),
              "The ligature table is missing or incomplete."))
            
            return False
        
        return True
    
    def _doAnalysis(self):
        self._buildInputs()
        self.analysis = set()
        self.finalDicts = {}
        self._fillStateRecs(0, [])
        self._fillStateRecs(1, [])
    
    def _doAnalysis_validated(self, logger):
        okToProceed = self._buildInputs_validated(logger)
        
        if not okToProceed:
            return False
        
        self.analysis = set()
        self.finalDicts = {}
        self._fillStateRecs(0, [])
        self._fillStateRecs(1, [])
        return True
    
    def _fillStateRecs(self, stateIndex, incomingStack):
        savedStack = list(incomingStack)
        deepToDo = set()
        thisState = self.stateArray[stateIndex]  # thisState is a list of
                                                 # entry indices, by class
        
        for classIndex, entryIndex in enumerate(thisState):
            stack = list(savedStack)
            
            if classIndex < 4:
                classGlyphs = frozenset()
            else:
                classGlyphs = self.classToGlyphs[classIndex]
            
            newStateOffset, flags = self.entryTable[entryIndex]
            
            newStateIndex = (
              (newStateOffset - self.offsets[1]) // self.numClasses)
            
            # we have to push first, before looking for ligActions
            if flags & 0x8000:
                stack.append(classGlyphs)
            
            ligActionOffset = flags & 0x3FFF
            
            if ligActionOffset:
                # use only the depth of stack corresponding to this ligAction
                laGroupStartIndex = (ligActionOffset - self.offsets[3]) // 4
                
                laGroupEndIndex = self.ligActionIsLast.index(
                  True,
                  laGroupStartIndex)
                
                count = laGroupEndIndex - laGroupStartIndex + 1
                t = (stateIndex, classIndex, tuple(stack[-count:]))
            
            else:
                t = (stateIndex, classIndex)
            
            if t not in self.analysis:
                stacks = set()
                
                if ligActionOffset:
                    finalDict = self.finalDicts.setdefault(t[0:2], {})
                    
                    laGroupStartIndex = (
                      (ligActionOffset - self.offsets[3]) // 4)
                    
                    laGroupStopIndex = (
                      self.ligActionIsLast.index(True, laGroupStartIndex) + 1)
                    
                    count = laGroupStopIndex - laGroupStartIndex
                    
                    theseActions = self.ligActions[
                      laGroupStartIndex:laGroupStopIndex]
                    
                    revStack = list(reversed(stack))  # Unlike stack, [0] is
                                                      # stack top in revStack
                    
                    for inTuple in itertools.product(*revStack[:count]):
                        outList = []
                        cumulOffset = 0
                        backToStack = []
                        it = enumerate(zip(inTuple, theseActions))
                        
                        for i, (inGlyph, ligAction) in it:
                            compOffset = ligAction & 0x3FFFFFFF
                            
                            if compOffset >= 0x20000000:
                                compOffset -= 0x40000000
                            
                            n = (compOffset + inGlyph) * 2
                            cIndex = (n - self.offsets[4]) // 2
                            cumulOffset += self.compOffsets[cIndex]
                            
                            if ligAction & 0xC0000000:
                                # last or store
                                ligIndex = (cumulOffset - self.offsets[5]) // 2
                                outLigature = self.ligatures[ligIndex]
                                outList.append(outLigature)
                                backToStack.append(frozenset([outLigature]))
                            
                            else:
                                outList.append(None)
                        
                        n = tuple(reversed(inTuple))
                        finalDict[n] = tuple(reversed(outList))
                        
                        alteredStack = list(stack)
                        alteredStack[-count:] = list(reversed(backToStack))
                        stacks.add(tuple(alteredStack))
                
                else:
                    stacks.add(tuple(stack))
                
                self.analysis.add(t)
                
                if newStateIndex > 1:
                    # don't walk down any further if we go to ground
                    if classIndex == 2 and newStateIndex == stateIndex:
                        pass
                    
                    else:
                        deepToDo.add((newStateIndex, frozenset(stacks)))
        
        for newStateIndex, stacks in deepToDo:
            for thisStack in stacks:
                self._fillStateRecs(newStateIndex, list(thisStack))
    
    def _findNumStates(self, w, stateArrayBaseOffset):
        v = w.unpackRest("2H", strict=False)
        maxOffset = max(offset for offset, ignore in v) - stateArrayBaseOffset
        self.numStates = 1 + (maxOffset // self.numClasses)
    
    def _makeClassMap(self, w):
        firstGlyph, count = w.unpack("2H")
        group = w.group("B", count)
        
        self.classMap = {
          i: c
          for i, c in enumerate(group, start=firstGlyph)
          if c != 1}
        
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: frozenset(v) for k, v in d.items() if k >= 4}
    
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
        self.classToGlyphs = {k: frozenset(v) for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = {0xFFFF}
        
        self.emptyClasses = (
          set(range(4, self.numClasses)) - set(self.classToGlyphs))
        
        return True
    
    #
    # Public methods
    #
    
    def analyze(self, **kwArgs):
        """
        >>> w = walkerbit.StringWalker(_binData)
        >>> obj = Analyzer(w)
        >>> obj.analyze()
        >>> f = operator.itemgetter(0)
        >>> for k, v in sorted(obj.finalDicts.items(), key=f): print(k, v)
        (2, 6) {(73, 73): (330, None)}
        (2, 7) {(73, 76): (192, None)}
        (2, 8) {(73, 79): (193, None)}
        (3, 7) {(330, 76): (331, None)}
        (3, 8) {(330, 79): (332, None)}
        (5, 6) {(73, 73): (330, None)}
        (5, 7) {(73, 76): (192, None)}
        (5, 8) {(73, 79): (193, None)}
        (6, 7) {(330, 76): (331, None)}
        (6, 8) {(330, 79): (332, None)}
        (8, 5) {(82, 331, 70, 72): (873, None, None, None)}
        """
        
        if self.analysis is None:
            if 'logger' in kwArgs:
                if not self._doAnalysis_validated(kwArgs['logger']):
                    self.analysis = None
            
            else:
                self._doAnalysis()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import operator
    from fontio3.utilities import pp, walkerbit
    
    _sv = [
        "00 0A",            # (0) numClasses
        "00 0E",            # (2) offset to class table
        "00 20",            # (4) offset to state array
        "00 7A",            # (6) offset to entry table
        "00 A8",            # (8) offset to ligAction table
        "00 D0",            # (A) offset to component table
        "00 DC",            # (C) offset to ligature table
        
        # class table
        
        "00 46",            # (E) first glyph
        "00 0D",            # (10) glyph count
        "04 01 05 06 01 01 07 01 01 08 01 01 09",   # (12) classes
        "00",               # (1F) padding
        
        # state array
        
        "00 00 00 00 00 00 01 00 00 02",    # (20) state 0: Start of text
        "00 00 00 00 00 00 01 00 00 02",    # (2A) state 1: Start of line
        "00 00 00 00 00 00 03 04 04 02",    # (34) state 2: Saw f
        "00 00 00 00 00 00 01 05 05 02",    # (3E) state 3: Saw ff
        "00 00 00 00 00 00 06 00 00 02",    # (48) state 4: Saw o
        "00 00 00 00 00 00 07 04 04 02",    # (52) state 5: Saw of
        "00 00 00 00 00 00 01 08 05 02",    # (5C) state 6: Saw off
        "00 00 00 00 09 00 01 00 00 02",    # (66) state 7: Saw offi
        "00 00 00 00 00 0A 01 00 00 02",    # (70) state 8: Saw offic
        
        # entry table
        
        "00 20 00 00",      # (7A) entry 0: ->Start of text
        "00 34 80 00",      # (7E) entry 1: Push, ->Saw f
        "00 48 80 00",      # (82) entry 2: Push, ->Saw o
        "00 3E 80 A8",      # (86) entry 3: Push, ligAction 0, ->Saw ff
        "00 20 80 B0",      # (8A) entry 4: Push, ligAction 2, ->Start of text
        "00 20 80 B8",      # (8E) entry 5: Push, ligAction 4, ->Start of text
        "00 52 80 00",      # (92) entry 6: Push, ->Saw of
        "00 5C 80 A8",      # (96) entry 7: Push, ligAction 0, ->Saw off
        "00 66 80 B8",      # (9A) entry 8: Push, ligAction 4, ->Saw offi
        "00 70 80 00",      # (9E) entry 9: Push, ->Saw offic
        "00 20 80 C0",      # (A2) entry A: Push, ligAction 6, ->Start of text
        "00 00",            # (A6) padding
        
        # ligAction table
        
        "00 00 00 20",      # (A8) ligAction 0
        "80 00 00 1F",      # (AC) ligAction 1
        
        "00 00 00 1E",      # (B0) ligAction 2
        "80 00 00 1F",      # (B4) ligAction 3
        
        "00 00 00 1E",      # (B8) ligAction 4
        "BF FF FF 21",      # (BC) ligAction 5
        
        "00 00 00 22",      # (C0) ligAction 6
        "00 00 00 24",      # (C4) ligAction 7
        "3F FF FF 21",      # (C8) ligAction 8
        "80 00 00 16",      # (CC) ligAction 9
        
        # component table
        
        "00 DC",    # (D0) component 0: base of ligature table
        "00 04",    # (D2) component 1: offset to lig[2] (ff)
        "00 00",    # (D4) component 2: offset to lig[0] (fi)
        "00 E2",    # (D6) component 3: additional offset from lig[0] (fi) to lig[3] (ffi)
        "00 0A",    # (D8) component 4: offset to lig[5] (special office lig)
        "00 02",    # (DA) component 5: offset to lig[1] (fl)
        
        # ligature table
        
        "00 C0",    # (DC) ligature 0: glyph 192 (fi)
        "00 C1",    # (DE) ligature 1: glyph 193 (fl)
        "01 4A",    # (E0) ligature 2: glyph 330 (ff)
        "01 4B",    # (E2) ligagure 3: glyph 331 (ffi)
        "01 4C",    # (E4) ligature 4: glyph 332 (ffl)
        "03 69"     # (E6) ligature 5: glyph 873 (special office lig)
        ]
    
    _binData = utilities.fromhex(' '.join(_sv))
    del _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
