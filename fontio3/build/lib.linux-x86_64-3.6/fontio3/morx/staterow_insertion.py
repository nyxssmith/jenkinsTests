#
# staterow_insertion.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'morx' insertion subtable.
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

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire single rows in the state array for an insertion
    subtable in a 'morx' table. These are dicts mapping class names to Entry
    objects.
    
    >>> _testingValues[0].pprint()
    Class 'End of text':
      Name of next state: Start of text
    Class 'Out of bounds':
      Name of next state: Start of text
    Class 'Deleted glyph':
      Name of next state: Start of text
    Class 'End of line':
      Name of next state: Start of text
    Class 'Letter':
      Mark current location: True
      Name of next state: SawLetter
    
    The "onlySignificant" flag may be passed into pprint() for StateRow objects
    to suppress the printing of default Entry values:
    
    >>> _testingValues[0].pprint(onlySignificant=True)
    Class 'Letter':
      Mark current location: True
      Name of next state: SawLetter
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

if __debug__:
    from fontio3.morx import entry_insertion
    
    E = entry_insertion.Entry
    
    _testingValues = (
        StateRow({
          'End of text': E(),
          'End of line': E(),
          'Deleted glyph': E(),
          'Out of bounds': E(),
          'Letter': E(newState="SawLetter", mark=True)}),)
    
    del E

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
