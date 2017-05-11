#
# pschainclass.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 (class) chaining contextual tables, both GPOS and GSUB.
"""

# System imports
import functools
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
  pschainclass_classtuple,
  pschainclass_key,
  pslookupgroup,
  pslookuprecord)
    
# -----------------------------------------------------------------------------

#
# Private functions
#

def _canRemove(d, key, **kwArgs):
    # First, validate the Key.
    t = (d.classDefBacktrack, d.classDefInput, d.classDefLookahead)
    
    for k, cd in zip(key, t):
        present = set(cd.values())
        
        if any(i not in present for i in k):
            return True
    
    # Second, validate the record
    if not d[key]:
        return True
    
    return False

def _keySort(k):
    return (k[1][0], k.ruleOrder) + tuple(k[1][1:])

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    r = True
    
    # Do a length check to guarantee no sequenceIndex refers to a value outside
    # the range actually present in the associated Key.
    
    for key, group in obj.items():
        for effectIndex, effect in enumerate(group):
            n = effect.sequenceIndex
            
            if n != int(n) or n < 0 or n >= len(key[1]):
                logger.error((
                  'V0388',
                  (effectIndex, key, len(key[1]) - 1, n),
                  "Effect %d of key %s should have a sequenceIndex from 0 "
                  "through %d, but the value is %s."))
                
                r = False
    
    # Make sure all classes defined in all Keys are actually represented in the
    # classDefs, and that there are no unused class indices in the classDefs.
    
    cds = [obj.classDefBacktrack, obj.classDefInput, obj.classDefLookahead]
    labels = ["backtrack", "input", "lookahead"]
    
    for keyPart, cd in enumerate(cds):
        subLogger = logger.getChild(labels[keyPart])
        present = set(cd.values()) | {0}
        found = set()
        
        for key in obj:
            key = key[keyPart]
            inThisKey = set(key)
            notInClass = inThisKey - present
            
            if notInClass:
                subLogger.error((
                  'V0389',
                  (sorted(notInClass), key),
                  "The classes %s in key %s do not appear in the ClassDef."))
                
                r = False
            
            found.update(inThisKey - notInClass)
        
        notInKeys = (present - found) - {0}
        
        if notInKeys:
            subLogger.warning((
              'V0390',
              (sorted(notInKeys),),
              "The class index values %s are not used in any Key."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PSChainClass(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 2 chaining contextual lookups. Note that these
    work for both GPOS and GSUB tables.
    
    These are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Key((ClassTuple((1,)), ClassTuple((1, 2)), ClassTuple((1,))), ruleOrder=0):
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Single substitution table):
            xyz21: xyz41
            xyz22: xyz42
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 22
    Class definition table (backtrack):
      xyz11: 1
      xyz12: 1
    Class definition table (input):
      xyz21: 1
      xyz22: 1
      xyz23: 2
      xyz41: 3
      xyz42: 3
    Class definition table (lookahead):
      xyz31: 1
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresortfunc = (lambda obj: (obj[1][0], obj.ruleOrder)),
        map_compactiblefunc = (lambda d, k, **kw: False),
        #map_compactiblefunc = _canRemove,
        map_maxcontextfunc = (lambda d: utilities.safeMax(len(k) for k in d)),
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        classDefBacktrack = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table (backtrack)"),
        
        classDefInput = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table (input)"),
        
        classDefLookahead = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Class definition table (lookahead)"),
        
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
        ((1,), (1, 2), (1,)), Relative order = 0
        """
        
        v = list(super(PSChainClass, self).__iter__())
        return iter(sorted(v, key=_keySort))
        
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ContextClass to the specified
        LinkedWriter.
        
        NOTE! There will be unresolved lookup list indices in the LinkedWriter
        after this method is finished. The caller (or somewhere higher up) is
        responsible for adding an index map to the LinkedWriter with the tag
        "lookupList" before the LinkedWriter's binaryString() method is called.
        
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> utilities.hexdump(w.binaryString())
               0 | 0002 0014 001C 0026  003C 0004 0000 0044 |.......&.<.....D|
              10 | 0000 0000 0001 0002  0014 0015 0001 000A |................|
              20 | 0002 0001 0001 0002  0003 0014 0015 0001 |................|
              30 | 0016 0016 0002 0028  0029 0003 0001 001E |.......(.)......|
              40 | 0001 0001 0001 0004  0001 0001 0002 0002 |................|
              50 | 0001 0001 0001 0000  0016                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 2)  # format
        
        inputClassToGlyphs = utilities.invertDictFull(
          self.classDefInput,
          asSets = True)
        
        firstInputClasses = set(k[1][0] for k in self)
        firstInputClassesSorted = sorted(firstInputClasses)
        
        firstInputGlyphs = functools.reduce(
          set.union,
          (inputClassToGlyphs[c] for c in firstInputClasses))
        
        covTable = coverage.Coverage.fromglyphset(firstInputGlyphs)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        
        v = [
          self.classDefBacktrack,
          self.classDefInput,
          self.classDefLookahead]
        
        vImm = [(obj.asImmutable()[1] if obj else None) for obj in v]
        cdPool = {}
        objStakes = {}
        
        for cd, cdImm in zip(v, vImm):
            if len(cd):
                obj = cdPool.setdefault(cdImm, cd)
                
                objStake = objStakes.setdefault(
                  obj.asImmutable(),
                  w.getNewStake())
                
                w.addUnresolvedOffset("H", stakeValue, objStake)
            
            else:
                w.add("H", 0)
        
        count = utilities.safeMax(self.classDefInput.values(), -1) + 1
        w.add("H", count)
        
        setStakes = dict(
          (firstInputClass, w.getNewStake())
          for firstInputClass in firstInputClassesSorted)
        
        for firstInputClass in range(count):
            if firstInputClass in firstInputClasses:
                w.addUnresolvedOffset(
                  "H",
                  stakeValue,
                  setStakes[firstInputClass])
            
            else:
                w.add("H", 0)
        
        covTable.buildBinary(w, stakeValue=covStake)
        
        for cdImm in sorted(cdPool):  # sort to guarantee repeatable ordering
            obj = cdPool[cdImm]
            obj.buildBinary(w, stakeValue=objStakes[obj.asImmutable()])
        
        orderings = {}
        ruleStakes = {}
        
        for firstInputClass in firstInputClassesSorted:
            setStake = setStakes[firstInputClass]
            w.stakeCurrentWithValue(setStake)
            
            o = orderings[firstInputClass] = sorted(
              (k.ruleOrder, k[1], k)
              for k in self
              if k[1][0] == firstInputClass)
            
            w.add("H", len(o))
            
            for order, ignore, key in o:
                ruleStake = w.getNewStake()
                ruleStakes[(firstInputClass, order)] = ruleStake
                w.addUnresolvedOffset("H", setStake, ruleStake)
        
        for firstInputClass in firstInputClassesSorted:
            for order, ignore, key in orderings[firstInputClass]:
                w.stakeCurrentWithValue(ruleStakes[(firstInputClass, order)])
                obj = self[key]
                w.add("H", len(key[0]))
                w.addGroup("H", reversed(key[0]))
                w.add("H", len(key[1]))
                w.addGroup("H", key[1][1:])
                w.add("H", len(key[2]))
                w.addGroup("H", key[2])
                w.add("H", len(obj))
                obj.buildBinary(w, **kwArgs)


    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PSChainClass from the specified
        FontWorkerSource.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSChainClass.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger = logger,
        ...   editor = {})
        FW_test.pschainclass - WARNING - line 20 -- unexpected token: foo
        FW_test.pschainclass - WARNING - line 22 -- invalid backtrack class: 4
        FW_test.pschainclass - WARNING - line 22 -- invalid input class: 7
        FW_test.pschainclass - WARNING - line 22 -- invalid lookahead class: 6
        FW_test.pschainclass - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Key((ClassTuple((2, 1, 0)), ClassTuple((0, 5)), ClassTuple((7, 8, 9, 0))), ruleOrder=0):
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
        Class definition table (backtrack):
          1: 1
          2: 2
          3: 3
        Class definition table (input):
          1: 4
          2: 5
          3: 6
        Class definition table (lookahead):
          1: 7
          2: 8
          3: 9
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pschainclass")
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber = fws.lineNumber

        # place-holders
        classDefBacktrack = classdef.ClassDef()
        classDefInput = classdef.ClassDef()
        classDefLookahead = classdef.ClassDef()

        ruleOrders = {}
        lookupGroups = {}
        stringKeys = {}
        
        for line in fws:
            if line.lower() in terminalStrings:
                r = cls(
                  lookupGroups,
                  classDefBacktrack = classDefBacktrack,
                  classDefInput = classDefInput,
                  classDefLookahead = classDefLookahead)
                
                return r
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                fVFWS = classdef.ClassDef.fromValidatedFontWorkerSource
                
                if tokens[0].lower() == 'backtrackclass definition begin':
                    classDefBacktrack = fVFWS(fws, logger=logger, **kwArgs)
                    cdBackSet = set(classDefBacktrack.values())
                
                elif tokens[0].lower() == 'class definition begin':
                    classDefInput = fVFWS(fws, logger=logger, **kwArgs)
                    cdInputSet = set(classDefInput.values())
                
                elif tokens[0].lower() == 'lookaheadclass definition begin':
                    classDefLookahead = fVFWS(fws, logger=logger, dbg=True, **kwArgs)
                    cdLookSet = set(classDefLookahead.values())
                
                elif tokens[0].lower() == 'class-chain':
                    CT = pschainclass_classtuple.ClassTuple
                    classTuple1 = CT()
                    classTuple2 = CT()
                    classTuple3 = CT()
                    classesOK = True
                    
                    if tokens[1] != '':
                        try:
                            classList1 = [int(x) for x in tokens[1].split(',')]
                            classList1.reverse() # backtrack goes in reverse order
                        except:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, tokens[1]),
                              'line %d -- invalid backtrack definition: %s'))
                              
                            classesOK = False

                        for classNum in classList1:
                            if classNum == 0:
                                continue
                            
                            if not classNum in cdBackSet:
                                logger.warning((
                                  'V0962',
                                  (fws.lineNumber, classNum),
                                  'line %d -- invalid backtrack class: %d'))
                                
                                classesOK = False
                        
                        classTuple1 = CT(classList1)
                    
                    if tokens[2] != '':
                        try:
                            classList2 = [int(x) for x in tokens[2].split(',')]
                        except ValueError:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, tokens[2]),
                              'line %d -- invalid input definition: %s'))
                              
                            classesOK = False
                        
                        for classNum in classList2:
                            if classNum == 0:
                                continue
                            
                            if not classNum in cdInputSet:
                                logger.warning((
                                  'V0962',
                                  (fws.lineNumber, classNum),
                                  'line %d -- invalid input class: %d'))
                                
                                classesOK = False
                        
                        classTuple2 = CT(classList2)
                    
                    if tokens[3] != '':
                        try:
                            classList3 = [int(x) for x in tokens[3].split(',')]
                        except ValueError:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, tokens[3]),
                              'line %d -- invalid lookahead definition: %s'))
                            
                            classesOK = False
                        
                        for classNum in classList3:
                            if classNum == 0:
                                continue
                            
                            if not classNum in cdLookSet:
                                logger.warning((
                                  'V0962',
                                  (fws.lineNumber, classNum),
                                  'line %d -- invalid lookahead class: %d'))
                                
                                classesOK = False
                        
                        classTuple3 = CT(classList3)

                    if not classesOK:
                        continue

                    lookupList = []
                    
                    for effect in tokens[4:]:
                        effectTokens = [x.strip() for x in effect.split(',')]
                        sequenceIndex = int(effectTokens[0]) - 1
                        lookupName = effectTokens[1]
                        
                        lookupList.append(
                          pslookuprecord.PSLookupRecord(
                            sequenceIndex,
                            lookup.Lookup.fromValidatedFontWorkerSource(
                                fws,
                                lookupName,
                                logger=logger,
                                **kwArgs)))

                    stringKey = "(%s), (%s), (%s)" % (
                      ",".join([str(ci) for ci in classTuple1[::-1]]),
                      ",".join([str(ci) for ci in classTuple2]),
                      ",".join([str(ci) for ci in classTuple3]))

                    if stringKey in stringKeys:
                        logger.warning((
                          'Vxxxx',
                          (fws.lineNumber, stringKey, stringKeys[stringKey]),
                          "line %d -- context '%s' previously defined at line %d"))
                          
                    else:
                        stringKeys[stringKey] = fws.lineNumber

                        key = pschainclass_key.Key([
                            classTuple1,
                            classTuple2,
                            classTuple3])
                    
                        ruleOrder = ruleOrders.get(classTuple2[0], 0)
                        key.ruleOrder = ruleOrder
                        ruleOrders[classTuple2[0]] = ruleOrder + 1
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

        r = cls(
          lookupGroups,
          classDefBacktrack = classDefBacktrack,
          classDefInput = classDefInput,
          classDefLookahead = classDefLookahead)

        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSChainClass object from the specified
        walker, doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("pschainclass_test")
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> fvb = PSChainClass.fromvalidatedbytes
        >>> obj2 = fvb(s, fixupList=FL, logger=logger)
        pschainclass_test.pschainclass - DEBUG - Walker has 90 remaining bytes.
        pschainclass_test.pschainclass - DEBUG - Format is 2
        pschainclass_test.pschainclass.coverage - DEBUG - Walker has 70 remaining bytes.
        pschainclass_test.pschainclass.coverage - DEBUG - Format is 1, count is 2
        pschainclass_test.pschainclass.coverage - DEBUG - Raw data are [20, 21]
        pschainclass_test.pschainclass - DEBUG - Backtrack offset is 28
        pschainclass_test.pschainclass.classDef - DEBUG - Walker has 62 remaining bytes.
        pschainclass_test.pschainclass.classDef - DEBUG - ClassDef is format 1.
        pschainclass_test.pschainclass.classDef - DEBUG - First is 10, and count is 2
        pschainclass_test.pschainclass.classDef - DEBUG - Raw data are (1, 1)
        pschainclass_test.pschainclass - DEBUG - Input offset is 38
        pschainclass_test.pschainclass.classDef - DEBUG - Walker has 52 remaining bytes.
        pschainclass_test.pschainclass.classDef - DEBUG - ClassDef is format 2.
        pschainclass_test.pschainclass.classDef - DEBUG - Count is 3
        pschainclass_test.pschainclass.classDef - DEBUG - Raw data are [(20, 21, 1), (22, 22, 2), (40, 41, 3)]
        pschainclass_test.pschainclass - DEBUG - Lookahead offset is 60
        pschainclass_test.pschainclass.classDef - DEBUG - Walker has 30 remaining bytes.
        pschainclass_test.pschainclass.classDef - DEBUG - ClassDef is format 1.
        pschainclass_test.pschainclass.classDef - DEBUG - First is 30, and count is 1
        pschainclass_test.pschainclass.classDef - DEBUG - Raw data are (1,)
        pschainclass_test.pschainclass - DEBUG - Set offsets are (0, 68, 0, 0)
        pschainclass_test.pschainclass.class index 0 - DEBUG - Set offset is zero
        pschainclass_test.pschainclass.class index 1 - DEBUG - Set offset is 68
        pschainclass_test.pschainclass.class index 1 - DEBUG - Rule count is 1
        pschainclass_test.pschainclass.class index 1 - DEBUG - Raw rule offsets are (4,)
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Backtrack count is 1
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Backtrack classes (reversed) are (1,)
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Input count is 2
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Input classes are (1, 2)
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Lookahead count is 1
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Lookahead classes are (1,)
        pschainclass_test.pschainclass.class index 1.rule order 0 - DEBUG - Action count is 1
        pschainclass_test.pschainclass.class index 1.rule order 0.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pschainclass_test.pschainclass.class index 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pschainclass_test.pschainclass.class index 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pschainclass_test.pschainclass.class index 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 22
        pschainclass_test.pschainclass.class index 2 - DEBUG - Set offset is zero
        pschainclass_test.pschainclass.class index 3 - DEBUG - Set offset is zero
        pschainclass_test.pschainclass - WARNING - The classes [3] in the ClassDef are not used in any key, so the corresponding glyphs [40, 41] will be removed from it.
        pschainclass_test.pschainclass - INFO - The following glyphs appear only in the ClassDef and are not present in the Coverage: [22]
        pschainclass_test.pschainclass - INFO - The following glyphs appear in the Coverage and the ClassDef: [20, 21]
        >>> d = {22: obj[k][0].lookup for k in obj}
        >>> for index, func in FL:
        ...     func(d[index])
        
        >>> fvb(s[:33], logger=logger, fixupList=FL)
        pschainclass_test.pschainclass - DEBUG - Walker has 33 remaining bytes.
        pschainclass_test.pschainclass - DEBUG - Format is 2
        pschainclass_test.pschainclass.coverage - DEBUG - Walker has 13 remaining bytes.
        pschainclass_test.pschainclass.coverage - DEBUG - Format is 1, count is 2
        pschainclass_test.pschainclass.coverage - DEBUG - Raw data are [20, 21]
        pschainclass_test.pschainclass - DEBUG - Backtrack offset is 28
        pschainclass_test.pschainclass.classDef - DEBUG - Walker has 5 remaining bytes.
        pschainclass_test.pschainclass.classDef - DEBUG - ClassDef is format 1.
        pschainclass_test.pschainclass.classDef - ERROR - Insufficient bytes for format 1 header.
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pschainclass")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 2:
            logger.error((
              'V0002',
              (format,),
              "Expected format 2, but got format %d."))
            
            return None
        
        else:
            logger.debug(('Vxxxx', (), "Format is 2"))
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger)
        
        if covTable is None:
            return None
        
        fvw = classdef.ClassDef.fromvalidatedwalker
        backOffset = w.unpack("H")
        logger.debug(('Vxxxx', (backOffset,), "Backtrack offset is %d"))
        
        if backOffset:
            cdBack = fvw(w.subWalker(backOffset), logger=logger)
            
            if cdBack is None:
                return None
        
        else:
            cdBack = classdef.ClassDef()
        
        inOffset = w.unpack("H")
        logger.debug(('Vxxxx', (inOffset,), "Input offset is %d"))
        cdIn = fvw(w.subWalker(inOffset), logger=logger)
        
        if cdIn is None:
            return None
        
        lookOffset = w.unpack("H")
        logger.debug(('Vxxxx', (lookOffset,), "Lookahead offset is %d"))
        
        if lookOffset:
            cdLook = fvw(w.subWalker(lookOffset), logger=logger)
            
            if cdLook is None:
                return None
        
        else:
            cdLook = classdef.ClassDef()
        
        r = cls(
          {},
          classDefBacktrack = cdBack,
          classDefInput = cdIn,
          classDefLookahead = cdLook)
        
        setCount = w.unpack("H")
        
        if w.length() < 2 * setCount:
            logger.error((
              'V0378',
              (),
              "The ChainClassSet offsets are missing or incomplete."))
            
            return None
        
        setOffsets = w.group("H", setCount)
        logger.debug(('Vxxxx', (setOffsets,), "Set offsets are %s"))
        ClassTuple = pschainclass_classtuple.ClassTuple
        Key = pschainclass_key.Key
        fvw = pslookupgroup.PSLookupGroup.fromvalidatedwalker
        
        for firstClassIndex, setOffset in enumerate(setOffsets):
            subLogger = logger.getChild("class index %d" % (firstClassIndex,))
            
            if setOffset:
                subLogger.debug(('Vxxxx', (setOffset,), "Set offset is %d"))
                wSet = w.subWalker(setOffset)
                
                if wSet.length() < 2:
                    subLogger.error((
                      'V0379',
                      (),
                      "The ChainClassRuleCount is missing or incomplete."))
                    
                    return None
                
                ruleCount = wSet.unpack("H")
                subLogger.debug(('Vxxxx', (ruleCount,), "Rule count is %d"))
                
                if wSet.length() < 2 * ruleCount:
                    subLogger.error((
                      'V0380',
                      (),
                      "The ChainClassRule offsets are missing or incomplete."))
                    
                    return None
                
                ruleOffsets = wSet.group("H", ruleCount)
                
                subLogger.debug((
                  'Vxxxx',
                  (ruleOffsets,),
                  "Raw rule offsets are %s"))
                
                for ruleOrder, ruleOffset in enumerate(ruleOffsets):
                    wRule = wSet.subWalker(ruleOffset)
                    
                    subLogger2 = subLogger.getChild(
                      "rule order %d" % (ruleOrder,))
                    
                    if wRule.length() < 2:
                        subLogger2.error((
                          'V0381',
                          (),
                          "The BacktrackGlyphCount is missing or incomplete."))
                        
                        return None
                    
                    backCount = wRule.unpack("H")
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (backCount,),
                      "Backtrack count is %d"))
                    
                    if wRule.length() < 2 * backCount:
                        subLogger2.error((
                          'V0382',
                          (),
                          "The Backtrack classes are missing or incomplete."))
                        
                        return None
                    
                    tBack = ClassTuple(reversed(wRule.group("H", backCount)))
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (tBack,),
                      "Backtrack classes (reversed) are %s"))
                    
                    if wRule.length() < 2:
                        subLogger2.error((
                          'V0383',
                          (),
                          "The InputGlyphCount is missing or incomplete."))
                        
                        return None
                    
                    inCount = wRule.unpack("H") - 1
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (inCount + 1,),
                      "Input count is %d"))
                    
                    if wRule.length() < 2 * inCount:
                        subLogger2.error((
                          'V0384',
                          (),
                          "The Input classes are missing or incomplete."))
                        
                        return None
                    
                    tIn = ClassTuple(
                      (firstClassIndex,) +
                      wRule.group("H", inCount))
                    
                    subLogger2.debug(('Vxxxx', (tIn,), "Input classes are %s"))
                    
                    if wRule.length() < 2:
                        subLogger2.error((
                          'V0385',
                          (),
                          "The LookaheadGlyphCount is missing or incomplete."))
                        
                        return None
                    
                    lookCount = wRule.unpack("H")
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (lookCount,),
                      "Lookahead count is %d"))
                    
                    if wRule.length() < 2 * lookCount:
                        subLogger2.error((
                          'V0386',
                          (),
                          "The Lookahead classes are missing or incomplete."))
                        
                        return None
                    
                    tLook = ClassTuple(wRule.group("H", lookCount))
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (tLook,),
                      "Lookahead classes are %s"))
                    
                    if wRule.length() < 2:
                        subLogger2.error((
                          'V0387',
                          (),
                          "The lookup count is missing or incomplete."))
                        
                        return None
                    
                    posCount = wRule.unpack("H")
                    
                    subLogger2.debug((
                      'Vxxxx',
                      (posCount,),
                      "Action count is %d"))
                    
                    key = Key([tBack, tIn, tLook], ruleOrder=ruleOrder)
                    
                    obj = fvw(
                      wRule,
                      count = posCount,
                      fixupList = fixupList,
                      logger = subLogger2,
                      **kwArgs)
                    
                    if obj is None:
                        return None
                    
                    r[key] = obj
            
            else:
                subLogger.debug(('Vxxxx', (), "Set offset is zero"))
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          {k[1] for k in r},
          [cdIn],
          logger = logger,
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(cdIn))
        
        if not okToProceed:
            r.clear()
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSChainClass from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this call is made, usually by the
                        top-level GPOS construction logic. The fixup call takes
                        one argument, the Lookup being set into it.
        
        >>> w = writer.LinkedWriter()
        >>> obj = _testingValues[1]
        >>> obj.buildBinary(w, forGPOS=False)
        >>> d = {obj[k][0].lookup.asImmutable(): 22 for k in obj}
        >>> w.addIndexMap("lookupList_GSUB", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> obj2 = PSChainClass.frombytes(s, fixupList=FL)
        >>> d = {22: obj[k][0].lookup for k in obj}
        >>> for index, func in FL:
        ...     func(d[index])
        
        At this point we have the object; note that the reconciliation phase
        has removed some unneeded classes from the ClassDef (see the doctest
        output for the validated method to see more details on this).
        
        >>> obj2.pprint_changes(obj)
        Class definition table (input):
          Deleted records:
            40: 3
            41: 3
        """
        
        assert 'fixupList' in kwArgs
        format = w.unpack("H")
        assert format == 2
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        f = classdef.ClassDef.fromwalker
        
        backOffset = w.unpack("H")
        
        if backOffset:
            cdBack = f(w.subWalker(backOffset))
        else:
            cdBack = classdef.ClassDef()
        
        cdIn = classdef.ClassDef.fromwalker(w.subWalker(w.unpack("H")))
        
        lookOffset = w.unpack("H")
        
        if lookOffset:
            cdLook = f(w.subWalker(lookOffset))
        else:
            cdLook = classdef.ClassDef()
        
        r = cls(
            {},
            classDefBacktrack = cdBack,
            classDefInput = cdIn,
            classDefLookahead = cdLook)
        
        setOffsets = w.group("H", w.unpack("H"))
        f = pslookupgroup.PSLookupGroup.fromwalker
        fixupList = kwArgs['fixupList']
        ClassTuple = pschainclass_classtuple.ClassTuple
        Key = pschainclass_key.Key
        
        for firstClassIndex, setOffset in enumerate(setOffsets):
            if setOffset:
                wSet = w.subWalker(setOffset)
                it = enumerate(wSet.group("H", wSet.unpack("H")))
                
                for ruleOrder, ruleOffset in it:
                    wRule = wSet.subWalker(ruleOffset)
                    
                    tBack = ClassTuple(
                      reversed(wRule.group("H", wRule.unpack("H"))))
                    
                    tIn = ClassTuple(
                      (firstClassIndex,) +
                      wRule.group("H", wRule.unpack("H") - 1))
                    
                    tLook = ClassTuple(wRule.group("H", wRule.unpack("H")))
                    key = Key([tBack, tIn, tLook], ruleOrder=ruleOrder)
                    
                    r[key] = f(
                      wRule,
                      count = wRule.unpack("H"),
                      fixupList = fixupList)
        
        # Now that we have the keys we can reconcile
        
        okToProceed, covSet = coverageutilities.reconcile(
          covTable,
          {k[1] for k in r},
          [cdIn],
          **kwArgs)
        
        r.coverageExtras.update(covSet - set(cdIn))
        
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

        if self.classDefBacktrack:
            s.write("backtrackclass definition begin\n")
            
            it = sorted(
              self.classDefBacktrack,
              key = (lambda x: (self.classDefBacktrack[x], x)))
            
            for k in it:
                v = self.classDefBacktrack[k]
                s.write("%s\t%d\n" % (bnfgi(k), v))
            
            s.write("class definition end\n\n")
            
        s.write("class definition begin\n")
        
        it = sorted(
          self.classDefInput,
          key = (lambda x: (self.classDefInput[x], x)))
        
        for k in it:
            v = self.classDefInput[k]
            s.write("%s\t%d\n" % (bnfgi(k), v))
        
        s.write("class definition end\n\n")
        
        if self.classDefLookahead:
            s.write("lookaheadclass definition begin\n")
            
            it = sorted(
              self.classDefLookahead,
              key = (lambda x:(self.classDefLookahead[x], x)))
            
            for k in it:
                v = self.classDefLookahead[k]
                s.write("%s\t%d\n" % (bnfgi(k), v))
            
            s.write("class definition end\n\n")
        
        for k in iter(self):
            v = self[k]
            btSeq, inSeq, laSeq = k[0], k[1], k[2]
            
            actionStr = "\t".join(
              [ "%d, %d" % (vi.sequenceIndex + 1, vi.lookup.sequence)
                for vi in v])
            
            if btSeq:
                btStr = ", ".join(
                  [ str(btSeq[sv-1])
                    for sv in range(len(btSeq), 0, -1)])
            
            else:
                btStr = ""
            
            inStr = ", ".join([str(sv) for sv in inSeq])
            laStr = ", ".join([str(sv) for sv in laSeq]) if laSeq else ""
            
            s.write(
              "class-chain\t%s\t%s\t%s\t%s\n" %
              (btStr, inStr, laStr, actionStr))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype import lookup
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer, writer
    from io import StringIO
    
    def _makeTV():
        from fontio3.GSUB import single
        
        cdBack = classdef.ClassDef({10: 1, 11: 1})
        cdIn = classdef.ClassDef({20: 1, 21: 1, 22: 2, 40: 3, 41: 3})
        cdLook = classdef.ClassDef({30: 1})
        back1 = pschainclass_classtuple.ClassTuple([1])
        in1 = pschainclass_classtuple.ClassTuple([1, 2])
        look1 = pschainclass_classtuple.ClassTuple([1])
        key1 = pschainclass_key.Key([back1, in1, look1], ruleOrder=0)
        sgl1 = single.Single({20: 40, 21: 41})
        lkup1 = lookup.Lookup([sgl1], sequence=22)
        rec1 = pslookuprecord.PSLookupRecord(sequenceIndex=0, lookup=lkup1)
        grp1 = pslookupgroup.PSLookupGroup([rec1])
        
        obj = PSChainClass(
          {key1: grp1},
          classDefBacktrack = cdBack,
          classDefInput = cdIn,
          classDefLookahead = cdLook)
        
        return obj
        
#         gv = pslookupgroup._testingValues
#         kv = pschainclass_key._testingValues
#         cdBackLook = classdef.ClassDef({61: 1, 62: 1, 63: 1, 64: 2})
#     
#         cdIn = classdef.ClassDef({
#           25: 1,
#           26: 1,
#           40: 2,
#           41: 2,
#           50: 3,
#           51: 3,
#           30: 4,
#           31: 4,
#           10: 5,
#           11: 5})
#     
#         _testingValues = (
#             PSChainClass(
#               {kv[0]: gv[1], kv[1]: gv[2], kv[2]: gv[0]},
#               classDefBacktrack = cdBackLook,
#               classDefInput = cdIn,
#               classDefLookahead = cdBackLook),)
#     
#         del gv, kv, cdBackLook, cdIn

    _testingValues = (PSChainClass, _makeTV())
    
    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 2,
        'C': 3
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
        backtrackclass definition begin
        A	1
        B	2
        C	3
        class definition end

        class definition begin
        A	4
        B	5
        C	6
        class definition end
        
        lookaheadclass definition begin
        A	7
        B	8
        C	9
        class definition end
        
        class-chain	0, 1,2	0, 5	7, 8, 9, 0	1,testSingle1	1,testSingle2
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        backtrackclass definition begin
        A	1
        B	2
        C	3
        class definition end

        class definition begin
        A	4
        B	5
        C	6
        class definition end
        
        lookaheadclass definition begin
        A	7
        B	8
        C	9
        class definition end
        
        foo
        class-chain	0,1,2	0, 5	7, 8, 9, 0	1,testSingle1	1,testSingle2
        class-chain	1,4	7	6, 8, 9	1,testSingle1	1,testSingle2
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
