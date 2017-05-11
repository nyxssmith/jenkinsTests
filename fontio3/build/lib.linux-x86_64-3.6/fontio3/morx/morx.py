#
# morx.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AAT (and GX) 'morx' tables.
"""

# System imports
import collections
import functools
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.morx import (
  contextual,
  coverage,
  featureentry,
  features,
  featuresetting,
  gsubconverter,
  insertion,
  ligature,
  noncontextual,
  rearrangement)

from fontio3.statetables.subtable_glyph_coverage_sets import \
    SubTableGlyphCoverageSets

# -----------------------------------------------------------------------------

#
# Private constants
#

_makers = {
  0: rearrangement.Rearrangement.fromwalker,
  1: contextual.Contextual.fromwalker,
  2: ligature.Ligature.fromwalker,
  4: noncontextual.Noncontextual.fromwalker,
  5: insertion.Insertion.fromwalker}

_makers_validated = {
  0: rearrangement.Rearrangement.fromvalidatedwalker,
  1: contextual.Contextual.fromvalidatedwalker,
  2: ligature.Ligature.fromvalidatedwalker,
  4: noncontextual.Noncontextual.fromvalidatedwalker,
  5: insertion.Insertion.fromvalidatedwalker}

_kindStrings = {
  0: "rearrangement",
  1: "contextual",
  2: "ligature",
  4: "noncontextual",
  5: "insertion"}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _defaultFlags_ppf(p, value, label, **kwArgs):
    s = "%X" % (value,)
    extra = len(s) % 8
    
    if extra:
        s = "0" * (8 - extra) + s
    
    p.simple(s, label=label, **kwArgs)

def _labelFunc(n, **kwArgs):
    kind = kwArgs['obj'].kind
    return "Subtable %d (%s)" % (n, _kindStrings[kind])

def _orLists(v1, v2):
    return list(map(operator.or_, v1, v2))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Morx(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'morx' tables. These are lists of subtable
    objects of the various kinds. There are two attributes:
    
        defaultFlags    An int of arbitary size, containing the total bit mask
                        for all features that are enabled by default.
    
        features        A Features object. Note that the mask values in this
                        object may span multiple chains; the internal logic
                        here will separate out individual chains.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = _labelFunc,
        item_pprintlabelfuncneedsobj = True,
        seq_compactremovesfalses = True)
    
    attrSpec = dict(
        defaultFlags = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Default flags",
            attr_pprintfunc = _defaultFlags_ppf),
        
        features = dict(
            attr_followsprotocol = True,
            attr_initfunc = features.Features,
            attr_label = "Feature map"),

        preferredVersion = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True,
            attr_pprintfunc = (lambda p,x,label,**k: p.simple(hex(x), label=label)),
            attr_wisdom = ("Preferred version when writing. Initially "
              "set to the same as originalVersion; override by setting "
              "a format number or set to None to allow fontio3 to "
              "analyze and write what it thinks is best for the content.")),

        originalVersion = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True,
            attr_pprintfunc = (lambda p,x,label,**k: p.simple(hex(x), label=label)),
            attr_wisdom = "Original version when read"))

    attrSorted = ('defaultFlags', 'features', 'preferredVersion',
                  'originalVersion')

    #
    # Methods
    #
    
    def _divideIntoChains(self, candidates):
        """
        Returns an iterator over Morx objects that will fit into a single
        chain. Note that depending on circumstances, the bit masks (in both
        the subtables and the features) may be redone.
        """
        
        # Determine how many bits each candidate needs
        
        nBits = [0] * len(candidates)
        seen = set()
        
        for i, c in enumerate(candidates):
            for subtableIndex in c:
                mv = self[subtableIndex].maskValue
                
                if mv not in seen:
                    seen.add(mv)
                    nBits[i] += bin(mv)[2:].count('1')
        
        # Now group 32 bits or less for the new chains, rebuilding the bit
        # masks for the enable and disable flags at the same time.
        
        currBitCount = 0
        cumulIndices = set()
        
        for i, c in enumerate(candidates):
            thisBitCount = nBits[i]
            
            if currBitCount + thisBitCount > 32:
                # emit this chain, then start the next one
                yield self._subset(sorted(cumulIndices))
                currBitCount = thisBitCount
                cumulIndices = set(c)
            
            else:
                currBitCount += thisBitCount
                cumulIndices.update(c)
        
        # emit this final chain
        yield self._subset(sorted(cumulIndices))
    
    def _makeChainGroupCandidates(self):
        """
        Returns a list of sets, each of which contains indices into self
        representing a connected group of subtables (connected via the info in
        the derived clusters). Each set therefore represents a group that could
        make up a single chain -- more can be added to a chain, but the group
        cannot be subdivided without causing potential glyph dependency bugs.
        """
        
        f = self.features
        combined = self.features.makeCombined()
        clusters = features._makeClusters(combined)
        r = []
        d = {}  # {featIndices} -> collector-OR'ed mask
        
        for c in clusters:
            d[c] = functools.reduce(operator.or_, (f[i].enableMask for i in c))
        
        featSetToSubtableIndices = collections.defaultdict(set)
        
        for i, subtable in enumerate(self):
            for fs, mask in d.items():
                if subtable.maskValue & mask:
                    featSetToSubtableIndices[fs].add(i)
        
        v = sorted(sorted(obj) for obj in featSetToSubtableIndices.values())
        cumul = set()
        
        for i, this in enumerate(v):
            if i == 0:
                newOne = max(this) + 1
                groupStartIndex = 0
                cumul = set(this)
            
            elif newOne == this[0]:  # should this be "newOne in this"?
                r.append(cumul)
                groupStartIndex = i
                newOne = max(newOne, max(this) + 1)
                cumul = set(this)
            
            else:
                cumul.update(this)
        
        r.append(cumul or set())
        return r
    
    def _subset(self, indices):
        """
        """
        
        v = [None] * len(indices)
        oldToNew = {}
        newDefaultFlags = 0
        nextBit = 1
        
        for newIndex, oldIndex in enumerate(indices):
            obj = self[oldIndex].__deepcopy__()
            old = obj.maskValue
            
            if old not in oldToNew:
                if bin(old)[2:].count('1') != 1:
                    raise ValueError(
                     "Subtable has maskValue with more than one bit set!")
                
                oldToNew[old] = nextBit
                
                if self.defaultFlags & old:
                    newDefaultFlags |= nextBit
                
                nextBit *= 2
            
            obj.maskValue = oldToNew[old]
            v[newIndex] = obj
        
        return type(self)(
          v,
          defaultFlags = newDefaultFlags,
          features = self.features.masksRenumbered(oldToNew))
    
    def buildBinary(self, w, **kwArgs):
        """
        The following keyword arguments are used:
        
            stakeValue      The stake value to be used at the start of this
                            output.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        version = 0x00020000  # default to version 2
        if self.preferredVersion:
            # check if caller prefers a specific version
            if self.preferredVersion in {0x00020000, 0x00030000}:
                version = self.preferredVersion
            else:
                raise ValueError("Unknown preferredVersion (0x%08X), expected 0x00020000 or 0x00030000" % (self.preferredVersion,))
        else:
            # use version 3 if there are any non-empty coverage sets
            for subtable in self:
                if subtable.glyphCoverageSet:
                    version = 0x00030000
                    break
        w.add("L", version)  # version
        
        if len(self) == 0:
            w.add("L", 0)
            return
        
        chainCountStake = w.addDeferredValue("L")
        chainCount = 0
        noFalses = self.__copy__()  # yes, shallow
        
        for i in range(len(noFalses) - 1, -1, -1):
            if not noFalses[i]:
                del noFalses[i]
        
        for chain in noFalses.chainIterator():
            chainStartLength = w.byteLength
            w.add("L", chain.defaultFlags)
            chainLengthStake = w.addDeferredValue("L")
            
            w.add(
              "L",
              1 + sum(obj.featureSetting != (0, 1) for obj in chain.features))
            
            w.add("L", len(chain))
            chain.features.buildBinary(w)
            
            for i, table in enumerate(chain):
                if table.kind == 2:
                    table = table.combinedActions()
                
                tableStartLength = w.byteLength
                tableLengthStake = w.addDeferredValue("L")
                table.coverage.buildBinary(w)
                w.add("L", table.maskValue)
                table.buildBinary(w, **kwArgs)
                w.alignToByteMultiple(4)
                
                w.setDeferredValue(
                  tableLengthStake,
                  "L",
                  int(w.byteLength - tableStartLength))

            if version == 0x00030000:
                glyphCoverageSets = SubTableGlyphCoverageSets(
                    [x.glyphCoverageSet for x in chain])
                glyphCoverageSets.buildBinary(w, **kwArgs)

            w.setDeferredValue(
              chainLengthStake,
              "L",
              int(w.byteLength - chainStartLength))
            
            chainCount += 1
        
        w.setDeferredValue(chainCountStake, "L", chainCount)
    
    def chainIterator(self):
        """
        """
        
        candidates = self._makeChainGroupCandidates()
        
        for chain in self._divideIntoChains(candidates):
            yield chain
    
