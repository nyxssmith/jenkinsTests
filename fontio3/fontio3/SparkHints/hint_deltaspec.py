#
# hint_deltaspec.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

# System imports
import collections

# Other imports
from fontio3.fontdata import keymeta

# -----------------------------------------------------------------------------

#
# Classes
#

_DS = collections.namedtuple(
  "_DS",
  ['ppem', 'pointIndex', 'shift'])

class DeltaSpec(_DS, metaclass=keymeta.FontDataMetaclass):
    """
    These are named tuples comprising three elements: PPEM, point index, and
    distance (float). The various DELTA hints are just sets of these; since
    each DELTA has its own particular requirements for input/output, this
    class has no buildBinary() or fromwalker() methods.
    
    Support is bare-bones here; see the specific DELTA classes for the full
    panoply of support.
    
    >>> DeltaSpec(12, 51, -0.25).pprint()
    (PPEM = 12, Point index = 51, Shift distance (pixels) = -0.25)
    """
    
    itemSpec = (
        dict(
            item_label = "PPEM"),
        
        dict(
            item_label = "Point index",
            item_renumberpointsdirect = True),
        
        dict(
            item_label = "Shift distance (pixels)",
            item_scaledirect = True))
    
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
    _test()

