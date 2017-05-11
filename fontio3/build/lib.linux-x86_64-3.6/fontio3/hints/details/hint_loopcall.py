#
# hint_loopcall.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the LOOPCALL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_LOOPCALL(self, **kwArgs):
    """
    LOOPCALL: Iterative function call, opcode 0x2A
    
    >>> logger = utilities.makeDoctestLogger("LOOPCALL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(3, 26)
    >>> hint_LOOPCALL(h, logger=logger)
    LOOPCALL_test - ERROR - Calling an unknown FDEF was attempted in test (PC 0).
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('function',))
    History for function calls:
      26: Extra index 1 in PUSH opcode index 0 in test
    >>> h.state.assign('pc', 0)
    >>> hint_LOOPCALL(h, logger=logger)
    LOOPCALL_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    count, functionIndex = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    ignore, indexHistory = t
    count = count.toNumber()
    
    if count is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if not self._16BitCheck("LOOPCALL", count, logger, False):
        
        # Normally a 16-bit check does not cause early termination, but
        # missing the CALLs in the loop would leave the stack in an
        # indeterminate state, so we can't really proceed.
        
        state.assign('pc', doNotProceedPC)
        return
    
    stats.addHistory('function', functionIndex, indexHistory)
    
    stats.noteEffect(
      kind = 'function',
      value = functionIndex,
      infoString = self.ultParent.infoString,
      pc = state.pc + self.ultDelta,
      relStackIndex = -1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        # we only deal with the FDEF index and count here; the startFDEF()
        # calls are done in _callSub (so it works for CALLs too).
        fatObj.notePop('fdefIndex', 'LOOPCALL')
        fatObj.notePop(None, 'LOOPCALL')
    
    while count:
        # The following call leaves state.pc untouched.
        self._callSub(functionIndex, **kwArgs)
        
        if self.state.pc == doNotProceedPC:
            return
        
        count -= 1
    
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
