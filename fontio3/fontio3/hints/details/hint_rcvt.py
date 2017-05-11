#
# hint_rcvt.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the RCVT opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import Collection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_RCVT(self, **kwArgs):
    """
    RCVT: Read CVT value, opcode 0x45
    
    >>> logger = utilities.makeDoctestLogger("RCVT_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([12, 15]), 12)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["RCVT"]))
    >>> h.state.cvt[12] = toCollection(1.5, newBasis=64)
    >>> h.state.cvt[15] = toCollection([-0.75, -0.25, 0], newBasis=64)
    >>> h.state.changed('cvt')
    >>> pp.PP().mapping(h.state.cvt)
    0: Singles: [4.375]
    1: Singles: [4.4375]
    2: Singles: [4.53125]
    3: Singles: [4.65625]
    4: Singles: [4.8125]
    5: Singles: [5.0]
    6: Singles: [5.21875]
    7: Singles: [5.46875]
    8: Singles: [5.75]
    9: Singles: [6.0625]
    10: Singles: [6.40625]
    11: Singles: [6.78125]
    12: Singles: [1.5]
    13: Singles: [7.625]
    14: Singles: [8.09375]
    15: Singles: [-0.75, -0.25, 0.0]
    16: Singles: [9.125]
    17: Singles: [9.6875]
    18: Singles: [10.28125]
    19: Singles: [10.90625]
    >>> hint_RCVT(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.cvt
    12
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Result of opcode RCVT at index 0 in test, with inputs:
      Extra index 1 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    96
    >>> h.state.assign('pc', 0)
    >>> hint_RCVT(h, logger=logger)
    >>> h.state.statistics.maxima.cvt
    15
    >>> h.state.stack[-1]
    Singles: [-48, -16, 0, 96]
    >>> h.state.statistics.pprint(keys=('cvt',))
    History for CVT values:
      12:
        Extra index 0 in PUSH opcode index 0 in test
        Extra index 1 in PUSH opcode index 0 in test
      15: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_RCVT(h, logger=logger)
    RCVT_test - ERROR - For RCVT opcode in test (PC 1), CVTs not present in CVT table: [-48, -16, 96]
    >>> hint_RCVT(h, logger=logger)
    RCVT_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    cvtIndex = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if cvtIndex is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    missing = sorted(n for n in cvtIndex if n not in state.cvt)
    
    if missing:
        logger.error((
          'E6005',
          (self.ultParent.infoString, state.pc + self.ultDelta, missing),
          "For RCVT opcode in %s (PC %d), "
          "CVTs not present in CVT table: %s"))
        
        state._validationFailed = True
    
    else:
        it = iter(cvtIndex)
        result = Collection(basis=64)
        
        for i in it:
            result = result.addToCollection(state.cvt[i])
        
        result = result.changedBasis(1)
        r2 = result.toNumber()
        
        if r2 is not None:
            result = r2
        
        state.append('stack', result)
        stats.addHistory('cvt', cvtIndex, history)
        
        stats.noteEffect(
          'cvt',
          cvtIndex,
          self.ultParent.infoString,
          state.pc + self.ultDelta,
          -1)
        
        state.append(
          'pushHistory',
          op.HistoryEntry_op(
            hintsObj = (id(self.ultParent), self.ultParent), 
            hintsPC = state.pc + self.ultDelta,
            opcode = self[state.pc].opcode,
            historyIterable = [history]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('cvtIndex', 'RCVT')
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
    from fontio3.triple.collection import toCollection
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
