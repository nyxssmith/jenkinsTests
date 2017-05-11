#
# hint_flipoff.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the FLIPOFF opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_FLIPOFF(self, **kwArgs):
    """
    FLIPOFF: Set autoflip to off, opcode 0x4E
    
    >>> logger = utilities.makeDoctestLogger("FLIPOFF_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.state.graphicsState.autoFlip
    True
    >>> hint_FLIPOFF(h, logger=logger)
    >>> h.state.graphicsState.autoFlip
    False
    """
    
    state = self.state
    state.assignDeep('graphicsState', 'autoFlip', False)
    
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
