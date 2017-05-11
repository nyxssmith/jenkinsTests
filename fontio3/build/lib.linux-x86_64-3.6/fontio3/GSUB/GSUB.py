#
# GSUB.py -- Top-level support for GSUB tables
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType GSUB tables.
"""

# System imports
import logging

# Other imports
from fontio3.GSUB import GSUB_v10, GSUB_v11
from fontio3.opentype import fontworkersource

# -----------------------------------------------------------------------------

#
# Public functions
#

def GSUB(w, **kwArgs):
    """
    Factory function to make a GSUB object (of whatever version) from the
    contents of the specified walker.
    """
    
    w.reset()
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        return GSUB_v10.GSUB.fromwalker(w, **kwArgs)
    
    elif version == 0x10001:
        return GSUB_v11.GSUB.fromwalker(w, **kwArgs)
        
    raise ValueError("Unknown GSUB version: 0x%08x" % (version,))


def GSUB_fromValidatedFontWorkerSource(s, **kwArgs):
    """
    Creates and returns a new GSUB from the specified stream containing
    FontWorker Source code with extensive validation via the logging module
    (the client should have done a logging.basicConfig call prior to calling
    this method, unless a logger is passed in via the 'logger' keyword
    argument).
    """
    fws = fontworkersource.FontWorkerSource(s)

    # should update to v1.1 at some point...
    return GSUB_v10.GSUB.fromValidatedFontWorkerSource(fws, **kwArgs)


def GSUB_validated(w, **kwArgs):
    """
    Factory function to make a GSUB object (of whatever version) from the
    contents of the specified walker, with validation at all levels.
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('GSUB')
    else:
        logger = logger.getChild('GSUB')
    
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        logger.info(('V0115', (), "GSUB is pre-OpenType 1.8."))
        return GSUB_v10.GSUB.fromvalidatedwalker(w, logger=logger, **kwArgs)
    
    elif version == 0x10001:
        logger.info(('V0115', (), "GSUB is OpenType 1.8 (table version 1.1)."))
        return GSUB_v11.GSUB.fromvalidatedwalker(w, logger=logger, **kwArgs)
    
    logger.error(('V0116', (version,), "Unknown version: 0x%08X."))

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
