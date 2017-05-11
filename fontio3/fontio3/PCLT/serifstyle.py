#
# serifstyle.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the serifStyle field in PCLT tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_strings = {
     0: "Sans-serif Square",
     1: "Sans-serif Round",
     2: "Serif Line",
     3: "Serif Triangle",
     4: "Serif Swath",
     5: "Serif Block",
     6: "Serif Bracket",
     7: "Rounded Bracket",
     8: "Flair Serif, Modified Sans-serif",
     9: "Script Nonconnecting",
    10: "Script Joining",
    11: "Script Calligraphic",
    12: "Script Broken Letter"}

# -----------------------------------------------------------------------------

#
# Classes
#

class SerifStyle(int, metaclass=enummeta.FontDataMetaclass):
    """
    Values representing serif styles in a PCLT table. These are ints.
    
    Note that there are no fromwalker() or buildBinary() methods here; this is
    handled at the PCLT level.
    
    >>> print(SerifStyle(1))
    Sans-serif Round
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> SerifStyle(1).isValid(logger=logger, editor=e)
    True
    
    >>> SerifStyle(19).isValid(logger=logger, editor=e)
    val - ERROR - Value 19 is not a valid enum value.
    False
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_stringsdefault = "Unknown serif style",
        enum_stringsdict = _strings,
        enum_validatecode_badenumvalue = 'E2200')

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
