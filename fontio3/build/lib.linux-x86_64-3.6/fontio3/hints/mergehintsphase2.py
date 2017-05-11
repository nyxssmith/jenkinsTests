#
# mergehintsphase2.py -- Second phase of hint merging, comprising changes to
#                        the (now unified) 'prep' to make sure glyphs have the
#                        correct graphics state when they start executing.
#
# Copyright © 2008-2013 Monotype Imaging Inc. All Rights Reserved.
#

# System imports
import functools

# Other imports
from fontio3.hints import common, hints_tt, opcode_tt, ttstate
from fontio3.triple import collection
from fontio3.utilities import span, tracker

# -----------------------------------------------------------------------------

#
# Constants
#

_aaOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["AA"])
_addOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ADD"])
_callOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["CALL"])
_cindexOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["CINDEX"])
_dupOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["DUP"])
_eifOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["EIF"])
_elseOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ELSE"])
_flipoffOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["FLIPOFF"])
_fliponOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["FLIPON"])
_ifOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["IF"])
_instctrlOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["INSTCTRL"])
_popOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["POP"])
_rsOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["RS"])
_s45RoundOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["S45ROUND"])
_scanctrlOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SCANCTRL"])
_scantypeOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SCANTYPE"])
_scvtciOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SCVTCI"])
_sdbOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SDB"])
_sdsOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SDS"])
_smdOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SMD"])
_sroundOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SROUND"])
_sswOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SSW"])
_sswciOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SSWCI"])
_swapOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["SWAP"])
_wsOpcode = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["WS"])

synthFDEFIdentifier = -21555  # used by hints_tt.Hints.isSyntheticMergeFDEF()
    
# -----------------------------------------------------------------------------

#
# Private functions
#

def _findAvailIndex(iterable):
    """
    Returns the smallest nonnegative integer not in the specified iterable.
    
    >>> _findAvailIndex([])
    0
    >>> _findAvailIndex([3, 4, 5])
    0
    >>> _findAvailIndex([0, 1])
    2
    >>> _findAvailIndex([0, 1, 2, 4, 5, 6])
    3
    """
    
    s = span.Span(iterable)
    
    if len(s) == 0 or s[0][0] > 0:
        return 0
    
    return s[0][1] + 1

def _makePiece_dupOne(storeIndex):
    """
    Returns hints to copy the top stack value thus:
    
    (starting stack)    a
    PUSH                a  storeIndex  2
    CINDEX              a  storeIndex  a
    WS                  a
    
    >>> print(_makePiece_dupOne(20))
    [PUSH [20, 2], CINDEX, WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex, 2])
    return [_push, _cindexOpcode, _wsOpcode]

def _makePiece_dupOneSetOne(storeIndex, constant):
    """
    Returns hints that store the specified constant in storeIndex and
    duplicates the top of the stack into storeIndex + 1.
    
    (starting stack)    a
    PUSH                a  storeIndex+1  3  storeIndex  constant
    WS                  a  storeIndex+1  3
    CINDEX              a  storeIndex+1  a
    WS                  a
    
    >>> print(_makePiece_dupOneSetOne(20, 1))
    [PUSH [21, 3, 20, 1], WS, CINDEX, WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex + 1, 3, storeIndex, constant])
    return [_push, _wsOpcode, _cindexOpcode, _wsOpcode]

def _makePiece_dupSkipOne(storeIndex):
    """
    Returns hints to copy the second-from-the-top stack value thus:
    
    (starting stack)    a  ignore
    PUSH                a  ignore  storeIndex  3
    CINDEX              a  ignore  storeIndex  a
    WS                  a  ignore
    
    >>> print(_makePiece_dupSkipOne(20))
    [PUSH [20, 3], CINDEX, WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex, 3])
    return [_push, _cindexOpcode, _wsOpcode]

def _makePiece_dupTwo(storeIndex):
    """
    Returns hints to copy the top two stack values thus:
    
    (starting stack)    a  b
    PUSH                a  b  storeIndex  2  storeIndex+1  5
    CINDEX              a  b  storeIndex  2  storeIndex+1  a
    WS                  a  b  storeIndex  2
    CINDEX              a  b  storeIndex  b
    WS                  a  b
    
    Note if storeIndex+1 doesn't fit in one byte, this effect might be able
    to be done in fewer hint bytes by single pushes and swaps.
    
    >>> print(_makePiece_dupTwo(20))
    [PUSH [20, 2, 21, 5], CINDEX, WS, CINDEX, WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex, 2, storeIndex + 1, 5])
    return [_push, _cindexOpcode, _wsOpcode, _cindexOpcode, _wsOpcode]

