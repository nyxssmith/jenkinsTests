#
# extenders.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for extender glyph sets, part of the 'JSTF' table.
"""

# Other imports
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Extenders(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing sets of glyph indices.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60002
    xyz16
    xyz3
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_isoutputglyph = True,
        item_renumberdirect = True,
        item_usenamerforstr = True,
        set_maxcontextfunc = (lambda obj: 1),
        set_showsorted = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Extenders object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0003 0002 000F 0061                      |.......a        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", len(self))
        w.addGroup("H", sorted(self))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an Extenders object from the specified walker.
        
        >>> fb = Extenders.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        return cls(w.group("H", w.unpack("H")))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        Extenders(),
        Extenders({15, 2, 97}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
