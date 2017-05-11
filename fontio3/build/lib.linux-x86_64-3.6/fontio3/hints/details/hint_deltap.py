#
# hint_deltap.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DELTAP opcodes.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DELTAP(self, **kwArgs):
    """
    DELTAP[1-3]: Single-point delta, opcodes 0x5D, 0x71 and 0x72
    
    Note that this current implementation ignores the bandDelta kwArg.
    
    >>> logger = utilities.makeDoctestLogger("DELTAP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(100, 5, 105, 3, 2)
    >>> hint_DELTAP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    5
    >>> hint_DELTAP(h, logger=logger)
    DELTAP_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    obj = self._popRemove(state, 'stack')
    
    if obj is None:
        state.assign('pc', doNotProceedPC)
        return
    
    count = self._toNumber(obj, doCheck=False)
    
    if count is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if count:  # some fonts have a zero count as a pseudo-NOP
        allPieces = self._popRemove(
          state,
          'stack',
          2 * count,
          coerceToCollection = True,
          coerceToList = True)
        
        if allPieces is None:
            state.assign('pc', doNotProceedPC)
            return
        
        argPiece = [
          self._toNumber(obj, doCheck=False, logger=logger)
          for obj in allPieces[0::2]]
        
        okToProceed = True
        
        for arg in argPiece:
            okToProceed = (
              self._8BitCheck("DELTAP", arg, logger) and
              okToProceed)
        
        if okToProceed:
            if argPiece != sorted(argPiece):
                logger.warning((
                  'V0491',
                  (self.ultParent.infoString, state.pc + self.ultDelta),
                  "The DELTAP opcode in %s (PC %d) has args unsorted "
                  "by PPEM. They should be sorted if this font is "
                  "to be used with iType."))
            
            pointPiece = allPieces[1::2]
            historyPiece = self._popRemove(state, 'pushHistory', 2 * count)
            
            if historyPiece is None:
                state.assign('pc', doNotProceedPC)
                return
            
            historyPiece = historyPiece[1::2]
            
            if self._zoneCheck("DELTAP", (0,), logger):
                zp0 = state.graphicsState.zonePointer0
                
                if self._pointCheck(
                  "DELTAP",
                  ((zp0, p, True) for p in pointPiece),
                  logger,
                  kwArgs.get('extraInfo', {})):
                    
                    for i, p in enumerate(pointPiece):
                        state.statistics.addHistory(
                          'pointMoved',
                          (zp0, p),
                          historyPiece[i])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'DELTAP')
        
        for i in range(count):
            fatObj.notePop('pointIndex', 'DELTAP')
            fatObj.notePop('deltaArg', 'DELTAP')
    
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
