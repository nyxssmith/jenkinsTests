#
# BASE.py
#
# Copyright © 2010-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType 'BASE' tables.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3.BASE import axis
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class BASE(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'BASE' tables. These are simple objects with
    two attributes:
    
        horizontal      An Axis object, or None.
        vertical        An Axis object, or None.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Horizontal axis:
      Script 'latn':
        Baseline 'abcd':
          Coordinate: -20
        Baseline 'wxyz':
          Coordinate: -10
          Device table:
            Tweak at 12 ppem: -5
            Tweak at 13 ppem: -3
            Tweak at 14 ppem: -1
            Tweak at 18 ppem: 2
            Tweak at 20 ppem: 3
        Default baseline tag: 'wxyz'
        Default MinMax data:
          Minimum coordinate:
            Coordinate: -20
          Maximum coordinate:
            Coordinate: 0
            Glyph: xyz26
            Point: 9
        LangSys-specific data:
          LangSys 'enUS':
            Minimum coordinate:
              Coordinate: -20
            Maximum coordinate:
              Coordinate: 0
              Glyph: xyz26
              Point: 9
          LangSys 'span':
            Minimum coordinate:
              Coordinate: -10
              Device table:
                Tweak at 12 ppem: -5
                Tweak at 13 ppem: -3
                Tweak at 14 ppem: -1
                Tweak at 18 ppem: 2
                Tweak at 20 ppem: 3
            Maximum coordinate:
              Coordinate: 0
              Glyph: xyz26
              Point: 9
            Feature-specific MinMax values:
              Feature 'abcd':
                Minimum coordinate:
                  Coordinate: 0
                Maximum coordinate:
                  Coordinate: 15
                  Device table:
                    Tweak at 12 ppem: -2
                    Tweak at 14 ppem: -1
                    Tweak at 18 ppem: 1
              Feature 'wxyz':
                Maximum coordinate:
                  Coordinate: -10
                  Glyph: xyz15
                  Point: 12
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        horizontal = dict(
            attr_followsprotocol = True,
            attr_label = "Horizontal axis",
            attr_representsy = True,  # horizontal baselines are y
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        vertical = dict(
            attr_followsprotocol = True,
            attr_label = "Vertical axis",
            attr_representsx = True,  # vertical baselines are x
            attr_showonlyiffunc = functools.partial(operator.is_not, None)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the BASE object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 0008 0000  0004 000E 0002 6162 |..............ab|
              10 | 6364 7778 797A 0001  6C61 746E 0008 0012 |cdwxyz..latn....|
              20 | 001A 0002 656E 5553  002C 7370 616E 003E |....enUS.,span.>|
              30 | 0001 0002 007C 0076  000E 0006 0000 0002 |.....|.v........|
              40 | 0000 0019 0009 0001  FFEC 000E 0006 0000 |................|
              50 | 0002 0000 0019 0009  0001 FFEC 0016 002A |...............*|
              60 | 0002 6162 6364 0032  001C 7778 797A 0000 |..abcd.2..wxyz..|
              70 | 0022 0003 FFF6 0020  0003 000F 0026 0002 |."..... .....&..|
              80 | FFF6 000E 000C 0002  0000 0019 0009 0001 |................|
              90 | 0000 000C 0014 0002  BDF0 0020 3000 000C |........... 0...|
              A0 | 0012 0001 8C04 0003  FFF6 000A 0001 FFEC |................|
              B0 | 000C 0014 0002 BDF0  0020 3000           |......... 0.    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)  # version
        
        if self.horizontal is not None:
            hStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, hStake)
        else:
            w.add("H", 0)
        
        if self.vertical is not None:
            vStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, vStake)
        else:
            w.add("H", 0)
        
        # Now add the actual data
        if self.horizontal is not None:
            self.horizontal.buildBinary(w, stakeValue=hStake, **kwArgs)
        
        if self.vertical is not None:
            self.vertical.buildBinary(w, stakeValue=vStake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new BASE object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("BASE_fvw")
        >>> fvb = BASE.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        BASE_fvw.BASE - DEBUG - Walker has 188 remaining bytes.
        BASE_fvw.BASE.horizontal.axis - DEBUG - Walker has 180 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript - DEBUG - Walker has 158 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'abcd'.coordinate_simple - DEBUG - Walker has 16 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'wxyz'.coordinate - DEBUG - Coordinate format 3.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device - DEBUG - Walker has 22 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Walker has 12 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.default minmax.minmax - DEBUG - Walker has 132 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.default minmax.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.default minmax.minmax.minimum.coordinate_simple - DEBUG - Walker has 118 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.default minmax.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.default minmax.minmax.maximum.coordinate_point - DEBUG - Walker has 126 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'enUS'.minmax - DEBUG - Walker has 114 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'enUS'.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'enUS'.minmax.minimum.coordinate_simple - DEBUG - Walker has 100 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'enUS'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'enUS'.minmax.maximum.coordinate_point - DEBUG - Walker has 108 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax - DEBUG - Walker has 96 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate - DEBUG - Coordinate format 3.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device - DEBUG - Walker has 74 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Walker has 42 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.maximum.coordinate_point - DEBUG - Walker has 54 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_simple - DEBUG - Walker has 46 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 3.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device - DEBUG - Walker has 68 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Walker has 30 remaining bytes.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - StartSize=12, endSize=18, format=1
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Data are (35844,)
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate - DEBUG - Coordinate format 2.
        BASE_fvw.BASE.horizontal.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate_point - DEBUG - Walker has 62 remaining bytes.
        >>> obj == _testingValues[1]
        True
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("BASE")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, hOffset, vOffset = w.unpack("L2H")
        
        if version != 0x00010000:
            logger.error((
              'E4320',
              (version,),
              "Was expecting version 0x00010000, but got 0x%08X."))
            
            return None
        
        r = cls()
        fvw = axis.Axis.fromvalidatedwalker
        
        if hOffset:
            obj = fvw(
              w.subWalker(hOffset),
              logger = logger.getChild("horizontal"),
              **kwArgs)
            
            if obj is None:
                return None
            
            r.horizontal = obj
        
        if vOffset:
            obj = fvw(
              w.subWalker(vOffset),
              logger = logger.getChild("vertical"),
              **kwArgs)
            
            if obj is None:
                return None
            
            r.vertical = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a BASE object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == BASE.frombytes(obj.binaryString())
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'BASE' version: 0x%08X" % (version,))
        
        hOffset, vOffset = w.unpack("2H")
        r = cls()
        
        if hOffset:
            r.horizontal = axis.Axis.fromwalker(w.subWalker(hOffset), **kwArgs)
        
        if vOffset:
            r.vertical = axis.Axis.fromwalker(w.subWalker(vOffset), **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _av = axis._testingValues
    
    _testingValues = (
        BASE(),
        BASE(horizontal=_av[1]))
    
    del _av

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
