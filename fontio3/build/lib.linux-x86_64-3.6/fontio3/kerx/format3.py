#
# format3.py
#
# Copyright © 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for simplified class-based kerning (in 'kerx' tables).

Note that format 3 is not documented in the most recent version of Apple's
'kerx' documentation, while it does appear in the earlier version. I'm keeping
this module for the time being, although it may never be used in production
fonts.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta, seqmeta
from fontio3.opentype import classdef
from fontio3.statetables import subtable_glyph_coverage_set

# -----------------------------------------------------------------------------

#
# Classes
#

class ClassPair(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a pair of class indices. These are tuples, and are
    used as keys in Format3 objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        seq_fixedlength = 2)

# -----------------------------------------------------------------------------

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
        
        for keyIndex, whichCD in ((0, copiedObj.leftClassDef), (1, copiedObj.rightClassDef)):
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
                        key = ClassPair(v)
                    
                    d[key] = value
                
                copiedObj.clear()
                copiedObj.update(d)
                
                # now update the classdef (and remove unreferenced glyphs)
                d = {g: remapDict[c] for g, c in whichCD.items() if c in remapDict}
                whichCD.clear()
                whichCD.update(d)
        
        return copiedObj
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Format3 object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0029 0004 0003 0003  0000 0000 FFE7 FFF6 |.)..............|
              10 | 000F 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              30 | 0001 0000 0000 0000  0000 0000 0000 0000 |................|
              40 | 0000 0000 0001 0000  0000 0000 0000 0000 |................|
              50 | 0000 0000 0000 0000  0002 0000 0000 0000 |................|
              60 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              70 | 0000 0000 0000 0001  0000 0000 0001 0000 |................|
              80 | 0000 0001 0000 0000  0000 0000 0000 0000 |................|
              90 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              A0 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              B0 | 0000 0000 0002 0000  0000 0000 0000 0001 |................|
              C0 | 0002 0000 0003 0000                      |........        |
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
        
        if len(valueSet) > 65535:
            raise ValueError("Too many kerning values for format 3!")
        
        if leftCount > 65535 or rightCount > 65535:
            raise ValueError("Too many classes for format 3!")
        
        valuesSorted = [0] + sorted(valueSet - {0})
        valueToIndex = {value: i for i, value in enumerate(valuesSorted)}
        glyphCount = max(max(self.leftClassDef), max(self.rightClassDef)) + 1
        w.add("4H2x", glyphCount, len(valueSet), leftCount, rightCount)
        w.addGroup("h", valuesSorted)
        w.addGroup("H", (self.leftClassDef.get(g, 0) for g in range(glyphCount)))
        w.addGroup("H", (self.rightClassDef.get(g, 0) for g in range(glyphCount)))
        it = (valueToIndex[self.get((L, R), 0)] for L in range(leftCount) for R in range(rightCount))
        w.addGroup("H", it)
        w.alignToByteMultiple(4)
    
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
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Format3 object from the specified walker, which
        should start at the subtable header. The following keyword arguments
        are suggested (if they are not present, the default values for coverage
        and tupleIndex will be used, which won't usually be what's wanted):
        
            coverage    A Coverage object.
            tupleIndex  The variations tuple index.
        
        >>> obj = _testingValues[1]
        >>> obj == Format3.frombytes(obj.binaryString(), coverage=obj.coverage)
        True
        """
        
        glyphCount, kCount, lCount, rCount = w.unpack("4H2x")  # flags not used
        kValues = w.group("h", kCount)
        lClasses = w.group("H", glyphCount)
        rClasses = w.group("H", glyphCount)
        indices = w.group("H", lCount * rCount)
        
        # Note the assumption implicit in the following two lines of code: the
        # [0] element of the kernValue array has a numeric value of zero FUnits
        # (i.e. a non-kerning pair). This assumption is not documented in
        # Apple's 'kerx' table documentation.
        
        leftCD = classdef.ClassDef((g, c) for g, c in enumerate(lClasses) if c)
        rightCD = classdef.ClassDef((g, c) for g, c in enumerate(rClasses) if c)
        
        for delKey in {'leftClassDef', 'rightClassDef'}:
            kwArgs.pop(delKey, None)
        
        r = cls(
          {},
          leftClassDef = leftCD,
          rightClassDef = rightCD,
          **utilities.filterKWArgs(cls, kwArgs))
        
        i = 0
        
        for rowIndex in range(lCount):
            for colIndex in range(rCount):
                value = kValues[indices[i]]
                
                if value:
                    r[ClassPair([rowIndex, colIndex])] = value
                
                i += 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.kerx import coverage
    
    _testingValues = (
        Format3(),
        
        Format3({
            ClassPair([1, 1]): -25,
            ClassPair([1, 2]): -10,
            ClassPair([2, 1]): 15},
            leftClassDef = classdef.ClassDef({15: 1, 25: 1, 35: 2}),
            rightClassDef = classdef.ClassDef({9: 1, 12: 1, 15: 1, 40: 2}),
            coverage = coverage.Coverage()))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
