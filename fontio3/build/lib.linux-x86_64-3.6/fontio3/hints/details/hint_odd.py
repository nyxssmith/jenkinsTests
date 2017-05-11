#
# hint_odd.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ODD opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ODD(self, **kwArgs):
    """
    ODD: Determine even/odd state, opcode 0x56
    
    >>> logger = utilities.makeDoctestLogger("ODD_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(96, 94)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["ODD"]))
    >>> hint_ODD(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Result of opcode ODD at index 0 in test, with inputs:
      Extra index 1 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    1
    >>> h.state.assign('pc', 0)
    >>> hint_ODD(h, logger=logger)
    >>> _popSync(h.state)
    0
    >>> hint_ODD(h, logger=logger)
    ODD_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    n = n.changedBasis(64)
    h = self._popRemove(state, 'pushHistory')
    
    if h is None:
        state.assign('pc', doNotProceedPC)
        return
    
    rounded = self._round(n, coerceToNumber=False)
    r = (rounded.changedBasis(1) & 0x40) >> 6
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
        historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'ODD')
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
