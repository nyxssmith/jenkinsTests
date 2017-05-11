#
# uvs_entry_set.py
#
# Copyright © 2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sets of default values for a single UVS.
"""

# Other imports
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, n):
    if n < 0x10000:
        s = "U+%04X" % (n,)
    else:
        s = "U+%06X" % (n,)
    
    p(s)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class UVS_Entry_Set(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing default values for a single Unicode Variation Selector
    value. These are sets of Unicode scalar values.
    
    Note that this class does not have ``buildBinary()`` or ``fromwalker()``
    methods; that functionality is handled at a higher level.
    
    >>> _testingValues[1].pprint()
    U+4E01
    U+4E08
    
    >>> _testingValues[2].pprint()
    U+5225
    U+022F43
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_pprintfunc = _ppf,
        set_showpresorted = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        UVS_Entry_Set(),
        
        UVS_Entry_Set([0x4E01, 0x4E08]),
        
        UVS_Entry_Set([0x5225, 0x22F43]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
