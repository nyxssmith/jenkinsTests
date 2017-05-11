#
# opcodewithargs_tt.py
#
# Copyright © 2005-2009, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes relating to single TrueType opcodes with associated arguments. These
are very similar to opcode_tt.OpcodeNew objects, but with additional
information about the specific stack arguments the opcode uses.
"""

# System imports
import collections
import functools
import itertools

# Other imports
from fontio3 import utilities
from fontio3.hints import hints_tt, common
from fontio3.utilities import pp, span, writer

# -----------------------------------------------------------------------------

#
# Constants
#

AAOpcode = 0x7F
deltaKBands = {0xA7: 0, 0xA8: 16, 0xA9: 32}
deltaLSMBands = {0xAA: 0, 0xAB: 16, 0xAC: 32, 0xAD: 0, 0xAE: 16, 0xAF: 32, 0xA2: 0, 0xA3: 16, 0xA4: 32}
deltaPBands = {0x5D: 0, 0x71: 16, 0x72: 32}
deltaShifts = dict(list(zip(list(range(16)), list(range(-8, 0)) + list(range(1, 9)))))
loopOpcodes = frozenset([0x32, 0x33, 0x38, 0x39, 0x3C, 0x80])
mazModeStroke = frozenset([0xA5, 0xA6])
nameToOpcodeMap = common.nameToOpcodeMap
opcodeToNameMap = common.opcodeToNameMap
pushOpcodes = frozenset(list(range(0x40, 0x42)) + list(range(0xB0, 0xC0)))
roundOpcodes = frozenset([0x18, 0x19, 0x3D, 0x7A, 0x7C, 0x7D])
setterAny = frozenset(list(range(0x0C)) + [0x0E])
setterPVOnly = frozenset([0x02, 0x03, 0x06, 0x07, 0x0A])
setterFVOnly = frozenset([0x00, 0x01, 0x04, 0x05, 0x08, 0x09, 0x0B, 0x0E])
SHZOpcodes = frozenset(list(range(0x36, 0x38)))

# -----------------------------------------------------------------------------

#
# Private functions
#

def _sanityCheck(v):
    """
    Walks v, which is a list of OpcodeWithArgs_nonpush objects, and creates and
    returns a new list which has silly parts removed (e.g. adjacent SVTCA
    opcodes).
    
    >>> op1 = OpcodeWithArgs_nonpush(nameToOpcodeMap["SVTCA[y]"])
    >>> op2 = OpcodeWithArgs_nonpush(nameToOpcodeMap["SPVTCA[y]"])
    >>> op3 = OpcodeWithArgs_nonpush(nameToOpcodeMap["SFVTCA[y]"])
    >>> op4 = OpcodeWithArgs_nonpush(nameToOpcodeMap["SFVTPV"])
    >>> op5 = OpcodeWithArgs_nonpush(nameToOpcodeMap["RUTG"])
    >>> op6 = OpcodeWithArgs_nonpush(nameToOpcodeMap["RDTG"])
    >>> _sanityCheck([op1, op1])
    [SVTCA[y]]
    >>> _sanityCheck([op5, op6])
    [RDTG]
    >>> _sanityCheck([op2, op4, op3])
    [SPVTCA[y], SFVTPV]
    >>> _sanityCheck([op1, op2])
    [SVTCA[y]]
    """
    
    r = list(v)
    toDel = set()
    currentRoundOpcode = nameToOpcodeMap["RTG"]
    pv = fv = 'x'
    m = nameToOpcodeMap
    
    for i, opObj in enumerate(r):
        op = opObj.opcode
        
        if op in roundOpcodes:
            if op == currentRoundOpcode:
                toDel.add(i)
            elif i and r[i - 1].opcode in roundOpcodes:
                toDel.add(i - 1)
            
            currentRoundOpcode = op
        
        elif op == m["SVTCA[y]"]:
            if pv == 'y' and fv == 'y':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterAny:
                        toDel.add(j)
                    else:
                        break
            
            pv = fv = 'y'
        
        elif op == m["SVTCA[x]"]:
            if pv == 'x' and fv == 'x':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterAny:
                        toDel.add(j)
                    else:
                        break
            
            pv = fv = 'x'
        
        elif op == m["SPVTCA[y]"]:
            if pv == 'y':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterPVOnly:
                        toDel.add(j)
                    else:
                        break
            
            pv = 'y'
        
        elif op == m["SPVTCA[x]"]:
            if pv == 'x':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterPVOnly:
                        toDel.add(j)
                    else:
                        break
            
            pv = 'x'
        
        elif op == m["SFVTCA[y]"]:
            if fv == 'y':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterFVOnly:
                        toDel.add(j)
                    else:
                        break
            
            fv = 'y'
        
        elif op == m["SFVTCA[x]"]:
            if fv == 'x':
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterFVOnly:
                        toDel.add(j)
                    else:
                        break
            
            fv = 'x'
        
        elif op in set([m["SPVTL[parallel]"], m["SPVTL[perpendicular]"], m["SPVFS"]]):
            pv = 'other'
            
            for j in range(i - 1, -1, -1):
                if r[j].opcode in setterPVOnly:
                    toDel.add(j)
                else:
                    break
        
        elif op in set([m["SFVTL[parallel]"], m["SFVTL[perpendicular]"], m["SFVFS"]]):
            fv = 'other'
            
            for j in range(i - 1, -1, -1):
                if r[j].opcode in setterFVOnly:
                    toDel.add(j)
                else:
                    break
        
        elif op == m["SFVTPV"]:
            if fv == pv:
                toDel.add(i)
            else:
                for j in range(i - 1, -1, -1):
                    if r[j].opcode in setterFVOnly:
                        toDel.add(j)
                    else:
                        break
            
            fv = pv
    
    for i in reversed(sorted(toDel)):
        del r[i]
    
    return r

# -----------------------------------------------------------------------------

#
# Functions
#

def bestPUSHString(inputList):
    """
    Return a binary string representing the best compression for the specified
    list.
    
    >>> [c for c in bestPUSHString([12])]
    [176, 12]
    >>> [c for c in bestPUSHString([512, 513])]
    [185, 2, 0, 2, 1]
    >>> [c for c in bestPUSHString([12, 512, 513, 13])]
    [176, 12, 185, 2, 0, 2, 1, 176, 13]
    """
    
    w = writer.LinkedWriter()
    
    for useWordForm, g in itertools.groupby(inputList, lambda x: x < 0 or x > 255):
        fullList = list(g)
        
        while fullList:
            v = fullList[:255]
            useNForm = len(v) > 8
            
            if useWordForm:
                data = ([0x41, len(v)] if useNForm else [0xB7 + len(v)])
            else:
                data = ([0x40, len(v)] if useNForm else [0xAF + len(v)])
            
            w.addGroup("B", data)
            w.addGroup(("h" if useWordForm else "B"), v)
            fullList = fullList[255:]
    
    return w.binaryString()

def OpcodeWithArgs_factory(opcode, args):
    """
    Returns either an OpcodeWithArgs_push object or an OpcodeWithArgs_nonpush
    object, depending on the specified opcode.
    
    >>> OpcodeWithArgs_factory(0x01, [])
    SVTCA[x]
    >>> OpcodeWithArgs_factory(0x41, [1, 2, 3])
    Push [1, 2, 3]
    """
    
    if opcode in pushOpcodes:
        r = OpcodeWithArgs_push(args)
    else:
        r = OpcodeWithArgs_nonpush(opcode, args)
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class OpcodeWithArgs_nonpush(object):
    """
    Objects representing a single TrueType opcode (excluding the PUSH opcodes),
    along with associated data if used by the opcode.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, opcode, iterable=None):
        """
        Initializes the object with the specified opcode and optional popped
        data.
        
        >>> opa = OpcodeWithArgs_nonpush(0x01)
        >>> opa.opcode, opa.data
        (1, [])
        >>> opa = OpcodeWithArgs_nonpush(0x5D, [204, 6, 204, 7, 2])
        >>> opa.opcode, opa.data
        (93, [204, 6, 204, 7, 2])
        >>> opa = OpcodeWithArgs_nonpush(0x41, [1, 2, 3, 6])
        Traceback (most recent call last):
          ...
        AssertionError: Push opcode provided to OpcodeWithArgs_nonpush!
        >>> OpcodeWithArgs_nonpush(400)
        Traceback (most recent call last):
          ...
        AssertionError: Opcode must fit in a byte!
        """
        
        assert 0 <= opcode < 256, "Opcode must fit in a byte!"
        assert opcode not in pushOpcodes, "Push opcode provided to OpcodeWithArgs_nonpush!"
        self.opcode = opcode
        self.data = ([] if iterable is None else list(iterable))
    
    #
    # Special methods
    #
    
    def __copy__(self):
        r = OpcodeWithArgs_nonpush(self.opcode)
        r.data = self.data
        return r
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy of self.
        
        >>> o = OpcodeWithArgs_nonpush(0x5D, [204, 6, 204, 7, 2])
        >>> c = o.__deepcopy__()
        >>> o.opcode == c.opcode, o.data == c.data
        (True, True)
        >>> o is c, o.data is c.data
        (False, False)
        """
        
        return OpcodeWithArgs_nonpush(self.opcode, iter(self.data))
    
    def __eq__(self, other):
        try:
            return self.opcode == other.opcode and self.data == other.data
        except:
            return False
    
    def __ne__(self, other): return not (self == other)
    
    def __repr__(self):
        """
        Returns a nice string representation of the object.
        
        >>> OpcodeWithArgs_nonpush(0x01)
        SVTCA[x]
        >>> OpcodeWithArgs_nonpush(0x5D, [204, 6, 204, 7, 2])
        DELTAP1 [204, 6, 204, 7, 2]
        """
        
        if self.data:
            return "%s %s" % (opcodeToNameMap[self.opcode], str(self.data))
        
        return opcodeToNameMap[self.opcode]
    
    #
    # Public methods
    #
    
    def binaryString(self, **kwArgs):
        """
        Returns the binary string. In the simplest case, this is a one-byte
        string containing the opcode. If it pops some fixed number of
        arguments, it contains first a PUSH for those arguments and then the
        opcode. If it pops a variable number of arguments (based on loop), it
        pushes the arguments, the count, and then includes a SLOOP before the
        specified opcode.
        
        >>> [c for c in OpcodeWithArgs_nonpush(0x01).binaryString()]
        [1]
        >>> [c for c in OpcodeWithArgs_nonpush(0x5D, [204, 6, 204, 7, 2]).binaryString()]
        [180, 204, 6, 204, 7, 2, 93]
        >>> [c for c in OpcodeWithArgs_nonpush(0x3C, [30, 31, 33, 39]).binaryString()]
        [180, 30, 31, 33, 39, 4, 23, 60]
        >>> [c for c in OpcodeWithArgs_nonpush(0x38, [7, 8, 9, 128]).binaryString()]
        [180, 7, 8, 9, 128, 3, 23, 56]
        """
        
        w = writer.LinkedWriter()
        
        if self.data:
            isLoop = self.opcode in loopOpcodes
            
            v = list(self.data)
            
            if isLoop:
                v.append(len(v) - (self.opcode == 0x38))  # SHPIX adjust if needed
            
            maxStack = kwArgs.get('maxStack', [0])
            maxStack[0] = max(maxStack[0], len(v))
            w.addString(bestPUSHString(v))
            
            if isLoop:
                w.add("B", nameToOpcodeMap["SLOOP"])
        
        w.add("B", self.opcode)
        return w.binaryString()
    
    deepcopy = __deepcopy__
    
    def isPush(self): return False

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class OpcodeWithArgs_push(object):
    """
    Objects representing a single TrueType push opcode, along with associated
    pushed data.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable):
        """
        Initializes the object with the specified opcode and data.
        
        >>> opa = OpcodeWithArgs_push([1, 2, 3, 6])
        >>> opa.data
        [1, 2, 3, 6]
        """
        
        self.data = list(iterable)
    
    #
    # Special methods
    #
    
    def __copy__(self):
        """
        Returns a shallow copy of self.
        
        >>> o = OpcodeWithArgs_push([1, 2, 3, 6])
        >>> c = o.__copy__()
        >>> o is c, o.data == c.data, o.data is c.data
        (False, True, True)
        """
        
        r = OpcodeWithArgs_push([])
        r.data = self.data
        return r
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy of self.
        
        >>> o = OpcodeWithArgs_push([1, 2, 3, 6])
        >>> c = o.__deepcopy__()
        >>> o is c, o.data == c.data, o.data is c.data
        (False, True, False)
        """
        
        return OpcodeWithArgs_push(self.data)
    
    def __eq__(self, other):
        try:
            return self.data == other.data
        except:
            return False
    
    def __ne__(self, other): return not (self == other)
    
    def __repr__(self):
        """
        Returns a nice string representation of the object.
        
        >>> OpcodeWithArgs_push([1, 2, 3, 6])
        Push [1, 2, 3, 6]
        """
        
        return "Push %s" % (str(self.data),)
    
    #
    # Public methods
    #
    
    def binaryString(self, **kwArgs):
        """
        Returns the binary string.
        
        >>> [c for c in OpcodeWithArgs_push([1, 2, 3, 6]).binaryString()]
        [179, 1, 2, 3, 6]
        """
        
        v = kwArgs.get('maxStack', [0])
        v[0] = max(v[0], len(self.data))
        return bestPUSHString(self.data)
    
    deepcopy = __deepcopy__
    
    def isPush(self): return True

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class HintsWithArgs(object):
    """
    These are sequences of OpcodeWithArgs_push and OpcodeWithArgs_nonpush
    objects with associated caches.
    
    >>> HintsWithArgs.frombytes(bytes([0xB8, 0xAB, 0xCD, 0x21])).pprint()
    000: POP [-21555]
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable=None, **kwArgs):
        """
        Initializes the list with objects taken from the specified iterable.
        While HintsWithArgs objects are lists of OpcodeWithArgs objects, the
        specified iterable should return simple Opcode_push or Opcode_nonpush
        objects. They will be analyzed and the OpcodeWithArgs_push and
        OpcodeWithArgs_nonpush objects synthesized using the results of that
        analysis.
        
        One keyword argument is currently supported:
        
            callInfo    If specified, should be a dict mapping FDEF values to
                        single integers representing how many values are popped
                        by that FDEF. Note that FDEFs that push values onto the
                        stack are not supported by HintsWithArgs objects.
        
        >>> _testingState_CALL().pprint()
        000: CALL [0, 74]
        001: CALL [0, 69]
        002: AA [1]
        
        >>> _testingState_ADD().pprint()
        000: MIRP[setRP0, respectMinimumDistance, roundDistance, black] [8, 51]
        """
        
        self.callInfo = kwArgs.get('callInfo', {})
        self.hints = []
        
        if iterable is not None:
            self._stack = []
            self._loop = 1
            
            for opObj in iterable:
                if opObj.isPush():
                    self._stack.extend(opObj.data)
                
                elif opObj.opcode == 0x17:  # SLOOP handled separately
                    self._loop = self._stack.pop()
                
                elif opObj.opcode == 0x60:
                    # Since we are careful to not include any opcodes that push
                    # results onto the stack, it's safe to do addition inline
                    # like this. This is important for supporting fonts that
                    # have been run through TTMerge, since the CVT and storage
                    # index tweaking code uses single-push ADDs.
                    self._stack[-2:] = [self._stack[-1] + self._stack[-2]]
                
                else:
                    self._opObj = opObj
                    self._dispatch[opObj.opcode](self)
        
        self._makeCaches()
        
        for toDel in ('_stack', '_loop', '_opObj'):
            if hasattr(self, toDel):
                delattr(self, toDel)
    
    #
    # Class methods
    #
    
    @classmethod
    def frombytes(cls, s, **kwArgs):
        return cls(hints_tt.Hints.frombytes(s), **kwArgs)
    
    #
    # Special methods
    #
    
    def __deepcopy__(self, memo=None):
        """
        Returns a deep copy of self
        
        >>> h = _testingState()
        >>> h2 = h.__deepcopy__()
        >>> h == h2
        True
        >>> h is h2
        False
        """
        
        return HintsWithArgs.frombytes(self.binaryString())
    
    def __delitem__(self, key):
        """
        Deletes the specified index or indices from the object. This adjusts
        both the hints list and also the internal caches, to make sure
        everything stays totally in sync.
        
        >>> h = _testingState()
        >>> del h[3:]
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAP1 [224, 9, 240, 9, 2]
        >>> del h[0]
        >>> h.pprint()
        000: SVTCA[y]
        001: DELTAP1 [224, 9, 240, 9, 2]
        """
        
        del self.hints[key]
        self._makeCaches()  # have to redo them, because deleted hints could affect things
    
    def __eq__(self, other): return self.hints == other.hints
    
    def __getitem__(self, key):
        """
        Returns a new HintsWithArgs object containing the specified item or
        slice.
        
        >>> h = _testingState()
        >>> h[1].pprint()
        000: SVTCA[y]
        >>> h[4:].pprint()
        000: SHZ[RP1] [1]
        001: DELTAS1 [53, 70, 2, 9]
        """
        
        newObj = HintsWithArgs()
        newObj.hints = (self.hints[key] if isinstance(key, slice) else [self.hints[key]])
        newObj._makeCaches()
        return newObj
    
    def __iter__(self):
        """
        Returns an iterator over OpcodeWithArgs objects contained here.
        
        >>> h = _testingState()
        >>> next(iter(h))
        AA [5]
        """
        
        return iter(self.hints)
    
    def __len__(self):
        """
        Returns the length of the hint stream.
        
        >>> len(_testingState())
        6
        """
        
        return len(self.hints)
    
    def __ne__(self, other): return self.hints != other.hints
    
    #
    # Private methods
    #
    
    def _badOpcode(self):
        """
        This is called if an opcode which can't be handled is encountered.
        """
        
        raise ValueError("Cannot work with %s!" % (repr(self._opObj),))
    
    def _do(self, count):
        v = self._stack[-count:]
        del self._stack[-count:]
        self.hints.append(OpcodeWithArgs_factory(self._opObj.opcode, v))
    
    def _findAllOpcodes(self, matchSet):
        """
        Returns an iterator over (index, obj) pairs for all elements of
        self.hints whose opcodes are in the specified matchSet.
        """
        
        for i, obj in enumerate(self.hints):
            if obj.opcode in matchSet:
                yield (i, obj)
    
    def _generic_NOP(self): pass
    
    def _handle_call(self):
        whichFDEF = self._stack[-1]
        
        if whichFDEF not in self.callInfo:
            raise ValueError("CALL with stack push effects not supported!")
        
        self._do(1 + self.callInfo[whichFDEF])
    
    def _handle_deltaCP(self): self._do(2 * self._stack[-1] + 1)
    def _handle_deltaK(self): self._do(self._stack[-1] + 2 + self._stack[-2-self._stack[-1]])
    def _handle_deltaLS(self): self._do(self._stack[-2] + 2)
    def _handle_popNone(self): self.hints.append(OpcodeWithArgs_nonpush(self._opObj.opcode))
    
    def _handle_popLoop(self, extra=0):
        count = self._loop + extra
        self._loop = 1
        self._do(count)
    
    def _makeCaches(self):
        """
        Constructs self._dirVecCache, which is a list of (proj, free) pairs,
        where proj and free are (1, 0), (-1, 0), (0, 1) or (0, -1). Any other
        value (such as might be set via SFVTL, for instance) will raise a
        ValueError.
        
        Also constructs self._refPtCache, which is a dict mapping reference
        point index to the actual value of the reference point referred to.
        """
        
        self._dirVecCache = []
        self._refPtCache = []
        self._deltaBaseCache = []
        self._deltaShiftCache = []
        self._freeProjInY = [False, False]
        self._refPts = {0: 0, 1: 0, 2: 0}
        self._currDeltaBase = 9
        self._currDeltaShift = 3
        
        for self._opObj in self.hints:
            self._dirVecCache.append(self._freeProjInY[0])
            self._refPtCache.append(self._refPts)
            self._deltaBaseCache.append(self._currDeltaBase)
            self._deltaShiftCache.append(self._currDeltaShift)
            self._dispatch_makeCaches[self._opObj.opcode](self)
        
        for toDel in ('_freeProjInY', '_refPts', '_opObj', '_currDeltaBase', '_currDeltaShift'):
            if hasattr(self, toDel):
                delattr(self, toDel)
    
    def _makeCaches_MxAP(self): self._refPts[0] = self._refPts[1] = self._opObj.data[0]
    
    def _makeCaches_MxRP(self, mask):
        p = self._opObj.data[0]
        d = self._refPts
        d[1] = d[0]
        d[2] = p
        
        if self._opObj.opcode & mask:
            d[0] = p
    
    def _makeCaches_SDB(self): self._currDeltaBase = self._opObj.data[0]
    def _makeCaches_SDS(self): self._currDeltaShift = self._opObj.data[0]
    def _makeCaches_SFVFS(self): self._freeProjInY[0] = self._opObj.data[-1] != 0
    def _makeCaches_SFVTCA(self): self._freeProjInY[0] = self._opObj.opcode == 0x04
    def _makeCaches_SFVTPV(self): self._freeProjInY[0] = self._freeProjInY[1]
    def _makeCaches_SPVFS(self): self._freeProjInY[1] = self._opObj.data[-1] != 0
    def _makeCaches_SPVTCA(self): self._freeProjInY[1] = self._opObj.opcode == 0x02
    
    def _makeCaches_SRP(self, which):
        self._refPts = self._refPts.copy()
        self._refPts[which] = self._opObj.data[0]
    
    def _makeCaches_SVTCA(self):
        newInY = self._opObj.opcode == 0x00
        self._freeProjInY[:] = [newInY, newInY]
    
    def _makeDirectionIterators(self, wantY):
        """
        Returns an iterator over iterators representing the contiguous
        direction groups within the hints. Each yielded iterator returns an
        (index, obj) pair.
        """
        
        startIndex = 0
        starts = []
        
        for groupIsInY, g in itertools.groupby(self._dirVecCache):
            thisLen = len(list(g))
            
            if groupIsInY == wantY:
                starts.append((startIndex, thisLen))
            
            startIndex += thisLen
        
        for startIndex, count in starts:
            yield self._makePieceIterator(startIndex, count)
    
    def _makePieceIterator(self, startIndex, count):
        """
        Returns a generator over (index, opcodeObj) pairs starting at the
        specified index and for the specified count.
        """
        
        while count:
            yield (startIndex, self.hints[startIndex])
            count -= 1
            startIndex += 1
    
    def _removeUnusedSRPs(self):
        """
        Any SRPs which used to be required for SHZs can be removed once the
        SHZs have been filtered by findAndRemoveWholeShifts().
        
        >>> h = _testingState()
        >>> h._removeUnusedSRPs()  # will not remove, because SHZ still refers to it
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAP1 [224, 9, 240, 9, 2]
        003: SRP1 [9]
        004: SHZ[RP1] [1]
        005: DELTAS1 [53, 70, 2, 9]
        """
        
        toDel = set()
        refPtsInUse = set()
        look = self._removeUnusedSRPs_lookup
        
        for index, obj in utilities.enumerateBackwards(self.hints):
            op = obj.opcode
            
            if 0x10 <= op < 0x13:  # the three SRPs
                refPt = op - 0x10
                
                if refPt not in refPtsInUse:
                    toDel.add(index)
                else:
                    refPtsInUse.discard(refPt)
            
            elif op in look:
                refPtsUsed, refPtsSet = look[op]
                refPtsInUse.update(refPtsUsed)
                refPtsInUse.difference_update(refPtsSet)
        
        if toDel:
            self.hints = [obj for i, obj in enumerate(self.hints) if i not in toDel]
            self._makeCaches()
    
    #
    # Dispatch tables and other method support data (includes some class constants)
    #
    
    m = nameToOpcodeMap
    _dispatch = collections.defaultdict(lambda: HintsWithArgs._badOpcode, [
      (nameToOpcodeMap["AA"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["ALIGNPTS"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["ALIGNRP"], _handle_popLoop),
      (nameToOpcodeMap["CALL"], _handle_call),
      (nameToOpcodeMap["DEBUG"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["DELTAC1"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAC2"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAC3"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAK1"], _handle_deltaK),
      (nameToOpcodeMap["DELTAK2"], _handle_deltaK),
      (nameToOpcodeMap["DELTAK3"], _handle_deltaK),
      (nameToOpcodeMap["DELTAL1"], _handle_deltaLS),
      (nameToOpcodeMap["DELTAL2"], _handle_deltaLS),
      (nameToOpcodeMap["DELTAL3"], _handle_deltaLS),
      (nameToOpcodeMap["DELTAP1"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAP2"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAP3"], _handle_deltaCP),
      (nameToOpcodeMap["DELTAS1"], _handle_deltaLS),
      (nameToOpcodeMap["DELTAS2"], _handle_deltaLS),
      (nameToOpcodeMap["DELTAS3"], _handle_deltaLS),
      (nameToOpcodeMap["FLIPOFF"], _handle_popNone),
      (nameToOpcodeMap["FLIPON"], _handle_popNone),
      (nameToOpcodeMap["FLIPPT"], _handle_popLoop),
      (nameToOpcodeMap["FLIPRGOFF"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["FLIPRGON"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["INSTCTRL"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["IP"], _handle_popLoop),
      (nameToOpcodeMap["ISECT"], functools.partial(_do, count=5)),
      (nameToOpcodeMap["IUP[x]"], _handle_popNone),
      (nameToOpcodeMap["IUP[y]"], _handle_popNone),
      (nameToOpcodeMap["MAZDELTA1"], _handle_deltaLS),
      (nameToOpcodeMap["MAZDELTA2"], _handle_deltaLS),
      (nameToOpcodeMap["MAZDELTA3"], _handle_deltaLS),
      (nameToOpcodeMap["MAZMODE"], functools.partial(_do, count=3)),
      (nameToOpcodeMap["MAZSTROKE"], functools.partial(_do, count=3)),
      (nameToOpcodeMap["MDAP[noRound]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["MDAP[round]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["MIAP[noRound]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["MIAP[round]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["MSIRP[noSetRP0]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["MSIRP[setRP0]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["POP"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["RDTG"], _handle_popNone),
      (nameToOpcodeMap["ROFF"], _handle_popNone),
      (nameToOpcodeMap["RTDG"], _handle_popNone),
      (nameToOpcodeMap["RTG"], _handle_popNone),
      (nameToOpcodeMap["RTHG"], _handle_popNone),
      (nameToOpcodeMap["RUTG"], _handle_popNone),
      (nameToOpcodeMap["S45ROUND"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SCANCTRL"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SCANTYPE"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SCFS"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SCVTCI"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SDB"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SDPVTL[parallel]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SDPVTL[perpendicular]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SDS"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SFVFS"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SFVTCA[x]"], _handle_popNone),
      (nameToOpcodeMap["SFVTCA[y]"], _handle_popNone),
      (nameToOpcodeMap["SFVTL[parallel]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SFVTL[perpendicular]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SFVTPV"], _handle_popNone),
      (nameToOpcodeMap["SHC[RP1]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SHC[RP2]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SHP[RP1]"], _handle_popLoop),
      (nameToOpcodeMap["SHP[RP2]"], _handle_popLoop),
      (nameToOpcodeMap["SHPIX"], functools.partial(_handle_popLoop, extra=1)),
      (nameToOpcodeMap["SHZ[RP1]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SHZ[RP2]"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SMD"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SPVFS"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SPVTCA[x]"], _handle_popNone),
      (nameToOpcodeMap["SPVTCA[y]"], _handle_popNone),
      (nameToOpcodeMap["SPVTL[parallel]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SPVTL[perpendicular]"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["SROUND"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SRP0"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SRP1"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SRP2"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SSW"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SSWCI"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SVTCA[x]"], _handle_popNone),
      (nameToOpcodeMap["SVTCA[y]"], _handle_popNone),
      (nameToOpcodeMap["SZP0"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SZP1"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SZP2"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["SZPS"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["UTP"], functools.partial(_do, count=1)),
      (nameToOpcodeMap["WCVTF"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["WCVTP"], functools.partial(_do, count=2)),
      (nameToOpcodeMap["WS"], functools.partial(_do, count=2))
      ])
    
    for opcode in range(0xC0, 0xE0):  # all the valid MDRPs
        if opcode % 4 != 3:
            _dispatch[opcode] = functools.partial(_do, count=1)
    
    for opcode in range(0xE0, 0x100):  # all the valid MIRPs
        if opcode % 4 != 3:
            _dispatch[opcode] = functools.partial(_do, count=2)
    
    _dispatch_makeCaches = collections.defaultdict(lambda: HintsWithArgs._generic_NOP, [
      (m["MDAP[noRound]"], _makeCaches_MxAP),
      (m["MDAP[round]"], _makeCaches_MxAP),
      (m["MIAP[noRound]"], _makeCaches_MxAP),
      (m["MIAP[round]"], _makeCaches_MxAP),
      (m["MSIRP[noSetRP0]"], functools.partial(_makeCaches_MxRP, mask=0x01)),
      (m["MSIRP[setRP0]"], functools.partial(_makeCaches_MxRP, mask=0x01)),
      (m["SDB"], _makeCaches_SDB),
      (m["SDS"], _makeCaches_SDS),
      (m["SFVFS"], _makeCaches_SFVFS),
      (m["SFVTCA[x]"], _makeCaches_SFVTCA),
      (m["SFVTCA[y]"], _makeCaches_SFVTCA),
      (m["SFVTPV"], _makeCaches_SFVTPV),
      (m["SPVFS"], _makeCaches_SPVFS),
      (m["SPVTCA[x]"], _makeCaches_SPVTCA),
      (m["SPVTCA[y]"], _makeCaches_SPVTCA),
      (m["SRP0"], functools.partial(_makeCaches_SRP, which=0)),
      (m["SRP1"], functools.partial(_makeCaches_SRP, which=1)),
      (m["SRP2"], functools.partial(_makeCaches_SRP, which=2)),
      (m["SVTCA[x]"], _makeCaches_SVTCA),
      (m["SVTCA[y]"], _makeCaches_SVTCA),
      ])
    
    for opcode in range(0xC0, 0x100):  # all the valid MDRPs and MIRPs
        if opcode % 4 != 3:
            _dispatch_makeCaches[opcode] = functools.partial(_makeCaches_MxRP, mask=0x10)
      
    del opcode
    
    _removeUnusedSRPs_lookup = {  # values are (refPtsUsed, refPtsSet)
      m["ALIGNRP"]: (frozenset([0]), frozenset([])),
      m["IP"]: (frozenset([1, 2]), frozenset([])),
      m["MDAP[noRound]"]: (frozenset([]), frozenset([0, 1])),
      m["MDAP[round]"]: (frozenset([]), frozenset([0, 1])),
      m["MIAP[noRound]"]: (frozenset([]), frozenset([0, 1])),
      m["MIAP[round]"]: (frozenset([]), frozenset([0, 1])),
      m["MSIRP[noSetRP0]"]: (frozenset([0]), frozenset([])),
      m["MSIRP[setRP0]"]: (frozenset([0]), frozenset([0])),
      m["SHC[RP1]"]: (frozenset([1]), frozenset([])),
      m["SHC[RP2]"]: (frozenset([2]), frozenset([])),
      m["SHP[RP1]"]: (frozenset([1]), frozenset([])),
      m["SHP[RP2]"]: (frozenset([2]), frozenset([])),
      m["SHZ[RP1]"]: (frozenset([1]), frozenset([])),
      m["SHZ[RP2]"]: (frozenset([2]), frozenset([]))}
    
    for op in range(0xC0, 0x100):  # all MDRPs and MIRPs
        if op % 4 != 3:
            refPtsSet = (frozenset([0, 1, 2]) if op & 0x10 else frozenset([1, 2]))
            _removeUnusedSRPs_lookup[op] = (frozenset([0]), refPtsSet)
    
    del op
    del refPtsSet
    
    #
    # Public methods
    #
    
    def binaryString(self, **kwArgs):
        """
        Returns the binary string for this object. Keyword arguments are:
        
            combinePUSHes   Default True.
            
            maxStack        Optional; should be a list with a single int if
                            present. The int will be set to the largest stack
                            attained by the hint stream.
        
        >>> h = _testingState()
        >>> myMax = [0]
        >>> [c for c in h.binaryString(maxStack=myMax)]
        [64, 12, 53, 70, 2, 9, 1, 9, 224, 9, 240, 9, 2, 5, 127, 0, 93, 17, 55, 173]
        >>> myMax[0]
        12
        >>> myMax[0] = 0
        >>> [c for c in h.binaryString(combinePUSHes=False, maxStack=myMax)]
        [176, 5, 127, 0, 180, 224, 9, 240, 9, 2, 93, 176, 9, 17, 176, 1, 55, 179, 53, 70, 2, 9, 173]
        >>> myMax[0]
        5
        """
        
        sv = []
        maxStack = kwArgs.get('maxStack', [0])
        
        if kwArgs.get('combinePUSHes', True):
            unifiedStack = []
            unifiedOps = []
            
            for opObj in self.hints:
                pieceStack = []

                for subObj in hints_tt.Hints.frombytes(opObj.binaryString()):
                    if subObj.isPush():
                        pieceStack.extend(list(subObj.data))
                        #unifiedStack.extend(list(reversed(subObj.data)))
                    else:
                        unifiedOps.append(subObj.opcode)

                pieceStack.reverse()
                unifiedStack.extend(pieceStack)
            
            if unifiedStack:
                sv.append(OpcodeWithArgs_push(list(reversed(unifiedStack))).binaryString())
                maxStack[0] = max(maxStack[0], len(unifiedStack))
            
            sv.append(bytes([op for op in unifiedOps]))
        
        else:
            for opObj in self.hints:
                v = [0]
                sv.append(opObj.binaryString(maxStack=v))
                maxStack[0] = max(maxStack[0], v[0])
        
        return b''.join(sv)
    
    deepcopy = __deepcopy__
    
    def filterDeleted(self, toDelete):
        """
        Removes selected hints from self (modifies self in-place). toDelete is
        a dict mapping ppem values to (deleteInX, deleteInY) pairs of booleans.
        """
        
        vOut = []
        deltaBase = 9
        fv, pv = 0, 0  # 0 is x, 1 is y
        rp = [0, 0, 0]
        pEffects = set()
        
        for opObj in self.hints:
            op = opObj.opcode
            data = opObj.data
            okToAppend = True
            toDel = []
            
            if op == 0x5E:  # SDB
                deltaBase = data[0]
            
            elif op == 0x00:  # SVTCA[y]
                fv = pv = 1
            
            elif op == 0x01:  # SVTCA[x]
                fv = pv = 0
            
            elif op == 0x02:  # SPVTCA[y]
                pv = 1
            
            elif op == 0x03:  # SPVTCA[x]
                pv = 0
            
            elif op == 0x04:  # SFVTCA[y]
                fv = 1
            
            elif op == 0x05:  # SFVTCA[x]
                fv = 0
            
            elif 0x06 <= op < 0x0C:
                raise ValueError("Setting vector to computed value not supported!")
            
            elif op == 0x0E:  # SFVTPV
                fv = pv
            
            elif 0x10 <= op < 0x13:  # SRP0, SRP1, SRP2
                rp[op - 0x10] = data[0]
            
            elif op in deltaKBands:
                band = deltaKBands[op] + deltaBase
                
                for i in range(len(data) - 3 - data[-1], -1, -1):
                    ppem = band + ((data[i] & 0xFF) // 16)
                    
                    if ppem in toDelete and toDelete[ppem][fv]:
                        toDel.append(i)
                
                for i in toDel:  # already in reverse order
                    del data[i]
                
                i = len(data) - 2 - data[-1]
                
                if i == 0:
                    okToAppend = False
                else:
                    data[i] = i
            
            elif op in deltaLSMBands:
                band = deltaLSMBands[op] + deltaBase
                
                for i in range(len(data) - 3, -1, -1):
                    ppem = band + ((data[i] & 0xFF) // 16)
                    
                    if ppem in toDelete and toDelete[ppem][fv]:
                        toDel.append(i)
                
                for i in toDel:  # already in reverse order
                    del data[i]
                
                i = len(data) - 2
                
                if i == 0:
                    okToAppend = False
                else:
                    data[-2] = i
            
            elif op in deltaPBands:
                band = deltaPBands[op] + deltaBase
                
                for i in range(len(data) - 3, -2, -2):
                    ppem = band + ((data[i] & 0xFF) // 16)
                    
                    if ppem in toDelete and toDelete[ppem][fv]:
                        toDel.append(i)
                    else:
                        pEffects.add(data[i + 1])
                
                for i in toDel:  # already in reverse order
                    del data[i:i+2]
                
                if len(data) == 1:
                    okToAppend = False
                else:
                    data[-1] = (len(data) - 1) // 2
            
            elif op in mazModeStroke:
                s = span.SpanFromPairs([(data[1], data[0])])
                
                for ppem, v in toDelete.items():
                    if v[fv]:
                        s.deleteRange(ppem, ppem)
                
                if len(s) == 1:
                    data[0:2] = [s[0][1], s[0][0]]
                else:
                    okToAppend = False
                    
                    if len(s):
                        for spanStart, spanEnd in s:
                            vOut.append(OpcodeWithArgs_nonpush(op, [spanEnd, spanStart, data[2]]))
            
            elif 0x36 <= op < 0x38:  # SHZ[RP2] and SHZ[RP1]
                if rp[0x38 - op] not in pEffects:
                    okToAppend = False
            
            if okToAppend:
                vOut.append(opObj)
        
        vOut = _sanityCheck(vOut)
        self.hints[:] = vOut
        self._makeCaches()
    
    def filterDeltaPs(self, keepSpan):
        """
        Modifies self by removing all DeltaP tweaks except those for ppems in
        keepSpan. It is important for findAndRemoveWholeShifts to be called
        before this method is, because otherwise you might inadvertently remove
        one or more DELTAP hints that were used to specify shifts in the
        reference point used by a SHZ hint.
        
        >>> h = _testingState()
        >>> h.filterDeltaPs(span.Span([12, 14]))
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: SRP1 [9]
        003: SHZ[RP1] [1]
        004: DELTAS1 [53, 70, 2, 9]
        >>> h = _testingState()
        >>> h.filterDeltaPs(span.Span([23]))
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAP1 [224, 9, 1]
        003: SRP1 [9]
        004: SHZ[RP1] [1]
        005: DELTAS1 [53, 70, 2, 9]
        """
        
        toDel = set()
        
        for index, obj in enumerate(self.hints):
            op = obj.opcode
            
            if op in deltaPBands:
                band = deltaPBands[op] + self._deltaBaseCache[index]
                keeps = []
                
                for arg, pt in zip(*[iter(obj.data)] * 2):
                    ppem = band + ((arg & 0xFF) // 16)
                    
                    if keepSpan.contains(ppem):
                        keeps.extend([arg, pt])
                
                if len(keeps) < len(obj.data) - 1:
                    if len(keeps):
                        keeps.append(len(keeps) // 2)
                        obj.data[:] = keeps
                    else:
                        toDel.add(index)
        
        if toDel:
            self.hints = [obj for i, obj in enumerate(self.hints) if i not in toDel]
            self._makeCaches()
    
    def findAndRemoveWholeShifts(self):
        """
        Returns a list of (inY, ppemSet, floatShift) triples for the
        HintsWithArgs object representing all SHZs. This method also removes
        all SHZs and their accompanying DELTAP hints from the stream, leaving
        it ready for further DELTA filtering or other processing. It also
        removes any superfluous SRPs which might have been used by the SHZs.
        
        >>> h = _testingState()
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAP1 [224, 9, 240, 9, 2]
        003: SRP1 [9]
        004: SHZ[RP1] [1]
        005: DELTAS1 [53, 70, 2, 9]
        >>> h.findAndRemoveWholeShifts()
        [(True, {24, 23}, -1.0)]
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAS1 [53, 70, 2, 9]
        """
        
        retVal = []
        toDel = set()
        
        for wantY in (False, True):
            for dirIterator in self._makeDirectionIterators(wantY):
                v = list(dirIterator)  # list of (index, obj) pairs
                shzIndices = [i for i, t in enumerate(v) if t[1].opcode in SHZOpcodes]
                assert len(shzIndices) < 2, "Too many SHZs in polarized piece!"
                
                if shzIndices:
                    shzIndex = shzIndices[0]
                    index, obj = v[shzIndex]
                    toDel.add(index)
                    whichRef = 0x38 - obj.opcode
                    actualRefPoint = self._refPtCache[index][whichRef]
                    ppemByShiftDict = collections.defaultdict(set)  # shift: set(ppems)
                    
                    while shzIndex > 0:
                        shzIndex -= 1
                        index, obj = v[shzIndex]
                        op = obj.opcode
                        
                        if op == AAOpcode:
                            break
                        
                        if op in deltaPBands:
                            band = deltaPBands[op] + self._deltaBaseCache[index]
                            floatShiftBase = 2.0 ** (-self._deltaShiftCache[index])
                            nonMatches = []
                            
                            for arg, pt in zip(*[iter(obj.data)] * 2):
                                if pt == actualRefPoint:
                                    arg &= 0xFF
                                    ppem = band + (arg // 16)
                                    shift = deltaShifts[arg & 0xF] * floatShiftBase
                                    ppemByShiftDict[shift].add(ppem)
                                else:
                                    nonMatches.extend([arg, pt])
                            
                            if nonMatches:
                                nonMatches.append(len(nonMatches) // 2)
                                obj.data[:] = nonMatches
                            else:
                                toDel.add(index)
                    
                    for shift, ppemSet in ppemByShiftDict.items():
                        retVal.append((wantY, ppemSet, shift))
        
        # Remove the toDel pieces
        if toDel:
            self.hints = [obj for i, obj in enumerate(self.hints) if i not in toDel]
            self._makeCaches()
        
        # Remove any now-superfluous SRPs
        self._removeUnusedSRPs()
        
        return retVal
    
    def pprint(self, **kwArgs):
        """
        Pretty-print the object.
        
        >>> h = _testingState()
        >>> h.pprint()
        000: AA [5]
        001: SVTCA[y]
        002: DELTAP1 [224, 9, 240, 9, 2]
        003: SRP1 [9]
        004: SHZ[RP1] [1]
        005: DELTAS1 [53, 70, 2, 9]
        """
        
        p = pp.PP(**kwArgs)
        
        for index, obj in enumerate(self.hints):
            p("%03d: %s" % (index, obj))

# -----------------------------------------------------------------------------

#
# Debugging support code
#

if __debug__:
    from fontio3.hints import opcode_tt
    
    def _testingState():
        oPush = opcode_tt.Opcode_push
        oNon = opcode_tt.Opcode_nonpush
        v = [
          oPush([53, 70, 2, 9, 1, 9, 224, 9, 240, 9, 2, 5]),
          oNon(nameToOpcodeMap["AA"]),
          oNon(nameToOpcodeMap["SVTCA[y]"]),
          oNon(nameToOpcodeMap["DELTAP1"]),
          oNon(nameToOpcodeMap["SRP1"]),
          oNon(nameToOpcodeMap["SHZ[RP1]"]),
          oNon(nameToOpcodeMap["DELTAS1"])]
        return HintsWithArgs(v)
    
    def _testingState_ADD():
        oPush = opcode_tt.Opcode_push
        oNon = opcode_tt.Opcode_nonpush
        v = [
            oPush([8, 1, 50]),
            oNon(nameToOpcodeMap["ADD"]),
            oNon(nameToOpcodeMap["MIRP[setRP0, respectMinimumDistance, roundDistance, black]"])]
        return HintsWithArgs(v)
    
    def _testingState_CALL():
        oPush = opcode_tt.Opcode_push
        oNon = opcode_tt.Opcode_nonpush
        v = [
            oPush([1, 0, 69, 0, 74]),
            oNon(nameToOpcodeMap["CALL"]),
            oNon(nameToOpcodeMap["CALL"]),
            oNon(nameToOpcodeMap["AA"])]
        return HintsWithArgs(v, callInfo={69: 1, 74: 1})

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

