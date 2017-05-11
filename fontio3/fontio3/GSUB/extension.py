#
# extension.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 7 (Extension) subtables for a GSUB table.
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
      xyz5: xyz11
      xyz6: afii60002
      xyz7: xyz19
    """
    
    #
    # Class constants
    #
    
    kind = ('GSUB', 7)
    kindString = "Extension substitution table"
    
# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.GSUB import single
    from fontio3.utilities import namer
    
    _testingValues = (
        Extension(original=single._testingValues[2]),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
