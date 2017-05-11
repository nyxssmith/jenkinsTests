#
# GSUB_v10.py
#
# Copyright © 2007-2014, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
The top-level classes and other common items for the pre-v1.8 OpenType 'GSUB'
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

from fontio3.opentype import version as otversion

# -----------------------------------------------------------------------------

#
# Classes
#

class GSUB(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Top-level GSUB objects. These are simple objects with three attributes:
    
        version     A Version object.
        features    A FeatureDict object.
        scripts     A ScriptDict object.
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
    
    objSpec = dict(
        obj_boolfalseiffalseset = frozenset({'features'}))
    
    attrSorted=('version', 'features', 'scripts')

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
            
            w.addIndexMap(
              "lookupList_GSUB",
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
        Custom code to compact the GSUB.
        """
        
        fNew = self.features.compacted(**kwArgs)
        
        if not fNew:
            return None
        
        sNew = self.scripts.__deepcopy__()
        sNew.trimToValidFeatures(set(fNew))
        return GSUB(features=fNew, scripts=sNew)

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new GSUB object from the specified
        FontWorkerSource object, with source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = GSUB.fromValidatedFontWorkerSource(_test_FW_s2, namer=_test_FW_namer, logger=logger, editor={})
        FW_test.GSUB.featuredict - WARNING - line 11 -- incorrect number of tokens, expected 3, found 1
        FW_test.GSUB.featuredict.lookup.single - WARNING - line 7 -- incorrect number of tokens, expected 2, found 1
        FW_test.GSUB.scriptdict - ERROR - line 16 -- incorrect number of tokens, expected 4, found 1
        >>> obj.pprint()
        Version:
          Major version: 1
          Minor version: 0
        Features:
          Feature 'locl0001':
            Lookup 0:
              Subtable 0 (Single substitution table):
                1: 7
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
                locl0001
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("GSUB")
        parseinfo = kwArgs.get('parseinfo', {})
        firstLine = 'FontDame GSUB table'
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
        kwArgs['forGPOS'] = False
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
        Creates and returns a new GSUB object from the specified walker, doing
        source validation.
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
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = otversion.Version.fromvalidatedwalker(w, logger=logger, **kwArgs)
        slOffset, flOffset, llOffset = w.unpack("3H")
        
        if version.major != 1 or version.minor != 0:
            logger.error((
              'V0454',
              (version,),
              "Expected version 1.0, but got %s"))
            
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
            return cls()
        
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
        
        r = cls(version=version, features=fd, scripts=sd)
        r._cachedOriginalLookupList = ll.__copy__()
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
        slOffset, flOffset, llOffset = w.unpack("3H")
        fitt = []
        
        if not all([slOffset, flOffset, llOffset]):
            return cls()
        
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
    
    def merged(self, other, **kwArgs):
        """
        This method is a front-end that does collision removal on the feature
        tags before passing the merged() process along down the line.
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
        Returns a new GSUB object where feature tags are changed as in the
        specified dict. If a tag is not in the dict, it is not modified.
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
        s.write("FontDame GSUB table\n\n")

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
