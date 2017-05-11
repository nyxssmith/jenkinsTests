#
# Zapf.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entire 'Zapf' tables.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.Zapf import glyphinfo

# -----------------------------------------------------------------------------

#
# Classes
#

class Zapf(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'Zapf' tables. These are dicts mapping glyph
    indices to GlyphInfo objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "Glyph %d" % (k,)),
        item_pprintlabelpresort = True,
        item_renumberdirectkeys = True)
    
    #
    # Methods
    #
    
    def _makePools(self, w):
        featPool = {}  # immut -> (obj, stake)
        giPool = {}  # groupObj -> stake
        gigPool = {}  # groupTupleObj -> stake
        
        for glyphInfoObj in self.values():
            featObj = glyphInfoObj.features
            
            if featObj is not None:
                immut = featObj.asImmutable()
                
                if immut not in featPool:
                    featPool[immut] = (featObj, w.getNewStake())
            
            groupObj = glyphInfoObj.groups
            
            if groupObj is not None:
                altsObj = groupObj.altForms
                
                if altsObj is not None or len(groupObj) > 1:
                    gigPool[groupObj] = w.getNewStake()
                
                # the following is NOT an elif, since we need the groups too
                if altsObj is not None:
                    if altsObj not in giPool:
                        giPool[altsObj] = w.getNewStake()
                
                for obj in groupObj:
                    if obj not in giPool:
                        giPool[obj] = w.getNewStake()
        
        return (featPool, giPool, gigPool)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Zapf object to the specified LinkedWriter.
        The following keyword arguments are used:
        
            fontGlyphCount      The number of glyphs in the font. This is
                                required.
            
            stakeValue          The stake representing the start of this
                                GlyphInfo record. This is optional (but usual).
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)  # version
        extraInfoStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, extraInfoStake)
        fgc = kwArgs['fontGlyphCount']
        glyphInfoStakes = [None] * fgc
        
        for i in range(fgc):
            stake = glyphInfoStakes[i] = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, stake)
        
        featPool, giPool, gigPool = self._makePools(w)
        
        for i in range(fgc):
            self[i].buildBinary(
              w,
              stakeValue = glyphInfoStakes[i],
              extraInfoStake = extraInfoStake,
              featPool = featPool,
              giPool = giPool,
              gigPool = gigPool)
        
        w.stakeCurrentWithValue(extraInfoStake)
        
        for obj, stake in sorted(featPool.values(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        for obj, stake in sorted(giPool.items(), key=operator.itemgetter(1)):
            obj.buildBinary(w, stakeValue=stake)
        
        for obj, stake in sorted(gigPool.items(), key=operator.itemgetter(1)):
            obj.buildBinary(
              w,
              stakeValue = stake,
              extraInfoStake = extraInfoStake,
              giPool = giPool)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Zapf object from the specified walker. The
        following keyword arguments are used:
        
            fontGlyphCount      The number of glyphs in the font. This keyword
                                argument is required.
            
            logger              A logger to which messages will be posted.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("Zapf")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x10000:
            logger.error((
              'V0760',
              (version,),
              "Expected version 0x00010000 but got 0x%08X instead."))
            
            return None
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes for extra offset."))
            return None
        
        wExtra = w.subWalker(w.unpack("L"))
        r = cls()
        fgc = kwArgs['fontGlyphCount']
        
        if w.length() < 4 * fgc:
            logger.error(('V0004', (), "Offsets incomplete or missing."))
            return None
        
        offsets = w.group("L", fgc)
        f = glyphinfo.GlyphInfo.fromvalidatedwalker
        featPool = {0xFFFFFFFF: None}
        giPool = {}
        groupTuplePool = {0xFFFFFFFF: None}
        
        for glyphIndex, offset in enumerate(offsets):
            r[glyphIndex] = f(
              w.subWalker(offset),
              featPool = featPool,
              groupPool = giPool,
              groupTuplePool = groupTuplePool,
              wExtra = wExtra,
              logger = logger.getChild("glyph %d" % (glyphIndex,)))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Zapf object from the specified walker. The
        following keyword arguments are used:
        
            fontGlyphCount      The number of glyphs in the font. This keyword
                                argument is required.
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'Zapf' version: 0x%08X" % (version,))
        
        wExtra = w.subWalker(w.unpack("L"))
        r = cls()
        offsets = w.group("L", kwArgs['fontGlyphCount'])
        f = glyphinfo.GlyphInfo.fromwalker
        featPool = {0xFFFFFFFF: None}
        giPool = {}
        groupTuplePool = {0xFFFFFFFF: None}
        
        for glyphIndex, offset in enumerate(offsets):
            r[glyphIndex] = f(
              w.subWalker(offset),
              featPool = featPool,
              groupPool = giPool,
              groupTuplePool = groupTuplePool,
              wExtra = wExtra)
        
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
