#
# hints_tt.py
#
# Copyright © 2005-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Contiguous sequences of opcode objects.
"""

# System imports
import functools
import logging
import math
import operator
import sys

# Other imports
from fontio3.hints import common, opcode_tt

from fontio3.hints.details import (
  hint_aa,
  hint_abs,
  hint_add,
  hint_alignpts,
  hint_alignrp,
  hint_and,
  hint_call,
  hint_ceiling,
  hint_cindex,
  hint_clear,
  hint_debug,
  hint_deltac,
  hint_deltak,
  hint_deltal,
  hint_deltap,
  hint_deltas,
  hint_depth,
  hint_div,
  hint_dup,
  hint_eif,
  hint_else,
  hint_eq,
  hint_even,
  hint_flipoff,
  hint_flipon,
  hint_flippt,
  hint_fliprgoff,
  hint_fliprgon,
  hint_floor,
  hint_gc,
  hint_getinfo,
  hint_gfv,
  hint_gt,
  hint_gteq,
  hint_if,
  hint_instctrl,
  hint_ip,
  hint_isect,
  hint_iup,
  hint_jmpr,
  hint_jrof,
  hint_jrot,
  hint_loopcall,
  hint_lt,
  hint_lteq,
  hint_mazdelta,
  hint_mazmode,
  hint_mazstroke,
  hint_max,
  hint_md,
  hint_mdap,
  hint_mdrp,
  hint_miap,
  hint_min,
  hint_mindex,
  hint_mirp,
  hint_mppem,
  hint_mps,
  hint_msirp,
  hint_mul,
  hint_neg,
  hint_neq,
  hint_not,
  hint_nround,
  hint_odd,
  hint_or,
  hint_pop,
  hint_rcvt,
  hint_rdtg,
  hint_roff,
  hint_roll,
  hint_round,
  hint_rs,
  hint_rtdg,
  hint_rtg,
  hint_rthg,
  hint_rutg,
  hint_scanctrl,
  hint_scantype,
  hint_scfs,
  hint_scvtci,
  hint_sdb,
  hint_sdpvtl,
  hint_sds,
  hint_sfvfs,
  hint_sfvtca,
  hint_sfvtl,
  hint_sfvtpv,
  hint_shc,
  hint_shp,
  hint_shpix,
  hint_shz,
  hint_sloop,
  hint_smd,
  hint_spvfs,
  hint_spvtca,
  hint_spvtl,
  hint_sround,
  hint_srp0,
  hint_srp1,
  hint_srp2,
  hint_ssw,
  hint_sswci,
  hint_sub,
  hint_svtca,
  hint_swap,
  hint_szp0,
  hint_szp1,
  hint_szp2,
  hint_szps,
  hint_utp,
  hint_wcvtf,
  hint_wcvtp,
  hint_ws)

from fontio3.hints.history import historygroup, op, push, refpt, storage
from fontio3.triple import collection, triple
from fontio3.utilities import pp, walkerbit, writer

# -----------------------------------------------------------------------------

#
# Constants
#

nameToOpcodeMap = common.nameToOpcodeMap
opcodeToNameMap = common.opcodeToNameMap
_op_CLEAR = nameToOpcodeMap["CLEAR"]
_op_EIF = nameToOpcodeMap["EIF"]
_op_ELSE = nameToOpcodeMap["ELSE"]
_op_IF = nameToOpcodeMap["IF"]
_preIndenters = frozenset([_op_EIF, _op_ELSE])
_postIndenters = frozenset([_op_ELSE, _op_IF])

_jumpOpcodes = frozenset([
  nameToOpcodeMap["JMPR"],
  nameToOpcodeMap["JROF"],
  nameToOpcodeMap["JROT"]])

Triple = triple.Triple
Collection = collection.Collection
toCollection = collection.toCollection

HG = historygroup.HistoryGroup
HE_op = op.HistoryEntry_op
HE_push = push.HistoryEntry_push
HE_refPt = refpt.HistoryEntry_refPt
HE_storage = storage.HistoryEntry_storage

synthFDEFIdentifier = -21555  # used by hints_tt.Hints.isSyntheticMergeFDEF()
doNotProceedPC = common.doNotProceedPC

# -----------------------------------------------------------------------------

#
# Exceptions
#

class CollectionUnsupported(TypeError):
    """
    Certain stack elements used by hints (e.g. the count in a DELTA hint) may
    not be Collections. If one is used there, this exception is raised.
    """

class CountInvalid(ValueError):
    """
    This exception is raised when a hint specified a count which is
    non-positive.
    """

class IFWithNoCondition(ValueError):
    """
    This exception is raised when an IF opcode is executed where the condition
    on top of the stack is an empty Collection.
    """

class InvalidCVTIndex(IndexError):
    """
    This exception is raised when a RCVT references a non-existent CVT entry.
    """

class InvalidStackIndex(IndexError):
    """
    This exception is raised if a hint refers to a stack position explicitly
    and the specified index is invalid. This can arise in CINDEX or MINDEX
    hints, for example.
    """

class LoopInvalid(ValueError):
    """
    This exception is raised if the graphicsState loop value is nonpositive.
    """

class MultipleELSE(ValueError):
    """
    This exception is raised if multiple ELSE opcodes are encountered without
    an intervening EIF or IF opcode.
    """

class StackUnderflow(IndexError):
    """
    This exception is raised when a hint attempts to pop more data from the
    TrueType stack than is actually present.
    """

class UnknownFunction(KeyError):
    """
    This exception is raised when a CALL or LOOPCALL attempts to call a
    nonexistent function.
    """

class UnknownOpcode(KeyError):
    """
    This exception is raised when an opcode is encountered which does not
    exist in the TrueType spec (or, someday, as an IDEF). This can happen if
    fontio3 attempts to work with TrueType 2.0 fonts containing ADJUST or RAW
    opcodes, since Apple has not published the details of those.
    """

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hints(list):
    """
    Objects representing a sequence of opcodes.
    
    These are lists of OpcodeNew-class objects. TrueType execution of these
    objects is permitted, but is limited to noting stack effects.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable=None, **kwArgs):
        """
        Initializes the object as specified, and constructs various internal
        maps to make it easier to edit later.
        
        If the optional "createdFrom" keyword argument is provided it should be
        a pair whose first element is the parent object and whose second
        element is the offset from the start of the parent to the beginning of
        this object. The "createdFrom" attribute is used to make sure the
        correct object and PC value is included in statistics annotations.
        
        >>> o1 = opcode_tt.Opcode_push([1, 2, 3])
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> h = Hints([o1, o2])
        """
        
        if iterable is not None:
            self.extend(iterable)
        
        self.infoString = kwArgs.get('infoString', repr(id(self)))
        self.createdFrom = kwArgs.get('createdFrom', (None, 0))
        self.isFDEF = kwArgs.get('isFDEF', False)
        self.ultParent, self.ultDelta = self, 0
        thisCF = self.ultParent.createdFrom
        
        while thisCF[0] is not None:
            self.ultParent = thisCF[0]
            self.ultDelta += thisCF[1]
            thisCF = self.ultParent.createdFrom
    
    #
    # Class methods
    #
    
    @classmethod
    def frombytes(cls, s, **kwArgs):
        return cls.fromwalker(walkerbit.StringWalker(s), **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        if kwArgs.get('suppressWatermark', True):
            if w.length() > 3:
                op1, n, op2 = w.unpack("3B", advance=False)
            
                if op1 == 0xB0 and op2 == 0x1C:
                    w.skip(n + 2)
        
        def provider():
            while w.stillGoing():
                yield(opcode_tt.fromWalker(w))
        
        return cls(provider(), **kwArgs)
    
    #
    # Special methods
    #
    
    def __copy__(self):
        """
        Returns a shallow copy.
        
        >>> o1 = opcode_tt.Opcode_push([1, 2, 3])
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> h = Hints([o1, o2])
        >>> h2 = h.__copy__()
        >>> h is h2, h == h2
        (False, True)
        >>> h.__dict__ is h2.__dict__, h.__dict__ == h2.__dict__
        (False, True)
        >>> h[0] is h2[0]
        True
        """
        
        r = Hints(self)
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy.
        
        >>> o1 = opcode_tt.Opcode_push([1, 2, 3])
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> h = Hints([o1, o2])
        >>> h2 = h.__deepcopy__()
        >>> h is h2, h == h2
        (False, True)
        >>> h.__dict__ is h2.__dict__, h.__dict__ == h2.__dict__
        (False, True)
        >>> h[0] is h2[0]
        False
        """
        
        r = Hints(obj.__deepcopy__(memo) for obj in self)
        # In the following, all are immutable, so a simple copy is OK.
        r.__dict__ = self.__dict__.copy()
        return r
    
    def __str__(self):
        sv = ['[']
        sv.append(', '.join(str(obj) for obj in self))
        sv.append(']')
        return ''.join(sv)
    
    #
    # Private methods
    #
    
    def _16BitCheck(self, opString, value, logger, signed):
        valueColl = toCollection(value)
        isBad = False
        lowCheck = (-32768 if signed else 0)
        highCheck = (32767 if signed else 65535)
        
        if None in valueColl:
            isBad = True
        
        elif valueColl.min() < lowCheck:
            isBad = True
        
        elif valueColl.max() > highCheck:
            isBad = True
        
        elif any(n != int(n) for n in valueColl):
            isBad = True
        
        if isBad:
            logger.error((
              'E6053',
              (opString,
               self.ultParent.infoString,
               self.state.pc + self.ultDelta,
               value),
              "%s hint in %s (PC %d) has value %s that does "
              "not fit in 16 bits."))
            
            self.state._validationFailed = True
            return False
        
        return True
    
    def _8BitCheck(self, opString, value, logger, signed=False):
        # The only clients of this for now are unsigned; that may change
        valueColl = toCollection(value)
        isBad = False
        lowCheck = (-128 if signed else 0)
        highCheck = (127 if signed else 255)
        
        if None in valueColl:
            isBad = True
        
        elif valueColl.min() < lowCheck:
            isBad = True
        
        elif valueColl.max() > highCheck:
            isBad = True
        
        elif any(n != int(n) for n in valueColl):
            isBad = True
        
        if isBad:
            logger.error((
              'E6054',
              (opString,
               self.ultParent.infoString,
               self.state.pc + self.ultDelta,
               value),
              "%s hint in %s (PC %d) has value %s that does "
              "not fit in 8 bits."))
            
            self.state._validationFailed = True
            return False
        
        return True
    
    def _callSub(self, functionIndex, **kwArgs):
        """
        Function that calls the FDEF indexed by functionIndex, which may be
        either a simple number or a Collection.
        """
        
        state = self.state
        savePC = state.pc
        logger = self._getLogger(**kwArgs)
        fColl = toCollection(functionIndex)
        fColl = toCollection(int(n) for n in fColl)
        fd = state._editor.get('fpgm', {})
        fes = kwArgs.get('fdefEntryStack', [])
        fatObj = kwArgs.get('fdefArgTracer', None)
        
        if any(f not in fd for f in fColl):
            logger.error((
              'E6020',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "Calling an unknown FDEF was attempted in %s (PC %d)."))
            
            state._validationFailed = True
            state.assign('pc', doNotProceedPC)
            return
        
        if len(fColl) == 1:
            state.assign('pc', 0)
            whichFunc = int(fColl)
            fes.append(whichFunc)
            func = fd[whichFunc]
            saveIS = func.infoString
            func.infoString = "%s (from %s)" % (saveIS, self.ultParent.infoString)
            
            if fatObj is not None:
                fatObj.startFDEF(whichFunc)
            
            func.run(state, **kwArgs)
            
            if fatObj is not None:
                fatObj.stopFDEF()
            
            func.infoString = saveIS
            # The following line happens because the state
            # might have changed via IFs in the function
            self.state = state = func.state
            fes.pop()
            
            # If the called function terminated with the special "do not
            # proceed" error code, propagate that upward.
            
            if state.pc != doNotProceedPC:
                state.assign('pc', savePC)
        
        else:
            postCallStates = []
            count = len(fColl)
            
            for i, f in enumerate(fColl):
                if i < count - 1:
                    thisState = state.__deepcopy__()
                    thisState.assign('pc', 0)
                    fes.append(f)
                    saveIS = fd[f].infoString
                    fd[f].infoString = "%s (from %s)" % (saveIS, self.ultParent.infoString)
                    
                    if fatObj is not None:
                        fatObj.startFDEF(f)
                    
                    fd[f].run(thisState, **kwArgs)
                    
                    if fatObj is not None:
                        fatObj.stopFDEF()
                    
                    fd[f].infoString = saveIS
                    # The following line happens because the state
                    # might have changed via IFs in the function
                    thisState = fd[f].state
                    fes.pop()
                    postCallStates.append(thisState)
                
                else:
                    state.assign('pc', 0)
                    fes.append(f)
                    saveIS = fd[f].infoString
                    fd[f].infoString = "%s (from %s)" % (saveIS, self.ultParent.infoString)
                    fd[f].run(state, **kwArgs)
                    fd[f].infoString = saveIS
                    # The following line happens because the state
                    # might have changed via IFs in the function
                    self.state = state = fd[f].state
                    fes.pop()
            
            # If any of the called functions terminated with the special "do
            # not proceed" error code, propagate that upward. We don't bother
            # combining the results (an expensive operation) in this case.
            
            if (
              (state.pc == doNotProceedPC) or
              any(obj.pc == doNotProceedPC for obj in postCallStates)):
                
                state.assign('pc', doNotProceedPC)
            
            else:
                for otherState in postCallStates:
                    state.combine(otherState)
                    
                    if otherState._validationFailed:
                        state._validationFailed = True
                
                state.assign('pc', savePC)
    
    if __debug__:
        def _debugDump(self, d, final=False):
            state = self.state
            stream = d.get('stream', sys.stdout)
            print("  Stack depth: %d" % (len(state.stack),), file=stream)
            
            if 'priorState' in d:
                state.pprint_changes(d['priorState'], indent=2, stream=stream)
            else:
                state.pprint(indent=2, stream=stream)
            
            d['priorState'] = state.__deepcopy__()
            s = ("End of Block" if final else self[state.pc])
            print("%s: %s" % (self.infoString, s), file=stream)
    
    def _getContras(self, logger):
        """
        Finds the IF and ELSE sublists of self, on the assumption that
        self.state.pc holds the location of the initial IF on entry to this
        method.

        Returns a triple. The first element is a Hints-class object
        containing the IF branch, or None. The second element is a
        Hints-class object containing the ELSE branch, or None. The third
        element is the index of the EIF (or of the last opcode in self, if the
        IF didn't have a corresponding EIF).
        
        >>> h = _testingState()
        >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["IF"]))
        >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["SVTCA[x]"]))
        >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["ELSE"]))
        >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["SVTCA[y]"]))
        >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["EIF"]))
        >>> logger = utilities.makeDoctestLogger("_getContras_test")
        >>> hIF, hELSE, eifOffset = h._getContras(logger)
        >>> print(hIF, hELSE, eifOffset)
        [SVTCA[x]] [SVTCA[y]] 4
        >>> del h[2]
        >>> hIF, hELSE, eifOffset = h._getContras(logger)
        >>> print(hIF, hELSE, eifOffset)
        [SVTCA[x], SVTCA[y]] None 3
        """
        
        startELSE, endIF, endELSE = -1, -1, -1
        eifOffset = None
        currDepth = 0
        walkPC = startIF = self.state.pc + 1  # first opcode past initial IF
        
        while walkPC < len(self):
            opObj = self[walkPC]
            
            if not opObj.isPush():
                op = opObj.opcode
                
                if op == _op_IF:
                    currDepth += 1
                
                elif op == _op_EIF:
                    if currDepth:
                        currDepth -= 1
                    
                    else:
                        if endIF == -1:
                            endIF = walkPC
                        
                        if startELSE != -1:
                            endELSE = walkPC
                        
                        eifOffset = walkPC
                        break
                
                elif op == _op_ELSE:
                    if not currDepth:
                        if startELSE != -1:
                            logger.error((
                              'V0492',
                              (self.ultParent.infoString,
                               self.state.pc + self.ultDelta),
                              "Two ELSEs without intervening IF or EIF "
                              "found in %s (PC %d)."))
                            
                            self.state._validationFailed = True
                            startIF = endIF = startELSE = endELSE = -1
                            eifOffset = len(self) - 1  # short circuit
                            break
                        
                        endIF = walkPC
                        startELSE = walkPC + 1
            
            walkPC += 1
        
        if endIF > startIF:
            info = "IF branch at PC %d of %s" % (startIF, self.infoString)
            
            hIF = Hints(
              self[startIF:endIF],
              createdFrom = (self, startIF),
              infoString = info,
              isFDEF = self.isFDEF)
        
        else:
            hIF = None
        
        if endELSE > startELSE:
            info = "ELSE branch at PC %d of %s" % (startELSE, self.infoString)
            
            hELSE = Hints(
              self[startELSE:endELSE],
              createdFrom = (self, startELSE),
              infoString = info,
              isFDEF = self.isFDEF)
        
        else:
            hELSE = None
        
        if eifOffset is None:
            logger.warning((
                ('E6008' if hELSE is not None else 'E6024'),
                (self.ultParent.infoString, self.state.pc + self.ultDelta),
                "No EIF found after IF or ELSE in %s (PC %d)."))
            
            eifOffset = len(self) - 1
        
        if hIF is None and hELSE is None:
            logger.error((
              'V0802',
              (self.ultParent.infoString,
               self.state.pc + self.ultDelta),
              "An empty IF-EIF was found in %s (PC %d)."))
            
            self.state._validationFailed = True
            eifOffset = len(self) - 1  # short circuit
        
        return hIF, hELSE, eifOffset
    
    def _getLogger(self, **kwArgs):
        """
        Gets and caches a logger. If there is a 'logger' keyword argument then
        it takes precedence. If not, we look for a '_logger' attribute on self.
        If neither of these is present, the default logger is obtained from the
        logging module.

        However one is obtained, it is also stored in the '_logger' attribute
        on self. This explains why most of the "_hint_xxx" methods below don't
        need to pass **kwArgs into their calls to _popRemove; the call to the
        _getLogger method sets things up so that subsequent calls would get the
        cached object.
        """
        
        if 'logger' in kwArgs:
            r = kwArgs['logger']
            self._logger = r
        
        elif hasattr(self, '_logger'):
            r = self._logger
        
        else:
            r = logging.getLogger()
            self._logger = r
        
        return r
    
    if 0:
        def _hintDispatchTable(self): pass
    
    f = functools.partial
    
    _hintDispatchTable = {
      nameToOpcodeMap["AA"]: hint_aa.hint_AA,
      nameToOpcodeMap["ABS"]: hint_abs.hint_ABS,
      nameToOpcodeMap["ADD"]: hint_add.hint_ADD,
      nameToOpcodeMap["ALIGNPTS"]: hint_alignpts.hint_ALIGNPTS,
      nameToOpcodeMap["ALIGNRP"]: hint_alignrp.hint_ALIGNRP,
      nameToOpcodeMap["AND"]: hint_and.hint_AND,
      nameToOpcodeMap["CALL"]: hint_call.hint_CALL,
      nameToOpcodeMap["CEILING"]: hint_ceiling.hint_CEILING,
      nameToOpcodeMap["CINDEX"]: hint_cindex.hint_CINDEX,
      nameToOpcodeMap["CLEAR"]: hint_clear.hint_CLEAR,
      nameToOpcodeMap["DEBUG"]: hint_debug.hint_DEBUG,
      nameToOpcodeMap["DELTAC1"]: f(hint_deltac.hint_DELTAC, bandDelta=0),
      nameToOpcodeMap["DELTAC2"]: f(hint_deltac.hint_DELTAC, bandDelta=16),
      nameToOpcodeMap["DELTAC3"]: f(hint_deltac.hint_DELTAC, bandDelta=32),
      nameToOpcodeMap["DELTAK1"]: f(hint_deltak.hint_DELTAK, bandDelta=0),
      nameToOpcodeMap["DELTAK2"]: f(hint_deltak.hint_DELTAK, bandDelta=16),
      nameToOpcodeMap["DELTAK3"]: f(hint_deltak.hint_DELTAK, bandDelta=32),
      nameToOpcodeMap["DELTAL1"]: f(hint_deltal.hint_DELTAL, bandDelta=0),
      nameToOpcodeMap["DELTAL2"]: f(hint_deltal.hint_DELTAL, bandDelta=16),
      nameToOpcodeMap["DELTAL3"]: f(hint_deltal.hint_DELTAL, bandDelta=32),
      nameToOpcodeMap["DELTAP1"]: f(hint_deltap.hint_DELTAP, bandDelta=0),
      nameToOpcodeMap["DELTAP2"]: f(hint_deltap.hint_DELTAP, bandDelta=16),
      nameToOpcodeMap["DELTAP3"]: f(hint_deltap.hint_DELTAP, bandDelta=32),
      nameToOpcodeMap["DELTAS1"]: f(hint_deltas.hint_DELTAS, bandDelta=0),
      nameToOpcodeMap["DELTAS2"]: f(hint_deltas.hint_DELTAS, bandDelta=16),
      nameToOpcodeMap["DELTAS3"]: f(hint_deltas.hint_DELTAS, bandDelta=32),
      nameToOpcodeMap["DEPTH"]: hint_depth.hint_DEPTH,
      nameToOpcodeMap["DIV"]: hint_div.hint_DIV,
      nameToOpcodeMap["DUP"]: hint_dup.hint_DUP,
      nameToOpcodeMap["EIF"]: hint_eif.hint_EIF,
      nameToOpcodeMap["ELSE"]: hint_else.hint_ELSE,
      nameToOpcodeMap["EQ"]: hint_eq.hint_EQ,
      nameToOpcodeMap["EVEN"]: hint_even.hint_EVEN,
      nameToOpcodeMap["FLIPOFF"]: hint_flipoff.hint_FLIPOFF,
      nameToOpcodeMap["FLIPON"]: hint_flipon.hint_FLIPON,
      nameToOpcodeMap["FLIPPT"]: hint_flippt.hint_FLIPPT,
      nameToOpcodeMap["FLIPRGOFF"]: hint_fliprgoff.hint_FLIPRGOFF,
      nameToOpcodeMap["FLIPRGON"]: hint_fliprgon.hint_FLIPRGON,
      nameToOpcodeMap["FLOOR"]: hint_floor.hint_FLOOR,
      nameToOpcodeMap["GC[current]"]: f(hint_gc.hint_GC, original=False),
      nameToOpcodeMap["GC[original]"]: f(hint_gc.hint_GC, original=True),
      nameToOpcodeMap["GETINFO"]: hint_getinfo.hint_GETINFO,
      nameToOpcodeMap["GFV"]: hint_gfv.hint_GFV,
      nameToOpcodeMap["GPV"]: f(hint_gfv.hint_GFV, which='projectionVector'),
      nameToOpcodeMap["GT"]: hint_gt.hint_GT,
      nameToOpcodeMap["GTEQ"]: hint_gteq.hint_GTEQ,
      nameToOpcodeMap["IF"]: hint_if.hint_IF,
      nameToOpcodeMap["INSTCTRL"]: hint_instctrl.hint_INSTCTRL,
      nameToOpcodeMap["IP"]: hint_ip.hint_IP,
      nameToOpcodeMap["ISECT"]: hint_isect.hint_ISECT,
      nameToOpcodeMap["IUP[x]"]: f(hint_iup.hint_IUP, inX=True),
      nameToOpcodeMap["IUP[y]"]: f(hint_iup.hint_IUP, inX=False),
      nameToOpcodeMap["JMPR"]: hint_jmpr.hint_JMPR,
      nameToOpcodeMap["JROF"]: hint_jrof.hint_JROF,
      nameToOpcodeMap["JROT"]: hint_jrot.hint_JROT,
      nameToOpcodeMap["LOOPCALL"]: hint_loopcall.hint_LOOPCALL,
      nameToOpcodeMap["LT"]: hint_lt.hint_LT,
      nameToOpcodeMap["LTEQ"]: hint_lteq.hint_LTEQ,
      nameToOpcodeMap["MAZDELTA1"]: f(hint_mazdelta.hint_MAZDELTA, bandDelta=0),
      nameToOpcodeMap["MAZDELTA2"]: f(hint_mazdelta.hint_MAZDELTA, bandDelta=16),
      nameToOpcodeMap["MAZDELTA3"]: f(hint_mazdelta.hint_MAZDELTA, bandDelta=32),
      nameToOpcodeMap["MAZMODE"]: hint_mazmode.hint_MAZMODE,
      nameToOpcodeMap["MAZSTROKE"]: hint_mazstroke.hint_MAZSTROKE,
      nameToOpcodeMap["MAX"]: hint_max.hint_MAX,
      nameToOpcodeMap["MD[gridfitted]"]: f(hint_md.hint_MD, original=False),
      nameToOpcodeMap["MD[original]"]: f(hint_md.hint_MD, original=True),
      nameToOpcodeMap["MDAP[noRound]"]: f(hint_mdap.hint_MDAP, round=False),
      nameToOpcodeMap["MDAP[round]"]: f(hint_mdap.hint_MDAP, round=True),
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=False, color='gray'),
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=False, color='black'),
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=False, color='white'),
      0xC3: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=True, color='gray'),
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=True, color='black'),
      nameToOpcodeMap["MDRP[noSetRP0, noRespectMinimumDistance, roundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=False, round=True, color='white'),
      0xC7: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=False, color='gray'),
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=False, color='black'),
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=False, color='white'),
      0xCB: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, roundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=True, color='gray'),
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, roundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=True, color='black'),
      nameToOpcodeMap["MDRP[noSetRP0, respectMinimumDistance, roundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=False, minDistance=True, round=True, color='white'),
      0xCF: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=False, color='gray'),
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=False, color='black'),
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=False, color='white'),
      0xD3: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, roundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=True, color='gray'),
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, roundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=True, color='black'),
      nameToOpcodeMap["MDRP[setRP0, noRespectMinimumDistance, roundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=False, round=True, color='white'),
      0xD7: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=False, color='gray'),
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=False, color='black'),
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=False, color='white'),
      0xDB: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, roundDistance, black]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=True, color='black'),
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, roundDistance, gray]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=True, color='gray'),
      nameToOpcodeMap["MDRP[setRP0, respectMinimumDistance, roundDistance, white]"]:
        f(hint_mdrp.hint_MDRP, setRP0=True, minDistance=True, round=True, color='white'),
      0xDF: hint_mdrp.hint_MDRP_badColor,
      nameToOpcodeMap["MIAP[noRound]"]: f(hint_miap.hint_MIAP, round=False),
      nameToOpcodeMap["MIAP[round]"]: f(hint_miap.hint_MIAP, round=True),
      nameToOpcodeMap["MIN"]: hint_min.hint_MIN,
      nameToOpcodeMap["MINDEX"]: hint_mindex.hint_MINDEX,
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=False, color='gray'),
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=False, color='black'),
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=False, color='white'),
      0xE3: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=True, color='gray'),
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=True, color='black'),
      nameToOpcodeMap["MIRP[noSetRP0, noRespectMinimumDistance, roundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=False, round=True, color='white'),
      0xE7: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=False, color='gray'),
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=False, color='black'),
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=False, color='white'),
      0xEB: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, roundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=True, color='gray'),
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, roundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=True, color='black'),
      nameToOpcodeMap["MIRP[noSetRP0, respectMinimumDistance, roundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=False, minDistance=True, round=True, color='white'),
      0xEF: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=False, color='gray'),
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=False, color='black'),
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=False, color='white'),
      0xF3: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, roundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=True, color='gray'),
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, roundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=True, color='black'),
      nameToOpcodeMap["MIRP[setRP0, noRespectMinimumDistance, roundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=False, round=True, color='white'),
      0xF7: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, noRoundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=False, color='gray'),
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, noRoundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=False, color='black'),
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, noRoundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=False, color='white'),
      0xFB: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, roundDistance, black]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=True, color='black'),
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, roundDistance, gray]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=True, color='gray'),
      nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, roundDistance, white]"]:
        f(hint_mirp.hint_MIRP, setRP0=True, minDistance=True, round=True, color='white'),
      0xFF: hint_mirp.hint_MIRP_badColor,
      nameToOpcodeMap["MPPEM"]: hint_mppem.hint_MPPEM,
      nameToOpcodeMap["MPS"]: hint_mps.hint_MPS,
      nameToOpcodeMap["MSIRP[noSetRP0]"]: f(hint_msirp.hint_MSIRP, setRP0=False),
      nameToOpcodeMap["MSIRP[setRP0]"]: f(hint_msirp.hint_MSIRP, setRP0=True),
      nameToOpcodeMap["MUL"]: hint_mul.hint_MUL,
      nameToOpcodeMap["NEG"]: hint_neg.hint_NEG,
      nameToOpcodeMap["NEQ"]: hint_neq.hint_NEQ,
      nameToOpcodeMap["NOT"]: hint_not.hint_NOT,
      nameToOpcodeMap["NROUND[black]"]: f(hint_nround.hint_NROUND, color='black'),
      nameToOpcodeMap["NROUND[gray]"]: f(hint_nround.hint_NROUND, color='gray'),
      nameToOpcodeMap["NROUND[white]"]: f(hint_nround.hint_NROUND, color='white'),
      0x6F: hint_nround.hint_NROUND_badColor,
      nameToOpcodeMap["ODD"]: hint_odd.hint_ODD,
      nameToOpcodeMap["OR"]: hint_or.hint_OR,
      nameToOpcodeMap["POP"]: hint_pop.hint_POP,
      nameToOpcodeMap["RCVT"]: hint_rcvt.hint_RCVT,
      nameToOpcodeMap["RDTG"]: hint_rdtg.hint_RDTG,
      nameToOpcodeMap["ROFF"]: hint_roff.hint_ROFF,
      nameToOpcodeMap["ROLL"]: hint_roll.hint_ROLL,
      nameToOpcodeMap["ROUND[black]"]: f(hint_round.hint_ROUND, color='black'),
      nameToOpcodeMap["ROUND[gray]"]: f(hint_round.hint_ROUND, color='gray'),
      nameToOpcodeMap["ROUND[white]"]: f(hint_round.hint_ROUND, color='white'),
      0x6B: hint_round.hint_ROUND_badColor,
      nameToOpcodeMap["RS"]: hint_rs.hint_RS,
      nameToOpcodeMap["RTDG"]: hint_rtdg.hint_RTDG,
      nameToOpcodeMap["RTG"]: hint_rtg.hint_RTG,
      nameToOpcodeMap["RTHG"]: hint_rthg.hint_RTHG,
      nameToOpcodeMap["RUTG"]: hint_rutg.hint_RUTG,
      nameToOpcodeMap["S45ROUND"]: f(hint_sround.hint_SROUND, is45Case=True),
      nameToOpcodeMap["SCANCTRL"]: hint_scanctrl.hint_SCANCTRL,
      nameToOpcodeMap["SCANTYPE"]: hint_scantype.hint_SCANTYPE,
      nameToOpcodeMap["SCFS"]: hint_scfs.hint_SCFS,
      nameToOpcodeMap["SCVTCI"]: hint_scvtci.hint_SCVTCI,
      nameToOpcodeMap["SDB"]: hint_sdb.hint_SDB,
      nameToOpcodeMap["SDPVTL[parallel]"]: f(hint_sdpvtl.hint_SDPVTL, parallel=True),
      nameToOpcodeMap["SDPVTL[perpendicular]"]: f(hint_sdpvtl.hint_SDPVTL, parallel=False),
      nameToOpcodeMap["SDS"]: hint_sds.hint_SDS,
      nameToOpcodeMap["SFVFS"]: hint_sfvfs.hint_SFVFS,
      nameToOpcodeMap["SFVTCA[x]"]: f(hint_sfvtca.hint_SFVTCA, toX=True),
      nameToOpcodeMap["SFVTCA[y]"]: f(hint_sfvtca.hint_SFVTCA, toX=False),
      nameToOpcodeMap["SFVTL[parallel]"]: f(hint_sfvtl.hint_SFVTL, parallel=True),
      nameToOpcodeMap["SFVTL[perpendicular]"]: f(hint_sfvtl.hint_SFVTL, parallel=False),
      nameToOpcodeMap["SFVTPV"]: hint_sfvtpv.hint_SFVTPV,
      nameToOpcodeMap["SHC[RP1]"]: f(hint_shc.hint_SHC, refPt=1),
      nameToOpcodeMap["SHC[RP2]"]: f(hint_shc.hint_SHC, refPt=2),
      nameToOpcodeMap["SHP[RP1]"]: f(hint_shp.hint_SHP, refPt=1),
      nameToOpcodeMap["SHP[RP2]"]: f(hint_shp.hint_SHP, refPt=2),
      nameToOpcodeMap["SHPIX"]: hint_shpix.hint_SHPIX,
      nameToOpcodeMap["SHZ[RP1]"]: f(hint_shz.hint_SHZ, refPt=1),
      nameToOpcodeMap["SHZ[RP2]"]: f(hint_shz.hint_SHZ, refPt=2),
      nameToOpcodeMap["SLOOP"]: hint_sloop.hint_SLOOP,
      nameToOpcodeMap["SMD"]: hint_smd.hint_SMD,
      nameToOpcodeMap["SPVFS"]: hint_spvfs.hint_SPVFS,
      nameToOpcodeMap["SPVTCA[x]"]: f(hint_spvtca.hint_SPVTCA, toX=True),
      nameToOpcodeMap["SPVTCA[y]"]: f(hint_spvtca.hint_SPVTCA, toX=False),
      nameToOpcodeMap["SPVTL[parallel]"]: f(hint_spvtl.hint_SPVTL, parallel=True),
      nameToOpcodeMap["SPVTL[perpendicular]"]: f(hint_spvtl.hint_SPVTL, parallel=False),
      nameToOpcodeMap["SROUND"]: hint_sround.hint_SROUND,
      nameToOpcodeMap["SRP0"]: hint_srp0.hint_SRP0,
      nameToOpcodeMap["SRP1"]: hint_srp1.hint_SRP1,
      nameToOpcodeMap["SRP2"]: hint_srp2.hint_SRP2,
      nameToOpcodeMap["SSW"]: hint_ssw.hint_SSW,
      nameToOpcodeMap["SSWCI"]: hint_sswci.hint_SSWCI,
      nameToOpcodeMap["SUB"]: hint_sub.hint_SUB,
      nameToOpcodeMap["SVTCA[x]"]: f(hint_svtca.hint_SVTCA, toX=True),
      nameToOpcodeMap["SVTCA[y]"]: f(hint_svtca.hint_SVTCA, toX=False),
      nameToOpcodeMap["SWAP"]: hint_swap.hint_SWAP,
      nameToOpcodeMap["SZP0"]: hint_szp0.hint_SZP0,
      nameToOpcodeMap["SZP1"]: hint_szp1.hint_SZP1,
      nameToOpcodeMap["SZP2"]: hint_szp2.hint_SZP2,
      nameToOpcodeMap["SZPS"]: hint_szps.hint_SZPS,
      nameToOpcodeMap["UTP"]: hint_utp.hint_UTP,
      nameToOpcodeMap["WCVTF"]: hint_wcvtf.hint_WCVTF,
      nameToOpcodeMap["WCVTP"]: hint_wcvtp.hint_WCVTP,
      nameToOpcodeMap["WS"]: hint_ws.hint_WS}
    
    del f
    
    def _jumpToOffset(self, offset):
        """
        Changes the PC as indicated. On entry to this method self.state.pc
        should still be pointing to the JMPR, JROF or JROT opcode.
        """
        
        state = self.state
        origPC = state.pc  # for logging, if needed
        logger = self._getLogger()
        offset = self._toNumber(offset)
        
        if offset is None:
            state.assign('pc', doNotProceedPC)
            return
        
        self[state.pc].annotate(('jumpFrom', state.nextAnnotation[0]))
        
        if offset > 0:
            while offset > 0 and state.pc < len(self):
                origLength = self[state.pc].getOriginalLength()
                state.assign('pc', state.pc + 1)
                offset -= origLength
            
            if offset:
                logger.error((
                  'V0515',
                  (self.ultParent.infoString, origPC + self.ultDelta),
                  "Jump hint in %s (PC %d) attempts to jump to something "
                  "that is not a hint."))
                
                state._validationFailed = True
                state.assign('pc', doNotProceedPC)
                return
        
        elif offset < 0:
            while offset < 0 and state.pc >= 0:
                state.assign('pc', state.pc - 1)
                origLength = self[state.pc].getOriginalLength()
                offset += origLength
            
            if offset:
                logger.error((
                  'V0515',
                  (self.ultParent.infoString, origPC + self.ultDelta),
                  "Jump hint in %s (PC %d) attempts to jump to something "
                  "that is not a hint."))
                
                state._validationFailed = True
                state.assign('pc', doNotProceedPC)
                return
        
        else:
            
            logger.error((
              'V0516',
              (self.ultParent.infoString, origPC + self.ultDelta),
              "Jump hint in %s (PC %d) jumps to itself, which would "
              "cause an infinite loop."))
            
            state._validationFailed = True
            state.assign('pc', doNotProceedPC)
            return
        
        if state.pc >= len(self):
            logger.error((
              'V0515',
              (self.ultParent.infoString, origPC + self.ultDelta),
              "Jump hint in %s (PC %d) attempts to jump to something "
              "that is not a hint."))
            
            state._validationFailed = True
            state.assign('pc', doNotProceedPC)
            return
        
        self[state.pc].annotate(('jumpTo', state.nextAnnotation[0]))
        state.nextAnnotation[0] += 1
        state.changed('nextAnnotation')
    
    def _pointCheck(self, opString, whichToCheck, logger, extraInfo):
        okToProceed = True
        
        for (zone, pointObj, moves) in whichToCheck:
            assert zone in {0, 1}  # has to be a number, not a Collection
            
            if None in pointObj:
                logger.error((
                  'V0801',
                  (opString,
                   self.ultParent.infoString,
                   self.state.pc + self.ultDelta),
                  "%s opcode in %s (PC %d) uses an uninitialized or "
                  "otherwise bad point index."))
                
                self.state._validationFailed = True
                okToProceed = False
                continue
            
            count = self.state._numPoints[zone]
            
            if zone:  # zone is glyph zone
                for point in pointObj:
                    if (point < 0) or (point != int(point)):
                        
                        logger.error((
                          'V0531',
                          (opString,
                           self.ultParent.infoString,
                           self.state.pc + self.ultDelta,
                           point),
                          "%s opcode in %s (PC %d) refers to negative or "
                          "non-integer point index %s."))
                        
                        self.state._validationFailed = True
                        okToProceed = False
                        continue
                    
                    if point < count:
                        continue
                    
                    if point == count:
                        if moves:
                            
                            logger.info((
                              'V0529',
                              (opString,
                               self.ultParent.infoString,
                               self.state.pc + self.ultDelta,
                               point),
                              "%s opcode in %s (PC %d) is hinting phantom "
                              "origin (point %d)."))
                            
                            extraInfo['phantomOriginHinted'] = True
                            FV = self.state.graphicsState.freedomVector
                            
                            if FV[0] != 1 or FV[1] != 0:
                                logger.warning((
                                  'V0792',
                                  (opString,
                                   self.ultParent.infoString,
                                   self.state.pc + self.ultDelta,
                                   point),
                                  "%s opcode in %s (PC %d) is moving the "
                                  "phantom origin (point %d) in a direction "
                                  "other than X."))
                    
                    elif point == count + 1:
                        if moves:
                            
                            logger.info((
                              'V0529',
                              (opString,
                               self.ultParent.infoString,
                               self.state.pc + self.ultDelta,
                               point),
                              "%s opcode in %s (PC %d) is hinting phantom "
                              "advance (point %d)."))
                            
                            extraInfo['phantomAdvanceHinted'] = True
                            FV = self.state.graphicsState.freedomVector
                            
                            if FV[0] != 1 or FV[1] != 0:
                                logger.warning((
                                  'V0792',
                                  (opString,
                                   self.ultParent.infoString,
                                   self.state.pc + self.ultDelta,
                                   point),
                                  "%s opcode in %s (PC %d) is moving the "
                                  "phantom advance (point %d) in a direction "
                                  "other than X."))
                    
                    else:
                        
                        logger.warning((
                          'V0530',
                          (opString,
                           self.ultParent.infoString,
                           self.state.pc + self.ultDelta,
                           point),
                          "%s opcode in %s (PC %d) is hinting point %d, "
                          "which does not exist for this glyph."))
                        
                        okToProceed = False
            
            else:  # zone is twilight zone
                for point in pointObj:
                    if point >= count:
                        
                        logger.error((
                          'E6039',
                          (opString,
                           self.ultParent.infoString,
                           self.state.pc + self.ultDelta,
                           point),
                          "%s opcode in %s (PC %d) is hinting point %d in "
                          "the twilight zone, which does not exist."))
                        
                        self.state._validationFailed = True
                        okToProceed = False
        
        return okToProceed
    
    def _popRemove(self, obj, attr, count=1, **kwArgs):
        """
        Returns some number of contiguous elements at the end of the specified list
        object. This function also removes those items from the list. If the count
        is 1, the last item in the list is returned itself, unless coerceToList is
        True in which case a one-element list is returned.
    
        If coerceToCollection is True then all returned elements will have
        toCollection called on them before returning. This does NOT coalesce the
        returned values into a single Collection!
        
        A StackUnderflow is raised if there are not sufficient elements to do the
        specified pop.
        
        >>> h = _testingState()
        >>> h.state.stack = list(range(10))
        >>> h._popRemove(h.state, 'stack')
        9
        >>> h.state.stack
        [0, 1, 2, 3, 4, 5, 6, 7, 8]
        >>> h._popRemove(h.state, 'stack', coerceToList=True)
        [8]
        >>> h._popRemove(h.state, 'stack', 2)
        [6, 7]
        >>> h._popRemove(h.state, 'stack', 2, coerceToCollection=True)
        [Singles: [4], Singles: [5]]
        >>> h.state.stack
        [0, 1, 2, 3]
        """
        
        listObj = getattr(obj, attr)
        
        if len(listObj) < count:
            logger = self._getLogger(**kwArgs)
            
            logger.critical((
              'E6046',
              (self.ultParent.infoString, self.state.pc + self.ultDelta),
              "Stack underflow in %s (PC %d)."))
            
            self.state._validationFailed = True
            return None
        
        v = listObj[-count:]
        del listObj[-count:]
        obj.changed(attr)
        
        if kwArgs.get('coerceToCollection', False):
            v = [toCollection(obj) for obj in v]
        
        return (
          v[0] if count == 1 and (not kwArgs.get('coerceToList', False))
          else v)
    
    def _round(self, n, color='gray', coerceToNumber=True):
        """
        Returns a Collection (basis 64) with the results of rounding n
        according to the current round state, as defined in the graphics state.
        
        >>> h = _testingState()
        >>> h._round(1.25)
        1.0
        >>> h._round(toCollection([1.2, 1.4, 1.6], 64))
        Singles: [1.0, 2.0]
        >>> h._round(Collection([Triple(-65536, 65536, 1)], 64))
        Ranges: [(-1024.0, 1025.0, 1.0)]
        
        >>> Collection([Triple(None, None, 1)], 64)
        Ranges: [(*, *, 0.015625, phase=0.0)]
        >>> hint_rdtg.hint_RDTG(h)
        >>> h._round(Collection([Triple(None, None, 1)], 64))
        Ranges: [(*, *, 1.0, phase=0.0)]
        """
        
        state = self.state
        gs = state.graphicsState
        n = toCollection(n, 64)
        r = Collection(basis=64)
        
        for period in gs.roundState[0]:
            if period:
                recip = 1.0 / period
                
                for phase in gs.roundState[1]:
                    phase *= period
                    
                    for threshold in gs.roundState[2]:
                        if threshold == -1.0:
                            threshold = period - 1.0 / 64.0  # rework this!
                        else:
                            threshold *= period
                        
                        #if phase or threshold:
                        negColl, posColl = n.signedParts()
                        colDist = getattr(state.colorDistances, color)
                        posColl += colDist
                        
                        part = (
                          recip * (posColl - phase + threshold) / recip)
                        
                        posColl = phase + part.floor()
                        r = r.addToCollection(posColl.convertToBasis(64))
                        negColl = colDist - negColl
                        
                        part = (
                          recip * (negColl - phase + threshold) / recip)
                        
                        negColl = -(phase + part.floor())
                        r = r.addToCollection(negColl.convertToBasis(64))
        
        if coerceToNumber:
            r2 = r.toNumber()
            
            if r2 is not None:
                r = r2
        
        return r
    
    def _round26Dot6(self, n):
        return int(self._round(n / 64.0) * 64)
    
    def _synthRefHistory(self, index):
        """
        Utility function which determines if the reference point history for
        the specified index is None. If it is not, that value is returned; if
        it is, a HistoryEntry of the appropriate kind is created and returned.
        """
        
        state = self.state
        
        if state.refPtHistory[index] is not None:
            return state.refPtHistory[index]
        
        return HE_refPt(
          hintsObj=(id(self.ultParent), self.ultParent),
          hintsPC=state.pc + self.ultDelta,
          refPtDefault=index)
    
    def _synthStorageHistory(self, index):
        """
        Utility function which determines if the storage history for the
        specified index exists. If it does, its value is returned; if it does
        not, a HistoryEntry of the appropriate kind is created and returned.
        
        >>> h = _testingState()
        >>> h._synthStorageHistory(Collection([Triple(1, 9, 2)])).pprint()
        Implicit zero for storage location 1 used at opcode index 0 in test
        Implicit zero for storage location 3 used at opcode index 0 in test
        Implicit zero for storage location 5 used at opcode index 0 in test
        Implicit zero for storage location 7 used at opcode index 0 in test
        """
        
        state = self.state
        sH = state.storageHistory
        
        def gen():
            for i in toCollection(index):
                if i in sH:
                    yield sH[i]
                else:
                    yield HE_storage(
                      hintsObj = (id(self.ultParent), self.ultParent),
                      hintsPC=state.pc + self.ultDelta,
                      storageDefault=i)
        
        return HG(gen())
    
    def _toNumber(self, obj, doCheck=True, **kwArgs):
        """
        If obj is not a Collection, this method simply returns it. If it is a
        Collection and it has exactly one element, this method returns that
        element. Otherwise, this method returns None.
        
        If doCheck is True, the value has to be greater than or equal to the
        specified checkLow value (default 1).
        
        >>> logger = utilities.makeDoctestLogger("_toNumber_test")
        >>> h = _testingState()
        >>> h._toNumber(12, logger=logger)
        12
        
        >>> h._toNumber(toCollection(15), logger=logger)
        15
        
        >>> h._toNumber(toCollection([3, 4]), logger=logger)
        _toNumber_test - ERROR - In test (PC 0) a Collection value was used, but is not supported in fontio.
        
        >>> h._toNumber(0, doCheck=True)
        _toNumber_test - ERROR - In test (PC 0) the value 0 is too low.
        """
        
        if hasattr(obj, 'toNumber'):
            if len(obj) != 1:
                self._getLogger(**kwArgs).error((
                  'V0511',
                  (self.ultParent.infoString, self.state.pc + self.ultDelta),
                  "In %s (PC %d) a Collection value was used, but is not "
                  "supported in fontio."))
                
                self.state._validationFailed = True
                r = None
            
            else:
                r = next(iter(obj))
        
        else:
            r = obj
        
        if doCheck and (r is not None) and (r < kwArgs.get('checkLow', 1)):
            self._getLogger(**kwArgs).error((
              'V0513',
              (self.ultParent.infoString, self.state.pc + self.ultDelta, r),
              "In %s (PC %d) the value %d is too low."))
            
            self.state._validationFailed = True
            r = None
        
        return r
    
    def _zoneCheck(self, opString, whichToCheck, logger):
        gs = self.state.graphicsState
        
        t = (
          self._toNumber(gs.zonePointer0, doCheck=False),
          self._toNumber(gs.zonePointer1, doCheck=False),
          self._toNumber(gs.zonePointer2, doCheck=False))
        
        okToProceed = (None not in t)
        
        if okToProceed and any(t[i] not in {0, 1} for i in whichToCheck):
            
            logger.error((
              'E6031',
              (opString,
               self.ultParent.infoString,
               self.state.pc + self.ultDelta),
              "%s opcode in %s (PC %d) refers to a zone "
              "that is neither zero nor one."))
            
            self.state._validationFailed = True
            okToProceed = False
        
        if okToProceed and self.state._inPreProgram:
            if any(t[i] for i in whichToCheck):
                
                logger.error((
                  'E6040',
                  (opString, self.state.pc + self.ultDelta),
                  "%s opcode in the pre-program (PC %d) uses the glyph "
                  "zone. The pre-program may only use the twilight zone."))
                
                self.state._validationFailed = True
                okToProceed = False
        
        return okToProceed
    
    #
    # Public methods
    #
    
    def asImmutable(self):
        return tuple(obj.asImmutable() for obj in self)
    
    def binaryString(self, **kwArgs):
        """
        Returns the binary string for this sequence. There is one optional
        keyword argument:
        
            indexToByteOffset       If present, should be an empty list. On
                                    return the list will have the starting byte
                                    offsets of each hint.
        
        >>> o1 = opcode_tt.Opcode_push([1, 2, 3])
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> h = Hints([o1, o2])
        >>> v = []
        >>> [x for x in h.binaryString(indexToByteOffset=v)]
        [178, 1, 2, 3, 80]
        >>> print(v)
        [0, 4]
        """
        
        w = writer.LinkedWriter()
        itbo = kwArgs.get('indexToByteOffset', None)
        
        if itbo is None:
            for opcode in self:
                w.addString(opcode.binaryString())
        
        else:
            for opcode in self:
                itbo.append(int(w.byteLength))
                w.addString(opcode.binaryString())
        
        return w.binaryString()
    
    def buildBinary(self, w, **kwArgs):
        w.addString(self.binaryString(**kwArgs))
    
    def containsJumps(self):
        """
        Returns True if any opcode contained in self is a jump, either
        conditional or unconditional.
        
        >>> o1 = opcode_tt.Opcode_push([4])
        >>> o2 = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["ROFF"])
        >>> Hints([o1, o2]).containsJumps()
        False
        >>> o3 = opcode_tt.Opcode_nonpush(common.nameToOpcodeMap["JMPR"])
        >>> Hints([o1, o3]).containsJumps()
        True
        """
        
        return any(
          (not op.isPush()) and (op.opcode in _jumpOpcodes)
          for op in self)
    
    def gatheredMaxContext(self, **kwArgs): return 0
    
    def getIndexToByteOffsetMap(self):
        """
        Returns a list of starting byte offsets in the resulting binary string.
        
        >>> o1 = opcode_tt.Opcode_push([1, 2, 3])
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> h = Hints([o1, o2])
        >>> print(h.getIndexToByteOffsetMap())
        [0, 4]
        """
        
        v = []
        self.binaryString(indexToByteOffset=v)  # ignore the return result
        return v
    
    def getNamer(self): return None
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        return self.__copy__()
    
    def isSyntheticMergeFDEF(self):
        """
        Returns True if the Hints object starts with a PUSH -21555; POP
        sequence. This sequence is used by the hint merging code to identify
        synthesized FDEFs.
        
        >>> o1 = opcode_tt.Opcode_push([synthFDEFIdentifier])
        >>> o1_not = opcode_tt.Opcode_push([-1024])
        >>> o2 = opcode_tt.Opcode_nonpush(nameToOpcodeMap["POP"])
        >>> Hints([o1, o2]).isSyntheticMergeFDEF()
        True
        >>> Hints([o1_not, o2]).isSyntheticMergeFDEF()
        False
        >>> Hints([]).isSyntheticMergeFDEF()
        False
        >>> Hints([o1]).isSyntheticMergeFDEF()
        False
        """
        
        stack = []
        i = 0
        opPOP = nameToOpcodeMap["POP"]
        
        while i < len(self):
            opObj = self[i]
            
            if opObj.isPush():
                stack.extend(opObj.data)
            else:
                break
            
            i += 1
        
        if 0 < i < len(self):
            if stack:
                if stack[-1] == synthFDEFIdentifier:
                    if self[i].opcode == opPOP:
                        return True
        
        return False
    
    def mutableHash(self):
        """
        Like __hash__ but for mutable objects (the lack of __hash__ prevents
        objects of this class from being used as dict keys, since they are
        still actually mutable).
        
        >>> o1 = opcode_tt.Opcode_push(list(range(70)))
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> obj1 = Hints([o1, o2])
        >>> obj2 = Hints([o1, o2])
        >>> obj1 is obj2, obj1 == obj2
        (False, True)
        >>> obj1.mutableHash() == obj2.mutableHash()
        True
        """
        
        return hash(tuple(obj.asImmutable() for obj in self))
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object to the specified stream.
        
        >>> o1 = opcode_tt.Opcode_push(list(range(70)))
        >>> o2 = opcode_tt.Opcode_nonpush(0x50)
        >>> Hints([o1, o2]).pprint(maxWidth=60)
        0000 (0x000000): PUSH
                           [0] 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
                           [16] 16 17 18 19 20 21 22 23 24 25 26 27
                           [28] 28 29 30 31 32 33 34 35 36 37 38 39
                           [40] 40 41 42 43 44 45 46 47 48 49 50 51
                           [52] 52 53 54 55 56 57 58 59 60 61 62 63
                           [64] 64 65 66 67 68 69
        0001 (0x000048): LT
        """
        
        p = pp.PP(**kwArgs)
        cumulOffset = 0
        currIndentSpaces = ""
        
        for i, opcode in enumerate(self):
            label = "%04d (0x%06X): " % (i, cumulOffset)
            
            if opcode.isPush():
                p(''.join([label, currIndentSpaces, "PUSH"]))
                extra = p.indent + p.indentDelta + 17 + len(currIndentSpaces)
                p2 = pp.PP(indent=extra, stream=p.stream, maxWidth=p.maxWidth)
                p2.sequence_tag_long(opcode.data)
            
            else:
                op = opcode.opcode
                
                if op in _preIndenters:
                    currIndentSpaces = currIndentSpaces[p.indentDelta:]
                
                p(''.join([label, currIndentSpaces, opcodeToNameMap[op]]))
                
                if op in _postIndenters:
                    currIndentSpaces += " " * p.indentDelta
            
            cumulOffset += opcode.getOriginalLength()
    
    def recalculated(self, **kwArgs):
        return self.__deepcopy__()
    
    def resolveToParent(self):
        """
        If this Hints-class object was created from another one (for
        instance, if it is an "ELSE" group), then this method walks back along
        the "createdFrom" references adding offsets, until it determines the
        ultimate parent. This method then returns a pair (ultimateParent,
        pcDelta). If this object is already an ultimate parent (as indicated by
        the "createdFrom" attribute being (None, 0)), then (self, 0) is
        returned.
        
        >>> h1 = Hints(list(range(100)))
        >>> h2 = Hints(h1[20:], createdFrom=(h1, 20))
        >>> h3 = Hints(h2[10:], createdFrom=(h2, 10))
        >>> h1.resolveToParent()[1]
        0
        >>> rtp2 = h2.resolveToParent()
        >>> id(rtp2[0]) == id(h1), rtp2[1]
        (True, 20)
        >>> rtp3 = h3.resolveToParent()
        >>> id(rtp3[0]) == id(h1), rtp3[1]
        (True, 30)
        """
        
        retVal = (self, 0)
        
        while retVal[0].createdFrom[0] is not None:
            thisCF = retVal[0].createdFrom
            retVal = (thisCF[0], retVal[1] + thisCF[1])
        
        return retVal
    
    def run(self, inState, **kwArgs):
        """
        Runs the hints for the given state.
        """
        
        if __debug__:
            if kwArgs.get('debugEntryTrace_run', False):
                f = kwArgs.get('debugEntryTrace_stream', sys.stdout)
                print(self.infoString, inState.pc, file=f)
        
        self.state = inState
        
