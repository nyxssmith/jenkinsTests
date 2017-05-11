#
# hint_sswci.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SSWCI opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SSWCI(self, **kwArgs):
    """
    SSWCI: Set single-width cut-in, opcode 0x1E
    
    >>> logger = utilities.makeDoctestLogger("SSWCI_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(96)
    >>> hint_SSWCI(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.singleWidthCutIn
    1.5
    >>> hint_SSWCI(h, logger=logger)
    SSWCI_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    distance = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if distance is None:
        state.assign('pc', doNotProceedPC)
        return
    
    distance = distance.changedBasis(1)
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if (
      (None not in distance) and
      any(n < -16384 or n >= 16384 for n in distance)):
        
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SSWCI opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
    
    else:
        distance = distance.changedBasis(64)
        d2 = distance.toNumber()
        
        if d2 is not None:
            distance = d2
        
        state.assignDeep('graphicsState', 'singleWidthCutIn', distance)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SSWCI')
    
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
