#
# opcode_tt.py
#
# Copyright © 2005-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes relating to single TrueType opcodes.
"""

# System import
import itertools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import seqmeta, simplemeta
from fontio3.hints import common
from fontio3.utilities import walkerbit, writer

# -----------------------------------------------------------------------------

#
# Constants
#

opcodeToNameMap = common.opcodeToNameMap
pushOpcodes = frozenset(list(range(0x40, 0x42)) + list(range(0xB0, 0xC0)))

# -----------------------------------------------------------------------------

#
# Functions
#

def frombytes(s):
    """
    Returns an opcode object from the specified binary string.
    
    >>> print(frombytes(utilities.fromhex("21")))
    POP
    >>> print(frombytes(utilities.fromhex("B1 03 01")))
    PUSH [3, 1]
    """
    
    return fromwalker(walkerbit.StringWalker(s))

fromBytes = frombytes  # compatibility

def fromwalker(w):
    """
    Returns an opcode object from the specified StringWalker.
    
    >>> print(fromWalker(walkerbit.StringWalker(utilities.fromhex("21"))))
    POP
    >>> print(fromWalker(walkerbit.StringWalker(utilities.fromhex("B1 03 01"))))
    PUSH [3, 1]
    """
    
    opcode = w.unpack("B")
    
    if opcode in pushOpcodes:
        w.skip(-1)
        return Opcode_push.fromwalker(w)
    
    return Opcode_nonpush(opcode)

fromWalker = fromwalker

def _validate_nonpush_opcode(opcode, **kwArgs):
    logger = kwArgs['logger']
    
    if opcode not in pushOpcodes:
        logger.error((
          'V0528',
          (opcode,),
          "0x%02X is a push opcode, and should not be passed to "
          "the non-push constructor!"))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Opcode_nonpush(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single TrueType opcodes, specifically excluding those
    opcodes used for the various TrueType push operations.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        opcode = dict(
            attr_initfunc = (lambda: 0),
            attr_validatefunc = _validate_nonpush_opcode),
        
        annotation = dict(
            attr_ignoreforcomparisons = True,
            attr_showonlyiftrue = True))
    
    attrSorted = ('opcode', 'annotation')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w):
        """
        Returns an Opcode_nonpush object initialized by the first byte pulled from the specified
        StringWalker.
        
        >>> Opcode_nonpush.fromwalker(walkerbit.StringWalker(bytes([0x21])))
        POP
        """
        
        return cls(w.unpack("B"))
    
    #
    # Special methods
    #
    
    def __repr__(self):
        """
        Returns a printable representation of the object.
        
        >>> print(Opcode_nonpush(0x01))
        SVTCA[x]
        >>> print(Opcode_nonpush(0x01, annotation=('jumpFrom', 14)))
        SVTCA[x], annotation = ('jumpFrom', 14)
        """
        
        if self.annotation is None:
            return opcodeToNameMap[self.opcode]
        
        return "%s, annotation = %s" % (opcodeToNameMap[self.opcode], self.annotation)
    
    __str__ = __repr__
    
    #
    # Public methods
    #
    
    def annotate(self, newAnnotation):
        """
        Adds the specified new annotation.
        
        >>> opObj = Opcode_nonpush(0x01)
        >>> print(opObj)
        SVTCA[x]
        >>> opObj.annotate(('jumpTo', 29))
        >>> print(opObj)
        SVTCA[x], annotation = frozenset({('jumpTo', 29)})
        >>> opObj.annotate(('jumpTo', 80))
        >>> opObj.annotation == frozenset({('jumpTo', 29), ('jumpTo', 80)})
        True
        """
        
        newEntry = frozenset([newAnnotation])
        
        if self.annotation is None:
            self.annotation = newEntry
        else:
            self.annotation = self.annotation | newEntry
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Opcode_nonpush object to the specified
        writer.
        
        >>> Opcode_nonpush(0x61).binaryString()
        b'a'
        """
        
        w.add("B", self.opcode)
    
    def getOriginalLength(self):
        """
        Returns 1.
        
        >>> Opcode_nonpush(0x01).getOriginalLength()
        1
        """
        
        return 1
    
    def isPush(self):
        """
        Returns False.
        
        >>> Opcode_nonpush(0x01).isPush()
        False
        """
        
        return False

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Data(tuple, metaclass=seqmeta.FontDataMetaclass):
    pass

