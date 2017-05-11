#
# staterow_rearrangement.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'morx' rearrangement subtable.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.statetables import classmap

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    sigOnly = kwArgs.get('onlySignificant', False)
    vFixed = classmap.fixedNames
    sFixed = set(vFixed)
    
    for s in vFixed:
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)
    
    for s in sorted(d):
        if s in sFixed:
            continue
        
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows in the state array for a 'morx' table.
    These are dicts mapping class names to Entry objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint)

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
