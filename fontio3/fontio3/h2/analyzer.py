#
# analyzer.py
#
# Copyright © 2015, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analyzing a stream of TrueType hints to determine what kinds of
values are used. This code can be used to analyze a 'fpgm' table, for example,
if the font doesn't have a 'MTfn' table present (or if one needs to be
reconstructed).
"""

# System imports
import collections
import difflib
import functools
import math
import operator

# Other imports
from fontio3 import utilities
from fontio3.h2 import analyzer_stack, analyzer_stack_entry, common, hints_tt

# -----------------------------------------------------------------------------

#
# Exceptions
#

class FDEFAnalysisFailure(ValueError): pass

# -----------------------------------------------------------------------------

#
# Constants
#

# The following is to get around a computed CALL. Grrrr.....

_fdef17_orig = bytes.fromhex(
  "20 69 B0 40 61 B0 00 8B "
  "20 B1 2C C0 8A 8C B8 10 "
  "00 62 60 2B 0C 64 23 64 "
  "61 5C 58 B0 03 61 59")

_fdef17_rewrite = bytes.fromhex(
  "20 69 20 B0 01 51 58 B0 "
  "2C 1B 20 B0 02 54 58 B0 "
  "2D 1B 20 B0 03 54 58 B0 "
  "2E 1B B0 2F 59 59 59 2B "
  "0C 64 23 64 61 5C 58 B0 "
  "03 61 59")

_fdef44_bad = bytes.fromhex(
  "20 B0 03 25 45 50 58 8A "
  "20 45 8A 8B 44 21 1B 21 "
  "45 44 59")

_fdef44_good = bytes.fromhex(
  "21 21 0C 64 23 64 8B B8 "
  "40 00 62")

# _fdef49_orig = utilities.fromhex(
#   "4B 53 58 20 B0 03 25 49 "
#   "64 69 20 B0 05 26 B0 06 "
#   "25 49 64 23 61 B0 80 62 "
#   "B0 20 61 6A B0 0E 23 44 "
#   "B0 04 26 10 B0 0E F6 8A "
#   "10 B0 0E 23 44 B0 0E F6 "
#   "B0 0E 23 44 B0 0E ED 1B "
#   "8A B0 04 26 11 12 20 39 "
#   "23 20 39 2F 2F 59")
# 
# _fdef49_rewrite = bytes([1])  # SVTCA[x] by default

# -----------------------------------------------------------------------------

#
# Functions
#

def _mergeAnalysis(dFrom, dTo, logger):
    dWork = collections.defaultdict(dict)
    
    for t, obj in dFrom.items():
        dWork[t[0]][t[1]] = obj
    
    bigBreak = False
    
    for fdefIndex, dSub in dWork.items():
        if len(dSub) == 1:
            dTo[fdefIndex] = dSub[0]
            continue
        
        # Now gather together all the sub-pieces and do two things: make sure
        # there are no contradictions, and gather everything together for
        # inclusion in dTo. We do this separately for the input piece and the
        # output piece.
        
        allOps = {t[3] for t in dSub.values() if t[3]}
        
        if len(allOps) > 1:
            raise ValueError("Inconsistent op sets!")
        elif len(allOps) == 1:
            ops = allOps.pop()
        else:
            ops = ()
        
        inCountSet = {t[1] for t in dSub.values()}
        inDeepestSet = {t[2] for t in dSub.values()}
        outCountSet = {t[5] for t in dSub.values()}
        assert len(inCountSet) < 2
        assert len(outCountSet) < 2
        inCount = (inCountSet.pop() if inCountSet else 0)
        inDeepest = (max(inDeepestSet) if inDeepestSet else 0)
        outCount = (outCountSet.pop() if outCountSet else 0)
        inParts = [t[0] for t in dSub.values()]
        outParts = [t[4] for t in dSub.values()]
        v = []
        
        for parts, count in ((inParts, inCount), (outParts, outCount)):
            dCumul = {}
            
            for part in parts:
                for stackIndex, t in part:
                    if stackIndex in dCumul:
                        if t[0] != dCumul[stackIndex][0]:
                            logger.error((
                              'Vxxxx',
                              (fdefIndex, stackIndex),
                              "In FDEF %d, stack index %d is being "
                              "interpreted in different ways in different "
                              "fictons."))
                            
                            bigBreak = True
                            break
                    
                    else:
                        dCumul[stackIndex] = t
                
                if bigBreak:
                    break
            
            v.append(tuple((i, dCumul[i]) for i in sorted(dCumul)))
            v.append(count)
            
            if bigBreak:
                break
        
        if bigBreak:
            bigBreak = False
            break
        
        v[2:2] = [inDeepest, ops]
        dTo[fdefIndex] = tuple(v)

def analyzeFPGM(fpgmObj, **kwArgs):
    """
    Returns a dict mapping FDEF index numbers to tuples (see below). This
    code takes care of the details of doing analysis of non-CALL guys
    first.
    
    Note that the Hints objects in the Fpgm object will not be h2 Hints,
    but are old hints_tt Hints; this code handles that.
    
    The returned value is either a dict (if the useDictForm kwArg is True), or
    a tuple (if it is False, the default, for historical reasons). The per-FPGM
    tuple has the following form:
    
        [0]     dIn             A tuple of kinds of input arguments. This
                                comprises a series of (stack index, kind)
                                pairs.
        
        [1]     inCount         The number of input arguments. Note that this
                                might not necessarily be the length of dIn!
        
        [2]     inDeepest       The deepest level of popping that is attained
                                by this FDEF. Because of intrinsic operations,
                                this might be considerably larger than either
                                len(dIn) or inCount.
        
        [3]     ops             Some operations (like MINDEX) can leave the
                                stack in a state that can't be emulated by a
                                simple series of pops and pushes. In this case
                                this value, ops, will be a tuple of commands
                                needed to adjust the stack after the hint
                                executes. For instance, a sample value of ops
                                might be (('delete', -3, -2),), meaning the
                                [-3:-2] slice should be deleted in order to
                                bring the stack into agreement with how the
                                hint would have left things.
        
        [4]     dOut            A tuple of kinds of output arguments. As with
                                dIn, this comprises a series of (stack index,
                                kind) pairs.
        
        [5]     outCount        The number of output arguments. As with inCount
                                this might be different than len(dOut)!
    """
    
    if 'logger' in kwArgs:
        logger = kwArgs.pop('logger')
    else:
        logger = utilities.makeDoctestLogger("analyzeFPGM", level=50)
    
    fb = hints_tt.Hints.frombytes
    f2 = {}
    
    for n, h in fpgmObj.items():
        bsOld = h.binaryString()
    
        if bsOld == _fdef17_orig:
            bsOld = _fdef17_rewrite
            
            logger.info((
              'Vxxxx',
              (),
              "Rewrote FDEF 17 to remove computed CALL"))
        
        elif bsOld == _fdef44_bad:
            bsOld = _fdef44_good
            
            logger.info((
              'Vxxxx',
              (),
              "Corrected erroneous FDEF 44"))
        
        f2[n] = fb(bsOld, infoString=h.infoString)
    
    rTemp = {}
    r = {}
    
    # do a separate first pass for non-CALLers; then loop...
    
    thisRound = set()
    badSet = {0x1C, 0x2A, 0x2B, 0x78, 0x79}
    
    for n, h in f2.items():
        if all(op.isPush or (op not in badSet) for op in h):
            thisRound.add(n)
    
    if not thisRound:
        logger.error((
          'Vxxxx',
          (),
          "All FDEFs call other FDEFs"))
        
        return None
    
    hadInconsistencies = False
    
    for n in sorted(thisRound):
        fictons = f2[n].removeIFs()
        
        logger.info((
          'Vxxxx',
          (n, len(fictons)),
          "FDEF %d disassembles into %d ficton(s)"))
        
        consistencySet = set()
        
        for i, h in enumerate(fictons):
            obj = Analyzer(h)
            t = obj.run()
            consistencySet.add((t[1], t[5]))
            rTemp[(n, i)] = t
        
        if len(consistencySet) > 1:
            logger.error((
              'V1071',
              (n, sorted(consistencySet),),
              "Different fictons for FDEF %d yield different numbers of "
              "inputs and outputs: %s"))
            
            hadInconsistencies = True
        
        del f2[n]
    
    if hadInconsistencies:
        return None
    
    _mergeAnalysis(rTemp, r, logger)
    
    # Now that we have the stack implications for the FDEFs without CALLs, go
    # through and use this as the callInfo to finish off the rest of the FDEFs.
    
    badSet.discard(0x2A)
    badSet.discard(0x2B)
    
    while f2:
        # A call to run() will return None if unknown CALLs are there.
        thisRound = set()
        
        for n, h in f2.items():
            if all(op.isPush or (op not in badSet) for op in h):
                thisRound.add(n)
        
        if not thisRound:
            logger.error((
              'Vxxxx',
              (),
              "All remaining FDEFs call other FDEFs that "
              "themselves call other FDEFs"))
        
            return None
        
        notYets = set()
        rTemp = {}
        hadInconsistencies = False
        
        for n in sorted(thisRound):
            fictons = f2[n].removeIFs()
            
            logger.info((
              'Vxxxx',
              (n, len(fictons)),
              "FDEF %d disassembles into %d ficton(s)"))
            
            consistencySet = set()
            
            for i, h in enumerate(fictons):
                obj = Analyzer(h)
                runOut = obj.run(callInfo=r)
                
                if runOut is None:
                    notYets.add(n)
                    
                    for k in list(rTemp):
                        if k[0] == n:
                            del rTemp[k]
                    
                    break
                
                consistencySet.add((runOut[1], runOut[5]))
                rTemp[(n, i)] = runOut
            
            if len(consistencySet) > 1:
                logger.error((
                  'V1071',
                  (n, sorted(consistencySet),),
                  "Different fictons for FDEF %d yield different numbers of "
                  "inputs and outputs: %s"))
                
                hadInconsistencies = True
        
        if hadInconsistencies:
            return None
        
        thisRound -= notYets
        _mergeAnalysis(rTemp, r, logger)
        
        for n in thisRound:
            del f2[n]
    
    if kwArgs.get('useDictForm', False):
        d = {}
        
        for fdefIndex, t in r.items():
            inTuple, inCount, inDeepest, ops, outTuple, outCount = t
        
            if inCount:
                dIn = dict.fromkeys(range(inCount))
            
                for i, t in inTuple:
                    dIn[i] = t
        
            else:
                dIn = {}
        
            if outCount:
                dOut = dict.fromkeys(range(outCount))
            
                for i, t in inTuple:
                    dOut[i] = t
        
            else:
                dOut = {}
        
            d[fdefIndex] = (dIn, inCount, inDeepest, ops, dOut, outCount)
        
        r = d
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Analyzer(object):
    """
    Analyzer objects are used to analyze what kinds of values are used in a
    given hint stream (represented by a Hints object).
    """
    
    #
    # Methods
    #
    
    def __init__(self, hintObj, **kwArgs):
        """
        Initializes the Analyzer object, preparing it for analysis of the
        specified Hints object (note this is an h2.hints_tt.Hints object, and
        not an older fontio3.hints_tt.Hints object).
        
        The following keyword arguments are supported:
        
            callInfo        A dict which should be the result of a call to
                            analyzeFPGM with the useDictForm flag set True.
                            See the docstring for that function for more
                            details on the exact for of this dict.
            
            stampInfo       A dict mapping stamps to (kind, history) pairs.
        """
        
        self.loop = kwArgs.pop('loop', 1)
        
        if self.loop != 1:
            raise ValueError("Non-unity import loop values not supported!")
        
        self.callInfo = kwArgs.pop('callInfo', {})
        self.hints = hintObj
        self.stampInfo = kwArgs.pop('stampInfo', {})  # stamp -> (kind, hist)
        self.stack = analyzer_stack.AnalyzerStack(stampInfo=self.stampInfo)
        self._hintDispatch = hintDispatchTable
        self.unhandledCALL = False
    
    def _hint_bad(self, **kwArgs):
        """
        This is called when an unknown TT hint is encountered. It raises a
        ValueError.
        """
        
        s = common.rawOpcodeToNameMap[kwArgs['op']]
        raise ValueError("Should not have hint %s!" % (s,))
    
    def _hint_CALL(self, **kwArgs):
        """
        Modify the stack to simulate making the CALL without actually calling
        anything. This uses self.callInfo to make all the needed changes to the
        stack.
        """
        
        callInfo = kwArgs['callInfo']
        fdefIndexEntry = self.stack.pop()
        
        if fdefIndexEntry.inOut == 'in':
            self.inDeepest = max(self.inDeepest, fdefIndexEntry.relStackIndex + 1)
        
        fdefIndex = fdefIndexEntry.value
        
        if fdefIndex is None:
            raise ValueError("Computed CALL index!")
        
        if fdefIndex not in callInfo:
            self.unhandledCALL = True
            return
        
        inTuple, inCount, inDeepest, ops, outTuple, outCount = callInfo[fdefIndex]
        
        if ops:
            for action, start, stop in ops:
                if action == 'delete':
                    del self.stack[start:stop]
                
                else:
                    pass  # may have to do something here later...
        
        else:
            dTemp = {i: t[0] for i, t in inTuple}
            
            for i in range(inCount):
                obj = self.stack.pop()
                
                if i in dTemp:
                    kind = dTemp[i]
                    
                    if (obj.kind is not None) and (obj.kind != kind):
                        if isinstance(obj.kind, frozenset):
                            kind = frozenset(obj.kind | {kind})
                        else:
                            kind = frozenset({obj.kind, kind})
                    
                    self.stampInfo[obj.itemStamp] = (kind, obj.wherePushed)
        
        if outTuple:
            ASE = analyzer_stack_entry.AnalyzerStackEntry
            assert outCount == len(outTuple)
            
            for i, t in utilities.enumerateBackwards(outTuple):
                assert i == t[0]
                kind, hist = t[1]
                outStamp = self.stack.stamperObj.stamp()
                self.stampInfo[outStamp] = (kind, hist)
                self.stack.append(ASE(0, 'out', outStamp, None, kind, hist))
    
    def _hint_CLEAR(self, **kwArgs):
        while self.stack:
            ignore = self.stack.pop()
    
    def _hint_cmindex_sub(self, **kwArgs):
        n = kwArgs['relStackIndex']
        
        if n == 'stack':
            obj = self.stack.pop()
            self.stampInfo[obj.itemStamp] = ('relStackIndex', obj.wherePushed)
            
            if obj.value is None:
                raise ValueError("Computed cmindex!")
            
            n = obj.value
        
        moveObj = self.stack[-n]
        
        if moveObj.inOut == 'in':
            enfCount = moveObj.relStackIndex + 1
        else:
            enfCount = 0
        
        if kwArgs['deleteOld']:
            del self.stack[-n]
        
        self.stack.append(moveObj)
        self.inDeepest = max(self.inDeepest, enfCount)
    
    def _hint_DEPTH(self, **kwArgs):
        ASE = analyzer_stack_entry.AnalyzerStackEntry
        outStamp = self.stack.stamperObj.stamp()
        hist = (self.hints.infoString, self.pc, None)
        self.stampInfo[outStamp] = (None, hist)
        n = len(self.stack)
        self.stack.append(ASE(n, 'out', outStamp, None, None, hist))
    
    def _hint_generic_dyadic(self, **kwArgs):
        func = kwArgs.get('func', None)
        doPPEMCheck = kwArgs.get('doPPEMCheck', False)
        obj1 = self.stack.pop()
        
        if obj1.inOut == 'in':
            self.inDeepest = max(self.inDeepest, obj1.relStackIndex + 1)
        
        obj2 = self.stack.pop()
        
        if obj2.inOut == 'in':
            self.inDeepest = max(self.inDeepest, obj2.relStackIndex + 1)
        
        ASE = analyzer_stack_entry.AnalyzerStackEntry
        
        if 'forceKind' in kwArgs:
            if doPPEMCheck:
                if (obj1.kind is None) and (obj2.kind == 'ppem'):
                    if obj1.itemStamp in self.stampInfo:
                        oldEntry = self.stampInfo[obj1.itemStamp]
                        self.stampInfo[obj1.itemStamp] = ('ppem', oldEntry[1])
                    
                    else:
                        self.stampInfo[obj1.itemStamp] = ('ppem', None)
                
                elif (obj2.kind is None) and (obj1.kind == 'ppem'):
                    if obj2.itemStamp in self.stampInfo:
                        oldEntry = self.stampInfo[obj2.itemStamp]
                        self.stampInfo[obj2.itemStamp] = ('ppem', oldEntry[1])
                    
                    else:
                        self.stampInfo[obj1.itemStamp] = ('ppem', None)
            
            newKind = kwArgs['forceKind']
        
        elif obj1.kind is None:
            if doPPEMCheck and (obj2.kind == 'ppem'):
                if obj1.itemStamp in self.stampInfo:
                    oldEntry = self.stampInfo[obj1.itemStamp]
                    self.stampInfo[obj1.itemStamp] = ('ppem', oldEntry[1])
                
                else:
                    self.stampInfo[obj1.itemStamp] = ('ppem', None)
            
            newKind = obj2.kind
        
        elif obj2.kind is None:
            if doPPEMCheck and (obj1.kind == 'ppem'):
                if obj2.itemStamp in self.stampInfo:
                    oldEntry = self.stampInfo[obj2.itemStamp]
                    self.stampInfo[obj2.itemStamp] = ('ppem', oldEntry[1])
                
                else:
                    self.stampInfo[obj2.itemStamp] = ('ppem', None)
            
            newKind = obj1.kind
        
        else:
            if obj1.kind != obj2.kind:
                raise ValueError("Kind mismatch!")
            
            newKind = obj1.kind
        
        if 'forceValue' in kwArgs:
            newValue = kwArgs['forceValue']
        elif (obj1.value is not None) and (obj2.value is not None):
            newValue = func(obj2.value, obj1.value)
        else:
            newValue = None
        
        outStamp = self.stack.stamperObj.stamp()
        hist = (self.hints.infoString, self.pc, None)
        self.stampInfo[outStamp] = (newKind, hist)
        self.stack.append(ASE(newValue, 'out', outStamp, None, newKind, hist))
    
    def _hint_generic_monadic(self, **kwArgs):
        func = kwArgs.get('func', None)
        obj = self.stack.pop()
        
        if obj.inOut == 'in':
            self.inDeepest = max(self.inDeepest, obj.relStackIndex + 1)
        
        ASE = analyzer_stack_entry.AnalyzerStackEntry
        newKind = kwArgs.get('forceKind', obj.kind)
        
        if 'forceValue' in kwArgs:
            newValue = kwArgs['forceValue']
        else:
            newValue = (None if obj.value is None else func(obj.value))
        
        outStamp = self.stack.stamperObj.stamp()
        hist = (self.hints.infoString, self.pc, None)
        self.stampInfo[outStamp] = (newKind, hist)
        self.stack.append(ASE(newValue, 'out', outStamp, None, newKind, hist))
    
    def _hint_LOOPCALL(self, **kwArgs):
        callInfo = kwArgs['callInfo']
        fdefIndex = self.stack[-1].value
        inArgs, inCount, inDeepest, ops, outArgs, outCount = callInfo[fdefIndex]
        
        if inCount == outCount and (not ops):
            self._hint_CALL(**kwArgs)
        else:
            raise ValueError("LOOPCALL with uneven stack effects!")
    
    def _hint_NOP(self, **kwArgs):
        return
    
    def _hint_poppush(self, **kwArgs):
        kindsIn = kwArgs.get('kindsIn', [])
        kindsOut = kwArgs.get('kindsOut', [])
        i = 0
        
        while i < len(kindsIn):
            if kindsIn[i] == 'loop':
                v = [kindsIn[i+1]] * self.loop
                i += 2
            
            elif kindsIn[i] == 'count':
                count = self.stack.pop().value
                
                if count is None:
                    raise ValueError("Computed count!")
                
                arg = kindsIn[i + 1]
                
                if isinstance(arg, list):
                    v = arg * count
                else:
                    v = [arg] * count
                
                i += 2
            
            else:
                v = [kindsIn[i]]
                i += 1
        
            for kind in v:
                obj = self.stack.pop()
                
                if obj.inOut == 'in':
                    self.inDeepest = max(self.inDeepest, obj.relStackIndex + 1)
            
                if kind is None:
                    continue
            
                if (obj.kind is not None) and (obj.kind != kind):
                    if isinstance(obj.kind, frozenset):
                        kind = frozenset(obj.kind | {kind})
                    else:
                        kind = frozenset({obj.kind, kind})
                    #raise ValueError("Inconsistent kinds!")
            
                self.stampInfo[obj.itemStamp] = (kind, obj.wherePushed)
        
        if kindsOut:
            ASE = analyzer_stack_entry.AnalyzerStackEntry
            
            for kind in kindsOut:
                outStamp = self.stack.stamperObj.stamp()
                hist = (self.hints.infoString, self.pc, None)
                self.stampInfo[outStamp] = (kind, hist)
                self.stack.append(ASE(0, 'out', outStamp, None, kind, hist))
    
    def _hint_SLOOP(self, **kwArgs):
        obj = self.stack.pop()
        
        if obj.inOut == 'in':
            self.inDeepest = max(self.inDeepest, obj.relStackIndex + 1)
        
        if obj.value is None:
            raise ValueError("Computed loop!")
        
        self.loop = obj.value
    
    def run(self, **kwArgs):
        """
        >>> h = _makeTestHints(0)
        >>> h.pprint()
        Generic hints
        0000 (0x000000): RCVT[]
        0001 (0x000001): SWAP[]
        0002 (0x000002): GC[N]
        0003 (0x000003): ADD[]
        0004 (0x000004): DUP[]
        0005 (0x000005): PUSH
                           [38]
        0006 (0x000007): ADD[]
        0007 (0x000008): PUSH
                           [4]
        0008 (0x00000A): MINDEX[]
        0009 (0x00000B): SWAP[]
        0010 (0x00000C): SCFS[]
        0011 (0x00000D): SCFS[]
        
        >>> obj = Analyzer(h)
        >>> inArgs, inCount, inDeepest, ops, outArgs, outCount = obj.run()
        >>> print(inCount, inDeepest, ops, outCount)
        4 4 () 0
        >>> for x in inArgs:
        ...     print(x)
        (0, ('cvtIndex', None))
        (1, ('pointIndex', None))
        (2, ('pointIndex', None))
        (3, ('pointIndex', None))
        
        >>> outArgs
        ()
        
        >>> h = _makeTestHints(1)
        >>> h.pprint()
        Generic hints
        0000 (0x000000): RCVT[]
        0001 (0x000001): PUSH
                           [19]
        0002 (0x000003): ADD[]
        
        >>> obj = Analyzer(h)
        >>> inArgs, inCount, inDeepest, ops, outArgs, outCount = obj.run()
        >>> print(inCount, inDeepest, ops, outCount)
        1 1 () 1
        >>> for x in inArgs:
        ...     print(x)
        (0, ('cvtIndex', None))
        
        >>> for x in outArgs:
        ...     print(x)
        (0, ('pixels', ('Generic hints', 2, None)))
        
        >>> h = _makeTestHints(2)
        >>> h.pprint()
        Generic hints
        0000 (0x000000): ROLL[]
        0001 (0x000001): POP[]
        
        >>> obj = Analyzer(h)
        >>> inArgs, inCount, inDeepest, ops, outArgs, outCount = obj.run()
        >>> print(inCount, inDeepest, ops, outCount)
        0 3 (('delete', -3, -2),) 0
        
        >>> h = _makeTestHints(3)
        >>> h.pprint()
        Generic hints
        0000 (0x000000): PUSH
                           [3]
        0001 (0x000002): CINDEX[]
        0002 (0x000003): POP[]
        
        >>> obj = Analyzer(h)
        >>> inArgs, inCount, inDeepest, ops, outArgs, outCount = obj.run()
        >>> print(inCount, inDeepest, ops, outCount)
        0 3 () 0
        """
        
        self.pc = 0
        it = enumerate(reversed(self.stack))
        stampToInitialDepth = {x.relStackIndex: i for i, x in it}
        self.inDeepest = 0
        
        while self.pc < len(self.hints):
            self.step(**kwArgs)
            
            if self.unhandledCALL:
                
                # If the CALL wasn't handled we let the client know this by
                # returning None. This is a signal that the code should skip
                # over this FDEF, for instance, deferring to a later pass.
                
                self.unhandledCALL = False
                return None
        
        countWalker = -1
        outCount = 0
        
        while self.stack[countWalker].inOut == 'out':
            outCount += 1
            countWalker -= 1
        
        if countWalker == -1:
            v = [obj.relStackIndex for obj in self.stack]
        else:
            v = [obj.relStackIndex for obj in self.stack[:countWalker+1]]
        
        inCount = v[-1]
        testRange = list(range(v[0], v[-1] - 1, -1))
        opcodes = []
        
        if v != testRange:
            # non-monotonic range detected
            v.extend(['x'] * outCount)
            testRange.extend(['x'] * outCount)
            rawOps = difflib.SequenceMatcher(a=testRange, b=v).get_opcodes()
            
            for obj in rawOps:
                if obj[0] == 'equal':
                    continue
                
                if obj[0] == 'delete':
                    opcodes.append((
                      'delete',
                      obj[1] - len(testRange),
                      obj[2] - len(testRange)))
                
                else:
                    raise ValueError("Unsupported stack change!")
        
        v = [
          (stampToInitialDepth[s], t)
          for s, t in self.stampInfo.items()
          if s in stampToInitialDepth
          if t != (None, None)
          ]
        
        inArgs = sorted(v, key=operator.itemgetter(0))
        outArgs = []
        
        for i, x in enumerate(reversed(self.stack)):
            if x.inOut != 'out':
                break
            
            outArgs.append((i, (x.kind, x.wherePushed)))
        
        return (
          tuple(inArgs),
          inCount,
          self.inDeepest,
          tuple(opcodes),
          tuple(outArgs),
          outCount)
    
    def step(self, **kwArgs):
        obj = self.hints[self.pc]
        callInfo = kwArgs.pop('callInfo', self.callInfo)
        
        if obj.isPush:
            for i, n in enumerate(obj):
                stmp = self.stack.stamperObj.stamp()
                hist = (self.hints.infoString, self.pc, i)
                
                newEntry = analyzer_stack_entry.AnalyzerStackEntry(
                  value = n,
                  inOut = 'out',
                  itemStamp = stmp,
                  relStackIndex = None,
                  kind = None,
                  wherePushed = hist)
                
                self.stampInfo[stmp] = (None, hist)
                self.stack.append(newEntry)
        
        else:
            f = self._hintDispatch[obj]
            f(self, op=obj, callInfo=callInfo, **kwArgs)
            self.stack.fillTo20()
            
            if obj != 0x17:
                self.loop = 1
        
        self.pc += 1  # this is always true now, since no IFs or JMPs

# -----------------------------------------------------------------------------

#
# Dispatch tables
#

f = functools.partial
gm = Analyzer._hint_generic_monadic
gd = Analyzer._hint_generic_dyadic
hpp = Analyzer._hint_poppush
cm = Analyzer._hint_cmindex_sub

hintDispatchTable = {
  0x06: f(hpp, kindsIn=['pointIndex'] * 2),
  0x07: f(hpp, kindsIn=['pointIndex'] * 2),
  0x08: f(hpp, kindsIn=['pointIndex'] * 2),
  0x09: f(hpp, kindsIn=['pointIndex'] * 2),
  0x0A: f(hpp, kindsIn=[None, None]),
  0x0B: f(hpp, kindsIn=[None, None]),
  0x0C: f(hpp, kindsOut=['2dot14'] * 2),
  0x0D: f(hpp, kindsOut=['2dot14'] * 2),
  0x0F: f(hpp, kindsIn=['pointIndex'] * 5),
  0x10: f(hpp, kindsIn=['pointIndex']),
  0x11: f(hpp, kindsIn=['pointIndex']),
  0x12: f(hpp, kindsIn=['pointIndex']),
  0x13: f(hpp, kindsIn=['zoneIndex']),
  0x14: f(hpp, kindsIn=['zoneIndex']),
  0x15: f(hpp, kindsIn=['zoneIndex']),
  0x16: f(hpp, kindsIn=['zoneIndex']),
  0x17: Analyzer._hint_SLOOP,
  0x1A: f(hpp, kindsIn=['pixels']),
  0x1B: Analyzer._hint_bad,
  0x1C: Analyzer._hint_bad,
  0x1D: f(hpp, kindsIn=['pixels']),
  0x1E: f(hpp, kindsIn=['pixels']),
  0x1F: f(hpp, kindsIn=['FUnits']),
  0x20: f(cm, relStackIndex=1, deleteOld=False),
  0x21: f(hpp, kindsIn=[None]),
  0x22: Analyzer._hint_CLEAR,
  0x23: f(cm, relStackIndex=2, deleteOld=True),
  0x24: Analyzer._hint_DEPTH,
  0x25: f(cm, relStackIndex='stack', deleteOld=False),
  0x26: f(cm, relStackIndex='stack', deleteOld=True),
  0x27: f(hpp, kindsIn=['pointIndex'] * 2),
  0x28: Analyzer._hint_bad,
  0x29: f(hpp, kindsIn=['pointIndex']),
  0x2A: Analyzer._hint_LOOPCALL,
  0x2B: Analyzer._hint_CALL,
  0x2C: Analyzer._hint_bad,
  0x2D: Analyzer._hint_bad,
  0x2E: f(hpp, kindsIn=['pointIndex']),
  0x2F: f(hpp, kindsIn=['pointIndex']),
  0x32: f(hpp, kindsIn=['loop', 'pointIndex']),
  0x33: f(hpp, kindsIn=['loop', 'pointIndex']),
  0x34: f(hpp, kindsIn=['contourIndex']),
  0x35: f(hpp, kindsIn=['contourIndex']),
  0x36: f(hpp, kindsIn=['zoneIndex']),
  0x37: f(hpp, kindsIn=['zoneIndex']),
  0x38: f(hpp, kindsIn=['pixels', 'loop', 'pointIndex']),
  0x39: f(hpp, kindsIn=['loop', 'pointIndex']),
  0x3A: f(hpp, kindsIn=['pixels', 'pointIndex']),
  0x3B: f(hpp, kindsIn=['pixels', 'pointIndex']),
  0x3C: f(hpp, kindsIn=['loop', 'pointIndex']),
  0x3E: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0x3F: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0x42: f(hpp, kindsIn=[None, 'storageIndex']),
  0x43: f(hpp, kindsIn=['storageIndex'], kindsOut=[None]),
  0x44: f(hpp, kindsIn=['pixels', 'cvtIndex']),
  0x45: f(hpp, kindsIn=['cvtIndex'], kindsOut=['pixels']),
  0x46: f(hpp, kindsIn=['pointIndex'], kindsOut=['pixels']),
  0x47: f(hpp, kindsIn=['pointIndex'], kindsOut=['pixels']),
  0x48: f(hpp, kindsIn=['pixels', 'pointIndex']),
  0x49: f(hpp, kindsIn=['pointIndex'] * 2, kindsOut=['pixels']),
  0x4A: f(hpp, kindsIn=['pointIndex'] * 2, kindsOut=['pixels']),
  0x4B: f(hpp, kindsOut=['ppem']),
  0x4C: f(hpp, kindsOut=['pointsize']),
  0x4F: f(hpp, kindsIn=['debugIndex']),
  0x50: f(gd, func=operator.lt, forceKind='boolean', doPPEMCheck=True),
  0x51: f(gd, func=operator.le, forceKind='boolean', doPPEMCheck=True),
  0x52: f(gd, func=operator.gt, forceKind='boolean', doPPEMCheck=True),
  0x53: f(gd, func=operator.ge, forceKind='boolean', doPPEMCheck=True),
  0x54: f(gd, func=operator.eq, forceKind='boolean', doPPEMCheck=True),
  0x55: f(gd, func=operator.ne, forceKind='boolean', doPPEMCheck=True),
  0x56: f(hpp, kindsIn=['pixels'], kindsOut=['boolean']),
  0x57: f(hpp, kindsIn=['pixels'], kindsOut=['boolean']),
  0x58: Analyzer._hint_bad,
  0x59: Analyzer._hint_bad,
  0x5A: f(gd, func=operator.and_, forceKind='boolean'),
  0x5B: f(gd, func=operator.or_, forceKind='boolean'),
  0x5C: f(gm, func=operator.not_, forceKind='boolean'),
  0x5D: f(hpp, kindsIn=['count', ['pointIndex', 'deltaSpec']]),
  0x5E: f(hpp, kindsIn=[None]),
  0x5F: f(hpp, kindsIn=[None]),
  0x60: f(gd, func=operator.add),
  0x61: f(gd, func=operator.sub),
  0x62: f(gd, forceValue=64),
  0x63: f(gd, forceValue=64),
  0x64: f(gm, func=operator.abs),
  0x65: f(gm, func=operator.neg),
  0x66: f(gm, func=(lambda x: 64 * int(math.floor(x / 64.0)))),
  0x67: f(gm, func=(lambda x: 64 * int(math.ceil(x / 64.0)))),
  0x68: f(gm, func=(lambda x: x)),
  0x69: f(gm, func=(lambda x: x)),
  0x6A: f(gm, func=(lambda x: x)),
  0x6B: Analyzer._hint_bad,
  0x6C: f(gm, func=(lambda x: x)),
  0x6D: f(gm, func=(lambda x: x)),
  0x6E: f(gm, func=(lambda x: x)),
  0x6F: Analyzer._hint_bad,
  0x70: f(hpp, kindsIn=['FUnits', 'cvtIndex']),
  0x71: f(hpp, kindsIn=['count', ['pointIndex', 'deltaSpec']]),
  0x72: f(hpp, kindsIn=['count', ['pointIndex', 'deltaSpec']]),
  0x73: f(hpp, kindsIn=['count', ['cvtIndex', 'deltaSpec']]),
  0x74: f(hpp, kindsIn=['count', ['cvtIndex', 'deltaSpec']]),
  0x75: f(hpp, kindsIn=['count', ['cvtIndex', 'deltaSpec']]),
  0x76: f(hpp, kindsIn=[None]),
  0x77: f(hpp, kindsIn=[None]),
  0x78: Analyzer._hint_bad,
  0x79: Analyzer._hint_bad,
  0x73: Analyzer._hint_bad,
  0x7F: Analyzer._hint_bad,  # AA not supported here (yet)
  0x80: f(hpp, kindsIn=['loop', 'pointIndex']),
  0x81: f(hpp, kindsIn=['pointIndex'] * 2),
  0x82: f(hpp, kindsIn=['pointIndex'] * 2),
  0x85: f(hpp, kindsIn=[None]),
  0x86: f(hpp, kindsIn=['pointIndex'] * 2),
  0x87: f(hpp, kindsIn=['pointIndex'] * 2),
  0x88: f(hpp, kindsIn=[None], kindsOut=[None]),
  0x89: Analyzer._hint_bad,
  0x8A: f(cm, relStackIndex=3, deleteOld=True),
  0x8B: f(gd, func=max),
  0x8C: f(gd, func=min),
  0x8D: f(hpp, kindsIn=[None]),
  0x8E: f(hpp, kindsIn=[None] * 2),
  0x8F: Analyzer._hint_bad,
  0x90: Analyzer._hint_bad,
  0xA2: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xA3: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xA4: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xA5: f(hpp, kindsIn=[None, 'ppem', 'ppem']),
  0xA6: f(hpp, kindsIn=['pointIndex', 'ppem', 'ppem']),
  0xA7: f(hpp, kindsIn=['count', 'pointIndex', 'count', 'deltaSpec']),
  0xA8: f(hpp, kindsIn=['count', 'pointIndex', 'count', 'deltaSpec']),
  0xA9: f(hpp, kindsIn=['count', 'pointIndex', 'count', 'deltaSpec']),
  0xAA: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xAB: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xAC: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xAD: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xAE: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xAF: f(hpp, kindsIn=['pointIndex', 'count', 'deltaSpec']),
  0xC0: f(hpp, kindsIn=['pointIndex']),
  0xC1: f(hpp, kindsIn=['pointIndex']),
  0xC2: f(hpp, kindsIn=['pointIndex']),
  0xC3: Analyzer._hint_bad,
  0xC4: f(hpp, kindsIn=['pointIndex']),
  0xC5: f(hpp, kindsIn=['pointIndex']),
  0xC6: f(hpp, kindsIn=['pointIndex']),
  0xC7: Analyzer._hint_bad,
  0xC8: f(hpp, kindsIn=['pointIndex']),
  0xC9: f(hpp, kindsIn=['pointIndex']),
  0xCA: f(hpp, kindsIn=['pointIndex']),
  0xCB: Analyzer._hint_bad,
  0xCC: f(hpp, kindsIn=['pointIndex']),
  0xCD: f(hpp, kindsIn=['pointIndex']),
  0xCE: f(hpp, kindsIn=['pointIndex']),
  0xCF: Analyzer._hint_bad,
  0xD0: f(hpp, kindsIn=['pointIndex']),
  0xD1: f(hpp, kindsIn=['pointIndex']),
  0xD2: f(hpp, kindsIn=['pointIndex']),
  0xD3: Analyzer._hint_bad,
  0xD4: f(hpp, kindsIn=['pointIndex']),
  0xD5: f(hpp, kindsIn=['pointIndex']),
  0xD6: f(hpp, kindsIn=['pointIndex']),
  0xD7: Analyzer._hint_bad,
  0xD8: f(hpp, kindsIn=['pointIndex']),
  0xD9: f(hpp, kindsIn=['pointIndex']),
  0xDA: f(hpp, kindsIn=['pointIndex']),
  0xDB: Analyzer._hint_bad,
  0xDC: f(hpp, kindsIn=['pointIndex']),
  0xDD: f(hpp, kindsIn=['pointIndex']),
  0xDE: f(hpp, kindsIn=['pointIndex']),
  0xDF: Analyzer._hint_bad,
  0xE0: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE1: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE2: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE3: Analyzer._hint_bad,
  0xE4: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE5: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE6: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE7: Analyzer._hint_bad,
  0xE8: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xE9: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xEA: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xEB: Analyzer._hint_bad,
  0xEC: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xED: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xEE: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xEF: Analyzer._hint_bad,
  0xF0: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF1: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF2: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF3: Analyzer._hint_bad,
  0xF4: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF5: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF6: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF7: Analyzer._hint_bad,
  0xF8: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xF9: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xFA: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xFB: Analyzer._hint_bad,
  0xFC: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xFD: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xFE: f(hpp, kindsIn=['cvtIndex', 'pointIndex']),
  0xFF: Analyzer._hint_bad}

del cm, hpp, gd, gm, f

hintDispatchTable.update({
  i: Analyzer._hint_NOP
  for i in range(256)
  if i not in hintDispatchTable})

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeTestHints(which):
        from fontio3.utilities import fromhex as fh
        from fontio3.h2 import hints_tt
        
        if which == 0:
            bs = fh("45 23 46 60 20 B0 26 60 B0 04 26 23 48 48")
        elif which == 1:
            bs = fh("45 B0 13 60")
        elif which == 2:
            bs = fh("8A 21")
        elif which == 3:
            bs = fh("B0 03 25 21")
        
        return hints_tt.Hints.frombytes(bs)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