class Opcode_push(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single TrueType push opcodes, which may push
    arbitrarily large numbers of values. Note the binaryString method may
    actually return multiple push opcodes, if the number of values being pushed
    is large enough or is mixed 8-bit and 16-bit.
    
    >>> print(Opcode_push([1, 3, -5]))
    PUSH [1, 3, -5]
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        data = dict(
            attr_ensuretype = Data,
            attr_followsprotocol = True),
        
        annotation = dict(
            attr_ignoreforcomparisons = True,
            attr_showonlyiftrue = True),
        
        originalLength = dict(
            attr_ignoreforcomparisons = True))
    
    attrSorted = ('data', 'annotation')
    
    #
    # Class methods
    #
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns an Opcode_push object initialized from the specified
        StringWalker, the first byte of which must be the correct TrueType
        opcode.
        
        >>> f = walkerbit.StringWalker
        >>> fh = utilities.fromhex
        >>> print(Opcode_push.fromwalker(f(fh("B1 05 0F"))))
        PUSH [5, 15]
        >>> print(Opcode_push.fromwalker(f(fh("BA 00 01 00 03 FF FB"))))
        PUSH [1, 3, -5]
        """
        
        opcode = w.unpack("B")
        
        if opcode == 0x40:
            fmt = "B"
            count = w.unpack("B")
            origLen = count + 2
        elif opcode == 0x41:
            fmt = "h"
            count = w.unpack("B")
            origLen = (count * 2) + 2
        elif opcode < 0xB8:
            fmt = "B"
            count = opcode - 0xAF
            origLen = count + 1
        else:
            fmt = "h"
            count = opcode - 0xB7
            origLen = (count * 2) + 1
        
        r = cls(w.groupIterator(fmt, count))
        r.originalLength = origLen
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Opcode_push object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("opcode_push")
        >>> f = walkerbit.StringWalker
        >>> h = utilities.fromhex
        >>> d = {'logger': logger}
        >>> fvw = Opcode_push.fromvalidatedwalker
        >>> print(fvw(f(h("40 02 05 0F")), **d))
        PUSH [5, 15]
        >>> print(fvw(f(h("B1 05 0F")), **d))
        PUSH [5, 15]
        >>> print(fvw(f(h("B8 05 0F")), **d))
        PUSH [1295]
        >>> fvw(f(h("40")), **d)
        opcode_push - ERROR - NPUSHB opcode is missing its count.
        >>> fvw(f(h("40 04 05 0F")), **d)
        opcode_push - ERROR - NPUSHB opcode expects 4 bytes but only 2 are present.
        >>> print(fvw(f(h("41 02 05 0F FF F2")), **d))
        PUSH [1295, -14]
        >>> fvw(f(h("41")), **d)
        opcode_push - ERROR - NPUSHW opcode is missing its count.
        >>> fvw(f(h("41 03 05 0F FF F2")), **d)
        opcode_push - ERROR - NPUSHW opcode expects 6 bytes but only 4 are present.
        >>> fvw(f(h("B5 05 0F")), **d)
        opcode_push - ERROR - PUSHB opcode expects 6 bytes but only 2 are present.
        >>> fvw(f(h("BB 05 0F")), **d)
        opcode_push - ERROR - PUSHW opcode expects 8 bytes but only 2 are present.
        """
        
        logger = kwArgs.get('logger', logging.getLogger())
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        opcode = w.unpack("B")
        
        if opcode == 0x40:  # NPUSHB
            if w.length() < 1:
                logger.error((
                  'V0521',
                  (),
                  "NPUSHB opcode is missing its count."))
                
                return None
            
            count = w.unpack("B")
            
            if w.length() < count:
                logger.error((
                  'V0522',
                  (count, int(w.length())),
                  "NPUSHB opcode expects %d bytes but only %d are present."))
                
                return None
            
            r = cls(w.group("B", count))
            r.originalLength = count + 2
        
        elif opcode == 0x41:  # NPUSHW
            if w.length() < 1:
                logger.error((
                  'V0523',
                  (),
                  "NPUSHW opcode is missing its count."))
                
                return None
            
            count = w.unpack("B")
            
            if w.length() < 2 * count:
                logger.error((
                  'V0524',
                  (count * 2, int(w.length())),
                  "NPUSHW opcode expects %d bytes but only %d are present."))
                
                return None
            
            r = cls(w.group("h", count))
            r.originalLength = (count * 2) + 2
        
        elif 0xB0 <= opcode < 0xB8:  # PUSHB
            count = opcode - 0xAF
            
            if w.length() < count:
                logger.error((
                  'V0525',
                  (count, int(w.length())),
                  "PUSHB opcode expects %d bytes but only %d are present."))
                
                return None
            
            r = cls(w.group("B", count))
            r.originalLength = count + 1
        
        elif 0xB8 <= opcode < 0xC0:
            count = opcode - 0xB7
            
            if w.length() < 2 * count:
                logger.error((
                  'V0526',
                  (count * 2, int(w.length())),
                  "PUSHW opcode expects %d bytes but only %d are present."))
                
                return None
            
            r = cls(w.group("h", count))
            r.originalLength = (count * 2) + 1
        
        else:
            logger.error((
              'V0527',
              (opcode,),
              "Opcode 0x%02X is not a valid push opcode."))
            
            return None
        
        return r
    
    #
    # Special methods
    #
    
    def __repr__(self):
        """
        Returns a printable representation of the object.
        
        >>> print(Opcode_push([1, 4]))
        PUSH [1, 4]
        >>> print(Opcode_push([1, 4], annotation=('fromJump', 9)))
        PUSH [1, 4], annotation = ('fromJump', 9)
        """
        
        if self.annotation is None:
            return "PUSH %s" % (list(self.data),)
        
        return "PUSH %s, annotation = %s" % (list(self.data), self.annotation)
    
    __str__ = __repr__
    
    #
    # Public methods
    #
    
    def addConstantToPushExtra(self, extraIndex, constantToAdd):
        """
        While Opcode_push objects are intended to be immutable, the hint
        merging code does need to make pinpoint changes. This method provides a
        way of doing this (see also replaceDataItem()).
        """
        
        if extraIndex >= len(self.data):
            raise IndexError(extraIndex)
        
        v = list(self.data)
        v[extraIndex] += constantToAdd
        self.data = Data(v)
    
    def annotate(self, newAnnotation):
        """
        Adds the specified new annotation.
        
        >>> opObj = Opcode_push([1, 3, 4])
        >>> print(opObj)
        PUSH [1, 3, 4]
        >>> opObj.annotate(('jumpTo', 29))
        >>> print(opObj)
        PUSH [1, 3, 4], annotation = frozenset({('jumpTo', 29)})
        >>> opObj.annotate(('jumpTo', 80))
        >>> opObj.annotation == frozenset({('jumpTo', 29), ('jumpTo', 80)})
        True
        """
        
        newEntry = frozenset([newAnnotation])
        
        if self.annotation is None:
            self.annotation = newEntry
        else:
            self.annotation = self.annotation | newEntry
    
    def buildBinary(self, wOrig, **kwArgs):
        """
        Return a binary string representing the best compression. Note this may
        change the length of the hints.

        Note that it's perfectly OK for a PUSH vector to have an arbitrarily
        large number of entries; this method will break them up into groups of
        255, as needed.
        
        >>> [c for c in Opcode_push([65, 66, 68, 67]).binaryString()]
        [179, 65, 66, 68, 67]
        >>> [c for c in Opcode_push([300, 200, 100, 0, -100]).binaryString()]
        [184, 1, 44, 178, 200, 100, 0, 184, 255, 156]
        """
        
        # We include the following test in case subsequent edits (via calls to
        # the deleteDataItem method) remove all content from the push.
        
        if not self.data:
            return
        
        w = writer.LinkedWriter()
        
        for useWordForm, g in itertools.groupby(self.data, lambda x: x < 0 or x > 255):
            fullList = list(g)
            
            while fullList:
                v = fullList[:255]
                useNForm = len(v) > 8
                
                if useWordForm:
                    data = ([0x41, len(v)] if useNForm else [0xB7 + len(v)])
                else:
                    data = ([0x40, len(v)] if useNForm else [0xAF + len(v)])
                
                w.addGroup("B", data)
                w.addGroup(("h" if useWordForm else "B"), v)
                fullList = fullList[255:]
        
        wOrig.addString(w.binaryString())
    
    def deleteDataItem(self, index):
        """
        Delete an item from the data associated with this push. Note that this
        operation is not performed often; the only current client of it in
        fontio3 is the jump-handler in the hint merging code.
        
        >>> obj = Opcode_push([2, 4, 9, 28])
        >>> obj.deleteDataItem(-2)
        >>> print(obj)
        PUSH [2, 4, 28]
        >>> obj.deleteDataItem(20)
        Traceback (most recent call last):
          ...
        IndexError: list assignment index out of range
        """
        
        v = list(self.data)
        del v[index]
        self.data = Data(v)
    
    def getOriginalLength(self):
        """
        Returns the original length of the push opcode used to construct this
        object, or the length of the binaryString() result if the object was
        constructed directly.
        
        >>> obj = Opcode_push.frombytes(bytes([0xB1, 5, 15]))
        >>> obj.getOriginalLength()
        3
        >>> obj = Opcode_push.frombytes(bytes([0xBA, 0, 1, 0, 3, 255, 251]))
        >>> obj.getOriginalLength()
        7
        >>> Opcode_push(list(range(-20, 21))).getOriginalLength()
        65
        """
        
        return self.originalLength or len(self.binaryString())
    
    def isPush(self): return True
    
    def replaceDataItem(self, index, newValue, onlyIfOldIs=None):
        """
        While Opcode_push objects are intended to be immutable, the hint
        merging code does need to make pinpoint changes. This method performs
        these changes.
        
        If onlyIfOldIs is a non-None value, the replacement will only be done
        if the current value at the specified location equals onlyIfOldIs.
        
        >>> obj = Opcode_push([2, 4, 9, 28])
        >>> obj.replaceDataItem(0, -5)
        >>> print(obj)
        PUSH [-5, 4, 9, 28]
        >>> obj.replaceDataItem(1, 12, onlyIfOldIs=20)
        >>> print(obj)
        PUSH [-5, 4, 9, 28]
        >>> obj.replaceDataItem(1, 12, onlyIfOldIs=4)
        >>> print(obj)
        PUSH [-5, 12, 9, 28]
        >>> obj.replaceDataItem(-1, 0)
        >>> print(obj)
        PUSH [-5, 12, 9, 0]
        >>> obj.replaceDataItem(25, 3)
        Traceback (most recent call last):
          ...
        IndexError: list assignment index out of range
        """
        
        if onlyIfOldIs is None or self.data[index] == onlyIfOldIs:
            v = list(self.data)
            v[index] = newValue
            self.data = Data(v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

