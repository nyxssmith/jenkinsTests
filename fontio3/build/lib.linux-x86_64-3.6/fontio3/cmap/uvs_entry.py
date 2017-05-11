#
# uvs_entry.py
#
# Copyright © 2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for variation information for a single Unicode Variation Selector value
(both default and non-default).
"""

# Other imports
from fontio3.cmap import uvs_entry_set
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class UVS_Entry(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects identifying variations for a single Unicode Variation Selector
    value. These are dicts mapping Unicode scalar values to glyph IDs.
    
    The following attributes are defined for this class:
    
    ``default``
        A :py:class:`~fontio3.cmap.uvs_entry_set.UVS_Entry_Set` object,
        representing the default mappimgs for this Unicode Variation Selector
        value.
    
    Note that this class does not have ``buildBinary()`` or ``fromwalker()``
    methods; that functionality is handled at a higher level.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    U+614E: xyz24
    U+6226: afii60002
    
    >>> _testingValues[2].pprint()
    Default mappings:
      U+4E01
      U+4E08
    
    >>> _testingValues[3].pprint()
    U+89EE: 41
    Default mappings:
      U+5225
      U+022F43
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc = (
          lambda c:
          ("U+%06X" if c > 0xFFFF else "U+%04X") % c),
        item_pprintlabelpresort = True,
        item_renumberdirectvalues = True,
        item_usenamerforstr = True)
    
    attrSpec = dict(
        default = dict(
            attr_followsprotocol = True,
            attr_initfunc = uvs_entry_set.UVS_Entry_Set,
            attr_label = "Default mappings",
            attr_showonlyiftrue = True))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _uestv = uvs_entry_set._testingValues
    
    _testingValues = (
        UVS_Entry(),
        
        UVS_Entry({0x614E: 23, 0x6226: 97}),
        
        UVS_Entry({}, default=_uestv[1]),
        
        UVS_Entry({0x89EE: 41}, default=_uestv[2]))
    
    del _uestv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
