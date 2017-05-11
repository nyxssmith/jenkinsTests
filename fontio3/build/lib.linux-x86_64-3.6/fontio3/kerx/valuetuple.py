#
# valuetuple.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for sequences of values in a 'kerx' table. A value is a shift distance
(in FUnits), and scales.

Note that 'kerx' values, unlike their 'kern' counterparts, do not carry info
about cross-stream shift resets; that is present at a higher level (the flags
in the Entry).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if not obj:
        logger.warning((
          'V0629',
          (),
          "The kerning value sequence is empty, and will have no effect."))
    
    badEntries = [i for i, x in enumerate(obj) if x == -1]
    
    if badEntries:
        logger.error((
          'V0769',
          (badEntries,),
          "The values at the following indices are -1, which is not a "
          "permitted value for a format 0 'kerx' subtable: %s"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ValueTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a collection of kerning values to be applied to a
    group of adjacent glyphs. First element of the tuple is applied to the
    glyph popped first, etc.
    
    >>> _testingValues[2].pprint()
    Pop #1: 200
    
    >>> _testingValues[2].scaled(1.5).pprint()
    Pop #1: 300
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x1000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    val - WARNING - The kerning value sequence is empty, and will have no effect.
    True
    
    >>> _testingValues[5].isValid(logger=logger, editor=e)
    val - ERROR - The values at the following indices are -1, which is not a permitted value for a format 0 'kerx' subtable: [0]
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintlabelfunc = (lambda i,**k: "Pop #%d" % (i + 1,)),
        item_scaledirect = True,
        seq_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ValueTuple to the specified writer.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[2].binaryString())
               0 | 00C8 FFFF                                |....            |
        
        >>> h(_testingValues[4].binaryString())
               0 | 00C8 FF38 FFFF                           |...8..          |
        
        ValueTuples containing a value of -1 are invalid, as the -1 is used to
        signal end-of-sequence in the binary data.
        
        >>> h(_testingValues[5].binaryString())
        Traceback (most recent call last):
          ...
        ValueError: Cannot kern by -1 FUnits!
        """
        
        if any(x == -1 for x in self):
            raise ValueError("Cannot kern by -1 FUnits!")
        
        w.addGroup("h", self)
        w.add("h", -1)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ValueTuple from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[4].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = ValueTuple.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.valuetuple - DEBUG - Walker has 6 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        fvw.valuetuple - DEBUG - Walker has 1 remaining bytes.
        fvw.valuetuple - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.valuetuple - DEBUG - Walker has 5 remaining bytes.
        fvw.valuetuple - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("valuetuple")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        n = w.unpack("h")
        v = []
        
        while n != -1:
            v.append(n)
            
            if w.length() < 2:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            n = w.unpack("h")
        
        return cls(v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ValueTuple from the specified walker.
        
        >>> v = []
        >>> for i in range(1, 5):
        ...     obj = _testingValues[i]
        ...     v.append(obj == ValueTuple.frombytes(obj.binaryString()))
        >>> print(v)
        [True, True, True, True]
        """
        
        v = []
        n = w.unpack("h")
        
        while n != -1:
            v.append(n)
            n = w.unpack("h")
        
        return cls(v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        ValueTuple(),
        ValueTuple([0]),
        ValueTuple([200]),
        ValueTuple([-200]),
        ValueTuple([200, -200]),
        ValueTuple([-1])  # this one will cause exception at buildBinary() time
        )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
