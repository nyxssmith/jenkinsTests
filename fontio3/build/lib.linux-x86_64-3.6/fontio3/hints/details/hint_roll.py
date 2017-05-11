#
# hint_roll.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the ROLL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_ROLL(self, **kwArgs):
    """
    ROLL: Roll top three stack positions, opcode 0x8A
    
    >>> logger = utilities.makeDoctestLogger("ROLL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(10, 3, 6, 9)
    >>> hint_ROLL(h, logger=logger)
    >>> h.state.stack
    [10, 6, 9, 3]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 3 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    >>> del h.state.stack[-2:]
    >>> h.state.changed('stack')
    >>> del h.state.pushHistory[-2:]
    >>> h.state.changed('pushHistory')
    >>> hint_ROLL(h, logger=logger)
    ROLL_test - ERROR - ROLL opcode in test (PC 1) does not have at least three stack elements to work with.
    """
    
    state = self.state
    stack = state.stack
    ph = state.pushHistory
    logger = self._getLogger(**kwArgs)
    
    if len(stack) < 3:
        logger.error((
          'E6030',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "ROLL opcode in %s (PC %d) does not have at least three "
          "stack elements to work with."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    stack[-3:] = [stack[-2], stack[-1], stack[-3]]
    state.changed('stack')
    ph[-3:] = [ph[-2], ph[-1], ph[-3]]
    state.changed('pushHistory')
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.hint_mindex(3)

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
