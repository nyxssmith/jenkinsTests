#
# hint_miap.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MIAP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MIAP(self, **kwArgs):
    """
    MIAP: Move indirect absolute point, opcodes 0x3E-0x3F
    
    >>> logger = utilities.makeDoctestLogger("MIAP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(2, 14)
    >>> m = h.state.statistics.maxima
    >>> hint_MIAP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point, m.cvt
    (2, 14)
    >>> h.state.statistics.pprint(keys=('cvt', 'point'))
    History for CVT values:
      14: Extra index 1 in PUSH opcode index 0 in test
    History for outline points (glyph zone):
      2: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_MIAP(h, logger=logger)
    MIAP_test - CRITICAL - Stack underflow in test (PC 1).
    >>> h = _testingState(2, 140)
    >>> hint_MIAP(h, logger=logger)
    MIAP_test - ERROR - For MIAP opcode in test (PC 0), CVTs not present in CVT table: [140]
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    point, cvtIndex = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    pointHist, cvtHist = t
    missing = sorted(n for n in cvtIndex if n not in state.cvt)
    
    if missing:
        logger.error((
          'E6005',
          (self.ultParent.infoString, state.pc + self.ultDelta, missing),
          "For MIAP opcode in %s (PC %d), "
          "CVTs not present in CVT table: %s"))
        
        state._validationFailed = True
    
    elif self._zoneCheck("MIAP", (0, 1), logger):
        zp0 = state.graphicsState.zonePointer0
        
        if self._pointCheck(
          "MIAP",
          [(zp0, point, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            stats.addHistory('pointMoved', (zp0, point), pointHist)
            stats.addHistory('cvt', cvtIndex, cvtHist)
            
            stats.noteEffect(
              'cvt',
              cvtIndex,
              self.ultParent.infoString,
              state.pc + self.ultDelta,
              -1)
            
            state.assignDeep('graphicsState', 'referencePoint0', point)
            state.assignDeep('graphicsState', 'referencePoint1', point)
            state.refPtHistory[0] = state.refPtHistory[1] = pointHist
            state.changed('refPtHistory')
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('cvtIndex', 'MIAP')
        fatObj.notePop('pointIndex', 'MIAP')
    
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
