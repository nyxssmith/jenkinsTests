#
# hint_cindex.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the CINDEX opcode.
"""

# System imports
import functools

# Other imports
from fontio3.hints.history import historygroup
from fontio3.hints.common import doNotProceedPC
from fontio3.triple import collection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_CINDEX(self, **kwArgs):
    """
    CINDEX: Copy indexed stack element, opcode 0x25
    
    >>> logger = utilities.makeDoctestLogger("CINDEX_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(5, 2, 8, 1, 3)
    >>> h.state.stack
    [5, 2, 8, 1, 3]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 3 in PUSH opcode index 0 in test
    Extra index 4 in PUSH opcode index 0 in test
    >>> hint_CINDEX(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack
    [5, 2, 8, 1, 2]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 3 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    >>> hint_CINDEX(h, logger=logger)
    >>> h.state.stack
    [5, 2, 8, 1, 8]
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Extra index 1 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    Extra index 3 in PUSH opcode index 0 in test
    Extra index 2 in PUSH opcode index 0 in test
    >>> hint_CINDEX(h, logger=logger)
    CINDEX_test - ERROR - CINDEX opcode in test (PC 2) attempted to read outside the confines of the stack.
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> h.state.assign('pc', 0)
    >>> hint_CINDEX(h, logger=logger)
    CINDEX_test - CRITICAL - Stack underflow in test (PC 0).
    >>> h = _testingState(11, 12, 13, 14, toCollection([1, 2, 4]))
    >>> hint_CINDEX(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.stack
    [11, 12, 13, 14, Singles: [11, 13, 14]]
    >>> pp.PP().sequence_deep_tag(h.state.pushHistory)
    0:
      Extra index 0 in PUSH opcode index 0 in test
    1:
      Extra index 1 in PUSH opcode index 0 in test
    2:
      Extra index 2 in PUSH opcode index 0 in test
    3:
      Extra index 3 in PUSH opcode index 0 in test
    4:
      Extra index 0 in PUSH opcode index 0 in test
      Extra index 2 in PUSH opcode index 0 in test
      Extra index 3 in PUSH opcode index 0 in test
    """
    
    state = self.state
    stack = state.stack
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    allIndices = set(t)
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if len(allIndices) == 1:
        k = next(iter(allIndices))
        
        try:
            history = state.pushHistory[-k-1]
        
        except IndexError:
            logger.error((
              'E6030',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "CINDEX opcode in %s (PC %d) attempted to read "
              "outside the confines of the stack."))
            
            state._validationFailed = True
            state.assign('pc', doNotProceedPC)
            return
        
        entry = stack[-k]
        
        if fatObj is not None:
            fatObj.notePop('stackIndex', 'CINDEX')
            fatObj.notePush(argIndex=fatObj.stack[-1][-k])
    
    else:
        if max(allIndices) > len(stack):
            logger.error((
              'E6030',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "CINDEX opcode in %s (PC %d) attempted to read "
              "outside the confines of the stack."))
            
            state._validationFailed = True
            state.assign('pc', doNotProceedPC)
            return
        
        entry = functools.reduce(
          collection.cluster,
          (stack[-k] for k in allIndices))
        
        history = historygroup.HistoryGroup(
          state.pushHistory[-k-1]
          for k in allIndices)
        
        if fatObj is not None:
            fatObj.notePop('stackIndex', 'CINDEX')
            stk = fatObj.stack[-1]
            argIndex = frozenset(stk[-k] for k in allIndices)
            fatObj.notePush(argIndex=argIndex)
    
    state.append('stack', entry)
    state.pushHistory[-1] = history
    state.changed('pushHistory')
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import pp
    from fontio3.triple.collection import toCollection
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
