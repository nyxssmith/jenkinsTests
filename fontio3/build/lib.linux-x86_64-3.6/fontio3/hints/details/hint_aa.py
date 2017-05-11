#
# hint_aa.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the AA opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_AA(self, **kwArgs):
    """
    AA: Adjust angle, opcode 0x7F (obsolete; used by iType for special
    hinting)
    
    >>> logger = utilities.makeDoctestLogger("AA_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(250, 2)
    >>> hint_AA(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.pprint(keys=('aa',))
    History for AA opcodes:
      2: Extra index 1 in PUSH opcode index 0 in test
    >>> hint_AA(h, logger=logger)
    AA_test - ERROR - AA opcode in test (PC 1) is for delta-compression, which is not yet supported in fontio.
    >>> h.state.assign('pc', 0)
    >>> hint_AA(h, logger=logger)
    AA_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    aaIndex = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if aaIndex is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('aaIndex', 'AA')
    
    aaIndex = aaIndex.toNumber()
    
    if aaIndex is None:
        logger.error((
          'V0511',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "AA opcode in %s (PC %d) is using a Collection, which is "
          "not supported in fontio at this time."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    if aaIndex >= 250:
        logger.error((
          'V0512',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "AA opcode in %s (PC %d) is for delta-compression, which "
          "is not yet supported in fontio."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    state.statistics.addHistory('aa', aaIndex, history)
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
