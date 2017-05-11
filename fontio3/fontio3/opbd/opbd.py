#
# opbd.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the AAT 'opbd' table.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.opbd import bounds_distance, bounds_point
from fontio3.utilities import bsh, span, writer

# -----------------------------------------------------------------------------

#
# Private functions
#

def _walkLookup(w, d, maker, fontGlyphCount):
    lookupFormat = w.unpack("H")
    pool = {}
    
    if lookupFormat == 0:
        
        # Despite what the docs say, a format 0 table is an array of offsets,
        # and NOT an array of actual 8-byte records. The offsets are measured
        # from the start of the 'opbd' table, not the start of the lookup.
        #
        # Also note that all records must be present; an offset of 0 or 0xFFFF
        # will be interpreted as an actual offset, and not as "data missing"!
        
        for i, offset in enumerate(w.group("H", fontGlyphCount)):
            if offset not in pool:
                pool[offset] = maker(w.subWalker(offset))
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    elif lookupFormat == 2:
        bshObj = bsh.BSH.fromwalker(w)
        
        for lastGlyph, firstGlyph, offset in w.group("3H", bshObj.nUnits):
            if offset not in pool:
                pool[offset] = maker(w.subWalker(offset))
            
            obj = pool[offset]
            
            if obj:
                for i in range(firstGlyph, lastGlyph + 1):
                    d[i] = obj
    
    elif lookupFormat == 4:
        
        # Despite what the docs say, the segment offset is relative to the
        # start of the lookup, not the start of the table. Furthermore, the
        # value at that offset is not the bounds objects directly, but rather
        # is a list of offsets (this time from the table, not the lookup!) to
        # the actual objects. Eeeek. (This was established by empirical means;
        # Apple Chancery has an 'opbd' table with lookup format 4)
        #
        # I've reported this to the Apple folks in an email on 9-Jul-2010.
        # Update: the docs are still incorrect as of 10-Jul-2012.
        
        bshObj = bsh.BSH.fromwalker(w)
        
        for lastGlyph, firstGlyph, offset in w.group("3H", bshObj.nUnits):
            count = lastGlyph - firstGlyph + 1
            wSub = w.subWalker(offset + 6)  # the +6 makes it lookup-relative
            
            for i, offset in enumerate(wSub.group("H", count), firstGlyph):
                if offset not in pool:
                    pool[offset] = maker(w.subWalker(offset))  # table-relative offset
                
                obj = pool[offset]
                
                if obj:
                    d[i] = obj
    
    elif lookupFormat == 6:
        bshObj = bsh.BSH.fromwalker(w)
        
        for i, offset in w.group("2H", bshObj.nUnits):
            if offset not in pool:
                pool[offset] = maker(w.subWalker(offset))
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    elif lookupFormat == 8:
        
        # Despite what the docs say, a format 8 table is an array of offsets,
        # and NOT an array of actual 8-byte records. The offsets are measured
        # from the start of the 'opbd' table, not the start of the lookup.
        #
        # Also note that all records must be present; an offset of 0 or 0xFFFF
        # will be interpreted as an actual offset, and not as "data missing"!
        
        firstGlyph, count = w.unpack("2H")
        
        for i, offset in enumerate(w.group("H", count), firstGlyph):
            if offset not in pool:
                pool[offset] = maker(w.subWalker(offset))
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    else:
        raise ValueError("Unknown lookup format in 'opbd' table: %d" % (lookupFormat,))

