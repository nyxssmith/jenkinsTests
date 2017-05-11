#
# pairglyphs_key.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 GPOS pair positioning tables.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects used as keys in a PairGlyphs dict; these are pairs (i.e. tuples) of
    glyph indices.

    Objects of this class don't have fromwalker() or buildBinary() methods;
    those are handled at the higher level of the PairGlyphs object itself.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0: xyz9
    1: xyz16
    
    >>> logger = utilities.makeDoctestLogger("pairglyphs_key")
    >>> e = utilities.fakeEditor(4500)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    pairglyphs_key.[1] - ERROR - Glyph index 5000 too large.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_fixedlength = 2)

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
      Key([8, 15]),
      Key([8, 20]),
      Key([10, 20]),
      Key([4000, 5000]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
