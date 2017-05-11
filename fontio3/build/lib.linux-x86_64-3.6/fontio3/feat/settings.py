#
# settings.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mapping setting values to name table indices.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Settings(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing all of the settings associated with a single feature.
    These are dicts mapping setting values to name table indices.
    
    >>> e = _fakeEditor()
    >>> _testingValues[1].pprint(editor=e)
    0: 303 ('Required Ligatures On')
    2: 304 ('Common Ligatures On')
    
    >>> _testingValues[2].pprint(editor=e)
    0: 306 ('Regular')
    1: 307 ('Small Caps')
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = _fakeEditor()
    >>> _testingValues[3].isValid(logger=logger, editor=e)
    val.[0] - ERROR - Name table index 12 not present in 'name' table.
    val.[1] - ERROR - The name table index 70000 does not fit in 16 bits.
    val.[2] - ERROR - The name table index 'fred' is not a real number.
    val.[5] - ERROR - Name table index 320 not present in 'name' table.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelpresort = True,
        item_renumbernamesdirectvalues = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Settings to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 012F 0002 0130                      |.../...0        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0000 0132 0001 0133                      |...2...3        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.addGroup("2H", ((k, self[k]) for k in sorted(self)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Settings object from the specified walker,
        doing source validation. There is one required keyword argument:
        
            count       The number of settings. This is determined from the
                        Feature object.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = Settings.fromvalidatedbytes
        >>> obj = fvb(s, count=2, logger=logger)
        fvw.settings - DEBUG - Walker has 8 remaining bytes.
        >>> obj == _testingValues[1]
        True
        
        >>> fvb(s[:-1], count=2, logger=logger)
        fvw.settings - DEBUG - Walker has 7 remaining bytes.
        fvw.settings - ERROR - Insufficient bytes.
        """
        
        count = kwArgs.pop('count')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("settings")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4 * count:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        return cls(w.group("2H", count))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Settings object from the specified walker.
        There is one required keyword argument:
        
            count       The number of settings. This is determined from the
                        Feature object.
        
        >>> for obj in _testingValues[1:3]:
        ...   print(obj == Settings.frombytes(obj.binaryString(), count=2))
        True
        True
        """
        
        return cls(w.group("2H", kwArgs['count']))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _fakeEditor():
        from fontio3.name import name
        
        _fakeNameTable = {
            (1, 0, 0, 303): "Required Ligatures On",
            (1, 0, 0, 304): "Common Ligatures On",
            (1, 0, 0, 306): "Regular",
            (1, 0, 0, 307): "Small Caps"}
        
        e = utilities.fakeEditor(0x1000)
        e.name = name.Name(_fakeNameTable)
        return e
    
    _testingValues = (
        Settings(),
        Settings({0: 303, 2: 304}),
        Settings({0: 306, 1: 307}),
        
        # bad values start here
        
        Settings({0: 12, 1: 70000, 2: "fred", 5: 320}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
