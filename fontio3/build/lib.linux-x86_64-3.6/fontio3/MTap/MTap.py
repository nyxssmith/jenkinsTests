#
# MTap.py
#
# Copyright © 2010 Monotype Imaging Inc. All Rights Reserved.
#

"""
Information relating to entire 'MTap' tables.
"""

# Other imports
from fontio3.MTap import table_v1, table_v2

# -----------------------------------------------------------------------------

#
# Functions
#

def MTap(w, **kwArgs):
    """
    Factory function for Table objects, either version 1 or version 2.
    """
    
    version = w.unpack("H", advance=False)
    
    if version == 1:
        return table_v1.Table.fromwalker(w, **kwArgs)
    elif version == 2:
        return table_v2.Table.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown 'MTap' version: %d" % (version,))

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
