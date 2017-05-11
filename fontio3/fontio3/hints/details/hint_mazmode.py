#
# hint_mazmode.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MAZMODE opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MAZMODE(self, **kwArgs):
    """
    MAZMODE: Edge mode, opcode 0xA5
    
    >>> logger = utilities.makeDoctestLogger("MAZMODE_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(10, 12, 29, 2)
    >>> hint_MAZMODE(h, logger=logger)
    >>> len(h.state.stack), len(h.state.pushHistory)
    (1, 1)
    >>> hint_MAZMODE(h, logger=logger)
    MAZMODE_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    
    if self._popRemove(state, 'stack', 3) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory', 3) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('mazMode', 'MAZMODE')
        fatObj.notePop('ppem', 'MAZMODE')
        fatObj.notePop('ppem', 'MAZMODE')
    
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
