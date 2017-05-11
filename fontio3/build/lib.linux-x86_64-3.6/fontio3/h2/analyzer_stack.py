#
# analyzer_stack.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType-style stacks as used in the analysis code.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.h2 import analyzer_stack_entry
from fontio3.utilities import stamp

# -----------------------------------------------------------------------------

#
# Classes
#

class AnalyzerStack(list, metaclass=seqmeta.FontDataMetaclass):
    """
    This is a list representing the active stack. The values in the list will
    be AnalyzerStackEntry objects.
    """
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = (lambda p, x, **k: p.simple(str(x), **k)))
    
    #
    # Methods
    #
    
    def __init__(self, **kwArgs):
        """
        >>> AnalyzerStack().pprint()
        0: (None, 'in', 19, None, None)
        1: (None, 'in', 18, None, None)
        2: (None, 'in', 17, None, None)
        3: (None, 'in', 16, None, None)
        4: (None, 'in', 15, None, None)
        5: (None, 'in', 14, None, None)
        6: (None, 'in', 13, None, None)
        7: (None, 'in', 12, None, None)
        8: (None, 'in', 11, None, None)
        9: (None, 'in', 10, None, None)
        10: (None, 'in', 9, None, None)
        11: (None, 'in', 8, None, None)
        12: (None, 'in', 7, None, None)
        13: (None, 'in', 6, None, None)
        14: (None, 'in', 5, None, None)
        15: (None, 'in', 4, None, None)
        16: (None, 'in', 3, None, None)
        17: (None, 'in', 2, None, None)
        18: (None, 'in', 1, None, None)
        19: (None, 'in', 0, None, None)
        """
        
        self.stamperObj = kwArgs.pop('stamper', stamp.Stamper())
        self.fillTo20(**kwArgs)
    
    def fillTo20(self, **kwArgs):
        """
        Makes sure there are at least 20 elements on the stack, to provide a
        context for execution.
        
        >>> obj = AnalyzerStack()
        >>> del obj[-3:]
        >>> obj.fillTo20()
        >>> obj.pprint()
        0: (None, 'in', 22, None, None)
        1: (None, 'in', 21, None, None)
        2: (None, 'in', 20, None, None)
        3: (None, 'in', 19, None, None)
        4: (None, 'in', 18, None, None)
        5: (None, 'in', 17, None, None)
        6: (None, 'in', 16, None, None)
        7: (None, 'in', 15, None, None)
        8: (None, 'in', 14, None, None)
        9: (None, 'in', 13, None, None)
        10: (None, 'in', 12, None, None)
        11: (None, 'in', 11, None, None)
        12: (None, 'in', 10, None, None)
        13: (None, 'in', 9, None, None)
        14: (None, 'in', 8, None, None)
        15: (None, 'in', 7, None, None)
        16: (None, 'in', 6, None, None)
        17: (None, 'in', 5, None, None)
        18: (None, 'in', 4, None, None)
        19: (None, 'in', 3, None, None)
        """
        
        if len(self) >= 20:
            return
        
        if len(self) == 0:
            startingCode = 0
        else:
            startingCode = self[0].relStackIndex + 1
        
        needCount = 20 - len(self)
        entryFunc = analyzer_stack_entry.AnalyzerStackEntry
        stamperFunc = self.stamperObj.stamp
        stampInfo = kwArgs.pop('stampInfo', None)
        v = []
        
        for i in range(needCount):
            stmp = stamperFunc()
            
            entry = entryFunc(
              None,
              'in',
              stmp,
              i + startingCode,
              None,
              None)
            
            if stampInfo is not None:
                stampInfo[stmp] = (None, None)
            
            v.append(entry)
        
        self[:] = list(reversed(v)) + self

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

