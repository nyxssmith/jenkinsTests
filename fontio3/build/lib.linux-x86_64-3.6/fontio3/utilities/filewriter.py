#
# filewriter.py
#
# Copyright © 2009-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
These objects are identical to LinkedWriters as defined in writer.py, with one
critical difference: the string pieces are not retained in memory, but are
written to a temporary file. This allows the creation of enormous writers
without having to worry about slowing down the rest of Python.
"""

# System imports
import collections
import sys
import tempfile

# Other imports
from fontio3 import utilities, utilitiesbackend

# -----------------------------------------------------------------------------

#
# Classes
#

_LinkTuple = collections.namedtuple(
  "_LinkTuple",
  [ 'format',
    'pieceIndex',
    'tagFrom',
    'tagTo',
    'offsetBitDelta',
    'bitLength',
    'negOK',
    'offsetDivisor'])

class LinkedFileWriter:
    """
    """
    
    #
    # Methods
    #
    
    def __del__(self):
        self.backingFile.close()
        self.backingFile = None
    
    def __init__(self):
        """
        """
        
        # When a new LinkedFileWriter is instantiated, its temporary file is
        # created. This does not happen in the reset() method, which is more
        # concerned with clearing out the running indices. Note that the file
        # is closed in the __del__() method.
        
        self.backingFile = tempfile.TemporaryFile()
        self.reset()
    
    @staticmethod
    def _bitsFromNumber(n, keepLowestCount):
        """
        Returns a bitstring with the lowest-order number of specified
        bits from the value of n treated as a bit string. The number n
        may be positive, negative, or zero.
        
        Numbers whose absolute values are extremely large are supported here,
        well beyond the 8-byte limitations of the simple add() method. However,
        any number that tries to fit into too few bits for its significant
        digits will raise an OverflowError.
        
        Note this is vastly simpler (and faster) than the old LinkedWriter
        version, since we can rely on Python 3 and thus to_bytes() method
        present in all integers.
        
        >>> w = LinkedFileWriter
        >>> utilities.hexdump(w._bitsFromNumber(-5, 4))
               0 | B0                                       |.               |
        
        >>> utilities.hexdump(w._bitsFromNumber(5, 4))
               0 | 50                                       |P               |
        
        >>> utilities.hexdump(w._bitsFromNumber(3, 8))
               0 | 03                                       |.               |
        
        >>> n = 0x112233445566778899AABBCCDDEEFF
        >>> utilities.hexdump(w._bitsFromNumber(n, 120))
               0 | 1122 3344 5566 7788  99AA BBCC DDEE FF   |."3DUfw........ |
        
        >>> utilities.hexdump(w._bitsFromNumber(n, 128))
               0 | 0011 2233 4455 6677  8899 AABB CCDD EEFF |.."3DUfw........|
        
        >>> w._bitsFromNumber(15, 3)
        Traceback (most recent call last):
          ...
        OverflowError: int too big to convert
        """
        
        rem = keepLowestCount % 8
        
        if rem:
            n <<= (8 - rem)
            keepLowestCount += (8 - rem)
        
        return n.to_bytes(keepLowestCount // 8, byteorder='big', signed=True)
    
    def _byteLength(self):
        """
        Returns the byte length currently accumulated, as an integer if it is
        an integral number of bytes, or as a float if it is not.
        
        >>> w = LinkedFileWriter()
        >>> w.byteLength
        0
        >>> w.add("LH", 1, 2)
        >>> w.byteLength
        6
        >>> w.addBits(bytes.fromhex("FF FF"), 10)
        >>> w.byteLength
        7.25
        """
        
        if self.bitLength & 7:
            return self.bitLength / 8
        
        return int(self.bitLength // 8)
    
    byteLength = property(_byteLength)
    
    def _makeResolvedIterator(self, **kwArgs):
        """
        Returns an iterator over bytes objects, based on self.pieces but with
        all references resolved. An AssertionError is raised if one or more of
        the following conditions are true:
        
            - A reference is made to a stakeName that is not defined. (Note
              that this assertion can be neutralized using the unresolvedOK
              keyword; this is useful for checksumming, where the whole writer
              might not yet be resolved, but the part being checksummed is).
            
            - A computed offset is negative and self.allowNegativeOffsets()
              has not been called.
            
            - A computed offset is not a multiple of 8.
        """
        
        v = self._resolveVariableFormatOffsets(**kwArgs)
        f = self.backingFile
        
        for format, pieceIndex, tag1, tag2 in self.indexLinks:
            # v[pieceIndex] needs to be changed to the value in the related
            # indexMap (note this is only supported for whole strings).
            thisMap = self.indexMaps[tag1]
            bs = utilitiesbackend.utPack(format, thisMap[tag2])
            v[pieceIndex] = (f.tell(), len(bs), None)
            f.write(bs)
        
        # Now create the actual string list to be returned
        rememberTell = f.tell()
        
        if any((t[2] is not None) and (t[2] & 7) for t in v):
            partial = []
            implode = utilitiesbackend.utImplode
            explode = utilitiesbackend.utExplode
            
            for offset, byteLen, bitCount in v:
                if not byteLen:
                    continue
                
                f.seek(offset)
                bs = f.read(byteLen)
                
                if bitCount is None:
                    if partial:
                        thisBitLen = 8 * len(bs)
                        partial += explode(bs)
                        yield implode(partial[0:thisBitLen])
                        partial = partial[thisBitLen:]
                    
                    else:  # this is purely an accelerator
                        yield bs
                
                else:
                    partial += explode(bs)[0:bitCount]
                    
                    if len(partial) > 7:
                        thisBitLen = 8 * (len(partial) // 8)
                        yield implode(partial[0:thisBitLen])
                        partial = partial[thisBitLen:]
            
            if partial:
                yield implode(partial)
        
        else:
            for offset, byteLen, bitCount in v:
                f.seek(offset)
                bs = f.read(byteLen)
                yield bs
        
        f.seek(rememberTell)
    
    def _resolveVariableFormatOffsets(self, **kwArgs):
        """
        """
        
        # First, fill out v assuming all variable-length links are zero-length,
        # which is how they are to start with. This will give us our first pass
        # at the pieceStarts array.
        
        v = list(self.pieces) + [(0, 0, None)]
        g = (t[1] * 8 if t[2] is None else t[2] for t in v)
        pieceStarts = utilities.cumulCount(g)
        unresolvedOK = kwArgs.get('unresolvedOK', False)
        sawCallable = False
        
        for i, t in enumerate(self.links):
            if unresolvedOK:
                if t.tagFrom not in self.stakes or t.tagTo not in self.stakes:
                    continue
            
            else:
                assert t.tagFrom in self.stakes, "Undefined tagFrom!"
                assert t.tagTo in self.stakes, "Undefined tagTo!"
            
            toStart = pieceStarts[self.stakes[t.tagTo]]
            fromStart = pieceStarts[self.stakes[t.tagFrom]]
            actualBitDelta = (toStart - fromStart) + t.offsetBitDelta
            
            if t.offsetDivisor != 1:
                test = (actualBitDelta & t.offsetDivisor) == 0
                assert test, "Word alignment bad boundary!"
                actualBitDelta //= t.offsetDivisor
            
            test = (actualBitDelta >= 0) or self.negOffsetsOK or t.negOK
            assert test, "Impermissible negative offset!"
            assert (actualBitDelta & 7) == 0, "Not at byte boundary!"
            
            if callable(t.format):
                v[t.pieceIndex] = self.pieces[t.pieceIndex]
                sawCallable = True
            
            elif t.bitLength is None:
                try:
                    bs = utilitiesbackend.utPack(t.format, actualBitDelta // 8)
                
                except ValueError:
                    if self.linkHistory is not None:
                        print(self.linkHistory[i], file=sys.stderr)
                    
                    raise
                
                v[t.pieceIndex] = (self.backingFile.tell(), len(bs), None)
                self.backingFile.write(bs)
            
            else:
                bs = self._bitsFromNumber(actualBitDelta // 8, t.bitLength)
                v[t.pieceIndex] = (self.backingFile.tell(), len(bs), t.bitLength)
                self.backingFile.write(bs)
        
        if not sawCallable:
            return v
        
        # Second, given the current (wrong) pieceStarts, replace all the v[]
        # variable-length entries with the results from calling their format()
        # routines.
        
        for t in self.links:
            if not callable(t.format):
                continue
            
            toStart = pieceStarts[self.stakes[t.tagTo]]
            fromStart = pieceStarts[self.stakes[t.tagFrom]]
            actualBitDelta = (toStart - fromStart) + t.offsetBitDelta
            
            if t.offsetDivisor != 1:
                test = (actualBitDelta & t.offsetDivisor) == 0
                assert test, "Word alignment bad boundary!"
                actualBitDelta //= t.offsetDivisor
            
            test = (actualBitDelta >= 0) or self.negOffsetsOK or t.negOK
            assert test, "Impermissible negative offset!"
            assert (actualBitDelta & 7) == 0, "Not at byte boundary!"
            bs = format(actualBitDelta // 8)
            v[t.pieceIndex] = (self.backingFile.tell(), len(bs), None)
            self.backingFile.write(bs)
        
        # Third, adjust the v[] entries corresponding to the variable-length
        # entries, and recalculate pieceStarts again. Keep doing this until
        # things stop wiggling.
        
        pieceStartsHistory = set([tuple(pieceStarts)])
        
        while True:
            g = (t[1] * 8 if t[2] is None else t[2] for t in v)
            newPieceStarts = utilities.cumulCount(g)
            
            if newPieceStarts == pieceStarts:
                break
            
            pieceStarts = newPieceStarts
            
            if tuple(pieceStarts) in pieceStartsHistory:
                raise ValueError("Critical resize loop!")
            
            pieceStartsHistory.add(tuple(pieceStarts))
            
            for t in self.links:
                if not callable(t.format):
                    continue
                
                toStart = pieceStarts[self.stakes[t.tagTo]]
                fromStart = pieceStarts[self.stakes[t.tagFrom]]
                actualBitDelta = (toStart - fromStart) + t.offsetBitDelta
            
                if t.offsetDivisor != 1:
                    test = (actualBitDelta & t.offsetDivisor) == 0
                    assert test, "Word alignment bad boundary!"
                    actualBitDelta //= t.offsetDivisor
            
                test = (actualBitDelta >= 0) or self.negOffsetsOK or t.negOK
                assert test, "Impermissible negative offset!"
                assert (actualBitDelta & 7) == 0, "Not at byte boundary!"
                bs = format(actualBitDelta // 8)
                v[t.pieceIndex] = (self.backingFile.tell(), len(bs), None)
                self.backingFile.write(bs)
        
        return v
    
    def add(self, format, *args):
        """
        Adds the specified arguments according to the specified format.
        
        >>> w = LinkedFileWriter()
        >>> w.add("h", -15)
        >>> w.add("BB", 2, 3)
        >>> utilities.hexdump(w.binaryString())
               0 | FFF1 0203                                |....            |
        """
        
        self.addString(utilitiesbackend.utPack(format, *args))
    
    def addBits(self, bitString, bitCount):
        """
        Adds the specified number of bits from the bytes in the specified
        bytestring or bytes object. The bits are taken from the high-order end.
        
        >>> w = LinkedFileWriter()
        >>> w.addBits(bytes.fromhex("FF FF"), 9)
        >>> utilities.hexdump(w.binaryString())
               0 | FF80                                     |..              |
        
        >>> w.addBits(bytes.fromhex("55"), 6)
        >>> utilities.hexdump(w.binaryString())
               0 | FFAA                                     |..              |
        """
        
        self.pieces.append((self.backingFile.tell(), len(bitString), bitCount))
        self.backingFile.write(bitString)
        self.bitLength += bitCount
    
    def addBitsFromNumber(self, n, keepLowestCount):
        """
        Adds to the writer the lowest-order number of specified bits from the
        value of n as a bit string. The number n may be positive, negative, or
        zero.
        
        Numbers whose absolute values are extremely large are supported here,
        well beyond the 8-byte limitations of the simple add() method.
        
        >>> w = LinkedFileWriter()
        >>> w.addBitsFromNumber(-5, 4)
        >>> w.addBitsFromNumber(5, 4)
        >>> w.addBitsFromNumber(3, 8)
        >>> w.addBitsFromNumber(0x112233445566778899AABBCCDDEEFF, 120)
        >>> utilities.hexdump(w.binaryString())
               0 | B503 1122 3344 5566  7788 99AA BBCC DDEE |..."3DUfw.......|
              10 | FF                                       |.               |
        
        >>> w.addBitsFromNumber(15, 3)
        Traceback (most recent call last):
          ...
        OverflowError: int too big to convert
        """
        
        bs = self._bitsFromNumber(n, keepLowestCount)
        self.addBits(bs, keepLowestCount)
    
    def addBitsGroup(self, iterable, bitsPerEntry, signed):
        """
        Given an iterable over numeric values, converts the values to
        bitstrings and adds them (in chunks of the specified size and
        signedness) to the writer. This method is an approximate inverse of
        WalkerBit.unpackBitsGroup().
        
        >>> w = LinkedFileWriter()
        >>> v = [4, 12, 2, 9, 10, 5, 5]
        >>> w.addBitsGroup(iter(v), 4, False)
        >>> utilities.hexdump(w.binaryString())
               0 | 4C29 A550                                |L).P            |
        
        >>> w.reset()
        >>> w.addBitsGroup(iter(v), 5, False)
        >>> utilities.hexdump(w.binaryString())
               0 | 2304 9514 A0                             |#....           |
        
        >>> w.reset()
        >>> w.addBitsGroup([-4, -3, -2, -1, 0, 1, 2, 3], 3, True)
        >>> utilities.hexdump(w.binaryString())
               0 | 9770 53                                  |.pS             |
        
        >>> w.reset()
        >>> w.addBitsGroup([-4, -3, -2, -1, 0, 1, 2, 3], 3, False)
        Traceback (most recent call last):
          ...
        ValueError: Value out of range for specified bitsPerEntry!
        """
        
        subDelta = 1 << bitsPerEntry
        
        if signed:
            v = [(n if n >= 0 else n + subDelta) for n in iterable]
        else:
            v = list(iterable)
        
        if any(n < 0 or n >= subDelta for n in v):
            raise ValueError("Value out of range for specified bitsPerEntry!")
        
        s = ''.join(bin(n+subDelta)[3:] for n in v)
        it = (c == '1' for c in s)
        self.addBits(utilitiesbackend.utImplode(it), bitsPerEntry*len(v))
    
    def addDeferredValue(self, format, value=0):
        """
        Adds a placeholder value with the specified format, and returns a stake
        value which can then be used in a subsequent call to setDeferredValue.
        This call differs from addReplaceableString in that a numeric value is
        intended, and that the length, once set here, is not allowed to vary.
        
        The format must be for a single value, not a grouping.
        
        >>> w = LinkedFileWriter()
        >>> w.addString(b"ab")
        >>> stake = w.addDeferredValue("H")
        >>> w.addString(b"yz")
        >>> utilities.hexdump(w.binaryString())
               0 | 6162 0000 797A                           |ab..yz          |
        
        >>> w.setDeferredValue(stake, "h", -1)
        >>> utilities.hexdump(w.binaryString())
               0 | 6162 FFFF 797A                           |ab..yz          |
        """
        
        stake = self.stakeCurrent()
        self.add(format, value)
        return stake
    
    def addGroup(self, format, iterable):
        """
        Adds a group according to the specified format.
        
        >>> w = LinkedFileWriter()
        >>> w.addGroup("4s", [b"abcdefg", b"WXYZ"])
        >>> print(w.binaryString())
        b'abcdWXYZ'
        
        >>> w = LinkedFileWriter()
        >>> w.addGroup("B", [65, 66, 67])
        >>> print(w.binaryString())
        b'ABC'
        
        >>> w = LinkedFileWriter()
        >>> w.addGroup("BB", [[65, 66], [67, 68]])
        >>> print(w.binaryString())
        b'ABCD'
        """
        
        it = iter(iterable)
        
        try:
            first = next(it)
        except StopIteration:
            return
        
        isSingle = False
        
        if isinstance(first, bytes) or isinstance(first, bytearray):
            self.add(format, first)
            isSingle = True
        
        else:
            try:
                self.add(format, *first)
            
            except TypeError:
                self.add(format, first)
                isSingle = True
        
        f = utilitiesbackend.utPack
        
        if isSingle:
            self.addString(b''.join(f(format, obj) for obj in it))
        else:
            self.addString(b''.join(f(format, *obj) for obj in it))
    
    def addIndexMap(self, tag1, theMap):
        """
        Associates the specified map with tag1, which will have been used in a
        related call to addUnresolvedIndex. This map's keys should be tag2
        values from that call, and its values should be the actual index values
        which will replace the placeholders that were added via
        addUnresolvedIndex.
        
        >>> w = LinkedFileWriter()
        >>> w.addUnresolvedIndex("L", 'a', 'x')
        >>> w.addUnresolvedIndex("H", 'a', 'y')
        >>> w.addIndexMap('a', {'x': 12, 'y': 13})
        >>> utilities.hexdump(w.binaryString())
               0 | 0000 000C 000D                           |......          |
        """
        
        if tag1 in self.indexMaps:
            raise ValueError("Tag %r is already in the indexMap!" % (tag1,))
        
        self.indexMaps[tag1] = theMap
    
    def addReplaceableString(self, stakeName, s=''):
        """
        Adds a "placeholder" string to the writer that will possibly be changed
        later on. The specified stakeName will then be used in a subsequent
        call to setReplaceableString() to update the string.
        
        It's OK if the subsequent string has a different length than the
        original placeholder. Links will also update automatically.
        
        >>> w = LinkedFileWriter()
        >>> fromStake = w.stakeCurrent()
        >>> toStake = w.getNewStake()
        >>> w.addUnresolvedOffset("H", fromStake, toStake)
        >>> myStake = w.getNewStake()
        >>> w.addReplaceableString(myStake, b"Fred")
        >>> w.stakeCurrentWithValue(toStake)
        >>> w.add("H", 255)
        >>> utilities.hexdump(w.binaryString())
               0 | 0006 4672 6564 00FF                      |..Fred..        |
        
        >>> w.setReplaceableString(myStake, b"Charlie")
        >>> utilities.hexdump(w.binaryString())
               0 | 0009 4368 6172 6C69  6500 FF             |..Charlie..     |
        """
        
        self.stakeCurrentWithValue(stakeName)
        self.addString(s)
    
    def addString(self, bs):
        """
        Adds a single bytestring.
        
        >>> w = LinkedFileWriter()
        >>> w.addString(b"ABC")
        >>> w.addString(b"def")
        >>> print(w.binaryString())
        b'ABCdef'
        """
        
        self.pieces.append((self.backingFile.tell(), len(bs), None))
        self.backingFile.write(bs)
        self.bitLength += (8 * len(bs))
    
    def addUnresolvedIndex(self, format, tag1, tag2):
        """
        Adds an unresolved value to be provided later. This is useful, for
        instance, for OpenType PosLookupRecords, where the lookupListIndex is
        needed at buildBinary time but won't actually be known until the
        top-level object is being made.

        The two tags are uninterpreted, except that both should be valid as
        dict keys, since a later addIndexMap call (q.v.) will provide a dict
        associated with tag1 mapping tag2 to values to be formatted as
        specified.
        
        >>> w = LinkedFileWriter()
        >>> w.addUnresolvedIndex("L", 'a', 'x')
        >>> w.addUnresolvedIndex("H", 'a', 'y')
        >>> w.addIndexMap('a', {'x': 12, 'y': 13})
        >>> utilities.hexdump(w.binaryString())
               0 | 0000 000C 000D                           |......          |
        """
        
        self.indexLinks.append((format, len(self.pieces), tag1, tag2))
        self.add(format, 0)
    
    def addUnresolvedOffset(self, format, tagFrom, tagTo, **kwArgs):
        """
        Adds an unresolved link with the byte distance from tagFrom to tagTo in
        the final resolved string. The size of this link will either be the
        size of the specified format, or smaller than that if a bitLength is
        also specified.
        
        Note that format may be either a regular format string (like 'H'), or
        else a function. This function should take one argument, a resolved
        numeric distance, and return a binary string representing that number
        in some application-specified optimal manner. This capability is used
        in the CFF code, for example. In this case, no value will be added to
        the writer at this method's call time; instead, the correct length will
        be determined in _makeResolvedIterator and all other offsets will be
        adjusted accordingly.
        
        The following keyword arguments are supported:
        
            bitLength           Only specified if the caller wants a link whose
                                length is smaller than format (i.e. some number
                                of bits). See fontio3.kern.entry for a sample.
                                It is OK to specify a bitLength along with one
                                of the delta keywords (see below).
            
            negOK               A Boolean allowing finer-grained control over
                                the permissibility of negative resolved offsets
                                than the writer's overall control (which is
                                specified via the allowNegativeOffsets() call).
                                Default is that current overall setting.
            
            offsetBitDelta      If a nonzero value is given, it will be added
                                to the final resolved bit offset; note,
                                however, that the final resolved offset must
                                always be on a byte boundary. Defaults to zero.
            
            offsetByteDelta     If a nonzero value is given, eight times the
                                value will be added to the final resolved bit
                                offset; note, however, that the final resolved
                                offset must always be on a byte boundary.
                                Defaults to zero. See fontio3.lcar.lcar for an
                                example.
            
            offsetDivisor       Sometimes a client wishes for the final and
                                resolved offset to be a word or longword offset
                                instead of a byte offset. In this case, specify
                                offsetDivisor as the desired multiple (2 for
                                word, 4 for longword, etc.) Note that this is
                                used to determine the granularity of an
                                offsetMultiDelta, if one is specified. The
                                default is 1 (i.e. normal byte offsets).
            
            offsetMultiDelta    If a nonzero value is given, eight times the
                                value times the offsetDivisor will be added to
                                the final resolved bit offset; note, however,
                                that the final resolved offset must always be
                                on a byte boundary. Defaults to zero.
        
        Note that if more than one delta is specified, the offsetMultiDelta has
        precedence; then the offsetByteDelta; and finally the offsetBitDelta.
        These do not cumulate: only one value is used.
        
        >>> w = LinkedFileWriter()
        >>> w.add("h", -1)
        >>> stake1 = w.stakeCurrent()
        >>> stake2 = w.getNewStake()
        >>> w.addUnresolvedOffset("H", stake1, stake2)
        >>> w.add("h", -2)
        >>> w.addUnresolvedOffset("H", stake1, stake2, offsetByteDelta=10)
        >>> w.add("h", -3)
        >>> w.stakeCurrentWithValue(stake2)
        >>> w.addString(b"Hi there")
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF 0008 FFFE 0012  FFFD 4869 2074 6865 |..........Hi the|
              10 | 7265                                     |re              |
        
        >>> w = LinkedFileWriter()
        >>> w.add("h", -1)
        >>> stake1 = w.stakeCurrent()
        >>> stake2 = w.getNewStake()
        >>> w.addBits(bytes([192]), 2)
        >>> w.addUnresolvedOffset("H", stake1, stake2, bitLength=14)
        >>> w.add("h", -2)
        >>> w.stakeCurrentWithValue(stake2)
        >>> w.add("h", -3)
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF C004 FFFE FFFD                      |........        |
        
        >>> w = LinkedFileWriter()
        >>> w.add("H", 0xABCD)
        >>> stake1 = w.stakeCurrent()
        >>> w.addGroup("H", range(1, 11))
        >>> stake2 = w.getNewStake()
        >>> w.addUnresolvedOffset(
        ...   "h", stake1, stake2, negOK=True, offsetDivisor=2,
        ...   offsetMultiDelta=-70)
        >>> w.addGroup("H", range(1, 11))
        >>> w.addBitsFromNumber(0, 3)
        >>> w.addUnresolvedOffset(
        ...   "l", stake1, stake2, negOK=True, offsetDivisor=2,
        ...   offsetMultiDelta=-70, bitLength=29)
        >>> w.addGroup("H", range(1, 11))
        >>> w.stakeCurrentWithValue(stake2)
        >>> w.add("H", 100)
        >>> utilities.hexdump(w.binaryString())
               0 | ABCD 0001 0002 0003  0004 0005 0006 0007 |................|
              10 | 0008 0009 000A FFDB  0001 0002 0003 0004 |................|
              20 | 0005 0006 0007 0008  0009 000A 1FFF FFDB |................|
              30 | 0001 0002 0003 0004  0005 0006 0007 0008 |................|
              40 | 0009 000A 0064                           |.....d          |
        """
        
        bitLength = kwArgs.get('bitLength', None)
        negOK = kwArgs.get('negOK', self.negOffsetsOK)
        offsetDivisor = kwArgs.get('offsetDivisor', 1)
        offsetMultiDelta = kwArgs.get('offsetMultiDelta')
        offsetByteDelta = kwArgs.get('offsetByteDelta')
        offsetBitDelta = kwArgs.get('offsetBitDelta')
        
        if offsetMultiDelta is not None:
            bitDelta = offsetMultiDelta * offsetDivisor * 8
        elif offsetByteDelta is not None:
            bitDelta = offsetByteDelta * 8
        elif offsetBitDelta is not None:
            bitDelta = offsetBitDelta
        else:
            bitDelta = 0
        
        self.links.append(_LinkTuple(
          format,
          len(self.pieces),
          tagFrom,
          tagTo,
          bitDelta,
          bitLength,
          negOK,
          offsetDivisor))
        
        if callable(format):
            self.addString(b'')
        elif bitLength is None:
            self.add(format, 0)
        else:
            self.addBitsFromNumber(0, bitLength)
        
        if self.linkHistory is not None:
            self.linkHistory.append(inspect.stack()[1][1:4])
    
    def alignToBitMultiple(self, multiple):
        """
        If the current bit length for the writer is not a multiple of multiple,
        zero bits are added to bring it up to that alignment.
        
        >>> w = LinkedFileWriter()
        >>> w.add("H", 1)  # length is now 16 bits
        >>> w.byteLength
        2
        >>> w.alignToBitMultiple(5)  # will bring length to 20 bits
        >>> w.byteLength
        2.5
        """
        
        excessBits = self.bitLength % multiple
        
        if excessBits:
            neededBits = multiple - excessBits
            s = b'\x00' * ((neededBits + 7) // 8)
            self.addBits(s, neededBits)
    
    def alignToByteMultiple(self, multiple=1):
        """
        Adds zero bits, if needed, to bring the current bit length of the
        writer up to an integral number of bytes.
        
        >>> w = LinkedFileWriter()
        >>> w.add("H", 2)
        >>> w.byteLength
        2
        >>> w.alignToByteMultiple(16)
        >>> w.byteLength
        16
        """
        
        self.alignToBitMultiple(8 * multiple)
    
    def allowNegativeOffsets(self):
        """
        If the resolution to an unresolved offset may legitimately be negative,
        then this method must be called before binaryString is called, or an
        AssertionError will be raised.
        
        >>> w = LinkedFileWriter()
        >>> backStake = w.stakeCurrent()
        >>> w.add("H", 5)
        >>> w.addString(b"Hello!")
        >>> fwdStake = w.stakeCurrent()
        >>> w.addUnresolvedOffset("h", fwdStake, backStake)
        >>> utilities.hexdump(w.binaryString())
        Traceback (most recent call last):
          ...
        AssertionError: Impermissible negative offset!
        
        >>> w.allowNegativeOffsets()
        >>> utilities.hexdump(w.binaryString())
               0 | 0005 4865 6C6C 6F21  FFF8                |..Hello!..      |
        """
        
        self.negOffsetsOK = True
    
    def binaryString(self):
        """
        """
        
        return b''.join(self._makeResolvedIterator())
    
    def checkSum(self, start=None, stop=None, **kwArgs):
        """
        Returns the checksum on the current state of the LinkedWriter, without
        actually creating a single big string. Normally this operates over the
        entire LinkedWriter, but the caller may specify a start and stop byte
        value to restrict the checksum to only that portion.
        
        >>> w = LinkedFileWriter()
        >>> w.add("B2H", 1, 0x203, 0x405)
        >>> print(hex(w.checkSum()))
        0x6020304
        
        >>> print(hex(w.checkSum(start=2, stop=4)))
        0x3040000
        """
        
        start = (0 if start is None else start)
        stop = (self.byteLength if stop is None else stop)
        currMod = cumul = currPosition = 0
        f = utilitiesbackend.utChecksum
        
        for s in self._makeResolvedIterator(**kwArgs):
            sOrigOrig = s
            
            if currPosition >= stop:
                break
            
            elif (currPosition + len(s)) < start:
                currPosition += len(s)
                continue
            
            else:
                # we know it intersects
                delFromFront = max(0, start - currPosition)
                delFromBack = max(0, (currPosition + len(s)) - stop)
                
                if delFromFront and delFromBack:
                    s = s[delFromFront:-delFromBack]
                elif delFromFront:
                    s = s[delFromFront:]
                elif delFromBack:
                    s = s[:-delFromBack]
            
            sOrig = s
            
            if currMod:
                s = (b'\x00' * currMod) + s
            
            cumul += f(s)
            currMod = (currMod + (len(sOrig) % 4)) % 4
            currPosition += len(sOrigOrig)
        
        return cumul % 0x100000000
    
    def deleteIndexMap(self, tag):
        """
        Removes the specified index map.
        """
        
        if tag in self.indexMaps:
            del self.indexMaps[tag]
    
    def enableHistory(self):
        """
        Turns on link history gathering.
        """
        
        self.linkHistory = [None] * len(self.links)
    
    def getNewIndexTag(self):
        """
        Returns a unique tag (string), not currently in use, so clients of the
        addUnresolvedIndex() method can be sure they're not colliding with a
        tag which may have been added by some other part of a large-scale
        buildBinary() train.
        
        >>> w = LinkedFileWriter()
        >>> w.getNewIndexTag()
        'Index tag 1'
        
        Note that the index must be used for a new one to be generated:
        
        >>> tag1 = w.getNewIndexTag()
        >>> tag1
        'Index tag 1'
        >>> w.addUnresolvedIndex("H", tag1, 'A')
        >>> w.getNewIndexTag()
        'Index tag 2'
        """
        
        i = 1
        s = "Index tag 1"
        present = set(t[2] for t in self.indexLinks)
        
        while s in present:
            i += 1
            s = "Index tag %d" % (i,)
        
        return s
    
    def getNewStake(self):
        """
        Returns a unique stake value not currently in use.
        
        >>> w = LinkedFileWriter()
        >>> s1 = w.getNewStake()
        >>> s2 = w.getNewStake()
        >>> s1 != s2
        True
        """
        
        retVal = self.nextAvailableStake
        self.nextAvailableStake += 1
        return retVal
    
    def reset(self):
        """
        """
        
        self.backingFile.seek(0)
        self.backingFile.truncate()
        self.pieces = []
        self.links = []
        self.linkHistory = None
        self.indexLinks = []
        self.indexMaps = {}
        self.stakes = {}  # stakeName -> index in self.pieces
        self.nextAvailableStake = 1
        self.negOffsetsOK = False
        self.bitLength = 0
    
    def setDeferredValue(self, stakeName, format, value):
        """
        Given a deferred value added earlier, replace it with a new value. Note
        the new value must take the same number of bytes as the original value;
        if you need to add a potentially variably-sized piece of data, use the
        addReplaceableString()/setReplaceableString() methods instead.
        
        >>> w = LinkedFileWriter()
        >>> w.addString(b"ab")
        >>> stake = w.addDeferredValue("H")
        >>> w.addString(b"yz")
        >>> utilities.hexdump(w.binaryString())
               0 | 6162 0000 797A                           |ab..yz          |
        
        >>> w.setDeferredValue(stake, "h", -1)
        >>> utilities.hexdump(w.binaryString())
               0 | 6162 FFFF 797A                           |ab..yz          |
        """
        
        assert stakeName in self.stakes, "Undefined stake!"
        bs = utilitiesbackend.utPack(format, value)
        pieceIndex = self.stakes[stakeName]
        piece = self.pieces[pieceIndex]
        assert piece[2] is None, "Cannot set deferred value with bit width!"
        test = (len(bs) == piece[1])
        assert test, "Cannot change length via setDeferredValue()!"
        self.pieces[pieceIndex] = (self.backingFile.tell(), len(bs), None)
        self.backingFile.write(bs)
        # no change to self.bitLength...
    
    def setReplaceableString(self, stakeName, s):
        """
        Sets a new value for a string that was added earlier. It's OK if the
        new string's length is not the same as the original string's length.
        
        >>> w = LinkedFileWriter()
        >>> fromStake = w.stakeCurrent()
        >>> toStake = w.getNewStake()
        >>> w.addUnresolvedOffset("H", fromStake, toStake)
        >>> myStake = w.getNewStake()
        >>> w.addReplaceableString(myStake, b"Fred")
        >>> w.stakeCurrentWithValue(toStake)
        >>> w.add("H", 255)
        >>> utilities.hexdump(w.binaryString())
               0 | 0006 4672 6564 00FF                      |..Fred..        |
        
        >>> w.setReplaceableString(myStake, b"Charlie")
        >>> utilities.hexdump(w.binaryString())
               0 | 0009 4368 6172 6C69  6500 FF             |..Charlie..     |
        """
        
        assert stakeName in self.stakes, "Undefined stake!"
        oldLen = self.pieces[self.stakes[stakeName]][1]
        self.bitLength += (8 * (len(s) - oldLen))
        self.pieces[self.stakes[stakeName]] = (self.backingFile.tell(), len(s), None)
        self.backingFile.write(s)
    
    def stakeCurrent(self):
        """
        Associates the current offset with a unique stake value, which is
        returned from this method.
        
        >>> w = LinkedFileWriter()
        >>> startStake = w.stakeCurrent()
        >>> futureStake = w.getNewStake()
        >>> w.addString(b"IJKL")
        >>> w.addUnresolvedOffset("L", startStake, futureStake)
        >>> w.addString(b"WXYZ")
        >>> w.stakeCurrentWithValue(futureStake)
        >>> w.add("h", -1)
        >>> utilities.hexdump(w.binaryString())
               0 | 494A 4B4C 0000 000C  5758 595A FFFF      |IJKL....WXYZ..  |
        """
        
        stakeValue = self.getNewStake()
        
        if stakeValue not in self.stakes:
            self.stakes[stakeValue] = len(self.pieces)
        else:
            raise ValueError("Duplicate stake!")
        
        return stakeValue
    
    def stakeCurrentWithValue(self, stakeValue):
        """
        Associates the current offset with the specified stakeValue, which will
        have been allocated earlier by the client via a call to getNewStake().
        
        >>> w = LinkedFileWriter()
        >>> startStake = w.stakeCurrent()
        >>> futureStake = w.getNewStake()
        >>> w.addString(b"IJKL")
        >>> w.addUnresolvedOffset("L", startStake, futureStake)
        >>> w.addString(b"WXYZ")
        >>> w.stakeCurrentWithValue(futureStake)
        >>> w.add("h", -1)
        >>> utilities.hexdump(w.binaryString())
               0 | 494A 4B4C 0000 000C  5758 595A FFFF      |IJKL....WXYZ..  |
        """
        
        if stakeValue not in self.stakes:
            self.stakes[stakeValue] = len(self.pieces)
        else:
            raise ValueError("Duplicate stake!")
    
    def writeToFile(self, path):
        """
        """
        
        with open(path, "wb") as f:
            for bs in self._makeResolvedIterator():
                f.write(bs)

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
    _test()
