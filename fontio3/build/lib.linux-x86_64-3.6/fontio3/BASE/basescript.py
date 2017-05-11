#
# basescript.py
#
# Copyright © 2010-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Script-specific baseline data from a 'BASE' table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.BASE import basescript_langsysdict, coordinate_simple, minmax
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if obj.defaultTag not in obj:
        EU = utilities.ensureUnicode
        
        logger.error((
          'V0646',
          ( EU(obj.defaultTag),
            ', '.join(''.join(["'", EU(s), "'"]) for s in sorted(obj))),
          "The default tag is '%s', which is not present in the currently "
          "defined keys [%s]."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BaseScript(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing all the baseline information for a single script. These
    are dicts whose keys are baseline tags (4-byte bytestrings) and whose
    values are Coordinate objects of one kind or another.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
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
    
    >>> obj = _testingValues[1].__deepcopy__()
    >>> obj.defaultTag = b'anne'
    >>> logger = utilities.makeDoctestLogger("basescript_test")
    >>> e = _fakeEditor()
    >>> obj.isValid(logger=logger, editor=e)
    basescript_test - ERROR - The default tag is 'anne', which is not present in the currently defined keys ['abcd', 'wxyz'].
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_deepconverterfunc = (
          lambda n, **k:
          coordinate_simple.Coordinate_simple(n)),
        
        item_followsprotocol = True,
        
        item_pprintlabelfunc = (
          lambda k:
          "Baseline '%s'" % (utilities.ensureUnicode(k),)),
        
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        defaultTag = dict(
            attr_label = "Default baseline tag",
            
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(
                "'%s'" % (utilities.ensureUnicode(x),),
                label = label,
                **k))),
        
        defaultMinMax = dict(
            attr_followsprotocol = True,
            attr_label = "Default MinMax data",
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        langSysDict = dict(
            attr_followsprotocol = True,
            attr_initfunc = basescript_langsysdict.LangSysDict,
            attr_label = "LangSys-specific data",
            attr_showonlyiftrue = True))
    
    attrSorted = ('defaultTag', 'defaultMinMax', 'langSysDict')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the BaseScript object to the specified
        LinkedWriter.
        
        >>> tl = (b'abcd', b'wxyz')
        >>> utilities.hexdump(_testingValues[1].binaryString(tagList=tl))
               0 | 0012 001A 0002 656E  5553 002C 7370 616E |......enUS.,span|
              10 | 003E 0001 0002 007C  0076 000E 0006 0000 |.>.....|.v......|
              20 | 0002 0000 0019 0009  0001 FFEC 000E 0006 |................|
              30 | 0000 0002 0000 0019  0009 0001 FFEC 0016 |................|
              40 | 002A 0002 6162 6364  0032 001C 7778 797A |.*..abcd.2..wxyz|
              50 | 0000 0022 0003 FFF6  0020 0003 000F 0026 |..."..... .....&|
              60 | 0002 FFF6 000E 000C  0002 0000 0019 0009 |................|
              70 | 0001 0000 000C 0014  0002 BDF0 0020 3000 |............. 0.|
              80 | 000C 0012 0001 8C04  0003 FFF6 000A 0001 |................|
              90 | FFEC 000C 0014 0002  BDF0 0020 3000      |........... 0.  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        doLocalCoords = 'coordinatePool' not in kwArgs
        coordPool = kwArgs.pop('coordinatePool', {})
        doLocalDevs = 'devicePool' not in kwArgs
        devPool = kwArgs.pop('devicePool', {})
        tagList = kwArgs['tagList']  # effectively an index-to-tag map
        
        if set(self) - set(tagList):
            raise ValueError("Tags in BaseScript not in base tag list!")
        
        bvStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, bvStake)
        
        if self.defaultMinMax is not None:
            dmmStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, dmmStake)
        else:
            w.add("H", 0)
        
        w.add("H", len(self.langSysDict))
        lsStakes = {}
        
        for key in sorted(self.langSysDict):
            obj = self.langSysDict[key]
            w.add("4s", key)
            lsStakes[key] = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, lsStakes[key])
        
        # Add the actual base values
        ig0 = operator.itemgetter(0)
        w.stakeCurrentWithValue(bvStake)
        w.add("2H", tagList.index(self.defaultTag), len(tagList))
        
        for tag in tagList:
            if tag in self and self[tag] is not None:
                
                # If the user did arithmetic on a simple coordinate, it will
                # have been demoted to a simple int. We need to cope with that.
                
                obj = self[tag]
                
                try:
                    obj.asImmutable
                
                except AttributeError:
                    obj = coordinate_simple.Coordinate_simple(obj)
                
                immut = obj.asImmutable(**kwArgs)
                
                if immut not in coordPool:
                    coordPool[immut] = (obj, w.getNewStake())
                
                w.addUnresolvedOffset("H", bvStake, coordPool[immut][1])
            
            else:
                w.add("H", 0)
        
        # Add the default minmax, if present
        if self.defaultMinMax is not None:
            self.defaultMinMax.buildBinary(w, stakeValue=dmmStake, **kwArgs)
        
        # Add the langsys objects, if present
        for key in sorted(self.langSysDict):
            self.langSysDict[key].buildBinary(
              w,
              stakeValue = lsStakes[key],
              **kwArgs)
        
        if doLocalCoords:
            for immut, (obj, stake) in sorted(coordPool.items(), key=ig0):
                obj.buildBinary(
                  w,
                  stakeValue = stake,
                  devicePool = devPool,
                  **kwArgs)
        
        if doLocalDevs:
            for immut, (obj, stake) in sorted(devPool.items(), key=ig0):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a BaseScript object from the specified walker.
        The following keyword arguments are used:
        
            logger      A logger to which messages will be posted.
        
            tagList     A sequence of bytestrings representing tags. This is
                        required.
        
        >>> TL = (b'abcd', b'wxyz')
        >>> s = _testingValues[1].binaryString(tagList=TL)
        >>> logger = utilities.makeDoctestLogger("basescript_fvw")
        >>> fvb = BaseScript.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, tagList=TL)
        basescript_fvw.basescript - DEBUG - Walker has 158 remaining bytes.
        basescript_fvw.basescript.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        basescript_fvw.basescript.tag 'abcd'.coordinate_simple - DEBUG - Walker has 16 remaining bytes.
        basescript_fvw.basescript.tag 'wxyz'.coordinate - DEBUG - Coordinate format 3.
        basescript_fvw.basescript.tag 'wxyz'.coordinate_device - DEBUG - Walker has 22 remaining bytes.
        basescript_fvw.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Walker has 12 remaining bytes.
        basescript_fvw.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        basescript_fvw.basescript.tag 'wxyz'.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        basescript_fvw.basescript.default minmax.minmax - DEBUG - Walker has 132 remaining bytes.
        basescript_fvw.basescript.default minmax.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        basescript_fvw.basescript.default minmax.minmax.minimum.coordinate_simple - DEBUG - Walker has 118 remaining bytes.
        basescript_fvw.basescript.default minmax.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        basescript_fvw.basescript.default minmax.minmax.maximum.coordinate_point - DEBUG - Walker has 126 remaining bytes.
        basescript_fvw.basescript.langsys 'enUS'.minmax - DEBUG - Walker has 114 remaining bytes.
        basescript_fvw.basescript.langsys 'enUS'.minmax.minimum.coordinate - DEBUG - Coordinate format 1.
        basescript_fvw.basescript.langsys 'enUS'.minmax.minimum.coordinate_simple - DEBUG - Walker has 100 remaining bytes.
        basescript_fvw.basescript.langsys 'enUS'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        basescript_fvw.basescript.langsys 'enUS'.minmax.maximum.coordinate_point - DEBUG - Walker has 108 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax - DEBUG - Walker has 96 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.minimum.coordinate - DEBUG - Coordinate format 3.
        basescript_fvw.basescript.langsys 'span'.minmax.minimum.coordinate_device - DEBUG - Walker has 74 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Walker has 42 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        basescript_fvw.basescript.langsys 'span'.minmax.minimum.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        basescript_fvw.basescript.langsys 'span'.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        basescript_fvw.basescript.langsys 'span'.minmax.maximum.coordinate_point - DEBUG - Walker has 54 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_simple - DEBUG - Walker has 46 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 3.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device - DEBUG - Walker has 68 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Walker has 30 remaining bytes.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - StartSize=12, endSize=18, format=1
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Data are (35844,)
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate - DEBUG - Coordinate format 2.
        basescript_fvw.basescript.langsys 'span'.minmax.tag 'wxyz'.coordinate_point - DEBUG - Walker has 62 remaining bytes.
        >>> obj == _testingValues[1]
        True
        """
        
        tagList = kwArgs['tagList']
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("basescript")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        r = cls()
        valuesOffset, defaultMMOffset, lsCount = w.unpack("3H")
        wSub = w.subWalker(valuesOffset)
        
        if wSub.length() < 2:
            logger.error((
              'V0641',
              (),
              "The default tag index is missing or incomplete."))
            
            return None
        
        r.defaultTag = tagList[wSub.unpack("H")]
        
        if wSub.length() < 2:
            logger.error((
              'V0642',
              (),
              "The count is missing or incomplete."))
            
            return None
        
        count = wSub.unpack("H")
        
        if count and (count != len(tagList)):
            logger.error((
              'V0643',
              (count, len(tagList)),
              "The BaseValues count is %d, but the length of the BaseTagList "
              "is %d"))
            
            return None
        
        if wSub.length() < 2 * count:
            logger.error((
              'V0644',
              (),
              "The BaseValues list is missing or incomplete."))
            
            return None
        
        fvw = coordinate.Coordinate_validated
        offsets = wSub.group("H", count)
        
        for tag, offset in zip(tagList, offsets):
            itemLogger = logger.getChild(
              "tag '%s'" % (utilities.ensureUnicode(tag),))
            
            obj = fvw(wSub.subWalker(offset), logger=itemLogger, **kwArgs)
            
            if obj is None:
                return None
            
            r[tag] = obj
        
        fvw = minmax.MinMax.fromvalidatedwalker
        
        if defaultMMOffset:
            obj = fvw(
              w.subWalker(defaultMMOffset),
              logger = logger.getChild("default minmax"),
              **kwArgs)
            
            if obj is None:
                return None
            
            r.defaultMinMax = obj
        
        if w.length() < 6 * lsCount:
            logger.error((
              'V0645',
              (),
              "The LangSys list of MinMax values is missing or incomplete."))
            
            return None
        
        for tag, offset in w.group("4sH", lsCount):
            obj = fvw(
              w.subWalker(offset),
              logger = logger.getChild(
                "langsys '%s'" % (utilities.ensureUnicode(tag),)),
              **kwArgs)
            
            if obj is None:
                return None
            
            r.langSysDict[tag] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a BaseScript object from the specified walker.
        The following keyword arguments are used:
        
            tagList     A sequence of bytestrings representing tags. This is
                        required.
        
        >>> obj = _testingValues[1]
        >>> tl = (b'abcd', b'wxyz')
        >>> obj == BaseScript.frombytes(
        ...   obj.binaryString(tagList=tl),
        ...   tagList=tl)
        True
        """
        
        r = cls()
        tagList = kwArgs['tagList']
        valuesOffset, defaultMMOffset, lsCount = w.unpack("3H")
        wSub = w.subWalker(valuesOffset)
        r.defaultTag = tagList[wSub.unpack("H")]
        count = wSub.unpack("H")
        
        if count > 0 and count != len(tagList):
            raise ValueError("BaseValues count does not match BaseTagList!")
        
        fw = coordinate.Coordinate
        
        for tag in tagList:
            r[tag] = fw(wSub.subWalker(wSub.unpack("H")), **kwArgs)
        
        fw = minmax.MinMax.fromwalker
        
        if defaultMMOffset:
            r.defaultMinMax = fw(w.subWalker(defaultMMOffset), **kwArgs)
        
        for tag, offset in w.group("4sH", lsCount):
            r.langSysDict[tag] = fw(w.subWalker(offset), **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.BASE import coordinate
    from fontio3.utilities import namer
    
    def _fakeEditor():
        from fontio3.head import head
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(200)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        e.head = head.Head()
        return e
    
    _cv = coordinate._testingValues
    _mmv = minmax._testingValues
    _lsdv = basescript_langsysdict._testingValues
    
    _testingValues = (
        BaseScript(),
        
        BaseScript(
          {b'abcd': _cv[2], b'wxyz': _cv[6]},
          defaultTag = b'wxyz',
          defaultMinMax = _mmv[1],
          langSysDict = _lsdv[1]))
    
    del _mmv, _cv, _lsdv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
