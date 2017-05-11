#
# hint_ip.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the IP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_IP(self, **kwArgs):
    """
    IP: Interpolate point, opcode 0x39
    
    >>> logger = utilities.makeDoctestLogger("IP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(3, 4, 6, 7, 2, 12, 3, 5)
    >>> m = h.state.statistics.maxima
    >>> h.state.assignDeep('graphicsState', 'loop', 4)
    >>> hint_IP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> m.point
    12
    >>> h.state.graphicsState.loop
    1
    >>> h.state.assignDeep('graphicsState', 'loop', 2)
    >>> h.state.assignDeep('graphicsState', 'referencePoint2', 14)
    >>> hint_IP(h, logger=logger)
    >>> m.point
    14
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      0:
        Implicit zero for RP1 used at opcode index 0 in test
        Implicit zero for RP2 used at opcode index 0 in test
        Implicit zero for RP1 used at opcode index 1 in test
      2: Extra index 4 in PUSH opcode index 0 in test
      3: Extra index 6 in PUSH opcode index 0 in test
      5: Extra index 7 in PUSH opcode index 0 in test
      6: Extra index 2 in PUSH opcode index 0 in test
      7: Extra index 3 in PUSH opcode index 0 in test
      12: Extra index 5 in PUSH opcode index 0 in test
      14: Implicit zero for RP2 used at opcode index 1 in test
    >>> h.state.assignDeep('graphicsState', 'loop', 3)
    >>> hint_IP(h, logger=logger)
    IP_test - CRITICAL - Stack underflow in test (PC 2).
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
      coerceToList=True)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("IP", (0, 1, 2), logger):
        zp0 = gs.zonePointer0
        zp1 = gs.zonePointer1
        zp2 = gs.zonePointer2
        v = [(zp2, p, True) for p in points]
        v.append((zp0, toCollection(gs.referencePoint1), False))
        v.append((zp1, toCollection(gs.referencePoint2), False))
        
        if self._pointCheck("IP", v, logger, kwArgs.get('extraInfo', {})):
            for i, p in enumerate(points):
                state.statistics.addHistory(
                  'pointMoved',
                  (gs.zonePointer2, p),
                  histories[i])
            
            rh1 = self._synthRefHistory(1)
            
            state.statistics.addHistory(
              'point',
              (gs.zonePointer0, gs.referencePoint1),
              rh1)
            
            rh2 = self._synthRefHistory(2)
            
            state.statistics.addHistory(
              'point',
              (gs.zonePointer1, gs.referencePoint2),
              rh2)
    
    state.assignDeep('graphicsState', 'loop', 1)
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        for p in points:
            fatObj.notePop('pointIndex', 'IP')

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
