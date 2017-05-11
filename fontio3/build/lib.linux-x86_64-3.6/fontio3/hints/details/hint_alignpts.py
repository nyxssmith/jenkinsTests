#
# hint_alignpts.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ALIGNPTS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ALIGNPTS(self, **kwArgs):
    """
    ALIGNPTS: Align points with each other, opcode 0x27
    
    >>> logger = utilities.makeDoctestLogger("ALIGNPTS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(7, 8)
    >>> hint_ALIGNPTS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      7: Extra index 0 in PUSH opcode index 0 in test
      8: Extra index 1 in PUSH opcode index 0 in test
    >>> h = _testingState(4, 11, 10, 5, 6)
    >>> hint_ALIGNPTS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m = h.state.statistics.maxima
    >>> m.point, m.tzPoint
    (6, -1)
    >>> h.state.assignDeep('graphicsState', 'zonePointer0', 0)
    >>> hint_ALIGNPTS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point, m.tzPoint
    (11, 10)
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> hint_ALIGNPTS(h, logger=logger)
    ALIGNPTS_test - CRITICAL - Stack underflow in test (PC 2).
    >>> h = _testingState(100, -3)
    >>> hint_ALIGNPTS(h, logger=logger)
    ALIGNPTS_test - WARNING - ALIGNPTS opcode in test (PC 0) is hinting point 100, which does not exist for this glyph.
    ALIGNPTS_test - ERROR - ALIGNPTS opcode in test (PC 0) refers to negative or non-integer point index -3.
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    points = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory', 2)
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    z0 = gs.zonePointer0
    z1 = gs.zonePointer1
    okToProceed = self._zoneCheck("ALIGNPTS", (0, 1), logger)
    
    if okToProceed:
        okToProceed = (
          self._pointCheck(
            "ALIGNPTS",
            ((z1, points[0], True), (z0, points[1], True)),
            logger,
            kwArgs.get('extraInfo', {})) and
          okToProceed)
    
    if okToProceed:
        state.statistics.addHistory(
          'pointMoved',
          (z1, points[0]),
          history[0])
        
        state.statistics.addHistory(
          'pointMoved',
          (z0, points[1]),
          history[1])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'ALIGNPTS')
        fatObj.notePop('pointIndex', 'ALIGNPTS')
    
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
