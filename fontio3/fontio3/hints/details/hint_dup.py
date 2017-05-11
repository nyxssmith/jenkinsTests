#
# hint_dup.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DUP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DUP(self, **kwArgs):
    """
    DUP: Duplicate top stack element, opcode 0x20
    
    >>> logger = utilities.makeDoctestLogger("DUP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(10, 20, 30)
    >>> h.state.statistics.maxima.stack
    3
    >>> hint_DUP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack
    [10, 20, 30, 30]
    >>> h.state.statistics.maxima.stack
    4
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> hint_DUP(h, logger=logger)
    DUP_test - ERROR - DUP opcode in test (PC 1) has an empty stack.
    """
    
    state = self.state
    stack = state.stack
    logger = self._getLogger(**kwArgs)
    
    if not (len(stack) and len(state.pushHistory)):
        logger.error((
          'E6046',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "DUP opcode in %s (PC %d) has an empty stack."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    state.append('stack', stack[-1])
    state.append('pushHistory', state.pushHistory[-1])
    state.statistics.stackCheck(stack)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePush(argIndex=fatObj.stack[-1][-1])
    
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
