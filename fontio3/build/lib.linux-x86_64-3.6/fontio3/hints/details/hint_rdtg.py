#
# hint_rdtg.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the RDTG opcode.
"""

# Other imports
from fontio3.hints.graphicsstate import one26Dot6, zero26Dot6

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_RDTG(self, **kwArgs):
    """
    RDTG: Set round mode to "round down to grid", opcode 0x7D
    
    >>> logger = utilities.makeDoctestLogger("RDTG_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.state.graphicsState.roundState
    [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
    >>> hint_RDTG(h, logger=logger)
    >>> h.state.graphicsState.roundState
    [Singles: [1.0], Singles: [0.0], Singles: [0.0]]
    """
    
    state = self.state
    gs = state.graphicsState
    rs = gs.roundState
    need = [one26Dot6, zero26Dot6, zero26Dot6]
    
    if rs != need:
        rs[:] = need
        gs.changed('roundState')
        state.changed('graphicsState')
    
    if 'fdefEntryStack' in kwArgs:
        # We only note graphicsState effects when a FDEF stack is available
        
        state.statistics.noteGSEffect(
          tuple(kwArgs['fdefEntryStack']),
          state.pc + self.ultDelta)
    
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
