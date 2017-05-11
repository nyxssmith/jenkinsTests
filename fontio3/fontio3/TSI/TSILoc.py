#
# TSILoc.py
#
# Copyright © 2012-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TSI location/index tables such as TSI0 and TSI2.

Data format:

Type          Name          Description
uint16        glyphIndex    Glyph Index associated with this block of text
                            (search via this field)

uint16        textLength    Length of text (or 0x8000 to indicate any value
                            larger than 32767)

uint32        textOffset    Offset from start of TSI data table (TSI1 or TSI3)

For text with a length less than 32768, the actual length should be placed in
the textLength field.

For text with a length greater than 32767, the value 0x8000 should be placed in
the textLength field. This record is repeated once for each valid glyph index
("normal records"), and is then followed by five more entries ("extra records")
at the end, as follows:

    *   "Magic number" used to check for validity. For this entry, the glyphIndex
        field must be set to 0xFFFE and the textOffset field is set to the
        magic number (0xABFC1F34).
    
    *   Offset to Pre-program source data. Set the glyphIndex field to 0xFFFA.
    
    *   Offset to CVT source data. Set the glyphIndex field to 0xFFFB.
    
    *   Reserved. Set the glyphIndex field to 0xFFFC.
    
    *   Offset to Font program source data. Set the glyphIndex field to 0xFFFD.

The table will then have the following structure:

glyphIndex     textLength     textOffset          [comment]
0              <length>       <actual offset>     "normal" record (pgm/HL glyph source)
              . . . . . . . . .                   "normal" record (pgm/HL glyph source)
numGlyphs-1    <length>       <actual offset>     "normal" record (pgm/HL glyph source)
0xFFFE         0              0xABFC1F34          "extra" record (magic number)
0xFFFA         <length>       <actual offset>     "extra" record (ppgm source)
0xFFFB         <length>       <actual offset>     "extra" record (cvt source)
0xFFFC         <length>       <actual offset>     "extra" record (reserved)
0xFFFD         <length>       <actual offset>     "extra" record (fpgm source)

