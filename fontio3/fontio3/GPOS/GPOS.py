#
# GPOS.py -- Top-level support for GPOS tables
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType GPOS tables.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import GPOS_v10, GPOS_v11
from fontio3.opentype import fontworkersource

# -----------------------------------------------------------------------------

#
# Public functions
#

def GPOS(w, **kwArgs):
    """
    Factory function to make a GPOS object (of whatever version) from the
    contents of the specified walker.
    """
    
    w.reset()
    version = w.unpack("L", advance=False)

    otcd = None
    GDEF = kwArgs.get('GDEF')
    if GDEF:
        ce = GDEF.__dict__.get('_creationExtras')
        if ce:
            otcd = ce.get('otcommondeltas')

    if version == 0x10000:
        return GPOS_v10.GPOS.fromwalker(w, otcommondeltas=otcd, **kwArgs)
    
    elif version == 0x10001:
        return GPOS_v11.GPOS.fromwalker(w, otcommondeltas=otcd, **kwArgs)
        
    raise ValueError("Unknown GPOS version: 0x%08x" % (version,))

def GPOS_fromValidatedFontWorkerSource(s, **kwArgs):
    """
    Creates and returns a new GPOS from the specified stream containing
    FontWorker Source code with extensive validation via the logging module
    (the client should have done a logging.basicConfig call prior to calling
    this method, unless a logger is passed in via the 'logger' keyword
    argument).
    
    We will always generate a GPOS_v11 from Font Worker source.    
    """
    fws = fontworkersource.FontWorkerSource(s)

    return GPOS_v11.GPOS.fromValidatedFontWorkerSource(fws, **kwArgs)

def GPOS_validated(w, **kwArgs):
    """
    Factory function to make a GPOS object (of whatever version) from the
    contents of the specified walker, with validation at all levels.
    """
    
    logger = kwArgs.pop('logger', None)

    if logger is None:
        logger = logging.getLogger().getChild('GPOS')
    else:
        logger = logger.getChild('GPOS')

    otcd = None
    GDEF = kwArgs.get('GDEF')
    if GDEF:
        ce = GDEF.__dict__.get('_creationExtras')
        if ce:
            otcd = ce.get('otcommondeltas')
    
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        logger.info(('V0115', (), "GPOS is pre-OpenType 1.8."))
        fvw = GPOS_v10.GPOS.fromvalidatedwalker
        return fvw(w, logger=logger, otcommondeltas=otcd, **kwArgs)
    
    elif version == 0x10001:
        logger.info(('V0115', (), "GPOS is OpenType 1.8 (table version 1.1)"))
        fvw = GPOS_v11.GPOS.fromvalidatedwalker
        return fvw(w, logger=logger, otcommondeltas=otcd, **kwArgs)
    
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
