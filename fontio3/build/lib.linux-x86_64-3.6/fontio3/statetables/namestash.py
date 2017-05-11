#
# namestash.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for covert stashing of class and state names in hidden locations within
a state table (in the AAT sense, although this technique works with anything).

Note that this code currently constrains the strings to being ASCII. At some
point we could extend this to use UTF-8 without much change, although the
pascalString() length returns by the walker and the actual string length might
differ in this case.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Constants
#

fixedStateNames = (
  "Start of text",
  "Start of line")

fixedClassNames = (
  "End of text",
  "Out of bounds",
  "Deleted glyph",
  "End of line")

# -----------------------------------------------------------------------------

#
# Classes
#

class NameStash(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects collection both class and state names for a state table, apart from
    the standard 4 classes and 2 states, which are NOT included here.
    
    >>> _testingValues[0].pprint()
    Added class names: ['Letter', 'Vowel', 'Punctuation']
    Added state names: ['SawLetter', 'SawLetterPair']
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        addedClassNames = dict(
            attr_initfunc = list,
            attr_label = "Added class names"),
        
        addedStateNames = dict(
            attr_initfunc = list,
            attr_label = "Added state names"))
    
    #
    # Class methods
    #
    
    @classmethod
    def fromcounts(cls, stateNonFixedCount, classNonFixedCount, **kwArgs):
        """
        Creates and returns a new NameStash object with synthesized names for
        states and classes based on the specified counts. The names will be of
        the format "User class 1" and "User state 1".
        
        >>> NameStash.fromcounts(3, 2).pprint()
        Added class names: ['User class 1', 'User class 2']
        Added state names: ['User state 1', 'User state 2', 'User state 3']
        """
        
        svState = [
          "User state %d" % (i + 1,)
          for i in range(stateNonFixedCount)]
        
        svClass = [
          "User class %d" % (i + 1,)
          for i in range(classNonFixedCount)]
        
        return cls(addedClassNames=svClass, addedStateNames=svState)
    
    @classmethod
    def fromstatedict(cls, sd, **kwArgs):
        """
        Given a StateDict, creates and returns a new NameStash using the non-
        standard state and class names.
        
        There is some custom logic here that specially sorts class and/or
        state names that are all the default kind (i.e. "User state nn" or
        "User class nn"). This ensures a proper numeric sort.
        """
        
        digits = set("0123456789")
        asn = set(sd) - set(fixedStateNames)
        f = None
        
        if all(s.startswith("User state ") for s in asn):
            if not any(set(s[11:]) - digits for s in asn):
                f = lambda s: int(s[11:])
        
        if f is None:
            sSorted = sorted(asn)
        else:
            sSorted = sorted(asn, key=f)
        
        csn = set(s for d in sd.values() for s in d)
        csn -= set(fixedClassNames)
        f = None
        
        if all(s.startswith("User class ") for s in csn):
            if not any(set(s[11:]) - digits for s in csn):
                f = lambda s: int(s[11:])
        
        if f is None:
            cSorted = sorted(csn)
        else:
            cSorted = sorted(csn, key=f)
        
        return cls(addedClassNames=cSorted, addedStateNames=sSorted)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates snd returns a new NameStash object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("namestash_fvw")
        >>> fvb = NameStash.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        namestash_fvw.namestash - DEBUG - Walker has 56 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[2:], logger=logger)
        namestash_fvw.namestash - DEBUG - Walker has 54 remaining bytes.
        namestash_fvw.namestash - ERROR - Expected a guard of 0xFEED, but got 0x0003.
        
        >>> fvb(_testingValues[1].binaryString(), logger=logger)
        namestash_fvw.namestash - DEBUG - Walker has 56 remaining bytes.
        namestash_fvw.namestash - ERROR - One or more stashed class names are the same as one or more of the fixed class names.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("namestash")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        guard = w.unpack("H")
        
        if guard != 0xFEED:
            logger.error((
              'V0680',
              (guard,),
              "Expected a guard of 0xFEED, but got 0x%04X."))
            
            return None
        
        if w.length() < 2:
            logger.error((
              'V0681',
              (),
              "The class name count in the name stash "
              "is missing or incomplete."))
            
            return None
        
        classNameCount = w.unpack("H")
        vCN = [None] * classNameCount
        
        for i in range(classNameCount):
            try:
                ps = w.pascalString()
            except IndexError:
                ps = b''
            
            if not ps:
                logger.error((
                  'V0682',
                  (i,),
                  "Class name index %d is missing or incomplete."))
                
                return None
            
            try:
                vCN[i] = str(ps, 'ascii')
            
            except UnicodeDecodeError:
                logger.error((
                  'V0683',
                  (i,),
                  "Class name index %d is not an ASCII string."))
                
                return None
        
        if w.length() < 2:
            logger.error((
              'V0684',
              (),
              "The state name count in the name stash "
              "is missing or incomplete."))
            
            return None
        
        stateNameCount = w.unpack("H")
        vSN = [None] * stateNameCount
        
        for i in range(stateNameCount):
            try:
                ps = w.pascalString()
            except IndexError:
                ps = b''
            
            if not ps:
                logger.error((
                  'V0685',
                  (i,),
                  "State name index %d is missing or incomplete."))
                
                return None
            
            try:
                vSN[i] = str(ps, 'ascii')
            
            except UnicodeDecodeError:
                logger.error((
                  'V0686',
                  (i,),
                  "State name index %d is not an ASCII string."))
                
                return None
        
        if any(s in fixedStateNames for s in vSN):
            logger.error((
              'V0687',
              (),
              "One or more stashed state names are the same as one or more "
              "of the fixed state names."))
            
            return None
        
        if any(s in fixedClassNames for s in vCN):
            logger.error((
              'V0688',
              (),
              "One or more stashed class names are the same as one or more "
              "of the fixed class names."))
            
            return None
        
        return cls(addedClassNames=vCN, addedStateNames=vSN)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new NameStash object from the specified walker. A
        ValueError is raised if the first 16 bits are not the value 0xFEED.
        
        >>> obj = _testingValues[0]
        >>> s = obj.binaryString()
        >>> obj == NameStash.frombytes(s)
        True
        """
        
        guard = w.unpack("H")
        
        if guard != 0xFEED:
            raise ValueError("First 16 bits of name stash are not 0xFEED!")
        
        vCN = [str(w.pascalString(), 'ascii') for i in range(w.unpack("H"))]
        vSN = [str(w.pascalString(), 'ascii') for i in range(w.unpack("H"))]
        return cls(addedClassNames=vCN, addedStateNames=vSN)
    
    @classmethod
    def readormake(cls, w, offsetTuple, numStates, numClasses):
        """
        Creates and returns a new NameStash. The specified walker is used to
        attempt to read a NameStash, but if that fails (or if the offsets in
        the offsetTuple indicate there's not enough room for a NameStash to
        exist) then a new NameStash based on the specified state and class
        counts is returned.
        
        >>> s = _testingValues[0].binaryString()
        >>> w = walkerbit.StringWalker(s)
        >>> NameStash.readormake(w, (1000,), 2, 3).pprint()
        Added class names: ['Letter', 'Vowel', 'Punctuation']
        Added state names: ['SawLetter', 'SawLetterPair']
        
        >>> NameStash.readormake(w, (-1000,), 3, 6).pprint()
        Added class names: ['User class 1', 'User class 2']
        Added state names: ['User state 1']
        """
        
        if (min(offsetTuple) - w.getOffset(relative=True)) < 6:
            return cls.fromcounts(numStates - 2, numClasses - 4)
        
        try:
            r = cls.fromwalker(w)
        except ValueError:
            r = cls.fromcounts(numStates - 2, numClasses - 4)
        
        return r
    
    @classmethod
    def readormake_validated(cls, w, offsetTuple, numStates, numClasses, **kwArgs):
        """
        Creates and returns a new NameStash object, doing source validation.
        The specified walker is used to attempt to read a NameStash, but if
        that fails (or if the offsets in the offsetTuple indicate there's not
        enough room for a NameStash to exist) then a new NameStash based on the
        specified state and class counts is returned.
        """
        
        if (min(offsetTuple) - w.getOffset(relative=True)) < 6:
            return cls.fromcounts(numStates - 2, numClasses - 4)
        
        if (w.length() < 2) or (w.unpack("H", advance=False) != 0xFEED):
            return cls.fromcounts(numStates - 2, numClasses - 4)
        
        return cls.fromvalidatedwalker(w, **kwArgs)
    
    #
    # Public methods
    #
    
    def allClassNames(self):
        """
        A convenience method that returns a list whose first four elements are
        the fixed names ("End of text", "Out of bounds", "Deleted glyph", and
        "End of line"), and whose remaining elements are the addedClassNames.
        
        >>> _testingValues[0].allClassNames()
        ['End of text', 'Out of bounds', 'Deleted glyph', 'End of line', 'Letter', 'Vowel', 'Punctuation']
        """
        
        return list(fixedClassNames) + self.addedClassNames
    
    def allStateNames(self):
        """
        A convenience method that returns a list whose first two elements are
        the fixed names ("Start of text", "Start of line"), and whose remaining
        elements are the addedStateNames.
        
        >>> _testingValues[0].allStateNames()
        ['Start of text', 'Start of line', 'SawLetter', 'SawLetterPair']
        """
        
        return list(fixedStateNames) + self.addedStateNames
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the NameStash to the specified LinkedWriter.
        There is one keyword argument:
        
            neededAlignment     Default is 2; new-style 'morx' and 'kerx' state
                                tables should pass 4.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | FEED 0003 064C 6574  7465 7205 566F 7765 |.....Letter.Vowe|
              10 | 6C0B 5075 6E63 7475  6174 696F 6E00 0209 |l.Punctuation...|
              20 | 5361 774C 6574 7465  720D 5361 774C 6574 |SawLetter.SawLet|
              30 | 7465 7250 6169 7200                      |terPair.        |
        """
        
        w.add("H", 0xFEED)  # special guard
        vCN = [s.encode('ascii') for s in self.addedClassNames]
        vSN = [s.encode('ascii') for s in self.addedStateNames]
        
        for v in (vCN, vSN):
            w.add("H", len(v))
            
            for s in v:
                w.add("B", len(s))
                w.addString(s)
        
        w.alignToByteMultiple(kwArgs.get('neededAlignment', 2))
    
    def nameClasses(self, classMap, namer):
        """
        Changes all class names of the form "User class nn" into more
        meaningful names. The specified classMap maps glyph indices to class
        names, and the namer can provide nicely readable names given a glyph
        index.
        
        >>> ns = NameStash.fromcounts(2, 4)
        >>> for s in ns.addedClassNames: print(s)
        User class 1
        User class 2
        User class 3
        User class 4
        >>> nm = namer.testingNamer()
        >>> cm = {
        ...   14: "User class 1",
        ...   19: "User class 1",
        ...   31: "User class 3",
        ...   32: "User class 3",
        ...   33: "User class 4",
        ...   35: "User class 3",
        ...   36: "User class 3",
        ...   41: "User class 3",
        ...   97: "User class 2"}
        >>> ns.nameClasses(cm, nm)
        >>> for s in ns.addedClassNames: print(s)
        xyz15, xyz20
        afii60002
        xyz32, xyz33 ... xyz37, xyz42
        xyz34
        """
        
        revClassMap = utilities.invertDictFull(classMap, asSets=True)
        newNames = list(self.addedClassNames)
        f = namer.bestNameForGlyphIndex
        
        for i, origName in enumerate(self.addedClassNames):
            gs = sorted(revClassMap.get(origName, set()))
            
            if not gs:
                continue
            
            if len(gs) < 5:
                namerNames = [f(glyphIndex) for glyphIndex in gs]
                newNames[i] = "%s" % (', '.join(namerNames),)
            
            else:
                t = (f(gs[0]), f(gs[1]), f(gs[-2]), f(gs[-1]))
                newNames[i] = "%s, %s ... %s, %s" % t
        
        self.addedClassNames = newNames

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer, walkerbit
    
    _testingValues = (
        NameStash(
          ["Letter", "Vowel", "Punctuation"],
          ["SawLetter", "SawLetterPair"]),
        
        # bad objects start here
        
        NameStash(
          ["Letter", "Vowel", "End of line"],
          ["SawLetter", "SawLetterPair"]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

