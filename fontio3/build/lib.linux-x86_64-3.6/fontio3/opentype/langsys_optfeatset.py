#
# langsys_optfeatset.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the optional features object in a LangSys object.
"""

# Other imports
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class OptFeatSet(set, metaclass=setmeta.FontDataMetaclass):
    """
    These are simple sets that show their members sorted. There are no
    fromwalker() or buildBinary() methods here; that is handled at the LangSys
    level.
    
    >>> _testingValues[1].pprint()
    abcd0001
    size0002
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_pprintfunc = (
          lambda p, x:
          p(ascii(x)[2:-1])),  # strip the "b''"
        set_showsorted = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        OptFeatSet([]),
        OptFeatSet([b'abcd0001', b'size0002']),
        OptFeatSet([b'abcd0002', b'size0001']))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
