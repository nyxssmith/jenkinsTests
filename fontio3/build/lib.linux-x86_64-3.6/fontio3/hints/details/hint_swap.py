#
# hint_swap.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SWAP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SWAP(self, **kwArgs):
    """
    SWAP: Swap top two stack elements, opcode 0x23
    
    >>> logger = utilities.makeDoctestLogger("SWAP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(9, 4, -1)
    >>> hint_SWAP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack
    [9, -1, 4]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> hint_SWAP(h, logger=logger)
    SWAP_test - ERROR - SWAP opcode in test (PC 1) does not have at least two stack elements to work with.
    """
    
    state = self.state
    stack = state.stack
    ph = state.pushHistory
    logger = self._getLogger(**kwArgs)
    
    if len(stack) < 2:
        logger.error((
          'E6030',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SWAP opcode in %s (PC %d) does not have at least two "
          "stack elements to work with."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    stack[-2:] = [stack[-1], stack[-2]]
    state.changed('stack')
    ph[-2:] = [ph[-1], ph[-2]]
    state.changed('pushHistory')
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.hint_mindex(2)

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
