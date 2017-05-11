#
# trackdata_entry.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for values in a TrackData dict.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.trak import sizedict

# -----------------------------------------------------------------------------

#
# Classes
#

class Entry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single values in a TrackData dict. These are simple
    objects with two attributes:
    
        nameTableIndex      An nameID for a sensible name for this track.
        
        perSizeTable        A SizeDict object.
    
    >>> e = _fakeEditor()
    >>> _testingValues[0].pprint(editor=e)
    Track 'name' table index: 290 ('Tight')
    Per-size shifts:
      9.0 ppem shift in FUnits: -35
      11.5 ppem shift in FUnits: -20
      14.0 ppem shift in FUnits: -1
      22.0 ppem shift in FUnits: 6

    >>> _testingValues[1].pprint(editor=e)
    Track 'name' table index: 291 ('Loose')
    Per-size shifts:
      9.0 ppem shift in FUnits: -15
      11.5 ppem shift in FUnits: 0
      14.0 ppem shift in FUnits: 5
      22.0 ppem shift in FUnits: 18
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        nameTableIndex = dict(
            attr_label = "Track 'name' table index",
            attr_renumbernamesdirect = True),
        
        perSizeTable = dict(
            attr_followsprotocol = True,
            attr_initfunc = sizedict.SizeDict,
            attr_label = "Per-size shifts"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _fakeEditor():
        from fontio3.name import name
        
        _fakeNameTable = {(1,0,0,290): "Tight", (1,0,0,291): "Loose"}
        e = utilities.fakeEditor(0x1000)
        e.name = name.Name(_fakeNameTable)
        return e
    
    _sdv = sizedict._testingValues
    
    _testingValues = (
        Entry(290, _sdv[0]),
        Entry(291, _sdv[1]),
        Entry(291, _sdv[2]))
    
    del _sdv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
