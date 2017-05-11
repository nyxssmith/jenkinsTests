#
# glyph_dict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for PointDict objects associated with particular glyph indices.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.gvar import point_dict
    
# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    These are dicts mapping glyph indices to PointDict objects. Conceptually
    they gather all the variation information for the whole 'glyf' table into
    a single place, organized by glyph index.
    
    Note that this is an organizational helper class; there are no specific
    buildBinary() or fromwalker() methods here. Those tasks are handled by the
    Gvar object itself.
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

