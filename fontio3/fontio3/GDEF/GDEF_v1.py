#
# GDEF_v1.py -- Top-level support for GDEF tables (OpenType 1.6)
#
# Copyright © 2005-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType 1.6 GDEF tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.GDEF import attachlist, glyphclass, ligcaret, markclass, markset
from fontio3.opentype import version as otversion

# -----------------------------------------------------------------------------

#
# Constants
#

_makers = (
  glyphclass.GlyphClassTable,
  attachlist.AttachListTable,
  ligcaret.LigCaretTable,
  markclass.MarkClassTable,
  markset.MarkSetTable)

# -----------------------------------------------------------------------------

#
# Classes
#

class GDEF(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire GDEF tables. These are simple objects with the
    following attribute values:
        version         A Version object.
    
        attachments     An attachlist.AttachListTable object, or None.
        
        glyphClasses    A glyphclass.GlyphClassTable object, or None.
        
        ligCarets       A ligcaret.LigCaretTable object, or None.
        
        markClasses     A markclass.MarkClassTable object, or None.
        
        markSets        A markset.MarkSetTable object, or None.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Version:
      Major version: 1
      Minor version: 2
    Glyph Classes:
      Base glyph: xyz8
      Ligature glyph: xyz5 - xyz7, xyz11 - xyz12, xyz16
    Attachment Points:
      afii60003: [1, 4]
      xyz46: [3, 19, 20]
      xyz51: [1, 4]
    Ligature Caret Points:
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
    Mark Classes:
      Mark class 1: xyz8
      Mark class 2: xyz5 - xyz7, xyz11 - xyz12, xyz16
    Mark Sets:
      Mark Glyph Set 0: xyz16, xyz23 - xyz24, xyz31
      Mark Glyph Set 1: xyz13, U+0163
      Mark Glyph Set 2: xyz16, xyz23 - xyz24, xyz31
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        version = dict(
            attr_followsprotocol = True,
            attr_initfunc = lambda: otversion.Version(minor=2),
            attr_label = "Version"),
            
        glyphClasses = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphclass.GlyphClassTable,
            attr_label = "Glyph Classes",
            attr_showonlyiftrue = True),
        
        attachments = dict(
            attr_followsprotocol = True,
            attr_initfunc = attachlist.AttachListTable,
            attr_label = "Attachment Points",
            attr_showonlyiftrue = True),
        
        ligCarets = dict(
            attr_followsprotocol = True,
            attr_initfunc = ligcaret.LigCaretTable,
            attr_label = "Ligature Caret Points",
            attr_showonlyiftrue = True),
        
        markClasses = dict(
            attr_followsprotocol = True,
            attr_initfunc = markclass.MarkClassTable,
            attr_label = "Mark Classes",
            attr_showonlyiftrue = True),
        
        markSets = dict(
            attr_followsprotocol = True,
            attr_initfunc = markset.MarkSetTable,
            attr_label = "Mark Sets",
            attr_showonlyiftrue = True))
    
    attrSorted = (
      'version',
      'glyphClasses',
      'attachments',
      'ligCarets',
      'markClasses',
      'markSets')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002 000E 002A  004C 0078 0094 0002 |.......*.L.x....|
              10 | 0004 0004 0006 0002  0007 0007 0001 000A |................|
              20 | 000B 0002 000F 000F  0002 000A 0003 0014 |................|
              30 | 001C 001C 0001 0003  002D 0032 0062 0003 |.........-.2.b..|
              40 | 0003 0013 0014 0002  0001 0004 0008 0002 |................|
              50 | 0010 0014 0001 0002  0047 0062 0001 0008 |.........G.b....|
              60 | 0001 0008 0001 01F4  0003 01F4 0006 000C |................|
              70 | 0011 0002 EF00 1200  0002 0004 0004 0006 |................|
              80 | 0002 0007 0007 0001  000A 000B 0002 000F |................|
              90 | 000F 0002 0001 0003  0000 0010 0000 001C |................|
              A0 | 0000 0010 0001 0004  000F 0016 0017 001E |................|
              B0 | 0001 0002 000C 0063                      |.......c        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Add content and unresolved references
        w.add("L", 0x10002)
        d = self.__dict__
        toBeWritten = []
        
        san = list(self.getSortedAttrNames())
        san.remove('version')
        for key in san:
            table = d[key]
            
            if table:
                tableStake = w.getNewStake()
                toBeWritten.append((table, tableStake))
                w.addUnresolvedOffset("H", stakeValue, tableStake)
            
            else:
                w.add("H", 0)
        
        # Resolve the references
        for table, tableStake in toBeWritten:
            table.buildBinary(w, stakeValue=tableStake, **kwArgs)
    
    @classmethod
    def frommtxxtables(cls, editor, **kwArgs):
        """
        Returns a GDEF object initialized via the MTxx (and other) tables in
        the specified editor.
        """
        
        if editor is None:
            return cls()
        
        hm = editor.get(b'hmtx')
        
        if not hm:
            return cls()
        
        sf = editor.get(b'MTsf', {})
        # when there's a MTxx table for marksets, add that here
        
        glyphClasses = glyphclass.GlyphClassTable()
        attachments = attachlist.AttachListTable()
        ligCarets = ligcaret.LigCaretTable()
        markClasses = markclass.MarkClassTable()
        markSets = markset.MarkSetTable()
        excluded = frozenset([0xFFFF, 0xFFFE])
        
        for glyphIndex, mtapRecord in editor.get(b'MTap', {}).items():
            # glyph class
            glyphClass = mtapRecord.glyphClass
            
            if glyphClass:
                glyphClasses[glyphIndex] = glyphClass
            
            # attachments
            anchor = mtapRecord.anchorData
            
            t1 = (
              () if anchor is None
              else tuple(anchor.pointGenerator(excludeFFFx=True)))
            
            conn = mtapRecord.connectionData

            if conn is None:
                t2 = ()
            
            else:
                it = conn.pointGenerator()
                
                t2 = tuple(
                  c.pointIndex
                  for c in it
                  if c.pointIndex not in excluded)
            
            if t1 or t2:
                attachments[glyphIndex] = attachlist.AttachPointTable(t1 + t2)
            
            # lig carets
            if glyphClass == 2: # ligature
                caretValues = mtapRecord.caretValuesFromMetrics(
                  hm[glyphIndex][0])
                
                if caretValues:
                    ligCarets[glyphIndex] = ligcaret.LigGlyphTable(caretValues)
            
            # marks
            elif glyphClass == 3 and sf: # mark
                markClass = sf[glyphIndex].originalClassIndex
                
                markClasses[glyphIndex] = (
                  0 if markClass == 0xFFFF
                  else markClass + 1)
        
        return cls(
          attachments = attachments,
          glyphClasses = glyphClasses,
          ligCarets = ligCarets,
          markClasses = markClasses,
          markSets = markSets)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new GDEF from the specified FontWorker Source
        code with extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword argument).

        >>> _test_FW_fws.goto(1) # go back to first line
        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> gdef = GDEF.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger, editor=None)
        >>> gdef.pprint()
        Version:
          Major version: 1
          Minor version: 2
        Glyph Classes:
          Base glyph: 5
          Ligature glyph: 7
          Mark glyph: 11
        Attachment Points:
          5: [23]
          7: [29, 31]
          11: [37, 41, 43]
        Ligature Caret Points:
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
        Mark Classes:
          Mark class 8: 5
          Mark class 10: 7
          Mark class 12: 11
        Mark Sets:
          Mark Glyph Set 0: 5, 7
          Mark Glyph Set 1: 5
          Mark Glyph Set 2: 11
        >>> gdef2 = GDEF.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger, editor=None)
        test_FW.GDEF.classDef - WARNING - line 8 -- glyph 'w' not found
        test_FW.GDEF.attachlist - WARNING - line 13 -- missing attachment points
        test_FW.GDEF.attachlist - WARNING - line 16 -- glyph 'x' not found
        test_FW.GDEF.ligcaret - ERROR - line 21 -- mismatch between caret count (2);and number of carets actually listed (3); discarding.
        test_FW.GDEF.ligcaret - ERROR - line 23 -- mismatch between caret count (3);and number of carets actually listed (2); discarding.
        test_FW.GDEF.ligcaret - WARNING - line 24 -- glyph 'y' not found
        test_FW.GDEF.classDef - WARNING - line 31 -- incorrect number of tokens, expected 2, found 1
        test_FW.GDEF.classDef - WARNING - line 32 -- glyph 'z' not found
        test_FW.GDEF.markset - WARNING - line 40 -- glyph 'asdfjkl' not found
        test_FW.GDEF.markset - WARNING - MarkFilterSet 1 will be renumbered to 0
        test_FW.GDEF.markset - WARNING - MarkFilterSet 99 will be renumbered to 1
        >>> gdef2.pprint()
        Version:
          Major version: 1
          Minor version: 2
        Glyph Classes:
          Base glyph: 5
          Ligature glyph: 7
          Mark glyph: 11
        Attachment Points:
          5: [23]
          11: [37, 41, 43]
        Ligature Caret Points:
          5:
            CaretValue #1:
              Simple caret value in FUnits: 42
        Mark Classes:
          Mark class 1: 5
          Mark class 2: 7
        Mark Sets:
          Mark Glyph Set 0: 5, 11
          Mark Glyph Set 1: 5, 7
        """

        editor = kwArgs['editor']
        namer = kwArgs['namer']

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('GDEF')
        else:
            logger = logger.getChild('GDEF')

        # create empty versions of these tables for now,
        # replace them with full versions later if the data is available
        glyphClasses = glyphclass.GlyphClassTable()
        attachments = attachlist.AttachListTable()
        ligCarets = ligcaret.LigCaretTable()
        markClasses = markclass.MarkClassTable()
        markSets = markset.MarkSetTable()

        firstLine = 'FontDame GDEF table'
        line = next(fws)
        if line != firstLine:
            logger.error((
              'V0958',
              (firstLine,),
              "Expected '%s' in first line."))
            return None

        for line in fws:
            if len(line) != 0:
                if line.lower() == 'class definition begin':
                    glyphClasses = \
                        glyphclass.GlyphClassTable.fromValidatedFontWorkerSource(
                        fws, namer=namer, logger=logger)
                elif line.lower() == 'attachment list begin':
                    attachments = \
                        attachlist.AttachListTable.fromValidatedFontWorkerSource(
                        fws, namer=namer, logger=logger)
                elif line.lower() == 'carets begin':
                    ligCarets = \
                        ligcaret.LigCaretTable.fromValidatedFontWorkerSource(
                            fws, namer=namer, logger=logger, editor=editor)
                elif line.lower() == 'mark attachment class definition begin':
                    markClasses = \
                        markclass.MarkClassTable.fromValidatedFontWorkerSource(
                            fws, namer=namer, logger=logger)
                elif line.lower() == 'markfilter set definition begin':
                    markSets = \
                        markset.MarkSetTable.fromValidatedFontWorkerSource(
                            fws, namer=namer, logger=logger)
                else:
                    logger.warning(('V0960',
                        (fws.lineNumber, line),
                        'line %d -- unexpected token: \'%s\''))

        return cls(
            attachments = attachments,
            glyphClasses = glyphClasses,
            ligCarets = ligCarets,
            markClasses = markClasses,
            markSets = markSets)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new GDEF. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = GDEF.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.GDEF - DEBUG - Walker has 184 remaining bytes.
        test.GDEF.version - DEBUG - Walker has 184 remaining bytes.
        test.GDEF.glyphclass.classDef - DEBUG - Walker has 170 remaining bytes.
        test.GDEF.glyphclass.classDef - DEBUG - ClassDef is format 2.
        test.GDEF.glyphclass.classDef - DEBUG - Count is 4
        test.GDEF.glyphclass.classDef - DEBUG - Raw data are [(4, 6, 2), (7, 7, 1), (10, 11, 2), (15, 15, 2)]
        test.GDEF.attachlist - DEBUG - Walker has 142 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Walker has 132 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Format is 1, count is 3
        test.GDEF.attachlist.coverage - DEBUG - Raw data are [45, 50, 98]
        test.GDEF.attachlist - INFO - Number of groups: 3.
        test.GDEF.ligcaret - DEBUG - Walker has 108 remaining bytes.
        test.GDEF.ligcaret.coverage - DEBUG - Walker has 100 remaining bytes.
        test.GDEF.ligcaret.coverage - DEBUG - Format is 1, count is 2
        test.GDEF.ligcaret.coverage - DEBUG - Raw data are [71, 98]
        test.GDEF.ligcaret - INFO - Number of LigGlyphTables: 2.
        test.GDEF.ligcaret.[0].ligglyph - DEBUG - Walker has 92 remaining bytes.
        test.GDEF.ligcaret.[0].ligglyph - INFO - Number of splits: 1.
        test.GDEF.ligcaret.[0].ligglyph.[0].caretvalue.coordinate - DEBUG - Walker has 84 remaining bytes.
        test.GDEF.ligcaret.[1].ligglyph - DEBUG - Walker has 88 remaining bytes.
        test.GDEF.ligcaret.[1].ligglyph - INFO - Number of splits: 1.
        test.GDEF.ligcaret.[1].ligglyph.[0].caretvalue.device - DEBUG - Walker has 80 remaining bytes.
        test.GDEF.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - Walker has 74 remaining bytes.
        test.GDEF.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - StartSize=12, endSize=17, format=2
        test.GDEF.ligcaret.[1].ligglyph.[0].caretvalue.device.device - DEBUG - Data are (61184, 4608)
        test.GDEF.markclass.classDef - DEBUG - Walker has 64 remaining bytes.
        test.GDEF.markclass.classDef - DEBUG - ClassDef is format 2.
        test.GDEF.markclass.classDef - DEBUG - Count is 4
        test.GDEF.markclass.classDef - DEBUG - Raw data are [(4, 6, 2), (7, 7, 1), (10, 11, 2), (15, 15, 2)]
        test.GDEF.markset - DEBUG - Walker has 36 remaining bytes.
        test.GDEF.markset - INFO - MarkSet has 3 element(s).
        test.GDEF.markset.[0].coverage - DEBUG - Walker has 20 remaining bytes.
        test.GDEF.markset.[0].coverage - DEBUG - Format is 1, count is 4
        test.GDEF.markset.[0].coverage - DEBUG - Raw data are [15, 22, 23, 30]
        test.GDEF.markset.[1].coverage - DEBUG - Walker has 8 remaining bytes.
        test.GDEF.markset.[1].coverage - DEBUG - Format is 1, count is 2
        test.GDEF.markset.[1].coverage - DEBUG - Raw data are [12, 99]
        test.GDEF.markset.[2].coverage - DEBUG - Walker has 20 remaining bytes.
        test.GDEF.markset.[2].coverage - DEBUG - Format is 1, count is 4
        test.GDEF.markset.[2].coverage - DEBUG - Raw data are [15, 22, 23, 30]
        
        >>> fvb(s[:1], logger=logger)
        test.GDEF - DEBUG - Walker has 1 remaining bytes.
        test.GDEF - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('GDEF')
        else:
            logger = logger.getChild('GDEF')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = otversion.Version.fromvalidatedwalker(w, logger=logger, **kwArgs)

        if version.major != 1 or version.minor != 2:
            logger.error((
              'V0113',
              (version,),
              "Expected version 1.2, got %s."))
            
            return None
        
        if w.length() < 10:
            logger.error(('V0114', (), "Insufficient bytes for offsets."))
            return None
        
        r = cls(version=version)

        stoffsets = w.group("H", 5)

        san = list(r.getSortedAttrNames())
        loggers = [logger] * 5
        loggers[0] = logger.getChild("glyphclass")
        loggers[3] = logger.getChild("markclass")
        for sti, sto in enumerate(stoffsets):
            if sto:
                fw = _makers[sti].fromvalidatedwalker
                wSub = w.subWalker(sto)
                st = fw(wSub, logger=loggers[sti], **kwArgs)
                r.__dict__[san[sti+1]] = st
            else:
                r.__dict__[san[sti+1]] = _makers[sti]()
                
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GDEF object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == GDEF.frombytes(obj.binaryString())
        True
        """

        version = otversion.Version.fromwalker(w, **kwArgs)
        
        if version.major != 1 or version.minor != 2:
            raise ValueError("Unsupported GDEF %s" % (version,))
        
        r = cls(version=version)

        stoffsets = w.group("H", 5)

        san = list(r.getSortedAttrNames())
        for sti, sto in enumerate(stoffsets):
            if sto:
                fw = _makers[sti].fromwalker
                wSub = w.subWalker(sto)
                st = fw(wSub, **kwArgs)
                r.__dict__[san[sti+1]] = st
            else:
                r.__dict__[san[sti+1]] = _makers[sti]()
                
        return r


    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write the GDEF table to stream 's' in Font Worker dump format.
        kwArg 'namer' is required.
        """
        namer = kwArgs.get('namer')
        bnfgi = namer.bestNameForGlyphIndex
            
        s.write("FontDame GDEF table\n\n")

        if self.glyphClasses:
            s.write("class definition begin\n")
            for gi in sorted(
              self.glyphClasses,
              key=lambda x:(self.glyphClasses[x], x)):
                gc = self.glyphClasses[gi]
                s.write("%s\t%d\n" % (bnfgi(gi), gc))
            s.write("class definition end\n\n")

        if self.attachments:
            s.write("attachment list begin\n")
            for gi,atl in sorted(self.attachments.items()):
                s.write("%s\t%s\n" % (bnfgi(gi), "\t".join([str(at) for at in atl])))
            s.write("attachment list end\n\n")
            
        if self.ligCarets:
            s.write("carets begin\n")
            for gi,lc in sorted(self.ligCarets.items()):
                s.write("%s\t%d\t%s\n" % (
                  bnfgi(gi),
                  len(lc),
                  "\t".join([str(c) for c in lc])))
            s.write("carets end\n\n")
            
        if self.markClasses:
            s.write("mark attachment class definition begin\n")
            for gi in sorted(
              self.markClasses,
              key=lambda x:(self.markClasses[x], x)):
                mc = self.markClasses[gi]
                s.write("%s\t%d\n" % (bnfgi(gi), mc))
            s.write("class definition end\n\n")
            
        if self.markSets:
            s.write("markfilter set definition begin\n")
            for gsi, gs in enumerate(self.markSets):
                for gi in sorted(gs):
                    s.write("%s\t%d\n" % (bnfgi(gi), gsi))
            s.write("set definition end\n\n")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    from io import StringIO
    from fontio3.opentype.fontworkersource import FontWorkerSource

    _testingValues = (
        GDEF(),
        
        GDEF(
          version = otversion.Version(minor=2),
          glyphClasses = glyphclass._testingValues[1],
          attachments = attachlist._testingValues[1],
          ligCarets = ligcaret._testingValues[1],
          markClasses = markclass._testingValues[1],
          markSets = markset._testingValues[1]))

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'a': 5,
        'b': 7,
        'c': 11
    }
    _test_FW_namer._initialized = True

    _test_FW_fws = FontWorkerSource(StringIO(
        """FontDame GDEF table

        class definition begin
        a\t1

        b\t2
        c\t3
        class definition end

        Attachment list begin
        a\t23
        b\t29\t31

        c\t37\t41\t43
        Attachment list end

        carets begin
        a\t1\t42
        b\t2\t50\t55
        c\t3\t12\t17\t37

        carets end

        mark attachment class definition begin

        a\t8
        b\t10
        c\t12
        class definition end
        
        markfilter set definition begin
        a\t0
        b\t0
        a\t1
        c\t2
        c\t2
        set definition end
        """
    ))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """FontDame GDEF table

        class definition begin
        a\t1

        b\t2
        c\t3
        w\t3
        class definition end

        Attachment list begin
        a\t23
        b

        c\t37\t41\t43
        x\t42
        Attachment list end

        carets begin
        a\t1\t42
        b\t2\t50\t55\t69

        c\t3\t12\t37
        y\t1\t43
        carets end

        mark attachment class definition begin

        a\t1
        b\t2
        c
        z\t4
        class definition end
        
        markfilter set definition begin
        a\t99
        b\t99
        a\t1
        c\t1
        asdfjkl\t34
        set definition end
        """
    ))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
