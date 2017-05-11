#
# hint_mps.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MPS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import Collection
from fontio3.triple.triple import Triple

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MPS(self, **kwArgs):
    """
    MPS: Measure pointsize, opcode 0x4C
    
    >>> logger = utilities.makeDoctestLogger("MPS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["MPS"]))
    >>> hint_MPS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.stack
    1
    >>> h.state.stack[-1]
    Ranges: [(5, *, 1)]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Result of opcode MPS at index 0 in test
    """
    
    state = self.state
    state.append('stack', Collection([Triple(5, None, 1)]))
    state.statistics.stackCheck(state.stack)
    
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
