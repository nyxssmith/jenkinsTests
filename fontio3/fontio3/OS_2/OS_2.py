#
# OS_2.py
#
# Copyright © 2010-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Factory functions for creating OS/2 tables, and converting them to different
versions.
"""

# Other imports
from fontio3.OS_2 import (
  OS_2_v0_mac,
  OS_2_v0,
  OS_2_v1,
  OS_2_v2,
  OS_2_v3,
  OS_2_v4,
  OS_2_v5)
  
from fontio3.utilities import convertertoken
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Private constants
#

_dispatchTable = {
  (0, 68): OS_2_v0_mac.OS_2.fromwalker,
  (0, 78): OS_2_v0.OS_2.fromwalker,
  (1, 86): OS_2_v1.OS_2.fromwalker,
  (2, 96): OS_2_v2.OS_2.fromwalker,
  (3, 96): OS_2_v3.OS_2.fromwalker,
  (4, 96): OS_2_v4.OS_2.fromwalker,
  (5, 100): OS_2_v5.OS_2.fromwalker}

_dispatchTable_validated = {
  (0, 68): OS_2_v0_mac.OS_2.fromvalidatedwalker,
  (0, 78): OS_2_v0.OS_2.fromvalidatedwalker,
  (1, 86): OS_2_v1.OS_2.fromvalidatedwalker,
  (2, 96): OS_2_v2.OS_2.fromvalidatedwalker,
  (3, 96): OS_2_v3.OS_2.fromvalidatedwalker,
  (4, 96): OS_2_v4.OS_2.fromvalidatedwalker,
  (5, 100): OS_2_v5.OS_2.fromvalidatedwalker}

_nextStepBackward = {
  5: OS_2_v5.OS_2.asVersion4,
  4: OS_2_v4.OS_2.asVersion3,
  3: OS_2_v3.OS_2.asVersion2,
  2: OS_2_v2.OS_2.asVersion1,
  1: OS_2_v1.OS_2.asVersion0,
  0: OS_2_v0.OS_2.asVersion0Mac}

_nextStepForward = {
  -1: OS_2_v0.OS_2.fromversion0mac,
  0: OS_2_v1.OS_2.fromversion0,
  1: OS_2_v2.OS_2.fromversion1,
  2: OS_2_v3.OS_2.fromversion2,
  3: OS_2_v4.OS_2.fromversion3,
  4: OS_2_v5.OS_2.fromversion4}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _addConverted(obj, **kwArgs):
    """
    Adds 'converted' method to object. Converter Tokens are added based
    on the object's current version.
    """
    
    CT = convertertoken.ConverterToken
    
    def cm(**kwArgs):
        if kwArgs.get('returnTokens', False):
            if obj.version == 0:
                return (
                  CT('To OS/2 Version 1', lambda x:versionConverted(x, 1)),
                  CT('To OS/2 Version 2', lambda x:versionConverted(x, 2)),
                  CT('To OS/2 Version 3', lambda x:versionConverted(x, 3)),
                  CT('To OS/2 Version 4', lambda x:versionConverted(x, 4)),
                  CT('To OS/2 Version 5', lambda x:versionConverted(x, 5)))

            if obj.version == 1:
                return (
                  CT('To OS/2 Version 2', lambda x:versionConverted(x, 2)),
                  CT('To OS/2 Version 3', lambda x:versionConverted(x, 3)),
                  CT('To OS/2 Version 4', lambda x:versionConverted(x, 4)),
                  CT('To OS/2 Version 5', lambda x:versionConverted(x, 5)))

            if obj.version == 2:
                return (
                  CT('To OS/2 Version 3', lambda x:versionConverted(x, 3)),
                  CT('To OS/2 Version 4', lambda x:versionConverted(x, 4)),
                  CT('To OS/2 Version 5', lambda x:versionConverted(x, 5)))

            if obj.version == 3:
                return (
                  CT('To OS/2 Version 4', lambda x:versionConverted(x, 4)),
                  CT('To OS/2 Version 5', lambda x:versionConverted(x, 5)))

            if obj.version == 4:
                return (
                  CT('To OS/2 Version 3', lambda x:versionConverted(x, 3)),
                  CT('To OS/2 Version 5', lambda x:versionConverted(x, 5)))

            if obj.version == 5:
                return (
                  CT('To OS/2 Version 3', lambda x:versionConverted(x, 3)),
                  CT('To OS/2 Version 4', lambda x:versionConverted(x, 4)))
            
        ctk = kwArgs.get('useToken', None)
        
        if ctk:
            return ctk.func(obj)
            
    obj.converted = cm

# -----------------------------------------------------------------------------

#
# Public functions
#

def OS_2(w, **kwArgs):
    """
    Factory function to make a OS_2 object from the contents of the specified
    walker.
    """
    
    w.reset()
    version = w.unpack("H", advance=False)
    byteLength = w.length()
    key = (version, byteLength)
    
    if key in _dispatchTable:
        tbl = _dispatchTable[key](w, **kwArgs)
        
        if tbl is not None:
            _addConverted(tbl)
        
        return tbl
    
    raise ValueError("Unknown version/length for OS/2 table: %s" % (key,))

def OS_2_validated(w, **kwArgs):
    """
    Validating version of factory function.
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('OS/2')
    else:
        logger = logger.getChild('OS/2')
    
    byteLength = w.length()
    logger.debug(('V0001', (byteLength,), "Walker has %d remaining bytes."))
    
    if byteLength < 2:
        logger.error((
          'E2127',
          (),
          "Insufficient bytes for OS/2 version"))
        
        return None
    
    version = w.unpack("H", advance=False)
    
    if not (0 <= version <= 5):
        logger.error((
          'E2132',
          (version,),
          "Version %d is not valid"))
        
        return None
    
    if version < 2:
        logger.warning((
          'W2106',
          (),
          "Table version is <2, and thus very old."))
    
    key = (version, byteLength)
    
    if key not in _dispatchTable_validated:
        logger.error((
          'E2127',
          (),
          "Table has unexpected length"))
        
        return None
    
    tbl = _dispatchTable_validated[key](
      w,
      logger = logger,
      annotateBits = True,
      **kwArgs)

    if tbl is not None:
        _addConverted(tbl)
    
    return tbl

def versionConverted(oldTable, newVersion, **kwArgs):
    """
    Given an OS_2 object returns a new object with the specified version.
    """
    
    oldVersion = oldTable.version
    
    if oldVersion == 0 and (not hasattr(oldTable, 'sTypoAscender')):
        oldVersion = -1  # original Mac version
    
    if oldVersion == newVersion:
        return oldTable
    
    if oldVersion < newVersion:
        # converting to more modern
        while oldVersion < newVersion:
            f = _nextStepForward[oldVersion]
            oldTable = f(oldTable, **kwArgs)
            oldVersion += 1
    
    else:
        # converting to older
        while oldVersion > newVersion:
            f = _nextStepBackward[oldVersion]
            oldTable = f(oldTable, **kwArgs)
            oldVersion -= 1

    _addConverted(oldTable)    
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
