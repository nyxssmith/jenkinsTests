#
# coverage.py
#
# Copyright © 2005-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions for OpenType Coverage objects.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist, writer

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    if list(range(len(obj))) != [obj[n] for n in sorted(obj)]:
        logger.error((
          'V0308',
          (),
          "The coverage values are not a dense, monotonically "
          "increasing set."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Coverage(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing ranges of glyph indices.
    
    These are dictionaries mapping glyph indices to coverage indices.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    afii60001: 3
    xyz34: 0
    xyz65: 1
    xyz86: 2
    
    >>> _testingValues[1].pprint()
    15: 0
    60: 1
    61: 2
    62: 3
    63: 4
    64: 5
    65: 6
    66: 7
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> obj = _testingValues[0].__copy__()
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(100))
    True
    
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(90))
    ivtest.glyph 96 - ERROR - Glyph index 96 too large.
    False
    
    >>> obj = Coverage({5:0, 6:1, 7:3})
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(100))
    ivtest - ERROR - The coverage values are not a dense, monotonically increasing set.
    False
    
    >>> obj = Coverage({10:0, 9:1})
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(100))
    ivtest - ERROR - The coverage values are not a dense, monotonically increasing set.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda n: "glyph %d" % (n,)),
        item_usenamerforstr = True,
        item_validatecode_toolargeglyph = 'V0307',
        item_validatefunc_partial = valassist.isFormat_H,
        map_mergechecknooverlap = True,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    @staticmethod
    def _makeFormat1(sortedKeys):
        """
        Returns a format 1 binary string.
        """
        
        w = writer.LinkedWriter()
        w.add("HH", 1, len(sortedKeys))
        w.addGroup("H", sortedKeys)  # already checked density and monotonicity
        return w.binaryString()
    
    @staticmethod
    def _makeFormat2(sortedKeys):
        """
        Returns a format 2 binary string.
        """
        
        # already checked density and monotonicity
        groups = []
        currIndex = 0
        it = utilities.monotonicGroupsGenerator(sortedKeys)
        
        for start, stop, skip in it:
            groups.append((start, stop - 1, currIndex))
            currIndex += (stop - start)
        
        w = writer.LinkedWriter()
        w.add("HH", 2, len(groups))
        w.addGroup("3H", groups)
        return w.binaryString()
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0001 0004 0021 0040  0055 0060           |.....!.@.U.`    |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0002 0002 000F 000F  0000 003C 0042 0001 |...........<.B..|
        
        >>> h(_testingValues[2].binaryString())
               0 | 0001 0000                                |....            |
        
        >>> Coverage({5: 2, 60: 8}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: Coverage values must be a dense, monotonic set!
        
        >>> Coverage({5: 1, 60: 0}).binaryString()
        Traceback (most recent call last):
          ...
        ValueError: Coverage values must be a dense, monotonic set!
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            if kwArgs.get('forceCoverageSort', False):
                # rather than test and potentially fail on write, just force
                # the issue (values are not written; only keys, so really all
                # we need to do is sort the keys).
                sortedKeys = sorted(self)
            else:
                # current default behavior
                sortedKeys = sorted(self)
                sortedValues = [self[key] for key in sortedKeys]
            
                if sortedValues != list(range(len(self))):
                    raise ValueError(
                      "Coverage values must be a dense, monotonic set!")
            
            fmt1 = self._makeFormat1(sortedKeys)
            fmt2 = self._makeFormat2(sortedKeys)
            s = (fmt1 if len(fmt1) <= len(fmt2) else fmt2)
            w.addString(s)
        
        else:
            w.add("HH", 1, 0)  # format 1, glyph count = 0
    
    @classmethod
    def fromglyphset(cls, glyphSet, **kwArgs):
        """
        Given a set of glyph indices, create a Coverage and return it. If a
        keyword argument 'backMap' is specified as an empty dict, on return it
        will be filled out with a mapping from coverage indices back to glyphs.
        The Coverage will be set up so the glyph indices are monotonic
        increasing.
        
        >>> s = set([2, 15, 5, 9, 1])
        >>> b = {}
        >>> c = Coverage.fromglyphset(s, backMap=b)
        >>> c.setNamer(namer.testingNamer())
        >>> print(c)
        {xyz10: 3, xyz16: 4, xyz2: 0, xyz3: 1, xyz6: 2}
        >>> print(b)
        {0: 1, 1: 2, 2: 5, 3: 9, 4: 15}
        """
        
        r = cls()
        backMap = kwArgs.get('backMap', {})
        
        for g in sorted(glyphSet):
            backMap[len(r)] = g
            r[g] = len(r)
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Coverage. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Coverage.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.coverage - DEBUG - Walker has 12 remaining bytes.
        test.coverage - DEBUG - Format is 1, count is 4
        test.coverage - DEBUG - Raw data are [33, 64, 85, 96]
        
        >>> fvb(s[:2], logger=logger)
        test.coverage - DEBUG - Walker has 2 remaining bytes.
        test.coverage - ERROR - Insufficient bytes.
        
        >>> obj = fvb(
        ...   s[:2] + utilities.fromhex("00 00") + s[4:],
        ...   logger=logger)
        test.coverage - DEBUG - Walker has 12 remaining bytes.
        test.coverage - DEBUG - Format is 1, count is 0
        test.coverage - WARNING - Count is zero.
        test.coverage - DEBUG - Raw data are []
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        test.coverage - DEBUG - Walker has 12 remaining bytes.
        test.coverage - DEBUG - Format is 16705, count is 4
        test.coverage - ERROR - Unknown format: 0x4141.
        
        >>> fvb(s[:4], logger=logger)
        test.coverage - DEBUG - Walker has 4 remaining bytes.
        test.coverage - DEBUG - Format is 1, count is 4
        test.coverage - ERROR - Insufficient bytes for format 1 table.
        
        >>> fvb(s[:4] + s[6:8] + s[4:6] + s[8:], logger=logger)
        test.coverage - DEBUG - Walker has 12 remaining bytes.
        test.coverage - DEBUG - Format is 1, count is 4
        test.coverage - DEBUG - Raw data are [64, 33, 85, 96]
        test.coverage - ERROR - Format 1 glyphs not sorted.
        
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.coverage - DEBUG - Walker has 16 remaining bytes.
        test.coverage - DEBUG - Format is 2, count is 2
        test.coverage - DEBUG - Raw data are [(15, 15, 0), (60, 66, 1)]
        
        >>> fvb(s[:4], logger=logger)
        test.coverage - DEBUG - Walker has 4 remaining bytes.
        test.coverage - DEBUG - Format is 2, count is 2
        test.coverage - ERROR - Insufficient bytes for format 2 table.
        
        >>> fvb(s[:10] + s[12:14] + s[10:12] + s[14:], logger=logger)
        test.coverage - DEBUG - Walker has 16 remaining bytes.
        test.coverage - DEBUG - Format is 2, count is 2
        test.coverage - DEBUG - Raw data are [(15, 15, 0), (66, 60, 1)]
        test.coverage - ERROR - Format 2 segment first greater than last.
        
        >>> fvb(s[:4] + s[10:16] + s[4:10], logger=logger)
        test.coverage - DEBUG - Walker has 16 remaining bytes.
        test.coverage - DEBUG - Format is 2, count is 2
        test.coverage - DEBUG - Raw data are [(60, 66, 1), (15, 15, 0)]
        test.coverage - ERROR - Format 2 records not sorted.
        
        >>> s = utilities.fromhex(
        ...   "00 02 00 02 00 04 00 04 00 00 01 3A 01 3F 00 06")
        >>> fvb(s, logger=logger)
        test.coverage - DEBUG - Walker has 16 remaining bytes.
        test.coverage - DEBUG - Format is 2, count is 2
        test.coverage - DEBUG - Raw data are [(4, 4, 0), (314, 319, 6)]
        test.coverage - ERROR - Format 2 coverage indices have gaps.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('coverage')
        else:
            logger = logger.getChild('coverage')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, count = w.unpack("2H")
        logger.debug(('V0087', (format, count), "Format is %d, count is %d"))
        
        if format not in {1, 2}:
            logger.error(('E5100', (format,), "Unknown format: 0x%04X."))
            return None
        
        if not count:
            logger.warning(('V0086', (), "Count is zero."))
        
        r = cls()
        
        if format == 1:
            if w.length() < 2 * count:
                logger.error((
                  'V0088',
                  (),
                  "Insufficient bytes for format 1 table."))
                
                return None
            
            v = list(w.group("H", count))
            logger.debug(('Vxxxx', (v,), "Raw data are %s"))
            
            if v != sorted(v):
                logger.error(('V0089', (), "Format 1 glyphs not sorted."))
                return None
            
            for i, glyph in enumerate(v):
                r[glyph] = i
        
        else:
            if w.length() < 6 * count:
                logger.error((
                  'V0090',
                  (),
                  "Insufficient bytes for format 2 table."))
                
                return None
            
            v = list(w.group("3H", count))
            logger.debug(('Vxxxx', (v,), "Raw data are %s"))
            
            if v != sorted(v, key=operator.itemgetter(0)):
                logger.error(('V0091', (), "Format 2 records not sorted."))
                return None
            
            expectBase = 0
            
            for startGlyph, endGlyph, coverBase in v:

                if startGlyph in r or endGlyph in r:
                    logger.error((
                      'V1014',
                      (startGlyph, endGlyph, coverBase),
                      "Format 2 segment (%d, %d, %d) overlaps or contains "
                      "duplicates of other ranges."))
                      
                    # Continue validating even with an error;
                    # duplication/overlap will be resolved when added to the
                    # result dictionary.

                if coverBase != expectBase:
                    logger.error((
                      'V0092',
                      (),
                      "Format 2 coverage indices have gaps."))
                    
                    return None
                
                if startGlyph > endGlyph:
                    logger.error((
                      'V0093',
                      (),
                      "Format 2 segment first greater than last."))
                    
                    return None
                
                for glyph in range(startGlyph, endGlyph + 1):
                    r[glyph] = coverBase + glyph - startGlyph
                
                expectBase += endGlyph - startGlyph + 1
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Coverage object created from the specified walker.
        
        >>> for obj in (_testingValues[0], _testingValues[1]):
        ...   print(obj == Coverage.frombytes(obj.binaryString()))
        True
        True
        """
        
        format, count = w.unpack("HH")
        
        if format != 1 and format != 2:
            raise ValueError("Unknown Coverage format: %d" % (format,))
        
        r = cls()
        
        if format == 1:
            for i, x in enumerate(w.group("H", count)):
                r[x] = i
        
        else:
            for startGlyph, endGlyph, coverBase in w.group("3H", count):
                for glyph in range(startGlyph, endGlyph + 1):
                    r[glyph] = coverBase + glyph - startGlyph
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        # this is format 1
        Coverage({33: 0, 64: 1, 85: 2, 96: 3}),
        
        # this is format 2
        Coverage({15: 0, 60: 1, 61: 2, 62: 3, 63: 4, 64: 5, 65: 6, 66: 7}),
        
        Coverage())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
