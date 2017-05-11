#
# lookup.py
#
# Copyright © 2007-2016 Monotype Imaging Inc. All Rights Reserved
#

"""
Definition of single LookupTables, whether for GPOS or GSUB tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.opentype import lookupflag, runningglyphs
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Constants
#

SMeq = seqmeta.SM_eq

# -----------------------------------------------------------------------------

#
# Private functions
#

def _fwtype(k):
    """
    Return a string representing the Font Worker lookup type, based on a
    lookup subtable's 'kind' attribute (tuple, passed in as 'k').
    """
    
    return {
      ('GPOS', 1): 'single',
      ('GPOS', 2): 'pair',
      ('GPOS', 3): 'cursive',
      ('GPOS', 4): 'mark to base',
      ('GPOS', 5): 'mark to ligature',
      ('GPOS', 6): 'mark to mark',
      ('GPOS', 7): 'context',
      ('GPOS', 8): 'chained',

      ('GSUB', 1): 'single',
      ('GSUB', 2): 'multiple',
      ('GSUB', 3): 'alternate',
      ('GSUB', 4): 'ligature',
      ('GSUB', 5): 'context',
      ('GSUB', 6): 'chained',
      ('GSUB', 8): 'reversechained',

      }.get(k, 'unknown')

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    r = True
    
    if obj.flags.useMarkFilteringSet and (not obj.markFilteringSet):
        logger.error((
          'V0404',
          (),
          "The flags specify mark filtering, "
          "but no filtering set is present."))
        
        r = False
    
    elif (not obj.flags.useMarkFilteringSet) and obj.markFilteringSet:
        logger.warning((
          'V0405',
          (),
          "The flags specify no mark filtering, "
          "but a filtering set is present."))
          
    # non-zero markAttachmentType must be present in GDEF.markClasses
    markClass = obj.flags.markAttachmentType
    
    if markClass:
        if editor.reallyHas(b'GDEF'):
            gdefClassVals = list(editor.GDEF.markClasses.values())
            
            if markClass not in gdefClassVals:
                logger.error((
                    'V0974',
                    (markClass,),
                    "MarkAttachmentType %d indicated but no glyphs in "
                    "GDEF.markClasses are assigned to the Class."))
        
        else:
            logger.error((
                'V0975',
                (),
                "Lookup uses non-zero MarkAttachmentType but a GDEF table is "
                "not present or is unreadable."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Lookup(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single GPOS or GSUB lookup tables. These are tuples of
    subtable objects of the various kinds (although all subtables in a single
    lookup must be of the same kind). Additionally, the following attributes
    are defined:
    
        flags
        lookupName
        markFilteringSet
        sequence
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Subtable 0 (Single positioning table):
      xyz11:
        FUnit adjustment to origin's x-coordinate: -10
    Lookup flags:
      Right-to-left for Cursive: False
      Ignore base glyphs: False
      Ignore ligatures: False
      Ignore marks: False
      Mark attachment type: 4
    Sequence order (lower happens first): 0
    
    >>> _testingValues[0] == _testingValues[0]
    True
    
    >>> _testingValues[0] == _testingValues[1]
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda i, obj:
          "Subtable %d (%s)" % (i, obj.kindString)),
        item_pprintlabelfuncneedsobj = True,
        seq_compactremovesfalses = True,
        seq_falseifcontentsfalse = True,
        seq_validatefunc_partial = _validate)
    
    attrSpec = dict(
        flags = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = lookupflag.LookupFlag,
            attr_label = "Lookup flags",
            attr_strneedsparens = True),

        lookupName = dict(
            attr_ignoreforcomparisons = True,
            attr_followsprotocol = False,
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: None),
            attr_label = "Lookup name",
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
        
        markFilteringSet = dict(
            attr_followsprotocol = True,  # these are Coverage objects
            attr_ignoreforbool = True,
            attr_label = "Mark filtering set",
            attr_showonlyiftrue = True,
            attr_strneedsparens = True),
        
        sequence = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Sequence order (lower happens first)",
            attr_validatefunc_partial = valassist.isNumber))
    
    _dispatchTable = None
    _dispatchTable_FontWorker = None
    _dispatchTable_FontWorker_validated = None
    _dispatchTable_validated = None
    
    #
    # Methods
    #
    
    def __eq__(self, other):
        """
        We perform a pre-test here, checking that self and other have the same
        kind of subtable, and fast-rejecting if they do not. If they do, the
        regular comparison is done. In Python 3, we don't need to provide a
        separate __ne__() method; in Python 2, we do.
        """
        
        if {x.kind for x in self} != {x.kind for x in other}:
            return False
        
        return SMeq(self, other)
    
    @classmethod
    def _handleExtension_GPOS(cls, w, **kwArgs):
        """
        """
        
        # from fontio3.GPOS import extension
        
        format, actualKind, offset = w.unpack("2HL")
        assert format == 1
        assert actualKind != 9
        
        orig = cls._dispatchTable[(True, actualKind)](
          w.subWalker(offset),
          **kwArgs)
        
        # return extension.Extension(original=orig)
        return orig
    
    @classmethod
    def _handleExtension_GPOS_validated(cls, w, **kwArgs):
        """
        """
        
        logger = kwArgs['logger']
        
        if w.length() < 8:
            logger.error((
              'V0400',
              (),
              "Insufficient bytes for Extension header."))
            
            return None
        
        format, actualKind, offset = w.unpack("2HL")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got %d instead."))
            
            return None
        
        if actualKind == 9:
            logger.error((
              'E4103',
              (),
              "Extension lookups cannot hold other Extensions."))
            
            return None
        
        f = cls._dispatchTable_validated.get((True, actualKind), None)
        
        if f is None:
            logger.error((
              'E4103',
              (actualKind,),
              "Actual kind %d in Extension not recognized."))
            
            return None
        
        return f(w.subWalker(offset), **kwArgs)
    
    @classmethod
    def _handleExtension_GSUB(cls, w, **kwArgs):
        """
        """
        
        # from fontio3.GSUB import extension
        
        format, actualKind, offset = w.unpack("2HL")
        assert format == 1
        assert actualKind != 7
        
        orig = cls._dispatchTable[(False, actualKind)](
          w.subWalker(offset),
          **kwArgs)
        
        # return extension.Extension(original=orig)
        return orig
    
    @classmethod
    def _handleExtension_GSUB_validated(cls, w, **kwArgs):
        """
        """
        
        logger = kwArgs['logger']
        
        if w.length() < 8:
            logger.error((
              'V0400',
              (),
              "Insufficient bytes for Extension header."))
            
            return None
        
        format, actualKind, offset = w.unpack("2HL")
        
        if format != 1:
            logger.error((
              'V0002',
              (format,),
              "Expected format 1, but got %d instead."))
            
            return None
        
        if actualKind == 7:
            logger.error((
              'E4202',
              (),
              "Extension lookups cannot hold other Extensions."))
            
            return None
        
        f = cls._dispatchTable_validated.get((False, actualKind), None)
        
        if f is None:
            logger.error((
              'E4202',
              (actualKind,),
              "Actual kind %d in Extension not recognized."))
            
            return None
        
        return f(w.subWalker(offset), **kwArgs)
    
    @classmethod
    def _makeDispatchTable(cls):
        """
        The dispatch table for constructing subtable contents from a binary
        stream is not created at class creation time, in order to avoid
        circular import problems. The first time the dispatch table is used
        this method is called to fill it.
        """
        
        # We separate the processing into two pieces to avoid namespace
        # collisions between gpos.subtables.single and gsub.subtables.single.
        
        def doGPOSPiece(d):
            from fontio3.GPOS import (
              chain,
              context,
              cursive,
              marktobase,
              marktoligature,
              marktomark,
              pair,
              single)
            
            d[True, 1] = single.Single.fromwalker
            d[True, 2] = pair.Pair  # already a factory function
            d[True, 3] = cursive.Cursive.fromwalker
            d[True, 4] = marktobase.MarkToBase.fromwalker
            d[True, 5] = marktoligature.MarkToLigature.fromwalker
            d[True, 6] = marktomark.MarkToMark.fromwalker
            d[True, 7] = context.Context
            d[True, 8] = chain.Chain
            d[True, 9] = Lookup._handleExtension_GPOS
        
        def doGSUBPiece(d):
            from fontio3.GSUB import (
              alternate,
              chain,
              context,
              ligature,
              multiple,
              reverse,
              single)
            
            d[False, 1] = single.Single.fromwalker
            d[False, 2] = multiple.Multiple.fromwalker
            d[False, 3] = alternate.Alternate.fromwalker
            d[False, 4] = ligature.Ligature.fromwalker
            d[False, 5] = context.Context
            d[False, 6] = chain.Chain
            d[False, 7] = Lookup._handleExtension_GSUB
            d[False, 8] = reverse.Reverse.fromwalker
        
        d = cls._dispatchTable = {}
        doGPOSPiece(d)
        doGSUBPiece(d)
    
    @classmethod
    def _makeDispatchTable_FontWorker_validated(cls):
        """
        The dispatch table for constructing subtable contents from FontWorker
        source is not created at class creation time, in order to avoid
        circular import problems. The first time the dispatch table is used
        this method is called to fill it.
        """

        # We separate the processing into two pieces to avoid namespace
        # collisions between gpos.subtables.single and gsub.subtables.single.

        def doGPOSPiece(d):
            from fontio3.GPOS import (
              chain,
              context,
              cursive,
              kernset,
              marktobase,
              marktoligature,
              marktomark,
              pair,
              single)

            d[True, 'single'] = single.Single.fromValidatedFontWorkerSource
            d[True, 'pair'] = pair.Pair_fromValidatedFontWorkerSource
            d[True, 'cursive'] = \
                cursive.Cursive.fromValidatedFontWorkerSource
            d[True, 'mark to base'] = \
                marktobase.MarkToBase.fromValidatedFontWorkerSource
            d[True, 'mark to ligature'] = \
                marktoligature.MarkToLigature.fromValidatedFontWorkerSource
            d[True, 'mark to mark'] = \
                marktomark.MarkToMark.fromValidatedFontWorkerSource
            d[True, 'context'] = \
                context.Context_fromValidatedFontWorkerSource
            d[True, 'chained'] = chain.Chain_fromValidatedFontWorkerSource
            # d[True, 9] = Lookup._handleExtension_GPOS
            d[True, 'kernset'] = kernset.Kernset_fromValidatedFontWorkerSource
            #        ^^^^^^^ see Kernset docstring.
            

        def doGSUBPiece(d):
            from fontio3.GSUB import (
              alternate,
              chain,
              context,
              ligature,
              multiple,
              reverse,
              single)
        
            d[False, 'single'] = single.Single.fromValidatedFontWorkerSource
            d[False, 'multiple'] = multiple.Multiple.fromValidatedFontWorkerSource
            d[False, 'alternate'] = alternate.Alternate.fromValidatedFontWorkerSource
            d[False, 'ligature'] = ligature.Ligature.fromValidatedFontWorkerSource
            d[False, 'context'] = context.Context_fromValidatedFontWorkerSource
            d[False, 'chained'] = chain.Chain_fromValidatedFontWorkerSource
            # d[False, '7'] = Lookup._handleExtension_GSUB
            d[False, 'reversechained'] = reverse.Reverse.fromValidatedFontWorkerSource

        d = cls._dispatchTable_FontWorker_validated = {}
        doGPOSPiece(d)
        doGSUBPiece(d)

    @classmethod
    def _makeDispatchTable_validated(cls):
        """
        The dispatch table for constructing subtable contents from a binary
        stream is not created at class creation time, in order to avoid
        circular import problems. The first time the dispatch table is used
        this method is called to fill it.
        
        This version does source validation.
        """
        
        # We separate the processing into two pieces to avoid namespace
        # collsisions between gpos.subtables.single and gsub.subtables.single.
        
        def doGPOSPiece(d):
            from fontio3.GPOS import (
              chain,
              context,
              cursive,
              marktobase,
              marktoligature,
              marktomark,
              pair,
              single)
            
            d[True, 1] = single.Single.fromvalidatedwalker
            d[True, 2] = pair.Pair_validated
            d[True, 3] = cursive.Cursive.fromvalidatedwalker
            d[True, 4] = marktobase.MarkToBase.fromvalidatedwalker
            d[True, 5] = marktoligature.MarkToLigature.fromvalidatedwalker
            d[True, 6] = marktomark.MarkToMark.fromvalidatedwalker
            d[True, 7] = context.Context_validated
            d[True, 8] = chain.Chain_validated
            d[True, 9] = Lookup._handleExtension_GPOS_validated
        
        def doGSUBPiece(d):
            from fontio3.GSUB import (
              alternate,
              chain,
              context,
              ligature,
              multiple,
              reverse,
              single)
            
            d[False, 1] = single.Single.fromvalidatedwalker
            d[False, 2] = multiple.Multiple.fromvalidatedwalker
            d[False, 3] = alternate.Alternate.fromvalidatedwalker
            d[False, 4] = ligature.Ligature.fromvalidatedwalker
            d[False, 5] = context.Context_validated
            d[False, 6] = chain.Chain_validated
            d[False, 7] = Lookup._handleExtension_GSUB_validated
            d[False, 8] = reverse.Reverse.fromvalidatedwalker
        
        d = cls._dispatchTable_validated = {}
        doGPOSPiece(d)
        doGSUBPiece(d)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. The following
        keyword arguments are used:
        
            extensionPool   A dict mapping the id() of non-extension objects to
                            (sortOrderValue, object, stake) pairs. At
                            buildBinary time for the top-level object (the GPOS
                            table, in this case), once the lookups have all
                            been added then the pool's values should be sorted
                            and then walked, and those pool tables added. Their
                            32-bit offsets will have already been staked here,
                            and the linkage will thus happen automatically.
            
            GDEF            If this Lookup is being added to a font for
                            OpenType 1.6 or later, and there is a non-None
                            markFilteringSet, then this argument must be the
                            GDEF object.
                            
                            Note: We require the Coverage in
                            self.markFilteringSet to already be present in the
                            GDEF table. This means the client code for the top
                            level needs to poll all lookups for any such
                            entries and use them to reconstruct the GDEF table
                            BEFORE calling this buildBinary method.
            
            stakeValue      The stake value for this Extension object. If none
                            is provided, one will be created.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0400 0001 0008  0001 0008 0001 FFF6 |................|
              10 | 0001 0001 000A                           |......          |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0002 0001 0008  0001 000E 0081 0031 |...............1|
              10 | 0002 0016 0030 0001  0002 0008 000A 0002 |.....0..........|
              20 | 000F 0000 0000 FFF6  0000 0000 0014 0000 |................|
              30 | 0034 0000 0000 0000  0001 0014 001E 001A |.4..............|
              40 | 0000 001A 000E 000C  0014 0002 BDF0 0020 |............... |
              50 | 3000 000C 0012 0001  8C04                |0.........      |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0002 0001 0001 0008  0002 004C 0081 0031 |...........L...1|
              10 | 0058 006E 0003 0002  0000 0000 0000 0000 |.X.n............|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0000 0000 0000 0000  0000 FFF6 0000 0000 |................|
              40 | 0000 0084 0000 0000  0000 001E 0084 0000 |................|
              50 | 0084 0078 0001 0004  0005 0006 0007 000F |...x............|
              60 | 0002 0003 0005 0006  0001 0007 0007 0002 |................|
              70 | 000F 000F 0001 0002  0001 0014 0016 0001 |................|
              80 | 000C 0014 0002 BDF0  0020 3000 000C 0012 |......... 0.....|
              90 | 0001 8C04                                |....            |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0001 0000 0001 0008  0001 0008 0001 FFF6 |................|
              10 | 0001 0001 000A                           |......          |
        
        >>> utilities.hexdump(_testingValues[4].binaryString())
               0 | 0001 0000 0001 0008  0002 000C 0003 000A |................|
              10 | 0061 0012 0001 0003  0004 0005 0006      |.a............  |
        
        >>> utilities.hexdump(_testingValues[5].binaryString())
               0 | 0004 0000 0002 000A  0024 0001 0008 0001 |.........$......|
              10 | 000E 0001 0001 0004  0001 0004 0061 0003 |.............a..|
              20 | 000B 001D 0001 000A  0002 0012 0018 0001 |................|
              30 | 0002 0005 000B 0002  000A 0010 0001 0010 |................|
              40 | 0020 0002 0009 001F  0002 0003 000D 0002 |. ..............|
              50 | 000C                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        extPool = kwArgs.get('extensionPool', None)
        
        if extPool is None:
            extPool = {}
            doLocal = True
        
        else:
            doLocal = False
        
        if self:
            kinds = [obj.kind for obj in self]
            
            if len(set(obj[0] for obj in kinds)) > 1:
                raise ValueError(
                  "Cannot mix GPOS and GSUB subtables in a single lookup!")
            
            v = [obj[1] for obj in kinds]
            
            if len(set(v)) > 1:
                raise ValueError(
                  "Cannot mix subtable types in a single lookup!")
        
        else:
            v = [1]
        
        w.add("H", v[0])
        self.flags.useMarkFilteringSet = bool(self.markFilteringSet)
        self.flags.buildBinary(w)
        w.add("H", len(self))
        localPool = {}
        
        for i, obj in enumerate(self):
            objID = id(obj)
            
            if objID not in localPool:
                localPool[objID] = (i, obj, w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, localPool[objID][2])
        
        if self.markFilteringSet is not None:
            try:
                w.add(
                  "H",
                  kwArgs['GDEF'].markSets.index(self.markFilteringSet))
            
            except ValueError:
                raise ValueError("Mark filtering set not in GDEF table!")
        
        for i, obj, stake in sorted(localPool.values()):
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
        
        if doLocal:
            for i, obj, stake in sorted(extPool.values()):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    def findIgnorables(self, glyphArray, **kwArgs):
        """
        Given an array of glyph indices, return a list of True or False values
        of the same length. The value of the flag indicates whether a glyph is
        to be ignored during run() processing.
        
        This therefore takes care of most of the specifications present in the
        LookupFlag object. In order to gain access to the GDEF object, an
        'editor' kwArg should be provided. In its absence, the returned list
        will be all False (i.e. nothing is ignorable).
        
        If a wantMarks keyword is provided it should be a list, whose contents
        will be replaces with an array of True/False values indicating whether
        the corresponding glyph is a mark.
        """
        
        r = [g == -1 for g in glyphArray]
        wantMarks = kwArgs.pop('wantMarks', [])
        wantMarks[:] = r
        
        if 'editor' not in kwArgs:
            return r
        
        e = kwArgs['editor']
        
        if not e.reallyHas('GDEF'):
            return r
        
        gc = e.GDEF.glyphClasses
        
        if gc is None:
            return r
        
        needToProcess = {1, 2, 3}
        f = self.flags
        mc = e.GDEF.markClasses or {}
        
        for i, glyphIndex in enumerate(glyphArray):
            if glyphIndex == -1:
                continue
            
            thisClass = gc.get(glyphIndex, 0)
            
            if thisClass not in needToProcess:
                continue
            
            if thisClass == 1:
                if f.ignoreBaseGlyphs:
                    r[i] = True
            
            elif thisClass == 2:
                if f.ignoreLigatures:
                    r[i] = True
            
            else:
                wantMarks[i] = True
                
                if f.ignoreMarks:
                    r[i] = True
                
                elif f.useMarkFilteringSet:
                    if glyphIndex not in self.markFilteringSet:
                        r[i] = True
                
                elif f.markAttachmentType:
                    if f.markAttachmentType != mc.get(glyphIndex, 0):
                        r[i] = True
        
        return r
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, lookupName, **kwArgs):
        """
        Creates and returns a new Lookup from the specified FontWorkerSource,
        with source validation.

        The following keyword arguments are supported:
        
            forGPOS                 Required; True if this Lookup is for a GPOS
                                    table and False if it is for a GSUB table.
                        
            logger                  A logger to which messages will be posted.

            lookupDict              Required; dictionary mapping lookup names
                                    to previously compiled lookups.

            lookupLineNumbers       Required; dictionary mapping lookup names
                                    to their corresponding line numbers in the
                                    FontWorkerSource.

            lookupSequenceOrder     Required; dictionary mapping lookup names
                                    to their corresponding sequence order.


        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_lookupDict = {}
        >>> l = Lookup.fromValidatedFontWorkerSource(_test_FW_fws2, 'testSingle', namer=_test_FW_namer, forGPOS=True, lookupDict=_test_FW_lookupDict, lookupLineNumbers=_test_FW_lookupLineNumbers,lookupSequenceOrder=_test_FW_lookupSequenceOrder, logger=logger, editor={})
        FW_test.lookup.single - ERROR - line 5 -- incorrect number of tokens, expected 3, found 1
        FW_test.lookup.single - WARNING - line 6 -- glyph 'B' not found
        >>> l.pprint()
        Subtable 0 (Single positioning table):
          1:
            FUnit adjustment to origin's x-coordinate: -123
        Lookup flags:
          Right-to-left for Cursive: False
          Ignore base glyphs: False
          Ignore ligatures: False
          Ignore marks: True
        Lookup name: testSingle
        Sequence order (lower happens first): 7

        >>> _test_FW_lookupDict = {}
        >>> l = Lookup.fromValidatedFontWorkerSource(_test_FW_fws3, 'testSingle', namer=_test_FW_namer, forGPOS=True, lookupDict=_test_FW_lookupDict, lookupLineNumbers=_test_FW_lookupSubtblLineNumbers,lookupSequenceOrder=_test_FW_lookupSequenceOrder, logger=logger, editor={})
        >>> l.pprint()
        Subtable 0 (Single positioning table):
          1:
            FUnit adjustment to origin's x-coordinate: -123
        Subtable 1 (Single positioning table):
          2:
            FUnit adjustment to origin's x-coordinate: 456
        Lookup flags:
          Right-to-left for Cursive: False
          Ignore base glyphs: False
          Ignore ligatures: False
          Ignore marks: False
        Lookup name: testSingle
        Sequence order (lower happens first): 7
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('lookup')
        editor = kwArgs['editor']
        GDEFTbl = editor.get(b'GDEF')
        forGPOS = kwArgs['forGPOS']
        lookupDict = kwArgs['lookupDict']
        
        if lookupName in lookupDict:
            return lookupDict[lookupName]

        fws.push() # save current line number

        if cls._dispatchTable_FontWorker_validated is None:
            cls._makeDispatchTable_FontWorker_validated()

        lookupLineNumbers = kwArgs['lookupLineNumbers']
        r = None  # default

        if lookupName in lookupLineNumbers:
            lookupLineNumber = lookupLineNumbers[lookupName][0]
            fws.goto(lookupLineNumber)
            line = next(fws)
            tokens = [x.strip() for x in line.split('\t')]
            lookupType = tokens[2]
            markFilteringSet = None
            terminalString = 'lookup end'
            flags = lookupflag.LookupFlag()
            
            for line in fws:
                if line.lower() == terminalString:
                    break
                
                if len(line) > 0:
                    tokens = [x.strip() for x in line.split('\t')]
                    firstToken = tokens[0].lower()
                    
                    if firstToken.lower() == 'righttoleft':
                        flags.rightToLeft = 'yes' in tokens[1]
                    
                    elif firstToken.lower() == 'ignorebaseglyphs':
                        flags.ignoreBaseGlyphs = 'yes' in tokens[1]
                    
                    elif firstToken.lower() == 'ignoreligatures':
                        flags.ignoreLigatures = 'yes' in tokens[1]
                    
                    elif firstToken.lower() == 'ignoremarks':
                        flags.ignoreMarks = 'yes' in tokens[1]
                    
                    elif firstToken.lower() == 'markattachmenttype':
                        flags.markAttachmentType = int(tokens[1])
                    
                    elif firstToken.lower() == 'markfiltertype':
                        mfi = int(tokens[1])
                        
                        if not GDEFTbl:
                            logger.error((
                              'Vxxxx',
                              (fws.lineNumber,),
                              "line %d -- MarkFilterType specified, but "
                              "GDEF is not present"))
                        
                        else:
                            if not hasattr(GDEFTbl, 'markSets'):
                                logger.error((
                                  'Vxxxx',
                                  (fws.lineNumber,),
                                  "line %d -- MarkFilterType specified, but "
                                  "GDEF does not have any MarkGlyphSets"))
                            
                            else:
                                if not 0 <= mfi < len(GDEFTbl.markSets):
                                    logger.error((
                                      'Vxxxx',
                                      (fws.lineNumber, mfi),
                                      "line %d -- MarkFilterType %d is "
                                      "out-of-range for the current GDEF's "
                                      "MarkGlyphSets."))
                                
                                else:
                                    flags.useMarkFilteringSet = True
                                    markFilteringSet = GDEFTbl.markSets[mfi]
                    
                    else:
                        fws.prev() # backup so we don't lose this line
                        lookupLineNumbers[lookupName][0] = fws.lineNumber
                        break

            key = (forGPOS, lookupType)
            factoryFunc = cls._dispatchTable_FontWorker_validated[key]
            lookupSequenceOrder = kwArgs['lookupSequenceOrder']

            if lookupType == 'kernset':
                subtables = factoryFunc(fws, logger=logger, **kwArgs)
            
            else:
                subtables = []
                
                for i, lineno in enumerate(lookupLineNumbers[lookupName]):
                    fws.goto(lineno + 1)
                    
                    if i > 0:
                        next(fws)
                    
                    stbl = factoryFunc(fws, logger=logger, **kwArgs)
                    
                    if stbl:
                        subtables.append(stbl)

            if subtables:
                if flags.markAttachmentType and getattr(flags, 'markFilteringSet', False):
                    logger.error((
                      'Vxxxx',
                      (),
                      "Lookup specifies both Mark Attachment Class and Mark "
                      "Filtering Set; only the Mark Filtering Set will be used."))
                    
                    flags.markAttachmentType = None

                r = cls(
                  tuple(subtables),
                  flags = flags,
                  lookupName = lookupName,
                  sequence = lookupSequenceOrder[lookupName],
                  markFilteringSet = markFilteringSet)
                
                lookupDict[lookupName] = r
            
        else:
            logger.error((
              'Vxxxx',
              (fws.lineNumber, lookupName),
              "line %d -- lookup '%s' not found."))

            r = None

        fws.pop() # restore current line number
        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Lookup object from the specified walker,
        doing source validation. The
        following keyword arguments are supported:
        
            forGPOS     Required; True if this Lookup is for a GPOS table and
                        False if it is for a GSUB table.
            
            GDEF        Optional; must be a GDEF object if the font is OpenType
                        1.6 or later.
            
            logger      A logger to which messages will be posted.
            
            sequence    A number indicating the position of this lookup in the
                        original lookup list. When a client adds new Lookups to
                        their OpenType objects, they may set the sequence to a
                        floating value positioned between two existing values,
                        or use any other numeric value that, when sorted,
                        results in the correct order for building the binary
                        data.
        """
        
        assert 'sequence' in kwArgs
        sequence = kwArgs.pop('sequence')
        forGPOS = kwArgs.pop('forGPOS')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('lookup')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        kind = w.unpack("H")
        logger.debug(('Vxxxx', (kind,), "Kind is %d"))
        
        if cls._dispatchTable_validated is None:
            cls._makeDispatchTable_validated()
        
        dispatchKey = (forGPOS, kind)
        
        if dispatchKey not in cls._dispatchTable_validated:
            logger.error((
              'E5701',
              (kind, ['GSUB', 'GPOS'][forGPOS]),
              "The LookupKind of %d is not valid for a %s table."))
            
            return None
        
        flags = lookupflag.LookupFlag.fromvalidatedwalker(
          w,
          logger = logger)
        
        if flags is None:
            return None
        
        offsetCount = w.unpack("H")
        logger.debug(('Vxxxx', (offsetCount,), "Number of subtables is %d"))
        
        if w.length() < 2 * offsetCount:
            logger.error((
              'E5703',
              (),
              "The Subtable offsets are missing or incomplete."))
            
            return None
        
        offsets = w.group("H", offsetCount)
        
#         if flags.ignoreBaseGlyphs and (dispatchKey == (False, 4)):
#             logger.error((
#               'V0999',
#               (),
#               "Ligature Lookup has ignoreBaseGlyphs set, which is invalid"))
#             
#             return None
        
        if flags.useMarkFilteringSet:  # only in OT 1.6 or later
            g = kwArgs.get('GDEF', None)

            if g is None:
                logger.error((
                  'V0952',
                  (),
                  "Mark filtering is specified, but the GDEF table "
                  "is not present in the font."))
                  
                return None

            if not hasattr(g, 'markSets'):
                logger.error((
                  'V0401',
                  (),
                  "Mark filtering is specified, but the GDEF table "
                  "is earlier than version 1.6."))
                
                return None
            
            if w.length() < 2:
                logger.error((
                  'V0402',
                  (),
                  "The mark set index is missing or incomplete."))
                
                return None
            
            msIndex = w.unpack("H")
            logger.debug(('Vxxxx', (msIndex,), "Mark set index is %d"))
            
            if msIndex >= len(g.markSets):
                logger.error((
                  'V0403',
                  (msIndex,),
                  "The mark set index %d is out of range."))
                
                return None
            
            ms = g.markSets[msIndex]
        
        else:
            ms = None
        
        factoryFunc = cls._dispatchTable_validated[dispatchKey]
        v = [None] * offsetCount
        
        for i, offset in enumerate(offsets):
            logger.debug(('Vxxxx', (i, offset), "Subtable offset %d is %d"))
            subLogger = logger.getChild("subtable %d" % (i,))
            
            obj = factoryFunc(
              w.subWalker(offset),
              logger = subLogger,
              **kwArgs)
            
            if obj is None:
                return None
            
            v[i] = obj
        
        r = cls(
          v,
          flags = flags,
          markFilteringSet = ms,
          sequence = sequence)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Lookup from the specified walker. The
        following keyword arguments are supported:
        
            forGPOS     Required; True if this Lookup is for a GPOS table and
                        False if it is for a GSUB table.
            
            GDEF        Optional; must be a GDEF object if the font is OpenType
                        1.6 or later.
            
            sequence    A number indicating the position of this lookup in the
                        original lookup list. When a client adds new Lookups to
                        their OpenType objects, they may set the sequence to a
                        floating value positioned between two existing values,
                        or use any other numeric value that, when sorted,
                        results in the correct order for building the binary
                        data.
        
        >>> t = _testingValues
        >>> f = Lookup.frombytes
        >>> t[0] == f(t[0].binaryString(), forGPOS=True, sequence=0)
        True
        
        >>> t[1] == f(t[1].binaryString(), forGPOS=True, sequence=1)
        True
        
        >>> t[2] == f(t[2].binaryString(), forGPOS=True, sequence=2)
        True
        
        >>> t[3] == f(t[3].binaryString(), forGPOS=True, sequence=3)
        True
        
        >>> t[4] == f(t[4].binaryString(), forGPOS=False, sequence=4)
        True
        
        >>> t[5] == f(t[5].binaryString(), forGPOS=False, sequence=5)
        True
        """
        
        forGPOS = kwArgs['forGPOS']
        kind = w.unpack("H")
        flags = lookupflag.LookupFlag.fromwalker(w)
        offsets = w.group("H", w.unpack("H"))
        
        if flags.useMarkFilteringSet:  # only in OT 1.6 or later
            try:
                ms = kwArgs['GDEF'].markSets[w.unpack("H")]
            except ValueError:
                raise ValueError("No mark filtering in GDEF table!")
        
        else:
            ms = None
        
        if cls._dispatchTable is None:
            cls._makeDispatchTable()
        
        factoryFunc = cls._dispatchTable[forGPOS, kind]
        
        r = cls(
            (factoryFunc(w.subWalker(offset), **kwArgs) for offset in offsets),
            flags=flags,
            markFilteringSet=ms,
            sequence=kwArgs['sequence'])
        
        return r

    def getMarkGlyphSetIndex(self, **kwArgs):
        """
        Return an integer representing the lookup's markSet which is (should
        be) defined in the GDEF, or None if it can't be found in the GDEF.
        'GDEF' must be in kwArgs so we can get to the table.
        """
        
        editor = kwArgs.get('editor')
        GDEFTbl = editor.GDEF if editor.reallyHas(b'GDEF') else None

        if GDEFTbl is None:
            return None

        if not hasattr(GDEFTbl, 'markSets'):
            return None
        
        if self.markFilteringSet:
            for i, ms in enumerate(GDEFTbl.markSets):
                if ms == self.markFilteringSet:
                    return i
        
        return None
    
    def run(self, glyphArray, **kwArgs):
        """
        """
        
        whichTable, subKind = self[0].kind
        
        if 'isRLCase' in kwArgs:
            isRLCase = kwArgs.pop('isRLCase')
        elif 'bidiLevels' in kwArgs:
            isRLCase = bool(min(kwArgs['bidiLevels'].values()) % 2)
        else:
            isRLCase = False
        
        if whichTable == 'GSUB':
            r = glyphArray
            
            if (subKind == 8) and self.flags.rightToLeft:
                startIndex = len(r) - 1
                
                while startIndex >= 0:
                    r, count = self.runOne_GSUB(r, startIndex, **kwArgs)
                    startIndex -= (count or 1)
            
            else:
                startIndex = 0
                
                while startIndex < len(r):  # note len(r) might change!
                    r, count = self.runOne_GSUB(r, startIndex, **kwArgs)
                    startIndex += (count or 1)
        
        else:  # GPOS
            if 'cumulEffects' in kwArgs:
                r = kwArgs.pop('cumulEffects')
            
            else:
                from fontio3.GPOS.effect import Effect
                
                r = [Effect() for g in glyphArray]
            
            if (subKind == 3) and self.flags.rightToLeft:
                startIndex = len(glyphArray) - 1
            
                while startIndex >= 0:
                    rNew, count = self.runOne_GPOS(
                      glyphArray,
                      startIndex,
                      cumulEffects = r,
                      isRLCase = isRLCase,
                      **kwArgs)
                
                    if rNew is not None:
                        r = rNew
                
                    startIndex -= (count or 1)
            
            else:
                startIndex = 0
            
                while startIndex < len(glyphArray):
                    rNew, count = self.runOne_GPOS(
                      glyphArray,
                      startIndex,
                      cumulEffects = r,
                      isRLCase = isRLCase,
                      **kwArgs)
                
                    if rNew is not None:
                        r = rNew
                
                    startIndex += (count or 1)
        
        return r
    
    def runOne_GPOS(self, glyphArray, startIndex, **kwArgs):
        """
        """
        
        from fontio3.GPOS.effect import Effect
        
        ga = runningglyphs.GlyphList.fromiterable(glyphArray)  # preserves offsets
        
        if 'cumulEffects' in kwArgs:
            r = kwArgs.pop('cumulEffects')
        else:
            r = [Effect() for g in ga]
        
        if 'igsFunc' not in kwArgs:
            kwArgs['igsFunc'] = self.findIgnorables
        
        # While inefficient, this has to be done here, because effects in GSUB
        # contextual or chaining subtables might redo the glyph array.
        
        if kwArgs['igsFunc'](glyphArray, **kwArgs)[startIndex]:
            return (r, 0)
        
        for subtable in self:
            rNew, count = subtable.runOne(
              ga,
              startIndex,
              cumulEffects = r,
              **kwArgs)
            
            if not count:
                assert rNew is None
                continue
            
            # Something happened, so we're done, by the OpenType rule that
            # states processing for a given glyph stops in a Lookup after the
            # first subtable that actually matches (even if no actual changes
            # are made to the glyph array).
            
            return (rNew, count)
        
        return (r, 0)
    
    def runOne_GSUB(self, glyphArray, startIndex, **kwArgs):
        """
        Do the processing of this Lookup for a single index within the given
        glyph array. This method is called by the Lookup's run() method, and in
        turn calls the runOne methods for the subtables.
        """
        
        r = runningglyphs.GlyphList.fromiterable(glyphArray)  # preserves offsets
        
        if 'igsFunc' not in kwArgs:
            kwArgs['igsFunc'] = self.findIgnorables
        
        if kwArgs['igsFunc'](glyphArray, **kwArgs)[startIndex]:
            return (glyphArray, 0)
        
        for i, subtable in enumerate(self):
            rNew, count = subtable.runOne(
              r,
              startIndex,
              **kwArgs)
            
            if not count:
                continue
            
            # Something happened, so we're done, by the OpenType rule that
            # states processing for a given glyph stops in a Lookup after the
            # first subtable that actually matches (even if no actual changes
            # are made to the glyph array).
            
            return (rNew, count)
        
        return (glyphArray, 0)
    
    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write the lookup tag entry, sequence, and type to stream 's' in
        FontWorker source format.
        """
        
        if (len(self) == 2 and 
            self[0].kindString == 'Pair (glyph) positioning table' and
            self[1].kindString == 'Pair (class) positioning table'):
            fwtype = 'kernset'
        
        else:
            fwtype = _fwtype(self[0].kind)

        s.write("\nlookup\t%d\t%s\n\n" % (self.sequence, fwtype))

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
    
    class _TV(object):
        def __init__(self):
            self.d = {}
        
        def __getitem__(self, n):
            if not self.d:
                self._fill()
            
            return self.d[n]
        
        def _fill(self):
            self._fillGPOS()
            self._fillGSUB()
        
        def _fillGPOS(self):
            from fontio3.GPOS import extension, pairclasses, pairglyphs, single
            lf = lookupflag.LookupFlag
            
            # [0] is GPOS Single
            self.d[0] = Lookup(
              [single._testingValues[0]],
              flags=lf(markAttachmentType=4),
              sequence=0)
            
            # [1] and [2] are GPOS pair (glyph and class, respectively)
            self.d[1] = Lookup(
              [pairglyphs._testingValues[0]],
              flags=lf(ignoreBaseGlyphs=True),
              sequence=1)
            
            self.d[2] = Lookup(
              [pairclasses._testingValues[0]],
              flags=lf(rightToLeft=True),
              sequence=2)
            
            # [3] is GPOS single
            self.d[3] = Lookup(
              [single._testingValues[0]],
              sequence=3)
        
        def _fillGSUB(self):
            from fontio3.GSUB import ligature, single
            lf = lookupflag.LookupFlag
            
            # [4] is GSUB Single
            self.d[4] = Lookup(
              [single._testingValues[2]],
              sequence=4)
            
            # [5] is GSUB ligature
            self.d[5] = Lookup(
              [ligature._testingValues[1], ligature._testingValues[2]],
              sequence=5)
    
    _testingValues = _TV()

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1,
        'X': 2,
    }
    _test_FW_namer._initialized = True
    
    _test_FW_lookupLineNumbers = {
        'testSingle': [1]
    }

    _test_FW_lookupSubtblLineNumbers = {
        'testSingle': [1, 4]
    }

    _test_FW_lookupSequenceOrder = {
        'testSingle': 7
    }
    _test_FW_fws = FontWorkerSource(StringIO(
        """lookup	testSingle	single
        
        x placement	A	-123
        lookup end
        """))

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """lookup	testSingle	single
        IgNoreMarks	yes

        x placement	A	-123
        foo
        x placement	B	-123
        lookup end
        """))

    _test_FW_fws3 = FontWorkerSource(StringIO(
        """lookup	testSingle	single
        
        x placement	A	-123
        %subtable

        x placement	X	456
        lookup end
        """))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
