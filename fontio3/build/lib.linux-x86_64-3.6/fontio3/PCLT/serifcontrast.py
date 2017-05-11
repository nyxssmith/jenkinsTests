#
# serifcontrast.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the serifContrast field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    1: "Sans-serif/Monoline",
    2: "Serif/Contrasting"}

# -----------------------------------------------------------------------------

#
# Classes
#

class SerifContrast(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing serif contrasts in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(SerifContrast(1))
    Sans-serif/Monoline
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> SerifContrast(1).isValid(logger=logger, editor=e)
    True
    
    >>> SerifContrast(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown serif contrast",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2209')

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
