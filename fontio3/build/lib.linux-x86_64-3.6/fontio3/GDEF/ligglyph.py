#
# ligglyph.py
#
# Copyright © 2005-2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to lists of attachment points in GDEF tables.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.GDEF import caretvalue

# -----------------------------------------------------------------------------

#
# Classes
#

class LigGlyphTable(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects containing caret positioning information for all the splits in a
    ligature. These are lists of CaretValue objects in display order (LR or RL,
    as appropriate).
    
    >>> _testingValues[2].pprint(label="Some ligature splits")
    Some ligature splits:
      CaretValue #1:
        Simple caret value in FUnits: -650
      CaretValue #2:
        Simple caret value in FUnits: 0
      CaretValue #3:
        Simple caret value in FUnits: 500
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda n: "CaretValue #%d" % (n + 1,)))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content to the specified LinkedWriter. There is one
        keyword argument:
        
            cvPool  If specified should be a dict for the CaretValue pool. If
                    not specified, a local pool will be used and the CaretValue
                    binary data will be written locally (with a locally-defined
                    device pool).
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0004 0001 01F4                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0003 0008 000C 0010  0001 FD76 0001 0000 |...........v....|
              10 | 0001 01F4                                |....            |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0002 0006 000A 0002  0000 0002 000C      |..............  |
        
        >>> utilities.hexdump(_testingValues[4].binaryString())
               0 | 0001 0004 0003 01F4  0006 000C 0011 0002 |................|
              10 | EF00 1200                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        cvPool = kwArgs.get('cvPool')
        
        if cvPool is None:
            cvPool = {}
            doLocal = True
        else:
            doLocal = False
        
        w.add("H", len(self))
        
        for obj in self:
            objID = id(obj)
            
            if objID not in cvPool:
                cvPool[objID] = (obj, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, cvPool[objID][1])
        
        if doLocal:
            devicePool = {}
            kwArgs.pop('devicePool', None)
            
            for obj, stake in cvPool.values():
                obj.buildBinary(
                  w,
                  stakeValue = stake,
                  devicePool = devicePool,
                  **kwArgs)
            
            for obj, stake in devicePool.values():
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new LigGlyphTable. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = LigGlyphTable.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.ligglyph - DEBUG - Walker has 8 remaining bytes.
        test.ligglyph - INFO - Number of splits: 1.
        test.ligglyph.[0].caretvalue.coordinate - DEBUG - Walker has 4 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        test.ligglyph - DEBUG - Walker has 1 remaining bytes.
        test.ligglyph - ERROR - Insufficient bytes.
        
        >>> obj = fvb(utilities.fromhex("00 00"), logger=logger)
        test.ligglyph - DEBUG - Walker has 2 remaining bytes.
        test.ligglyph - WARNING - No offsets present.
        
        >>> fvb(utilities.fromhex("00 00") + s[2:], logger=logger)
        test.ligglyph - DEBUG - Walker has 8 remaining bytes.
        test.ligglyph - ERROR - Count is zero but more bytes are present.
        
        >>> fvb(s[:2], logger=logger)
        test.ligglyph - DEBUG - Walker has 2 remaining bytes.
        test.ligglyph - INFO - Number of splits: 1.
        test.ligglyph - ERROR - Insufficient bytes for offset array.
        
        >>> fvb(s[:4], logger=logger)
        test.ligglyph - DEBUG - Walker has 4 remaining bytes.
        test.ligglyph - INFO - Number of splits: 1.
        test.ligglyph.[0].caretvalue - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ligglyph')
        else:
            logger = logger.getChild('ligglyph')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        
        if not count:
            if w.length():
                logger.error((
                  'V0100',
                  (),
                  "Count is zero but more bytes are present."))
                
                return None
            
            else:
                logger.warning(('V0101', (), "No offsets present."))
        
        else:
            logger.info(('V0102', (count,), "Number of splits: %d."))
        
        if w.length() < 2 * count:
            logger.error(('V0103', (), "Insufficient bytes for offset array."))
            return None
        
        offsets = w.group("H", count)
        fv = caretvalue.CaretValue_validated  # factory function
        r = cls([None] * count)
        okToReturn = True
        
        for i, offset in enumerate(offsets):
            subLogger = logger.getChild("[%d]" % (i,))
            obj = fv(w.subWalker(offset), logger=subLogger, **kwArgs)
            
            if obj is None:
                okToReturn = False
            else:
                r[i] = obj
        
        return (r if okToReturn else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new LigGlyphTable from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == LigGlyphTable.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == LigGlyphTable.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[3]
        >>> obj == LigGlyphTable.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[4]
        >>> obj == LigGlyphTable.frombytes(obj.binaryString())
        True
        """
        
        # LigGlyph table
        # bytes 0 - 1 : CaretCount
        # bytes 2 ... : two-byte offsets (from byte 0 of LigGlyph table) to
        #               CaretValue tables
        
        f = caretvalue.CaretValue  # factory function, takes a walker
        
        return cls(
          f(w.subWalker(offset), **kwArgs)
          for offset in w.group("H", w.unpack("H")))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _cvtv = caretvalue._testingValues
    
    _testingValues = (
        LigGlyphTable(),
        LigGlyphTable([_cvtv[1]]),
        LigGlyphTable([_cvtv[2], _cvtv[0], _cvtv[1]]),
        LigGlyphTable([_cvtv[3], _cvtv[4]]),
        LigGlyphTable([_cvtv[5]]),
        LigGlyphTable([_cvtv[6]]))
    
    del _cvtv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
