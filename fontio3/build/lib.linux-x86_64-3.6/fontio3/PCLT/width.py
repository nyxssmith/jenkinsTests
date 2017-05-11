#
# width.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the width field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    0: "Normal",
    1: "Condensed",
    2: "Compressed, extra condensed",
    3: "Extra compressed",
    4: "Ultra compressed",
    6: "Expanded, extended",
    7: "Extra expanded, extra extended"}

# -----------------------------------------------------------------------------

#
# Classes
#

class Width(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing widths in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(Width(4))
    Ultra compressed
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Width(4).isValid(logger=logger, editor=e)
    True
    
    >>> Width(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown width",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2207')

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
