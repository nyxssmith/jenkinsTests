#
# strokeweight.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the strokeWeight field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    -7: "Ultra Thin",
    -6: "Extra Thin",
    -5: "Thin",
    -4: "Extra Light",
    -3: "Light",
    -2: "Demilight",
    -1: "Semilight",
     0: "Book, text, regular, etc.",
     1: "Semibold (Medium, when darker than Book)",
     2: "Demibold",
     3: "Bold",
     4: "Extra Bold",
     5: "Black",
     6: "Extra Black",
     7: "Ultra Black, or Ultra"}

# -----------------------------------------------------------------------------

#
# Classes
#

class StrokeWeight(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing stroke weights in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(StrokeWeight(4))
    Extra Bold
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> StrokeWeight(4).isValid(logger=logger, editor=e)
    True
    
    >>> StrokeWeight(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown weight",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2203')

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
    if __debug__:
        _test()
