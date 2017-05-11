#
# baselinekinds.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Constant definitions for the 'bsln' table.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Constants
#

DEFAULT = "(reserved)"

STRINGS = {
  0: "Roman",
  1: "Ideographic (centered)",
  2: "Ideographic (low)",
  3: "Hanging",
  4: "Mathematical"}

# -----------------------------------------------------------------------------

#
# Classes
#

class BaselineKind(int, metaclass=enummeta.FontDataMetaclass):
    """
    Definitions of the 32 AAT baseline kinds.
    
    >>> print(BaselineKind(2))
    Ideographic (low)
    >>> BaselineKind(0).pprint()
    Baseline kind: Roman
    >>> print(BaselineKind(22))
    (reserved)
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_pprintlabel = "Baseline kind",
        enum_stringsdefault = DEFAULT,
        enum_stringsdict = STRINGS)

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
