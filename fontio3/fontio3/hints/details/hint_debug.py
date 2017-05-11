#
# hint_debug.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DEBUG opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DEBUG(self, **kwArgs):
    """
    DEBUG: Debugging call, opcode 0x4F (unimplemented)
    
    >>> logger = utilities.makeDoctestLogger("DEBUG_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(12)
    >>> hint_DEBUG(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('debug',))
    History for DEBUG opcodes:
      12: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_DEBUG(h, logger=logger)
    DEBUG_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    value = self._popRemove(state, 'stack')
    
    if value is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('debugCode', 'DEBUG')
    
    state.statistics.addHistory('debug', value, history)
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
