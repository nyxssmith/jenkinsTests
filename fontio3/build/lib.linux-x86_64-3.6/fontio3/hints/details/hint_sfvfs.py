#
# hint_sfvfs.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SFVFS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SFVFS(self, **kwArgs):
    """
    SFVFS: Set freedom vector from stack, opcode 0x0B
    
    >>> logger = utilities.makeDoctestLogger("SFVFS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(11585, 11585)
    >>> h.state.graphicsState.freedomVector
    (Singles: [1], Singles: [0])
    >>> hint_SFVFS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.freedomVector
    (Singles: [0.70709228515625], Singles: [0.70709228515625])
    >>> hint_SFVFS(h, logger=logger)
    SFVFS_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    x, y = t
    
    if self._popRemove(state, 'pushHistory', 2) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._16BitCheck("SFVFS", x, logger, True):
        if self._16BitCheck("SFVFS", y, logger, True):
            
            state.assignDeep(
              'graphicsState',
              'freedomVector',
              (x.changedBasis(16384), y.changedBasis(16384)))
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SFVFS')
        fatObj.notePop(None, 'SFVFS')
    
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
