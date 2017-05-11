#
# hint_wcvtp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the WCVTP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import Collection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_WCVTP(self, **kwArgs):
    """
    WCVTP: Write CVT entry in pixels, opcode 0x44
    
    >>> logger = utilities.makeDoctestLogger("WCVTP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([5, 7]), 150, 7, 188)
    >>> h.state.cvt[5] = toCollection(1.5, newBasis=64)
    >>> h.state.changed('cvt')
    >>> hint_WCVTP(h, logger=logger)
    >>> h.state.cvt[7]
    Singles: [2.9375]
    >>> hint_WCVTP(h, logger=logger)
    >>> h.state.cvt[5]
    Singles: [1.5, 2.34375]
    >>> h.state.cvt[7]
    Singles: [2.34375, 2.9375]
    >>> h.state.statistics.pprint(keys=('cvt',))
    History for CVT values:
      5: Extra index 0 in PUSH opcode index 0 in test
      7:
        Extra index 0 in PUSH opcode index 0 in test
        Extra index 2 in PUSH opcode index 0 in test
    >>> hint_WCVTP(h, logger=logger)
    WCVTP_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    cvtIndex, distance = t
    distance = distance.changedBasis(1)
    cvtHistory = self._popRemove(state, 'pushHistory', 2)
    
    if cvtHistory is None:
        state.assign('pc', doNotProceedPC)
        return
    
    cvtHistory = cvtHistory[0]
    okToProceed = True
    
    if (
      (None not in distance) and
      any(n < -16384 or n >= 16384 for n in distance)):
        
        logger.error((
          'E6019',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "WCVTP opcode in %s (PC %d) has out-of-range FUnit distance."))
        
        state._validationFailed = True
        okToProceed = False
    
    missing = sorted(n for n in cvtIndex if n not in state.cvt)
    
    if missing:
        
        logger.error((
          'E6005',
          (self.ultParent.infoString, state.pc + self.ultDelta, missing),
          "For WCVTP opcode in %s (PC %d), "
          "CVTs not present in CVT table: %s"))
        
        state._validationFailed = True
        okToProceed = False
    
    if okToProceed:
        stats.addHistory('cvt', cvtIndex, cvtHistory)
        
        stats.noteEffect(
          'cvt',
          cvtIndex,
          self.ultParent.infoString,
          state.pc + self.ultDelta,
          -2)
        
        scaledVal = distance.changedBasis(64)
        
        # This next logic requires a bit of explanation. If the cvtIndex
        # comprises a single value, there is only one possible outcome, and
        # so there is no ambiguity: the value is simply stored in that
        # index. If the cvtIndex comprises multiple values, on the other
        # hand, then it's like the fissioning of universes at a quantum
        # event. We don't know which actual index gets stored in a
        # particular universe, and it's possible that a result present in
        # the cvt array won't actually be touched, even if its index
        # matches one of the indices in cvtIndex. For this reason, we need
        # to create the combination of any existing values with the new
        # values as the new set of potential values for all the cells in
        # the cvt table indexed by cvtIndex.
        
        if len(cvtIndex) == 1:
            n2 = cvtIndex.toNumber()
            
            if n2 is not None:
                cvtIndex = n2
            
            state.cvt[cvtIndex] = scaledVal
        
        else:
            for indivIndex in cvtIndex:
                orig = state.cvt[indivIndex]
                
                assert \
                  isinstance(orig, Collection) and orig.basis == 64, \
                  "cvt entry not basis 64!"
                
                state.cvt[indivIndex] = orig.addToCollection(scaledVal)
        
        state.changed('cvt')
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'WCVTP')
        fatObj.notePop('cvtIndex', 'WCVTP')
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
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
