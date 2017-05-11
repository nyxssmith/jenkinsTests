#
# kindnamesenum.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Enumerated values for the various KindName kinds.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_namesDict = {
    0: "Universal name",
    1: "Apple name",
    2: "Adobe name",
    3: "AFII name",
    4: "Unicode name",
   64: "Japanese CID",
   65: "Traditional Chinese CID",
   66: "Simplified Chinese CID",
   67: "Korean CID",
   68: "Version history note index in 'name' table",
   69: "Designer's short name index in 'name' table",
   70: "Designer's long name index in 'name' table",
   71: "Designer's usage notes index in 'name' table",
   72: "Designer's historical notes index in 'name' table"}

for i in range(128):
    if i not in _namesDict:
        _namesDict[i] = "Unknown name"

# -----------------------------------------------------------------------------

#
# Classes
#

class KindNamesEnum(int, metaclass=enummeta.FontDataMetaclass):
    """
    Instances of this class are ints whose actual interpretation is a string
    representing the KindName kind. They are used as keys in a KindNames
    object.
    
    >>> print(KindNamesEnum(0))
    Universal name (0)
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_annotatevalue = True,
        enum_stringsdict = _namesDict)

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
