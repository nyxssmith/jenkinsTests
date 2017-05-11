#
# storage.py
#
# Copyright © 2007-2008, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for HistoryEntry objects referring to storage locations.
"""

# Other imports
from fontio3.hints.history import historyentry
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryEntry_storage(historyentry.HistoryEntry):
    """
    Objects representing the history of how a particular storage location index
    was used during executing TrueType code.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, hintsObj, hintsPC, storageDefault):
        """
        Initializes the storage-type HistoryEntry with the specified data.
        """
        
        super(HistoryEntry_storage, self).__init__('storage')
        self.hintsObj = hintsObj
        self.hintsPC = hintsPC
        self.storageDefault = storageDefault
    
    #
    # Private methods
    #
    
    def _makeQuint(self):
        """
        Returns a quint for this object.
        
        >>> h = _makeFakeHistoryEntry_storage("Fred", 2, 28)
        >>> h._makeQuint()
        ('storage', 99, 2, 28)
        """
        
        return ('storage', self.hintsObj[0], self.hintsPC, self.storageDefault)
    
    #
    # Public methods
    #
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> _makeFakeHistoryEntry_storage("Fred", 2, 28).pprint()
        Implicit zero for storage location 28 used at opcode index 2 in Fred
        """
        
        p = pp.PP(**kwArgs)
        t = (self.storageDefault, self.hintsPC, self.hintsObj[1].infoString)
        p("Implicit zero for storage location %d used at opcode index %d in %s" % t)

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
    
    def _makeFakeHistoryEntry_storage(infoString, PC, which):
        return HistoryEntry_storage(_makeFakeHintObj(infoString), PC, which)

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
