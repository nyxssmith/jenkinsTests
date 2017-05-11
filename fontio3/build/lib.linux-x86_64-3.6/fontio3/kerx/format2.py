#
# format2.py
#
# Copyright © 2011-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for class-based kerning (in 'kerx' tables).
"""

# System imports
import collections
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.kerx import classpair, coverage
from fontio3.opentype import classdef  # OT and AAT mixing?! Dogs and cats...
from fontio3.utilities import lookup
from fontio3.statetables import subtable_glyph_coverage_set

# -----------------------------------------------------------------------------

#
# Classes
#

class Format2(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing class kerning tables. These are dicts mapping
    ClassPair objects to FUnit kerning values. There are four attributes
    defined:
    
        leftClassDef    A ClassDef object for left-hand glyphs.
        
        rightClassDef   A ClassDef object for right-hand glyphs.
        
        coverage        A Coverage object.
        
        tupleIndex      If the coverage indicates variation data are present,
                        this will be a tuple index for variation kerning.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    ClassPair((1, 1)): -25
    ClassPair((1, 2)): -10
    ClassPair((2, 1)): 15
    Left-hand classes:
      xyz16: 1
      xyz26: 1
      xyz36: 2
    Right-hand classes:
      xyz10: 1
      xyz13: 1
      xyz16: 1
      xyz41: 2
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
        item_keyfollowsprotocol = True,
        item_pprintlabelpresort = True,
        item_scaledirectvalues = True,
        map_compactremovesfalses = True)
    
    attrSpec = dict(
        leftClassDef = dict(
            attr_followsprotocol = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Left-hand classes"),
        
        rightClassDef = dict(
            attr_followsprotocol = True,
            attr_initfunc = classdef.ClassDef,
            attr_label = "Right-hand classes"),
        
        coverage = dict(
            attr_followsprotocol = True,
            attr_label = "Header information"),
        
        tupleIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Variations tuple index",
            attr_showonlyiffuncobj = (lambda t,obj: obj.coverage.variation)),

        glyphCoverageSet = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue=True,
            attr_initfunc = subtable_glyph_coverage_set.SubtableGlyphCoverageSet,
            attr_label = 'Glyph Coverage Set'))

    attrSorted = ('leftClassDef', 'rightClassDef', 'coverage', 'tupleIndex',
                  'glyphCoverageSet')
    
    format = 2  # class constant
    
    #
    # Methods
    #
    
    def _keysCompacted(self):
        """
        Returns a new Format2 object where both the left-side and right-side
        key sets are made dense.
        
        >>> cd1 = classdef.ClassDef({15: 1, 25: 4, 35: 4})
        >>> cd2 = classdef.ClassDef({9: 1, 12: 5, 15: 11, 90: 5})
        >>> CP = classpair.ClassPair
        >>> f2 = Format2({
        ...     CP([1, 1]): 5,
        ...     CP([1, 5]): 6,
        ...     CP([1, 11]): 7,
        ...     CP([4, 1]): -5,
        ...     CP([4, 5]): -6,
        ...     CP([4, 11]): -7},
        ...     leftClassDef = cd1, rightClassDef = cd2)
        >>> f2._keysCompacted().pprint(keys=('leftClassDef', 'rightClassDef'))
        ClassPair((1, 1)): 5
        ClassPair((1, 2)): 6
        ClassPair((1, 3)): 7
        ClassPair((2, 1)): -5
        ClassPair((2, 2)): -6
        ClassPair((2, 3)): -7
        Left-hand classes:
          15: 1
          25: 2
          35: 2
        Right-hand classes:
          9: 1
          12: 2
          15: 3
          90: 2
        """
        
        copiedObj = self.__deepcopy__()
        CP = classpair.ClassPair
        it = ((0, copiedObj.leftClassDef), (1, copiedObj.rightClassDef))
        
        for keyIndex, whichCD in it:
            s = set(key[keyIndex] for key in copiedObj)
            s.discard(0)
            
            if s != set(range(1, max(s) + 1)):
                # need to pack
                s = sorted(s)
                remapDict = {n: i+1 for i, n in enumerate(s)}
                d = {}
                
                for key, value in copiedObj.items():
                    old = key[keyIndex]
                    new = remapDict[old]
                    
                    if old != new:
                        v = list(key)
                        v[keyIndex] = new
                        key = CP(v)
                    
                    d[key] = value
                
                copiedObj.clear()
                copiedObj.update(d)
                
                # now update the classdef (and remove unreferenced glyphs)
                d = {
                  g: remapDict[c]
                  for g, c in whichCD.items()
                  if c in remapDict}
                
                whichCD.clear()
                whichCD.update(d)
        
        return copiedObj
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format2 object to the specified
        LinkedWriter.
        
        >>> _testingValues[1].pprint()
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
          Horizontal
          With-stream
          No variation kerning
          Process forward
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0006 0000 001C  0000 0038 0000 0058 |...........8...X|
              10 | 0006 0004 0003 0008  0001 0004 000F 0006 |................|
              20 | 0019 0006 0023 000C  FFFF FFFF 0006 0004 |.....#..........|
              30 | 0004 0010 0002 0000  0009 0002 000C 0002 |................|
              40 | 000F 0002 0028 0004  FFFF FFFF 0000 0000 |.....(..........|
              50 | 0000 0000 FFE7 FFF6  0000 000F 0000      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self = self._keysCompacted()
        leftUniques = set(self.leftClassDef.values())
        rightUniques = set(self.rightClassDef.values())
        nRows = 1 + len(leftUniques)
        nCols = 1 + len(rightUniques)
        rowBytes = nCols * 2
        w.add("L", rowBytes)
        headerAdj = 12
        
        leftLookup = lookup.Lookup({
          i: j * rowBytes
          for i, j in self.leftClassDef.items()})
        
        rightLookup = lookup.Lookup({
          i: j * 2
          for i, j in self.rightClassDef.items()})
        
        leftStake = w.getNewStake()
        rightStake = w.getNewStake()
        arrayStake = w.getNewStake()
        
        w.addUnresolvedOffset("L", stakeValue, leftStake, offsetByteDelta=headerAdj)
        w.addUnresolvedOffset("L", stakeValue, rightStake, offsetByteDelta=headerAdj)
        w.addUnresolvedOffset("L", stakeValue, arrayStake, offsetByteDelta=headerAdj)
        
        leftLookup.buildBinary(w, stakeValue=leftStake, **kwArgs)
        rightLookup.buildBinary(w, stakeValue=rightStake, **kwArgs)
        v = [0] * (nRows * nCols)
        CP = classpair.ClassPair
        
        for leftIndex in leftUniques:
            for rightIndex in rightUniques:
                key = CP([leftIndex, rightIndex])
                
                if key in self:
                    v[leftIndex * nCols + rightIndex] = self[key]
        
        w.stakeCurrentWithValue(arrayStake)
        w.addGroup("h", v)
    
    @classmethod
    def fromformat0(cls, f0):
        """
        Creates and returns a new Format2 object derived from the specified
        Format0 object. This method can take a while to execute, as it needs to
        go through and build up deductions about the list of class members for
        both the left-hand and right-hand sides.
        
        >>> Format2.fromformat0(_f0tv()[1]).pprint()
        ClassPair((1, 1)): -25
        ClassPair((1, 3)): -30
        ClassPair((2, 2)): 12
        Left-hand classes:
          14: 1
          18: 2
        Right-hand classes:
          23: 1
          38: 2
          96: 3
        Header information:
          Horizontal
          With-stream
          No variation kerning
          Process forward
        """
        
        assert f0.format == 0
        allLefts = set(t[0] for t in f0)
        allRights = set(t[1] for t in f0)
        dLefts = collections.defaultdict(set)
        dRights = collections.defaultdict(set)
        
        for lg in allLefts:
            v = []
            
            for (lgTest, rg), value in f0.items():
                if lgTest == lg:
                    v.append((value, rg))
            
            t = tuple(sorted(v))
            dLefts[t].add(lg)
        
        for rg in allRights:
            v = []
            
            for (lg, rgTest), value in f0.items():
                if rgTest == rg:
                    v.append((value, lg))
            
            t = tuple(sorted(v))
            dRights[t].add(rg)
        
        leftCD = classdef.ClassDef()
        rightCD = classdef.ClassDef()
        
        for i, v in enumerate(sorted(sorted(s) for s in dLefts.values()), 1):
            for glyph in v:
                leftCD[glyph] = i
        
        for i, v in enumerate(sorted(sorted(s) for s in dRights.values()), 1):
            for glyph in v:
                rightCD[glyph] = i
        
        invLeft = utilities.invertDictFull(leftCD)
        invRight = utilities.invertDictFull(rightCD)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          coverage = f0.coverage,
          tupleIndex = f0.tupleIndex)
        
        CP = classpair.ClassPair
        
        for leftClass, vLeft in invLeft.items():
            for rightClass, vRight in invRight.items():
                key = (vLeft[0], vRight[0])
                
                if key in f0:
                    r[CP([leftClass, rightClass])] = f0[key]
        
        return r
    
    @classmethod
    def fromgposclasses(cls, pcObj, **kwArgs):
        """
        Creates and returns a new Format2 object from the specified PairClasses
        object. If there are any keys whose associated Values cannot be
        converted, they will be shown in a ValueError raised by this method.
        
        The following keyword arguments are used:
        
            coverage        A Coverage object. If not provided, a default
                            Coverage will be created and used.
            
            tupleIndex      The variations tuple index. Default is 0.
        """
        
        if 'coverage' not in kwArgs:
            kwArgs['coverage'] = coverage.Coverage()
        
        if 'tupleIndex' not in kwArgs:
            kwArgs['tupleIndex'] = 0
        
        couldNotProcess = set()
        horizontal = not kwArgs['coverage'].vertical
        CP = classpair.ClassPair
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = pcObj.classDef1,
          rightClassDef = pcObj.classDef2,
          **utilities.filterKWArgs(cls, kwArgs))
        
        for gposKey, gposValue in pcObj.items():
            fmt2Key = CP(gposKey)
            gposFirst = gposValue.first
            gposMask1 = (0 if gposFirst is None else gposFirst.getMask())
            gposSecond = gposValue.second
            gposMask2 = (0 if gposSecond is None else gposSecond.getMask())
            delta = 0
            
            # We only process effects that move the glyphs internally. That
            # means any Values that use anything other than an advance shift
            # on the first glyph or an origin shift on the second are not
            # processed, and their keys will be added to couldNotProcess.
            
            if horizontal:
                if gposMask1 == 4:  # xAdvance
                    delta += gposFirst.xAdvance
                
                elif gposMask1:
                    couldNotProcess.add(gposKey)
                    continue
                
                if gposMask2 == 1:  # xPlacement
                    delta += gposSecond.xPlacement
                
                elif gposMask2:
                    couldNotProcess.add(gposKey)
                    continue
            
            else:
                if gposMask1 == 8:  # yAdvance
                    delta += gposFirst.yAdvance
                
                elif gposMask1:
                    couldNotProcess.add(gposKey)
                    continue
                
                if gposMask2 == 2:  # yPlacement
                    delta += gposSecond.yPlacement
                
                elif gposMask2:
                    couldNotProcess.add(gposKey)
                    continue
            
            if delta:
                r[fmt2Key] = delta
        
        if couldNotProcess:
            v = sorted(couldNotProcess)
            raise ValueError("Could not process these GPOS keys: %s" % (v,))
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format2 object from the specified walker, doing
        source validation. The walker should start at the subtable header. The
        following keyword arguments are suggested (if they are not present, the
        default values for coverage and tupleIndex will be used, which won't
        usually be what's wanted):
        
            coverage    A Coverage object.
            logger      A logger to which messages will be posted.
            tupleIndex  The variations tuple index.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Format2.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.format2 - DEBUG - Walker has 94 remaining bytes.
        fvw.format2.left.lookup_aat - DEBUG - Walker has 78 remaining bytes.
        fvw.format2.left.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 76 remaining bytes.
        fvw.format2.right.lookup_aat - DEBUG - Walker has 50 remaining bytes.
        fvw.format2.right.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 48 remaining bytes.
        
        >>> fvb(s[:1], logger=logger)
        fvw.format2 - DEBUG - Walker has 1 remaining bytes.
        fvw.format2 - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.format2 - DEBUG - Walker has 93 remaining bytes.
        fvw.format2.left.lookup_aat - DEBUG - Walker has 77 remaining bytes.
        fvw.format2.left.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 75 remaining bytes.
        fvw.format2.right.lookup_aat - DEBUG - Walker has 49 remaining bytes.
        fvw.format2.right.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 47 remaining bytes.
        fvw.format2 - ERROR - The array is missing or incomplete.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('format2')
        else:
            logger = utilities.makeDoctestLogger('format2')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        kwArgs.pop('fontGlyphCount', None)
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        headerAdj = 12
        rowBytes = w.unpack("L")
        
        if not rowBytes:
            logger.warning((
              'V0605',
              (),
              "The rowBytes value is zero, so there is no table data."))
            
            return cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        nCols = rowBytes // 2
        leftOffset, rightOffset, arrayBase = w.unpack("3L")
        
        # Determine nRows, by finding the largest offset present in the left
        # class table.
        
        if leftOffset < headerAdj:
            logger.error((
              'V0607',
              (leftOffset,),
              "The leftOffset value %d is too small."))
            
            return None
        
        wLeft = w.subWalker(leftOffset - headerAdj)
        
        leftLookup = lookup.Lookup.fromvalidatedwalker(
          wLeft,
          logger = logger.getChild("left"),
          **kwArgs)
        
        if leftLookup is None:
            return None  # error will already have been logged
        
        bad = {i for i in leftLookup.values() if i % rowBytes}
        
        if bad:
            logger.error((
              'V0612',
              (sorted(bad),),
              "The following left-class values are not multiples of "
              "the rowBytes value: %s"))
            
            return None
        
        leftCD = classdef.ClassDef({
          i: j // rowBytes
          for i, j in leftLookup.items()})
        
        usedRows = set(leftCD.values())
        nRows = 1 + max(usedRows)
        unusedRows = (set(range(nRows)) - usedRows) - {0}
        
        if unusedRows:
            logger.warning((
              'Vxxxx',
              (sorted(unusedRows),),
              "The following rows are never referred to by any "
              "left-hand entry: %s"))
        
        if rightOffset < headerAdj:
            logger.error((
              'V0614',
              (rightOffset,),
              "The rightOffset value %d is too small."))
            
            return None
        
        wRight = w.subWalker(rightOffset - headerAdj)
        
        rightLookup = lookup.Lookup.fromvalidatedwalker(
          wRight,
          logger = logger.getChild("right"),
          **kwArgs)
        
        if rightLookup is None:
            return None  # error will already have been logged
        
        bad = {i for i in rightLookup.values() if i % 2}
        
        if bad:
            logger.error((
              'V0615',
              (sorted(bad),),
              "The following right-class values are not multiples of 2: %s"))
            
            return None
        
        rightCD = classdef.ClassDef({
          i: j // 2
          for i, j in rightLookup.items()})
        
        usedCols = set(rightCD.values())
        unusedCols = (set(range(nCols)) - usedCols) - {0}
        
        if unusedCols:
            logger.warning((
              'Vxxxx',
              (sorted(unusedCols),),
              "The following columns are never referred to by any "
              "right-hand entry: %s"))
        
        if arrayBase < headerAdj:
            logger.error((
              'V0609',
              (arrayBase,),
              "The arrayBase value %d is too small."))
            
            return None
        
        wArray = w.subWalker(arrayBase - headerAdj)
        
        if wArray.length() < 2 * nCols * nRows:
            logger.error((
              'V0610',
              (),
              "The array is missing or incomplete."))
            
            return None
        
        arrayData = wArray.group("h", nCols * nRows)
        leftUniques = set(leftLookup.values())
        rightUniques = set(rightLookup.values())
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        CP = classpair.ClassPair
        
        for uLeft in leftUniques:
            rowIndex = uLeft // rowBytes
            
            for uRight in rightUniques:
                dlt = arrayData[(uLeft + uRight) // 2]
                
                if dlt:
                    r[CP([rowIndex, uRight // 2])] = dlt
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format2 object from the specified walker, which
        should start at the subtable header. The following keyword arguments
        are suggested (if they are not present, the default values for coverage
        and tupleIndex will be used, which won't usually be what's wanted):
        
            coverage    A Coverage object.
            tupleIndex  The variations tuple index.
        
        >>> obj = _testingValues[1]
        >>> obj == Format2.frombytes(
        ...   obj.binaryString(),
        ...   coverage = coverage.Coverage())
        True
        """
        
        headerAdj = 12
        rowBytes = w.unpack("L")
        nCols = rowBytes // 2
        leftOffset, rightOffset, arrayBase = w.unpack("3L")
        
        # Determine nRows, by finding the largest offset present in the left
        # class table.
        
        wLeft = w.subWalker(leftOffset - headerAdj)
        leftLookup = lookup.Lookup.fromwalker(wLeft)
        
        leftCD = classdef.ClassDef({
          i: j // rowBytes
          for i, j in leftLookup.items()})
        
        nRows = 1 + max(leftCD.values())
        wRight = w.subWalker(rightOffset - headerAdj)
        rightLookup = lookup.Lookup.fromwalker(wRight)
        
        rightCD = classdef.ClassDef({
          i: j // 2
          for i, j in rightLookup.items()})
        
        wArray = w.subWalker(arrayBase - headerAdj)
        arrayData = wArray.group("h", nCols * nRows)
        leftUniques = set(leftLookup.values())
        rightUniques = set(rightLookup.values())
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        CP = classpair.ClassPair
        
        for uLeft in leftUniques:
            rowIndex = uLeft // rowBytes
            
            for uRight in rightUniques:
                dlt = arrayData[(uLeft + uRight) // 2]
                
                if dlt:
                    r[CP([rowIndex, uRight // 2])] = dlt
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    def _f0tv():
        from fontio3.kerx import format0
        
        return format0._testingValues
    
    _cptv = classpair._testingValues
    
    _testingValues = (
        Format2(),
        
        Format2(
            {_cptv[0]: -25, _cptv[1]: -10, _cptv[2]: 15},
            leftClassDef = classdef.ClassDef({15: 1, 25: 1, 35: 2}),
            rightClassDef = classdef.ClassDef({9: 1, 12: 1, 15: 1, 40: 2}),
            coverage = coverage.Coverage()))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
