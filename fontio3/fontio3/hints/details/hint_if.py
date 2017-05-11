#
# hint_if.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the IF opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_IF(self, **kwArgs):
    """
    IF: Conditional test, opcode 0x58
    
    >>> logger = utilities.makeDoctestLogger("IF_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(Collection())
    >>> hint_IF(h, logger=logger)
    IF_test - WARNING - No EIF found after IF or ELSE in test (PC 0).
    IF_test - ERROR - An empty IF-EIF was found in test (PC 0).
    >>> h.state.assign('pc', 0)
    >>> hint_IF(h, logger=logger)
    IF_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    safetyCopy = state.__deepcopy__()  # don't like having to do this...
    logger = self._getLogger(**kwArgs)
    obj = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if obj is None:
        state.assign('pc', doNotProceedPC)
        return
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('boolean', 'IF')
    
    condition = obj.encompassedBooleans()
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    hIF, hELSE, eifOffset = self._getContras(logger)
    
    if hIF is None and hELSE is None:
        state.assign('pc', doNotProceedPC)
        return
    
    savedPC = state.pc
    state.assign('pc', 0)
    
    if len(condition) == 2:
        stateForELSE = state.__deepcopy__()
        fatCopyCase = False
        
        if fatObj is not None:
            if (hIF is not None) and (hELSE is not None):
                fatCopyCase = True
                fatObj.stack.append(list(fatObj.stack[-1]))
        
        if hIF is not None:
            try:
                hIF.run(state, **kwArgs)
                failedIF = (state.pc == doNotProceedPC)
            
            except:
                failedIF = True
                state.assign('pc', doNotProceedPC)  # simulate it
            
            if 'failedIfsElses' in kwArgs:
                kwArgs['failedIfsElses'].add(hIF.infoString)
            
            if fatCopyCase:
                del fatObj.stack[-1]
        
        if hELSE is not None:
            try:
                hELSE.run(stateForELSE, **kwArgs)
                failedELSE = (stateForELSE.pc == doNotProceedPC)
            
            except:
                failedELSE = True
                stateForELSE.pc = doNotProceedPC
            
            if 'failedIfsElses' in kwArgs:
                kwArgs['failedIfsElses'].add(hELSE.infoString)
        
        if hIF is not None and hELSE is not None:
            if not (failedIF or failedELSE):
                
                # The following line is just for the actual merger; the
                # actual value gets reset below, anyway.
                
                state.assign('pc', 0)
                stateForELSE.assign('pc', 0)
                
                # If the opcode immediately after the EIF is a CLEAR, we
                # clear both the stack and the pushHistory in both states
                # before attempting a merger. This fixes TTM-81.
                
                v = self.ultParent[self.ultDelta+eifOffset+1:]
                
                if (
                  v and
                  (not v[0].isPush()) and
                  (v[0].opcode == 0x22)):
                    
                    state.stack[:] = []
                    state.changed('stack')
                    state.pushHistory[:] = []
                    state.changed('pushHistory')
                    stateForELSE.stack[:] = []
                    stateForELSE.changed('stack')
                    stateForELSE.pushHistory[:] = []
                    stateForELSE.changed('pushHistory')
                
                try:
                    state.combine(stateForELSE)
                    
                    if stateForELSE._validationFailed:
                        state._validationFailed = True
                
                except utilities.MergeSyncFailure:
                    logger.error((
                      'V0550',
                      (self.ultParent.infoString, state.pc + self.ultDelta),
                      "IF hint in %s (PC %d) has a stack imbalance "
                      "between the IF and ELSE branches."))
                    
                    state.assign('pc', doNotProceedPC)
            
            elif failedIF:
                self.state = stateForELSE
            
            elif failedELSE:
                pass
            
            else:
                self.state = safetyCopy
                self.state.assign('pc', doNotProceedPC)
        
        elif hIF is None:
            if failedELSE:
                self.state = safetyCopy
                self.state.assign('pc', doNotProceedPC)
            
            else:
                state.assign('pc', 0)
                stateForELSE.assign('pc', 0)
                
                # We now combine the ELSE state with pre-IF state.
                
                try:
                    state.combine(stateForELSE)
                    
                    if stateForELSE._validationFailed:
                        state._validationFailed = True
                
                except utilities.MergeSyncFailure:
                    logger.error((
                      'V0550',
                      (self.ultParent.infoString, state.pc + self.ultDelta),
                      "IF hint in %s (PC %d) has a stack imbalance "
                      "between the IF and ELSE branches."))
                    
                    state.assign('pc', doNotProceedPC)
                
                self.state = state
        
        elif hELSE is None:
            if failedIF:
                self.state = safetyCopy
                self.state.assign('pc', doNotProceedPC)
            
            else:
                state.assign('pc', 0)
                stateForELSE.assign('pc', 0)
                
                # We now combine the IF state with pre-IF state.
                
                try:
                    state.combine(stateForELSE)
                    
                    if stateForELSE._validationFailed:
                        state._validationFailed = True
                
                except utilities.MergeSyncFailure:
                    logger.error((
                      'V0550',
                      (self.ultParent.infoString, state.pc + self.ultDelta),
                      "IF hint in %s (PC %d) has a stack imbalance "
                      "between the IF and ELSE branches."))
                    
                    state.assign('pc', doNotProceedPC)
                
                self.state = state
        
        # else: do nothing, since nothing ran, so state is unchanged
    
    elif 1 in condition:
        if hIF is not None:
            try:
                hIF.run(state, **kwArgs)
                failedIF = (state.pc == doNotProceedPC)
            
            except:
                failedIF = True
                state.assign('pc', doNotProceedPC)
            
            if 'failedIfsElses' in kwArgs:
                kwArgs['failedIfsElses'].add(hIF.infoString)
            
            if failedIF:
                self.state = safetyCopy
                self.state.assign('pc', doNotProceedPC)
            
            else:
                self.state = state
        
        elif 'unusedIfsElses' in kwArgs:
            kwArgs['unusedIfsElses'].add((self.infoString, savedPC))
    
    elif 0 in condition:
        if hELSE is not None:
            try:
                hELSE.run(state, **kwArgs)
                failedELSE = (state == doNotProceedPC)
            
            except:
                failedELSE = True
                state.assign('pc', doNotProceedPC)
            
            if 'failedIfElses' in kwArgs:
                kwArgs['failedIfsElses'].add(hELSE.infoString)
            
            if failedELSE:
                self.state = safetyCopy
                self.state.assign('pc', doNotProceedPC)
            
            else:
                self.state = state
        
        elif 'unusedIfsElses' in kwArgs:
            kwArgs['unusedIfsElses'].add((self.infoString, savedPC))
    
    else:
        logger.warning((
          'V0514',
          (self.ultParent.infoString, safetyCopy.pc + self.ultDelta),
          "The IF in %s (PC %d) has a condition of zero, and no ELSE "
          "clause, and will thus never have any effect."))
    
    # We only restore the actual PC value if nothing went wrong in any of
    # the variant branches.
    
    if self.state.pc != doNotProceedPC:
        self.state.assign('pc', eifOffset + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.triple.collection import Collection
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
