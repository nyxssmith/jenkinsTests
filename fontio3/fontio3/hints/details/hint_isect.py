#
# hint_isect.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ISECT opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ISECT(self, **kwArgs):
    """
    ISECT: Move point to intersection of two lines, opcode 0x0F
    
    >>> logger = utilities.makeDoctestLogger("ISECT_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(3, 15, 6, 11, 2)
    >>> hint_ISECT(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    15
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      2: Extra index 4 in PUSH opcode index 0 in test
      3: Extra index 0 in PUSH opcode index 0 in test
      6: Extra index 2 in PUSH opcode index 0 in test
      11: Extra index 3 in PUSH opcode index 0 in test
      15: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_ISECT(h, logger=logger)
    ISECT_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    points = self._popRemove(state, 'stack', 5, coerceToCollection=True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = self._popRemove(state, 'pushHistory', 5)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    zones = [
      gs.zonePointer2,
      gs.zonePointer1,
      gs.zonePointer1,
      gs.zonePointer0,
      gs.zonePointer0]
    
    if self._zoneCheck("ISECT", (0, 1, 2), logger):
        v = [(zones[i], p, i == 0) for i, p in enumerate(points)]
        
        if self._pointCheck(
          "ISECT",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, p in enumerate(points):
                state.statistics.addHistory(
                  'pointMoved',
                  (zones[i], p),
                  histories[i])
    
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        for p in points:
            fatObj.notePop('pointIndex', 'ISECT')

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
