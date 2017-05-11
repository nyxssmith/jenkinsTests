#
# SPRK_v16.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the current (as of May, 2015) version of the Monotype-defined SPRK
table. This is version 16 (hex 0x10), and the format is completely different
than that of the version 1 objects.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.SPRK import grouptable

# -----------------------------------------------------------------------------

#
# Classes
#

class SPRK(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    """
    
    version = 16
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the SPRK object to the specified LinkedWriter.
        
        >>> obj = SPRK()
        >>> utilities.hexdump(obj.binaryString())
               0 | 0010 0000                                |....            |
        
        >>> gt = grouptable.GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> obj[0] = gt
        >>> utilities.hexdump(obj.binaryString())
               0 | 0010 0001 0000 0000  000A 0005 0004 0003 |................|
              10 | 0006 0000 0007 0001  0008 0003 000F 0002 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        ss = sorted(self)
        w.add("2H", self.version, len(self))
        dStakes = {key: w.getNewStake() for key in ss}
        
        for key in ss:
            w.add("H", key)
            w.addUnresolvedOffset("L", stakeValue, dStakes[key])
        
        for key in ss:
            self[key].buildBinary(w, stakeValue=dStakes[key], **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SPRK object from the specified walker, doing
        validation.
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> obj = SPRK()
        >>> gt = grouptable.GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> obj[0] = gt
        >>> bs = obj.binaryString()
        >>> obj2 = SPRK.fromvalidatedbytes(bs, logger=logger)
        test.SPRK_v16 - DEBUG - Walker has 32 remaining bytes.
        test.SPRK_v16 - DEBUG - Version 16, count 1
        test.SPRK_v16 - DEBUG - Raw list of tags/offsets: ((0, 10),)
        test.SPRK_v16.tag 0.grouptable - DEBUG - Walker has 22 remaining bytes.
        test.SPRK_v16.tag 0.grouptable - DEBUG - Count is 5, raw data is ((4, 3), (6, 0), (7, 1), (8, 3), (15, 2))
        
        >>> obj == obj2
        True
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('SPRK_v16')
        else:
            logger = logger.getChild('SPRK_v16')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        vCheck, numTables = w.unpack("2H")
        logger.debug(('Vxxxx', (vCheck, numTables), "Version %d, count %d"))
        
        if vCheck != cls.version:
            logger.error((
              'V0953',
              (vCheck, vCheck),
              "Was expecting version 16 (0x0010), but got %d (0x%04X)."))
            
            return None
        
        if w.length() < 6 * numTables:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes for directory."))
            
            return None
        
        r = cls()
        tagOffsets = w.group("HL", numTables)
        
        logger.debug((
          'Vxxxx',
          (tagOffsets,),
          "Raw list of tags/offsets: %s"))
        
        lowCheck = 4 + 6 * numTables
        highCheck = w.length()
        fvw = grouptable.GroupTable.fromvalidatedwalker
        
        for i, (tag, offset) in enumerate(tagOffsets):
            if (offset < lowCheck) or (offset >= highCheck):
                logger.error((
                  'Vxxxx',
                  (offset,),
                  "Offset %d is out of range."))
                
                return None
            
            wSub = w.subWalker(offset)
            
            if tag == 0:
                subLogger = logger.getChild("tag %d" % (tag,))
                r[tag] = fvw(wSub, logger=subLogger, **kwArgs)
            
            else:
                logger.error((
                  'Vxxxx',
                  (tag,),
                  "Unknown table tag: %d"))
                
                return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new SPRK object from the specified walker.
        
        >>> obj = SPRK()
        >>> gt = grouptable.GroupTable((3,3,3,3,3,0,0,1,3,2,2,2,2,2,2,2))
        >>> obj[0] = gt
        >>> bs = obj.binaryString()
        >>> obj2 = SPRK.frombytes(bs)
        >>> obj == obj2
        True
        """
        
        vCheck, numTables = w.unpack("2H")
        
        if vCheck != cls.version:
            raise ValueError("Unknown 'SPRK' version: 0x%04X" % (vCheck,))
        
        r = cls()
        tagOffsets = w.group("HL", numTables)
        
        for i, (tag, offset) in enumerate(tagOffsets):
            wSub = w.subWalker(offset)
            
            if tag == 0:
                r[tag] = grouptable.GroupTable.fromwalker(wSub, **kwArgs)
            
            else:
                raise ValueError("Unknown tag: %d" % (tag,))
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


