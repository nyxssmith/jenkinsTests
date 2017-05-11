#
# multiple.py
#
# Copyright © 2007-2010, 2012-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 2 (Multiple Substitution) subtables for a GSUB table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.GSUB import multiple_glyphtuple
from fontio3.GSUB.effects import EffectsSummary
from fontio3.opentype import coverage, runningglyphs

# -----------------------------------------------------------------------------

#
# Constants
#

GT = multiple_glyphtuple.Multiple_GlyphTuple

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    
    for inGlyph, outSeq in obj.items():
        if len(outSeq) == 1:
            if inGlyph == outSeq[0]:
                logger.warning((
                  'V0424',
                  (inGlyph,),
                  "Glyph %d maps to an output sequence of length "
                  "one that comprises the same glyph."))
            
            else:
                logger.warning((
                  'V0425',
                  (inGlyph,),
                  "Glyph %d maps to a single output glyph; this "
                  "might be better accomplished via a Single lookup."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Multiple(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Multiple substitution subtables for a GSUB table. These are dicts whose
    keys are glyph indices and whose values are GT objects.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz5:
      0: afii60002
      1: xyz9
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    xyz26:
      0: xyz16
      1: xyz17
      2: xyz18
    xyz27:
      0: xyz16
      1: xyz17
      2: xyz18
    xyz28:
      0: xyz41
      1: xyz31
    
    >>> print(sorted(_testingValues[2].gatheredOutputGlyphs()))
    [15, 16, 17, 30, 40]
    
    >>> logger = utilities.makeDoctestLogger("multiple_iv")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    multiple_iv - WARNING - Glyph 19 maps to an output sequence of length one that comprises the same glyph.
    multiple_iv.glyph 12 - WARNING - The output list is empty; the OpenType spec explicitly prohibits using a Multiple Lookup to remove glyphs.
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_subloggernamefunc = (lambda i: "glyph %d" % (i,)),
        item_usenamerforstr = True,
        map_maxcontextfunc = (lambda d: 1),
        map_validatefunc_partial = _validate)
    
    kind = ('GSUB', 2)
    kindString = "Multiple substitution table"
    
    #
    # Methods
    #
    
    def asAAT(self, **kwArgs):
        """
        Returns a list of AAT 'morx' subtable objects that have the same effect
        as this Multiple object.
        
        >>> GT = multiple_glyphtuple.Multiple_GlyphTuple
        >>> mObj = Multiple({
        ...   20: GT([20, 91, 92]),
        ...   30: GT([40, 41]),
        ...   31: GT([42, 43])})
        >>> v = mObj.asAAT()
        >>> len(v)
        3
        >>> v[0].pprint()
        30: 65534
        31: 65533
        Mask value: 00000001
        Coverage:
          Subtable kind: 4
    
        >>> v[1].pprint(onlySignificant=True)
        State 'Start of text':
          Class 'glyph 20':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 91
              1: 92
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 65533':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 43
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 65534':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 41
            Current insertion is kashida-like: True
            Name of next state: Start of text
        State 'Start of line':
          Class 'glyph 20':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 91
              1: 92
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 65533':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 43
            Current insertion is kashida-like: True
            Name of next state: Start of text
          Class 'glyph 65534':
            Insert glyphs before current: False
            Glyphs to insert at current:
              0: 41
            Current insertion is kashida-like: True
            Name of next state: Start of text
        Class table:
          20: glyph 20
          65533: glyph 65533
          65534: glyph 65534
        Mask value: (no data)
        Coverage: (no data)
    
        >>> v[2].pprint()
        65533: 42
        65534: 40
        Mask value: 00000001
        Coverage:
          Subtable kind: 4
        """
        
        if not self:
            return []
        
        from fontio3.morx import insertion, noncontextual
        
        _makeIns = insertion.Insertion.fromglyphdict
        _FakeSwash = noncontextual.Noncontextual_allowFakeGlyphs
        
        if all(k == v[0] for k, v in self.items()):
            dIns = {k: v[1:] for k, v in self.items()}
            return [_makeIns(dIns)]
    
        # If we get here there is at least one entry for which the replacement
        # sequence does NOT start with the key. In this case we need to make a
        # _FakeSwash map to create the trigger values, then build the insertion
        # subtable, and finally another _FakeSwash to do the final replacement
        # of the initial glyph.
        #
        # For example, suppose self maps 'a' to the new sequence 'bcd'. The
        # first _FakeSwash will change 'a' to a fake value 0xFFFE. Then the
        # insertion subtable adds 'cd' to this fake glyph. Finally, a second
        # _FakeSwash will change the 0xFFFE to 'b'.
    
        nextAvail = 0xFFFE
        dIns = {}
        dSwash1 = {}
        dSwash2 = {}
    
        for k, v in self.items():
            if k == v[0]:
                dIns[k] = v[1:]
        
            else:
                dSwash1[k] = nextAvail
                dIns[nextAvail] = v[1:]
                dSwash2[nextAvail] = v[0]
                nextAvail -= 1
    
        return [
          _FakeSwash(dSwash1),
          _makeIns(dIns),
          _FakeSwash(dSwash2)]
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Multiple object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0006 0000 0001  0000                |..........      |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0008 0001 000E  0001 0001 0004 0002 |................|
              10 | 0061 0008                                |.a..            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0001 000C 0003 0016  0016 001E 0001 0003 |................|
              10 | 0019 001A 001B 0003  000F 0010 0011 0002 |................|
              20 | 0028 001E                                |.(..            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # format
        covTable = coverage.Coverage.fromglyphset(self)
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        sortedKeys = sorted(self)
        w.add("H", len(self))
        pool = {}  # unique obj -> stake
        stakes = []
        
        for inGlyph in sortedKeys:
            obj = self[inGlyph]
            
            if obj in pool:
                stakes.append(pool[obj])
            
            else:
                stake = w.getNewStake()
                pool[obj] = stake
                stakes.append(stake)
        
        for stake in stakes:
            w.addUnresolvedOffset("H", stakeValue, stake)
        
        covTable.buildBinary(w, stakeValue=covStake, **kwArgs)
        kwArgs.pop('countFirst', None)
        
        for t in sorted((stake, obj) for obj, stake in pool.items()):
            t[1].buildBinary(w, stakeValue=t[0], countFirst=True, **kwArgs)
    
    def compacted(self, **kwArgs):
        """
        After doing canonical compacting we inspect records for cases where a
        glyph index maps to a tuple of one element equalling that same glyph
        index. These entries are removed; if the resulting Multiple object is
        empty, None is returned.
        """
        
        r = mapmeta.M_compacted(self, **kwArgs)
        
        if not r:
            return None
        
        toDel = set()
        
        for key, glyphTuple in r.items():
            if len(glyphTuple) == 1 and key == glyphTuple[0]:
                toDel.add(key)
        
        for key in toDel:
            del r[key]
        
        return (r or None)
    
    def effects(self, **kwArgs):
        raise DeprecationWarning(
          "The effects() method is deprecated; "
          "please use effectsSummary() instead.")
    
    def effectsSummary(self, **kwArgs):
        """
        Returns an EffectsSummary object. If present, notes will be made in a
        provided memo kwArgs to allow elision of reprocessing, which should
        eliminate the combinatoric explosion.
        
        >>> obj = _testingValues[2]
        >>> memo = {}
        >>> es = obj.effectsSummary(memo=memo)
        >>> es.pprint()
        25:
          15
          16
          17
        26:
          15
          16
          17
        27:
          30
          40
        >>> id(obj) in memo
        True
        """
        
        memo = kwArgs.pop('memo', {})
        
        if id(self) in memo:
            return memo[id(self)]
        
        r = EffectsSummary()
        
        for gIn, tOut in self.items():
            for gOut in tOut:
                r[gIn].add(gOut)
        
        memo[id(self)] = r
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new Multiple constructed from the specified FontWorkerSource,
        with source validation.
        
        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_fws.goto(1) # go back to start of file
        >>> m = Multiple.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> m.pprint()
        5:
          0: 2
          1: 3
        7:
          0: 2
          1: 2
          2: 3
        >>> l = Multiple.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        FW_test.multiple - WARNING - line 3 -- multiple substitution deletes input glyph by converting input glyphs to empty output. This is expressly prohibited by the OpenType specification.
        FW_test.multiple - WARNING - line 3 -- glyph 'A' not found
        FW_test.multiple - WARNING - line 5 -- glyph 'B' not found
        FW_test.multiple - WARNING - line 5 -- glyph 'C' not found
        FW_test.multiple - ERROR - line 0 -- did not find matching 'subtable end/lookup end'
        >>> l.pprint()
        5:
          0: 2
          1: 3
        7:
          0: 2
          1: 2
          2: 3
        """
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("multiple")

        namer = kwArgs['namer']
        terminalStrings = ('subtable end', 'lookup end')
        startingLineNumber=fws.lineNumber
        r = cls()
        for line in fws:
            if line.lower() in terminalStrings:
                return r
            if len(line) > 0:
                tokens = [x.strip() for x in line.split('\t')]
                if len(tokens) < 2:
                    # warn, but proceed anyway...
                    logger.warning((
                      'V0957',
                      (fws.lineNumber,), 
                      "line %d -- multiple substitution deletes input glyph "
                      "by converting input glyphs to empty output. This is "
                      "expressly prohibited by the OpenType specification."))

                glyphsOK=True
                glyphIndices = [namer.glyphIndexFromString(t) for t in tokens]
                for i in range(len(tokens)):
                    if glyphIndices[i] is None:
                        logger.warning(('V0956', (fws.lineNumber, tokens[i]),
                            "line %d -- glyph '%s' not found"))
                        glyphsOK=False

                if glyphsOK:
                    key = glyphIndices[0]
                    if key in r:
                        logger.warning((
                          'V0963',
                          (fws.lineNumber, tokens[0]),
                          "line %d -- ignoring duplicated entry for '%s'"))
                    else:
                        value = multiple_glyphtuple.Multiple_GlyphTuple(
                            glyphIndices[1:])
                        r[key] = value

        logger.error((
            'V0958',
            (startingLineNumber, "/".join(terminalStrings)),
            'line %d -- did not find matching \'%s\''))

        return r


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Multiple object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("multiple_test")
        >>> s = _testingValues[2].binaryString()
        >>> fvb = Multiple.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        multiple_test.multiple - DEBUG - Walker has 36 remaining bytes.
        multiple_test.multiple.coverage - DEBUG - Walker has 24 remaining bytes.
        multiple_test.multiple.coverage - DEBUG - Format is 1, count is 3
        multiple_test.multiple.coverage - DEBUG - Raw data are [25, 26, 27]
        multiple_test.multiple.glyph 25.glyphtuple - DEBUG - Walker has 14 bytes remaining.
        multiple_test.multiple.glyph 25.glyphtuple - DEBUG - Count is 3
        multiple_test.multiple.glyph 25.glyphtuple - DEBUG - Data are (15, 16, 17)
        multiple_test.multiple.glyph 27.glyphtuple - DEBUG - Walker has 6 bytes remaining.
        multiple_test.multiple.glyph 27.glyphtuple - DEBUG - Count is 2
        multiple_test.multiple.glyph 27.glyphtuple - DEBUG - Data are (40, 30)
        
        >>> fvb(s[:5], logger=logger)
        multiple_test.multiple - DEBUG - Walker has 5 remaining bytes.
        multiple_test.multiple - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("multiple")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format, covOffset, count = w.unpack("3H")
        r = cls()
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1 but got format %d instead."))
            
            return None
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        if not count:
            logger.warning(('V0442', (), "The SequenceCount is zero."))
            return r
        
        if count != len(covTable):
            logger.error((
              'V0422',
              (count, len(covTable)),
              "The SequenceCount (%d) does not match the length "
              "of the Coverage (%d)."))
            
            return None
        
        if w.length() < 2 * count:
            logger.error((
              'V0423',
              (),
              "The Sequence offsets are missing or incomplete."))
            
            return None
        
        it = zip(sorted(covTable), w.group("H", count))
        pool = {}
        kwArgs.pop('countFirst', None)
        
        for inGlyph, offset in it:
            if offset not in pool:
                obj = GT.fromvalidatedwalker(
                  w.subWalker(offset),
                  countFirst = True,
                  logger = logger.getChild("glyph %d" % (inGlyph,)),
                  **kwArgs)
                
                if obj is None:
                    return None
                
                pool[offset] = obj
            
            r[inGlyph] = pool[offset]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Multiple object from the specified walker.
        
        >>> for i in range(3):
        ...   obj = _testingValues[i]
        ...   print(obj == Multiple.frombytes(obj.binaryString()))
        True
        True
        True
        """
        
        format, covOffset, count = w.unpack("3H")
        
        if format != 1:
            raise ValueError(
              "Unknown format for Multiple subtable: %s" % (format,))
        
        covTable = coverage.Coverage.fromwalker(w.subWalker(covOffset))
        
        if count != len(covTable):
            raise ValueError("Count mismatch in Multiple subtable!")
        
        it = zip(sorted(covTable), w.group("H", count))
        r = cls()
        pool = {}
        
        for inGlyph, offset in it:
            if offset not in pool:
                pool[offset] = GT.fromwalker(
                  w.subWalker(offset),
                  countFirst=True)
            
            r[inGlyph] = pool[offset]
        
        return r
    
    def run(glyphArray, **kwArgs):
        raise DeprecationWarning(
          "The run() method is deprecated; "
          "please use runOne() instead.")
    
    def runOne(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing for a single glyph in a glyph array. This method is
        called by the Lookup object's run() method (and possibly by actions
        within contextual or related subtables).
        
        This method returns a pair: the new output GlyphList, and a count of
        the number of glyph indices involved (or zero, if no action happened).
        
        Note that the igsFunc is not used in this method.
        
        >>> gt = multiple_glyphtuple.Multiple_GlyphTuple([37, 35, 50])
        >>> obj = Multiple({5: gt})
        >>> ga = runningglyphs.GlyphList.fromiterable([3, 4, 5, 6, 7])
        >>> ga.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 4
          originalOffset: 1
        2:
          Value: 5
          originalOffset: 2
        3:
          Value: 6
          originalOffset: 3
        4:
          Value: 7
          originalOffset: 4
        
        >>> r, count = obj.runOne(ga, 0)
        >>> count
        0
        
        When no match is found, the same (input) glyphArray is returned:
        
        >>> r is ga
        True
        
        >>> r, count = obj.runOne(ga, 2)
        >>> count
        3
        >>> r.pprint()
        0:
          Value: 3
          originalOffset: 0
        1:
          Value: 4
          originalOffset: 1
        2:
          Value: 37
          originalOffset: 2
        3:
          Value: 35
          originalOffset: 2
        4:
          Value: 50
          originalOffset: 2
        5:
          Value: 6
          originalOffset: 3
        6:
          Value: 7
          originalOffset: 4
        """
        
        inGlyph = glyphArray[startIndex]
        
        if inGlyph not in self:
            return (glyphArray, 0)
        
        r = glyphArray.fromiterable(glyphArray)  # preserves offsets
        sub = self[inGlyph]
        G = runningglyphs.Glyph
        
        v = [
          G(
            n,
            originalOffset = inGlyph.originalOffset,
            shaperClass = inGlyph.shaperClass)
          for n in sub]
        
        r[startIndex:startIndex+1] = v
        return (r, len(v))

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Writes contents of lookup to provided stream 's'. Uses
        namer.bestNameForGlyphIndex if a namer is provided, otherwise
        uses Font Worker glyph index labeling ("# <id>").
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex

        for inGlyph, outTuple in sorted(self.items()):
            outTupleStr = "\t".join([bnfgi(g) for g in outTuple])
            s.write("%s\t%s\n" % (bnfgi(inGlyph), outTupleStr))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    gttv = multiple_glyphtuple._testingValues
    
    _testingValues = (
        Multiple(),
        Multiple({4: gttv[0]}),
        Multiple({25: gttv[1], 26: gttv[1], 27: gttv[2]}),
        # bad entries start here
        Multiple({12: gttv[3], 19: gttv[5]}))
    
    del gttv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'f': 2,
        'i': 3,
        'fi': 5,
        'ffi': 7
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        fi	f	i
        ffi	f	f	i
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        fi	f	i
        A
        ffi	f	f	i
        B	C
        """))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
