#
# ligcaret.py
#
# Copyright © 2005-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to lists of attachment points in GDEF tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GDEF import ligglyph
from fontio3.opentype import coverage
from fontio3.opentype.fontworkersource import fwsint
from fontio3.GDEF import caretvalue_coord

# -----------------------------------------------------------------------------

#
# Classes
#

class LigCaretTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing positioning information for carets within ligatures.
    
    These are dicts mapping glyph indices to LigGlyphTable objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60003:
      CaretValue #1:
        Caret value in FUnits: 500
        Device record:
          Tweak at 12 ppem: -2
          Tweak at 13 ppem: -1
          Tweak at 16 ppem: 1
          Tweak at 17 ppem: 2
    xyz72:
      CaretValue #1:
        Simple caret value in FUnits: 500
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_mergechecknooverlap = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter. There is one
        keyword argument:
        
            devicePool      If specified should be a dict for the device pool.
                            If not specified, a local pool will be used and the
                            Device binary will be written locally.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0008 0002 0010 0014  0001 0002 0047 0062 |.............G.b|
              10 | 0001 0008 0001 0008  0001 01F4 0003 01F4 |................|
              20 | 0006 000C 0011 0002  EF00 1200           |............    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        devicePool = kwArgs.pop('devicePool', None)
        cvPool = {}
        kwArgs.pop('cvPool', None)
        
        if devicePool is None:
            devicePool = {}
            doLocal = True
        else:
            doLocal = False
        
        # Add content and unresolved references
        sortedKeys = sorted(self)
        d = dict(zip(sortedKeys, range(len(self))))
        covTable = coverage.Coverage(d)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", len(self))
        localPool = {}
        
        for key in sortedKeys:
            objID = id(self[key])
            
            if objID not in localPool:
                localPool[objID] = (self[key], w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, localPool[objID][1])
        
        # Resolve the references
        covTable.buildBinary(w, stakeValue=covStake, **kwArgs)
        
        for key in sortedKeys:
            objID = id(self[key])
            
            if objID in localPool:
                obj, stake = localPool[objID]
                obj.buildBinary(w, stakeValue=stake, cvPool=cvPool, **kwArgs)
                del localPool[objID]
        
        for obj, stake in cvPool.values():
            obj.buildBinary(
              w,
              stakeValue = stake,
              devicePool = devicePool,
              **kwArgs)
        
        if doLocal:
            for obj, stake in devicePool.values():
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
        
        else:
            kwArgs['devicePool'] = devicePool
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new LigCaretTable from the specified FontWorker
        source code with extensive validation via the logging module (the
        client should have done a logging.basicConfig call prior to calling
        this method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> _test_FW_fws.goto(1) # go back to first line
        >>> lct = LigCaretTable.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger, editor=_test_FW_editor)
        test_FW.ligcaret - WARNING - line 5 -- no explicit caret positions specified; auto-calculating from advance width.
        >>> lct.pprint()
        5:
          CaretValue #1:
            Simple caret value in FUnits: 42
        7:
          CaretValue #1:
            Simple caret value in FUnits: 50
          CaretValue #2:
            Simple caret value in FUnits: 55
        11:
          CaretValue #1:
            Simple caret value in FUnits: 12
          CaretValue #2:
            Simple caret value in FUnits: 17
          CaretValue #3:
            Simple caret value in FUnits: 37
        13:
          CaretValue #1:
            Simple caret value in FUnits: 512
          CaretValue #2:
            Simple caret value in FUnits: 1024
        >>> lct2 = LigCaretTable.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger, editor=_test_FW_editor)
        test_FW.ligcaret - ERROR - line 3 -- mismatch between caret count (2);and number of carets actually listed (3); discarding.
        test_FW.ligcaret - ERROR - line 4 -- mismatch between caret count (3);and number of carets actually listed (2); discarding.
        test_FW.ligcaret - WARNING - line 5 -- glyph 'z' not found
        test_FW.ligcaret - WARNING - did not find 'carets end'
        >>> lct2.pprint()
        5:
          CaretValue #1:
            Simple caret value in FUnits: 42
        """
        editor = kwArgs['editor']
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('ligcaret')
        else:
            logger = logger.getChild('ligcaret')

        namer = kwArgs['namer']

        r = cls()

        terminalString = 'carets end'
        CVC = caretvalue_coord.CaretValue_Coord

        for line in fws:
            if line.lower() == terminalString:
                return r
            elif len(line) > 0:
                tokens = line.split('\t')
                glyphName = tokens[0]
                glyphIndex = namer.glyphIndexFromString(glyphName)
                if glyphIndex:
                    caretCount = fwsint(tokens[1])
                    if caretCount:
                        caretPositions = []
                        for x in tokens[2:]:
                            cpi = fwsint(x)
                            if cpi:
                                caretPositions.append(CVC(cpi))
                            else:
                                logger.error((
                                    'Vxxxx',
                                    (fws.lineNumber, x),
                                    "line %d -- could not read '%s' as a ligature "
                                    "caret position"))

                        if len(caretPositions) == 0:
                            logger.warning((
                                'Vxxxx',
                                (fws.lineNumber,),
                                "line %d -- no explicit caret positions specified; "
                                "auto-calculating from advance width."))
                            aw = editor.hmtx[glyphIndex].advance
                            gdiv = caretCount + 1
                            cw = int(round(aw/gdiv * 1.0))
                            caretPositions = [CVC(cw*i) for i in range(1, gdiv)]

                        elif len(caretPositions) != caretCount:
                            logger.error((
                                'V0955',
                                (fws.lineNumber, caretCount, len(caretPositions)),
                                "line %d -- mismatch between caret count (%d);"
                                "and number of carets actually listed (%d); "
                                "discarding."))
                            continue

                    else:
                        logger.error((
                            'Vxxxx',
                            (fws.lineNumber, tokens[1]),
                            "line %d -- unrecognized value '%s' for caret count"))
                        continue

                    r[glyphIndex] = ligglyph.LigGlyphTable(caretPositions)

                else:
                    logger.warning(('V0956', (fws.lineNumber, glyphName),
                        "line %d -- glyph '%s' not found"))

        logger.warning(('V0958', (terminalString), "did not find '%s'"))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new LigCaretTable. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = functools.partial(
        ...   LigCaretTable.fromvalidatedbytes,
        ...   is_v0=False)
        >>> obj = fvb(s, logger=logger)
        test.ligcaret - DEBUG - Walker has 44 remaining bytes.
        test.ligcaret.coverage - DEBUG - Walker has 36 remaining bytes.
        test.ligcaret.coverage - DEBUG - Format is 1, count is 2
        test.ligcaret.coverage - DEBUG - Raw data are [71, 98]
        test.ligcaret - INFO - Number of LigGlyphTables: 2.
        test.ligcaret.[0].ligglyph - DEBUG - Walker has 28 remaining bytes.
        test.ligcaret.[0].ligglyph - INFO - Number of splits: 1.
        test.ligcaret.[0].ligglyph.[0].caretvalue.coordinate - DEBUG - Walker has 20 remaining bytes.
        test.ligcaret.[1].ligglyph - DEBUG - Walker has 24 remaining bytes.
        test.ligcaret.[1].ligglyph - INFO - Number of splits: 1.
        test.ligcaret.[1].ligglyph.[0].caretvalue.device - DEBUG - Walker has 16 remaining bytes.
        test.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - Walker has 10 remaining bytes.
        test.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - StartSize=12, endSize=17, format=2
        test.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - Data are (61184, 4608)
        
        >>> fvb(s[:1], logger=logger)
        test.ligcaret - DEBUG - Walker has 1 remaining bytes.
        test.ligcaret - ERROR - Insufficient bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.ligcaret - DEBUG - Walker has 2 remaining bytes.
        test.ligcaret.coverage - DEBUG - Walker has 0 remaining bytes.
        test.ligcaret.coverage - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ligcaret')
        else:
            logger = logger.getChild('ligcaret')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        wSub = w.subWalker(w.unpack("H"))
        cover = coverage.Coverage.fromvalidatedwalker(wSub, logger=logger)
        
        if cover is None:
            return None
        
        localPool = {}  # offset -> LigGlyphTable
        ligGlyphRecords = []
        fvw = ligglyph.LigGlyphTable.fromvalidatedwalker
        
        if w.length() < 2:
            logger.error(('V0104', (), "Insufficient bytes for offset count."))
            return None
        
        offsetCount = w.unpack("H")
        
        if offsetCount:
            logger.info((
              'V0105',
              (offsetCount,),
              "Number of LigGlyphTables: %d."))
        
        elif w.length() and (not kwArgs["is_v0"]):
            logger.error((
              'V0106',
              (),
              "Offset count is zero but bytes remain."))
            
            return None
        
        else:
            logger.warning(('V0107', (), "Offset count is zero."))
        
        if w.length() < 2 * offsetCount:
            logger.error(('V0108', (), "Insufficient bytes for offset table."))
            return None
        
        okToReturn = True
        
        for i, offset in enumerate(w.group("H", offsetCount)):
            if offset not in localPool:
                subLogger = logger.getChild("[%d]" % (i,))
                obj = fvw(w.subWalker(offset), logger=subLogger, **kwArgs)
                
                if obj is None:
                    okToReturn = False
                
                localPool[offset] = obj
            
            ligGlyphRecords.append(localPool[offset])
        
        if not okToReturn:
            return None
        
        r = cls()
        
        for glyphIndex, coverageIndex in cover.items():
            if coverageIndex >= len(ligGlyphRecords):
                logger.error((
                  'V0135',
                  (coverageIndex,),
                  "No LigGlyphTable for coverageIndex %d."))
                
                return None
            
            r[glyphIndex] = ligGlyphRecords[coverageIndex]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LigCaretTable from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == LigCaretTable.frombytes(obj.binaryString())
        True
        """
        
        # LigCaretList table
        # bytes 0 - 1 : Coverage offset
        # bytes 2 - 3 : LigGlyphCount
        # bytes 4 ... : two-bytes offsets (from byte 0 of LigCaretList
        #               table) to LigGlyph tables
        
        cover = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        localPool = {}  # offset -> ligglyph
        ligGlyphRecords = []
        fw = ligglyph.LigGlyphTable.fromwalker
        
        for offset in w.group("H", w.unpack("H")):
            if offset not in localPool:
                localPool[offset] = fw(w.subWalker(offset), **kwArgs)
            
            ligGlyphRecords.append(localPool[offset])
        
        r = cls()
        
        for glyphIndex, coverageIndex in cover.items():
            r[glyphIndex] = ligGlyphRecords[coverageIndex]
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from collections import namedtuple
    import functools
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.hmtx import Hmtx, MtxEntry
    from io import StringIO
    from fontio3.opentype.fontworkersource import FontWorkerSource
    
    _lgtv = ligglyph._testingValues
    
    _testingValues = (
        LigCaretTable(),
        LigCaretTable({71: _lgtv[1], 98: _lgtv[4]}),
        LigCaretTable({10: _lgtv[5]}))
    
    del _lgtv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'a': 5,
        'b': 7,
        'c': 11,
        'd': 13
    }
    _test_FW_namer._initialized = True
    
    _test_FW_hmtx = Hmtx()
    _test_FW_hmtx[13] = MtxEntry(1536, 100)
    
    _test_FW_editor = namedtuple('editor', ['hmtx']) # avoid circular import issues...
    _test_FW_editor.hmtx = _test_FW_hmtx
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        a\t1\t42
        b\t2\t50\t55
        c\t3\t12\t17\t37
        d\t2
        carets end
        """
    ))
    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        a\t1\t42
        b\t2\t50\t55\t60
        c\t3\t12\t17
        z\t1\t43
        """
    ))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
