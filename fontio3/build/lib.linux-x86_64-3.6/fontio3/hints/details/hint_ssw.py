#
# hint_ssw.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SSW opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SSW(self, **kwArgs):
    """
    SSW: Set single-width value, opcode 0x1F
    
    >>> logger = utilities.makeDoctestLogger("SSW_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(48)
    >>> hint_SSW(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.singleWidthValue
    0.75
    >>> hint_SSW(h, logger=logger)
    SSW_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    distance = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if distance is None:
        state.assign('pc', doNotProceedPC)
        return
    
    distance = distance.changedBasis(1)
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if not self._16BitCheck("SSW", distance, logger, False):
        pass
    
    elif (
      (None not in distance) and
      any(n < -16384 or n >= 16384 for n in distance)):
        
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SSW opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
    
    else:
        distance = distance.changedBasis(64)
        d2 = distance.toNumber()
        
        if d2 is not None:
            distance = d2
        
        state.assignDeep('graphicsState', 'singleWidthValue', distance)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a
            # FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SSW')
    
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
