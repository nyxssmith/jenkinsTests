#
# extension.py
#
# Copyright © 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 9 (Extension) subtables for a GPOS table.
"""

# Other imports
from fontio3.opentype import psextension

# -----------------------------------------------------------------------------

#
# Classes
#

class Extension(psextension.PSExtension):
    """
    Objects representing PSExtension tables. These are very simple wrappers,
    being simple objects with a single attribute:
    
        original    The original subtable.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    original:
      afii60003:
        Device for origin's x-coordinate:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
        Device for origin's y-coordinate:
          Tweak at 12 ppem: -5
          Tweak at 13 ppem: -3
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 2
          Tweak at 20 ppem: 3
      xyz46:
        FUnit adjustment to origin's x-coordinate: 30
        Device for vertical advance:
          Tweak at 12 ppem: -2
          Tweak at 14 ppem: -1
          Tweak at 18 ppem: 1
      xyz6:
        FUnit adjustment to origin's x-coordinate: -10
    """
    
    #
    # Class constants
    #
    
    kind = ('GPOS', 9)
    kindString = "Extension positioning table"
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GPOS import single
    from fontio3.utilities import namer
    
    _testingValues = (
        Extension(original=single._testingValues[1]),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
