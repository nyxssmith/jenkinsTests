#
# hint_div.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DIV opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DIV(self, **kwArgs):
    """
    DIV: Divide, opcode 0x62
    
    >>> logger = utilities.makeDoctestLogger("DIV_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(
    ...   toCollection([32, 64]),
    ...   toCollection([32, 64]),
    ...   128)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["DIV"]))
    >>> hint_DIV(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    Singles: [0.25, 0.5]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Result of opcode DIV at index 0 in test, with inputs:
      Extra index 1 in PUSH opcode index 0 in test
      Extra index 2 in PUSH opcode index 0 in test
    >>> h.state.assign('pc', 0)
    >>> hint_DIV(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    Singles: [1.0, 2.0, 4.0]
    >>> h = _testingState(64, 0, 3 * 64, 2 * 64)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["DIV"]))
    >>> hint_DIV(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    96
    >>> h.state.assign('pc', 0)
    >>> hint_DIV(h, logger=logger)
    >>> h.state.stack[-1]
    0
    >>> h.state.assign('pc', 0)
    >>> hint_DIV(h, logger=logger)
    DIV_test - ERROR - Division by zero in DIV opcode in test (PC 0).
    >>> h = _testingState(20000000 * 64, 2)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["DIV"]))
    >>> hint_DIV(h, logger=logger)
    DIV_test - ERROR - DIV opcode in test (PC 0) resulted in a number that cannot be represented in 26.6 notation.
    >>> hint_DIV(h, logger=logger)
    DIV_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    numer, denom = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h1, h2 = t
    
    if 0 in denom:
        logger.error((
          'E6006',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "Division by zero in DIV opcode in %s (PC %d)."))
        
        state._validationFailed = True
        state.append('stack', 0)
    
    else:
        result = numer.changedBasis(64) / denom.changedBasis(64)
        rMin = result.min()
        rMax = result.max()
        
        if (
          (rMin is not None) and
          (rMax is not None) and
          (rMin < -33554432.0 or rMax > 33554431.984375)):
            
            logger.error((
              'E6036',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "DIV opcode in %s (PC %d) resulted in a number that cannot "
              "be represented in 26.6 notation."))
            
            state._validationFailed = True
            result = 0
        
        else:
            r2 = result.changedBasis(1).toNumber()
            
            if r2 is not None:
                result = r2
        
        state.append('stack', result)
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [h1, h2]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        argIndex1 = fatObj.notePop(None, 'DIV')
        argIndex2 = fatObj.notePop(None, 'DIV')
        
        if (argIndex1 is not None) and (argIndex2 is not None):
            if not isinstance(argIndex1, tuple):
                argIndex1 = (argIndex1,)
            
            if not isinstance(argIndex2, tuple):
                argIndex2 = (argIndex2,)
            
            argIndex = frozenset(argIndex1 + argIndex2)
            
            if len(argIndex) == 1:
                argIndex = next(iter(argIndex))
        
        elif argIndex1 is not None:
            argIndex = argIndex1
        
        elif argIndex2 is not None:
            argIndex = argIndex2
        
        else:
            argIndex = None
        
        fatObj.notePush(argIndex=argIndex)
    
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
    from fontio3.triple.collection import toCollection
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
