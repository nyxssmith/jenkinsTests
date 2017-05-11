#
# vendor2.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the vendor2 field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    1: "Agfa Corporation",
    2: "Bitstream",
    3: "Linotype",
    4: "Monotype",
    5: "Adobe",
    6: "(font repackagers)",
    7: "(vendors of unique typefaces)"}

# -----------------------------------------------------------------------------

#
# Classes
#

class Vendor2(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing vendor2s in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(Vendor2(4))
    Monotype
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Vendor2(4).isValid(logger=logger, editor=e)
    True
    
    >>> Vendor2(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown vendor2",
        enum_stringsdict = _strings)

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
