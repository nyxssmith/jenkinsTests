#
# trak.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for AAT 'trak' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.trak import trackdata

# -----------------------------------------------------------------------------

#
# Classes
#

class Trak(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire AAT 'trak' tables. These are simple objects
    with two attributes: horizontal and vertical.
    
    >>> _testingValues[0].pprint(editor=_fakeEditor())
    Horizontal track data:
      Track -1.0:
        Track 'name' table index: 290 ('Tight')
        Per-size shifts:
          9.0 ppem shift in FUnits: -35
          11.5 ppem shift in FUnits: -20
          14.0 ppem shift in FUnits: -1
          22.0 ppem shift in FUnits: 6
      Track 1.0:
        Track 'name' table index: 291 ('Loose')
        Per-size shifts:
          9.0 ppem shift in FUnits: -15
          11.5 ppem shift in FUnits: 0
          14.0 ppem shift in FUnits: 5
          22.0 ppem shift in FUnits: 18
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        horizontal = dict(
            attr_followsprotocol = True,
            attr_label = "Horizontal track data",
            attr_showonlyiftrue = True),
        
        vertical = dict(
            attr_followsprotocol = True,
            attr_label = "Vertical track data",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Trak object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0001 0000 0000 000C  0000 0000 0002 0004 |................|
              10 | 0000 0024 FFFF 0000  0122 0034 0001 0000 |...$.....".4....|
              20 | 0123 003C 0009 0000  000B 8000 000E 0000 |.#.<............|
              30 | 0016 0000 FFDD FFEC  FFFF 0006 FFF1 0000 |................|
              40 | 0005 0012                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("LH", 0x10000, 0)
        
        if self.horizontal is not None:
            hStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, hStake)
        else:
            w.add("H", 0)
        
        if self.vertical is not None:
            vStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, vStake)
        else:
            w.add("H", 0)
        
        w.add("H", 0)
        
        if self.horizontal:
            self.horizontal.buildBinary(
              w,
              tableStake = stakeValue,
              stakeValue = hStake)
        
        if self.vertical:
            self.vertical.buildBinary(
              w,
              tableStake = stakeValue,
              stakeValue = vStake)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Trak object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("trak")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, format, hOffset, vOffset, rsrvd = w.unpack("L4H")
        
        if version != 0x10000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00010000 but got 0x%08X instead."))
            
            return None
        
        if format:
            logger.error((
              'V0829',
              (format,),
              "Expected format 0, but got %d instead."))
            
            return None
        
        if rsrvd:
            logger.warning((
              'V0830',
              (),
              "The zero-reserved field in the 'trak' header had "
              "a nonzero value."))
        
        if hOffset:
            wSub = w.subWalker(0, relative=False)
            wSub.skip(hOffset)
            
            hTable = trackdata.TrackData.fromvalidatedwalker(
              wSub,
              logger = logger.getChild("horiz"))
            
            if hTable is None:
                return None
        
        else:
            hTable = None
        
        if vOffset:
            wSub = w.subWalker(0, relative=False)
            wSub.skip(vOffset)
            
            vTable = trackdata.TrackData.fromvalidatedwalker(
              wSub,
              logger = logger.getChild("vert"))
            
            if vTable is None:
                return None
        
        else:
            vTable = None
        
        return cls(hTable, vTable)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Trak object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == Trak.frombytes(obj.binaryString())
        True
        """
        
        version, format, hOffset, vOffset = w.unpack("L3H2x")
        
        if version != 0x10000 or format != 0:
            raise ValueError("Unknown version or format in 'trak' table!")
        
        if hOffset:
            wSub = w.subWalker(0, relative=False)
            wSub.skip(hOffset)
            hTable = trackdata.TrackData.fromwalker(wSub)
        
        else:
            hTable = None
        
        if vOffset:
            wSub = w.subWalker(0, relative=False)
            wSub.skip(vOffset)
            vTable = trackdata.TrackData.fromwalker(wSub)
        
        else:
            vTable = None
        
        return cls(hTable, vTable)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _fakeEditor = trackdata._fakeEditor
    _tdv = trackdata._testingValues
    
    _testingValues = (
        Trak(horizontal=_tdv[0]),)
    
    del _tdv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
