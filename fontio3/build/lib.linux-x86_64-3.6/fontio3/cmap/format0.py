#
# format0.py
#
# Copyright © 2004-2011, 2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module defines the ``Format0`` class, which is the living object
representing a single format 0 subtable. In general, these are just dicts
mapping some number (a character code of some flavor) to a glyph index.

Note that format 0 is a very limited format, only allowing 8-bit character
codes and 8-bit glyph indices. It is mainly of historic interest at this point.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import writer

# -----------------------------------------------------------------------------

#
# Classes
#

class Format0(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    ``Format0`` objects are working objects, not really intended for use by any
    client other than ``CmapSubtable``.
    
    The following attributes are defined:
    
    ``language``
        The language code associated with this subtable. Default is None.
    
    Example of ``map_compactremovesfalses``:
    
    >>> d = Format0({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {15: 3, 25: 0, 26: 0}
    >>> print(d.compacted())
    {15: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = Format0({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {15: 200, 16: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``:
    
    >>> d1 = Format0({15: 3}, language = 1)
    >>> d2 = Format0({15: 3}, language = 2)
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
        Checks that all keys and values are in the range 0..FF. Raises a
        ValueError if any are not.
        """
        
        for key, value in self.items():
            if key < 0 or key > 0xFF:
                raise ValueError(
                  "One or more keys out of range for format 0 subtable!")
            
            if value < 0 or value > 0xFF:
                raise ValueError(
                  "One or more values out of range for format 0 subtable!")
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: None
        :raises ValueError: if one or more values cannot fit into one byte
        
        >>> pp.PP().sequence_grouped(_testingValues[0].binaryString())
        [0-1]: 0
        [2]: 1
        [3]: 6
        [4-261]: 0
        
        >>> pp.PP().sequence_grouped(_testingValues[1].binaryString())
        [0-1]: 0
        [2]: 1
        [3]: 6
        [4-47]: 0
        [48]: 100
        [49-261]: 0
        
        >>> s = Format0({300: 5}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: One or more keys out of range for format 0 subtable!
        
        >>> s = Format0({5: 300}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: One or more values out of range for format 0 subtable!
        """
        
        self._preBuildValidate()
        w.add("3H", 0, 262, (self.language or 0))
        f = self.get
        w.addGroup("B", (f(i, 0) for i in range(256)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format0`` instance from the specified walker,
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
        >>> obj = Format0.fromvalidatedbytes(s, logger=logger)
        test.cmap.format0 - DEBUG - Walker has 262 remaining bytes.
        test.cmap.format0 - INFO - Language code is 0.
        test.cmap.format0 - INFO - 3 character(s) mapped, 253 unmapped
        test.cmap.format0 - INFO - 3 unique character codes mapped to 3 unique glyphs.
        
        >>> obj = Format0.fromvalidatedbytes(s[:-1], logger=logger)
        test.cmap.format0 - DEBUG - Walker has 261 remaining bytes.
        test.cmap.format0 - ERROR - Insufficient bytes.
        
        >>> obj = Format0.fromvalidatedbytes(b'A' + s[1:], logger=logger)
        test.cmap.format0 - DEBUG - Walker has 262 remaining bytes.
        test.cmap.format0 - ERROR - Invalid format (0x4100).
        
        >>> obj = Format0.fromvalidatedbytes(s[:3] + b'A' + s[4:], logger=logger)
        test.cmap.format0 - DEBUG - Walker has 262 remaining bytes.
        test.cmap.format0 - ERROR - Invalid size (0x0141).
        
        >>> s = _testingValues[0].binaryString()
        >>> obj = Format0.fromvalidatedbytes(s, logger=logger)
        test.cmap.format0 - DEBUG - Walker has 262 remaining bytes.
        test.cmap.format0 - INFO - Language code is 0.
        test.cmap.format0 - WARNING - All characters were mapped to the missing glyph.
        test.cmap.format0 - INFO - 0 unique character codes mapped to 0 unique glyphs.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('format0')
        else:
            logger = logger.getChild('format0')
        
        byteLength = w.length()
        
        logger.debug((
          'V0001',
          (byteLength,),
          "Walker has %d remaining bytes."))
        
        if byteLength < 262:
            logger.error(('E0301', (), "Insufficient bytes."))
            return None
        
        format, size, language = w.unpack("3H")
        
        if format != 0:
            logger.error(('V0002', (format,), "Invalid format (0x%04X)."))
            return None
        
        if size != 262:
            logger.error(('E0301', (size,), "Invalid size (0x%04X)."))
            return None
        
        logger.info(('V0005', (language,), "Language code is %d."))
        r = cls(language=language)
        mapCount = 0
        
        for char, glyph in enumerate(w.group("B", 256)):
            if glyph:
                r[char] = glyph
                mapCount += 1
        
        if not mapCount:
            logger.warning((
              'V0006',
              (),
              "All characters were mapped to the missing glyph."))
        
        else:
            logger.info((
              'V0007',
              (mapCount, 256 - mapCount),
              "%d character(s) mapped, %d unmapped"))
        
        t = (len(set(r)), len(set(r.values())))
        
        logger.info((
          'V0008',
          t,
          "%d unique character codes mapped to %d unique glyphs."))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``Format0`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
        :raises ValueError: if the format is not 0 or the size is not
            exactly 262 bytes
    
        .. note::
        
            This is a class method!
        
        >>> fb = Format0.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        format, size, language = w.unpack("3H")
        
        if format != 0 and size != 262:
            raise ValueError("Bad format 0 subtable format!")
        
        r = cls(language=language)
        
        for char, glyph in enumerate(w.group("B", 256)):
            if glyph:
                r[char] = glyph
        
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
        Format0(),
        Format0({42: 100}),
        Format0({65: 100, 66: 101, 90: 150}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
