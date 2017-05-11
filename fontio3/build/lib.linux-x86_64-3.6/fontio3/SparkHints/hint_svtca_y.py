#
# hint_svtca_y.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
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

class Hint_SVTCA_Y(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Spark SVTCA[y] opcodes.
    """
    
    attrSpec = {}
    
    kindString = 'SVTCA_Y'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> print((Hint_SVTCA_Y()))
        SVTCA[y]
        """
        
        return "SVTCA[y]"
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        >>> utilities.hexdump(Hint_SVTCA_Y().binaryString())
               0 | 00                                       |.               |
        """
        
        w.add("B", 0)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SVTCA_Y from the specified walker, with validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_SVTCA_Y.fromvalidatedbytes
        >>> bs = utilities.fromhex("00")
        >>> obj = fvb(bs, logger=logger)
        test.svtca_y - DEBUG - Remaining walker bytes: 1
        
        >>> fvb(b"", logger=logger)
        test.svtca_y - DEBUG - Remaining walker bytes: 0
        test.svtca_y - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("01")
        >>> fvb(bs, logger=logger)
        test.svtca_y - DEBUG - Remaining walker bytes: 1
        test.svtca_y - ERROR - Was expecting opcode 0x00, but got 0x01 instead
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('svtca_y')
        else:
            logger = logger.getChild('svtca_y')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op = w.unpack("B")
        
        if op != 0:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0x00, but got 0x%02X instead"))
            
            return None
        
        return cls()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SVTCA_Y from the specified walker.
        
        >>> fb = Hint_SVTCA_Y.frombytes
        >>> bs = utilities.fromhex("00")
        >>> fb(bs).pprint()
        SVTCA[y]
        """
        
        n = w.unpack("B")
        assert n == 0
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