def _makePiece_setOneConstant(storeIndex, constant):
    """
    Returns hints to set the storage index to the constant.
    
    (starting stack)    ***
    PUSH                ***  storeIndex  constant
    WS                  ***
    
    >>> print(_makePiece_setOneConstant(20, 4))
    [PUSH [20, 4], WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex, constant])
    return [_push, _wsOpcode]

def _makePiece_setTwoConstants(storeIndex, constant1, constant2):
    """
    Returns hints to set storeIndex to constant1 and storeIndex+1 to constant2.
    
    (starting stack)    ***
    PUSH                ***  storeIndex+1  constant2  storeIndex  constant
    WS                  ***  storeIndex+1  constant2
    WS                  ***
    
    >>> print(_makePiece_setTwoConstants(20, 4, 1))
    [PUSH [21, 1, 20, 4], WS, WS]
    """
    
    _push = opcode_tt.Opcode_push([storeIndex + 1, constant2, storeIndex, constant1])
    return [_push, _wsOpcode, _wsOpcode]

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GSTweaks(object):
    """
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, editor, prepSplitIndex, synthFDEFSet, otherEditor, **kwArgs):
        """
        Initializes the object with the specified Editor. The prepSplitIndex
        parameter is an index into the 'prep' Hints object where the second
        (merged) font's prep table starts. The synthFDEFSet parameter is a set
        of FDEF indices that were added by phase 1 of the hint merging process.
        The otherEditor is an Editor for the second font; its glyphs are
        updated with calls to the new synthetic FDEF.
        """
        
        self.editor = editor
        self.prepSplitIndex = prepSplitIndex
        self.synthFDEFSet = synthFDEFSet
        self.otherEditor = otherEditor
        self.tracker = kwArgs.get('tracker', tracker.ProgressTracker_List())
    
    #
    # Private methods
    #
    
    def _addSynthCall(self, hString, which, isAACase):
        """
        Given a hint string (which might be potentially empty), adds a call to
        self.synthFDEFIndex to the beginning, integrating with existing PUSHes,
        if present, to make the addition as small as possible. If isAACase is
        True, and the hint string is empty, adds an explicit AA 0 after the
        synth call.
        
        Returns the augmented hint string.
        """
        
        if hString:
            h = hints_tt.Hints.frombytes(hString)
            
            if not h[0].isPush():
                _push = opcode_tt.Opcode_push([which, self.synthFDEFIndex])
                return hints_tt.Hints([_push, _callOpcode] + h).binaryString()
            
            for i, op in enumerate(h):
                if not op.isPush():
                    break
            
            # i is first non-push, so add values to h[i-1] push
            
            h[i - 1] = opcode_tt.Opcode_push(h[i - 1].data + (which, self.synthFDEFIndex))
            h.insert(i, _callOpcode)
        
        elif isAACase:
            _push = opcode_tt.Opcode_push([0, which, self.synthFDEFIndex])
            h = hints_tt.Hints([_push, _callOpcode, _aaOpcode])
        
        else:
            _push = opcode_tt.Opcode_push([which, self.synthFDEFIndex])
            h = hints_tt.Hints([_push, _callOpcode])
        
        return h.binaryString()
    
    def _filterOutMonads(self):
        """
        Remove from self.postPrepEffects any entries relating to graphics state
        values that are single and thus not in need of change tracking.
        """
        
        tc = collection.toCollection
        nt = self.needTracking = set()
        ktc = self.kindToCounts
        gsb = self.postPrepBaseOnlyGS.__dict__
        
        for k, obj in self.postPrepGS.__dict__.items():
            if k not in ktc:
                continue  # ?
            
            if ktc[k][0] > 1:
                for subObj in obj:
                    asColl = tc(subObj)
                    
                    if None in asColl or len(asColl) > 1:
                        nt.add(k)
                        break  # out of subObj loop
            
            else:
                asColl = tc(obj)
                asCollB = tc(gsb[k])
                
                if (
                  (None in asColl) or
                  (len(asColl) > 1) or 
                  (None in asCollB) or
                  (len(asCollB) > 1) or
                  (asColl != asCollB)):
                    
                    nt.add(k)
        
        effectsToDelete = set()
        fGet = self._getOpcode
        kindMap = self.opcodeToKind
        
        for k in self.postPrepEffects:
            op = fGet(*k)
            
            if op not in kindMap:
                effectsToDelete.add(k)
            
            else:
                opKind = kindMap[op][1]
                
                if not (opKind & nt):
                    effectsToDelete.add(k)
        
        self.postPrepEffects -= effectsToDelete
    
    def _gatherStats(self):
        """
        Runs the 'prep' and saves the graphicsState and gsEffectNotes.
        """
        
        self.tracker.commentStart("Running unified pre-program")
        state = ttstate.TrueTypeState.fromeditor(self.editor)
        v = []
        state.runPreProgram(fdefEntryStack=[], copyGSAt=("Prep table", self.prepSplitIndex, v))
        self.postPrepBaseOnlyGS = v[0]
        self.postPrepGS = state.graphicsState
        self.postPrepEffects = state.statistics.gsEffectNotes
        self.tracker.commentEnd()
    
    def _getOpcode(self, stackTuple, pc):
        """
        Given a stack tuple (which is empty for the 'prep' table, and has the
        FDEF index in the final position otherwise) and a pc, returns the
        Opcode object at that location.
        """
        
        if stackTuple:
            h = self.editor.fpgm[stackTuple[-1]]
        else:
            h = self.editor.prep
        
        return h[pc].opcode
    
    def _makeAlternateFDEFs(self):
        """
        Creates the fdefMap and adds the duplicate FDEFs to the font.
        """
        
        needToDup = functools.reduce(set.union, (set(k[0]) for k in self.postPrepEffects), set())
        self.fdefMap = {}  # from original index to new, copy index
        fpgm = self.editor.fpgm
        
        for origFuncIndex in needToDup:
            copyFuncIndex = _findAvailIndex(fpgm)
            self.fdefMap[origFuncIndex] = copyFuncIndex
            fpgm[copyFuncIndex] = fpgm[origFuncIndex].__copy__()
    
    def _makeGlyphChanges(self):
        """
        Updates all hints for all glyphs to add calls to the newly-added
        synthetic FDEF.
        """
        
        didSomething = False
        isAACase = self.editor.head.isAAFont()
        
        for mainGlyph in self.editor.glyf.values():
            hString = mainGlyph.hintBytes
            
            if hString or isAACase:
                mainGlyph.hintBytes = self._addSynthCall(hString, 0, isAACase)
                didSomething = True
        
        if didSomething:
            self.editor.changed(b'glyf')
            didSomething = False
        
        isAACase = self.otherEditor.head.isAAFont()
        
        for otherGlyph in self.otherEditor.glyf.values():
            hString = otherGlyph.hintBytes
            
            if hString or isAACase:
                otherGlyph.hintBytes = self._addSynthCall(hString, 1, isAACase)
                didSomething = True
        
        if didSomething:
            self.otherEditor.changed(b'glyf')
    
    def _makeNewStorageMap(self):
        """
        Creates self.kindToIndex, mapping kind strings to storage indices.
        """
        
        baseAvail = nextAvail = self.editor.maxp.maxStorage + 1
        kti = self.kindToIndex = {}
        ktc = self.kindToCounts
        
        for kind in self.needTracking:
            kti[kind] = nextAvail
            nextAvail += 2 * ktc[kind][1]
        
        self.editor.maxp.maxStorage += (nextAvail - baseAvail)
        self.editor.changed(b'maxp')
    
    def _makePrepFpgmChanges(self):
        """
        Walk the gsEffects and add the code needed to store the changes.
        """
        
        e = self.editor
        otk = self.opcodeToKind
        insertions = {}  # -1 for prep, n for FDEF --> dict pc->Hints
        ktc = self.kindToCounts
        
        for t, pc in self.postPrepEffects:
            if t:
                insIndex = t[-1]
                h = e.fpgm[insIndex]
                e.changed(b'fpgm')
                alt = insIndex in self.synthFDEFSet
            else:
                h = e.prep
                e.changed(b'prep')
                alt = pc >= self.prepSplitIndex
                insIndex = -1
            
            op = h[pc].opcode
            func, kinds = otk[op]
            v = []
            
            for kind in kinds:
                storeIndex = self.kindToIndex[kind] + (alt * ktc[kind][1])
                v.extend(func(storeIndex))
            
            insertions.setdefault(insIndex, {})[pc] = hints_tt.Hints(v)
        
        # Now that we know all the insertions, go through and make them
        
        for whichFDEF, d in insertions.items():
            if whichFDEF == -1:
                h = e.prep
            else:
                h = e.fpgm[whichFDEF]
            
            for pc in sorted(d, reverse=True):
                h[pc:pc] = d[pc]
    
    def _makeSyntheticFDEF(self):
        """
        Creates the FDEF that establishes the correct graphics state.
        """
        
        p = opcode_tt.Opcode_push        
        v = [p([synthFDEFIdentifier]), _popOpcode]  # unique identifier for synthetic FDEFs
        kti = self.kindToIndex
        nt = self.needTracking
        
        # In all the stack simulation comments below, "si" stands for the
        # resolved storage index of the first (if multiple) value
        
        if 'autoFlip' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['autoFlip']]),         # is2ndFont  is2ndFont  autoFlipBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  needFlipOn
              _ifOpcode,                    # is2ndFont
              _fliponOpcode,                # is2ndFont
              _elseOpcode,                  # is2ndFont
              _flipoffOpcode,               # is2ndFont
              _eifOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        if 'cvtCutIn' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['cvtCutIn']]),         # is2ndFont  is2ndFont  cvtCutInBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  cvtCutInValue
              _scvtciOpcode])               # is2ndFont  -- all sequences must leave stack thus
        
        if 'deltaBase' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['deltaBase']]),        # is2ndFont  is2ndFont  deltaBaseBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  deltaBaseValue
              _sdbOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        if 'deltaShift' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['deltaShift']]),       # is2ndFont  is2ndFont  deltaShiftBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  deltaShiftValue
              _sdsOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        if 'instructControl' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              _dupOpcode,                   # is2ndFont  is2ndFont  is2ndFont
              _addOpcode,                   # is2ndFont  2*is2ndFont
              p([kti['instructControl']]),  # is2ndFont  2*is2ndFont  instCtrlBase
              _addOpcode,                   # is2ndFont  si
              _dupOpcode,                   # is2ndFont  si  si
              p([1]),                       # is2ndFont  si  si  1
              _addOpcode,                   # is2ndFont  si  si+1
              _rsOpcode,                    # is2ndFont  si  instCtrlValue2
              _swapOpcode,                  # is2ndFont  instCtrlValue2  si
              _rsOpcode,                    # is2ndFont  instCtrlValue2  instCtrlValue1
              _instctrlOpcode])             # is2ndFont  -- all sequences must leave stack thus
        
        if 'minimumDistance' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['minimumDistance']]),  # is2ndFont  is2ndFont  minDistBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  minDistValue
              _smdOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        # For round state, it's nice if the TrueType engine is intelligent
        # about interpreting SROUND values that match the special round opcodes
        # (like SROUND of 0x44 being internally short-circuited to RDTG), but
        # strictly speaking we do not require this. SROUND works just fine.
        
        if 'roundState' in nt:
            v.extend([                      # stack, starts off as is2ndFont
              _dupOpcode,                   # is2ndFont  is2ndFont
              _dupOpcode,                   # is2ndFont  is2ndFont  is2ndFont
              _addOpcode,                   # is2ndFont  2*is2ndFont
              p([kti['roundState']]),       # is2ndFont  2*is2ndFont  roundStateBase
              _addOpcode,                   # is2ndFont  si
              _dupOpcode,                   # is2ndFont  si  si
              p([1]),                       # is2ndFont  si  si  1
              _addOpcode,                   # is2ndFont  si  si+1
              _rsOpcode,                    # is2ndFont  si  roundValue
              _swapOpcode,                  # is2ndFont  roundValue  si
              _rsOpcode,                    # is2ndFont  roundValue  is45Case
              _ifOpcode,                    # is2ndFont  roundValue
              _s45RoundOpcode,              # is2ndFont
              _elseOpcode,                  # is2ndFont  roundValue
              _sroundOpcode,                # is2ndFont
              _eifOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        if 'scanControl' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['scanControl']]),      # is2ndFont  is2ndFont  scanCtrlBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  scanCtrlValue
              _scanctrlOpcode])             # is2ndFont  -- all sequences must leave stack thus
        
        if 'scanType' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['scanType']]),         # is2ndFont  is2ndFont  scanTypeBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  scanTypeValue
              _scantypeOpcode])             # is2ndFont  -- all sequences must leave stack thus
        
        if 'singleWidthCutIn' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['singleWidthCutIn']]), # is2ndFont  is2ndFont  sswciBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  sswciValue
              _sswciOpcode])                # is2ndFont  -- all sequences must leave stack thus
        
        if 'singleWidthValue' in nt:
            v.extend([                      # STACK (starts with just is2ndFont)
              _dupOpcode,                   # is2ndFont  is2ndFont
              p([kti['singleWidthValue']]), # is2ndFont  is2ndFont  sswBase
              _addOpcode,                   # is2ndFont  si
              _rsOpcode,                    # is2ndFont  sswValue
              _sswOpcode])                  # is2ndFont  -- all sequences must leave stack thus
        
        v.append(_popOpcode)  # all the above left only is2ndFont on stack, so pop it off
        fpgm = self.editor.fpgm
        self.synthFDEFIndex = _findAvailIndex(fpgm)
        fpgm[self.synthFDEFIndex] = hints_tt.Hints(v)
    
    #
    # Public methods
    #
    
    def tweak(self):
        """
        Public entry point for making all the editor changes.
        """
        
        self.tracker.commentStart("Setting tables to preserve graphics state")
        self._gatherStats()
        self._filterOutMonads()
        self._makeAlternateFDEFs()
        self._makeNewStorageMap()
        self._makePrepFpgmChanges()
        self._makeSyntheticFDEF()
        self._makeGlyphChanges()
        # self.editor.maxp.maxStackElements += 1000
        # self.editor.changed('maxp')
        self.tracker.commentEnd()
    
    #
    # Constants
    #
    
    m = common.nameToOpcodeMap
    f = functools.partial
    
    opcodeToKind = {
      m["FLIPOFF"]:
        (f(_makePiece_setOneConstant, constant=0), set(['autoFlip'])),
      m["FLIPON"]:
        (f(_makePiece_setOneConstant, constant=1), set(['autoFlip'])),
      m["INSTCTRL"]:
        (_makePiece_dupTwo, set(['instructControl'])),
      m["RDTG"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x44), set(['roundState'])),
      m["ROFF"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x04), set(['roundState'])),
      m["RTDG"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x08), set(['roundState'])),
      m["RTG"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x48), set(['roundState'])),
      m["RTHG"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x68), set(['roundState'])),
      m["RUTG"]:
        (f(_makePiece_setTwoConstants, constant1=0, constant2=0x40), set(['roundState'])),
      m["S45ROUND"]:
        (f(_makePiece_dupOneSetOne, constant=1), set(['roundState'])),
      m["SCANCTRL"]:
        (_makePiece_dupOne, set(['scanControl'])),
      m["SCANTYPE"]:
        (_makePiece_dupOne, set(['scanType'])),
      m["SCVTCI"]:
        (_makePiece_dupOne, set(['cvtCutIn'])),
      m["SDB"]:
        (_makePiece_dupOne, set(['deltaBase'])),
      m["SDS"]:
        (_makePiece_dupOne, set(['deltaShift'])),
      m["SMD"]:
        (_makePiece_dupOne, set(['minimumDistance'])),
      m["SROUND"]:
        (f(_makePiece_dupOneSetOne, constant=0), set(['roundState'])),
      m["SSW"]:
        (_makePiece_dupOne, set(['singleWidthValue'])),
      m["SSWCI"]:
        (_makePiece_dupOne, set(['singleWidthCutIn']))}
    
    kindToCounts = {  # kind -> (componentsInGSVar, neededStorageCells)
      'autoFlip': (1, 1),
      'cvtCutIn': (1, 1),
      'deltaBase': (1, 1),
      'deltaShift': (1, 1),
      'instructControl': (1, 2),
      'minimumDistance': (1, 1),
      'roundState': (3, 2),
      'scanControl': (1, 1),
      'scanType': (1, 1),
      'singleWidthCutIn': (1, 1),
      'singleWidthValue': (1, 1)}
    
    del m

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