#         # To get around a snarl of logic involving getOriginalLength() on
#         # undefined hints (as part of a watermark), we put special logic here
#         # that looks for an initial push, JMPR and pre-advances the PC past the
#         # whole thing before starting to run the hints.
#         
#         if (
#           (len(self) > 2) and
#           (self[self.state.pc].isPush()) and
#           (len(self[self.state.pc].data) == 1) and
#           (not self[self.state.pc+1].isPush()) and
#           (self[self.state.pc+1].opcode == 0x1C)):
#           
#             import pdb; pdb.set_trace()
#             origLen = self[self.state.pc].originalLength
#             self.state.pc += origLen + self[self.state.pc].data[0]
        
        while self.state.pc < len(self):
            self.step(self.state, **kwArgs)
        
        if __debug__:
            d = kwArgs.get('debugDumpDict', None)
            
            if d is not None:
                self._debugDump(d, final=True)
        
        inState._validationFailed = self.state._validationFailed
    
    def setNamer(self, namer):
        pass
    
    def step(self, state, **kwArgs):
        """
        Runs a single hint (at the current pc) for the given state.
        """
        
        self.state = state
        stack = state.stack
        
        assert \
          len(stack) == len(state.pushHistory), \
          "History stack out of sync!"
        
        thisOpcode = self[state.pc]
        
        if __debug__:
            if kwArgs.get('debugEntryTrace_step', False):
                f = kwArgs.get('debugEntryTrace_stream', sys.stdout)
                print(self.infoString, state.pc, file=f)
                #print("  ", self.ultParent.infoString, state.pc + self.ultDelta)
            
            t = kwArgs.get('breakAt', None)
            
            if t is not None:
                if self.infoString == t[0] and state.pc == t[1]:
                    import pdb
                    pdb.set_trace()
            
            t = kwArgs.get('breakAtCVTChange', None)
            
            if t is not None:
                if state.cvt[t[0]] != t[1]:
                    import pdb
                    pdb.set_trace()
            
            d = kwArgs.get('debugDumpDict', None)
            
            if d is not None:
                self._debugDump(d)
            
            t = kwArgs.get('copyGSAt', None)
            
            if t is not None:
                if self.infoString == t[0] and state.pc == t[1]:
                    t[2].append(state.graphicsState.__deepcopy__())
        
        if thisOpcode.isPush():
            stack.extend(thisOpcode.data)
            
            for i in range(len(thisOpcode.data)):
                he = HE_push(
                  hintsObj = (id(self.ultParent), self.ultParent),
                  hintsPC = state.pc + self.ultDelta,
                  extraIndex = i)
                
                state.pushHistory.append(he)
            
            fatObj = kwArgs.get('fdefArgTracer', None)
    
            if fatObj is not None:
                fatObj.notePush(count=len(thisOpcode.data))
            
            state.statistics.stackCheck(stack)
            state.pc += 1
            return
        
        f = self._hintDispatchTable.get(thisOpcode.opcode, None)
        
        if f is not None:
            
            # The following requires some explanation. Some of the entries in
            # the hintDispatchTable are unbound methods, and some are the
            # results of calls to functools.partial. A problem arises for cases
            # like S45ROUND. This essentially is just a call to SROUND with a
            # pre-bound keyword argument 'is45Case' set to True. This works in
            # most cases, but if there happens to be an argument 'is45Case' in
            # kwArgs, it will override the setting we want. This is usually the
            # right thing to do, but for special control elements like this one
            # we need instead to force it to pay attention to the value that
            # was bound in the partial() call. The logic below does this.
            
            if hasattr(f, 'keywords'):
                filt = {
                  k: v
                  for k, v in kwArgs.items()
                  if k not in getattr(f, 'keywords', {})}
            
                f(self, **filt)
            
            else:
                f(self, **kwArgs)
            
            return
        
        if 'logger' in kwArgs:
            kwArgs['logger'].error((
              'V0804',
              (thisOpcode.opcode,
               self.ultParent.infoString,
               self.state.pc + self.ultDelta),
              "An unknown TrueType opcode 0x%02X was encountered in "
              "%s (PC %d)."))
            
            self.state._validationFailed = True
            self.state.pc = len(self) + 1
            return
        
        raise UnknownOpcode()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _popSync(state):
        state.changed('pushHistory')
        state.changed('stack')
        del state.pushHistory[-1]
        return state.stack.pop()
    
    def _testingState(*args):
        from fontio3.hints import ttstate
        t = ttstate.TrueTypeState()
        
        for i in range(20):
            t.cvt[i] = toCollection(280 + ((i + 3) * i), 64)
        
        t.changed('cvt')
        t._numPoints = {0: 14, 1: 45}
        t._numContours = {0: 0, 1: 6}
        t._inPreProgram = False
        t._editor = {'fpgm': {}}
        t.stack.extend(args)
        
        if args:
            t.changed('stack')
        
        h = Hints(infoString="test")
        h.state = t
        v = [HE_push((id(h), h), 0, i) for i in range(len(args))]
        t.pushHistory.extend(v)
        t.statistics.stackCheck(t.stack)
        return h

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

