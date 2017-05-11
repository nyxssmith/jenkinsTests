#
# kern.py
#
# Copyright © 2010-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'kern' tables, both old and new..
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta

from fontio3.kern import (
  coverage_v0,
  coverage_v1,
  format0,
  format1,
  format2,
  format3)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs.get('logger')

    isOK = True

    for i, st in enumerate(obj):
        if st is None:
            isOK = False
            
            logger.warning((
              'V0990',
              (i,),
              "Subtable %d could not be validated."))
        
        elif not len(st):
            isOK = False
            
            logger.warning((
              'V0989',
              (i,),
              "Subtable %d is empty (present but contains no entries)."))

    return isOK

# -----------------------------------------------------------------------------

#
# Private constants
#

_makers = {
  0: format0.Format0.fromwalker,
  1: format1.Format1.fromwalker,
  2: format2.Format2.fromwalker,
  3: format3.Format3.fromwalker}

_validatedmakers = {
  0: format0.Format0.fromvalidatedwalker,
  1: format1.Format1.fromvalidatedwalker,
  2: format2.Format2.fromvalidatedwalker,
  3: format3.Format3.fromvalidatedwalker}

# -----------------------------------------------------------------------------

#
# Classes
#

class Kern(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire 'kern' tables. These are lists of individual
    kerning subtable objects (Format0, Format1, etc.)
    
    >>> _testingValues[1].pprint()
    Subtable 0 (format 0):
      (xyz15, afii60001): -30
      (xyz15, xyz24): -25
      (xyz19, xyz39): 12
      Header information:
        Vertical text: False
        Cross-stream: False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda i, obj: "Subtable %d (format %d)" % (i, obj.format)),
        item_pprintlabelfuncneedsobj = True,
        seq_compactremovesfalses = True,
        seq_validatefunc_partial = _validate,
        item_wisdom = (
          "A kerning subtable, usually format 0 (pairs), but can be one of "
          "the other formats for an old GX font (AAT fonts now use the 'kerx' "
          "table instead)."),
        seq_wisdom = (
          "Each subtable is done seriatim; note, however, that many OSs will "
          "only ever do the first subtable in the table. If this is a "
          "problem, you might consider converting the data to a 'GPOS' or "
          "'kerx' table; check out fontio3.GPOS.pairclasses.fromformat2()."))

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Kern object to the specified LinkedWriter.
        The keyword arguments are:
        
            addSentinel     Set to True to cause (where appropriate) subtables
                            to have the (0xFFFF, 0xFFFF, 0) sentinel added at
                            the end (note this does not affect the subtable's
                            count of numPairs or whatever).
            
            stakeValue      The stake value to be used at the start of this
                            output.
        
        >>> h = utilities.hexdump
        >>> obj = _testingValues[1]
        >>> h(obj.binaryString())
               0 | 0001 0000 0000 0001  0000 0022 0000 0000 |..........."....|
              10 | 0003 000C 0001 0006  000E 0017 FFE7 000E |................|
              20 | 0060 FFE2 0012 0026  000C                |.`.....&..      |
        
        >>> h(obj.binaryString(addSentinel=True))
               0 | 0001 0000 0000 0001  0000 0028 0000 0000 |...........(....|
              10 | 0003 000C 0001 0006  000E 0017 FFE7 000E |................|
              20 | 0060 FFE2 0012 0026  000C FFFF FFFF 0000 |.`.....&........|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        s = set(obj.coverage.format for obj in self)
        
        if len(s) != 1:
            raise ValueError(
              "Mixed coverages not supported in a single kern table!")
        
        isVersion1 = bool(s.pop())
        
        if isVersion1:
            w.add("2L", 0x10000, len(self))
            
            for subtable in self:
                startLength = w.byteLength
                lengthStake = w.addDeferredValue("L")
                subtable.coverage.buildBinary(w)
                w.add("B", subtable.format)
                w.add("H", (subtable.tupleIndex or 0))
                subtable.buildBinary(w, **kwArgs)
                
                w.setDeferredValue(
                  lengthStake,
                  "L",
                  int(w.byteLength - startLength))
        
        else:
            w.add("2H", 0, len(self))
            
            for subtable in self:
                startLength = w.byteLength
                w.add("H", 0)  # ignore the subtable version
                lengthStake = w.addDeferredValue("H")
                w.add("B", subtable.format)
                subtable.coverage.buildBinary(w)
                subtable.buildBinary(w, **kwArgs)

                w.setDeferredValue(
                  lengthStake,
                  "H",
                  int(min(w.byteLength - startLength, 0xFFFF)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Kern. However, it also
        does validation via the logging module (the client should have done a
        logging.basicConfig() call prior to calling this method, unless a
        logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Kern.fromvalidatedbytes
        >>> obj = fvb(s[0:2], logger=logger)
        test.kern - DEBUG - Walker has 2 remaining bytes.
        test.kern - ERROR - Length 2 is too short
        
        >>> obj = fvb(s[0:9], logger=logger)
        test.kern - DEBUG - Walker has 9 remaining bytes.
        test.kern - INFO - Version 1 table with 1 subtables
        test.kern - ERROR - Length 9 is too short for 1 subtables in version 1 table
        
        >>> obj = fvb(s, logger=logger)
        test.kern - DEBUG - Walker has 42 remaining bytes.
        test.kern - INFO - Version 1 table with 1 subtables
        test.kern - INFO - Subtable 0 uses format 0
        test.kern.format0 - DEBUG - Walker has 26 remaining bytes.
        test.kern.format0 - INFO - There are 3 kerning pairs.
        test.kern.format0.[0].glyphpair - DEBUG - Walker has 18 remaining bytes.
        test.kern.format0.[1].glyphpair - DEBUG - Walker has 12 remaining bytes.
        test.kern.format0.[2].glyphpair - DEBUG - Walker has 6 remaining bytes.
        
        >>> s = _testingValues[2].binaryString()
        >>> obj = fvb(s[0:5], logger=logger)
        test.kern - DEBUG - Walker has 5 remaining bytes.
        test.kern - INFO - Version 0 table with 1 subtables
        test.kern - ERROR - Length 5 is too short for 1 subtables in version 0 table
        
        >>> obj = fvb(s[0:17], logger=logger)
        test.kern - DEBUG - Walker has 17 remaining bytes.
        test.kern - INFO - Version 0 table with 1 subtables
        test.kern - WARNING - Subtable 0's declared length 26 is greater than the kern table's length 17
        test.kern - INFO - Subtable 0 uses format 0
        test.kern.format0 - DEBUG - Walker has 7 remaining bytes.
        test.kern.format0 - ERROR - Insufficient bytes.
        
        >>> obj = fvb(s, logger=logger)
        test.kern - DEBUG - Walker has 36 remaining bytes.
        test.kern - INFO - Version 0 table with 1 subtables
        test.kern - INFO - Subtable 0 uses format 0
        test.kern.format0 - DEBUG - Walker has 26 remaining bytes.
        test.kern.format0 - INFO - There are 3 kerning pairs.
        test.kern.format0.[0].glyphpair - DEBUG - Walker has 18 remaining bytes.
        test.kern.format0.[1].glyphpair - DEBUG - Walker has 12 remaining bytes.
        test.kern.format0.[2].glyphpair - DEBUG - Walker has 6 remaining bytes.

        >>> s = utilities.fromhex("00 05 00 01 00 00 00 01")
        >>> obj = fvb(s, logger=logger)
        test.kern - DEBUG - Walker has 8 remaining bytes.
        test.kern - ERROR - Unknown version 0x00050001
        
        >>> s = utilities.fromhex("00 00 00 01 00 07 00 06 7F 03")
        >>> obj = fvb(s, logger=logger)
        test.kern - DEBUG - Walker has 10 remaining bytes.
        test.kern - INFO - Version 0 table with 1 subtables
        test.kern - ERROR - Subtable 0 uses unknown format: 127

        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('kern')
            
        tblLen = w.length()
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if tblLen < 4:
            logger.error(('V0004', (tblLen,), "Length %d is too short"))
            return None
        
        isVersion1 = bool(w.unpack("H", advance=False))
        
        if isVersion1 and tblLen < 8:
            logger.error((
              'E1606',
              (tblLen,),
              "Length %d is too short for version 1"))
            
            return None
            
        version, numTables = w.unpack("2L" if isVersion1 else "2H")
        
        if isVersion1 and (version != 0x00010000):
            logger.error((
              'E1607',
              (version,),
              "Unknown version 0x%08X"))
            
            return None
        
        if numTables == 0:
            logger.error(('E1603', (), "The number of subtables is zero"))
            return None

        logger.info((
          'I1603',
          (version / 65536, numTables),
          "Version %d table with %d subtables"))
        
        r = cls([None] * numTables)
        
        minLen = (8 + (numTables * 8)) if isVersion1 else (4 + (numTables * 6))

        if tblLen < minLen:
            logger.error((
              'E1604',
              (tblLen, numTables, version / 65536),
              "Length %d is too short for %d subtables in version %d table"))
            
            return None

        kwArgs.pop('coverage', None)
        kwArgs.pop('tupleIndex', None)
        
        for i in range(numTables):
            if isVersion1:
                byteLength = w.unpack("L") - 8  # left after the header
                
                cov = coverage_v1.Coverage.fromvalidatedwalker(
                  w,
                  logger = logger)
                
                format, tupleIndex = w.unpack("BH")
            
            else:
                byteLength = w.unpack("2xH") - 6  # left after the header
                format = w.unpack("B")

                if byteLength > tblLen:
                    logger.warning((
                      'V1002',
                      (i, byteLength, tblLen),
                      "Subtable %d's declared length %d is greater than the "
                      "kern table's length %d"))

                cov = coverage_v0.Coverage.fromvalidatedwalker(
                  w,
                  logger = logger)
                
                tupleIndex = None
            
            if format in _validatedmakers:
                logger.info((
                  'I1605',
                  (i, format),
                  "Subtable %d uses format %d"))
                
                wSub = w.subWalker(0, relative=True, newLimit=byteLength)
                
                thisSubtable = _validatedmakers[format](
                  wSub,
                  coverage = cov,
                  tupleIndex = tupleIndex,
                  logger = logger,
                  **kwArgs)
                
                r[i] = thisSubtable
                w.skip(byteLength)
            
            else:
                logger.error((
                  'E1605',
                  (i, format),
                  "Subtable %d uses unknown format: %d"))
                
                # instead of completely bailing on unknown formats, simply skip
                # the bytes and attempt to handle the next subtable
                
                r[i] = None
                w.skip(byteLength)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Kern object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == Kern.frombytes(obj.binaryString())
        True
        """
        
        isVersion1 = bool(w.unpack("H", advance=False))
        version, numTables = w.unpack("2L" if isVersion1 else "2H")
        r = cls([None] * numTables)
        
        for i in range(numTables):
            if isVersion1:
                byteLength = w.unpack("L") - 8  #  left after the header
                cov = coverage_v1.Coverage.fromwalker(w)
                format, tupleIndex = w.unpack("BH")
            
            else:
                
                # This is a bit tricky. The length field is only 16 bits, so if
                # the number of pairs is large enough, overflow happens. In
                # this case we special-case format 0 subtables and read the
                # actual number of pairs, and use that to set the length of
                # the walker.
                
                byteLength = w.unpack("2xH") - 6  #  left after the header
                format = w.unpack("B")
                cov = coverage_v0.Coverage.fromwalker(w)
                tupleIndex = None
                
                if format == 0:
                    numPairs = w.unpack("H", advance=False)
                    byteLength = 6 * numPairs + 8  # 8 for bin search header
            
            if format not in _makers:
                raise ValueError(
                  "Unknown 'kern' subtable format: %d" % (format,))
            
            wSub = w.subWalker(0, relative=True, newLimit=byteLength)
            
            thisSubtable = _makers[format](
              wSub,
              coverage = cov,
              tupleIndex = tupleIndex,
              **kwArgs)
            
            r[i] = thisSubtable
            w.skip(byteLength)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _f0tv = format0._testingValues
    
    _testingValues = (
        Kern(),
        Kern([_f0tv[1]]),
        Kern([_f0tv[3]]))
    
    del _f0tv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
