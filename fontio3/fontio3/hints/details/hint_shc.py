#
# hint_shc.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the SHC opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_SHC(self, **kwArgs):
    """
    SHC: Shift contour, opcodes 0x34-0x35
    
    >>> logger = utilities.makeDoctestLogger("SHC_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(0, 0, 1, 12, 8)
    >>> hint_srp1.hint_SRP1(h, logger=logger)
    >>> hint_srp2.hint_SRP2(h, logger=logger)
    >>> hint_SHC(h, refPt=1, logger=logger)
    >>> hint_SHC(h, refPt=2, logger=logger)
    >>> h.state.statistics.maxima.pprint(keys=('point', 'stack'))
    Highest point index in the glyph zone: 12
    Deepest stack attained: 5
    >>> h.state.statistics.pprint(keys=('contour', 'point'))
    History for SHC contours (glyph zone):
      0: Extra index 1 in PUSH opcode index 0 in test
      1: Extra index 2 in PUSH opcode index 0 in test
    History for outline points (glyph zone):
      8: Extra index 4 in PUSH opcode index 0 in test
      12: Extra index 3 in PUSH opcode index 0 in test
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state._inPreProgram = True
    >>> hint_SHC(h, refPt=1, logger=logger)
    SHC_test - ERROR - SHC opcode (PC 4) should not be used in the pre-program.
    >>> h.state.assign('pc', 4)
    >>> hint_SHC(h, logger=logger)
    SHC_test - CRITICAL - Stack underflow in test (PC 4).
    """
    
    state = self.state
    gs = state.graphicsState
    logger = self._getLogger(**kwArgs)
    contour = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if contour is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    indexMin = contour.min()
    indexMax = contour.max()
    
    if state._inPreProgram:
        logger.error((
          'E6037',
          (state.pc,),
          "SHC opcode (PC %d) should not be used in the pre-program."))
        
        state._validationFailed = True
    
    elif (
      (None in contour) or
      (indexMin < 0) or
      (indexMax >= state._numContours[1])):
        
        logger.error((
          'E6004',
          (contour, self.ultParent.infoString, state.pc + self.ultDelta),
          "Contour index %d in SHC opcode (%s, PC %d) is out of range."))
        
        state._validationFailed = True
    
    elif self._zoneCheck("SHC", (0, 1, 2), logger):
        
        state.statistics.addHistory(
          'contour',
          (gs.zonePointer2, contour),
          history)
        
        if kwArgs.get('refPt', 1) == 1:
            
            state.statistics.addHistory(
              'point',
              (gs.zonePointer0, gs.referencePoint1),
              self._synthRefHistory(1))
        
        else:
            
            state.statistics.addHistory(
              'point',
              (gs.zonePointer1, gs.referencePoint2),
              self._synthRefHistory(2))
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('contourIndex', 'SHC')
    
    state.assign('pc', state.pc + 1)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.hints.details import hint_srp1, hint_srp2
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
