#
# format1.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for state table kerning in a 'kerx' state table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta
from fontio3.kerx import classtable, coverage, entry, staterow, valuetuple
from fontio3.statetables import namestash, stutils
from fontio3.utilities import valassist
from fontio3.statetables import subtable_glyph_coverage_set

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

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format1(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire state-based kerning tables in a 'kerx' table.
    These are dicts mapping state name strings to StateRow objects. There are
    three attributes:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        tupleIndex      If the coverage indicates variation data are present,
                        this will be a tuple index for variation kerning.
    
    >>> _testingValues[1].pprint(
    ...   namer = namer.testingNamer(),
    ...   onlySignificant = True)
    State 'Start of text':
      Class 'Letter':
        Go to state 'In word'
    State 'Start of line':
      Class 'Letter':
        Go to state 'In word'
    State 'In word':
      Class 'Out of bounds':
        Go to state 'In word'
      Class 'Deleted glyph':
        Go to state 'In word'
      Class 'Letter':
        Push this glyph, then go to state 'In word' after applying these kerning shifts to the popped glyphs:
          Pop #1: 682
      Class 'Punctuation':
        Go to state 'In word'
      Class 'Space':
        Reset kerning, then go to state 'Start of text'
    Class table:
      afii60001: Letter
      afii60002: Letter
      xyz13: Punctuation
      xyz14: Punctuation
      xyz31: Letter
      xyz32: Letter
      xyz4: Space
      xyz5: Punctuation
      xyz52: Letter
      xyz6: Punctuation
      xyz7: Punctuation
    Header information:
      Horizontal
      Cross-stream
      No variation kerning
      Process forward
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint)
    
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

    format = 1  # class constant
    
    #
    # Methods
    #
    
    @staticmethod
    def _combinedClasses(leftCD, rightCD, leftMap=None):
        """
        Given a pair of classDefs (or similar dict-like objects) which might
        have some glyphs in common, return a new ClassTable object. This is
        necessary in AAT because kerning state tables don't have separate left
        and right class maps.

        If a leftMap is provided, it will be filled with keys of leftCD class
        indices pointing to sets of class names involving those indices.
        
        >>> L = {
        ...   6: 1,
        ...   8: 1,
        ...   10: 2,
        ...   14: 2,
        ...   16: 2,
        ...   23: 3,
        ...   29: 3,
        ...   31: 4,
        ...   32: 4,
        ...   34: 4,
        ...   35: 4}
        >>> R = {
        ...   7: 1,
        ...   9: 1,
        ...   10: 2,
        ...   11: 2,
        ...   12: 2,
        ...   23: 5,
        ...   24: 4,
        ...   25: 3,
        ...   29: 5,
        ...   32: 5}
        >>> M = {}
        >>> Format1._combinedClasses(L, R, M).pprint()
        6: class_L_1
        7: class_R_1
        8: class_L_1
        9: class_R_1
        10: class_LR_2_2
        11: class_R_2
        12: class_R_2
        14: class_L_2
        16: class_L_2
        23: class_LR_3_5
        24: class_R_4
        25: class_R_3
        29: class_LR_3_5
        31: class_L_4
        32: class_LR_4_5
        34: class_L_4
        35: class_L_4
        
        >>> for lc, s in sorted(M.items()): print(lc, sorted(s))
        1 ['class_L_1']
        2 ['class_LR_2_2', 'class_L_2']
        3 ['class_LR_3_5']
        4 ['class_LR_4_5', 'class_L_4']
        """
        
        leftCD = {k: v for k, v in leftCD.items() if v}
        rightCD = {k: v for k, v in rightCD.items() if v}
        allLeftGlyphs = set(leftCD)
        allRightGlyphs = set(rightCD)
        allGlyphs = allLeftGlyphs | allRightGlyphs
        d = {}  # combinedName -> glyph set
        
        if leftMap is None:
            leftMap = {}
        
        for glyph in allGlyphs:
            if glyph in allLeftGlyphs and glyph in allRightGlyphs:
                leftClass = leftCD[glyph]
                rightClass = rightCD[glyph]
                name = "class_LR_%d_%d" % (leftClass, rightClass)
            
            elif glyph in allLeftGlyphs:
                leftClass = leftCD[glyph]
                name = "class_L_%d" % (leftClass,)
            
            else:
                leftClass = None
                name = "class_R_%d" % (rightCD[glyph],)
            
            d.setdefault(name, set()).add(glyph)
            
            if leftClass is not None:
                leftMap.setdefault(leftClass, set()).add(name)
        
        return classtable.ClassTable((g, cn) for cn, s in d.items() for g in s)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format1 object to the specified writer.
        The following keyword arguments are used:
        
            stakeValue      A value that will stake the start of the data. This
                            is optional.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0007 0000 003C  0000 0074 0000 00A0 |.......<...t....|
              10 | 0000 00B8 FEED 0003  064C 6574 7465 720B |.........Letter.|
              20 | 5075 6E63 7475 6174  696F 6E05 5370 6163 |Punctuation.Spac|
              30 | 6500 0107 496E 2077  6F72 6400 0002 0006 |e...In word.....|
              40 | 0006 0018 0002 000C  0003 0003 0006 0006 |................|
              50 | 0004 0005 000D 000C  0005 001F 001E 0004 |................|
              60 | 0033 0033 0004 0061  0060 0004 FFFF FFFF |.3.3...a.`......|
              70 | 0001 0000 0001 0001  0001 0001 0000 0001 |................|
              80 | 0001 0001 0001 0001  0001 0000 0001 0001 |................|
              90 | 0001 0000 0000 0001  0002 0000 0003 0000 |................|
              A0 | 0002 0000 FFFF 0000  0000 FFFF 0002 8000 |................|
              B0 | 0000 0000 2000 FFFF  02AA FFFF           |.... .......    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
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
        w.addUnresolvedOffset("L", stakeValue, vtStake)
        
        delKeys = {
          'classDict',
          'neededAlignment',
          'stateDict',
          'valueRevDict'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        nsObj.buildBinary(w, neededAlignment=4, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        w.alignToByteMultiple(4)
        
        # build the value and entry pools
        valuePool = {}
        entryPool = {}
        
        # Order is important in the following, since it affects the assignment
        # of entry indices. (The *specific* order is not important, only that
        # it is reproducible across calls)
        
        it1 = sorted(self.items(), key=operator.itemgetter(0))
        
        for stateName, stateRow in it1:
            it2 = sorted(stateRow.items(), key=operator.itemgetter(0))
            
            for className, entryObj in it2:
                immut = entryObj.asImmutable()
                
                if immut not in entryPool:
                    entryPool[immut] = (len(entryPool), entryObj)
                
                entryObjValues = entryObj.values
                
                if entryObjValues is not None:
                    immut = entryObjValues.asImmutable()
                    
                    if immut not in valuePool:
                        valuePool[immut] = (len(valuePool), entryObjValues)
        
        # write the state array
        w.stakeCurrentWithValue(saStake)
        
        for stateName in stateNames:  # order is important!
            row = self[stateName]
            row.buildBinary(w, classNames=classNames, entryPool=entryPool)
        
        w.alignToByteMultiple(4)
        
        # write the entry table
        w.stakeCurrentWithValue(etStake)
        vrd = {k: t[0] for k, t in valuePool.items()}
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for index, entryObj in it:
            entryObj.buildBinary(
              w,
              stateDict = revStateMap,
              valueRevDict = vrd,
              **kwArgs)
        
        w.alignToByteMultiple(4)
        
        # write the value table
        w.stakeCurrentWithValue(vtStake)
        it = sorted(valuePool.values(), key=operator.itemgetter(0))
        
        for index, valueTuple in it:
            valueTuple.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromformat2(cls, fmt2Obj, **kwArgs):
        """
        Creates and returns a new Format1 object from the specified 'kerx'
        Format2 object.
        """
        
        leftMap = {}
        
        unionCT = cls._combinedClasses(
          fmt2Obj.leftClassDef,
          fmt2Obj.rightClassDef,
          leftMap)
        
        r = cls(
          {},
          classTable = unionCT,
          coverage = kwArgs.pop('coverage', coverage.Coverage()),
          tupleIndex = kwArgs.pop('tupleIndex', 0))
        
        addedClassNames = tuple(sorted(set(unionCT.values())))
        classNames = namestash.fixedClassNames + addedClassNames
        
        addedStateNames = tuple(
          "Saw_L_%d" % (n,)
          for n in sorted(set(fmt2Obj.leftClassDef.values())))
        
        stateNames = namestash.fixedStateNames + addedStateNames
        E = entry.Entry
        defaultEntry = E()
        
        for stateName in stateNames:
            newRow = staterow.StateRow()
            
            for className in classNames:
                if className == 'Deleted glyph':
                    newRow[className] = E(newState=stateName)
                else:
                    newRow[className] = defaultEntry
            
            r[stateName] = newRow
        
        for cp, dist in fmt2Obj.items():
            if not dist:
                continue
            
            # For the SOT and SOL states, each cell belonging to either
            # class_L_cp[0] or class_LR_cp[0]* gets a link to the Saw_L_cp[0]
            # state.
            
            f2LeftClass, f2RightClass = cp
            firstCell = E(newState="Saw_L_%d" % (f2LeftClass,))
            match1 = "class_L_%d" % (f2LeftClass,)
            match2 = "class_LR_%d_" % (f2LeftClass,)
            
            for className in classNames[4:]:
                if className == match1 or className.startswith(match2):
                    for sn in ("Start of text", "Start of line"):
                        if r[sn][className] == defaultEntry:
                            r[sn][className] = firstCell
            
            match3 = "class_R_%d" % (f2RightClass,)
            match4 = "class_LR_"
            match5 = "_%d" % (f2RightClass,)
            
            for className in classNames[4:]:
                isLR = (
                  className.startswith(match4) and
                  className.endswith(match5))
                
                if (className == match3) or isLR:
                    sn = "Saw_L_%d" % (f2LeftClass,)
                    assert r[sn][className] == defaultEntry
                    val = valuetuple.ValueTuple([dist])
                    
                    if className == match3:
                        r[sn][className] = E(
                          newState = "Start of text",
                          push = True,
                          values = val)
                    
                    else:
                        r[sn][className] = E(
                          newState = "Saw_L_%s" % (className.split('_')[2],),
                          push = True,
                          values = val)
        
        # Now that the nonzero kerning entries are there, go through and fill
        # in the links for any cells which are still empty but have a LR class.
        
        for stateName in stateNames[2:]:
            for className in classNames[4:]:
                if className.startswith("class_R"):
                    continue
                
                cell = r[stateName][className]
                
                if cell != defaultEntry:
                    continue
                
                r[stateName][className] = E(
                  newState = "Saw_L_%s" % (className.split('_')[2],))
        
        return r
    
    @classmethod
    def fromkern_format1(cls, k1, **kwArgs):
        """
        Creates and returns a new Format1 object using the specified 'kern'
        Format1 object.
        """
        
        cv = coverage.Coverage.fromkern_coverage(k1.coverage)
        ct = classtable.ClassTable(k1.classTable)
        r = cls({}, coverage=cv, tupleIndex=k1.tupleIndex, classTable=ct)
        
        for stateName, stateRowObj in k1.items():
            newRow = staterow.StateRow()
            
            for className, entryObj in stateRowObj.items():
                # The main difference that needs to be taken account of is the
                # different position of the "reset cross-stream kerning" flag.
                # In the 'kern' world, that's all the way down in the Value
                # object, while in the 'kerx' world it's up at the Entry level.
                
                reset = False
                
                if entryObj.values is not None:
                    v = []
                    
                    for value in entryObj.values:
                        v.append(int(value))
                        
                        if value.resetCrossStream:
                            reset = True
                    
                    values = valuetuple.ValueTuple(v)
                
                else:
                    values = None
                
                newRow[className] = entry.Entry(
                  newState = entryObj.newState,
                  noAdvance = entryObj.noAdvance,
                  push = entryObj.push,
                  reset = reset,
                  values = values)
            
            r[stateName] = newRow
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format1 object from the specified walker,
        doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format1")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 20:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        t = w.unpack("5L")
        numClasses, oCT, oSA, oET, oVT = t
        
        if numClasses < 4:
            logger.error((
              'V0634',
              (numClasses,),
              "The number of classes in the state table must be at least "
              "four, but is only %d."))
            
            return None
        
        firstValid = w.getOffset() - stBaseOffset
        lastValidPlusOne = firstValid + w.length()
        
        if any(o < firstValid or o >= lastValidPlusOne for o in t[1:]):
            logger.error((
              'V0635',
              (),
              "One or more offsets to state table components are outside "
              "the bounds of the state table itself."))
            
            return None
        
        wCT, wSA, wET, wVT = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          *t[1:])
        
        wETCopy = wET.subWalker(0, relative=True)
        v = wETCopy.unpackRest("3H", strict=False)
        numStates = 1 + utilities.safeMax(x[0] for x in v)
        numEntries = len(v)
        
        nsObj = namestash.NameStash.readormake_validated(
          w,
          (oCT, oSA, oET, oVT),
          numStates,
          numClasses,
          logger = logger)
        
        if nsObj is None:
            return None
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromvalidatedwalker(
          wCT,
          classNames = classNames,
          logger = logger)
        
        if classTable is None:
            return None
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        # build value table
        valueDict = {}
        fvw = valuetuple.ValueTuple.fromvalidatedwalker
        index = 0
        
        while wVT.stillGoing():
            obj = fvw(wVT, logger=logger.getChild("value %d" % (index,)))
            
            if obj is None:
                return None
            
            valueDict[index] = obj
            index += 1
        
        # build entry table
        entries = []
        index = 0
        fvw = entry.Entry.fromvalidatedwalker
        
        while index < numEntries:
            obj = fvw(
              wET,
              stateNames = stateNames,
              valueDict = valueDict,
              logger = logger.getChild("entry %d" % (index,)))
            
            if obj is None:
                return None
            
            entries.append(obj)
            index += 1
        
        # finally, build state table
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
        Creates and returns a new Format1 object from the specified walker.
        
        >>> d = {'coverage': _testingValues[1].coverage.__copy__()}
        >>> obj = _testingValues[1]
        >>> obj == Format1.frombytes(obj.binaryString(), **d)
        True
        """
        
        numClasses, oCT, oSA, oET, oVT = w.unpack("5L")
        
        wCT, wSA, wET, wVT = stutils.offsetsToSubWalkers(
          w.subWalker(0),
          oCT,
          oSA,
          oET,
          oVT)
        
        wETCopy = wET.subWalker(0, relative=True)
        v = wETCopy.unpackRest("3H", strict=False)
        numStates = 1 + utilities.safeMax(x[0] for x in v)
        numEntries = len(v)
        
        nsObj = namestash.NameStash.readormake(
          w,
          (oCT, oSA, oET, oVT),
          numStates,
          numClasses)
        
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        
        classTable = classtable.ClassTable.fromwalker(
          wCT,
          classNames = classNames)
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        # build value table
        valueDict = {}
        fw = valuetuple.ValueTuple.fromwalker
        index = 0
        
        while wVT.stillGoing():
            valueDict[index] = fw(wVT)
            index += 1
        
        # build entry table
        fw = entry.Entry.fromwalker
        d = {'stateNames': stateNames, 'valueDict': valueDict}
        entries = [fw(wET, **d) for i in range(numEntries)]
        
        # finally, build state table
        fw = staterow.StateRow.fromwalker
        d = {'classNames': classNames, 'entries': entries}
        
        for stateName in stateNames:
            r[stateName] = fw(wSA, **d)
        
        return r
    
    def normalize(self):
        """
        Makes sure the complete complement of rows and columns are present.
        """
        
        stutils.normalize(self, staterow.StateRow, entry.Entry)
    
    def renameClasses(self, oldToNew):
        """
        Renames all class names (in each StateRow, and in the class table) as
        specified by the oldToNew dict, which maps old strings to new ones. If
        an old name is not present as a key in oldToNew, that class name will
        not be changed.
        
        >>> obj = _testingValues[1].__deepcopy__()
        >>> oldToNew = {"Space": "Whitespace"}
        >>> obj.renameClasses(oldToNew)
        >>> obj.pprint(namer=namer.testingNamer(), onlySignificant=True)
        State 'Start of text':
          Class 'Letter':
            Go to state 'In word'
        State 'Start of line':
          Class 'Letter':
            Go to state 'In word'
        State 'In word':
          Class 'Out of bounds':
            Go to state 'In word'
          Class 'Deleted glyph':
            Go to state 'In word'
          Class 'Letter':
            Push this glyph, then go to state 'In word' after applying these kerning shifts to the popped glyphs:
              Pop #1: 682
          Class 'Punctuation':
            Go to state 'In word'
          Class 'Whitespace':
            Reset kerning, then go to state 'Start of text'
        Class table:
          afii60001: Letter
          afii60002: Letter
          xyz13: Punctuation
          xyz14: Punctuation
          xyz31: Letter
          xyz32: Letter
          xyz4: Whitespace
          xyz5: Punctuation
          xyz52: Letter
          xyz6: Punctuation
          xyz7: Punctuation
        Header information:
          Horizontal
          Cross-stream
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
        
        >>> oldToNew = {"In word": "Doing shift"}
        >>> obj = _testingValues[1].__deepcopy__()
        >>> obj.renameStates(oldToNew)
        >>> obj.pprint(namer=namer.testingNamer(), onlySignificant=True)
        State 'Start of text':
          Class 'Letter':
            Go to state 'Doing shift'
        State 'Start of line':
          Class 'Letter':
            Go to state 'Doing shift'
        State 'Doing shift':
          Class 'Out of bounds':
            Go to state 'Doing shift'
          Class 'Deleted glyph':
            Go to state 'Doing shift'
          Class 'Letter':
            Push this glyph, then go to state 'Doing shift' after applying these kerning shifts to the popped glyphs:
              Pop #1: 682
          Class 'Punctuation':
            Go to state 'Doing shift'
          Class 'Space':
            Reset kerning, then go to state 'Start of text'
        Class table:
          afii60001: Letter
          afii60002: Letter
          xyz13: Punctuation
          xyz14: Punctuation
          xyz31: Letter
          xyz32: Letter
          xyz4: Space
          xyz5: Punctuation
          xyz52: Letter
          xyz6: Punctuation
          xyz7: Punctuation
        Header information:
          Horizontal
          Cross-stream
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
    
    _srtv = staterow._testingValues
    _cv = coverage.Coverage(crossStream=True)
    
    _ct = classtable.ClassTable({
      3: "Space",
      4: "Punctuation",
      5: "Punctuation",
      6: "Punctuation",
      12: "Punctuation",
      13: "Punctuation",
      30: "Letter",
      31: "Letter",
      51: "Letter",
      96: "Letter",
      97: "Letter"})
    
    _testingValues = (
        Format1(),
        
        Format1(
          { "Start of text": _srtv[1],
            "Start of line": _srtv[1],
            "In word": _srtv[2]},
          classTable = _ct,
          coverage = _cv))
    
    del _srtv, _ct, _cv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
