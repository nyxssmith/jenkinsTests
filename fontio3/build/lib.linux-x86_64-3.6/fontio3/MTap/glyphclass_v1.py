#
# glyphclass_v1.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to glyph class values in version 1 'MTap' tables.
"""

# Other imports
from fontio3.fontdata import enummeta

# -----------------------------------------------------------------------------

#
# Classes
#

class GlyphClass(int, metaclass=enummeta.FontDataMetaclass):
    """
    Integer values representing glyph class enumerated values.
    
    >>> print(_testingValues[0])
    No class (0)
    
    >>> print(_testingValues[1])
    Base/Simple (1)
    
    >>> print(_testingValues[2])
    Ligature (2)
    """
    
    #
    # Class definition variables
    #
    
    enumSpec = dict(
        enum_annotatevalue = True,
        enum_stringsdict = {
          0: "No class",
          1: "Base/Simple",
          2: "Ligature",
          3: "Mark",
          4: "Component"})
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the GlyphClass object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 02                                       |.               |
        """
        
        w.add("B", self)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a GlyphClass object from the specified walker.
        
        >>> fb = GlyphClass.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        """
        
        return cls(w.unpack("B"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        GlyphClass(0),
        GlyphClass(1),
        GlyphClass(2),
        GlyphClass())

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
