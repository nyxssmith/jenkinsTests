#
# sbix.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for top-level Sbix objects.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.sbix import strike, strike_key

# -----------------------------------------------------------------------------

#
# Classes
#

class Sbix(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing whole 'sbix' tables. These are dicts whose keys are
    StrikeKey objects, and whose values are Strike objects. There is one
    attribute: drawOnlyBitmaps.
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresort = True)
    
    attrSpec = dict(
        drawOnlyBitmaps = dict(
            attr_initfunc = (lambda: False),
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H", 1)  # version
        w.add("H", 1 + (0 if self.drawOnlyBitmaps else 2))
        w.add("L", len(self))
        
        sortedKeys = sorted(self)
        stakes = [w.getNewStake() for i in sortedKeys]
        
        for stake in stakes:
            w.addUnresolvedOffset("L", stakeValue, stake, offsetByteDelta=-4)
        
        for key, stake in zip(sortedKeys, stakes):
            ppem, resolution = key
            w.add("2H", ppem, resolution)
            
            # Note that the staked location comes *after* the ppem and
            # resolution have been written. The Strike's code knows this,
            # and adjusts offsets accordingly.
            
            self[key].buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('sbix')
        else:
            logger = logger.getChild('sbix')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, flags, numStrikes = w.unpack("2HL")
        
        if version != 1:
            logger.error((
              'V1018',
              (version,),
              "Unknown 'sbix' version: %d."))
            
            return None
        
        if flags & 0xFFFC:
            logger.warning((
              'V1019',
              (flags,),
              "The flags value of 0x%04X contains undefined bits. These "
              "will be ignored."))
            
            flags &= 3  # mask off all but valid bits
        
        if not (flags & 1):
            logger.warning((
              'V1020',
              (),
              "The specification for the 'sbix' table requires bit 0 "
              "to always be set."))
        
        r = cls({}, drawOnlyBitmaps=(not (flags & 2)))
        
        if w.length() < 4 * numStrikes:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        offsets = w.group("L", numStrikes)
        SK = strike_key.StrikeKey
        fw = strike.Strike.fromvalidatedwalker
        
        for i, offset in enumerate(offsets):
            subLogger = logger.getChild("strike %d" % (i,))
            wSub = w.subWalker(offset)
            
            if wSub.length() < 4:
                subLogger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            ppem, resolution = wSub.unpack("2H")
            key = SK(ppem, resolution)
            wSub = w.subWalker(offset + 4)
            r[key] = fw(wSub, logger=subLogger, **kwArgs)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        version, flags, numStrikes = w.unpack("2HL")
        r = cls({}, drawOnlyBitmaps=(flags==1))
        offsets = w.group("L", numStrikes)
        SK = strike_key.StrikeKey
        fw = strike.Strike.fromwalker
        
        for offset in offsets:
            wSub = w.subWalker(offset)
            ppem, resolution = wSub.unpack("2H")
            key = SK(ppem, resolution)
            wSub = w.subWalker(offset + 4)
            r[key] = fw(wSub, **kwArgs)
        
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

