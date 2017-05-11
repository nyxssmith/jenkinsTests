#
# hint_flippt.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the FLIPPT opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_FLIPPT(self, **kwArgs):
    """
    FLIPPT: Switch between on-curve and off-curve, opcode 0x80
    
    >>> logger = utilities.makeDoctestLogger("FLIPPT_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(2, 12, 3, 5)
    >>> h.state.assignDeep('graphicsState', 'loop', 4)
    >>> hint_FLIPPT(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    12
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      2: Extra index 0 in PUSH opcode index 0 in test
      3: Extra index 2 in PUSH opcode index 0 in test
      5: Extra index 3 in PUSH opcode index 0 in test
      12: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_FLIPPT(h, logger=logger)
    FLIPPT_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    gs = state.graphicsState
    
    points = self._popRemove(
      state,
      'stack',
      gs.loop,
      coerceToCollection = True,
      coerceToList = True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = self._popRemove(
      state,
      'pushHistory',
      gs.loop,
      coerceToList = True)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("FLIPPT", (0,), logger):
        zp0 = gs.zonePointer0
        
        if self._pointCheck(
          "FLIPPT",
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
            fatObj.notePop('pointIndex', 'FLIPPT')
    
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
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
