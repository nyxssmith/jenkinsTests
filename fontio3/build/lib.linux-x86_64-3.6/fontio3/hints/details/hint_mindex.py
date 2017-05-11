#
# hint_mindex.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the MINDEX opcode.
"""

# Other imports
from fontio3.hints.history import historygroup
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import Collection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_MINDEX(self, **kwArgs):
    """
    MINDEX: Move indexed stack element, opcode 0x26
    
    >>> logger = utilities.makeDoctestLogger("MINDEX_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(1, 2, -1, 3)
    >>> hint_MINDEX(h, logger=logger)
    >>> h.state.stack
    [2, -1, 1]
    >>> pp.PP().sequence_deep_tag_smart(
    ...  h.state.pushHistory,
    ...  (lambda x: False))
    0: Extra index 1 in PUSH opcode index 0 in test
    1: Extra index 2 in PUSH opcode index 0 in test
    2: Extra index 0 in PUSH opcode index 0 in test
    >>> h = _testingState(10, toCollection([20, 30]), 40, toCollection([2, 3]))
    >>> hint_MINDEX(h, logger=logger)
    >>> h.state.stack[-1]
    Ranges: [(10, 40, 10)]
    >>> h.state.stack[-2]
    40
    >>> h.state.stack[-3]
    Ranges: [(10, 40, 10)]
    >>> pp.PP().sequence_deep_tag(h.state.pushHistory)
    0:
      Extra index 0 in PUSH opcode index 0 in test
      Extra index 1 in PUSH opcode index 0 in test
    1:
      Extra index 2 in PUSH opcode index 0 in test
    2:
      Extra index 0 in PUSH opcode index 0 in test
      Extra index 1 in PUSH opcode index 0 in test
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> hint_MINDEX(h, logger=logger)
    MINDEX_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    stack = state.stack
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    allIndices = set(t)
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    largestSpan = max(allIndices)
    
    if largestSpan > len(stack):
        logger.error((
          'E6030',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "MINDEX opcode in %s (PC %d) attempted to reach past the start "
          "of the stack."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    workRange = list(range(-largestSpan, 0))
    indexLists = [mindexSub(workRange, n) for n in allIndices]
    newStackPiece, newHistoryPiece = [], []
    
    for n in workRange:
        contributors = set(v[n] for v in indexLists)
        
        if len(contributors) == 1:
            resolvedIndex = contributors.pop()
            newStackPiece.append(stack[resolvedIndex])
            newHistoryPiece.append(state.pushHistory[resolvedIndex])
        
        else:
            newCollection = Collection()
            newHistoryPieces = []
            
            for resolvedIndex in contributors:
                newCollection = newCollection.addToCollection(
                  stack[resolvedIndex])
                
                newHistoryPieces.append(state.pushHistory[resolvedIndex])
            
            nc2 = newCollection.toNumber()
            
            if nc2 is not None:
                newCollection = nc2
            
            newStackPiece.append(newCollection)
            newHistoryPiece.append(historygroup.HistoryGroup(newHistoryPieces))
    
    stack[-largestSpan:] = newStackPiece
    state.changed('stack')
    state.pushHistory[-largestSpan:] = newHistoryPiece
    state.changed('pushHistory')
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('stackIndex', 'MINDEX')
        
        if len(allIndices) > 1:
            raise ValueError(
              "FDEF argument tracking cannot deal with Collections "
              "as stack indices.")
        
        fatObj.hint_mindex(largestSpan)

def mindexSub(v, i):
    """
    Given a stack-like list and a stack index (positive), returns a new list
    with the specified element moved to the top of the stack.
    
    >>> mindexSub(['a', 'b', 'c', 'd', 'e'], 2)
    ['a', 'b', 'c', 'e', 'd']
    >>> mindexSub(['a', 'b', 'c', 'd', 'e'], 4)
    ['a', 'c', 'd', 'e', 'b']
    """
    
    retVal = list(v)
    newTop = retVal[-i]
    del retVal[-i]
    retVal.append(newTop)
    return retVal

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
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
