#
# ADFH_v15.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for version 1.5 ADFH tables.
"""

# System imports
import logging

# Other imports
from fontio3.ADFH import csmmap, groups15, nocenters
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_partial(p, obj, **kwArgs):
    p.simple(obj.version, label="Table version")

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ADFH(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire version 1.5 ADFH tables. These are simple
    collections of attributes:
    
        csmMap          A CSMMap object representing MAZ glyphs.
        
        groups          A groups15.Groups object representing BAZ glyphs.
        
        noCenters       A NoCenters object representing glyphs that will not be
                        automatically centered.
    
    >>> _testingValues[0].pprint()
    Table version: 1.5
    
    >>> _testingValues[1].pprint()
    Table version: 1.5
    Glyph-to-CSM map:
      [0-1399]:
        Entry #1:
          Lower limit of size range (inclusive): 12
          Inside cutoff: 0.25
          Outside cutoff: -2.0
          Gamma: -0.25
        Entry #2:
          Lower limit of size range (inclusive): 20
          Inside cutoff: 0.75
          Outside cutoff: -1.0
          Gamma: -0.25
      [1400-1402]:
        Entry #1:
          Lower limit of size range (inclusive): 18
          Inside cutoff: -0.5
          Outside cutoff: 0.25
          Gamma: 0.5
      [1403-1999]:
        Entry #1:
          Lower limit of size range (inclusive): 12
          Inside cutoff: 0.25
          Outside cutoff: -2.0
          Gamma: -0.25
        Entry #2:
          Lower limit of size range (inclusive): 20
          Inside cutoff: 0.75
          Outside cutoff: -1.0
          Gamma: -0.25
    Non-centered glyphs:
      26-28, 258-259
    BAZ information:
      2-4, 10-11, 30-31, 33, 35-39
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_pprintfunc_partial = _pprint_partial)
    
    attrSpec = dict(
        csmMap = dict(
            attr_followsprotocol = True,
            attr_initfunc = csmmap.CSMMap,
            attr_label = "Glyph-to-CSM map",
            attr_showonlyiftrue = True),
      
        noCenters = dict(
            attr_followsprotocol = True,
            attr_initfunc = nocenters.NoCenters,
            attr_label = "Non-centered glyphs",
            attr_showonlyiftrue = True),
      
        groups = dict(
            attr_followsprotocol = True,
            attr_initfunc = groups15.Groups,
            attr_label = "BAZ information",
            attr_showonlyiftrue = True))
    
    attrSorted = ('csmMap', 'noCenters', 'groups')
    
    version = 1.5  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ADFH object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 5000 0000 0000  0000 0000           |..P.........    |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 5000 0003 002E  0577 0000 057A 001E |..P......w...z..|
              10 | 07CF 0000 0002 000C  0000 4000 FFFE 0000 |..........@.....|
              20 | FFFF C000 0014 0000  C000 FFFF 0000 FFFF |................|
              30 | C000 0001 0012 FFFF  8000 0000 4000 0000 |............@...|
              40 | 8000 0005 001A 001B  001C 0102 0103 0005 |................|
              50 | 0002 0004 0000 000A  000B 0000 001E 001F |................|
              60 | 0000 0021 0021 0000  0023 0027 0000      |...!.!...#.'..  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x00015000)
        self.csmMap.buildBinary(w, **kwArgs)
        self.noCenters.buildBinary(w, **kwArgs)
        self.groups.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns an ADFH object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("adfh15")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x00015000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00015000, but got 0x%08X."))
            
            return None
        
        csmMap = csmmap.CSMMap.fromvalidatedwalker(w, logger=logger, **kwArgs)
        
        if csmMap is None:
            return None
        
        noCenters = nocenters.NoCenters.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if noCenters is None:
            return None
        
        groups = groups15.Groups.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if groups is None:
            return None
        
        return cls(csmMap, noCenters, groups)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an ADFH object from the specified walker.
        
        >>> fb = ADFH.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x15000:
            raise ValueError("Unknown ADFH version: 0x%08X" % (version,))
        
        csmMap = csmmap.CSMMap.fromwalker(w, **kwArgs)
        noCenters = nocenters.NoCenters.fromwalker(w, **kwArgs)
        groups = groups15.Groups.fromwalker(w, **kwArgs)
        return cls(csmMap, noCenters, groups)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        ADFH(),
        
        ADFH(
          csmMap = csmmap._testingValues[1],
          noCenters = nocenters._testingValues[1],
          groups = groups15._testingValues[1]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
