#
# hint_sds.py
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

class Hint_SDS(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing Spark SDS opcodes.
    """
    
    attrSpec = dict(
        shift = dict())
    
    kindString = 'SDS'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> print((Hint_SDS(2)))
        SDS 2
        """
        
        return "SDS %d" % (self.shift,)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        >>> utilities.hexdump(Hint_SDS(2).binaryString())
               0 | 5F02                                     |_.              |
        """
        
        w.add("BB", 0x5F, self.shift)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SDS from the specified walker, with validation.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_SDS.fromvalidatedbytes
        >>> bs = utilities.fromhex("5F 04")
        >>> obj = fvb(bs, logger=logger)
        test.sds - DEBUG - Remaining walker bytes: 2
        >>> print(obj)
        SDS 4
        
        >>> fvb(b"", logger=logger)
        test.sds - DEBUG - Remaining walker bytes: 0
        test.sds - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00 01")
        >>> fvb(bs, logger=logger)
        test.sds - DEBUG - Remaining walker bytes: 2
        test.sds - ERROR - Was expecting opcode 0x5F, but got 0x00 instead
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('sds')
        else:
            logger = logger.getChild('sds')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        op, shift = w.unpack("BB")
        
        if op != 0x5F:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0x5F, but got 0x%02X instead"))
            
            return None
        
        return cls(shift)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_SDS from the specified walker.
        
        >>> fb = Hint_SDS.frombytes
        >>> bs = utilities.fromhex("5F 04")
        >>> fb(bs).pprint()
        SDS 4
        """
        
        n, shift = w.unpack("BB")
        assert n == 0x5F
        return cls(shift)
    
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

