#
# GDEF.py -- Top-level support for GDEF tables
#
# Copyright © 2005-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType GDEF tables.
"""

# System imports
import logging

# Other imports
from fontio3.GDEF import GDEF_v0, GDEF_v1, GDEF_v13
from fontio3.opentype import fontworkersource

# -----------------------------------------------------------------------------

#
# Public functions
#

def GDEF(w, **kwArgs):
    """
    Factory function to make a GDEF object (of whatever version) from the
    contents of the specified walker.
    
    >>> bw = walker.StringWalker
    >>> obj = GDEF(bw(_testingData[0]))
    >>> obj.pprint()
    Version:
      Major version: 1
      Minor version: 0

    >>> obj = GDEF(bw(_testingData[1]))
    >>> obj.pprint()
    Version:
      Major version: 1
      Minor version: 2

    >>> ed = utilities.fakeEditor(5)
    >>> obj = GDEF(bw(_testingData[2]), editor=ed)
    >>> obj.pprint()
    Version:
      Major version: 1
      Minor version: 3

    >>> obj = GDEF(bw(_testingData[3]))
    Traceback (most recent call last):
    ...
    ValueError: Unknown GDEF version: 0xDEADBEEF
    """
    
    w.reset()
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        return GDEF_v0.GDEF.fromwalker(w, **kwArgs)
    
    elif version == 0x10002:
        return GDEF_v1.GDEF.fromwalker(w, **kwArgs)
        
    elif version == 0x10003:
        return GDEF_v13.GDEF.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown GDEF version: 0x%08X" % (version,))

def GDEF_fromValidatedFontWorkerSource(s, **kwArgs):
    """
    Creates and returns a new GDEF from the specified stream containing
    FontWorker Source code with extensive validation via the logging module
    (the client should have done a logging.basicConfig call prior to calling
    this method, unless a logger is passed in via the 'logger' keyword
    argument).
    
    We will always generate a GDEF_v1 from Font Worker source.
    
    >>> s = StringIO("Some random text")
    >>> ed = utilities.fakeEditor(5)
    >>> logger = utilities.makeDoctestLogger("test")
    >>> namer = ed.getNamer()
    >>> obj = GDEF_fromValidatedFontWorkerSource(s, editor=ed, logger=logger, namer=namer)
    test.GDEF - ERROR - Expected 'FontDame GDEF table' in first line.
    """
    fws = fontworkersource.FontWorkerSource(s)

    return GDEF_v1.GDEF.fromValidatedFontWorkerSource(fws, **kwArgs)

def GDEF_validated(w, **kwArgs):
    """
    Factory function to make a GDEF object (of whatever version) from the
    contents of the specified walker, with validation at all levels.

    >>> logger = utilities.makeDoctestLogger('test')
    >>> bw = walker.StringWalker
    >>> obj = GDEF_validated(bw(_testingData[0]), logger=logger)
    test.GDEF - DEBUG - Walker has 12 remaining bytes.
    test.GDEF - INFO - GDEF is pre-OpenType 1.6.
    test.GDEF.GDEF - DEBUG - Walker has 12 remaining bytes.
    test.GDEF.GDEF.version - DEBUG - Walker has 12 remaining bytes.

    >>> obj = GDEF_validated(bw(_testingData[1]), logger=logger)
    test.GDEF - DEBUG - Walker has 14 remaining bytes.
    test.GDEF - INFO - GDEF is OpenType 1.6.
    test.GDEF.GDEF - DEBUG - Walker has 14 remaining bytes.
    test.GDEF.GDEF.version - DEBUG - Walker has 14 remaining bytes.

    >>> ed = utilities.fakeEditor(5)
    >>> obj = GDEF_validated(bw(_testingData[2]), editor=ed, logger=logger)
    test.GDEF - DEBUG - Walker has 18 remaining bytes.
    test.GDEF - INFO - GDEF is OpenType 1.8 (version 1.3).
    test.GDEF.GDEF - DEBUG - Walker has 18 remaining bytes.
    test.GDEF.GDEF.version - DEBUG - Walker has 18 remaining bytes.

    >>> obj = GDEF_validated(bw(_testingData[3]), logger=logger)
    test.GDEF - DEBUG - Walker has 4 remaining bytes.
    test.GDEF - ERROR - Unknown version: 0xDEADBEEF.
    
    >>> obj = GDEF_validated(bw(_testingData[0][:1]), logger=logger)
    test.GDEF - DEBUG - Walker has 1 remaining bytes.
    test.GDEF - ERROR - Insufficient bytes.
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('GDEF')
    else:
        logger = logger.getChild('GDEF')
    
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version == 0x10000:
        logger.info(('V0115', (), "GDEF is pre-OpenType 1.6."))
        return GDEF_v0.GDEF.fromvalidatedwalker(
            w, logger=logger, is_v0=True, **kwArgs)
    
    elif version == 0x10002:
        logger.info(('V0115', (), "GDEF is OpenType 1.6."))
        return GDEF_v1.GDEF.fromvalidatedwalker(
            w, logger=logger, is_v0=False, **kwArgs)
    
    elif version == 0x10003:
        logger.info(('V0115', (), "GDEF is OpenType 1.8 (version 1.3)."))
        return GDEF_v13.GDEF.fromvalidatedwalker(
            w, logger=logger, is_v0=False, **kwArgs)
    
    logger.error(('V0116', (version,), "Unknown version: 0x%08X."))
    return None

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walker
    from io import StringIO

    _testingData = (
      utilities.fromhex("00010000 0000 0000 0000 0000"),
      utilities.fromhex("00010002 0000 0000 0000 0000 0000"),
      utilities.fromhex("00010003 0000 0000 0000 0000 0000 0000 0000"),
      utilities.fromhex("DEADBEEF"))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
