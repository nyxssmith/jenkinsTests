#
# deltadict.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class DeltaDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dicts mapping AxialCoordinates to signed FUnit deltas, to be applied to CVT
    values.
    """
    
    mapSpec = dict(
        item_keyfollowsprotocol = True,
        item_pprintlabelfunc = str)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

