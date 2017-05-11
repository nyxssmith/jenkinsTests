#
# groups15.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ADFH 1.5 collections of (uninterpreted) glyph indices.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import setmeta
from fontio3.utilities import span2

# -----------------------------------------------------------------------------

#
# Classes
#

class Groups(set, metaclass=setmeta.FontDataMetaclass):
    """
    Sets gathering glyph indices.
    
    >>> _testingValues[1].pprint()
    2-4, 10-11, 30-31, 33, 35-39
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_renumberdirect = True,
        set_pprintfunc = (lambda p,obj: p(str(span2.Span(obj)))))
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a compact representation of the glyph indices covered by the
        Groups object.
        
        >>> g = Groups()
        >>> g.update(range(100, 2000))
        >>> g.update(range(2200, 4000))
        >>> print(g)
        100-1999, 2200-3999
        """
        
        return str(span2.Span(self))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Groups to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0005 0002 0004 0000  000A 000B 0000 001E |................|
              10 | 001F 0000 0021 0021  0000 0023 0027 0000 |.....!.!...#.'..|
        """
        
        s = span2.Span(self)
        groups = list(s.ranges())
        w.add("H", len(groups))
        w.addGroup("2Hxx", groups)
    
    @classmethod
    def from20(cls, g):
        """
        Returns a Groups from a version 2.0 Groups. The keys of the 2.0 Groups
        are used, and nothing else.
        """
        
        return cls(g)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Group object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("groups15_fvw")
        >>> fvb = Groups.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        groups15_fvw.groups15 - DEBUG - Walker has 32 remaining bytes.
        groups15_fvw.groups15 - INFO - The group index array is sorted by start glyph.
        
        >>> fvb(s[:1], logger=logger)
        groups15_fvw.groups15 - DEBUG - Walker has 1 remaining bytes.
        groups15_fvw.groups15 - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        groups15_fvw.groups15 - DEBUG - Walker has 31 remaining bytes.
        groups15_fvw.groups15 - ERROR - The group index array is missing or incomplete.
        
        >>> obj = fvb(s[:23] + utilities.fromhex("27") + s[24:], logger=logger)
        groups15_fvw.groups15 - DEBUG - Walker has 32 remaining bytes.
        groups15_fvw.groups15 - INFO - The group index array is sorted by start glyph.
        groups15_fvw.groups15 - WARNING - Some of the group index records overlap (that is, some glyphs are members of more than one record).
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("groups15")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0001', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if w.length() < 6 * count:
            logger.error((
              'V0571',
              (),
              "The group index array is missing or incomplete."))
            
            return None
        
        rawList = w.group("2H2x", count)
        
        if list(rawList) != sorted(rawList):
            logger.info((
              'V0572',
              (),
              "The group index array is not sorted by start glyph."))
        
        else:
            logger.info((
              'V0573',
              (),
              "The group index array is sorted by start glyph."))
        
        rawCount = sum(t[1] - t[0] + 1 for t in rawList)
        theSpan = span2.Span.fromranges(rawList)
        
        if len(theSpan) != rawCount:
            logger.warning((
              'V0574',
              (),
              "Some of the group index records overlap (that is, some glyphs "
              "are members of more than one record)."))
        
        return cls(theSpan)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Groups from the specified walker.
        
        >>> fb = Groups.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        count = w.unpack("H")
        rawList = w.group("2H2x", count)
        theSpan = span2.Span.fromranges(rawList)
        return cls(theSpan)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Groups(),
        Groups({2, 3, 4, 10, 11, 30, 31, 33, 35, 36, 37, 38, 39}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
