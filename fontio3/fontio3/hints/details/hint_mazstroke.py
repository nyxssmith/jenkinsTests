#
# hint_mazstroke.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MAZSTROKE opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MAZSTROKE(self, **kwArgs):
    """
    MAZSTROKE: Edge stroke, opcode 0xA6
    
    >>> logger = utilities.makeDoctestLogger("MAZSTROKE_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(100, 12, 29, 8)
    >>> hint_MAZSTROKE(h, logger=logger)
    >>> len(h.state.stack), len(h.state.pushHistory)
    (1, 1)
    >>> h.state.statistics.maxima.point
    8
    >>> hint_MAZSTROKE(h, logger=logger)
    MAZSTROKE_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    p = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if p is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'stack', 2) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory', 2) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("MAZSTROKE", (0,), logger):
        zp0 = state.graphicsState.zonePointer0
        
        if self._pointCheck(
          "MAZSTROKE",
          [(zp0, p, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('pointMoved', (zp0, p), history)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'MAZSTROKE')
        fatObj.notePop('ppem', 'MAZSTROKE')
        fatObj.notePop('ppem', 'MAZSTROKE')
    
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
