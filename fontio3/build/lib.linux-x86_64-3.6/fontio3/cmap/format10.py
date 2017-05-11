#
# format10.py
#
# Copyright © 2004-2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 10 ``'cmap'`` subtables. These are trimmed arrays, similar
to format 6, but with 32-bit character codes instead of 16-bit codes.

This format is only rarely used.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Format10(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format10`` objects are working objects, not really intended for use by
    any client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``dict_compactremovesfalses``:
    
    >>> d = Format10({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format10({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format10({15: 3}, language = 1)
    >>> d2 = Format10({15: 3}, language = 2)
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
        10FFFF. This is because format 10 subtables can be used with
        non-Unicode encodings, and so the check needs to be driven by what the
        format can hold, and not by any specific encoding's limits)
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFFFFFFFF:
                raise ValueError(
                  "One or more keys out of range for format 10 subtable!")
            
            if value < 0 or value > 0xFFFF:
                raise ValueError(
                  "One or more values out of range for format 10 subtable!")
                  
        # Precalculate size required to store table and raise a ValueError if
        # size exceeds 0x7FFFFFFF. Although that value is less than the maximum
        # possible table size of 0xFFFFFFFF, it almost certainly indicates that
        # this format is not well-suited for the code values mapped.
        if self:
            sizeNeeded = 2 * (max(self) + 1 - min(self))
            
            if sizeNeeded > 0x7FFFFFFF:
                raise ValueError(
                  "Range of codepoints is too large for format10 subtable!")
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        bad = (False, None)
        
        if endOfWalker < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return bad
        
        format, size, language = w.unpack("3L")
        
        if format != 0xA0000:
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
               0 | 000A 0000 0000 0014  0000 0000 0000 0000 |................|
              10 | 0000 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000A 0000 0000 0016  0000 0000 0000 3A00 |..............:.|
              10 | 0000 0001 0019                           |......          |
        
        >>> pp.PP().sequence_grouped(_testingValues[2].binaryString())
        [0]: 0
        [1]: 10
        [2-4]: 0
        [5]: 19
        [6]: 210
        [7]: 70
        [8-13]: 0
        [14]: 58
        [15-16]: 0
        [17]: 9
        [18]: 233
        [19]: 25
        [20]: 0
        [21]: 25
        [22-1299012]: 0
        [1299013]: 26
        """
        
        self._preBuildValidate()
        startLength = w.byteLength
        w.add("HH", 10, 0)  # format and pad
        lengthStake = w.addDeferredValue("L")
        w.add("L", (self.language or 0))
        
        if self:
            firstKey = min(self)
            lastKey32 = min(max(self), 0x7FFFFFFE)  # avoid 32-bit overflow in xrange
            lastKey = max(self)
            w.add("LL", firstKey, lastKey - firstKey + 1)
            g = self.get
            
            for k in range(firstKey, lastKey32 + 1):
                w.add("H", g(k, 0))
            
            for k in range(0x7FFFFFFE, lastKey + 1):
                w.add("H", g(k, 0))

        
        else:
            w.add("LL", 0, 0)
        
        w.setDeferredValue(lengthStake, "L", w.byteLength - startLength)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format10`` instance from the specified walker,
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
        >>> s = _testingValues[2].binaryString()
        >>> fvb = Format10.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format10 - DEBUG - Walker has 1299014 remaining bytes.
        test.cmap.format10 - INFO - Language code is 0.
        test.cmap.format10 - INFO - 2 unique character codes mapped to 2 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format10 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format10 - ERROR - Insufficient bytes.
        
        xxx add more tests here (but keep in mind they're expensive in format 10)
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format10')
        else:
            logger = logger.getChild('format10')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        okToProceed, language = cls._validate_header(w, logger, endOfWalker)
        
        if not okToProceed:
            return None
        
        r = cls(language=language)
        
        if w.length() < 8:
            logger.error(('V0047', (), "Insufficient bytes for array header."))
            return None
        
        first, count = w.unpack("2L")
        
        if w.length() < 2 * count:
            logger.error(('V0046', (), "Insufficient bytes for array."))
            return None
        
        for i, glyph in enumerate(w.group("H", count)):
            if glyph:
                r[first + i] = glyph
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format10`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format10.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        format, size, language, first, count = w.unpack("5L")
        
        if format != 0xA0000:
            raise ValueError("Bad format 10 subtable format!")
        
        r = cls(language=language)
        
        for i, glyph in enumerate(w.group("H", count)):
            if glyph:
                r[first + i] = glyph
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import pp
    
    _testingValues = (
        Format10(),
        Format10({0x3A00: 25}),
        Format10({0x3A00: 25, 0xA2318: 26}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
