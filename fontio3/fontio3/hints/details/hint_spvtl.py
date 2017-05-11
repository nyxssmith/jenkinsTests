#
# hint_spvtl.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SPVTL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SPVTL(self, **kwArgs):
    """
    SPVTL: Set projection vector to line, opcodes 0x06-0x07
    
    >>> logger = utilities.makeDoctestLogger("SPVTL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(14, 3, 11)
    >>> hint_SPVTL(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    11
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      3: Extra index 1 in PUSH opcode index 0 in test
      11: Extra index 2 in PUSH opcode index 0 in test
    >>> hint_SPVTL(h, logger=logger)
    SPVTL_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection = True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    p1, p2 = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h1, h2 = t
    
    if self._zoneCheck("SPVTL", (1, 2), logger):
        v = [(gs.zonePointer1, p1, False), (gs.zonePointer2, p2, False)]
        
        if self._pointCheck(
          "SPVTL",
          v,
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('point', (gs.zonePointer1, p1), h1)
            state.statistics.addHistory('point', (gs.zonePointer2, p2), h2)
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'SPVTL')
        fatObj.notePop('pointIndex', 'SPVTL')
    
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
