#
# table_v2.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for version 2 'MTap' tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.MTap import record_v2

# -----------------------------------------------------------------------------

#
# Classes
#

class Table(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing version 2 'MTap' tables. These are dicts mapping
    glyph indices to record_v2.Record objects.
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
        
            editor      An Editor-class object, from which the living MTad and
                        MTcc objects will be obtained. (If the MTca class ever
                        comes to life, it will be used here too)
                        
                        Note that the Editor object assures that the living
                        objects are current with respect to any changes in this
                        MTap object before this buildBinary method is called.
        
        >>> d = {'editor': _FakeEditor(3)}
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0002 0000 0000 FFFF  FFFF FFFF 0301 0000 |................|
              10 | 0000 0000 FFFF 0102  0000 0001 FFFF FFFF |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 2)  # version
        e = kwArgs['editor']
        adMap = {obj.asImmutable(**kwArgs): i for i, obj in enumerate(e.MTad)}
        ccMap = {obj.asImmutable(**kwArgs): i for i, obj in enumerate(e.MTcc)}
        
        for i in range(e.maxp.numGlyphs):
            self[i].buildBinary(w, adMap=adMap, ccMap=ccMap, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Table object from the specified walker. There is
        one required keyword argument:
        
            editor      An Editor-class object, from which the living MTad and
                        MTcc objects will be obtained. (If the MTca class ever
                        comes to life, it will be used here too)
        
        >>> d = {'editor': _FakeEditor(3)}
        >>> obj = _testingValues[1]
        >>> obj == Table.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        version = w.unpack("H")
        
        if version != 2:
            raise ValueError(
              "Version number is not 2 for version 2 'MTap' table!")
        
        fw = record_v2.Record.fromwalker
        count = kwArgs['editor'].maxp.numGlyphs
        return cls((i, fw(w, **kwArgs)) for i in range(count))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.maxp import maxp_tt
    from fontio3.MTad import MTad
    from fontio3.MTcc import MTcc
    from fontio3.utilities import namer
    
    class _FakeEditor(object):
        def __init__(self, n):
            self.maxp = maxp_tt.Maxp_TT(numGlyphs=n)
            self.MTad = MTad._testingValues[1]
            self.MTcc = MTcc._testingValues[1]
    
    _rv = record_v2._testingValues
    
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
