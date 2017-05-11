#
# ligatureanalyzer.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing 'morx' ligature subtables.
"""

# System imports
import itertools

# Other imports
from fontio3 import utilities
from fontio3.statetables import stutils
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Classes
#

class Analyzer:
    """
    Objects performing ligature analysis for 'morx' type 2 subtables.
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
        t = self.w.unpack("7L")
        self.numClasses, oCT, oSA, oET, oLA, oCP, oLG = t
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          self.w,
          *t[1:])
        
        self.entryTable = list(wET.unpackRest("3H", strict=False))
        
        self.numStates = max(
          int(wSA.length()) // (2 * self.numClasses),
          1 + max(t[0] for t in self.entryTable))
        
        self.classMap = lookup.Lookup.fromwalker(wCT)
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: frozenset(v) for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = frozenset([0xFFFF])
        self.stateArray = wSA.group("H" * self.numClasses, self.numStates)
        self.ligActions = wLA.unpackRest("L")
        self.ligActionIsLast = [bool(n & 0x80000000) for n in self.ligActions]
        self.compIndices = wCP.unpackRest("H")
        self.ligatures = wLG.unpackRest("H")
    
    def _buildInputs_validated(self, logger):
        self.w.reset()
        stBaseOffset = self.w.getOffset()
        
        if self.w.length() < 28:
            logger.error(('V0004', (), "Insufficient bytes."))
            return False
        
        t = self.w.unpack("7L")
        self.numClasses, oCT, oSA, oET, oLA, oCP, oLG = t
        
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
        
        wCT, wSA, wET, wLA, wCP, wLG = stutils.offsetsToSubWalkers(
          self.w,
          *t[1:])
        
        self.entryTable = list(wET.unpackRest("3H", strict=False))
        
        if not self.entryTable:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
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
        
        self.classMap = lookup.Lookup.fromvalidatedwalker(wCT, logger=logger)
        
        if self.classMap is None:
            return False
        
        d = utilities.invertDictFull(self.classMap, asSets=True)
        self.classToGlyphs = {k: frozenset(v) for k, v in d.items() if k >= 4}
        self.classToGlyphs[2] = frozenset([0xFFFF])
        
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
              (),
              "At least one state array cell contains an entry index that "
              "is out of range."))
            
            return False
        
        self.ligActions = wLA.unpackRest("L")
        
        if not self.ligActions:
            logger.error((
              'V0690',
              (),
              "The ligature action list is missing or incomplete."))
            
            return False
        
        self.ligActionIsLast = [bool(n & 0x80000000) for n in self.ligActions]
        self.compIndices = wCP.unpackRest("H")
        
        if not self.compIndices:
            logger.error((
              'V0691',
              (),
              "The component table is missing or incomplete."))
            
            return False
        
        self.ligatures = wLG.unpackRest("H")
        
        if not self.ligatures:
            logger.error((
              'V0692',
              (),
              "The ligature table is missing or incomplete."))
            
            return False
        
        return True
    
    def _doAnalysis(self, **kwArgs):
        self._buildInputs()
        self.analysis = set()
        self.finalDicts = {}
        
        if not self._fillStateRecs(0, [], **kwArgs):
            return False
        
        if not self._fillStateRecs(1, [], **kwArgs):
            return False
        
        return True
    
    def _doAnalysis_validated(self, logger, **kwArgs):
        okToProceed = self._buildInputs_validated(logger)
        
        if not okToProceed:
            return False
        
        self.analysis = set()
        self.finalDicts = {}
        
        if not self._fillStateRecs(0, [], logger=logger, **kwArgs):
            return False
        
        if not self._fillStateRecs(1, [], logger=logger, **kwArgs):
            return False
        
        return True
    
    def _fillStateRecs(self, stateIndex, incomingStack, **kwArgs):
        logger = kwArgs.pop('logger', None)
        history = kwArgs.pop('history', None)
        forceToBase = kwArgs.pop('forceToBase', False)
        
        if history is None:
            history = []
        
        savedStack = list(incomingStack)
        deepToDo = set()
        thisState = self.stateArray[stateIndex]  # thisState is a list of
                                                 # entry indices, by class
        
        for classIndex, entryIndex in enumerate(thisState):
            stack = list(savedStack)
            
            if classIndex in {0, 1, 3}:
                classGlyphs = frozenset()
            else:
                classGlyphs = self.classToGlyphs[classIndex]
            
            newStateIndex, flags, laFirstIndex = self.entryTable[entryIndex]
            
            if (flags & 0x2000) and (newStateIndex > 1):
                if logger is not None:
                    logger.warning((
                      'V0902',
                      (stateIndex, classIndex),
                      "The entry for state %d, class %d does ligature "
                      "substitution, but does not lead back to the ground "
                      "state. This might be problematic."))
                
                if forceToBase:
                    newStateIndex = 0
                    self.entryTable[entryIndex] = (0, flags, laFirstIndex)
            
            # we have to push first, before looking for ligActions
            if flags & 0x8000:
                stack.append(classGlyphs)
            
            if flags & 0x2000:  # the "performAction" flag
                # use only the depth of stack corresponding to this ligAction
                laLastIndex = self.ligActionIsLast.index(
                  True,
                  laFirstIndex)
                
                count = laLastIndex - laFirstIndex + 1
                
                if count > len(stack):
                    if logger is not None:
                        hsv = []
                        modHist = history + [(stateIndex, stack)]
                        
                        for hStateIndex, hStack in modHist:
                            if hStack:
                                hStackPiece = " %s" % (sorted(hStack),)
                            else:
                                hStackPiece = ''
                            
                            if hStateIndex == 0:
                                hsv.append("SOT%s" % (hStackPiece,))
                            elif hStateIndex == 1:
                                hsv.append("SOL%s" % (hStackPiece,))
                            else:
                                hsv.append("State %d%s" % (hStateIndex, hStackPiece))
                        
                        logger.error((
                          'V0800',
                          ('->'.join(hsv),),
                          "Stack underflow for this sequence: %s"))
                    
                    return False
                
                else:
                    t = (stateIndex, classIndex, tuple(stack[-count:]))
            
            else:
                t = (stateIndex, classIndex)
            
            if t not in self.analysis:
                stacks = set()
                
                if flags & 0x2000:
                    finalDict = self.finalDicts.setdefault(t[0:2], {})
                    laLastIndexPlusOne = 1 + laLastIndex
                    
                    theseActions = self.ligActions[
                      laFirstIndex:laLastIndexPlusOne]
                    
                    revStack = list(reversed(stack))  # Unlike stack, [0] is
                                                      # stack top in revStack
                    
                    for inTuple in itertools.product(*revStack[:count]):
                        outList = []
                        cumulIndex = 0
                        backToStack = []
                        it = enumerate(zip(inTuple, theseActions))
                        
                        for i, (inGlyph, ligAction) in it:
                            cIndex = ligAction & 0x3FFFFFFF
                            
                            if cIndex >= 0x20000000:
                                cIndex -= 0x40000000
                            
                            cIndex += inGlyph
                            
                            if not (0 <= cIndex < len(self.compIndices)):
                                if logger is not None:
                                    logger.error((
                                      'V0803',
                                      (stateIndex, classIndex),
                                      "A LigatureAction in state %d, class %d "
                                      "is out of range."))
                                
                                return False
                            
                            cumulIndex += self.compIndices[cIndex]
                            
                            if ligAction & 0xC0000000:
                                # last or store
                                outLigature = self.ligatures[cumulIndex]
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
                
                if not self._fillStateRecs(
                  newStateIndex,
                  list(thisStack),
                  logger = logger,
                  history = history + [(stateIndex, incomingStack)],
                  forceToBase = forceToBase,
                  **kwArgs):
                  
                    return False
        
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
            logger = kwArgs.pop('logger', None)
            
            if logger is not None:
                if not self._doAnalysis_validated(logger=logger, **kwArgs):
                    self.analysis = None
            
            else:
                if not self._doAnalysis(**kwArgs):
                    raise ValueError("Ligature analysis failed!")

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
        # State table header starts here (offset = 0x0000 bytes)
        "00 00 00 0A",   # numClasses
        "00 00 00 1C",   # offset to class table
        "00 00 00 3C",   # offset to state array
        "00 00 00 F0",   # offset to entry table
        "00 00 01 34",   # offset to ligAction table
        "00 00 01 5C",   # offset to component table
        "00 00 01 68",   # offset to ligature table
        
        # Class table starts here (offset = 0x001C bytes)
        "00 08 00 46 00 0D",         # format 8, first = 70 (c), count = 13
        "00 04 00 01 00 05 00 06",   # class data
        "00 01 00 01 00 07 00 01",   # class data
        "00 01 00 08 00 01 00 01",   # class data
        "00 09",                     # class data
        
        # State array starts here (offset = 0x003C bytes)
        "00 00 00 00 00 00 00 00",   # state 0: Start of text (SOT)
        "00 00 00 00 00 01 00 00",
        "00 00 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 1: Start of line (SOL)
        "00 00 00 00 00 01 00 00",
        "00 00 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 2: Saw f
        "00 00 00 00 00 03 00 04",
        "00 04 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 3: Saw ff
        "00 00 00 00 00 01 00 05",
        "00 05 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 4: Saw o
        "00 00 00 00 00 06 00 00",
        "00 00 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 5: Saw of
        "00 00 00 00 00 07 00 04",
        "00 04 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 6: Saw off
        "00 00 00 00 00 01 00 08",
        "00 05 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 7: Saw offi
        "00 09 00 00 00 01 00 00",
        "00 00 00 02",
        
        "00 00 00 00 00 00 00 00",   # state 8: Saw offic
        "00 00 00 0A 00 01 00 00",
        "00 00 00 02",
        
        # Entry table starts here (offset = 0x00F0 bytes)
        "00 00 00 00 00 00",   # entry 0: ->SOT
        "00 02 80 00 00 00",   # entry 1: Push, ->Saw f
        "00 04 80 00 00 00",   # entry 2: Push, ->Saw o
        "00 03 A0 00 00 00",   # entry 3: Push, ligAction 0, ->Saw ff
        "00 00 A0 00 00 02",   # entry 4: Push, ligAction 2, ->SOT
        "00 00 A0 00 00 04",   # entry 5: Push, ligAction 4, ->SOT
        "00 05 80 00 00 00",   # entry 6: Push, ->Saw of
        "00 06 A0 00 00 00",   # entry 7: Push, ligAction 0, ->Saw off
        "00 07 A0 00 00 04",   # entry 8: Push, ligAction 4, ->Saw offi
        "00 08 80 00 00 00",   # entry 9: Push, ->Saw offic
        "00 00 A0 00 00 06",   # entry A: Push, ligAction 6, ->SOT
        "00 00",               # padding to longword boundary
        
        # LigAction table starts here (offset = 0x0134)
        "3F FF FF B7",   # LA 0: f (0x49) + (-0x49) = c. 0
        "BF FF FF B8",   # LA 1: f (0x49) + (-0x48) = c. 1, last
        
        "3F FF FF B6",   # LA 2: i (0x4C) or l (0x4F) + (-0x4A) = c. 2 or 5
        "BF FF FF B7",   # LA 3: f (0x49) + (-0x49) = c. 0, last
        
        "3F FF FF B6",   # LA 4: i (0x4C) or l (0x4F) + (-0x4A) = c. 2 or 5
        "BF FF FE B9",   # LA 5: ff (0x14A) + (-0x147) = c. 3
        
        "3F FF FF B8",   # LA 6: e (0x48) + (-0x48) = c. 0
        "3F FF FF BA",   # LA 7: c (0x46) + (-0x46) = c. 0
        "3F FF FE B5",   # LA 8: ffi (0x14B) + (-0x14B) = c. 0
        "BF FF FF B2",   # LA 9: o (0x52) + (-0x4E) = c. 4
        
        # Component table starts here (offset = 0x015C)
        "00 00",   # component 0: base of ligature table
        "00 02",   # component 1: offset to lig[2] (ff)
        "00 00",   # component 2: offset to lig[0] (fi)
        "00 03",   # component 3: delta from lig[0] (fi) to lig[3] (ffi)
        "00 05",   # component 4: offset to lig[5] (special office lig)
        "00 01",   # component 5: offset to lig[1] (fl)
        
        # Ligature table starts here (offset = 0x0168)
        "00 C0",   # ligature 0: glyph 192 (fi)
        "00 C1",   # ligature 1: glyph 193 (fl)
        "01 4A",   # ligature 2: glyph 330 (ff)
        "01 4B",   # ligagure 3: glyph 331 (ffi)
        "01 4C",   # ligature 4: glyph 332 (ffl)
        "03 69"    # ligature 5: glyph 873 (special office lig)
        ]
    
    _binData = utilities.fromhex(' '.join(_sv))
    del _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
