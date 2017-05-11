#
# hint_or.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the OR opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import Collection
from fontio3.triple.triple import Triple

# -----------------------------------------------------------------------------

#
# Constants
#

hint_OR_table = {  # only these keys are valid
  (False, True, False, True): lambda: 1,
  (False, True, True, False): lambda: 1,
  (False, True, True, True): lambda: 1,
  (True, False, False, True): lambda: 1,
  (True, False, True, False): lambda: 0,
  (True, False, True, True): lambda: Collection([Triple(0, 2, 1)]),
  (True, True, False, True): lambda: 1,
  (True, True, True, False): lambda: Collection([Triple(0, 2, 1)]),
  (True, True, True, True): lambda: Collection([Triple(0, 2, 1)])}

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_OR(self, **kwArgs):
    """
    OR: Logical OR, opcode 0x5B
    
    >>> logger = utilities.makeDoctestLogger("OR_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(4, 0, 0)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["OR"]))
    >>> hint_OR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    0
    >>> h.state.assign('pc', 0)
    >>> hint_OR(h, logger=logger)
    >>> h.state.stack[-1]
    1
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode OR at index 0 in test, with inputs:
      Extra index 0 in PUSH opcode index 0 in test
      Result of opcode OR at index 0 in test, with inputs:
        Extra index 1 in PUSH opcode index 0 in test
        Extra index 2 in PUSH opcode index 0 in test
    >>> hint_OR(h, logger=logger)
    OR_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    e1, e2 = [obj.encompassedBooleans() for obj in t]
    vh = self._popRemove(state, 'pushHistory', 2)
    
    if vh is None:
        state.assign('pc', doNotProceedPC)
        return
    
    t = (0 in e1, 1 in e1, 0 in e2, 1 in e2)
    state.append('stack', hint_OR_table[t]())
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = vh))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'OR')
        fatObj.notePop(None, 'OR')
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
