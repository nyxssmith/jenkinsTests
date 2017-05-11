#
# STAT.py
#
# Copyright © 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for STAT tables.
"""

# System imports
import logging

# Other imports
from fontio3.STAT import STAT_v10, STAT_v11

# -----------------------------------------------------------------------------

#
# Public functions
#

def STAT(w, **kwArgs):
    """
    Factory function to make a STAT object (of whatever version) from the
    specified walker.
    """
    
    w.reset()
    version = w.unpack("L", advance=False)
    
    if version == 0x00010000:
        return STAT_v10.STAT.fromwalker(w, **kwArgs)
    
    if version == 0x00010001:
        return STAT_v11.STAT.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown STAT version: 0x%08X" % (version,))


def STAT_validated(w, **kwArgs):
    """
    Factory function to make a STAT object (of whatever version) from the
    specified walker, doing source validation.
    """
    
    origLogger = kwArgs.pop('logger', None)
    
    if origLogger is None:
        logger = logging.getLogger().getChild('STAT_factory')
    else:
        logger = origLogger.getChild('STAT_factory')
    
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x00010000:
        return STAT_v10.STAT.fromvalidatedwalker(w, logger=origLogger, **kwArgs)
    
    if version == 0x00010001:
        return STAT_v11.STAT.fromvalidatedwalker(w, logger=origLogger, **kwArgs)
        
    logger.error(('V1076', (version,), "Unknown version: 0x%08X."))
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
