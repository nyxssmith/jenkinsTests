#
# maxp.py
#
# Copyright © 2004-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType 'maxp' tables.
"""

# System imports
import logging

# Other imports
from fontio3.maxp import maxp_cff, maxp_tt

# -----------------------------------------------------------------------------

#
# Functions
#

def Maxp(w, **kwArgs):
    """
    Factory function for Maxp_TT or Maxp_CFF objects.
    """
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        return maxp_tt.Maxp_TT.fromwalker(w, **kwArgs)
    elif version == 0x5000:
        return maxp_cff.Maxp_CFF.fromwalker(w, **kwArgs)
    else:
        raise ValueError("Unknown 'maxp' version: 0x%08X" % (version,))

def Maxp_validated(w, **kwArgs):
    """
    Factory function that also does validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("maxp")
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        fvw = maxp_tt.Maxp_TT.fromvalidatedwalker
    
    elif version == 0x5000:
        fvw = maxp_cff.Maxp_CFF.fromvalidatedwalker
    
    else:
        logger.error((
          'E1908',
          (version,),
          "Unknown version: 0x%08X."))
        
        return None
    
    return fvw(w, logger=logger, **kwArgs)

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
