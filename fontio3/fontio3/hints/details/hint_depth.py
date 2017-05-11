#
# hint_depth.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DEPTH opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DEPTH(self, **kwArgs):
    """
    DEPTH: Depth of the stack, opcode 0x24
    
    >>> logger = utilities.makeDoctestLogger("DEPTH_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(100, 101)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["DEPTH"]))
    >>> h.state.statistics.maxima.stack
    2
    >>> hint_DEPTH(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack
    [100, 101, 2]
    >>> h.state.statistics.maxima.stack
    3
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Result of opcode DEPTH at index 0 in test
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    state.append('stack', len(state.stack))
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = []))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePush()
    
    state.statistics.stackCheck(state.stack)
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints import opcode_tt
    from fontio3.hints.common import nameToOpcodeMap
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
