#
# glyphtuple.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for tuples of glyph indices. Instances of the two classes defined in
this module are used as keys or values in a GlyphTupleDict (q.v.)
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphTupleInput(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a tuple of glyph indices. These are used as keys in a
    GlyphTupleDict object. Their semantic is that of input glyphs, so they will
    be included in a gatheredInputGlyphs() call.
    
    >>> obj = GlyphTupleInput((14, 55, 97))
    >>> print(obj)
    (14, 55, 97)
    
    >>> obj.setNamer(namer.testingNamer())
    >>> print(obj)
    (xyz15, xyz56, afii60002)
    
    >>> obj.pprint()  # remember, namer has already been set for obj
    0: xyz15
    1: xyz56
    2: afii60002
    
    >>> sorted(obj.gatheredInputGlyphs())
    [14, 55, 97]
    
    >>> sorted(obj.gatheredOutputGlyphs())
    []
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_maxcontextfunc = len)

# -----------------------------------------------------------------------------

class GlyphTupleOutput(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a tuple of glyph indices. These are used as values in
    a GlyphTupleDict object. Their semantic is that of output glyphs, so they
    will be included in a gatheredOutputGlyphs() call.
    
    >>> obj = GlyphTupleOutput((14, 55, 97))
    >>> print(obj)
    (14, 55, 97)
    
    >>> obj.setNamer(namer.testingNamer())
    >>> print(obj)
    (xyz15, xyz56, afii60002)
    
    >>> obj.pprint()  # remember, namer has already been set for obj
    0: xyz15
    1: xyz56
    2: afii60002
    
    >>> sorted(obj.gatheredInputGlyphs())
    []
    
    >>> sorted(obj.gatheredOutputGlyphs())
    [14, 55, 97]
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_isoutputglyph = True,
        item_prevalidatedglyphset = {65535},
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_maxcontextfunc = len)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
