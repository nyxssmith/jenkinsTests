#
# feature.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single AAT features in a 'feat' table.
"""

# System imports
import logging

# Other imports
from fontio3.feat import settings
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Feature(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single features in a 'feat' table. These are simple
    collections of attributes:
        settings        A settings.Settings object.
        
        default         The default setting value, or None.
        
        nameIndex       Index in the 'name' table of the name for this feature.
        
        isExclusive     True if the settings are mutually exclusive; False
                        otherwise.
    
    >>> _testingValues[0].pprint(editor=_fakeEditor())
    Feature name index: None
    Settings are mutually exclusive: True
    
    >>> _testingValues[1].pprint(editor=_fakeEditor())
    Settings:
      0: 303 ('Required Ligatures On')
      2: 304 ('Common Ligatures On')
    Default value: 0
    Feature name index: 308 ('Ligatures')
    Settings are mutually exclusive: False
    
    >>> _testingValues[2].pprint(editor=_fakeEditor())
    Settings:
      0: 306 ('Regular')
      1: 307 ('Small Caps')
    Default value: 1
    Feature name index: 309 ('Lettercase')
    Settings are mutually exclusive: True
    
    >>> e = _fakeEditor()
    >>> logger = utilities.makeDoctestLogger("val")
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    val.nameIndex - ERROR - Name table index 340 not present in 'name' table.
    val.settings.[0] - ERROR - Name table index 12 not present in 'name' table.
    val.settings.[1] - ERROR - The name table index 70000 does not fit in 16 bits.
    val.settings.[2] - ERROR - The name table index 'fred' is not a real number.
    val.settings.[5] - ERROR - Name table index 320 not present in 'name' table.
    False
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        settings = dict(
            attr_followsprotocol = True,
            attr_initfunc = settings.Settings,
            attr_label = "Settings",
            attr_showonlyiftrue = True),
        
        default = dict(
            attr_label = "Default value",
            attr_showonlyiffunc = (lambda obj: obj is not None)),
        
        nameIndex = dict(
            attr_label = "Feature name index",
            attr_renumbernamesdirect = True),
        
        isExclusive = dict(
            attr_initfunc = (lambda: True),
            attr_label = "Settings are mutually exclusive"))
    
    attrSorted = ('settings', 'default', 'nameIndex', 'isExclusive')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Feature to the specified LinkedWriter.
        
        >>> w = writer.LinkedWriter()
        >>> baseStake = w.stakeCurrent()
        >>> pool = {}
        >>> d = {
        ...   'baseStake': baseStake,
        ...   'settingPool': pool,
        ...   'featureIndex': 19}
        >>> _testingValues[1].buildBinary(w, **d)
        >>> stake, sett = next(iter(pool.values()))
        >>> sett.buildBinary(w, stakeValue=stake)
        >>> utilities.hexdump(w.binaryString())
               0 | 0013 0002 0000 000C  0000 0134 0000 012F |...........4.../|
              10 | 0002 0130                                |...0            |
        
        >>> w = writer.LinkedWriter()
        >>> baseStake = w.stakeCurrent()
        >>> pool.clear()
        >>> _testingValues[2].buildBinary(w, **d)
        >>> stake, sett = next(iter(pool.values()))
        >>> sett.buildBinary(w, stakeValue=stake)
        >>> utilities.hexdump(w.binaryString())
               0 | 0013 0002 0000 000C  C001 0135 0000 0132 |...........5...2|
              10 | 0001 0133                                |...3            |
        """
        
        settingPool = kwArgs.get('settingPool', {})
        w.add("2H", kwArgs['featureIndex'], len(self.settings))
        immut = self.settings.asImmutable()  # immut -> (stake, SettingsObj)
        
        if immut not in settingPool:
            settingPool[immut] = (w.getNewStake(), self.settings)
        
        w.addUnresolvedOffset("L", kwArgs['baseStake'], settingPool[immut][0])
        
        if self.default:
            if self.default not in self.settings:
                raise ValueError("Specified default not a valid setting!")
            
            dflt = sorted(self.settings).index(self.default)
        
        else:
            dflt = 0
        
        flags = (0x8000 if self.isExclusive else 0)
        
        if dflt:
            flags |= (0x4000 + dflt)
        
        w.add("2H", flags, self.nameIndex)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Feature object from the specified walker,
        doing source validation. This method skips the first two bytes of data
        (the feature type value), since the top-level Feat object will have
        already used it.
        
        >>> w = writer.LinkedWriter()
        >>> baseStake = w.stakeCurrent()
        >>> pool = {}
        >>> d = {
        ...   'baseStake': baseStake,
        ...   'settingPool': pool,
        ...   'featureIndex': 1}
        >>> _testingValues[1].buildBinary(w, **d)
        >>> stake, sett = next(iter(pool.values()))
        >>> sett.buildBinary(w, stakeValue=stake)
        >>> s = w.binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Feature.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.feature - DEBUG - Walker has 20 remaining bytes.
        fvw.feature.settings - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:2], logger=logger)
        fvw.feature - DEBUG - Walker has 2 remaining bytes.
        fvw.feature - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-2], logger=logger)
        fvw.feature - DEBUG - Walker has 18 remaining bytes.
        fvw.feature.settings - DEBUG - Walker has 6 remaining bytes.
        fvw.feature.settings - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("feature")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 12:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count, offset, flags, nameIndex = w.unpack("2xHL2H")
        
        if not count:
            logger.error((
              'V0805',
              (),
              "The setting count is zero for this feature."))
            
            return None
        
        if flags & 0x3F00:
            logger.error((
              'V0806',
              (),
              "One or more reserved bits in the feature flags are set."))
            
            return None
        
        s = settings.Settings.fromvalidatedwalker(
          w.subWalker(offset),
          count = count,
          logger = logger)
        
        if s is None:
            return None
        
        excl = bool(flags & 0x8000)
        dflt = min(s)
        
        if (flags & 0xC000) == 0xC000:
            dflt = sorted(s)[flags & 0xFF]
        
        elif flags & 0xFF:
            logger.warning((
              'V0807',
              (flags,),
              "The flags word 0x%04X has a nonzero value in the low-order "
              "eight bits, but the 0xC000 bits are not set. The low-order "
              "bits will be ignored."))
        
        return cls(s, dflt, nameIndex, excl)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Feature object from the specified walker. This
        method skips the first two bytes of data (the feature type value),
        since the top-level Feat object will have already used it.
        
        >>> w = writer.LinkedWriter()
        >>> baseStake = w.stakeCurrent()
        >>> pool = {}
        >>> d = {
        ...   'baseStake': baseStake,
        ...   'settingPool': pool,
        ...   'featureIndex': 19}
        >>> _testingValues[1].buildBinary(w, **d)
        >>> stake, sett = next(iter(pool.values()))
        >>> sett.buildBinary(w, stakeValue=stake)
        >>> _testingValues[1] == Feature.frombytes(w.binaryString())
        True
        
        >>> w = writer.LinkedWriter()
        >>> baseStake = w.stakeCurrent()
        >>> pool = {}
        >>> d = {
        ...   'baseStake': baseStake,
        ...   'settingPool': pool,
        ...   'featureIndex': 19}
        >>> _testingValues[2].buildBinary(w, **d)
        >>> stake, sett = next(iter(pool.values()))
        >>> sett.buildBinary(w, stakeValue=stake)
        >>> _testingValues[2] == Feature.frombytes(w.binaryString())
        True
        """
        
        count, offset, flags, nameIndex = w.unpack("2xHL2H")
        s = settings.Settings.fromwalker(w.subWalker(offset), count=count)
        excl = bool(flags & 0x8000)
        dflt = min(s)
        
        if (flags & 0xC000) == 0xC000:
            dflt = sorted(s)[flags & 0xFF]
        
        return cls(s, dflt, nameIndex, excl)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer
    
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
    
    _sv = settings._testingValues
    
    _testingValues = (
        Feature(),
        Feature(_sv[1], 0, 308, False),
        Feature(_sv[2], 1, 309, True),
        
        # bad values start here
        
        Feature(_sv[3], 1, 340, True))
    
    del _sv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
