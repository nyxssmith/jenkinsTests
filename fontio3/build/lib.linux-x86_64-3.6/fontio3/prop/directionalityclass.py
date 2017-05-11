#
# directionalityclass.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions for directionality classes as used in the AAT 'prop' table.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Constants
#

names = {
   0: "Strong (left-to-right)",
   1: "Strong (right-to-left, non-Arabic)",
   2: "Arabic letters (right-to-left)",
   3: "European number",
   4: "European number separator",
   5: "European number terminator",
   6: "Arabic number",
   7: "Common number separator",
   8: "Block separator",
   9: "Segment separator",
  10: "Whitespace",
  11: "Other neutrals"}

names.update({i: "Directionality class %d" % (i,) for i in range(12, 32)})

# -----------------------------------------------------------------------------

#
# Classes
#

class DirectionalityClass(int, metaclass=enummeta.FontDataMetaclass):
    """
    Integer values defining various Unicode directionality classes.
    
    >>> DirectionalityClass(6).pprint()
    Directionality class: Arabic number
    
    >>> print(DirectionalityClass(10))
    Whitespace
    
    >>> print(DirectionalityClass(23))
    Directionality class 23
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_pprintlabel = "Directionality class",
        enum_stringsdict = names)

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
