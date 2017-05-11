#
# index.py
#
# Copyright © 2012-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Generic support for INDEX structures in 'CFF ' tables.
"""

# System imports
import logging

# Other imports
from fontio3.CFF import cffdict
from fontio3.utilitiesbackend import utPack
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Private classes
#

class _WriteIndexValue(object):
    """
    A callable class which returns packed binary string for a number. The size
    (format) of the number is dependent upon self.format. An instance is used
    for writer.addUnresolvedOffset where we are building the offset stakes
    before we know the actual lengths of the values in the INDEX.

    The instance's .maxoffset should be updated prior to .buildBinary being called.
    """
    def __init__(self):
        """initialize with largest possible (4 bytes)"""
        self.maxoffset = 16777217

    def __call__(self, n):
        """make it callable"""
        if self.maxoffset < 256: return utPack("B", n)
        elif self.maxoffset < 65536: return utPack("H", n)
        elif self.maxoffset < 16777216: return utPack("T", n)
        else: return utPack("I", n)

    def numBytes(self):
        """number of bytes required based on maxoffset"""
        if self.maxoffset < 256: return 1
        elif self.maxoffset < 65536: return 2
        elif self.maxoffset < 16777216: return 3
        else: return 4


# -----------------------------------------------------------------------------

#
# Public Functions
#

if 0:
    def __________________(): pass

def fromwalker(w, **kwArgs):
    """
    This method reads a CFF INDEX structure from the supplied Walker.

    The following kwArgs are supported:
        'asDict'            Return the results as a Python dictionary instead
                            of the default list.

        'itemmethod'        A method to perform on each item (i.e. a constructor). If
                            not supplied, items will be raw bytes.

    INDEX data format:
    Card16      count               number of items in INDEX
    OffSize     offSize             size of items in offset array
    Offset[]    offset[count+1]     offset array (from byte preceding object data)
    Card8       data[]              the object data

    >>> data = utilities.fromhex(_testingData[0])
    >>> w = walker.StringWalker(data)
    >>> fromwalker(w)
    [b'test', b'one', b'two']

    >>> w = walker.StringWalker(data)
    >>> fromwalker(w, asDict=True)
    {0: b'test', 1: b'one', 2: b'two'}

    >>> data = utilities.fromhex(_testingData[5]) # unsorted
    >>> w = walker.StringWalker(data)
    >>> fromwalker(w)
    Traceback (most recent call last):
    ...
    ValueError: Offsets not sorted in INDEX!
    """

    asDict = kwArgs.pop('asDict', False)
    itemmethod = kwArgs.pop('itemmethod', None)

    if asDict:
        idx = {}
    else:
        idx = []

    count = w.unpack("H")

    if count == 0:
        return idx

    if not asDict:
        # this allows us to build idx using [] notation for either dict or list
        idx = [None] * count

    offSize = w.unpack("B")

    fmt = {1: "B", 2: "H", 3: "T", 4: "I"}[offSize]
    offsets = w.group(fmt, count + 1)

    # Why is this here instead of just allowing the inevitable failure later?
    # Because unsorted offsets will result in a negative calculated 'length'
    # which, when passed to the backend (C Extension) walker, will crash it.
    # This moves the problem here instead which is somewhat more graceful.
    
    if sorted(offsets) != list(offsets):
        raise ValueError("Offsets not sorted in INDEX!")

    for i, offset in enumerate(offsets[:-1]):
        length = offsets[i+1] - offset

        chunk = w.chunk(length)

        if itemmethod:
            itemW = walker.StringWalker(chunk)
            idx[i] = itemmethod(itemW, **kwArgs)
        else:
            idx[i] = chunk

    return idx

def fromvalidatedwalker(w, **kwArgs):
    """
    Like fromwalker, this method reads a CFF INDEX structure from the supplied
    Walker. It also performs extensive validation on the data structures,
    reporting via a supplied logger.

    The following kwArgs are supported:
        'asDict'            Return the results as a Python dictionary instead
                            of the default list.

        'itemmethod'        A method to perform on each item (i.e. a constructor). If
                            not supplied, items will be raw bytes.

        'logger'            A logger to handle messages generated during validation.

    INDEX data format:
    Card16      count               number of items in INDEX
    OffSize     offSize             size of items in offset array
    Offset[]    offset[count+1]     offset array (from byte preceding object data)
    Card8       data[]              the object data

    >>> logger = utilities.makeDoctestLogger("test")

    >>> data = utilities.fromhex(_testingData[1])
    >>> w = walker.StringWalker(data)
    >>> fromvalidatedwalker(w, logger=logger)
    test.INDEX - DEBUG - Walker has 17 remaining bytes.
    test.INDEX - INFO - INDEX count: 3
    test.INDEX - DEBUG - offSize = 1
    test.INDEX - ERROR - Length 7 for INDEX entry 2 is past end of INDEX structure.

    >>> data = utilities.fromhex(_testingData[2])
    >>> w = walker.StringWalker(data)
    >>> fromvalidatedwalker(w, logger=logger)
    test.INDEX - DEBUG - Walker has 17 remaining bytes.
    test.INDEX - INFO - INDEX count: 3
    test.INDEX - DEBUG - offSize = 255
    test.INDEX - ERROR - Invalid INDEX offSize 255

    >>> data = utilities.fromhex(_testingData[3])
    >>> w = walker.StringWalker(data)
    >>> idx = fromvalidatedwalker(w, logger=logger)
    test.INDEX - DEBUG - Walker has 2 remaining bytes.
    test.INDEX - INFO - INDEX count: 0

    >>> data = utilities.fromhex(_testingData[4])
    >>> w = walker.StringWalker(data)
    >>> idx = fromvalidatedwalker(w, logger=logger)
    test.INDEX - DEBUG - Walker has 1 remaining bytes.
    test.INDEX - ERROR - Insufficient bytes.

    >>> data = utilities.fromhex(_testingData[5])
    >>> w = walker.StringWalker(data)
    >>> idx = fromvalidatedwalker(w, logger=logger)
    test.INDEX - DEBUG - Walker has 17 remaining bytes.
    test.INDEX - INFO - INDEX count: 3
    test.INDEX - DEBUG - offSize = 1
    test.INDEX - ERROR - Negative length -2 for INDEX entry 1.
    """

    asDict = kwArgs.pop('asDict', False)

    logger = kwArgs.pop('logger', None)

    if logger is None:
        logger = logging.getLogger().getChild('INDEX')
    else:
        logger = logger.getChild('INDEX')

    itemmethod = kwArgs.pop('itemmethod', None)

    if asDict:
        idx = {}
    else:
        idx = []

    logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))

    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None

    count = w.unpack("H")

    logger.info(('V0846', (count,), "INDEX count: %d"))

    if count == 0:  # Empty INDEX is OK, not an error
        return idx

    if not asDict:
        # this allows us to build idx using [] notation for either dict or list
        idx = [None] * count

    offSize = w.unpack("B")

    logger.debug(('V0001', (offSize,), 'offSize = %d'))

    if not(1 <= offSize <= 4):
        logger.error(('V0843', (offSize,), "Invalid INDEX offSize %d"))
        return None

    if w.length() < (offSize * (count + 1)):
        logger.error(('V0942', (), "INDEX length too short for count."))
        return None

    fmt = {1: "B", 2: "H", 3: "T", 4: "I"}[offSize]
    offsets = w.group(fmt, count + 1)

    for i, offset in enumerate(offsets[:-1]):
        length = offsets[i+1] - offset

        if length < 0:
            logger.error((
                'V0979',
                (length, i),
                "Negative length %d for INDEX entry %d."))
            return None

        if length > w.length():
            logger.error((
                'V0845',
                (length, i,),
                "Length %d for INDEX entry %d is past end of INDEX structure."))
            return None

        chunk = w.chunk(length)

        if itemmethod:
            itemW = walker.StringWalker(chunk)
            itemlogger = logger.getChild("[%d]" % i) if logger else None
            idx[i] = itemmethod(itemW, logger=itemlogger, **kwArgs)
        else:
            idx[i] = chunk

    return idx

def buildBinary(index, w, **kwArgs):
    """
    Builds a binary CFF INDEX structure from the supplied index, adding
    it to the suppplied LinkedWriter. The supplied offSizeMax value, used
    for building of the top-level CFF, is updated if needed.

    The following kwArgs are supported:
        'fromDict'      The supplied 'index' is a dictionary (default is sequence).

    >>> data = utilities.fromhex(_testingData[0])
    >>> w = walker.StringWalker(data)
    >>> idx = fromwalker(w)
    >>> wr = writer.LinkedWriter()
    >>> buildBinary(idx, wr)
    >>> utilities.hexdump(wr.binaryString())
           0 | 0003 0101 0508 0B74  6573 746F 6E65 7477 |.......testonetw|
          10 | 6F                                       |o               |
    
    >>> idx = {0: b'test', 1: b'one', 2: b'two'}
    >>> wr = writer.LinkedWriter()
    >>> buildBinary(idx, wr, fromDict=True)
    >>> utilities.hexdump(wr.binaryString())
           0 | 0003 0101 0508 0B74  6573 746F 6E65 7477 |.......testonetw|
          10 | 6F                                       |o               |
    """
    fromDict = kwArgs.get('fromDict', False)
    isFD = kwArgs.get('isFD', False)
    
    if isFD:
        cffstakes = kwArgs.get('cffstakes') # mandatory if 'isFD'
    
    w.add("H", len(index)) # count

    if len(index) < 1:
        return

    if index is not None:
        offSizeStake = w.addDeferredValue("B") # offsize
        offsetBaseStake = w.getNewStake()
        offsetStakes = [w.getNewStake() for i in index]
        offsetStakes.append(w.getNewStake())

        oFunc = _WriteIndexValue()

        w.addUnresolvedOffset(
          oFunc,
          offsetBaseStake,
          offsetStakes[0],
          offsetByteDelta=1) # initial entry

        if fromDict:
            for i in sorted(index):
                w.addUnresolvedOffset(
                  oFunc,
                  offsetBaseStake,
                  offsetStakes[i + 1],
                  offsetByteDelta=1)
        else:
            for i in range(len(index)):
                w.addUnresolvedOffset(
                  oFunc,
                  offsetBaseStake,
                  offsetStakes[i + 1],
                  offsetByteDelta=1)

        w.stakeCurrentWithValue(offsetBaseStake)

        dbase = w._byteLength()
        
        if len(index) and isinstance(index[0], bytes):
            for i, v in enumerate(index):
                w.stakeCurrentWithValue(offsetStakes[i])
                
                if fromDict:
                    w.addString(index[v])
                else:
                    w.addString(v)

        elif isFD:
            # 'index' will be list of (dict,origOrderList)
            for i, fd in enumerate(index):
                w.stakeCurrentWithValue(offsetStakes[i])
                cffdict.buildBinary(
                  fd[0],
                  w,
                  originalOrder=fd[1],
                  fdindex=i,
                  stakeValues=cffstakes,
                  **kwArgs)

        else:
            for i, v in enumerate(index):
                w.stakeCurrentWithValue(offsetStakes[i])
                
                if fromDict:
                    index[v].buildBinary(w, **kwArgs)

                elif isinstance(v, str):
                    w.addString(bytearray(v, 'ascii', 'ignore'))

                else:
                    v.buildBinary(w, **kwArgs)

        w.stakeCurrentWithValue(offsetStakes[-1])
        oFunc.maxoffset = (w._byteLength() - dbase) + 1
        w.setDeferredValue(offSizeStake, "B", oFunc.numBytes())


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer

    _testingData = (
      "00 03 01 01 05 08 0B 74 65 73 74 6F 6E 65 74 77 6F",
      "00 03 01 01 05 08 0F 74 65 73 74 6F 6E 65 74 77 6F",
      "00 03 FF 01 05 08 0F 74 65 73 74 6F 6E 65 74 77 6F",
      "00 00",
      "FF",
      "00 03 01 01 05 03 0B 74 65 73 74 6F 6E 65 74 77 6F",
      )

    _testingValues = ()

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

