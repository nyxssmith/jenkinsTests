#
# coverageset.py
#
# Copyright © 2009-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType Coverage tables, treated as sets.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import setmeta
from fontio3.utilities import valassist, writer

# -----------------------------------------------------------------------------

#
# Classes
#

class CoverageSet(frozenset, metaclass=setmeta.FontDataMetaclass):
    """
    These are OpenType Coverage objects represented as frozensets. The main
    advantage of this is that these objects can be used as dict keys.
    
    Note: sets are unordered, but the Coverage data structure has the glyphs
    monotonically increasing, so the set is simply sorted to recover the glyph-
    to-coverage index value (the index is the position within the sorted list).
    Don't know why I didn't just make these tuples, come to think of it...
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        item_validatecode_toolargeglyph = 'V0307',
        item_validatefunc_partial = valassist.isFormat_H,
        set_mergechecknooverlap = True,
        set_showsorted = True)
    
    #
    # Methods
    #
    
    @staticmethod
    def _makeFormat1(sortedGlyphs):
        w = writer.LinkedWriter()
        w.add("HH", 1, len(sortedGlyphs))
        w.addGroup("H", sortedGlyphs)
        return w.binaryString()
    
    @staticmethod
    def _makeFormat2(sortedGlyphs):
        groups = []
        currIndex = 0
        it = utilities.monotonicGroupsGenerator(sortedGlyphs)
        
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
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0004 0021 0040  0055 0060           |.....!.@.U.`    |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0002 000F 000F  0000 003C 0042 0001 |...........<.B..|
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 0000                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            sortedGlyphs = sorted(self)
            fmt1 = self._makeFormat1(sortedGlyphs)
            fmt2 = self._makeFormat2(sortedGlyphs)
            w.addString(fmt1 if len(fmt1) <= len(fmt2) else fmt2)
        
        else:
            w.add("HH", 1, 0)  # format 1, no glyphs
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new CoverageSet from the specified FontWorkerSource.

        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> cd = CoverageSet.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        test_FW.coverageset - WARNING - line 3 -- glyph 'foo' not found
        test_FW.coverageset - WARNING - line 4 -- incorrect number of tokens, expected 1, found 2
        test_FW.coverageset - WARNING - line 0 -- did not find matching 'coverage definition end'
        >>> cd.pprint()
        5
        7
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('coverageset')
        else:
            logger = logger.getChild('coverageset')

        namer = kwArgs['namer']
        lookupLineNumber = fws.lineNumber
        terminalString = 'coverage definition end'
        glyphSet = set()

        for line in fws:
            if line.lower() == terminalString:
                r = cls(glyphSet)
                return r

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                if len(tokens) == 1:
                    glyphName = tokens[0]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    
                    if glyphIndex:
                        glyphSet.add(glyphIndex)                    
                    else:
                        logger.warning((
                            'V0956',
                            (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))
                        continue

                else:
                    logger.warning(('V0957', (fws.lineNumber, len(tokens)),
                        'line %d -- incorrect number of tokens, expected 1, found %d'))

        logger.warning(('V0958', (lookupLineNumber, terminalString),
            'line %d -- did not find matching \'%s\''))

        r = cls(glyphSet)

        return r

    @classmethod
    def fromglyphset(cls, glyphSet, **kwArgs):
        """
        Given a set of glyph indices, create a CoverageSet and return it. If a
        keyword argument 'backMap' is specified as an empty dict, on return it
        will be filled out with a mapping from coverage indices back to glyphs.
        
        >>> s = set([2, 15, 5, 9, 1])
        >>> b = {}
        >>> c = CoverageSet.fromglyphset(s, backMap=b)
        >>> c.setNamer(namer.testingNamer())
        >>> print(c)
        {xyz10, xyz16, xyz2, xyz3, xyz6}
        >>> print(b)
        {0: 1, 1: 2, 2: 5, 3: 9, 4: 15}
        """
        
        r = cls(glyphSet)
        
        if 'backMap' in kwArgs:
            kwArgs['backMap'].update(r.getBackMap())
        
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
        >>> fvb = CoverageSet.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.coverageset - DEBUG - Walker has 12 remaining bytes.
        test.coverageset - DEBUG - Format is 1, count is 4
        test.coverageset - DEBUG - Raw data are [33, 64, 85, 96]

        >>> fvb(s[:2], logger=logger)
        test.coverageset - DEBUG - Walker has 2 remaining bytes.
        test.coverageset - ERROR - Insufficient bytes.
        
        >>> obj = fvb(
        ...   s[:2] + utilities.fromhex("00 00") + s[4:],
        ...   logger=logger)
        test.coverageset - DEBUG - Walker has 12 remaining bytes.
        test.coverageset - DEBUG - Format is 1, count is 0
        test.coverageset - WARNING - Count is zero.
        test.coverageset - DEBUG - Raw data are []

        >>> fvb(b'AA' + s[2:], logger=logger)
        test.coverageset - DEBUG - Walker has 12 remaining bytes.
        test.coverageset - DEBUG - Format is 16705, count is 4
        test.coverageset - ERROR - Unknown format: 0x4141.
        
        >>> fvb(s[:4], logger=logger)
        test.coverageset - DEBUG - Walker has 4 remaining bytes.
        test.coverageset - DEBUG - Format is 1, count is 4
        test.coverageset - ERROR - Insufficient bytes for format 1 table.
        
        >>> fvb(s[:4] + s[6:8] + s[4:6] + s[8:], logger=logger)
        test.coverageset - DEBUG - Walker has 12 remaining bytes.
        test.coverageset - DEBUG - Format is 1, count is 4
        test.coverageset - DEBUG - Raw data are [64, 33, 85, 96]
        test.coverageset - ERROR - Format 1 glyphs not sorted.
        
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.coverageset - DEBUG - Walker has 16 remaining bytes.
        test.coverageset - DEBUG - Format is 2, count is 2
        test.coverageset - DEBUG - Raw data are [(15, 15, 0), (60, 66, 1)]

        >>> fvb(s[:4], logger=logger)
        test.coverageset - DEBUG - Walker has 4 remaining bytes.
        test.coverageset - DEBUG - Format is 2, count is 2
        test.coverageset - ERROR - Insufficient bytes for format 2 table.
        
        >>> fvb(s[:10] + s[12:14] + s[10:12] + s[14:], logger=logger)
        test.coverageset - DEBUG - Walker has 16 remaining bytes.
        test.coverageset - DEBUG - Format is 2, count is 2
        test.coverageset - DEBUG - Raw data are [(15, 15, 0), (66, 60, 1)]
        test.coverageset - ERROR - Format 2 segment first greater than last.
        
        >>> fvb(s[:4] + s[10:16] + s[4:10], logger=logger)
        test.coverageset - DEBUG - Walker has 16 remaining bytes.
        test.coverageset - DEBUG - Format is 2, count is 2
        test.coverageset - DEBUG - Raw data are [(60, 66, 1), (15, 15, 0)]
        test.coverageset - ERROR - Format 2 records not sorted.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('coverageset')
        else:
            logger = logger.getChild('coverageset')
        
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

        r = set()
        
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
            
            r.update(v)
        
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
            
            for startGlyph, endGlyph, ignore in v:

                if startGlyph in r or endGlyph in r:
                    logger.error((
                      'V1014',
                      (startGlyph, endGlyph, ignore),
                      "Format 2 segment (%d, %d, %d) overlaps or contains "
                      "duplicates of other ranges."))

                    # Continue validating even with an error;
                    # duplication/overlap will be resolved when added to the
                    # result dictionary.

                if startGlyph > endGlyph:
                    logger.error((
                      'V0093',
                      (),
                      "Format 2 segment first greater than last."))
                    
                    return None
                
                r.update(range(startGlyph, endGlyph + 1))
        
        return cls(r)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new CoverageSet object created from the specified walker.
        
        >>> for obj in (_testingValues[0], _testingValues[1]):
        ...   print(obj == CoverageSet.frombytes(obj.binaryString()))
        True
        True
        """
        
        format, count = w.unpack("HH")
        
        if format == 1:
            r = cls(w.group("H", count))
        
        elif format == 2:
            work = set()
            
            for start, end, ignore in w.group("3H", count):
                work.update(set(range(start, end + 1)))
            
            r = cls(work)
        
        else:
            raise ValueError("Unknown Coverage format: %d" % (format,))
        
        return r
    
    def getBackMap(self):
        """
        Returns a dict mapping coverage indices to glyph indices.
        
        >>> d = _testingValues[0].getBackMap()
        >>> for k in sorted(d): print(k, d[k])
        0 33
        1 64
        2 85
        3 96
        """
        
        return dict(zip(range(len(self)), sorted(self)))
    
    def getMap(self):
        """
        Returns a dict mapping glyph indices to coverage indices.
        
        >>> d = _testingValues[0].getMap()
        >>> for k in sorted(d): print(k, d[k])
        33 0
        64 1
        85 2
        96 3
        """
        
        return dict(zip(sorted(self), range(len(self))))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer
    from io import StringIO

    _testingValues = (
        CoverageSet([33, 64, 85, 96]),  # format 1
        CoverageSet([15, 60, 61, 62, 63, 64, 65, 66]),  # format 2
        CoverageSet([]))

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {'period':5, 'comma':7}
    _test_FW_namer._initialized = True

    _test_FW_fws = FontWorkerSource(StringIO(
        """
        period
        comma
        coverage definition end
        """
    ))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        period
        foo
        one\ttwo
        comma
        """
    ))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
