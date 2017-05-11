#
# walker.py -- Python front-end for the C-backed StringWalker replacement
#
# Copyright © 2009-2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Front-end module for Python programs using fast StringWalkers.
"""

# Other imports
from fontio3 import walkerbackend

# -----------------------------------------------------------------------------

#
# Classes
#

class StringWalker:
    """
    Very fast StringWalkers.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, s, start=0, limit=None, endian='>'):
        """
        Initializes the StringWalker object.
        """
        
        self.context = walkerbackend.wkNewContext(s, start, limit or len(s), endian == '>')
    
    #
    # Public methods
    #

    def absRest(self, offset):
        """
        Returns a new string representing the whole old string starting at the
        specified absolute offset.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.absRest(0)
        b'ABCDEFGHIJKL'
        >>> w.absRest(8)
        b'IJKL'
        >>> bitString = w.unpackBits(5)
        >>> w.absRest(1)
        Traceback (most recent call last):
          ...
        ValueError: Cannot call absRest when phase is nonzero!
        >>> w = StringWalker(b"ABCDEFGHIJKL", start=3)
        >>> w.getOffset(relative=False), w.getOffset(relative=True)
        (3, 0)
        >>> w.absRest(0)
        b'DEFGHIJKL'
        """
        
        return walkerbackend.wkAbsRest(self.context, offset)
    
    def align(self, multiple=2):
        """
        First byte-aligns the walker, and then aligns to the specified
        multiple.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.unpack("B")
        65
        >>> w.getOffset()
        1
        >>> w.align(multiple=4)
        >>> w.getOffset()
        4
        >>> w.unpack("B")
        69
        >>> w.getOffset()
        5
        >>> w.align(multiple=2)
        >>> w.getOffset()
        6
        """
        
        walkerbackend.wkAlign(self.context, multiple)
    
    def asStringAndOffset(self):
        """
        Returns a pair (s, offset) representing the walker's current state.
        
        >>> s = b"abcdefgh"
        >>> w = StringWalker(s)
        >>> ignore = w.unpack("H")
        >>> t = w.asStringAndOffset()
        >>> t[0] is s
        True
        >>> t[1]
        2
        """
        
        return walkerbackend.wkAsStringAndOffset(self.context)
    
    def atEnd(self):
        """
        Returns True if the string has been completely processed.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.atEnd()
        False
        >>> w.unpack("12s")
        b'ABCDEFGHIJKL'
        >>> w.atEnd()
        True
        >>> w.getOffset()
        12
        """
        
        return walkerbackend.wkAtEnd(self.context)
    
    def bitLength(self):
        """
        Returns the number of bits remaining in the walker.
        
        >>> w = StringWalker(b"ABCD")
        >>> w.bitLength()
        32
        >>> bitString = w.unpackBits(9)
        >>> w.bitLength()
        23
        >>> s = w.chunk(2)
        >>> w.bitLength()
        7
        """
        
        return walkerbackend.wkBitLength(self.context)
    
    def byteAlign(self):
        """
        If the phase is nonzero, advances the offset to the next byte and
        resets the phase to zero. Has no effect if the phase is already zero.
        
        >>> w = StringWalker(b"ABC")
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (0, 5)
        >>> w.byteAlign()
        >>> w.getOffset(), w.getPhase()
        (1, 0)
        """
        
        self.align(1)
    
    @staticmethod
    def calcsize(format):
        """
        A static method returning the size of the specified format. We can't
        simply use struct.calcsize, since we define new format specifiers (like
        'T' and 't') that aren't defined in struct.
        
        >>> StringWalker.calcsize("L")
        4
        >>> StringWalker.calcsize("5T2x")
        17
        """
        
        return walkerbackend.wkCalcSize(format)
    
    def chunk(self, byteLength):
        """
        Returns a string of specified length from the current location.
        
        >>> w = StringWalker(b"ABCDE")
        >>> w.chunk(1)
        b'A'
        >>> w.chunk(3)
        b'BCD'
        """
        
        return walkerbackend.wkUnpackBits(self.context, 8 * byteLength)
    
    def getOffset(self, relative=False):
        """
        Returns the current offset, either absolute or relative to the original
        starting offset.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL", start=3)
        >>> w.getOffset(relative=False)
        3
        >>> w.getOffset(relative=True)
        0
        >>> w.unpack("4B")
        (68, 69, 70, 71)
        >>> w.getOffset(relative=False)
        7
        >>> w.getOffset(relative=True)
        4
        """
        
        return walkerbackend.wkGetOffset(self.context, relative)
    
    def getPhase(self):
        """
        Returns the current phase (i.e. the bit number next to be accessed,
        where 0 is the most significant bit of each byte).
        
        >>> w = StringWalker(b"ABC")
        >>> w.getPhase()
        0
        >>> bitString = w.unpackBits(5)
        >>> w.getPhase()
        5
        >>> bitString2 = w.unpackBits(5)
        >>> w.getPhase()
        2
        """
        
        return walkerbackend.wkGetPhase(self.context)
    
    def group(self, format, count, finalCoerce=False):
        """
        Unpacks count records, each of which has format, and returns them in a
        tuple. If the format specifies more than one value per record, then the
        resulting tuple will itself have tuples, one per grouping.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.group("B", 5)
        (65, 66, 67, 68, 69)
        >>> w.group("BB", 2)
        ((70, 71), (72, 73))
        >>> w.reset()
        >>> w.group("H", 1)
        (16706,)
        >>> w.reset()
        >>> w.group("H", 1, finalCoerce=True)
        16706
        """
        
        return walkerbackend.wkGroup(self.context, format, count, finalCoerce)
    
    def groupIterator(self, format, count):
        """
        Like the group method but returns an iterator rather than an actual
        list. This iterator can then be called to get the items in the group.
        
        This method is mostly for backward compatibility.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> for g in w.groupIterator("4B", 3): print(g)
        ... 
        (65, 66, 67, 68)
        (69, 70, 71, 72)
        (73, 74, 75, 76)
        >>> w.atEnd()
        True
        """
        
        return iter(walkerbackend.wkGroup(self.context, format, count, False))
    
    def length(self, fromStart=False):
        """
        Returns the current available length (as if it were a string).
        
        If fromStart is True, the returned length is the total original length,
        and not just the length of the remaining piece.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL", start=3)
        >>> w.length()
        9
        >>> w.length(fromStart=True)
        9
        >>> w.unpack("4B")
        (68, 69, 70, 71)
        >>> w.length()
        5
        >>> w.length(fromStart=True)
        9
        """
        
        return walkerbackend.wkLength(self.context, fromStart)
    
    def pascalString(self):
        """
        Reads a Pascal string and returns it as a regular Python string. A
        Pascal string is an old Mac OS construct, comprising a length byte
        immediately followed by that many data bytes.
        
        >>> w = StringWalker(bytes.fromhex("03 41 42 43 05 61 62 63 64 65"))
        >>> w.pascalString()
        b'ABC'
        >>> w.pascalString()
        b'abcde'
        """
        
        return walkerbackend.wkPascalString(self.context)
    
    def piece(self, length, offset=0, relative=True):
        """
        Returns a chunk of data as a new string from anywhere within the
        walker. Does NOT advance the walker.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
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
        
        return walkerbackend.wkPiece(self.context, length, offset, relative)
    
    remainingLength = length  # old name for the same method

    def reset(self):
        """
        Resets the object so processing starts either at the absolute beginning
        of the string, or at the offset it started with.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.getOffset()
        0
        >>> w.unpack("6s")
        b'ABCDEF'
        >>> w.getOffset()
        6
        >>> w.reset()
        >>> w.getOffset()
        0
        """
        
        walkerbackend.wkReset(self.context)
    
    def rest(self):
        """
        Returns a string with the rest of the unread data. Note that unlike the
        pure Python version, this version will return fractional bytes.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.unpack("3B")
        (65, 66, 67)
        >>> w.rest()
        b'DEFGHIJKL'
        >>> w.reset()
        >>> s = w.unpackBits(85)  # remaining bits are 011 0100 1100
        >>> tuple(w.rest())  # will parse as 01101001 10000000, or 0x69, 0x80 (105, 128)
        (105, 128)
        """
        
        return walkerbackend.wkRest(self.context)

    def setOffset(self, offset, relative=False, okToExceed=False):
        """
        Sets the offset to the specified value, either absolute or relative to
        the current offset. This operation always resets the phase to zero.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
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
        
        walkerbackend.wkSetOffset(self.context, offset, relative, okToExceed)
    
    def skip(self, byteCount, resetPhase=True):
        """
        Advances the current offset by the specified number of bytes. Reset the
        phase to zero if specified.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
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
        """
        
        walkerbackend.wkSkip(self.context, byteCount, resetPhase);
    
    def skipBits(self, bitCount):
        """
        Advances the phase by the specified number of bits, and then adjusts
        the phase and offset to their corresponding natural values.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
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
        
        walkerbackend.wkSkipBits(self.context, bitCount)
    
    def stillGoing(self):
        """
        The opposite of the atEnd method: returns True if there are still
        unprocessed bytes.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w.stillGoing()
        True
        >>> w.rest()
        b'ABCDEFGHIJKL'
        >>> w.stillGoing()
        False
        """
        
        return not walkerbackend.wkAtEnd(self.context)
    
    def subWalker(self, offset, relative=False, absoluteAnchor=False, newLimit=None):
        """
        Creates a new walker based on the current walker.
        
        In understanding how the 'relative' parameter is interpreted it's
        important to remember that when a StringWalker is created its
        self.offset field is initialized to its startOffset, and NOT to zero.
        This means that self.offset is an offset from the [0] offset of self.s,
        and not from the self.originalStart offset of self.s.

        If the 'relative' argument is False (the default) then the new walker
        starts at an offset of self.originalStart plus the 'offset' argument.
        If a newLimit is specified it is in that same space (i.e.
        self.originalStart plus the 'newLimit' argument is one past the end of
        the subWalker's coverage).

        If the 'relative' argument is True then the new walker starts at an
        offset of self.offset plus the 'offset' argument. If a newLimit is
        specified, it is relative to the current location.
        
        If the 'absoluteAnchor' argument is True, then the 'relative' argument
        is ignored and offset is considered from the start of self.s.
        
        >>> w = StringWalker(b"ABCDEFGHIJKL")
        >>> w2 = w.subWalker(10)
        >>> w.rest(), w2.rest()
        (b'ABCDEFGHIJKL', b'KL')
        >>> w.reset()
        >>> w.chunk(3)
        b'ABC'
        >>> w2 = w.subWalker(0, relative=True)
        >>> w3 = w.subWalker(0, absoluteAnchor=True)
        >>> w.chunk(3), w2.chunk(5), w3.chunk(3)
        (b'DEF', b'DEFGH', b'ABC')
        >>> w.rest(), w2.rest(), w3.rest()
        (b'GHIJKL', b'IJKL', b'DEFGHIJKL')
        >>> w.reset()
        >>> w.chunk(3)
        b'ABC'
        >>> w4 = w.subWalker(4, newLimit=7)
        >>> w4.rest()
        b'EFG'
        >>> w5 = w.subWalker(1, relative=True, newLimit=3)
        >>> w5.rest()
        b'EFG'
        """
        
        return StringWalker(*walkerbackend.wkSubWalkerSetup(self.context, offset, relative, absoluteAnchor, newLimit))
    
    def unpack(self, format, coerce=True, advance=True):
        """
        Unpacks one or more values from the walker, based on the format
        specified, returning then in a tuple. If advance is False, the walker
        will remain at its current location. If coerce is True and the returned
        tuple has only one element, that element will be returned directly (not
        wrapped in a tuple).
        
        >>> fh = bytes.fromhex
        >>> w = StringWalker(fh("80 81 80 81 41 42"))
        >>> w.unpack("BBbbxc")
        (128, 129, -128, -127, b'B')
        
        >>> w = StringWalker(fh("FF FE FE FF FF FE FE FF"), endian='<')
        >>> w.unpack("Hh")
        (65279, -2)
        >>> w.unpack(">Hh")
        (65534, -257)
        
        >>> w = StringWalker(bytes.fromhex("00 01 02 FF FF FE 02 01 00 FE FF FF"))
        >>> w.unpack(">Tt")
        (258, -2)
        >>> w.unpack("<Tt")
        (258, -2)
        
        >>> w = StringWalker(fh("FF 80 70 E0 FF 80 70 E0 FF 80 70 E0 FF 80 70 E0"))
        >>> w.unpack("Ll")
        (4286607584, -8359712)
        >>> w.unpack("<Ll")
        (3765469439, -529497857)
        
        >>> w = StringWalker(bytearray([255, 0, 0, 0, 0, 0, 0, 254] * 4), endian='<')
        >>> w.unpack("Qq")
        (18302628885633695999, -144115188075855617)
        >>> w.unpack(">Qq")
        (18374686479671623934, -72057594037927682)
        
        >>> w = StringWalker(fh("41 42 43 44 45 03 58 59 5A 20 20 20"))
        >>> w.unpack("3s x s 7p", advance=False)
        (b'ABC', b'E', b'XYZ')
        >>> w.unpack("3s")
        b'ABC'
        
        >>> w = StringWalker(fh("3F C0 00 00 00 00 C0 3F"))
        >>> w.unpack(">f")
        1.5
        >>> w.unpack("<f")
        1.5
        
        >>> w = StringWalker(fh("3F F8 00 00 00 00 00 00 00 00 00 00 00 00 F8 3F"))
        >>> w.unpack(">d")
        1.5
        >>> w.unpack("<d")
        1.5
        """
        
        return walkerbackend.wkUnpack(self.context, format, coerce, advance)
    
    def unpack8Bit(self, wantSigned=False):
        """
        Returns an 8-bit quantity, signed or not as specified.
        
        >>> w = StringWalker(bytes.fromhex("41 FF FF"))
        >>> w.unpack8Bit()
        65
        >>> w.unpack8Bit()
        255
        >>> w.unpack8Bit(True)
        -1
        """
        
        return walkerbackend.wkUnpack(self.context, ('b' if wantSigned else 'B'), True, True)
    
    def unpack16Bit(self, wantSigned=False):
        """
        Returns a 16-bit quantity, signed or not as specified. The global
        endian state is used.
        
        >>> w = StringWalker(bytes.fromhex("FF FE FF FE"))
        >>> w.unpack16Bit()
        65534
        >>> w.unpack16Bit(True)
        -2
        
        >>> w = StringWalker(bytes.fromhex("FF FE FF FE"), endian='<')
        >>> w.unpack16Bit()
        65279
        >>> w.unpack16Bit(True)
        -257
        """
        
        return walkerbackend.wkUnpack(self.context, ('h' if wantSigned else 'H'), True, True)
    
    def unpack24Bit(self, wantSigned=False):
        """
        Unpacks a single 24-bit value, signed or not as indicated.
        
        This method works with nonzero phases as well.
        
        >>> w = StringWalker(bytearray([255, 128, 0] * 16), endian='>')
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (16744448, -32768)
        >>> w.getOffset(), w.getPhase()
        (6, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (6, 5)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (15728671, -1048545)
        >>> w.getOffset(), w.getPhase()
        (12, 5)
        
        >>> w = StringWalker(bytearray([255, 128, 0] * 16), endian='<')
        >>> w.skip(1)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (16711808, -65408)
        >>> w.getOffset(), w.getPhase()
        (7, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (7, 5)
        >>> w.unpack24Bit(wantSigned=False), w.unpack24Bit(wantSigned=True)
        (15736576, -1040640)
        >>> w.getOffset(), w.getPhase()
        (13, 5)
        """
        
        # Note we use a custom format code here, 'T' or 't'. Since we're not
        # using the struct module here, it should be OK.
        
        return walkerbackend.wkUnpack(self.context, ('t' if wantSigned else 'T'), True, True)
    
    def unpack32Bit(self, wantSigned=False):
        """
        Returns a 32-bit quantity, signed or not as specified. The global
        endian state is used.
        
        >>> w = StringWalker(bytes.fromhex("FF FF FF FE FF FF FF FE"))
        >>> w.unpack32Bit()
        4294967294
        >>> w.unpack32Bit(True)
        -2
        >>> w = StringWalker(bytes.fromhex("FF FF FF FE FF FF FF FE"), endian='<')
        >>> w.unpack32Bit()
        4278190079
        >>> w.unpack32Bit(True)
        -16777217
        """
        
        return walkerbackend.wkUnpack(self.context, ('l' if wantSigned else 'L'), True, True)
    
    def unpack64Bit(self, wantSigned=False):
        """
        Unpacks a single 64-bit value, signed or not as indicated.
        
        This method works with nonzero phases as well.
        
        >>> w = StringWalker(bytearray([255, 170, 85, 0] * 32))
        >>> w.unpack("Qq")
        (18422630688490149120, -24113385219402496)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (18422630688490149120, -24113385219402496)
        >>> w.getOffset(), w.getPhase()
        (32, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (32, 5)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (17675115746688671775, -771628327020879841)
        >>> w.getOffset(), w.getPhase()
        (48, 5)
        
        >>> w = StringWalker(bytearray([255, 170, 85, 0] * 32), endian='<')
        >>> w.skip(1)
        >>> w.unpack("Qq")
        (18374780672582636970, -71963401126914646)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (18374780672582636970, -71963401126914646)
        >>> w.getOffset(), w.getPhase()
        (33, 0)
        >>> bitString = w.unpackBits(5)
        >>> w.getOffset(), w.getPhase()
        (33, 5)
        >>> w.unpack64Bit(wantSigned=False), w.unpack64Bit(wantSigned=True)
        (17663012507370889290, -783731566338662326)
        >>> w.getOffset(), w.getPhase()
        (49, 5)
        """
        
        return walkerbackend.wkUnpack(self.context, ('q' if wantSigned else 'Q'), True, True)
    
    def unpackBCD(self, count, byteLength=1, coerce=True):
        """
        Unpacks one or more binary-coded decimal values from the stream and
        return a list of them. If coerce is True and count is 1 then the
        simple value is returned, not a list.
        
        >>> w = StringWalker(bytes.fromhex("12 34 56 78 90"))
        >>> w.unpackBCD(2)
        (1, 2)
        >>> w.unpackBCD(2, byteLength=2)
        (34, 56)
        >>> w.unpackBCD(1, byteLength=2)
        78
        >>> w.skip(-1)
        >>> w.unpackBCD(1, byteLength=2, coerce=False)
        (78,)
        """
        
        return walkerbackend.wkUnpackBCD(self.context, count, byteLength, coerce);
    
    def unpackBits(self, bitCount):
        """
        Returns a string with the specified number of bits from the source.
        
        >>> w = StringWalker(b"ABCDE")  # 01000001 01000010 01000011 01000100 01000101
        >>> ord(w.unpackBits(7))
        64
        >>> tuple(w.unpackBits(9))
        (161, 0)
        >>> w.chunk(3)
        b'CDE'
        """
        
        return walkerbackend.wkUnpackBits(self.context, bitCount)

    def unpackRest(self, format, coerce=True):
        """
        Returns a tuple with values from the remainder of the string, as per
        the specified format. Members of the returned tuple will themselves be
        tuples, unless coerce is True and the format specifies only a single
        value.
        
        >>> w = StringWalker(bytearray(range(10)))
        >>> w.unpack("H")
        1
        >>> w.unpackRest("BB")
        ((2, 3), (4, 5), (6, 7), (8, 9))
        >>> w.reset()
        >>> w.unpackRest("H")
        (1, 515, 1029, 1543, 2057)
        >>> w.reset()
        >>> w.unpackRest("H", coerce=False)
        ((1,), (515,), (1029,), (1543,), (2057,))
        """
        
        return walkerbackend.wkUnpackRest(self.context, format, coerce)

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
