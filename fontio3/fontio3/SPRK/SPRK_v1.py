#
# SPRK_v1.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the original Monotype-defined SPRK table, version 1, used in (and
to identify) iType Spark fonts. Note that this version is obsolete; use
SPRK_v16.py instead.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class SPRK(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing SPRK tables. Right now these are very simple: just a
    version.
    """
    
    version = 1
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SPRK object to the specified LinkedWriter.
        
        >>> obj = SPRK()
        >>> utilities.hexdump(obj.binaryString())
               0 | 0000 0001                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add('L', self.version)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> fvb = SPRK.fromvalidatedbytes
        >>> bs = utilities.fromhex("00 00 00 01")
        >>> obj = fvb(bs, logger=logger)
        test.SPRK_v1 - DEBUG - Walker has 4 remaining bytes.
        >>> obj == SPRK.frombytes(obj.binaryString())
        True
        
        >>> fvb(bs[:-1], logger=logger)
        test.SPRK_v1 - DEBUG - Walker has 3 remaining bytes.
        test.SPRK_v1 - ERROR - Insufficient bytes.
        
        >>> bs = utilities.fromhex("00 00 00 02")
        >>> obj = fvb(bs, logger=logger)
        test.SPRK_v1 - DEBUG - Walker has 4 remaining bytes.
        test.SPRK_v1 - ERROR - Unknown SPRK version: 0x00000002.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('SPRK_v1')
        else:
            logger = logger.getChild('SPRK_v1')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        v = w.unpack("L")
        
        if v != cls.version:
            logger.error(('V0953', (v,), "Unknown SPRK version: 0x%08X."))
            return None
        
        return cls()
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new SPRK object from the data in the specified walker.
        
        >>> fb = SPRK.frombytes
        >>> bs = utilities.fromhex("00 00 00 01")
        >>> obj = fb(bs)
        >>> obj.version
        1
        
        >>> obj == fb(obj.binaryString())
        True
        """
        
        v = w.unpack('L')
        return cls()

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
    if __debug__:
        _test()