def _walkLookup_validated(w, d, maker, **kwArgs):
    logger = kwArgs['logger']
    fontGlyphCount = kwArgs['fontGlyphCount']
    pool = {}
    
    if w.length() < 2:
        logger.error(('V0004', (), "Lookup format missing or incomplete."))
        return False
    
    lookupFormat = w.unpack("H")
    
    if lookupFormat not in {0, 2, 4, 6, 8}:
        logger.error((
          'V0701',
          (lookupFormat,),
          "The lookup format %d is not recognized."))
        
        return False
    
    if lookupFormat == 0:
        
        # Despite what the docs say, a format 0 table is an array of offsets,
        # and NOT an array of actual 8-byte records. The offsets are measured
        # from the start of the 'opbd' table, not the start of the lookup.
        #
        # Also note that all records must be present; an offset of 0 or 0xFFFF
        # will be interpreted as an actual offset, and not as "data missing"!
        
        if w.length() < 2 * fontGlyphCount:
            logger.error((
              'V0702',
              (),
              "The lookup format 0 offsets are missing or incomplete."))
            
            return False
        
        offsets = w.group("H", fontGlyphCount)
        
        for i, offset in enumerate(offsets):
            if offset not in pool:
                
                obj = maker(
                  w.subWalker(offset),
                  logger = logger.getChild("glyph %d" % (i,)))
                
                if obj is None:
                    return False
                
                pool[offset] = obj
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    elif lookupFormat == 2:
        bshObj = bsh.BSH.fromvalidatedwalker(w, logger=logger)
        
        if bshObj is None:
            return False
        
        if bshObj.unitSize != 6:
            logger.error((
              'V0709',
              (bshObj.unitSize,),
              "Was expecting a unitSize of 6 in the binary search "
              "header for a format 2 lookup table, but got %d instead."))
            
            return False
        
        if w.length() < 6 * bshObj.nUnits:
            logger.error((
              'V0704',
              (),
              "The lookup format 2 index records are missing or incomplete."))
            
            return False
        
        recs = w.group("3H", bshObj.nUnits)
        badIndices = {recs[:2] for t in recs if t[1] > t[0]}
        
        if badIndices:
            logger.error((
              'V0705',
              (sorted(badIndices),),
              "The following glyph ranges have their start and end "
              "glyph indices swapped: %s"))
            
            return False
        
        if list(rec) != sorted(rec, key=operator.itemgetter(1)):
            logger.error((
              'V0715',
              (),
              "The segments are not sorted by first glyph."))
            
            return False
        
        countByRange = sum(t[0] - t[1] + 1 for t in rec)
        countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
        
        if countByRange != countBySet:
            logger.error((
              'V0716',
              (),
              "The segments have overlaps in glyph coverage."))
            
            return False
        
        for lastGlyph, firstGlyph, offset in recs:
            if lastGlyph == firstGlyph == 0xFFFF:
                continue
            
            if offset not in pool:
                
                obj = maker(
                  w.subWalker(offset),
                  logger = logger.getChild("glyph %d" % (firstGlyph,)))
                
                if obj is None:
                    return False
                
                pool[offset] = obj
            
            obj = pool[offset]
            
            if obj:
                for i in range(firstGlyph, lastGlyph + 1):
                    d[i] = obj
    
    elif lookupFormat == 4:
        
        # Despite what the docs say, the segment offset is relative to the
        # start of the lookup, not the start of the table. Furthermore, the
        # value at that offset is not the bounds objects directly, but rather
        # is a list of offsets (this time from the table, not the lookup!) to
        # the actual objects. Eeeek. (This was established by empirical means;
        # Apple Chancery has an 'opbd' table with lookup format 4)
        #
        # I've reported this to the Apple folks in an email on 9-Jul-2010.
        # Update: the docs are still incorrect as of 10-Jul-2012.
        
        bshObj = bsh.BSH.fromvalidatedwalker(w, logger=logger)
        
        if bshObj is None:
            return False
        
        if bshObj.unitSize != 6:
            logger.error((
              'V0709',
              (bshObj.unitSize,),
              "Was expecting a unitSize of 6 in the binary search "
              "header for a format 4 lookup table, but got %d instead."))
            
            return False
        
        if w.length() < 6 * bshObj.nUnits:
            logger.error((
              'V0706',
              (),
              "The data for the format 4 Lookup are missing "
              "or incomplete."))
            
            return False
        
        v = w.group("3H", bshObj.nUnits)
        badOrder = sorted(t[:2] for t in v if t[1] > t[0])
        
        if badOrder:
            logger.error((
              'V0705',
              (sorted(badOrder),),
              "The following glyph ranges have their start and end "
              "glyph indices swapped: %s"))
            
            return False
        
        if list(v) != sorted(v, key=operator.itemgetter(1)):
            logger.error((
              'V0715',
              (),
              "The segments are not sorted by first glyph."))
            
            return False
        
        countByRange = sum(t[0] - t[1] + 1 for t in v)
        countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
        
        if countByRange != countBySet:
            logger.error((
              'V0716',
              (),
              "The segments have overlaps in glyph coverage."))
            
            return False
        
        for lastGlyph, firstGlyph, offset in v:
            if lastGlyph == firstGlyph == 0xFFFF:
                continue
            
            count = lastGlyph - firstGlyph + 1
            wSub = w.subWalker(offset + 6)  # the +6 makes it lookup-relative
            
            if wSub.length() < 2 * count:
                logger.error((
                  'V0707',
                  (firstGlyph,),
                  "The offset array for the group starting with glyph %d "
                  "is missing or incomplete."))
                
                return False
            
            for i, offset in enumerate(wSub.group("H", count), firstGlyph):
                if offset not in pool:
                    
                    obj = maker(
                      w.subWalker(offset),  # table-relative offset
                      logger = logger.getChild(
                        "group starting at glyph %d" % (i,)))
                    
                    if obj is None:
                        return False
                    
                    pool[offset] = obj
                
                obj = pool[offset]
                
                if obj:
                    d[i] = obj
    
    elif lookupFormat == 6:
        bshObj = bsh.BSH.fromwalker(w)
        
        if bshObj is None:
            return False
        
        if bshObj.unitSize != 4:
            logger.error((
              'V0709',
              (bshObj.unitSize,),
              "Was expecting a unitSize of 4 in the binary search "
              "header for a format 6 lookup table, but got %d instead."))
            
            return False
        
        if w.length() < 4 * bshObj.nUnits:
            logger.error((
              'V0710',
              (),
              "The data for the format 6 Lookup are missing "
              "or incomplete."))
            
            return False
        
        v = w.group("2H", bshObj.nUnits)
        
        if len({t[0] for t in v}) != len(v):
            logger.error((
              'V0713',
              (),
              "There are duplicate glyphs in the format 6 data."))
            
            return False
        
        elif list(v) != sorted(v):
            logger.error((
              'V0714',
              (),
              "The glyphs are not sorted."))
            
            return False
    
        
        for i, offset in v:
            if offset not in pool:
                
                obj = maker(
                  w.subWalker(offset),
                  logger = logger.getChild("glyph %d" % (i,)))
                
                if obj is None:
                    return False
                
                pool[offset] = obj
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    else:
        
        # Despite what the docs say, a format 8 table is an array of offsets,
        # and NOT an array of actual 8-byte records. The offsets are measured
        # from the start of the 'opbd' table, not the start of the lookup.
        #
        # Also note that all records must be present; an offset of 0 or 0xFFFF
        # will be interpreted as an actual offset, and not as "data missing"!
        
        if w.length() < 4:
            logger.error((
              'V0711',
              (),
              "The format 8 header is missing or incomplete."))
            
            return False
        
        firstGlyph, count = w.unpack("2H")
        
        if w.length() < 2 * count:
            logger.error((
              'V0712',
              (),
              "The format 8 data is missing or incomplete."))
            
            return None
        
        for i, offset in enumerate(w.group("H", count), firstGlyph):
            if offset not in pool:
                
                obj = maker(
                  w.subWalker(offset),
                  logger = logger.getChild("glyph %d" % (i,)))
                
                pool[offset] = obj
            
            obj = pool[offset]
            
            if obj:
                d[i] = obj
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Opbd(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing optical bounds data for glyphs in a font. This is a
    sparse dict mapping glyph indices to either Bounds_Distance or
    Bounds_Point objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    xyz13:
      Left delta: 1
      Top delta: 2
      Right delta: 3
      Bottom delta: 4
    xyz14:
      Left delta: 1
      Top delta: 2
      Right delta: 3
      Bottom delta: 4
    xyz4:
      Left delta: 1
      Top delta: 2
      Right delta: 3
      Bottom delta: 4
    xyz5:
      Left delta: 1
      Top delta: 2
      Right delta: 3
      Bottom delta: 4
    xyz6:
      Left delta: 5
      Top delta: 6
      Right delta: 7
      Bottom delta: 8
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    attrSpec = dict(
        preferredFormat = dict(
            attr_initfunc = (lambda: None),
            attr_ignoreforcomparisons = True,
            attr_label = "Preferred format"))
    
    attrSorted = ()
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Opbd object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("opbd")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, format = w.unpack("LH")
        
        if version != 0x10000:
            logger.error((
              'V0782',
              (version,),
              "The 'opbd' version of 0x%08X is not recognized."))
            
            return None
        
        if format not in {0, 1}:
            logger.error((
              'V0783',
              (format,),
              "The format value should be 0 or 1, but is %d instead."))
            
            return None
        
        if format == 0:
            maker = bounds_distance.Bounds_Distance.fromvalidatedwalker
        else:
            maker = bounds_point.Bounds_Point.fromvalidatedwalker
        
        r = cls()
        
        if not _walkLookup_validated(w, r, maker, logger=logger, **kwArgs):
            return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Opbd object from the data in the specified
        walker. There is one required keyword argument: fontGlyphCount.
        
        >>> obj = _testingValues[0]
        >>> obj.setPreferredFormat(0)
        >>> obj == Opbd.frombytes(obj.binaryString(fontGlyphCount=20), fontGlyphCount=20)
        True
        >>> obj.setPreferredFormat(2)
        >>> obj == Opbd.frombytes(obj.binaryString(fontGlyphCount=20), fontGlyphCount=20)
        True
        >>> obj.setPreferredFormat(4)
        >>> obj == Opbd.frombytes(obj.binaryString(fontGlyphCount=20), fontGlyphCount=20)
        True
        >>> obj.setPreferredFormat(6)
        >>> obj == Opbd.frombytes(obj.binaryString(fontGlyphCount=20), fontGlyphCount=20)
        True
        >>> obj.setPreferredFormat(8)
        >>> obj == Opbd.frombytes(obj.binaryString(fontGlyphCount=20), fontGlyphCount=20)
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'opbd' version: %d" % (version,))
        
        format = w.unpack("H")
        
        if format == 0:
            maker = bounds_distance.Bounds_Distance.fromwalker
        elif format == 1:
            maker = bounds_point.Bounds_Point.fromwalker
        else:
            raise ValueError("Unknown format in 'opbd' table: %d" % (format,))
        
        r = cls()
        _walkLookup(w, r, maker, kwArgs['fontGlyphCount'])
        return r
    
    #
    # Private methods
    #
    
    def _addBest(self, fontGlyphCount, isDistanceKind):
        keySpan = span.Span(self)
        
        if keySpan[0][0] < 0 or keySpan[-1][1] >= fontGlyphCount:
            raise IndexError("One or more keys in Opbd table out of range!")
        
        if isDistanceKind:
            emptyObj = bounds_distance.Bounds_Distance()
        else:
            emptyObj = bounds_point.Bounds_Point()
        
        sv = [
          self._makeLookup0(fontGlyphCount, emptyObj),
          self._makeLookup2(keySpan),
          self._makeLookup4(keySpan),
          self._makeLookup6(keySpan),
          self._makeLookup8(keySpan, emptyObj)]
        
        if self.preferredFormat is not None:
            return sv[self.preferredFormat // 2]
        
        sv.sort(key=len)
        return sv[0]  # the shortest
    
    def _makeLookup0(self, fontGlyphCount, emptyObj):
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 0)
        pool = {}
        
        for i in range(fontGlyphCount):
            obj = self.get(i, emptyObj)
            objID = id(obj)
            
            if objID not in pool:
                pool[objID] = (w.getNewStake(), obj)
            
            w.addUnresolvedOffset("H", stakeStart, pool[objID][0], offsetByteDelta=6)  # table-relative
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup2(self, keySpan):
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 2)
        bStake = w.getNewStake()
        w.addReplaceableString(bStake, ' ' * 10)  # we don't know nUnits yet...
        pool = {}  # an id-pool; safe because scope is limited to this method
        nUnits = 0
        
        for spanStart, spanEnd in keySpan:
            firstGlyph = spanStart
            it = ((id(self[i]), self[i]) for i in range(spanStart, spanEnd + 1))
            
            for k, g in itertools.groupby(it, operator.itemgetter(0)):
                v = list(g)
                if k not in pool:
                    pool[k] = (w.getNewStake(), v[0][1])
                
                n = len(v)
                w.add("2H", firstGlyph + n - 1, firstGlyph)
                w.addUnresolvedOffset("H", stakeStart, pool[k][0], offsetByteDelta=6)  # table offset, not lookup offset
                firstGlyph += n
                nUnits += 1
        
        # add the sentinel (doesn't count toward nUnits)
        w.add("3H", 0xFFFF, 0xFFFF, 0)
        
        # we now know nUnits, so retrofit the BSH
        w.setReplaceableString(bStake, bsh.BSH(nUnits=nUnits, unitSize=6).binaryString())
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup4(self, keySpan):
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()  # start of lookup
        w.add("H", 4)
        bsh.BSH(nUnits=len(keySpan), unitSize=6).buildBinary(w)
        pool = {}  # id(obj) -> (objStake, obj)
        ooStakes = [w.getNewStake() for obj in keySpan]
        
        for (spanStart, spanEnd), stake in zip(keySpan, ooStakes):
            w.add("2H", spanEnd, spanStart)
            w.addUnresolvedOffset("H", stakeStart, stake)  # from lookup, not table!!
        
        # add the sentinel
        w.add("3H", 0xFFFF, 0xFFFF, 0)
        
        # add the offset vectors
        for (spanStart, spanEnd), stake in zip(keySpan, ooStakes):
            w.stakeCurrentWithValue(stake)
            
            for glyphIndex in range(spanStart, spanEnd + 1):
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset("H", stakeStart, pool[thisID][0], offsetByteDelta=6)  # from table, not lookup!!
        
        # add the actual objects
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup6(self, keySpan):
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 6)
        bsh.BSH(nUnits=len(self), unitSize=4).buildBinary(w)
        pool = {}  # an id-pool
        
        for spanStart, spanEnd in keySpan:  # a convenient already-sorted source...
            for glyphIndex in range(spanStart, spanEnd + 1):
                w.add("H", glyphIndex)
                obj = self[glyphIndex]
                thisID = id(obj)
                
                if thisID not in pool:
                    pool[thisID] = (w.getNewStake(), obj)
                
                w.addUnresolvedOffset("H", stakeStart, pool[thisID][0], offsetByteDelta=6)
        
        # add the sentinel (doesn't count toward nUnits)
        w.add("2H", 0xFFFF, 0)
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    def _makeLookup8(self, keySpan, emptyObj):
        w = writer.LinkedWriter()
        stakeStart = w.stakeCurrent()
        w.add("H", 8)
        firstGlyph = keySpan[0][0]
        count = keySpan[-1][1] - firstGlyph + 1
        w.add("2H", firstGlyph, count)
        pool = {}
        
        for i in range(firstGlyph, firstGlyph + count):
            obj = self.get(i, emptyObj)
            objID = id(obj)
            
            if objID not in pool:
                pool[objID] = (w.getNewStake(), obj)
            
            w.addUnresolvedOffset("H", stakeStart, pool[objID][0], offsetByteDelta=6)  # table-relative
        
        # Now add the deferred values
        for stake, obj in sorted(pool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        return w.binaryString()
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Opbd object to the specified
        LinkedWriter.
        
        >>> obj = _testingValues[0]
        >>> obj.setPreferredFormat(0)
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=20))
               0 | 0001 0000 0000 0000  0030 0030 0030 0038 |.........0.0.0.8|
              10 | 0038 0040 0030 0030  0030 0030 0030 0030 |.8.@.0.0.0.0.0.0|
              20 | 0038 0038 0030 0030  0030 0030 0030 0030 |.8.8.0.0.0.0.0.0|
              30 | 0000 0000 0000 0000  0001 0002 0003 0004 |................|
              40 | 0005 0006 0007 0008                      |........        |
        
        >>> obj.setPreferredFormat(2)
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=20))
               0 | 0001 0000 0000 0002  0006 0003 000C 0001 |................|
              10 | 0006 0004 0003 002A  0005 0005 0032 000D |.......*.....2..|
              20 | 000C 002A FFFF FFFF  0000 0001 0002 0003 |...*............|
              30 | 0004 0005 0006 0007  0008                |..........      |
        
        >>> obj.setPreferredFormat(4)
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=20))
               0 | 0001 0000 0000 0004  0006 0002 000C 0001 |................|
              10 | 0000 0005 0003 001E  000D 000C 0024 FFFF |.............$..|
              20 | FFFF 0000 002E 002E  0036 002E 002E 0001 |.........6......|
              30 | 0002 0003 0004 0005  0006 0007 0008      |..............  |
        
        >>> obj.setPreferredFormat(6)
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=20))
               0 | 0001 0000 0000 0006  0004 0005 0010 0002 |................|
              10 | 0004 0003 002A 0004  002A 0005 0032 000C |.....*...*...2..|
              20 | 002A 000D 002A FFFF  0000 0001 0002 0003 |.*...*..........|
              30 | 0004 0005 0006 0007  0008                |..........      |
        
        >>> obj.setPreferredFormat(8)
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=20))
               0 | 0001 0000 0000 0008  0003 000B 002A 002A |.............*.*|
              10 | 0032 0022 0022 0022  0022 0022 0022 002A |.2.".".".".".".*|
              20 | 002A 0000 0000 0000  0000 0001 0002 0003 |.*..............|
              30 | 0004 0005 0006 0007  0008                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)
        
        # make sure all the values are the same kind
        kinds = {obj.isDistance for obj in self.values()}
        assert len(kinds) == 1, "Mixed record kinds in Opbd object!"
        isDistanceKind = kinds.pop()
        w.add("H", (0 if isDistanceKind else 1))
        w.addString(self._addBest(kwArgs['fontGlyphCount'], isDistanceKind))
    
    def setPreferredFormat(self, format):
        """
        If the client wishes the output to be in a particular lookup format,
        this method can be called. Normally this won't be needed, as the code
        will always choose the smallest representation.
        """
        
        self.preferredFormat = format

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    d1 = bounds_distance.Bounds_Distance(1, 2, 3, 4)
    d2 = bounds_distance.Bounds_Distance(5, 6, 7, 8)
    
    _testingValues = (
        Opbd({3: d1, 4: d1, 5: d2, 12: d1, 13: d1}),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


