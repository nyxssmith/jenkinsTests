#
# ligature_glyphtuple.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for output records in a LookupType 2 (Ligature Substitution) GSUB
subtable.
"""

# Other imports
from fontio3.opentype import glyphtuple

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning(('V0421', (), "The output list is empty."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Ligature_GlyphTuple(glyphtuple.GlyphTuple_NoShrink):
    """
    This is a GlyphTuple whose entries are identified as input glyphs.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0: xyz5
    1: xyz12
    2: xyz30
    
    >>> logger = utilities.makeDoctestLogger("mgt_iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    mgt_iv - WARNING - The output list is empty.
    True
    
    >>> _testingValues[5].isValid(logger=logger, editor=e)
    mgt_iv.[0] - ERROR - The glyph index 2.5 is not an integer.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        seq_validatefunc_partial = _validate)

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
        Ligature_GlyphTuple([4, 11, 29]),
        Ligature_GlyphTuple([5, 9]),
        Ligature_GlyphTuple([5, 3]),
        Ligature_GlyphTuple([11, 12]),
        # bad entries start here
        Ligature_GlyphTuple([]),
        Ligature_GlyphTuple([2.5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
