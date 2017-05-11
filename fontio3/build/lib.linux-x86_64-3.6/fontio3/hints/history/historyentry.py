#
# historyentry.py
#
# Copyright © 2007-2008, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Abstract superclass for all HistoryEntry objects. These are collected together
into a History object (q.v.)
"""

# -----------------------------------------------------------------------------

#
# Classes
#

class HistoryEntry(object):
    """
    Abstract superclass for history entry objects. These objects are immutable.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, kind):
        """
        This method is usually called by the subclasses as part of their own
        __init__ methods.
        """
        
        self.kind = kind
        self.cachedQuint = None
    
    #
    # Special methods
    #
    
    def __copy__(self): return self  # all HistoryEntry objects are immutable
    def __deepcopy__(self, memo=None): return self  # ditto
    
    def __eq__(self, other):
        if self is other:
            return True
        
        try:
            return self.quint() == other.quint()
        except AttributeError:
            return False
    
    def __hash__(self): return hash(self.quint())
    
    def __ne__(self, other):
        if self is other:
            return False
        
        try:
            return self.quint() != other.quint()
        except AttributeError:
            return True
    
    #
    # Public methods
    #
    
    def leafIterator(self): yield self
    
    def quint(self):
        """
        Returns a hashable object representing this entry.
        """
        
        if self.cachedQuint is None:
            self.cachedQuint = self._makeQuint()
        
        return self.cachedQuint
    
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
    _test()
