#
# hint_mdrp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MDRP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MDRP(self, **kwArgs):
    """
    MDRP: Move direct relative point, opcodes 0xC0-0xDF
    
    >>> logger = utilities.makeDoctestLogger("MDRP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(6, 12)
    >>> pp.PP().mapping_deep_smart(h.state.refPtHistory, lambda x: False)
    0: (no data)
    1: (no data)
    2: (no data)
    >>> m = h.state.statistics.maxima
    >>> hint_MDRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    12
    >>> h.state.assignDeep('graphicsState', 'referencePoint0', 16)
    >>> hint_MDRP(h, logger=logger)
    >>> m.point
    16
    >>> pp.PP().mapping_deep_smart(h.state.refPtHistory, lambda x: False)
    0: (no data)
    1: (no data)
    2: Extra index 0 in PUSH opcode index 0 in test
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      0: Implicit zero for RP0 used at opcode index 0 in test
      6: Extra index 0 in PUSH opcode index 0 in test
      12: Extra index 1 in PUSH opcode index 0 in test
      16: Implicit zero for RP0 used at opcode index 1 in test
    >>> hint_MDRP(h, logger=logger)
    MDRP_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    gs = state.graphicsState
    rph = state.refPtHistory
    logger = self._getLogger(**kwArgs)
    p = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if p is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("MDRP", (0, 1), logger):
        zp1 = gs.zonePointer1
        
        v = [
          (zp1, p, True),
          (gs.zonePointer0, toCollection(gs.referencePoint0), False)]
        
        if self._pointCheck(
          "MDRP",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('pointMoved', (zp1, p), history)
            refHist = self._synthRefHistory(0)
            
            state.statistics.addHistory(
              'point',
              (gs.zonePointer0, gs.referencePoint0),
              refHist)
            
            state.assignDeep(
              'graphicsState',
              'referencePoint1',
              gs.referencePoint0)
            
            state.assignDeep('graphicsState', 'referencePoint2', p)
            rph[1] = rph[0]
            rph[2] = history
            state.changed('refPtHistory')
            
            if kwArgs.get('setRP0', False):
                state.assignDeep('graphicsState', 'referencePoint0', p)
                rph[0] = history
                state.changed('refPtHistory')
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'MDRP')
    
    state.assign('pc', state.pc + 1)

def hint_MDRP_badColor(self, **kwArgs):
    state = self.state
    logger = self._getLogger(**kwArgs)
    self._popRemove(state, 'stack')
    self._popRemove(state, 'pushHistory')
    
    logger.error((
      'E6027',
      (self.ultParent.infoString, state.pc + self.ultDelta),
      "MDRP opcode in %s (PC %d) has invalid color distance (3)."))
    
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
    from fontio3.utilities import pp
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
