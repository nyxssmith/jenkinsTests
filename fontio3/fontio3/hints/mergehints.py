#
# mergehints.py
#
# Copyright © 2007-2013 Monotype Imaging. All Rights Reserved.
#

"""
Support for merging the hint-related parts of a TrueType font (e.g. the 'fpgm',
'cvt ', 'prep', and glyph-specific hints).
"""

# System imports
import logging
import re

# Other imports
from fontio3.hints import common, hints_tt, mergehintsphase2, opcode_tt, ttstate
from fontio3.triple import collection
from fontio3.utilities import tracker

# -----------------------------------------------------------------------------

#
# Private constants
#

_addOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ADD"])
_clearOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["CLEAR"])
_dupOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["DUP"])
_eifOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["EIF"])
_elseOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ELSE"])
_eqOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["EQ"])
_ifOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["IF"])
_mindexOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["MINDEX"])
_rollOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ROLL"])
_swapOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SWAP"])

DIGIT_GROUP = re.compile(r'([0-9]+)')

# -----------------------------------------------------------------------------

#
# Private functions
#

def _findAvailIndex(aSet):
    """
    Given a set of integers, returns the smallest non-negative value not
    present.
    
    >>> _findAvailIndex(set())
    0
    >>> _findAvailIndex(set([0, 1, 3, 4]))
    2
    >>> _findAvailIndex(set([1]))
    0
    >>> _findAvailIndex(set([0, 1, 2]))
    3
    """
    
    if not aSet:
        return 0
    
    m = max(aSet) + 1
    
    if len(aSet) == m:
        return m
    
    return min(set(range(m)) - aSet)

def _hasJumps(editor):
    """
    If any hint object contained in the specified editor has JMPR, JROF or
    JROT opcodes, this function returns True. Otherwise it returns False.
    """

    keys = list(editor.keys())

    if b'prep' in keys and editor.prep.containsJumps():
        return True

    if b'fpgm' in keys and any(x.containsJumps() for x in editor.fpgm.values()):
        return True

    for d in editor.glyf.values():
        if d.hintBytes:
            x = hints_tt.Hints.frombytes(d.hintBytes)

            if x.containsJumps():
                return True

    return False

def _makeTTFragment_call(fdefSet, fdefMap):
    """
    Returns a Hints object containing a fragment of TrueType code designed to
    map any value in fdefSet into the corresponding value in fdefMap. Note that
    idempotent mappings do not result in any TrueType code.
    
    If no changes need to be made, None is returned.
    """
    
    # First determine which functions actually need to be altered.
    needMap = dict((fIn, fOut) for fIn, fOut in fdefMap.items() if fIn in fdefSet if fIn != fOut)
    
    if not needMap:
        return None
    
    # Now generate the code
    H = hints_tt.Hints
    
    if len(needMap) == 1:
        # for a single map, just add the difference
        fIn, fOut = needMap.popitem()
        _delta = opcode_tt.Opcode_push([fOut - fIn])
        return H([_delta, _addOpcode])
    
    stillToDo = len(needMap)
    v = []
    
    for fIn, fOut in needMap.items():
        stillToDo -= 1
        _trial = opcode_tt.Opcode_push([fIn])
        _delta = opcode_tt.Opcode_push([fOut - fIn])
        v.extend([_dupOpcode, _trial, _eqOpcode, _ifOpcode, _delta, _addOpcode])
        
        if stillToDo:
            v.append(_elseOpcode)
    
    v.extend([_eifOpcode] * len(needMap))
    return H(v)

