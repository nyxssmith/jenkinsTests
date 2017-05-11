#
# hint_shpix.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SHPIX opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SHPIX(self, **kwArgs):
    """
    SHPIX: Shift points by pixels, opcode 0x38
    
    >>> logger = utilities.makeDoctestLogger("SHPIX_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(4, 19, 3, -128, 3)
    >>> hint_sloop.hint_SLOOP(h, logger=logger)
    >>> hint_SHPIX(h, logger=logger)
    >>> h.state.statistics.maxima.pprint(keys=('point', 'stack'))
    Highest point index in the glyph zone: 19
    Deepest stack attained: 5
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      3: Extra index 2 in PUSH opcode index 0 in test
      4: Extra index 0 in PUSH opcode index 0 in test
      19: Extra index 1 in PUSH opcode index 0 in test
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> hint_SHPIX(h, logger=logger)
    SHPIX_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    distance = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if distance is None:
        state.assign('pc', doNotProceedPC)
        return
    
    distance = distance.changedBasis(1)
    
    points = self._popRemove(
      state,
      'stack',
      gs.loop,
      coerceToList = True,
      coerceToCollection = True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = self._popRemove(state, 'pushHistory', gs.loop + 1)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = histories[:-1]
    
    if (None not in distance) and any(n < -16384 or n >= 16384 for n in distance):
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SHPIX opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
    
    elif self._zoneCheck("SHPIX", (2,), logger):
        zp2 = gs.zonePointer2
        
        if self._pointCheck(
          "SHPIX",
          [(zp2, p, True) for p in points],
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, p in enumerate(points):
                
                state.statistics.addHistory(
                  'pointMoved',
                  (zp2, p),
                  histories[i])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'SHPIX')
        
        for p in points:
            fatObj.notePop('pointIndex', 'SHPIX')
    
    state.assignDeep('graphicsState', 'loop', 1)
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints.details import hint_sloop
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
