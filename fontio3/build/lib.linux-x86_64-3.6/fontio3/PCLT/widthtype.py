#
# widthtype.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the widthType field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    -5: "Ultra Compressed",
    -4: "Extra Compressed",
    -3: "Compressed, or Extra Condensed",
    -2: "Condensed",
    -1: "Slightly Condensed",
     0: "Normal",
     1: "Slightly Expanded",
     2: "Expanded",
     3: "Extended, or Extra Expanded",
     4: "Extra Extended",
     5: "Ultra Extended"}

# -----------------------------------------------------------------------------

#
# Classes
#

class WidthType(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing width types in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(WidthType(4))
    Extra Extended
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> WidthType(4).isValid(logger=logger, editor=e)
    True
    
    >>> WidthType(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown width type",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2211')

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
