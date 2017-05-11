#
# TSIText.py
#
# Copyright © 2013-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TSI text blocks, which make up values for TSIDat tables.
"""

# System imports
import logging
import re

# Other imports
from fontio3.fontdata import textmeta

# -----------------------------------------------------------------------------

#
# Constants
#

_encodings = ['ascii', 'utf-8', 'macroman']

# -----------------------------------------------------------------------------

#
# Functions
#

def _findglyphids(s, **kwArgs):
    """
    Utility function to find glyph ids in text. This is only useful in TSI1
    tables, since only the composite OFFSET command refers to glyph indices.
    """

    pat = re.compile(r"S?OFFSET\s*\[\s*[R|r]\s*\]\s*,\s*(\d+)\s*,")
    x = pat.search(s)
    
    while x is not None:
        start, end = x.start(1), x.end(1)
        yield (start, end - start)
        x = pat.search(s, end)


def _getglyphids(s, **kwArgs):
    """
    Utility function to return glyph ids in text. This basically iterates over
    the results of _findglyphids, returning the ids as integers.
    
    >>> st = 'OFFSET[R], 9, 100,100'
    >>> _getglyphids(st)
    [9]
    >>> _getglyphids("asdfasdfasdfasdf")
    []
    """
    ids = [int(s[st:st+ed]) for st,ed in _findglyphids(s)]
    
    return ids

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass


class TSIText(str, metaclass=textmeta.FontDataMetaclass):
    """
    Objects containing TSI Text, such as individual glyph
    high-level/VTTTalk code, low-level/"pgm" code, prep tables, etc.
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        is_cvt = dict(
          attr_initfunc = (lambda: False)),
        is_fpgm = dict(
          attr_initfunc = (lambda: False)),
        is_prep = dict(
          attr_initfunc = (lambda: False)),
        input_encoding = dict(
          attr_initfunc = (lambda: 'ascii')),
      )

    attrSorted = ()

    textSpec = dict(
      text_findglyphsfunc = _findglyphids,
      text_encoding = 'utf-8') 
    
    #
    # Methods
    #

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        r"""
        Like fromwalker, but with validation.

        The following keyword arguments are supported:

            logger      A logger to which notices will be posted. This is
                        optional; the default logger will be used if this is
                        not provided.

            type        An optional key to indicate whether the table is one of
                        the "special" keys (cvt, prep, fpgm). This is used to
                        set the is_cvt, is_fpgm, or is_prep attributes.

        >>> fvb = TSIText.fromvalidatedbytes
        >>> l = utilities.makeDoctestLogger("test.tsitext")
        >>> obj = fvb(b'ABCDE\xb3', logger=l)
        test.tsitext - DEBUG - Walker has 6 remaining bytes.
        test.tsitext - INFO - Using macroman coding.
        >>> bad = TSIText.fromvalidatedbytes(b'\x00\x01\x02\x03', logger=l)
        test.tsitext - DEBUG - Walker has 4 remaining bytes.
        test.tsitext - INFO - Using ascii coding.
        test.tsitext - ERROR - Contains NULL bytes.
        """

        logger = kwArgs.pop('logger', None)
        ttype = kwArgs.pop('type', None)
        w_len = w.length()

        if logger is None:
            logger = logging.getLogger().getChild("tsitext")

        logger.debug((
          'V0001',
          (w_len,),
          "Walker has %d remaining bytes."))

        # We've recently discovered that new VTT will use UTF-8 for source.
        # We're assuming the worst, i.e. that they won't indicate it in any
        # way. Old source used MacRoman, and often only the ASCII subset of
        # that. So we loop through those 3 encodings to convert from.

        rawbytes = w.rest()

        for enc in _encodings:
            try:
                txt = re.sub('\r', '\n', str(rawbytes, enc))
                break

            except UnicodeDecodeError:
                pass

        logger.info(('V0894', (enc,), "Using %s coding."))

        if '\x00' in txt:
            logger.error(('V0893', (), "Contains NULL bytes."))

        r = cls(txt)
        r.input_encoding = enc

        if ttype:
            r.is_cvt = ttype == "cvt"
            r.is_fpgm = ttype == "fpgm"
            r.is_prep = ttype == "prep"

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        r"""
        Like fromwalker, but with validation.

        The following keyword arguments are supported:

            type        An optional key to indicate whether the table is
                        one of the "special" keys (cvt, prep, fpgm).
                        This is used to set the is_cvt, is_fpgm, or
                        is_prep attributes.

        >>> s = b"Test, 1, 2,3 "
        >>> obj = TSIText.frombytes(s, type='cvt')
        >>> obj.pprint()  # Don't PEP-8 me, bro! Extra space is intended.
        Test, 1, 2,3 
        >>> obj.is_cvt
        True
        >>> obj.input_encoding
        'ascii'
        >>> s = b"XLink(0, 1, 22, \xB3)"
        >>> obj = TSIText.frombytes(s)
        >>> _testingValues[2].input_encoding == 'macroman'
        True
        """

        # We've recently discovered that new VTT will use UTF-8 for source.
        # We're assuming the worst, i.e. that they won't indicate it in any
        # way. Strategy is to first assume UTF-8, but trap in a try/except
        # block. Interpreting MacRoman bytes as UTF-8 *should* throw a
        # UnicodeDecodeError; if we get that then fall back to interpreting as
        # MacRoman.

        ttype = kwArgs.pop('type', None)
        rawbytes = w.rest()

        for enc in _encodings:
            try:
                txt = re.sub('\r', '\n', str(rawbytes, enc))
                break

            except UnicodeDecodeError:
                pass

        r = cls(txt)
        r.input_encoding = enc

        if ttype:
            r.is_cvt = ttype == "cvt"
            r.is_fpgm = ttype == "fpgm"
            r.is_prep = ttype == "prep"

        return r

    #
    # Public methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for a TSIText object
        to the specified LinkedWriter.

        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 2F2A 5465 7374 2031  2C20 322C 2033 2A2F |/*Test 1, 2, 3*/|
        
        >>> h(_testingValues[1].binaryString())
               0 | 0041 4243 4445 46                        |.ABCDEF         |
        
        >>> h(_testingValues[2].binaryString())
               0 | B3FE                                     |..              |
        
        >>> h(_testingValues[3].binaryString())
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        out_str = self.encode(self.input_encoding)

        w.addString(out_str)


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

    _testingValues = (
        TSIText("/*Test 1, 2, 3*/", type='cvt'),
        TSIText('\x00ABCDEF'),
        TSIText.frombytes(b'\xB3\xFE'),
        TSIText(""),
        )


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
