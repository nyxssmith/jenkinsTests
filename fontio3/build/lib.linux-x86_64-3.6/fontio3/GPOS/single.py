#
# single.py
#
# Copyright © 2007-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 1 (Single Adjustment) subtables for a GPOS table.
"""

# System imports
import collections
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.GPOS import effect, value
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    # Issue warnings for any Values that have no effect
    
    for glyph, val in obj.items():
        if not val:
            logger.warning((
              'V0323',
              (glyph,),
              "Value for glyph %d has no effect, and may be removed."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Single(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing LookupType 1 (Single Adjustment) subtables.

    These are dictionaries mapping glyph indices to Value objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    xyz11:
      FUnit adjustment to origin's x-coordinate: -10
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60003:
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
    xyz46:
      FUnit adjustment to origin's x-coordinate: 30
      Device for vertical advance:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    xyz6:
      FUnit adjustment to origin's x-coordinate: -10
    
    >>> _testingValues[0].gatheredMaxContext()
    1
    
    >>> logger = utilities.makeDoctestLogger("iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Single({14: value.Value()}).isValid(logger=logger, editor=e)
    iv - WARNING - Value for glyph 14 has no effect, and may be removed.
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_compactremovesfalses = True,
        map_maxcontextfunc = (lambda d: 1),
        map_validatefunc_partial = _validate)
    
    kind = ('GPOS', 1)
    kindString = "Single positioning table"
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        The topology of the dict is respected here, so no attempt is made to
        combine references to distinct but equal objects. If the client wishes
        this to happen, then this method should be called with a coalesced()
        value.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0008 0001 FFF6  0001 0001 000A      |..............  |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0020 00B1 0003  FFF6 0000 0000 0000 |... ............|
              10 | 001E 0000 0000 0036  0000 0036 002A 0000 |.......6...6.*..|
              20 | 0001 0003 0005 002D  0062 000C 0014 0002 |.......-.b......|
              30 | BDF0 0020 3000 000C  0012 0001 8C04      |... 0.........  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        localPool = {}  # id(Value) -> (Value, stake)
        devicePool = {}  # id(Device) -> (Device, stake)
        
        for obj in self.values():
            localPool[id(obj)] = (obj, w.getNewStake())
        
        lpv = list(localPool.values())
        
        valueFormat = functools.reduce(
          operator.or_,
          [obj[0].getMask() for obj in lpv])
        
        kad = kwArgs.copy()
        kad['valueFormat'] = valueFormat
        kad['devicePool'] = devicePool
        kad['posBase'] = stakeValue
        covTable = coverage.Coverage.fromglyphset(self)
        covStake = w.getNewStake()
        w.add("H", 1 + (len(lpv) > 1))  # format
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", valueFormat)
        
        if len(lpv) == 1:
            lpv[0][0].buildBinary(w, stakeValue=lpv[0][1], **kad)
        
        else:
            w.add("H", len(self))
            
            for g in sorted(self):
                obj = self[g]
                obj.buildBinary(w, stakeValue=localPool[id(obj)][1], **kad)
        
        # Resolve the references
        covTable.buildBinary(w, stakeValue=covStake)
        
        # we decorate-sort to ensure a repeatable, canonical ordering
        it = sorted(
          (sorted(obj.asImmutable()[1]), obj, stake)
          for obj, stake in devicePool.values())
        
        for ignore, obj, stake in it:
            obj.buildBinary(w, stakeValue=stake)
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectExtrema() instead.")
    
    def effectExtrema(self, forHorizontal=True, **kwArgs):
        """
        Returns a dict, indexed by glyph, of pairs of values. If
        forHorizontal is True, these values will be the yMaxDelta and
        yMinDelta; if False, they will be the xMaxDelta and xMinDelta. These
        values can then be used to test against the font's ascent/descent
        values in order to show VDMA-like output, or to be accumulated across
        all the features that are performed for a given script and lang/sys.
        
        Note that either or both of these values may be None; this can arise
        for cases like mark-to-mark, where potentially infinite stacking of
        marks can occur.
        
        The following keyword arguments are used:
            
            cache               A dict mapping object IDs to result dicts.
                                This is used during processing to speed up
                                analysis of deeply nested subtables, so the
                                effectExtrema() call need only be made once per
                                subtable.
            
            editor              The Editor object containing this subtable.
        
        >>> _testingValues[1].pprint()
        5:
          FUnit adjustment to origin's x-coordinate: -10
        45:
          FUnit adjustment to origin's x-coordinate: 30
          Device for vertical advance:
            Tweak at 12 ppem: -2
            Tweak at 14 ppem: -1
            Tweak at 18 ppem: 1
        98:
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
        
        >>> d = _testingValues[1].effectExtrema()
        >>> for g in sorted(d):
        ...   print(g, d[g])
        
        >>> d = _testingValues[1].effectExtrema(forHorizontal=False)
        >>> for g in sorted(d):
        ...   print(g, d[g])
        5 (0, -10)
        45 (30, 0)
        """
        
        cache = kwArgs.get('cache', {})
        
        if id(self) in cache:
            return cache[id(self)]
        
        r = {}
        fv = effect.Effect.fromvalue
        
        for glyph, valObj in self.items():
            p = fv(valObj).toPair(forHorizontal)
            
            if any(p):
                r[glyph] = fv(valObj).toPair(forHorizontal)
        
        cache[id(self)] = r
        return r

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new Single constructed from the specified FontWorkerSource,
        with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> s = Single.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.single - WARNING - line 3 -- glyph 'E' not found
        FW_test.single - ERROR - line 4 -- incorrect number of tokens, expected 3, found 1
        FW_test.single - WARNING - line 6 -- glyph 'F' not found
        >>> s.pprint()
        2:
          FUnit adjustment to origin's x-coordinate: -123
        5:
          FUnit adjustment to horizontal advance: -789
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('single')

        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber
        valuedict = collections.defaultdict(value.Value)
        r = cls()

        for line in fws:
            if line.lower() in terminalStrings:
                for gidx, gvalues in valuedict.items():
                    r[gidx] = gvalues            
                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                if len(tokens) != 3:
                    logger.error(('Vxxxx', (fws.lineNumber, len(tokens)),
                      "line %d -- incorrect number of tokens, expected 3, found %d"))
                    continue

                token = tokens[0].lower()
                if token in ['x advance','x placement',
                             'y advance', 'y placement']:
                    glyphName = tokens[1]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    if glyphIndex:
                        val = int(tokens[2])
                        if val != 0:
                            gval = valuedict[glyphIndex]
                            # test for duplicates here?
                            if tokens[0].lower() == 'x advance':
                                if gval.xAdvance:
                                    logger.warning(('Vxxxx', (fws.lineNumber, glyphName),
                                      "line %d -- ignoring duplicate x advance for "
                                      "glyph '%s'"))
                                else:
                                    gval.xAdvance = val

                            elif tokens[0].lower() == 'x placement':
                                if gval.xPlacement:
                                    logger.warning(('Vxxxx', (fws.lineNumber, glyphName),
                                      "line %d -- ignoring duplicate x placement for "
                                      "glyph '%s'"))
                                else:
                                    gval.xPlacement = val

                            elif tokens[0].lower() == 'y advance':
                                if gval.yAdvance:
                                    logger.warning(('Vxxxx', (fws.lineNumber, glyphName),
                                      "line %d -- ignoring duplicate y advance for "
                                      "glyph '%s'"))
                                else:
                                    gval.yAdvance = val

                            elif tokens[0].lower() == 'y placement':
                                if gval.yPlacement:
                                    logger.warning(('Vxxxx', (fws.lineNumber, glyphName),
                                      "line %d -- ignoring duplicate y placement for "
                                      "glyph '%s'"))
                                else:
                                    gval.yPlacement = val

                    else:
                        logger.warning(('V0956', (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))

                        continue

                else:
                    logger.warning((
                        'V0960',
                        (fws.lineNumber, tokens[0]),
                        'line %d -- unexpected token: %s'))

        logger.warning((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        return r


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Single from the specified walker, with source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("gpos")
        >>> fvb = Single.fromvalidatedbytes
        >>> fvb(s, logger=logger).pprint(namer=namer.testingNamer())
        gpos.single - DEBUG - Walker has 62 remaining bytes.
        gpos.single.coverage - DEBUG - Walker has 30 remaining bytes.
        gpos.single.coverage - DEBUG - Format is 1, count is 3
        gpos.single.coverage - DEBUG - Raw data are [5, 45, 98]
        gpos.single.value - DEBUG - Walker has 54 remaining bytes.
        gpos.single.value - DEBUG - Walker has 46 remaining bytes.
        gpos.single.value.yAdvDevice.device - DEBUG - Walker has 8 remaining bytes.
        gpos.single.value.yAdvDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        gpos.single.value.yAdvDevice.device - DEBUG - Data are (35844,)
        gpos.single.value - DEBUG - Walker has 38 remaining bytes.
        gpos.single.value.xPlaDevice.device - DEBUG - Walker has 8 remaining bytes.
        gpos.single.value.xPlaDevice.device - DEBUG - StartSize=12, endSize=18, format=1
        gpos.single.value.xPlaDevice.device - DEBUG - Data are (35844,)
        gpos.single.value.yPlaDevice.device - DEBUG - Walker has 20 remaining bytes.
        gpos.single.value.yPlaDevice.device - DEBUG - StartSize=12, endSize=20, format=2
        gpos.single.value.yPlaDevice.device - DEBUG - Data are (48624, 32, 12288)
        afii60003:
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
        xyz46:
          FUnit adjustment to origin's x-coordinate: 30
          Device for vertical advance:
            Tweak at 12 ppem: -2
            Tweak at 14 ppem: -1
            Tweak at 18 ppem: 1
        xyz6:
          FUnit adjustment to origin's x-coordinate: -10
        
        >>> fvb(s[:3], logger=logger)
        gpos.single - DEBUG - Walker has 3 remaining bytes.
        gpos.single - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('single')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        r = cls()
        posBase = w.subWalker(0)
        format = w.unpack("H")
        
        if format not in {1, 2}:
            logger.error((
              'V0321',
              (format,),
              "The value %d is not a valid format for a Single table."))
            
            return None
        
        offset = w.unpack("H")
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(offset),
          logger = logger)
        
        if covTable is None:
            return None
        
        valueFormat = w.unpack("H")
        
        if valueFormat & 0xFF00:
            logger.error((
              'E4110',
              (valueFormat,),
              "Reserved bits are set in the 0x%04X ValueFormat field."))
            
            return None
        
        vfvw = value.Value.fromvalidatedwalker
        
        if format == 1:
            obj = vfvw(
              w,
              valueFormat = valueFormat,
              posBase = posBase,
              logger = logger)
            
            if obj is None:
                return None
            
            for glyphIndex in covTable:
                r[glyphIndex] = obj
        
        else:
            objs = []
            
            if w.length() < 2:
                logger.error((
                  'V0322',
                  (),
                  "Insufficient bytes for format 2 Value count."))
                
                return None
            
            count = w.unpack("H")
            
            while count:
                obj = vfvw(
                  w,
                  valueFormat = valueFormat,
                  posBase = posBase,
                  logger = logger)
                
                if obj is None:
                    return None
                
                objs.append(obj)
                count -= 1
            
            for glyphIndex, coverageIndex in covTable.items():
                if coverageIndex >= len(objs):
                    logger.error((
                      'V0931',
                      (coverageIndex, len(objs)),
                      "A coverage index was %d, which is out of range, given "
                      "that there are only %d Value record(s)."))
                    
                    return None
                
                r[glyphIndex] = objs[coverageIndex]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Single constructed from the specified walker.
        
        >>> for obj in (_testingValues[0], _testingValues[1]):
        ...     print(obj == Single.frombytes(obj.binaryString()))
        True
        True
        """
        
        r = cls()
        posBase = w.subWalker(0)
        format = w.unpack("H")
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        valueFormat = w.unpack("H")
        vfw = value.Value.fromwalker
        
        if format == 1:
            obj = vfw(w, valueFormat=valueFormat, posBase=posBase)
            
            for glyphIndex in covTable:
                r[glyphIndex] = obj
        
        elif format == 2:
            objs = []
            count = w.unpack("H")
            
            while count:
                objs.append(vfw(w, valueFormat=valueFormat, posBase=posBase))
                count -= 1
            
            for glyphIndex, coverageIndex in covTable.items():
                r[glyphIndex] = objs[coverageIndex]
        
        return r

    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single glyph in the specified glyph array. This
        method is called by the runOne_GPOS() method of the Lookup (which is,
        in turn, called by the run() method there).
        
        This method returns a pair of values. The first value will be None if
        no processing was actually done; otherwise it will be an array of
        Effect objects of the same length as glyphArray. The second value is
        the number of glyph indices involved (or zero if no matching occurred).
        
        >>> valObj = value.Value(xPlacement=-10)
        >>> obj = Single({5: valObj})
        >>> obj.pprint()
        5:
          FUnit adjustment to origin's x-coordinate: -10
        
        >>> ga = runningglyphs.GlyphList.fromiterable([3, 4, 5, 6, 7])
        >>> r, count = obj.runOne(ga, 0)
        >>> (r, count)
        (None, 0)
        
        >>> r, count = obj.runOne(ga, 2)
        >>> count
        1
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 3, originalOffset = 0 
        glyph 4, originalOffset = 1 
        glyph 5, originalOffset = 2 xPlacementDelta = -10
        glyph 6, originalOffset = 3 
        glyph 7, originalOffset = 4 
        
        Single objects support GPOS variations:
        
        >>> d = {'wght': (-1.0, -0.5, 0.0), 'wdth': (0.0, 0.5, 1.0)}
        >>> key = LivingRegion.fromdict(d)
        >>> ldObj = LivingDeltas({LivingDeltasMember((key, -180))})
        >>> valObj.xPlaVariation = ldObj
        >>> obj.pprint()
        5:
          FUnit adjustment to origin's x-coordinate: -10
          Variation for origin's x-coordinate:
            A delta of -180 applies in region 'wdth': (start 0.0, peak 0.5, end 1.0), 'wght': (start -1.0, peak -0.5, end 0.0)
        
        >>> coord1 = LivingAxialCoordinate.fromdict({'wght': -0.5, 'wdth': 0.5})
        >>> r, count = obj.runOne(ga, 2, coordinateTuple=coord1)
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 3, originalOffset = 0 
        glyph 4, originalOffset = 1 
        glyph 5, originalOffset = 2 xPlacementDelta = -190
        glyph 6, originalOffset = 3 
        glyph 7, originalOffset = 4 
        
        >>> coord2 = LivingAxialCoordinate.fromdict({'wght': -0.25, 'wdth': 0.75})
        >>> r, count = obj.runOne(ga, 2, coordinateTuple=coord2)
        >>> for glyph, eff in zip(ga, r):
        ...     print("glyph", glyph, eff)
        glyph 3, originalOffset = 0 
        glyph 4, originalOffset = 1 
        glyph 5, originalOffset = 2 xPlacementDelta = -55
        glyph 6, originalOffset = 3 
        glyph 7, originalOffset = 4 
        """
        
        inGlyph = glyphArray[startIndex]
        
        if inGlyph not in self:
            return (None, 0)
        
        E = effect.Effect
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs['cumulEffects']
        else:
            r = [E() for g in glyphArray]
        
        r[startIndex].add(E.fromvalue(self[inGlyph], **kwArgs))
        return (r, 1)

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of Single to provided stream 's' in Font Worker source
        format.
        """
        
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for k,v in sorted(self.items()):
            v.writeFontWorkerSource(s, lbl=bnfgi(k))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import itertools
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    
    from fontio3.opentype.living_variations import (
      LivingAxialCoordinate,
      LivingDeltas,
      LivingDeltasMember,
      LivingRegion)
    
    from io import StringIO
    
    v = value._testingValues
    
    _testingValues = (
        Single({10: v[0]}),
        Single({5: v[0], 45: v[2], 98: v[3]}),)
    
    del v

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 2,
        'B': 3,
        'C': 5,
        'D': 7
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        x placement	A	-123
        y placement	B	456
        x advance	C	-789
        y advance	D	987
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        x placement	A	-123
        y placement	E	456
        foo
        x advance	C	-789
        y advance	F	987
        lookup end
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
