#
# hint_rtgah.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

# Future imports

import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class Hint_RTGAH(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Spark RTGAH (AA 11) opcode.
    """
    
    attrSpec = {}
    
    kindString = 'RTGAH'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> print((Hint_RTGAH()))
        RTGAH
        """
        
        return "RTGAH"
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        >>> utilities.hexdump(Hint_RTGAH().binaryString())
               0 | 7F0B                                     |..              |
        """
        
        w.add("BB", 0x7F, 0x0B)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_RTGAH from the specified walker, with validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_RTGAH.fromvalidatedbytes
        >>> bs = utilities.fromhex("7F 0B")
        >>> obj = fvb(bs, logger=logger)
        test.rtgah - DEBUG - Remaining walker bytes: 2
        
        >>> fvb(b"", logger=logger)
        test.rtgah - DEBUG - Remaining walker bytes: 0
        test.rtgah - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00 01")
        >>> fvb(bs, logger=logger)
        test.rtgah - DEBUG - Remaining walker bytes: 2
        test.rtgah - ERROR - Was expecting RTGAH, but got 0x00 0x01 instead
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('rtgah')
        else:
            logger = logger.getChild('rtgah')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op, arg = w.unpack("BB")
        
        if op != 0x7F or arg != 0x0B:
            logger.error((
              'V0002',
              (op, arg),
              "Was expecting RTGAH, but got 0x%02X 0x%02X instead"))
            
            return None
        
        return cls()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_RTGAH from the specified walker.
        
        >>> fb = Hint_RTGAH.frombytes
        >>> bs = utilities.fromhex("7F 0B")
        >>> fb(bs).pprint()
        RTGAH
        """
        
        n, arg = w.unpack("BB")
        assert n == 0x7F and arg == 0x0B
        return cls()
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints self.
        """
        
        if 'p' in kwArgs:
            p = kwArgs.pop('p')
        else:
            p = pp.PP(**kwArgs)
        
        p(str(self))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()

