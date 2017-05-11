#
# opcode_tt.py
#
# Copyright © 2005-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes relating to single TrueType opcodes.
"""

# System import
import itertools
import logging

# Other imports
from fontio3.fontdata import enummeta, seqmeta
from fontio3.h2 import common
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Constants
#

PUSH_OPCODES = frozenset(list(range(0x40, 0x42)) + list(range(0xB0, 0xC0)))

NON_PUSH_NAMES = {
  k: v
  for k, v in common.rawOpcodeToNameMap.items()
  if k not in PUSH_OPCODES}

UNUSED_COLOR_OPCODES = {
  0x6B,  # ROUND
  0x6F,  # NROUND
  0xC3,  # MDRP[m<r]
  0xC7,  # MDRP[m<R]
  0xCB,  # MDRP[m>r]
  0xCF,  # MDRP[m>R]
  0xD3,  # MDRP[M<r]
  0xD7,  # MDRP[M<R]
  0xDB,  # MDRP[M>r]
  0xDF,  # MDRP[M>R]
  0xE3,  # MIRP[m<r]
  0xE7,  # MIRP[m<R]
  0xEB,  # MIRP[m>r]
  0xEF,  # MIRP[m>R]
  0xF3,  # MIRP[M<r]
  0xF7,  # MIRP[M<R]
  0xFB,  # MIRP[M>r]
  0xFF,  # MIRP[M>R]
  }

# -----------------------------------------------------------------------------

#
# Functions
#

def _needsWord(n):
    return n < 0 or n > 255

def frombytes(s):
    """
    Factory function to return an opcode object, either Opcode_nonpush or
    Opcode_push, from the specified binary string.
    """
    
    opcode = s[0]
    
    if opcode in PUSH_OPCODES:
        return Opcode_push.frombytes(s)
    
    return Opcode_nonpush(opcode)

def fromvalidatedwalker(w, **kwArgs):
    """
    Factory function to return an opcode object, either Opcode_nonpush or
    Opcode_push, from the specified walker. Validation is done.
    """
    
    opcode = w.unpack("B", advance=False)
    
    if opcode in PUSH_OPCODES:
        return Opcode_push.fromvalidatedwalker(w, **kwArgs)
    
    return Opcode_nonpush.fromvalidatedwalker(w, **kwArgs)

def fromwalker(w, **kwArgs):
    """
    Factory function to return an opcode object, either Opcode_nonpush or
    Opcode_push, from the specified walker. No validation is done.
    """
    
    opcode = w.unpack("B", advance=False)
    
    if opcode in PUSH_OPCODES:
        return Opcode_push.fromwalker(w, **kwArgs)
    
    return Opcode_nonpush.fromwalker(w, **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Opcode_nonpush(int, metaclass=enummeta.FontDataMetaclass):
    """
    Objects representing single TrueType opcodes, specifically excluding those
    opcodes used for the various TrueType push operations.
    """
    
    enumSpec = dict(
        enum_pprintlabel = "Opcode",
        enum_stringsdict = NON_PUSH_NAMES,
        enum_validatecode_badenumvalue = 'V0528',
        enum_validatefunc_partial = valassist.isFormat_B)
    
    #
    # Class constants
    #
    
    isPush = False
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Opcode_nonpush object to the specified
        writer.
        
        >>> Opcode_nonpush(0x61).binaryString()
        b'a'
        """
        
        w.add("B", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns an Opcode_nonpush object initialized by the first byte pulled
        from the specified StringWalker. Validation is done.
        
        >>> logger = utilities.makeDoctestLogger("opcode_nonpush")
        >>> fvb = Opcode_nonpush.fromvalidatedbytes
        >>> fh = utilities.fromhex
        >>> print((fvb(fh('21'), logger=logger)))
        opcode_nonpush - DEBUG - Walker has 1 remaining bytes.
        POP[]
        
        >>> fvb(fh('B0 04'), logger=logger)
        opcode_nonpush - DEBUG - Walker has 2 remaining bytes.
        opcode_nonpush - ERROR - The opcode value 0xB0 is not a valid non-push opcode!
        
        >>> fvb(b'', logger=logger)
        opcode_nonpush - DEBUG - Walker has 0 remaining bytes.
        opcode_nonpush - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        n = w.unpack("B")
        
        if n in UNUSED_COLOR_OPCODES:
            logger.warning((
              'V1068',
              (n,),
              "The opcode value 0x%02X specifies an undefined color distance"))
        
        elif n not in NON_PUSH_NAMES:
            logger.error((
              'V0528',
              (n,),
              "The opcode value 0x%02X is not a valid non-push opcode!"))
            
            return None
        
        return cls(n)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns an Opcode_nonpush object initialized by the first byte pulled
        from the specified StringWalker. If the first byte is a PUSH opcode,
        or undefined, None is returned.
        
        >>> fb = Opcode_nonpush.frombytes
        >>> print((fb(utilities.fromhex('21'))))
        POP[]
        
        >>> print((fb(utilities.fromhex('B0 04'))))
        None
        """
        
        n = w.unpack('B')
        return (cls(n) if n in NON_PUSH_NAMES else None)
    
    def getOriginalLength(self):
        """
        Returns 1.
        
        >>> Opcode_nonpush(0x01).getOriginalLength()
        1
        """
        
        return 1

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Opcode_push(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single TrueType push opcodes, which may push
    arbitrarily large numbers of values. Note the binaryString method may
    actually return multiple push opcodes, if the number of values being pushed
    is large enough or is mixed 8-bit and 16-bit.
    
    >>> print((Opcode_push([1, 3, -5])))
    PUSH [1, 3, -5]
    """
    
    seqSpec = dict(
        item_validatefunc_partial = valassist.isFormat_h)
    
    attrSpec = dict(
        originalLength = dict(
            attr_ignoreforcomparisons = True))
    
    attrSorted = ()
    
    #
    # Class constants
    #
    
    isPush = True
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a printable representation of the object.
        
        >>> print((Opcode_push([1, 4])))
        PUSH [1, 4]
        """
        
        return "PUSH %s" % (list(self),)
    
    def buildBinary(self, w, **kwArgs):
        """
        Return a binary string representing the best compression. Note this may
        change the length of the hints.

        Note that it's perfectly OK for a PUSH vector to have an arbitrarily
        large number of entries; this method will break them up into groups of
        255, as needed.
        
        >>> list(Opcode_push([65, 66, 68, 67]).binaryString())
        [179, 65, 66, 68, 67]
        >>> list(Opcode_push([300, 200, 100, 0, -100]).binaryString())
        [184, 1, 44, 178, 200, 100, 0, 184, 255, 156]
        """
        
        if not self:
            return
        
        for useWordForm, g in itertools.groupby(self, _needsWord):
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
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Opcode_push object from the specified walker,
        doing source validation.
        
        >>> logger = utilities.makeDoctestLogger("opcode_push")
        >>> h = utilities.fromhex
        >>> d = {'logger': logger}
        >>> fvb = Opcode_push.fromvalidatedbytes
        >>> print((fvb(h("40 02 05 0F"), **d)))
        opcode_push - DEBUG - Walker has 4 remaining bytes.
        PUSH [5, 15]
        
        >>> print((fvb(h("B1 05 0F"), **d)))
        opcode_push - DEBUG - Walker has 3 remaining bytes.
        PUSH [5, 15]
        
        >>> print((fvb(h("B8 05 0F"), **d)))
        opcode_push - DEBUG - Walker has 3 remaining bytes.
        PUSH [1295]
        
        >>> fvb(h("40"), **d)
        opcode_push - DEBUG - Walker has 1 remaining bytes.
        opcode_push - ERROR - NPUSHB opcode is missing its count.
        
        >>> fvb(h("40 04 05 0F"), **d)
        opcode_push - DEBUG - Walker has 4 remaining bytes.
        opcode_push - ERROR - NPUSHB opcode expects 4 bytes but only 2 are present.
        
        >>> print((fvb(h("41 02 05 0F FF F2"), **d)))
        opcode_push - DEBUG - Walker has 6 remaining bytes.
        PUSH [1295, -14]
        
        >>> fvb(h("41"), **d)
        opcode_push - DEBUG - Walker has 1 remaining bytes.
        opcode_push - ERROR - NPUSHW opcode is missing its count.
        
        >>> fvb(h("41 03 05 0F FF F2"), **d)
        opcode_push - DEBUG - Walker has 6 remaining bytes.
        opcode_push - ERROR - NPUSHW opcode expects 6 bytes but only 4 are present.
        
        >>> fvb(h("B5 05 0F"), **d)
        opcode_push - DEBUG - Walker has 3 remaining bytes.
        opcode_push - ERROR - PUSHB opcode expects 6 bytes but only 2 are present.
        
        >>> fvb(h("BB 05 0F"), **d)
        opcode_push - DEBUG - Walker has 3 remaining bytes.
        opcode_push - ERROR - PUSHW opcode expects 8 bytes but only 2 are present.
        """
        
        logger = kwArgs.get('logger', logging.getLogger())
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
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
            
            return cls(w.group("B", count), originalLength=count+2)
        
        if opcode == 0x41:  # NPUSHW
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
            
            return cls(w.group("h", count), originalLength=(count*2)+2)
        
        if 0xB0 <= opcode < 0xB8:  # PUSHB
            count = opcode - 0xAF
            
            if w.length() < count:
                logger.error((
                  'V0525',
                  (count, int(w.length())),
                  "PUSHB opcode expects %d bytes but only %d are present."))
                
                return None
            
            return cls(w.group("B", count), originalLength=count+1)
        
        if 0xB8 <= opcode < 0xC0:
            count = opcode - 0xB7
            
            if w.length() < 2 * count:
                logger.error((
                  'V0526',
                  (count * 2, int(w.length())),
                  "PUSHW opcode expects %d bytes but only %d are present."))
                
                return None
            
            return cls(w.group("h", count), originalLength=(count*2)+1)
        
        logger.error((
          'V0527',
          (opcode,),
          "Opcode 0x%02X is not a valid push opcode."))
        
        return None
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns an Opcode_push object initialized from the specified
        StringWalker, the first byte of which must be the correct TrueType
        opcode.
        
        >>> fb = Opcode_push.frombytes
        >>> fh = utilities.fromhex
        >>> print((fb(fh("B1 05 0F"))))
        PUSH [5, 15]
        
        >>> print((fb(fh("BA 00 01 00 03 FF FB"))))
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
        
        return cls(w.groupIterator(fmt, count), originalLength=origLen)
    
    def getOriginalLength(self):
        """
        Returns the original length of the push opcode used to construct this
        object, or the length of the binaryString() result if the object was
        constructed directly.
        
        >>> fb = Opcode_push.frombytes
        >>> fh = utilities.fromhex
        >>> obj = fb(fh("B1 05 15"))
        >>> obj.getOriginalLength()
        3
        >>> obj = fb(fh("BA 00 01 00 03 FF FB"))
        >>> obj.getOriginalLength()
        7
        >>> Opcode_push(list(range(-20, 21))).getOriginalLength()
        65
        """
        
        return self.originalLength or len(self.binaryString())

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


