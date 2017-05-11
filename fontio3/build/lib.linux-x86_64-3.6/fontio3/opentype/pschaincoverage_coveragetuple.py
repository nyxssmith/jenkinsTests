#
# pschaincoverage_coveragetuple.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for CoverageTuples, which are components of a Key for a
PSChainCoverage object.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class CoverageTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    This is a tuple of CoverageSet objects. It is one of the components in a
    Key.
    
    There are no fromwalker or buildBinary methods; that is handled at the
    higher level of the PSChainCoverage object itself.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    0:
      xyz31
      xyz32
    1:
      afii60001
      afii60002
      xyz95
    """
    
    #
    # Class definition variables
    #
    
    __hash__ = tuple.__hash__
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_usenamerforstr = True,
        seq_fixedlength = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import coverageset
    from fontio3.utilities import namer
    
    CS = coverageset.CoverageSet
    
    _testingValues = (
        CoverageTuple([CS([20, 21]), CS([30, 31])]),
        CoverageTuple([CS([30, 31]), CS([94, 96, 97])]),
        CoverageTuple([CS([94, 96, 97]), CS([20, 30, 40])]))
    
    del CS

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
