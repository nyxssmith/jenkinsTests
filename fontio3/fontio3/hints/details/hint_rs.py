#
# hint_rs.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the RS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_RS(self, **kwArgs):
    """
    RS: Read storage, opcode 0x43
    
    >>> logger = utilities.makeDoctestLogger("RS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([2, 5, 19]), 5)
    >>> h.state.storage[5] = 10
    >>> h.state.changed('storage')
    >>> hint_RS(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.storage
    5
    >>> _popSync(h.state)
    10
    >>> h.state.statistics.pprint(keys=('storage',))
    History for storage locations:
      5: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_RS(h, logger=logger)
    >>> h.state.statistics.pprint(keys=('storage',))
    History for storage locations:
      2: Extra index 0 in PUSH opcode index 0 in test
      5:
        Extra index 0 in PUSH opcode index 0 in test
        Extra index 1 in PUSH opcode index 0 in test
      19: Extra index 0 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    Singles: [0, 10]
    >>> hint_RS(h, logger=logger)
    RS_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    stats = state.statistics
    store = state.storage
    logger = self._getLogger(**kwArgs)
    index = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if index is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    it = iter(index)
    n = toCollection(store.get(next(it), 0))
    
    for i in it:
        n = n.addToCollection(store.get(i, 0))
    
    n2 = n.toNumber()
    
    if n2 is not None:
        n = n2
    
    state.append('stack', n)
    stats.addHistory('storage', index, history)
    
    stats.noteEffect(
      'storage',
      index,
      self.ultParent.infoString,
      state.pc + self.ultDelta,
      -1)
    
    state.append('pushHistory', self._synthStorageHistory(index))
    state.assign('pc', state.pc + 1)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('storageIndex', 'RS')
        fatObj.notePush()

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
