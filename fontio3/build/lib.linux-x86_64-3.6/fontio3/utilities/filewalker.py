#
# filewalker.py -- Python front-end for the C-backed FileWalker replacement
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Front-end module for Python programs using fast FileWalkers.
"""

# Other imports
from fontio3 import filewalkerbackend

# -----------------------------------------------------------------------------

#
# Classes
#

class FileWalker:
    """
    Very fast FileWalkers; note the files are read-only and opened for binary
    processing.
    """
    
    #
    # Methods
    #
    
    def __init__(self, path, start=0, limit=None, endian='>'):
        """
        Initializes the FileWalker for the specified file path.
        """
        
        if path is not None:
            self.context = filewalkerbackend.fwkNewContext(
              path,
              start,
              limit,
              endian == '>')
    
    def _debugPrint(self):
        """
        Prints out a variety of information about the current state of the
        walker.
        """
        
        filewalkerbackend.fwkDebugPrint(self.context)
    
    def absRest(self, offset):
        """
        Returns a string with the contents of the entire file from offset +
        currentOffset to the end of the file. Note that limit is ignored in
        this method.
        
        >>> w = FileWalker(_tempPath)
        >>> w.absRest(254) == bytearray([254, 255])
        True
        """
        
        return filewalkerbackend.fwkAbsRest(self.context, offset)
    
    def align(self, multiple=2):
        """
        First byte-aligns the walker, and then aligns to the specified
        multiple.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> ord(w.unpackBits(5))
        64
        >>> w.align(1)
        >>> w.unpack("c")
        b'B'
        >>> w.align(8)
        >>> w.unpack("c")
        b'H'
        """
        
        filewalkerbackend.fwkAlign(self.context, multiple)
    
    def asStringAndOffset(self):
        """
        This method is not available for FileWalkers, and raises a
        NotImplementedError.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> w.asStringAndOffset()
        Traceback (most recent call last):
          ...
        NotImplementedError: FileWalkers should not use asStringAndOffset()!
        """
        
        raise NotImplementedError(
          "FileWalkers should not use asStringAndOffset()!")
    
    def atEnd(self):
        """
        Returns True if the string has been completely processed.
        
        >>> w = FileWalker(_tempPath, start=250)
        >>> w.atEnd()
        False
        >>> w.unpack("5B")
        (250, 251, 252, 253, 254)
        >>> w.atEnd()
        False
        >>> ord(w.unpackBits(3))
        224
        >>> w.atEnd()
        False
        >>> w.align(1)
        >>> w.atEnd()
        True
        """
        
        return filewalkerbackend.fwkAtEnd(self.context)
    
    def bitLength(self):
        """
        Returns the number of bits remaining in the walker.
        
        >>> w = FileWalker(_tempPath, start=252)
        >>> w.bitLength()
        32
        >>> bitString = w.unpackBits(9)
        >>> w.bitLength()
        23
        >>> s = w.chunk(2)
        >>> w.bitLength()
        7
        """
        
        return filewalkerbackend.fwkBitLength(self.context)
    
    @staticmethod
    def calcsize(format):
        """
        A static method returning the size of the specified format. We can't
        simply use struct.calcsize, since we define new format specifiers (like
        'T' and 't') that aren't defined in struct.
        
        >>> FileWalker.calcsize("L")
        4
        >>> FileWalker.calcsize("5T2x")
        17
        """
        
        return filewalkerbackend.fwkCalcSize(format)
    
    def chunk(self, byteLength):
        """
        Returns a bytestring of specified length from the current location.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> w.chunk(1)
        b'A'
        >>> w.chunk(3)
        b'BCD'
        """
        
        return filewalkerbackend.fwkUnpackBits(self.context, 8 * byteLength)
    
    @classmethod
    def fromcontext(cls, newContext):
        """
        Called by subWalker().
        """
        
        r = cls(None)  # passing None as the path means do no initialization
        r.context = newContext
        return r
    
    def getOffset(self, relative=False):
        """
        Returns the current offset, either absolute or relative to the original
        starting offset.
        
        >>> wMain = FileWalker(_tempPath)
        >>> w = wMain.subWalker(3)
        >>> w.getOffset(relative=False)
        3
        >>> w.getOffset(relative=True)
        0
        >>> w.unpack("4B")
        (3, 4, 5, 6)
        >>> w.getOffset(relative=False)
        7
        >>> w.getOffset(relative=True)
        4
        >>> s = w.unpackBits(6)
        >>> w.getOffset()
        7
        """
        
        return filewalkerbackend.fwkGetOffset(self.context, relative)
    
    def getPhase(self):
        """
        Returns the current phase (i.e. the bit number next to be accessed,
        where 0 is the most significant bit of each byte).
        
        >>> w = FileWalker(_tempPath)
        >>> w.getPhase()
        0
        >>> bitString = w.unpackBits(5)
        >>> w.getPhase()
        5
        >>> bitString2 = w.unpackBits(5)
        >>> w.getPhase()
        2
        """
        
        return filewalkerbackend.fwkGetPhase(self.context)
    
    def group(self, format, count, finalCoerce=False):
        """
        Unpacks count records, each of which has format, and returns them in a
        tuple. If the format specifies more than one value per record, then the
        resulting tuple will itself have tuples, one per grouping.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> w.group("B", 5)
        (65, 66, 67, 68, 69)
        >>> w.group("BB", 2)
        ((70, 71), (72, 73))
        
        >>> w = FileWalker(_tempPath, start=65)
        >>> w.group("H", 1)
        (16706,)
        
        >>> w = FileWalker(_tempPath, start=65)
        >>> w.group("H", 1, finalCoerce=True)
        16706
        """
        
        return filewalkerbackend.fwkGroup(
          self.context,
          format,
          count,
          finalCoerce)
    
    def groupIterator(self, format, count):
        """
        Like the group method but returns an iterator rather than an actual
        list. This iterator can then be called to get the items in the group.
        
        This method is mostly for backward compatibility.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> for g in w.groupIterator("4B", 3): print(g)
        ... 
        (65, 66, 67, 68)
        (69, 70, 71, 72)
        (73, 74, 75, 76)
        """
        
        return iter(
          filewalkerbackend.fwkGroup(self.context, format, count, False))
    
    def length(self, fromStart=False):
        """
        Returns the current available length (as if it were a string).
        
        If fromStart is True, the returned length is the total original length,
        and not just the length of the remaining piece.
        
        >>> wTop = FileWalker(_tempPath, start=244)  # starts at ASCII A
        >>> w = wTop.subWalker(3, relative=True)
        >>> w.length()
        9
        >>> w.length(fromStart=True)
        9
        >>> w.unpack("4B")
        (247, 248, 249, 250)
        >>> w.length()
        5
        >>> w.length(fromStart=True)
        9
        """
        
        return filewalkerbackend.fwkLength(self.context, fromStart)
    
    def pascalString(self):
        """
        Reads a Pascal string and returns it as a regular Python string. A
        Pascal string is an old Mac OS construct, comprising a length byte
        immediately followed by that many data bytes.
        
        >>> w = FileWalker(_tempPath, start=2)
        >>> [c for c in w.pascalString()]
        [3, 4]
        >>> [c for c in w.pascalString()]
        [6, 7, 8, 9, 10]
        """
        
        return filewalkerbackend.fwkPascalString(self.context)
    
    def piece(self, length, offset=0, relative=True):
        """
        Returns a chunk of data as a new string from anywhere within the
        walker. Does NOT advance the walker.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> w.piece(3)
        b'ABC'
        >>> w.piece(3)
        b'ABC'
        >>> w.piece(3, offset=7)
        b'HIJ'
        >>> w.group("B", 6)
        (65, 66, 67, 68, 69, 70)
        >>> w.piece(3)
        b'GHI'
        >>> w.piece(3, relative=False)
        b'ABC'
        >>> w.piece(3, offset=1, relative=False)
        b'BCD'
        """
        
        return filewalkerbackend.fwkPiece(
          self.context,
          length,
          offset,
          relative)
    
    remainingLength = length  # old name for the same method

    def reset(self):
        """
        Resets the object so processing starts either at the absolute beginning
        of the string, or at the offset it started with.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> w.getOffset()
        65
        >>> w.unpack("6s")
        b'ABCDEF'
        >>> w.getOffset()
        71
        >>> w.reset()
        >>> w.getOffset()
        65
        """
        
        filewalkerbackend.fwkReset(self.context)
    
    def rest(self):
        """
        Returns a string with the rest of the unread data. Note that unlike the
        pure Python version, this version will return fractional bytes.
        
        >>> w = FileWalker(_tempPath, start=248)  # starts at ASCII A
        >>> w.unpack("3B")
        (248, 249, 250)
        >>> [c for c in w.rest()]
        [251, 252, 253, 254, 255]
        
        >>> w = FileWalker(_tempPath, start=242)
        >>> s = w.unpackBits(85)
        >>> [c for c in w.rest()]
        [159, 191, 223, 224]
        """
        
        return self.unpackBits(self.bitLength())

    def setOffset(self, offset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset. This operation always resets the phase to zero.
        
        >>> w = FileWalker(_tempPath)
        >>> w.setOffset(5)
        >>> w.getOffset()
        5
        >>> w.setOffset(-1, relative=True)
        >>> w.getOffset()
        4
        >>> w.setOffset(-1, relative=False)
        Traceback (most recent call last):
          ...
        IndexError: attempt to set offset past the limit
        >>> w.getOffset()
        4
        """
        
        filewalkerbackend.fwkSetOffset(
          self.context,
          offset,
          relative,
          okToExceed)
    
    def skip(self, byteCount, resetPhase=True):
        """
        Advances the current offset by the specified number of bytes. Reset the
        phase to zero if specified.
        
        >>> w = FileWalker(_tempPath)
        >>> w.getOffset(), w.getPhase()
        (0, 0)
        >>> w.skip(5)
        >>> w.getOffset(), w.getPhase()
        (5, 0)
        >>> bitString = w.unpackBits(3)
        >>> w.getOffset(), w.getPhase()
        (5, 3)
        >>> w.skip(2, resetPhase=False)
        >>> w.getOffset(), w.getPhase()
        (7, 3)
        >>> w.skip(1)
        >>> w.getOffset(), w.getPhase()
        (8, 0)
        
        >>> w = FileWalker(_tempPath, start=10)
        >>> w.getOffset()
        10
        >>> w.skip(5)
        >>> w.getOffset()
        15
        """
        
        filewalkerbackend.fwkSkip(self.context, byteCount, resetPhase)
    
    def skipBits(self, bitCount):
        """
        Advances the phase by the specified number of bits, and then adjusts
        the phase and offset to their corresponding natural values.
        
        >>> w = FileWalker(_tempPath)
        >>> w.getOffset(), w.getPhase()
        (0, 0)
        >>> w.skipBits(19)
        >>> w.getOffset(), w.getPhase()
        (2, 3)
        >>> w.skipBits(19)
        >>> w.getOffset(), w.getPhase()
        (4, 6)
        >>> w.skipBits(19)
        >>> w.getOffset(), w.getPhase()
        (7, 1)
        """
        
        filewalkerbackend.fwkSkipBits(self.context, bitCount)
    
    def stillGoing(self):
        """
        Returns True if the string has not yet been completely processed.
        
        >>> w = FileWalker(_tempPath, start=250)
        >>> w.stillGoing()
        True
        >>> w.unpack("5B")
        (250, 251, 252, 253, 254)
        >>> w.stillGoing()
        True
        >>> ord(w.unpackBits(3))
        224
        >>> w.stillGoing()
        True
        >>> w.align(1)
        >>> w.stillGoing()
        False
        """
        
        return not filewalkerbackend.fwkAtEnd(self.context)
    
    def subWalker(
      self,
      offset,
      relative = False,
      absoluteAnchor = False,
      newLimit = None):
        
        """
        Returns a new FileWalker based on the same file as self. Even though
        they're using the same POSIX FILE object, each walker maintains its own
        state, including file position, so each walker always retrieves the
        correct data.
        
        To understand how all the parameters work, consider an existing
        FileWalker with these values:
        
            old.origStart = 20
            old.currOffset = 30
            old.limit = 100
        
        A call of subWalker(5, False, False, None) would yield this FileWalker:
        
            new.origStart = 25
            new.currOffset = 25
            new.limit = 100
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, False, False, None)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (25, 99)
        
        A call of subWalker(5, False, False, 60) would yield this FileWalker:
        
            new.origStart = 25
            new.currOffset = 25
            new.limit = 80  <-- relative to old.origStart, so 60 - 5 == 80 - 25
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, False, False, 60)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (25, 79)
        
        A call of subWalker(5, True, False, None) would yield this FileWalker:
        
            new.origStart = 35
            new.currOffset = 35
            new.limit = 100
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, True, False, None)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (35, 99)
        
        A call of subWalker(5, True, False, 30) would yield this FileWalker:
        
            new.origStart = 35
            new.currOffset = 35
            new.limit = 65  <-- newLimit is relative to new.origStart
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, True, False, 30)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (35, 64)
        
        A call of subWalker(5, ignore, True, None) would yield this FileWalker:
        
            new.origStart = 5
            new.currOffset = 5
            new.limit = 100
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, False, True, None)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (5, 99)
        
        A call of subWalker(5, ignore, True, 50) would yield this FileWalker:
        
            new.origStart = 5
            new.currOffset = 5
            new.limit = 50
        
        >>> w = FileWalker(_tempPath, start=20, limit=100)
        >>> w.skip(10)  # currOffset is now 30
        >>> wSub = w.subWalker(5, False, True, 50)
        >>> v = wSub.unpackRest("B")
        >>> v[0], v[-1]
        (5, 49)
        """
        
        return self.fromcontext(
          filewalkerbackend.fwkSubWalkerSetup(
            self.context, offset, relative, absoluteAnchor, newLimit))
    
    def unpack(self, format, coerce=True, advance=True):
        """
        Unpacks one or more values from the filewalker and returns them in a
        tuple. If only a single value is being unpacked and coerce is True (the
        default) then the value itself will be returned, instead of a
        one-element tuple.

        If advance is False, the walker is not moved after the items are read,
        so a subsequent unpack() call will re-process the same location.
        
        >>> w = FileWalker(_tempPath, start=128)  # bytes with high bit set
        >>> w.unpack("BbHhLlTt")
        (128, -127, 33411, -31611, 2257029257, -1970566003, 9342864, -7236973)
        >>> w.unpack(">fd")
        (-1.5104552404603995e-26, -3.5916126958448044e-190)
        >>> w.unpack("<fd")
        (-1.763252604431516e-17, -2.4380131109097072e-98)
        """
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          format,
          coerce,
          advance)
    
    def unpack8Bit(self, wantSigned=False):
        """
        Returns an 8-bit quantity, signed or not as specified.
        
        This method works with nonzero phases as well.
        
        >>> w = FileWalker(_tempPath, start=127)
        >>> print(w.unpack8Bit())
        127
        >>> print(w.unpack8Bit())
        128
        >>> print(w.unpack8Bit(True))
        -127
        
        >>> w = FileWalker(_tempPath, start=127)
        >>> bitString = w.unpackBits(5)
        >>> print(w.unpack8Bit(True))
        -16
        >>> print(w.unpack8Bit())
        16
        >>> print(w.unpack8Bit())
        48
        """
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          ('b' if wantSigned else 'B'),
          True,
          True)
    
    def unpack16Bit(self, wantSigned=False):
        """
        Returns a 16-bit quantity, signed or not as specified. The global
        endian state is used.
        
        This method works with nonzero phases as well.
        
        >>> w = FileWalker(_tempPath, start=127)
        >>> w.unpack16Bit()
        32640
        >>> w.unpack16Bit(True)
        -32382
        
        >>> w = FileWalker(_tempPath, start=127, endian='<')
        >>> w.unpack16Bit()
        32895
        >>> w.unpack16Bit(True)
        -32127
        """
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          ('h' if wantSigned else 'H'),
          True,
          True)
    
    def unpack24Bit(self, wantSigned=False):
        """
        Unpacks a single 24-bit value, signed or not as indicated.
        
        This method works with nonzero phases as well.
        
        >>> w = FileWalker(_tempPath, start=128)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (8421762, -8158075)
        >>> w.getOffset(), w.getPhase()
        (134, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (134, 5)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (13693201, 3232113)
        >>> w.getOffset(), w.getPhase()
        (140, 5)
        
        >>> w = FileWalker(_tempPath, start=128, endian='<')
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (8552832, -8027005)
        >>> bitString = w.unpackBits(5)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (1176016, 7426353)
        """
        
        # Note we use our custom format code here, 'T' or 't'.
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          ('t' if wantSigned else 'T'),
          True,
          True)
    
    def unpack32Bit(self, wantSigned=False):
        """
        Returns a 32-bit quantity, signed or not as specified. The global
        endian state is used.
        
        This method works with nonzero phases as well.
        
        >>> w = FileWalker(_tempPath, start=128)
        >>> print(w.unpack32Bit())
        2155971203
        >>> w.unpack32Bit(True)
        -2071624057
        
        >>> w = FileWalker(_tempPath, start=128, endian='<')
        >>> print(w.unpack32Bit())
        2206368128
        >>> w.unpack32Bit(True)
        -2021227132
        """
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          ('l' if wantSigned else 'L'),
          True,
          True)
    
    def unpack64Bit(self, wantSigned=False):
        """
        Unpacks a single 64-bit value, signed or not as indicated.
        
        This method works with nonzero phases as well.
        
        >>> w = FileWalker(_tempPath, start=128)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (9259825810226120327, -8608196880778817905)
        >>> w.getOffset(), w.getPhase()
        (144, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (144, 5)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (1311201093559177971, 1383541266397254644)
        >>> w.getOffset(), w.getPhase()
        (160, 5)
        
        >>> w = FileWalker(_tempPath, start=128, endian='<')
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (9765639646188044672, -8102383044816893560)
        >>> bitString = w.unpackBits(5)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (17569301438378684946, -805102462492789997)
        """
        
        return filewalkerbackend.fwkUnpack(
          self.context,
          ('q' if wantSigned else 'Q'),
          True,
          True)
    
    def unpackBCD(self, count, byteLength=1, coerce=True):
        r"""
        Unpacks one or more binary-coded decimal values from the stream and
        return a list of them. If coerce is True and count is 1 then the
        simple value is returned, not a list.
        
        >>> w = FileWalker(_tempPath, start=18)
        >>> w.unpackBCD(2)
        (1, 2)
        >>> w.unpackBCD(2, byteLength=2)
        (13, 14)
        >>> w.unpackBCD(1, byteLength=2)
        15
        >>> w.skip(-1)
        >>> w.unpackBCD(1, byteLength=2, coerce=False)
        (15,)
        """
        
        return filewalkerbackend.fwkUnpackBCD(
          self.context,
          count,
          byteLength,
          coerce);
    
    def unpackBits(self, bitCount):
        """
        Returns a string with the specified number of bits from the source.
        
        >>> w = FileWalker(_tempPath, start=65)  # starts at ASCII upper-case A
        >>> list(w.unpackBits(7))
        [64]
        >>> list(w.unpackBits(9))
        [161, 0]
        >>> w.chunk(3)
        b'CDE'
        """
        
        return filewalkerbackend.fwkUnpackBits(self.context, bitCount)

    def unpackRest(self, format, coerce=True):
        """
        Returns a tuple with values from the remainder of the string, as per
        the specified format. Members of the returned tuple will themselves be
        tuples, unless coerce is True and the format specifies only a single
        value.
        
        >>> w = FileWalker(_tempPath, start=248)
        >>> print(w.unpack("H"))
        63737
        >>> print(w.unpackRest("BB"))
        ((250, 251), (252, 253), (254, 255))
        
        >>> w.reset()
        >>> print(w.unpackRest("H"))
        (63737, 64251, 64765, 65279)
        
        >>> w.reset()
        >>> print(w.unpackRest("H", coerce=False))
        ((63737,), (64251,), (64765,), (65279,))
        """
        
        return filewalkerbackend.fwkUnpackRest(self.context, format, coerce)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __name__=="__main__" and __debug__:
    import os
    import tempfile
    
    fd, _tempPath = tempfile.mkstemp()
    os.close(fd)
    f = open(_tempPath, "wb")
    f.write(bytearray(range(256)))
    f.close()
    del f, fd

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
