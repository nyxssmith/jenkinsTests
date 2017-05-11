#
# strike.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a Strike. Note that all of the logic here assumes the Strike data
start with the offset table; the ppem and resolution are taken by the top-
level Sbix object (for the key), and they don't need to be reflected here.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.sbix import glyphrecord

# -----------------------------------------------------------------------------

#
# Classes
#

class Strike(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing a single Strike. These are dicts mapping glyph index
    values to GlyphRecord objects.
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the Strike to the specified writer.
        
        >>> GR = glyphrecord.GlyphRecord
        >>> rec1 = GR(15, -35, 'tiff', b"Some data here")
        >>> rec2 = GR(0, 16, 'tiff', b"ABC")
        >>> obj = Strike({4: rec1, 5: rec2})
        >>> utilities.hexdump(obj.binaryString(fontGlyphCount=10))
               0 | 0000 0030 0000 0030  0000 0030 0000 0030 |...0...0...0...0|
              10 | 0000 0030 0000 0046  0000 0051 0000 0051 |...0...F...Q...Q|
              20 | 0000 0051 0000 0051  0000 0051 000F FFDD |...Q...Q...Q....|
              30 | 7469 6666 536F 6D65  2064 6174 6120 6865 |tiffSome data he|
              40 | 7265 0000 0010 7469  6666 4142 43        |re....tiffABC   |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # The "+2" in the following accounts for the extra offset needed at
        # the end, to compute the size of the last entry.
        
        maxGlyph = utilities.getFontGlyphCount(**kwArgs) - 1
        stakes = [w.getNewStake() for i in range(maxGlyph + 2)]
        
        for stake in stakes:
            
            # The offsetByteDelta in the following allows us to bypass the
            # ppem and resolution here, leaving them for the parent Sbix
            # object to handle.
            
            w.addUnresolvedOffset("L", stakeValue, stake, offsetByteDelta=4)
        
        for glyphIndex in range(maxGlyph + 1):
            stake = stakes[glyphIndex]
            
            if (glyphIndex not in self) or (self[glyphIndex] is None):
                w.stakeCurrentWithValue(stake)
            else:
                self[glyphIndex].buildBinary(w, stakeValue=stake)
        
        w.stakeCurrentWithValue(stakes[-1])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphRecord object from the specified walker,
        doing validation.
        
        >>> logger = utilities.makeDoctestLogger("strike")
        >>> fvb = Strike.fromvalidatedbytes
        >>> GR = glyphrecord.GlyphRecord
        >>> rec1 = GR(15, -35, 'tiff', b"Some data here")
        >>> rec2 = GR(0, 16, 'tiff', b"ABC")
        >>> obj = Strike({4: rec1, 5: rec2})
        >>> bs = obj.binaryString(fontGlyphCount=10)
        >>> obj = fvb(bs, fontGlyphCount=10, logger=logger)
        strike.strike - DEBUG - Walker has 77 remaining bytes.
        strike.strike.glyph 4.glyphrecord - DEBUG - Walker has 22 remaining bytes.
        strike.strike.glyph 5.glyphrecord - DEBUG - Walker has 11 remaining bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('strike')
        else:
            logger = logger.getChild('strike')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        baseOffset = w.getOffset()
        fgc = utilities.getFontGlyphCount(**kwArgs)
        
        if fgc is None:
            logger.error((
              'V1017',
              (),
              "Unable to ascertain the font's glyph count."))
            
            return None
        
        if w.length() < (4 * (fgc + 1)):
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        offsets = w.group("L", fgc + 1)
        fw = glyphrecord.GlyphRecord.fromvalidatedwalker
        r = cls()
        
        for i in range(fgc):
            if offsets[i] == offsets[i + 1]:
                continue
            
            wSub = w.subWalker(
              offsets[i] - 4,
              newLimit = baseOffset + offsets[i + 1] - 4)
            
            subLogger = logger.getChild("glyph %d" % (i,))
            r[i] = fw(wSub, logger=subLogger, **kwArgs)
            
            if r[i] is None:
                return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new GlyphRecord object from the specified walker.
        
        >>> GR = glyphrecord.GlyphRecord
        >>> rec1 = GR(15, -35, 'tiff', b"Some data here")
        >>> rec2 = GR(0, 16, 'tiff', b"ABC")
        >>> obj = Strike({4: rec1, 5: rec2})
        >>> bs = obj.binaryString(fontGlyphCount=10)
        >>> Strike.frombytes(bs, fontGlyphCount=10).pprint()
        4:
          originOffsetX: 15
          originOffsetY: -35
          graphicType: tiff
          data: b'Some data here'
        5:
          originOffsetX: 0
          originOffsetY: 16
          graphicType: tiff
          data: b'ABC'
        """
        
        baseOffset = w.getOffset()
        fgc = utilities.getFontGlyphCount(**kwArgs)
        offsets = w.group("L", fgc + 1)
        fw = glyphrecord.GlyphRecord.fromwalker
        r = cls()
        
        for i in range(fgc):
            if offsets[i] == offsets[i + 1]:
                continue
            
            wSub = w.subWalker(
              offsets[i] - 4,
              newLimit = baseOffset + offsets[i + 1] - 4)
            
            r[i] = fw(wSub, **kwArgs)
        
        return r

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

