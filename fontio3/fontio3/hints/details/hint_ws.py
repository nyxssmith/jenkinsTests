#
# hint_ws.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the WS opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection
from fontio3.hints.history.historygroup import HistoryGroup as HG

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_WS(self, **kwArgs):
    """
    WS: Write to storage, opcode 0x42
    
    >>> logger = utilities.makeDoctestLogger("WS_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([8, 15]), 64, 15, -128)
    >>> h.state.storage[8] = 32
    >>> h.state.changed('storage')
    >>> hint_WS(h, logger=logger)
    >>> h.state.storage[15]
    -128
    >>> hint_WS(h, logger=logger)
    >>> h.state.storage[8]
    Singles: [32, 64]
    >>> h.state.storage[15]
    Singles: [-128, 64]
    >>> h.state.statistics.pprint(keys=('storage',))
    History for storage locations:
      8: Extra index 0 in PUSH opcode index 0 in test
      15:
        Extra index 0 in PUSH opcode index 0 in test
        Extra index 2 in PUSH opcode index 0 in test
    >>> hint_WS(h, logger=logger)
    WS_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    storageIndex, value = t
    t = self._popRemove(state, 'pushHistory', 2)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    indexHistory, valueHistory = t
    stats.addHistory('storage', storageIndex, indexHistory)
    
    stats.noteEffect(
      kind = 'storage',
      value = storageIndex,
      infoString = self.ultParent.infoString,
      pc = state.pc + self.ultDelta,
      relStackIndex = -2)
    
    if len(storageIndex) == 1:
        indivIndex = int(storageIndex)
        n2 = value.toNumber()
        
        if n2 is not None:
            value = n2
        
        state.storage[indivIndex] = value
        state.storageHistory[indivIndex] = valueHistory
    
    else:
        for indivIndex in storageIndex:
            orig = toCollection(state.storage[indivIndex])
            orig = orig.addToCollection(value)
            n2 = orig.toNumber()
            
            if n2 is not None:
                orig = n2
            
            origHistory = self._synthStorageHistory(indivIndex)
            state.storage[indivIndex] = orig
            
            state.storageHistory[indivIndex] = (
              HG([origHistory, valueHistory]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'WS')
        fatObj.notePop('storageIndex', 'WS')
    
    state.changed('storage')
    state.changed('storageHistory')
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
