#
# livingdeltas_dict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Living Deltas in the HVAR and VVAR tables.
"""

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class LivingDeltasDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping glyph indices to Living Deltas. These are synthesized from
    a combination of an Item Variation Store plus an (outer, inner) index map.
    They are not read from or written to binary directly; hence there are no
    from*walker() or buildBinary() methods.
    """

    #
    # Class definition variables
    #

    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_pprintlabelpresort = True,
        item_valueislivingdeltas = True)

    #
    # Methods
    #

    def _validateTightness(self):
        """
        Checks to make sure the keys are tight (that is, there are no numeric
        gaps and they start at zero). If they are not tight, an IndexError is
        raised.
        """
        
        minGlyphIndex = min(self)
        
        if minGlyphIndex:
            raise IndexError("The dictionary does not start at glyph zero!")
        
        maxGlyphIndex = max(self)
        
        if maxGlyphIndex != len(self) - 1:
            raise IndexError("There are gaps in the keys!")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


