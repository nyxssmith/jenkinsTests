#
# hint_not.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the NOT opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_NOT(self, **kwArgs):
    """
    NOT: Logical NOT, opcode 0x5C
    
    >>> logger = utilities.makeDoctestLogger("NOT_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(Collection([Triple(0, 8, 4)]), 0, 5)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["NOT"]))
    >>> hint_NOT(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Result of opcode NOT at index 0 in test, with inputs:
      Extra index 2 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    0
    >>> h.state.assign('pc', 0)
    >>> hint_NOT(h, logger=logger)
    >>> _popSync(h.state)
    1
    >>> h.state.assign('pc', 0)
    >>> hint_NOT(h, logger=logger)
    >>> _popSync(h.state)
    Singles: [0, 1]
    >>> hint_NOT(h, logger=logger)
    NOT_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h = self._popRemove(state, 'pushHistory')
    
    if h is None:
        state.assign('pc', doNotProceedPC)
        return
    
    v = list(n.encompassedBooleans())
    
    if len(v) == 1:
        v = [1 - v[0]]
    
    state.append('stack', (v[0] if len(v) == 1 else toCollection(v)))
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'NOT')
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
