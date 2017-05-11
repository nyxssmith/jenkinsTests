#
# hint_getinfo.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the GETINFO opcode.
"""

# System imports
import functools
import operator

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.hints.history import op
from fontio3.triple.collection import Collection
from fontio3.triple.triple import Triple

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_GETINFO(self, **kwArgs):
    """
    GETINFO: Get information, opcode 0x88
    
    >>> logger = utilities.makeDoctestLogger("GETINFO_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0x8000, 1)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["GETINFO"]))
    >>> hint_GETINFO(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> pp.PP().sequence_deep(h.state.pushHistory)
    Extra index 0 in PUSH opcode index 0 in test
    Result of opcode GETINFO at index 0 in test, with inputs:
      Extra index 1 in PUSH opcode index 0 in test
    >>> _popSync(h.state)
    Ranges: [(0, 1024, 1)]
    
    >>> h.state.assign('pc', 0)
    >>> hint_GETINFO(h, logger=logger)
    GETINFO_test - ERROR - GETINFO hint in test (PC 0) uses selector bits that are reserved and should be set to zero.
    
    >>> _popSync(h.state)
    Ranges: [(0, 1024, 1)]
    >>> h.state.assign('pc', 0)
    >>> hint_GETINFO(h, logger=logger)
    GETINFO_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    h = self._popRemove(state, 'pushHistory')
    
    if h is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._16BitCheck("GETINFO", n, logger, False):
        mask = functools.reduce(operator.or_, iter(n))
        
        if kwArgs.get('forApple', False):
            isBad = bool(mask & 0xFFE0)
        else:
            isBad = bool(mask & 0xE000)
        
        if isBad:
            logger.error((
              'E6044',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "GETINFO hint in %s (PC %d) uses selector bits that are "
              "reserved and should be set to zero."))
            
            state._validationFailed = True
    
    state.append('stack', Collection([Triple(0, 1024, 1)]))
    
    state.append(
      'pushHistory',
      op.HistoryEntry_op(
        hintsObj = (id(self.ultParent), self.ultParent), 
        hintsPC = state.pc + self.ultDelta,
        opcode = self[state.pc].opcode,
        historyIterable = [h]))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('selector', 'GETINFO')
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
