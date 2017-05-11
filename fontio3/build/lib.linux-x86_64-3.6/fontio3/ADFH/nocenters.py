#
# nocenters.py
#
# Copyright © 2010-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the no-center portion of the ADFH table.
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

class NoCenters(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing collections of glyph indices for those glyphs not to
    be auto-centered.
    
    >>> nc = NoCenters(set(range(300, 1200)) - set({450}))
    >>> print(nc)
    300-449, 451-1199
    
    >>> d = dict(zip(range(300, 350), range(7000, 7050)))
    >>> nc.glyphsRenumbered(d).pprint(label="Glyph spans")
    Glyph spans:
      350-449, 451-1199, 7000-7049
    
    >>> r1 = set(range(100, 199, 3))
    >>> r2 = set(range(101, 200, 3))
    >>> NoCenters(r1 | r2).pprint(label="Ranges", maxWidth=75)
    Ranges:
      100-101, 103-104, 106-107, 109-110, 112-113, 115-116, 118-119, 121-122,
      124-125, 127-128, 130-131, 133-134, 136-137, 139-140, 142-143, 145-146,
      148-149, 151-152, 154-155, 157-158, 160-161, 163-164, 166-167, 169-170,
      172-173, 175-176, 178-179, 181-182, 184-185, 187-188, 190-191, 193-194,
      196-197
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
      item_renumberdirect = True,
      set_pprintfunc = (lambda p,i: p(str(span2.Span(i)))))
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of the object.
        
        >>> print(_testingValues[1])
        26-28, 258-259
        """
        
        return str(span2.Span(self))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the NoCenters object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0005 001A 001B 001C  0102 0103           |............    |
        """
        
        w.add("H", len(self))
        w.addGroup("H", sorted(self))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new NoCenter object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("nocenters_test")
        >>> fvb = NoCenters.fromvalidatedbytes
        >>> print(fvb(s, logger=logger))
        nocenters_test.nocenters - DEBUG - Walker has 12 remaining bytes.
        26-28, 258-259
        
        >>> fvb(s[:1], logger=logger)
        nocenters_test.nocenters - DEBUG - Walker has 1 remaining bytes.
        nocenters_test.nocenters - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        nocenters_test.nocenters - DEBUG - Walker has 11 remaining bytes.
        nocenters_test.nocenters - ERROR - There were not enough NoCenter glyphs to match the specified count (5).
        
        >>> print(fvb(utilities.fromhex("00 00"), logger=logger), end='')
        nocenters_test.nocenters - DEBUG - Walker has 2 remaining bytes.
        nocenters_test.nocenters - INFO - The NoCenter count is zero.
        
        >>> fvb(s[:4] + s[6:] + s[4:6], logger=logger)
        nocenters_test.nocenters - DEBUG - Walker has 12 remaining bytes.
        nocenters_test.nocenters - ERROR - The NoCenter list is not sorted by glyph index.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("nocenters")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if not count:
            logger.info((
              'V0557',
              (),
              "The NoCenter count is zero."))
            
            return cls()
        
        if w.length() < 2 * count:
            logger.error((
              'V0556',
              (count,),
              "There were not enough NoCenter glyphs to match the "
              "specified count (%d)."))
            
            return None
        
        v = list(w.group("H", count))
        
        if v != sorted(v):
            logger.error((
              'V0567',
              (),
              "The NoCenter list is not sorted by glyph index."))
            
            return None
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new NoCenter object from the specified walker.
        
        >>> fb = NoCenters.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        return cls(w.group("H", w.unpack("H")))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        NoCenters({}),
        NoCenters({26, 27, 28, 258, 259}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
