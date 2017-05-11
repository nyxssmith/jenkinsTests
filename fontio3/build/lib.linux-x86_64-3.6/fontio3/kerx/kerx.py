#
# kerx.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'kerx' tables.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.kerx import (
  coverage,
  format0,
  format1,
  format2,
  format3,
  format4,
  gposconverter)

from fontio3.statetables.subtable_glyph_coverage_sets import \
    SubTableGlyphCoverageSets

# -----------------------------------------------------------------------------

#
# Private constants
#

_makers = {
  0: format0.Format0.fromwalker,
  1: format1.Format1.fromwalker,
  2: format2.Format2.fromwalker,
  3: format3.Format3.fromwalker,
  4: format4.Format4.fromwalker}

_makers_validated = {
  0: format0.Format0.fromvalidatedwalker,
  1: format1.Format1.fromvalidatedwalker,
  2: format2.Format2.fromvalidatedwalker,
  # 3: format3.Format3.fromvalidatedwalker,
  4: format4.Format4.fromvalidatedwalker}

# -----------------------------------------------------------------------------

#
# Classes
#

class Kerx(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'kerx' tables. These are lists of individual
    kerning subtable objects (Format0, Format1, etc.)
    
    >>> _testingValues[1].pprint()
    Subtable #1 (format 0):
      GlyphPair((14, 23)): -25
      GlyphPair((14, 96)): -30
      GlyphPair((18, 38)): 12
      Header information:
        Horizontal
        With-stream
        No variation kerning
        Process forward
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Subtable #1 (format 0):
      (xyz15, afii60001): -30
      (xyz15, xyz24): -25
      (xyz19, xyz39): 12
      Header information:
        Horizontal
        With-stream
        No variation kerning
        Process forward
    
    >>> _testingValues[2].pprint()
    Subtable #1 (format 2):
      ClassPair((1, 1)): -25
      ClassPair((1, 2)): -10
      ClassPair((2, 1)): 15
      Left-hand classes:
        15: 1
        25: 1
        35: 2
      Right-hand classes:
        9: 1
        12: 1
        15: 1
        40: 2
      Header information:
        Horizontal
        With-stream
        No variation kerning
        Process forward
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda i, obj: "Subtable #%d (format %d)" % (i + 1, obj.format)),
        item_pprintlabelfuncneedsobj = True,
        seq_compactremovesfalses = True)

    attrSpec = dict(
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

    attrSorted = ('preferredVersion', 'originalVersion')

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Kerx object to the specified LinkedWriter.
        The keyword arguments are:
        
            addSentinel     Set to True to cause (where appropriate) subtables
                            to have the (0xFFFF, 0xFFFF, 0) sentinel added at
                            the end (note this does not affect the subtable's
                            count of numPairs or whatever).
            
            stakeValue      The stake value to be used at the start of this
                            output.

        >>> h = utilities.hexdump
        >>> obj = _testingValues[1]
        >>> h(obj.binaryString())
               0 | 0002 0000 0000 0001  0000 002E 0000 0000 |................|
              10 | 0000 0000 0000 0003  0000 000C 0000 0001 |................|
              20 | 0000 0006 000E 0017  FFE7 000E 0060 FFE2 |.............`..|
              30 | 0012 0026 000C                           |...&..          |
        >>> h(obj.binaryString(addSentinel=True))
               0 | 0002 0000 0000 0001  0000 0034 0000 0000 |...........4....|
              10 | 0000 0000 0000 0003  0000 000C 0000 0001 |................|
              20 | 0000 0006 000E 0017  FFE7 000E 0060 FFE2 |.............`..|
              30 | 0012 0026 000C FFFF  FFFF 0000           |...&........    |
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
        w.add("2L", version, len(self))

        for subtable in self:
            startLength = w.byteLength
            lengthStake = w.addDeferredValue("L")
            subtable.coverage.buildBinary(w)
            w.add("BL", subtable.format, (subtable.tupleIndex or 0))
            subtable.buildBinary(w, **kwArgs)
            
            w.setDeferredValue(
              lengthStake,
              "L",
              int(w.byteLength - startLength))

        if version == 0x00030000:
            glyphCoverageSets = SubTableGlyphCoverageSets(
                [subtable.glyphCoverageSet for subtable in self])
            glyphCoverageSets.buildBinary(w, isKerx=True, **kwArgs)

    @classmethod
    def fromGPOS(cls, gposObj, scriptTag, **kwArgs):
        """
        Creates and returns a new Kerx object from the specified GPOS object
        for the specified script. The Lookup order will be preserved as the
        subtable order in the new Kerx object.
        
        The following keyword arguments are supported:
        
            backMap     If a dict is passed in as this keyword argument, it
                        will be filled with a mapping from GPOS feature tag to
                        sets of Kerx indices.
            
            langSys     A 4-byte bytestring representing the langSys to be
                        converted in the specified script. If this value is not
                        specified, the defaultLangSys will be used; if the
                        specified script does not have any features in the
                        defaultLangSys then an empty Kerx object will be
                        returned.
        
        ### gposObj = _makeGPOS()
        ### gposObj.pprint()
        Features:
          Feature 'kern0001':
            Lookup 0:
              Subtable 0 (Pair (glyph) positioning table):
                Key((15, 32)):
                  Second adjustment:
                    FUnit adjustment to origin's x-coordinate: -18
                Key((20, 30)):
                  Second adjustment:
                    FUnit adjustment to origin's x-coordinate: 14
              Lookup flags:
                Right-to-left for Cursive: False
                Ignore base glyphs: False
                Ignore ligatures: False
                Ignore marks: False
              Sequence order (lower happens first): 0
        Scripts:
          Script object latn:
            Default LangSys object:
              Optional feature tags:
                kern0001
        
        ### e = utilities.fakeEditor(0x100)
        ### k = Kerx.fromGPOS(gposObj, b'latn', editor=e)
        ### k.pprint()
        Subtable #1 (format 0):
          GlyphPair((15, 32)): -18
          GlyphPair((20, 30)): 14
          Header information:
            Horizontal
            With-stream
            No variation kerning
            Process forward
        """
        
        r = cls()
        
        if scriptTag not in gposObj.scripts:
            return r
        
        lsdObj = gposObj.scripts[scriptTag]
        ls = kwArgs.pop('langSys', None)
        
        if ls is None:
            lsObj = lsdObj.defaultLangSys
        elif ls in lsdObj:
            lsObj = lsdObj[ls]
        else:
            return r
        
        if lsObj.requiredFeature:
            allFeats = {lsObj.requiredFeature}
        else:
            allFeats = set(lsObj.optionalFeatures)
        
        # At this point we have all the needed feature tags. Now we need to
        # retrieve the Feature objects so we can ascertain the ordering.
        
        featDict = gposObj.features
        orderDict = {}
        
        for featTag in allFeats:
            featObj = featDict[featTag]
            
            for lkupIndex, lkupObj in enumerate(featObj):
                orderDict[(featTag, lkupIndex)] = lkupObj.sequence
        
        # Now we're ready to start converting, and additionally filling in the
        # backmap (or a throwaway local version, if one wasn't specified).
        
        it = sorted(orderDict.items(), key=operator.itemgetter(1))
        backMap = kwArgs.pop('backMap', {})
        
        for (featTag, lkupIndex), sequence in it:
            lkupObj = featDict[featTag][lkupIndex]
            
            for subObj in lkupObj:
                gTuples, eTuples = subObj.effects(**kwArgs)
                v = gposconverter.analyze(gTuples, eTuples, **kwArgs)
        
                rg = range(len(r), len(r) + len(v))
                backMap.setdefault(featTag, set()).update(rg)
                r.extend(v)
        
        return r
    
    @classmethod
    def fromkern(cls, k, **kwArgs):
        """
        Creates and returns a new Kerx object from the specified Kern object.
        """
        
        def _it():
            for oldTable in k:
                if oldTable.format == 0:
                    yield format0.Format0.fromkern_format0(oldTable)
                elif oldTable.format == 1:
                    yield format1.Format1.fromkern_format1(oldTable)
                else:
                    raise ValueError("Unknown old 'kern' subtable format!")
        
        return cls(_it())
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Kerx object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Kerx.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.kerx - DEBUG - Walker has 54 remaining bytes.
        fvw.kerx.subtable 0.format0 - DEBUG - Walker has 34 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.kerx - DEBUG - Walker has 1 remaining bytes.
        fvw.kerx - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("kerx")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, numTables = w.unpack("2L")

        if version not in {0x20000, 0x30000}:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00020000 or 0x00030000 but got 0x%08X."))
            
            return None
        
        r = cls(
            [None] * numTables,
            originalVersion=version,
            preferredVersion=version)

        kwArgs.pop('tupleIndex', None)
        kwArgs.pop('coverage', None)

        newTables = []
        for i in range(numTables):
            itemLogger = logger.getChild("subtable %d" % (i,))
            
            if w.length() < 4:
                itemLogger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            byteLength = w.unpack("L") - 12 # i.e. what's left after the header
            cov = coverage.Coverage.fromvalidatedwalker(w, logger=itemLogger)
            
            if cov is None:
                return None
            
            if w.length() < 5:
                itemLogger.error((
                  'V0790',
                  (),
                  "The coverage and tupleIndex are missing or incomplete."))
                
                return None
            
            format, tupleIndex = w.unpack("BL")
            
            if format not in _makers_validated:
                itemLogger.error((
                  'V0791',
                  (format,),
                  "Subtable format %d is not valid."))
                
                return None
            
            wSub = w.subWalker(0, relative=True, newLimit=byteLength)
            
            thisSubtable = _makers_validated[format](
              wSub,
              coverage = cov,
              tupleIndex = tupleIndex,
              logger = itemLogger,
              **kwArgs)
            
            if thisSubtable is None:
                return None
            
            newTables.append(thisSubtable)
            w.skip(byteLength)

        if version == 0x30000:
            subtableGlyphCoverageSets = SubTableGlyphCoverageSets.fromwalker(
                w, numTables, **kwArgs)
            for i, thisSubtable in enumerate(newTables):
                thisSubtable.glyphCoverageSet = subtableGlyphCoverageSets[i]

        for i, thisSubtable in enumerate(newTables):
            r[i] = thisSubtable

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Kerx object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Kerx.frombytes(obj.binaryString())
        True
        """
        
        version, numTables = w.unpack("2L")
        
        if version not in {0x20000, 0x30000}:
            raise ValueError("Unknown 'kerx' version: 0x%08X!" % (version,))
        
        r = cls(
            [None] * numTables,
            originalVersion=version,
            preferredVersion=version)
        kwArgs.pop('tupleIndex', None)
        kwArgs.pop('coverage', None)

        newTables = []
        for i in range(numTables):
            byteLength = w.unpack("L") - 12  # i.e. what's left after header
            cov = coverage.Coverage.fromwalker(w)
            format, tupleIndex = w.unpack("BL")
            
            if format not in _makers:
                
                raise ValueError(
                  "Unknown 'kerx' subtable format: %d" % (format,))
            
            wSub = w.subWalker(0, relative=True, newLimit=byteLength)
            
            thisSubtable = _makers[format](
              wSub,
              coverage = cov,
              tupleIndex = tupleIndex,
              **kwArgs)

            newTables.append(thisSubtable)
            w.skip(byteLength)

        if version == 0x30000:
            subtableGlyphCoverageSets = SubTableGlyphCoverageSets.fromwalker(
                w, numTables, **kwArgs)
            for i, thisSubtable in enumerate(newTables):
                thisSubtable.glyphCoverageSet = subtableGlyphCoverageSets[i]

        for i, thisSubtable in enumerate(newTables):
            r[i] = thisSubtable

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
    
    def _makeGPOS():
        from fontio3.GPOS import (
          GPOS,
          pairglyphs,
          pairglyphs_key,
          pairvalues,
          value)
        
        from fontio3.opentype import (
          featuredict,
          featuretable,
          langsys,
          langsys_optfeatset,
          langsysdict,
          lookup,
          scriptdict)
        
        # Return a GPOS with (15, 32) kerned -18, and (20, 30) kerned +14
        v1 = value.Value(xPlacement=-18)
        v2 = value.Value(xPlacement=14)
        pv1 = pairvalues.PairValues(second=v1)
        pv2 = pairvalues.PairValues(second=v2)
        k1 = pairglyphs_key.Key((15, 32))
        k2 = pairglyphs_key.Key((20, 30))
        pairObj = pairglyphs.PairGlyphs({k1: pv1, k2: pv2})
        lkObj = lookup.Lookup([pairObj])
        ftObj = featuretable.FeatureTable([lkObj])
        featObj = featuredict.FeatureDict({b'kern0001': ftObj})
        
        optSetObj = langsys_optfeatset.OptFeatSet({b'kern0001'})
        lsObj = langsys.LangSys(optionalFeatures=optSetObj)
        lsdObj = langsysdict.LangSysDict({}, defaultLangSys=lsObj)
        scptObj = scriptdict.ScriptDict({b'latn': lsdObj})
        return GPOS.GPOS(features=featObj, scripts=scptObj)
    
    _f0tv = format0._testingValues
    _f2tv = format2._testingValues
    
    _testingValues = (
        Kerx([]),
        Kerx([_f0tv[1]]),
        Kerx([_f2tv[1]]))
    
    del _f0tv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
