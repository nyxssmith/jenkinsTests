#
# loca.py
#
# Copyright © 2004-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Functions and classes for displaying and editing data from the 'loca' table.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Loca(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects containing offset data into a 'glyf' table for the starts of
    glyphs. This table is usually only needed on font input or output, as the
    live Glyph objects are what carry the semantic utility.
    
    These are lists of (offset, byteLength) pairs, and there are the same
    number of entries as there are in the 'glyf' table. Note this is a change
    from the old fontio class!
    
    >>> _testingValues[1].pprint()
    Glyph 0: Offset 0x00000000, length 50
    Glyph 1: Offset 0x00000032, length 200
    Glyph 2: Offset 0x000000FA, length 150
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintlabelfunc = (lambda i: "Glyph %d" % (i,)),
        item_pprintfunc = (
          lambda p, x, label:
          p.simple("Offset 0x%08X, length %d" % x, label=label)),
        seq_indexisglyphindex = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Loca object to the specified LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0000                                     |..              |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0000 0019 007D 00C8                      |.....}..        |
        
        >>> h(_testingValues[2].binaryString())
               0 | 0000 0000 0000 0032  0002 2312 0002 2326 |.......2..#...#&|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            it = map(operator.itemgetter(0), self)
            
            if self.needsLongOffsets():
                w.addGroup("L", it)
                w.add("L", self[-1][0] + self[-1][1])
            
            else:
                w.addGroup("H", (n // 2 for n in it))
                w.add("H", (self[-1][0] + self[-1][1]) // 2)
        
        else:
            w.add("H", 0)
    
    @classmethod
    def fromglyfobject(cls, glyfObj, **kwArgs):
        """
        Returns a new Loca instance from the specified Glyf object. There is
        one optional keyword argument:
        
            glyfBinStringList   If present, it should be an empty list on entry
                                to this method. This method will fill it with
                                the binary strings for all glyphs. This can
                                then be used by the caller to prevent
                                duplication in generating the binary data.
        """
        
        minGlyphIndex = min(glyfObj)
        assert minGlyphIndex == 0
        maxGlyphIndex = max(glyfObj)
        assert maxGlyphIndex == (len(glyfObj) - 1)
        walkOffset = 0
        v = []
        bsCachedList = kwArgs.get('glyfBinStringList')
        
        for i in range(len(glyfObj)):
            bs = glyfObj[i].binaryString()
            
            if bsCachedList is not None:
                bsCachedList.append(bs)
            
            v.append((walkOffset, len(bs)))
            walkOffset += len(bs)
        
        return cls(v)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker, but with validation.
        
        The following keyword arguments are supported:
        
            fontGlyphCount      The glyph count from the 'maxp' table. This is
                                required.
            
            glyfLength          The byte length of the 'glyf' table. This is
                                required.
            
            isLongOffsets       If True, the offsets are four bytes long and
                                represent byte positions. If False, the offsets
                                are two bytes long and represent word positions
                                (these will be converted into byte offsets for
                                the final returned object). This is required.
            
            logger              A logger to which notices will be posted. This
                                is optional; the default logger will be used if
                                this is not provided.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('loca')
        else:
            logger = logger.getChild('loca')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        isLong = kwArgs['isLongOffsets']
        fontGlyphCount = kwArgs['fontGlyphCount']
        glyfLength = kwArgs['glyfLength']
        
        if w.length() != (4 if isLong else 2) * (fontGlyphCount + 1):
            logger.error((
              'E1701',
              (),
              "'loca' table length does not match font's glyph count "
              "and long-offset state."))
            
            return None
        
        v = list(w.group(("L" if isLong else "H"), fontGlyphCount + 1))
        
        if not isLong:
            v = [2 * n for n in v]
        
        # At this point, v is byte offsets
        
        if v != sorted(v):
            logger.error((
              'E1702',
              (),
              "'loca' table entries are not sorted."))
            
            return None
        
        if v[-1] > glyfLength:
            logger.error((
              'V0951',
              (v[-1], glyfLength),
              "The last 'loca' entry ends at 0x%08X, but the 'glyf' "
              "table reports being only 0x%08X bytes long."))
            
            return None
        
        possibleBads = {(i, n) for i, n in enumerate(v) if n >= glyfLength}
        
        if len(possibleBads) > 1:
            # remove last contiguous band, then check for stragglers
            i = len(v) - 1
            n = v[-1]
            emptiesAtEnd = set()
            
            while (i, n) in possibleBads:
                emptiesAtEnd.add(i)
                possibleBads.discard((i, n))
                i -= 1
            
            emptiesAtEnd.discard(len(v) - 1)
            
            if emptiesAtEnd:
                logger.warning((
                  'V0294',
                  (min(emptiesAtEnd),),
                  "Glyphs starting at %d are all zero-length."))
            
            for i, n in sorted(possibleBads):
                logger.error((
                  'E1703',
                  (i, n),
                  "Byte offset for glyph %d is %d, which is outside "
                  "the 'glyf' table's boundaries."))
        
        it = zip(iter(v), itertools.islice(v, 1, None))
        r = cls((a, b-a) for a, b in it)
        
        if any(t[0] % 4 for t in r):
            logger.warning((
              'W1701',
              (),
              "Not all glyphs are longword-aligned."))
        
        if r[-1][0] + r[-1][1] < glyfLength:
            logger.warning((
              'W1702',
              (),
              "There is an unused gap at the end of the 'glyf' table."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Loca instance from the specified walker. There is one
        required keyword argument:
        
            isLongOffsets       If True, the offsets are four bytes long and
                                represent byte positions. If False, the offsets
                                are two bytes long and represent word positions
                                (these will be converted into byte offsets for
                                the final returned object).
        
        >>> _testingValues[0] == Loca.frombytes(
        ...   _testingValues[0].binaryString(),
        ...   isLongOffsets = False)
        True
        
        >>> _testingValues[1] == Loca.frombytes(
        ...   _testingValues[1].binaryString(),
        ...   isLongOffsets = False)
        True
        
        >>> _testingValues[2] == Loca.frombytes(
        ...   _testingValues[2].binaryString(),
        ...   isLongOffsets = True)
        True
        """
        
        bytesAvailable = int(w.length())
        assert bytesAvailable == w.length()  # can't be non-byte aligned
        
        if kwArgs['isLongOffsets']:
            assert (bytesAvailable % 4) == 0
            entryCount = bytesAvailable // 4
            v = w.group("L", entryCount)
            r = cls((v[i], v[i + 1] - v[i]) for i in range(entryCount - 1))
        
        else:
            assert (bytesAvailable % 2) == 0
            entryCount = bytesAvailable // 2
            v = w.group("H", entryCount)
            
            r = cls(
              (2 * v[i], 2 * (v[i + 1] - v[i]))
              for i in range(entryCount - 1))
        
        return r
    
    def needsLongOffsets(self):
        """
        Returns True if the 'loca' table generated from this data required long
        (i.e. 4-byte) offsets.
        
        >>> _testingValues[1].needsLongOffsets()
        False
        
        >>> _testingValues[2].needsLongOffsets()
        True
        """
        
        if self:
            last = self[-1]
            return (last[0] + last[1]) >= 0x20000
        
        return False

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Loca(),
        Loca([(0, 50), (50, 200), (250, 150)]),  # OK to use short
        Loca([(0, 50), (50, 140000), (140050, 20)]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
