#
# ADFH_v20.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for version 2.0 ADFH tables.
"""

# System imports
import logging

# Other imports
from fontio3.ADFH import csmmap, groups20, nocenters
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
    Objects representing entire version 2.0 ADFH tables. These are simple
    collections of attributes:
    
        csmMap          A CSMMap object representing MAZ glyphs.
        
        groups          A groups20.Groups object representing BAZ glyphs.
        
        noCenters       A NoCenters object representing glyphs that will not be
                        automatically centered.
    
    >>> _testingValues[0].pprint()
    Table version: 2.0
    
    >>> _testingValues[1].pprint()
    Table version: 2.0
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
      [300-359]:
        Index of first CVT value: 4
        Number of y-lines: 12
        Adjust strokes right-to-left: True
      [1200-1249, 1400-1419]:
        Index of first CVT value: 12
        Number of y-lines: 30
        Adjust strokes right-to-left: False
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
            attr_initfunc = groups20.Groups,
            attr_label = "BAZ information",
            attr_showonlyiftrue = True))
    
    attrSorted = ('csmMap', 'noCenters', 'groups')
    
    version = 2.0  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ADFH object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 0000 0000 0000  0000 0000           |............    |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0000 0003 002E  0577 0000 057A 001E |.........w...z..|
              10 | 07CF 0000 0002 000C  0000 4000 FFFE 0000 |..........@.....|
              20 | FFFF C000 0014 0000  C000 FFFF 0000 FFFF |................|
              30 | C000 0001 0012 FFFF  8000 0000 4000 0000 |............@...|
              40 | 8000 0005 001A 001B  001C 0102 0103 0003 |................|
              50 | 012C 0167 0000 04B0  04E1 0001 0578 058B |.,.g.........x..|
              60 | 0001 0002 0004 000C  0001 0000 000C 001E |................|
              70 | 0000 0000                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x00020000)
        self.csmMap.buildBinary(w, **kwArgs)
        self.noCenters.buildBinary(w, **kwArgs)
        self.groups.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns an ADFH object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("ADFH_20_fvw")
        >>> fvb = ADFH.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        ADFH_20_fvw.adfh20 - DEBUG - Walker has 116 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap - DEBUG - Walker has 112 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap.glyph 0 thru glyph 1399.csmentry - DEBUG - Walker has 96 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap.glyph 0 thru glyph 1399.csmentry.entry 0.csmrecord - DEBUG - Walker has 94 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap.glyph 0 thru glyph 1399.csmentry.entry 1.csmrecord - DEBUG - Walker has 80 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap.glyph 1400 thru glyph 1402.csmentry - DEBUG - Walker has 66 remaining bytes.
        ADFH_20_fvw.adfh20.csmmap.glyph 1400 thru glyph 1402.csmentry.entry 0.csmrecord - DEBUG - Walker has 64 remaining bytes.
        ADFH_20_fvw.adfh20.nocenters - DEBUG - Walker has 50 remaining bytes.
        ADFH_20_fvw.adfh20.groups20 - DEBUG - Walker has 38 remaining bytes.
        ADFH_20_fvw.adfh20.groups20.group 0.grouprecord - DEBUG - Walker has 16 remaining bytes.
        ADFH_20_fvw.adfh20.groups20.group 1.grouprecord - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:3], logger=logger)
        ADFH_20_fvw.adfh20 - DEBUG - Walker has 3 remaining bytes.
        ADFH_20_fvw.adfh20 - ERROR - Insufficient bytes.
        
        >>> fvb(s[2:4] + s[2:4] + s[4:], logger=logger)
        ADFH_20_fvw.adfh20 - DEBUG - Walker has 116 remaining bytes.
        ADFH_20_fvw.adfh20 - ERROR - Expected version 0x00020000 but got 0x00000000 instead.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("adfh20")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x20000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00020000 but got 0x%08X instead."))
            
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
        
        groups = groups20.Groups.fromvalidatedwalker(
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
        
        if version != 0x20000:
            raise ValueError("Unknown ADFH version: 0x%08X" % (version,))
        
        csmMap = csmmap.CSMMap.fromwalker(w, **kwArgs)
        noCenters = nocenters.NoCenters.fromwalker(w, **kwArgs)
        groups = groups20.Groups.fromwalker(w, **kwArgs)
        
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
          groups = groups20._testingValues[2]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
