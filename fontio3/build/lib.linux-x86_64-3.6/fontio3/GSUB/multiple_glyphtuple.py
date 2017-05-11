#
# multiple_glyphtuple.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for output records in a LookupType 2 (Multiple Substitution) GSUB
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
        logger.warning((
          'V0421',
          (),
          "The output list is empty; the OpenType spec explicitly "
          "prohibits using a Multiple Lookup to remove glyphs."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Multiple_GlyphTuple(glyphtuple.GlyphTuple):
    """
    This is a GlyphTuple whose entries are identified as output glyphs.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0: afii60002
    1: xyz9
    
    >>> logger = utilities.makeDoctestLogger("mgt_iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    mgt_iv - WARNING - The output list is empty; the OpenType spec explicitly prohibits using a Multiple Lookup to remove glyphs.
    True
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    mgt_iv.[0] - ERROR - The glyph index 2.5 is not an integer.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_isoutputglyph = True,
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
        Multiple_GlyphTuple([97, 8]),
        Multiple_GlyphTuple([15, 16, 17]),
        Multiple_GlyphTuple([40, 30]),
        # bad entries start here
        Multiple_GlyphTuple([]),
        Multiple_GlyphTuple([2.5]),
        Multiple_GlyphTuple([19]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
