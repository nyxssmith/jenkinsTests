#
# refpt.py
#
# Copyright © 2007-2008, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for HistoryEntry objects referring to reference points.
"""

# Other imports
from fontio3.hints.history import historyentry
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryEntry_refPt(historyentry.HistoryEntry):
    """
    Objects representing the history of how a particular implicit zero for a
    reference point was used during executing TrueType code.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, hintsObj, hintsPC, refPtDefault):
        """
        Initializes the refPt-type HistoryEntry with the specified data.
        """
        
        super(HistoryEntry_refPt, self).__init__('refPt')
        self.hintsObj = hintsObj
        self.hintsPC = hintsPC
        self.refPtDefault = refPtDefault
    
    #
    # Private methods
    #
    
    def _makeQuint(self):
        """
        Returns a quint for this object.
        
        >>> h = _makeFakeHistoryEntry_refPt("Fred", 2, 1)
        >>> h._makeQuint()
        ('refPt', 99, 2, 1)
        """
        
        return ('refPt', self.hintsObj[0], self.hintsPC, self.refPtDefault)
    
    #
    # Public methods
    #
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object.
        
        >>> _makeFakeHistoryEntry_refPt("Fred", 2, 1).pprint()
        Implicit zero for RP1 used at opcode index 2 in Fred
        """
        
        p = pp.PP(**kwArgs)
        t = (self.refPtDefault, self.hintsPC, self.hintsObj[1].infoString)
        p("Implicit zero for RP%d used at opcode index %d in %s" % t)

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
    
    def _makeFakeHistoryEntry_refPt(infoString, PC, which):
        return HistoryEntry_refPt(_makeFakeHintObj(infoString), PC, which)

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
