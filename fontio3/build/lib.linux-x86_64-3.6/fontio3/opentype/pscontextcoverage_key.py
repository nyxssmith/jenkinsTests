#
# pscontextcoverage_key.py
#
# Copyright © 2009-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys used in PSContextCoverage objects.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing keys in a PSContextCoverage dict. These are tuples of
    CoverageSet objects, which (being frozensets) are immutable and thus OK
    with their use here.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0:
      xyz21
      xyz22
    1:
      xyz31
      xyz32
    2:
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
        Key([CS([20, 21]), CS([30, 31]), CS([94, 96, 97])]),)
    
    del CS

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
