#
# record_v1.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Single glyph information for a version 1 'MTap' table.
"""

# System imports
import functools
import operator

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.MTap import glyphclass_v1

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the data for a single glyph in a version 1 'MTap'
    table. These are simple objects with the following attributes:
    
        bottom0Index
        bottom1Index
        glyphClass
        top0Index
        top1Index
    
    >>> _testingValues[1].pprint()
    Glyph class: Component (4)
    Top 0 point index: 12
    Bottom 0 point index: 9
    
    >>> _testingValues[2].pprint()
    Glyph class: Mark (3)
    Top 0 point index: 5
    Top 1 point index: 6
    Bottom 0 point index: 7
    Bottom 1 point index: 8
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        glyphClass = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphclass_v1.GlyphClass,
            attr_label = "Glyph class",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(str(x), label=label)),
            attr_showonlyiftrue = True),
        
        top0Index = dict(
            attr_label = "Top 0 point index",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        top1Index = dict(
            attr_label = "Top 1 point index",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        bottom0Index = dict(
            attr_label = "Bottom 0 point index",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None)),
        
        bottom1Index = dict(
            attr_label = "Bottom 1 point index",
            attr_renumberpointsdirect = True,
            attr_showonlyiffunc = functools.partial(operator.is_not, None)))
    
    attrSorted = (
      'glyphClass',
      'top0Index',
      'top1Index',
      'bottom0Index',
      'bottom1Index')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Record object to the specified
        LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[1].binaryString())
               0 | 0004 000C FFFF 0009  FFFF                |..........      |
        
        >>> h(_testingValues[2].binaryString())
               0 | 0003 0005 0006 0007  0008                |..........      |
        """
        
        w.add("B", 0)
        self.glyphClass.buildBinary(w, **kwArgs)
        
        v = [
          self.top0Index,
          self.top1Index,
          self.bottom0Index,
          self.bottom1Index]
        
        w.addGroup("H", ((0xFFFF if n is None else n) for n in v))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker.
        
        >>> fb = Record.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == fb(_testingValues[2].binaryString())
        True
        """
        
        w.skip(1)
        gc = glyphclass_v1.GlyphClass.fromwalker(w, **kwArgs)
        v = [(None if n == 0xFFFF else n) for n in w.group("H", 4)]
        return cls(*([gc] + v))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    GC = glyphclass_v1.GlyphClass
    
    _testingValues = (
        Record(),
        Record(GC(4), 12, None, 9, None),
        Record(GC(3), 5, 6, 7, 8))
    
    del GC

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
