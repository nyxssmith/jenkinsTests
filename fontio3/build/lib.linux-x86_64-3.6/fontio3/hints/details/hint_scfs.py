#
# hint_scfs.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SCFS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SCFS(self, **kwArgs):
    """
    SCFS: Set coordinate from stack, opcode 0x48
    
    >>> logger = utilities.makeDoctestLogger("SCFS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(128, 16, -64)
    >>> hint_SCFS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    16
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      16: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_SCFS(h, logger=logger)
    SCFS_test - CRITICAL - Stack underflow in test (PC 1).
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
    
    history = self._popRemove(state, 'pushHistory', 2, **kwArgs)
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = history[0]
    
    if (None not in distance) and any(n < -16384 or n >= 16384 for n in distance):
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SCFS opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
    
    elif self._zoneCheck("SCFS", (2,), logger):
        
        if self._pointCheck(
          "SCFS",
          [(gs.zonePointer2, point, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory(
              'pointMoved',
              (gs.zonePointer2, point),
              history)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SCFS')
        fatObj.notePop('pointIndex', 'SCFS')
    
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
