#
# hint_sloop.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SLOOP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SLOOP(self, **kwArgs):
    """
    SLOOP: Set loop in graphics state, opcode 0x17
    
    >>> logger = utilities.makeDoctestLogger("SLOOP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([2, 3]), toCollection(2), 5)
    >>> hint_SLOOP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.graphicsState.loop
    5
    >>> hint_SLOOP(h, logger=logger)
    >>> h.state.graphicsState.loop
    2
    >>> hint_SLOOP(h, logger=logger)
    SLOOP_test - ERROR - SLOOP opcode in test (PC 2) cannot be a Collection.
    >>> h.state.assign('pc', 3)
    >>> hint_SLOOP(h, logger=logger)
    SLOOP_test - CRITICAL - Stack underflow in test (PC 3).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    n = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if n is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._popRemove(state, 'pushHistory') is None:
        state.assign('pc', doNotProceedPC)
        return
    
    n = n.toNumber()
    
    if n is None:
        logger.error((
          'V0511',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SLOOP opcode in %s (PC %d) cannot be a Collection."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    if n <= 0:
        logger.error((
          'E6055',
          (self.ultParent.infoString, state.pc + self.ultDelta),
          "SLOOP opcode in %s (PC %d) specifies a value less than one."))
        
        state._validationFailed = True
        state.assign('pc', doNotProceedPC)
        return
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('loopCounter', 'SLOOP')
    
    state.assignDeep('graphicsState', 'loop', n)
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
