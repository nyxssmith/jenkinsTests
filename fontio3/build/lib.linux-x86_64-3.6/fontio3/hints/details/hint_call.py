#
# hint_call.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the CALL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_CALL(self, **kwArgs):
    """
    CALL: Call a FDEF, opcode 0x2B
    
    >>> logger = utilities.makeDoctestLogger("CALL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(26)
    >>> hint_CALL(h, logger=logger)
    CALL_test - ERROR - Calling an unknown FDEF was attempted in test (PC 0).
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('function',))
    History for function calls:
      26: Extra index 0 in PUSH opcode index 0 in test
    >>> h.state.assign('pc', 0)
    >>> hint_CALL(h, logger=logger)
    CALL_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    functionIndex = self._popRemove(state, 'stack')
    
    if functionIndex is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    stats.addHistory('function', functionIndex, history)
    
    stats.noteEffect(
      kind = 'function',
      value = functionIndex,
      infoString = self.ultParent.infoString,
      pc = state.pc + self.ultDelta,
      relStackIndex = -1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        # we only deal with the popped FDEF index here; the startFDEF()
        # call is done in _callSub (so it works for LOOPCALLs too).
        fatObj.notePop('fdefIndex', 'CALL')
    
    self._callSub(functionIndex, **kwArgs)  # leaves state.pc untouched
    state = self.state  # might have changed in _callSub()
    
    if state.pc != doNotProceedPC:
        state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
