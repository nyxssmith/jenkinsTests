#
# ankr.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to entire 'ankr' tables.
"""

# System imports
import logging
import operator

# Other imports
from fontio3.ankr import anchorpoints
from fontio3.fontdata import mapmeta
from fontio3.utilities import lookup

# -----------------------------------------------------------------------------

#
# Classes
#

class Ankr(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'ankr' tables. These are dicts mapping glyph
    indices to AnchorPoints objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Ankr object to the specified writer. The
        following keyword arguments are supported:
        
            preferredIOLookupFormat     If you need the actual input glyph to
                                        output glyph lookup to be written in a
                                        specific format, use this keyword. The
                                        default (as usual for Lookup objects)
                                        is to use the smallest one possible.
                                        
                                        Note this keyword is usually specified
                                        in the perTableOptions dict passed into
                                        the Editor's writeFont() method.
        
            stakeValue                  A value that will stake the start of
                                        the data. This is optional.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0000 0000 000C  0000 0030 0006 0004 |...........0....|
              10 | 0005 0010 0002 0004  000A 001C 000B 0010 |................|
              20 | 000E 001C 000F 001C  0064 0000 FFFF FFFF |.........d......|
              30 | 0000 0003 FF38 0000  0000 0096 0000 FF06 |.....8..........|
              40 | 0000 0002 0000 0000  0064 0000 0000 0002 |.........d......|
              50 | 0064 FF9C 0102 0304                      |.d......        |
        
        >>> d = {'preferredIOLookupFormat': 2}
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0000 0000 0000 000C  0000 003A 0002 0006 |...........:....|
              10 | 0004 0018 0002 0000  000A 000A 001C 000B |................|
              20 | 000B 0010 000F 000E  001C 0064 0064 0000 |...........d.d..|
              30 | FFFF FFFF FFFF FFFF  FFFF 0000 0003 FF38 |...............8|
              40 | 0000 0000 0096 0000  FF06 0000 0002 0000 |................|
              50 | 0000 0064 0000 0000  0002 0064 FF9C 0102 |...d.......d....|
              60 | 0304                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", 0, 0)  # version, flags
        lookupStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, lookupStake)
        dataStake = w.getNewStake()
        w.addUnresolvedOffset("L", stakeValue, dataStake)
        w.stakeCurrentWithValue(lookupStake)
        
        # To build the lookup we first need to determine which format is
        # smallest.
        
        d = {}
        
        for glyph, obj in self.items():
            immut = obj.asImmutable()
            d.setdefault(immut, set()).add(glyph)
        
        stakeDict = {}
        
        for immut, glyphSet in d.items():
            sv = w.getNewStake()
            
            for glyph in glyphSet:
                stakeDict[glyph] = sv
        
        # For now, raise an error if the largest stake is >64K; if this ever
        # actually arises, we could remap the stakes temporarily.
        
        if max(stakeDict.values()) > 65535:
            raise ValueError("Too many stakes!")
        
        lk = lookup.Lookup(stakeDict)
        preferredFormat = kwArgs.get('preferredIOLookupFormat', None)
        
        if preferredFormat is None:
            bestFormat = lk.binaryString(noGaps=True)[1]
            lk._preferredFormat = bestFormat
        
        else:
            lk._preferredFormat = preferredFormat
        
        lk.buildBinary(w, baseStake=dataStake)
        
        # Now add the actual data
        
        w.stakeCurrentWithValue(dataStake)
        it = sorted(d.items(), key=operator.itemgetter(0))
        
        for immut, glyphSet in it:
            glyph = glyphSet.pop()
            self[glyph].buildBinary(w, stakeValue=stakeDict[glyph])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ankr object from the specified walker, doing
        source validation.
        
        >>> bs = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Ankr.fromvalidatedbytes
        >>> obj = fvb(bs, logger=logger)
        fvw.Ankr - DEBUG - Walker has 88 remaining bytes.
        fvw.Ankr.lookup_aat - DEBUG - Walker has 76 remaining bytes.
        fvw.Ankr.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 74 remaining bytes.
        fvw.Ankr.glyph 10.anchorpoints - DEBUG - Walker has 12 remaining bytes.
        fvw.Ankr.glyph 10.anchorpoints.[0].anchorpoint - DEBUG - Walker has 8 remaining bytes.
        fvw.Ankr.glyph 10.anchorpoints.[1].anchorpoint - DEBUG - Walker has 4 remaining bytes.
        fvw.Ankr.glyph 11.anchorpoints - DEBUG - Walker has 24 remaining bytes.
        fvw.Ankr.glyph 11.anchorpoints.[0].anchorpoint - DEBUG - Walker has 20 remaining bytes.
        fvw.Ankr.glyph 11.anchorpoints.[1].anchorpoint - DEBUG - Walker has 16 remaining bytes.
        fvw.Ankr.glyph 100.anchorpoints - DEBUG - Walker has 40 remaining bytes.
        fvw.Ankr.glyph 100.anchorpoints.[0].anchorpoint - DEBUG - Walker has 36 remaining bytes.
        fvw.Ankr.glyph 100.anchorpoints.[1].anchorpoint - DEBUG - Walker has 32 remaining bytes.
        fvw.Ankr.glyph 100.anchorpoints.[2].anchorpoint - DEBUG - Walker has 28 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(bs[:3], logger=logger)
        fvw.Ankr - DEBUG - Walker has 3 remaining bytes.
        fvw.Ankr - ERROR - Insufficient bytes.
        
        >>> fvb(bs[:14], logger=logger)
        fvw.Ankr - DEBUG - Walker has 14 remaining bytes.
        fvw.Ankr.lookup_aat - DEBUG - Walker has 2 remaining bytes.
        fvw.Ankr.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 0 remaining bytes.
        fvw.Ankr.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("Ankr")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, flags, lookupOffset, dataOffset = w.unpack("2H2L")
        
        if version != 0:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0, but got version %d instead."))
            
            return None
        
        if flags:
            logger.warning((
              'V0853',
              (flags,),
              "Flags should be zero but were %04X instead."))
        
        if lookupOffset < 12:
            logger.error((
              'V0854',
              (lookupOffset,),
              "The lookupTableOffset value of %d is within the 'ankr' "
              "table's header, and thus incorrect."))
            
            return None
        
        wLookup = w.subWalker(lookupOffset)
        lk = lookup.Lookup.fromvalidatedwalker(wLookup, logger=logger)
        
        if lk is None:
            return None
        
        if dataOffset < 12:
            logger.error((
              'V0855',
              (dataOffset,),
              "The glyphDataTableOffset value of %d is within the 'ankr' "
              "table's header, and thus incorrect."))
            
            return None
        
        wData = w.subWalker(dataOffset)
        fvw = anchorpoints.AnchorPoints.fromvalidatedwalker
        r = cls()
        pool = {}
        
        for glyphIndex, dataOffset in lk.items():
            if dataOffset not in pool:
                obj = fvw(
                  wData.subWalker(dataOffset),
                  logger = logger.getChild("glyph %d" % (glyphIndex,)))
                
                if obj is None:
                    return None
                
                pool[dataOffset] = obj
            
            r[glyphIndex] = pool[dataOffset]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Ankr object from the specified walker.
        
        >>> bs = _testingValues[1].binaryString()
        >>> obj = Ankr.frombytes(bs)
        >>> obj == _testingValues[1]
        True
        """
        
        version, flags, lookupOffset, dataOffset = w.unpack("2H2L")
        
        if version:
            raise ValueError("Unknown 'ankr' version: %04X" % (version,))
        
        wLookup = w.subWalker(lookupOffset)
        lk = lookup.Lookup.fromwalker(wLookup)
        wData = w.subWalker(dataOffset)
        fw = anchorpoints.AnchorPoints.fromwalker
        r = cls()
        pool = {}
        
        for glyphIndex, dataOffset in lk.items():
            if dataOffset not in pool:
                pool[dataOffset] = fw(wData.subWalker(dataOffset))
            
            r[glyphIndex] = pool[dataOffset]
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _tv = anchorpoints._testingValues
    
    _testingValues = (
        Ankr(),
        
        Ankr({10: _tv[1], 11: _tv[2], 14: _tv[1], 15: _tv[1], 100: _tv[3]}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
