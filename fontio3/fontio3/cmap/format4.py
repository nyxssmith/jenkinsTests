#
# format4.py
#
# Copyright © 2004-2014, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 4 ``'cmap'`` subtables. These are the most common subtables
in use for Unicodes in the Basic Multilingual Plane (BMP).
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.utilities import bsh, span2, writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Format4(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format4`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``map_compactremovesfalses``:
    
    >>> d = Format4({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format4({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format4({15: 3}, language = 1)
    >>> d2 = Format4({15: 3}, language = 2)
    >>> d1 == d2
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectvalues = True,
        map_compactremovesfalses = True)
    
    attrSpec = dict(
        language = dict(
            attr_ignoreforcomparisons = True,
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def _buildBinary_sub(self, contigRanges):
        """
        Does the actual work for binary string building. This method returns
        None if so many idRangeOffset values get accumulated that the offsets
        go over 64K; in this case the caller will redo the contigRanges via
        subdivision, which will always succeed.
        """
        
        w = writer.LinkedWriter()
        startLength = w.byteLength
        w.add("H", 4)  # format
        lengthStake = w.addDeferredValue("H")
        w.add("H", (self.language or 0))
        segCount = len(contigRanges) + 1
        idDeltas = [0] * len(contigRanges)
        idRangeOffsets = [0] * len(contigRanges)
        currentGIA = []
        f = self._fmt4Analyze
        
        for i, x in enumerate(contigRanges):
            glyphs = [self.get(k, 0) for k in range(x[0], x[1]+1)]
            idDelta = f(glyphs, x[0])
            idDeltas[i] = idDelta % 65536
            
            if idDelta == 0:
                ro = 2 * (len(currentGIA) + segCount - i)
                
                if ro >= 0x10000:
                    return None
                
                idRangeOffsets[i] = ro
                currentGIA.extend(glyphs)
            
            else:
                idRangeOffsets[i] = 0
        
        idDeltas.append(1)
        idRangeOffsets.append(0)
        w.add("H", 2 * segCount)
        bshObj = bsh.BSH(nUnits=segCount, unitSize=2)
        w.addString(bshObj.binaryString(skipUnitSize=True)[2:])
        w.addGroup("H", (x[1] for x in contigRanges))
        w.add("hH", -1, 0)
        w.addGroup("H", (x[0] for x in contigRanges))
        w.add("h", -1)
        w.addGroup("H", idDeltas)
        w.addGroup("H", idRangeOffsets)
        
        if currentGIA:
            w.addGroup("H", currentGIA)
        
        # We pin the length field to FFFF in case it's larger.
        byteSize = min(0xFFFF, w.byteLength - startLength)
        w.setDeferredValue(lengthStake, "H", byteSize)
        return w.binaryString()
    
    @staticmethod
    def _fmt4Analyze(glyphs, startCode):
        """
        Determines the idDelta for the specified list of glyphs. Missing glyphs are
        ignored as long as they don't break the sequence.
    
        >>> Format4._fmt4Analyze([12, 13, 14, 15], 60)
        -48
        >>> Format4._fmt4Analyze([12, 0, 14, 15], 60)
        -48
        >>> Format4._fmt4Analyze([12, 19, 14, 15], 60)
        0
        """
    
        g = utilities.monotonicGroupsGenerator(glyphs, allowZeroes=True)
        return (glyphs[0] - startCode if len(list(g)) == 1 else 0)

    def _preBuildValidate(self):
        """
        Checks that all keys and values are in the range 0..FFFF. Raises a
        ValueError if any are not.
        """
        
        if not self:
            return
        
        if min(self) < 0 or max(self) > 0xFFFF:
            raise ValueError(
              "One or more keys out of range for format 4 subtable!")
        
        if min(self.values()) < 0 or max(self.values()) > 0xFFFF:
            raise ValueError(
              "One or more values out of range for format 4 subtable!")
    
    def _subdivide(self, keepZeroes=False):
        """
        Returns a list with (first, last) pairs of keys that are contiguous and
        whose associated glyphs are monotonic.
        
        >>> obj = Format4({50: 4, 51: 5, 52: 6, 53: 10, 54: 11, 60: 12})
        >>> obj._subdivide()
        [(50, 52), (53, 54), (60, 60)]
        """
        
        r = []
        mgg = utilities.monotonicGroupsGenerator
        
        for uFirst, uLast in span2.Span(self).ranges():
            gVec = [self[u] for u in range(uFirst, uLast + 1)]
            pieceIndex = 0
            
            for piece in mgg(gVec, allowZeroes=keepZeroes):
                pieceLen = piece[1] - piece[0]
                
                r.append((
                  uFirst + pieceIndex,
                  uFirst + pieceIndex + pieceLen - 1))
                
                pieceIndex += pieceLen
        
        return r
    
    @staticmethod
    def _validate_binSearch(w, logger):
        bad = (False, None)
        
        if w.length() < 2:
            logger.error(('V0017', (), "Insufficient bytes for segCount."))
            return bad
        
        segCountTimesTwo = w.unpack("H")
        
        if segCountTimesTwo % 2:
            logger.error(('E0312', (), "Segment count times two is odd."))
            return bad
        
        segCount = segCountTimesTwo // 2
        
        if segCount:
            logger.info(('V0018', (segCount,), "There are %d segments."))
        else:
            logger.warning(('V0945', (), "The format 4 segment count is 0."))
        
        if w.length() < 6:
            logger.error((
              'V0019',
              (),
              "Insufficient bytes for binary search fields."))
            
            return bad
        
        searchRange, entrySelector, rangeShift = w.unpack("3H")
        bshAvatar = bsh.BSH(nUnits=segCount, unitSize=2)
        
        if searchRange != bshAvatar.searchRange:
            logger.warning((
              'E0311',
              (searchRange, bshAvatar.searchRange),
              "Incorrect searchRange 0x%04X; should be 0x%04X."))
        
        else:
            logger.info(('V0020', (), "searchRange is correct."))
        
        if entrySelector != bshAvatar.entrySelector:
            logger.warning((
              'E0305',
              (entrySelector, bshAvatar.entrySelector),
              "Incorrect entrySelector 0x%04X; should be 0x%04X."))
        
        else:
            logger.info(('V0021', (), "entrySelector is correct."))
        
        if rangeShift != bshAvatar.rangeShift:
            logger.warning((
              'E0309',
              (rangeShift, bshAvatar.rangeShift),
              "Incorrect rangeShift 0x%04X; should be 0x%04X."))
        
        else:
            logger.info(('V0022', (), "rangeShift is correct."))
        
        return True, segCount
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        bad = (False, None)
        
        if endOfWalker < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return bad
        
        format, size, language = w.unpack("3H")
        
        if format != 4:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return bad
        
        if endOfWalker > 0xFFFF:
            # The format allows subtables larger than 64K, although the length
            # field is limited to two bytes. This is detected by the special
            # value 0xFFFF in the length field.
            
            if size != 0xFFFF:
                logger.warning((
                  'V0009',
                  (),
                  "Size field is not 0xFFFF special value."))
            
            else:
                logger.info((
                  'V0010',
                  (),
                  "Size field has correct special 0xFFFF value."))
        
        elif endOfWalker != size:
            logger.warning((
              'V0011',
              (int(size), int(endOfWalker)),
              "Size field value (0x%04X) is not expected (0x%04X)."))
        
        logger.info(('V0005', (language,), "Language code is %d."))
        return True, language
    
    @staticmethod
    def _validate_ranges(w, logger, segCount):
        bad = (False, None, None, None)
        
        if w.length() < 2 * segCount:
            logger.error(('V0023', (), "Insufficient bytes for endCodes."))
            return bad
        
        endCodes = w.group("H", segCount)
        
        if list(endCodes) != sorted(endCodes):
            logger.error(('E0304', (), "endCodes not sorted."))
            return bad
        
        if endCodes[-1] != 0xFFFF:
            logger.error(('E0306', (), "Last endCode value not 0xFFFF."))
            return bad
        
        logger.info(('V0024', (), "endCodes are correct."))
        
        if w.length() < 2:
            logger.error(('V0025', (), "Insufficient bytes for reservedPad."))
            return bad
        
        reservedPad = w.unpack("H")
        
        if reservedPad:
            logger.warning(('E0310', (), "Nonzero reservedPad value."))
        else:
            logger.info(('V0026', (), "Correct zero reservedPad value."))
        
        if w.length() < 2 * segCount:
            logger.error(('V0027', (), "Insufficient bytes for startCodes."))
            return bad
        
        startCodes = w.group("H", segCount)
        
        if list(startCodes) != sorted(startCodes):
            logger.error(('V0028', (), "startCodes not sorted."))
            return bad
        
        if startCodes[-1] != 0xFFFF:
            logger.error(('V0029', (), "Last startCode value not 0xFFFF."))
            return bad
        
        # check that all startCodes are <= all endCodes
        if any(s > e for s, e in zip(startCodes, endCodes)):
            logger.error((
              'E0313',
              (),
              "One or more startCodes greater than corresponding endCodes."))
            
            return bad
        
        logger.info(('V0030', (), "startCodes are correct."))
        
        if w.length() < 2 * segCount:
            logger.error(('V0031', (), "Insufficient bytes for idDeltas."))
            return bad
        
        idDeltas = w.group("H", segCount)   # yes, unsigned
        
        if any(idDeltas):
            logger.info(('V0032', (), "Nonzero idDeltas are present."))
        else:
            logger.info(('V0033', (), "All idDeltas are zero."))
        
        return True, endCodes, startCodes, idDeltas
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (see below)
        :return: None
        :raises ValueError: if one or more values cannot fit into two bytes
        
        The following ``kwArgs`` are supported:
        
        ``keepZeroGlyphUnicodes``
            If False (the default) entries explicitly mapping to glyph 0 will
            be removed, since the defined ``'cmap'`` behavior is to map all
            unmapped character codes to glyph 0 anyway. However, sometimes the
            explicit zero should be kept; if you want this, set this flag to
            True.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0004 0018 0000 0002  0002 0000 0000 FFFF |................|
              10 | 0000 FFFF 0001 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0004 0020 0000 0004  0004 0001 0000 002A |... ...........*|
              10 | FFFF 0000 002A FFFF  003A 0001 0000 0000 |.....*...:......|
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0004 0020 0000 0004  0004 0001 0000 002B |... ...........+|
              10 | FFFF 0000 002A FFFF  003A 0001 0000 0000 |.....*...:......|
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0004 0028 0000 0006  0004 0001 0002 002B |...(...........+|
              10 | 1234 FFFF 0000 002A  1234 FFFF 003A EDD1 |.4.....*.4...:..|
              20 | 0001 0000 0000 0000                      |........        |
        """
        
        keepZeroes = kwArgs.pop('keepZeroGlyphUnicodes', False)
        self._preBuildValidate()
        bs = self._buildBinary_sub(list(span2.Span(self).ranges()))
        
        if bs is None:
            bs = self._buildBinary_sub(self._subdivide(keepZeroes=keepZeroes))
        
        w.addString(bs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format4`` instance from the specified walker,
        performing validation on the correctness of the binary data.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (see below)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        The following ``kwArgs`` are supported:
        
        ``keepZeroGlyphUnicodes``
            Default is False. As the binary data are unpacked, normally any
            explicit maps to glyph zero are removed, since unmapped characters
            always get mapped to glyph zero. If this flag is True, however,
            then these explicit zero maps will be kept.
        
        ``logger``
            A logger to which validation information will be posted.
        
        >>> logger = utilities.makeDoctestLogger('test.cmap')
        >>> s = _testingValues[3].binaryString()
        >>> fvb = Format4.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format4 - DEBUG - Walker has 40 remaining bytes.
        test.cmap.format4 - INFO - Language code is 0.
        test.cmap.format4 - INFO - There are 3 segments.
        test.cmap.format4 - INFO - searchRange is correct.
        test.cmap.format4 - INFO - entrySelector is correct.
        test.cmap.format4 - INFO - rangeShift is correct.
        test.cmap.format4 - INFO - endCodes are correct.
        test.cmap.format4 - INFO - Correct zero reservedPad value.
        test.cmap.format4 - INFO - startCodes are correct.
        test.cmap.format4 - INFO - Nonzero idDeltas are present.
        test.cmap.format4 - INFO - 3 unique character codes mapped to 3 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format4 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format4 - ERROR - Insufficient bytes.
        
        >>> fvb(b'A' + s[1:], logger=logger)
        test.cmap.format4 - DEBUG - Walker has 40 remaining bytes.
        test.cmap.format4 - ERROR - Invalid format (0x4104).
        
        xxx add more tests here
        """
        
        keepZeroes = kwArgs.pop('keepZeroGlyphUnicodes', False)
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format4')
        else:
            logger = logger.getChild('format4')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        okToProceed, language = cls._validate_header(w, logger, endOfWalker)
        
        if not okToProceed:
            return None
        
        r = cls(language=language)
        okToProceed, segCount = cls._validate_binSearch(w, logger)
        
        if not okToProceed:
            return None
        
        if not segCount:
            return r
        
        okToProceed, endCodes, startCodes, idDeltas = cls._validate_ranges(
          w,
          logger,
          segCount)
        
        if not okToProceed:
            return None
        
        # now walk each segment and retrieve a vector of relevant GIA data
        if w.length() < 2 * (segCount - 1):
            logger.error((
              'V0034',
              (),
              "Insufficient bytes for idRangeOffsets."))
            
            return None
        
        for i in range(segCount - 1):
            offset = w.unpack("H")
            
            if offset:
                subW = w.subWalker(offset - 2, relative=True)
                count = endCodes[i] - startCodes[i] + 1
                
                if subW.length() < 2 * count:
                    logger.error((
                      'V0035',
                      (),
                      "Attempt to read past the end of the subtable."))
                    
                    return None
                
                v = subW.group("H", count)
                
                for j, glyph in enumerate(v):
                    if glyph or keepZeroes:
                        r[startCodes[i] + j] = (glyph + idDeltas[i]) % 65536
            
            else:
                for charCode in range(startCodes[i], endCodes[i] + 1):
                    r[charCode] = (charCode + idDeltas[i]) % 65536
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format4`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (see below)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        The following ``kwArgs`` are supported:
        
        ``keepZeroGlyphUnicodes``
            Default is False. As the binary data are unpacked, normally any
            explicit maps to glyph zero are removed, since unmapped characters
            always get mapped to glyph zero. If this flag is True, however,
            then these explicit zero maps will be kept.
        
        >>> fb = Format4.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        
        >>> _testingValues[3] == fb(_testingValues[3].binaryString())
        True
        """
        
        format, size, language = w.unpack("3H")
        keepZeroes = kwArgs.pop('keepZeroGlyphUnicodes', False)
        
        if format != 4:
            raise ValueError("Bad format 4 subtable format!")
        
        r = cls(language=language)
        segCount = w.unpack("Hxxxxxx") // 2
        endCodes = w.group("H", segCount)
        w.skip(2)  # I no longer even remember why we put this in, sigh
        startCodes = w.group("H", segCount)
        idDeltas = w.group("H", segCount)
        
        # now walk each segment and retrieve a vector of relevant GIA data
        for i in range(segCount - 1):
            offset = w.unpack("H")
            
            if offset:
                subW = w.subWalker(offset - 2, relative=True)
                count = endCodes[i] - startCodes[i] + 1
                v = subW.group("H", count)
                
                for j, glyph in enumerate(v):
                    if glyph or keepZeroes:
                        r[startCodes[i] + j] = (glyph + idDeltas[i]) % 65536
            
            else:
                for charCode in range(startCodes[i], endCodes[i] + 1):
                    r[charCode] = (charCode + idDeltas[i]) % 65536
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        Format4(),
        Format4({42: 100}),
        Format4({42: 100, 43: 101}),
        Format4({42: 100, 43: 101, 0x1234: 5}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
