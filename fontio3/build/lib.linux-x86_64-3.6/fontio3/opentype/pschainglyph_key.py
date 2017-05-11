#
# pschainglyph_key.py
#
# Copyright © 2009-2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Keys used in PSChainGlyph objects.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    This is the type of object used as keys in a PSChainGlyph table. It is a
    tuple of GlyphTuple objects. (Perhaps we can use the new python NamedTuple
    at some point to identify the members of the Key. We CANNOT use a
    simplemeta object, because the key has to be immutable).
    
    The [0] element is the backtrack, the [1] element is the input sequence,
    and the [2] element is the lookahead. Note that the order of glyphs in the
    [0] element is the same as the order in the [1] and [2] elements: that is,
    the "natural" order. The reversal in the binary data is handled internally,
    and the client doesn't have to worry about it.
    
    There are no fromwalker or buildBinary methods; that is handled at the
    higher level of the PSChainGlyph object itself.
    
    >>> obj = _testingValues[3].__deepcopy__()
    >>> obj.setNamer(namer.testingNamer())
    >>> print(obj)
    ((xyz26, xyz41), (xyz81,), (xyz86, xyz87)), Relative order = 0
    """
    
    #
    # Class definition variables
    #
    
    __hash__ = tuple.__hash__
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_usenamerforstr = True,
        seq_fixedlength = 3)
    
    attrSpec = dict(
        ruleOrder = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Relative order",
            attr_validatefunc = valassist.isNumber))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import pschainglyph_glyphtuple
    from fontio3.utilities import namer
    
    gtv = pschainglyph_glyphtuple._testingValues
    
    _testingValues = (
        Key([gtv[0], gtv[1], gtv[2]], ruleOrder=1),
        Key([gtv[3], gtv[4], gtv[0]]),
        Key([gtv[0], gtv[5], gtv[0]]),
        Key([gtv[1], gtv[2], gtv[3]]))
    
    del gtv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
