#
# classdef.py -- New classdef module
#
# Copyright © 2007-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes supporting ClassDefs in OpenType tables.
"""

# System imports
import itertools
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
    allValues = set(obj.values())
    
    if 0 in allValues:
        logger.warning((
          'V0305',
          (),
          "One or more glyphs unnecessarily mapped explicitly to class zero."))
        
        allValues.discard(0)
    
    if allValues != set(range(1, len(allValues) + 1)):
        logger.warning((
          'V0306',
          (),
          "The values in the ClassDef are not contiguous."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ClassDef(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping glyphs to classes.
    
    These are dicts mapping glyph indices to numbers. A primary difference
    between ClassDef and Coverage objects is that Coverages map glyphs to
    unique values, while ClassDefs may map multiple glyphs to the same value.
    
    >>> _testingValues[1].pprint()
    4: 2
    5: 2
    6: 2
    7: 1
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz11: 2
    xyz12: 2
    xyz16: 2
    xyz5: 2
    xyz6: 2
    xyz7: 2
    xyz8: 1
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> obj = _testingValues[1].__copy__()
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(10))
    True
    
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(6))
    ivtest.glyph 6 - ERROR - Glyph index 6 too large.
    ivtest.glyph 7 - ERROR - Glyph index 7 too large.
    False
    
    >>> obj[12] = 0
    >>> obj[13] = 4
    >>> obj[18] = -5
    >>> obj[29] = 1
    >>> obj.isValid(logger=logger, editor=utilities.fakeEditor(25))
    ivtest - WARNING - One or more glyphs unnecessarily mapped explicitly to class zero.
    ivtest - WARNING - The values in the ClassDef are not contiguous.
    ivtest.glyph 18 - ERROR - The negative value -5 cannot be used in an unsigned field.
    ivtest.glyph 29 - ERROR - Glyph index 29 too large.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda n: "glyph %d" % (n,)),
        item_usenamerforstr = True,
        item_validatecode_toolargeglyph = 'V0304',
        item_validatefunc_partial = valassist.isFormat_H,
        map_compactremovesfalses = True,
        map_mergechecknooverlap = True,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def __eq__(self, other):
        """
        Test for equal topologies, not just equal values. Note that any glyphs
        explicitly mapped to 0 are excluded (since all non-present glyphs
        implictly map to 0, explicit maps to zero are redundant).
        
        >>> c1 = ClassDef({15: 2, 16: 1, 17: 2, 19: 3, 25: 1})
        >>> c2 = ClassDef({15: 2, 16: 9, 17: 2, 19: 3, 25: 9})
        >>> c1 == c2
        True
        >>> c2[28] = 0
        >>> c1 == c2
        True
        >>> c2[30] = 2
        >>> c1 == c2
        False
        >>> 
        """
        
        revSelf = utilities.invertDictFull(self)
        revOther = utilities.invertDictFull(other)
        
        if 0 in revSelf:
            del revSelf[0]
        
        if 0 in revOther:
            del revOther[0]
        
        topSelf = set(frozenset(v) for v in revSelf.values())
        topOther = set(frozenset(v) for v in revOther.values())
        return topSelf == topOther
    
    def __getitem__(self, key):
        """
        Returns the specified item, or zero if that item is not present.
        
        >>> c = ClassDef({4: 2, 5: 3, 6: 2})
        >>> c[5]
        3
        >>> c[9]
        0
        """
        
        if key in self:
            return super(ClassDef, self).__getitem__(key)
        
        return 0
    
    def __ne__(self, other): return not (self == other)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0002 0000                                |....            |
        
        >>> h(_testingValues[1].binaryString())
               0 | 0001 0004 0004 0002  0002 0002 0001      |..............  |
        
        >>> h(_testingValues[2].binaryString())
               0 | 0002 0004 0004 0006  0002 0007 0007 0001 |................|
              10 | 000A 000B 0002 000F  000F 0002           |............    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            v = sorted(self)
            sv = []
            
            if len(v) == (v[-1] - v[0] + 1):
                # ok to try format 1
                w1 = writer.LinkedWriter()
                w1.add("3H", 1, v[0], len(v))
                w1.addGroup("H", [self[i] for i in v])
                sv.append(w1.binaryString())
            
            w2 = writer.LinkedWriter()
            groups = []
            
            for start, stop, skip in utilities.monotonicGroupsGenerator(v):
                cumulCount = 0
                it = (self[i] for i in range(start, stop, skip))
                
                for k, g in itertools.groupby(it):
                    subCount = len(list(g))
                    
                    groups.append((
                      start + cumulCount,
                      start + cumulCount + subCount - 1,
                      k))
                    
                    cumulCount += subCount
            
            w2.add("HH", 2, len(groups))
            w2.addGroup("3H", groups)
            sv.append(w2.binaryString())
            sv.sort(key=len)
            w.addString(sv[0])  # shortest
        
        else:
            w.add("HH", 2, 0)  # format 0, no ranges
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Like fromFontWorkerSource, this method returns a new ClassDef from the
        specified stream containing FontWorker source code. However, it also
        does extensive validation via the logging module (the client should have
        done a logging.basicConfig call prior to calling this method, unless a
        logger is passed in via the 'logger' keyword argument).

        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> _test_FW_fws.goto(1) # go back to the first line
        >>> cd = ClassDef.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> cd.pprint()
        5: 2
        7: 4
        11: 6
        >>> cd = ClassDef.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        test_FW.classDef - WARNING - line 3 -- incorrect number of tokens, expected 2, found 1
        test_FW.classDef - WARNING - line 4 -- incorrect number of tokens, expected 2, found 3
        test_FW.classDef - WARNING - line 5 -- glyph 'z' not found
        test_FW.classDef - WARNING - line 6 -- token 'bar' for glyph 'b' could not be parsed as a class index (integer)
        test_FW.classDef - WARNING - line 7 -- class for 'a' previously defined
        test_FW.classDef - WARNING - line 0 -- did not find matching 'class definition end'
        >>> cd.pprint()
        5: 2
        """
        
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('classDef')
        else:
            logger = logger.getChild('classDef')

        namer = kwArgs.get('namer')
        lookupLineNumber = fws.lineNumber
        terminalString = 'class definition end'
        r = cls()
        
        for line in fws:
            if line.lower() == terminalString:
                return r
            
            elif len(line) > 0:
                tokens = line.split('\t')
                if len(tokens) == 2:
                    glyphName = tokens[0].strip()
                    glyphIndex = namer.glyphIndexFromString(glyphName)

                    try:
                        classIndex = int(tokens[1])
                    except ValueError:
                        classIndex = None

                    if glyphIndex is None:
                        logger.warning(('V0956', (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))
                        continue

                    if classIndex is None:
                        logger.warning((
                            'Vxxxx',
                            (fws.lineNumber, tokens[1], glyphName),
                            "line %d -- token '%s' for glyph '%s' could not "
                            "be parsed as a class index (integer)"))
                        continue

                    if glyphIndex in r:
                        logger.warning((
                          'Vxxxx',
                          (fws.lineNumber, glyphName),
                          "line %d -- class for '%s' previously defined"))
                    else:
                        if classIndex == 0:
                            logger.warning((
                                'Vxxxx',
                                (fws.lineNumber, glyphName),
                                "line %d -- glyph '%s' explicitly mapped "
                                "to class 0; will re-map"))
                        r[glyphIndex] = classIndex

                else:
                    logger.warning(('V0957', (fws.lineNumber, len(tokens)), 
                        'line %d -- incorrect number of tokens, expected 2, found %d'))
        
        logger.warning(('V0958', (lookupLineNumber, terminalString),
            'line %d -- did not find matching \'%s\''))
        
        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new ClassDef. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = ClassDef.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.classDef - DEBUG - Walker has 14 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 1.
        test.classDef - DEBUG - First is 4, and count is 4
        test.classDef - DEBUG - Raw data are (2, 2, 2, 1)
        
        >>> fvb(s[:1], logger=logger)
        test.classDef - DEBUG - Walker has 1 remaining bytes.
        test.classDef - ERROR - Insufficient bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.classDef - DEBUG - Walker has 2 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 1.
        test.classDef - ERROR - Insufficient bytes for format 1 header.
        
        >>> fvb(s[:6], logger=logger)
        test.classDef - DEBUG - Walker has 6 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 1.
        test.classDef - DEBUG - First is 4, and count is 4
        test.classDef - ERROR - Insufficient bytes for format 1 table.
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.classDef - DEBUG - Walker has 28 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 2.
        test.classDef - DEBUG - Count is 4
        test.classDef - DEBUG - Raw data are [(4, 6, 2), (7, 7, 1), (10, 11, 2), (15, 15, 2)]
        
        >>> fvb(s[:2], logger=logger)
        test.classDef - DEBUG - Walker has 2 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 2.
        test.classDef - ERROR - Insufficient bytes for format 2 count.
        
        >>> fvb(s[:4], logger=logger)
        test.classDef - DEBUG - Walker has 4 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 2.
        test.classDef - DEBUG - Count is 4
        test.classDef - ERROR - Insufficient bytes for format 2 table.
        
        >>> fvb(s[:4] + s[6:8] + s[4:6] + s[8:], logger=logger)
        test.classDef - DEBUG - Walker has 28 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 2.
        test.classDef - DEBUG - Count is 4
        test.classDef - DEBUG - Raw data are [(6, 4, 2), (7, 7, 1), (10, 11, 2), (15, 15, 2)]
        test.classDef - ERROR - Format 2 segment first greater than last.
        
        >>> fvb(s[:4] + s[10:16] + s[4:10] + s[16:], logger=logger)
        test.classDef - DEBUG - Walker has 28 remaining bytes.
        test.classDef - DEBUG - ClassDef is format 2.
        test.classDef - DEBUG - Count is 4
        test.classDef - DEBUG - Raw data are [(7, 7, 1), (4, 6, 2), (10, 11, 2), (15, 15, 2)]
        test.classDef - ERROR - Format 2 segments not sorted by first glyph.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        test.classDef - DEBUG - Walker has 28 remaining bytes.
        test.classDef - ERROR - Unknown format 0x4141.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('classDef')
        else:
            logger = logger.getChild('classDef')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if 'forceFormat' in kwArgs:
            format = kwArgs['forceFormat']
        
        else:
            if w.length() < 2:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            format = w.unpack("H")
        
        if format not in {1, 2}:
            logger.error(('E5000', (format,), "Unknown format 0x%04X."))
            return None
        
        logger.debug(('V0079', (format,), "ClassDef is format %d."))
        r = cls()
        
        if kwArgs.get('longValues', False):
            dataFormat = "L"
            dataFormatSize = 4
        
        else:
            dataFormat = "H"
            dataFormatSize = 2
        
        if format == 1:
            if w.length() < 4:
                logger.error((
                  'V0080',
                  (),
                  "Insufficient bytes for format 1 header."))
                
                return None
            
            first, count = w.unpack("2H")
            
            logger.debug((
              'Vxxxx',
              (first, count),
              "First is %d, and count is %d"))
            
            if w.length() < count * dataFormatSize:
                logger.error((
                  'V0081',
                  (),
                  "Insufficient bytes for format 1 table."))
                
                return None
            
            v = w.group(dataFormat, count)
            logger.debug(('Vxxxx', (v,), "Raw data are %s"))
            
            for i in range(count):
                r[i + first] = v[i]
        
        else:
            if w.length() < 2:
                logger.error((
                  'V0082',
                  (),
                  "Insufficient bytes for format 2 count."))
                
                return None
            
            count = w.unpack("H")
            logger.debug(('Vxxxx', (count,), "Count is %d"))
            
            if w.length() < count * (4 + dataFormatSize):
                logger.error((
                  'V0083',
                  (),
                  "Insufficient bytes for format 2 table."))
                return None
            
            v = list(w.group("2H" + dataFormat, count))
            logger.debug(('Vxxxx', (v,), "Raw data are %s"))
            
            if v != sorted(v, key=operator.itemgetter(0)):
                logger.error((
                  'V0084',
                  (),
                  "Format 2 segments not sorted by first glyph."))
                
                return None
            
            for first, last, classIndex in v:
                if first > last:
                    logger.error((
                      'V0085',
                      (),
                      "Format 2 segment first greater than last."))
                    
                    return None
                
                for glyphIndex in range(first, last + 1):
                    r[glyphIndex] = classIndex
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new ClassDef from the specified walker. In order to support
        the creation of ClassDef objects for format 2 'kern' and 'kerx' table,
        we allow these keyword arguments:
        
            forceFormat     If this is provided, it should be either 1 or 2,
                            and will be used as the format (note in this case
                            no 16-bit value for format will be unpacked)
            
            longValues      Default False; if True, values will be unpacked as
                            32-bit values instead of the usual 16-bit values.
        
        >>> fb = ClassDef.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        if 'forceFormat' in kwArgs:
            format = kwArgs['forceFormat']
        
        else:
            format = w.unpack("H")
            
            if format != 1 and format != 2:
                raise ValueError("Unknown ClassDef format: %s" % (format,))
        
        r = cls()
        dataFormat = ("L" if kwArgs.get('longValues', False) else "H")
        
        if format == 1:
            first, count = w.unpack("HH")
            v = w.group(dataFormat, count)
            
            for i in range(count):
                r[i + first] = v[i]
        
        else:
            it = w.group("2H" + dataFormat, w.unpack("H"))
            
            for first, last, classIndex in it:
                for glyphIndex in range(first, last + 1):
                    r[glyphIndex] = classIndex
        
        return r
    
    def newValueObject(self, fromValue=None):
        """
        Returns a value not currently used in the dict. If fromValue is
        specified and is not currently used, it will be returned. Note that no
        attempt is made to "fill in holes" or to keep the dict from becoming
        sparse in values.
        
        >>> _testingValues[1].newValueObject()
        3
        >>> _testingValues[1].newValueObject(12)
        12
        >>> _testingValues[1].newValueObject(1)
        3
        >>> _testingValues[0].newValueObject()
        1
        """
        
        s = set(self.values())
        
        if (fromValue is not None) and (fromValue not in s):
            return fromValue
        
        if not self:
            return 1  # don't return zero, as that value is special
        
        return sorted(s)[-1] + 1

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    from io import StringIO
    from fontio3.opentype.fontworkersource import FontWorkerSource

    _testingValues = (
        ClassDef(),  # empty
        ClassDef({4: 2, 5: 2, 6: 2, 7: 1}),  # format 1
        ClassDef({4: 2, 5: 2, 6: 2, 7: 1, 10: 2, 11: 2, 15: 2}))  # format 2

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'a': 5,
        'b': 7,
        'c': 11
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        a\t2
        b\t4
        c\t6
        class definition end
        """
    ))
    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        a\t2
        b
        c\t6\t7
        z\t11
        b\tbar
        a\t5
        """
    ))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
