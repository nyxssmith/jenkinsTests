#
# VDMX.py
#
# Copyright © 2010-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for full VDMX tables.
"""

# System imports
import operator
import pickle

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.VDMX import group, ratio_v0, ratio_v1, vdmxrecord
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

    if 'vdmxpicklefile' in editor.__dict__:
        tmpfile = open(editor.__dict__['vdmxpicklefile'], 'rb+')
        dNew = pickle.load(tmpfile)
        return (d != dNew, dNew)
    
    dNew = d.__deepcopy__()
    
    for i, o in enumerate(d):
        r = o.recalculated(**kwArgs)
        dNew[i] = r
    
    return (d != dNew, dNew)

def _validate(d, **kwArgs):
    """
    Get recalculated version of table (see _recalc) and call each item's
    isValid() with 'recalculateditem' kwArg.
    """

    logger = kwArgs['logger']
    
    for i,st in enumerate(d):
        if not(st.group):
            logger.error((
              'V0915',
              (i,),
              "Subtable %d could not be validated because it "
              " is missing, empty, or could not be read."))
            return False
    
        if len(st.group) == 0:
            logger.warning((
                'V0915',
                (i,),
                "Subtable %d has an empty ppem list!"))

    if 'scaler' in kwArgs:
        try:
            r = d.recalculated(**kwArgs)
        
        except ScalerError:
            logger.error((
              'V0554',
              (),
              "An error occured in the scaler during device metrics "
              "calculation, preventing validation."))
            
            return False
        
        isOK = True
        
        for i, ri in enumerate(r):
            isOK = d[i].isValid(recalculateditem=ri, **kwArgs) and isOK
        
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

class VDMX(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing entire VDMX tables. These are lists of VDMXRecord
    objects.
    
    >>> _testingValues[1].pprint()
    Entry #1:
      Ratio:
        Start ratio: 2:1
        End ratio: 1:1
        Char set: All glyphs (0)
      Group:
        14 PPEM:
          Maximum y-value (in pixels): 10
          Minimum y-value (in pixels): -3
        15 PPEM:
          Maximum y-value (in pixels): 11
          Minimum y-value (in pixels): -3
        16 PPEM:
          Maximum y-value (in pixels): 11
          Minimum y-value (in pixels): -4
    Entry #2:
      Ratio:
        Start ratio: 4:3
        End ratio: 1:1
        Char set: All glyphs (1)
      Group:
        14 PPEM:
          Maximum y-value (in pixels): 10
          Minimum y-value (in pixels): -3
        16 PPEM:
          Maximum y-value (in pixels): 11
          Minimum y-value (in pixels): -4
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Entry #%d" % (i + 1,)),
        seq_recalculatefunc = _recalc,
        seq_validatefunc = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the VDMX object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0002 0002 0002  0102 0104 0304 0012 |................|
              10 | 0028 0003 0E10 000E  000A FFFD 000F 000B |.(..............|
              20 | FFFD 0010 000B FFFC  0002 0E10 000E 000A |................|
              30 | FFFD 0010 000B FFFC                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # To determine the version, canvass the Ratios
        
        versionSet = set(obj.ratio.ratioVersion for obj in self)
        
        if len(versionSet) > 1:
            raise ValueError("Cannot mix version 0 and version 1 Ratios!")
        
        w.add("H", versionSet.pop())
        
        # Build the set of (possibly combined) Groups and associated stakes
        
        pool = {}
        
        for obj in self:
            immut = obj.group.asImmutable()
            
            if immut not in pool:
                pool[immut] = (w.getNewStake(), obj.group)
        
        w.add("2H", len(pool), len(self))
        
        for obj in self:
            obj.ratio.buildBinary(w, **kwArgs)
        
        for obj in self:
            immut = obj.group.asImmutable()
            w.addUnresolvedOffset("H", stakeValue, pool[immut][0])
        
        it = sorted(pool.items(), key=(lambda x: sorted(x[0][1])))
        
        for immut, (stake, groupObj) in it:
            groupObj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a VDMX object from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == VDMX.frombytes(obj.binaryString())
        True
        """
        
        version = w.unpack("H")
        
        if version != 0 and version != 1:
            raise ValueError("Unknown VDMX version: %d" % (version,))
        
        count = w.unpack("2xH")  # ignore numRecs, not needed
        fw = (ratio_v1.Ratio if version else ratio_v0.Ratio).fromwalker
        ratios = [fw(w, **kwArgs) for i in range(count)]
        offsets = w.group("H", count)
        fw = group.Group.fromwalker
        groups = [fw(w.subWalker(offset, **kwArgs)) for offset in offsets]
        f = vdmxrecord.VDMXRecord
        return cls(f(r, g) for r, g in zip(ratios, groups))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new VDMX. However, it also
        does validation via the logging module (the client should have done a
        logging.basicConfig call prior to calling this method, unless a logger
        is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> fvb = VDMX.fromvalidatedbytes

        >>> b = utilities.fromhex("00 03 00 00 00 00 00 00")
        >>> obj = fvb(b, logger=logger)
        test.VDMX - DEBUG - Walker has 8 remaining bytes.
        test.VDMX - ERROR - Table version 3 is not known
        test.VDMX - DEBUG - nRecs is 0
        test.VDMX - INFO - All of the VDMX groups are within the table
        
        >>> obj = fvb(b[2:4], logger=logger)
        test.VDMX - DEBUG - Walker has 2 remaining bytes.
        test.VDMX - ERROR - Length 2 is too short (minimum 8)

        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.VDMX - DEBUG - Walker has 56 remaining bytes.
        test.VDMX - INFO - Table version is 1
        test.VDMX - DEBUG - nRecs is 2
        test.VDMX - INFO - All of the VDMX groups are within the table
        test.VDMX.Group - DEBUG - Walker has 38 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 32 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 26 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 20 remaining bytes.
        test.VDMX.Group - DEBUG - Walker has 16 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 10 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 4 remaining bytes.
        test.VDMX.[2:1:2].Group - DEBUG - Walker has 38 remaining bytes.
        test.VDMX.[2:1:2].Group.Record - DEBUG - Walker has 32 remaining bytes.
        test.VDMX.[2:1:2].Group.Record - DEBUG - Walker has 26 remaining bytes.
        test.VDMX.[2:1:2].Group.Record - DEBUG - Walker has 20 remaining bytes.
        test.VDMX.[4:3:4].Group - DEBUG - Walker has 16 remaining bytes.
        test.VDMX.[4:3:4].Group.Record - DEBUG - Walker has 10 remaining bytes.
        test.VDMX.[4:3:4].Group.Record - DEBUG - Walker has 4 remaining bytes.

        >>> b = utilities.fromhex("00 01 00 01 00 01 05 01 01 01 00 FF 00 01")
        >>> obj = fvb(b, logger=logger)
        test.VDMX - DEBUG - Walker has 14 remaining bytes.
        test.VDMX - INFO - Table version is 1
        test.VDMX - DEBUG - nRecs is 1
        test.VDMX - ERROR - A VDMX group isn't within the table

        >>> b = utilities.fromhex("00 01 00 01 00 01 05 01 01 01 00 0C 00 01 08 08 00 08 00 05 FF FE")
        >>> obj = fvb(b, logger=logger)
        test.VDMX - DEBUG - Walker has 22 remaining bytes.
        test.VDMX - INFO - Table version is 1
        test.VDMX - DEBUG - nRecs is 1
        test.VDMX - INFO - All of the VDMX groups are within the table
        test.VDMX.Group - DEBUG - Walker has 10 remaining bytes.
        test.VDMX.Group.Record - DEBUG - Walker has 4 remaining bytes.
        test.VDMX.[1:1:1].Group - DEBUG - Walker has 10 remaining bytes.
        test.VDMX.[1:1:1].Group.Record - DEBUG - Walker has 4 remaining bytes.
        """

        logger = kwArgs.pop('logger', None)
        if logger is None:
            logger = logging.getLogger().getChild('VDMX')
        else:
            logger = logger.getChild('VDMX')
            
        tblLen = w.length()
        logger.debug(('V0001', (tblLen,), "Walker has %d remaining bytes."))
        
        if tblLen < 8:
            logger.error((
              'V0004',
              (tblLen,),
              "Length %d is too short (minimum 8)"))
            
            return None
        
        version = w.unpack("H")
        
        if version > 1:
            logger.error((
            'E2504',
            (version,),
            "Table version %d is not known"))
        
        else:
            logger.info(('P2503', (version,), "Table version is %d"))

        nrecs = w.unpack("H")  # NOTE: fromwalker ignores numRecs, but we're
                               #       going to check/report it here.
        
        logger.debug(('XXXXX', (nrecs,), "nRecs is %d"))
        count = w.unpack("H")
        actLen = w.length()
        minLen = count * 6 # 4 bytes for each Ratio and 2 bytes for each offset

        if actLen < minLen:
            logger.error((
              'V0004',
              (actLen, count, minLen),
              'Remaining length %d is too short for %d Ratios; expected %d'))
            
            return None

        fvw = (ratio_v1 if version else ratio_v0).Ratio.fromvalidatedwalker
        ratios = [fvw(w, logger=logger, **kwArgs) for i in range(count)]
        offsets = w.group("H", count)

        for o in offsets:
            if o > tblLen:
                logger.error((
                  'E2501',
                  (),
                  "A VDMX group isn't within the table"))
                
                # NOTE: MS also has "offset is *invalid*"; not sure
                #       how to determine that...overlap?
                
                return None

        logger.info((
          'P2501',
          (),
          "All of the VDMX groups are within the table"))
        
        # similar to above, there's a P2502 "were in a valid range"
        
        fvw = group.Group.fromvalidatedwalker
        
        groups = [
          fvw(w.subWalker(offset, **kwArgs), logger=logger)
          for offset in offsets]
        
        groups = []
        
        for i, offset in enumerate(offsets):
            ratioxyy = (
              ratios[i].xRatio,
              ratios[i].yStartRatio,
              ratios[i].yEndRatio)
            
            grouplogger = logger.getChild("[%d:%d:%d]" % ratioxyy )
            
            groups.append(
              fvw(w.subWalker(offset, **kwArgs), logger=grouplogger))
        
        f = vdmxrecord.VDMXRecord
        return cls(f(r, g) for r, g in zip(ratios, groups))       

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _tv = vdmxrecord._testingValues
    
    _testingValues = (
        VDMX(),
        VDMX(_tv[1:3]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
