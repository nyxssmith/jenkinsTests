#
# format13.py
#
# Copyright © 2004-2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 13 ``'cmap'`` subtables. This is a specialized format that
is primarily used for "Last Resort"-style fonts. It allows efficient mapping of
large number of character codes to the same glyph.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format13(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format13`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``dict_compactremovesfalses``:
    
    >>> d = Format13({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format13({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format13({15: 3}, language = 1)
    >>> d2 = Format13({15: 3}, language = 2)
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
        10FFFF. This is because format 13 subtables can be used with
        non-Unicode encodings, and so the check needs to be driven by what the
        format can hold, and not by any specific encoding's limits)
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFFFFFFFF:
                raise ValueError(
                  "One or more keys out of range for format 13 subtable!")
            
            if value < 0 or value > 0xFFFF:
                raise ValueError(
                  "One or more values out of range for format 13 subtable!")
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        bad = (False, None)
        
        if endOfWalker < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return bad
        
        format, size, language = w.unpack("3L")
        
        if format != 0xD0000:
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
               0 | 000D 0000 0000 0010  0000 0000 0000 0000 |................|
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000D 0000 0000 0034  0000 0000 0000 0003 |.......4........|
              10 | 0000 0004 0000 03B5  0000 000A 0000 03C0 |................|
              20 | 0000 03C0 0000 000A  0000 03C1 0000 07D0 |................|
              30 | 0000 000B                                |....            |
        """
        
        self._preBuildValidate()
        startLength = w.byteLength
        w.add("HH", 13, 0)  # format and pad
        lengthStake = w.addDeferredValue("L")
        w.add("L", (self.language or 0))
        groups = []
        
        if self:
            it = ((c, self[c]) for c in sorted(self))
            mgg = utilities.monotonicGroupsGenerator
            ig0 = operator.itemgetter(0)
            
            for k, g in itertools.groupby(it, operator.itemgetter(1)):
                v = list(g)
                
                for start, stop, ignore in mgg(map(ig0, iter(v))):
                    groups.append((start, stop - 1, k))
        
        w.add("L", len(groups))
        w.addGroup("3L", groups)
        w.setDeferredValue(lengthStake, "L", w.byteLength - startLength)
        
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format13`` instance from the specified walker,
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
        >>> fvb = Format13.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format13 - DEBUG - Walker has 52 remaining bytes.
        test.cmap.format13 - INFO - Language code is 0.
        test.cmap.format13 - INFO - There are 3 groups.
        test.cmap.format13 - INFO - 1987 unique character codes mapped to 2 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format13 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format13 - ERROR - Insufficient bytes.
        
        xxx add more tests here (but keep in mind they're expensive in format 10)
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format13')
        else:
            logger = logger.getChild('format13')
        
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
            logger.error(('V0052', (), "Insufficient bytes for header."))
            return None
        
        count = w.unpack("L")
        logger.info(('V0053', (count,), "There are %d groups."))
        
        if w.length() < 12 * count:
            logger.error(('V0054', (), "Insufficient bytes for groups."))
            return None
        
        groups = list(w.group("3L", count))
        
        if groups != sorted(groups, key=operator.itemgetter(0)):
            logger.error(('V0055', (), "Groups not sorted."))
            return None
        
        for thisRec, nextRec in zip(groups, itertools.islice(groups, 1, None)):
            if thisRec[0] > thisRec[1]:
                logger.error((
                  'V0056',
                  (),
                  "Start code greater than end code."))
                
                return None
            
            if thisRec[1] >= nextRec[0]:
                logger.error(('V0057', (), "Groups have overlap."))
                return None
        
        # Below addresses issue with use of xrange under 32-bit, which
        # overflows at 0x80000000. We gather ranges where use of xrange is
        # OK or not OK, then enumerate with xrange or range, for
        # 'xrangeBad' cases.

        xrangeOK = [t for t in groups if t[1] < 0x7FFFFFFE]
        xrangeBad = [t for t in groups if t[1] >= 0x7FFFFFFE]

        for startChar, endChar, glyph in xrangeOK:
            if glyph:
                for char in range(startChar, endChar + 1):
                    r[char] = glyph
        
        for startChar, endChar, glyph in xrangeBad:
            logger.debug((
              'Vxxxx',
              (endChar,),
              "Using 'range()' for endChar 0x%08X"))
            
            if glyph:
                for char in range(startChar, endChar + 1):
                    r[char] = glyph
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format13`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format13.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        format, size, language, count = w.unpack("4L")
        
        if format != 0xD0000:
            raise ValueError("Bad format 13 subtable format!")
        
        r = cls(language=language)
        
        # Below addresses issue with use of xrange under 32-bit, which
        # overflows at 0x80000000. We gather ranges where use of xrange is
        # OK or not OK, then enumerate with xrange or range, for
        # 'xrangeBad' cases.

        groups = w.group("3L", count)
        xrangeOK = [t for t in groups if t[1] < 0x7FFFFFFE]
        xrangeBad = [t for t in groups if t[1] >= 0x7FFFFFFE]

        for startChar, endChar, glyph in xrangeOK:
            if glyph:
                for char in range(startChar, endChar + 1):
                    r[char] = glyph
        
        for startChar, endChar, glyph in xrangeBad:
            if glyph:
                for char in range(startChar, endChar + 1):
                    r[char] = glyph
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    d = Format13()
    for i in range(4, 950): d[i] = 10
    d[960] = 10
    for i in range(961, 2001): d[i] = 11
    
    _testingValues = (
        Format13(),
        d)
    
    del d, i

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
