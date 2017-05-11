#
# classmap.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from glyph to class.
"""

# System imports
import collections
import itertools

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Constants
#

fixedNames = (
  "End of text",
  "Out of bounds",
  "Deleted glyph",
  "End of line")

# -----------------------------------------------------------------------------

#
# Private functions
#

def _nToName(n):
    if n < 4:
        return fixedNames[n]
    
    return "User class %d" % (n - 3,)

# -----------------------------------------------------------------------------

#
# Classes
#

class _DD(collections.defaultdict):
    def __missing__(self, key):
        # We don't actually update the dictionary in the OOB case
#         r = self[key] = fixedNames[1]
        r = fixedNames[1]
        return r

class ClassMap(_DD, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping glyphs to class names.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    afii60002: Consonant
    xyz41: Vowel
    xyz45: Vowel
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_makefunc = (lambda s,*a,**k: type(s)(_DD, *a, **k)))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker_aat_old(cls, w, **kwArgs):
        """
        Creates and returns a ClassMap object from the specified walker, which
        refers to an old-style (8-bit class values) AAT class mapping. There is
        one optional keyword argument:
        
            nameList    If provided and is an empty list, then on return from
                        this method the list will be filled with the names of
                        each of the classes, in the read order.
                        
                        If provided and is a non-empty list, then it is assumed
                        to have the names to be used for the classes.
        
        >>> w = writer.LinkedWriter()
        >>> nm = {}
        >>> _testingValues[1].buildBinary_aat_old(w, nameMap=nm)
        >>> nl = [name for name, num in sorted(nm.items(), key=operator.itemgetter(1))]
        >>> w = walkerbit.StringWalker(w.binaryString())
        >>> obj = ClassMap.fromwalker_aat_old(w, nameList=nl)
        >>> obj == _testingValues[1]
        True
        """
        
        r = cls()
        first, count = w.unpack("2H")
        it = zip(itertools.count(first), w.group("B", count))
        nMax = -1
        names = kwArgs.get('nameList')
        
        for glyph, n in it:
            if n > nMax:
                nMax = n
            
            if n != 1:  # we don't explicitly encode OOBs
                r[glyph] = (names[n] if names else _nToName(n))
        
        if names == []:
            kwArgs['nameList'][:] = (_nToName(i) for i in range(nMax + 1))
        
        return r
    
    #
    # Public methods
    #
    
    def buildBinary_aat_old(self, w, **kwArgs):
        """
        Adds the binary data for the xxx object to the specified LinkedWriter.
        Raises a ValueError if there are more than 255 classes currently
        defined (as that's the old AAT limit).
        
        There are two optional keyword arguments:
        
            nameMap             If provided, should be an empty dict. On return
                                from this method the dict will be filled with a
                                mapping from name to class number (which is
                                dynamically calculated as part of this method's
                                process). Note that if an nsObj is also
                                provided, the names that go into this nameMap
                                will be the fixedNames, followed by the names
                                from the nsObj's addedClassNames list.
            
            neededAlignment     After the content is written, the writer will
                                be aligned to this byte multiple. Default is 2.
            
            nsObj               If provided, should be a NameStash object. This
                                will be used to map the class names to their
                                correct values.
        
        >>> w = writer.LinkedWriter()
        >>> nm = {}
        >>> _testingValues[1].buildBinary_aat_old(w, nameMap=nm)
        >>> utilities.hexdump(w.binaryString())
               0 | 0028 003A 0401 0101  0401 0101 0101 0101 |.(.:............|
              10 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              20 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              30 | 0101 0101 0101 0101  0101 0101 0105      |..............  |
        
        >>> for name, num in sorted(nm.items(), key=operator.itemgetter(1)):
        ...     print(name, num)
        End of text 0
        Out of bounds 1
        Deleted glyph 2
        End of line 3
        Vowel 4
        Consonant 5
        
        >>> w = writer.LinkedWriter()
        >>> nm = {}
        >>> namestash = _ns()
        >>> nsObj = namestash.NameStash(addedClassNames=["Consonant", "Vowel"])
        >>> _testingValues[1].buildBinary_aat_old(w, nameMap=nm, nsObj=nsObj)
        >>> utilities.hexdump(w.binaryString())
               0 | 0028 003A 0501 0101  0501 0101 0101 0101 |.(.:............|
              10 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              20 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              30 | 0101 0101 0101 0101  0101 0101 0104      |..............  |
        
        >>> for name, num in sorted(nm.items(), key=operator.itemgetter(1)):
        ...     print(name, num)
        End of text 0
        Out of bounds 1
        Deleted glyph 2
        End of line 3
        Consonant 4
        Vowel 5
        
        >>> w = writer.LinkedWriter()
        >>> nm = {}
        >>> namestash = _ns()
        >>> nsObj = namestash.NameStash(addedClassNames=["Consonant", "Vowel"])
        >>> _testingValues[1].buildBinary_aat_old(w, nameMap=nm, nsObj=nsObj, neededAlignment=4)
        >>> utilities.hexdump(w.binaryString())
               0 | 0028 003A 0501 0101  0501 0101 0101 0101 |.(.:............|
              10 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              20 | 0101 0101 0101 0101  0101 0101 0101 0101 |................|
              30 | 0101 0101 0101 0101  0101 0101 0104 0000 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        firstGlyph = min(self)
        lastGlyph = max(self)
        dMap = {s: i for i, s in enumerate(fixedNames)}
        nsObj = kwArgs.get('nsObj', None)
        
        if nsObj is not None:
            for i, s in enumerate(nsObj.addedClassNames):
                dMap[s] = i + len(fixedNames)
        
        for name in self.values():
            if name not in dMap:
                dMap[name] = len(dMap)
        
        if len(dMap) > 255:
            raise ValueError("Old AAT class lookups are limited to 255 classes!")
        
        w.add("2H", firstGlyph, lastGlyph - firstGlyph + 1)
        w.addGroup("B", (dMap[self[glyph]] for glyph in range(firstGlyph, lastGlyph + 1)))
        
        if 'nameMap' in kwArgs:
            kwArgs['nameMap'].update(dMap)
        
        w.alignToByteMultiple(kwArgs.get('neededAlignment', 2))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import operator
    from fontio3 import utilities
    from fontio3.utilities import namer, walkerbit, writer
    
    def _ns():
        from fontio3.statetables import namestash
        return namestash
    
    _testingValues = (
        ClassMap(),
        ClassMap({40: "Vowel", 44: "Vowel", 97: "Consonant"}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
