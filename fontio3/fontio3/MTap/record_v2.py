#
# record_v2.py
#
# Copyright © 2010, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Single glyph information for a version 2 'MTap' table.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.MTap import directionclass_v2, glyphclass_v1

# -----------------------------------------------------------------------------

#
# Classes
#

class Record(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing the data for a single glyph in a version 2 'MTap'
    table. These are simple objects with the following attributes:
    
        anchorData
        caretData
        connectionData
        direction
        glyphClass
        ligComponentCount
    
    >>> _testingValues[1].pprint()
    Direction class: Right to Left (3)
    Glyph class: Base/Simple (1)
    Anchor data:
      AnchorTuple 0:
        Anchor 0:
          Anchor type: 1
          Point index: 69
          X-coordinate: -16
          Y-coordinate: 5
        Anchor 1:
          Anchor type: 1
          Point index: 2
          X-coordinate: 12
          Y-coordinate: -30
        Anchor 2:
          Anchor type: 3
          Point index: 35
          X-coordinate: 250
          Y-coordinate: 50
        Anchor 3:
          Anchor type: 1
          Point index: 14
          X-coordinate: 19
          Y-coordinate: 18
        Anchor 4:
          Anchor type: 4
          Point index: 68
          X-coordinate: -55
          Y-coordinate: -44
        Anchor 5:
          Anchor type: 6
          Point index: 0
          X-coordinate: 12
          Y-coordinate: 9
        Anchor 6:
          Anchor type: 2
          Point index: 19
          X-coordinate: 0
          Y-coordinate: -97
        Anchor 7:
          Anchor type: 11
          Point index: 39
          X-coordinate: -28
          Y-coordinate: 36
        Anchor 8:
          Anchor type: 1
          Point index: 60
          X-coordinate: 170
          Y-coordinate: 266
        Anchor 9:
          Anchor type: 2
          Point index: 24
          X-coordinate: 900
          Y-coordinate: -450
    Connection data:
      Horizontal entry:
        Connection type: True
        Point index: 69
        X-coordinate: -16
        Y-coordinate: 5
      Horizontal exit:
        Connection type: False
        Point index: 12
        X-coordinate: 30
        Y-coordinate: -30
      Vertical entry:
        Connection type: True
        Point index: 4
        X-coordinate: 0
        Y-coordinate: -90
      Vertical exit:
        Connection type: False
        Point index: (no data)
        X-coordinate: -100
        Y-coordinate: 100
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        direction = dict(
            attr_followsprotocol = True,
            attr_initfunc = directionclass_v2.DirectionClass,
            attr_label = "Direction class",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(str(x), label=label)),
            attr_showonlyiftrue = True),
        
        glyphClass = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphclass_v1.GlyphClass,
            attr_label = "Glyph class",
            attr_pprintfunc = (
              lambda p, x, label, **k:
              p.simple(str(x), label=label)),
            attr_showonlyiftrue = True),
        
        ligComponentCount = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Ligature component count",
            attr_showonlyiftrue = True),
        
        anchorData = dict(
            attr_followsprotocol = True,  # a MTad.anchorrecord.AnchorRecord
            attr_label = "Anchor data"),
        
        connectionData = dict(
            attr_followsprotocol = True,  # a MTcc.record.Record
            attr_label = "Connection data"),
        
        caretData = dict(
            attr_label = "Caret data",
            attr_showonlyiftrue = True))
    
    attrSorted = (
      'direction',
      'glyphClass',
      'ligComponentCount',
      'anchorData',
      'connectionData',
      'caretData')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Record object to the specified
        LinkedWriter. The following keyword arguments are required:
        
            adMap       A dict mapping immutable versions of the anchorData
                        objects to their indices in the tuple.
        
            ccMap       A dict mapping immutable versions of the connectionData
                        objects to their indices in the tuple.
        
        >>> obj = _testingValues[1]
        >>> adMap = {obj.anchorData.asImmutable(): 1}
        >>> ccMap = {obj.connectionData.asImmutable(): 0}
        >>> d = {'adMap': adMap, 'ccMap': ccMap}
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | 0301 0000 0001 0000  FFFF                |..........      |
        """
        
        self.direction.buildBinary(w, **kwArgs)
        self.glyphClass.buildBinary(w, **kwArgs)
        w.add("H", self.ligComponentCount)
        
        if self.anchorData is not None:
            w.add("H", kwArgs['adMap'][self.anchorData.asImmutable()])
        else:
            w.add("H", 0xFFFF)
        
        if self.connectionData is not None:
            w.add("H", kwArgs['ccMap'][self.connectionData.asImmutable()])
        else:
            w.add("H", 0xFFFF)
        
        w.add("H", 0xFFFF)  # caret index; not currently used
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Record object from the specified walker. There is
        one required keyword argument:
        
            editor      An Editor-class object, used to obtain the MTad, MTcc,
                        and MTca objects (indices into which are part of this
                        Record).
        
        >>> obj = _testingValues[1]
        >>> adMap = {obj.anchorData.asImmutable(): 0}
        >>> ccMap = {obj.connectionData.asImmutable(): 0}
        >>> d = {'adMap': adMap, 'ccMap': ccMap}
        >>> class Ed(object): pass
        >>> e = Ed()
        >>> e.MTad = [obj.anchorData]
        >>> e.MTcc = [obj.connectionData]
        >>> obj == Record.frombytes(obj.binaryString(**d), editor=e)
        True
        """
        
        dc = directionclass_v2.DirectionClass.fromwalker(w, **kwArgs)
        gc = glyphclass_v1.GlyphClass.fromwalker(w, **kwArgs)
        ligCount, adIndex, ccIndex, caIndex = w.unpack("4H")
        ed = kwArgs.get('editor', None)
        ad = (None if adIndex == 0xFFFF else ed.MTad[adIndex])
        cc = (None if ccIndex == 0xFFFF else ed.MTcc[ccIndex])
        ca = (None if caIndex == 0xFFFF else ed.MTca[caIndex])
        return cls(dc, gc, ligCount, ad, cc, ca)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.MTad import MTad
    from fontio3.MTcc import MTcc
    
    _vAD = MTad._testingValues
    _vCC = MTcc._testingValues
    
    _testingValues = (
        Record(),
        
        Record(
          directionclass_v2.DirectionClass(3),
          glyphclass_v1.GlyphClass(1),
          0,
          _vAD[1][0],
          _vCC[1][0],
          None),
        
        Record(
          directionclass_v2.DirectionClass(1),
          glyphclass_v1.GlyphClass(2),
          0,
          _vAD[1][1],
          None,
          None))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
