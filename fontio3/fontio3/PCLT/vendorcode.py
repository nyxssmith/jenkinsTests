#
# vendorcode.py
#
# Copyright © 2009-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the vendorCode field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
  ord(b'A'): "Adobe",
  ord(b'B'): "Bitstream",
  ord(b'C'): "Agfa Corporation",
  ord(b'H'): "Bigelow & Holmes",
  ord(b'L'): "Linotype",
  ord(b'M'): "Monotype"}

# -----------------------------------------------------------------------------

#
# Classes
#

class VendorCode(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing vendor codes in a PCLT table. These are single chars.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(VendorCode(ord(b'M')))
    Monotype
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> VendorCode(ord(b'M')).isValid(logger=logger, editor=e)
    True
    
    >>> VendorCode(ord(b'Q')).isValid(logger=logger, editor=e)
    val - ERROR - Value 81 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown vendor",
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
