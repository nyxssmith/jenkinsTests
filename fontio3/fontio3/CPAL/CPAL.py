#
# CPAL.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Top-level support for CPAL tables.
"""

# System imports
import logging

# Other imports
from fontio3.CPAL import CPAL_v0, CPAL_v1

# -----------------------------------------------------------------------------

#
# Public functions
#

def CPAL(w, **kwArgs):
    """
    Factory function to make a CPAL object (of whatever version) from the
    contents of the specified walker.
    """

    w.reset()
    version = w.unpack("H", advance=False)

    if version == 0:
        return CPAL_v0.CPAL.fromwalker(w, **kwArgs)

    else:
        # 1 or higher will return v1, since USHORT versions are supposed to be
        # forward-compatible.
        return CPAL_v1.CPAL.fromwalker(w, **kwArgs)

def CPAL_validated(w, **kwArgs):
    """
    Factory function to make a CPAL object (of whatever version) from the
    contents of the specified walker, with validation at all levels
    """

    logger = kwArgs.pop('logger', None)

    if logger is None:
        logger = logging.getLogger().getChild('CPAL')
    else:
        logger = logger.getChild('CPAL')

    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))

    if w.length() < 14:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None

    w.reset()
    version = w.unpack("H", advance=False)
    logger.info(('Vxxxx', (version,), "Version is %d."))

    if version == 0:
        return CPAL_v0.CPAL.fromvalidatedwalker(w, logger=logger, **kwArgs)

    else:
        if version > 1:
            # 1 _or higher_ will return v1, since USHORT versions are supposed
            # to be forward-compatible, but we will warn about unknown version.
            logger.warning((
              'Vxxxx',
              (version,),
              "Unknown CPAL version %d; interpreting as v1."))
        
        return CPAL_v1.CPAL.fromvalidatedwalker(w, logger=logger, **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():  # pragma: no cover
    import doctest
    doctest.testmod()

if __name__ == "__main__":  # pragma: no cover
    if __debug__:
        _test()

