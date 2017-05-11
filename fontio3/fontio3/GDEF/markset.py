#
# markset.py
#
# Copyright © 2009-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to mark sets.
"""

# System imports
from collections import defaultdict
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.opentype import coverage, coverageset
from fontio3.utilities import span

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, obj, **kwArgs):
    if not obj:
        p.simple("No mark glyph sets are defined.", **kwArgs)
        return
    
    nm = kwArgs.get('namer', obj.getNamer())
    
    for i,v in enumerate(obj):
        if not v:
            continue
        
        s = span.Span(v)
        
        if nm is not None:
            sv = []
            nf = nm.bestNameForGlyphIndex
            
            for first, last in s:
                if first == last:
                    sv.append(nf(first))
                else:
                    sv.append("%s - %s" % (nf(first), nf(last)))
            
            p.simple(
              ', '.join(sv),
              label = "Mark Glyph Set %d" % (i,),
              multilineExtraIndent = 0)
        
        else:
            p.simple(
              str(s),
              label = "Mark Glyph Set %d" % (i,),
              multilineExtraIndent = 0)

# -----------------------------------------------------------------------------

#
# Classes
#

class MarkSetTable(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects collecting Coverages for OpenType 1.6 mark set tables.
    
    These are lists whose elements are Coverage objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Mark Glyph Set 0: xyz16, xyz23 - xyz24, xyz31
    Mark Glyph Set 1: xyz13, U+0163
    Mark Glyph Set 2: xyz16, xyz23 - xyz24, xyz31
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_pprintfunc = _pprint)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0003 0000 0010  0000 001C 0000 0010 |................|
              10 | 0001 0004 000F 0016  0017 001E 0001 0002 |................|
              20 | 000C 0063                                |...c            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Add content and unresolved references
        w.add("HH", 1, len(self))
        localPool = {}
        
        for obj in self:
            objID = id(obj)
            
            if objID not in localPool:
                localPool[objID] = (obj, w.getNewStake())
            
            w.addUnresolvedOffset("L", stakeValue, localPool[objID][1])
        
        # Resolve the references
        for obj, stake in localPool.values():
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new MarkSetTable from the specified FontWorkerSource.

        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> mst = MarkSetTable.fromValidatedFontWorkerSource(_test_FW_fws1, namer=_test_FW_namer, logger=logger)
        >>> mst.pprint()
        Mark Glyph Set 0: 1, 5
        Mark Glyph Set 1: 4, 7
        Mark Glyph Set 2: 5
        Mark Glyph Set 3: 3
        >>> mst = MarkSetTable.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        test_FW.markset - WARNING - line 8 -- glyph 'glyph9123412' not found
        test_FW.markset - WARNING - MarkFilterSet 1 will be renumbered to 0
        test_FW.markset - WARNING - MarkFilterSet 8 will be renumbered to 1
        test_FW.markset - WARNING - MarkFilterSet 9 will be renumbered to 2
        >>> mst.pprint()
        Mark Glyph Set 0: 4-5
        Mark Glyph Set 1: 3
        Mark Glyph Set 2: 5, 7
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('markset')
        else:
            logger = logger.getChild('markset')

        namer = kwArgs['namer']
        lookupLineNumber = fws.lineNumber
        terminalString = 'set definition end'

        glyphSetsDict = defaultdict(set)

        r = cls()

        for line in fws:
            if line.lower() == terminalString:
                cvgs = []
                
                for k, gs in sorted(glyphSetsDict.items()):
                    if k != len(cvgs):
                        logger.warning((
                            'Vxxxx',
                            (k, len(cvgs)),
                            "MarkFilterSet %d will be renumbered to %d"))
                    
                    cvgs.append(coverageset.CoverageSet.fromglyphset(gs))

                return cls(cvgs)

            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]

                if len(tokens) == 2:
                    glyphName = tokens[0]
                    glyphIndex = namer.glyphIndexFromString(glyphName)
                    setIndex = int(tokens[1])
                    
                    if glyphIndex:
                        glyphSetsDict[setIndex].add(glyphIndex)
                    
                    else:
                        logger.warning((
                            'V0956',
                            (fws.lineNumber, glyphName),
                            "line %d -- glyph '%s' not found"))
                        
                        continue

                else:
                    logger.warning((
                      'V0957',
                      (fws.lineNumber, len(tokens)),
                      'line %d -- incorrect number of tokens, '
                      'expected 2, found %d'))

        logger.warning(('V0958', (lookupLineNumber, terminalString),
            'line %d -- did not find matching \'%s\''))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new MarkSetTable. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = MarkSetTable.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.markset - DEBUG - Walker has 36 remaining bytes.
        test.markset - INFO - MarkSet has 3 element(s).
        test.markset.[0].coverage - DEBUG - Walker has 20 remaining bytes.
        test.markset.[0].coverage - DEBUG - Format is 1, count is 4
        test.markset.[0].coverage - DEBUG - Raw data are [15, 22, 23, 30]
        test.markset.[1].coverage - DEBUG - Walker has 8 remaining bytes.
        test.markset.[1].coverage - DEBUG - Format is 1, count is 2
        test.markset.[1].coverage - DEBUG - Raw data are [12, 99]
        test.markset.[2].coverage - DEBUG - Walker has 20 remaining bytes.
        test.markset.[2].coverage - DEBUG - Format is 1, count is 4
        test.markset.[2].coverage - DEBUG - Raw data are [15, 22, 23, 30]
        
        >>> fvb(s[:1], logger=logger)
        test.markset - DEBUG - Walker has 1 remaining bytes.
        test.markset - ERROR - Insufficient bytes.
        
        >>> fvb(b'AA' + s[2:], logger=logger)
        test.markset - DEBUG - Walker has 36 remaining bytes.
        test.markset - ERROR - Unknown format: 0x4141.
        
        >>> fvb(s[:2], logger=logger)
        test.markset - DEBUG - Walker has 2 remaining bytes.
        test.markset - ERROR - Insufficient bytes for offset count.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('markset')
        else:
            logger = logger.getChild('markset')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 1:
            logger.error(('V0109', (format,), "Unknown format: 0x%04X."))
            return None
        
        if w.length() < 2:
            logger.error(('V0110', (), "Insufficient bytes for offset count."))
            return None
        
        offsetCount = w.unpack("H")
        logger.info(('V0111', (offsetCount,), "MarkSet has %d element(s)."))
        
        if w.length() < 4 * offsetCount:
            logger.error(('V0112', (), "Insufficient bytes for offset table."))
            return None
        
        offsets = w.group("L", offsetCount)
        fvw = coverage.Coverage.fromvalidatedwalker
        okToReturn = True
        r = cls([None] * offsetCount)
        
        for i, offset in enumerate(offsets):
            subLogger = logger.getChild("[%d]" % (i,))
            obj = fvw(w.subWalker(offset), logger=subLogger, **kwArgs)
            
            if obj is None:
                okToReturn = False
            else:
                r[i] = obj
        
        return (r if okToReturn else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MarkSetTable from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == MarkSetTable.frombytes(obj.binaryString())
        True
        """
        
        format = w.unpack("H")
        
        if format != 1:
            raise ValueError("Unsupported Mark Set format: %d" % (format,))
        
        offsets = w.group("L", w.unpack("H"))
        maker = coverage.Coverage.fromwalker
        return cls(maker(w.subWalker(offset), **kwArgs) for offset in offsets)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from io import StringIO

    from fontio3 import utilities
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer
    
    _cv1 = coverage.Coverage({15: 0, 22: 1, 23: 2, 30: 3})
    _cv2 = coverage.Coverage({12: 0, 99: 1})
    
    _testingValues = (
        MarkSetTable(),
        MarkSetTable([_cv1, _cv2, _cv1]))
    
    del _cv1, _cv2

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {'glyph%d' % (x,):x for x in range(10)}
    _test_FW_namer._initialized = True

    _test_FW_fws1 = FontWorkerSource(StringIO(
        """
        glyph1\t0
        glyph4\t1
        glyph5\t0
        glyph7\t1
        glyph5\t2
        glyph3\t3
        set definition end
        """
    ))
    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        glyph5\t1
        glyph4\t1
        glyph5\t9
        glyph7\t9
        glyph5\t9
        glyph3\t8
        glyph9123412\t3
        set definition end
        """
    ))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
