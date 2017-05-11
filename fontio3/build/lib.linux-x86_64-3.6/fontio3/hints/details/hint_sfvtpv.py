#
# hint_sfvtpv.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SFVTPV opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SFVTPV(self, **kwArgs):
    """
    SFVTPV: Set freedom vector to projection vector, opcode 0x0E
    
    >>> logger = utilities.makeDoctestLogger("SFVTPV_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.state.graphicsState.projectionVector = yAxis
    >>> (h.state.graphicsState.freedomVector,
    ...   h.state.graphicsState.projectionVector)
    ((Singles: [1], Singles: [0]), (Singles: [0], Singles: [1]))
    >>> hint_SFVTPV(h, logger=logger)
    >>> (h.state.graphicsState.freedomVector,
    ...   h.state.graphicsState.projectionVector)
    ((Singles: [0], Singles: [1]), (Singles: [0], Singles: [1]))
    """
    
    state = self.state
    gs = state.graphicsState
    state.assignDeep('graphicsState', 'freedomVector', gs.projectionVector)
    
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
    from fontio3.hints.graphicsstate import yAxis
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
