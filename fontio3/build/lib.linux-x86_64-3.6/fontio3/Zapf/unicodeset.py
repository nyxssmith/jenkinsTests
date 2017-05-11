#
# unicodeset.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for unordered sets of Unicode scalar values.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import setmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pf(p, n):
    if n < 0x10000:
        p("U+%04X" % (n,))
    else:
        p("U+%06X" % (n,))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class UnicodeSet(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    Frozen sets of integers, intended to be interpreted as Unicode scalar
    values.
    
    >>> _testingValues[0].pprint()
    U+0020
    U+0186A0
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_pprintfunc = _pf,
        set_showpresorted = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the UnicodeSet object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 0020 D821 DEA0                      |... .!..        |
        """
        
        v16 = []
        
        for n in sorted(self):
            if n < 0x10000:
                v16.append(n)
            
            else:
                n1, n2 = divmod(n - 0x10000, 1024)
                v16.extend([n1 + 0xD800, n2 + 0xDC00])
        
        w.add("H", len(v16))
        w.addGroup("H", v16)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new UnicodeSet object from the specified walker,
        doing source validation. The walker should point to the n16BitUnicodes
        field in the GlyphInfo structure.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = UnicodeSet.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.unicodeset - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.unicodeset - DEBUG - Walker has 1 remaining bytes.
        fvw.unicodeset - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.unicodeset - DEBUG - Walker has 7 remaining bytes.
        fvw.unicodeset - ERROR - Insufficient bytes for array.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("unicodeset")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if w.length() < 2 * count:
            logger.error(('V0004', (), "Insufficient bytes for array."))
            return None
        
        v = w.group("H", count)
        s = set()
        i = 0
        
        while i < len(v):
            n = v[i]
            i += 1
            
            if 0xD800 <= n < 0xDC00:
                if i == len(v):
                    logger.error((
                      'V0759',
                      (n,),
                      "The last 16-bit value in the array is the first half "
                      "of an incomplete surrogate pair."))
                    
                    return None
                
                n2 = v[i]
                i += 1
                
                if not (0xDC00 <= n2 < 0xE000):
                    logger.error((
                      'V0759',
                      (),
                      "The second 16-bit value of a surrogate pair is not "
                      "in the range 0xDC00 through 0xDFFF."))
                    
                    return None
                
                s.add(0x10000 + (n - 0xD800) * 1024 + (n2 - 0xDC00))
            
            else:
                s.add(n)
        
        return cls(s)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new UnicodeSet object from the data in the
        specified walker, which should point to the n16BitUnicodes field in the
        GlyphInfo structure.
        
        >>> _testingValues[0] == UnicodeSet.frombytes(_testingValues[0].binaryString())
        True
        """
        
        v = w.group("H", w.unpack("H"))
        s = set()
        i = 0
        
        while i < len(v):
            n = v[i]
            i += 1
            
            if 0xD800 <= n < 0xDC00:
                if i == len(v):
                    raise ValueError("Incomplete surrogate pair!")
                
                n2 = v[i]
                i += 1
                
                if not (0xDC00 <= n2 < 0xE000):
                    raise ValueError("Incorrect surrogate pair!")
                
                s.add(0x10000 + (n - 0xD800) * 1024 + (n2 - 0xDC00))
            
            else:
                s.add(n)
        
        return cls(s)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        UnicodeSet([32, 100000]),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
