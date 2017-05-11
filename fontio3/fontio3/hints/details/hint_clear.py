#
# hint_clear.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the CLEAR opcode.
"""

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_CLEAR(self, **kwArgs):
    """
    CLEAR: Clear the stack, opcode 0x22
    
    >>> logger = utilities.makeDoctestLogger("CLEAR_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(1, 2, 3)
    >>> len(h.state.stack)
    3
    >>> hint_CLEAR(h, logger=logger)
    >>> len(h.state.stack), len(h.state.pushHistory)
    (0, 0)
    """
    
    state = self.state
    state.stack[:] = []
    state.changed('stack')
    state.pushHistory[:] = []
    state.changed('pushHistory')
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.stack[-1][:] = []
    
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
