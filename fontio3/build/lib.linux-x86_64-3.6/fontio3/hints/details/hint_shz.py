#
# hint_shz.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SHZ opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SHZ(self, **kwArgs):
    """
    SHZ: Shift zone, opcodes 0x36-0x37
    
    >>> logger = utilities.makeDoctestLogger("SHZ_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(1, 0, 12, 8)
    >>> hint_srp1.hint_SRP1(h, logger=logger)
    >>> hint_srp2.hint_SRP2(h, logger=logger)
    >>> hint_SHZ(h, refPt=1, logger=logger)
    >>> hint_SHZ(h, refPt=2, logger=logger)
    >>> h.state.statistics.maxima.pprint(keys=('point', 'stack'))
    Highest point index in the glyph zone: 12
    Deepest stack attained: 4
    >>> h.state.statistics.pprint(keys=('point', 'zone'))
    History for outline points (glyph zone):
      8: Extra index 3 in PUSH opcode index 0 in test
      12: Extra index 2 in PUSH opcode index 0 in test
    History for SHZ zones:
      0: Extra index 1 in PUSH opcode index 0 in test
      1: Extra index 0 in PUSH opcode index 0 in test
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> hint_SHZ(h, logger=logger)
    SHZ_test - CRITICAL - Stack underflow in test (PC 4).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    zone = self._popRemove(state, 'stack')
    
    if zone is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("SHZ", (zone,), logger):
        state.statistics.addHistory('zone', zone, history)
        
        if kwArgs.get('refPt', 1) == 1:
            if self._pointCheck(
              "SHZ",
              [(gs.zonePointer0, toCollection(gs.referencePoint1), False)],
              logger,
              kwArgs.get('extraInfo', {})):
                
                state.statistics.addHistory(
                  'point',
                  (gs.zonePointer0, gs.referencePoint1),
                  self._synthRefHistory(1))
        
        else:
            if self._pointCheck(
              "SHZ",
              [(gs.zonePointer1, toCollection(gs.referencePoint2), False)],
              logger,
              kwArgs.get('extraInfo', {})):
                
                state.statistics.addHistory(
                  'point',
                  (gs.zonePointer1, gs.referencePoint2),
                  self._synthRefHistory(2))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('zoneIndex', 'SHZ')
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints.details import hint_srp1, hint_srp2
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
