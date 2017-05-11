#
# forcepos.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for classes that ensure values are positive (e.g. usWinDescent).
"""

from fontio3.fontdata import valuemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class UInt16(int, metaclass=valuemeta.FontDataMetaclass):
    """
    """
    
    valueSpec = dict(
        value_representsy = True,
        value_scales = True)
    
    #
    # Methods
    #
    
    def __new__(cls, n):
        value = min(abs(n), 0xFFFF)
        return int.__new__(cls, value)
    
    def buildBinary(self, w, **kwArgs):
        """
        """
        
        w.add("H", self)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        return cls(w.unpack("H"))

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

