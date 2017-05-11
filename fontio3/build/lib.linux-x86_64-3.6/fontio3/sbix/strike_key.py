#
# strike_key.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the objects used as keys in a Strike.
"""

# System imports
import collections

# -----------------------------------------------------------------------------

#
# Classes
#

_StrikeKey = collections.namedtuple("_StrikeKey", ['ppem', 'resolution'])

class StrikeKey(_StrikeKey):
    """
    Tuples representing keys in a Strike. These are pairs of values, (ppem,
    resolution). They have a custom __str__ method.
    
    >>> print((StrikeKey(24, 72)))
    (ppem=24, resolution=72)
    """
    
    def __str__(self):
        return "(ppem=%d, resolution=%d)" % (self.ppem, self.resolution)

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

