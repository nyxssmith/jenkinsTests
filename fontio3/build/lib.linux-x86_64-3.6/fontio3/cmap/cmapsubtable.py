#
# cmapsubtable.py
#
# Copyright © 2004-2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module defines the ``CmapSubtable`` class, which is the living object
representing a single subtable in a :py:class:`~fontio3.cmap.cmap.Cmap`. In
general, these are just dicts mapping some number (a character code of some
flavor) to a glyph index.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities

from fontio3.cmap import (
  format0,
  format2,
  format4,
  format6,
  format8,
  format10,
  format12,
  format13)

from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private constants
#

_workClasses = {
    0: format0.Format0,
    2: format2.Format2,
    4: format4.Format4,
    6: format6.Format6,
    8: format8.Format8,
    10: format10.Format10,
    12: format12.Format12,
    13: format13.Format13}

# -----------------------------------------------------------------------------

#
# Classes
#

class CmapSubtable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    In this model, a ``CmapSubtable`` is simply and always a dictionary mapping
    unsigned 32-bit numbers to glyph indices. Details like platform, script,
    and character-set conversions do not enter into it; they can be handled by
    higher-level classes.
    
    The following attributes are defined for this class, in the following
    order:
    
    ``language``
        A code for the language, which is associated with the platform and
        script already present in the :py:class:`~fontio3.cmap.cmap.Cmap` key.
        
        It is a historical oddity that language is here, while platform and
        script are elsewhere.
    
    ``preferredFormat``
        Often the same data can be represented in multiple subtable formats. If
        you have a preference you can set it in this attribute. In the absence
        of a preference, the ``buildBinary()`` logic will use the most
        space-efficient format.
    
    ``originalFormat``
        The format the original data used.
    
    Example of ``map_compactremovesfalses``:
    
    >>> d = CmapSubtable({15: 3, 25: 0, 26: 0})
    >>> print(d)
    {0x000F: 3, 0x0019: 0, 0x001A: 0}
    >>> print(d.compacted())
    {0x000F: 3}
    
    Example of ``item_renumberdirectvalues``:
    
    >>> d = CmapSubtable({15: 3, 16: 4})
    >>> print(d.glyphsRenumbered({3: 200, 4: 201}))
    {0x000F: 200, 0x0010: 201}
    
    Example of ``attr_ignoreforcomparisons`` for ``language``,
    ``preferredFormat`` and ``originalFormat``:
    
    >>> d1 = CmapSubtable({15: 3}, language=1, preferredFormat=10, originalFormat=2)
    >>> d2 = CmapSubtable({15: 3}, language=2, preferredFormat=4)
    >>> d1 == d2
    True
    
    Example of ``item_pprintlabelfunc`` (BMP get 4 digits, non-BMP get 6):
    
    >>> CmapSubtable({32: 5, 0x15FFF: 6}).pprint(namer=namer.testingNamer())
    0x0020: xyz6
    0x015FFF: xyz7
    
    >>> e = utilities.fakeEditor(0x10000)
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("val", stream=f)
    >>> c = CmapSubtable({-5: 1, 2.75: 2, "fred": 3})
    >>> c.isValid(logger=logger, editor=e)
    False
    
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    val.['fred'] - ERROR - The value 'fred' is not a real number.
    val.[-5] - ERROR - The negative value -5 cannot be used in an unsigned field.
    val.[2.75] - ERROR - The value 2.75 is not an integer.
    >>> f.close()
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc = (
          lambda c: ("0x%06X" if c > 0xFFFF else "0x%04X") % c),
        item_renumberdirectvalues = True,
        item_usenamerforstr = True,
        item_validatecode_toolargeglyph = 'E0314',
        item_validatefunckeys_partial = valassist.isFormat_L,
        item_wisdom_key = (
          "Numerical character code value (not a string; an actual number). "
          "It's OK for multiple keys to map to the same value."),
        item_wisdom_value = (
          "Glyph index; 0 means the missing glyph. You never need to "
          "explicitly map a character to 0, since TrueType does this "
          "automatically."),
        map_compactremovesfalses = True,
        map_wisdom = "Mapping from character code to glyph")
    
    attrSpec = dict(
        language = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 0),
            attr_showonlyiftrue = True,
            attr_wisdom = "Language code (or 0)"),
        
        preferredFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True,
            attr_wisdom = ("Preferred format when writing. Initially "
              "set to the same as originalFormat; override by setting "
              "a format number or set to None to allow fontio3 to "
              "analyze and write what it thinks is best for the content.")),
        
        originalFormat = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True,
            attr_wisdom = "Original format when read"))
    
    attrSorted = ('language', 'preferredFormat', 'originalFormat')
    
    #
    # Methods
    #
    
    def _validOutputFormats(self):
        """
        Returns a list of formats valid for the current data.
        
        >>> cs = CmapSubtable({0x12: 6})
        >>> cs._validOutputFormats()
        [0, 2, 4, 6, 13]
        >>> cs[0x1234] = 7
        >>> cs._validOutputFormats()
        [4, 6, 13]
        >>> del cs[0x12]
        >>> cs._validOutputFormats()
        [2, 4, 6, 13]
        >>> cs[0x12345678] = 8
        >>> cs._validOutputFormats()
        [10, 12, 13]
        >>> del cs[0x1234]
        >>> cs._validOutputFormats()
        [8, 10, 12, 13]
        """
        
        if not self:
            return [6]
        
        maxKey = max(self)
        r = []
        
        # Format 0 is only an option if there are 256 or fewer entries, the
        # maximum key is less than 256, and the maximum value is also less than
        # 256.
        
        if (0 <= maxKey < 256) and (0 <= max(self.values()) < 256):
            r.append(0)
        
        # Format 2 is only an option if the largest key is less than 64K and
        # there are no one-byte keys which match the high byte of any two-byte
        # key.
        
        if maxKey <= 0xFFFF:
            sHigh = set(key // 256 for key in self if key > 255)
            sLow = set(key for key in self if key < 256)
            
            if not (sHigh & sLow):
                r.append(2)
            
            # Formats 4 and 6 are options if maxKey < 64K.
            r.extend([4, 6])
        
        # Format 8 is only an option if there are no two-byte keys which match
        # the high word of any four-byte key.
        
        else:
            sHigh = set(key // 65536 for key in self if key > 65535)
            sLow = set(key for key in self if key < 65536)
            
            if not (sHigh & sLow):
                r.append(8)
            
            # Formats 10 and 12 are always options if maxKey > 64K.
            r.extend([10, 12])
        
        # Format 13 is always an option
        r.append(13)
        
        return r
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (see below)
        :return: None
        :raises ValueError: if no eligible subtable format can accommodate
            the data present in ``self``
        
        The following ``kwArgs`` are supported:
        
        ``stakeValue``
            A stake that will be placed at the start of the binary data laid
            down by this method. One will be synthesized if not provided.
            See :py:class:`~fontio3.utilities.writer.LinkedWriter` for a
            description of stakes and how they're used.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0006 000A 0000 0000  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000D 0000 0000 001C  0000 0000 0000 0001 |................|
              10 | 0000 0020 0000 C34F  0000 0003           |... ...O....    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0004 0028 0000 0006  0004 0001 0002 0021 |...(...........!|
              10 | 61A8 FFFF 0000 0020  61A8 FFFF FFE5 9E5F |a...... a......_|
              20 | 0001 0000 0000 0000                      |........        |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 000C 0000 0000 0028  0000 0000 0000 0002 |.......(........|
              10 | 0000 0020 0000 0021  0000 0005 0000 61A8 |... ...!......a.|
              20 | 0000 61A8 0000 0007                      |..a.....        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.preferredFormat is not None:
            c = _workClasses[self.preferredFormat]
            best = c(self, language=self.language).binaryString(**kwArgs)
        
        else:
            best = None
            
            for trialFormat in self._validOutputFormats():
                try:
                    c = _workClasses[trialFormat]
                    s = c(self, language=self.language).binaryString(**kwArgs)
                except ValueError:
                    s = None
                
                if s is not None and (best is None or len(s) < len(best)):
                    best = s
        
        if best is None:
            raise ValueError("No cmap subtable format will accept these data!")
        
        w.addString(best)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new ``CmapSubtable`` instance from the specified walker,
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
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> obj = CmapSubtable.fromvalidatedbytes(s, logger=logger)
        test.cmapsubtable - DEBUG - Walker has 28 remaining bytes.
        test.cmapsubtable.format13 - DEBUG - Walker has 28 remaining bytes.
        test.cmapsubtable.format13 - INFO - Language code is 0.
        test.cmapsubtable.format13 - INFO - There are 1 groups.
        test.cmapsubtable.format13 - INFO - 49968 unique character codes mapped to 1 unique glyphs.
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = CmapSubtable.fromvalidatedbytes(s, logger=logger)
        test.cmapsubtable - DEBUG - Walker has 40 remaining bytes.
        test.cmapsubtable.format4 - DEBUG - Walker has 40 remaining bytes.
        test.cmapsubtable.format4 - INFO - Language code is 0.
        test.cmapsubtable.format4 - INFO - There are 3 segments.
        test.cmapsubtable.format4 - INFO - searchRange is correct.
        test.cmapsubtable.format4 - INFO - entrySelector is correct.
        test.cmapsubtable.format4 - INFO - rangeShift is correct.
        test.cmapsubtable.format4 - INFO - endCodes are correct.
        test.cmapsubtable.format4 - INFO - Correct zero reservedPad value.
        test.cmapsubtable.format4 - INFO - startCodes are correct.
        test.cmapsubtable.format4 - INFO - Nonzero idDeltas are present.
        test.cmapsubtable.format4 - INFO - 3 unique character codes mapped to 3 unique glyphs.
        
        >>> s = _testingValues[3].binaryString()
        >>> obj = CmapSubtable.fromvalidatedbytes(s, logger=logger)
        test.cmapsubtable - DEBUG - Walker has 40 remaining bytes.
        test.cmapsubtable.format12 - DEBUG - Walker has 40 remaining bytes.
        test.cmapsubtable.format12 - INFO - Language code is 0.
        test.cmapsubtable.format12 - INFO - There are 2 groups.
        test.cmapsubtable.format12 - INFO - 3 unique character codes mapped to 3 unique glyphs.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('cmapsubtable')
        else:
            logger = logger.getChild('cmapsubtable')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H", advance=False)
        
        if format not in _workClasses:
            logger.error((
              'E0321',
              (format,),
              "Unknown subtable format 0x%04X."))
            
            return None
        
        workObj = _workClasses[format].fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
        
        if workObj is None:
            return None
        
        return cls(
          workObj,
          language = workObj.language,
          originalFormat = format,
          preferredFormat = format)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new ``CmapSubtable`` instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        >>> for i in range(4):
        ...   obj = _testingValues[i]
        ...   print(obj == CmapSubtable.frombytes(obj.binaryString()))
        True
        True
        True
        True
        """
        
        format = w.unpack("H", advance=False)
        workObj = _workClasses[format].fromwalker(w, **kwArgs)
        
        return cls(
          workObj,
          language = workObj.language,
          originalFormat = format,
          preferredFormat = format)
    
    def getReverseMap(self):
        """
        Get a map from glyph index back to character code.
        
        :return: Map from glyph index to character code
        :rtype: dict(int, int)
        
        .. warning::
        
            Clients should be careful using this, as many CmapSubtable objects
            contain multiple mappings to the same glyph. The use of
            ``getReverseMapTuple()`` neatly solves this potential problem.
        
        >>> d = CmapSubtable({32: 5, 33: 6, 25000: 7})
        >>> print(d.getReverseMap())
        {5: 32, 6: 33, 7: 25000}
        """
        
        r = {}
        
        for char, glyph in self.items():
            r[glyph] = char
        
        return r
    
    def getReverseMapTuple(self):
        """
        Get a map from glyph index back to all character codes that map to
        that glyph.
        
        :return: Map from glyph index to list of character codes
        :rtype: dict(int, list)
        
        Note that the values in this dictionary are actually lists and not
        tuples; the name is for historical reasons.
        
        >>> cs = CmapSubtable({5:10, 6:11, 7:12, 300:11})
        >>> cs.getReverseMapTuple()
        {10: [5], 11: [6, 300], 12: [7]}
        """
        
        return utilities.invertDictFull(self, coerce=False, sorted=True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import io
    from fontio3.utilities import namer
    
    _testingValues = (
        CmapSubtable(),
        CmapSubtable(dict.fromkeys(range(32, 50000), 3)),
        CmapSubtable({32: 5, 33: 6, 25000: 7}),
        CmapSubtable({32: 5, 33: 6, 25000: 7}, preferredFormat=12))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
