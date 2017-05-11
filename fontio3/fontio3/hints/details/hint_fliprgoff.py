#
# hint_fliprgoff.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the FLIPRGOFF opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_FLIPRGOFF(self, **kwArgs):
    """
    FLIPRGOFF: Set a range of points to off-curve, opcode 0x82
    
    >>> logger = utilities.makeDoctestLogger("FLIPRGOFF_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0, Collection([Triple(5, 15, 2)]), 9, 7, 2, 6)
    >>> hint_FLIPRGOFF(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    6
    >>> hint_FLIPRGOFF(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    9
    >>> hint_FLIPRGOFF(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    13
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      0: Extra index 0 in PUSH opcode index 0 in test
      2: Extra index 4 in PUSH opcode index 0 in test
      5: Extra index 1 in PUSH opcode index 0 in test
      6: Extra index 5 in PUSH opcode index 0 in test
      7:
        Extra index 1 in PUSH opcode index 0 in test
        Extra index 3 in PUSH opcode index 0 in test
      9:
        Extra index 1 in PUSH opcode index 0 in test
        Extra index 2 in PUSH opcode index 0 in test
      11: Extra index 1 in PUSH opcode index 0 in test
      13: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_FLIPRGOFF(h, logger=logger)
    FLIPRGOFF_test - CRITICAL - Stack underflow in test (PC 3).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    points = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = self._popRemove(state, 'pushHistory', 2)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("FLIPRGOFF", (0,), logger):
        zp0 = state.graphicsState.zonePointer0
        
        if self._pointCheck(
          "FLIPRGOFF",
          ((zp0, p, True) for p in points),
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, p in enumerate(points):
                state.statistics.addHistory(
                  'pointMoved',
                  (zp0, p),
                  histories[i])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        for p in points:
            fatObj.notePop('pointIndex', 'FLIPRGOFF')
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.triple.collection import Collection
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
