#
# csmrecord.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
A single CSM record in an ADFH table.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import mathutilities
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class CSMRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects describing cutoff values and gammas for a range of sizes starting
    at a particular size. These are simple objects with four attributes:
    
        gamma               A float.
        insideCutoff        A float.
        outsideCutoff       A float.
        size                An integer.
    
    >>> _testingValues[1].pprint()
    Lower limit of size range (inclusive): 12
    Inside cutoff: 0.25
    Outside cutoff: -2.0
    Gamma: -0.25
    
    >>> logger = utilities.makeDoctestLogger("csmrecord_test")
    >>> obj = _testingValues[1].__copy__()
    >>> e = utilities.fakeEditor(0x10000)
    >>> obj.isValid(editor=e, logger=logger)
    True
    
    >>> obj.gamma = "Fred"
    >>> obj.insideCutoff = 15000000
    >>> obj.size = 1.5
    >>> obj.isValid(editor=e, logger=logger)
    csmrecord_test.gamma - ERROR - The value 'Fred' is not a real number.
    csmrecord_test.insideCutoff - ERROR - The value 15000000 cannot be represented in signed (16.16) format.
    csmrecord_test.size - ERROR - The value 1.5 is not an integer.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
      gamma = dict(
        attr_initfunc = (lambda: 0.0),
        attr_label = "Gamma",
        attr_validatefunc = valassist.isNumber_fixed),
      
      insideCutoff = dict(
        attr_initfunc = (lambda: 0.0),
        attr_label = "Inside cutoff",
        attr_validatefunc = valassist.isNumber_fixed),
      
      outsideCutoff = dict(
        attr_initfunc = (lambda: 0.0),
        attr_label = "Outside cutoff",
        attr_validatefunc = valassist.isNumber_fixed),
      
      size = dict(
        attr_initfunc = (lambda: 0),
        attr_label = "Lower limit of size range (inclusive)",
        attr_validatefunc = functools.partial(
          valassist.isNumber_integer_unsigned,
          numBits = 16)))
    
    attrSorted = ('size', 'insideCutoff', 'outsideCutoff', 'gamma')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CSMRecord to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000 0000 0000  0000 0000 0000      |..............  |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000C 0000 4000 FFFE  0000 FFFF C000      |....@.........  |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0014 0000 C000 FFFF  0000 FFFF C000      |..............  |
        """
        
        f = mathutilities.floatToFixed
        
        w.add("H3l",
          self.size,
          f(self.insideCutoff),
          f(self.outsideCutoff),
          f(self.gamma))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CSMRecord from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("csmrecord_fvw")
        >>> fvb = CSMRecord.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        csmrecord_fvw.csmrecord - DEBUG - Walker has 14 remaining bytes.
        
        >>> fvb(s[:3], logger=logger)
        csmrecord_fvw.csmrecord - DEBUG - Walker has 3 remaining bytes.
        csmrecord_fvw.csmrecord - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("csmrecord")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 14:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.unpack("H3l")
        return cls(t[0], t[1] / 65536, t[2] / 65536, t[3] / 65536)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a CSMRecord from the specified walker.
        
        >>> fb = CSMRecord.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        return cls(
          w.unpack("H"),
          w.unpack("l") / 65536,
          w.unpack("l") / 65536,
          w.unpack("l") / 65536)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        CSMRecord(),
        CSMRecord(size=12, insideCutoff=0.25, outsideCutoff=-2.0, gamma=-0.25),
        CSMRecord(size=20, insideCutoff=0.75, outsideCutoff=-1.0, gamma=-0.25),
        CSMRecord(size=18, insideCutoff=-0.5, outsideCutoff=0.25, gamma=0.5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
