#
# op.py
#
# Copyright © 2007, 2008 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for HistoryEntry objects referring to the results of TrueType
operations.
"""

# Other imports
from fontio3.hints import common
from fontio3.hints.history import historyentry
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Constants
#

opcodeToNameMap = common.opcodeToNameMap

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryEntry_op(historyentry.HistoryEntry):
    """
    Objects representing the history of how a particular value was placed onto
    the stack during the execution of TrueType code, specifically by the
    execution of an opcode with one or more operands. The histories of the
    operands are themselves also maintained, recursively if needed.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, hintsObj, hintsPC, opcode, historyIterable):
        """
        Initializes the op-type HistoryEntry with the specified data.
        """
        
        super(HistoryEntry_op, self).__init__('op')
        self.hintsObj = hintsObj
        self.hintsPC = hintsPC
        self.opcode = opcode
        self.historyTuple = tuple(historyIterable)
    
    #
    # Private methods
    #
    
    def _makeQuint(self):
        """
        Returns a quint for this object.
        
        >>> fakeHint = _makeFakeHintObj("Fred", 88)
        >>> pushHist1 = _makeFakeHistoryEntry_push("George", 12, 9)
        >>> pushHist2 = _makeFakeHistoryEntry_push("George", 12, 10)
        >>> obj = HistoryEntry_op(fakeHint, 15, 0x63, (pushHist1, pushHist2))
        >>> obj.quint()
        ('op', 88, 15, 99, (('push', 99, 12, 9), ('push', 99, 12, 10)))
        """
        
        q = tuple(obj.quint() for obj in self.historyTuple)
        return ('op', self.hintsObj[0], self.hintsPC, self.opcode, q)
    
    #
    # Public methods
    #
    
    def leafIterator(self):
        """
        Returns a generator over the leaf nodes of the historyTuple.
        
        >>> fakeHint = _makeFakeHintObj("Fred", 88)
        >>> pushHist1 = _makeFakeHistoryEntry_push("George", 12, 9)
        >>> pushHist2 = _makeFakeHistoryEntry_push("George", 12, 10)
        >>> pushHist3 = _makeFakeHistoryEntry_push("George", 12, 11)
        >>> obj = HistoryEntry_op(fakeHint, 15, 0x63, (pushHist1, pushHist2))
        >>> for x in obj.leafIterator(): print(x.quint())
        ('push', 99, 12, 9)
        ('push', 99, 12, 10)
        >>> obj2 = HistoryEntry_op(fakeHint, 22, 0x61, (obj, pushHist3))
        >>> for x in obj2.leafIterator(): print(x.quint())
        ('push', 99, 12, 9)
        ('push', 99, 12, 10)
        ('push', 99, 12, 11)
        """
        
        for obj in self.historyTuple:
            for subObj in obj.leafIterator():
                yield subObj
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object. Standard arguments are:
        
            indent          An integer representing the number of spaces in the
                            current indent. Default is 0.
            
            indentDelta     An integer representing the number of extra spaces
                            to add at each indent level. Default is 2.
            
            stream          The stream to which the output is to be written.
                            Default is sys.stdout.
        
        >>> fakeHint = _makeFakeHintObj("Fred")
        >>> HistoryEntry_op(fakeHint, 20, 0x4B, []).pprint()
        Result of opcode MPPEM at index 20 in Fred
        >>> pushHist1 = _makeFakeHistoryEntry_push("George", 12, 9)
        >>> pushHist2 = _makeFakeHistoryEntry_push("George", 12, 10)
        >>> HistoryEntry_op(fakeHint, 15, 0x63, (pushHist1, pushHist2)).pprint()
        Result of opcode MUL at index 15 in Fred, with inputs:
          Extra index 9 in PUSH opcode index 12 in George
          Extra index 10 in PUSH opcode index 12 in George
        """
        
        p = pp.PP(**kwArgs)
        t = (opcodeToNameMap[self.opcode], self.hintsPC, self.hintsObj[1].infoString)
        
        if self.historyTuple:
            s = "Result of opcode %s at index %d in %s, with inputs" % t
            p.sequence_deep(self.historyTuple, label=s)
        else:
            p("Result of opcode %s at index %d in %s" % t)

# -----------------------------------------------------------------------------

#
# Debugging support code
#

if 0:
    def __________________(): pass

if __debug__:
    # Other imports
    from fontio3.hints.history import historylist, push
    
    class _Fake(object):
        def __init__(self, s): self.infoString = s
        
    def _makeFakeHintObj(infoString, fakeID=99):
        return (fakeID, _Fake(infoString))
    
    def _makeFakeHistoryEntry_push(infoString, PC, extra):
        return push.HistoryEntry_push(_makeFakeHintObj(infoString), PC, extra)
    
    def _makeFakeHistoryList(*args):
        return historylist.HistoryList(args)

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

