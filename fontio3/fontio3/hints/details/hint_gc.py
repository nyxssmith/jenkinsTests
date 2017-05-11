#
# hint_gc.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the GC opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import Collection
from fontio3.triple.triple import Triple

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_GC(self, **kwArgs):
    """
    GC: Get coordinate, opcodes 0x46-0x47
    
    >>> logger = utilities.makeDoctestLogger("GC_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(7)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["GC[current]"]))
    >>> hint_GC(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    7
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      7: Extra index 0 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    Ranges: [(*, *, 1, phase=0)]
    >>> hint_GC(h, logger=logger)
    GC_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    point = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if point is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("GC", (2,), logger):
        zp2 = state.graphicsState.zonePointer2
        
        if self._pointCheck(
          "GC",
          [(zp2, point, False)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('point', (zp2, point), history)
    
    state.append('stack', Collection([Triple(None, None, 1)]))
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [history]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'GC')
        fatObj.notePush()
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints import opcode_tt
    from fontio3.hints.common import nameToOpcodeMap
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
