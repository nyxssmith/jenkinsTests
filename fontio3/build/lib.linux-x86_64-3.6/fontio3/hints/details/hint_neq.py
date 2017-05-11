#
# hint_neq.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the NEQ opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_NEQ(self, **kwArgs):
    """
    NEQ: Test for inequality, opcode 0x55
    
    >>> logger = utilities.makeDoctestLogger("NEQ_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(Collection([Triple(5, 6, 1)]), 1, 0, 1)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["NEQ"]))
    >>> hint_NEQ(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    1
    >>> h.state.assign('pc', 0)
    >>> hint_NEQ(h, logger=logger)
    >>> h.state.stack[-1]
    0
    >>> h.state.assign('pc', 0)
    >>> hint_NEQ(h, logger=logger)
    >>> h.state.stack[-1]
    1
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode NEQ at index 0 in test, with inputs:
      Extra index 0 in PUSH opcode index 0 in test
      Result of opcode NEQ at index 0 in test, with inputs:
        Extra index 1 in PUSH opcode index 0 in test
        Result of opcode NEQ at index 0 in test, with inputs:
          Extra index 2 in PUSH opcode index 0 in test
          Extra index 3 in PUSH opcode index 0 in test
    >>> hint_NEQ(h, logger=logger)
    NEQ_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    e1, e2 = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h1, h2 = t
    e1, e2 = e1.commonBasis(e2)
    r = e1.equal(e2).logicalNOT()
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
        historyIterable = [h1, h2]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'NEQ')
        fatObj.notePop(None, 'NEQ')
        fatObj.notePush()
    
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
