#
# glyphset.py
#
# Copyright © 2010-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Sets of glyph indices.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphSet(set, metaclass=setmeta.FontDataMetaclass):
    """
    These are sets of glyph indices. No special flags are set.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz4
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    afii60003
    xyz12
    xyz6
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        set_showsorted = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GlyphSet object to the specified
        LinkedWriter. Note that the values are always written sorted. The
        following keyword arguments are supported:
        
            countFirst      If True, the length of the set will be written
                            before the set values themselves are written.
                            Default is False.
            
            stakeValue      The stake value to be used for the data start.
        
        >>> utilities.hexdump(_testingValues[0].binaryString(countFirst=True))
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[0].binaryString(countFirst=False))
        
        >>> utilities.hexdump(_testingValues[1].binaryString(countFirst=True))
               0 | 0001 0003                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(countFirst=False))
               0 | 0003                                     |..              |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(countFirst=True))
               0 | 0003 0005 000B 0062                      |.......b        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(countFirst=False))
               0 | 0005 000B 0062                           |.....b          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if kwArgs.get('countFirst', False):
            w.add("H", len(self))
        
        w.addGroup("H", sorted(self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphSet object from the specified walker,
        doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('glyphset')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Logger has %d bytes remaining."))
        
        if kwArgs.pop('countFirst', False):
            if w.length() < 2:
                logger.error((
                  'V0419',
                  (),
                  "The glyph count is missing or incomplete."))
                
                return None
            
            count = w.unpack("H")
            logger.debug(('Vxxxx', (count,), "Count is %d"))
        
        else:
            assert 'count' in kwArgs
            count = kwArgs.pop('count')
        
        v = []
        
        if count:
            if w.length() < 2 * count:
                logger.error((
                  'V0420',
                  (),
                  "The glyph sequence is missing or incomplete."))
                
                return None
            
            v = w.group("H", count)
            logger.debug(('Vxxxx', (v,), "Data are %s"))
        
        r = cls(v)
        
        if len(r) != len(v):
            logger.warning((
              'V0429',
              (v,),
              "Duplicate glyphs in alternate set %s."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphSet from the specified walker. The
        following keyword arguments are supported:
        
            count           If present, the number of glyphs to be read. If not
                            present the countFirst keyword argument must be
                            specified.
            
            countFirst      If True, a count for the set will be read from the
                            walker. If False then the count keyword must be
                            specified.
        
        >>> t = _testingValues
        >>> fb = GlyphSet.frombytes
        
        >>> t[0] == fb(t[0].binaryString(countFirst=True), countFirst=True)
        True
        
        >>> t[0] == fb(t[0].binaryString(countFirst=False), count=0)
        True
        
        >>> t[1] == fb(t[1].binaryString(countFirst=True), countFirst=True)
        True
        
        >>> t[1] == fb(t[1].binaryString(countFirst=False), count=1)
        True
        
        >>> t[2] == fb(t[2].binaryString(countFirst=True), countFirst=True)
        True
        
        >>> t[2] == fb(t[2].binaryString(countFirst=False), count=3)
        True
        """
        
        if kwArgs.get('countFirst', False):
            count = w.unpack("H")
        else:
            count = kwArgs.get('count', None)
        
        assert count is not None
        return cls(w.group("H", count))

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
        GlyphSet([]),
        GlyphSet([3]),
        GlyphSet([11, 98, 5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
