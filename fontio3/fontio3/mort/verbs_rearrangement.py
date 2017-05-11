#
# verbs_rearrangement.py
#
# Copyright © 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
An enumeration of the 16 different action kinds for a 'mort' rearrangement
subtable.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Verb(int, metaclass=enummeta.FontDataMetaclass):
    """
    Objects defining kinds of rearrangement ("verbs"). These are enumerated
    values.
    
    >>> Verb(4).pprint()
    Rearrangement kind: ABx => xAB
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_pprintlabel = "Rearrangement kind",
        enum_stringsdict = {
           0: "No change",
           1: "Ax => xA",
           2: "xD => Dx",
           3: "AxD => DxA",
           4: "ABx => xAB",
           5: "ABx => xBA",
           6: "xCD => CDx",
           7: "xCD => DCx",
           8: "AxCD => CDxA",
           9: "AxCD => DCxA",
          10: "ABxD => DxAB",
          11: "ABxD => DxBA",
          12: "ABxCD => CDxAB",
          13: "ABxCD => CDxBA",
          14: "ABxCD => DCxAB",
          15: "ABxCD => DCxBA"})

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
