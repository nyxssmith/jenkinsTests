#
# glyphpair.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys for simple pairwise kerning (in 'kern' tables).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphPair(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a pair of glyphs. These are tuples, and are used as
    keys in Format0 objects.
    
    >>> _testingValues[0].pprint()
    0: 14
    1: 23
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    0: xyz15
    1: afii60001
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_fixedlength = 2)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Add the binary data for the GlyphPair object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 000E 0017                                |....            |
        """
        
        w.addGroup("H", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphPair object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("glyphpair_fvw")
        >>> fvb = GlyphPair.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        glyphpair_fvw.glyphpair - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:2], logger=logger)
        glyphpair_fvw.glyphpair - DEBUG - Walker has 2 remaining bytes.
        glyphpair_fvw.glyphpair - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("glyphpair")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(w.group("H", 2))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphPair object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == GlyphPair.frombytes(obj.binaryString())
        True
        """
        
        return cls(w.group("H", 2))

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
        GlyphPair([14, 23]),
        GlyphPair([14, 96]),
        GlyphPair([18, 38]),
        GlyphPair([0, 23]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
