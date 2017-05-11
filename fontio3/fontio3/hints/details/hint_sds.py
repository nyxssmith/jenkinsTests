#
# hint_sds.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SDS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SDS(self, **kwArgs):
    """
    SDS: Set delta shift, opcode 0x5F
    
    >>> logger = utilities.makeDoctestLogger("SDS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(9, 2)
    >>> hint_SDS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.deltaShift
    2
    >>> hint_SDS(h, logger=logger)
    SDS_test - ERROR - SDS hint in test (PC 1) attempted to set a value that was not an integer between 0 and 6, inclusive.
    >>> hint_SDS(h, logger=logger)
    SDS_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if not self._16BitCheck("SDS", n, logger, False):
        pass
    
    elif any(x not in set(range(7)) for x in n):
        logger.error((
          'E6052',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SDS hint in %s (PC %d) attempted to set a value that was not "
          "an integer between 0 and 6, inclusive."))
        
        state._validationFailed = True
    
    else:
        n2 = n.toNumber()
        
        if n2 is not None:
            n = n2
        
        state.assignDeep('graphicsState', 'deltaShift', n)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SDS')
    
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
