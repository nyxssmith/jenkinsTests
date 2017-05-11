#
# format4.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mark positioning in a 'kerx' table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.kerx import (
  anchorentry,
  classtable,
  coordentry,
  entry4,
  format4analyzer,
  pointentry,
  staterow)

from fontio3.statetables import namestash, stutils
from fontio3.utilities import valassist
from fontio3.statetables import subtable_glyph_coverage_set


# -----------------------------------------------------------------------------

#
# Private constants
#

_actionClasses = (
  pointentry.PointEntry,
  anchorentry.AnchorEntry,
  coordentry.CoordEntry)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    vFixed = ["Start of text", "Start of line"]
    sFixed = set(vFixed)
    kwArgs.pop('label', None)
    
    for s in vFixed:
        p.deep(d[s], label=("State '%s'" % (s,)), **kwArgs)
    
    for s in sorted(d):
        if s not in sFixed:
            p.deep(d[s], label=("State '%s'" % (s,)), **kwArgs)
    
    attrhelper.M_pprint(d, p, d.getNamer, **kwArgs)

def _validate(obj, **kwArgs):
    logger = kwArgs.pop('logger')
    editor = kwArgs['editor']
    r = True
    
    kinds = {
      e.action.kind
      for row in obj.values()
      for e in row.values()
      if e.action is not None}
    
    if len(kinds) > 1:
        logger.error((
          'V0881',
          (sorted(kinds),),
          "Multiple kinds %s are present; this is not allowed."))
        
        r = False
    
    elif not kinds:
        logger.warning((
          'V0882',
          (),
          "There are no actions in the subtable, which thus will have "
          "no effect. This means the subtable may be removed."))
        
        return True
    
    kind = kinds.pop()
    
    if kind == 2:
        # for coordinates, just check numeric validity
        is_h = valassist.isFormat_h
        
        for stateName, row in obj.items():
            for className, entryObj in row.items():
                if entryObj is not None:
                    
                    subLogger = logger.getChild(
                      "state '%s' class '%s'" % (stateName, className))
                    
                    r = entryObj.isValid(logger=subLogger, **kwArgs) and r
        
        return r
    
    # If we get here, it's kind 0 or 1.
    
    if not stutils.isValid(obj, logger=logger):
        return False
    
    a = format4analyzer.Analyzer(obj)
    glyf = editor.glyf
    immutToMark, immutToCurr, immutToEntry = a.analyze()

    if kind == 0:
        for stateName, row in obj.items():
            for className, entryObj in row.items():
                if entryObj is None or entryObj.action is None:
                    continue
                
                subLogger = logger.getChild(
                  "state '%s' class '%s'" % (stateName, className))
                
                immut = entryObj.asImmutable()
                
                for glyph in immutToMark[immut]:
                    try:
                        count = glyf[glyph].pointCount(editor=editor)
                    except:
                        count = None
                    
                    if count is None:
                        continue  # logging the error will happen elsewhere
                    
                    if entryObj.markedPoint >= (count + 2):
                        subLogger.error((
                          'V0888',
                          (entryObj.markedPoint, glyph),
                          "Marked point %d does not exist in glyph %d"))
                        
                        r = False
                    
                    elif entryObj.markedPoint >= count:
                        subLogger.warning((
                          'V0889',
                          (entryObj.markedPoint, glyph),
                          "Phantom point %d is being used as the mark "
                          "point for glyph %d"))
                    
                for glyph in immutToCurr[immut]:
                    try:
                        count = glyf[glyph].pointCount(editor=editor)
                    except:
                        count = None
                    
                    if count is None:
                        continue  # logging the error will happen elsewhere
                    
                    if entryObj.currentPoint >= (count + 2):
                        subLogger.error((
                          'V0888',
                          (entryObj.currentPoint, glyph),
                          "Current point %d does not exist in glyph %d"))
                        
                        r = False
                    
                    elif entryObj.currentPoint >= count:
                        subLogger.warning((
                          'V0889',
                          (entryObj.currentPoint, glyph),
                          "Phantom point %d is being used as the current "
                          "point for glyph %d"))
        
        return r
    
    # If we get here, it's kind 1.
    
    if not editor.reallyHas(b'ankr'):
        logger.error((
          'V0553',
          (),
          "Format 1 (anchor) is being used, but the font does not "
          "have an 'ankr' table."))
        
        return False
    
    ankrObj = editor.ankr
    
    for stateName, row in obj.items():
        for className, entryObj in row.items():
            if entryObj is None or entryObj.action is None:
                continue
            
            subLogger = logger.getChild(
              "state '%s' class '%s'" % (stateName, className))
            
            immut = entryObj.asImmutable()
            
            for glyph in immutToMark[immut]:
                count = len(ankrObj.get(glyph, []))
                
                if not count:
                    logger.error((
                      'V0890',
                      (glyph,),
                      "Marked glyph %d does not have an entry in "
                      "the 'ankr' table."))
                    
                    r = False
                    continue
                
                if entryObj.action.markedAnchor >= (count + 2):
                    subLogger.error((
                      'V0888',
                      (entryObj.action.markedAnchor, glyph),
                      "Marked point %d does not exist in glyph %d"))
                    
                    r = False
                
                elif entryObj.action.markedAnchor >= count:
                    subLogger.warning((
                      'V0889',
                      (entryObj.action.markedAnchor, glyph),
                      "Phantom point %d is being used as the mark "
                      "point for glyph %d"))
                
            for glyph in immutToCurr[immut]:
                count = len(ankrObj.get(glyph, []))
                
                if not count:
                    logger.error((
                      'V0890',
                      (glyph,),
                      "Current glyph %d does not have an entry in "
                      "the 'ankr' table."))
                    
                    r = False
                    continue
                
                if entryObj.action.currentAnchor >= (count + 2):
                    subLogger.error((
                      'V0888',
                      (entryObj.action.currentAnchor, glyph),
                      "Current point %d does not exist in glyph %d"))
                    
                    r = False
                
                elif entryObj.action.currentAnchor >= count:
                    subLogger.warning((
                      'V0889',
                      (entryObj.action.currentAnchor, glyph),
                      "Phantom point %d is being used as the current "
                      "point for glyph %d"))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format4(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing state-based mark positioning subtables in a 'kerx'
    table. These are dicts mapping state name strings to StateRow objects.
    There are four attributes:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        tupleIndex      If the coverage indicates variation data are present,
                        this will be a tuple index for variation kerning.
    
    >>> _makePointExample().pprint(onlySignificant=True)
    State 'Start of text':
      Class 'x':
        Mark this glyph, then go to state 'Saw x'
    State 'Start of line':
      Class 'x':
        Mark this glyph, then go to state 'Saw x'
    State 'Saw x':
      Class 'acute':
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 19
          Current glyph's point: 12
      Class 'grave':
        Go to state 'Start of text' after doing this alignment:
          Marked glyph's point: 19
          Current glyph's point: 4
      Class 'x':
        Mark this glyph, then go to state 'Saw x'
    Class table:
      30: x
      96: acute
      97: grave
    Header information:
      Horizontal
      With-stream
      No variation kerning
      Process forward
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint,
        map_validatefunc = _validate)
    
    attrSpec = dict(
        coverage = dict(
            attr_followsprotocol = True,
            attr_label = "Header information"),
        
        tupleIndex = dict(
            attr_label = "Variations tuple index",
            attr_showonlyiffunc = functools.partial(operator.is_not, None),
            attr_validatefunc = functools.partial(
              valassist.isFormat_H,
              allowNone = True,
              label = "tuple index")),
        
        classTable = dict(
            attr_followsprotocol = True,
            attr_initfunc = classtable.ClassTable,
            attr_label = "Class table"),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    attrSorted = ('classTable', 'coverage', 'tupleIndex', 'glyphCoverageSet')

    format = 4  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format1 object to the specified writer.
        The following keyword arguments are used:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        A ValueError will be raised if the actions present in the Entry objects
        are of mixed kinds.
        
        >>> h = utilities.hexdump
        >>> h(_makePointExample().binaryString())
               0 | 0000 0007 0000 0030  0000 004C 0000 0078 |.......0...L...x|
              10 | 0000 0090 FEED 0003  0561 6375 7465 0567 |.........acute.g|
              20 | 7261 7665 0178 0001  0553 6177 2078 0000 |rave.x...Saw x..|
              30 | 0006 0004 0003 0008  0001 0004 001E 0006 |................|
              40 | 0060 0004 0061 0005  FFFF 0001 0000 0000 |.`...a..........|
              50 | 0000 0000 0000 0000  0001 0000 0000 0000 |................|
              60 | 0000 0000 0000 0001  0000 0000 0000 0000 |................|
              70 | 0002 0003 0001 0000  0000 0000 FFFF 0002 |................|
              80 | 8000 FFFF 0000 0000  0000 0000 0000 0001 |................|
              90 | 0013 000C 0013 0004                      |........        |
        
        >>> h(_makeAnchorExample().binaryString())
               0 | 0000 0007 0000 0030  0000 004C 0000 0078 |.......0...L...x|
              10 | 4000 0090 FEED 0003  0561 6375 7465 0567 |@........acute.g|
              20 | 7261 7665 0178 0001  0553 6177 2078 0000 |rave.x...Saw x..|
              30 | 0006 0004 0003 0008  0001 0004 001E 0006 |................|
              40 | 0060 0004 0061 0005  FFFF 0001 0000 0000 |.`...a..........|
              50 | 0000 0000 0000 0000  0001 0000 0000 0000 |................|
              60 | 0000 0000 0000 0001  0000 0000 0000 0000 |................|
              70 | 0002 0003 0001 0000  0000 0000 FFFF 0002 |................|
              80 | 8000 FFFF 0000 0000  0000 0000 0000 0001 |................|
              90 | 0013 000C 0013 0004                      |........        |
        
        >>> h(_makeCoordExample().binaryString())
               0 | 0000 0007 0000 0030  0000 004C 0000 0078 |.......0...L...x|
              10 | 8000 0090 FEED 0003  0561 6375 7465 0567 |.........acute.g|
              20 | 7261 7665 0178 0001  0553 6177 2078 0000 |rave.x...Saw x..|
              30 | 0006 0004 0003 0008  0001 0004 001E 0006 |................|
              40 | 0060 0004 0061 0005  FFFF 0001 0000 0000 |.`...a..........|
              50 | 0000 0000 0000 0000  0001 0000 0000 0000 |................|
              60 | 0000 0000 0000 0001  0000 0000 0000 0000 |................|
              70 | 0002 0003 0001 0000  0000 0000 FFFF 0002 |................|
              80 | 8000 FFFF 0000 0000  0000 0000 0000 0001 |................|
              90 | 00C8 0640 01C2 044C  00C8 0640 012C 03E8 |...@...L...@.,..|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        kinds = {
          e.action.kind
          for row in self.values()
          for e in row.values()
          if e.action is not None}
        
        if len(kinds) != 1:
            raise ValueError(
              "Cannot mix action kinds in 'kerx' format 4 subtables!")
        
        kind = kinds.pop()
        assert kind in {0, 1, 2}
        nsObj = namestash.NameStash.fromstatedict(self)
        classNames = nsObj.allClassNames()
        revClassMap = {s: i for i, s in enumerate(classNames)}
        stateNames = nsObj.allStateNames()
        revStateMap = {s: i for i, s in enumerate(stateNames)}
        w.add("L", len(classNames))
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, etStake)
        vtStake = w.getNewStake()
        w.add("B", kind << 6)
        w.addUnresolvedOffset("T", stakeValue, vtStake)  # 3-byte offset, yay!
        
        delKeys = {'classDict', 'neededAlignment', 'revDict', 'stateDict'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        nsObj.buildBinary(w, neededAlignment=4, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        w.alignToByteMultiple(4)
        actionPool = {}  # immut(action) -> (index, actionObj)
        entryPool = {}  # immut(entry) -> (index, entryObj)
        
        for stateName in stateNames:
            stateRow = self[stateName]
            
            for className in classNames:
                entryObj = stateRow[className]
                immut = entryObj.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), entryObj)
                
                action = entryObj.action
                
                if action is not None:
                    immut = action.asImmutable()
                    
                    if immut not in actionPool:
                        actionPool[immut] = (len(actionPool), action)
        
        w.stakeCurrentWithValue(saStake)
        
        for stateName in stateNames:  # order is important!
            row = self[stateName]
            row.buildBinary(w, classNames=classNames, entryPool=entryPool)
        
        w.alignToByteMultiple(4)
        w.stakeCurrentWithValue(etStake)
        ard = {k: t[0] for k, t in actionPool.items()}
        it = iter(entryPool.values())
        
        for index, entryObj in sorted(it, key=operator.itemgetter(0)):
            
            entryObj.buildBinary(
              w,
              stateDict = revStateMap,
              revDict = ard,
              **kwArgs)
        
        w.alignToByteMultiple(4)
        w.stakeCurrentWithValue(vtStake)
        it = actionPool.values()
        
        for index, action in sorted(it, key=operator.itemgetter(0)):
            action.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format4 object from the specified walker,
        doing source validation.
        
        >>> obj = _makePointExample()
        >>> k = {'coverage': obj.coverage, 'tupleIndex': obj.tupleIndex}
        >>> k['logger'] = utilities.makeDoctestLogger("fvw")
        >>> bs = obj.binaryString()
        >>> obj2 = Format4.fromvalidatedbytes(bs, **k)
        fvw.format4 - DEBUG - Walker has 152 remaining bytes.
        fvw.format4.namestash - DEBUG - Walker has 132 remaining bytes.
        fvw.format4 - DEBUG - Walker has 28 remaining bytes.
        fvw.format4.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.format4.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        fvw.format4.actions.[0].pointentry - DEBUG - Walker has 8 remaining bytes.
        fvw.format4.actions.[1].pointentry - DEBUG - Walker has 4 remaining bytes.
        fvw.format4.entries.[0].entry4 - DEBUG - Walker has 24 remaining bytes.
        fvw.format4.entries.[1].entry4 - DEBUG - Walker has 18 remaining bytes.
        fvw.format4.entries.[2].entry4 - DEBUG - Walker has 12 remaining bytes.
        fvw.format4.entries.[3].entry4 - DEBUG - Walker has 6 remaining bytes.
        fvw.format4.state Start of text.staterow - DEBUG - Walker has 44 remaining bytes.
        fvw.format4.state Start of line.staterow - DEBUG - Walker has 30 remaining bytes.
        fvw.format4.state Saw x.staterow - DEBUG - Walker has 16 remaining bytes.
        >>> obj == obj2
        True
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format4")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        numClasses, oCT, oSA, oET, kind, oVT = w.unpack("4LBT")
        
        if numClasses < 4:
            logger.error((
              'V0634',
              (numClasses,),
              "The number of classes in the state table must be at least "
              "four, but is only %d."))
            
            return None
        
        if kind & 0x3F:
            logger.warning((
              'V0879',
              (kind,),
              "One or more reserved bits in the flag byte %02X are not zero."))
        
        kind >>= 6
        
        if kind == 3:
            logger.error((
              'V0880',
              (),
              "Action type mask is 3, which is undefined."))
            
            return None
        
        t = (oCT, oSA, oET, oVT)
        firstValid = w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in t):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return None
        
        wCT, wSA, wET, wVT = stutils.offsetsToSubWalkers(w.subWalker(0), *t)
        
        wETCopy = wET.subWalker(0, relative=True)
        v = wETCopy.unpackRest("3H", strict=False)
        wET = wET.subWalker(0, relative=True, newLimit=6*len(v))
        numStates = max(2, 1 + utilities.safeMax(x[0] for x in v))
        fvw = namestash.NameStash.readormake_validated
        nsObj = fvw(w, t, numStates, numClasses, logger=logger)
        
        if nsObj is None:
            return None
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        fvw = classtable.ClassTable.fromvalidatedwalker
        classTable = fvw(wCT, classNames=classNames, logger=logger)
        
        if classTable is None:
            return None
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        wVTCopy = wVT.subWalker(0, relative=True)
        v = wVTCopy.unpackRest(("2H" if kind < 2 else "4h"), strict=False)
        
        wVT = wVT.subWalker(
          0,
          relative = True,
          newLimit = (4 if kind < 2 else 8) * len(v))
        
        gfvw = _actionClasses[kind].groupfromvalidatedwalker
        v = gfvw(wVT, logger=logger.getChild("actions"), **kwArgs)
        
        if v is None:
            return None
        
        actionMap = dict(enumerate(v))
        
        entries = entry4.Entry.groupfromvalidatedwalker(
          wET,
          actionMap = actionMap,
          stateNames = stateNames,
          logger = logger.getChild("entries"))
        
        if entries is None:
            return None
        
        fvw = staterow.StateRow.fromvalidatedwalker
        
        for stateName in stateNames:
            obj = fvw(
              wSA,
              classNames = classNames,
              entries = entries,
              logger = logger.getChild("state %s" % (stateName,)))
            
            if obj is None:
                return None
            
            r[stateName] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format4 object from the specified walker.
        
        >>> obj = _makePointExample()
        >>> k = {'coverage': obj.coverage, 'tupleIndex': obj.tupleIndex}
        >>> bs = obj.binaryString()
        >>> obj2 = Format4.frombytes(bs, **k)
        >>> obj == obj2
        True
        
        >>> obj = _makeAnchorExample()
        >>> bs = obj.binaryString()
        >>> obj2 = Format4.frombytes(bs, **k)
        >>> obj == obj2
        True
        
        >>> obj = _makeCoordExample()
        >>> bs = obj.binaryString()
        >>> obj2 = Format4.frombytes(bs, **k)
        >>> obj == obj2
        True
        """
        
        numClasses, oCT, oSA, oET, kind, oVT = w.unpack("4LBT")
        kind >>= 6
        
        if kind not in {0, 1, 2}:
            raise ValueError("Unknown action type mask!")
        
        t = (oCT, oSA, oET, oVT)
        wCT, wSA, wET, wVT = stutils.offsetsToSubWalkers(w.subWalker(0), *t)
        wETCopy = wET.subWalker(0, relative=True)
        v = wETCopy.unpackRest("3H", strict=False)
        wET = wET.subWalker(0, relative=True, newLimit=6*len(v))
        numStates = max(2, 1 + utilities.safeMax(x[0] for x in v))
        nsObj = namestash.NameStash.readormake(w, t, numStates, numClasses)
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        fw = classtable.ClassTable.fromwalker
        classTable = fw(wCT, classNames=classNames)
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        wVTCopy = wVT.subWalker(0, relative=True)
        v = wVTCopy.unpackRest(("2H" if kind < 2 else "4h"), strict=False)
        
        wVT = wVT.subWalker(
          0,
          relative = True,
          newLimit = (4 if kind < 2 else 8) * len(v))
        
        v = _actionClasses[kind].groupfromwalker(wVT, **kwArgs)
        actionMap = dict(enumerate(v))
        gfw = entry4.Entry.groupfromwalker
        entries = gfw(wET, actionMap=actionMap, stateNames=stateNames)
        fw = staterow.StateRow.fromwalker
        
        for stateName in stateNames:
            r[stateName] = fw(wSA, classNames=classNames, entries=entries)
        
        return r
    
    def normalize(self):
        """
        Makes sure the complete complement of rows and columns are present.
        """
        
        stutils.normalize(self, staterow.StateRow, entry4.Entry)
    
    def renameClasses(self, oldToNew):
        """
        Renames all class names (in each StateRow, and in the class table) as
        specified by the oldToNew dict, which maps old strings to new ones. If
        an old name is not present as a key in oldToNew, that class name will
        not be changed.
        
        >>> oldToNew = {"acute": "acuteaccent", "grave": "graveaccent"}
        >>> obj = _makePointExample()
        >>> obj.renameClasses(oldToNew)
        >>> obj.pprint(onlySignificant=True)
        State 'Start of text':
          Class 'x':
            Mark this glyph, then go to state 'Saw x'
        State 'Start of line':
          Class 'x':
            Mark this glyph, then go to state 'Saw x'
        State 'Saw x':
          Class 'acuteaccent':
            Go to state 'Start of text' after doing this alignment:
              Marked glyph's point: 19
              Current glyph's point: 12
          Class 'graveaccent':
            Go to state 'Start of text' after doing this alignment:
              Marked glyph's point: 19
              Current glyph's point: 4
          Class 'x':
            Mark this glyph, then go to state 'Saw x'
        Class table:
          30: x
          96: acuteaccent
          97: graveaccent
        Header information:
          Horizontal
          With-stream
          No variation kerning
          Process forward
        """
        
        ct = classtable.ClassTable()
        
        for glyph, className in self.classTable.items():
            ct[glyph] = oldToNew.get(className, className)
        
        self.classTable = ct
        
        for stateName in self:
            stateRow = self[stateName]
            sr = staterow.StateRow()
            
            for className, entryObj in stateRow.items():
                sr[oldToNew.get(className, className)] = entryObj
            
            self[stateName] = sr
    
    def renameStates(self, oldToNew):
        """
        Renames all state names (as keys in the Format1 object, and as
        newStateName values in the individual Entry objects) as specified by
        the oldToNew dict, which maps old strings to new ones. If an old name
        is not present as a key in oldToNew, that class name will not be
        changed.
        
        >>> oldToNew = {"Saw x": "In interesting state"}
        >>> obj = _makePointExample()
        >>> obj.renameStates(oldToNew)
        >>> obj.pprint(onlySignificant=True)
        State 'Start of text':
          Class 'x':
            Mark this glyph, then go to state 'In interesting state'
        State 'Start of line':
          Class 'x':
            Mark this glyph, then go to state 'In interesting state'
        State 'In interesting state':
          Class 'acute':
            Go to state 'Start of text' after doing this alignment:
              Marked glyph's point: 19
              Current glyph's point: 12
          Class 'grave':
            Go to state 'Start of text' after doing this alignment:
              Marked glyph's point: 19
              Current glyph's point: 4
          Class 'x':
            Mark this glyph, then go to state 'In interesting state'
        Class table:
          30: x
          96: acute
          97: grave
        Header information:
          Horizontal
          With-stream
          No variation kerning
          Process forward
        """
        
        for stateRow in self.values():
            for entryObj in stateRow.values():
                s = entryObj.newState
                entryObj.newState = oldToNew.get(s, s)
        
        d = {oldToNew.get(s, s): obj for s, obj in self.items()}
        self.clear()
        self.update(d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.kerx import coverage
    from fontio3.utilities import namer
    
    def _makeAnchorExample():
        cv = coverage.Coverage(crossStream=False)
        ct = classtable.ClassTable({30: "x", 96: "acute", 97: "grave"})
        pe1 = anchorentry.AnchorEntry(markedAnchor=19, currentAnchor=12)
        pe2 = anchorentry.AnchorEntry(markedAnchor=19, currentAnchor=4)
        e1 = entry4.Entry(newState="Start of text")
        e2 = entry4.Entry(newState="Saw x", mark=True)
        e3 = entry4.Entry(newState="Start of text", action=pe1)
        e4 = entry4.Entry(newState="Start of text", action=pe2)
    
        row1 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e1,
          "grave": e1})
    
        row2 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e3,
          "grave": e4})
        
        return Format4(
          {"Start of text": row1, "Start of line": row1, "Saw x": row2},
          coverage = cv,
          classTable = ct)
    
    def _makeCoordExample():
        cv = coverage.Coverage(crossStream=False)
        ct = classtable.ClassTable({30: "x", 96: "acute", 97: "grave"})
        
        pe1 = coordentry.CoordEntry(
          markedX = 200,
          markedY = 1600,
          currentX = 450,
          currentY = 1100)
        
        pe2 = coordentry.CoordEntry(
          markedX = 200,
          markedY = 1600,
          currentX = 300,
          currentY = 1000)
        
        e1 = entry4.Entry(newState="Start of text")
        e2 = entry4.Entry(newState="Saw x", mark=True)
        e3 = entry4.Entry(newState="Start of text", action=pe1)
        e4 = entry4.Entry(newState="Start of text", action=pe2)
    
        row1 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e1,
          "grave": e1})
    
        row2 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e3,
          "grave": e4})
        
        return Format4(
          {"Start of text": row1, "Start of line": row1, "Saw x": row2},
          coverage = cv,
          classTable = ct)
    
    def _makePointExample():
        cv = coverage.Coverage(crossStream=False)
        ct = classtable.ClassTable({30: "x", 96: "acute", 97: "grave"})
        pe1 = pointentry.PointEntry(markedPoint=19, currentPoint=12)
        pe2 = pointentry.PointEntry(markedPoint=19, currentPoint=4)
        e1 = entry4.Entry(newState="Start of text")
        e2 = entry4.Entry(newState="Saw x", mark=True)
        e3 = entry4.Entry(newState="Start of text", action=pe1)
        e4 = entry4.Entry(newState="Start of text", action=pe2)
    
        row1 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e1,
          "grave": e1})
    
        row2 = staterow.StateRow({
          "End of text": e1,
          "Out of bounds": e1,
          "Deleted glyph": e1,
          "End of line": e1,
          "x": e2,
          "acute": e3,
          "grave": e4})
        
        return Format4(
          {"Start of text": row1, "Start of line": row1, "Saw x": row2},
          coverage = cv,
          classTable = ct)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
