#
# hint_szps.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SZPS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SZPS(self, **kwArgs):
    """
    SZPS: Set all three zone pointers, opcode 0x16
    
    >>> logger = utilities.makeDoctestLogger("SZPS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0)
    >>> gs = h.state.graphicsState
    >>> gs.zonePointer0, gs.zonePointer1, gs.zonePointer2
    (1, 1, 1)
    >>> hint_SZPS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> gs.zonePointer0, gs.zonePointer1, gs.zonePointer2
    (0, 0, 0)
    >>> h.state.statistics.pprint(keys=('zone',))
    History for SHZ zones:
      0: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_SZPS(h, logger=logger)
    SZPS_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    zone = self._popRemove(state, 'stack')
    
    if zone is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    state.assignDeep('graphicsState', 'zonePointer0', zone)
    state.assignDeep('graphicsState', 'zonePointer1', zone)
    state.assignDeep('graphicsState', 'zonePointer2', zone)
    
    if self._zoneCheck("SZPS", (0, 1, 2), logger):
        state.statistics.addHistory('zone', zone, history)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a
            # FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('zoneIndex', 'SZPS')
    
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
