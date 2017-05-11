#
# pscontextclass.py
#
# Copyright © 2009-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 (class) contextual tables, both GPOS and GSUB.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
  classdef,
  coverage,
  coverageset,
  coverageutilities,
  glyphset,
  pscontextclass_key,
  pslookupgroup,
  pslookuprecord)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _canRemove(d, key, **kwArgs):
    # First, validate the Key.
    present = set(d.classDef.values())
    
    if any(i not in present for i in key):
        return True
    
    # Second, validate the record
    if not d[key]:
        return True
    
    return False

def _keySort(k):
    return (k[0], k.ruleOrder) + tuple(k[1:])

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    # Do a length check to guarantee no sequenceIndex refers to a value outside
    # the range actually present in the associated Key.
    
    for key, group in obj.items():
        for effectIndex, effect in enumerate(group):
            n = effect.sequenceIndex
            
            if n != int(n) or n < 0 or n >= len(key):
                logger.error((
                  'V0361',
                  (effectIndex, key, len(key) - 1, n),
                  "Effect %d of key %s should have a sequenceIndex from 0 "
                  "through %d, but the value is %s."))
                
                r = False
    
    # Make sure all classes defined in all Keys are actually represented in the
    # classDef, and that there are no unused class indices in the classDef.
    
    present = set(obj.classDef.values()) | {0}
    found = set()
    
    for key in obj:
        inThisKey = set(key)
        notInClass = inThisKey - present
        
        if notInClass:
            logger.error((
              'V0376',
              (sorted(notInClass), key),
              "The classes %s in key %s do not appear in the ClassDef."))
            
            r = False
        
        found.update(inThisKey - notInClass)
    
    notInKeys = (present - found) - {0}
    
    if notInKeys:
        logger.warning((
          'V0377',
          (sorted(notInKeys),),
          "The class index values %s are not used in any Key."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PSContextClass(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 2 contextual lookups. Note that these work for
    both GPOS and GSUB tables.
    
    These are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Key((1, 2, 1), ruleOrder=0):
      Effect #1:
        Sequence index: 1
        Lookup:
          Subtable 0 (Single substitution table):
            xyz31: xyz76
            xyz32: xyz77
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 23
    Key((3, 2), ruleOrder=0):
      Effect #1:
        Sequence index: 1
        Lookup:
          Subtable 0 (Single substitution table):
            xyz31: xyz51
            xyz32: xyz52
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 22
    Class definition table:
      xyz21: 1
      xyz22: 1
      xyz23: 1
      xyz31: 2
      xyz32: 2
      xyz41: 3
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresortfunc = _keySort,
        map_compactiblefunc = (lambda d, k, **kw: False),
        #map_compactiblefunc = _canRemove,
        map_maxcontextfunc = (lambda d: utilities.safeMax(len(k) for k in d)),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        classDef = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table"),
        
        coverageExtras = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = glyphset.GlyphSet,
            attr_label = "Coverage glyphs not in ClassDef",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def __iter__(self):
        """
        We provide a custom iterator to make sure the ruleOrder is correctly
        being followed.
        
        >>> for k in _testingValues[1]: print(k)
        (1, 2, 1), Relative order = 0
        (3, 2), Relative order = 0
        """
        
        v = list(super(PSContextClass, self).__iter__())
        return iter(sorted(v, key=_keySort))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PSContextClass to the specified
        LinkedWriter.
        
        NOTE! There will be unresolved lookup list indices in the LinkedWriter
        after this method is finished. The caller (or somewhere higher up) is
        responsible for adding an index map to the LinkedWriter with the tag
        "lookupList_GPOS" or "lookupList_GSUB" before the LinkedWriter's
        binaryString() method is called.
        
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 + (k[0] == 1) for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> utilities.hexdump(w.binaryString())
               0 | 0002 0010 001C 0004  0000 0032 0000 0036 |...........2...6|
              10 | 0001 0004 0014 0015  0016 0028 0002 0003 |...........(....|
              20 | 0014 0016 0001 001E  001F 0002 0028 0028 |.............(.(|
              30 | 0003 0001 0008 0001  0010 0003 0001 0002 |................|
              40 | 0001 0001 0017 0002  0001 0002 0001 0016 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 2)  # format
        classToGlyphs = utilities.invertDictFull(self.classDef, asSets=True)
        firstClasses = set(k[0] for k in self)
        firstGlyphs = {g for c in firstClasses for g in classToGlyphs[c]}
        s = firstGlyphs | self.coverageExtras
        covTable = coverage.Coverage.fromglyphset(s)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        classStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, classStake)
        count = utilities.safeMax(firstClasses, -1) + 1
        w.add("H", count)
        
        setStakes = dict(
          (firstClass, w.getNewStake())
          for firstClass in firstClasses)
        
        for firstClass in range(count):
            if firstClass in firstClasses:
                w.addUnresolvedOffset("H", stakeValue, setStakes[firstClass])
            else:
                w.add("H", 0)
        
        covTable.buildBinary(w, stakeValue=covStake)
        self.classDef.buildBinary(w, stakeValue=classStake)
        orderings = {}
        firstClasses = sorted(firstClasses)
        ruleStakes = {}
        
        for firstClass in firstClasses:
            w.stakeCurrentWithValue(setStakes[firstClass])
            
            o = orderings[firstClass] = sorted(
              (k.ruleOrder, k)
              for k in self
              if k[0] == firstClass)
            
            w.add("H", len(o))
            
            for order, key in o:
                stake = ruleStakes[(firstClass, order)] = w.getNewStake()
                w.addUnresolvedOffset("H", setStakes[firstClass], stake)
        
        for firstClass in firstClasses:
            for order, key in orderings[firstClass]:
                w.stakeCurrentWithValue(ruleStakes[(firstClass, order)])
                obj = self[key]
                w.add("HH", len(key), len(obj))
                w.addGroup("H", key[1:])
                obj.buildBinary(w, **kwArgs)


    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PSContextClass from the specified
        FontWorkerSource, with source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSContextClass.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger = logger,
        ...   editor={})
        FW_test.pscontextclass - WARNING - line 8 -- unexpected token: foo
        FW_test.pscontextclass - WARNING - line 10 -- invalid class: 4
        FW_test.pscontextclass - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        FW_test.pscontextclass - INFO - The following glyphs appear in the Coverage and the ClassDef: [2, 3, 5]
        FW_test.pscontextclass - ERROR - Key uses class zero, but there are no extra glyphs in the coverage set.
        >>> obj.pprint()
        Key((0, 1, 2, 3), ruleOrder=0):
          Effect #1:
            Sequence index: 0
            Lookup:
              3:
                FUnit adjustment to horizontal advance: 678
          Effect #2:
            Sequence index: 0
            Lookup:
              3:
                FUnit adjustment to horizontal advance: 901
        Class definition table:
          2: 1
          3: 2
          5: 3
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pscontextclass")
        terminalStrings = ('subtable end', 'lookup end')
        classDef = classdef.ClassDef() # place-holder
        lookupGroups = {}
        ruleOrders = {}
        startingLineNumber = fws.lineNumber
        fVFWS = classdef.ClassDef.fromValidatedFontWorkerSource
        
        for line in fws:
            if line.lower() in terminalStrings:
                r = cls(lookupGroups, classDef=classDef)

                covTable = coverage.Coverage.fromglyphset(classDef.keys())
                okToProceed, covSet = coverageutilities.reconcile(
                  covTable,
                  r,
                  [classDef],
                  logger = logger,
                  loggerprefix = "line %d -- " % (fws.lineNumber,),
                  **kwArgs)
                r.coverageExtras.update(covSet - set(classDef))

                return r
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() == 'class definition begin':
                    classDef = fVFWS(fws, logger=logger, **kwArgs)
                
                elif tokens[0].lower() == 'class':
                    classesOK = True
                    classList = [int(x) for x in tokens[1].split(',')]
                    
                    for classNum in classList:
                        if classNum == 0:
                            continue
                        
                        if not classNum in list(classDef.values()):
                            logger.warning((
                              'V0962',
                              (fws.lineNumber, classNum),
                              'line %d -- invalid class: %d'))
                            
                            classesOK = False
                    
                    if not classesOK:
                        continue

                    classTuple = tuple(classList)
                    ruleOrder = ruleOrders.get(classTuple[0],0)
                    lookupList = []
                    
                    for effect in tokens[2:]:
                        effectTokens = [x.strip() for x in effect.split(',')]
                        sequenceIndex = int(effectTokens[0]) - 1
                        lookupName = effectTokens[1]
                        
                        lookupList.append(
                          pslookuprecord.PSLookupRecord(
                            sequenceIndex,
                            lookup.Lookup.fromValidatedFontWorkerSource(
                              fws,
                              lookupName,
                              logger = logger,
                              **kwArgs)))
                    
                    key = pscontextclass_key.Key(classTuple)
                    key.ruleOrder = ruleOrder
                    ruleOrders[classTuple[0]] = ruleOrder + 1
                    lookupGroup = pslookupgroup.PSLookupGroup(lookupList)
                    lookupGroups[key] = lookupGroup
                
                else:
                    logger.warning((
                      'V0960',
                      (fws.lineNumber, tokens[0]),
                      'line %d -- unexpected token: %s'))
                
        logger.warning((
          'V0958',
          (startingLineNumber, "/".join(terminalStrings)),
          "line %d -- did not find matching '%s'"))

        r = cls(lookupGroups, classDef=classDef)

        covTable = coverage.Coverage.fromglyphset(
          [g for g in classDef])
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          r,
          [classDef],
          logger = logger,
          **kwArgs)
        r.coverageExtras.update(covSet - set(classDef))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSContextClass object from the specified
        walker, doing source validation. The following keyword arguments are
        supported:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromvalidatedwalker(). The fixup call takes
                        one argument: the Lookup being set into it.
            
            logger      A logger to which messages will be posted.
        
        >>> logger = utilities.makeDoctestLogger("pscontextclass_test")
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 + (k[0] == 1) for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> fvb = PSContextClass.fromvalidatedbytes
        >>> obj2 = fvb(s, fixupList=FL, logger=logger)
        pscontextclass_test.pscontextclass - DEBUG - Walker has 80 remaining bytes.
        pscontextclass_test.pscontextclass - DEBUG - Format is 2
        pscontextclass_test.pscontextclass.coverage - DEBUG - Walker has 64 remaining bytes.
        pscontextclass_test.pscontextclass.coverage - DEBUG - Format is 1, count is 4
        pscontextclass_test.pscontextclass.coverage - DEBUG - Raw data are [20, 21, 22, 40]
        pscontextclass_test.pscontextclass.classDef - DEBUG - Walker has 52 remaining bytes.
        pscontextclass_test.pscontextclass.classDef - DEBUG - ClassDef is format 2.
        pscontextclass_test.pscontextclass.classDef - DEBUG - Count is 3
        pscontextclass_test.pscontextclass.classDef - DEBUG - Raw data are [(20, 22, 1), (30, 31, 2), (40, 40, 3)]
        pscontextclass_test.pscontextclass - DEBUG - Number of ClassSets is 4
        pscontextclass_test.pscontextclass - DEBUG - ClassSet offsets are (0, 50, 0, 54)
        pscontextclass_test.pscontextclass.class index 1 - DEBUG - Rule count is 1
        pscontextclass_test.pscontextclass.class index 1 - DEBUG - Rule offsets are (8,)
        pscontextclass_test.pscontextclass.class index 1.rule set 0 - DEBUG - Glyph count is 3
        pscontextclass_test.pscontextclass.class index 1.rule set 0 - DEBUG - Action count is 1
        pscontextclass_test.pscontextclass.class index 1.rule set 0.pslookupgroup - DEBUG - Walker has 14 bytes remaining.
        pscontextclass_test.pscontextclass.class index 1.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 14 remaining bytes.
        pscontextclass_test.pscontextclass.class index 1.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 1
        pscontextclass_test.pscontextclass.class index 1.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 23
        pscontextclass_test.pscontextclass.class index 3 - DEBUG - Rule count is 1
        pscontextclass_test.pscontextclass.class index 3 - DEBUG - Rule offsets are (16,)
        pscontextclass_test.pscontextclass.class index 3.rule set 0 - DEBUG - Glyph count is 2
        pscontextclass_test.pscontextclass.class index 3.rule set 0 - DEBUG - Action count is 1
        pscontextclass_test.pscontextclass.class index 3.rule set 0.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pscontextclass_test.pscontextclass.class index 3.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pscontextclass_test.pscontextclass.class index 3.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 1
        pscontextclass_test.pscontextclass.class index 3.rule set 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 22
        pscontextclass_test.pscontextclass - INFO - The following glyphs appear only in the ClassDef and are not present in the Coverage: [30, 31]
        pscontextclass_test.pscontextclass - INFO - The following glyphs appear in the Coverage and the ClassDef: [20, 21, 22, 40]
        >>> d = {22 + (k[0] == 1): obj[k][0].lookup for k in obj}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == obj2
        True
        
        >>> fvb(s[:5], fixupList=FL, logger=logger)
        pscontextclass_test.pscontextclass - DEBUG - Walker has 5 remaining bytes.
        pscontextclass_test.pscontextclass - ERROR - Insufficient bytes.
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pscontextclass")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 2:
            logger.error((
              'V0002',
              (format,),
              "Expected format 2, but got format %d instead."))
            
            return None
        
        logger.debug(('Vxxxx', (), "Format is 2"))
        
        covOffset = w.unpack("H")
        
        if not covOffset:
            logger.error((
              'V0330',
              (),
              "The offset to the Coverage is zero."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger)
        
        if covTable is None:
            return None
        
        classDef = classdef.ClassDef.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger)
        
        if classDef is None:
            return None
        
        r = cls({}, classDef=classDef)
        count = w.unpack("H")
        logger.debug(('Vxxxx', (count,), "Number of ClassSets is %d"))
        
        if w.length() < 2 * count:
            logger.error((
              'V0356',
              (),
              "The offsets to the ClassSets are missing or incomplete."))
            
            return None
        
        offsets = w.group("H", count)
        logger.debug(('Vxxxx', (offsets,), "ClassSet offsets are %s"))
        fvw = pslookupgroup.PSLookupGroup.fromvalidatedwalker
        Key = pscontextclass_key.Key
        
        for classIndex, offset in enumerate(offsets):
            if not offset:
                continue
            
            subLogger = logger.getChild("class index %d" % (classIndex,))
            wSet = w.subWalker(offset)
            
            if wSet.length() < 2:
                subLogger.error((
                  'V0357',
                  (),
                  "The ClassRuleCount is missing or incomplete."))
                
                return None
            
            ruleCount = wSet.unpack("H")
            subLogger.debug(('Vxxxx', (ruleCount,), "Rule count is %d"))
            
            if wSet.length() < 2 * ruleCount:
                subLogger.error((
                  'V0358',
                  (),
                  "The ClassRule offsets are missing or incomplete."))
                
                return None
            
            ruleOffsets = wSet.group("H", ruleCount)
            subLogger.debug(('Vxxxx', (ruleOffsets,), "Rule offsets are %s"))
            
            for ruleOrder, ruleOffset in enumerate(ruleOffsets):
                subLogger2 = subLogger.getChild("rule set %d" % (ruleOrder,))
                wRule = wSet.subWalker(ruleOffset)
                
                if wRule.length() < 4:
                    subLogger2.error((
                      'V0359',
                      (),
                      "The ClassRule header is incomplete."))
                    
                    return None
                
                glyphCount, posCount = wRule.unpack("2H")
                subLogger2.debug(('Vxxxx', (glyphCount,), "Glyph count is %d"))
                subLogger2.debug(('Vxxxx', (posCount,), "Action count is %d"))
                
                if wRule.length() < 2 * (glyphCount - 1):
                    subLogger2.error((
                      'V0354',
                      (),
                      "ClassRule is missing or only partially present."))
                    
                    return None
                
                key = Key(
                  (classIndex,) + wRule.group("H", glyphCount - 1),
                  ruleOrder = ruleOrder)
                
                obj = fvw(
                  wRule,
                  count = posCount,
                  fixupList = fixupList,
                  logger = subLogger2,
                  **kwArgs)
                
                if obj is None:
                    return None
                
                r[key] = obj
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          r,
          [classDef],
          logger = logger,
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(classDef))
        
        if not okToProceed:
            r.clear()
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSContextClass from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromwalker(). The fixup call takes one
                        argument: the Lookup being set into it.
        
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 + (k[0] == 1) for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> obj2 = PSContextClass.frombytes(s, fixupList=FL)
        >>> d = {22 + (k[0] == 1): obj[k][0].lookup for k in obj}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == obj2
        True
        """
        
        format = w.unpack("H")
        assert format == 2
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        cd = classdef.ClassDef.fromwalker(w.subWalker(w.unpack("H")))
        r = cls()
        r.classDef = cd
        firstOffsets = w.group("H", w.unpack("H"))
        f = pslookupgroup.PSLookupGroup.fromwalker
        fixupList = kwArgs['fixupList']
        Key = pscontextclass_key.Key
        
        for firstClassIndex, firstOffset in enumerate(firstOffsets):
            if firstOffset:
                wSet = w.subWalker(firstOffset)
                it = enumerate(wSet.group("H", wSet.unpack("H")))
                
                for ruleOrder, ruleOffset in it:
                    wRule = wSet.subWalker(ruleOffset)
                    glyphCount, posCount = wRule.unpack("2H")
                    
                    key = Key(
                      (firstClassIndex,) + wRule.group("H", glyphCount - 1),
                      ruleOrder=ruleOrder)
                    
                    r[key] = f(wRule, count=posCount, fixupList=fixupList)
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          r,
          [cd],
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(cd))
        
        if not okToProceed:
            r.clear()
        
        return r

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
        s.write("class definition begin\n")
        c_sorted = sorted(self.classDef, key=(lambda x: (self.classDef[x], x)))
        
        for k in c_sorted:
            v = self.classDef[k]
            s.write("%s\t%d\n" % (bnfgi(k), v))
        
        s.write("class definition end\n\n")
        
        for k in iter(self):
            v = self[k]
            classStr = ", ".join([str(ki) for ki in k])
            
            actionStr = "\t".join([
              "%d, %d" % (vi.sequenceIndex + 1, vi.lookup.sequence)
              for vi in v])
            
            s.write("class\t%s\t%s\n" % (classStr, actionStr))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import lookup
    from fontio3.utilities import namer, writer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    def _makeTV():
        from fontio3.GSUB import single
        
        cd = classdef.ClassDef({20: 1, 21: 1, 22: 1, 30: 2, 31: 2, 40: 3})
        key1 = pscontextclass_key.Key((3, 2), ruleOrder=0)
        key2 = pscontextclass_key.Key((1, 2, 1), ruleOrder=0)
        sgl1 = single.Single({30: 50, 31: 51})
        sgl2 = single.Single({30: 75, 31: 76})
        lkup1 = lookup.Lookup([sgl1], sequence=22)
        lkup2 = lookup.Lookup([sgl2], sequence=23)
        rec1 = pslookuprecord.PSLookupRecord(sequenceIndex=1, lookup=lkup1)
        rec2 = pslookuprecord.PSLookupRecord(sequenceIndex=1, lookup=lkup2)
        grp1 = pslookupgroup.PSLookupGroup([rec1])
        grp2 = pslookupgroup.PSLookupGroup([rec2])
        obj = PSContextClass({key1: grp1, key2: grp2}, classDef=cd)
        return obj
    
    _testingValues = (PSContextClass(), _makeTV())
    
    # FontWorker method test data
    
    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'F': 2,
        'period': 3,
        'quoteleft': 5
    }
    _test_FW_namer._initialized = True
    
    def _make_test_FW_lookupDict():
        from fontio3.GPOS import single, value
        
        S = single.Single
        V = value.Value
        
        return {
          'testSingle1': S({3: V(xAdvance=678)}),
          'testSingle2': S({3: V(xAdvance=901)})}
    
    _test_FW_lookupDict = _make_test_FW_lookupDict()

    _test_FW_fws = FontWorkerSource(StringIO(
        """
        class definition begin
        F	1
        period	2
        quoteleft	3
        class definition end
        
        class	0, 1, 2, 3	1,testSingle1	1,testSingle2

        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        class definition begin
        F	1
        period	2
        quoteleft	3
        class definition end
        
        foo
        class	0, 1, 2, 3	1,testSingle1	1,testSingle2
        class	0, 1, 2, 4	1,testSingle1	1,testSingle2

        """))
    

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