Because the actual length of a record may or may not be stored in the
textLength field, follow these rules to determine the actual length:
     
     *   If the length stored in the record is less than 32768, then the actual
         length is the length noted in the record.
     
     *   If the length stored in the record is 32768 (0x8000), then the actual
         length is computed as follows:
     
     *   For the last "extra" record (the very last record of the table), the
         length is the difference between the total length of the TSI1 table
         and the textOffset of the final record.
     
     *   For the last "normal" record (the last record just prior to the record
         containing the "magic number"), the length is the difference between
         the textOffset of the record following the "magic number" record and
         the textOffset of the last "normal" record.
     
     *   For all other records with a length of 0x8000, the length is the
         difference between the textOffset of the record in question and the
         textOffset of the next record.
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class TSILoc(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing index data into a TSIData table for the offsets and
    lengths of text sources.

    This is a dict of (textLength, textOffset) tuples indexed by glyphID.
    "Extra" records (for 'prep', 'cvt ', 'fpgm' text sources as well as the
    "magic" and reserved records) are stored as class attributes.

    >>> _testingValues[1][0] == (10, 0)
    True
    >>> _testingValues[1].magic == (0xFEED, 0xDEADBEEF)
    True
    >>> _testingValues[1].cvt == (0, 0)
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc = (lambda i: "GlyphID %d" % (i,)),
#        item_pprintfunc = (lambda p,x,label: p.simple("length %d, offset 0x%08X" % (x[0], x[1]), label=label)),
        item_renumberdirectkeys = True)
        
    attrSpec = dict(
        cvt = dict(
            attr_initfunc = (lambda: (0, 0))),
        
        prep = dict(
            attr_initfunc = (lambda: (0, 0))),
        
        fpgm = dict(
            attr_initfunc = (lambda: (0, 0))),
        
        magic = dict(
            # Initialized with a known and unlikely value to detect
            # presence/absence
            attr_initfunc = (lambda: (0xFEED, 0xDEADBEEF))),
        
        reserved = dict(
            attr_initfunc = (lambda: (0, 0))))
    
    #
    # Class methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TSILoc object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 000A 0000 0000  FFFE FEED DEAD BEEF |................|
              10 | FFFA 0000 0000 0000  FFFD 0000 0000 0000 |................|
              20 | FFFB 0000 0000 0000  FFFC 0000 0000 0000 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # normal records
        
        for i in range(len(self)):
            actualLength, offset = self[i]
            writeLength = (actualLength if actualLength < 0x8000 else 0x8000)
            w.add("2HL", i, writeLength, offset)
            
        # extra records
        
        w.add("2HL", 0xFFFE, self.magic[0], self.magic[1])
        attr = ['prep', 'fpgm', 'cvt', 'reserved']
        hrec = [0xFFFA, 0xFFFD, 0xFFFB, 0xFFFC]
        
        for a, h in zip(attr, hrec):
            actualLength,offset = self.__dict__[a]
            writeLength = (actualLength if actualLength < 0x8000 else 0x8000)
            w.add("2HL", h, writeLength, offset)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker, but with validation.
        
        The following keyword arguments are supported:
        
            fontGlyphCount          The glyph count from the 'maxp' table. This
                                    is required.
            
            flavor                  'TSI0' or 'TSI2', indicating which table
                                    this is. This is required.
            
            logger                  A logger to which notices will be posted.
                                    This is optional; the default logger will
                                    be used if this is not provided.
            
            TSIDataTableLength      The byte length of the TSIData table that
                                    this indexes into. This is required.
                                
        >>> fvb = TSILoc.fromvalidatedbytes
        >>> l = utilities.makeDoctestLogger("test")
        >>> s = utilities.fromhex(
        ...   "00 00 80 00 00 00 00 00 00 01 00 00 00 00 80 01 "
        ...   "FF FE 00 00 AB FC 1F 34 FF FA 00 00 00 00 00 00 "
        ...   "FF FD 00 00 00 00 00 00 FF FB 00 00 00 00 00 00 "
        ...   "FF FC 00 00 00 00 00 00")
        >>> obj = fvb(
        ...   s,
        ...   fontGlyphCount = 2,
        ...   flavor = 'TSI0',
        ...   TSIDataTableLength = 32769,
        ...   logger=l)
        test.TSI0 - DEBUG - Walker has 56 remaining bytes.
        test.TSI0 - INFO - Number of entries agrees with the font's glyph count.

        >>> s = utilities.fromhex(
        ...   "00 00 80 00 00 00 00 00 00 01 00 00 00 00 80 01 "
        ...   "FF FA 00 00 00 00 00 00 FF FD 00 00 00 00 00 00 "
        ...   "FF FB 00 00 00 00 00 00 FF FC 00 00 00 00 00 00")
        >>> obj = fvb(
        ...   s,
        ...   fontGlyphCount = 100,
        ...   flavor = 'TSI0',
        ...   TSIDataTableLength = 12,
        ...   logger=l)
        test.TSI0 - DEBUG - Walker has 48 remaining bytes.
        test.TSI0 - ERROR - Offset 32769 for glyphID 1 exceeds the TSI1 table's length 12.
        test.TSI0 - WARNING - Number of entries (2) does not agree with the font's glyph count (100).
        test.TSI0 - ERROR - Magic record not present.
        """
        
        fontGlyphCount = kwArgs['fontGlyphCount']
        flavor = kwArgs['flavor']
        TSIDataTableLength = kwArgs['TSIDataTableLength']
        logger = kwArgs.pop('logger', None)
        datTblName = ('TSI1' if flavor == 'TSI0' else 'TSI3')
        
        if logger is None:
            logger = logging.getLogger().getChild(flavor)
        else:
            logger = logger.getChild(flavor)
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        v = w.unpackRest("2HL", strict=True)
        r = cls()
        
        for glyphID, textLength, textOffset in v:
            if glyphID < 0xFFFA:
                # normal glyph entry
                r[glyphID] = (textLength, textOffset)
            
            elif glyphID == 0xFFFE:
                # extra record: Magic number
                r.magic = (textLength, textOffset)
            
            elif glyphID == 0xFFFA:
                # prep source
                r.prep = (textLength, textOffset)
            
            elif glyphID == 0xFFFD:
                # fpgm source
                r.fpgm = (textLength, textOffset)
                
                if r.prep[0] == 0x8000:
                    r.prep = (textOffset - r.prep[1], r.prep[1])
            
            elif glyphID == 0xFFFB:
                # cvt source
                r.cvt = (textLength, textOffset)
                
                if r.fpgm[0] == 0x8000:
                    r.fpgm = (textOffset - r.fpgm[1], r.fpgm[1])
            
            elif glyphID == 0xFFFC:
                # reserved (used to compute actual length if
                # cvt textLength == 0x8000)
                r.reserved = (textLength, textOffset)
                
                if r.cvt[0] == 0x8000:
                    r.cvt = (textOffset - r.cvt[1], r.cvt[1])

        allGIDs = sorted(r)
        
        for key in r:
            textLength, textOffset = r[key]
            
            if textLength == 0x8000:
                if key == len(r):
                    #special case for final "normal" record
                    newLength = r.prep[1] - textOffset
                
                else:
                    nextGID = allGIDs.index(key) + 1
                    newLength = r[nextGID][1] - textOffset

                r[key] = (newLength, textOffset)
                
            if textOffset > TSIDataTableLength:
                logger.error((
                  'V0484',
                  (textOffset, key, datTblName, TSIDataTableLength),
                  "Offset %d for glyphID %d exceeds the %s "
                  "table's length %d."))
        
        if len(r) != fontGlyphCount:
            logger.warning((
              'V0482',
              (len(r), fontGlyphCount),
              "Number of entries (%d) does not agree with "
              "the font's glyph count (%d)."))
        else:
            logger.info((
              'V0483',
              (),
              "Number of entries agrees with the font's glyph count."))

        if r.magic != (0, 0xABFC1F34):
            if r.magic == (0xFEED, 0xDEADBEEF):
                logger.error(('V0488', (), "Magic record not present."))
            
            else:
                logger.error((
                  'V0487',
                  r.magic,
                  "Magic record length-offset entry %d,0x%08x does not "
                  "match the expected values 0,0xABFC1F34"))

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initializes a TSILoc object from the specified walker.
        """

        v = w.unpackRest("2HL", strict=True)
        r = cls()
        
        for glyphID, textLength, textOffset in v:
            if glyphID < 0xFFFA:
                #normal glyph entry
                r[glyphID] = (textLength, textOffset)
            
            elif glyphID == 0xFFFE:
                # extra record: Magic number
                r.magic = (textLength, textOffset)
            
            elif glyphID == 0xFFFA:
                # prep source
                r.prep = (textLength, textOffset)
            
            elif glyphID == 0xFFFD:
                # fpgm source
                r.fpgm = (textLength, textOffset)
                
                if r.prep[0] == 0x8000:
                    r.prep = (textOffset - r.prep[1], r.prep[1])
            
            elif glyphID == 0xFFFB:
                # cvt source
                r.cvt = (textLength, textOffset)
                
                if r.fpgm[0] == 0x8000:
                    r.fpgm = (textOffset - r.fpgm[1], r.fpgm[1])
            
            elif glyphID == 0xFFFC:
                # reserved (used to compute actual length if cvt textLength == 0x8000)
                r.reserved = (textLength, textOffset)
                
                if r.cvt[0] == 0x8000:
                    r.cvt = (textOffset - r.cvt[1], r.cvt[1])

        allGIDs = sorted(r)
        
        for key in r:
            textLength, textOffset = r[key]
            
            if textLength == 0x8000:
                if key == len(r):
                    #special case for final "normal" record
                    newLength = r.prep[1] - textOffset
                else:
                    nextGID = allGIDs.index(key) + 1
                    newLength = r[nextGID][1] - textOffset

                r[key] = (newLength, textOffset)
                
        if r.magic != (0, 0xABFC1F34):
            raise ValueError("Magic record not found or invalid.")

        return r
    

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        TSILoc(),
        TSILoc({0:(10,0)}),
        )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
