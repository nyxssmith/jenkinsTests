#
# glyphtuple.py
#
# Copyright © 2009-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Simple sequences of glyph indices.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    These are tuples of glyph indices. No special flags are set.
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    0: xyz12
    1: afii60003
    2: xyz6
    """
    
    #
    # Class definition variables
    #
    
    # __hash__ = tuple.__hash__ -- don't know if this is still needed...
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_maxcontextfunc = len)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. The following
        keyword arguments are supported:
        
            countFirst      If True, the length of the tuple will be written
                            before the tuple values themselves are written.
                            Default is False.
            
            sortGlyphs      If True, the sorted tuple will be written. Default
                            is False.
            
            stakeValue      The stake value to be used for the data start.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
        
        >>> utilities.hexdump(_testingValues[0].binaryString(countFirst=True))
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0003                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(countFirst=True))
               0 | 0001 0003                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 000B 0062 0005                           |...b..          |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(sortGlyphs=True))
               0 | 0005 000B 0062                           |.....b          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if kwArgs.get('countFirst', False):
            w.add("H", len(self))
        
        w.addGroup("H", (sorted(self) if kwArgs.get('sortGlyphs', False) else self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphTuple from the specified walker, doing
        source validation. The following keyword arguments are supported:
        
            count           If present, the number of glyphs to be read. If not
                            present the countFirst keyword argument must be
                            specified.
            
            countFirst      If True, a count for the tuple will be read from
                            the walker. If False then the count keyword must be
                            specified.
            
            logger          A logger to which messages will be posted.
        
        >>> logger = utilities.makeDoctestLogger("glyphtuple_test")
        >>> fvb = GlyphTuple.fromvalidatedbytes
        >>> h = utilities.fromhex
        >>> obj = fvb(h("00 02 00 30 00 4E"), countFirst=True, logger=logger)
        glyphtuple_test.glyphtuple - DEBUG - Walker has 6 bytes remaining.
        glyphtuple_test.glyphtuple - DEBUG - Count is 2
        glyphtuple_test.glyphtuple - DEBUG - Data are (48, 78)
        
        >>> obj = fvb(h("00 03 00 30 00 4E"), countFirst=True, logger=logger)
        glyphtuple_test.glyphtuple - DEBUG - Walker has 6 bytes remaining.
        glyphtuple_test.glyphtuple - DEBUG - Count is 3
        glyphtuple_test.glyphtuple - ERROR - The glyph sequence is missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("glyphtuple")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
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
        
        else:
            logger.warning(('V0443', (), "The count is zero."))
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphTuple from the specified walker. The
        following keyword arguments are supported:
        
            count           If present, the number of glyphs to be read. If not
                            present the countFirst keyword argument must be
                            specified.
            
            countFirst      If True, a count for the tuple will be read from
                            the walker. If False then the count keyword must be
                            specified.
        
        >>> f = GlyphTuple.frombytes
        >>> v = _testingValues
        >>> v[0] == f(v[0].binaryString(countFirst=True), countFirst=True)
        True
        >>> v[0] == f(v[0].binaryString(), count=len(v[0]))
        True
        >>> v[1] == f(v[1].binaryString(countFirst=True), countFirst=True)
        True
        >>> v[1] == f(v[1].binaryString(), count=len(v[1]))
        True
        >>> v[2] == f(v[2].binaryString(countFirst=True), countFirst=True)
        True
        >>> v[2] == f(v[2].binaryString(), count=len(v[2]))
        True
        """
        
        if kwArgs.get('countFirst', False):
            count = w.unpack("H")
        else:
            count = kwArgs.get('count', None)
        
        assert count is not None
        return cls(w.group("H", count))

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class GlyphTuple_NoShrink(GlyphTuple):
    seqSpec = dict(seq_fixedlength=True)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class GlyphTuple_Output(GlyphTuple):
    seqSpec = dict(item_isoutputglyph=True)

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
        GlyphTuple([]),
        GlyphTuple([3]),
        GlyphTuple([11, 98, 5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
