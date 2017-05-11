#
# trackdata.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Tracking data for a single orientation (horizontal or vertical).
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.trak import sizedict, trackdata_entry

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    s = set(frozenset(d.perSizeTable) for d in obj.values())
    
    if len(s) > 1:
        logger.error((
          'V0828',
          (),
          "Not all Entries have the same set of PPEM keys."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TrackData(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing full tracking information for one particular orientation
    (i.e. horizontal or vertical). These are dicts whose keys are
    floating-point track numbers and whose values are Entry objects.
    
    >>> _testingValues[0].pprint(editor=_fakeEditor())
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
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    val - ERROR - Not all Entries have the same set of PPEM keys.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "Track %s" % (k,)),
        item_pprintlabelpresort = True,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TrackData object to the specified
        LinkedWriter.
        
        >>> w = writer.LinkedWriter()
        >>> tableStart = w.stakeCurrent()
        >>> w.add("2LH", 0, 0, 0)
        >>> _testingValues[0].buildBinary(w, tableStake=tableStart)
        >>> utilities.hexdump(w.binaryString())
               0 | 0000 0000 0000 0000  0000 0000 0002 0004 |................|
              10 | 0000 0024 FFFF 0000  0122 0034 0001 0000 |...$.....".4....|
              20 | 0123 003C 0009 0000  000B 8000 000E 0000 |.#.<............|
              30 | 0016 0000 FFDD FFEC  FFFF 0006 FFF1 0000 |................|
              40 | 0005 0012                                |....            |
        """
        
        # align to longword boundary before staking
        w.alignToByteMultiple(4)
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        tableStake = kwArgs['tableStake']
        ppemSet = {frozenset(obj.perSizeTable) for obj in self.values()}
        assert len(ppemSet) == 1, "Inconsistent PPEMs!"
        ppems = sorted(ppemSet.pop())
        w.add("2H", len(self), len(ppems))
        sizeTableStake = w.getNewStake()
        w.addUnresolvedOffset("L", tableStake, sizeTableStake)
        d = {}
        
        for track in sorted(self):
            obj = self[track]
            w.add("lH", int(track * 65536), obj.nameTableIndex)
            d[track] = w.getNewStake()
            w.addUnresolvedOffset("H", tableStake, d[track])
        
        w.stakeCurrentWithValue(sizeTableStake)
        w.addGroup("l", (int(n * 65536) for n in ppems))
        
        for track in sorted(self):
            self[track].perSizeTable.buildBinary(
              w,
              stakeValue = d[track],
              ppems = ppems)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TrackData object from the specified walker,
        doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("trackdata")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        nTracks, nSizes, sizesOffset = w.unpack("2HL")
        r = cls()
        
        if nTracks == 0:
            logger.warning((
              'V0822',
              (),
              "The number of tracks is zero. Remove the empty orientation "
              "to save space."))
            
            return r
        
        if nSizes == 0:
            logger.error((
              'V0823',
              (nTracks,),
              "The number of sizes is zero, even though the number of tracks "
              "is %d. This is an error."))
            
            return None
        
        wSizes = w.subWalker(sizesOffset)
        
        if wSizes.length() < 4 * nSizes:
            logger.error((
              'V0824',
              (),
              "The size table is missing or incomplete."))
            
            return None
        
        ppems = [n / 65536 for n in wSizes.group("L", nSizes)]
        
        if ppems != sorted(ppems):
            logger.error((
              'V0825',
              (ppems,),
              "The size table values (%s) are not sorted."))
            
            return None
        
        if w.length() < 8 * nTracks:
            logger.error((
              'V0826',
              (),
              "The track table is missing or incomplete."))
            
            return None
        
        tt = w.group("l2H", nTracks)
        v = [x[0] for x in tt]
        
        if v != sorted(v):
            logger.error((
              'V0827',
              (v,),
              "The track table values (%s) are not sorted."))
            
            return None
        
        fvw = sizedict.SizeDict.fromvalidatedwalker
        Entry = trackdata_entry.Entry
        
        for track, nameIndex, offset in tt:
            track /= 65536
            itemLogger = logger.getChild("track %s" % (track,))
            obj = fvw(w.subWalker(offset), ppems=ppems, logger=itemLogger)
            
            if obj is None:
                return None
            
            r[track] = Entry(nameIndex, obj)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TrackData object from the specified walker.
        
        >>> w = writer.LinkedWriter()
        >>> tableStart = w.stakeCurrent()
        >>> _testingValues[0].buildBinary(w, tableStake=tableStart)
        >>> s = w.binaryString()
        >>> _testingValues[0] == TrackData.frombytes(s)
        True
        """
        
        nTracks, nSizes, sizesOffset = w.unpack("2HL")
        
        ppems = [
          n / 65536
          for n in w.subWalker(sizesOffset).group("L", nSizes)]
        
        r = cls()
        f = sizedict.SizeDict.fromwalker
        Entry = trackdata_entry.Entry
        
        for track, nameIndex, offset in w.group("l2H", nTracks):
            r[track / 65536] = Entry(
              nameIndex,
              f(w.subWalker(offset), ppems=ppems))
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer
    
    _fakeEditor = trackdata_entry._fakeEditor
    _tde = trackdata_entry._testingValues
    
    _testingValues = (
        TrackData({-1.0: _tde[0], 1.0: _tde[1]}),
        
        # bad values start here
        
        TrackData({-1.0: _tde[0], 1.0: _tde[2]}))
    
    del _tde

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
