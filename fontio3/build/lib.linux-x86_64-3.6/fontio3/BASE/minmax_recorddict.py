#
# minmax_recorddict.py
#
# Copyright © 2010-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to minimum or maximum Records for a collection of feature
tags.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class RecordDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing collections of Records. These are dicts whose keys are
    4-byte tags and whose values are Record objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
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
          lambda k: "Feature '%s'" % (utilities.ensureUnicode(k),)))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.BASE import minmax_record
    from fontio3.utilities import namer
    
    _rv = minmax_record._testingValues
    
    _testingValues = (
        RecordDict(),
        RecordDict({b'abcd': _rv[1], b'wxyz': _rv[3]}))
    
    del _rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
