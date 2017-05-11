#
# reverse_key.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Keys used in a Reverse object.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#
    
class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    This is the type of object used as keys in a Reverse table. It is a triple
    of objects: CoverageTuple, CoverageSet, and CoverageTuple. (Perhaps we can
    use the new python NamedTuple at some point to identify the members of the
    Key. We CANNOT use a simplemeta object, because the key has to be
    immutable).

    The [0] element is the backtrack, the [1] element is the input sequence,
    and the [2] element is the lookahead. Note that the order of CoverageSets
    in the [0] element is the same as the order in the [1] and [2] elements:
    that is, the "natural" order. The reversal in the binary data is handled
    internally, and the client doesn't have to worry about it.

    There are no fromwalker or buildBinary methods; that is handled at the
    higher level of the PSChainCoverage object itself.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Backtrack:
      0:
        xyz21
        xyz22
      1:
        xyz31
        xyz32
    Input:
      xyz51
      xyz52
      xyz54
      xyz57
      xyz58
    Lookahead:
      0:
        afii60001
        afii60002
        xyz95
      1:
        xyz21
        xyz31
        xyz41
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda i:
          ["Backtrack", "Input", "Lookahead"][i]),
        item_usenamerforstr = True,
        seq_fixedlength = 3)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GSUB import reverse_coveragetuple
    from fontio3.opentype import coverageset
    from fontio3.utilities import namer
    
    kIn = coverageset.CoverageSet([50, 51, 53, 56, 57])
    ctv = reverse_coveragetuple._testingValues
    
    _testingValues = (
        Key([ctv[0], kIn, ctv[1]]),)
    
    del kIn, ctv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
