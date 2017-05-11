#
# ttcontourgroup.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for logically connected groups of TTContour objects, where the
connection represents interior opposite-chirality groups. These objects can be
used to construct hierarchical collections of contours representing high-level
parts of a glyph.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.glyf import ttcontour

# -----------------------------------------------------------------------------

#
# Classes
#

class TTContourGroup(ttcontour.TTContour):
    """
    A TTContourGroup is a subclass of TTContour. It comprises a single
    contour at the top level, and a single attribute, children, which is
    a list of all the TTContour or TTContourGroup objects contained
    directly within it (in fact, it is a TTContourGroups object). Since
    TTContourGroup objects can contain other TTContourGroup objects, you
    can see how this class allows arbitrarily deep structures of
    contours.
    
    Note that by this definition, the bounds and extrema for a TTContourGroup
    are the same as those for this topmost contour.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        children = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue = True))
    
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