def _makeTTFragment_delta(delta, relStack):
    """
    Returns a Hints object containing a fragment of TrueType code designed to
    add the specified delta to the stack element at the relStack position.
    
    >>> _makeTTFragment_delta(20, -1)
    [PUSH [20], ADD]
    >>> _makeTTFragment_delta(20, -2)
    [SWAP, PUSH [20], ADD, SWAP]
    >>> _makeTTFragment_delta(20, -3)
    [ROLL, PUSH [20], ADD, ROLL, ROLL]
    >>> _makeTTFragment_delta(20, -4)
    [PUSH [4], MINDEX, PUSH [20], ADD, PUSH [4], MINDEX, PUSH [4], MINDEX, PUSH [4], MINDEX]
    """
    
    H = hints_tt.Hints
    _delta = opcode_tt.Opcode_push([delta])
    
    if relStack == -1:
        # top of stack is easy case; just PUSH and ADD
        return H([_delta, _addOpcode])
    
    if relStack == -2:
        return H([_swapOpcode, _delta, _addOpcode, _swapOpcode])
    
    if relStack == -3:
        return H([_rollOpcode, _delta, _addOpcode, _rollOpcode, _rollOpcode])
    
    # if we get here, the element to be changed is very deep, so we handle it
    # in a generic way
    
    _count = opcode_tt.Opcode_push([-relStack])
    
    v = [_count, _mindexOpcode, _delta, _addOpcode]
    v.extend([_count, _mindexOpcode] * (-relStack - 1))
    return H(v)

