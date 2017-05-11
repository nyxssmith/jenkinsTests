#
# alternate_glyphset.py
#
# Copyright © 2007-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for output records in a Lookup Type 3 (alternates) GSUB table.
"""

# Other imports
from fontio3.opentype import glyphset

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0426',
          (),
          "No alternates are specified."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Alternate_GlyphSet(glyphset.GlyphSet):
    """
    This is a GlyphSet whose entries are identified as output glyphs.
    
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> _testingValues[0].pprint(namer=nm)
    xyz9 (glyph 8)
    afii60002 (glyph 97)
    
    >>> logger = utilities.makeDoctestLogger("ags_iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    ags_iv - WARNING - No alternates are specified.
    True
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    ags_iv.element - ERROR - The glyph index 2.5 is not an integer.
    False
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_isoutputglyph = True,
        set_showpresorted = True,
        set_validatefunc_partial = _validate)

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
        Alternate_GlyphSet([97, 8]),
        Alternate_GlyphSet([15, 16, 17]),
        Alternate_GlyphSet([40, 30]),
        # bad entries start here
        Alternate_GlyphSet([]),
        Alternate_GlyphSet([2.5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
