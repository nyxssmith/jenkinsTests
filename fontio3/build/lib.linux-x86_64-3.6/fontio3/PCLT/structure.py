#
# structure.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the structure field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
    0: "Solid (normal, black)",
    1: "Outline (hollow)",
    2: "Inline (incised, engraved)",
    3: "Contour, edged (antique, distressed)",
    4: "Solid with shadow",
    5: "Outline with shadow",
    6: "Inline with shadow",
    7: "Contour, or edged, with shadow",
    8: "Pattern filled",
    9: "Pattern filled #1 (when more than one pattern)",
   10: "Pattern filled #2 (when more than two patterns)",
   11: "Pattern filled #3 (when more than three patterns)",
   12: "Pattern filled with shadow",
   13: "Pattern filled with shadow #1 (when more than one pattern or shadow)",
   14: "Pattern filled with shadow #2 (when more than two patterns or shadows)",
   15: "Pattern filled with shadow #3 (when more than three patterns or shadows)",
   16: "Inverse",
   17: "Inverse with border"}

# -----------------------------------------------------------------------------

#
# Classes
#

class Structure(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing structures in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(Structure(4))
    Solid with shadow
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Structure(4).isValid(logger=logger, editor=e)
    True
    
    >>> Structure(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown structure",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2206')

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
