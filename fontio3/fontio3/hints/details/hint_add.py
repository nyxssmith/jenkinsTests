#
# hint_add.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ADD opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ADD(self, **kwArgs):
    """
    ADD: Add, opcode 0x60
    
    >>> logger = utilities.makeDoctestLogger("ADD_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(40000000, toCollection([3, 5, 11]), 4, -12)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["ADD"]))
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 3 in PUSH opcode index 0 in test
    >>> hint_ADD(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Result of opcode ADD at index 0 in test, with inputs:
      Extra index 2 in PUSH opcode index 0 in test
      Extra index 3 in PUSH opcode index 0 in test
    >>> h.state.stack[-1]
    -8
    
    >>> h.state.assign('pc', 0)
    >>> hint_ADD(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    Singles: [-5, -3, 3]
    
    >>> h.state.assign('pc', 0)
    >>> hint_ADD(h, logger=logger)
    ADD_test - ERROR - ADD opcode in test (PC 0) resulted in a number that cannot be represented in 26.6 notation.
    
    >>> hint_ADD(h, logger=logger)
    ADD_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    e1, e2 = t
    vh = self._popRemove(state, 'pushHistory', 2)
    
    if vh is None:
        state.assign('pc', doNotProceedPC)
        return
    
    r = e1 + e2
    rMin = r.min()
    rMax = r.max()
    
    if (
      (rMin is not None) and
      (rMax is not None) and
      (rMin < -33554432.0 or rMax > 33554431.984375)):
        
        logger.error((
          'E6036',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "ADD opcode in %s (PC %d) resulted in a number that cannot "
          "be represented in 26.6 notation."))
        
        state._validationFailed = True
        r = 0
    
    else:
        r2 = r.toNumber()
        
        if r2 is not None:
            r = r2
    
    state.append('stack', r)
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = vh))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        argIndex1 = fatObj.notePop(None, 'ADD')
        argIndex2 = fatObj.notePop(None, 'ADD')
        
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
