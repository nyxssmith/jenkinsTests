#
# hint_jrot.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the JROT opcode.
"""

# Other imports
from fontio3.hints.common import doNotProceedPC

# -----------------------------------------------------------------------------

#
# Functions
#

def hint_JROT(self, **kwArgs):
    """
    JROT: Jump relative if true, opcode 0x78
    
    >>> logger = utilities.makeDoctestLogger("JROT_test")
    >>> _popSync, _testingState = _testFuncs()
    >>> h = _testingState(2, 1)
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["JROT"]))
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["IUP[x]"]))
    >>> h.append(opcode_tt.Opcode_nonpush(nameToOpcodeMap["IUP[y]"]))
    >>> hint_JROT(h, logger=logger)
    >>> len(h.state.stack) == len(h.state.pushHistory)
    True
    >>> h.state.pc
    2
    >>> h.state.statistics.pprint(keys=('jump',))
    History for jump opcodes:
      ('test', 0, -2): Extra index 0 in PUSH opcode index 0 in test
    >>> hint_JROT(h, logger=logger)
    JROT_test - CRITICAL - Stack underflow in test (PC 2).
    """
    
    state = self.state
    logger = self._getLogger(**kwArgs)
    t = self._popRemove(state, 'stack', 2, coerceToCollection=True)
    
    if t is None:
        state.assign('pc', doNotProceedPC)
        return
    
    offset, condition = t
    history = self._popRemove(state, 'pushHistory', 2)
    
    if history is None:
        state.assign('pc', doNotProceedPC)
        return
    
    condition = condition.toNumber()
    
    if condition is None:
        state.assign('pc', doNotProceedPC)
        return
    
    t = (self.ultParent.infoString, state.pc + self.ultDelta, -2)
    state.statistics.addHistory('jump', t, history[0])
    
    fatObj = kwArgs.get('fdefArgTracer', None)
    
    if fatObj is not None:
        fatObj.notePop('boolean', 'JROT')
        fatObj.notePop('jumpOffset', 'JROT')
    
    if condition:
        self._jumpToOffset(offset)
    else:
        state.assign('pc', state.pc + 1)

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
    
    def _testFuncs():
        from fontio3.hints import hints_tt
        return hints_tt._popSync, hints_tt._testingState

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
