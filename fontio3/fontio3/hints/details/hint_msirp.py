#
# hint_msirp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MSIRP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MSIRP(self, **kwArgs):
    """
    MSIRP: Move stack indirect relative point, opcodes 0x3A-0x3B
    
    >>> logger = utilities.makeDoctestLogger("MSIRP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(7, -32, 12, 3, 64)
    >>> m = h.state.statistics.maxima
    >>> hint_MSIRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    3
    >>> hint_srp0.hint_SRP0(h, logger=logger)
    >>> hint_MSIRP(h, logger=logger)
    >>> m.point
    12
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      0: Implicit zero for RP0 used at opcode index 0 in test
      3: Extra index 3 in PUSH opcode index 0 in test
      7: Extra index 0 in PUSH opcode index 0 in test
      12: Extra index 2 in PUSH opcode index 0 in test
    >>> hint_MSIRP(h, logger=logger)
    MSIRP_test - CRITICAL - Stack underflow in test (PC 3).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    distance = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if distance is None:
        state.assign('pc', doNotProceedPC)
        return
    
    distance = distance.changedBasis(1)
    point = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if point is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory', 2)
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = history[0]
    
    if (None not in distance) and any(n < -16384 or n >= 16384 for n in distance):
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "MSIRP opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
    
    elif self._zoneCheck("MSIRP", (0, 1), logger):
        zp0, zp1 = gs.zonePointer0, gs.zonePointer1
        
        v = [
          (zp1, point, True),
          (zp0, toCollection(gs.referencePoint0), False)]
        
        if self._pointCheck(
          "MSIRP",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory(
              'pointMoved',
              (zp1, point),
              history)
            
            refHist = self._synthRefHistory(0)
            
            state.statistics.addHistory(
              'point',
              (zp0, gs.referencePoint0),
              refHist)
            
            if kwArgs.get('setRP0', False):
                state.assignDeep('graphicsState', 'referencePoint0', point)
                state.refPtHistory[0] = history
                state.changed('refPtHistory')
                
                if 'fdefEntryStack' in kwArgs:
                    # We only note graphicsState effects when a
                    # FDEF stack is available
                    
                    state.statistics.noteGSEffect(
                      tuple(kwArgs['fdefEntryStack']),
                      state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'MSIRP')
        fatObj.notePop('pointIndex', 'MSIRP')
    
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
