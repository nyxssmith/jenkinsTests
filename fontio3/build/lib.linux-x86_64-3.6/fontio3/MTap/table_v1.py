#
# table_v1.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for version 1 'MTap' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.MTap import record_v1

# -----------------------------------------------------------------------------

#
# Classes
#

class Table(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing version 1 'MTap' tables. These are dicts mapping
    glyph indices to record_v1.Record objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz1:
    xyz2:
      Glyph class: Component (4)
      Top 0 point index: 12
      Bottom 0 point index: 9
    xyz3:
      Glyph class: Mark (3)
      Top 0 point index: 5
      Top 1 point index: 6
      Bottom 0 point index: 7
      Bottom 1 point index: 8
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Table object to the specified
        LinkedWriter. There is one required keyword argument:
        
            editor      An Editor-class object, whose Maxp object will be used
                        to obtain the font's glyph count. (We don't pass in the
                        glyph count directly, because version 2 Table objects
                        need other things from the editor as well)
        
        >>> d = {'editor': _FakeEditor(3)}
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0001 0000 FFFF FFFF  FFFF FFFF 0004 000C |................|
              10 | FFFF 0009 FFFF 0003  0005 0006 0007 0008 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # version
        count = kwArgs['editor'].maxp.numGlyphs
        
        for i in range(count):
            self[i].buildBinary(w, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Table object from the specified walker. There is
        one required keyword argument:
        
            editor      An Editor-class object, whose Maxp object will be used
                        to obtain the font's glyph count. (We don't pass in the
                        glyph count directly, because version 2 Table objects
                        need other things from the editor as well)
        
        >>> d = {'editor': _FakeEditor(3)}
        >>> fb = Table.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString(**d), **d)
        True
        """
        
        version = w.unpack("H")
        
        if version != 1:
            raise ValueError(
              "Version number is not 1 for version 1 'MTap' table!")
        
        fw = record_v1.Record.fromwalker
        count = kwArgs['editor'].maxp.numGlyphs
        return cls((i, fw(w)) for i in range(count))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.maxp import maxp_tt
    from fontio3.utilities import namer
    
    class _FakeEditor(object):
        def __init__(self, n):
            self.maxp = maxp_tt.Maxp_TT(numGlyphs=n)
    
    _rv = record_v1._testingValues
    
    _testingValues = (
        Table(),
        Table({0: _rv[0], 1: _rv[1], 2: _rv[2]}))
    
    del _rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
