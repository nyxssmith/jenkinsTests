#
# hint_jmpr.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the JMPR opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_JMPR(self, **kwArgs):
    """
    JMPR: Jump relative, opcode 0x1C
    
    >>> logger = utilities.makeDoctestLogger("JMPR_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(toCollection([3, 8]), 2)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["JMPR"]))
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["IUP[x]"]))
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["IUP[y]"]))
    >>> hint_JMPR(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.pc
    2
    >>> h.state.statistics.pprint(keys=('jump',))
    History for jump opcodes:
      ('test', 0, -1): Extra index 1 in PUSH opcode index 0 in test
    >>> hint_JMPR(h, logger=logger)
    JMPR_test - ERROR - In test (PC 2) a Collection value was used, but is not supported in fontio.
    >>> h.state.assign('pc', 0)
    >>> hint_JMPR(h, logger=logger)
    JMPR_test - CRITICAL - Stack underflow in test (PC 0).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    offset = self._popRemove(state, 'stack', coerceToCollection=True)
    
    if offset is None:
        state.assign('pc', doNotProceedPC)
        return
    
    history = self._popRemove(state, 'pushHistory')
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    t = (self.ultParent.infoString, state.pc + self.ultDelta, -1)
    state.statistics.addHistory('jump', t, history)
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('jumpOffset', 'JMPR')
    
    self._jumpToOffset(offset)

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
