#
# hint_deltak.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DELTAK opcodes.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DELTAK(self, **kwArgs):
    """
    DELTAK[1-3]: Smart grouped delta, opcodes 0xA7-0xA9
    
    Note that this current implementation ignores the bandDelta kwArg.
    
    >>> logger = utilities.makeDoctestLogger("DELTAK_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(100, 100, 2, 4, 7, 3, 3)
    >>> hint_DELTAK(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    7
    >>> hint_DELTAK(h, logger=logger)
    DELTAK_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack')
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    lowCount = self._toNumber(n)
    
    if lowCount is None or self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    lowVec = self._popRemove(  # points
      state,
      'stack',
      lowCount,
      coerceToCollection = True,
      coerceToList = True)
    
    if lowVec is None:
        state.assign('pc', doNotProceedPC)
        return
    
    historyVec = self._popRemove(
      state,
      'pushHistory',
      lowCount,
      coerceToList = True)
    
    if historyVec is None:
        state.assign('pc', doNotProceedPC)
        return
    
    n = self._popRemove(state, 'stack')
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    highCount = self._toNumber(n)
    
    if highCount is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'stack', highCount) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory', highCount + 1) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    zp0 = state.graphicsState.zonePointer0
    
    if self._zoneCheck("DELTAK", (0,), logger):
        
        if self._pointCheck(
          "DELTAK",
          ((zp0, p, True) for p in lowVec),
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, pointIndex in enumerate(lowVec):
                state.statistics.addHistory(
                  'pointMoved',
                  (zp0, pointIndex),
                  historyVec[i])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'DELTAK')
        
        for p in lowVec:
            fatObj.notePop('cvtIndex', 'DELTAK')
        
        for i in range(highCount):
            fatObj.notePop('deltaArg', 'DELTAK')
    
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
