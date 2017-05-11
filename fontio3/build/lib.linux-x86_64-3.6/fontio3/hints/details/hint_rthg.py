#
# hint_rthg.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the RTHG opcode.
"""

# Other imports
from fontio3.hints.graphicsstate import half26Dot6, one26Dot6

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_RTHG(self, **kwArgs):
    """
    RTHG: Set round mode to "round to half grid", opcode 0x19
    
    >>> logger = utilities.makeDoctestLogger("RTHG_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.state.graphicsState.roundState
    [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
    >>> hint_RTHG(h, logger=logger)
    >>> h.state.graphicsState.roundState
    [Singles: [1.0], Singles: [0.5], Singles: [0.5]]
    """
    
    state = self.state
    gs = state.graphicsState
    rs = gs.roundState
    need = [one26Dot6, half26Dot6, half26Dot6]
    
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
