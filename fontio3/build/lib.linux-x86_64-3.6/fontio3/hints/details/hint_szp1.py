#
# hint_szp1.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SZP1 opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SZP1(self, **kwArgs):
    """
    SZP1: Set zone pointer 1, opcode 0x14
    
    >>> logger = utilities.makeDoctestLogger("SZP1_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0)
    >>> hint_SZP1(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.zonePointer1
    0
    >>> h.state.statistics.pprint(keys=('zone',))
    History for SHZ zones:
      0: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_SZP1(h, logger=logger)
    SZP1_test - CRITICAL - Stack underflow in test (PC 1).
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
    
    state.assignDeep('graphicsState', 'zonePointer1', zone)
    
    if self._zoneCheck("SZP1", (1,), logger):
        state.statistics.addHistory('zone', zone, history)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a
            # FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('zoneIndex', 'SZP1')
    
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
