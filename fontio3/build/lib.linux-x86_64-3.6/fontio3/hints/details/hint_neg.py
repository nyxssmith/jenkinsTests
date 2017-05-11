#
# hint_neg.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the NEG opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_NEG(self, **kwArgs):
    """
    NEG: Negate, opcode 0x65
    
    >>> logger = utilities.makeDoctestLogger("NEG_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(
    ...   Collection([Triple(1, 11, 2), Triple(-20, -10, 5)]), -5)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["NEG"]))
    >>> hint_NEG(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Result of opcode NEG at index 0 in test, with inputs:
      Extra index 1 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    5
    >>> h.state.assign('pc', 0)
    >>> hint_NEG(h, logger=logger)
    >>> _popSync(h.state)
    Singles: [15, 20], Ranges: [(-9, 1, 2)]
    >>> hint_NEG(h, logger=logger)
    NEG_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack')
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h = self._popRemove(state, 'pushHistory')
    
    if h is None:
        state.assign('pc', doNotProceedPC)
        return
    
    state.append('stack', -n)
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        argIndex = fatObj.notePop(None, 'NEG')
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
