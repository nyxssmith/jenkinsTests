#
# format12.py
#
# Copyright © 2004-2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 12 ``'cmap'`` subtables. This is a segment-based format,
analogous to format 4 but for 32-bit character codes.

This is a frequently used format, as it can accommodate Unicode values outside
the Basic Multilingual Plane.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.utilities import span2
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format12(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format12`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``dict_compactremovesfalses``:
    
    >>> d = Format12({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format12({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format12({15: 3}, language = 1)
    >>> d2 = Format12({15: 3}, language = 2)
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
    
    def _preBuildValidate(self):
        """
        Checks that all keys are in the range 0..FFFFFFFF, and all values are
        in the range 0..FFFF. Raises a ValueError if any are not. (Note that
        the checking does not explicitly stop at the last Unicode codepoint,
        10FFFF. This is because format 12 subtables can be used with
        non-Unicode encodings, and so the check needs to be driven by what the
        format can hold, and not by any specific encoding's limits)
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFFFFFFFF:
                raise ValueError(
                  "One or more keys out of range for format 12 subtable!")
            
            if value < 0 or value > 0xFFFF:
                raise ValueError(
                  "One or more values out of range for format 12 subtable!")
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        bad = (False, None)
        
        if endOfWalker < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return bad
        
        format, size, language = w.unpack("3L")
        
        if format != 0xC0000:
            logger.error(('V0002', (format,), "Invalid format (0x%08X)."))
            return bad
        
        logger.info(('V0005', (language,), "Language code is %d."))
        
        if endOfWalker != size:
            logger.warning((
              'V0011',
              (int(size), int(endOfWalker)),
              "Size field value (0x%04X) is not expected (0x%04X)."))
        
        return True, language
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: None
        :raises ValueError: if one or more values cannot fit into four bytes
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 000C 0000 0000 0010  0000 0000 0000 0000 |................|
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000C 0000 0000 001C  0000 0000 0000 0001 |................|
              10 | 0000 3A00 0000 3A00  0000 0019           |..:...:.....    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 000C 0000 0000 0028  0000 0000 0000 0002 |.......(........|
              10 | 0000 3A00 0000 3A01  0000 0019 0000 3A02 |..:...:.......:.|
              20 | 0000 3A02 0000 001D                      |..:.....        |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 000C 0000 0000 0034  0000 0000 0000 0003 |.......4........|
              10 | 0000 3A00 0000 3A01  0000 0019 0000 3A02 |..:...:.......:.|
              20 | 0000 3A02 0000 001D  000A 2318 000A 2318 |..:.......#...#.|
              30 | 0000 001B                                |....            |
        """
        
        self._preBuildValidate()
        startLength = w.byteLength
        w.add("HH", 12, 0)  # format and pad
        lengthStake = w.addDeferredValue("L")
        w.add("L", (self.language or 0))
        groups = []
        
        if self:
            mgg = utilities.monotonicGroupsGenerator
            sp = span2.Span(self)
            
            for g in sp.ranges():
                if g[1] < 0x7FFFFFFE:
                    vC = [x for x in range(g[0], g[1] + 1)]
                else:
                    vC = list(range(g[0], g[1] + 1))

                charIndex = 0
                itSub = mgg(self[c] for c in vC)
                
                for glyphStart, glyphStopPlusOne, ignore in itSub:
                    thisLen = glyphStopPlusOne - glyphStart
                    
                    groups.append((
                      vC[charIndex],
                      vC[charIndex + thisLen - 1],
                      glyphStart))
                    
                    charIndex += thisLen
        
        w.add("L", len(groups))
        w.addGroup("3L", groups)
        w.setDeferredValue(lengthStake, "L", w.byteLength - startLength)
        
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format12`` instance from the specified walker,
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
        >>> s = _testingValues[3].binaryString()
        >>> fvb = Format12.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format12 - DEBUG - Walker has 52 remaining bytes.
        test.cmap.format12 - INFO - Language code is 0.
        test.cmap.format12 - INFO - There are 3 groups.
        test.cmap.format12 - INFO - 4 unique character codes mapped to 4 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format12 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format12 - ERROR - Insufficient bytes.
        
        xxx add more tests here
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format12')
        else:
            logger = logger.getChild('format12')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        okToProceed, language = cls._validate_header(w, logger, endOfWalker)
        
        if not okToProceed:
            return None
        
        r = cls(language=language)
        
        if w.length() < 2:
            logger.error(('V0048', (), "Insufficient bytes for header."))
            return None
        
        count = w.unpack("L")
        logger.info(('V0049', (count,), "There are %d groups."))
        
        if w.length() < 12 * count:
            logger.error(('V0050', (), "Insufficient bytes for groups."))
            return None
        
        groups = list(w.group("3L", count))
        
        if groups != sorted(groups, key=operator.itemgetter(0)):
            logger.error(('E0302', (), "Groups not sorted."))
            return None
        
        for thisRec, nextRec in zip(groups, itertools.islice(groups, 1, None)):
            if thisRec[0] > thisRec[1]:
                logger.error((
                  'E0303',
                  (),
                  "Start code greater than end code."))
                
                return None
            
            if thisRec[1] >= nextRec[0]:
                logger.error(('V0051', (), "Groups have overlap."))
                return None

        # Below addresses issue with use of xrange under 32-bit, which
        # overflows at 0x80000000. We gather ranges where use of xrange is
        # OK or not OK, then enumerate with xrange or range, for
        # 'xrangeBad' cases.

        xrangeOK = [t for t in groups if t[1] < 0x7FFFFFFE]
        xrangeBad = [t for t in groups if t[1] >= 0x7FFFFFFE]

        for startChar, endChar, startGlyph in xrangeOK:
            for i, char in enumerate(range(startChar, endChar + 1)):
                r[char] = startGlyph + i

        for startChar, endChar, startGlyph in xrangeBad:
            logger.debug((
              'Vxxxx',
              (endChar,),
              "Using 'range()' for endChar 0x%08X"))
            
            for i, char in enumerate(range(startChar, endChar + 1)):
                r[char] = startGlyph + i

        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format12`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format12.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        
        >>> _testingValues[3] == fb(_testingValues[3].binaryString())
        True
        """
        
        format, size, language, count = w.unpack("4L")
        
        if format != 0xC0000:
            raise ValueError("Bad format 12 subtable format!")
        
        r = cls(language=language)

        # Below addresses issue with use of xrange under 32-bit, which
        # overflows at 0x80000000. We gather ranges where use of xrange is
        # OK or not OK, then enumerate with xrange or range, for
        # 'xrangeBad' cases.

        groups = w.group("3L", count)
        xrangeOK = [t for t in groups if t[1] < 0x7FFFFFFE]
        xrangeBad = [t for t in groups if t[1] >= 0x7FFFFFFE]

        for startChar, endChar, startGlyph in xrangeOK:
            for i, char in enumerate(range(startChar, endChar + 1)):
                r[char] = startGlyph + i

        for startChar, endChar, startGlyph in xrangeBad:
            for i, char in enumerate(range(startChar, endChar + 1)):
                r[char] = startGlyph + i

        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import pp
    
    _testingValues = (
        Format12(),
        Format12({0x3A00: 25}),
        Format12({0x3A00: 25, 0x3A01: 26, 0x3A02: 29}),
        Format12({0x3A00: 25, 0x3A01: 26, 0x3A02: 29, 0xA2318: 27}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
