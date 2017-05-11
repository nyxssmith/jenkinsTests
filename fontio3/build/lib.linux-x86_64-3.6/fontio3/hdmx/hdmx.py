#
# hdmx.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'hdmx' tables.
"""

# System imports
import pickle

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.hdmx import ppemdict
from fontio3.utilities import ScalerError

# -----------------------------------------------------------------------------

#
# Private functions
#

def _recalc(d, **kwArgs):
    """
    Look for cached recalculated table first; if present, unpickle and return
    it. Otherwise, recalc by calling each item's recalc *from here* since this
    is full recalc.
    """

    editor = kwArgs['editor']

    if 'hdmxpicklefile' in editor.__dict__:
        tmpfile = open(editor.__dict__['hdmxpicklefile'], 'rb+')
        dNew = pickle.load(tmpfile)
        return (d != dNew, dNew)
    
    dNew = d.__deepcopy__()
    
    for o in d.keys():
        dNew[o] = d[o].recalculated(**kwArgs)
    
    return (d != dNew, dNew)

def _validate(d, **kwArgs):
    """
    Get recalculated version of table (see _recalc) and call each item's
    isValid() with 'recalculateditem' kwArg.
    """

    logger = kwArgs['logger']

    if 'scaler' in kwArgs:
        try:
            dNew = d.recalculated(**kwArgs)
        
        except ScalerError:
            logger.error((
              'V0554',
              (),
              "An error occured in the scaler during device metrics "
              "calculation, preventing validation."))
            
            return False
        
        isOK = True
        kwArgs.pop('recalculateditem', None)
        
        for i in sorted(dNew.keys()):
            isOK = d[i].isValid(recalculateditem=dNew[i], **kwArgs) and isOK 
               
        return isOK
    
    logger.warning((
      'V0785',
      (),
      "Device metrics will not be tested against scaler results "
      "because a scaler was not supplied."))
    
    return False

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hdmx(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'hdmx' tables. These are dicts mapping PPEM
    values to PPEMDict objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda n: "%d PPEM" % (n,)),
        item_pprintlabelpresort = True,
        map_recalculatefunc=_recalc,
        map_validatefunc=_validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Hdmx object to the specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        fontGlyphCount = kwArgs.pop('fontGlyphCount')
        repertoires = {frozenset(d) for d in self.values()}
        
        if len(repertoires) > 1:
            raise ValueError("Inconsistent key sets in member PPEMDicts!")
        
        if repertoires.pop() != frozenset(range(fontGlyphCount)):
            raise ValueError("Key sets do not match font's glyph count!")
        
        sizeDevRec = ((fontGlyphCount + 5) // 4) * 4
        w.add("2HL", 0, len(self), sizeDevRec)
        
        for key in sorted(self):
            self[key].buildBinary(w, fontGlyphCount=fontGlyphCount, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Hdmx. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> from fontio3 import utilities
        >>> logger = utilities.makeDoctestLogger('test')
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('hdmx')
        else:
            logger = logger.getChild('hdmx')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        version, count, sizeDevRec = w.unpack("2HL")
        
        if version != 0:
            logger.error((
              'E1206',
              (version,),
              "Expected version zero, but got %d"))
        
        else:
            logger.info((
              'V0895',
              (),
              "Table version is 0"))
        
        if count == 0:
            logger.warning(('V0231', (), "Device record count is zero"))
        
        else:
            logger.info((
              'V0896',
              (count,),
              "Device record count is %d"))
        
        fontGlyphCount = kwArgs.pop('fontGlyphCount')
        expectedSizeDevRec = ((fontGlyphCount + 5) // 4) * 4
        
        if sizeDevRec % 4:
            logger.error((
              'E1203',
              (),
              "Device record size is not a multiple of 4"))
        
        if sizeDevRec != expectedSizeDevRec:
            logger.error((
              'E1204',
              (expectedSizeDevRec, sizeDevRec),
              "Expected a Device record size of %d, but got %d"))
        
        else:
            logger.info((
              'V0897',
              (),
              "The table's device record size matches the expected value."))
        
        r = cls()
        fvw = ppemdict.PPEMDict.fromvalidatedwalker
        seen = set()
        lastSeen = None
        kwArgs.pop('sizeDeviceRecord', None)
        
        for i in range(count):
            itemLogger = logger.getChild("[%d]" % (i,))
            
            obj = fvw(
              w,
              logger = itemLogger,
              fontGlyphCount = fontGlyphCount,
              sizeDeviceRecord = sizeDevRec,
              **kwArgs)
            
            if obj is None:
                return None
            
            if lastSeen is not None:
                if obj.ppem in seen:
                    logger.error((
                      'E1201',
                      (obj.ppem,),
                      "Duplicate record for %d PPEM"))
                    
                    return None
                
                elif obj.ppem < lastSeen:
                    logger.error((
                      'E1205',
                      (),
                      "Device records not sorted by PPEM"))
                    
                    return None
            
            lastSeen = obj.ppem
            seen.add(obj.ppem)
            r[obj.ppem] = obj
            
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        version, count, sizeDevRec = w.unpack("2HL")
        
        if version != 0:
            raise ValueError("Unknown 'hdmx' version: 0x%04X" % (version,))
        
        r = cls()
        fw = ppemdict.PPEMDict.fromwalker
        fontGlyphCount = kwArgs.pop('fontGlyphCount')
        
        while count:
            obj = fw(w, fontGlyphCount=fontGlyphCount, **kwArgs)
            r[obj.ppem] = obj
            count -= 1
        
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
