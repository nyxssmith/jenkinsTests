#
# SPRK.py -- factory
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# Other imports
from fontio3.SPRK import SPRK_v1, SPRK_v16

# -----------------------------------------------------------------------------

#
# Functions
#

def SPRK(w, **kwArgs):
    """
    """
    
    version = w.unpack("H", advance=False)
    
    if version == 0:  # the first 2 bytes of the 4-byte value "1" will be 0
        return SPRK_v1.SPRK.fromwalker(w, **kwArgs)
    elif version == 16:
        return SPRK_v16.SPRK.fromwalker(w, **kwArgs)
    else:
        raise ValueError("Unknown SPRK version: %d" % (version,))

def SPRK_validated(w, **kwArgs):
    """
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('SPRK')
    else:
        logger = logger.getChild('SPRK')
    
    byteLength = w.length()
    logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
    
    if byteLength < 2:
        logger.error((
          'V0004',
          (),
          "Insufficient bytes for OS/2 version"))
        
        return None
    
    version = w.unpack("H", advance=False)
    
    if version not in {0, 16}:
        logger.error((
          'V0002',
          (version,),
          "Unknown SPRK version: %d"))
        
        return None
    
    kwArgs['logger'] = logger
    
    if version == 0:  # the first 2 bytes of the 4-byte value "1" will be 0
        return SPRK_v1.SPRK.fromvalidatedwalker(w, **kwArgs)
    
    return SPRK_v16.SPRK.fromvalidatedwalker(w, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

