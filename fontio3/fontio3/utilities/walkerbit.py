#
# walkerbit.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Front-end module for Python programs using fast StringWalkerBits.
"""

from fontio3 import walkerbitbackend

# -----------------------------------------------------------------------------

#
# Classes
#

class StringWalkerBit:
    """
    Very fast StringWalkerBits. These are bytestring-backed; for file-backed
    walkers, see the filewalkerbit module. Conceptually, StringWalkerBit
    objects have these "attributes" (although all of this is maintained in the
    C backend code, and is only available to clients via methods):
    
        origBitStart    The bit offset representing the start of data for this
                        StringWalkerBit. It does not have to be zero.
        
        currBitOffset   The bit offset representing the "current" location.
                        This value advances as data are unpacked from the
                        StringWalkerBit.
        
        bitLimit        The bit offset representing the first bit after all the
                        data for the StringWalkerBit. This follows Python's
                        usual conventions: you can determine the total amount
                        of data in a StringWalkerBit by subtracting the
                        origBitStart from the bitLimit.
        
        endian          Normally big-endian data are the norm (as that's what
                        all sfnt-housed data use), but the client has the
                        option of specifying little-endian. Note this is just
                        the default; a specific unpack operation may override
                        this via the "<" or ">" format codes, as with the
                        struct module.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, s, bitStart=0, bitLimit=None, endian='>'):
        """
        Initializes the StringWalkerBit for the specified bytestring.
        """
        
        self.context = walkerbitbackend.wkbNewContext(
          s,
          bitStart,
          bitLimit or (len(s) * 8),
          endian == '>')
    
    #
    # Public methods
    #
    
    def absBitRest(self, bitOffset):
        """
        Returns a new bytestring representing the whole old bytestring starting
        at the specified absolute bit offset.
        
        >>> wb = StringWalkerBit(bytes.fromhex("FE FF B4 E6 99"))
        >>> utilities.hexdump(wb.absBitRest(21))
               0 | 9CD3 20                                  |..              |
        >>> print(wb.getBitOffset())
        0
        """
        
        return walkerbitbackend.wkbAbsRest(self.context, bitOffset)
    
    def absRest(self, offset):
        """
        Returns a new bytestring representing the whole old bytestring starting
        at the specified absolute byte offset.
        
        >>> wb = StringWalkerBit(b"ABCDEFG")
        >>> wb.absRest(4)
        b'EFG'
        """
        
        return walkerbitbackend.wkbAbsRest(self.context, 8 * offset)
    
    def align(self, byteMultiple=2):
        """
        Advances currBitOffset, if needed, so it is aligned with the specified
        byte multiple.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKL", bitStart=8)
        >>> wb.align()
        >>> wb.unpack("c")
        b'C'
        >>> wb.align(8)
        >>> wb.unpack("c")
        b'I'
        """
        
        walkerbitbackend.wkbAlign(self.context, 8 * byteMultiple, True)
    
    def asStringAndOffset(self):
        """
        Returns a pair (s, offset) representing the walker's current state.
        
        >>> s = b"abcdefgh"
        >>> wb = StringWalkerBit(s)
        >>> ignore = wb.unpackBits(5)
        >>> t = wb.asStringAndOffset()
        >>> t[0] is s
        True
        >>> t[1]
        5
        """
        
        return walkerbitbackend.wkbAsStringAndOffset(self.context)
    
    def atEnd(self):
        """
        Returns True if the string has been completely processed.
        
        >>> wb = StringWalkerBit(b"ABC")
        >>> wb.atEnd()
        False
        >>> wb.unpackBits(24)
        b'ABC'
        >>> wb.atEnd()
        True
        >>> wb.getBitOffset()
        24
        """
        
        return walkerbitbackend.wkbAtEnd(self.context)
    
    def bitAlign(self, bitMultiple=8, absolute=True):
        """
        Aligns to the specified bit multiple. This will normally be with
        respect to zero; if absolute is False, it is relative to the original
        start instead.
        
        >>> wb = StringWalkerBit(bytes.fromhex("12 34 56 78"), bitStart=3)
        >>> print(wb.getBitOffset())
        3
        >>> wb.bitAlign(8)
        >>> print(wb.getBitOffset())
        8
        >>> wb.bitAlign(8, absolute=False)
        >>> print(wb.getBitOffset())
        11
        >>> wb.bitAlign(700)
        Traceback (most recent call last):
          ...
        IndexError: Align leaves walker past end of data!
        """
        
        return walkerbitbackend.wkbAlign(self.context, bitMultiple, absolute)
    
    def bitLength(self):
        """
        Returns the number of bits remaining in the walker.
        
        >>> wb = StringWalkerBit(b"ABCD")
        >>> wb.bitLength()
        32
        >>> bitString = wb.unpackBits(9)
        >>> wb.bitLength()
        23
        """
        
        return walkerbitbackend.wkbBitLength(self.context)
    
    def bitPiece(self, bitLength, bitOffset=0, relative=True):
        """
        Returns a chunk of data as a new bytestring from anywhere within the
        walker. Does not advance the walker.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKLMN")
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
        
        return walkerbitbackend.wkbPiece(self.context, bitLength, bitOffset, relative)
    
    def bitSubWalker(self, bitOffset, relative=False, newBitLimit=None, anchor=False):
        """
        Returns a new StringWalkerBit based on the same file as self.
        
        To understand how the parameters work, consider an existing
        StringWalkerBit with these values:
        
            old.origBitStart = 20
            old.currBitOffset = 30
            old.bitLimit = 100
        
        A call of bitSubWalker(bitOffset=5, relative=False, newBitLimit=None)
        would yield this new StringWalkerBit:
        
            new.origBitStart = 25
            new.currBitOffset = 25
            new.bitLimit = 100
        
        >>> _tempString = bytes(range(256))
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, False, None)
        >>> wSub.bitLength()
        75
        >>> wSub.bitLength() + wSub.getBitOffset()
        100
        >>> wSub.unpack("5B")
        (6, 8, 10, 12, 14)
        
        A call of bitSubWalker(bitOffset=5, relative=False, newBitLimit=60)
        would yield this new StringWalkerBit; note the new bit limit is
        expressed relative to the old original bit start:
        
            new.origBitStart = 25
            new.currBitOffset = 25
            new.bitLimit = 60
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, False, 60)
        >>> wSub.bitLength()
        35
        >>> wSub.bitLength() + wSub.getBitOffset()
        60
        >>> wSub.unpack("3B")
        (6, 8, 10)
        
        A call of bitSubWalker(bitOffset=5, relative=True, newBitLimit=None)
        would yield this new StringWalkerBit:
        
            new.origBitStart = 35
            new.currBitOffset = 35
            new.bitLimit = 100
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, True, None)
        >>> wSub.bitLength()
        65
        >>> wSub.bitLength() + wSub.getBitOffset()
        100
        >>> wSub.unpack("5B")
        (32, 40, 48, 56, 64)
        
        A call of bitSubWalker(bitOffset=5, relative=True, newBitLimit=30)
        would yield this new StringWalkerBit; note that when the relative
        parameter is True, a specified newBitLimit is interpreted as relative
        to the start of the *new* StringWalkerBit, not the old one. It can thus
        be thought of as the bit length of the new walker:
        
            new.origBitStart = 35
            new.currBitOffset = 35
            new.bitLimit = 65
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
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
        value is zero, then the limit for the new StringWalkerBit will be the
        file's size. This is the only way in which limits can be "reset" for
        walkers.
        
        Continuing with the examples based on the "old" StringWalkerBit
        (above), a call of bitSubWalker(5, anchor=True) will return this new
        object:
        
            new.origBitStart = 5
            new.currBitOffset = 5
            new.bitLimit = 100
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
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
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30
        >>> wSub = wb.bitSubWalker(5, anchor=True, newBitLimit=70)
        >>> wSub.bitLength()
        65
        >>> wSub.bitLength() + wSub.getBitOffset()
        70
        
        A call of bitSubWalker(5, anchor=True, newBitLimit=0) results in:
        
        >>> wb = StringWalkerBit(_tempString, bitStart=20, bitLimit=100)
        >>> wb.skipBits(10)  # currOffset is now 30, and there are 50 bits left
        >>> wSub = wb.bitSubWalker(5, anchor=True, newBitLimit=0)
        >>> wSub.bitLength()
        2043
        >>> wSub.bitLength() + wSub.getBitOffset()
        2048
        """
        
        return StringWalkerBit(
          *walkerbitbackend.wkbSubWalkerSetup(
            self.context,
            bitOffset,
            relative,
            anchor,
            newBitLimit))
    
    def byteAlign(self):
        """
        If the phase is nonzero, advances the offset to the next byte and
        resets the phase to zero. Has no effect if the phase is already zero.
        
        >>> wb = StringWalkerBit(b"ABC")
        >>> bitString = wb.unpackBits(5)
        >>> wb.getBitOffset()
        5
        >>> wb.byteAlign()
        >>> wb.getBitOffset()
        8
        """
        
        self.bitAlign()
    
    @staticmethod
    def calcsize(format):
        """
        A static method returning the size of the specified format. We can't
        simply use struct.calcsize, since we define new format specifiers (like
        'T' and 't') that aren't defined in struct.
        
        >>> StringWalkerBit.calcsize("L")
        4
        >>> StringWalkerBit.calcsize("5T2x")
        17
        """
        
        return walkerbitbackend.wkbCalcSize(format)
    
    def chunk(self, byteLength):
        """
        Returns a string of specified length from the current location.
        
        >>> wb = StringWalkerBit(b"ABCDE")
        >>> wb.chunk(1)
        b'A'
        >>> wb.chunk(3)
        b'BCD'
        """
        
        return walkerbitbackend.wkbUnpackBits(self.context, 8 * byteLength)
    
    def getBitOffset(self, relative=False):
        """
        Returns the current offset. This is always relative to the original
        bit start value.
        
        >>> wMain = StringWalkerBit(bytes(range(256)))
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
        
        return walkerbitbackend.wkbGetOffset(self.context, relative)
    
    def getOffset(self, relative=False):
        """
        Returns the current byte offset. This is an integer for backwards
        compatibility, and will be the floor of the actual fractional value.
        The older clients are used to calling getPhase() to get the other part
        of the information from a byte viewpoint.
        
        >>> wMain = StringWalkerBit(bytes(range(256)))
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
        
        return walkerbitbackend.wkbGetOffset(self.context, relative) // 8
    
    def getPhase(self): return self.getBitOffset() % 8
    
    def group(self, format, count, finalCoerce=False):
        """
        Unpacks count records, each of which has format, and returns them in a
        tuple. If the format specifies more than one value per record, then the
        resulting tuple will itself have tuples, one per grouping.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKL")
        >>> wb.group("B", 5)
        (65, 66, 67, 68, 69)
        >>> wb.group("BB", 2)
        ((70, 71), (72, 73))
        >>> wb.reset()
        >>> wb.group("H", 1)
        (16706,)
        >>> wb.reset()
        >>> wb.group("H", 1, finalCoerce=True)
        16706
        """
        
        return walkerbitbackend.wkbGroup(self.context, format, count, finalCoerce)
    
    def groupIterator(self, format, count):
        """
        Like the group method but returns an iterator rather than an actual
        list. This iterator can then be called to get the items in the group.
        
        This method is mostly for backward compatibility.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKL")
        >>> for g in wb.groupIterator("4B", 3): print(g)
        ... 
        (65, 66, 67, 68)
        (69, 70, 71, 72)
        (73, 74, 75, 76)
        >>> wb.atEnd()
        True
        """
        
        return iter(walkerbitbackend.wkbGroup(self.context, format, count, False))
    
    def length(self):
        """
        Returns the byte length still available for unpacking. Note this is a
        float, and will have a nonzero fractional part if the currBitOffset is
        not a multiple of 8.
        
        >>> wb = StringWalkerBit(bytes(range(256)), bitStart=252 * 8)
        >>> wb.length()
        4.0
        >>> bitString = wb.unpackBits(9)
        >>> wb.length()
        2.875
        >>> s = wb.chunk(2)
        >>> wb.length()
        0.875
        """
        
        return walkerbitbackend.wkbBitLength(self.context) / 8
    
    def pascalString(self):
        """
        Reads a Pascal string and returns it as a regular Python string. A
        Pascal string is an old Mac OS construct, comprising a length byte
        immediately followed by that many data bytes.
        
        >>> wb = StringWalkerBit(bytes.fromhex("03 41 42 43 05 61 62 63 64 65"))
        >>> wb.pascalString()
        b'ABC'
        >>> wb.pascalString()
        b'abcde'
        """
        
        return walkerbitbackend.wkbPascalString(self.context)
    
    def piece(self, byteLength, byteOffset=0, relative=True):
        """
        Returns a chunk of data as a new bytestring from anywhere within the
        walker. Does NOT advance the walker.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKLMNO")
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
        
        return walkerbitbackend.wkbPiece(
          self.context,
          8 * byteLength,
          8 * byteOffset,
          relative)
    
    remainingLength = length  # old name for the same method
    
    def reset(self):
        """
        Resets the object so processing restarts at the origBitOffset the
        StringWalkerBit was created with.
        
        >>> wb = StringWalkerBit(bytes(range(256)), bitStart=65*8)
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
        
        walkerbitbackend.wkbReset(self.context)
    
    def rest(self):
        """
        Returns a bytestring with the rest of the unread data. This is exactly
        equivalent to calling self.unpackBits(self.bitLength()).
        
        >>> wb = StringWalkerBit(bytes(range(256)), bitStart=248*8)  # starts at ASCII upper-case A
        >>> wb.unpack("3B")
        (248, 249, 250)
        >>> [c for c in wb.rest()]
        [251, 252, 253, 254, 255]
        
        >>> wb = StringWalkerBit(bytes(range(256)), bitStart=242*8)
        >>> s = wb.unpackBits(85)
        >>> [c for c in wb.rest()]
        [159, 191, 223, 224]
        """
        
        return self.unpackBits(self.bitLength())

    def setBitOffset(self, bitOffset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKL")
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
        
        walkerbitbackend.wkbSetOffset(self.context, bitOffset, relative, okToExceed)

    def setOffset(self, byteOffset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset. This operation always resets the phase to zero.
        
        >>> wb = StringWalkerBit(bytes(range(256)))
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
        
        walkerbitbackend.wkbSetOffset(
          self.context,
          byteOffset * 8,
          relative,
          okToExceed)
    
    def skip(self, byteCount):
        """
        Skips the specified number of bytes.
        
        >>> wb = StringWalkerBit(bytes(range(256)))
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
        
        walkerbitbackend.wkbSkip(self.context, 8 * byteCount)
    
    def skipBits(self, bitsToSkip):
        """
        Skips the specified number of bits, which may be positive or negative.
        
        >>> wb = StringWalkerBit(b"ABCDEFGHIJKL")
        >>> wb.getBitOffset()
        0
        >>> wb.skipBits(19)
        >>> wb.getBitOffset()
        19
        >>> wb.skipBits(-4)
        >>> wb.getBitOffset()
        15
        
        Offsets are pinned to 0 and the current limit:
        
        >>> wb.skipBits(-20000)
        >>> wb.getBitOffset()
        0
        >>> wb.skipBits(20000)
        >>> wb.getBitOffset()
        96
        """
        
        walkerbitbackend.wkbSkip(self.context, bitsToSkip)
    
    def stillGoing(self):
        """
        Returns True if the string has not yet been completely processed.
        
        >>> wb = StringWalkerBit(bytes(range(256)), bitStart=250*8)
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
        
        return not walkerbitbackend.wkbAtEnd(self.context)
    
    def subWalker(self, byteOffset, relative=False, absoluteAnchor=False, newLimit=None):
        """
        Returns a new StringWalkerBit based on the same file as self.
        
        To understand how the parameters work, consider an existing
        StringWalkerBit with these values:
        
            old.origBitStart = 520
            old.currBitOffset = 536
            old.bitLimit = 1024
        
        A call of subWalker(byteOffset=1, relative=False, newLimit=None)
        would yield this new StringWalkerBit:
        
            new.origBitStart = 528
            new.currBitOffset = 528
            new.bitLimit = 1024
        
        >>> _tempString = bytes(range(256))
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1)
        >>> wSub.length()
        62.0
        >>> wSub.length() + wSub.getOffset()
        128.0
        >>> wSub.unpack("5c")
        (b'B', b'C', b'D', b'E', b'F')
        
        A call of subWalker(bytOffset=1, relative=False, newLimit=75)
        would yield this new StringWalkerBit; note the new limit is expressed
        relative to the old original start:
        
            new.origBitStart = 528
            new.currBitOffset = 528
            new.bitLimit = 600
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, newLimit=75)
        >>> wSub.length()
        9.0
        >>> wSub.length() + wSub.getOffset()
        75.0
        >>> wSub.unpackRest("c")
        (b'B', b'C', b'D', b'E', b'F', b'G', b'H', b'I', b'J')
        
        A call of subWalker(byteOffset=1, relative=True, newLimit=None)
        would yield this new StringWalkerBit:
        
            new.origBitStart = 544
            new.currBitOffset = 544
            new.bitLimit = 1024
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, relative=True)
        >>> wSub.length()
        60.0
        >>> wSub.length() + wSub.getOffset()
        128.0
        >>> wSub.unpack("5c")
        (b'D', b'E', b'F', b'G', b'H')
        
        A call of subWalker(byteOffset=1, relative=True, newLimit=7)
        would yield this new StringWalkerBit; note that when the relative
        parameter is True, a specified new limit is interpreted as relative
        to the start of the *new* StringWalkerBit, not the old one. It can thus
        be thought of as the length of the new walker:
        
            new.origBitStart = 544
            new.currBitOffset = 544
            new.bitLimit = 600
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
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
        this value is zero, then the limit for the new StringWalkerBit will be
        the file's size. This is the only way in which limits can be "reset"
        for walkers.
        
        Continuing with the examples based on the "old" StringWalkerBit
        (above), a call of subWalker(1, anchor=True) will return this new
        object:
        
            new.origBitStart = 8
            new.currBitOffset = 8
            new.bitLimit = 1024
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
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
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, absoluteAnchor=True, newLimit=75)
        >>> wSub.length()
        74.0
        >>> wSub.length() + wSub.getOffset()
        75.0
        
        A call of subWalker(1, absoluteAnchor=True, newLimit=0) results in:
        
        >>> wb = StringWalkerBit(_tempString, bitStart=520, bitLimit=1024)
        >>> wb.skip(2)  # currOffset is now 536
        >>> wSub = wb.subWalker(1, absoluteAnchor=True, newLimit=0)
        >>> wSub.length()
        255.0
        >>> wSub.length() + wSub.getOffset()
        256.0
        """
        
        return StringWalkerBit(
          *walkerbitbackend.wkbSubWalkerSetup(
            self.context,
            8 * byteOffset,
            relative,
            absoluteAnchor,
            (None if newLimit is None else 8 * newLimit)))  # 0 stays 0
    
    def unpack(self, format, coerce=True, advance=True):
        """
        Unpacks one or more values from the walker, based on the format
        specified, returning then in a tuple. If advance is False, the walker
        will remain at its current location. If coerce is True and the returned
        tuple has only one element, that element will be returned directly (not
        wrapped in a tuple).
        
        >>> wb = StringWalkerBit(bytearray([128, 129] * 2 + [65, 66]))
        >>> wb.unpack("BBbbxc")
        (128, 129, -128, -127, b'B')
        
        >>> wb = StringWalkerBit(bytearray([255, 254, 254, 255] * 2), endian='<')
        >>> wb.unpack("Hh")
        (65279, -2)
        >>> wb.unpack(">Hh")
        (65534, -257)
        
        >>> wb = StringWalkerBit(bytearray([255, 128, 112, 224] * 4))
        >>> wb.unpack("Ll")
        (4286607584, -8359712)
        >>> wb.unpack("<Ll")
        (3765469439, -529497857)
        
        >>> wb = StringWalkerBit(bytearray([255, 0, 0, 0, 0, 0, 0, 254] * 4), endian='<')
        >>> wb.unpack("Qq")
        (18302628885633695999, -144115188075855617)
        >>> wb.unpack(">Qq")
        (18374686479671623934, -72057594037927682)
        
        >>> wb = StringWalkerBit(bytes.fromhex("41 42 43 44 45 03 58 59 5A 20 20 20"))
        >>> wb.unpack("3s x s 7p", advance=False)
        (b'ABC', b'E', b'XYZ')
        >>> wb.unpack("3s")
        b'ABC'
        """
        
        return walkerbitbackend.wkbUnpack(
          self.context,
          format,
          coerce,
          advance)
    
    def unpackBits(self, bitCount):
        """
        Returns a string with the specified number of bits.
        
        >>> wb = StringWalkerBit(bytes.fromhex("FE FF B4 E6 99"))
        >>> utilities.hexdump(wb.unpackBits(19))
               0 | FEFF A0                                  |...             |
        
        >>> utilities.hexdump(wb.unpackBits(7))
               0 | A6                                       |.               |
        
        >>> utilities.hexdump(wb.unpackBits(4))
               0 | 90                                       |.               |
        """
        
        return walkerbitbackend.wkbUnpackBits(self.context, bitCount)
    
    def unpackBitsGroup(self, bitCountPerItem, itemCount, signed=False):
        """
        Returns a list with itemCount numeric values, each one of which is
        unpacked from the walker in bitCountPerItem chunks. If signed is True
        the resulting values will be interpreted as twos-complement; otherwise
        they will be unsigned.
        
        >>> wb = StringWalkerBit(bytes.fromhex("F5 B3 9E 01 28 44"))
        >>> wb.unpackBitsGroup(2, 8)
        (3, 3, 1, 1, 2, 3, 0, 3)
        >>> wb.reset()
        >>> wb.unpackBitsGroup(2, 8, True)
        (-1, -1, 1, 1, -2, -1, 0, -1)
        >>> wb.reset()
        >>> wb.unpackBitsGroup(6, 8)
        (61, 27, 14, 30, 0, 18, 33, 4)
        >>> wb.unpackBitsGroup(6, 8)
        Traceback (most recent call last):
          ...
        IndexError: Attempt to unpack past end of string!
        """
        
        return walkerbitbackend.wkbUnpackBitsGroup(
          self.context,
          bitCountPerItem,
          itemCount,
          signed)
    
    def unpackRest(self, format, coerce=True, strict=True):
        """
        Returns a tuple with values from the remainder of the string, as per
        the specified format. Members of the returned tuple will themselves be
        tuples, unless coerce is True and the format specifies only a single
        value.
        
        >>> wb = StringWalkerBit(bytearray(range(10)))
        >>> wb.unpack("H")
        1
        >>> wb.unpackRest("BB")
        ((2, 3), (4, 5), (6, 7), (8, 9))
        >>> wb.reset()
        >>> wb.unpackRest("H")
        (1, 515, 1029, 1543, 2057)
        >>> wb.reset()
        >>> wb.unpackRest("H", coerce=False)
        ((1,), (515,), (1029,), (1543,), (2057,))
        
        If strict is True, the bits left must exactly fit the format.
        
        >>> wb.reset()
        >>> ignore = wb.unpackBits(3)
        >>> wb.unpackRest("B", strict=False)
        (0, 8, 16, 24, 32, 40, 48, 56, 64)
        
        >>> wb.reset()
        >>> ignore = wb.unpackBits(3)
        >>> wb.unpackRest("B", strict=True)
        Traceback (most recent call last):
          ...
        ValueError: Leftover bits in unpackRest!
        """
        
        return walkerbitbackend.wkbUnpackRest(self.context, format, coerce, strict)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class StringWalker(StringWalkerBit):
    """
    StringWalkers are actually just thin wrappers around StringWalkerBits.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, s, start=0, limit=None, endian='>'):
        """
        >>> wb = StringWalker(bytes(range(256)), start=65, limit=68)
        >>> wb.rest()
        b'ABC'
        """
        
        super().__init__(
          s = s,
          bitStart = 8 * start,
          bitLimit = (None if limit is None else 8 * limit),
          endian = endian)

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
