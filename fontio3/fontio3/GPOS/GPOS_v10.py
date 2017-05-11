#
# GPOS_v10.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the pre-OpenType 1.8 'GPOS'
table (table version 1.0).
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import simplemeta

from fontio3.opentype import (
  featuredict,
  fontworkersource,
  lookuplist,
  scriptdict)

from fontio3.opentype import living_variations
from fontio3.opentype import version as otversion

# -----------------------------------------------------------------------------

#
# Classes
#

class GPOS(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Top-level GPOS objects. These are simple objects with three attributes:
    
        version     A Version object.
        features    A FeatureDict object.
        scripts     A ScriptDict object.
    
    >>> _testingValues[0].pprint()
    Version:
      Major version: 1
      Minor version: 0
    Features:
    Scripts:
    
    >>> bool(_testingValues[0].features and _testingValues[0].scripts)
    False
    
    >>> _testingValues[1].pprint()
    Version:
      Major version: 1
      Minor version: 0
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
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = otversion.Version,
            attr_label = "Version"),
            
        features = dict(
            attr_followsprotocol = True,
            attr_initfunc = featuredict.FeatureDict,
            attr_label = "Features"),
        
        scripts = dict(
            attr_followsprotocol = True,
            attr_initfunc = scriptdict.ScriptDict,
            attr_label = "Scripts"))
    
    attrSorted = ('version', 'features', 'scripts')

    #
    # Methods
    #
    
    def _allKerningEffects_gather(self, **kwArgs):
        from fontio3.GPOS import pairglyphs
        from fontio3.kern import format0
        
        e = kwArgs.pop('editor', None)
        sources = kwArgs.pop('sources', set())
        fpc = pairglyphs.PairGlyphs.frompairclasses
        fgp = format0.Format0.fromgpospairs
        featIndex = self.scripts.featureIndex()
        r = {}
        gTypeString = "Pair (glyph) positioning table"
        cTypeString = "Pair (class) positioning table"
    
        for slsCode, (reqFeats, optFeats) in featIndex.items():
            d = {}
        
            for featTag in itertools.chain(iter(reqFeats), iter(optFeats)):
                featTable = self.features[featTag]
            
                for lkIndex, lkObj in enumerate(featTable):
                    lkSeen = set()
                    
                    for subIndex, subObj in enumerate(lkObj):
                        if subObj.kindString == cTypeString:
                            gbTable = fpc(
                              self.features[featTag][lkIndex][subIndex],
                              useSpecialClass0 = False,
                              fullExpansion = True,
                              editor = e)
                        
                            f0Table = fgp(gbTable)
                    
                        elif subObj.kindString == gTypeString:
                            f0Table = fgp(subObj, keepZeroes=True)
                    
                        else:
                            continue
                    
                        sources.add((slsCode, featTag, lkIndex))
                        
                        for pair, dist in f0Table.items():
                            if pair not in d:
                                lkSeen.add(pair)
                                d[pair] = dist
                            
                            elif pair not in lkSeen:
                                lkSeen.add(pair)
                                d[pair] += dist
            
            d = {
              (int(pair[0]), int(pair[1])): int(dist)
              for pair, dist in d.items()
              if dist}
            
            r[slsCode] = d
        
        return r
    
    @staticmethod
    def _allKerningEffects_reconcile(f0Pile, **kwArgs):
        allPairs = {pair for f0Table in f0Pile.values() for pair in f0Table}
        bads = set()
        
        for pair in allPairs:
            distSet = {
              f0Table[pair]
              for f0Table in f0Pile.values()
              if pair in f0Table}
            
            if len(distSet) > 1:
                bads.add(pair)
        
        for pair in sorted(bads):
            #print("    Inconsistent kerning for", pair)
            
            target = min(
              abs(f0Pile[slsCode][pair])
              for slsCode in sorted(f0Pile)
              if pair in f0Pile[slsCode])
            
            for slsCode in sorted(f0Pile):
                f0Table = f0Pile[slsCode]
                
                if pair not in f0Table:
                    continue
                
                if abs(f0Table[pair]) > target:
