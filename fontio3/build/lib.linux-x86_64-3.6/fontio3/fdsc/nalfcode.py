#
# nalfcode.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the non-alphabetic code enumeration.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Constants
#

DEFAULT = "(unknown)"

STRINGS = {
  0: "Alphabetic",
  1: "Dingbats",
  2: "Pi characters",
  3: "Fleurons",
  4: "Decorative borders",
  5: "International symbols",
  6: "Math symbols"}

# -----------------------------------------------------------------------------

#
# Classes
#

class NalfCode(int, metaclass=enummeta.FontDataMetaclass):
    """
    Objects representing different kinds of non-alphabeticness. These are ints
    interpreted as enumerated values.
    
    >>> print(_testingValues[0])
    Alphabetic (0)
    
    >>> _testingValues[1].pprint()
    Value: Decorative borders (4)
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_annotatevalue = True,
        enum_stringsdefault = DEFAULT,
        enum_stringsdict = STRINGS)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        NalfCode(0),
        NalfCode(4),
        
        # bad values start here
        
        NalfCode(23))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
