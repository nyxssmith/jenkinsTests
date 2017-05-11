#
# hint_sdb.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SDB opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SDB(self, **kwArgs):
    """
    SDB: Set delta base, opcode 0x5E
    
    >>> logger = utilities.makeDoctestLogger("SDB_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(16)
    >>> hint_SDB(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.deltaBase
    16
    >>> hint_SDB(h, logger=logger)
    SDB_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack')
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._16BitCheck("SDB", n, logger, False):
        state.assignDeep('graphicsState', 'deltaBase', n)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a
            # FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SDB')
    
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
