#
# MTcl.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for glyph colorization information.
"""

# System imports
import logging

# imports
from fontio3.fontdata import simplemeta
from fontio3.MTcl import highlighttable

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class MTcl(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Top-level MTcl objects. These are simple objects with 1 attribute:
 
        highlightTable  A highlight table
        
    >>> _testingValues[1].pprint()
    Highlight Table:
      5:
        Red value: 255
        Green value: 0
        Blue value: 0
        Alpha value: 0
      6:
        Red value: 0
        Green value: 255
        Blue value: 0
        Alpha value: 0
    """
    
    attrSpec = dict(
        highlightTable = dict(
            attr_followsprotocol = True,
            attr_initfunc = highlighttable.HighlightTable,
            attr_label = "Highlight Table"))
        
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTcl object to the specified LinkedWriter.
        
        >>> b = _testingValues[1].binaryString()
        >>> utilities.hexdump(b)
               0 | 0001 0000 0000 0008  0002 0005 FF00 0000 |................|
              10 | 0006 00FF 0000                           |......          |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("L", 0x10000)
        
        if self.highlightTable:
            htstake = w.getNewStake()
            w.addUnresolvedOffset("L", stakeValue, htstake)
            self.highlightTable.buildBinary(w, stakeValue=htstake, **kwArgs)
            
        else:
            w.add("L", 0)

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MTcl object from the specified walker, doing
        source validation.
        >>> l = utilities.makeDoctestLogger("test")

        >>> h = "00 01 00 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = MTcl.fromvalidatedwalker(w, logger=l)
        test.MTcl - DEBUG - Walker has 4 remaining bytes.
        test.MTcl - ERROR - Insufficient bytes.

        >>> h = "00 05 00 00 00 00 00 08 00 02 00 01 7F 7F 00 00 00 02 FF FF 00 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = MTcl.fromvalidatedwalker(w, logger=l)
        test.MTcl - DEBUG - Walker has 22 remaining bytes.
        test.MTcl - ERROR - Expected version 0x00010000, but got 0x00050000.
        
        >>> h = "00 01 00 00 00 00 00 00 00 02 00 01 7F 7F 00 00 00 02 FF FF 00 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = MTcl.fromvalidatedwalker(w, logger=l)
        test.MTcl - DEBUG - Walker has 22 remaining bytes.
        test.MTcl - ERROR - HighlightTable offset is zero but table has bytes remaining.

        >>> h = "00 01 00 00 00 00 00 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = MTcl.fromvalidatedwalker(w, logger=l)
        test.MTcl - DEBUG - Walker has 8 remaining bytes.
        test.MTcl - WARNING - No HighlightTable.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("MTcl")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
            
        version, offsetToHighlightTable = w.unpack("2L")
        
        if version != 0x10000:
            logger.error((
              'Vxxxx',
              (version,),
              "Expected version 0x00010000, but got 0x%08X."))
              
            return None
            
        if not offsetToHighlightTable:
            if w.length() > 0:
                logger.error((
                  'Vxxxx',
                  (),
                  "HighlightTable offset is zero but table has bytes remaining."))
                  
                return None

            else:
                logger.warning((
                  'Vxxxx',
                  (),
                  "No HighlightTable."))

                ht = highlighttable.HighlightTable()

        else:
            ht = highlighttable.HighlightTable.fromvalidatedwalker(
              w.subWalker(offsetToHighlightTable),
              logger = logger,
              **kwArgs)
          
        return cls(highlightTable=ht)

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MTcl object from the specified walker.
        """
        
        version, offsetToHighlightTable = w.unpack("2L")

        if offsetToHighlightTable:
            ht = highlighttable.HighlightTable.fromwalker(
              w.subWalker(offsetToHighlightTable),
              **kwArgs)
        else:
            ht = highlighttable.HighlightTable()

        return cls(highlightTable=ht)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.MTcl import rgba
    from fontio3 import utilities
    from fontio3.utilities import walker
    
    _testingValues = (
      MTcl(),
      MTcl(
        highlightTable=highlighttable.HighlightTable({
          5:rgba.RGBA.fromnumber(0xFF000000),
          6:rgba.RGBA.fromnumber(0x00FF0000)})),
      )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

