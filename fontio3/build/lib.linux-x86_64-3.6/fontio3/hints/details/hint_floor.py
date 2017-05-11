#
# hint_floor.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the FLOOR opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_FLOOR(self, **kwArgs):
    """
    FLOOR: Numerical floor, opcode 0x66
    
    >>> logger = utilities.makeDoctestLogger("FLOOR_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(Collection([Triple(32, 512, 16)]), -1, 127, 129)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["FLOOR"]))
    >>> hint_FLOOR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Result of opcode FLOOR at index 0 in test, with inputs:
      Extra index 3 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    128
    >>> h.state.assign('pc', 0)
    >>> hint_FLOOR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> _popSync(h.state)
    64
    >>> h.state.assign('pc', 0)
    >>> hint_FLOOR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> _popSync(h.state)
    -64
    >>> h.state.assign('pc', 0)
    >>> hint_FLOOR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> _popSync(h.state)
    Ranges: [(0, 512, 64)]
    >>> hint_FLOOR(h, logger=logger)
    FLOOR_test - CRITICAL - Stack underflow in test (PC 1).
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
    
    n = n.changedBasis(64).floor()
    n2 = n.toNumber()
    
    if n2 is not None:
        n = n2
    
    state.append('stack', n << 6)
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        argIndex = fatObj.notePop(None, 'FLOOR')
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
