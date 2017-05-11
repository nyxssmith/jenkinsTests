#
# device.py
#
# Copyright © 2005-2013, 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions for OpenType Device records.
"""

# System imports
import functools
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Private functions
#

def _packDevice(v):
    """
    Takes a list of values and returns a list of packed equivalents, along with
    the chunkSize that was used.
    """
    
    lo, hi = min(v), max(v)
    count = len(v)
    retVal = []
    
    if lo >= -2 and hi <= 1:
        chunkSize = 2
    elif lo >= -8 and hi <= 7:
        chunkSize = 4
    elif lo >= -128 and hi <= 127:
        chunkSize = 8
    else:
        raise ValueError("Value outside -128..+127 valid range!")
    
    # I started out combining the logic of the following three parts, but the
    # result was a lot less clear, so I'm leaving it as is
    
    if chunkSize == 2:
        z = [2, 3, 0, 1]
        v += ([0] * 7)
        chunks = (count + 7) // 8
        
        for i in range(chunks):
            piece = v[i * 8 : (i + 1) * 8]
            
            retVal.append(
              sum(
                z[x + 2] << (14 - 2 * i)
                for i, x in enumerate(piece)))
    
    elif chunkSize == 4:
        z = list(range(8, 16)) + list(range(0, 8))
        v += ([0] * 3)
        chunks = (count + 3) // 4
        
        for i in range(chunks):
            piece = v[i * 4 : (i + 1) * 4]
            
            retVal.append(
              sum(
                z[x + 8] << (12 - 4 * i)
                for i, x in enumerate(piece)))
    
    else:
        z = list(range(128, 256)) + list(range(0, 128))
        v += [0]
        chunks = (count + 1) // 2
        
        for i in range(chunks):
            piece = v[i * 2 : (i + 1) * 2]
            
            retVal.append(
              sum(
                z[x + 128] << (8 - 8 * i)
                for i, x in enumerate(piece)))
    
    return retVal, chunkSize

def _unpackDevice(t, chunkSize):
    """
    Takes a tuple of uint16s and returns a deconvoluted list.
    """
    
    v = []
    
    for p in t:
        if chunkSize == 2:
            tmp = (
              (p & 0xC000) >> 14,
              (p & 0x3000) >> 12,
              (p & 0x0C00) >> 10,
              (p & 0x0300) >> 8,
              (p & 0x00C0) >> 6,
              (p & 0x0030) >> 4,
              (p & 0x000C) >> 2,
              (p & 0x0003))
            
            v.extend([(0, 1, -2, -1)[x] for x in tmp])
        
        elif chunkSize == 4:
            tmp = (
              (p & 0xF000) >> 12,
              (p & 0x0F00) >> 8,
              (p & 0x00F0) >> 4,
              (p & 0x000F))
            
            lookup = (0, 1, 2, 3, 4, 5, 6, 7, -8, -7, -6, -5, -4, -3, -2, -1)
            v.extend([lookup[x] for x in tmp])
        
        else:
            x = (p & 0xFF00) >> 8
            v.append(x - 256 if x > 127 else x)
            x = (p & 0x00FF)
            v.append(x - 256 if x > 127 else x)
    
    return v

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    unneededKeys = {key for key, value in obj.items() if not value}
    
    if unneededKeys:
        logger.warning((
          'V0312',
          (sorted(unneededKeys),),
          "The keys %s have zero adjustments; these are redundant."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Device(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Dictionaries mapping ppem values to pixel tweaks.
    
    Zero tweaks are ignored:
    
    >>> d1 = Device({14: -3})
    >>> d2 = Device({14: -3})
    >>> d2[15] = 0
    >>> d1 == d2
    True
    
    Empty Devices, or ones with no nonzero values, are False:
    
    >>> bool(Device())
    False
    >>> bool(Device({12: 0}))
    False
    >>> bool(Device({12: -1}))
    True
    
    >>> logger = utilities.makeDoctestLogger("device")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    True
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("dev2", stream=f)
    >>> d = Device({-5: 3, 4.25: 2, "fred": 1, 19: 0, 14: -1, 21: 200})
    >>> d.isValid(logger=logger, editor=e)
    False
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    dev2 - WARNING - The keys [19] have zero adjustments; these are redundant.
    dev2.['fred'] - ERROR - The key 'fred' is not a real number.
    dev2.[-5] - ERROR - The key -5 cannot be used in an unsigned field.
    dev2.[21] - ERROR - The signed value 200 does not fit in 8 bits.
    dev2.[4.25] - ERROR - The key 4.25 is not an integer.
    >>> f.close()
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc = (lambda k: "Tweak at %d ppem" % (k,)),
        item_scaledirectvalues = True,
        item_validatecode_nonnumericnumber = 'V0310',
        item_validatefunc_partial = valassist.isFormat_b,
        
        item_validatefunckeys_partial = functools.partial(
          valassist.isFormat_H,
          label = "key"),
        
        map_compactremovesfalses = True,
        map_compareignoresfalses = True,
        map_validatefunc_partial = _validate)

    attrSpec = dict(
        isVariable = dict(
            attr_initfunc = lambda: False,
            attr_label = "Represents a Variation Index value",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 000C 0012 0001 8C04                      |........        |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000C 0014 0002 BDF0  0020 3000           |......... 0.    |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 000C 0010 0003 F700  0000 1400           |............    |
               
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0008 0019 8000                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.isVariable:
            # write format 0x8000; self[0] is outer, self[1] is inner
            w.add("HHH", self[0], self[1], 0x8000)

        else:
            # use conventional/non-variable scheme as before
            keys = sorted(self)
            w.add("HH", keys[0], keys[-1])
            v = [self.get(key, 0) for key in range(keys[0], keys[-1] + 1)]
            packed, chunkSize = _packDevice(v)
            w.add("H", (chunkSize // 4) + 1) # cheapo log(2), OK for limited domain
            fmt = "%dH" % (len(packed),)
            w.add(fmt, *packed)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Device. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Device.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.device - DEBUG - Walker has 8 remaining bytes.
        test.device - DEBUG - StartSize=12, endSize=18, format=1
        test.device - DEBUG - Data are (35844,)
        
        >>> fvb(s[:2], logger=logger)
        test.device - DEBUG - Walker has 2 remaining bytes.
        test.device - ERROR - Insufficient bytes.
        
        >>> fvb(s[:6], logger=logger)
        test.device - DEBUG - Walker has 6 remaining bytes.
        test.device - DEBUG - StartSize=12, endSize=18, format=1
        test.device - ERROR - Insufficient bytes for compressed table.
        
        >>> fvb(s[2:4] + s[0:2] + s[4:], logger=logger)
        test.device - DEBUG - Walker has 8 remaining bytes.
        test.device - DEBUG - StartSize=18, endSize=12, format=1
        test.device - ERROR - Start size is greater than end size.
        
        >>> fvb(s[:4] + b'AA' + s[6:], logger=logger)
        test.device - DEBUG - Walker has 8 remaining bytes.
        test.device - DEBUG - StartSize=12, endSize=18, format=16705
        test.device - ERROR - Unknown format: 0x4141.
        
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.device - DEBUG - Walker has 12 remaining bytes.
        test.device - DEBUG - StartSize=12, endSize=20, format=2
        test.device - DEBUG - Data are (48624, 32, 12288)
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.device - DEBUG - Walker has 12 remaining bytes.
        test.device - DEBUG - StartSize=12, endSize=16, format=3
        test.device - DEBUG - Data are (63232, 0, 5120)
        
        >>> s = utilities.fromhex("0001 0005 8000")  # format 0x8000/Variable
        >>> obj = fvb(s, logger=logger)
        test.device - DEBUG - Walker has 6 remaining bytes.
        test.device - DEBUG - VariationIndex (1, 5)
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('device')
        else:
            logger = logger.getChild('device')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        startSize, endSize, format = w.unpack("3H")
        
        if format == 0x8000:
            # OT 1.8; startSize and endSize are actually DeltaSetOuterIndex and
            # DeltaSetInnerIndex. Return (outer, inner) tuple; calling code should
            # test and convert to LivingDeltas.
            logger.debug(('Vxxxx', (startSize, endSize), "VariationIndex (%d, %d)"))

            return (startSize, endSize)
        
        logger.debug((
          'V0095',
          (startSize, endSize, format),
          "StartSize=%d, endSize=%d, format=%d"))
        
        if startSize > endSize:
            logger.error(('E5202', (), "Start size is greater than end size."))
            return None
        
        if format not in {1, 2, 3}:
            logger.error(('E5200', (format,), "Unknown format: 0x%04X."))
            return None
        
        numPPEMs = endSize - startSize + 1
        entrySizeInBits = 2 ** format
        totalBitsNeeded = numPPEMs * entrySizeInBits
        num16s = (totalBitsNeeded + 15) // 16
        
        if w.length() < 2 * num16s:
            logger.error((
              'E5201',
              (),
              "Insufficient bytes for compressed table."))
            
            return None
        
        t = w.group("H", num16s)
        logger.debug(('Vxxxx', (t,), "Data are %s"))
        r = cls()
        
        for i, tweak in enumerate(_unpackDevice(t, entrySizeInBits)):
            if tweak:
                r[startSize + i] = tweak
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Device from the specified walker.
        
        >>> all(
        ...   obj == Device.frombytes(obj.binaryString())
        ...   for obj in _testingValues[0:3])
        True
        >>> b = utilities.fromhex("0008 0019 8000")  # format 0x8000/Variable
        >>> Device.frombytes(b) == (8, 25)  # resolve to LivingDeltas upstream
        True
        """
        
        startSize, endSize, format = w.unpack("3H")

        if format == 0x8000:
            return (startSize, endSize)

        numPPEMs = endSize - startSize + 1
        entrySizeInBits = 2 ** format
        totalBitsNeeded = numPPEMs * entrySizeInBits
        num16s = (totalBitsNeeded + 15) // 16
        t = w.group("H", num16s)
        r = cls()
        
        for i, tweak in enumerate(_unpackDevice(t, entrySizeInBits)):
            if tweak:
                r[startSize + i] = tweak
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    import io
    from fontio3 import utilities
    
    _testingValues = (
        # This entry is type 1, 2-bit values
        Device({12: -2, 14: -1, 18: 1}),
        
        # This entry is type 2, 4-bit values
        Device({12: -5, 13: -3, 14: -1, 18: 2, 20: 3}),
        
        # This entry is type 3, 8-bit values
        Device({12: -9, 16: 20}),
        
        # This entry is type 3, but for Variable fonts.
        Device({0: 8, 1: 25}, isVariable=True))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
