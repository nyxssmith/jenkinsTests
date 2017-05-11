#
# format3.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for simplified class-based kerning (in 'kern' tables).
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.kern import classpair
from fontio3.opentype import classdef
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
          "Format 3 'kern' subtables are only supported for the Apple "
          "platform, and will be ignored elsewhere."))
    
    objDense = obj._keysCompacted()
    
    if objDense != obj:
        logger.info((
          'V0621',
          (),
          "The keys in the subtable were not dense, and have been "
          "compacted."))
        
        obj = objDense
    
    valueSet = set(obj.values()) | {0}
    
    if len(valueSet) > 256:
        logger.error((
          'V0622',
          (len(valueSet),),
          "There are %d kerning values, but format 3 only supports 256."))
        
        r = False
    
    leftCount = 1 + max(k[0] for k in obj)
    rightCount = 1 + max(k[1] for k in obj)
    
    if leftCount > 256 or rightCount > 256:
        logger.error((
          'V0623',
          (leftCount, rightCount),
          "The left class count is %d, and the right class count is %d. "
          "Both of these must be 256 or less for a format 3 subtable."))
        
        r = False
    
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

class Format3(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing a pair of class indices. Mostly similar to format 2,
    but with some limitations and a simpler binary representation.
    
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
    
    format = 3  # class constant
    
    #
    # Methods
    #
    
    def _keysCompacted(self):
        """
        Returns a new Format3 object where both the left-side and right-side
        key sets are made dense.
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
        Adds the binary data for the Format3 object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0029 0403 0300 0000  FFE7 FFF6 000F 0000 |.)..............|
              10 | 0000 0000 0000 0000  0000 0000 0001 0000 |................|
              20 | 0000 0000 0000 0001  0000 0000 0000 0000 |................|
              30 | 0002 0000 0000 0000  0000 0000 0000 0000 |................|
              40 | 0100 0001 0000 0100  0000 0000 0000 0000 |................|
              50 | 0000 0000 0000 0000  0000 0000 0000 0002 |................|
              60 | 0000 0000 0102 0003  0000                |..........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Make sure the keys are dense in both axes
        self = self._keysCompacted()  # I love Python!
        valueSet = set(self.values()) | {0}
        leftCount = 1 + max(k[0] for k in self)
        rightCount = 1 + max(k[1] for k in self)
        
        if len(valueSet) > 256:
            raise ValueError("Too many kerning values for format 3!")
        
        if leftCount > 256 or rightCount > 256:
            raise ValueError("Too many classes for format 3!")
        
        valuesSorted = [0] + sorted(valueSet - {0})
        valueToIndex = {value: i for i, value in enumerate(valuesSorted)}
        glyphCount = max(max(self.leftClassDef), max(self.rightClassDef)) + 1
        w.add("H3Bx", glyphCount, len(valueSet), leftCount, rightCount)
        w.addGroup("h", valuesSorted)
        
        w.addGroup(
          "B",
          (self.leftClassDef.get(g, 0) for g in range(glyphCount)))
        
        w.addGroup(
          "B",
          (self.rightClassDef.get(g, 0) for g in range(glyphCount)))
        
        it = (
          valueToIndex[self.get((L, R), 0)]
          for L in range(leftCount)
          for R in range(rightCount))
        
        w.addGroup("B", it)
        
        w.alignToByteMultiple(2)  # spec doesn't say this,
                                  # but I think it's implicit
    
    @classmethod
    def fromformat2(cls, format2Obj):
        """
        Creates a Format3 object from the specified Format2 object. Note this
        is simply a pass-through; checks on count limits are not made until the
        binary version is generated.
        """
        
        return cls(
          dict(format2Obj),
          **utilities.filterKWArgs(cls, format2Obj.__dict__))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format3 object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("format3_fvw")
        >>> fvb = Format3.fromvalidatedbytes
        >>> cv = _testingValues[1].coverage.__copy__()
        >>> d = {'logger': logger, 'coverage': cv, 'fontGlyphCount': 41}
        >>> obj = fvb(s, **d)
        format3_fvw.format3 - DEBUG - Walker has 106 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:3], **d)
        format3_fvw.format3 - DEBUG - Walker has 3 remaining bytes.
        format3_fvw.format3 - ERROR - Insufficient bytes.
        
        >>> d['fontGlyphCount'] = 100
        >>> fvb(s, **d)
        format3_fvw.format3 - DEBUG - Walker has 106 remaining bytes.
        format3_fvw.format3 - ERROR - The font has 100 glyphs, but the glyphCount field is 41.
        """
        
        fgc = kwArgs.pop('fontGlyphCount', 0x10000)
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("format3")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        glyphCount, kCount, lCount, rCount, flags = w.unpack("H4B")
        
        if glyphCount != fgc:
            logger.error((
              'V0617',
              (fgc, glyphCount),
              "The font has %d glyphs, but the glyphCount field is %d."))
            
            return None
        
        if not all([kCount, lCount, rCount]):
            logger.warning((
              'V0618',
              (),
              "One or more of the kernValueCount, leftClassCount, and "
              "rightClassCount is zero. The table is thus empty."))
            
            return cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        if flags:
            logger.warning((
              'V0619',
              (flags,),
              "The flags should be zero, but are %d."))
        
        if w.length() < (2 * (kCount + glyphCount)) + (lCount * rCount):
            logger.error((
              'V0620',
              (),
              "The arrays are missing or incomplete."))
            
            return None
        
        kValues = w.group("h", kCount)
        lClasses = w.group("B", glyphCount)
        rClasses = w.group("B", glyphCount)
        indices = w.group("B", lCount * rCount)
        
        # Note the assumption implicit in the following two lines of code: the
        # [0] element of the kernValue array has a numeric value of zero FUnits
        # (i.e. a non-kerning pair). This assumption is not documented in
        # Apple's 'kern' table documentation.
        
        leftCD = classdef.ClassDef(
          (g, c)
          for g, c in enumerate(lClasses)
          if c)
        
        rightCD = classdef.ClassDef(
          (g, c)
          for g, c in enumerate(rClasses)
          if c)
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        i = 0
        CP = classpair.ClassPair
        
        for rowIndex in range(lCount):
            for colIndex in range(rCount):
                value = kValues[indices[i]]
                
                if value:
                    r[CP([rowIndex, colIndex])] = value
                
                i += 1
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format3 object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Format3.frombytes(obj.binaryString(), coverage=obj.coverage)
        True
        """
        
        glyphCount, kCount, lCount, rCount = w.unpack("H3Bx")  # flags not used
        kValues = w.group("h", kCount)
        lClasses = w.group("B", glyphCount)
        rClasses = w.group("B", glyphCount)
        indices = w.group("B", lCount * rCount)
        
        # Note the assumption implicit in the following two lines of code: the
        # [0] element of the kernValue array has a numeric value of zero FUnits
        # (i.e. a non-kerning pair). This assumption is not documented in
        # Apple's 'kern' table documentation.
        
        leftCD = classdef.ClassDef(
          (g, c)
          for g, c in enumerate(lClasses)
          if c)
        
        rightCD = classdef.ClassDef(
          (g, c)
          for g, c in enumerate(rClasses)
          if c)
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        i = 0
        CP = classpair.ClassPair
        
        for rowIndex in range(lCount):
            for colIndex in range(rCount):
                value = kValues[indices[i]]
                
                if value:
                    r[CP([rowIndex, colIndex])] = value
                
                i += 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.kern import coverage_v1
    
    CP = classpair.ClassPair
    
    _testingValues = (
        Format3(),
        
        Format3({
            CP([1, 1]): -25,
            CP([1, 2]): -10,
            CP([2, 1]): 15},
            leftClassDef = classdef.ClassDef({15: 1, 25: 1, 35: 2}),
            rightClassDef = classdef.ClassDef({9: 1, 12: 1, 15: 1, 40: 2}),
            coverage = coverage_v1.Coverage()))
    
    del CP

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
