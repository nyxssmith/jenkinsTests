#
# GPOS_v11.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for OpenType v1.8 'GPOS' table
(table version 1.1).
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import simplemeta

from fontio3.GPOS.GPOS_v10 import GPOS as GPOS_v10

from fontio3.opentype import (
  featuredict,
  featurevariations,
  lookuplist,
  scriptdict)

from fontio3.opentype import version as otversion
from fontio3.opentype import living_variations

# -----------------------------------------------------------------------------

#
# Classes
#

class GPOS(GPOS_v10, metaclass=simplemeta.FontDataMetaclass):
    """
    Top-level GPOS objects. These are simple objects with four attributes:
    
        version             A Version object.
        features            A FeatureDict object.
        scripts             A ScriptDict object.
        featureVariations   A FeatureVariations object.
    
    >>> _testingValues[0].pprint()
    Version:
      Major version: 1
      Minor version: 1
    Features:
    Scripts:
    Feature Variations:
    
    >>> bool(_testingValues[0].features and _testingValues[0].scripts)
    False
    
    >>> _testingValues[1].pprint()
    Version:
      Major version: 1
      Minor version: 1
    Features:
      Feature 'abcd0001':
        Lookup 0:
          Subtable 0 (Pair (glyph) positioning table):
            Key((8, 15)):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            Key((8, 20)):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
            Key((10, 20)):
              First adjustment:
                FUnit adjustment to origin's x-coordinate: 30
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
              Second adjustment:
                Device for origin's x-coordinate:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
                Device for origin's y-coordinate:
                  Tweak at 12 ppem: -5
                  Tweak at 13 ppem: -3
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 2
                  Tweak at 20 ppem: 3
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: True
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 1
      Feature 'size0002':
        Feature parameters object:
          Design size in decipoints: 80
          Subfamily value: 4
          Name table index of common subfamily: 300
          Small end of usage range in decipoints: 80
          Large end of usage range in decipoints: 120
      Feature 'wxyz0003':
        Lookup 0:
          Subtable 0 (Single positioning table):
            10:
              FUnit adjustment to origin's x-coordinate: -10
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 3
    Scripts:
      Script object latn:
        LangSys object enGB:
          Required feature tag: wxyz0003
        LangSys object enUS:
          Optional feature tags:
            abcd0001
            size0002
        Default LangSys object:
          Required feature tag: wxyz0003
          Optional feature tags:
            abcd0001
            size0002
    Feature Variations: (no data)
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: otversion.Version(minor=1),
            attr_label = "Version"),
            
        featureVariations = dict(
            attr_followsprotocol = True,
            attr_initfunc = featurevariations.FeatureVariations,
            attr_label = "Feature Variations"))
    
    attrSorted = ('version', 'features', 'scripts', 'featureVariations')

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GPOS object to the specified LinkedWriter.
        (Note that this class has an explicit binaryString() method as well).
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0001 000E 0040  006E 0000 0000 0001 |.......@.n......|
              10 | 6C61 746E 0008 0010  0002 656E 4742 001A |latn......enGB..|
              20 | 656E 5553 0020 0000  0002 0002 0000 0001 |enUS. ..........|
              30 | 0000 0002 0000 0000  FFFF 0002 0000 0001 |................|
              40 | 0003 6162 6364 0014  7369 7A65 001A 7778 |..abcd..size..wx|
              50 | 797A 0028 0000 0001  0000 0004 0000 0050 |yz.(...........P|
              60 | 0004 012C 0050 0078  0000 0001 0001 0002 |...,.P.x........|
              70 | 0006 0016 0009 0002  0001 0008 0001 0002 |................|
              80 | 0000 0018 0009 0000  0001 0008 0001 0001 |................|
              90 | 0000 005A 0001 000E  0081 0031 0002 0016 |...Z.......1....|
              A0 | 0030 0001 0002 0008  000A 0002 000F 0000 |.0..............|
              B0 | 0000 FFF6 0000 0000  0014 0000 0034 0000 |.............4..|
              C0 | 0000 0000 0001 0014  001E 001A 0000 001A |................|
              D0 | 000E 000C 0014 0002  BDF0 0020 3000 000C |........... 0...|
              E0 | 0012 0001 8C04 0001  0008 0001 FFF6 0001 |................|
              F0 | 0001 000A                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        editor = kwArgs.get('editor')
        if editor is not None:
            if editor.reallyHas(b'fvar'):
                ao = editor.fvar.axisOrder
                kwArgs['axisOrder'] = ao
            else:
                ao = None

            if editor.reallyHas(b'GDEF'):
                kwArgs['GDEF'] = editor.GDEF
                gdce = getattr(editor.GDEF, '_creationExtras', {})
                otcd = gdce.get('otcommondeltas')
                if otcd:
                    bsfd = living_variations.IVS.binaryStringFromDeltas
                    otIVS = bsfd(otcd, axisOrder=ao)
                    kwArgs['otIVS'] = otIVS
        
        # We only bother adding content if the feature dict is not empty,
        # or it is explicitly forced via the forceForEmpty keyword.
        ffe = kwArgs.get('forceForEmpty', False)
        
        if self.features or ffe:
            if not ffe:
                self.scripts.trimToValidFeatures(set(self.features))
            
            ll = lookuplist.LookupList.fromtoplevel(self.features)
            
            if self.featureVariations:
                llIDset = set(id(obj) for obj in ll)
                llv = lookuplist.LookupList.fromtoplevel(self.featureVariations)
                for lkp in llv:
                    if id(lkp) not in llIDset:
                        ll.append(lkp)
                        llIDset.add(id(lkp))
                ll._sort()
            
            w.addIndexMap(
              "lookupList_GPOS",
              dict((obj.asImmutable(), i) for i, obj in enumerate(ll)))
            
            ttfi = dict(zip(sorted(self.features), itertools.count()))
            w.add("L", 0x10001)  # Version (1.1)
            stakes = [w.getNewStake(), w.getNewStake(), w.getNewStake()]
            
            for stake in stakes:
                w.addUnresolvedOffset("H", stakeValue, stake)

            if self.featureVariations:
                fvstake = w.getNewStake()
                w.addUnresolvedOffset("L", stakeValue, fvstake)
            else:
                w.add("L", 0)  # offset to FeatureVariationsTable
            
            self.scripts.buildBinary(
              w,
              stakeValue = stakes[0],
              tagToFeatureIndex = ttfi)
            
            self.features.buildBinary(w, stakeValue=stakes[1], lookupList=ll)
            extPool = {}
            kwArgs.pop('extensionPool', None)
            kwArgs['memo'] = {}
            
            ll.buildBinary(
              w,
              stakeValue = stakes[2],
              extensionPool = extPool,
              **kwArgs)

            if self.featureVariations:
                self.featureVariations.buildBinary(
                  w,
                  lookupList=ll,
                  stakeValue=fvstake,
                  tagToFeatureIndex=ttfi,
                  **kwArgs)
            
            for i, obj, stake in sorted(extPool.values()):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GPOS object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = GPOS.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("GPOS_test")
        >>> obj = fvb(s, logger=logger)
        GPOS_test.GPOS - DEBUG - Walker has 244 remaining bytes.
        GPOS_test.GPOS.version - DEBUG - Walker has 244 remaining bytes.
        GPOS_test.GPOS.lookuplist - DEBUG - Walker has 134 bytes remaining.
        GPOS_test.GPOS.lookuplist - DEBUG - Offset count is 2
        GPOS_test.GPOS.lookuplist - DEBUG - Offset 0 is 6
        GPOS_test.GPOS.lookuplist.lookup 0.lookup - DEBUG - Walker has 128 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup - DEBUG - Kind is 9
        GPOS_test.GPOS.lookuplist.lookup 0.lookup - DEBUG - Number of subtables is 1
        GPOS_test.GPOS.lookuplist.lookup 0.lookup - DEBUG - Subtable offset 0 is 8
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair - DEBUG - Walker has 96 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs - DEBUG - Walker has 96 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.coverage - DEBUG - Walker has 82 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.coverage - DEBUG - Format is 1, count is 2
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.coverage - DEBUG - Raw data are [8, 10]
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 15.pairvalues - DEBUG - Walker has 70 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 70 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 15.pairvalues.value - DEBUG - Walker has 66 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 58 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 58 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 22 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 54 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues - DEBUG - Walker has 44 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 44 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Walker has 22 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yAdvDevice.device - DEBUG - Data are (35844,)
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value - DEBUG - Walker has 40 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Walker has 22 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.xPlaDevice.device - DEBUG - Data are (35844,)
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Walker has 34 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
        GPOS_test.GPOS.lookuplist.lookup 0.lookup.subtable 0.pair.pairglyphs.second glyph 20.pairvalues.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
        GPOS_test.GPOS.lookuplist - DEBUG - Offset 1 is 22
        GPOS_test.GPOS.lookuplist.lookup 1.lookup - DEBUG - Walker has 112 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 1.lookup - DEBUG - Kind is 9
        GPOS_test.GPOS.lookuplist.lookup 1.lookup - DEBUG - Number of subtables is 1
        GPOS_test.GPOS.lookuplist.lookup 1.lookup - DEBUG - Subtable offset 0 is 8
        GPOS_test.GPOS.lookuplist.lookup 1.lookup.subtable 0.single - DEBUG - Walker has 14 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 1.lookup.subtable 0.single.coverage - DEBUG - Walker has 6 remaining bytes.
        GPOS_test.GPOS.lookuplist.lookup 1.lookup.subtable 0.single.coverage - DEBUG - Format is 1, count is 1
        GPOS_test.GPOS.lookuplist.lookup 1.lookup.subtable 0.single.coverage - DEBUG - Raw data are [10]
        GPOS_test.GPOS.lookuplist.lookup 1.lookup.subtable 0.single.value - DEBUG - Walker has 8 remaining bytes.
        GPOS_test.GPOS.featuredict - DEBUG - Walker has 180 remaining bytes.
        GPOS_test.GPOS.featuredict - DEBUG - Count is 3
        GPOS_test.GPOS.featuredict - DEBUG - Feature 0: tag is 'abcd', offset is 20
        GPOS_test.GPOS.featuredict.feature table 0.featuretable - DEBUG - Walker has 160 remaining bytes.
        GPOS_test.GPOS.featuredict.feature table 0.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 1
        GPOS_test.GPOS.featuredict.feature table 0.featuretable - DEBUG - Entry 0 is Lookup 0
        GPOS_test.GPOS.featuredict - DEBUG - Feature 1: tag is 'size', offset is 26
        GPOS_test.GPOS.featuredict.feature table 1.featuretable - DEBUG - Walker has 154 remaining bytes.
        GPOS_test.GPOS.featuredict.feature table 1.featuretable - DEBUG - FeatureParams offset is 4, lookupCount is 0
        GPOS_test.GPOS.featuredict.feature table 1.featuretable.featureparams_GPOS_size - DEBUG - Walker has 150 remaining bytes.
        GPOS_test.GPOS.featuredict.feature table 1.featuretable.featureparams_GPOS_size - DEBUG - Data are (80, 4, 300, 80, 120)
        GPOS_test.GPOS.featuredict - DEBUG - Feature 2: tag is 'wxyz', offset is 40
        GPOS_test.GPOS.featuredict.feature table 2.featuretable - DEBUG - Walker has 140 remaining bytes.
        GPOS_test.GPOS.featuredict.feature table 2.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 1
        GPOS_test.GPOS.featuredict.feature table 2.featuretable - DEBUG - Entry 0 is Lookup 1
        GPOS_test.GPOS.scriptdict - DEBUG - Walker has 230 remaining bytes.
        GPOS_test.GPOS.scriptdict - DEBUG - Group count is 1
        GPOS_test.GPOS.scriptdict - DEBUG - Script rec for tag 'latn' at offset 8
        GPOS_test.GPOS.scriptdict.script latn.langsysdict - DEBUG - Walker has 222 remaining bytes.
        GPOS_test.GPOS.scriptdict.script latn.langsysdict - DEBUG - Default offset is 16; langSys count is 2
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.default.langsys - DEBUG - Walker has 206 bytes remaining.
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.default.langsys - DEBUG - Lookup order is 0, Required index is 2, feature count is 2
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.default.langsys - DEBUG - Optional feature 0 is 0
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.default.langsys - DEBUG - Optional feature 1 is 1
        GPOS_test.GPOS.scriptdict.script latn.langsysdict - DEBUG - LangSys tag 'enGB' has offset 26
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enGB.langsys - DEBUG - Walker has 196 bytes remaining.
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enGB.langsys - DEBUG - Lookup order is 0, Required index is 2, feature count is 0
        GPOS_test.GPOS.scriptdict.script latn.langsysdict - DEBUG - LangSys tag 'enUS' has offset 32
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enUS.langsys - DEBUG - Walker has 190 bytes remaining.
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enUS.langsys - DEBUG - Lookup order is 0, Required index is 65535, feature count is 2
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enUS.langsys - DEBUG - Optional feature 0 is 0
        GPOS_test.GPOS.scriptdict.script latn.langsysdict.tag enUS.langsys - DEBUG - Optional feature 1 is 1
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("GPOS")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = otversion.Version.fromvalidatedwalker(w, logger=logger, **kwArgs)
        slOffset, flOffset, llOffset, fvtOffset = w.unpack("3HL")
        
        if version.major != 1 or version.minor != 1:
            logger.error((
              'V0454',
              (version,),
              "Expected version 1.1, but got %s."))
            
            return None
        
        if not slOffset:
            logger.warning((
              'V0455',
              (),
              "The ScriptList offset is zero; no further GPOS "
              "validation will be performed."))
        
        if not flOffset:
            logger.warning((
              'V0456',
              (),
              "The FeatureList offset is zero; no further GPOS "
              "validation will be performed."))
        
        if not llOffset:
            logger.warning((
              'V0457',
              (),
              "The LookupList offset is zero; no further GPOS "
              "validation will be performed."))
        
        if not all([slOffset, flOffset, llOffset]):
            return cls()  # note: okay to have null offset to FV table
        
        delKeys = {'featureIndexToTag', 'forGPOS', 'lookupList'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        fitt = []
        
        ll = lookuplist.LookupList.fromvalidatedwalker(
          w.subWalker(llOffset),
          forGPOS = True,
          logger = logger,
          **kwArgs)
        
        if ll is None:
            return None
        
        fd = featuredict.FeatureDict.fromvalidatedwalker(
          w.subWalker(flOffset),
          featureIndexToTag = fitt,
          forGPOS = True,
          lookupList = ll,
          logger = logger,
          **kwArgs)
        
        if fd is None:
            return None
        
        sd = scriptdict.ScriptDict.fromvalidatedwalker(
          w.subWalker(slOffset),
          featureIndexToTag = fitt,
          logger = logger,
          **kwArgs)
        
        if sd is None:
            return None
        
        if fvtOffset:
            fvt = featurevariations.FeatureVariationsTable.fromvalidatedwalker(
              w.subWalker(fvtOffset),
              logger=logger,
              lookupList=ll,
              **kwArgs)
        else:
            fvt = None
        
        r = cls(version=version, features=fd, scripts=sd, featureVariations=fvt)
        r._cachedOriginalLookupList = ll.__copy__()
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GPOS object from the specified walker.
        
        >>> obj = _testingValues[1]

        <<< obj == GPOS.frombytes(obj.binaryString())
        >>> obj.pprint_changes(GPOS.frombytes(obj.binaryString()))
        """
        
        version = otversion.Version.fromwalker(w, **kwArgs)
        slOffset, flOffset, llOffset, fvtOffset = w.unpack("3HL")
        fitt = []
        
        if not all([slOffset, flOffset, llOffset]):
            return cls()  # note: okay to have null offset to FV table
        
        delKeys = {'featureIndexToTag', 'forGPOS', 'lookupList'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        ll = lookuplist.LookupList.fromwalker(
          w.subWalker(llOffset),
          forGPOS=True,
          **kwArgs)
        
        fd = featuredict.FeatureDict.fromwalker(
          w.subWalker(flOffset),
          featureIndexToTag=fitt,
          forGPOS=True,
          lookupList=ll,
          **kwArgs)
        
        sd = scriptdict.ScriptDict.fromwalker(
          w.subWalker(slOffset),
          featureIndexToTag=fitt,
          **kwArgs)
        
        if fvtOffset:
            fvt = featurevariationstable.FeatureVariationsTable.fromwalker(
              w.subWalker(fvtOffset),
              lookupList=ll,
              **kwArgs)
        else:
            fvt = None
        
        r = cls(version=version, features=fd, scripts=sd, featureVariations=fvt)
        r._cachedOriginalLookupList = ll.__copy__()
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
    from io import StringIO
    
    fdtv = featuredict._testingValues
    sdtv = scriptdict._testingValues
    
    _testingValues = (
        GPOS(),
        GPOS(features=fdtv[2], scripts=sdtv[1], featureVariations=None))
    
    del fdtv, sdtv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
