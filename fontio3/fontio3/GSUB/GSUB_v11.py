#
# GSUB.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the OpenType v1.8 'GSUB'
table (table version 1.1).
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.GSUB.GSUB_v10 import GSUB as GSUB_v10

from fontio3.opentype import (
  featuredict,
  featurevariations,
  fontworkersource,
  lookuplist,
  scriptdict)

from fontio3.opentype import version as otversion

# -----------------------------------------------------------------------------

#
# Classes
#

class GSUB(GSUB_v10, metaclass=simplemeta.FontDataMetaclass):
    """
    Top-level GSUB objects. These are simple objects with four attributes:
    
        version             A Version object.
        features            A FeatureDict object.
        scripts             A ScriptDict object.
        featureVariations   A FeatureVariationsTable object.
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

    attrSorted=('version', 'features', 'scripts', 'featureVariations')

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GSUB object to the specified LinkedWriter.
        (Note that this class has an explicit binaryString() method as well).
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        editor = kwArgs.get('editor')
        if editor.reallyHas(b'GDEF'):
            kwArgs['GDEF'] = editor.GDEF
        
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
              "lookupList_GSUB",
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
                if 'axisOrder' not in kwArgs:
                    kwArgs['axisOrder'] = editor.fvar.axisOrder
                
                self.featureVariations.buildBinary(
                  w,
                  lookupList = ll,
                  stakeValue = fvstake,
                  tagToFeatureIndex = ttfi,
                  **kwArgs)
            
            for i, obj, stake in sorted(extPool.values()):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GSUB object from the specified walker, doing
        source validation.
        
        
        Bare-minimum example...1 script, 1 feature, 1 lookup, etc.
        >>> s = ("0001 0001 000E 0022 0030 0000 0050 0001"
        ...      "7363 7230 0008 0004 0000 0000 FFFF 0001"
        ...      "0000 0001 6665 6130 0008 0000 0001 0000"
        ...      "0001 0004 0007 0000 0001 0008 0001 0001"
        ...      "0000 0008 0001 0006 001A 0001 0001 0004"
        ...      "0001 0000 0000 0001 0000 0010 0000 001E"
        ...      "0001 0000 0006 0001 0001 8000 7FFF 0000"
        ...      "0001 0001 0000 0000 000C 0000 0001 0000")

        >>> b = utilities.fromhex(s)

        <<< utilities.hexdump(b)  # for debugging
        >>> ao = ('wght', 'wdth')
        >>> l = utilities.makeDoctestLogger("test")
        >>> ll = _lltv[1]
        >>> fvb = GSUB.fromvalidatedbytes
        >>> obj = fvb(b, logger=l, axisOrder=ao, lookupList=ll)
        test.GSUB - DEBUG - Walker has 128 remaining bytes.
        test.GSUB.version - DEBUG - Walker has 128 remaining bytes.
        test.GSUB.lookuplist - DEBUG - Walker has 80 bytes remaining.
        test.GSUB.lookuplist - DEBUG - Offset count is 1
        test.GSUB.lookuplist - DEBUG - Offset 0 is 4
        test.GSUB.lookuplist.lookup 0.lookup - DEBUG - Walker has 76 remaining bytes.
        test.GSUB.lookuplist.lookup 0.lookup - DEBUG - Kind is 7
        test.GSUB.lookuplist.lookup 0.lookup - DEBUG - Number of subtables is 1
        test.GSUB.lookuplist.lookup 0.lookup - DEBUG - Subtable offset 0 is 8
        test.GSUB.lookuplist.lookup 0.lookup.subtable 0.single - DEBUG - Walker has 60 bytes remaining.
        test.GSUB.lookuplist.lookup 0.lookup.subtable 0.single.coverage - DEBUG - Walker has 54 remaining bytes.
        test.GSUB.lookuplist.lookup 0.lookup.subtable 0.single.coverage - DEBUG - Format is 1, count is 1
        test.GSUB.lookuplist.lookup 0.lookup.subtable 0.single.coverage - DEBUG - Raw data are [4]
        test.GSUB.featuredict - DEBUG - Walker has 94 remaining bytes.
        test.GSUB.featuredict - DEBUG - Count is 1
        test.GSUB.featuredict - DEBUG - Feature 0: tag is 'fea0', offset is 8
        test.GSUB.featuredict.feature table 0.featuretable - DEBUG - Walker has 86 remaining bytes.
        test.GSUB.featuredict.feature table 0.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 1
        test.GSUB.featuredict.feature table 0.featuretable - DEBUG - Entry 0 is Lookup 0
        test.GSUB.scriptdict - DEBUG - Walker has 114 remaining bytes.
        test.GSUB.scriptdict - DEBUG - Group count is 1
        test.GSUB.scriptdict - DEBUG - Script rec for tag 'scr0' at offset 8
        test.GSUB.scriptdict.script scr0.langsysdict - DEBUG - Walker has 106 remaining bytes.
        test.GSUB.scriptdict.script scr0.langsysdict - DEBUG - Default offset is 4; langSys count is 0
        test.GSUB.scriptdict.script scr0.langsysdict.default.langsys - DEBUG - Walker has 102 bytes remaining.
        test.GSUB.scriptdict.script scr0.langsysdict.default.langsys - DEBUG - Lookup order is 0, Required index is 65535, feature count is 1
        test.GSUB.scriptdict.script scr0.langsysdict.default.langsys - DEBUG - Optional feature 0 is 0
        test.GSUB.featurevariations - DEBUG - Walker has 48 remaining bytes.
        test.GSUB.version - DEBUG - Walker has 48 remaining bytes.
        test.GSUB.featurevariations - INFO - FeatureVariationRecordCount is 1
        test.GSUB.featurevariations - DEBUG - offsetConditionSet: 0x00000010, offsetFeatureTableSubst: 0x0000001E
        test.GSUB.conditionset - DEBUG - Walker has 32 remaining bytes.
        test.GSUB.conditionset - INFO - ConditionCount is 1
        test.GSUB.condition - DEBUG - Walker has 26 remaining bytes.
        test.GSUB.condition - INFO - AxisTag 'wdth'
        test.GSUB.condition - INFO - Min: -2.000000, Max: 1.999939
        test.GSUB.featuretablesubst - DEBUG - Walker has 18 remaining bytes.
        test.GSUB.version - DEBUG - Walker has 18 remaining bytes.
        test.GSUB.featuretablesubst - INFO - SubstitutionCount is 1
        test.GSUB.featuretablesubst - DEBUG - Feature index 0, offset 0x0000000C
        test.GSUB.featuretable - DEBUG - Walker has 6 remaining bytes.
        test.GSUB.featuretable - DEBUG - FeatureParams offset is 0, lookupCount is 1
        test.GSUB.featuretable - DEBUG - Entry 0 is Lookup 0
        """
        
        editor = kwArgs.get('editor')
        if editor:
            if editor.reallyHas(b'GDEF') and 'GDEF' not in kwArgs:
                kwArgs['GDEF'] = editor.GDEF
            if editor.reallyHas(b'fvar') and 'axisOrder' not in kwArgs:
                kwArgs['axisOrder'] = editor.fvar.axisOrder
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("GSUB")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = otversion.Version.fromvalidatedwalker(w, logger=logger, **kwArgs)
        slOffset, flOffset, llOffset, fvtOffset = w.unpack("3HL")
        
        if version.major != 1 or version.minor != 1:
            logger.error((
              'V0454',
              (version,),
              "Expected version 1.1, but got %s"))
            
            return None
        
        if not slOffset:
            logger.warning((
              'V0455',
              (),
              "The ScriptList offset is zero; no further GSUB "
              "validation will be performed."))
        
        if not flOffset:
            logger.warning((
              'V0456',
              (),
              "The FeatureList offset is zero; no further GSUB "
              "validation will be performed."))
        
        if not llOffset:
            logger.warning((
              'V0457',
              (),
              "The LookupList offset is zero; no further GSUB "
              "validation will be performed."))
        
        if not all([slOffset, flOffset, llOffset]):
            return cls()  # note: okay to have null offset to FV table
        
        delKeys = {'featureIndexToTag', 'forGPOS', 'lookupList'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        fitt = []
        
        ll = lookuplist.LookupList.fromvalidatedwalker(
          w.subWalker(llOffset),
          forGPOS = False,
          logger = logger,
          **kwArgs)
        
        if ll is None:
            return None
        
        fd = featuredict.FeatureDict.fromvalidatedwalker(
          w.subWalker(flOffset),
          featureIndexToTag = fitt,
          forGPOS = False,
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
            fvt = featurevariations.FeatureVariations.fromvalidatedwalker(
              w.subWalker(fvtOffset),
              featureIndexToTag = fitt,
              logger = logger,
              lookupList = ll,
              **kwArgs)
        else:
            fvt = featurevariations.FeatureVariations()
        
        r = cls(version=version, features=fd, scripts=sd, featureVariations=fvt)
        r._cachedOriginalLookupList = ll.__copy__()
        return r
    
    @classmethod
    def fromversion10(cls, v10table, **kwArgs):
        """
        Up-convert from v1.0 GSUB to v1.1
        """
        
        r = cls(features=v10table.features, scripts=v10table.scripts)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GSUB object from the specified walker.
        """
        
        editor = kwArgs.get('editor')
        if editor:
            if editor.reallyHas(b'GDEF') and 'GDEF' not in kwArgs:
                kwArgs['GDEF'] = editor.GDEF
            if editor.reallyHas(b'fvar') and 'axisOrder' not in kwArgs:
                kwArgs['axisOrder'] = editor.fvar.axisOrder
        
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
          forGPOS=False,
          **kwArgs)
        
        fd = featuredict.FeatureDict.fromwalker(
          w.subWalker(flOffset),
          featureIndexToTag=fitt,
          forGPOS=False,
          lookupList=ll,
          **kwArgs)
        
        sd = scriptdict.ScriptDict.fromwalker(
          w.subWalker(slOffset),
          featureIndexToTag=fitt,
          **kwArgs)
         
        if fvtOffset:
            fvt = featurevariations.FeatureVariations.fromwalker(
              w.subWalker(fvtOffset),
              featureIndexToTag = fitt,
              lookupList=ll,
              **kwArgs)
        else:
            fvt = featurevariations.FeatureVariations()
        
        r = cls(version=version, features=fd, scripts=sd, featureVariations=fvt)
        r._cachedOriginalLookupList = ll.__copy__()
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
              "Cannot validate the 'GSUB' table, because one or more "
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

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype import lookuplist
    from fontio3.utilities import namer
    from io import StringIO

    _lltv = lookuplist._testingValues

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 7
    }
    _test_FW_namer._initialized = True

    fws = fontworkersource.FontWorkerSource

    _test_FW_s = fws(StringIO(
        """FontDame GSUB table

        lookup	testSingle	single
        A	B
        lookup end
        
        feature table begin
        0	locl	testSingle
        feature table end
        
        script table begin
        thai	default		0
        script table end
        """))

    _test_FW_s2 = fws(StringIO(
        """FontDame GSUB table

        This should be ignored, per FontWorker spec.
        
        lookup	testSingle	single
        A	B
        abc
        lookup end
        
        feature table begin
        def
        0	locl	testSingle
        feature table end
        
        script table begin
        ghi
        thai	default		0
        script table end

        This also should be ignored, per FontWorker spec.
        """))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
