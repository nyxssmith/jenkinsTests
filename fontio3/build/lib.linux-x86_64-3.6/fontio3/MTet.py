#
# MTet.py
#
# Copyright © 2007-2008, 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to the entire MTet table, which has information on times
each glyph in a font was last edited.
"""

# System imports
import datetime

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class MTet(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'MTet' tables. These are dicts whose keys are
    glyph indices and whose values are integers representing the number of
    seconds elapsed since midnight, January 1, 1904.
    
    >>> _testingValues[1].pprint()
    0: 2015-11-25 04:09:04
    1: 2015-11-25 09:42:24
    2: 2015-11-24 00:22:24
    3: 2015-11-25 04:09:04
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz1: 2015-11-25 04:09:04
    xyz2: 2015-11-25 09:42:24
    xyz3: 2015-11-24 00:22:24
    xyz4: 2015-11-25 04:09:04
    """
    
    #
    # Class definition variables
    #
    
    def _pf(p, n, label, **kwArgs):
        dBase = datetime.datetime(1904, 1, 1)
        p.simple(str(dBase + datetime.timedelta(seconds=n)), label=label)
    
    mapSpec = dict(
        item_pprintfunc = _pf,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    del _pf
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a MTet object from the specified walker.
        
        >>> d = {'fontGlyphCount': 4}
        >>> _testingValues[1] == MTet.frombytes(_testingValues[1].binaryString(), **d)
        True
        
        >>> _testingValues[0] == MTet.frombytes(_testingValues[0].binaryString(), **d)
        Traceback (most recent call last):
          ...
        ValueError: 'MTet' entry count (0) does not match font glyph count (4)
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'MTet' version: 0x%08X" % (version,))
        
        fgc = kwArgs['fontGlyphCount']
        t = w.unpackRest("L")
        
        if len(t) != fgc:
            s = "'MTet' entry count (%d) does not match font glyph count (%d)"
            raise ValueError(s % (len(t), fgc))
        
        return cls(zip(range(fgc), t))
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTet object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 D27A E4E0  D27B 3300 D279 5E40 |.....z...{3..y^@|
              10 | D27A E4E0                                |.z..            |
        """
        
        count = len(self)
        
        if set(self) != set(range(count)):
            raise ValueError("MTet keys are not dense!")
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)  # version
        w.addGroup("L", (self[i] for i in range(count)))
    
    def setToNow(self, iterable):
        """
        Sets the timestamp for all glyph indices in iterable to now.
        
        >>> d = _testingValues[1].__copy__()
        >>> d[0] == d[2], d[0] == _testingValues[1][0], d[2] == _testingValues[1][2]
        (False, True, True)
        >>> d.setToNow([0, 2])
        >>> d[0] == d[2], d[0] == _testingValues[1][0], d[2] == _testingValues[1][2]
        (True, False, False)
        """
        
        nowDelta = datetime.datetime.now() - datetime.datetime(1904, 1, 1)
        now = nowDelta.days * 86400 + nowDelta.seconds
        
        for glyphIndex in iterable:
            self[glyphIndex] = now

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        MTet(),
        MTet({0: 3531269344, 1: 3531289344, 2: 3531169344, 3: 3531269344}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
