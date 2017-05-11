#
# hint_deltac.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the DELTAC opcodes.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC
from fontio3.triple.collection import toCollection

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_DELTAC(self, **kwArgs):
    """
    DELTAC[1-3]: CVT-based delta hint, opcodes 0x73-0x75
    
    Note that this current implementation ignores the bandDelta kwArg.
    
    >>> logger = utilities.makeDoctestLogger("DELTAC_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(98, 4, 114, 6, 2)
    >>> hint_DELTAC(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.cvt
    6
    >>> h.state.stack[:] = [0]
    >>> h.state.changed('stack')
    >>> hint_DELTAC(h, logger=logger)
    DELTAC_test - ERROR - In test (PC 1) the value 0 is too low.
    >>> h.state.stack[:] = []
    >>> h.state.changed('stack')
    >>> h.state.assign('pc', 0)
    >>> hint_DELTAC(h, logger=logger)
    DELTAC_test - CRITICAL - Stack underflow in test (PC 0).
    >>> h = _testingState(98, 4, 114, 6, toCollection([2]))
    >>> hint_DELTAC(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.cvt
    6
    >>> h = _testingState(98, 4, 114, 6, toCollection([2, 3]))
    >>> hint_DELTAC(h, logger=logger)
    DELTAC_test - ERROR - In test (PC 0) a Collection value was used, but is not supported in fontio.
    """
    
    state = self.state
    stats = state.statistics
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack')
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    count = self._toNumber(n, doCheck=True)
    
    if count is None or self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if count:  # some fonts have a zero count as a pseudo-NOP, hmph.
        historyPiece = self._popRemove(state, 'pushHistory', 2 * count)
        
        if historyPiece is None:
            state.assign('pc', doNotProceedPC)
            return
        
        historyPiece = historyPiece[1::2]
        allPieces = self._popRemove(state, 'stack', 2 * count)
        
        if allPieces is None:
            state.assign('pc', doNotProceedPC)
            return
        
        argPiece = allPieces[0::2]
        okToProceed = True
        
        for arg in argPiece:
            okToProceed = (
              self._8BitCheck("DELTAC", arg, logger) and
              okToProceed)
        
        if okToProceed:
            if argPiece != sorted(argPiece):
                logger.warning((
                  'V0491',
                  (self.ultParent.infoString, state.pc + self.ultDelta),
                  "The DELTAC opcode in %s (PC %d) has args unsorted "
                  "by PPEM. They should be sorted if this font is "
                  "to be used with iType."))
            
            cvtPiece = allPieces[1::2]
            
            missing = sorted(
              n
              for x in cvtPiece
              for n in toCollection(x)
              if n not in state.cvt)
            
            if missing:
                logger.error((
                  'E6005',
                  (self.ultParent.infoString,
                   state.pc + self.ultDelta,
                   missing),
                  "For DELTAC opcode in %s (PC %d), these "
                  "CVT indices are not present in CVT table: %s"))
                
                state._validationFailed = True
            
            thisHint = self.ultParent
            thisPC = state.pc + self.ultDelta
            
            for i, cvtIndex in enumerate(cvtPiece):
                he = historyPiece[i]
                stats.addHistory('cvt', cvtIndex, he)
                
                stats.noteEffect(
                  'cvt',
                  cvtIndex,
                  thisHint.infoString,
                  thisPC,
                  2 * (i - count))
    
    else:
        logger.warning((
          'V0490',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "DELTAC opcode in %s (PC %d) has a specification count "
          "of zero, meaning it's being used as a pseudo-NOP."))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop(None, 'DELTAC')
        
        for i in range(count):
            fatObj.notePop('cvtIndex', 'DELTAC')
            fatObj.notePop('deltaArg', 'DELTAC')
    
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
