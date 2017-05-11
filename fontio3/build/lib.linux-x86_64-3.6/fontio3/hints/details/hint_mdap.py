#
# hint_mdap.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MDAP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MDAP(self, **kwArgs):
    """
    MDAP: Move direct absolute point, opcodes 0x2E-0x2F
    
    >>> logger = utilities.makeDoctestLogger("MDAP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(12)
    >>> pp.PP().mapping_deep_smart(h.state.refPtHistory, lambda x: False)
    0: (no data)
    1: (no data)
    2: (no data)
    >>> hint_MDAP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    12
    >>> pp.PP().mapping_deep_smart(h.state.refPtHistory, lambda x: False)
    0: Extra index 0 in PUSH opcode index 0 in test
    1: Extra index 0 in PUSH opcode index 0 in test
    2: (no data)
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      12: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_MDAP(h, logger=logger)
    MDAP_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    p = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if p is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("MDAP", (0,), logger):
        zp0 = gs.zonePointer0
        
        if self._pointCheck(
          "MDAP",
          [(zp0, p, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('pointMoved', (zp0, p), history)
            state.assignDeep('graphicsState', 'referencePoint0', p)
            state.assignDeep('graphicsState', 'referencePoint1', p)
            state.refPtHistory[0] = state.refPtHistory[1] = history
            state.changed('refPtHistory')
            
            if 'fdefEntryStack' in kwArgs:
                # We only note graphicsState effects when a
                # FDEF stack is available
                
                state.statistics.noteGSEffect(
                  tuple(kwArgs['fdefEntryStack']),
                  state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'MDAP')
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
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
