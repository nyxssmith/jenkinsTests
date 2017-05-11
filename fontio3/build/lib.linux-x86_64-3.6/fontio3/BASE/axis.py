#
# axis.py
#
# Copyright © 2010-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for all orientation-specific baseline information from an OpenType
'BASE' table.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.BASE import basescript
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Axis(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing a single axis in a BASE table. These are dicts which
    map script tags to BaseScript objects. (Note this is something of a
    simplification from the OpenType-specified layout)
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
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
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda k: "Script '%s'" % (utilities.ensureUnicode(k),)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Axis object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0004 000E 0002 6162  6364 7778 797A 0001 |......abcdwxyz..|
              10 | 6C61 746E 0008 0012  001A 0002 656E 5553 |latn........enUS|
              20 | 002C 7370 616E 003E  0001 0002 007C 0076 |.,span.>.....|.v|
              30 | 000E 0006 0000 0002  0000 0019 0009 0001 |................|
              40 | FFEC 000E 0006 0000  0002 0000 0019 0009 |................|
              50 | 0001 FFEC 0016 002A  0002 6162 6364 0032 |.......*..abcd.2|
              60 | 001C 7778 797A 0000  0022 0003 FFF6 0020 |..wxyz..."..... |
              70 | 0003 000F 0026 0002  FFF6 000E 000C 0002 |.....&..........|
              80 | 0000 0019 0009 0001  0000 000C 0014 0002 |................|
              90 | BDF0 0020 3000 000C  0012 0001 8C04 0003 |... 0...........|
              A0 | FFF6 000A 0001 FFEC  000C 0014 0002 BDF0 |................|
              B0 | 0020 3000                                |. 0.            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Make the tagList by gathering all the keys from the BaseScripts
        s = set()
        
        for d in self.values():
            s.update(d)
        
        tagList = sorted(s)
        tlStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, tlStake)
        slStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, slStake)
        
        # Add the tag list
        w.stakeCurrentWithValue(tlStake)
        w.add("H", len(tagList))
        w.addGroup("4s", tagList)
        
        # Add the script list
        w.stakeCurrentWithValue(slStake)
        w.add("H", len(self))
        stakes = {}
        
        for tag in sorted(self):
            w.add("4s", tag)
            stakes[tag] = w.getNewStake()
            w.addUnresolvedOffset("H", slStake, stakes[tag])
        
        # Finally, add the actual BaseScripts
        d = kwArgs.copy()
        cp = d['coordinatePool'] = {}
        dp = d['devicePool'] = {}
        d['tagList'] = tagList
        
        for tag in sorted(self):
            self[tag].buildBinary(w, stakeValue=stakes[tag], **d)
        
        ig0 = operator.itemgetter(0)
        kwArgs.pop('devicePool', None)
        
        for immut, (obj, stake) in sorted(cp.items(), key=ig0):
            obj.buildBinary(w, stakeValue=stake, devicePool=dp, **kwArgs)
        
        for immut, (obj, stake) in sorted(dp.items(), key=ig0):
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Axis object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("axis_fvw")
        >>> fvb = Axis.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        axis_fvw.axis - DEBUG - Walker has 180 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript - DEBUG - Walker has 158 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        axis_fvw.axis.script 'latn'.basescript.tag 'abcd'.coordinate_simple - DEBUG - Walker has 16 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.tag 'wxyz'.coordinate - DEBUG - Coordinate format 3.
        axis_fvw.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device - DEBUG - Walker has 22 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Walker has 12 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        axis_fvw.axis.script 'latn'.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        axis_fvw.axis.script 'latn'.basescript.default minmax.minmax - DEBUG - Walker has 132 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.default minmax.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        axis_fvw.axis.script 'latn'.basescript.default minmax.minmax.minimum.coordinate_simple - DEBUG - Walker has 118 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.default minmax.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        axis_fvw.axis.script 'latn'.basescript.default minmax.minmax.maximum.coordinate_point - DEBUG - Walker has 126 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'enUS'.minmax - DEBUG - Walker has 114 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'enUS'.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        axis_fvw.axis.script 'latn'.basescript.langsys 'enUS'.minmax.minimum.coordinate_simple - DEBUG - Walker has 100 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'enUS'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        axis_fvw.axis.script 'latn'.basescript.langsys 'enUS'.minmax.maximum.coordinate_point - DEBUG - Walker has 108 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax - DEBUG - Walker has 96 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate - DEBUG - Coordinate format 3.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device - DEBUG - Walker has 74 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Walker has 42 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.maximum.coordinate_point - DEBUG - Walker has 54 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_simple - DEBUG - Walker has 46 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 3.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device - DEBUG - Walker has 68 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Walker has 30 remaining bytes.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - StartSize=12, endSize=18, format=1
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Data are (35844,)
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate - DEBUG - Coordinate format 2.
        axis_fvw.axis.script 'latn'.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate_point - DEBUG - Walker has 62 remaining bytes.
        >>> obj == _testingValues[1]
        True
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("axis")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        tagListOffset, scriptListOffset = w.unpack("2H")
        wSub = w.subWalker(tagListOffset)
        
        if wSub.length() < 2:
            logger.error((
              'V0647',
              (),
              "The tagList count is missing or incomplete."))
            
            return None
        
        tagListCount = wSub.unpack("H")
        
        if wSub.length() < 4 * tagListCount:
            logger.error((
              'V0648',
              (),
              "The tagList is missing or incomplete."))
            
            return None
        
        tagList = wSub.group("4s", tagListCount)
        
        if sorted(tagList) != list(tagList):
            logger.error((
              'V0649',
              (),
              "The tagList is not sorted."))
            
            return None
        
        wSub = w.subWalker(scriptListOffset)
        
        if wSub.length() < 2:
            logger.error((
              'V0650',
              (),
              "The ScriptList count is missing or incomplete."))
            
            return None
        
        scriptListCount = wSub.unpack("H")
        
        if wSub.length() < 6 * scriptListCount:
            logger.error((
              'V0651',
              (),
              "The ScriptList is missing or incomplete."))
            
            return None
        
        scriptsOffsets = wSub.group("4sH", scriptListCount)
        r = cls()
        fvw = basescript.BaseScript.fromvalidatedwalker
        
        for scriptTag, offset in scriptsOffsets:
            obj = fvw(
              wSub.subWalker(offset),
              tagList = tagList,
              logger = logger.getChild(
                "script '%s'" % (utilities.ensureUnicode(scriptTag),)))
            
            if obj is None:
                return None
            
            r[scriptTag] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns an Axis object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Axis.frombytes(obj.binaryString())
        True
        """
        
        tagListOffset, scriptListOffset = w.unpack("2H")
        wSub = w.subWalker(tagListOffset)
        tagList = wSub.group("4s", wSub.unpack("H"))
        wSub = w.subWalker(scriptListOffset)
        scriptsOffsets = wSub.group("4sH", wSub.unpack("H"))
        r = cls()
        fw = basescript.BaseScript.fromwalker
        
        for scriptTag, offset in scriptsOffsets:
            r[scriptTag] = fw(wSub.subWalker(offset), tagList=tagList)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _bv = basescript._testingValues
    
    _testingValues = (
        Axis(),
        Axis({b'latn': _bv[1]}))
    
    del _bv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
