#
# format2.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for class-based kerning (in 'kern' tables).
"""

# System imports
import collections
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.kern import classpair, coverage_v1
from fontio3.opentype import classdef  # OT and AAT mixing?! Dogs and cats...
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    r = True
    
    if editor is None:
        return True
    
    if not kwArgs.get('forApple', False):
        logger.warning((
          'V0616',
          (),
          "Format 2 'kern' subtables are only supported for the Apple "
          "platform, and will be ignored elsewhere."))
    
    if editor.reallyHas(b'head'):
        upem = editor.head.unitsPerEm
    
    else:
        logger.warning((
          'V0603',
          (),
          "No 'head' table is present, so validation will assume a "
          "units-per-em value of 1000."))
        
        upem = 1000  # if there's no 'head' table, it's probably a CFF font
    
    f = functools.partial(valassist.isNumber_integer_signed, numBits=16)
    
    for key in sorted(obj):
        value = obj[key]
        itemLogger = logger.getChild("[%s]" % (key,))
        
        if not f(value, logger=itemLogger):
            r = False
        
        elif not value:
            itemLogger.warning((
              'V0141',
              (key,),
              "The kerning value for %s is zero."))
        
        elif abs(value) >= upem:
            itemLogger.warning((
              'V0604',
              (key, value),
              "The kerning value for %s (%s) seems excessive."))
        
    return r

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

class Format2(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing class kerning tables. These are dicts mapping
    ClassPair objects to FUnit kerning values. There are four attributes
    defined:
    
        leftClassDef    A ClassDef object for left-hand glyphs.
        
        rightClassDef   A ClassDef object for right-hand glyphs.
        
        coverage        A Coverage object, either version 0 or version 1.
        
        tupleIndex      If the coverage is version 1, this will be a tuple
                        index for variation kerning, if the coverage.variation
                        flag is set. Otherwise it is None (and it is always
                        None for version 0 coverages).
    
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
      Vertical text: False
      Cross-stream: False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_keyfollowsprotocol = True,
        item_pprintlabelpresort = True,
        item_scaledirectvalues = True,
        map_compactremovesfalses = True,
        map_validatefunc_partial = _validate)
    
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
            attr_label = "Variations tuple index",
            attr_showonlyiffuncobj = (
              lambda t, obj: (t is not None) and obj.coverage.variation),
            attr_validatefunc = _validate_tupleIndex))
    
    attrSorted = ('leftClassDef', 'rightClassDef', 'coverage', 'tupleIndex')
    
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
        
        for keyIndex, whichCD in (
          (0, copiedObj.leftClassDef),
          (1, copiedObj.rightClassDef)):
            
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
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0006 0022 0050 0010  0000 0000 0000 0000 |...".P..........|
              10 | FFE7 FFF6 0000 000F  0000 000F 0015 0016 |................|
              20 | 0010 0010 0010 0010  0010 0010 0010 0010 |................|
              30 | 0010 0016 0010 0010  0010 0010 0010 0010 |................|
              40 | 0010 0010 0010 001C  0009 0020 0002 0000 |........... ....|
              50 | 0000 0002 0000 0000  0002 0000 0000 0000 |................|
              60 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              70 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              80 | 0000 0000 0000 0000  0000 0004           |............    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Make sure the keys are dense in both axes
        self = self._keysCompacted()  # I love Python!
        nRows = 1 + len(set(self.leftClassDef.values()))
        nCols = 1 + len(set(self.rightClassDef.values()))
        rowBytes = nCols * 2
        headerAdj = (6 if self.coverage.format == 0 else 8)
        fullHeaderAdj = headerAdj + 8
        w.add("H", rowBytes)
        leftCDStake = w.getNewStake()
        rightCDStake = w.getNewStake()
        
        w.addUnresolvedOffset(
          "H",
          stakeValue,
          leftCDStake,
          offsetByteDelta = headerAdj)
        
        w.addUnresolvedOffset(
          "H",
          stakeValue,
          rightCDStake,
          offsetByteDelta = headerAdj)
        
        w.add("H", fullHeaderAdj)  # we always put the array first, so this
                                   # is constant, except for headerAdj
        
        # Put the array contents
        v = [0] * (nRows * nCols)
        
        for key, value in self.items():
            row, col = key
            v[row * nCols + col] = value
        
        w.addGroup("h", v)
        
        for cd, stake, toMul, toAdd in (
          (self.leftClassDef, leftCDStake, rowBytes, fullHeaderAdj),
          (self.rightClassDef, rightCDStake, 2, 0)):
            
            w.stakeCurrentWithValue(stake)
            minGlyph = min(cd)
            maxGlyphPlusOne = max(cd) + 1
            w.add("2H", minGlyph, maxGlyphPlusOne - minGlyph)
            
            for glyphIndex in range(minGlyph, maxGlyphPlusOne):
                value = cd.get(glyphIndex, 0)
                w.add("H", value * toMul + toAdd)
    
    @classmethod
    def fromformat0(cls, f0):
        """
        Creates and returns a new Format2 object derived from the specified
        Format0 object. This method can take a while to execute, as it needs to
        go through and build up deductions about the list of class members for
        both the left-hand and right-hand sides.
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
        
        if not f0.coverage.format:
            newCov = coverage_v1.Coverage(
              vertical = f0.coverage.vertical,
              crossStream = f0.coverage.crossStream)
        
        else:
            newCov = f0.coverage
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          coverage = newCov,
          tupleIndex = f0.tupleIndex)
        
        CP = classpair.ClassPair
        
        for leftClass, vLeft in invLeft.items():
            for rightClass, vRight in invRight.items():
                key = (vLeft[0], vRight[0])
                
                if key in f0:
                    r[CP([leftClass, rightClass])] = f0[key]
        
        return r
    
    @classmethod
    def fromformat3(cls, format3Obj):
        """
        Creates a Format2 object from the specified Format3 object. Conversions
        in this direction always work, since Format2 objects do not have the
        count limits that Format3 objects have.
        """
        
        return cls(
          dict(format3Obj),
          **utilities.filterKWArgs(cls, format3Obj.__dict__))
    
    @classmethod
    def fromgposclasses(cls, pcObj, **kwArgs):
        """
        Creates and returns a new Format2 object from the specified PairClasses
        object. If there are any keys whose associated Values cannot be
        converted, they will be shown in a ValueError raised by this method.
        
        The following keyword arguments are used:
        
            coverage        A version 1 Coverage object. If not provided, a
                            default Coverage will be created and used.
            
            tupleIndex      The variations tuple index. Default is 0.
        """
        
        if 'coverage' not in kwArgs:
            kwArgs['coverage'] = coverage_v1.Coverage()
        
        if 'tupleIndex' not in kwArgs:
            kwArgs['tupleIndex'] = 0
        
        couldNotProcess = set()
        horizontal = not kwArgs['coverage'].vertical
        kwArgs.pop('leftClassDef', None)
        kwArgs.pop('rightClassDef', None)
        
        r = cls(
          {},
          leftClassDef = pcObj.classDef1,
          rightClassDef = pcObj.classDef2,
          **kwArgs)
        
        for gposKey, gposValue in pcObj.items():
            fmt2Key = classpair.ClassPair(gposKey)
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
        Creates and returns a Format 2 object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("format2_fvw")
        >>> fvb = Format2.fromvalidatedbytes
        >>> cv = _testingValues[1].coverage.__copy__()
        >>> obj = fvb(s, logger=logger, coverage=cv)
        format2_fvw.format2 - DEBUG - Walker has 140 remaining bytes.
        format2_fvw.format2.right classes.classDef - DEBUG - Walker has 68 remaining bytes.
        format2_fvw.format2.right classes.classDef - DEBUG - ClassDef is format 1.
        format2_fvw.format2.right classes.classDef - DEBUG - First is 9, and count is 32
        format2_fvw.format2.right classes.classDef - DEBUG - Raw data are (2, 0, 0, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4)
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:3], logger=logger, coverage=cv)
        format2_fvw.format2 - DEBUG - Walker has 3 remaining bytes.
        format2_fvw.format2 - ERROR - Insufficient bytes.
        """
        
        kwArgs.pop('fontGlyphCount', None)
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format2")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        headerAdj = (6 if kwArgs['coverage'].format == 0 else 8)
        
        if w.length() < 8:
            logger.error(('V0001', (), "Insufficient bytes."))
            return None
        
        rowBytes, leftOffset, rightOffset, arrayBase = w.unpack("4H")
        
        if not rowBytes:
            logger.warning((
              'V0605',
              (),
              "The rowBytes value is zero, so there is no table data."))
            
            return cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        nCols = rowBytes // 2
        
        # Determine nRows, by finding the largest offset present in the left
        # class table.
        
        if leftOffset < headerAdj:
            logger.error((
              'V0607',
              (leftOffset,),
              "The leftOffset value %d is too small."))
            
            return None
        
        wLeft = w.subWalker(leftOffset - headerAdj)
        
        if wLeft.length() < 4:
            logger.error((
              'V0608',
              (),
              "The left-class table is missing or incomplete."))
            
            return None
        
        leftFirstGlyph, leftCount = wLeft.unpack("2H")
        
        if wLeft.length() < 2 * leftCount:
            logger.error((
              'V0608',
              (),
              "The left-class table is missing or incomplete."))
            
            return None
        
        vLeft = wLeft.group("H", leftCount)
        nRows = 1 + ((max(vLeft) - arrayBase) // rowBytes)
        
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
        
        arrayData = wArray.group("h" * nCols, nRows)
        
        # Make the two ClassDef objects
        
        leftCD = classdef.ClassDef()
        
        if any(n < arrayBase for n in vLeft):
            logger.error((
              'V0611',
              (),
              "At least one left class index is negative."))
            
            return None
        
        for n in vLeft:
            cIndex, modCheck = divmod(n - arrayBase, rowBytes)
            
            if modCheck:
                logger.error((
                  'V0612',
                  (),
                  "At least one left offset is not an even multiple of "
                  "the rowBytes past the array base."))
                
                return None
            
            if cIndex:
                leftCD[leftFirstGlyph] = cIndex
            
            leftFirstGlyph += 1
        
        if rightOffset < headerAdj:
            logger.error((
              'V0614',
              (rightOffset,),
              "The rightOffset value %d is too small."))
            
            return None
        
        wRight = w.subWalker(rightOffset - headerAdj)
        
        d = classdef.ClassDef.fromvalidatedwalker(
          wRight,
          logger = logger.getChild("right classes"),
          forceFormat = 1)
        
        if d is None:
            return None
        
        rightCD = classdef.ClassDef()
        
        for k, v in d.items():
            if v:
                cIndex, modCheck = divmod(v, 2)
                
                if modCheck:
                    logger.error((
                      'V0615',
                      (),
                      "At least one right offset is not an even multiple of "
                      "the rowBytes past the array base."))
                    
                    return None
                
                rightCD[k] = cIndex
        
        # At this point, arrayData is a list of nRows rows, each containing
        # nCols kerning values. Since we know nRows and nCols explicitly, all
        # we need to do at this point is walk the data setting the dict's
        # values directly.
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        CP = classpair.ClassPair
        
        for rowIndex, row in enumerate(arrayData):
            for colIndex, value in enumerate(row):
                if value:  # most will be zero, remember
                    r[CP([rowIndex, colIndex])] = value
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format2 object from the specified walker. The
        following keyword arguments are used:
        
            coverage    A Coverage object (for either version 0 or version 1
                        'kern' tables).
            
            tupleIndex  The tuple index (or 0) for a version 1 'kern' table, or
                        None for a version 0 'kern' table.
        
        >>> obj = _testingValues[1]
        >>> obj == Format2.frombytes(
        ...   obj.binaryString(),
        ...   coverage = coverage_v1.Coverage())
        True
        """
        
        headerAdj = (6 if kwArgs['coverage'].format == 0 else 8)
        rowBytes = w.unpack("H")
        nCols = rowBytes // 2
        leftOffset, rightOffset, arrayBase = w.unpack("3H")
        
        # Determine nRows, by finding the largest offset present in the left
        # class table.
        
        wLeft = w.subWalker(leftOffset - headerAdj)
        leftFirstGlyph, leftCount = wLeft.unpack("2H")
        vLeft = wLeft.group("H", leftCount)
        nRows = 1 + ((max(vLeft) - arrayBase) // rowBytes)
        wArray = w.subWalker(arrayBase - headerAdj)
        arrayData = wArray.group("h" * nCols, nRows)
        
        # Make the two ClassDef objects
        
        leftCD = classdef.ClassDef()
        
        for n in vLeft:
            cIndex = (n - arrayBase) // rowBytes
            
            if cIndex:
                leftCD[leftFirstGlyph] = cIndex
            
            leftFirstGlyph += 1
        
        wRight = w.subWalker(rightOffset - headerAdj)
        d = classdef.ClassDef.fromwalker(wRight, forceFormat=1)
        rightCD = classdef.ClassDef((k, v // 2) for k,v in d.items() if v)
        
        # At this point, arrayData is a list of nRows rows, each containing
        # nCols kerning values. Since we know nRows and nCols explicitly, all
        # we need to do at this point is walk the data setting the dict's
        # values directly.
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        CP = classpair.ClassPair
        
        for rowIndex, row in enumerate(arrayData):
            for colIndex, value in enumerate(row):
                if value:  # most will be zero, remember
                    r[CP([rowIndex, colIndex])] = value
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    CP = classpair.ClassPair
    
    _testingValues = (
        Format2(),
        
        Format2({
            CP([1, 1]): -25,
            CP([1, 2]): -10,
            CP([2, 1]): 15},
            leftClassDef = classdef.ClassDef({15: 1, 25: 1, 35: 2}),
            rightClassDef = classdef.ClassDef({9: 1, 12: 1, 15: 1, 40: 2}),
            coverage = coverage_v1.Coverage()))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
