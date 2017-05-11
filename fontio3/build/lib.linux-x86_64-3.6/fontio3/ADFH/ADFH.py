#
# ADFH.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ADFH tables.
"""

# System imports
import logging

# Other imports
from fontio3.ADFH import ADFH_v15, ADFH_v20

# -----------------------------------------------------------------------------

#
# Public functions
#

def ADFH(w, **kwArgs):
    """
    Factory function to make an ADFH object (of whatever version) from the
    specified walker.
    """
    
    w.reset()
    version = w.unpack("L", advance=False)
    
    if version == 0x00015000:
        return ADFH_v15.ADFH.fromwalker(w, **kwArgs)
    
    if version == 0x00020000:
        return ADFH_v20.ADFH.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown ADFH version: 0x%08X" % (version,))

def ADFH_validated(w, **kwArgs):
    """
    Factory function to make an ADFH object (of whatever version) from the
    specified walker, doing source validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("ADFH")
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x00015000:
        return ADFH_v15.ADFH.fromvalidatedwalker(w, logger=logger, **kwArgs)
    
    if version == 0x00020000:
        return ADFH_v20.ADFH.fromvalidatedwalker(w, logger=logger, **kwArgs)
    
    logger.error(('V0599', (version,), "Unknown version: 0x%08X."))
    return None

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
