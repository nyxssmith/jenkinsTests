#
# hint_instctrl.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the INSTCTRL opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_INSTCTRL(self, **kwArgs):
    """
    INSTCTRL: Instruction execution control, opcode 0x8E
    
    >>> logger = utilities.makeDoctestLogger("INSTCTRL_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(1, 2, 0, 2)
    >>> hint_INSTCTRL(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> hint_INSTCTRL(h, logger=logger)
    INSTCTRL_test - ERROR - INSTCTRL hint in test (PC 1) has selector 2, but value is neither 0 nor 2.
    >>> hint_INSTCTRL(h, logger=logger)
    INSTCTRL_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    okToProceed = True
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    value, selector = t
    
    if self._popRemove(state, 'pushHistory', 2) is None:
        state.assign('pc', doNotProceedPC)
        return
    
    v2 = value.toNumber()
    s2 = selector.toNumber()
    
    if s2 is not None and v2 is not None:
        if s2 == 1 and v2 not in {0, 1}:
            logger.error((
              'E6050',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "INSTCTRL hint in %s (PC %d) has selector 1, but value "
              "is neither 0 nor 1."))
            
            state._validationFailed = True
            okToProceed = False
        
        elif s2 == 2 and v2 not in {0, 2}:
            logger.error((
              'E6051',
              (self.ultParent.infoString, state.pc + self.ultDelta),
              "INSTCTRL hint in %s (PC %d) has selector 2, but value "
              "is neither 0 nor 2."))
            
            state._validationFailed = True
            okToProceed = False
    
    if okToProceed:
        if 'fdefEntryStack' in kwArgs:
            # We only note graphicsState effects when a FDEF stack is available
            
            state.statistics.noteGSEffect(
              tuple(kwArgs['fdefEntryStack']),
              state.pc + self.ultDelta)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('selector', 'INSTCTRL')
        fatObj.notePop(None, 'INSTCTRL')
    
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
