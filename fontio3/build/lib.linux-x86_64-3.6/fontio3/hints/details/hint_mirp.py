#
# hint_mirp.py
#
# Copyright © 2014, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MIRP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MIRP(self, **kwArgs):
    """
    MIRP: Move indirect relative point, opcodes 0xE0-0xFF
    
    >>> logger = utilities.makeDoctestLogger("MIRP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(7, 11, 12, 3, 15)
    >>> m = h.state.statistics.maxima
    >>> hint_MIRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point, m.cvt
    (3, 15)
    >>> hint_srp0.hint_SRP0(h, logger=logger)
    >>> hint_MIRP(h, logger=logger)
    >>> m.point, m.cvt
    (12, 15)
    >>> h.state.statistics.pprint(keys=('cvt', 'point'))
    History for CVT values:
      11: Extra index 1 in PUSH opcode index 0 in test
      15: Extra index 4 in PUSH opcode index 0 in test
    History for outline points (glyph zone):
      0: Implicit zero for RP0 used at opcode index 0 in test
      3: Extra index 3 in PUSH opcode index 0 in test
      7: Extra index 0 in PUSH opcode index 0 in test
      12: Extra index 2 in PUSH opcode index 0 in test
    >>> hint_MIRP(h, logger=logger)
    MIRP_test - CRITICAL - Stack underflow in test (PC 3).
    """
    
    state = self.state
    stack = state.stack
    stats = state.statistics
    gs = state.graphicsState
    rph = state.refPtHistory
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
          "For MIRP opcode in %s (PC %d), "
          "CVTs not present in CVT table: %s"))
        
        state._validationFailed = True
    
    elif self._zoneCheck("MIRP", (0, 1), logger):
        zp0, zp1 = gs.zonePointer0, gs.zonePointer1
        
        v = [
          (zp1, point, True),
          (zp0, toCollection(gs.referencePoint0), False)]
        
        if self._pointCheck(
          "MIRP",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            stats.addHistory('cvt', cvtIndex, cvtHist)
            
            stats.noteEffect(
              'cvt',
              cvtIndex,
              self.ultParent.infoString,
              state.pc + self.ultDelta,
              -1)
            
            stats.addHistory('pointMoved', (zp1, point), pointHist)
            refHist = self._synthRefHistory(0)
            
            stats.addHistory(
              'point',
              (zp0, gs.referencePoint0),
              refHist)
            
            state.assignDeep(
              'graphicsState',
              'referencePoint1',
              gs.referencePoint0)
            
            state.assignDeep('graphicsState', 'referencePoint1', point)
            rph[1] = rph[0]
            rph[2] = pointHist
            state.changed('refPtHistory')
            
            if kwArgs.get('setRP0', False):
                state.assignDeep('graphicsState', 'referencePoint0', point)
                rph[0] = pointHist
                state.changed('refPtHistory')
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('cvtIndex', 'MIRP')
        fatObj.notePop('pointIndex', 'MIRP')
    
    state.assign('pc', state.pc + 1)

def hint_MIRP_badColor(self, **kwArgs):
    state = self.state
    logger = self._getLogger(**kwArgs)
    self._popRemove(state, 'stack', 2)
    self._popRemove(state, 'pushHistory', 2)
    
    logger.error((
      'E6027',
      (self.ultParent.infoString, state.pc + self.ultDelta),
      "MIRP opcode in %s (PC %d) has invalid color distance (3)."))
    
    state._validationFailed = True
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints.details import hint_srp0
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
