#
# hint_and.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the AND opcode.
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

AND_table = {  # only these keys are valid
  (False, True, False, True): lambda: 1,
  (False, True, True, False): lambda: 0,
  (False, True, True, True): lambda: Collection([Triple(0, 2, 1)]),
  (True, False, False, True): lambda: 0,
  (True, False, True, False): lambda: 0,
  (True, False, True, True): lambda: 0,
  (True, True, False, True): lambda: Collection([Triple(0, 2, 1)]),
  (True, True, True, False): lambda: 0,
  (True, True, True, True): lambda: Collection([Triple(0, 2, 1)])}

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_AND(self, **kwArgs):
    """
    AND: Logical AND, opcode 0x5A
    
    >>> logger = utilities.makeDoctestLogger("AND_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(1, 2)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["AND"]))
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    >>> hint_AND(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode AND at index 0 in test, with inputs:
      Extra index 0 in PUSH opcode index 0 in test
      Extra index 1 in PUSH opcode index 0 in test
    >>> h = _testingState(0, toCollection([0, 4]), 4, 5)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["AND"]))
    >>> hint_AND(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack[-1]
    1
    >>> h.state.assign('pc', 0)
    >>> hint_AND(h, logger=logger)
    >>> h.state.stack[-1]
    Singles: [0, 1]
    >>> h.state.assign('pc', 0)
    >>> hint_AND(h, logger=logger)
    >>> h.state.stack[-1]
    0
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> hint_AND(h, logger=logger)
    AND_test - CRITICAL - Stack underflow in test (PC 1).
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
    state.append('stack', AND_table[t]())
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = vh))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'AND')
        fatObj.notePop(None, 'AND')
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