#                     print(
#                       "        Script",
#                       slsCode,
#                       "kerns by",
#                       f0Table[pair],
#                       "<<<=== WILL BE REMOVED")
                    
                    del f0Table[pair]
                
#                 else:
#                     print(
#                       "        Script",
#                       slsCode,
#                       "kerns by",
#                       f0Table[pair])
    
    def allKerningEffects(self, **kwArgs):
        """
        Returns a simple dict mapping simple pairs of integral glyph indices to
        simple FUnit shifts, for all kerning-like subtables in self.
        
        One required keyword argument: 'editor'
        """
        
        d = self._allKerningEffects_gather(**kwArgs)
        self._allKerningEffects_reconcile(d, **kwArgs)
        r = {}
        
        for f0Table in d.values():
            for pair, dist in f0Table.items():
                r[pair] = dist
        
        return r
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GPOS object to the specified LinkedWriter.
        (Note that this class has an explicit binaryString() method as well).
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 000A 003C  006A 0001 6C61 746E |.......<.j..latn|
              10 | 0008 0010 0002 656E  4742 001A 656E 5553 |......enGB..enUS|
              20 | 0020 0000 0002 0002  0000 0001 0000 0002 |. ..............|
              30 | 0000 0000 FFFF 0002  0000 0001 0003 6162 |..............ab|
              40 | 6364 0014 7369 7A65  001A 7778 797A 0028 |cd..size..wxyz.(|
              50 | 0000 0001 0000 0004  0000 0050 0004 012C |...........P...,|
              60 | 0050 0078 0000 0001  0001 0002 0006 0016 |.P.x............|
              70 | 0009 0002 0001 0008  0001 0002 0000 0018 |................|
              80 | 0009 0000 0001 0008  0001 0001 0000 005A |...............Z|
              90 | 0001 000E 0081 0031  0002 0016 0030 0001 |.......1.....0..|
              A0 | 0002 0008 000A 0002  000F 0000 0000 FFF6 |................|
              B0 | 0000 0000 0014 0000  0034 0000 0000 0000 |.........4......|
              C0 | 0001 0014 001E 001A  0000 001A 000E 000C |................|
              D0 | 0014 0002 BDF0 0020  3000 000C 0012 0001 |....... 0.......|
              E0 | 8C04 0001 0008 0001  FFF6 0001 0001 000A |................|
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
            
            w.addIndexMap(
              "lookupList_GPOS",
              dict((obj.asImmutable(), i) for i, obj in enumerate(ll)))
            
            ttfi = dict(zip(sorted(self.features), itertools.count()))
            w.add("L", 0x10000)
            stakes = [w.getNewStake(), w.getNewStake(), w.getNewStake()]
            
            for stake in stakes:
                w.addUnresolvedOffset("H", stakeValue, stake)
            
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
            
            for i, obj, stake in sorted(extPool.values()):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    def compacted(self, **kwArgs):
        """
        Custom code to compact the GPOS.
        """
        
        fNew = self.features.compacted(**kwArgs)
        
        if not fNew:
            return None
        
        sNew = self.scripts.__deepcopy__()
        sNew.trimToValidFeatures(set(fNew))
        return GPOS(features=fNew, scripts=sNew)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new GPOS object from the specified
        FontWorkerSource object, with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = GPOS.fromValidatedFontWorkerSource(_test_FW_s2, namer=_test_FW_namer, logger=logger, editor={})
        FW_test.GPOS.featuredict.lookup.single - ERROR - line 8 -- incorrect number of tokens, expected 3, found 1
        FW_test.GPOS.featuredict - WARNING - line 14 -- incorrect number of tokens, expected 3, found 1
        FW_test.GPOS.scriptdict - ERROR - line 19 -- incorrect number of tokens, expected 4, found 1
        >>> obj.pprint()
        Version:
          Major version: 1
          Minor version: 0
        Features:
          Feature 'kern0001':
            Lookup 0:
              Subtable 0 (Single positioning table):
                1:
                  FUnit adjustment to origin's x-coordinate: -123
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Lookup name: testSingle
              Sequence order (lower happens first): 0
        Scripts:
          Script object thai:
            Default LangSys object:
              Optional feature tags:
                kern0001
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("GPOS")
        parseinfo = kwArgs.get('parseinfo', {})
        firstLine = 'FontDame GPOS table'
        lookupDict = {}
        kwArgs['lookupDict'] = lookupDict
        line = next(fws)
        
        if line != firstLine:
            logger.error((
              'Vxxxx',
              (firstLine,),
              "Expected '%s' in first line."))
            
            return None

        lookupLineNumbers = dict()
        lookupSequenceOrder = dict()
        sequenceOrder = 0
        lookupNamesParsed = set()

        for line in fws:
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0] == 'EM':
                    #EM = int(tokens[1])
                    continue
                
                elif tokens[0].lower().startswith('script table begin'):
                    scriptTableLineNumber = fws.lineNumber
                
                elif tokens[0].lower().startswith('feature table begin'):
                    featureTableLineNumber = fws.lineNumber
                
                elif tokens[0].lower().startswith('lookup end'):
                    lookupNamesParsed.add(lookupName)
                    continue
                
                elif tokens[0].lower().startswith('lookup'):
                    lookupName = tokens[1]
                    
                    if lookupName in lookupLineNumbers:
                        logger.warning((
                          'Vxxxx',
                          (fws.lineNumber, lookupName, lookupLineNumbers[lookupName][0]),
                          "line %d -- lookup '%s' previously defined at line %d"))
                    
                    lookupLineNumbers[lookupName] = [fws.lineNumber]
                    lookupSequenceOrder[lookupName] = sequenceOrder
                    sequenceOrder += 1
                
                elif tokens[0].lower().startswith('subtable end'):
                    lookupLineNumbers[lookupName].append(fws.lineNumber)

        parseinfo['lookupNames'] = lookupNamesParsed
        featureIndexToTag = {} # Note that this is a list in the binary version
        kwArgs['lookupLineNumbers'] = lookupLineNumbers
        kwArgs['lookupSequenceOrder'] = lookupSequenceOrder
        kwArgs['scriptTableLineNumber'] = scriptTableLineNumber
        kwArgs['featureTableLineNumber'] = featureTableLineNumber
        kwArgs['featureIndexToTag'] = featureIndexToTag
        kwArgs['forGPOS'] = True
        fws.goto(featureTableLineNumber + 1)
        
        featureDict = featuredict.FeatureDict.fromValidatedFontWorkerSource(
            fws,
            logger = logger,
            **kwArgs)

        kwArgs['featureDict'] = featureDict
        fws.goto(scriptTableLineNumber + 1)
        
        scriptDict = scriptdict.ScriptDict.fromValidatedFontWorkerSource(
            fws,
            logger = logger,
            **kwArgs)

        return cls(features=featureDict, scripts=scriptDict)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GPOS object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> fvb = GPOS.fromvalidatedbytes
        >>> logger = utilities.makeDoctestLogger("GPOS_test")
        >>> obj = fvb(s, logger=logger)
        GPOS_test.GPOS - DEBUG - Walker has 240 remaining bytes.
        GPOS_test.GPOS.version - DEBUG - Walker has 240 remaining bytes.
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
        slOffset, flOffset, llOffset = w.unpack("3H")
        
        if version.major != 1 or version.minor != 0:
            logger.error((
              'V0454',
              (version,),
              "Expected version 1.0, but got %s."))
            
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
            return cls()
        
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
        
        r = cls(version=version, features=fd, scripts=sd)
        r._cachedOriginalLookupList = ll.__copy__()
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GPOS object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == GPOS.frombytes(obj.binaryString())
        True
        """
        
        version = otversion.Version.fromwalker(w, **kwArgs)
        slOffset, flOffset, llOffset = w.unpack("3H")
        fitt = []
        
        if not all([slOffset, flOffset, llOffset]):
            return cls()
        
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
        
        r = cls(version=version, features=fd, scripts=sd)
        r._cachedOriginalLookupList = ll.__copy__()
        return r
    
    def getOriginalLookupList(self, **kwArgs):
        """
        Returns a tuple whose contents are the same (and in the same order) as
        the original lookup list used to create the object. If the object was
        created directly, and not via fromwalker, this will be None.
        """
        
        r = self.__dict__.get('_cachedOriginalLookupList', None)
        
        if (r is None) and kwArgs.pop('makeIfMissing', False):
            r = lookuplist.LookupList.fromtoplevel(self, **kwArgs)
            self.__dict__['_cachedOriginalLookupList'] = r
        
        return r
    
    def isValid(self, **kwArgs):
        """
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        r = self.scripts.isValid(logger=logger.getChild("scripts"), **kwArgs)
        logger.debug(('Vxxxx', (), "Gathering Lookups..."))
        keyTrace = {}
        kwArgs.pop('suppressDeepValidation', None)
        
        try:
            ll = lookuplist.LookupList.fromtoplevel(
              self.features,
              keyTrace = keyTrace)
        
        except utilities.CycleError:
            logger.error((
              'V0912',
              (),
              "Cannot validate the 'GPOS' table, because one or more "
              "Lookups include circular references."))
            
            return False
        
        for i, obj in enumerate(ll):
            logger.debug(('Vxxxx', (i,), "Lookup %d"))
            
            if id(obj) in keyTrace:
                s = sorted({x[0] for x in keyTrace[id(obj)]})
                subLogger = logger.getChild(str(s))
            else:
                subLogger = logger.getChild("feature")
            
            rThis = obj.isValid(
              suppressDeepValidation = True,
              logger = subLogger,
              **kwArgs)
            
            r = rThis and r
        
        for featKey, featTable in self.features.items():
            fp = featTable.featureParams
            
            if fp is not None:
                subLogger = logger.getChild(str(featKey))
                r = fp.isValid(logger=subLogger, **kwArgs) and r
        
        # detect orphaned features
        allFeatures = set(self.features.keys())
        
        for scriptTag, scriptTable in self.scripts.items():
            if scriptTable.defaultLangSys:
                defLangSys = scriptTable.defaultLangSys
                
                if defLangSys.requiredFeature:
                    allFeatures.discard(defLangSys.requiredFeature)
                
                for optFeatTag in sorted(defLangSys.optionalFeatures):
                    allFeatures.discard(optFeatTag)

            for langSysTag, langSysTable in scriptTable.items():
                if langSysTable.requiredFeature:
                    allFeatures.discard(langSysTable.requiredFeature)
                
                for optFeatTag in sorted(langSysTable.optionalFeatures):
                    allFeatures.discard(optFeatTag)
                    
        # allFeatures should be empty if all are accounted for 
        # in the scriptTable; error otherwise.
        if len(allFeatures):
            logger.error((
              'V0959',
              (",".join([f.decode('ascii', errors='ignore') for f in sorted(allFeatures)]), ),
              "The following features are orphaned (not referenced "
              "in the Script Table): %s"))
            
            r = False

        return r
    
    def merged(self, other, **kwArgs):
        """
        This method is a front-end that does collision removal on the feature
        tags.
        """
        
        if not other:
            return self.__deepcopy__()
        
        mkc = {}
        
        fMerged = self.features.merged(
          other.features,
          mergedKeyChanges = mkc,
          **kwArgs)
        
        osCopy = other.scripts.__deepcopy__().tagsRenamed(mkc)
        sMerged = self.scripts.merged(osCopy, **kwArgs)
        return type(self)(features=fMerged, scripts=sMerged)
    
    def tagsRenamed(self, oldToNew):
        """
        Returns a new GPOS object where feature tags are changed as in the
        specified dict. If a tag is not in the dict, it is not modified.
        
        >>> bs1 = _testingValues[1].binaryString()
        >>> _testingValues[1].tagsRenamed({b'abcd0001': b'abcd0006'}).pprint()
        Version:
          Major version: 1
          Minor version: 0
        Features:
          Feature 'abcd0006':
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
                abcd0006
                size0002
            Default LangSys object:
              Required feature tag: wxyz0003
              Optional feature tags:
                abcd0006
                size0002
        
        >>> bs2 = _testingValues[1].binaryString()
        >>> bs1 == bs2
        True
        """
        
        return type(self)(
          features = self.features.tagsRenamed(oldToNew),
          scripts = self.scripts.tagsRenamed(oldToNew))

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of GPOS table to provided stream 's' in
        FontWorker dump format. Although not used directly at 
        this level, the following keywords are required by sub-tables:
        
        namer       a Namer-like object to return glyph name strings
        datatable   Glyf or CFF object from which to obtain XYtoPointMaps
        editor      Editor (to retrieve GDEF table for markfiltersets)
        """
        
        sorted_feature_keys = sorted(self.features)
        sfki = sorted_feature_keys.index

        # Header
        s.write("FontDame GPOS table\n\n")
        s.write("EM\t%d\n\n" % (kwArgs.get('upem'),))

        # FW script table
        s.write("\nscript table begin\n")
        
        for sc in sorted(self.scripts):
            deftable = self.scripts[sc].defaultLangSys
            reqfeattag = deftable.requiredFeature
            
            if reqfeattag:
                req = str(sfki(reqfeattag))
            else:
                req = None
            
            sorted_default_tags = sorted(deftable.optionalFeatures)
            tags_str = ", ".join([str(sfki(t)) for t in sorted_default_tags])
            tag_dec = sc.decode('ascii')
            s.write("%s\tdefault\t%s\t%s\n" % (tag_dec, req or "", tags_str))
    
            for ls in sorted(self.scripts[sc]):
                lstable = self.scripts[sc][ls]
                reqfeattag = lstable.requiredFeature
                
                if reqfeattag:
                    req = str(sfki(reqfeattag))
                else:
                    req = None
                
                sorted_ls_tags = sorted(lstable.optionalFeatures)
                tags_str = ", ".join([str(sfki(t)) for t in sorted_ls_tags])
                tag_dec = sc.decode('ascii')
                lstag_dec = ls.decode('ascii')
                s.write("%s\t%s\t%s\t%s\n" % (tag_dec, lstag_dec, req or "", tags_str))
        
        s.write("script table end\n\n")

        # FW feature table
        s.write("\nfeature table begin\n")
        
        for i, k in enumerate(sorted_feature_keys):
            feat_str = ", ".join([str(l.sequence) for l in self.features[k]])
            tag_dec = (k[0:4]).decode('ascii')
            s.write("%d\t%s\t%s\n" % (i, tag_dec, feat_str))    
        
        s.write("\nfeature table end\n")

        # FW lookups
        original_lookup_seq = self.getOriginalLookupList() or []
        
        for lkp in original_lookup_seq:
            lkp.writeFontWorkerSource(s)
    
            if lkp.flags.useMarkFilteringSet:
                mgsi = lkp.getMarkGlyphSetIndex(**kwArgs)
            else:
                mgsi = None
    
            lkp.flags.writeFontWorkerSource(s, markglyphsetindex=mgsi)
    
            for sti, st in enumerate(lkp):
                if hasattr(st, 'writeFontWorkerSource'):
                    if sti > 0: s.write("\nsubtable end\n\n")
                    st.writeFontWorkerSource(s, **kwArgs)
                else:
                    s.write("% unsupported lookup type\n")

            s.write("\nlookup end\n\n")

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
        GPOS(features=fdtv[2], scripts=sdtv[1]))
    
    del fdtv, sdtv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1
    }
    _test_FW_namer._initialized = True

    fws = fontworkersource.FontWorkerSource

    _test_FW_s = fws(StringIO(
        """FontDame GPOS table

        EM	 2048

        lookup	testSingle	single
        x placement	A	-123
        lookup end
        
        feature table begin
        0	kern	testSingle
        feature table end
        
        script table begin
        thai	default		0
        script table end
        """))

    _test_FW_s2 = fws(StringIO(
        """FontDame GPOS table

        EM	 2048

        abc
        
        lookup	testSingle	single
        def
        x placement	A	-123
        lookup end
        
        feature table begin
        0	kern	testSingle
        ghi
        feature table end
        
        script table begin
        thai	default		0
        jkl
        script table end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
