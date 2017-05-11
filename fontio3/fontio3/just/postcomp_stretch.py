#
# postcomp_stretch.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for action type 3 (unconditionial add) in a 'just' postcompensation
table.
"""

# Other imports
from fontio3.fontdata import minimalmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Postcomp_Stretch(object, metaclass=minimalmeta.FontDataMetaclass):
    """
    Objects representing unconditional add actions. These are minimal objects;
    they have no attributes or data, only an identifying string (and a "kind"
    class constant).
    
    >>> Postcomp_Stretch().pprint()
    Stretch glyph
    
    >>> len(Postcomp_Stretch().binaryString())
    0
    """
    
    #
    # Class definition variables
    #
    
    minSpec = dict(
        minimal_string = "Stretch glyph")
    
    kind = 3  # Class constant for this action kind
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        return cls()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        return cls()
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        pass

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
      Postcomp_Stretch(),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