#     @classmethod
#     def fromGSUB(cls, gsubObj, scriptTag, **kwArgs):
#         """
#         Creates and returns a new Morx object from the specified GSUB object
#         for the specified script. The Lookup order will be preserved as the
#         subtable order in the new Morx object.
#         
#         Note that *only* the Lookups will be reflected in the new Morx; this
#         method does not attempt to add the shaping rules. This is a low-level
#         translator only.
#         
#         The following keyword arguments are supported:
#         
#             backMap     If a dict is passed in as this keyword argument, it
#                         will be filled with a mapping from GSUB feature tag to
#                         sets of Morx indices.
#             
#             langSys     A 4-byte bytestring representing the langSys to be
#                         converted in the specified script. If this value is not
#                         specified, the defaultLangSys will be used; if the
#                         specified script does not have any features in the
#                         defaultLangSys then an empty Morx object will be
#                         returned.
#             
#             optionals   A set of 4-byte bytestring feature tags representing
#                         features that will not be on by default. If this value
#                         is not specified, all generated Morx subtables will be
#                         on by default.
#         
#         >>> gsubObj = _makeGSUB()
#         >>> gsubObj.pprint()
#         Features:
#           Feature 'liga0001':
#             Lookup 0:
#               Subtable 0 (Ligature substitution table):
#                 Ligature_GlyphTuple((20, 30)): 40
#               Lookup flags:
#                 Right-to-left for Cursive: False
#                 Ignore base glyphs: False
#                 Ignore ligatures: False
#                 Ignore marks: False
#               Sequence order (lower happens first): 0
#         Scripts:
#           Script object latn:
#             Default LangSys object:
#               Optional feature tags:
#                 liga0001
#         
#         >>> m = Morx.fromGSUB(gsubObj, b'latn')
#         >>> m.pprint(onlySignificant=True)
#         Subtable 0 (contextual):
#           State 'Start of text':
#             Class '20':
#               Mark this glyph, then go to state 'Saw_20'
#           State 'Start of line':
#             Class '20':
#               Mark this glyph, then go to state 'Saw_20'
#           State 'Saw_20':
#             Class 'Deleted glyph':
#               Go to state 'Saw_20'
#             Class '20':
#               Mark this glyph, then go to state 'Saw_20'
#             Class '30':
#               Go to state 'Start of text' after changing the marked glyph thus:
#                 20: 40
#               and changing the current glyph thus:
#                 30: Deleted glyph
#           Class table:
#             20: 20
#             30: 30
#           Mask value: 00000001
#           Coverage:
#             Subtable kind: 0
#         Default flags: 00000001
#         Feature map:
#           Feature 1:
#             Feature/setting: No features disabled (0, 0)
#             Enable mask: 00000001
#             Disable mask: FFFFFFFF
#           Feature 2:
#             Feature/setting: All features disabled (0, 1)
#             Enable mask: 00000000
#             Disable mask: 00000000
#         """
#         
#         r = cls()
#         
#         if scriptTag not in gsubObj.scripts:
#             return r
#         
#         lsdObj = gsubObj.scripts[scriptTag]
#         ls = kwArgs.pop('langSys', None)
#         
#         if ls is None:
#             lsObj = lsdObj.defaultLangSys
#         elif ls in lsdObj:
#             lsObj = lsdObj[ls]
#         else:
#             return r
#         
#         dfltOnFeats = set()
#         dfltOffFeats = set()
#         optionals = kwArgs.pop('optionals', set())
#         
#         if lsObj.requiredFeature:
#             dfltOnFeats.add(lsObj.requiredFeature)
#         
#         for featTag in lsObj.optionalFeatures:
#             if featTag in optionals:
#                 dfltOffFeats.add(featTag)
#             else:
#                 dfltOnFeats.add(featTag)
#         
#         # At this point we have all the needed feature tags. Now we need to
#         # retrieve the Feature objects so we can ascertain the ordering.
#         
#         featDict = gsubObj.features
#         orderDict = {}
#         
#         for featTag in dfltOnFeats | dfltOffFeats:
#             featObj = featDict[featTag]
#             
#             for lkupIndex, lkupObj in enumerate(featObj):
#                 orderDict[(featTag, lkupIndex)] = lkupObj.sequence
#         
#         # Now we're ready to start converting, and additionally filling in the
#         # backmap (or a throwaway local version, if one wasn't specified).
#         
#         it = sorted(orderDict.items(), key=operator.itemgetter(1))
#         backMap = kwArgs.pop('backMap', {})
#         currMask = 2  # we reserve 1 for "default on" features
#         currSetting = 0
#         stdCoverage = coverage.Coverage()
#         featObj = features.Features([])
#         FE = featureentry.FeatureEntry
#         FS = featuresetting.FeatureSetting
#         
#         featObj.append(
#           FE(featureSetting=FS((0, 0)), enableMask=1, disableMask=0xFFFFFFFF))
#         
#         for (featTag, lkupIndex), sequence in it:
#             lkupObj = featDict[featTag][lkupIndex]
#             
#             for subObj in lkupObj:
#                 inTuples, outTuples = subObj.effects(**kwArgs)
#                 v = gsubconverter.analyze(inTuples, outTuples, **kwArgs)
#                 
#                 if featTag in dfltOnFeats:
#                     useMask = 1
#                 
#                 else:
#                     useMask = currMask
#                     
#                     newFeatEntry = FE(
#                       featureSetting = FS((5000, currSetting)),
#                       enableMask = useMask,
#                       disableMask = 0xFFFFFFFF)
#                     
#                     featObj.append(newFeatEntry)
#                     currMask *= 2
#                 
#                 for obj in v:
#                     obj.coverage = stdCoverage
#                     obj.maskValue = useMask
#                 
#                 rg = range(len(r), len(r) + len(v))
#                 backMap.setdefault(featTag, set()).update(rg)
#                 r.extend(v)
#         
#         featObj.append(features.LAST_ENTRY)
#         r.defaultFlags = 1
#         r.features = featObj
#         
#         # xxx what about the 'feat' table?
#         
#         return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Morx object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('morx')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, chainCount = w.unpack("2L")
        
        if version not in {0x00020000, 0x00030000}:
            logger.error((
              'V0002',
              (version,),
              "Unknown 'morx' version: 0x%08X."))

            return None
        
        r = cls()
        r.originalVersion = version
        r.preferredVersion = version
        kwArgs.pop('coverage', None)
        kwArgs.pop('maskValue', None)
        
        if not chainCount:
            logger.warning((
              'V0729',
              (),
              "The chainCount is zero, so there is no content."))
            
            return r
        
        else:
            logger.info(('V0907', (chainCount,), "Number of chains is %d"))
        
        for chainIndex in range(chainCount):
            extraShift = 32 * chainIndex
            
            if w.length() < 16:
                logger.error((
                  'V0730',
                  (chainIndex,),
                  "The header for chain %d is missing or incomplete."))
                
                return None
            
            chainDefFlags, flagCount, subtableCount = w.unpack("L4x2L")
            
            logger.info((
              'V0908',
              (chainIndex, subtableCount),
              "Chain %d's subtable count is %d"))
            
            r.defaultFlags |= (chainDefFlags << extraShift)
            
            chainFeatures = features.Features.fromvalidatedwalker(
              w,
              count = flagCount,
              extraShift = extraShift,
              logger = logger)
            
            # If this isn't the last chain, remove the (0, 1) entry
            if chainIndex < (chainCount - 1):
                if chainFeatures[-1].featureSetting == (0, 1):
                    del chainFeatures[-1]
            
            r.features.extend(chainFeatures)

            newTables = []
            for subtableIndex in range(subtableCount):
                if w.length() < 4:
                    logger.error((
                      'V0731',
                      (subtableIndex,),
                      "The header for subtable %d is missing or incomplete."))
                    
                    return None
                
                subtableLength = w.unpack("L")
                
                if subtableLength < 12:
                    logger.error((
                      'V0732',
                      (subtableLength,),
                      "The subtable length is %d, which is too small."))
                    
                    return None
                
                logger.debug((
                  'V0909',
                  (chainIndex, subtableIndex, subtableLength),
                  "Chain %d, subtable %d has length %d"))
                
                cov = coverage.Coverage.fromvalidatedwalker(
                  w,
                  logger = logger.getChild("subtable %d" % (subtableIndex,)),
                  **kwArgs)
                
                if cov is None:
                    return None
                
                if w.length() < 4:
                    logger.error((
                      'V0731',
                      (subtableIndex,),
                      "The header for subtable %d is missing or incomplete."))
                    
                    return None
                
                mask = w.unpack("L") << extraShift
                
                wSub = w.subWalker(
                  0,
                  relative = True,
                  newLimit = subtableLength - 12)
                
                w.skip(subtableLength - 12)
                maker = _makers_validated[cov.kind]
                
                newTable = maker(
                  wSub,
                  coverage = cov,
                  maskValue = mask,
                  logger = logger.getChild("subtable %d" % (subtableIndex,)),
                  **kwArgs)
                
                if newTable is None:
                    return None
                
                newTables.append(newTable)

            if version == 0x30000:
                subtableGlyphCoverageSets = \
                    SubTableGlyphCoverageSets.fromwalker(
                        w, subtableCount, **kwArgs)

                for i, subtableGlyphCoverageSet in enumerate(subtableGlyphCoverageSets):
                    gatheredInputGlyphs = newTables[i].gatheredInputGlyphs()
                    if subtableGlyphCoverageSet.difference(gatheredInputGlyphs):
                        logger.warning((
                            'V1063',
                            (i,),
                            "The glyph coverage set for subtable %d contains glyphs that are not used for input in the subtable."))
                    newTables[i].glyphCoverageSet = subtableGlyphCoverageSet

            for newTable in newTables:
                r.append(newTable)

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        version, chainCount = w.unpack("2L")
        
        if version not in {0x20000, 0x30000}:
            raise ValueError("Unknown 'morx' version: 0x%08X" % (version,))
        
        r = cls(
            originalVersion = version,
            preferredVersion = version)
        kwArgs.pop('coverage', None)
        kwArgs.pop('maskValue', None)
        
        for chainIndex in range(chainCount):
            extraShift = 32 * chainIndex
            chainDefFlags, flagCount, numSubtables = w.unpack("L4x2L")
            r.defaultFlags |= (chainDefFlags << extraShift)
            
            chainFeatures = features.Features.fromwalker(
              w,
              count = flagCount,
              extraShift = extraShift)
            
            # If this isn't the last chain, remove the (0, 1) entry
            if chainIndex < (chainCount - 1):
                assert chainFeatures[-1].featureSetting == (0, 1)
                del chainFeatures[-1]
            
            r.features.extend(chainFeatures)

            newTables = []
            subtableCount = numSubtables
            while subtableCount:
                subtableLength = w.unpack("L")
                cov = coverage.Coverage.fromwalker(w, **kwArgs)
                mask = w.unpack("L") << extraShift
                
                wSub = w.subWalker(
                  0,
                  relative = True,
                  newLimit = subtableLength - 12)
                
                w.skip(subtableLength - 12)
                maker = _makers[cov.kind]
                newTable = maker(wSub, coverage=cov, maskValue=mask, **kwArgs)
                newTables.append(newTable)
                subtableCount -= 1

            if version == 0x30000:
                subtableGlyphCoverageSets = \
                    SubTableGlyphCoverageSets.fromwalker(
                        w, numSubtables, **kwArgs)

                for i, subtableGlyphCoverageSet in enumerate(subtableGlyphCoverageSets):
                    newTables[i].glyphCoverageSet = subtableGlyphCoverageSet

            for newTable in newTables:
                r.append(newTable)

        return r
    
    def run(self, glyphArray, **kwArgs):
        """
        """
        
        # For now just run all subtables; add flag sensitivity next...
        
        if not isinstance(glyphArray[0], tuple):
            glyphArray = list(enumerate(glyphArray))
        
        nm = kwArgs.get('namer', None)
        nmbf = (str if nm is None else nm.bestNameForGlyphIndex)
        bads = frozenset([0xFFFF, 0xFFFE, None])
        f = lambda g: "None" if g in bads else nmbf(g)
        s = ', '.join(f(t[1]) for t in glyphArray)
        print("Initial array: [%s]" % (s,))
        print()
        
        for subtableIndex, subtable in enumerate(self):
            glyphArray = subtable.run(glyphArray, **kwArgs)
            s = ', '.join(f(t[1]) for t in glyphArray)
            print("After subtable %d: [%s]" % (subtableIndex, s))
            print()

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _makeGSUB():
        from fontio3.GSUB import GSUB, ligature, ligature_glyphtuple
        
        from fontio3.opentype import (
          featuredict,
          featuretable,
          langsys,
          langsys_optfeatset,
          langsysdict,
          lookup,
          scriptdict)
        
        # Return a GSUB with a b'liga' feature (20, 30) -> 40
        ligGTObj = ligature_glyphtuple.Ligature_GlyphTuple((20, 30))
        ligObj = ligature.Ligature({ligGTObj: 40}, keyOrder=[ligGTObj])
        lkObj = lookup.Lookup([ligObj])
        ftObj = featuretable.FeatureTable([lkObj])
        featObj = featuredict.FeatureDict({b'liga0001': ftObj})
        
        optSetObj = langsys_optfeatset.OptFeatSet({b'liga0001'})
        lsObj = langsys.LangSys(optionalFeatures=optSetObj)
        lsdObj = langsysdict.LangSysDict({}, defaultLangSys=lsObj)
        scptObj = scriptdict.ScriptDict({b'latn': lsdObj})
        return GSUB.GSUB(features=featObj, scripts=scptObj)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
