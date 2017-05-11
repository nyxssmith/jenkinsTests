#
# hint_utp.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the UTP opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_UTP(self, **kwArgs):
    """
    UTP: Untouch point, opcode 0x29
    
    >>> logger = utilities.makeDoctestLogger("UTP_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(12)
    >>> hint_UTP(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.statistics.maxima.point
    12
    >>> h.state.statistics.pprint(keys=('point',))
    History for outline points (glyph zone):
      12: Extra index 0 in PUSH opcode index 0 in test
    >>> hint_UTP(h, logger=logger)
    UTP_test - CRITICAL - Stack underflow in test (PC 1).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    p = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if p is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    if self._zoneCheck("UTP", (0,), logger):
        zp0 = state.graphicsState.zonePointer0
        
        if self._pointCheck(
          "UTP",
          [(zp0, p, True)],
          logger,
          kwArgs.get('extraInfo', {})):
            
            state.statistics.addHistory('pointMoved', (zp0, p), history)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('pointIndex', 'UTP')
    
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
