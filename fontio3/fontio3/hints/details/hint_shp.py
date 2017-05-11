#
# hint_shp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SHP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SHP(self, **kwArgs):
    """
    SHP: Shift points, opcodes 0x32-0x33
    
    >>> logger = utilities.makeDoctestLogger("SHP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(11, 4, 2, 6, 5, 2, 10, 8)
    >>> hint_srp1.hint_SRP1(h, logger=logger)
    >>> hint_srp2.hint_SRP2(h, logger=logger)
    >>> hint_sloop.hint_SLOOP(h, logger=logger)
    >>> hint_SHP(h, refPt=1, logger=logger)
    >>> hint_sloop.hint_SLOOP(h, logger=logger)
    >>> hint_SHP(h, refPt=2, logger=logger)
    >>> h.state.statistics.maxima.pprint(keys=('point', 'stack'))
    Highest point index in the glyph zone: 11
    Deepest stack attained: 8
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      4: Extra index 1 in PUSH opcode index 0 in test
      5: Extra index 4 in PUSH opcode index 0 in test
      6: Extra index 3 in PUSH opcode index 0 in test
      8: Extra index 7 in PUSH opcode index 0 in test
      10: Extra index 6 in PUSH opcode index 0 in test
      11: Extra index 0 in PUSH opcode index 0 in test
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> hint_SHP(h, logger=logger)
    SHP_test - CRITICAL - Stack underflow in test (PC 6).
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
    
    histories = self._popRemove(
      state,
      'pushHistory',
      gs.loop,
      coerceToList = True)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("SHP", (0, 1, 2), logger):
        v = [(gs.zonePointer2, p, True) for p in points]
        v.append((gs.zonePointer0, toCollection(gs.referencePoint1), False))
        v.append((gs.zonePointer1, toCollection(gs.referencePoint2), False))
        
        if self._pointCheck(
          "SHP",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, p in enumerate(points):
                
                state.statistics.addHistory(
                  'pointMoved',
                  (gs.zonePointer2, p),
                  histories[i])
            
            if kwArgs.get('refPt', 1) == 1:
                
                state.statistics.addHistory(
                  'point',
                  (gs.zonePointer0, gs.referencePoint1),
                  self._synthRefHistory(1))
            
            else:
                
                state.statistics.addHistory(
                  'point',
                  (gs.zonePointer1, gs.referencePoint2),
                  self._synthRefHistory(2))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        for p in points:
            fatObj.notePop('pointIndex', 'SHP')
    
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
    from fontio3.hints.details import hint_sloop, hint_srp1, hint_srp2
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
