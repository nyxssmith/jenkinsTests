#
# hint_svtca.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SVTCA opcode.
"""

# Other imports
from fontio3.hints.graphicsstate import xAxis, yAxis

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SVTCA(self, **kwArgs):
    """
    SVTCA: Set vectors to coordinate axis, opcodes 0x00-0x01
    
    >>> logger = utilities.makeDoctestLogger("SVTCA_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> (h.state.graphicsState.freedomVector,
    ...   h.state.graphicsState.projectionVector)
    ((Singles: [1], Singles: [0]), (Singles: [1], Singles: [0]))
    >>> hint_SVTCA(h, toX=False, logger=logger)
    >>> (h.state.graphicsState.freedomVector,
    ...   h.state.graphicsState.projectionVector)
    ((Singles: [0], Singles: [1]), (Singles: [0], Singles: [1]))
    """
    
    state = self.state
    
    if kwArgs.get('toX', True):
        t = xAxis
    else:
        t = yAxis
    
    state.assignDeep('graphicsState', 'freedomVector', t)
    state.assignDeep('graphicsState', 'projectionVector', t)
    
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
