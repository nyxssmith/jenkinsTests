#
# fdefargtracer.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# System imports
import collections

# -----------------------------------------------------------------------------

#
# Constants
#

validKinds = frozenset({
  'aaIndex',
  'boolean',
  'contourIndex',
  'cvtIndex',
  'debugCode',
  'deltaArg',
  'fdefIndex',
  'jumpOffset',
  'loopCounter',
  'mazMode',
  'pointIndex',
  'ppem',
  'roundState',
  'selector',
  'stackIndex',
  'storageIndex',
  'zoneIndex'})

# -----------------------------------------------------------------------------

#
# Classes
#

class FDEFArgTracer:
    """
    """
    
    #
    # Methods
    #
    
    def __init__(self):
        self.stack = [[]]
        self.activeFDEF = []
        DD = collections.defaultdict
        self.argInfo = DD(lambda: DD(set))  # FDEF index -> {argIndex: {(kind, opcode) [,...]}}
    
    def hint_mindex(self, i):
        vTemp = list(self.stack[-1])
        newTop = vTemp[-i]
        del vTemp[-i]
        vTemp.append(newTop)
        self.stack[-1][:] = vTemp
    
    def notePop(self, kind, opcode, ignore=False):
        argIndex = self.stack[-1].pop()
        
        if not self.activeFDEF:
            return None
        
        if (argIndex is not None) and (not ignore):
            self.argInfo[self.activeFDEF[-1]][argIndex].add((kind, opcode))
        
        return argIndex
    
    def notePush(self, argIndex=None, count=1):
        self.stack[-1].extend([argIndex] * count)
    
    def showResults(self):
        for fdefIndex in sorted(self.argInfo):
            argDict = self.argInfo[fdefIndex]
            print("FDEF", fdefIndex)
            
            for argIndex in sorted(argDict):
                tupleSet = argDict[argIndex]
                kinds = {arg[0] for arg in tupleSet}
                
                if len(kinds) > 1 and None in kinds:
                    kinds.discard(None)
                
                assert len(kinds) == 1
                
                kind = kinds.pop()
                
                if kind is None:
                    kind = "number"
                
                if argIndex == 0:
                    print("  Argument 0 (top of stack):", kind)
                else:
                    print("  Argument %d:" % (argIndex,), kind)
    
    def startFDEF(self, fdefIndex):
        self.stack.append(list(range(len(self.stack[-1]))))
        self.stack[-1].reverse()
        self.activeFDEF.append(fdefIndex)
    
    def stopFDEF(self):
        endStack = self.stack.pop()
        limitLen = len(endStack)
        self.stack[-1] = self.stack[-1][:limitLen]
        del self.activeFDEF[-1]

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
