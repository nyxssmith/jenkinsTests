#
# classpair.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys for class-based kerning (in 'kerx' tables).
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class ClassPair(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a pair of class indices. These are tuples, and are
    used as keys in Format2 objects.
    
    >>> _testingValues[2].pprint()
    0: 2
    1: 1
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    val.[0] - ERROR - The class index -3 cannot be used in an unsigned field.
    val.[1] - ERROR - The class index 3.5 is not an integer.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_validatefunc = functools.partial(
          valassist.isFormat_H,
          label = "class index"),
        seq_fixedlength = 2)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Add the binary data for the ClassPair object to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002                                |....            |
        """
        
        w.addGroup("H", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassPair object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = ClassPair.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.classpair - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:2], logger=logger)
        fvw.classpair - DEBUG - Walker has 2 remaining bytes.
        fvw.classpair - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("classpair")
        
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
        Creates and returns a new ClassPair object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == ClassPair.frombytes(obj.binaryString())
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
    
    _testingValues = (
        ClassPair([1, 1]),
        ClassPair([1, 2]),
        ClassPair([2, 1]),
        
        # bad values start here
        
        ClassPair([-3, 3.5]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
