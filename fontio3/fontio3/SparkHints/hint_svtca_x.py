#
# hint_svtca_x.py
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

class Hint_SVTCA_X(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Spark SVTCA[x] opcodes.
    """
    
    attrSpec = {}
    
    kindString = 'SVTCA_X'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> print((Hint_SVTCA_X()))
        SVTCA[x]
        """
        
        return "SVTCA[x]"
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        >>> utilities.hexdump(Hint_SVTCA_X().binaryString())
               0 | 01                                       |.               |
        """
        
        w.add("B", 1)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SVTCA_X from the specified walker, with validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_SVTCA_X.fromvalidatedbytes
        >>> bs = utilities.fromhex("01")
        >>> obj = fvb(bs, logger=logger)
        test.svtca_x - DEBUG - Remaining walker bytes: 1
        
        >>> fvb(b"", logger=logger)
        test.svtca_x - DEBUG - Remaining walker bytes: 0
        test.svtca_x - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00")
        >>> fvb(bs, logger=logger)
        test.svtca_x - DEBUG - Remaining walker bytes: 1
        test.svtca_x - ERROR - Was expecting opcode 0x01, but got 0x00 instead
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('svtca_x')
        else:
            logger = logger.getChild('svtca_x')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op = w.unpack("B")
        
        if op != 1:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0x01, but got 0x%02X instead"))
            
            return None
        
        return cls()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SVTCA_X from the specified walker.
        
        >>> fb = Hint_SVTCA_X.frombytes
        >>> bs = utilities.fromhex("01")
        >>> fb(bs).pprint()
        SVTCA[x]
        """
        
        n = w.unpack("B")
        assert n == 1
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

