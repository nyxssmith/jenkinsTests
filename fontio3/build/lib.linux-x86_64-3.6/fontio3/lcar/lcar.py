#
# lcar.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Top-level support for the AAT 'lcar' (ligature-caret) table.
"""

# System imports
import itertools
import operator

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.lcar import splits_distance, splits_point
from fontio3.utilities import bsh, span, writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Lcar(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing ligature-caret splits. These are dicts whose keys are
    glyph indices and whose values are either Splits_Distance or Splits_Point
    objects.
    
    >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
    >>> s2 = splits_distance.Splits_Distance([250, 500])
    >>> s3 = s1.__deepcopy__()
    >>> Lcar({5: s1, 6: s1, 15: s2, 98: s3}).pprint(namer=namer.testingNamer())
    afii60003:
      0: 10 FUnits
      1: 500 FUnits
      2: 800 FUnits
    xyz16:
      0: 250 FUnits
      1: 500 FUnits
    xyz6:
      0: 10 FUnits
      1: 500 FUnits
      2: 800 FUnits
    xyz7:
      0: 10 FUnits
      1: 500 FUnits
      2: 800 FUnits
    
    >>> s4 = splits_point.Splits_Point([15, 2, 6])
    >>> s5 = splits_point.Splits_Point([9, 11])
    >>> s6 = s4.__deepcopy__()
    >>> Lcar({5: s4, 6: s4, 15: s5, 98: s6}).pprint(namer=namer.testingNamer())
    afii60003:
      0: Point 15
      1: Point 2
      2: Point 6
    xyz16:
      0: Point 9
      1: Point 11
    xyz6:
      0: Point 15
      1: Point 2
      2: Point 6
    xyz7:
      0: Point 15
      1: Point 2
      2: Point 6
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_compactremovesfalses = True)
    
    #
    # Methods
    #
    
    def _makeLookup0(self, fontGlyphCount):
        """
        Creates and returns a bytestring for the lookup-specific portions of
        the output data, for lookup format 0.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> utilities.hexdump(d._makeLookup0(30))
               0 | 0000 0000 0000 0000  0000 0000 0044 0044 |.............D.D|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0054 0000 0000 0000  0000 0000 0000 0000 |.T..............|
              30 | 0000 0000 004C 0000  0000 0000 0000 0003 |.....L..........|
              40 | 000A 01F4 0320 0003  000A 01F4 0320 0002 |..... ....... ..|
              50 | 00FA 01F4                                |....            |
        """
        
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 0)
        pool = {}  # an id-pool; safe because scope is limited to this method
        
        for glyphIndex in range(fontGlyphCount):
            if glyphIndex in self:
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeStart,
                  pool[thisID][0],
                  offsetByteDelta = 6)
            
            else:
                w.add("H", 0)  # spec is unclear whether this is 0 or 0xFFFF
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup2(self, keySpan):
        """
        Creates and returns a bytestring for the lookup-specific portions of
        the output data, for lookup format 2.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> utilities.hexdump(d._makeLookup2(ks))
               0 | 0002 0006 0003 000C  0001 0006 0006 0005 |................|
              10 | 002A 000F 000F 003A  0019 0019 0032 FFFF |.*.....:.....2..|
              20 | FFFF 0000 0003 000A  01F4 0320 0003 000A |........... ....|
              30 | 01F4 0320 0002 00FA  01F4                |... ......      |
        """
        
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 2)
        bStake = w.getNewStake()
        w.addReplaceableString(bStake, b' ' * 10)  # don't know nUnits yet...
        pool = {}  # an id-pool; safe because scope is limited to this method
        nUnits = 0
        
        for spanStart, spanEnd in keySpan:
            firstGlyph = spanStart
            
            it = (
              (id(self[i]), self[i])
              for i in range(spanStart, spanEnd + 1))
            
            for k, g in itertools.groupby(it, operator.itemgetter(0)):
                v = list(g)
                if k not in pool:
                    pool[k] = (w.getNewStake(), v[0][1])
                
                n = len(v)
                w.add("2H", firstGlyph + n - 1, firstGlyph)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeStart,
                  pool[k][0],
                  offsetByteDelta = 6)
                
                firstGlyph += n
                nUnits += 1
        
        # add the sentinel (doesn't count toward nUnits)
        w.add("3H", 0xFFFF, 0xFFFF, 0)
        
        # we now know nUnits, so retrofit the BSH
        w.setReplaceableString(
          bStake,
          bsh.BSH(nUnits=nUnits, unitSize=6).binaryString())
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup4(self, keySpan):
        """
        Creates and returns a bytestring for the lookup-specific portions of
        the output data, for lookup format 4.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> utilities.hexdump(d._makeLookup4(ks))
               0 | 0004 0006 0003 000C  0001 0006 0006 0005 |................|
              10 | 002A 000F 000F 002E  0019 0019 0030 FFFF |.*...........0..|
              20 | FFFF 0000 0032 0032  0042 003A 0003 000A |.....2.2.B.:....|
              30 | 01F4 0320 0003 000A  01F4 0320 0002 00FA |... ....... ....|
              40 | 01F4                                     |..              |
        """
        
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 4)
        bsh.BSH(nUnits=len(keySpan), unitSize=6).buildBinary(w)
        pool = {}  # an id-pool
        offsetOffsets = [w.getNewStake() for obj in keySpan]
        
        for (spanStart, spanEnd), stake in zip(keySpan, offsetOffsets):
            w.add("2H", spanEnd, spanStart)
            w.addUnresolvedOffset("H", stakeStart, stake, offsetByteDelta=6)
        
        # add the sentinel (doesn't count toward nUnits)
        w.add("3H", 0xFFFF, 0xFFFF, 0)
        
        for (spanStart, spanEnd), stake in zip(keySpan, offsetOffsets):
            w.stakeCurrentWithValue(stake)
            
            for glyphIndex in range(spanStart, spanEnd + 1):
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeStart,
                  pool[thisID][0],
                  offsetByteDelta = 6)
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup6(self, keySpan):
        """
        Creates and returns a bytestring for the lookup-specific portions of
        the output data, for lookup format 6.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> utilities.hexdump(d._makeLookup6(ks))
               0 | 0006 0004 0004 0010  0002 0000 0005 0026 |...............&|
              10 | 0006 0026 000F 0036  0019 002E FFFF 0000 |...&...6........|
              20 | 0003 000A 01F4 0320  0003 000A 01F4 0320 |....... ....... |
              30 | 0002 00FA 01F4                           |......          |
        """
        
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 6)
        bsh.BSH(nUnits=len(self), unitSize=4).buildBinary(w)
        pool = {}  # an id-pool
        
        for spanStart, spanEnd in keySpan:  # a nice already-sorted source...
            for glyphIndex in range(spanStart, spanEnd + 1):
                w.add("H", glyphIndex)
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeStart,
                  pool[thisID][0],
                  offsetByteDelta = 6)
        
        # add the sentinel (doesn't count toward nUnits)
        w.add("2H", 0xFFFF, 0)
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup8(self, keySpan):
        """
        Creates and returns a bytestring for the lookup-specific portions of
        the output data, for lookup format 8.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> utilities.hexdump(d._makeLookup8(ks))
               0 | 0008 0005 0015 0036  0036 0000 0000 0000 |.......6.6......|
              10 | 0000 0000 0000 0000  0000 0046 0000 0000 |...........F....|
              20 | 0000 0000 0000 0000  0000 0000 0000 003E |...............>|
              30 | 0003 000A 01F4 0320  0003 000A 01F4 0320 |....... ....... |
              40 | 0002 00FA 01F4                           |......          |
        """
        
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 8)
        firstGlyph = keySpan[0][0]
        lastGlyph = keySpan[-1][1]
        w.add("2H", firstGlyph, lastGlyph - firstGlyph + 1)
        pool = {}  # an id-pool
        
        for glyphIndex in range(firstGlyph, lastGlyph + 1):
            if glyphIndex in self:
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset(
                  "H",
                  stakeStart,
                  pool[thisID][0],
                  offsetByteDelta = 6)
            
            else:
                w.add("H", 0)  # spec is unclear whether this is 0 or 0xFFFF
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _parseLookup0(self, w, makerFunc, **kwArgs):
        """
        Fills self from the walker data.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> s = utilities.fromhex("00 01 00 00 00 00") + d._makeLookup0(30)
        >>> w = walkerbit.StringWalker(s)
        >>> w.skip(8)
        >>> mf = splits_distance.Splits_Distance.fromwalker
        >>> d2 = Lcar()
        >>> d2._parseLookup0(w, mf, fontGlyphCount=30)
        >>> d == d2
        True
        >>> d2[5] is d2[6]
        True
        >>> d2[5] is d2[25], d2[5] == d2[25]
        (False, True)
        """
        
        offsets = w.group("H", kwArgs['fontGlyphCount'])
        missing = {0, 0xFFFF}  # the docs don't specify which
        pool = {}
        
        for glyphIndex, offset in enumerate(offsets):
            if offset not in missing:
                if offset not in pool:
                    pool[offset] = makerFunc(w.subWalker(offset))
                
                self[glyphIndex] = pool[offset]
    
    def _parseLookup2(self, w, makerFunc, **kwArgs):
        """
        Fills self from the walker data.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> s = utilities.fromhex("00 01 00 00 00 00") + d._makeLookup2(ks)
        >>> w = walkerbit.StringWalker(s)
        >>> w.skip(8)
        >>> mf = splits_distance.Splits_Distance.fromwalker
        >>> d2 = Lcar()
        >>> d2._parseLookup2(w, mf, fontGlyphCount=30)
        >>> d == d2
        True
        >>> d2[5] is d2[6]
        True
        >>> d2[5] is d2[25], d2[5] == d2[25]
        (False, True)
        """
        
        bshObj = bsh.BSH.fromwalker(w)
        fgc = kwArgs['fontGlyphCount']
        pool = {}
        
        if bshObj.unitSize != 6:
            raise ValueError("Bad unitSize in 'lcar' lookup format 2!")
        
        for lastGlyph, firstGlyph, offset in w.group("3H", bshObj.nUnits):
            if lastGlyph >= fgc:
                raise ValueError(
                  "'lcar' lookup 2 has segment outside font's glyph count!")
            
            if offset not in pool:
                pool[offset] = makerFunc(w.subWalker(offset))
            
            obj = pool[offset]
            
            for glyphIndex in range(firstGlyph, lastGlyph + 1):
                self[glyphIndex] = obj
    
    def _parseLookup4(self, w, makerFunc, **kwArgs):
        """
        Fills self from the walker data.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> s = utilities.fromhex("00 01 00 00 00 00") + d._makeLookup4(ks)
        >>> w = walkerbit.StringWalker(s)
        >>> w.skip(8)
        >>> mf = splits_distance.Splits_Distance.fromwalker
        >>> d2 = Lcar()
        >>> d2._parseLookup4(w, mf, fontGlyphCount=30)
        >>> d == d2
        True
        >>> d2[5] is d2[6]
        True
        >>> d2[5] is d2[25], d2[5] == d2[25]
        (False, True)
        """
        
        bshObj = bsh.BSH.fromwalker(w)
        fgc = kwArgs['fontGlyphCount']
        pool = {}
        
        if bshObj.unitSize != 6:
            raise ValueError("Bad unitSize in 'lcar' lookup format 4!")
        
        for lastGlyph, firstGlyph, offoff in w.group("3H", bshObj.nUnits):
            if lastGlyph >= fgc:
                raise ValueError(
                  "'lcar' lookup 4 has segment outside font's glyph count!")
            
            itGlyph = range(firstGlyph, lastGlyph + 1)
            
            offsets = (w.subWalker(offoff)).group(
              "H",
              lastGlyph - firstGlyph + 1)
            
            for glyphIndex, offset in zip(itGlyph, offsets):
                if offset not in pool:
                    pool[offset] = makerFunc(w.subWalker(offset))
                
                self[glyphIndex] = pool[offset]
    
    def _parseLookup6(self, w, makerFunc, **kwArgs):
        """
        Fills self from the walker data.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> s = utilities.fromhex("00 01 00 00 00 00") + d._makeLookup6(ks)
        >>> w = walkerbit.StringWalker(s)
        >>> w.skip(8)
        >>> mf = splits_distance.Splits_Distance.fromwalker
        >>> d2 = Lcar()
        >>> d2._parseLookup6(w, mf, fontGlyphCount=30)
        >>> d == d2
        True
        >>> d2[5] is d2[6]
        True
        >>> d2[5] is d2[25], d2[5] == d2[25]
        (False, True)
        """
        
        bshObj = bsh.BSH.fromwalker(w)
        fgc = kwArgs['fontGlyphCount']
        pool = {}
        
        if bshObj.unitSize != 4:
            raise ValueError("Bad unitSize in 'lcar' lookup format 6!")
        
        for glyphIndex, offset in w.group("2H", bshObj.nUnits):
            if glyphIndex >= fgc:
                raise ValueError(
                  "'lcar' lookup 6 has glyph outside font's glyph count!")
            
            if offset not in pool:
                pool[offset] = makerFunc(w.subWalker(offset))
            
            self[glyphIndex] = pool[offset]
    
    def _parseLookup8(self, w, makerFunc, **kwArgs):
        """
        Fills self from the walker data.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> ks = span.Span(d)
        >>> s = utilities.fromhex("00 01 00 00 00 00") + d._makeLookup8(ks)
        >>> w = walkerbit.StringWalker(s)
        >>> w.skip(8)
        >>> mf = splits_distance.Splits_Distance.fromwalker
        >>> d2 = Lcar()
        >>> d2._parseLookup8(w, mf, fontGlyphCount=30)
        >>> d == d2
        True
        >>> d2[5] is d2[6]
        True
        >>> d2[5] is d2[25], d2[5] == d2[25]
        (False, True)
        """
        
        firstGlyph, count = w.unpack("2H")
        fgc = kwArgs['fontGlyphCount']
        
        if firstGlyph + count > fgc:
            raise ValueError(
              "'lcar' lookup 8 has lastGlyph outside font's glyph count!")
        
        offsets = w.group("H", count)
        missing = {0, 0xFFFF}  # the docs don't specify which
        pool = {}
        
        for glyphIndex, offset in enumerate(offsets, firstGlyph):
            if offset not in missing:
                if offset not in pool:
                    pool[offset] = makerFunc(w.subWalker(offset))
                
                self[glyphIndex] = pool[offset]
    
    _dispatchTable = {
      0: _parseLookup0,
      2: _parseLookup2,
      4: _parseLookup4,
      6: _parseLookup6,
      8: _parseLookup8}
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Lcar object to the specified LinkedWriter.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> utilities.hexdump(d.binaryString(fontGlyphCount=30))
               0 | 0001 0000 0000 0006  0004 0004 0010 0002 |................|
              10 | 0000 0005 0026 0006  0026 000F 0036 0019 |.....&...&...6..|
              20 | 002E FFFF 0000 0003  000A 01F4 0320 0003 |............. ..|
              30 | 000A 01F4 0320 0002  00FA 01F4           |..... ......    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)
        dataFormats = {obj.dataFormat for obj in self.values()}
        
        if len(dataFormats) != 1:
            raise ValueError("Mixed splits types in Lcar table!")
        
        w.add("H", dataFormats.pop())
        fgc = kwArgs['fontGlyphCount']
        assert max(self) < fgc
        keySpan = span.Span(self)
        
        sv = [
          self._makeLookup0(fgc),
          self._makeLookup2(keySpan),
          self._makeLookup4(keySpan),
          self._makeLookup6(keySpan),
          self._makeLookup8(keySpan)]
        
        sv.sort(key=len)
        w.addString(sv[0])  # the shortest
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Lcar object from the specified walker.
        
        >>> s1 = splits_distance.Splits_Distance([10, 500, 800])
        >>> s2 = splits_distance.Splits_Distance([250, 500])
        >>> s3 = s1.__deepcopy__()
        >>> d = Lcar({5: s1, 6: s1, 15: s2, 25: s3})
        >>> d == Lcar.frombytes(
        ...   d.binaryString(fontGlyphCount=30),
        ...   fontGlyphCount=30)
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'lcar' table version: %s" % (version,))
        
        format = w.unpack("H")
        
        if format == 0:
            makerFunc = splits_distance.Splits_Distance.fromwalker
        elif format == 1:
            makerFunc = splits_point.Splits_Point.fromwalker
        else:
            raise ValueError("Unknown 'lcar' table format: %s" % (format,))
        
        lookupFormat = w.unpack("H")
        
        if lookupFormat not in cls._dispatchTable:
            raise ValueError(
              "Unknown lookup format %d in 'lcar' table" % (lookupFormat,))
        
        r = cls()
        cls._dispatchTable[lookupFormat](r, w, makerFunc, **kwArgs)
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer, walkerbit

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
