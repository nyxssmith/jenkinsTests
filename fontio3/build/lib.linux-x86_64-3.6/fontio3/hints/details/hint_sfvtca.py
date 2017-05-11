#
# hint_sfvtca.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SFVTCA opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.graphicsstate import xAxis, yAxis

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SFVTCA(self, **kwArgs):
    """
    SFVTCA: Set freedom vector to coordinate axis, opcodes 0x04-0x05
    
    >>> logger = utilities.makeDoctestLogger("SFVTCA_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.state.graphicsState.freedomVector
    (Singles: [1], Singles: [0])
    >>> hint_SFVTCA(h, toX=False, logger=logger)
    >>> h.state.graphicsState.freedomVector
    (Singles: [0], Singles: [1])
    >>> hint_SFVTCA(h, toX=True, logger=logger)
    >>> h.state.graphicsState.freedomVector
    (Singles: [1], Singles: [0])
    """
    
    state = self.state
    toX = kwArgs.get('toX', True)
    
    state.assignDeep(
      'graphicsState',
      'freedomVector',
      (xAxis if toX else yAxis))
    
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
