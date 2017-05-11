#
# format6.py
#
# Copyright © 2004-2011, 2013, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 6 'cmap' subtables. These 16-bit maps are not used very
often, but there are cases where a format 6 subtable will occupy considerably
less space than a format 4 subtable.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.utilities import writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Format6(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format6`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``dict_compactremovesfalses``:
    
    >>> d = Format6({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format6({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format6({15: 3}, language = 1)
    >>> d2 = Format6({15: 3}, language = 2)
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
        Checks that all keys and values are in the range 0..FFFF. Raises a
        ValueError if any are not.
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFFFF:
                raise ValueError(
                  "One or more keys out of range for format 6 subtable!")
            
            if value < 0 or value > 0xFFFF:
                raise ValueError(
                  "One or more values out of range for format 6 subtable!")
    
    @staticmethod
    def _validate_header(w, logger, endOfWalker):
        bad = (False, None)
        
        if endOfWalker < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return bad
        
        format, size, language = w.unpack("3H")
        
        if format != 6:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return bad
        
        if endOfWalker > 0xFFFF:
            # The format allows subtables larger than 64K, although the length
            # field is limited to two bytes. This is detected by the special
            # value 0xFFFF in the length field.
            #
            # Note that this is MOST unlikely for format 6 subtables.
            
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
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: None
        :raises ValueError: if one or more values cannot fit into two bytes
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0006 000A 0000 0000  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0006 000C 0000 002A  0001 0064           |.......*...d    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0006 000E 0000 002A  0002 0064 0065      |.......*...d.e  |
        
        >>> pp.PP().sequence_grouped(_testingValues[3].binaryString())
        [0]: 0
        [1]: 6
        [2]: 36
        [3]: 32
        [4-6]: 0
        [7]: 42
        [8]: 18
        [9]: 11
        [10]: 0
        [11]: 100
        [12]: 0
        [13]: 101
        [14-9246]: 0
        [9247]: 5
        """
        
        self._preBuildValidate()
        startLength = w.byteLength
        w.add("H", 6)  # format
        lengthStake = w.addDeferredValue("H")
        w.add("H", (self.language or 0))
        
        if self:
            keys = sorted(self)
            first = keys[0]
            last = keys[-1]
            w.add("HH", first, last - first + 1)
            w.addGroup("H", (self.get(i, 0) for i in range(first, last + 1)))
        
        else:
            w.add("HH", 0, 0)
        
        # We pin the length field to FFFF in case it's larger.
        byteSize = min(0xFFFF, w.byteLength - startLength)
        w.setDeferredValue(lengthStake, "H", byteSize)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format6`` instance from the specified walker,
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
        >>> fvb = Format6.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.cmap.format6 - DEBUG - Walker has 9248 remaining bytes.
        test.cmap.format6 - INFO - Language code is 0.
        test.cmap.format6 - INFO - 3 unique character codes mapped to 3 unique glyphs.
        
        >>> fvb(s[0:2], logger=logger)
        test.cmap.format6 - DEBUG - Walker has 2 remaining bytes.
        test.cmap.format6 - ERROR - Insufficient bytes.
        
        >>> fvb(s[0:6], logger=logger)
        test.cmap.format6 - DEBUG - Walker has 6 remaining bytes.
        test.cmap.format6 - WARNING - Size field value (0x2420) is not expected (0x0006).
        test.cmap.format6 - INFO - Language code is 0.
        test.cmap.format6 - ERROR - Insufficient bytes for header.
        
        xxx add more tests here
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format6')
        else:
            logger = logger.getChild('format6')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        okToProceed, language = cls._validate_header(w, logger, endOfWalker)
        
        if not okToProceed:
            return None
        
        r = cls(language=language)
        
        if w.length() < 4:
            logger.error(('V0036', (), "Insufficient bytes for header."))
            return None
        
        firstCode, count = w.unpack("2H")
        
        if firstCode + count > 0xFFFF:
            logger.error(('V0037', (), "Attempt to set character codes >64K."))
            return None
        
        if w.length() < 2 * count:
            logger.error(('V0038', (), "Insufficient bytes for content."))
            return None
        
        for char, glyph in enumerate(w.group("H", count)):
            if glyph:
                r[char + firstCode] = glyph
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format6`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format6.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        
        >>> _testingValues[3] == fb(_testingValues[3].binaryString())
        True
        """
        
        format, size, language = w.unpack("3H")
        
        if format != 6:
            raise ValueError("Bad format 6 subtable format!")
        
        firstCode, count = w.unpack("HH")
        r = cls(language=language)
        
        for char, glyph in enumerate(w.group("H", count)):
            if glyph:
                r[char + firstCode] = glyph
        
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
        Format6(),
        Format6({42: 100}),
        Format6({42: 100, 43: 101}),
        Format6({42: 100, 43: 101, 0x1234: 5}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
