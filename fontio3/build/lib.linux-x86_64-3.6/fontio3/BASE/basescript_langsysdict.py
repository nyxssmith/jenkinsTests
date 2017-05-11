#
# basescript_langsysdict.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Script-specific baseline data from a 'BASE' table.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class LangSysDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping LangSys tags to MinMax objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    LangSys 'enUS':
      Minimum coordinate:
        Coordinate: -20
      Maximum coordinate:
        Coordinate: 0
        Glyph: xyz26
        Point: 9
    LangSys 'span':
      Minimum coordinate:
        Coordinate: -10
        Device table:
          Tweak at 12 ppem: -5
          Tweak at 13 ppem: -3
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 2
          Tweak at 20 ppem: 3
      Maximum coordinate:
        Coordinate: 0
        Glyph: xyz26
        Point: 9
      Feature-specific MinMax values:
        Feature 'abcd':
          Minimum coordinate:
            Coordinate: 0
          Maximum coordinate:
            Coordinate: 15
            Device table:
              Tweak at 12 ppem: -2
              Tweak at 14 ppem: -1
              Tweak at 18 ppem: 1
        Feature 'wxyz':
          Maximum coordinate:
            Coordinate: -10
            Glyph: xyz15
            Point: 12
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda k:
          "LangSys '%s'" % (utilities.ensureUnicode(k),)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.BASE import minmax
    from fontio3.utilities import namer
    
    _mmv = minmax._testingValues
    
    _testingValues = (
      LangSysDict(),
      LangSysDict({
        b'enUS': _mmv[1],
        b'span': _mmv[2]}))
    
    del _mmv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
