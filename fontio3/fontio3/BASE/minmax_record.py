#
# minmax_record.py
#
# Copyright © 2010-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to single minimum or maximum records in a RecordDict.
"""

# System imports
import functools
import operator

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Simple objects comprising just a minimum and a maximum coordinate. Either
    or both of these may be None or a Coordinate object.
    
    >>> _testingValues[0].pprint()
    
    >>> _testingValues[1].pprint()
    Minimum coordinate:
      Coordinate: 0
    Maximum coordinate:
      Coordinate: 15
      Device table:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    
    >>> _testingValues[2].pprint()
    Minimum coordinate:
      Coordinate: 85
    
    >>> _testingValues[3].pprint(namer=namer.testingNamer())
    Maximum coordinate:
      Coordinate: -10
      Glyph: xyz15
      Point: 12
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        minCoord = dict(
            attr_followsprotocol = True,
            attr_label = "Minimum coordinate",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        maxCoord = dict(
            attr_followsprotocol = True,
            attr_label = "Maximum coordinate",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)))
    
    attrSorted = ('minCoord', 'maxCoord')

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.BASE import coordinate
    from fontio3.utilities import namer
    
    _cv = coordinate._testingValues
    
    _testingValues = (
        Record(),
        Record(_cv[0], _cv[7]),
        Record(_cv[1], None),
        Record(None, _cv[4]))
    
    del _cv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
