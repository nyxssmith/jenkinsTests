#
# positions_point.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the control-point format of 'bsln' baseline data.
"""

# System imports
import logging

# Other imports
from fontio3.bsln import baselinekinds
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprintFunc(p, seq, **k):
    STRINGS = baselinekinds.STRINGS
    
    for i, n in enumerate(seq):
        if i in STRINGS and n is not None:
            p.simple("Point %d" % (n,), label=STRINGS[i])

def _validate(obj, **kwArgs):
    okSet = set(baselinekinds.STRINGS)
    logger = kwArgs.pop('logger')
    r = True
    
    unexpected = [
      i
      for i, n in enumerate(obj)
      if (n is not None) and (i not in okSet)]
    
    if unexpected:
        logger.warning((
          'V0811',
          (unexpected,),
          "The following baseline kinds had points specified, but are not "
          "defined in this version of the 'bsln' table: %s"))
    
    for i in okSet:
        n = obj[i]
        
        if n is not None:
            if not valassist.isPointIndex(
              glyphIndex = obj.controlGlyph,
              logger = logger.getChild("kind %d" % (i,))):
              
                r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Positions_Point(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    Roman: Point 6
    Ideographic (centered): Point 2
    Ideographic (low): Point 19
    Hanging: Point 4
    Mathematical: Point 14
    Control glyph: xyz33
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_renumberpointsdirect = True,
        seq_fixedlength = 32,
        seq_pprintfunc = _pprintFunc,
        seq_validatefunc = _validate)
    
    attrSpec = dict(
        controlGlyph = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Control glyph",
            attr_renumberdirect = True,
            attr_usenamerforstr = True))
    
    isDistance = False
    
    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Positions_Point object from the specified
        walker, doing source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("positions_point")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 66:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        cg = w.unpack("H")
        v = [(None if n == 0xFFFF else n) for n in w.group("H", 32)]
        return cls(v, controlGlyph=cg)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Positions_Point object from the data in
        the specified walker.
        
        >>> t = _testingValues[0]
        >>> t == Positions_Point.frombytes(t.binaryString())
        True
        """
        
        cg = w.unpack("H")
        v = [(None if n == 0xFFFF else n) for n in w.group("H", 32)]
        return cls(v, controlGlyph=cg)
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Positions_Point object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0020 0006 0002 0013  0004 000E FFFF FFFF |. ..............|
              10 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              20 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              30 | FFFF FFFF FFFF FFFF  FFFF FFFF FFFF FFFF |................|
              40 | FFFF                                     |..              |
        """
        
        v = [(n if n is not None else 0xFFFF) for n in self]
        w.add("H", self.controlGlyph)
        w.addGroup("H", v)
    
    def pointsRenumbered(self, mapData, **kwArgs):
        """
        We override pointsRenumbered() in order to make sure the controlGlyph
        gets passed in as the glyphIndex to check against.
        
        >>> md = {32: {2: 100, 19: 101}}
        >>> nm = namer.testingNamer()
        >>> _testingValues[0].pointsRenumbered(md).pprint(namer=nm)
        Roman: Point 6
        Ideographic (centered): Point 100
        Ideographic (low): Point 101
        Hanging: Point 4
        Mathematical: Point 14
        Control glyph: xyz33
        """
        
        kwArgs.pop('glyphIndex', None)  # get rid of it (if it's there)
        
        return seqmeta.M_pointsRenumbered(
          self,
          mapData,
          glyphIndex = self.controlGlyph,
          **kwArgs)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        Positions_Point([6, 2, 19, 4, 14] + ([None] * 27), controlGlyph=32),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
