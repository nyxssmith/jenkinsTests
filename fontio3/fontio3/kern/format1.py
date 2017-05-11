#
# format1.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for state-based kerning from an old-style 'kern' table.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, mapmeta

from fontio3.kern import (
  classtable,
  coverage_v1,
  entry,
  staterow,
  value,
  valuetuple)

from fontio3.statetables import namestash, stutils
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _combinedClasses(leftCD, rightCD, leftMap=None):
    """
    Given a pair of classDefs (or similar dict-like objects) which might have
    some glyphs in common, return a new ClassTable object. This is necessary
    in AAT because kerning state tables don't have separate left and right
    class maps.
    
    If a leftMap is provided, it will be filled with keys of leftCD class
    indices pointing to sets of class names involving those indices.
    
    >>> L = {6:1, 8:1, 10:2, 14:2, 16:2, 23:3, 29:3, 31:4, 32:4, 34:4, 35:4}
    >>> R = {7:1, 9:1, 10:2, 11:2, 12:2, 23:5, 24:4, 25:3, 29:5, 32:5}
    >>> M = {}
    >>> _combinedClasses(L, R, M).pprint()
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

def _validate_tupleIndex(obj, **kwArgs):
    if obj is None:
        return True
    
    if not valassist.isNumber_integer_unsigned(obj, numBits=16, **kwArgs):
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Format1(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire state-based kerning subtables for old-style
    'kern' tables. These are dicts mapping state name strings to StateRow
    objects. The following attributes are defined:
    
        classTable      A ClassTable object, mapping glyphs to class strings.
        
        coverage        A Coverage object.
        
        tupleIndex      If the coverage indicates variation data are present,
                        this will be a tuple index for variation kerning.
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
            attr_validatefunc = _validate_tupleIndex),
        
        classTable = dict(
            attr_followsprotocol = True,
            attr_initfunc = classtable.ClassTable,
            attr_label = "Class table"))
    
    format = 1  # class constant
    
    #
    # Methods
    #
    
    @staticmethod
    def _findNumStates(w, stateArrayBaseOffset, numClasses):
        """
        """
        
        v = w.unpackRest("2H")
        maxOffset = max(offset for offset, flags in v) - stateArrayBaseOffset
        return 1 + (maxOffset // numClasses)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format1 object to the specified writer.
        The following keyword arguments are supported:
        
            stakeValue      If specified, a value that will stake the start of
                            the subtable.
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
        assert len(classNames) < 256
        w.add("H", len(classNames))
        ctStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, ctStake)
        saStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, saStake)
        etStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, etStake)
        vtStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, vtStake)
        kwArgs.pop('neededAlignment', None)
        kwArgs.pop('classDict', None)
        nsObj.buildBinary(w, neededAlignment=2, **kwArgs)
        
        self.classTable.buildBinary(
          w,
          stakeValue = ctStake,
          classDict = revClassMap,
          **kwArgs)
        
        rowStakes = {s: w.getNewStake() for s in stateNames}
        entryPool = {}
        w.stakeCurrentWithValue(saStake)
        
        for key in stateNames:
            self[key].buildBinary(
              w,
              classNameList = classNames,
              entryPool = entryPool,
              stakeValue = rowStakes[key])
        
        w.alignToByteMultiple(2)
        w.stakeCurrentWithValue(etStake)
        valueTuplePool = {}  # immut(ValueTuple) -> (stake, ValueTuple)
        it = sorted(entryPool.values(), key=operator.itemgetter(0))
        
        for index, obj in it:
            obj.buildBinary(
              w,
              stateArrayStakes = rowStakes,
              stateTableBase = stakeValue,
              valueTuplePool = valueTuplePool)
        
        w.stakeCurrentWithValue(vtStake)
        ics = (False if self.coverage is None else self.coverage.crossStream)
        
        for stake, obj in valueTuplePool.values():
            obj.buildBinary(
              w,
              isCrossStream = self.coverage.crossStream,
              stakeValue = stake)
    
    @classmethod
    def fromformat2(cls, fmt2Obj, **kwArgs):
        """
        Creates and returns a new Format1 object from the specified Format2
        object.
        
        >>> obj = _f2()
        >>> obj.pprint()
        ClassPair((1, 1)): -25
        ClassPair((1, 2)): -10
        ClassPair((2, 1)): 15
        Left-hand classes:
          15: 1
          25: 1
          35: 2
        Right-hand classes:
          9: 1
          12: 1
          15: 1
          40: 2
        Header information:
          Vertical text: False
          Cross-stream: False
        >>> Format1.fromformat2(obj).pprint(onlySignificant=True)
        State 'Start of text':
          Class 'class_LR_1_1':
            Go to state 'Saw_L_1'
          Class 'class_L_1':
            Go to state 'Saw_L_1'
          Class 'class_L_2':
            Go to state 'Saw_L_2'
        State 'Start of line':
          Class 'class_LR_1_1':
            Go to state 'Saw_L_1'
          Class 'class_L_1':
            Go to state 'Saw_L_1'
          Class 'class_L_2':
            Go to state 'Saw_L_2'
        State 'Saw_L_1':
          Class 'class_LR_1_1':
            Push this glyph, then go to state 'Saw_L_1' after performing these actions:
              Pop #1:
                Value: -25
          Class 'class_L_1':
            Go to state 'Saw_L_1'
          Class 'class_L_2':
            Go to state 'Saw_L_2'
          Class 'class_R_1':
            Push this glyph, then go to state 'Start of text' after performing these actions:
              Pop #1:
                Value: -25
          Class 'class_R_2':
            Push this glyph, then go to state 'Start of text' after performing these actions:
              Pop #1:
                Value: -10
        State 'Saw_L_2':
          Class 'class_LR_1_1':
            Push this glyph, then go to state 'Saw_L_1' after performing these actions:
              Pop #1:
                Value: 15
          Class 'class_L_1':
            Go to state 'Saw_L_1'
          Class 'class_L_2':
            Go to state 'Saw_L_2'
          Class 'class_R_1':
            Push this glyph, then go to state 'Start of text' after performing these actions:
              Pop #1:
                Value: 15
        Class table:
          9: class_R_1
          12: class_R_1
          15: class_LR_1_1
          25: class_L_1
          35: class_L_2
          40: class_R_2
        Header information:
          Vertical text: False
          Cross-stream: False
        Variations tuple index: 0
        """
        
        if 'coverage' not in kwArgs:
            kwArgs['coverage'] = coverage_v1.Coverage()
        
        if 'tupleIndex' not in kwArgs:
            kwArgs['tupleIndex'] = 0
        
        leftMap = {}
        
        unionCT = _combinedClasses(
          fmt2Obj.leftClassDef,
          fmt2Obj.rightClassDef,
          leftMap)
        
        kwArgs.pop('classTable', None)
        r = cls({}, classTable=unionCT, **utilities.filterKWArgs(cls, kwArgs))
        addedClassNames = tuple(sorted(set(unionCT.values())))
        classNames = namestash.fixedClassNames + addedClassNames
        
        addedStateNames = tuple(
          "Saw_L_%d" % (n,)
          for n in sorted(set(fmt2Obj.leftClassDef.values())))
        
        stateNames = namestash.fixedStateNames + addedStateNames
        defaultEntry = entry.Entry()
        
        for stateName in stateNames:
            newRow = staterow.StateRow()
            
            for className in classNames:
                newRow[className] = defaultEntry
            
            r[stateName] = newRow
        
        for cp, dist in fmt2Obj.items():
            if not dist:
                continue
            
            # For the SOT and SOL states, each cell belonging to either
            # class_L_cp[0] or class_LR_cp[0]* gets a link to the Saw_L_cp[0]
            # state.
            
            f2LeftClass, f2RightClass = cp
            firstCell = entry.Entry(newState="Saw_L_%d" % (f2LeftClass,))
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
                    val = valuetuple.ValueTuple([value.Value(dist)])
                    
                    if className == match3:
                        r[sn][className] = entry.Entry(
                          newState = "Start of text",
                          push = True,
                          values = val)
                    
                    else:
                        r[sn][className] = entry.Entry(
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
                
                r[stateName][className] = entry.Entry(
                  newState = "Saw_L_%s" % (className.split('_')[2],))
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format1 object from the specified walker,
        doing source validation, which must start at the beginning (numClasses)
        of the state table. The following keyword arguments are supported:
        
            coverage    A Coverage object. This is required.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format1")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 10:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        stBaseOffset = w.getOffset()
        t = w.unpack("5H")
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
        
        if wETCopy.length() < 4:
            logger.error((
              'V0636',
              (),
              "The entry table is missing or incomplete."))
            
            return None
        
        v = wETCopy.unpackRest("2H")
        maxOffset = max(offset for offset, flags in v) - oSA
        numStates = 1 + (maxOffset // numClasses)
        
        nsObj = namestash.NameStash.readormake(w, t[1:], numStates, numClasses)
        stateNames = nsObj.allStateNames()
        classNames = nsObj.allClassNames()
        fgc = kwArgs.pop('fontGlyphCount')
        
        classTable = classtable.ClassTable.fromvalidatedwalker(
          wCT,
          classNames = classNames,
          logger = logger,
          fontGlyphCount = fgc)
        
        if classTable is None:
            return None
        
        kwArgs.pop('classTable', None)
        
        r = cls(
          {},
          classTable = classTable,
          **utilities.filterKWArgs(cls, kwArgs))
        
        fvw = staterow.StateRow.fromvalidatedwalker
        cover = kwArgs['coverage']
        entryPool = {}
        valueTuplePool = {}
        
        delKeys = {
          'classNames',
          'entryPool',
          'isCrossStream',
          'logger',
          'stateArrayBaseOffset',
          'stateNames',
          'valueTuplePool',
          'wEntryTable',
          'wSubtable'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        for stateName in stateNames:
            itemLogger = logger.getChild("state '%s'" % (stateName,))
            
            obj = fvw(
              wSA,
              classNames = classNames,
              entryPool = entryPool,
              isCrossStream = cover.crossStream,
              logger = itemLogger,
              stateArrayBaseOffset = oSA,
              stateNames = stateNames,
              valueTuplePool = valueTuplePool,
              wEntryTable = wET,
              wSubtable = w,
              **kwArgs)
            
            if obj is None:
                return None
            
            r[stateName] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Format1 object from the specified walker,
        which must start at the beginning (numClasses) of the state table. The
        following keyword arguments are supported:
        
            coverage    A Coverage object. This is required.
        """
        
        numClasses, oCT, oSA, oET, oVT = w.unpack("5H")
        
        wCT, wSA, wET, wVT = stutils.offsetsToSubWalkers(
          w.subWalker(0),  # can't just use w; it gets reset
          oCT,
          oSA,
          oET,
          oVT)
        
        numStates = cls._findNumStates(
          wET.subWalker(0, relative=True),
          oSA,
          numClasses)
        
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
        
        fw = staterow.StateRow.fromwalker
        cover = kwArgs['coverage']
        entryPool = {}
        valueTuplePool = {}
        
        delKeys = {
          'classNames',
          'entryPool',
          'isCrossStream',
          'stateArrayBaseOffset',
          'stateNames',
          'valueTuplePool',
          'wEntryTable',
          'wSubtable'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        for stateName in stateNames:
            r[stateName] = fw(
              wSA,
              classNames = classNames,
              entryPool = entryPool,
              isCrossStream = cover.crossStream,
              stateArrayBaseOffset = oSA,
              stateNames = stateNames,
              valueTuplePool = valueTuplePool,
              wEntryTable = wET,
              wSubtable = w,
              **kwArgs)
        
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
    def _f2():
        from fontio3.kern import format2
        
        return format2._testingValues[1]

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
