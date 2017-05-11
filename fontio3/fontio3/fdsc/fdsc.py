#
# fdsc.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entire 'fdsc' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fdsc import nalfcode
from fontio3.fontdata import simplemeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Fdsc(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'fdsc' tables.
    
    >>> _testingValues[0].pprint()
    Weight factor: 1.0
    Width factor: 1.0
    Slant (degrees): 0.0
    Design (optical) size: 12.0
    Non-alphabetic code: Alphabetic (0)
    
    >>> _testingValues[1].pprint()
    Weight factor: 1.25
    Width factor: 1.125
    Slant (degrees): 4.75
    Design (optical) size: 13.0
    Non-alphabetic code: Dingbats (1)
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        weight = dict(
            attr_initfunc = (lambda: 1.0),
            attr_label = "Weight factor",
            attr_validatefunc = valassist.isNumber_fixed),
        
        width = dict(
            attr_initfunc = (lambda: 1.0),
            attr_label = "Width factor",
            attr_validatefunc = valassist.isNumber_fixed),
        
        slant = dict(
            attr_initfunc = (lambda: 0.0),
            attr_label = "Slant (degrees)",
            attr_validatefunc = valassist.isNumber_fixed),
        
        designSize = dict(
            attr_initfunc = (lambda: 12.0),
            attr_label = "Design (optical) size",
            attr_validatefunc = valassist.isNumber_fixed),
        
        nonAlphabeticCode = dict(
            attr_followsprotocol = True,
            attr_initfunc = nalfcode.NalfCode,
            attr_label = "Non-alphabetic code",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(str(x), label=label, **k))))
    
    attrSorted = (
      'weight',
      'width',
      'slant',
      'designSize',
      'nonAlphabeticCode')
    
    validTags = {
      b'wght': "weight",
      b'wdth': "width",
      b'slnt': "slant",
      b'opsz': "designSize",
      b'nalf': "nonAlphabeticCode"}
    
    validTagsRev = {v: k for k, v in validTags.items()}
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Fdsc object to the specified LinkedWriter.
        
        >>> obj = _testingValues[0]
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000 0000 0000                      |........        |
        
        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000 0000 0005  7767 6874 0001 4000 |........wght..@.|
              10 | 7764 7468 0001 2000  736C 6E74 0004 C000 |wdth.. .slnt....|
              20 | 6F70 737A 000D 0000  6E61 6C66 0000 0001 |opsz....nalf....|
        
        >>> obj = _testingValues[2]
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000 0000 0001  7764 7468 0001 8000 |........wdth....|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)  # version
        ref = type(self)()  # a reference, having default initial values
        refd = ref.__dict__
        lengthStake = w.addDeferredValue("L")
        count = 0
        d = self.__dict__
        
        for key in self.getSortedAttrNames():
            if d[key] != refd[key]:
                count += 1
                w.add("4s", self.validTagsRev[key])
                
                if key == "nonAlphabeticCode":
                    w.add("L", d[key])
                else:
                    w.add("L", int(round(d[key] * 65536.0)))
        
        w.setDeferredValue(lengthStake, "L", count)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Fdsc object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("fdsc")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x10000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00010000, but got 0x%08X instead."))
            
            return None
        
        r = cls()
        rd = r.__dict__
        vt = cls.validTags
        descriptorCount = w.unpack("L")
        
        if not descriptorCount:
            logger.warning((
              'V0813',
              (),
              "The descriptorCount is zero, which makes the table useless."))
            
            return r
        
        if w.length() < 8 * descriptorCount:
            logger.error((
              'V0814',
              (),
              "The descriptor table is missing or only partially present."))
            
            return None
        
        okToReturn = True
        
        for tag, value in w.group("4sl", descriptorCount):
            if tag not in vt:
                logger.error((
                  'V0815',
                  (ascii(tag)[2:-1],),
                  "The descriptor tag '%s' is not recognized."))
                
                okToReturn = False
                continue
            
            if tag == b'nalf':
                r.nonAlphabeticCode = nalfcode.NalfCode(value)
            else:
                rd[vt[tag]] = value / 65536
        
        return (r if okToReturn else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Fdsc object from the specified walker.
        
        >>> obj = _testingValues[0]
        >>> obj == Fdsc.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[1]
        >>> obj == Fdsc.frombytes(obj.binaryString())
        True
        
        >>> obj = _testingValues[2]
        >>> obj == Fdsc.frombytes(obj.binaryString())
        True
        """
        
        version = w.unpack("L")
        
        if version != 0x10000:
            raise ValueError("Unknown 'fdsc' version: 0x%08X" % (version,))
        
        r = cls()
        rd = r.__dict__
        vt = cls.validTags
        
        for tag, value in w.group("4sl", w.unpack("L")):
            if tag not in vt:
                raise ValueError("Unknown tag %r in 'fdsc' table!" % (tag,))
            
            if tag == b'nalf':
                r.nonAlphabeticCode = nalfcode.NalfCode(value)
            else:
                rd[vt[tag]] = value / 65536
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Fdsc(),
        
        Fdsc(
          weight = 1.25,
          width = 1.125,
          slant = 4.75,
          designSize = 13.0,
          nonAlphabeticCode = nalfcode.NalfCode(1)),
        
        Fdsc(width=1.5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
