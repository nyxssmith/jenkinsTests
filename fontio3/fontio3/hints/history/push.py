#
# push.py
#
# Copyright © 2007-2008, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for HistoryEntry objects referring to explicit pushes.
"""

# Other imports
from fontio3.hints.history import historyentry
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryEntry_push(historyentry.HistoryEntry):
    """
    Objects representing the history of how a particular value was placed onto
    the stack during the execution of TrueType code.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, hintsObj, hintsPC, extraIndex):
        """
        Initializes the push-type HistoryEntry with the specified data.
        """
        
        super(HistoryEntry_push, self).__init__('push')
        self.hintsObj = hintsObj
        self.hintsPC = hintsPC
        self.extraIndex = extraIndex
    
    #
    # Private methods
    #
    
    def _makeQuint(self):
        """
        Returns a quint for this object.
        
        >>> h = _makeFakeHistoryEntry_push("Fred", 2, 3)
        >>> h._makeQuint()
        ('push', 99, 2, 3)
        """
        
        return ('push', self.hintsObj[0], self.hintsPC, self.extraIndex)
    
    #
    # Public methods
    #
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> _makeFakeHistoryEntry_push("Fred", 2, 3).pprint()
        Extra index 3 in PUSH opcode index 2 in Fred
        """
        
        p = pp.PP(**kwArgs)
        t = (self.extraIndex, self.hintsPC, self.hintsObj[1].infoString)
        p("Extra index %d in PUSH opcode index %d in %s" % t)

# -----------------------------------------------------------------------------

#
# Debugging support code
#

if 0:
    def __________________(): pass

if __debug__:
    # Other imports
    class _Fake(object):
        def __init__(self, s): self.infoString = s
        
    def _makeFakeHintObj(infoString, fakeID=99):
        return (fakeID, _Fake(infoString))
    
    def _makeFakeHistoryEntry_push(infoString, PC, extra):
        return HistoryEntry_push(_makeFakeHintObj(infoString), PC, extra)

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
