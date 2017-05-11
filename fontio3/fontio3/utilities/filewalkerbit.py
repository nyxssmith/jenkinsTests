#
# filewalkerbit.py -- Python front-end for the C-backed FileWalkerBit replacement
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Front-end module for Python programs using fast FileWalkerBits.
"""

# Other imports
from fontio3 import filewalkerbitbackend

# -----------------------------------------------------------------------------

#
# Classes
#

class FileWalkerBit:
    """
    Very fast FileWalkerBits; note the files are read-only and opened for
    binary processing. Conceptually, they have these "attributes" (although all
    of this is maintained in the C backend code, and is only available to
    clients via methods):
    
        origBitStart    The bit offset representing the start of data for this
                        FileWalkerBit. It does not have to be zero.
        
        currBitOffset   The bit offset representing the "current" location.
                        This value advances as data are unpacked from the
                        FileWalkerBit.
        
        bitLimit        The bit offset representing the first bit after all the
                        data for the FileWalkerBit. This follows Python's usual
                        conventions: you can determine the total amount of data
                        in a FileWalkerBit by subtracting the origBitStart from
                        the bitLimit.
        
        endian          Normally big-endian data are the norm (as that's what
                        all sfnt-housed data use), but the client has the
                        option of specifying little-endian. Note this is just
                        the default; a specific unpack operation may override
                        this via the "<" or ">" format codes, as with the
                        struct module.
    """
    
    #
    # Methods
    #
    
    def __init__(self, path, bitStart=0, bitLimit=None, endian='>'):
        """
        Initializes the FileWalkerBit for the specified file path.
        """
        
        if path is not None:
            self.context = filewalkerbitbackend.fwkbNewContext(
              path,
              bitStart,
              bitLimit,
              endian == '>')
    
    def absBitRest(self, bitOffset):
        """
        Returns a bytestring with the contents of the entire file from
        (bitOffset + origBitStart) to the end of the file.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.absBitRest(254 * 8) == bytearray([254, 255])
        True
        """
        
        return filewalkerbitbackend.fwkbAbsRest(self.context, bitOffset)
    
    def absRest(self, offset):
        """
        Returns a bytestring with the contents of the entire file from ((8 *
        offset) + origBitStart) to the end of the file.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.absRest(254) == bytearray([254, 255])
        True
        """
        
        return filewalkerbitbackend.fwkbAbsRest(self.context, 8 * offset)
    
    def align(self, byteMultiple=2):
        """
        Advances currBitOffset, if needed, so it is aligned with the specified
        byte multiple.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65 * 8)  # starts at ASCII A
        >>> ord(wb.unpackBits(5))
        64
        >>> wb.align(1)
        >>> wb.unpack("c")
        b'B'
        >>> wb.align(8)
        >>> wb.unpack("c")
        b'H'
        """
        
        filewalkerbitbackend.fwkbAlign(self.context, 8 * byteMultiple, True)
    
    def asStringAndOffset(self):
        """
        This method is not available for FileWalkers, and raises a
        NotImplementedError.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.asStringAndOffset()
        Traceback (most recent call last):
          ...
        NotImplementedError: FileWalkerBits should not use asStringAndOffset()!
        """
        
        raise NotImplementedError(
          "FileWalkerBits should not use asStringAndOffset()!")
    
    def atEnd(self):
        """
        Returns True if the file has been completely processed (to the limit
        that was originally specified).
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=250 * 8)
        >>> wb.atEnd()
        False
        >>> wb.unpack("5B")
        (250, 251, 252, 253, 254)
        >>> wb.atEnd()
        False
        >>> ord(wb.unpackBits(3))
        224
        >>> wb.atEnd()
        False
        >>> wb.bitAlign()
        >>> wb.atEnd()
        True
        """
        
        return filewalkerbitbackend.fwkbAtEnd(self.context)
    
    def bitAlign(self, bitMultiple=8, absolute=True):
        """
        Aligns the FileWalkerBit to the next available bit offset that is a
        multiple of the specified bitMultiple, or leaves it where it is if the
        currently location is already such a multiple.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65 * 8)  # starts at ASCII A
        >>> ord(wb.unpackBits(5))
        64
        >>> wb.bitAlign()
        >>> wb.unpack("c")
        b'B'
        >>> wb.bitAlign(64)
        >>> wb.unpack("c")
        b'H'
        """
        
        filewalkerbitbackend.fwkbAlign(self.context, bitMultiple, absolute)
    
    def bitLength(self):
        """
        Returns the number of bits remaining in the walker.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=252 * 8)
        >>> wb.bitLength()
        32
        >>> bitString = wb.unpackBits(9)
        >>> wb.bitLength()
        23
        >>> s = wb.chunk(2)
        >>> wb.bitLength()
        7
        """
        
        return filewalkerbitbackend.fwkbBitLength(self.context)
    
    def bitPiece(self, bitLength, bitOffset=0, relative=True):
        """
        Returns a chunk of data as a new bytestring from anywhere within the
        walker. Does not advance the walker.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65 * 8)  # starts at ASCII A
        >>> wb.bitPiece(19)
        b'AB@'
        >>> wb.bitPiece(24)
        b'ABC'
        >>> wb.bitPiece(24, bitOffset=7*8)
        b'HIJ'
        >>> wb.group("B", 6)
        (65, 66, 67, 68, 69, 70)
        >>> wb.bitPiece(24)
        b'GHI'
        >>> wb.bitPiece(24, relative=False)
        b'ABC'
        >>> wb.bitPiece(24, bitOffset=8, relative=False)
        b'BCD'
        """
        
        return filewalkerbitbackend.fwkbPiece(
          self.context,
          bitLength,
          bitOffset,
          relative)
    
    def bitSubWalker(
      self,
      bitOffset,
      relative = False,
      newBitLimit = None,
      anchor = False):
        
        """
        Returns a new FileWalkerBit based on the same file as self.
        
        To understand how the parameters work, consider an existing
        FileWalkerBit with these values:
        
            old.origBitStart = 20
            old.currBitOffset = 30
            old.bitLimit = 100
        
        A call of bitSubWalker(bitOffset=5, relative=False, newBitLimit=None)
        would yield this new FileWalkerBit:
        
            new.origBitStart = 25
            new.currBitOffset = 25
            new.bitLimit = 100
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, False, None)
        >>> wSub.bitLength()
        75
        >>> wSub.bitLength() + wSub.getBitOffset()
        100
        >>> wSub.unpack("5B")
        (6, 8, 10, 12, 14)
        
        A call of bitSubWalker(bitOffset=5, relative=False, newBitLimit=60)
        would yield this new FileWalkerBit; note the new bit limit is expressed
        relative to the old original bit start:
        
            new.origBitStart = 25
            new.currBitOffset = 25
            new.bitLimit = 60
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, False, 60)
        >>> wSub.bitLength()
        35
        >>> wSub.bitLength() + wSub.getBitOffset()
        60
        >>> wSub.unpack("3B")
        (6, 8, 10)
        
        A call of bitSubWalker(bitOffset=5, relative=True, newBitLimit=None)
        would yield this new FileWalkerBit:
        
            new.origBitStart = 35
            new.currBitOffset = 35
            new.bitLimit = 100
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, True, None)
        >>> wSub.bitLength()
        65
        >>> wSub.bitLength() + wSub.getBitOffset()
        100
        >>> wSub.unpack("5B")
        (32, 40, 48, 56, 64)
        
        A call of bitSubWalker(bitOffset=5, relative=True, newBitLimit=30)
        would yield this new FileWalkerBit; note that when the relative
        parameter is True, a specified newBitLimit is interpreted as relative
        to the start of the *new* FileWalkerBit, not the old one. It can thus
        be thought of as the bit length of the new walker:
        
            new.origBitStart = 35
            new.currBitOffset = 35
            new.bitLimit = 65
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, True, 30)
        >>> wSub.bitLength()
        30
        >>> wSub.bitLength() + wSub.getBitOffset()
        65
        >>> wSub.unpack("3B")
        (32, 40, 48)
        
        The anchor parameter causes the origBitStart to be ignored; instead,
        all values are relative to the absolute start of the file. (The
        relative parameter is ignored if anchor is True). In this case, there
        is a special value that can be passed in for the newBitLimit: if this
        value is zero, then the limit for the new FileWalkerBit will be the
        file's size. This is the only way in which limits can be "reset" for
        walkers.
        
        Continuing with the examples based on the "old" FileWalkerBit (above),
        a call of bitSubWalker(5, anchor=True) will return this new object:
        
            new.origBitStart = 5
            new.currBitOffset = 5
            new.bitLimit = 100
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, anchor=True)
        >>> wSub.bitLength()
        95
        >>> wSub.bitLength() + wSub.getBitOffset()
        100
        
        A call of bitSubWalker(5, anchor=True, newBitLimit=70) results in:
        
            new.origBitStart = 5
            new.currBitOffset = 5
            new.bitLimit = 70
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, anchor=True, newBitLimit=70)
        >>> wSub.bitLength()
        65
        >>> wSub.bitLength() + wSub.getBitOffset()
        70
        
        A call of bitSubWalker(5, anchor=True, newBitLimit=0) results in:
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30, and there are 50 bits left
        >>> wSub = wb.bitSubWalker(5, anchor=True, newBitLimit=0)
        >>> wSub.bitLength()
        2043
        >>> wSub.bitLength() + wSub.getBitOffset()
        2048
        """
        
        return self.fromcontext(
          filewalkerbitbackend.fwkbSubWalkerSetup(
            self.context,
            bitOffset,
            relative,
            anchor,
            newBitLimit))
    
    def byteAlign(self): self.bitAlign()
    
    @staticmethod
    def calcsize(format):
        """
        A static method returning the size of the specified format. We can't
        simply use struct.calcsize, since we define new format specifiers (like
        'T' and 't') that aren't defined in struct.
        
        >>> FileWalkerBit.calcsize("L")
        4
        >>> FileWalkerBit.calcsize("5T2x")
        17
        """
        
        return filewalkerbitbackend.fwkbCalcSize(format)
    
    def chunk(self, byteLength):
        """
        Returns a bytestring of specified length from the current location.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65 * 8)  # starts at ASCII A
        >>> wb.chunk(1)
        b'A'
        >>> wb.chunk(3)
        b'BCD'
        """
        
        return filewalkerbitbackend.fwkbUnpackBits(
          self.context,
          8 * byteLength)
    
    @classmethod
    def fromcontext(cls, newContext):
        """
        Called by bitSubWalker().
        """
        
        r = cls(None)  # passing None as the path means do no initialization
        r.context = newContext
        return r
    
    def getBitOffset(self, relative=False):
        """
        Returns the current offset. This is always relative to the original
        bit start value.
        
        >>> wMain = FileWalkerBit(_tempPath)
        >>> wb = wMain.bitSubWalker(25)
        >>> wb.getBitOffset()
        25
        >>> wb.unpack("4B")
        (6, 8, 10, 12)
        >>> wb.getBitOffset()
        57
        >>> wb.getBitOffset(relative=True)
        32
        >>> s = wb.unpackBits(6)
        >>> wb.getBitOffset()
        63
        """
        
        return filewalkerbitbackend.fwkbGetOffset(self.context, relative)
    
    def getOffset(self, relative=False):
        """
        Returns the current byte offset. This is an integer for backwards
        compatibility, and will be the floor of the actual fractional value.
        The older clients are used to calling getPhase() to get the other part
        of the information from a byte viewpoint.
        
        >>> wMain = FileWalkerBit(_tempPath)
        >>> wb = wMain.bitSubWalker(25)
        >>> wb.getOffset(), wb.getPhase()
        (3, 1)
        >>> wb.unpack("4B")
        (6, 8, 10, 12)
        >>> wb.getOffset(), wb.getPhase()
        (7, 1)
        >>> wb.getOffset(relative=True)
        4
        >>> s = wb.unpackBits(6)
        >>> wb.getOffset(), wb.getPhase()
        (7, 7)
        """
        
        return filewalkerbitbackend.fwkbGetOffset(self.context, relative) // 8
    
    def getPhase(self): return self.getBitOffset() % 8
    
    def group(self, format, count, finalCoerce=False):
        """
        Unpacks count records, each of which has format, and returns them in a
        tuple. If the format specifies more than one value per record, then the
        resulting tuple will itself have tuples, one per grouping.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)  # starts at ASCII A
        >>> wb.group("B", 5)
        (65, 66, 67, 68, 69)
        >>> wb.group("BB", 2)
        ((70, 71), (72, 73))
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)
        >>> wb.group("H", 1)
        (16706,)
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)
        >>> wb.group("H", 1, finalCoerce=True)
        16706
        """
        
        return filewalkerbitbackend.fwkbGroup(
          self.context,
          format,
          count,
          finalCoerce)
    
    def groupIterator(self, format, count):
        """
        Like the group method but returns an iterator rather than an actual
        list. This iterator can then be called to get the items in the group.
        
        This method is mostly for backward compatibility.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)  # starts at ASCII A
        >>> for g in wb.groupIterator("4B", 3): print(g)
        ... 
        (65, 66, 67, 68)
        (69, 70, 71, 72)
        (73, 74, 75, 76)
        """
        
        return iter(
          filewalkerbitbackend.fwkbGroup(self.context, format, count, False))
    
    def length(self):
        """
        Returns the byte length still available for unpacking. Note this is a
        float, and will have a nonzero fractional part if the currBitOffset is
        not a multiple of 8.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=252 * 8)
        >>> wb.length()
        4.0
        >>> bitString = wb.unpackBits(9)
        >>> wb.length()
        2.875
        >>> s = wb.chunk(2)
        >>> wb.length()
        0.875
        """
        
        return filewalkerbitbackend.fwkbBitLength(self.context) / 8
    
    def pascalString(self):
        """
        Reads a Pascal string and returns it as a bytestring. A Pascal string
        is an old Mac OS construct, comprising a length byte immediately
        followed by that many data bytes.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=2*8)
        >>> [c for c in wb.pascalString()]
        [3, 4]
        >>> [c for c in wb.pascalString()]
        [6, 7, 8, 9, 10]
        """
        
        return filewalkerbitbackend.fwkbPascalString(self.context)
    
    def piece(self, byteLength, byteOffset=0, relative=True):
        """
        Returns a chunk of data as a new bytestring from anywhere within the
        walker. Does NOT advance the walker.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65 * 8)  # starts at ASCII A
        >>> wb.piece(3)
        b'ABC'
        >>> wb.piece(3)
        b'ABC'
        >>> wb.piece(3, byteOffset=7)
        b'HIJ'
        >>> wb.group("B", 6)
        (65, 66, 67, 68, 69, 70)
        >>> wb.piece(3)
        b'GHI'
        >>> wb.piece(3, relative=False)
        b'ABC'
        >>> wb.piece(3, byteOffset=1, relative=False)
        b'BCD'
        """
        
        return filewalkerbitbackend.fwkbPiece(
          self.context,
          8 * byteLength,
          8 * byteOffset,
          relative)
    
    remainingLength = length  # old name for the same method

    def reset(self):
        """
        Resets the object so processing restarts at the origBitOffset the
        FileWalkerBit was created with.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)  # starts at ASCII A
        >>> wb.getBitOffset()
        520
        >>> wb.unpack("6s")
        b'ABCDEF'
        >>> wb.getBitOffset()
        568
        >>> wb.reset()
        >>> wb.getBitOffset()
        520
        """
        
        filewalkerbitbackend.fwkbReset(self.context)
    
    def rest(self):
        """
        Returns a bytestring with the rest of the unread data. This is exactly
        equivalent to calling self.unpackBits(self.bitLength()).
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=248*8)  # starts at ASCII A
        >>> wb.unpack("3B")
        (248, 249, 250)
        >>> [c for c in wb.rest()]
        [251, 252, 253, 254, 255]
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=242*8)
        >>> s = wb.unpackBits(85)
        >>> [c for c in wb.rest()]
        [159, 191, 223, 224]
        """
        
        return self.unpackBits(self.bitLength())

    def setBitOffset(self, bitOffset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.setBitOffset(5)
        >>> wb.getBitOffset()
        5
        >>> wb.setBitOffset(-1, relative=True)
        >>> wb.getBitOffset()
        4
        >>> wb.setBitOffset(-1, relative=False)
        Traceback (most recent call last):
          ...
        IndexError: Attempt to set offset past the limit
        >>> wb.getBitOffset()
        4
        """
        
        filewalkerbitbackend.fwkbSetOffset(
          self.context,
          bitOffset,
          relative,
          okToExceed)

    def setOffset(self, byteOffset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset. This operation always resets the phase to zero.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.setOffset(5)
        >>> wb.getOffset()
        5
        >>> wb.setOffset(-1, relative=True)
        >>> wb.getOffset()
        4
        >>> wb.setOffset(-1, relative=False)
        Traceback (most recent call last):
          ...
        IndexError: Attempt to set offset past the limit
        >>> wb.getOffset()
        4
        """
        
        filewalkerbitbackend.fwkbSetOffset(
          self.context,
          byteOffset * 8,
          relative,
          okToExceed)
    
    def skip(self, byteCount):
        """
        Skips the specified number of bytes.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.getOffset()
        0
        >>> wb.skip(19)
        >>> wb.getOffset()
        19
        >>> wb.skipBits(19)
        >>> wb.getOffset(), wb.getPhase()
        (21, 3)
        >>> wb.getBitOffset()
        171
        """
        
        filewalkerbitbackend.fwkbSkip(self.context, 8 * byteCount)
    
    def skipBits(self, bitCount):
        """
        Skips the specified number of bits.
        
        >>> wb = FileWalkerBit(_tempPath)
        >>> wb.getBitOffset()
        0
        >>> wb.skipBits(19)
        >>> wb.getBitOffset()
        19
        >>> wb.skipBits(19)
        >>> wb.getBitOffset()
        38
        """
        
        filewalkerbitbackend.fwkbSkip(self.context, bitCount)
    
    def stillGoing(self):
        """
        Returns True if the file has not yet been completely processed.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=250*8)
        >>> wb.stillGoing()
        True
        >>> wb.unpack("5B")
        (250, 251, 252, 253, 254)
        >>> wb.stillGoing()
        True
        >>> ord(wb.unpackBits(3))
        224
        >>> wb.stillGoing()
        True
        >>> wb.bitAlign()
        >>> wb.stillGoing()
        False
        """
        
        return not filewalkerbitbackend.fwkbAtEnd(self.context)
    
    def subWalker(
      self,
      byteOffset,
      relative = False,
      absoluteAnchor = False,
      newLimit = None):
        
        """
        Returns a new FileWalkerBit based on the same file as self.
        
        To understand how the parameters work, consider an existing
        FileWalkerBit with these values:
        
            old.origBitStart = 520
            old.currBitOffset = 536
            old.bitLimit = 1024
        
        A call of subWalker(byteOffset=1, relative=False, newLimit=None)
        would yield this new FileWalkerBit:
        
            new.origBitStart = 528
            new.currBitOffset = 528
            new.bitLimit = 1024
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1)
        >>> wSub.length()
        62.0
        >>> wSub.length() + wSub.getOffset()
        128.0
        >>> wSub.unpack("5c")
        (b'B', b'C', b'D', b'E', b'F')
        
        A call of subWalker(bytOffset=1, relative=False, newLimit=75)
        would yield this new FileWalkerBit; note the new limit is expressed
        relative to the old original start:
        
            new.origBitStart = 528
            new.currBitOffset = 528
            new.bitLimit = 600
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, newLimit=75)
        >>> wSub.length()
        9.0
        >>> wSub.length() + wSub.getOffset()
        75.0
        >>> wSub.unpackRest("c")
        (b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J')
        
        A call of subWalker(byteOffset=1, relative=True, newLimit=None)
        would yield this new FileWalkerBit:
        
            new.origBitStart = 544
            new.currBitOffset = 544
            new.bitLimit = 1024
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, relative=True)
        >>> wSub.length()
        60.0
        >>> wSub.length() + wSub.getOffset()
        128.0
        >>> wSub.unpack("5c")
        (b'D', b'E', b'F', b'G', b'H')
        
        A call of subWalker(byteOffset=1, relative=True, newLimit=7)
        would yield this new FileWalkerBit; note that when the relative
        parameter is True, a specified new limit is interpreted as relative
        to the start of the *new* FileWalkerBit, not the old one. It can thus
        be thought of as the length of the new walker:
        
            new.origBitStart = 544
            new.currBitOffset = 544
            new.bitLimit = 600
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, relative=True, newLimit=7)
        >>> wSub.length()
        7.0
        >>> wSub.length() + wSub.getOffset()
        75.0
        >>> wSub.unpack("3c")
        (b'D', b'E', b'F')
        
        The absoluteAnchor parameter causes the original start to be ignored;
        instead, all values are relative to the absolute start of the file.
        (The relative parameter is ignored if anchor is True). In this case,
        there is a special value that can be passed in for the new limit: if
        this value is zero, then the limit for the new FileWalkerBit will be
        the file's size. This is the only way in which limits can be "reset"
        for walkers.
        
        Continuing with the examples based on the "old" FileWalkerBit (above),
        a call of subWalker(1, anchor=True) will return this new object:
        
            new.origBitStart = 8
            new.currBitOffset = 8
            new.bitLimit = 1024
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, absoluteAnchor=True)
        >>> wSub.length()
        127.0
        >>> wSub.length() + wSub.getOffset()
        128.0
        
        A call of subWalker(1, absoluteAnchor=True, newLimit=70) results in:
        
            new.origBitStart = 5
            new.currBitOffset = 5
            new.bitLimit = 70
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, absoluteAnchor=True, newLimit=75)
        >>> wSub.length()
        74.0
        >>> wSub.length() + wSub.getOffset()
        75.0
        
        A call of subWalker(1, absoluteAnchor=True, newLimit=0) results in:
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, absoluteAnchor=True, newLimit=0)
        >>> wSub.length()
        255.0
        >>> wSub.length() + wSub.getOffset()
        256.0
        """
        
        return self.fromcontext(
          filewalkerbitbackend.fwkbSubWalkerSetup(
            self.context,
            8 * byteOffset,
            relative,
            absoluteAnchor,
            (None if newLimit is None else 8 * newLimit)))  # 0 stays 0
    
    def unpack(self, format, coerce=True, advance=True):
        """
        Unpacks one or more values from the filewalker and returns them in a
        tuple. If only a single value is being unpacked and coerce is True (the
        default) then the value itself will be returned, instead of a
        one-element tuple.

        If advance is False, the walker is not moved after the items are read,
        so a subsequent unpack() call will re-process the same location.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=128*8)  # high bit bytes
        >>> wb.unpack("BbHhLlTt")
        (128, -127, 33411, -31611, 2257029257, -1970566003, 9342864, -7236973)
        >>> wb.unpack(">fd")
        (-1.5104552404603995e-26, -3.5916126958448044e-190)
        >>> wb.unpack("<fd")
        (-1.763252604431516e-17, -2.4380131109097072e-98)
        """
        
        return filewalkerbitbackend.fwkbUnpack(
          self.context,
          format,
          coerce,
          advance)
    
    def unpackBits(self, bitCount):
        """
        Returns a bytestring with the specified number of bits from the source.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)  # starts at ASCII A
        >>> list(wb.unpackBits(7))
        [64]
        >>> list(wb.unpackBits(9))
        [161, 0]
        >>> wb.chunk(3)
        b'CDE'
        """
        
        return filewalkerbitbackend.fwkbUnpackBits(self.context, bitCount)
    
    def unpackBitsGroup(self, bitCountPerItem, itemCount, signed=False):
        """
        Returns a list with itemCount numeric values, each one of which is
        unpacked from the walker in bitCountPerItem chunks. If signed is True
        the resulting values will be interpreted as twos-complement; otherwise
        they will be unsigned.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=65*8)  # starts at ASCII A
        >>> wb.unpackBitsGroup(5, 12)
        (8, 5, 1, 4, 6, 17, 2, 5, 8, 25, 3, 20)
        >>> wb.reset()
        >>> wb.unpackBitsGroup(5, 12, True)
        (8, 5, 1, 4, 6, -15, 2, 5, 8, -7, 3, -12)
        """
        
        return filewalkerbitbackend.fwkbUnpackBitsGroup(
          self.context,
          bitCountPerItem,
          itemCount,
          signed)

    def unpackRest(self, format, coerce=True, strict=True):
        """
        Returns a tuple with values from the remainder of the file, as per the
        specified format. Members of the returned tuple will themselves be
        tuples, unless coerce is True and the format specifies only a single
        value.
        
        Normally, the number of bits remaining in the FileWalkerBit must be
        exactly divisible by the bit length of the format. If it is not, an
        exception will be raised, unless strict is set to False, in which case
        as many data values as possible will be unpacked, but there may be
        leftover unused bits.
        
        >>> wb = FileWalkerBit(_tempPath, bitStart=248*8)
        >>> print(wb.unpack("H"))
        63737
        >>> print(wb.unpackRest("BB"))
        ((250, 251), (252, 253), (254, 255))
        
        >>> wb.reset()
        >>> print(wb.unpackRest("H"))
        (63737, 64251, 64765, 65279)
        
        >>> wb.reset()
        >>> print(wb.unpackRest("H", coerce=False))
        ((63737,), (64251,), (64765,), (65279,))
        """
        
        return filewalkerbitbackend.fwkbUnpackRest(
          self.context,
          format,
          coerce,
          strict)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class FileWalker(FileWalkerBit):
    """
    FileWalkers are actually just thin wrappers around FileWalkerBits.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, path, start=0, limit=None, endian='>'):
        """
        >>> wb = FileWalker(_tempPath, start=65, limit=68)
        >>> wb.rest()
        b'ABC'
        """
        
        super().__init__(
          path = path,
          bitStart = 8 * start,
          bitLimit = (None if limit is None else 8 * limit),
          endian = endian)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass


if __name__ == "__main__" and __debug__:
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
