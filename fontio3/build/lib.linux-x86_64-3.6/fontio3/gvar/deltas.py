#
# deltas.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for deltas (x and y) associated with particular AxialCoordinates
objects.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.fontmath import point
    
# -----------------------------------------------------------------------------

#
# Functions
#

def _pprint_effectiveDomain(p, obj, **kwArgs):
    if obj.edge1.axisOrder != obj.edge2.axisOrder:
        raise ValueError("Axis order mismatch!")
    
    p.simple('', **kwArgs)
    
    for tag, a1, a2 in zip(obj.edge1.axisOrder, obj.edge1, obj.edge2):
        p.simple("  '%s' from %s to %s" % (tag, a1, a2))

# -----------------------------------------------------------------------------

#
# Classes
#

class Deltas(point.Point, metaclass=seqmeta.FontDataMetaclass):
    """
    Deltas in X and Y.
    
    >>> Deltas(200, -50).pprint()
    Delta X: 200
    Delta Y: -50
    """
    
    seqSpec = dict(
        item_pprintlabelfunc = (lambda i: ("Delta X", "Delta Y")[i]),
        seq_fixedlength = 2)
    
    attrSpec = dict(
        effectiveDomain = dict(
            attr_followsprotocol = True,
            attr_ignoreforcomparisons = True,
            attr_pprintfunc = _pprint_effectiveDomain,
            attr_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.gvar import axial_coordinate

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

