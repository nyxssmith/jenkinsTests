#
# hint_sround.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SROUND opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SROUND(self, **kwArgs):
    """
    SROUND: Super round, opcode 0x76
    
    >>> logger = utilities.makeDoctestLogger("SROUND_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([0x61, 0xD5]), 0x61)
    >>> hint_SROUND(h, logger=logger)
    >>> h.state.graphicsState.roundState
    [Singles: [1.0], Singles: [0.5], Singles: [-0.375]]
    >>> hint_SROUND(h, logger=logger)
    SROUND_test - ERROR - In test (PC 1) a Collection value was used, but is not supported in fontio.
    >>> h.state.assign('pc', 0)
    >>> hint_SROUND(h, logger=logger)
    SROUND_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    is45Case = kwArgs.get('is45Case', False)
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    n = self._toNumber(n)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._8BitCheck(("S45ROUND" if is45Case else "SROUND"), n, logger):
        thresholdIndex = n & 15
        phaseIndex = (n // 16) & 3
        periodIndex = (n // 64) & 3
        
        if periodIndex == 3:
            
            logger.error((
              'E6000',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "Reserved value of 3 used for period in SROUND or "
              "S45ROUND hint in %s (PC %d)."))
            
            state._validationFailed = True
        
        else:
            if is45Case:
                sqrt2 = math.sqrt(2.0)
                period = [0.5 * sqrt2, sqrt2, 2.0 * sqrt2][periodIndex]
            
            else:
                period = [0.5, 1.0, 2.0][periodIndex]
            
            phase = [0.0, 0.25, 0.5, 0.75][phaseIndex]
            threshold = [x / 8.0 for x in range(-4, 12)]
            
            if thresholdIndex:
                threshold = threshold[thresholdIndex]
            else:
                threshold = -1.0
            
            need = [
              toCollection(period, 64),
              toCollection(phase, 64),
              toCollection(threshold, 64)]
            
            state.assignDeep('graphicsState', 'roundState', need)
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('roundState', 'SROUND')
    
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
