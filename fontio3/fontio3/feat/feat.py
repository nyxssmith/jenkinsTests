#
# feat.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'feat' tables.
"""

# System imports
import logging

# Other imports
from fontio3.feat import feature
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Feat(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire 'feat' tables. These are dicts mapping feature
    indices (unsigned 16-bit values) to Feature objects.
    
    >>> _testingValues[1].pprint(editor=_fakeEditor())
    Feature index 1:
      Settings:
        0: 303 ('Required Ligatures On')
        2: 304 ('Common Ligatures On')
      Default value: 0
      Feature name index: 308 ('Ligatures')
      Settings are mutually exclusive: False
    Feature index 3:
      Settings:
        0: 306 ('Regular')
        1: 307 ('Small Caps')
      Default value: 1
      Feature name index: 309 ('Lettercase')
      Settings are mutually exclusive: True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Feature index %d" % (i,)),
        item_pprintlabelpresort = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Feat object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 0002 0000  0000 0000 0001 0002 |................|
              10 | 0000 0024 0000 0134  0003 0002 0000 002C |...$...4.......,|
              20 | C001 0135 0000 012F  0002 0130 0000 0132 |...5.../...0...2|
              30 | 0001 0133                                |...3            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("LH6x", 0x10000, len(self))
        pool = {}
        
        for featIndex in sorted(self):
            self[featIndex].buildBinary(
              w,
              featureIndex=featIndex,
              baseStake=stakeValue,
              settingPool=pool)
        
        for stake, obj in sorted(pool.values()):
            obj.buildBinary(w, stakeValue=stake)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Feat object from the specified walker, doing
        source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Feat.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.feat - DEBUG - Walker has 52 remaining bytes.
        fvw.feat.feature 1.feature - DEBUG - Walker has 40 remaining bytes.
        fvw.feat.feature 1.feature.settings - DEBUG - Walker has 16 remaining bytes.
        fvw.feat.feature 3.feature - DEBUG - Walker has 28 remaining bytes.
        fvw.feat.feature 3.feature.settings - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.feat - DEBUG - Walker has 1 remaining bytes.
        fvw.feat - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('feat')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x00010000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00010000 but got 0x%08X instead."))
            
            return None
        
        count, rsrv1, rsrv2 = w.unpack("2HL")
        
        if rsrv1 or rsrv2:
            logger.warning((
              'V0808',
              (),
              "One or both of the zero-reserved values in the 'feat' "
              "header is not zero."))
        
        r = cls()
        fvw = feature.Feature.fromvalidatedwalker
        
        while count:
            if w.length() < 2:
                logger.error((
                  'V0809',
                  (),
                  "The feature name array is missing or incomplete."))
                
                return None
            
            index = w.unpack("H", advance=False)
            
            obj = fvw(
              w,
              logger = logger.getChild("feature %d" % (index,)),
              **kwArgs)
            
            if obj is None:
                return None
            
            r[index] = obj
            count -= 1
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Feat from the specified walker.
        
        >>> fb = Feat.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'feat' version: 0x%08X" % (version,))
        
        count = w.unpack("H6x")
        r = cls()
        fw = feature.Feature.fromwalker
        
        while count:
            count -= 1
            index = w.unpack("H", advance=False)
            r[index] = fw(w, **kwArgs)
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _fv = feature._testingValues
    
    def _fakeEditor():
        from fontio3.name import name
        
        _fakeNameTable = {
            (1, 0, 0, 303): "Required Ligatures On",
            (1, 0, 0, 304): "Common Ligatures On",
            (1, 0, 0, 306): "Regular",
            (1, 0, 0, 307): "Small Caps",
            (1, 0, 0, 308): "Ligatures",
            (1, 0, 0, 309): "Lettercase"}
        
        e = utilities.fakeEditor(0x1000)
        e.name = name.Name(_fakeNameTable)
        return e
    
    _testingValues = (
        Feat(),
        Feat({1: _fv[1], 3: _fv[2]}))
    
    del _fv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
