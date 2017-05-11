#
# glyphpair.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys for simple pairwise kerning (in 'kerx' tables).
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphPair(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a pair of glyphs. These are tuples, and are used as
    keys in Format0 objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0: xyz15
    1: xyz24
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_fixedlength = 2)
    
    # The fromwalker and buildBinary methods are provided higher up.

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        GlyphPair([14, 23]),
        GlyphPair([14, 96]),
        GlyphPair([18, 38]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
