#
# rgba.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for RGBA color objects of MTcl tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    """
    This doesn't do anything (yet) and is not linked in to seqSpec.
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

class RGBA(object, metaclass=simplemeta.FontDataMetaclass):
    """
    An RGBA is a simple object representing combinations of Red, Green, Blue,
    Alpha values.
    
    >>> _testingValues[1].pprint()
    Red value: 0
    Green value: 0
    Blue value: 127
    Alpha value: 0
    """
    
    attrSpec = dict(
        red = dict(attr_label = "Red value", attr_initfunc = lambda: 0),
        green = dict(attr_label = "Green value", attr_initfunc = lambda: 0),
        blue = dict(attr_label = "Blue value", attr_initfunc = lambda: 0),
        alpha = dict(attr_label = "Alpha value", attr_initfunc = lambda: 0),
        )
        
    attrSorted = ('red', 'green', 'blue', 'alpha')
        
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the RGBA object to the specified LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[1].binaryString())
               0 | 0000 7F00                                |....            |
        """
        
        w.add("4B", self.red, self.green, self.blue, self.alpha)
        
    def asrgb(self, **kwArgs):
        """
        Returns the RGBA object as a (R,G,B) tuple.
        
        >>> _testingValues[1].asrgb()
        (0, 0, 127)
        """
        
        return (self.red, self.green, self.blue)
        
    def ashtml(self, **kwArgs):
        """
        Returns the RGBA object as a #RRGGBB string, suitable for use in HTML/CSS.
        
        >>> _testingValues[1].ashtml()
        '#00007F'
        """
        
        return "#%02X%02X%02X" % (self.red, self.green, self.blue)

    @classmethod
    def fromhtml(cls, s, **kwArgs):
        """
        Creates and returns a new RGBA object from string 's', an HTML/CSS color
        in the form #RRGGBB.

        >>> RGBA.fromhtml("#FF0032").pprint()
        Red value: 255
        Green value: 0
        Blue value: 50
        Alpha value: 0

        Always returns an RGBA, even with crud input:
        >>> RGBA.fromhtml("foobar!").pprint()
        Red value: 0
        Green value: 0
        Blue value: 0
        Alpha value: 0
        """
        
        if len(s) == 7:
            try:
                c = RGBA(
                  red = int(s[1:3], 16),
                  green = int(s[3:5], 16),
                  blue = int(s[5:7], 16),
                  alpha = 0)
            
            except ValueError:
                c = cls()
        
        else:
            c = cls()
            
        return c        

    @classmethod
    def fromnumber(cls, n, **kwArgs):
        """
        Creates and returns a new RGBA object from the specified number (32-bit int).
        
        >>> RGBA.fromnumber(0xAABBCCDD).pprint()
        Red value: 170
        Green value: 187
        Blue value: 204
        Alpha value: 221
        """
        
        r, g, b, a = (n >> i & 0xFF for i in (24, 16, 8, 0))
        return cls(red = r, green = g, blue = b, alpha = a)
        
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new RGBA object from the specified walker, doing
        source validation.
        >>> l = utilities.makeDoctestLogger("test")
        >>> b = utilities.fromhex("FF 7F 80")
        >>> w = walker.StringWalker(b)
        >>> c = RGBA.fromvalidatedwalker(w, logger=l)
        test.RGBA - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("RGBA")
        
        if w.length() < 4:
            logger.error((
              'V0004',
              (),
              "Insufficient bytes."))

            return None
            
        v = w.group("B", 4)
        return cls(red=v[0], green=v[1], blue=v[2], alpha=v[3])

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new RGBA object from the specified walker.
        
        >>> b = utilities.fromhex("7F 30 92 AF")
        >>> w = walker.StringWalker(b)
        >>> c = RGBA.fromwalker(w)
        >>> c.pprint()
        Red value: 127
        Green value: 48
        Blue value: 146
        Alpha value: 175
        """
        
        v = w.group("B", 4)
        return cls(red=v[0], green=v[1], blue=v[2], alpha=v[3])

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
      RGBA(),
      RGBA(blue=0x7f),
      )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

