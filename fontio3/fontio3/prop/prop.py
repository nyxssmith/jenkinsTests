#
# prop.py
#
# Copyright © 2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'prop' table.
"""

# System imports
import logging

# Other imports
from fontio3.prop import prop_v1, prop_v2, prop_v3

# -----------------------------------------------------------------------------

#
# Private constants
#

_dispatchTable = {
  0x10000: prop_v1.Prop.fromwalker,
  0x20000: prop_v2.Prop.fromwalker,
  0x30000: prop_v3.Prop.fromwalker}

_dispatchTable_validated = {
  0x10000: prop_v1.Prop.fromvalidatedwalker,
  0x20000: prop_v2.Prop.fromvalidatedwalker,
  0x30000: prop_v3.Prop.fromvalidatedwalker}

_nextStepBackward = {
  0x20000: prop_v2.Prop.asVersion1,
  0x30000: prop_v3.Prop.asVersion2}

_nextStepForward = {
  0x10000: prop_v2.Prop.fromversion1,
  0x20000: prop_v3.Prop.fromversion2}

# -----------------------------------------------------------------------------

#
# Public functions
#

def Prop(w, **kwArgs):
    """
    Factory function to make a Prop object of the correct type.
    """
    
    w.reset()
    version = w.unpack("L", advance=False)
    
    if version in _dispatchTable:
        return _dispatchTable[version](w, **kwArgs)
    
    raise ValueError("Unknown version for 'prop' table: %s" % (version,))

def Prop_validated(w, **kwArgs):
    """
    Factory function to make a Prop object of the correct type, doing source
    validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("prop")
    w.reset()
    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
    
    if w.length() < 4:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    version = w.unpack("L", advance=False)
    
    if version not in _dispatchTable_validated:
        logger.error((
          'V0002',
          (version,),
          "Version 0x%08X is not recognized for a 'prop' table."))
        
        return None
    
    return _dispatchTable_validated[version](w, logger=logger, **kwArgs)

def versionConverted(oldTable, newVersion, **kwArgs):
    """
    """
    
    oldVersion = oldTable.tableVersion
    
    if oldVersion == newVersion:
        return oldTable
    
    if oldVersion < newVersion:
        # converting to more modern
        while oldVersion < newVersion:
            f = _nextStepForward[oldVersion]
            oldTable = f(oldTable, **kwArgs)
            oldVersion = oldTable.tableVersion
    
    else:
        # converting to older version
        while oldVersion > newVersion:
            f = _nextStepBackward[oldVersion]
            oldTable = f(oldTable, **kwArgs)
            oldVersion = oldTable.tableVersion
    
    return oldTable

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
