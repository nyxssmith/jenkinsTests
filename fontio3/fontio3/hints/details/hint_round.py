#
# hint_round.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ROUND opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ROUND(self, **kwArgs):
    """
    ROUND: Round using current mode, opcodes 0x68-0x6B
    
    >>> logger = utilities.makeDoctestLogger("ROUND_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(65)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["ROUND[gray]"]))
    >>> hint_ROUND(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> _popSync(h.state)
    64
    >>> hint_ROUND(h, logger=logger)
    ROUND_test - CRITICAL - Stack underflow in test (PC 1).
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
          "ROUND opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
        state.append('stack', 0)
    
    else:
        result = self._round(
          distance.changedBasis(64),
          color = kwArgs.get('color', 'gray'),
          coerceToNumber = False)
        
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
        argIndex = fatObj.notePop(None, 'ROUND')
        fatObj.notePush(argIndex=argIndex)
    
    state.assign('pc', state.pc + 1)

def hint_ROUND_badColor(self, **kwArgs):
    state = self.state
    logger = self._getLogger(**kwArgs)
    self._popRemove(state, 'stack')
    self._popRemove(state, 'pushHistory')
    
    logger.error((
      'E6027',
      (self.ultParent.infoString, state.pc + self.ultDelta),
      "ROUND opcode in %s (PC %d) has invalid color distance (3)."))
    
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
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
