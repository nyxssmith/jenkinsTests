#
# format2.py
#
# Copyright © 2004-2011, 2013, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 ``'cmap'`` subtables. These allow mixed 8/16-bit character
encodings, such as the old Apple Shift-JIS format. They are not terribly useful
for modern encodings such as Unicode; formats 4 and 12 are preferred there.
"""

# System imports
import collections
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Format2(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format2`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``map_compactremovesfalses``:
    
    >>> d = Format2({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format2({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format2({15: 3}, language = 1)
    >>> d2 = Format2({15: 3}, language = 2)
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
    
    def _checkForOneTwoConflicts(self):
        """
        Creates the dict of [highByte][lowByte] mappings, and checks it make
        sure there are no high bytes that are also the first bytes of a
        two-byte value.
        
        Returns the [high][low] dict.
        """
        
        byHighByte = collections.defaultdict(dict)
        
        byHighByte[0] = {}  # we always force this, in order to
                            # support special single-byte handling
        
        for key, value in self.items():
            high, low = divmod(key, 256)
            byHighByte[high][low] = value
        
        for oneByteChar in byHighByte[0]:
            if oneByteChar and (oneByteChar in byHighByte):
                raise ValueError(
                  "Same value as one-byte and high-byte of two-byte key!")
        
        return byHighByte
    
    @staticmethod
    def _makeSubHeader(dLow, roPool, isZeroCase):
        """
        Creates and returns a tuple with 4 elements from the specified low-byte
        dict:
        
            [0] firstCode
            [1] entryCount (will always be 256 for the zero case)
            [2] idDelta (unsigned, cast from signed)
            [3] a tuple of the range offset values
        
        The new range will be checked against the existing ranges in the pool,
        and the same object will be reused, if possible. If a new object ends
        up being used, it is added to the pool.
        """
        
        firstCode = (0 if isZeroCase else min(dLow))
        entryCount = (256 if isZeroCase else max(dLow) - firstCode + 1)
        
        thisTopo = tuple(
          dLow.get(i, 0)
          for i in range(firstCode, firstCode + entryCount))
        
        if roPool:
            
            # If there is an existing pool entry with the same topology as
            # thisTopo, we use it with a modified idDelta; otherwise we just
            # use an idDelta of 0 and use the normal approach.
            
            for topo in roPool:
                if len(topo) == len(thisTopo):
                    diffPool = set()
                    
                    for x, y in zip(topo, thisTopo):
                        if (x == 0) != (y == 0):
                            break  # no match, topologies differ
                        
                        if x:
                            thisDiff = x - y
                            
                            if diffPool and (thisDiff not in diffPool):
                                break  # no match, topologies differ
                            
                            diffPool.add(thisDiff)
                    
                    else:
                        idRangeTuple = topo
                        break  # out of topo loop
            
            else:
                idRangeTuple = thisTopo
                roPool[idRangeTuple] = len(roPool)
        
        else:
            idRangeTuple = thisTopo
            roPool[idRangeTuple] = len(roPool)
        
        idDelta = (thisTopo[0] - idRangeTuple[0]) % 0x10000
        return (firstCode, entryCount, idDelta, idRangeTuple)
    
    def _preBuildValidate(self):
        """
        Checks that all keys and values are in the range 0..FFFF. Raises a
        ValueError if any are not.
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFFFF:
                raise ValueError(
                  "One or more keys out of range for format 2 subtable!")
            
            if value < 0 or value > 0xFFFF:
                raise ValueError(
                  "One or more values out of range for format 2 subtable!")
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: None
        :raises ValueError: if one or more values cannot fit into two bytes
        
        >>> Format2({100000: 5}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: One or more keys out of range for format 2 subtable!
        
        >>> Format2({5: 90000}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: One or more values out of range for format 2 subtable!
        """
        
        self._preBuildValidate()
        wWork = writer.LinkedWriter()
        startLength = 0  # we just created the writer, so its length is zero
        wWork.add("H", 2)
        byHighByte = self._checkForOneTwoConflicts()
        lengthStake = wWork.addDeferredValue("H")
        wWork.add("H", (self.language or 0))
        rangeOffsetPool = {}  # idRangeTuple -> sequence number
        subHeaders = []
        
        for highByte in range(256):
            if highByte not in byHighByte:
                wWork.add("H", 0)  # no subHeaderKey for this high byte
                continue
            
            wWork.add("H", 8 * len(subHeaders))
            
            subHeaders.append(
              self._makeSubHeader(
                byHighByte[highByte],
                rangeOffsetPool,
                highByte == 0))
        
        roStakePool = dict(
          (key, wWork.getNewStake())
          for key in rangeOffsetPool)
        
        for firstCode, entryCount, idDelta, idRangeTuple in subHeaders:
            wWork.add("3H", firstCode, entryCount, idDelta)
            here = wWork.stakeCurrent()
            # Wow, this is SO much easier with LinkedWriters!!
            wWork.addUnresolvedOffset("H", here, roStakePool[idRangeTuple])
        
        for t in sorted((n, tp) for tp, n in rangeOffsetPool.items()):
            idRangeTuple = t[1]
            wWork.stakeCurrentWithValue(roStakePool[idRangeTuple])
            wWork.addGroup("H", idRangeTuple)
        
        # We pin the length field to FFFF in case it's larger.
        byteSize = min(0xFFFF, wWork.byteLength - startLength)
        wWork.setDeferredValue(lengthStake, "H", byteSize)
        
        # It may be possible to prove this exception cannot arise (because of
        # the self-local nature of idRangeOffsets); if that proves to be the
        # case, the following can be removed from the try block, and the wWork
        # hack can be removed and content just added to w.
        
        try:
            w.addString(wWork.binaryString())
        
        except ValueError:
            raise ValueError(
              "Internal format 2 offsets too large for 'H' format!")
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format2`` instance from the specified walker,
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
        
        ``logger``
            A logger to which validation information will be posted.
        
        >>> logger = utilities.makeDoctestLogger('test.cmap')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Format2.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format2 - DEBUG - Walker has 1060 remaining bytes.
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - INFO - 6 unique character codes mapped to 6 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format2 - ERROR - Insufficient bytes.
        
        >>> fvb(b'A' + s[1:], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 1060 remaining bytes.
        test.cmap.format2 - ERROR - Invalid format (0x4102).
        
        >>> obj = fvb(s[0:3] + b'A' + s[4:], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 1060 remaining bytes.
        test.cmap.format2 - WARNING - Size field value (0x0441) is not expected (0x0424).
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - INFO - 6 unique character codes mapped to 6 unique glyphs.
        
        >>> fvb(s[0:8], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 8 remaining bytes.
        test.cmap.format2 - WARNING - Size field value (0x0424) is not expected (0x0008).
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - ERROR - Insufficient bytes for subHeaderKeys.
        
        >>> fvb(s[0:518], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 518 remaining bytes.
        test.cmap.format2 - WARNING - Size field value (0x0424) is not expected (0x0206).
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - ERROR - Insufficient bytes for high-byte index.
        
        >>> fvb(s[0:528], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 528 remaining bytes.
        test.cmap.format2 - WARNING - Size field value (0x0424) is not expected (0x0210).
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - ERROR - Insufficient bytes for high-byte table.
        
        >>> fvb(s[0:1054], logger=logger)
        test.cmap.format2 - DEBUG - Walker has 1054 remaining bytes.
        test.cmap.format2 - WARNING - Size field value (0x0424) is not expected (0x041E).
        test.cmap.format2 - INFO - Language code is 0.
        test.cmap.format2 - ERROR - Insufficient bytes for high-byte table 0.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format2')
        else:
            logger = logger.getChild('format2')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, size, language = w.unpack("3H")
        
        if format != 2:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return None
        
        if byteLength > 0xFFFF:
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
        
        elif byteLength != size:
            logger.warning((
              'V0011',
              (int(size), int(byteLength)),
              "Size field value (0x%04X) is not expected (0x%04X)."))
        
        logger.info(('V0005', (language,), "Language code is %d."))
        r = cls(language=language)
        
        if w.length() < 512:
            logger.error((
              'V0012',
              (),
              "Insufficient bytes for subHeaderKeys."))
            
            return None
        
        subHeaderKeys = [x // 8 for x in w.group("H", 256)]
        
        if w.length() < 8:
            logger.error((
              'V0013',
              (),
              "Insufficient bytes for high-byte index."))
            
            return None
        
        first, count, idDelta, offset = w.unpack("2HhH")
        subW = w.subWalker(offset - 2, relative=True)
        
        if subW.length() < 512:
            logger.error((
              'V0014',
              (),
              "Insufficient bytes for high-byte table."))
            
            return None
        
        glyphs = subW.group("H", 256)
        
        for charCode, glyphCode in enumerate(glyphs):
            if glyphCode:
                r[charCode] = glyphCode
        
        bigCount = max(subHeaderKeys)
        subHeaders = [None]  # we've already processed the zero entry
        
        for i in range(bigCount):
            if w.length() < 8:
                logger.error((
                  'V0015',
                  (i,),
                  "Insufficient bytes for high-byte index %d."))
                
                return None
            
            first, count, idDelta, offset = w.unpack("2HhH")
            subW = w.subWalker(offset - 2, relative=True)
            
            if subW.length() < 2 * count:
                logger.error((
                  'V0016',
                  (i,),
                  "Insufficient bytes for high-byte table %d."))
                
                return None
            
            v = subW.group("H", count)
            subHeaders.append((first, idDelta, v))
        
        for highByte in range(1, 256):
            charCodeBase = 256 * highByte
            
            if subHeaderKeys[highByte]:
                first, idDelta, v = subHeaders[subHeaderKeys[highByte]]
                
                for i, j in enumerate(v):
                    if j:
                        charCode = charCodeBase + first + i
                        glyphCode = (j + idDelta) % 65536
                        r[charCode] = glyphCode
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format2`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format2.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        format, size, language = w.unpack("3H")
        
        if format != 2:
            raise ValueError("Bad format 2 subtable format!")
        
        r = cls(language=language)
        subHeaderKeys = [x // 8 for x in w.group("H", 256)]
        first, count, idDelta, offset = w.unpack("HHhH")
        subW = w.subWalker(offset - 2, relative=True)
        glyphs = subW.group("H", 256)
        
        for charCode, glyphCode in enumerate(glyphs):
            if glyphCode:
                r[charCode] = glyphCode
        
        bigCount = max(subHeaderKeys)
        subHeaders = [None]  # we've already processed the zero entry
        
        for i in range(bigCount):
            first, count, idDelta, offset = w.unpack("HHhH")
            subW = w.subWalker(offset - 2, relative=True)
            v = subW.group("H", count)
            subHeaders.append((first, idDelta, v))
        
        for highByte in range(1, 256):
            charCodeBase = 256 * highByte
            
            if subHeaderKeys[highByte]:
                first, idDelta, v = subHeaders[subHeaderKeys[highByte]]
                
                for i, j in enumerate(v):
                    if j:
                        r[charCodeBase + first + i] = (j + idDelta) % 65536
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Format2({}),
        Format2({42: 100, 60: 150, 61: 151, 0x1234: 5, 0x1A10: 40, 0x1A11: 41}))

def _extra_tests():
    """
    >>> utilities.hexdump(_testingValues[0].binaryString())
           0 | 0002 040E 0000 0000  0000 0000 0000 0000 |................|
          10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          30 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          40 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          50 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          60 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          70 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          80 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          90 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         100 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         110 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         120 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         130 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         140 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         150 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         160 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         170 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         180 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         190 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         200 | 0000 0000 0000 0000  0100 0000 0002 0000 |................|
         210 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         220 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         230 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         240 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         250 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         260 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         270 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         280 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         290 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         300 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         310 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         320 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         330 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         340 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         350 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         360 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         370 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         380 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         390 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         400 | 0000 0000 0000 0000  0000 0000 0000      |..............  |

    >>> utilities.hexdump(_testingValues[1].binaryString())
           0 | 0002 0424 0000 0000  0000 0000 0000 0000 |...$............|
          10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          20 | 0000 0000 0000 0000  0000 0008 0000 0000 |................|
          30 | 0000 0000 0000 0000  0000 0010 0000 0000 |................|
          40 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          50 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          60 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          70 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          80 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          90 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
          F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         100 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         110 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         120 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         130 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         140 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         150 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         160 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         170 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         180 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         190 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         1F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         200 | 0000 0000 0000 0000  0100 0000 0012 0034 |...............4|
         210 | 0001 0000 020A 0010  0002 0000 0204 0000 |................|
         220 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         230 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         240 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         250 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         260 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         270 | 0000 0064 0000 0000  0000 0000 0000 0000 |...d............|
         280 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         290 | 0000 0000 0000 0096  0097 0000 0000 0000 |................|
         2A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         2F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         300 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         310 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         320 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         330 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         340 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         350 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         360 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         370 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         380 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         390 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3B0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3C0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3D0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3E0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         3F0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         400 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
         410 | 0000 0000 0000 0000  0000 0000 0000 0005 |................|
         420 | 0028 0029                                |.(.)            |
    """
    
    pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
