#
# MTsf.py
#
# Copyright © 2007-2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for MTsf tables.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.MTsf import record

# -----------------------------------------------------------------------------

#
# Classes
#

class MTsf(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire MTsf tables. These are dicts mapping glyph
    indices to Record objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz1:
      Use proportion correction: False
      Baseline is shifted: False
      Class name: (no data)
    xyz2:
      Use proportion correction: False
      Baseline is shifted: True
      Class name: 'fred'
    xyz3:
      Use proportion correction: True
      Baseline is shifted: False
      Class name: 'wxyz'
    xyz4:
      Use proportion correction: False
      Baseline is shifted: False
      Class name: 'abcdef'
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a MTsf object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> fakeEditor = {
        ...     b'maxp': maxp_tt.Maxp_TT(numGlyphs=4),
        ...     b'MTsc': MTsc._testingValues[1]}
        >>> d = {'editor': fakeEditor}
        >>> obj == MTsf.frombytes(obj.binaryString(**d), **d)
        True
        """
        
        version = w.unpack("H")
        
        if version != 1:
            raise ValueError("Unknown MTsf version: %d" % (version,))
        
        e = kwArgs['editor']
        mtscTable = e.get(b'MTsc', [])
        fgc = e[b'maxp'].numGlyphs
        fw = record.Record.fromwalker
        return cls((i, fw(w, classMap=mtscTable)) for i in range(fgc))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTsf object to the specified LinkedWriter.
        
        >>> obj = _testingValues[1]
        >>> fakeEditor = {
        ...     b'maxp': maxp_tt.Maxp_TT(numGlyphs=4),
        ...     b'MTsc': MTsc._testingValues[1]}
        >>> d = {'editor': fakeEditor}
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | 0001 0000 FFFF 0000  0000 0000 0001 0002 |................|
              10 | 0000 0000 0000 0100  0000 0000 0000 0000 |................|
              20 | 0000 0001 0000 0000  0000                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Note that the MTsc object obtained from the editor will be current,
        # since the editor's _updateDependentObjects() method will have been
        # called as part of the editor's buildBinary() process.
        
        e = kwArgs['editor']
        
        if set(self) != set(range(e[b'maxp'].numGlyphs)):
            raise ValueError("There are holes in the glyph indices!")
        
        sc = e.get(b'MTsc', MTsc.MTsc())
        revMap = {s: i for i, s in enumerate(sc)}
        w.add("H", 1)
        
        for i in range(e[b'maxp'].numGlyphs):
            self[i].buildBinary(w, classRevMap=revMap)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import MTsc, utilities
    from fontio3.maxp import maxp_tt
    from fontio3.utilities import namer
    
    _rv = record._testingValues
    
    _testingValues = (
        MTsf(),
        
        MTsf({
          0: _rv[0],
          1: _rv[1],
          2: _rv[2],
          3: _rv[3]}))
    
    del _rv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
