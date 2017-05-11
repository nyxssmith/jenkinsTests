#
# hint_scanctrl.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SCANCTRL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SCANCTRL(self, **kwArgs):
    """
    SCANCTRL: Scan conversion control, opcode 0x85
    
    >>> logger = utilities.makeDoctestLogger("SCANCTRL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0x0900, 10)
    >>> h.state.graphicsState.scanControl
    0
    >>> hint_SCANCTRL(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.scanControl
    Singles: [10]
    >>> hint_SCANCTRL(h, logger=logger)
    SCANCTRL_test - ERROR - SCANCTRL opcode in test (PC 1): bits 8 and 11 cannot both be set.
    >>> h.state.assign('pc', 0)
    >>> hint_SCANCTRL(h, logger=logger)
    SCANCTRL_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    value = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if value is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    okToProceed = True
    
    if not self._16BitCheck("SCANCTRL", value, logger, False):
        okToProceed = False
    
    else:
        if 1 in (value & 0xC000).encompassedBooleans():
            logger.error((
              'E6042',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "SCANCTRL in %s (PC %d) has at least one reserved bit set."))
            
            state._validationFailed = True
            okToProceed = False
        
        if 0x2400 in (value & 0x2400):
            logger.error((
              'E6001',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "SCANCTRL opcode in %s (PC %d): bits 10 and 13 "
              "cannot both be set."))
            
            state._validationFailed = True
            okToProceed = False
        
        if 0x0900 in (value & 0x0900):
            logger.error((
              'E6002',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "SCANCTRL opcode in %s (PC %d): bits 8 and 11 "
              "cannot both be set."))
            
            state._validationFailed = True
            okToProceed = False
        
        if 0x1200 in (value & 0x1200):
            logger.error((
              'E6003',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "SCANCTRL opcode in %s (PC %d): bits 9 and 12 "
              "cannot both be set."))
            
            state._validationFailed = True
            okToProceed = False
    
    if okToProceed:
        state.assignDeep('graphicsState', 'scanControl', value)
        
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a
            # FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('selector', 'SCANCTRL')
    
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
