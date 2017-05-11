#
# pschainglyph.py
#
# Copyright © 2009-2016 Monotype Imaging Inc. All Rights Reserved
#

"""
Support for format 1 (glyph) chaining contextual tables, both GPOS and GSUB.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
  coverage,
  pschainglyph_glyphtuple,
  pschainglyph_key,
  pslookupgroup,
  pslookuprecord)

# -----------------------------------------------------------------------------

#
# Private functions
#

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
                  'V0375',
                  (effectIndex, key, len(key[1]) - 1, n),
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

class PSChainGlyph(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    These are objects representing chained contextual (glyph) mappings. They
    are dicts mapping Keys to PSLookupGroups.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    ((xyz86, xyz87), (xyz26, xyz51), ()), Relative order = 0:
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
    ((), (xyz26, xyz41), (xyz81,)), Relative order = 1:
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
    ((), (xyz31, xyz11, xyz31), ()), Relative order = 0:
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
        ((85, 86), (25, 50), ()), Relative order = 0
        ((), (25, 40), (80,)), Relative order = 1
        ((), (30, 10, 30), ()), Relative order = 0
        """
        
        v = list(super(PSChainGlyph, self).__iter__())
        return iter(sorted(v, key=_keySort))
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ContextGlyph to the specified
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
              10 | 001E 0002 000A 001C  0001 002A 0002 0056 |...........*...V|
              20 | 0055 0002 0032 0000  0001 0001 0019 0000 |.U...2..........|
              30 | 0002 0028 0001 0050  0002 0000 000B 0001 |...(...P........|
              40 | 0019 0000 0003 000A  001E 0000 0001 0002 |................|
              50 | 000A                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        firstGlyphs = sorted(set(k[1][0] for k in self))
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
            setStake = setStakes[firstGlyph]
            w.stakeCurrentWithValue(setStake)
            
            o = orderings[firstGlyph] = sorted(
              (k.ruleOrder, k[1], k)
              for k in self
              if k[1][0] == firstGlyph)
            
            w.add("H", len(o))
            
            for order, ignore, key in o:
                ruleStake = ruleStakes[(firstGlyph, order)] = w.getNewStake()
                w.addUnresolvedOffset("H", setStake, ruleStake)
        
        for firstGlyph in firstGlyphs:
            for order, ignore, key in orderings[firstGlyph]:
                w.stakeCurrentWithValue(ruleStakes[(firstGlyph, order)])
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
        Creates and returns a new PSChainGlyph from the specified
        FontWorkerSource, doing source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> obj = PSChainGlyph.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   namer = _test_FW_namer,
        ...   forGPOS = True,
        ...   lookupDict = _test_FW_lookupDict,
        ...   logger=logger,
        ...   editor={})
        FW_test.pschainglyph - WARNING - line 2 -- unexpected token: foo
        FW_test.pschainglyph - WARNING - line 3 -- glyph 'X' not found
        FW_test.pschainglyph - WARNING - line 3 -- glyph 'Y' not found
        FW_test.pschainglyph - WARNING - line 3 -- glyph 'Z' not found
        FW_test.pschainglyph - WARNING - line 5 -- context '(A,B), (C,D,E), (F,G)' previously defined at line 4
        FW_test.pschainglyph - WARNING - line 0 -- did not find matching 'subtable end/lookup end'
        >>> obj.pprint()
        Key((GlyphTuple((2, 1)), GlyphTuple((3, 4, 5)), GlyphTuple((6, 7))), ruleOrder=0):
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
        logger = logger.getChild("pschainglyph")

        terminalStrings = ('subtable end', 'lookup end')
        namer = kwArgs['namer']
        startingLineNumber = fws.lineNumber
    
        ruleOrders = {}
        lookupGroups = {}
        stringKeys = {}

        GT = pschainglyph_glyphtuple.GlyphTuple
        gIFS = namer.glyphIndexFromString
        bNFGI = namer.bestNameForGlyphIndex

        for line in fws:
            if line in terminalStrings:
                return cls(lookupGroups)
            
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                
                if tokens[0].lower() == 'glyph':
                
                    if len(tokens) < 4:
                        logger.warning((
                            'Vxxxx',
                            (fws.lineNumber,),
                            "line %d -- unexpected input"))
                        continue

                    glyphTuples = {}

                    glyphNamesOK = True
                    for i in range(1,4):
                        if tokens[i].strip():
                            glyphNames = tokens[i].split(',')
                            glyphIndices = [gIFS(t.strip()) for t in glyphNames]
                            for j in range(len(glyphIndices)):
                                if glyphIndices[j] is None:
                                    glyphNamesOK = False
                                    logger.warning((
                                      'V0956',
                                      (fws.lineNumber, glyphNames[j]),
                                      "line %d -- glyph '%s' not found"))
                        else:
                            glyphIndices = []

                        glyphTuples[i] = glyphIndices

                    if glyphNamesOK:
                        glyphTuples[1].reverse()
                        glyphTuple1 = GT(glyphTuples[1])
                        glyphTuple2 = GT(glyphTuples[2])
                        glyphTuple3 = GT(glyphTuples[3])

                        lookupList = []
                        
                        for effect in tokens[4:]:
                            effectTokens = [
                              x.strip()
                              for x in effect.split(',')]
                            
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
                          ",".join([bNFGI(gi) for gi in glyphTuple1[::-1]]),
                          ",".join([bNFGI(gi) for gi in glyphTuple2]),
                          ",".join([bNFGI(gi) for gi in glyphTuple3]))
                          
                        if stringKey in stringKeys:
                            logger.warning((
                              'Vxxxx',
                              (fws.lineNumber, stringKey, stringKeys[stringKey]),
                              "line %d -- context '%s' previously defined at line %d"))
                        else:
                            stringKeys[stringKey] = fws.lineNumber

                            key = pschainglyph_key.Key([
                              glyphTuple1,
                              glyphTuple2,
                              glyphTuple3])
                        
                            ruleOrder = ruleOrders.get(glyphTuple2[0], 0)
                            key.ruleOrder = ruleOrder
                            ruleOrders[glyphTuple2[0]] = ruleOrder + 1
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

        return cls(lookupGroups)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PSChainGlyph object from the specified
        walker, doing source validation.
        
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
        >>> logger = utilities.makeDoctestLogger("pschainglyph_test")
        >>> fvb = PSChainGlyph.fromvalidatedbytes
        >>> obj = fvb(s, fixupList=FL, logger=logger)
        pschainglyph_test.pschainglyph - DEBUG - Walker has 82 remaining bytes.
        pschainglyph_test.pschainglyph - DEBUG - Format is 1
        pschainglyph_test.pschainglyph - DEBUG - Coverage offset is 10, and set count is 2
        pschainglyph_test.pschainglyph.coverage - DEBUG - Walker has 72 remaining bytes.
        pschainglyph_test.pschainglyph.coverage - DEBUG - Format is 1, count is 2
        pschainglyph_test.pschainglyph.coverage - DEBUG - Raw data are [25, 30]
        pschainglyph_test.pschainglyph - DEBUG - Set offsets are (18, 24)
        pschainglyph_test.pschainglyph.first glyph 25 - DEBUG - Rule count is 2
        pschainglyph_test.pschainglyph.first glyph 25 - DEBUG - Rule offsets are (10, 28)
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Backtrack count is 2
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Backtrack glyphs (reversed) are (85, 86)
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Input count is 2
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Input glyphs are (25, 50)
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Lookahead count is 0
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Lookahead glyphs are ()
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0 - DEBUG - Action count is 1
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0.pslookupgroup - DEBUG - Walker has 40 bytes remaining.
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 40 remaining bytes.
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 1
        pschainglyph_test.pschainglyph.first glyph 25.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 25
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Backtrack count is 0
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Backtrack glyphs (reversed) are ()
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Input count is 2
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Input glyphs are (25, 40)
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Lookahead count is 1
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Lookahead glyphs are (80,)
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1 - DEBUG - Action count is 2
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup - DEBUG - Walker has 24 bytes remaining.
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 24 remaining bytes.
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 0
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 11
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Walker has 20 remaining bytes.
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Sequence index is 1
        pschainglyph_test.pschainglyph.first glyph 25.rule order 1.pslookupgroup.[1].pslookuprecord - DEBUG - Lookup index is 25
        pschainglyph_test.pschainglyph.first glyph 30 - DEBUG - Rule count is 1
        pschainglyph_test.pschainglyph.first glyph 30 - DEBUG - Rule offsets are (42,)
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Backtrack count is 0
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Backtrack glyphs (reversed) are ()
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Input count is 3
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Input glyphs are (30, 10, 30)
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Lookahead count is 0
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Lookahead glyphs are ()
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0 - DEBUG - Action count is 1
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0.pslookupgroup - DEBUG - Walker has 4 bytes remaining.
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Walker has 4 remaining bytes.
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Sequence index is 2
        pschainglyph_test.pschainglyph.first glyph 30.rule order 0.pslookupgroup.[0].pslookuprecord - DEBUG - Lookup index is 10
        
        >>> fvb(s[:20], fixupList=FL, logger=logger)
        pschainglyph_test.pschainglyph - DEBUG - Walker has 20 remaining bytes.
        pschainglyph_test.pschainglyph - DEBUG - Format is 1
        pschainglyph_test.pschainglyph - DEBUG - Coverage offset is 10, and set count is 2
        pschainglyph_test.pschainglyph.coverage - DEBUG - Walker has 10 remaining bytes.
        pschainglyph_test.pschainglyph.coverage - DEBUG - Format is 1, count is 2
        pschainglyph_test.pschainglyph.coverage - DEBUG - Raw data are [25, 30]
        pschainglyph_test.pschainglyph - DEBUG - Set offsets are (18, 24)
        pschainglyph_test.pschainglyph.first glyph 25 - DEBUG - Rule count is 2
        pschainglyph_test.pschainglyph.first glyph 25 - ERROR - The ChainRule offsets are missing or incomplete.
        """
        
        assert 'fixupList' in kwArgs
        fixupList = kwArgs.pop('fixupList')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pschainglyph")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
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
        covOffset, setCount = w.unpack("2H")
        
        logger.debug((
          'Vxxxx',
          (covOffset, setCount),
          "Coverage offset is %d, and set count is %d"))
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger)
        
        if covTable is None:
            return None
        
        firstGlyphs = sorted(covTable)
        
        if setCount != len(firstGlyphs):
            logger.error((
              'V0364',
              (setCount, len(firstGlyphs)),
              "The ChainSetRuleCount is %d, but the Coverage length is %d."))
            
            return None
        
        if w.length() < 2 * setCount:
            logger.error((
              'V0365',
              (),
              "The ChainRuleSet offsets are missing or incomplete."))
            
            return None
        
        setOffsets = w.group("H", setCount)
        logger.debug(('Vxxxx', (setOffsets,), "Set offsets are %s"))
        r = cls()
        fvw = pslookupgroup.PSLookupGroup.fromvalidatedwalker
        GlyphTuple = pschainglyph_glyphtuple.GlyphTuple
        Key = pschainglyph_key.Key
        
        for firstGlyph, setOffset in zip(firstGlyphs, setOffsets):
            wSet = w.subWalker(setOffset)
            subLogger = logger.getChild("first glyph %d" % (firstGlyph,))
            
            if wSet.length() < 2:
                subLogger.error((
                  'V0366',
                  (),
                  "The ChainRuleCount is missing or incomplete."))
                
                return None
            
            ruleCount = wSet.unpack("H")
            subLogger.debug(('Vxxxx', (ruleCount,), "Rule count is %d"))
            
            if wSet.length() < 2 * ruleCount:
                subLogger.error((
                  'V0367',
                  (),
                  "The ChainRule offsets are missing or incomplete."))
                
                return None
            
            ruleOffsets = wSet.group("H", ruleCount)
            subLogger.debug(('Vxxxx', (ruleOffsets,), "Rule offsets are %s"))
            
            for ruleOrder, ruleOffset in enumerate(ruleOffsets):
                wRule = wSet.subWalker(ruleOffset)
                subLogger2 = subLogger.getChild("rule order %d" % (ruleOrder,))
                
                if wRule.length() < 2:
                    subLogger2.error((
                      'V0368',
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
                      'V0369',
                      (),
                      "The Backtrack glyphs are missing or incomplete."))
                    
                    return None
                
                backTuple = GlyphTuple(reversed(wRule.group("H", backCount)))
                
                subLogger2.debug((
                  'Vxxxx',
                  (backTuple,),
                  "Backtrack glyphs (reversed) are %s"))
                
                if wRule.length() < 2:
                    subLogger2.error((
                      'V0370',
                      (),
                      "The InputGlyphCount is missing or incomplete."))
                    
                    return None
                
                inCount = wRule.unpack("H") - 1  # firstGlyph is already there
                subLogger2.debug(('Vxxxx', (inCount+1,), "Input count is %d"))
                
                if wRule.length() < 2 * inCount:
                    subLogger2.error((
                      'V0371',
                      (),
                      "The Input glyphs are missing or incomplete."))
                    
                    return None
                
                inTuple = GlyphTuple((firstGlyph,) + wRule.group("H", inCount))
                subLogger2.debug(('Vxxxx', (inTuple,), "Input glyphs are %s"))
                
                if wRule.length() < 2:
                    subLogger2.error((
                      'V0372',
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
                      'V0373',
                      (),
                      "The Lookahead glyphs are missing or incomplete."))
                    
                    return None
                
                lookTuple = GlyphTuple(wRule.group("H", lookCount))
                
                subLogger2.debug((
                  'Vxxxx',
                  (lookTuple,),
                  "Lookahead glyphs are %s"))
                
                key = Key((backTuple, inTuple, lookTuple), ruleOrder=ruleOrder)
                
                if wRule.length() < 2:
                    subLogger2.error((
                      'V0374',
                      (),
                      "The LookupCount is missing or incomplete."))
                    
                    return None
                
                posCount = wRule.unpack("H")
                subLogger2.debug(('Vxxxx', (posCount,), "Action count is %d"))
                
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
        Creates and returns a new PSChainGlyph from the specified walker.
        
        There is one required keyword argument:
        
            fixupList   A list, to which (lookupListIndex, fixupFunc) pairs
                        will be appended. The actual lookup won't be set in the
                        PSLookupRecord until this call is made, usually by the
                        top-level GPOS construction logic. The fixup call takes
                        one argument, the Lookup being set into it.
        
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
        >>> obj = PSChainGlyph.frombytes(s, fixupList=FL)
        >>> d = {10: ltv[0], 11: ltv[1], 25: ltv[2]}
        >>> for index, func in FL:
        ...     func(d[index])
        >>> obj == _testingValues[0]
        True
        """
        
        assert 'fixupList' in kwArgs
        format = w.unpack("H")
        assert format == 1
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        firstGlyphs = sorted(covTable)
        setOffsets = w.group("H", w.unpack("H"))
        r = cls()
        f = pslookupgroup.PSLookupGroup.fromwalker
        GlyphTuple = pschainglyph_glyphtuple.GlyphTuple
        Key = pschainglyph_key.Key
        
        for setIndex, firstGlyph in enumerate(firstGlyphs):
            wSet = w.subWalker(setOffsets[setIndex])
            it = enumerate(wSet.group("H", wSet.unpack("H")))
            
            for ruleOrder, ruleOffset in it:
                wRule = wSet.subWalker(ruleOffset)
                
                backTuple = GlyphTuple(
                  reversed(wRule.group("H", wRule.unpack("H"))))
                
                inTuple = GlyphTuple(
                  (firstGlyph,) + wRule.group("H", wRule.unpack("H") - 1))
                
                lookTuple = GlyphTuple(wRule.group("H", wRule.unpack("H")))
                key = Key((backTuple, inTuple, lookTuple), ruleOrder=ruleOrder)
                posCount = wRule.unpack("H")
                r[key] = f(wRule, count=posCount, **kwArgs)
        
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
            btSeq, inSeq, laSeq = k[0], k[1], k[2]
            actionStr = "\t".join(
              ["%d, %d" % (vi.sequenceIndex + 1, vi.lookup.sequence) for vi in v])
            btStr = ", ".join(
              [bnfgi(btSeq[sv-1]) for sv in range(len(btSeq), 0, -1)]) if btSeq else ""
            inStr = ", ".join([bnfgi(sv) for sv in inSeq])
            laStr = ", ".join([bnfgi(sv) for sv in laSeq]) if laSeq else ""

            s.write("glyph\t%s\t%s\t%s\t%s\n" % (
              btStr, inStr, laStr, actionStr))

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
    
    kv = pschainglyph_key._testingValues
    gv = pslookupgroup._testingValues
    
    _testingValues = (
        PSChainGlyph({kv[0]: gv[1], kv[1]: gv[2], kv[2]: gv[0]}),)
    
    del gv, kv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'B': 2,
        'C': 3,
        'D': 4,
        'E': 5,
        'F': 6,
        'G': 7
    }
    _test_FW_namer._zapfTable = {}
    _test_FW_namer._cffCharset = {}
    _test_FW_namer._glyphToPost = {v:k for k,v in list(_test_FW_namer._nameToGlyph.items())}
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
        glyph	A, B	C, D, E	F, G	1,testSingle1 	1,testSingle2
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        foo
        glyph	A,X	C,Y,E	F,Z	1,testSingle1 	1,testSingle2
        glyph	A, B	C, D, E	F, G	1,testSingle1 	1,testSingle2
        glyph	A, B	C, D, E	F, G	2,testSingle1 	1,testSingle2
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
