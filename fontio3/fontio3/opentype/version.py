#
# version.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for uniform version numbers, with a major and a minor UInt16 piece.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Version(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing versions, used in OpenType 1.8 and beyond. These are
    simple collections of two attributes:
    
        major   The major version number.
        minor   The minor version number.
    
    Note these are always UInt16 values. This removes the old ambiguity about
    how 0x00018000, for instance, is intended to be read: 1.5? 1.8? Something
    else?
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        major = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Major version",
            attr_validatefunc = valassist.isFormat_H),
        
        minor = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minor version",
            attr_validatefunc = valassist.isFormat_H))
    
    attrSorted = ('major', 'minor')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Version object to the specified writer.
        
        >>> obj = Version(major=2, minor=1)
        >>> utilities.hexdump(obj.binaryString())
               0 | 0002 0001                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2H", self.major, self.minor)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Version object from the specified walker,
        doing validation.
        
        >>> bs = bytes.fromhex("00020001")
        >>> obj = Version.fromvalidatedbytes(bs)
        version - DEBUG - Walker has 4 remaining bytes.
        
        >>> obj.pprint()
        Major version: 2
        Minor version: 1
        
        >>> Version.fromvalidatedbytes(bs[:-1])
        version - DEBUG - Walker has 3 remaining bytes.
        version - ERROR - Insufficient bytes.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('version')
        else:
            logger = utilities.makeDoctestLogger('version')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        t = w.group("H", 2)
        return cls(major=t[0], minor=t[1])
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Version object from the specified walker.
        
        >>> bs = bytes.fromhex("00020001")
        >>> obj = Version.frombytes(bs)
        >>> obj.pprint()
        Major version: 2
        Minor version: 1
        """
        
        t = w.group("H", 2)
        return cls(major=t[0], minor=t[1])

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
