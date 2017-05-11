#
# stamp.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for unique, monotonically increasing numeric stamps that may be used to
identify when data changes.
"""

# -----------------------------------------------------------------------------

#
# Classes
#

class Stamper:
    """
    Objects that can keep track of what changes in a large collection of values
    so merging can omit large swaths of unneeded copying.
    
    >>> s = Stamper(start=4, delta=3)
    >>> s.stamp()
    4
    >>> s.stamp()
    7
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, start=0, delta=1):
        """
        Initializes the Stamper with the specified start value.
        """
        
        assert delta > 0
        self._nextStamp = start
        self._delta = delta
    
    #
    # Public methods
    #
    
    def stamp(self):
        """
        Returns the next stamp value, and increments the internal value for the
        next call.
        """
        
        n = self._nextStamp
        self._nextStamp += self._delta
        return n

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
