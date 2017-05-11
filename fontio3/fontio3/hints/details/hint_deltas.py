#
# hint_deltas.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DELTAS opcodes.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DELTAS(self, **kwArgs):
    """
    DELTAS[1-3]: Smart contour delta, opcodes 0xAD-0xAF
    
    Note that this current implementation ignores the bandDelta kwArg.
    
    >>> logger = utilities.makeDoctestLogger("DELTAS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(100, 100, 2, 8)
    >>> hint_DELTAS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    8
    >>> hint_DELTAS(h, logger=logger)
    DELTAS_test - CRITICAL - Stack underflow in test (PC 1).
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
    
    obj = self._popRemove(state, 'stack')
    
    if obj is None:
        state.assign('pc', doNotProceedPC)
        return
    
    count = self._toNumber(obj)
    
    if count is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'stack', count) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory', count + 1) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("DELTAS", (0,), logger):
        zp0 = state.graphicsState.zonePointer0
        
        if self._pointCheck(
          "DELTAS",
          [(zp0, p, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory(
              'pointMoved',
              (zp0, p),
              history)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'DELTAS')
        fatObj.notePop(None, 'DELTAS')
        
        for i in range(count):
            fatObj.notePop('deltaArg', 'DELTAS')
    
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
