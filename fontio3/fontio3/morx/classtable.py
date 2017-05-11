#
# classtable.py
#
# Copyright © 2012-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from glyph to class for 'morx' tables (specifically the
state table portions; noncontextual mappings are handled separately).
"""

# System imports
import logging
import operator
import re

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.utilities import bsh, lookup

# -----------------------------------------------------------------------------

#
# Constants
#

PAT_UNIQUE = re.compile(r"(.*)_unique (\d+)$")

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    allValues = set(obj.values())
    
    if (not obj) or (allValues == {"Out of bounds"}):
        logger.warning((
          'V0717',
          (),
          "Class table empty or only maps to 'Out of bounds'."))
    
    elif "Out of bounds" in allValues:
        logger.warning((
          'V0718',
          (),
          "Class table has explicit entries mapping to 'Out of bounds'; "
          "since this is the default, these entries should be removed "
          "to save space."))
    
    if allValues & {"End of text", "Deleted glyph", "End of line"}:
        logger.warning((
          'V0719',
          (),
          "Class table has one or more explicit mappings to the fixed "
          "classes 'End of text', 'Deleted glyph', or 'End of line'. "
          "This is not usual practice."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class ClassTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing mappings from glyph index to class name string.
    
    >>> _testingValues[1].pprint()
    0: Letter
    1: Digit
    
    >>> _testingValues[2].pprint()
    0: Letter
    1: Digit
    23: Punctuation
    24: Punctuation
    25: Punctuation
    26: Punctuation
    27: Punctuation
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        _preferredFormat = dict())
    
    attrSorted = ()
    
    #
    # Methods
    #
    
    def _merged_checkCollisions(self, other):
        """
        Returns True if there are key overlaps in self and other, AND some
        names in other in this key overlap set have associated glyph sets that
        are not in this overlap.
        
        >>> c1 = ClassTable({5: 'a', 10: 'a', 14: 'b', 19: 'c'})
        >>> c1._merged_checkCollisions({80: 'z'})
        False
        >>> c1._merged_checkCollisions({10: 'x', 30: 'z'})
        False
        >>> c1._merged_checkCollisions({10: 'x', 30: 'x'})
        True
        """
        
        commonKeys = set(self) & set(other)
        
        if not commonKeys:
            return False
        
        otherNamesToGlyphSets = utilities.invertDictFull(other, asSets=True)
        
        for g in commonKeys:
            s = otherNamesToGlyphSets[other[g]]
            
            if s - commonKeys:
                return True
        
        return False
    
    def _merged_cleanUp(self, *dicts):
        revDict = utilities.invertDictFull(self, asSets=True)
        renames = []
        
        for oldName, gSet in revDict.items():
            if len(gSet) > 1:
                continue
            
            m = PAT_UNIQUE.match(oldName)
            
            if m:
                newName = m.group(1)
                
                if newName.endswith('_'):
                    newName = newName[:-1]
                
                if '_' in newName:
                    sv = newName.split('_')
                    
                    if len(sv) == 2 and sv[0] == sv[1]:
                        newName = sv[0]
                
                if newName not in revDict:
                    renames.append((oldName, newName))
        
        for oldName, newName in renames:
            for g in revDict[oldName]:
                self[g] = newName
            
            for d in dicts:
                for s1, s2 in d.items():
                    if s2 == oldName:
                        d[s1] = newName
    
    @staticmethod
    def _merged_nextUnique(*dicts):
        nextUnique = 1
        
        for d in dicts:
            valueSet = set(d.values())
            
            for s in valueSet:
                m = PAT_UNIQUE.match(s)
                
                if m:
                    nextUnique = max(nextUnique, int(m.group(2)) + 1)
        
        return nextUnique
    
    def _merged_uniquifyValues(self, other, oldToNew):
        """
        Returns a dict matching other, but any values in other that also occur
        in self will be changed to special "unique" values.
        
        >>> ct = ClassTable({4: 'a', 6: 'b'})
        >>> otn = {}
        >>> ct._merged_uniquifyValues({19: 'r'}, otn)
        {19: 'r'}
        >>> otn
        {}
        
        >>> ct._merged_uniquifyValues({19: 'b'}, otn)
        {19: 'b_unique 1'}
        >>> otn
        {'b': 'b_unique 1'}
        
        >>> otn.clear()
        >>> ct._merged_uniquifyValues({19: 'b_unique 1'}, otn)
        {19: 'b_unique 1'}
        >>> otn
        {}
        
        >>> otn.clear()
        >>> ct[8] = 'k_unique 4'
        >>> ct._merged_uniquifyValues({19: 'k_unique 1'}, otn)
        {19: 'k_unique 1'}
        >>> otn
        {}
        
        >>> otn.clear()
        >>> ct._merged_uniquifyValues({19: 'k_unique 4'}, otn)
        {19: 'k_unique 5'}
        >>> otn
        {'k_unique 4': 'k_unique 5'}
        """
        
        selfValueSet = set(self.values())
        nextUnique = self._merged_nextUnique(self)
        r = {}
        pool = {}
        it = sorted(other.items(), key=operator.itemgetter(0))
        
        for key, value in it:
            if value in selfValueSet:
                if value not in pool:
                    origValue = value
                    m = PAT_UNIQUE.match(value)
                    
                    if m:
                        value = m.group(1)
                    
                    pool.setdefault(
                      value,
                      "%s_unique %d" % (value, nextUnique))
                    
                    nextUnique += 1
                
                oldToNew[origValue] = pool[value]
                value = pool[value]
            
            r[key] = value
        
        return r
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ClassTable object to the specified writer.
        The following keyword arguments are supported:
        
            classDict   A dict mapping class names to their corresponding
                        numeric values. This is required.
        
        >>> cd = dict(zip(_testClassNames, range(7)))
        >>> h = utilities.hexdump
        
        Format 0:
        >>> obj = _testingValues[1]
        >>> h(obj.binaryString(classDict=cd))
               0 | 0000 0004 0005                           |......          |
        
        Format 2:
        >>> obj = _testingValues[2]
        >>> h(obj.binaryString(classDict=cd))
               0 | 0002 0006 0003 000C  0001 0006 0000 0000 |................|
              10 | 0004 0001 0001 0005  001B 0017 0006 FFFF |................|
              20 | FFFF FFFF                                |....            |
        
        Format 4:
        >>> obj = _testingValues[3]
        >>> h(obj.binaryString(classDict=cd))
               0 | 0004 0006 0002 000C  0001 0000 0045 0032 |.............E.2|
              10 | 001E 00A9 0096 0046  FFFF FFFF FFFF 0004 |.......F........|
              20 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
              30 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
              40 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
              50 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
              60 | 0005 0004 0005 0004  0005 0004 0005      |..............  |
        
        Format 6:
        >>> obj = _testingValues[4]
        >>> h(obj.binaryString(classDict=cd))
               0 | 0006 0004 0002 0008  0001 0000 000C 0004 |................|
              10 | 005A 0005 FFFF FFFF                      |.Z......        |
        
        Format 8:
        >>> obj = _testingValues[5]
        >>> h(obj.binaryString(classDict=cd))
               0 | 0008 000C 0001 0004                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self:
            if self._preferredFormat is not None:
                kwArgs['preferredFormat'] = self._preferredFormat
            
            classDict = kwArgs['classDict']
            d = {glyph: classDict[name] for glyph, name in self.items()}
            w.addString(lookup.bestFromDict(d, **kwArgs))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable from the specified walker, doing
        source validation. Note that in all cases, class indices less than 4
        will be skipped, since no glyph explicitly maps to any of the fixed
        classes.
        
        The following keyword arguments are supported:
        
            classNames      A sequence of all class names. This is required.
            
            logger          A logger to which messages will be logged.
        
        >>> logger = utilities.makeDoctestLogger("classtable_fvw")
        >>> fvb = ClassTable.fromvalidatedbytes
        >>> cn = _testClassNames
        >>> cd = dict(zip(cn, range(7)))
        >>> s = _testingValues[2].binaryString(classDict=cd)
        >>> obj = fvb(s, classNames=cn, logger=logger)
        classtable_fvw.clstable - DEBUG - Walker has 36 remaining bytes.
        classtable_fvw.clstable.binsearch.binsrch header - DEBUG - Walker has 34 remaining bytes.
        """
        
        classNames = kwArgs.pop('classNames', None)
        assert classNames
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("clstable")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        r = cls()
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format not in {0, 2, 4, 6, 8}:
            logger.error((
              'V0701',
              (format,),
              "The classTable format (%d) is not recognized."))
            
            return None
        
        if format == 0:
            v = w.unpackRest("H")
            
            if not v:
                logger.warning((
                  'V0702',
                  (),
                  "The format 0 classTable has no actual data."))
                
                return r
            
            badIndices = {i for i, n in enumerate(v) if n >= len(classNames)}
            
            if badIndices:
                logger.error((
                  'V0703',
                  (sorted(badIndices),),
                  "The following glyph indices map to class index values "
                  "that are out of range: %s"))
                
                return None
            
            for glyph, classIndex in enumerate(v):
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        elif format == 2:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 6:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 6 in the binary search "
                  "header for a format 2 class table, but got %d instead."))
                
                return None
            
            if w.length() < 6 * b.nUnits:
                logger.error((
                  'V0704',
                  (),
                  "The data for the format 2 classTable are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("3H", b.nUnits)
            badIndices = {(t[1], t[0]) for t in v if t[2] >= len(classNames)}
            
            if badIndices:
                logger.error((
                  'V0703',
                  (sorted(badIndices),),
                  "The following glyph ranges map to class index values "
                  "that are out of range: %s"))
                
                return None
            
            badIndices = {t[:2] for t in v if t[1] > t[0]}
            
            if badIndices:
                logger.error((
                  'V0705',
                  (sorted(badIndices),),
                  "The following glyph ranges have their start and end "
                  "glyph indices swapped: %s"))
                
                return None
            
            if list(v) != sorted(v, key=operator.itemgetter(1)):
                logger.error((
                  'V0715',
                  (),
                  "The segments are not sorted by first glyph."))
                
                return None
            
            countByRange = sum(t[0] - t[1] + 1 for t in v)
            countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
            
            if countByRange != countBySet:
                logger.error((
                  'V0716',
                  (),
                  "The segments have overlaps in glyph coverage."))
                
                return None
            
            for last, first, classIndex in v:
                if classIndex >= 4:
                    for glyph in range(first, last + 1):
                        r[glyph] = classNames[classIndex]
        
        elif format == 4:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 6:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 6 in the binary search "
                  "header for a format 4 class table, but got %d instead."))
                
                return None
            
            if w.length() < 6 * b.nUnits:
                logger.error((
                  'V0706',
                  (),
                  "The data for the format 4 classTable are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("3H", b.nUnits)
            
            if v and (v[-1][:2] == (0xFFFF, 0xFFFF)):
                v = v[:-1]
            
            badOrder = sorted(t[:2] for t in v if t[1] > t[0])
            
            if badOrder:
                logger.error((
                  'V0705',
                  (sorted(badOrder),),
                  "The following glyph ranges have their start and end "
                  "glyph indices swapped: %s"))
                
                return None
            
            if list(v) != sorted(v, key=operator.itemgetter(1)):
                logger.error((
                  'V0715',
                  (),
                  "The segments are not sorted by first glyph."))
                
                return None
            
            countByRange = sum(t[0] - t[1] + 1 for t in v)
            countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
            
            if countByRange != countBySet:
                logger.error((
                  'V0716',
                  (),
                  "The segments have overlaps in glyph coverage."))
                
                return None
            
            badIndices = set()
            
            for last, first, offset in v:
                count = last - first + 1
                
                if offset < 12 + 6 * len(v):
                    logger.error((
                      'V0708',
                      (first, last, offset),
                      "The segment offset for the (%d, %d) group is %d, "
                      "which places it within the segment index data. This "
                      "is probably incorrect."))
                    
                    return None
                
                wSub = w.subWalker(offset)
                
                if wSub.length() < 2 * count:
                    logger.error((
                      'V0707',
                      (),
                      "The segment data at the specified offset are missing "
                      "or incomplete."))
                    
                    return None
                
                vSub = wSub.group("H", count)
                
                for glyph, classIndex in zip(range(first, last + 1), vSub):
                    if classIndex >= len(classNames):
                        badIndices.add((first, last))
                    
                    elif classIndex >= 4:
                        r[glyph] = classNames[classIndex]
            
            if badIndices:
                logger.error((
                  'V0703',
                  (sorted(badIndices),),
                  "The following glyph ranges map to class index values "
                  "that are out of range: %s"))
                
                return None
        
        elif format == 6:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 4:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 4 in the binary search "
                  "header for a format 6 class table, but got %d instead."))
                
                return None
            
            if w.length() < 4 * b.nUnits:
                logger.error((
                  'V0710',
                  (),
                  "The data for the format 6 classTable are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("2H", b.nUnits)
            badIndices = {t[0] for t in v if t[1] >= len(classNames)}
            
            if badIndices:
                logger.error((
                  'V0703',
                  (sorted(badIndices),),
                  "The following glyphs map to class index values "
                  "that are out of range: %s"))
                
                return None
            
            if len({t[0] for t in v}) != len(v):
                logger.error((
                  'V0713',
                  (),
                  "There are duplicate glyphs in the format 6 data."))
                
                return None
            
            elif list(v) != sorted(v):
                logger.error((
                  'V0714',
                  (),
                  "The glyphs are not sorted."))
                
                return None
        
            for glyph, classIndex in v:
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        else:  # safe, since full check was made above
            if w.length() < 4:
                logger.error((
                  'V0711',
                  (),
                  "The format 8 header is missing or incomplete."))
                
                return None
            
            first, count = w.unpack("2H")
            
            if w.length() < 2 * count:
                logger.error((
                  'V0712',
                  (),
                  "The format 8 data is missing or incomplete."))
                
                return None
            
            v = w.group("H", count)
            
            badIndices = {
              i + first
              for i, n in enumerate(v)
              if n >= len(classNames)}
            
            if badIndices:
                logger.error((
                  'V0703',
                  (sorted(badIndices),),
                  "The following glyphs map to class index values "
                  "that are out of range: %s"))
                
                return None
            
            for glyph, classIndex in enumerate(v, start=first):
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ClassTable from the specified walker. Note
        that in all cases, class indices less than 4 will be skipped, since no
        glyph explicitly maps to any of the fixed classes.
        
        The following keyword arguments are supported:
        
            classNames      A sequence of all class names. This is required.
        
        >>> fb = ClassTable.frombytes
        >>> fh = utilities.fromhex
        >>> cn = _testClassNames
        >>> cd = dict(zip(_testClassNames, range(7)))
        
        >>> for obj in _testingValues[1:6]:
        ...     print(obj == fb(obj.binaryString(classDict=cd), classNames=cn))
        True
        True
        True
        True
        True
        """
        
        classNames = kwArgs.pop('classNames')
        assert classNames is not None
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        format = w.unpack("H")
        
        if format == 0:
            for glyph, classIndex in enumerate(w.unpackRest("H")):
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        elif format == 2:
            for last, first, classIndex in w.group("3H", w.unpack("2xH6x")):
                if classIndex >= 4:
                    for glyph in range(first, last + 1):
                        r[glyph] = classNames[classIndex]
        
        elif format == 4:
            for last, first, offset in w.group("3H", w.unpack("2xH6x")):
                if last == first == 0xFFFF:
                    continue
                
                wSub = w.subWalker(offset)
                v = wSub.group("H", last - first + 1)
                
                for glyph, classIndex in zip(range(first, last + 1), v):
                    if classIndex >= 4:
                        r[glyph] = classNames[classIndex]
        
        elif format == 6:
            for glyph, classIndex in w.group("2H", w.unpack("2xH6x")):
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        elif format == 8:
            first, count = w.unpack("2H")
            it = enumerate(w.group("H", count), start=first)
            
            for glyph, classIndex in it:
                if classIndex >= 4:
                    r[glyph] = classNames[classIndex]
        
        else:
            raise ValueError("Unknown format: 0x%04X" % (format,))
        
        return r
    
    def merged(self, other, **kwArgs):
        """
        Return a ClassTable representing a merger between self and other. This
        involves custom logic to deal with glyphs that appear in both maps; see
        the unittests for examples.
        
        A ValueError will be raised if (1) there are duplicate keys in other
        and self; and (2) at least one of these duplicate keys maps (again, in
        other) to a class name that occurs elsewhere in other associated with
        glyph indices that are not duplicated in self.
        
        The following keyword arguments are used (note that for ClassTable
        objects the normal conflictPreferOther and replaceWhole keywords are
        not supported):
        
            otherOldToNew       If specified, should be a dict, which will be
                                filled with mappings from old class names in
                                other to their new values (or their old values,
                                if they don't need to change).
        
            selfOldToNew        If specified, should be a dict, which will be
                                filled with mappings from old class names in
                                self to their new values (or their old values,
                                if they don't need to change).
        """
        
        if self._merged_checkCollisions(other):
            raise ValueError("These cannot be merged!")
        
        otherOriginals = set(other.values())
        selfOriginals = set(self.values())
        r = self.__copy__()
        otherOldToNew = kwArgs.pop('otherOldToNew', {})
        otherOldToNew.update({s: s for s in other.values()})
        selfOldToNew = kwArgs.pop('selfOldToNew', {})
        selfOldToNew.update({s: s for s in self.values()})
        other = self._merged_uniquifyValues(other, otherOldToNew)
        nextUnique = self._merged_nextUnique(self, other)
        pool = {}  # className -> new className for collisions only
        it = sorted(other.items(), key=operator.itemgetter(0))
        
        for glyphIndex, className in it:
            if glyphIndex not in r:
                r[glyphIndex] = className
                continue
            
            if className not in pool:
                selfName = r[glyphIndex]
                m = PAT_UNIQUE.match(selfName)
                
                if m:
                    selfName = m.group(1)
                
                m = PAT_UNIQUE.match(className)
                
                if m:
                    className = m.group(1)
                
                t = (selfName, className, nextUnique)
                s = pool[className] = "%s_%s_unique %d" % t
                nextUnique += 1
                
                selfOldToNew[r[glyphIndex]] = s
                otherOldToNew[className] = s
                
                for g in r:
                    if r[g] == r[glyphIndex]:
                        r[g] = s
            
            r[glyphIndex] = pool[className]
        
        # Do final cleanups
        r._merged_cleanUp(selfOldToNew, otherOldToNew)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testClassNames = (
      'End of text',
      'Out of bounds',
      'Deleted glyph',
      'End of line',
      'Letter',
      'Digit',
      'Punctuation')
    
    def _makeTestingValues():
        cn = _testClassNames
        r = []
        r.append(ClassTable({0: "Letter", 1: "Digit"}))
        r.append(ClassTable({0: "Letter", 1: "Digit"}))
        r[-1].update({i: "Punctuation" for i in range(23, 28)})
        r.append(ClassTable({i: cn[4+(i%2)] for i in range(50, 70)}))
        r[-1].update({i: cn[4+(i%2)] for i in range(150, 170)})
        r.append(ClassTable({12: "Letter", 90: "Digit"}))
        r.append(ClassTable({12: "Letter"}))
        return r
    
    # In the following, testing values [1:6] are formats [0:10:2]
    _testingValues = (ClassTable(),) + tuple(_makeTestingValues())
    del _makeTestingValues

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
