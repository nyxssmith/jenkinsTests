#
# pscontextglyph.py
#
# Copyright © 2009-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 1 (glyph) contextual tables, both GPOS and GSUB.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
    coverage,
    pscontextglyph_key,
    pslookupgroup,
    pslookuprecord)

# -----------------------------------------------------------------------------

#
# Private functions
#

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
                  'V0355',
                  (effectIndex, key, len(key) - 1, n),
                  "Effect %d of key %s should have a sequenceIndex from 0 "
                  "through %d, but the value is %s."))
                
                r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PSContextGlyph(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing format 1 contextual lookups. Note that these work for
    both GPOS and GSUB tables.
    
    These are dicts mapping Keys to PSLookupGroups. There is an explicit
    iterator present for this class that ensures the keys' ruleOrder attribute
    is respected.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    (xyz26, xyz51), Relative order = 0:
      Effect #1:
        Sequence index: 1
        Lookup:
          Subtable 0 (Pair (class) positioning table):
            (First class 1, Second class 1):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            (First class 2, Second class 0):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
            (First class 2, Second class 1):
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
            Class definition table for first glyph:
              xyz16: 1
              xyz6: 1
              xyz7: 1
              xyz8: 2
            Class definition table for second glyph:
              xyz21: 1
              xyz22: 1
              xyz23: 1
          Lookup flags:
            Right-to-left for Cursive: True
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 2
    (xyz26, xyz41), Relative order = 1:
      Effect #1:
        Sequence index: 0
        Lookup:
          Subtable 0 (Pair (glyph) positioning table):
            (xyz11, xyz21):
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
            (xyz9, xyz16):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            (xyz9, xyz21):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: True
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 1
      Effect #2:
        Sequence index: 1
        Lookup:
          Subtable 0 (Pair (class) positioning table):
            (First class 1, Second class 1):
              Second adjustment:
                FUnit adjustment to origin's x-coordinate: -10
            (First class 2, Second class 0):
              First adjustment:
                Device for vertical advance:
                  Tweak at 12 ppem: -2
                  Tweak at 14 ppem: -1
                  Tweak at 18 ppem: 1
            (First class 2, Second class 1):
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
            Class definition table for first glyph:
              xyz16: 1
              xyz6: 1
              xyz7: 1
              xyz8: 2
            Class definition table for second glyph:
              xyz21: 1
              xyz22: 1
              xyz23: 1
          Lookup flags:
            Right-to-left for Cursive: True
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
          Sequence order (lower happens first): 2
    (xyz31, xyz11, xyz31), Relative order = 0:
      Effect #1:
        Sequence index: 2
        Lookup:
          Subtable 0 (Single positioning table):
            xyz11:
              FUnit adjustment to origin's x-coordinate: -10
          Lookup flags:
            Right-to-left for Cursive: False
            Ignore base glyphs: False
            Ignore ligatures: False
            Ignore marks: False
            Mark attachment type: 4
          Sequence order (lower happens first): 0
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresortfunc = _keySort,
        item_renumberdeepkeys = True,
        item_usenamerforstr = True,
        map_compactiblefunc = (lambda d, k, **kw: False),
        #map_compactremovesfalses = True,
        map_maxcontextfunc = (lambda d: utilities.safeMax(len(k) for k in d)),
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def __iter__(self):
        """
        We provide a custom iterator to make sure the ruleOrder is correctly
        being followed.
        
        >>> for k in _testingValues[0]: print(k)
        (25, 50), Relative order = 0
        (25, 40), Relative order = 1
        (30, 10, 30), Relative order = 0
        """
        
        v = list(super(PSContextGlyph, self).__iter__())
        return iter(sorted(v, key=_keySort))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PSContextGlyph to the specified
        LinkedWriter.
        
        NOTE! There will be unresolved lookup list indices in the LinkedWriter
        after this method is finished. The caller (or somewhere higher up) is
        responsible for adding an index map to the LinkedWriter with the tag
        "lookupList" before the LinkedWriter's binaryString() method is called.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> w.addIndexMap(
        ...   "lookupList_GPOS",
        ...   { ltv[0].asImmutable(): 10,
        ...     ltv[1].asImmutable(): 11,
        ...     ltv[2].asImmutable(): 25})
        >>> utilities.hexdump(w.binaryString())
               0 | 0001 000A 0002 0012  0018 0001 0002 0019 |................|
              10 | 001E 0002 000A 0014  0001 001C 0002 0001 |................|
              20 | 0032 0001 0019 0002  0002 0028 0000 000B |.2.........(....|
              30 | 0001 0019 0003 0001  000A 001E 0002 000A |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        firstGlyphs = sorted(set(k[0] for k in self))
        covTable = coverage.Coverage.fromglyphset(firstGlyphs)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", len(firstGlyphs))
        
        setStakes = dict(
          (firstGlyph, w.getNewStake())
          for firstGlyph in firstGlyphs)
        
        for firstGlyph in firstGlyphs:
            w.addUnresolvedOffset("H", stakeValue, setStakes[firstGlyph])
        
        covTable.buildBinary(w, stakeValue=covStake)
        orderings = {}
        ruleStakes = {}
        
        for firstGlyph in firstGlyphs:
            w.stakeCurrentWithValue(setStakes[firstGlyph])
            
            o = orderings[firstGlyph] = sorted(
              (k.ruleOrder, k)
              for k in self
              if k[0] == firstGlyph)
            
            w.add("H", len(o))
            
            for order, key in o:
                stake = ruleStakes[(firstGlyph, order)] = w.getNewStake()
                w.addUnresolvedOffset("H", setStakes[firstGlyph], stake)
        
        for firstGlyph in firstGlyphs:
            for order, key in orderings[firstGlyph]:
                w.stakeCurrentWithValue(ruleStakes[(firstGlyph, order)])
                obj = self[key]
                w.add("HH", len(key), len(obj))
                w.addGroup("H", key[1:])
                obj.buildBinary(w, **kwArgs)


    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new PSContextGlyph from the specified
        FontWorkerSource, doing source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSContextGlyph.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger = logger,
        ...   editor={})
        FW_test.pscontextglyph - WARNING - line 2 -- unexpected token: foo
        FW_test.pscontextglyph - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Key((1, 3, 5), ruleOrder=0):
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
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pscontextglyph")
        terminalStrings = ('subtable end', 'lookup end')
        namer = kwArgs['namer']
        startingLineNumber=fws.lineNumber
        ruleOrder = 0
        lookupGroups = {}
        
        gIFS = namer.glyphIndexFromString
        
        for line in fws:
            if line in terminalStrings:
                return cls(lookupGroups)
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() == 'glyph':
                    glyphNames = tokens[1].split(',')
                    glyphIndices = [gIFS(t.strip()) for t in glyphNames]
                    glyphsOK = True
                    for i in range(len(glyphIndices)):
                        if glyphIndices[i] is None:
                            glyphsOK = False
                            logger.warning((
                              'V0956',
                              (fws.lineNumber, glyphNames[i]),
                              "line %d -- glyph '%s' not found; "
                              "will not make entry for this line."))
                            
                    if glyphsOK:
                        glyphTuple = tuple(glyphIndices)

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
                                    logger=logger,
                                    **kwArgs)))

                        key = pscontextglyph_key.Key(glyphTuple)
                        key.ruleOrder = ruleOrder
                        ruleOrder += 1
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
          'line %d -- did not find matching \'%s\''))
    
        return cls(lookupGroups)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSContextGlyph object from the specified
        walker, doing source validation. The following keyword arguments are
        supported:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromvalidatedwalker(). The fixup call takes
                        one argument: the Lookup being set into it.
            
            logger      A logger to which messages will be posted.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {
        ...   ltv[0].asImmutable(): 10,
        ...   ltv[1].asImmutable(): 11,
        ...   ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> logger = utilities.makeDoctestLogger("pscontextglyph_test")
        >>> fvb = PSContextGlyph.fromvalidatedbytes
        >>> obj = fvb(s, fixupList=FL, logger=logger)
        pscontextglyph_test.pscontextglyph - DEBUG - Walker has 64 bytes remaining.
        pscontextglyph_test.pscontextglyph - DEBUG - Format is 1
        pscontextglyph_test.pscontextglyph.coverage - DEBUG - Walker has 54 remaining bytes.
        pscontextglyph_test.pscontextglyph.coverage - DEBUG - Format is 1, count is 2
        pscontextglyph_test.pscontextglyph.coverage - DEBUG - Raw data are [25, 30]
        pscontextglyph_test.pscontextglyph - DEBUG - RuleSetCount is 2
        pscontextglyph_test.pscontextglyph - DEBUG - RuleSet offsets are (18, 24)
        pscontextglyph_test.pscontextglyph.rule set 0 - DEBUG - Rule count is 2
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0 - DEBUG - Glyph count is 2
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0 - DEBUG - Action count is 1
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0.pslookupgroup - DEBUG - Walker has 30 bytes remaining.
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 30 remaining bytes.
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 1
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 25
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1 - DEBUG - Glyph count is 2
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1 - DEBUG - Action count is 2
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup - DEBUG - Walker has 20 bytes remaining.
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 20 remaining bytes.
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 11
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Walker has 16 remaining bytes.
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Sequence index is 1
        pscontextglyph_test.pscontextglyph.rule set 0.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Lookup index is 25
        pscontextglyph_test.pscontextglyph.rule set 1 - DEBUG - Rule count is 1
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0 - DEBUG - Glyph count is 3
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0 - DEBUG - Action count is 1
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 2
        pscontextglyph_test.pscontextglyph.rule set 1.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 10
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pscontextglyph")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d bytes remaining."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got format %d."))
            
            return None
        
        logger.debug(('Vxxxx', (), "Format is 1"))
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(w.unpack("H")),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        firstGlyphs = sorted(covTable)
        count = w.unpack("H")
        logger.debug(('Vxxxx', (count,), "RuleSetCount is %d"))
        
        if count != len(firstGlyphs):
            logger.error((
              'V0350',
              (),
              "The RuleSetCount does not match the length of the Coverage."))
            
            return None
        
        if w.length() < 2 * count:
            logger.error((
              'V0351',
              (),
              "The RuleSet is missing or only partially present."))
            
            return None
        
        setOffsets = w.group("H", count)
        logger.debug(('Vxxxx', (setOffsets,), "RuleSet offsets are %s"))
        r = cls()
        fvw = pslookupgroup.PSLookupGroup.fromvalidatedwalker
        Key = pscontextglyph_key.Key
        
        for i, setOffset in enumerate(setOffsets):
            subLogger = logger.getChild("rule set %d" % (i,))
            wSet = w.subWalker(setOffset)
            
            if wSet.length() < 2:
                subLogger.error((
                  'V0352',
                  (),
                  "The RuleCount is missing or only partially present."))
                
                return None
            
            ruleCount = wSet.unpack("H")
            subLogger.debug(('Vxxxx', (ruleCount,), "Rule count is %d"))
            
            if wSet.length() < 2 * ruleCount:
                subLogger.error((
                  'V0353',
                  (),
                  "The Rule offsets are missing or only partially present."))
                
                return None
            
            it = enumerate(wSet.group("H", ruleCount))
            
            for ruleOrder, ruleOffset in it:
                subLogger2 = subLogger.getChild("rule order %d" % (ruleOrder,))
                wRule = wSet.subWalker(ruleOffset)
                
                if wRule.length() < 4:
                    subLogger2.error((
                      'V0354',
                      (),
                      "Rule is missing or only partially present."))
                    
                    return None
                
                glyphCount, posCount = wRule.unpack("2H")
                subLogger2.debug(('Vxxxx', (glyphCount,), "Glyph count is %d"))
                subLogger2.debug(('Vxxxx', (posCount,), "Action count is %d"))
                
                if wRule.length() < 2 * (glyphCount - 1):
                    subLogger2.error((
                      'V0354',
                      (),
                      "Rule is missing or only partially present."))
                    
                    return None
                
                key = Key(
                  (firstGlyphs[i],) + wRule.group("H", glyphCount - 1),
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
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSContextGlyph from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this fixupFunc is called by
                        lookuplist.fromwalker(). The fixup call takes one
                        argument: the Lookup being set into it.
        
        >>> w = writer.LinkedWriter()
        >>> _testingValues[0].buildBinary(w, forGPOS=True)
        >>> ltv = lookup._testingValues
        >>> d = {
        ...   ltv[0].asImmutable(): 10,
        ...   ltv[1].asImmutable(): 11,
        ...   ltv[2].asImmutable(): 25}
        >>> w.addIndexMap("lookupList_GPOS", d)
        >>> s = w.binaryString()
        >>> FL = []
        >>> obj = PSContextGlyph.frombytes(s, fixupList=FL)
        >>> d = {10: ltv[0], 11: ltv[1], 25: ltv[2]}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == _testingValues[0]
        True
        """
        
        format = w.unpack("H")
        assert format == 1
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        firstGlyphs = sorted(covTable)
        count = w.unpack("H")
        assert count == len(covTable)
        setOffsets = w.group("H", count)
        r = cls()
        fixupList = kwArgs['fixupList']
        f = pslookupgroup.PSLookupGroup.fromwalker
        Key = pscontextglyph_key.Key
        
        for i, setOffset in enumerate(setOffsets):
            wSet = w.subWalker(setOffset)
            it = enumerate(wSet.group("H", wSet.unpack("H")))
            
            for ruleOrder, ruleOffset in it:
                wRule = wSet.subWalker(ruleOffset)
                glyphCount, posCount = wRule.unpack("2H")
                
                key = Key(
                  (firstGlyphs[i],) + wRule.group("H", glyphCount - 1),
                  ruleOrder = ruleOrder)
                
                r[key] = f(wRule, count=posCount, fixupList=fixupList)
        
        return r

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for k in iter(self):
            v = self[k]
            ctxStr = ", ".join([bnfgi(g) for g in k])
            
            actionStr = "\t".join([
              "%d, %d" % (vi.sequenceIndex + 1, vi.lookup.sequence)
              for vi in v])            
            
            s.write("glyph\t%s\t%s\n" % (ctxStr, actionStr))

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
    
    gv = pslookupgroup._testingValues
    kv = pscontextglyph_key._testingValues
    
    _testingValues = (
        PSContextGlyph({kv[0]: gv[1], kv[1]: gv[2], kv[2]: gv[0]}),)
    
    del gv, kv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'F': 1,
        'period': 3,
        'quoteright': 5
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
        glyph	F, period, quoteright	1,testSingle1	1,testSingle2
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        foo
        glyph	F, period, quoteright	1,testSingle1	1,testSingle2
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
