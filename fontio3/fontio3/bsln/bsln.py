#
# bsln.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the AAT 'bsln' table.
"""

# System imports
import collections
import logging
import operator

# Other imports
from fontio3.bsln import baselinekinds, positions_distance, positions_point
from fontio3.fontdata import mapmeta
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Private constants
#

# To save having zillions of different objects all with the same actual value
# and meaning, we pre-define baseline kinds to be used throughout this code.

_premades = tuple(baselinekinds.BaselineKind(n) for n in range(32))

# -----------------------------------------------------------------------------

#
# Classes
#

class Bsln(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'bsln' tables. These are dicts mapping glyph
    indices to BaselineKind values. There is a single attribute called
    positions which is either a Positions_Distance or a Positions_Point object.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    attrSpec = dict(
        positions = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: positions_distance.Positions_Distance([0] * 32)),
            attr_label = "Baseline positions"))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bsln object from the specified walker, doing
        source validation. There is one required keyword argument,
        fontGlyphCount.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("bsln")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x10000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00010000, but got 0x%08X instead."))
            
            return None
        
        format, n = w.unpack("2H")
        
        if not (0 <= format < 4):
            logger.error((
              'V0812',
              (format,),
              "Unrecognized data format (%d) for the 'bsln' table."))
            
            return None
        
        d = dict.fromkeys(range(kwArgs['fontGlyphCount']), _premades[n])
        
        if format < 2:
            p = positions_distance.Positions_Distance.fromvalidatedwalker(
              w,
              logger = logger)
            
            if p is None:
                return None
            
            if format == 1:
                lk = lookup.Lookup.fromvalidatedwalker(w, logger=logger)
                
                if lk is None:
                    return None
                
                d.update(lk)
        
        else:
            p = positions_point.Positions_Point.fromvalidatedwalker(
              w,
              logger = logger)
            
            if p is None:
                return None
            
            if format == 3:
                lk = lookup.Lookup.fromvalidatedwalker(w, logger=logger)
                
                if lk is None:
                    return None
                
                d.update(lk)
        
        return cls(d, positions=p)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Bsln object from the specified walker. There
        is one required keyword argument, fontGlyphCount.
        
        >>> for i in range(4):
        ...     t = _testingValues[i]
        ...     print(t == Bsln.frombytes(t.binaryString(), fontGlyphCount=30))
        True
        True
        True
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'bsln' version: %d" % (version,))
        
        format, n = w.unpack("2H")
        
        if not (0 <= format < 4):
            raise ValueError("Unknown format in 'bsln' table: %d" % (format,))
        
        d = dict.fromkeys(range(kwArgs['fontGlyphCount']), _premades[n])
        
        if format < 2:
            p = positions_distance.Positions_Distance.fromwalker(w)
            
            if format == 1:
                d.update(lookup.Lookup.fromwalker(w))
        
        else:
            p = positions_point.Positions_Point.fromwalker(w)
            
            if format == 3:
                d.update(lookup.Lookup.fromwalker(w))
        
        return cls(d, positions=p)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Bsln object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0000 0000 0000  0000 0400 FFEC 0708 |................|
              10 | 0384 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              40 | 0000 0000 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 0001 0000  0000 0400 FFEC 0708 |................|
              10 | 0384 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              40 | 0000 0000 0000 0000  0002 0006 0003 000C |................|
              50 | 0001 0006 0006 0004  0001 000B 000B 0004 |................|
              60 | 0014 0013 0001 FFFF  FFFF 0000           |............    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 0000 0002 0000  0020 0006 0002 0013 |......... ......|
              10 | 0004 000E FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              20 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              30 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              40 | FFFF FFFF FFFF FFFF  FFFF                |..........      |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0001 0000 0003 0000  0020 0006 0002 0013 |......... ......|
              10 | 0004 000E FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              20 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              30 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              40 | FFFF FFFF FFFF FFFF  FFFF 0002 0006 0003 |................|
              50 | 000C 0001 0006 0006  0004 0001 000B 000B |................|
              60 | 0004 0014 0013 0001  FFFF FFFF 0000      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)
        dCounts = collections.defaultdict(int)
        
        for value in self.values():
            dCounts[int(value)] += 1
        
        format = (0 if len(dCounts) == 1 else 1)
        
        if not self.positions.isDistance:
            format += 2
        
        w.add("H", format)
        v = sorted(dCounts.items(), key=operator.itemgetter(1))
        default = v[-1][0]
        w.add("H", default)
        self.positions.buildBinary(w, **kwArgs)
        
        if len(dCounts) > 1:
            lk = lookup.Lookup({g: n for g, n in self.items() if n != default})
            lk.buildBinary(w, noGaps=True, sentinelValue=0)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    d = dict.fromkeys(range(30), _premades[0])
    d2 = dict.fromkeys(range(30), _premades[0])
    d2[4] = d2[5] = d2[6] = d2[19] = d2[20] = _premades[1]
    d2[11] = _premades[4]
    
    _testingValues = (
        Bsln(d, positions=positions_distance._testingValues[0]),
        Bsln(d2, positions=positions_distance._testingValues[0]),
        Bsln(d, positions=positions_point._testingValues[0]),
        Bsln(d2, positions=positions_point._testingValues[0]))
    
    del d, d2

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
