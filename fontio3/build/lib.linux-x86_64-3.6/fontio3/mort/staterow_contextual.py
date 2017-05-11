#
# staterow_contextual.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'mort' contextual subtable.
"""

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, label, **k):
    if (
      obj.newState != "Start of text" or
      obj.mark or
      obj.noAdvance or
      obj.markSubstitutionDict or
      obj.currSubstitutionDict):
        
        p.deep(obj, label=label, **k)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows in the state array for a 'mort' table.
    These are dicts mapping class names to Entry objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = _ppf,
        item_pprintlabelfunc = (lambda k: "Class '%s'" % (k,)))

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
