#
# prep.py
#
# Copyright © 2007-2008, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType pre-programs.
"""

# Other imports
from fontio3.hints import hints_tt

# -----------------------------------------------------------------------------

#
# Classes
#

class Prep(hints_tt.Hints):
    """
    Objects representing 'prep' tables for TrueType fonts. These are actually
    just Hints objects with a prep-specific infoString.
    
    >>> Prep.frombytes(utilities.fromhex("00 01")).pprint()
    0000 (0x000000): SVTCA[y]
    0001 (0x000001): SVTCA[x]
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, iterable=None, **kwArgs):
        """
        Initializes the object as specified.
        
        >>> p = Prep.frombytes(bytes([0, 1]))
        >>> p.pprint()
        0000 (0x000000): SVTCA[y]
        0001 (0x000001): SVTCA[x]
        >>> p.infoString
        'Prep table'
        """
        
        d = kwArgs.copy()
        d['infoString'] = "Prep table"
        super(Prep, self).__init__(iterable, **d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
