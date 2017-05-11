#
# hint_sdb.py
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

class Hint_SDB(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Spark SDB opcodes.
    """
    
    attrSpec = dict(
        base = dict())
    
    kindString = 'SDB'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> print((Hint_SDB(7)))
        SDB 7
        """
        
        return "SDB %d" % (self.base,)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        >>> utilities.hexdump(Hint_SDB(7).binaryString())
               0 | 5E07                                     |^.              |
        """
        
        w.add("BB", 0x5E, self.base)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SDB from the specified walker, with validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_SDB.fromvalidatedbytes
        >>> bs = utilities.fromhex("5E 0F")
        >>> obj = fvb(bs, logger=logger)
        test.sdb - DEBUG - Remaining walker bytes: 2
        >>> print(obj)
        SDB 15
        
        >>> fvb(b"", logger=logger)
        test.sdb - DEBUG - Remaining walker bytes: 0
        test.sdb - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00 01")
        >>> fvb(bs, logger=logger)
        test.sdb - DEBUG - Remaining walker bytes: 2
        test.sdb - ERROR - Was expecting opcode 0x5E, but got 0x00 instead
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('sdb')
        else:
            logger = logger.getChild('sdb')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op, base = w.unpack("BB")
        
        if op != 0x5E:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0x5E, but got 0x%02X instead"))
            
            return None
        
        return cls(base)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SDB from the specified walker.
        
        >>> fb = Hint_SDB.frombytes
        >>> bs = utilities.fromhex("5E 0B")
        >>> fb(bs).pprint()
        SDB 11
        """
        
        n, base = w.unpack("BB")
        assert n == 0x5E
        return cls(base)
    
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

