#
# vhea.py
#
# Copyright © 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType 'vhea' tables.
"""

# Other imports
from fontio3.vhea import vhea_v1, vhea_v11

# -----------------------------------------------------------------------------

#
# Functions
#

def Vhea(w, **kwArgs):
    """
    Factory function for Vhea objects of any version.
    """
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        return vhea_v1.Vhea.fromwalker(w, **kwArgs)
    elif version == 0x11000:
        return vhea_v11.Vhea.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown 'vhea' version: 0x%08X." % (version,))

def Vhea_validated(w, **kwArgs):
    """
    Factory function that also does validation.
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('vhea')
    else:
        logger = logger.getChild('vhea')
    
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        return vhea_v1.Vhea.fromvalidatedwalker(w, logger=logger, **kwArgs)
    elif version == 0x11000:
        return vhea_v11.Vhea.fromvalidatedwalker(w, logger=logger, **kwArgs)
    
    logger.error((
      'E2602',
      (version,),
      "Unrecognized 'vhea' version: 0x%08X."))
    
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
