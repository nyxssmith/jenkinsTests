#
# glyphdict.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from input glyphs to output glyphs.
"""

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, label, **k):
    if obj == 65535:
        p.simple("Deleted glyph", label=label, **k)
    
    else:
        bnf = k.get('bestNameFunc', str)
        p.simple(bnf(obj), label=label, **k)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GlyphDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing simple maps from input glyphs to output glyphs. Note
    that glyph indices of 0xFFFF are handled specially in pprint() to print the
    string "Deleted glyph".
    
    >>> GlyphDict({14: 29, 15: 97, 4: 50, 35: 65535}).pprint(namer=namer.testingNamer())
    xyz15: xyz30
    xyz16: afii60002
    xyz36: Deleted glyph
    xyz5: xyz51
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintfunc = _ppf,
        item_prevalidatedglyphsetkeys = {65535},
        item_prevalidatedglyphsetvalues = {65535},
        item_renumberdirectkeys = True,
        item_renumberdirectvalues = True,
        item_usenamerforstr = True,
        item_valueisoutputglyph = True)
    
    # There are no fromwalker() or buildBinary() methods for this class, since
    # heavy processing is needed to convert the structures into a format that's
    # compatible with 'mort' or 'morx' tables.

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
