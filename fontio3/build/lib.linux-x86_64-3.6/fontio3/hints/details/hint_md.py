#
# hint_md.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MD opcode.
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

def hint_MD(self, **kwArgs):
    """
    MD: Measure distance, opcodes 0x49-0x4A
    
    >>> logger = utilities.makeDoctestLogger("MD_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(6, 10)
    >>> h.append(
    ...   opcode_tt.Opcode_nonpush(nameToOpcodeMap["MD[gridfitted]"]))
    >>> hint_MD(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    10
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      6: Extra index 0 in PUSH opcode index 0 in test
      10: Extra index 1 in PUSH opcode index 0 in test
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode MD[gridfitted] at index 0 in test, with inputs:
      Extra index 0 in PUSH opcode index 0 in test
      Extra index 1 in PUSH opcode index 0 in test
    >>> hint_MD(h, logger=logger)
    MD_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    points = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if points is None:
        state.assign('pc', doNotProceedPC)
        return
    
    histories = self._popRemove(state, 'pushHistory', 2)
    
    if histories is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("MD", (0, 1), logger):
        v = [
          (gs.zonePointer0, points[0], False),
          (gs.zonePointer1, points[1], False)]
        
        if self._pointCheck("MD", v, logger, kwArgs.get('extraInfo', {})):
            for i, t in enumerate(v):
                state.statistics.addHistory('point', t, histories[i])
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = histories))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'MD')
        fatObj.notePop('pointIndex', 'MD')
        fatObj.notePush()
    
    state.append('stack', Collection([Triple(None, None, 1)]))
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
    from fontio3.utilities import pp
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
