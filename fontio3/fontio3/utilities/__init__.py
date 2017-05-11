#
# __init__.py
#
# Copyright © 2004-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Package file for fontio3.utilities.
"""

# System imports
import builtins
import collections
import functools
import io
import itertools
import logging
import math
import operator
import re
import struct
import sys
import textwrap

# Other imports
from fontio3 import utilitiesbackend

# -----------------------------------------------------------------------------

#
# Exceptions
#

class CycleError(LookupError):
    """
    Exception class raised when a fontdata object has references to itself,
    either directly or via multiple levels of children.
    """
    
    pass

class InvalidDeleteMissingGlyphID(LookupError):
    """
    Exception class raised when a renumberGlyphIndices message is propagating
    throughout an object hierarchy with keepMissing set to False, and a class
    somewhere objects that it cannot delete the missing glyph ID.
    """
    
    pass

class MergeSyncFailure(ValueError):
    """
    This exception is raised when an attempt is made to combine or merge
    objects of different lengths. It is used primarily in the hints package.
    """
    
    pass

class ValueTooLargeForFormat(ValueError):
    """
    Exception raised when StringWriter objects attempt to write a value which
    is too big for the specified format (e.g. writing 300 with a "B" format).
    It's unfortunate that the struct module doesn't raise any exceptions by
    itself, so we have to catch them.
    """
    
    pass

class ScalerError(ValueError):
    """
    Exception to be raised when calls to a scaler fail, for example:
        try: scaler.doSomething()
        except: raise ScalerError()
    This is used in validation to get more fine-grained exception handling.
    """
    
    pass

class SH(logging.StreamHandler):
    def emit(self, record):
        record.msg = record.msg[2] % record.msg[1]
        super(SH, self).emit(record)

class LA(logging.LoggerAdapter):
    def getChild(self, s):
        if isinstance(s, bytes):
            s = str(s, 'ascii')
        
        sNew = '.'.join([self.extra['customlocation'], s])
        return type(self)(self.logger, {'customlocation': sNew})

# -----------------------------------------------------------------------------

#
# Private constants
#

_validStructFormats = frozenset("><!=@")
_patComment = re.compile(r"(/\*)|(\*/)")
_patNonWS = re.compile(r"\s+")
_patPSNameVal = re.compile("[A-Za-z0-9._]")
_patTagMin = re.compile(r'[A-Za-z][A-Za-z0-9 ]{3}')
_patTagPrv = re.compile(r'[A-Z][A-Z0-9 ]{3}')

_validSparkStarts = frozenset({
  b"\x7F\xF8",
  b"\x7F\xF9",
  b"\xB0\xF8\x7F",
  b"\xB0\xF9\x7F"})

_validRegisteredTags = {'ital', 'opsz', 'slnt', 'wdth', 'wght'}

# -----------------------------------------------------------------------------

#
# Internal functions
#

if 0:
    def __________________(): pass

def _binaryAccumulator(x, y):
    return 2 * x + y

def _binaryDecomposer(v):
    r = v[0] % 2
    v[0] //= 2
    return r

def _byteOrderMarkIsBigEndian(c):
    """
    Takes a single-byte string representing a byte-ordering character as
    defined by the struct module and returns True if that character resolves to
    big-endian.
    
    >>> _byteOrderMarkIsBigEndian(">")
    True
    >>> _byteOrderMarkIsBigEndian("<")
    False
    """
    
    return struct.unpack(c + "H", b"\x00\x01")[0] == 1

def _hexline(s):
    """
    Formats a single line of from 1 to 16 bytes for hexdump. The argument must
    be a bytes or bytearray object.
    
    >>> _hexline(b"A")
    '41                                       |A               |'
    >>> _hexline(bytearray(b"A"))
    '41                                       |A               |'
    >>> _hexline(b"ABCDEFGH")
    '4142 4344 4546 4748                      |ABCDEFGH        |'
    >>> _hexline(b"ABCDEFG")
    '4142 4344 4546 47                        |ABCDEFG         |'
    """
    
    sv = (["%0.2X" % x for x in s] + ["  "] * 15)[:16]
    c = (''.join(('.', chr(x))[32 <= x < 127] for x in s) + " " * 15)[:16]
    return "%s%s %s%s %s%s %s%s  %s%s %s%s %s%s %s%s |%s|" % tuple(sv + [c])

def _imageline(width, s):
    """
    Creates a line of dots and Xs representing the binary data in s. The
    binary data argument must be a bytes or bytearray object.
    
    >>> _imageline(16, b"A")
    '.X.....X'
    >>> _imageline(8, bytearray([0x55]))
    '.X.X.X.X'
    """
    
    v = []
    
    for n in s:
        v.extend(binlist(n, 8))
    
    l = ''.join([['.', 'X'][x] for x in v])
    return l[:width]

def _polarizeFormat(s, desiredByteOrdering='>'):
    """
    Returns a struct formatting string based on the specified input string,
    with a prepended ">" or "<" if one is not already there (depending on the
    state of the desiredByteOrdering argument). If a byte-ordering character is
    already present it is left alone.
    
    >>> _polarizeFormat("H")
    '>H'
    >>> _polarizeFormat("<H")
    '<H'
    >>> _polarizeFormat("H", ">")
    '>H'
    >>> _polarizeFormat(">H", ">")
    '>H'
    >>> _polarizeFormat("<H", ">")
    '<H'
    """
    
    sv = ([s] if s[0] in _validStructFormats else [desiredByteOrdering, s])
    return ''.join(sv)

def _printxheader(x_lo, width, stream):
    """
    Prints the top header for printglyph.
    """
    
    r = list(range(x_lo, x_lo + width))
    print("     %s" % ''.join([str(abs(x)//100) for x in r]), file=stream)
    print("     %s" % ''.join([str((abs(x) % 100)//10) for x in r]), file=stream)
    print("     %s" % ''.join([str(abs(x) % 10) for x in r]), file=stream)

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def binlist(x, width=0):
    """
    Returns a list of 0s and 1s representing the binary value of x, zero-
    padded on the left to width elements.
    
    >>> binlist(100)
    [1, 1, 0, 0, 1, 0, 0]
    >>> binlist(100, width=16)
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0]
    """
    
    if width:
        return list(int(c) for c in bin(x)[2:].rjust(width, '0'))
    
    return list(int(c) for c in bin(x)[2:])

def ceilingRound(x, castType=None):
    """
    "Rounds" by taking the ceiling.
    
    >>> v = [-14, -9.75, -9.5, -8.5, 0, 4.5, 5.5, 12]
    >>> [ceilingRound(n) for n in v]
    [-14, -9.0, -9.0, -8.0, 0, 5.0, 6.0, 12]
    
    >>> [ceilingRound(n, int) for n in v]
    [-14, -9, -9, -8, 0, 5, 6, 12]
    """
    
    return (castType or type(x))(math.ceil(x))

def characterize(x):
    """
    Creates a characterization of object x, which includes what kind of object
    it is (i.e. is it list-like, dict-like or other), as well as whether it is
    a simple type..

    Returns a pair (isSimple, kind) where isSimple now is always True (since
    attrobjs no longer exist), and where kind is 'dict', 'list' or 'other'.
    
    >>> characterize(15)
    (True, 'other')
    >>> characterize([1, 2, 3])
    (True, 'list')
    >>> characterize({'a': 1, 'b': 2})
    (True, 'dict')
    >>> characterize("some text")
    (True, 'other')
    """
    
    if isinstance(x, str):
        return (True, 'other')
    
    try:
        for value in x.values():
            isSimple, kind = characterize(value)
            
            if not isSimple:
                return (False, 'dict')
        
        else:
            return (True, 'dict')
    
    except AttributeError:
        try:
            for value in x:
                isSimple, kind = characterize(value)
                
                if not isSimple:
                    return (False, 'list')
            
            else:
                return (True, 'list')
        
        except TypeError:
            return (True, 'other')

def cleanText(s):
    """
    Returns a version of the string s with /* */ comment blocks removed
    (including support for nested comments), and with whitespace removed.
    
    >>> cleanText("")
    ''
    
    >>> cleanText("Just whitespace here")
    'Justwhitespacehere'
    
    >>> cleanText("ABC /* DEF */ XYZ")
    'ABCXYZ'
    
    >>> cleanText("ABC /* DEF /* GHI */ UVW */ XYZ")
    'ABCXYZ'
    
    >>> cleanText("/*")
    Traceback (most recent call last):
      ...
    ValueError: Unbalanced comment delimiters: '/*'
    
    >>> cleanText("*/")
    Traceback (most recent call last):
      ...
    ValueError: Unbalanced comment delimiters: '*/'
    """
    
    v = [obj for obj in _patComment.split(s) if obj]
    removes = []
    currDepth = 0
    currStart = None
    
    for i, obj in enumerate(v):
        if obj == '/*':
            if currDepth == 0:
                currStart = i
            
            currDepth += 1
        
        elif obj == '*/':
            if currDepth == 0:
                raise ValueError("Unbalanced comment delimiters: %r" % (s,))
            
            currDepth -= 1
            
            if currDepth == 0:
                removes.append((currStart, i))
                currStart = None
    
    if currDepth:
        raise ValueError("Unbalanced comment delimiters: %r" % (s,))
    
    for first, last in reversed(removes):
        del v[first:last+1]
    
    s = ''.join(v)
    return ''.join(_patNonWS.split(s))

def constrainedOrderItems(mapping, orderDependencies):
    """
    Given a mapping and a dict mapping keys to sets of required keys, returns a
    generator over (key, value) pairs from mapping respecting the ordering
    implied by this set of dependencies. A ValueError is raised if a cycle is
    encountered
    
    >>> d = {'a': 5, 'b': 9, 'i': 300}
    >>> od = {'a': {'i'}, 'b': {'a'}}  # a depends on i, b depends on a
    >>> list(constrainedOrderItems(d, od))
    [('i', 300), ('a', 5), ('b', 9)]
    
    Any order dependency keys or set elements that aren't actually present in
    mapping will be ignored; note that the generator has to actually be used
    for this ValueError to arise.
    
    >>> od['x'] = {'a'}
    >>> od['b'].add('r')
    >>> list(constrainedOrderItems(d, od))
    [('i', 300), ('a', 5), ('b', 9)]
    
    >>> od['i'] = {'b'}  # makes it circular
    >>> list(constrainedOrderItems(d, od))
    Traceback (most recent call last):
      ...
    ValueError: Cycle detected in orderDependencies!
    """
    
    dOrdDep = {}
    allKeys = set(mapping)
    
    for dep, upon in orderDependencies.items():
        if dep not in allKeys:
            continue
        
        s = {k for k in upon if k in allKeys}
        
        if s:
            dOrdDep[dep] = s
    
    toDo = set(mapping)
    done = set()
    
    while toDo:
        for k in toDo:
            if (k in dOrdDep) and (dOrdDep[k] - done):
                continue
            
            yield (k, mapping[k])
            done.add(k)
        
        if not done:
            raise ValueError("Cycle detected in orderDependencies!")
        
        toDo -= done

def cumulCount(iterable, wantEndIndices=False, addExtraValue=False, adjustment=0):
    """
    Given an iterable whose items are integers representing lengths of some
    sequence, returns a list with cumulative counts. The process is controlled
    by these arguments:
    
        addExtraValue       If True, an extra value will be added at one end of
                            the returned list. This will be the first unused
                            index at the end if wantEndIndices is False; or a
                            fixed value of -1 at the front if wantEndIndices is
                            True.
        
        adjustment          A constant value to be added to all numbers in the
                            returned list. Useful for getting 1-based indices,
                            Default is zero.
        
        wantEndIndices      If True, the values returned will be the indices of
                            the last member of each subitem from the iterable;
                            if False, the indices of the first member are used.
                            Default is False.
    
    >>> v = [4, 2, 6, 9]
    >>> cumulCount(v)
    [0, 4, 6, 12]
    >>> cumulCount(v, wantEndIndices=True)
    [3, 5, 11, 20]
    >>> cumulCount(v, adjustment=1)
    [1, 5, 7, 13]
    >>> cumulCount(v, wantEndIndices=True, adjustment=1)
    [4, 6, 12, 21]
    >>> cumulCount(v, addExtraValue=True)
    [0, 4, 6, 12, 21]
    >>> cumulCount(v, wantEndIndices=True, addExtraValue=True)
    [-1, 3, 5, 11, 20]
    """
    
    r = []
    
    if wantEndIndices:
        n = adjustment - 1
        
        if addExtraValue:
            r.append(n)
        
        for thisLen in iterable:
            n += thisLen
            r.append(n)
    
    else:
        n = adjustment
        
        for thisLen in iterable:
            r.append(n)
            n += thisLen
        
        if addExtraValue:
            r.append(n)
    
    return r

debugStream = io.StringIO

def diffDict(old, new):
    """
    For two given dictionaries, this function determines which keys in new are
    added (i.e. not in old), which keys are in old but no longer in new, and
    which keys are different between the two. Three sets are returned: added,
    deleted and changed.
    
    >>> d1 = {'a': 2, 'c': 5, 'd': 9, 'e': -3}
    >>> d2 = {'a': 3, 'b': 8, 'e': -3}
    >>> diffDict(d1, d2) == ({'b'}, {'c', 'd'}, {'a'})
    True
    """
    
    unionKeys = set(old) | set(new)
    added, deleted, changed = set(), set(), set()
    
    for key in unionKeys:
        if key in new and key not in old:
            added.add(key)
        elif key in old and key not in new:
            deleted.add(key)
        elif old[key] != new[key]:
            changed.add(key)
    
    return added, deleted, changed

def dumpBinStringToCUnsignedLongs(s):
    """
    Dumps the binary string to stdout in a form suitable for inclusion in C
    code. The argument must be a bytes or bytearray object.
    
    >>> s = utilitiesbackend.utPack(">5L", 1, 3, 5, 7, 8)
    >>> dumpBinStringToCUnsignedLongs(s)
    unsigned long  data[5] = {
        0x00000001UL,   /* [0] */
        0x00000003UL,   /* [1] */
        0x00000005UL,   /* [2] */
        0x00000007UL,   /* [3] */
        0x00000008UL};  /* [4] */
    """
    
    assert (len(s) % 4) == 0, "String must be multiple of 4 long"
    numLongs = len(s) // 4
    maxTagLen = len(str(numLongs - 1)) + 2  # the 2 extra are for the brackets
    print("unsigned long  data[%d] = {" % numLongs)
    
    for i in range(numLongs):
        x = struct.unpack(">L", s[4*i:4*i+4])[0]
        n = ("[%d]" % i).rjust(maxTagLen)
        
        if i == (numLongs - 1):
            print("    0x%0.8XUL};  /* %s */" % (x, n))
        else:
            print("    0x%0.8XUL,   /* %s */" % (x, n))

def ensureBytes(obj):
    """
    Given the change from Python 2 to Python 3 with respect to strings
    and bytes, it is necessary to make sure that objects are of the
    correct kind during fromwalker() or buildBinary() calls. This
    function, and its twin ensureUnicode(), accomplish this.
    
    >>> s = b"abc"
    >>> s is ensureBytes(s)
    True
    
    >>> s = bytearray([97, 98, 99])
    >>> s is ensureBytes(s)
    True
    
    >>> ensureBytes('abc')
    b'abc'
    
    >>> ensureBytes([97, 98, 99])
    b'abc'
    
    >>> ensureBytes(97)
    b'a'
    """
    
    if isinstance(obj, (bytes, bytearray)):
        return obj
    
    if isinstance(obj, str):
        return bytes(obj, 'utf-8')
    
    try:
        len(obj)
        r = bytes(obj)
    
    except TypeError:
        r = bytes([obj])
    
    return r

def ensureUnicode(obj):
    """
    Given the change from Python 2 to Python 3 with respect to strings
    and bytes, it is necessary to make sure that objects are of the
    correct kind during fromwalker() or buildBinary() calls. This
    function, and its twin ensureBytes(), accomplish this.
    
    >>> s = "abc"
    >>> s is ensureUnicode(s)
    True
    
    >>> ensureUnicode(b'abc')
    'abc'
    
    >>> ensureUnicode(bytearray([97, 98, 99]))
    'abc'
    
    >>> ensureUnicode([97, 98, 99])
    'abc'
    
    >>> ensureUnicode(97)
    'a'
    """
    
    if isinstance(obj, str):
        return obj
    
    try:
        r = str(obj, 'utf-8')
    
    except TypeError:
        try:
            len(obj)
            r = str(bytearray(obj), 'utf-8')
        
        except TypeError:
            r = str(bytearray([obj]), 'utf-8')
    
    return r

def enumerateBackwards(seq):
    """
    Returns a generator which, like enumerate, returns (index, obj) pairs where
    obj are taken in reverse order from seq (which must be a sequence, not just
    an iterator). The important thing here is that the index values track in
    original sequence, not the reversed sequence.
    
    It surprises me that this functionality is not an option in enumerate().
    
    >>> list(enumerateBackwards(["cat", "dog", "hippo"]))
    [(2, 'hippo'), (1, 'dog'), (0, 'cat')]
    """
    
    for n in range(len(seq) - 1, -1, -1):
        yield (n, seq[n])

def explode(s):
    """
    Given a string, takes each byte in turn and change it into eight 0s or 1s.
    Then return all these joined into a single list.
    
    >>> explode("ABC")
    [0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1]
    """
    
    return utilitiesbackend.utExplode(s)

def explodeFull(iterator, **kwArgs):
    """
    Given an iterator over values (which may be characters or integers),
    returns a generator over 0s and 1s. Several keywords control the process:
    
        groupSize       The number of bits per group. Default is 32 for numeric
                        values and is always 8 for characters. Note that this
                        value does not necessarily need to be a multiple of 2.
        
        ignoreCount     Normally the generator will start with the first
                        available bit of the first value. If this count is
                        nonzero, then that many bits will be skipped before the
                        first bit is yielded.
        
        isLSBFirst      If True, objects obtained from the iterator will have
                        their resulting bits reversed for the output generator.
                        Default is False. Note this happens item-by-item, and
                        not over the whole input iterator.
        
        isSigned        If True, signed values are present in the input
                        iterator. This even applies to characters. Default is
                        False.
        
        wantCount       Number of values actually wanted from the generator; if
                        None (the default) then all values will be returned.
    
    >>> list(explodeFull([29], groupSize=8))
    [0, 0, 0, 1, 1, 1, 0, 1]
    >>> list(explodeFull([29], groupSize=8, isLSBFirst=True))
    [1, 0, 1, 1, 1, 0, 0, 0]
    >>> list(explodeFull([29], groupSize=8, ignoreCount=3))
    [1, 1, 1, 0, 1]
    >>> list(explodeFull("ABC"))
    [0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1]
    >>> list(explodeFull("ABC", wantCount=9))
    [0, 1, 0, 0, 0, 0, 0, 1, 0]
    >>> list(explodeFull("ABC", isLSBFirst=True))
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0]
    >>> list(explodeFull([-8, -4, 0, 4, 7], isSigned=True, groupSize=4))
    [1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1]
    >>> list(explodeFull([-8, -4, 0, 4, 7], isSigned=True, groupSize=3))
    Traceback (most recent call last):
      ...
    ValueError: Value cannot fit in specified size: -8
    """
    
    isSigned = kwArgs.get('isSigned', False)
    isLSBFirst = kwArgs.get('isLSBFirst', False)
    skipCount = kwArgs.get('ignoreCount', 0)
    baseGroupSize = kwArgs.get('groupSize', 32)
    wantCount = kwArgs.get('wantCount', None)
    fullBaseSize = 2 ** baseGroupSize
    halfBaseSize = fullBaseSize // 2
    
    for inValue in iterator:
        if isinstance(inValue, str):
            feed = [ord(c) for c in inValue]
            group, full, half = 8, 256, 128
        else:
            feed = [inValue]
            group, full, half = baseGroupSize, fullBaseSize, halfBaseSize
        
        for value in feed:
            if isSigned:
                if value >= half or value < -half:
                    raise ValueError("Value cannot fit in specified size: %s" % (value,))
                
                if value < 0:
                    value += full
            
            elif value >= full or value < 0:
                raise ValueError("Value cannot fit in specified size: %s" % (value,))
            
            v = list(map(_binaryDecomposer, itertools.repeat([value], group)))
            
            if isLSBFirst:
                for i in v:
                    if skipCount:
                        skipCount -= 1
                    else:
                        yield i
                        
                        if wantCount is not None:
                            wantCount -= 1
                            
                            if not wantCount:
                                raise StopIteration()
            
            else:
                for i in reversed(v):
                    if skipCount:
                        skipCount -= 1
                    else:
                        yield i
                        
                        if wantCount is not None:
                            wantCount -= 1
                            
                            if not wantCount:
                                raise StopIteration()

def explodeRow(s, bitDepth, width):
    """
    Given a binary string, a bitDepth and a pixel width, returns a list of
    values in the range [0, 2**bitDepth]. The list will be width items long.
    
    >>> bs = b'\x0F'
    >>> explodeRow(bs, 1, 8)
    [0, 0, 0, 0, 1, 1, 1, 1]
    """
    
    if bitDepth == 1:
        v = explode(s)[:width]
    
    elif bitDepth == 2:
        v2 = explode(s)
        v3 = [2 * a + b for a, b in zip(v2[0::2], v2[1::2])]
        v = v3[:width]
    
    elif bitDepth == 4:
        v2 = []
        
        for n in list(s):
            v2.extend(list(divmod(n, 16)))
        
        v = v2[:width]
    
    else:
        v = list(s)
    
    return v

def fakeEditor(n, **kwArgs):
    """
    Many of the isValid() doctests need to be passed an editor, but the only
    thing used in that editor (usually) is maxp.numGlyphs. This function
    returns a minimal Editor with maxp.numGlyphs set to n. Several additional
    tables may be added, as controlled by various keyword arguments.
    
    >>> e = fakeEditor(200)
    >>> e.maxp.numGlyphs
    200
    
    >>> fakeEditor(1000, name=True).name.pprint()
    MS/BMP/English (U.S.) Family (3, 1, 1033, 1): Fred
    MS/BMP/English (U.S.) Subfamily (3, 1, 1033, 2): Regular
    MS/BMP/English (U.S.) Full Name (3, 1, 1033, 4): Fred Regular
    MS/BMP/English (U.S.) Name ID 256 (3, 1, 1033, 256): String 1
    
    If you need extra values added, pass a name_extras dict; note that in this
    case you don't need to explicitly set name=True, though it doesn't hurt:
    
    >>> myExtras = {257: "String 2", 258: "Fred is great"}
    >>> fakeEditor(1000, name_extras=myExtras).name.pprint()
    MS/BMP/English (U.S.) Family (3, 1, 1033, 1): Fred
    MS/BMP/English (U.S.) Subfamily (3, 1, 1033, 2): Regular
    MS/BMP/English (U.S.) Full Name (3, 1, 1033, 4): Fred Regular
    MS/BMP/English (U.S.) Name ID 256 (3, 1, 1033, 256): String 1
    MS/BMP/English (U.S.) Name ID 257 (3, 1, 1033, 257): String 2
    MS/BMP/English (U.S.) Name ID 258 (3, 1, 1033, 258): Fred is great
    
    You may pass in a simple dict glyphIndex->advance in the 'hmtx' keyword
    argument, and a full Hmtx object will be constructed (all glyphs not
    explicitly included will get advances of 0, and all glyphs get sidebearings
    of zero regardless):
    
    >>> e = fakeEditor(7, hmtx={4: 550, 5: 650, 6: 900})
    >>> e.hmtx.pprint()
    0:
      Advance width: 0
      Left sidebearing: 0
    1:
      Advance width: 0
      Left sidebearing: 0
    2:
      Advance width: 0
      Left sidebearing: 0
    3:
      Advance width: 0
      Left sidebearing: 0
    4:
      Advance width: 550
      Left sidebearing: 0
    5:
      Advance width: 650
      Left sidebearing: 0
    6:
      Advance width: 900
      Left sidebearing: 0
    """
    
    from fontio3 import fontedit, hmtx
    from fontio3.head import head
    from fontio3.maxp import maxp_tt, maxp_cff
    from fontio3.name import name, name_key
    
    e = fontedit.Editor()
    
    if kwArgs.get('forCFF', False):
        e.maxp = maxp_cff.Maxp_CFF(numGlyphs=n)
    else:
        e.maxp = maxp_tt.Maxp_TT(numGlyphs=n)
    
    dExtras = kwArgs.get('name_extras', {})
    
    if dExtras or kwArgs.get('name', False):
        K = name_key.Name_Key
        d = {1: "Fred", 2: "Regular", 4: "Fred Regular", 256: "String 1"}
        d.update(dExtras)
        e.name = name.Name()
        
        for n, s in d.items():
            e.name[K((3, 1, 1033, n))] = s

    if kwArgs.get('head', False):
        e.head = head.Head()
    
    d = kwArgs.get('hmtx', None)
    
    if d is not None:
        e.hmtx = h = hmtx.Hmtx({})
        ME = hmtx.MtxEntry
        
        for i in range(n):
            h[i] = ME(advance=d.get(i, 0))

    return e

def filterKWArgs(cls, d):
    """
    Given a class object which uses the fontdata metaclasses, return a new dict
    based on d but only with the valid attribute keys present (if any).
    """
    
    AS = cls._ATTRSPEC
    return {k: v for k, v in d.items() if k in AS}

def findAvailableIndex(iterable):
    """
    Given an iterator over integers, returns the smallest non-negative index not
    already present.

    >>> findAvailableIndex([])
    0
    >>> findAvailableIndex([0, 1, 3, 4])
    2
    >>> findAvailableIndex([1])
    0
    >>> findAvailableIndex([0, 1, 2])
    3
    """

    s = set(iterable)

    if not s:
        return 0

    m = max(s) + 1

    if len(s) == m:
        return m

    return min(set(range(m)) - s)

def findSubsequence(seqToLookInto, seqToFind):
    """
    Given a sequence, find the index of a specified subSequence (if present).
    If not present, return None.
    
    >>> big = [2, 1, 5, 3, 2, 7, 8, 7, 8, 9, 4, 1, 2, 12, -4, 2, 3]
    >>> print(findSubsequence(big, (7, 8, 9)))
    7
    >>> print(findSubsequence(big, []))
    0
    >>> print(findSubsequence(big, [2] * 50))
    None
    >>> print(findSubsequence(big, [5, 2]))
    None
    >>> print(findSubsequence(big, [-4]))
    14
    """
    
    findLen = len(seqToFind)
    
    if findLen == 0:
        return 0
    
    if findLen > len(seqToLookInto):
        return None
    
    start = 0
    highest = len(seqToLookInto) - findLen
    
    while start <= highest:
        try:
            index = seqToLookInto.index(seqToFind[0], start)
        except ValueError:
            index = None
        
        if index is None or index > highest:
            return None
        
        if list(seqToLookInto[index:index+findLen]) == list(seqToFind):
            return index
        
        start = index + 1
    
    return None

fromhex = bytes.fromhex

def fromhexdump(s):
    """
    Reconstruct a bytestring from the output from hexdump().
    
    >>> b = bytes(range(256))
    >>> s = hexdumpString(b)
    >>> print(s, end='')
           0 |0001 0203 0405 0607  0809 0A0B 0C0D 0E0F |................|
          10 |1011 1213 1415 1617  1819 1A1B 1C1D 1E1F |................|
          20 |2021 2223 2425 2627  2829 2A2B 2C2D 2E2F | !"#$%&'()*+,-./|
          30 |3031 3233 3435 3637  3839 3A3B 3C3D 3E3F |0123456789:;<=>?|
          40 |4041 4243 4445 4647  4849 4A4B 4C4D 4E4F |@ABCDEFGHIJKLMNO|
          50 |5051 5253 5455 5657  5859 5A5B 5C5D 5E5F |PQRSTUVWXYZ[\]^_|
          60 |6061 6263 6465 6667  6869 6A6B 6C6D 6E6F |`abcdefghijklmno|
          70 |7071 7273 7475 7677  7879 7A7B 7C7D 7E7F |pqrstuvwxyz{|}~.|
          80 |8081 8283 8485 8687  8889 8A8B 8C8D 8E8F |................|
          90 |9091 9293 9495 9697  9899 9A9B 9C9D 9E9F |................|
          A0 |A0A1 A2A3 A4A5 A6A7  A8A9 AAAB ACAD AEAF |................|
          B0 |B0B1 B2B3 B4B5 B6B7  B8B9 BABB BCBD BEBF |................|
          C0 |C0C1 C2C3 C4C5 C6C7  C8C9 CACB CCCD CECF |................|
          D0 |D0D1 D2D3 D4D5 D6D7  D8D9 DADB DCDD DEDF |................|
          E0 |E0E1 E2E3 E4E5 E6E7  E8E9 EAEB ECED EEEF |................|
          F0 |F0F1 F2F3 F4F5 F6F7  F8F9 FAFB FCFD FEFF |................|
    
    >>> b2 = fromhexdump(s)
    >>> b == b2
    True
    """
    
    sv = []
    pat = re.compile('([0-9A-F][0-9A-F])')
    
    for line in s.splitlines():
        startdelim = line.find("|")
        enddelim = line.find("|", startdelim + 1)
        sv.append(' '.join(pat.findall(line[startdelim:enddelim])))

    return fromhex(' '.join(sv))

def getFontGlyphCount(**kwArgs):
    """
    Parses the kwArgs looking for either a fontGlyphCount argument, or an
    editor (used to get a Maxp object), in order to return the font's glyph
    count. If both are provided, the 'fontGlyphCount' is preferred. If neither
    is provided, None is returned and no exception is raised.
    
    >>> e = fakeEditor(300)
    >>> print(getFontGlyphCount(fontGlyphCount=250))
    250
    >>> print(getFontGlyphCount(editor=e))
    300
    >>> print(getFontGlyphCount(editor=e, fontGlyphCount=250))
    250
    >>> print(getFontGlyphCount())
    None
    """
    
    if 'fontGlyphCount' in kwArgs:
        return kwArgs['fontGlyphCount']
    
    if 'editor' in kwArgs:
        e = kwArgs['editor']

        if e.reallyHas(b'maxp'):
            return e.maxp.numGlyphs

    return None

def getLoggerName(logger):
    """
    Returns the name associated with the specified logger. If the logger uses
    the custom LoggerAdapter LA (defined in this module), the special name it
    uses will be returned; otherwise, the logger's simple name will be
    returned.
    
    >>> logBase = logging.getLogger("Base")
    >>> log1 = logBase.getChild("Fredtest")
    >>> log2 = makeDoctestLogger("Georgetest")
    >>> getLoggerName(logBase)
    'Base'
    >>> getLoggerName(log1)
    'Base.Fredtest'
    >>> getLoggerName(log2)
    'Georgetest'
    """
    
    try:
        r = logger.extra['customlocation']
    except:
        r = logger.name
    
    return r

def glyphStringList(v, stream=sys.stdout):
    """
    Returns a list of strings representing lines of printASCII() output for the
    glyph whose data are presented in list v, whose elements are:
    
        [0]  lo_x
        [1]  hi_y
        [2]  width
        [3]  height
        [4]  bytes per line
        [5]  a string containing the bitmap
    
    >>> v = [1, 5, 5, 7, 1, bytes.fromhex("F8 88 88 88 88 88 F8")]
    >>> for line in glyphStringList(v): print(line)
         00000
         00000
         12345
      +5 XXXXX
      +4 X...X
      +3 X...X
      +2 X...X
      +1 X...X
      +0 X...X
      -1 XXXXX
    """
    
    sv = []
    r = range(v[0], v[0] + v[2])  # in Python 3, don't need to make it a list
    sv.append("     %s" % ''.join(str(abs(x)//100) for x in r))
    sv.append("     %s" % ''.join(str((abs(x) % 100)//10) for x in r))
    sv.append("     %s" % ''.join(str(abs(x) % 10) for x in r))
    
    for line in range(v[3]):
        start = line * v[4]
        end = start + v[4]
        sv.append("%+4d %s" % (v[1] - line, _imageline(v[2], v[5][start:end])))
    
    return sv

def hashableSignature(obj):
    """
    Returns an immutable and hashable representation of the specified object.
    For lists, this representation is a tuple. For dicts, it's a tuple of
    (key, value) pairs. In all cases, objects are descended recursively.
    
    The intent of this function is to allow equality comparison for objects
    which may not have __eq__ or __ne__ implemented.
    
    >>> v = [1, 2]        
    >>> v2 = [3, v, 4]
    >>> v3 = [5, v2, 6, v]
    >>> d = {'fred': v3, 34: {'a': v2, 'b': [v3, 12]}}
    >>> d2 = {d: "Bad!"}
    Traceback (most recent call last):
      ...
    TypeError: unhashable type: 'dict'
    >>> d2 = {hashableSignature(d): "Good!"}
    >>> d == {
    ...   34: {'a': [3, [1, 2], 4], 'b': [[5, [3, [1, 2], 4], 6, [1, 2]], 12]},
    ...   'fred': [5, [3, [1, 2], 4], 6, [1, 2]]}
    True
    >>> hashableSignature(d)
    (('fred', (5, (3, (1, 2), 4), 6, (1, 2))), (34, (('a', (3, (1, 2), 4)), ('b', ((5, (3, (1, 2), 4), 6, (1, 2)), 12)))))
    >>> class X(object):
    ...   def __init__(self, n): self.n = n
    >>> hashableSignature(X(5))
    (('n', 5),)
    """
    
    if isinstance(obj, (list, tuple)):
        newList = list(obj)
        
        if hasattr(obj, '__dict__') and bool(obj.__dict__):
            newList.append(obj.__dict__)
        
        v = [hashableSignature(entry) for entry in newList]
        return tuple(v)
    
    elif isinstance(obj, dict):
        s = sorted(list((key, repr(key)) for key in obj), key=operator.itemgetter(1))
        v = [(k[0], hashableSignature(obj[k[0]])) for k in s]
        
        if hasattr(obj, '__dict__') and bool(obj.__dict__):
            v.append(hashableSignature(obj.__dict__))
        
        return tuple(v)
    
    elif isinstance(obj, (set, frozenset)):
        v = sorted(hashableSignature(x) for x in obj)
        
        if hasattr(obj, '__dict__') and bool(obj.__dict__):
            v.append(hashableSignature(obj.__dict__))
        
        return tuple(v)
    
    elif hasattr(obj, '__dict__') and bool(obj.__dict__):
        return hashableSignature(obj.__dict__)
    
    try:
        hash(obj)
        return obj
    except TypeError:
        return ('objectID', id(obj))

def hexdump(s, stream=None, indent=0):
    """
    Does a formatted dump of the hex data in the specified string.
    """
    
    if stream is None:
        stream = sys.stdout
    
    indentSpaces = " " * indent
    startOffset = 0
    origLen = len(s)
    
    while startOffset < origLen:
        print("%s%8X |" % (indentSpaces, startOffset), end=' ', file=stream)
        chunkLen = min(16, origLen - startOffset)
        print(_hexline(s[startOffset:startOffset+chunkLen]), file=stream)
        startOffset += 16
        
def hexdumpString(s):
    """
    Does a formatted dump of the hex data in the specified string.
    Similar to hexdump(). This method returns a string.
    """
    hexString = ""
    startOffset = 0
    origLen = len(s)
    
    while startOffset < origLen:
        hexString += "%8X |" % startOffset
        chunkLen = min(16, origLen - startOffset)
        hexString += _hexline(s[startOffset:startOffset+chunkLen]) + "\n"
        startOffset += 16
        
    return hexString

def hintKind(s):
    """
    Given a binary string, returns the kind of hints represented therein.
    Currently returns either 'TT' or 'Spark'.
    
    >>> hintKind(fromhex("00"))
    'TT'
    >>> hintKind(fromhex("B0 F9 7F"))
    'Spark'
    """
    
    if any(s.startswith(test) for test in _validSparkStarts):
        return 'Spark'
    
    return 'TT'

def implode(v):
    """
    Given a list of 1s and 0s, returns a binary string such that the [0]
    element of the list is the MSB of the first byte of the returned string,
    padding with zero bits on the end if needed.
    
    >>> implode([0,0,1])      
    b' '
    >>> implode([0,0,1,0,0,0,0,0])
    b' '
    """
    
    return utilitiesbackend.utImplode(v)
            
def implodeFull(iterable, **kwArgs):
    """
    This function is designed to be a more powerful version of implode. Given
    an iterable source of 1s and 0s, it returns a generator over values
    collected from those bits. Several keyword arguments control the process:
    
        groupSize       The number of bits per group. Default is 32, unless
                        wantAsChar is specified, in which case the value is
                        forced to 8. Note that this value does not necessarily
                        need to be a multiple of two.
        
        lastPadLeft     If there are any bits left over, the usual behavior is
                        pad them with zero bits on the right. If this flag is
                        set, however, then the result will be padded on the
                        left instead. Note this means the resulting value will
                        always be positive, even if wantSigned is True.
        
        wantAsChar      If True, the generator will yield single-byte strings
                        (created via the chr() function), instead of integers.
                        Note that specifying this forces groupSize to 8,
                        irrespective of any value that may have been explicitly
                        set. This flag and wantSigned are mutually exclusive;
                        if both are set, a ValueError is raised.
        
        wantLSBFirst    If True, the order of accumulated bits will be reversed
                        before the output value is yielded. Default is False.
        
        wantSigned      If True, the values are treated as two's-complement.
                        Default is False. This flag and wantAsChar are mutually
                        exclusive; if both are set, a ValueError is raised.
    
    >>> v = [0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1]
    >>> list(implodeFull(v))
    [1635407872]
    >>> list(implodeFull(v, lastPadLeft=True))
    [798539]
    >>> list(implodeFull(v, groupSize=4))
    [6, 1, 7, 10, 5, 8]
    >>> list(implodeFull(v, groupSize=4, wantSigned=True))
    [6, 1, 7, -6, 5, -8]
    >>> list(implodeFull(v, groupSize=4, wantLSBFirst=True))
    [6, 8, 14, 5, 10, 1]
    >>> list(implodeFull(v, groupSize=4, wantLSBFirst=True, wantSigned=True))
    [6, -8, -2, 5, -6, 1]
    >>> list(implodeFull(v, groupSize=3, wantSigned=True))
    [3, 0, 2, -1, -3, 1, 3]
    >>> list(implodeFull(v, wantAsChar=True))
    ['a', 'z', 'X']
    >>> list(implodeFull(v, wantSigned=True, wantAsChar=True))
    Traceback (most recent call last):
      ...
    ValueError: Cannot specify both wantSigned and wantAsChar!
    """
    
    if kwArgs.get('wantAsChar', False):
        wantAsChar = True
        groupSize = 8  # hardwired in this case
    else:
        wantAsChar = False
        groupSize = kwArgs.get('groupSize', 32)
    
    wantSigned = kwArgs.get('wantSigned', False)
    
    if wantSigned:
        if wantAsChar:
            raise ValueError("Cannot specify both wantSigned and wantAsChar!")
        
        fullValue = 2 ** groupSize
        halfValue = fullValue // 2
    
    wantLSBFirst = kwArgs.get('wantLSBFirst', False)
    lastPadLeft = kwArgs.get('lastPadLeft', False)
    cumul = []
    
    for bit in iterable:
        cumul.append(bit)
        
        if len(cumul) == groupSize:
            source = (reversed(cumul) if wantLSBFirst else iter(cumul))
            n = functools.reduce(_binaryAccumulator, source)
            
            if wantSigned and (n >= halfValue):
                n -= fullValue
            
            yield (chr(n) if wantAsChar else n)
            cumul = []
    
    if cumul:  # might be leftovers
        if lastPadLeft:
            cumul = [0] * (groupSize - len(cumul)) + cumul
        else:
            cumul.extend([0] * (groupSize - len(cumul)))
        
        source = (reversed(cumul) if wantLSBFirst else iter(cumul))
        n = functools.reduce(_binaryAccumulator, source)
        
        if wantSigned and (n >= halfValue):
            n -= fullValue
        
        yield (chr(n) if wantAsChar else n)


def inRangeForAxis(v, axisTag, **kwArgs):
    """
    Check that value 'v' is within the allowed ranges for OpenType 1.8
    Variation Axis tags. For registered tags, checks against the specification
    value. For unregistered tags, checks that value is in range for Fixed.

    >>> inRangeForAxis(0.5, 'ital')
    True
    >>> inRangeForAxis(-1, 'opsz')
    False
    >>> inRangeForAxis(-25, 'slnt')
    True
    >>> inRangeForAxis(-100, 'wdth')
    False
    >>> inRangeForAxis(1200, 'wght')
    False
    """

    if axisTag == 'ital':
        return 0 <= v <= 1

    if axisTag == 'opsz':
        return 0 < v < 32768

    if axisTag == 'slnt':
        return -90 < v < 90

    if axisTag == 'wdth':
        return 0 < v < 32768

    if axisTag == 'wght':
        return 1 <= v <= 1000

    return -32768 <= v < 32768


def inRangeLong(v):
    """
    Simple function to check that 'v' is an integer and is in-range for LONG
    as used in OpenType. Can be used as the function for attr_inputcheckfunc
    ('checkInput()') in protocol objects.
    >>> inRangeLong(42)
    True
    >>> inRangeLong(-1.21)
    False
    """
    return isinstance(v, int) and -2147483648 <= v <= 2147483647


def inRangeShort(v):
    """
    Simple function to check that 'v' is an integer and is in-range for SHORT
    as used in OpenType. Can be used as the function for attr_inputcheckfunc
    ('checkInput()') in protocol objects.
    >>> inRangeShort(42)
    True
    >>> inRangeShort(-1.21)
    False
    """
    return isinstance(v, int) and -32768 <= v <= 32767


def inRangeUlong(v):
    """
    Simple function to check that 'v' is an integer and is in-range for ULONG
    as used in OpenType. Can be used as the function for attr_inputcheckfunc
    ('checkInput()') in protocol objects.
    >>> inRangeUlong(42)
    True
    >>> inRangeUlong(-1.21)
    False
    """
    return isinstance(v, int) and 0 <= v <= 0xFFFFFFFF


def inRangeUshort(v):
    """
    Simple function to check that 'v' is an integer and is in-range for USHORT
    as used in OpenType. Can be used as the function for attr_inputcheckfunc
    ('checkInput()') in protocol objects.
    >>> inRangeUshort(42)
    True
    >>> inRangeUshort(-1.21)
    False
    """
    return isinstance(v, int) and 0 <= v <= 0xFFFF


def invertDictFull(d, sorted=False, coerce=False, asSets=False):
    """
    Returns a new dictionary whose keys are values from the input dictionary,
    and whose values are lists of all the keys in the input dictionary that map
    to that value. These lists will be sorted if indicated by the sorted flag.
    if coerce is True any one-element lists in the returned dict's values will
    be changed to their non-list contents.

    If asSets is True, the values will be sets, not lists, and no coercion will
    take place.
    
    >>> d = {'aabc': 1, 'fred': 2, 'WXYZ': 1, 'ahem': 3}
    >>> invertDictFull(d, sorted=True) == {1: ['WXYZ', 'aabc'], 2: ['fred'], 3: ['ahem']}
    True
    
    >>> invertDictFull(d, sorted=True) == {1: ['WXYZ', 'aabc'], 2: ['fred'], 3: ['ahem']}
    True
    
    >>> invertDictFull(d, coerce=True, sorted=True) == {1: ['WXYZ', 'aabc'], 2: 'fred', 3: 'ahem'}
    True
    
    >>> d = {'a': [1, 2], 'b': 5, 'c': 5, 'x': [1, 2]}
    >>> invertDictFull(d, sorted=True) == {(1, 2): ['a', 'x'], 5: ['b', 'c']}
    True
    >>> invertDictFull(d, asSets=True) == {(1, 2): {'a', 'x'}, 5: {'c', 'b'}}
    True
    """
    
    retVal = {}
    f = retVal.setdefault
    bs = builtins.sorted  # I chose sorted as a parameter name before sorted() existed...
    
    for key, value in d.items():
        f(hashableSignature(value), set()).add(key)
    
    if not asSets:
        if sorted and coerce:
            for key in retVal:
                old = retVal[key]
                retVal[key] = (next(iter(old)) if len(old) == 1 else bs(old))
        
        elif sorted:
            for key in retVal:
                retVal[key] = bs(retVal[key])
        
        elif coerce:
            for key in retVal:
                old = retVal[key]
                retVal[key] = (next(iter(old)) if len(old) == 1 else list(old))
        
        else:
            for key in retVal:
                retVal[key] = list(retVal[key])
    
    return retVal


def isValidAxisTag(tag, **kwArgs):
    """
    Tests the validity of variation axis tag against the OpenType Specification
    v1.8. If none of the options are specified, assumes checking for private
    tags, which must begin with an uppercase letter and otherwise consist of
    only uppercase letters or digits 0-9.
    
    Note that this can also be used to check whether other related tags are
    minimally valid or private (e.g. MVAR valueTags).

    Options may be specified via kwArgs:

        registeredOnly      returns True only if tag is one of the registered
                            tags: 'ital', 'opsz', 'slnt', 'wdth', 'wght'.
                            Default is False. If True, overrides all other
                            options.

        minimallyValid      returns True if tag meets the minimum validity
                            requirements: starts with a letter A-Z or a-z,
                            following characters are A-Z, a-z, 0-9, or space
                            and any spaces are at the end. Default is False.

    >>> isValidAxisTag('wght', registeredOnly=True)
    True
    >>> isValidAxisTag('Test')
    False
    >>> isValidAxisTag('Test', minimallyValid=True)
    True
    >>> isValidAxisTag('  HI')
    False
    >>> isValidAxisTag('HI  ', minimallyValid=True)
    True
    """

    if kwArgs.get('registeredOnly', False):
        return tag in _validRegisteredTags

    ns = tag.replace(' ', '') == tag.rstrip()

    if kwArgs.get('minimallyValid', False):
        mn = _patTagMin.match(tag)
        return mn is not None and ns and len(tag) == 4

    pr = _patTagPrv.match(tag)

    return pr is not None and ns and len(tag) == 4


def isValidPSName(s, **kwArgs):
    """
    Tests the validity of string 's' according to the following criteria:
        1) Is 31 characters or less
        2) Consists only of characters A-Z, a-z, 0-9, ., and _
        3) Does not start with a digit or "." (except ".notdef")
        *4) is not None
        *5) has length > 0

    >>> isValidPSName(".notdef")
    True
    >>> isValidPSName("twocents")
    True
    >>> isValidPSName("a1")
    True
    >>> isValidPSName("_")
    True
    >>> isValidPSName("2cents")
    False
    >>> isValidPSName(".twocents")
    False
    >>> isValidPSName("")
    False
    >>> isValidPSName(None)
    False
    """

    if s is None: return False
    if s == ".notdef": return True
    if (len(s) > 31) or (len(s) < 1): return False
    if s[0] in ".0123456789": return False
    if len(_patPSNameVal.sub("", s)): return False
    return True

def makeDoctestLogger(name, **kwArgs):
    """
    Returns a logger which can be used by doctests in fontio modules. The
    following keyword arguments are supported:

        doCleanup   Close and remove any existing top-level Handlers.

        level       Desired logging level as string (one of 'DEBUG', 'INFO',
                   'WARNING', 'ERROR', 'CRITICAL'). Default is 'DEBUG'.

        stream      A stream to which the logging messages will be posted. The
                    default is sys.stdout (not sys.stderr, note!)
    """
    
    logger = logging.getLogger(name)
    level = kwArgs.get('level', 'DEBUG')

    if kwArgs.get('doCleanup', True):
        for handler in logger.handlers:
            handler.close()
        logger.handlers = []

    logger.setLevel(level)

    ch = SH(kwArgs.get('stream', sys.stdout))
    ch.setLevel(level)

    formatter = logging.Formatter(
      '%(customlocation)s - %(levelname)s - %(message)s')
    
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    adapter = LA(logger, {'customlocation': name})
    return adapter

def makeNonIgPiece(glyphArray, start, igs, backCount, fwdCount, **kwArgs):
    """
    Create an excerpt of glyphArray, skipping over ignorables. There is one
    keyword argument:
    
        backIndices     If present, should be an empty list. It will contain
                        the indices in glyphArray contained in the returned
                        list.

    >>> glyphArray = [10, 40, 11, 12, 13, 41, 42, 14, 43, 15]
    >>> igs = [False, True, False, False, False, True, True, False, True, False]
    >>> makeNonIgPiece(glyphArray, 0, igs, 0, 3)
    [10, 11, 12]
    >>> makeNonIgPiece(glyphArray, 1, igs, 0, 3)
    [11, 12, 13]
    >>> makeNonIgPiece(glyphArray, 0, igs, 0, 6)
    [10, 11, 12, 13, 14, 15]

    If you ask for more than is there, just what's there is returned:

    >>> makeNonIgPiece(glyphArray, 0, igs, 0, 10)
    [10, 11, 12, 13, 14, 15]

    The backCount is used for backtrack cases:

    >>> makeNonIgPiece(glyphArray, 7, igs, 3, 2)
    [11, 12, 13, 14, 15]
    >>> makeNonIgPiece(glyphArray, 7, igs, 100, 100)
    [10, 11, 12, 13, 14, 15]
    
    Use the backIndices to know where the excerpt comes from:
    
    >>> b = []
    >>> makeNonIgPiece(glyphArray, 7, igs, 100, 100, backIndices=b)
    [10, 11, 12, 13, 14, 15]
    >>> b
    [0, 2, 3, 4, 7, 9]
    """

    r = []
    b = kwArgs.pop('backIndices', list())

    if backCount:
        i = start - 1

        while (i >= 0) and backCount:
            while igs[i]:
                i -= 1

                if i == -1:
                    break

            else:
                r.append(glyphArray[i])
                b.append(i)
                i -= 1
                backCount -= 1

        r.reverse()
        b.reverse()

    while fwdCount:
        while igs[start]:
            start += 1

            if start == len(glyphArray):
                return r

        r.append(glyphArray[start])
        b.append(start)
        fwdCount -= 1
        start += 1

        if start == len(glyphArray):
            return r

    return r

def monotonicGroupsGenerator(iterable, delta=1, allowZeroes=False):
    """
    Returns a generator over sublists of the specified iterable whose numeric
    values differ by a constant delta. If the allowZeroes flag is set, zeroes
    are treated as wildcards, matching the sequence value they replace.
    
    >>> v = list(range(25, 45))
    >>> for piece in monotonicGroupsGenerator(v): print(piece)
    (25, 45, 1)
    >>> v[6] = 99
    >>> v[14] = 0
    >>> for piece in monotonicGroupsGenerator(v): print(piece)
    (25, 31, 1)
    (99, 100, 1)
    (32, 39, 1)
    (0, 1, 1)
    (40, 45, 1)
    >>> for piece in monotonicGroupsGenerator(v, allowZeroes=True): print(piece)
    (25, 31, 1)
    (99, 100, 1)
    (32, 45, 1)
    >>> for piece in monotonicGroupsGenerator([10, 7, 4, 1], delta=-3): print(piece)
    (10, -2, -3)
    """
    
    prevValue = None
    
    for value in iterable:
        if prevValue is None:
            startValue = value
        
        elif value == 0 and allowZeroes:
            value = prevValue + delta
        
        elif value != prevValue + delta:
            yield (startValue, prevValue + delta, delta)
            startValue = value
        
        prevValue = value
    
    if prevValue is not None:
        yield (startValue, prevValue + delta, delta)

def nameFromKwArgs(nameID, **kwArgs):
    """
    Given a nameID, returns a string representing it. This might be just a
    string version of the number, but if the kwArgs contain either an 'editor'
    or a 'nameTableObj' keyword, a name will be looked up from that.
    
    >>> nto, e = _forNFKA()
    >>> print(nameFromKwArgs(303))
    303
    
    >>> print(nameFromKwArgs(303, nameTableObj=nto))
    303 ('Required Ligatures On')
    
    >>> print(nameFromKwArgs(304, editor=e))
    304 ('Common Ligatures On')
    """
    
    if nameID is None:
        return str(nameID)
    
    if isinstance(nameID, str):
        try:
            n = int(nameID)
        except:
            n = None
        
        if n is None:
            return str(nameID)
        
        nameID = n

    obj = None
    nto = None
    
    if 'nameTableObj' in kwArgs:
        nto = kwArgs.pop('nameTableObj')
    
    elif 'editor' in kwArgs:
        editor = kwArgs.pop('editor')
        
        if (editor is not None) and editor.reallyHas(b'name'):
            nto = editor.name
    
    if nto is not None:
        try:
            x = nto.getNameFromID(nameID, default=None)
        except AttributeError:
            x = None
        
        if x is not None:
            obj = "%d ('%s')" % (nameID, x)
    
    return obj or str(nameID)

def newRound(x, castType=None):
    """
    Python 3 rounds 0.5 cases to the nearest even value, unlike Python 2 which
    rounds away from zero. If a metaclass turns oon the python3rounding flag,
    this function will be used. It uses Python 3's builtin round() function.
    
    This function always returns a value whose type is the same as that of the
    input value, unless the caller overrides this by specifying a type to cast
    the rounded result to.
    
    >>> v = [-14, -9.75, -9.5, -8.5, 0, 4.5, 5.5, 12]
    >>> [newRound(n) for n in v]
    [-14, -10.0, -10.0, -8.0, 0, 4.0, 6.0, 12]
    
    >>> [oldRound(n) for n in v]
    [-14, -10.0, -10.0, -9.0, 0, 5.0, 6.0, 12]
    
    >>> [newRound(n, int) for n in v]
    [-14, -10, -10, -8, 0, 4, 6, 12]
    """
    
    return (castType or type(x))(round(x))

def oldRound(x, castType=None):
    """
    Python 3 rounds 0.5 cases to the nearest even value, unlike Python 2 which
    rounds away from zero. If a metaclass turns off the python3rounding flag,
    this function will be used in fontio3 to simulate the results of Python 2
    rounding.
    
    This function always returns a value whose type is the same as that of the
    input value, unless the caller overrides this by specifying a type to cast
    the rounded result to.
    
    >>> v = [-14, -9.75, -9.5, -8.5, 0, 4.5, 5.5, 12]
    >>> [oldRound(n) for n in v]
    [-14, -10.0, -10.0, -9.0, 0, 5.0, 6.0, 12]
    
    >>> [newRound(n) for n in v]
    [-14, -10.0, -10.0, -8.0, 0, 4.0, 6.0, 12]
    
    >>> [oldRound(n, int) for n in v]
    [-14, -10, -10, -9, 0, 5, 6, 12]
    """
    
    if x - math.floor(x) != 0.5:
        return (castType or type(x))(round(x))
    
    return (castType or type(x))(x - 0.5 if x < 0 else x + 0.5)

def onAMac():
    """
    Returns True if called on a Mac; note that this test isn't the best, but
    it'll do.
    """
    
    return sys.platform == 'darwin'

def pairwise(iterable):
    """
    s -> (s0,s1), (s1,s2), (s2, s3), ...

    >>> list(pairwise([3, 5, 6, 8]))
    [(3, 5), (5, 6), (6, 8)]
    """

    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def pprint_changes_dict(dCurr, dPrior, **kwArgs):
    """
    Prints nothing if the two dicts are equal. Otherwise prints a label
    (if specified) and what changed. Keyword arguments used are:
    
        indent          How many spaces to indent on left (default 0)
        indentDelta     Extra spaces per new indent (default 2)
        keys            Which keys to report (default all)
        label           Header label (no default)
        stream          Stream to receive output (default sys.stdout)
    
    >>> dCurr = {'a': 2, 'c': 5, 'd': 9, 'e': -3}
    >>> dPrior = {'a': 3, 'b': 8, 'e': -3}
    >>> f = debugStream()
    >>> pprint_changes_dict(dCurr, dPrior, stream=f)
    >>> print(f.getvalue(), end='')
    New entry 'c' with value 5
    New entry 'd' with value 9
    Deleted entry 'b'
    Entry 'a' changed from 3 to 2
    >>> f.close()
    >>> f = debugStream()
    >>> pprint_changes_dict(dCurr, dPrior, label="Summary of changes", stream=f)
    >>> print(f.getvalue(), end='')
    Summary of changes:
      New entry 'c' with value 5
      New entry 'd' with value 9
      Deleted entry 'b'
      Entry 'a' changed from 3 to 2
    >>> f.close()
    """
    
    added, deleted, changed = diffDict(dPrior, dCurr)
    
    if added or deleted or changed:
        kg = kwArgs.get
        indent = kg('indent', 0)
        indentDelta = kg('indentDelta', 2)
        stream = kg('stream', sys.stdout)
        label = kg('label', None)
        sp = " " * indent
        
        if label is not None:
            print("%s%s:" % (sp, label), file=stream)
            sp = " " * (indent + indentDelta)
        
        for key in sorted(added):
            print("%sNew entry %s with value %s" % (sp, repr(key), repr(dCurr[key])), file=stream)
        
        for key in sorted(deleted):
            print("%sDeleted entry %s" % (sp, repr(key)), file=stream)
        
        for key in sorted(changed):
            t = (sp, repr(key), repr(dPrior[key]), repr(dCurr[key]))
            print("%sEntry %s changed from %s to %s" % t, file=stream)

def pprint_changes_dict_deep(dCurr, dPrior, **kwArgs):
    """
    Like pprint_changes_dict, but changes are displayed via a subsequent call
    to pprint. Keyword arguments used are:
    
        indent          How many spaces to indent on left (default 0)
        indentDelta     Extra spaces per new indent (default 2)
        label           Header label (no default)
        stream          Stream to receive output (default sys.stdout)
    
    >>> class X(object):
    ...    def __init__(self, n): self.v = list(range(n))
    ...    def pprint(self, **k):
    ...        sp = " " * k.get('indent', 0)
    ...        st = k.get('stream', sys.stdout)
    ...        for i, n in enumerate(self.v): print("%s[%d] = %d" % (sp, i, n), file=st)
    >>> xv = [X(i) for i in range(2, 6)]
    >>> dPrior = {'a': xv[0], 'c': xv[1], 'd': xv[2]}
    >>> dCurr = {'b': xv[0], 'c': xv[3], 'd': xv[2]}
    >>> f = debugStream()
    >>> pprint_changes_dict_deep(dCurr, dPrior, label="Summary of changes", stream=f)
    >>> print(f.getvalue(), end='')
    Summary of changes:
      New entry 'b':
        [0] = 0
        [1] = 1
      Deleted entry 'a':
        [0] = 0
        [1] = 1
      Entry 'c' changed from this:
        [0] = 0
        [1] = 1
        [2] = 2
      to this:
        [0] = 0
        [1] = 1
        [2] = 2
        [3] = 3
        [4] = 4
    >>> f.close()
    """
    
    added, deleted, changed = diffDict(dPrior, dCurr)
    
    if added or deleted or changed:
        indent = kwArgs.pop('indent', 0)
        indentDelta = kwArgs.setdefault('indentDelta', 2)
        stream = kwArgs.setdefault('stream', sys.stdout)
        label = kwArgs.pop('label', None)
        
        sp = " " * indent
        i2 = indent + indentDelta
        
        if label is not None:
            print("%s%s:" % (sp, label), file=stream)
            sp = " " * i2
            i2 += indentDelta
        
        kwArgs['indent'] = i2
        
        for key in sorted(added):
            print("%sNew entry %s:" % (sp, repr(key)), file=stream)
            dCurr[key].pprint(**kwArgs)
        
        for key in sorted(deleted):
            print("%sDeleted entry %s:" % (sp, repr(key)), file=stream)
            dPrior[key].pprint(**kwArgs)
        
        for key in sorted(changed):
            print("%sEntry %s changed from this:" % (sp, repr(key)), file=stream)
            dPrior[key].pprint(**kwArgs)
            print("%sto this:" % (sp,), file=stream)
            dCurr[key].pprint(**kwArgs)

def pprint_changes_list(vCurr, vPrior, label=None, indent=0, indentDelta=2, stream=sys.stdout):
    """
    Given two lists (which should have some chronological relationship), print
    out a summary of changes. Note that insertions and deletions are not
    detected or handled specially; thus, deletions or insertions early in one
    list will potentially result in a lot of output.
    
    >>> v1 = [1, 2, 3, 4]
    >>> v2 = [1, 5, 3, 1, 12]
    >>> f = debugStream()
    >>> pprint_changes_list(v2, v1, stream=f)
    >>> print(f.getvalue(), end='')
    Element [1] changed from 2 to 5
    Element [3] changed from 4 to 1
    New element [4] added with value 12
    >>> f.close()
    >>> v3 = [1, 9]
    >>> f = debugStream()
    >>> pprint_changes_list(v3, v1, label="The changes", stream=f)
    >>> print(f.getvalue(), end='')
    The changes:
      Element [1] changed from 2 to 9
      Elements [2] through [3] were deleted
    >>> f.close()
    """
    
    currLen, priorLen = len(vCurr), len(vPrior)
    diffs = []
    
    for i, (currObj, priorObj) in enumerate(zip(vCurr, vPrior)):
        if currObj is not priorObj and currObj != priorObj:
            diffs.append(i)
    
    dels = (currLen, priorLen - 1) if currLen < priorLen else None
    adds = (priorLen, currLen) if currLen > priorLen else None
    sp = " " * indent
    
    if diffs or dels or adds:
        if label is not None:
            print("%s%s:" % (sp, label), file=stream)
            sp = " " * (indent + indentDelta)
        
        for index in diffs:
            t = (sp, index, repr(vPrior[index]), repr(vCurr[index]))
            print("%sElement [%d] changed from %s to %s" % t, file=stream)
        
        if dels:
            first, last = dels
            
            if first == last:
                print("%sElement [%d] was deleted" % (sp, first), file=stream)
            else:
                print("%sElements [%d] through [%d] were deleted" % (sp, first, last), file=stream)
        
        if adds:
            for index in range(*adds):
                s = "%sNew element [%d] added with value %s" % (sp, index, repr(vCurr[index]))
                print(s, file=stream)

def printglyph(v, stream=sys.stdout):
    """
    Prints a visual representation of the glyph info in the list v, whose
    elements are:
    
        [0]  lo_x
        [1]  hi_y
        [2]  width
        [3]  height
        [4]  bytes per line
        [5]  a string containing the bitmap
    """
    
    _printxheader(v[0], v[2], stream)
    
    for line in range(v[3]):
        start = line * v[4]
        end = start + v[4]
        print("%+4d %s" % (v[1] - line, _imageline(v[2], v[5][start:end])), file=stream)

def printLongList(iterable, maxWidth=80, label="Glyphs", indent=0, indentDelta=2, stream=sys.stdout):
    """
    Prints the list specified by the iterable to the specified stream. No line
    will be longer than the specified maximum width. Each line will start with
    indent number of spaces. If the list (plus indent and label) fits on one
    line it is printed that way; otherwise, the label is printed on one line
    and the list is broken into pieces, each indented by indent + indentDelta
    spaces, and printed on subsequent lines.
    """
    
    printLongString(str(list(iterable))[1:-1], maxWidth, label, indent, indentDelta, stream)

def printLongString(s, maxWidth=80, label="Glyphs", indent=0, indentDelta=2, stream=sys.stdout):
    """
    Prints the specified string to the specified stream. No line will be longer
    than the specified maximum width. Each line will start with indent number
    of spaces. If the string (plus indent and label) fits on one line it is
    printed that way; otherwise, the label is printed on one line and the
    string is broken into pieces, each indented by indent + indentDelta spaces,
    and printed on subsequent lines.
    """
    
    indentSpaces = " " * indent
    v = s.splitlines()
    label = "" if label is None else (label + ": ")
    
    if len(v) == 1:
        if (indent + len(label) + 2 + len(s)) <= maxWidth:
            # it all fits on one line
            print("%s%s%s" % (indentSpaces, label, s), file=stream)
        
        else:
            # it has to be broken up
            if label:
                print("%s%s" % (indentSpaces, label), file=stream)
            
            is2 = " " * (indent + indentDelta) if label else indentSpaces
            sBig = textwrap.fill(s, initial_indent=is2, subsequent_indent=is2, width=maxWidth)
            print(sBig, file=stream)
    
    else:
        if label:
            print("%s%s" % (indentSpaces, label), file=stream)
        
        is2 = " " * (indent + indentDelta) if label else indentSpaces
        
        for line in v:
            sBig = textwrap.fill(line, initial_indent=is2, subsequent_indent=is2, width=maxWidth)
            print(sBig, file=stream)

def puzzleFit(d, keySetOrDict):
    """
    Given a dict d whose keys are zero-based integers, and a keySet of numbers,
    return a new keySet none of whose members is a key in d. The minimum value
    of this new keySet will be as close to zero as possible without collisions
    occurring.
    
    If keySetOrDict is a dict instead of a set, then an additional check will
    be made for an exact match in topology and contents (though not necessarily
    the same keys) betweek d and keySetOrDict. If one is found, then the
    returned testSet will match d's keys for the topological match. The caller
    can distinguish the two cases by seeing if set(d) intersects the returned
    value. If it does, it is this topological matching case; if not, it is the
    puzzle-fit "hole".
        
    >>> puzzleFit({}, {3, 5, 6})
    {0, 2, 3}
    
    >>> puzzleFit({2: 'a'}, {3, 5, 6})
    {1, 3, 4}
    
    >>> puzzleFit({2: 'a', 5: 'r', 7: 'z'}, {11: 'r', 13: 'z'})
    {5, 7}
    
    >>> puzzleFit({2: 'a', 5: 'r', 7: 'z'}, {11: 'r', 14: 'z'})
    {0, 3}
    """
    
    ksMin = min(keySetOrDict)
    
    if d and isinstance(keySetOrDict, dict):
        dTry = {k - ksMin: v for k, v in keySetOrDict.items()}
        dSet = set(d)
        dMax = max(d)
        
        while max(dTry) <= dMax:
            s = set(dTry)
            
            if len(s) == len(s & dSet):
                # all the keys are present, now check the values
                if all(d[k] == dTry[k] for k in dTry):
                    # a match!
                    return s
            
            dTry = {k + 1: v for k, v in dTry.items()}
    
    testSet = {i - ksMin for i in keySetOrDict}
    
    if not d:
        return testSet
    
    dSet = set(d)
    
    while testSet & dSet:
        testSet = {i + 1 for i in testSet}
    
    return testSet

def safeMax(iterable, default=0):
    """
    Since max() raises a ValueError if the iterable is empty, this function
    serves as an alternative version. It will return the default in this case.
    
    >>> safeMax([])
    0
    >>> safeMax([1, 4, 2])
    4
    >>> safeMax([1, 4, 3], default=10)
    10
    """
    
    return max(itertools.chain(iter([default]), iterable))

def safeMin(iterable, default=0xFFFFFFFF):
    """
    Since min() raises a ValueError if the iterable is empty, this function
    serves as an alternative version. It will return the default in this case.

    >>> safeMin([]) == 4294967295
    True
    >>> safeMin([1, 4, 2])
    1
    >>> safeMin([1, 4, 2], 0)
    0
    """
    
    return min(itertools.chain(iter([default]), iterable))

def sampleGenerator(x, index):
    """
    Given a list x of sublists, and an index within x, this function returns a
    generator which yields lists of single elements from the sublists,
    exhaustively covering all possible such sublists, starting at index.
    
    Note that since this is a generator (and it uses recursive generators), no
    actual large list of combinations is made. This means sampleGenerator can
    be used for quite large lists.
    
    >>> v = [[1, 2, 3, 4], [5,  6], [7], [8, 9, 10]]
    >>> for vSub in sampleGenerator(v, 0): print(list(vSub))
    [1, 5, 7, 8]
    [1, 5, 7, 9]
    [1, 5, 7, 10]
    [1, 6, 7, 8]
    [1, 6, 7, 9]
    [1, 6, 7, 10]
    [2, 5, 7, 8]
    [2, 5, 7, 9]
    [2, 5, 7, 10]
    [2, 6, 7, 8]
    [2, 6, 7, 9]
    [2, 6, 7, 10]
    [3, 5, 7, 8]
    [3, 5, 7, 9]
    [3, 5, 7, 10]
    [3, 6, 7, 8]
    [3, 6, 7, 9]
    [3, 6, 7, 10]
    [4, 5, 7, 8]
    [4, 5, 7, 9]
    [4, 5, 7, 10]
    [4, 6, 7, 8]
    [4, 6, 7, 9]
    [4, 6, 7, 10]
    >>> for vSub in sampleGenerator(v, 1): print(list(vSub))
    [5, 7, 8]
    [5, 7, 9]
    [5, 7, 10]
    [6, 7, 8]
    [6, 7, 9]
    [6, 7, 10]
    """

    if index == len(x) - 1:
        for n in x[-1]:
            yield [n]
    else:
        for n in x[index]:
            for rest in sampleGenerator(x, index + 1):
                yield [n] + rest

def sequencify(obj, makeIteratorsIntoLists=False):
    """
    Returns an object guaranteed to be a list or tuple. If the specified object
    is not already a list or tuple (or some other iterable type), it is made
    into one. However, string objects are treated as non-iterables and
    therefore wrapped.
    
    >>> sequencify("abc")
    ['abc']
    >>> sequencify(["abc"])
    ['abc']
    >>> sequencify(12)
    [12]
    >>> sequencify([5, 6, 7])
    [5, 6, 7]
    >>> sequencify((x for x in (1, 2, 3)), True)
    [1, 2, 3]
    >>> type(sequencify(x for x in (1, 2, 3)))
    <class 'list'>
    """
    
    if isinstance(obj, str):
        return [obj]
    
    if hasattr(obj, 'next') and isinstance(obj.__next__, collections.Callable):
        return list(obj) if makeIteratorsIntoLists else obj
    
    try:
        len(obj)
    
    except TypeError:
        try:
            it = iter(obj)
            obj = list(it)
        except TypeError:
            obj = [obj]
    
    return obj

def sunpack(fmt, s, coerce=True):
    """
    Returns a tuple containing the unpacked info and a shortened string.

    Note that since everything in a TrueType font is big-endian, we prepend a
    '>' to fmt.

    Note that if struct.unpack returns a tuple of length 1, we just return the
    value if coerce is True.

    This function is largely obsolete; use of the StringWalker class is
    strongly encouraged in its stead.
    """
    
    size = struct.calcsize(">"+fmt)
    value = struct.unpack(">"+fmt, s[:size])
    
    if coerce and (len(value) == 1):
        value = value[0]
    
    return value, s[size:]

def truncateBytes(s):
    """
    Given a bytes object representing (usually) ASCII text, return a possibly
    smaller bytes object terminated at the first zero byte. This can be useful
    in dealing with C-convention strings.
    
    >>> s = fromhex("41 42 43 00 00 44 45")
    >>> hexdump(s)
           0 | 4142 4300 0044 45                        |ABC..DE         |
    >>> hexdump(truncateBytes(s))
           0 | 4142 43                                  |ABC             |
    """
    
    if 0 in s:
        return s[:s.index(0)]
    
    return s

def truncateRound(x, castType=None):
    """
    TrueType performs "rounding" in some cases by essentially always moving to
    the integral value that is lower. This function emulates that behavior.
    
    The returned result will be of castType, or if castType is None it will be
    its original type.
    
    >>> v = [-14, -9.75, -9.5, -8.5, 0, 4.5, 5.5, 12]
    >>> [truncateRound(n) for n in v]
    [-14, -10.0, -10.0, -9.0, 0, 4.0, 5.0, 12]
    
    >>> [truncateRound(n, int) for n in v]
    [-14, -10, -10, -9, 0, 4, 5, 12]
    """
    
    return (castType or type(x))(math.floor(x))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _forNFKA():
        _fakeNameTable = {
            (1, 0, 0, 303): "Required Ligatures On",
            (1, 0, 0, 304): "Common Ligatures On",
            (1, 0, 0, 306): "Regular",
            (1, 0, 0, 307): "Small Caps"}
        
        def _fakeEditor():
            from fontio3.name.name import Name
            
            e = fakeEditor(0x1000)
            e.name = Name(_fakeNameTable)
            return e
        
        e = _fakeEditor()
        return e.name, e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
