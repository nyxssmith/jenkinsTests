#
# pschainglyph_glyphtuple.py
#
# Copyright © 2009-2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for components of Keys used in PSChainGlyph objects.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    This is a tuple of glyph indices. It is one of the components in a Key.
    
    There are no fromwalker or buildBinary methods; that is handled at the
    higher level of the PSChainGlyph object itself.
    
    >>> t = GlyphTuple([14, 60, 97])
    >>> t.setNamer(namer.testingNamer())
    >>> print(t)
    (xyz15, xyz61, afii60002)
    """
    
    #
    # Class definition variables
    #
    
    __hash__ = tuple.__hash__
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_fixedlength = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        GlyphTuple([]),
        GlyphTuple([25, 40]),
        GlyphTuple([80]),
        GlyphTuple([85, 86]),
        GlyphTuple([25, 50]),
        GlyphTuple([30, 10, 30]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
