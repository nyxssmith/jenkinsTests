#
# GDEF_v13.py -- Top-level support for GDEF tables (version 1.3/OpenType 1.8)
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType 1.8/version 1.3 GDEF tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.GDEF import attachlist, glyphclass, ligcaret, markclass, markset
from fontio3.opentype import living_variations
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

    <<< _testingValues[1].pprint(namer=namer.testingNamer())
    Version:
      Major version: 1
      Minor version: 3
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
        version=dict(
            attr_followsprotocol=True,
            attr_initfunc=lambda: otversion.Version(minor=3),
            attr_label="Version"),

        glyphClasses=dict(
            attr_followsprotocol=True,
            attr_initfunc=glyphclass.GlyphClassTable,
            attr_label="Glyph Classes",
            attr_showonlyiftrue=True),

        attachments=dict(
            attr_followsprotocol=True,
            attr_initfunc=attachlist.AttachListTable,
            attr_label="Attachment Points",
            attr_showonlyiftrue=True),

        ligCarets=dict(
            attr_followsprotocol=True,
            attr_initfunc=ligcaret.LigCaretTable,
            attr_label="Ligature Caret Points",
            attr_showonlyiftrue=True),

        markClasses=dict(
            attr_followsprotocol=True,
            attr_initfunc=markclass.MarkClassTable,
            attr_label="Mark Classes",
            attr_showonlyiftrue=True),

        markSets=dict(
            attr_followsprotocol=True,
            attr_initfunc=markset.MarkSetTable,
            attr_label="Mark Sets",
            attr_showonlyiftrue=True))

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

        A single kwArg is recognized:

            'otIVS'    if present, should be a tuple of (ivsBinaryString,
                       LivingDelta-to-DeltaSetIndexMap). The ivsBinaryString
                       will be written here. The map is used to write various
                       structures that reference the deltas.

        <<< utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0003 0012 002E  0050 007C 0098 0000 |.........P.|....|
              10 | 0000 0002 0004 0004  0006 0002 0007 0007 |................|
              20 | 0001 000A 000B 0002  000F 000F 0002 000A |................|
              30 | 0003 0014 001C 001C  0001 0003 002D 0032 |.............-.2|
              40 | 0062 0003 0003 0013  0014 0002 0001 0004 |.b..............|
              50 | 0008 0002 0010 0014  0001 0002 0047 0062 |.............G.b|
              60 | 0001 0008 0001 0008  0001 01F4 0003 01F4 |................|
              70 | 0006 000C 0011 0002  EF00 1200 0002 0004 |................|
              80 | 0004 0006 0002 0007  0007 0001 000A 000B |................|
              90 | 0002 000F 000F 0002  0001 0003 0000 0010 |................|
              A0 | 0000 001C 0000 0010  0001 0004 000F 0016 |................|
              B0 | 0017 001E 0001 0002  000C 0063           |...........c    |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        editor = kwArgs.get('editor')
        if editor is not None:
            if editor.reallyHas(b'fvar'):
                ao = editor.fvar.axisOrder

            gdce = getattr(self, '_creationExtras', {})
            otcd = gdce.get('otcommondeltas')
            if otcd:
                bsfd = living_variations.IVS.binaryStringFromDeltas
                ivsBs, LDtoDSMap = bsfd(otcd, axisOrder=ao)

        # Add content and unresolved references
        w.add("L", 0x10003)
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

        if ivsBs:
            ivsStake = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, ivsStake)
        else:
            w.add("L", 0)

        # Resolve subtable references
        for table, tableStake in toBeWritten:
            table.buildBinary(w, stakeValue=tableStake, **kwArgs)

        if ivsBs:
            w.stakeCurrentWithValue(ivsStake)
            w.addString(ivsBs)

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
            if glyphClass == 2:  # ligature
                caretValues = mtapRecord.caretValuesFromMetrics(
                  hm[glyphIndex][0])

                if caretValues:
                    ligCarets[glyphIndex] = ligcaret.LigGlyphTable(caretValues)

            # marks
            elif glyphClass == 3 and sf:  # mark
                markClass = sf[glyphIndex].originalClassIndex

                markClasses[glyphIndex] = (
                  0 if markClass == 0xFFFF
                  else markClass + 1)

        return cls(
          attachments=attachments,
          glyphClasses=glyphClasses,
          ligCarets=ligCarets,
          markClasses=markClasses,
          markSets=markSets)

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new GDEF from the specified FontWorker Source
        code with extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).

        >>> _test_FW_fws.goto(1) # go back to first line
        >>> logger = utilities.makeDoctestLogger('test_FW')
        >>> fvfws = GDEF.fromValidatedFontWorkerSource
        >>> gdef = fvfws(_test_FW_fws, namer=_test_FW_namer,
        ...   logger=logger, editor=None)
        >>> gdef.pprint()
        Version:
          Major version: 1
          Minor version: 3
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
        >>> gdef2 = fvfws(_test_FW_fws2, namer=_test_FW_namer,
        ...   logger=logger, editor=None)
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
          Minor version: 3
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
                    logger.warning((
                      'V0960',
                      (fws.lineNumber, line),
                      'line %d -- unexpected token: \'%s\''))

        return cls(
            attachments=attachments,
            glyphClasses=glyphClasses,
            ligCarets=ligCarets,
            markClasses=markClasses,
            markSets=markSets)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new GDEF. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        >>> ed = utilities.fakeEditor(5)
        >>> from fontio3.fvar import fvar, axial_coordinate, axis_info
        >>> acmin = axial_coordinate.AxialCoordinate(300)
        >>> acdef = axial_coordinate.AxialCoordinate(400)
        >>> acmax = axial_coordinate.AxialCoordinate(700)
        >>> wght_ax_info = axis_info.AxisInfo(
        ...   minValue=acmin, defaultValue=acdef, maxValue=acmax)
        >>> ed.fvar = fvar.Fvar({'wght': wght_ax_info}, axisOrder=('wght',))
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("00010003"  # version
        ...      "0012"      # GlyphClassDef offset
        ...      "001A"      # AttachList offset
        ...      "002A"      # LigCaretList offset
        ...      "0046"      # MarkAttachClassDef offset
        ...      "0050"      # MarkGlyphSetsDef offset
        ...      "0000005E"  # ItemVarStore offset
        ...      "0001 0001 0001 0003"  # GlyphClassDef data
        ...      "0006 0001 000C  0001 0001 0004  0001 0005" # AttachList data
        ...      "0006 0001 000C  0001 0001 0003"  # LigCaret partial data
        ...      "0001 0004  0003 0048 0006  0000 0000 8000"  # LigCaret data
        ...      "0002 0001 0000 0004 0003"  # MarkAttachClassDef data
        ...      "0001 0001 00000008  0001 0001 0002"  # MarkGlyphSetsDef
        ...      "0001 0000000C 0001 0000001C"  # IVS data
        ...      "0001 0001 E000 1000 4000 C000 0000 4000"  # IVS data
        ...      "0001 0001 0001 0000 FF4C"  # IVS data
        ...      )
        >>> b = utilities.fromhex(s)
        >>> fvb = GDEF.fromvalidatedbytes
        >>> obj = fvb(b, logger=logger, editor=ed)
        test.GDEF - DEBUG - Walker has 132 remaining bytes.
        test.GDEF.version - DEBUG - Walker has 132 remaining bytes.
        test.GDEF.IVS - DEBUG - Walker has 38 remaining bytes.
        test.GDEF.IVS - INFO - Format 1
        test.GDEF.IVS - DEBUG - Data count is 1
        test.GDEF.IVS - DEBUG - Axis count is 1
        test.GDEF.IVS - DEBUG - Region count is 1
        test.GDEF.IVS - DEBUG - Delta (0, 0)
        test.GDEF.glyphclass.classDef - DEBUG - Walker has 114 remaining bytes.
        test.GDEF.glyphclass.classDef - DEBUG - ClassDef is format 1.
        test.GDEF.glyphclass.classDef - DEBUG - First is 1, and count is 1
        test.GDEF.glyphclass.classDef - DEBUG - Raw data are (3,)
        test.GDEF.attachlist - DEBUG - Walker has 106 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Walker has 100 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Format is 1, count is 1
        test.GDEF.attachlist.coverage - DEBUG - Raw data are [4]
        test.GDEF.attachlist - INFO - Number of groups: 1.
        test.GDEF.ligcaret - DEBUG - Walker has 90 remaining bytes.
        test.GDEF.ligcaret.coverage - DEBUG - Walker has 84 remaining bytes.
        test.GDEF.ligcaret.coverage - DEBUG - Format is 1, count is 1
        test.GDEF.ligcaret.coverage - DEBUG - Raw data are [3]
        test.GDEF.ligcaret - INFO - Number of LigGlyphTables: 1.
        test.GDEF.ligcaret.[0].ligglyph - DEBUG - Walker has 78 remaining bytes.
        test.GDEF.ligcaret.[0].ligglyph - INFO - Number of splits: 1.
        test.GDEF.ligcaret.[0].ligglyph.[0].caretvalue.variation - DEBUG - Walker has 74 remaining bytes.
        test.GDEF.ligcaret.[0].ligglyph.[0].caretvalue.variation.device - DEBUG - Walker has 68 remaining bytes.
        test.GDEF.ligcaret.[0].ligglyph.[0].caretvalue.variation.device - DEBUG - VariationIndex (0, 0)
        test.GDEF.ligcaret.[0].ligglyph.[0].caretvalue.variation - DEBUG - LivingDeltas ('wght': (start -0.5, peak 0.25, end 1.0), -180)
        test.GDEF.markclass.classDef - DEBUG - Walker has 62 remaining bytes.
        test.GDEF.markclass.classDef - DEBUG - ClassDef is format 2.
        test.GDEF.markclass.classDef - DEBUG - Count is 1
        test.GDEF.markclass.classDef - DEBUG - Raw data are [(0, 4, 3)]
        test.GDEF.markset - DEBUG - Walker has 52 remaining bytes.
        test.GDEF.markset - INFO - MarkSet has 1 element(s).
        test.GDEF.markset.[0].coverage - DEBUG - Walker has 44 remaining bytes.
        test.GDEF.markset.[0].coverage - DEBUG - Format is 1, count is 1
        test.GDEF.markset.[0].coverage - DEBUG - Raw data are [2]

        >>> fvb(b[:1], logger=logger, editor=ed)
        test.GDEF - DEBUG - Walker has 1 remaining bytes.
        test.GDEF - ERROR - Insufficient bytes.
        """

        logger = kwArgs.pop('logger', None)
        editor = kwArgs.pop('editor')

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

        if version.major != 1 or version.minor != 3:
            logger.error((
              'V0113',
              (version,),
              "Expected version 1.3, got %s."))

            return None

        if w.length() < 8:
            logger.error(('V0114', (), "Insufficient bytes for offsets."))
            return None

        r = cls(version=version)

        stoffsets = w.group("H", 5)
        oIVS = w.unpack("L")

        # Get IVS first, since it may be used by the LigCaretTable.
        if oIVS:
            wSub = w.subWalker(oIVS)
            ao = editor.fvar.axisOrder
            fvw = living_variations.IVS.fromvalidatedwalker
            ivs = fvw(wSub, logger=logger, axisOrder=ao, **kwArgs)
            r.__dict__['_creationExtras'] = {'otcommondeltas': ivs}
            kwArgs['otcommondeltas'] = ivs

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

        >>> ed = utilities.fakeEditor(5)
        >>> from fontio3.fvar import fvar, axial_coordinate, axis_info
        >>> acmin = axial_coordinate.AxialCoordinate(300)
        >>> acdef = axial_coordinate.AxialCoordinate(400)
        >>> acmax = axial_coordinate.AxialCoordinate(700)
        >>> wght_ax_info = axis_info.AxisInfo(
        ...   minValue=acmin, defaultValue=acdef, maxValue=acmax)
        >>> ed.fvar = fvar.Fvar({'wdth': wght_ax_info}, axisOrder=('wdth',))
        >>> s = ("00010003"  # version
        ...      "0012"      # GlyphClassDef offset
        ...      "001A"      # AttachList offset
        ...      "002A"      # LigCaretList offset
        ...      "0046"      # MarkAttachClassDef offset
        ...      "0050"      # MarkGlyphSetsDef offset
        ...      "0000005E"  # ItemVarStore offset
        ...      "0001 0001 0001 0002"  # GlyphClassDef data
        ...      "0006 0001 000C  0001 0001 0004  0001 000A" # AttachList data
        ...      "0006 0001 000C  0001 0001 0003"  # LigCaret partial data
        ...      "0001 0004  0003 0048 0006  0000 0000 8000"  # LigCaret data
        ...      "0002 0001 0000 0004 0003"  # MarkAttachClassDef data
        ...      "0001 0001 00000008  0001 0001 0002"  # MarkGlyphSetsDef
        ...      "0001 0000000C 0001 0000001C"  # IVS data
        ...      "0001 0001 E000 1000 4000 C000 0000 4000"  # IVS data
        ...      "0001 0001 0001 0000 FF4E"  # IVS data
        ...      )
        >>> b = utilities.fromhex(s)
        >>> obj = GDEF.frombytes(b, editor=ed)
        >>> obj.pprint()
        Version:
          Major version: 1
          Minor version: 3
        Glyph Classes:
          Ligature glyph: 1
        Attachment Points:
          4: [10]
        Ligature Caret Points:
          3:
            CaretValue #1:
              Caret value in FUnits: 72
              Variation Record:
                A delta of -178 applies in region 'wdth': (start -0.5, peak 0.25, end 1.0)
        Mark Classes:
          Mark class 3: 0-4
        Mark Sets:
          Mark Glyph Set 0: 2
        """

        editor = kwArgs.pop('editor')

        version = otversion.Version.fromwalker(w, **kwArgs)

        if version.major != 1 or version.minor != 3:
            raise ValueError("Unsupported GDEF %s" % (version,))

        r = cls(version=version)

        stoffsets = w.group("H", 5)
        oIVS = w.unpack("L")

        # Get IVS first, since it may be used by the LigCaretTable.
        if oIVS:
            wSub = w.subWalker(oIVS)
            ao = editor.fvar.axisOrder
            ivs = living_variations.IVS.fromwalker(wSub, axisOrder=ao, **kwArgs)
            r.__dict__['_creationExtras'] = {'otcommondeltas': ivs}
            kwArgs['otcommondeltas'] = ivs

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
              key=lambda x: (self.glyphClasses[x], x)):
                gc = self.glyphClasses[gi]
                s.write("%s\t%d\n" % (bnfgi(gi), gc))
            s.write("class definition end\n\n")

        if self.attachments:
            s.write("attachment list begin\n")
            for gi, atl in sorted(self.attachments.items()):
                s.write("%s\t%s\n" % (bnfgi(gi), "\t".join([str(at) for at in atl])))
            s.write("attachment list end\n\n")

        if self.ligCarets:
            s.write("carets begin\n")
            for gi, lc in sorted(self.ligCarets.items()):
                s.write("%s\t%d\t%s\n" % (
                  bnfgi(gi),
                  len(lc),
                  "\t".join([str(c) for c in lc])))
            s.write("carets end\n\n")

        if self.markClasses:
            s.write("mark attachment class definition begin\n")
            for gi in sorted(
              self.markClasses,
              key=lambda x: (self.markClasses[x], x)):
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
          version=otversion.Version(minor=3),
          glyphClasses=glyphclass._testingValues[1],
          attachments=attachlist._testingValues[1],
          ligCarets=ligcaret._testingValues[2],
          markClasses=markclass._testingValues[1],
          markSets=markset._testingValues[1]))

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
