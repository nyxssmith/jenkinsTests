#
# avar.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'avar' table, used in TrueType variations fonts.
"""

# Other imports
from fontio3 import utilities
from fontio3.avar import axisdict
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Avar(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing 'avar' tables. These are dicts mapping axis tags to
    AxisDict objects. There is a single attribute with axisOrder.
    
    >>> AD = axisdict.AxisDict
    >>> ad1 = AD({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
    >>> ad2 = AD({-1.0: -1.0, -0.75: -0.25, 0.0: 0.0, 0.5: 0.75, 1.0: 1.0})
    >>> ao = ('wght', 'wdth')
    >>> obj = Avar({'wght': ad1, 'wdth': ad2}, axisOrder=ao)
    >>> obj.pprint()
    'wdth':
      -1.0: -1.0
      -0.75: -0.25
      0.0: 0.0
      0.5: 0.75
      1.0: 1.0
    'wght':
      -1.0: -1.0
      0.0: 0.0
      0.5: 0.25
      1.0: 1.0
    axisOrder: ('wght', 'wdth')
    """
    
    mapSpec = dict(
        item_followsprotocol = True)
    
    attrSpec = dict(
        axisOrder = dict())
    
    VERSION = 0x10000
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Avar object to the specified writer.
        
        >>> AD = axisdict.AxisDict
        >>> ad1 = AD({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> ad2 = AD({-1.0: -1.0, -0.75: -0.25, 0.0: 0.0, 0.5: 0.75, 1.0: 1.0})
        >>> ao = ('wght', 'wdth')
        >>> obj = Avar({'wght': ad1, 'wdth': ad2}, axisOrder=ao)
        >>> utilities.hexdump(obj.binaryString())
               0 | 0001 0000 0000 0002  0004 C000 C000 0000 |................|
              10 | 0000 2000 1000 4000  4000 0005 C000 C000 |.. ...@.@.......|
              20 | D000 F000 0000 0000  2000 3000 4000 4000 |........ .0.@.@.|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("LHH", self.VERSION, 0, len(self))
        
        for key in self.axisOrder:
            self[key].buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Avar object from the data in the specified
        walker, doing validation. Caller must provide either an 'axisOrder' or
        an 'editor' keyword argument.
        
        >>> logger = utilities.makeDoctestLogger('fvw')
        >>> AD = axisdict.AxisDict
        >>> ad1 = AD({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> ad2 = AD({-1.0: -1.0, -0.75: -0.25, 0.0: 0.0, 0.5: 0.75, 1.0: 1.0})
        >>> ao = ('wght', 'wdth')
        >>> obj = Avar({'wght': ad1, 'wdth': ad2}, axisOrder=ao)
        >>> bs = obj.binaryString()
        >>> obj2 = Avar.fromvalidatedbytes(bs, logger=logger, axisOrder=ao)
        fvw.axisdict - DEBUG - Walker has 48 remaining bytes.
        fvw.axisdict.wght.axisdict - DEBUG - Walker has 40 remaining bytes.
        fvw.axisdict.wdth.axisdict - DEBUG - Walker has 22 remaining bytes.
        >>> obj == obj2
        True
        >>> bs = utilities.fromhex("0001 0000 0005 0009 C000 C000 0000 0000")
        >>> obj3 = Avar.fromvalidatedbytes(bs, logger=logger, axisOrder=ao)
        fvw.axisdict - DEBUG - Walker has 16 remaining bytes.
        fvw.axisdict - ERROR - Reserved field is 0x0005; expected 0.
        fvw.axisdict - ERROR - The axisCount 9 does not match axisCount 2 from the 'fvar' table.
        fvw.axisdict.wght.axisdict - DEBUG - Walker has 8 remaining bytes.
        fvw.axisdict.wght.axisdict - ERROR - Insufficient bytes.
        fvw.axisdict.wdth.axisdict - DEBUG - Walker has 6 remaining bytes.
        fvw.axisdict.wdth.axisdict - ERROR - Insufficient bytes.
        >>> obj4 = Avar.fromvalidatedbytes(b'ABC', logger=logger)
        fvw.axisdict - DEBUG - Walker has 3 remaining bytes.
        fvw.axisdict - ERROR - Insufficient bytes.
        >>> bs = utilities.fromhex("0123 4567 0000 FFFF")
        >>> obj5 = Avar.fromvalidatedbytes(bs, logger=logger, axisOrder=ao)
        fvw.axisdict - DEBUG - Walker has 8 remaining bytes.
        fvw.axisdict - ERROR - Was expecting 'avar' version 0x00010000 but got 0x01234567 instead.
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('axisdict')
        else:
            logger = utilities.makeDoctestLogger('axisdict')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        assert ('axisOrder' in kwArgs) or ('editor' in kwArgs)
        
        if 'axisOrder' in kwArgs:
            ao = tuple(kwArgs['axisOrder'])
        else:
            ao = tuple(kwArgs['editor'].fvar.axisOrder)
        
        vers, reserved, count = w.unpack("LHH")
        
        if vers != cls.VERSION:
            logger.error((
              'Vxxxx',
              (cls.VERSION, vers),
              "Was expecting 'avar' version 0x%08X but got "
              "0x%08X instead."))
            
            return None

        if reserved != 0:
            logger.error((
              'Vxxxx',
              (reserved,),
              "Reserved field is 0x%04X; expected 0."))

        if count != len(ao):
            logger.error((
              'Vxxxx',
              (count, len(ao)),
              "The axisCount %d does not match axisCount %d from the 'fvar' table."))


        r = cls({}, axisOrder=ao)
        fvw = axisdict.AxisDict.fromvalidatedwalker
        
        for axisTag in ao:
            subLogger = logger.getChild(axisTag)
            r[axisTag] = fvw(w, logger=subLogger, **kwArgs)
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Avar object from the data in the specified
        walker. Caller must provide either an 'axisOrder' or an 'editor'
        keyword argument.
        
        >>> AD = axisdict.AxisDict
        >>> ad1 = AD({-1.0: -1.0, 0.0: 0.0, 0.5: 0.25, 1.0: 1.0})
        >>> ad2 = AD({-1.0: -1.0, -0.75: -0.25, 0.0: 0.0, 0.5: 0.75, 1.0: 1.0})
        >>> ao = ('wght', 'wdth')
        >>> obj = Avar({'wght': ad1, 'wdth': ad2}, axisOrder=ao)
        >>> bs = obj.binaryString()
        >>> obj2 = Avar.frombytes(bs, axisOrder=ao)
        >>> obj == obj2
        True
        >>> bs = utilities.fromhex("DEAD BEEF FFFF 0000")
        >>> obj3 = Avar.frombytes(bs, axisOrder=ao)
        Traceback (most recent call last):
            ...
        ValueError: Unknown 'avar' version!
        """
        
        assert ('axisOrder' in kwArgs) or ('editor' in kwArgs)
        
        if 'axisOrder' in kwArgs:
            ao = tuple(kwArgs['axisOrder'])
        else:
            ao = tuple(kwArgs['editor'].fvar.axisOrder)
        
        vers, reserved, count = w.unpack("LHH")
        
        if vers != cls.VERSION:
            raise ValueError("Unknown 'avar' version!")
        
        r = cls({}, axisOrder=ao)
        fw = axisdict.AxisDict.fromwalker
        
        for axisTag in ao:
            r[axisTag] = fw(w, **kwArgs)
        
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
