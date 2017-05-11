#
# highlighttable.py
#
# Copyright © 2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for HighlightTable objects of MTcl tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.MTcl import rgba

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    """
    This doesn't do anything (yet) and is not linked in to mapSpec.
    """
    
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class HighlightTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    HighlightTables map glyph indices to RGBA objects.

    >>> _testingValues[1].pprint()
    5:
      Red value: 255
      Green value: 0
      Blue value: 0
      Alpha value: 0
    9:
      Red value: 0
      Green value: 255
      Blue value: 0
      Alpha value: 0
    """
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_followsprotocol = True,
        item_subloggernamefunc = (lambda n: "glyph %d" % (n,)),
        item_validatecode_toolargeglyph = 'Vxxxx')
        
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MTcl object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0002 0005 FF00 0000  0009 00FF 0000      |..............  |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        if self:
            v = sorted(self)
            w.add("H", len(v))
            
            for g in sorted(self):
                w.add("H", g)
                self[g].buildBinary(w, **kwArgs)
        
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new HighlightTable object from the specified
        walker, doing source validation.
        
        >>> l = utilities.makeDoctestLogger("test")

        >>> h = "00 FF 00 FF 7F 7F 00 00 00 01 FF FF 00 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = HighlightTable.fromvalidatedwalker(w, logger=l)
        test.HighlightTable - DEBUG - Walker has 14 remaining bytes.
        test.HighlightTable - ERROR - Subtable length 12 is not valid for count 255.

        >>> h = "00 03 00 FF 7F 7F 00 00 00 01 FF FF 00 00 00 FF 80 80 80 00"
        >>> s = utilities.fromhex(h)
        >>> w = walker.StringWalker(s)
        >>> t = HighlightTable.fromvalidatedwalker(w, logger=l)
        test.HighlightTable - DEBUG - Walker has 20 remaining bytes.
        test.HighlightTable - WARNING - There are duplicated entries.
        test.HighlightTable - WARNING - ColorEntry values not in sorted order by glyph index.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("HighlightTable")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        count = w.unpack("H")

        if w.length() != (count * 6):
            logger.error((
              'Vxxxx',
              (w.length(), count),
              "Subtable length %d is not valid for count %d."))
            return None
            
        cvals = w.group("HL", count)
        d = {g:rgba.RGBA.fromnumber(r) for g,r in cvals}
        
        if len(d) != len(cvals):
            logger.warning((
              'Vxxxx',
              (),
              "There are duplicated entries."))
        
        if sorted(d) != [cv[0] for cv in cvals]:
            logger.warning((
              'Vxxxx',
              (),
              "ColorEntry values not in sorted order by glyph index."))
        
        return cls(d)

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new HighlightTable object from the specified walker.
        """
        
        count = w.unpack("H")
        d = {g:rgba.RGBA.fromnumber(r) for g,r in w.group("HL", count)}
        return cls(d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import walker
    
    _testingValues = (
      HighlightTable(),
      HighlightTable({
        5:rgba.RGBA(red=255),
        9:rgba.RGBA(green=255),
        })
      )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

