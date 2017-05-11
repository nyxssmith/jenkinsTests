#
# hint_nround.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the NROUND opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_NROUND(self, **kwArgs):
    """
    NROUND: No round (engine only), opcodes 0x6C-0x6F
    
    >>> logger = utilities.makeDoctestLogger("NROUND_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(65)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["NROUND[gray]"]))
    >>> h.state.colorDistances.gray = Collection([Triple(2, 3, 1)], 64)
    >>> h.state.changed('colorDistances')
    >>> hint_NROUND(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode NROUND[gray] at index 0 in test, with inputs:
      Extra index 0 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    67
    >>> hint_NROUND(h, logger=logger)
    NROUND_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    distance = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if distance is None:
        state.assign('pc', doNotProceedPC)
        return
    
    distance = distance.changedBasis(1)
    h = self._popRemove(state, 'pushHistory')
    
    if h is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if (None not in distance) and any(n < -16384 or n >= 16384 for n in distance):
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "NROUND opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
        state.append('stack', 0)
    
    else:
        colorDist = getattr(state.colorDistances, kwArgs.get('color', 'gray'))
        cNeg, cPos = distance.changedBasis(64).signedParts()
        result = (cNeg - colorDist).addToCollection(cPos + colorDist)
        result = result.changedBasis(1)
        r2 = result.toNumber()
        
        if r2 is not None:
            result = r2
        
        state.append('stack', result)
        
        state.append(
          'pushHistory',
          op.HistoryEntry_op(
            hintsObj = (id(self.ultParent), self.ultParent), 
            hintsPC = state.pc + self.ultDelta,
            opcode = self[state.pc].opcode,
            historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        argIndex = fatObj.notePop(None, 'NROUND')
        fatObj.notePush(argIndex=argIndex)
    
    state.assign('pc', state.pc + 1)

def hint_NROUND_badColor(self, **kwArgs):
    state = self.state
    logger = self._getLogger(**kwArgs)
    self._popRemove(state, 'stack')
    self._popRemove(state, 'pushHistory')
    
    logger.error((
      'E6027',
      (self.ultParent.infoString, state.pc + self.ultDelta),
      "NROUND opcode in %s (PC %d) has invalid color distance (3)."))
    
    state._validationFailed = True
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints import opcode_tt
    from fontio3.hints.common import nameToOpcodeMap
    from fontio3.triple.collection import Collection
    from fontio3.triple.triple import Triple
    from fontio3.utilities import pp
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