def _makeTTFragments_delta(delta, relSet):
    """
    Returns a Hints object containing a fragment of TrueType code designed to
    add the specified delta to the stack elements at the positions noted in the
    relSet (whose length will always be greater than one; if there is only one
    value, the client should call _makeTTFragment_delta instead).
    
    >>> _makeTTFragments_delta(20, set([-1, -3]))
    [PUSH [3], MINDEX, PUSH [20], ADD, PUSH [3], MINDEX, PUSH [3], MINDEX, PUSH [20], ADD]
    >>> _makeTTFragments_delta(20, set([-2, -4]))
    [PUSH [4], MINDEX, PUSH [20], ADD, PUSH [4], MINDEX, PUSH [4], MINDEX, PUSH [20], ADD, PUSH [4], MINDEX]
    """
    
    lowest = min(relSet)
    _p = opcode_tt.Opcode_push([-lowest])
    _delta = opcode_tt.Opcode_push([delta])
    v = []
    
    while lowest < 0:
        v.extend([_p, _mindexOpcode])
        
        if lowest in relSet:
            v.extend([_delta, _addOpcode])
        
        lowest += 1
    
    return hints_tt.Hints(v)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Merger(object):
    """
    Merger objects control the merging of hints between some number of fonts.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, baseEditor, otherEditor, **kwArgs):
        """
        Creates a Merger object with the specified base and other Editors. Note
        the whole contents of otherEditor are merged into baseEditor, so it a
        client wishes to only merge part of a font, the editor should be
        changed to reflect that before creating the Merger instance.
        """
        
        if _hasJumps(baseEditor):
            raise Merger_CannotMergeHintsWithJumps("Base editor contains jumps!")

        if _hasJumps(otherEditor):
            raise Merger_CannotMergeHintsWithJumps("Other editor contains jumps!")

        self.baseEditor = baseEditor
        self.otherEditor = otherEditor
        self.logger = kwArgs.get('logger', logging.getLogger())
        self.tracker = kwArgs.get('tracker', tracker.ProgressTracker_List())
        self.cvtBase = kwArgs.get('cvtBase', len(baseEditor[b'cvt ']))
        self.storageBase = kwArgs.get('storageBase', baseEditor.maxp.maxStorage + 1)
        self.storageFinal = self.storageBase + otherEditor.maxp.maxStorage + 1
    
    #
    # Private methods
    #
    
    def _createFDEFMap(self):
        """
        Creates self.fdefMap with the indices from the base font.
        """
        
        self.tracker.commentStart("Creating map of needed FDEF duplicates")
        baseFPGM = self.baseEditor.get(b'fpgm', {})
        baseInUse = set(baseFPGM)
        addedFPGM = self.otherEditor.get(b'fpgm', {})
        dMap = self.fdefMap = {}  # maps addedIndex to baseIndex
        dHash = {}  # maps hash to set of baseIndices
        
        for i, f in baseFPGM.items():
            dHash.setdefault(f.mutableHash(), set()).add(i)
        
        noShare = self.noShare = self._findNoShareFDEFs()
        nextAvail = _findAvailIndex(baseInUse)
        
        for addedIndex, addedFunc in addedFPGM.items():
            stillNeedToDo = True
            h = addedFunc.mutableHash()
            
            if addedIndex not in noShare:
                for baseIndex in dHash.get(h, set()):
                    if addedFunc == baseFPGM[baseIndex]:
                        dMap[addedIndex] = baseIndex
                        stillNeedToDo = False
                        break
            
            if stillNeedToDo:
                dMap[addedIndex] = nextAvail
                baseInUse.add(nextAvail)
                nextAvail = _findAvailIndex(baseInUse)
        
        self.tracker.commentEnd()
    
    def _findNoShareFDEFs(self):
        """
        Returns a set of FDEF indices that contain code referring to another
        FDEF index, a CVT index, or a storage index. This set thus defines
        those FDEFs in need of duplication.
        """
        
        r = set()
        
        for dKind in self.stats.effectNotes.values():
            for t in dKind:
                if t[0].startswith('FDEF'):
                    v = DIGIT_GROUP.findall(t[0][5:])
                    r.add(int(v[0]))
        
        return r
    
    def _fixDualGraphicsStates(self):
        """
        """
        
        s = set(newFDEF for oldFDEF, newFDEF in self.fdefMap.items() if oldFDEF != newFDEF)
        
        m = mergehintsphase2.GSTweaks(
          editor=self.baseEditor,
          prepSplitIndex=self.prepSplitIndex,
          synthFDEFSet=s,
          otherEditor=self.otherEditor,
          tracker=self.tracker)
        
        m.tweak()
    
    def _gatherStats(self):
        """
        Creates self.stats, containing the statistics from a full analysis of
        the specified editor.
        """
        
        self.tracker.commentStart("Gathering statistics")
        state = ttstate.TrueTypeState.fromeditor(self.otherEditor)
        self.tracker.commentStart("Running pre-program")
        state.runPreProgram(fdefEntryStack=[], logger=self.logger)
        #self.postOtherPrepGS = state.graphicsState.__deepcopy__()
        self.postOtherPrepGSEffects = set(state.statistics.gsEffectNotes)
        self.tracker.commentEnd()
        self.stats = stats = state.statistics.__deepcopy__()
        cookie = self.tracker.start(self.otherEditor.maxp.numGlyphs, "Processing glyph")
        wantKeys = ('maxima', 'effectNotes')
        
        for glyphIndex in range(self.otherEditor.maxp.numGlyphs):
            self.tracker.bump(cookie)
            h, runState = state.runGlyphSetup(glyphIndex)
            
            if runState is not None:
                h.run(runState, logger=self.logger)
                stats.combine(runState.statistics, keys=wantKeys)
        
        self.otherMaxima = stats.maxima
        self.tracker.done(cookie)
        self.tracker.commentEnd()
    
    def _mergeCVTTables(self):
        """
        Append the other CVT values to the base editor's CVT values.
        """
        
        self.tracker.commentStart("Merging CVT entries")
        cBase = self.baseEditor[b'cvt ']
        actualNext = len(cBase)
        
        if self.baseEditor.head.isAAFont():
            # the "42" in the following is iType's fs_object.h:ARABIC_CVT_USED
            if len(cBase) >= 42:
                self.autohintExtraCVTs = cBase[-42:]
            else:
                self.autohintExtraCVTs = list(cBase)
        
        else:
            self.autohintExtraCVTs = None
        
        cOther = self.otherEditor[b'cvt ']
        thisBase = self.cvtBase
        
        if actualNext > thisBase:
            raise ValueError("Specified cvtBases overlap actual data!")
        
        if actualNext < thisBase:
            cBase.extend([0] * (thisBase - actualNext))
        
        cBase.extend(cOther)
        self.baseEditor.changed(b'cvt ')
        self.tracker.commentEnd()
    
    def _mergeHintObj(self, hintObj):
        """
        Modifies hintObj to renumber references and insert needed conversion
        hint code.

        Note that this method raises Merger_CannotMergeHintsWithJumps if there
        are any jump opcodes in the specified hintObj. This may be addressed in
        the future, once I figure out how to handle this case.
        """
        
        thisIS = hintObj.infoString
        insertions = {}
        effectNotes = self.stats.effectNotes
        
        for kind, d in effectNotes.items():
            if kind == 'function':
                for t, fdefSet in d.items():
                    whichObj, pc = t[0:2]  # relStack is always -1 for CALL and LOOPCALL
                    
                    if thisIS == whichObj:
                        h = _makeTTFragment_call(fdefSet, self.fdefMap)
                        
                        if h is not None:
                            insertions[pc] = h
            
            else:
                delta = (self.cvtBase if kind == 'cvt' else self.storageBase)
                relPieces = {}
                
                for whichObj, pc, relStack in d:
                    if thisIS == whichObj:
                        relPieces.setdefault(pc, set()).add(relStack)
                
                for pc, relSet in relPieces.items():
                    if len(relSet) == 1:
                        insertions[pc] = _makeTTFragment_delta(delta, relSet.pop())
                    else:
                        insertions[pc] = _makeTTFragments_delta(delta, relSet)
        
        # Now that the gathering is done, process the insertions.
        for pc in sorted(insertions, reverse=True):
            hintObj[pc:pc] = insertions[pc]
    
    def _mergeSingle(self):
        """
        Does all the merging of self.otherEditor into self.baseEditor.
        """
        
        self.tracker.commentStart("Starting actual merge")
        self._gatherStats()
        self._createFDEFMap()
        eBase = self.baseEditor
        self.prepSplitIndex = len(eBase.prep)
        eOther = self.otherEditor
        self.tracker.commentStart("Merging 'prep'")
        
        if b'prep' in eOther:
            eBase.prep.append(_clearOpcode)
            h = eOther.prep
            self._mergeHintObj(h)
            eBase.prep.extend(h)
            eBase.changed(b'prep')
        
        self.tracker.commentEnd()
        self.tracker.commentStart("Merging 'fpgm'")
        
        if b'fpgm' in eOther:
            for otherIndex, baseIndex in self.fdefMap.items():
                if baseIndex not in eBase.fpgm:
                    h = eOther.fpgm[otherIndex]
                    self._mergeHintObj(h)
                    eBase.fpgm[baseIndex] = h
                    eBase.changed(b'fpgm')
        
        self.tracker.commentEnd()
        cookie = self.tracker.start(len(eOther.glyf), "Merging glyph hints")
        
        for otherGlyphIndex in eOther.glyf:
            self.tracker.bump(cookie)
            s = "Glyph %d hints" % (otherGlyphIndex,)
            h = hints_tt.Hints.frombytes(eOther.glyf[otherGlyphIndex].hintBytes, infoString=s)
            self._mergeHintObj(h)
            eOther.glyf[otherGlyphIndex].hintBytes = h.binaryString()
            eOther.changed(b'glyf')
        
        self.tracker.done(cookie)
        self.tracker.commentEnd()
    
    def _updateMaxp(self):
        """
        Update the relevant values in the 'maxp' table, now that we know the
        real numbers.
        """
        
        eBase = self.baseEditor
        m = eBase.maxp
        m.maxStorage = self.storageFinal + 1
        
        if b'fpgm' in eBase:
            m.maxFunctionDefs = max(eBase.fpgm) + 1
        
        if self.otherMaxima.stack > m.maxStackElements:
            m.maxStackElements = self.otherMaxima.stack
        
        eBase.changed(b'maxp')
    
    #
    # Public methods
    #
    
    def merge(self):
        """
        Perform the actual merger. After this method finishes, self.baseEditor
        will have the merged tables.
        """
        
        self._mergeCVTTables()
        self._mergeSingle()
        self._updateMaxp()
        self._fixDualGraphicsStates()
        
        # as a very last step, add the duplicate CVTs for the autohinter
        if self.autohintExtraCVTs is not None:
            self.baseEditor[b'cvt '].extend(self.autohintExtraCVTs)

# -----------------------------------------------------------------------------

class Merger_CannotMergeHintsWithJumps(ValueError):
    """
    This exception is raised when a hint object contains jumps, which cannot
    currently be handled.
    """

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test_main():
    """
    Run integrated tests for the whole module.
    """
    
    import sys, time
    from fontio3 import fontedit2
    
    print(time.asctime())
    e1 = fontedit2.Editor.frompath("/Users/opstad/Desktop/TheFonts/fred.ttf")
    e2 = fontedit2.Editor.frompath("/Users/opstad/Desktop/TheFonts/tetra_mo_Subset.ttf")
    t = tracker.ProgressTracker_List(stream=sys.stdout)
    m = Merger(e1, e2, tracker=t)
    m.merge()
    e1.writeFont("/Users/opstad/Desktop/TheFonts/newmerge.ttf")
    print(time.asctime())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
#         _test_main()
