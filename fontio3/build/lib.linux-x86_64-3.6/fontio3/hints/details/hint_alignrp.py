#
# hint_alignrp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ALIGNRP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ALIGNRP(self, **kwArgs):
    """
    ALIGNRP: Align to reference point, opcode 0x3C
    
    >>> logger = utilities.makeDoctestLogger("ALIGNRP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(6, 9, 5)
    >>> h.state.assignDeep('graphicsState', 'loop', 3)
    >>> hint_ALIGNRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      0: Implicit zero for RP0 used at opcode index 0 in test
      5: Extra index 2 in PUSH opcode index 0 in test
      6: Extra index 0 in PUSH opcode index 0 in test
      9: Extra index 1 in PUSH opcode index 0 in test
    >>> h = _testingState(Collection([Triple(11, 31, 2)]), 4, 6, 3)
    >>> h.state.assignDeep('graphicsState', 'loop', 2)
    >>> m = h.state.statistics.maxima
    >>> hint_ALIGNRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    6
    >>> h.state.graphicsState.loop
    1
    >>> h.state.assignDeep('graphicsState', 'referencePoint0', 19)
    >>> hint_ALIGNRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    19
    >>> hint_ALIGNRP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    29
    >>> hint_ALIGNRP(h, logger=logger)
    ALIGNRP_test - CRITICAL - Stack underflow in test (PC 3).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    
    points = self._popRemove(
      state,
      'stack',
      gs.loop,
      coerceToCollection = True,
      coerceToList = True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(
      state,
      'pushHistory',
      gs.loop,
      coerceToList = True)
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    z0 = gs.zonePointer0
    z1 = gs.zonePointer1
    okToProceed = self._zoneCheck("ALIGNRP", (0, 1), logger)
    
    if okToProceed:
        v = [(z1, p, True) for p in points]
        v.append((z0, toCollection(gs.referencePoint0), False))
        
        okToProceed = (
          self._pointCheck(
            "ALIGNRP",
            v,
            logger,
            kwArgs.get('extraInfo', {})) and
          okToProceed)
    
    if okToProceed:
        for i, p in enumerate(points):
            state.statistics.addHistory(
              'pointMoved',
              (z1, p),
              history[i])
        
        refHist = self._synthRefHistory(0)
        
        state.statistics.addHistory(
          'point',
          (z0, gs.referencePoint0),
          refHist)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        for p in points:
            fatObj.notePop('pointIndex', 'ALIGNRP')
    
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
    from fontio3.triple.collection import Collection, toCollection
    from fontio3.triple.triple import Triple
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
