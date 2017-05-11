#
# hint_gfv.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the GFV opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_GFV(self, **kwArgs):
    """
    GFV: Get freedom vector, opcode 0x0D
    
    >>> logger = utilities.makeDoctestLogger("GFV_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState()
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["GFV"]))
    >>> hint_GFV(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep_tag_smart(
    ...   h.state.pushHistory,
    ...   (lambda x: False))
    0: Result of opcode GFV at index 0 in test
    1: Result of opcode GFV at index 0 in test
    >>> h.state.statistics.maxima.stack
    2
    >>> h.state.stack[-1]
    0
    >>> h.state.stack[-2]
    1
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    gsd = state.graphicsState.__dict__
    which = gsd[kwArgs.get('which', 'freedomVector')]
    n = which[0].changedBasis(1)
    n2 = n.toNumber()
    
    if n2 is not None:
        n = n2
    
    state.append('stack', n)
    n = which[1].changedBasis(1)
    n2 = n.toNumber()
    
    if n2 is not None:
        n = n2
    
    state.append('stack', n)
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = []))
    
    state.append('pushHistory', state.pushHistory[-1])
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePush()
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
