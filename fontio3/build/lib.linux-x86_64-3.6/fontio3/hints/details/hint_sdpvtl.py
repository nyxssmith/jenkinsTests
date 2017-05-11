#
# hint_sdpvtl.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SDPVTL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SDPVTL(self, **kwArgs):
    """
    SDPVTL: Set dual projection vector to line, opcodes 0x86-0x87
    
    >>> logger = utilities.makeDoctestLogger("SDPVTL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(14, 3, 11)
    >>> hint_SDPVTL(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    11
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      3: Extra index 1 in PUSH opcode index 0 in test
      11: Extra index 2 in PUSH opcode index 0 in test
    >>> hint_SDPVTL(h, logger=logger)
    SDPVTL_test - CRITICAL - Stack underflow in test (PC 1).
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
    
    if self._zoneCheck("SDPVTL", (1, 2), logger):
        zones = (gs.zonePointer1, gs.zonePointer2)
        
        if self._pointCheck(
          "SDPVTL",
          ((zones[i], p, False) for i, p in enumerate(points)),
          logger,
          kwArgs.get('extraInfo', {})):
            
            for i, p in enumerate(points):
                
                state.statistics.addHistory(
                  'point',
                  (zones[i], p),
                  history[i])
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'SDPVTL')
        fatObj.notePop('pointIndex', 'SDPVTL')
    
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
