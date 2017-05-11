#
# pairvalues.py
#
# Copyright © 2007-2014, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Objects representing a pair of Value objects.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.GPOS import value

# -----------------------------------------------------------------------------

#
# Classes
#

class PairValues(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects with two attributes, first and second, either or both of which may
    be None or a Value object.
    
    >>> print(bool(PairValues()))
    False
    
    >>> _testingValues[0].pprint()
    Second adjustment:
      FUnit adjustment to origin's x-coordinate: -10
    
    >>> _testingValues[1].pprint()
    First adjustment:
      Device for vertical advance:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    
    >>> _testingValues[2].pprint()
    First adjustment:
      FUnit adjustment to origin's x-coordinate: 30
      Device for vertical advance:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
    Second adjustment:
      Device for origin's x-coordinate:
        Tweak at 12 ppem: -2
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 1
      Device for origin's y-coordinate:
        Tweak at 12 ppem: -5
        Tweak at 13 ppem: -3
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 2
        Tweak at 20 ppem: 3
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        first = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "First adjustment",
            attr_showonlyiftrue = True),
        
        second = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Second adjustment",
            attr_showonlyiftrue = True))
    
    attrSorted = ('first', 'second')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter. The following
        keyword arguments are supported:
        
            devicePool          A dict mapping device IDs to the Device
                                objects. This is optional; if not specified, a
                                local pool will be used. The devices will only
                                be actually added if devicePool is not
                                specified; if it is specified, a higher-level
                                client is responsible for this.
            
            posBase             A stake representing the base from which device
                                offsets will be computed. This is required.
            
            valueFormatFirst    The mask representing which values are to be
                                included for the second Value. This is
                                optional; if not present the getMasks() mask is
                                used instead.
            
            valueFormatSecond   The mask representing which values are to be
                                included for the second Value. This is
                                optional; if not present the getMask() mask is
                                used instead.
        
        >>> d = {
        ...   'posBase': "test stake",
        ...   'valueFormatFirst': 255,
        ...   'valueFormatSecond': 255}
        >>> w = writer.LinkedWriter()
        >>> w.stakeCurrentWithValue("test stake")
        >>> w.add("l", -1)
        >>> _testingValues[0].buildBinary(w, **d)
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF FFFF 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 FFF6 0000  0000 0000 0000 0000 |................|
              20 | 0000 0000                                |....            |
        
        >>> w.reset()
        >>> w.stakeCurrentWithValue("test stake")
        >>> w.add("l", -1)
        >>> _testingValues[1].buildBinary(w, **d)
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF FFFF 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0024 0000 0000  0000 0000 0000 0000 |...$............|
              20 | 0000 0000 000C 0012  0001 8C04           |............    |
        
        >>> w.reset()
        >>> w.stakeCurrentWithValue("test stake")
        >>> w.add("l", -1)
        >>> _testingValues[2].buildBinary(w, **d)
        >>> utilities.hexdump(w.binaryString())
               0 | FFFF FFFF 001E 0000  0000 0000 0000 0000 |................|
              10 | 0000 0030 0000 0000  0000 0000 0030 0024 |...0.........0.$|
              20 | 0000 0000 000C 0014  0002 BDF0 0020 3000 |............. 0.|
              30 | 000C 0012 0001 8C04                      |........        |
        """
        
        valueFormatFirst = kwArgs.pop('valueFormatFirst', None)
        valueFormatSecond = kwArgs.pop('valueFormatSecond', None)
        kwArgs.pop('valueFormat', None)
        
        if valueFormatFirst is None or valueFormatSecond is None:
            m1, m2 = self.getMasks()
            
            if valueFormatFirst is None:
                valueFormatFirst = m1
            
            if valueFormatSecond is None:
                valueFormatSecond = m2
                
        devicePool = kwArgs.pop('devicePool', None)
        
        if devicePool is None:
            devicePool = {}
            doLocal = True
        else:
            doLocal = False

        if valueFormatFirst:
            obj = self.first or value.Value()
            
            obj.buildBinary(
              w,
              valueFormat = valueFormatFirst,
              devicePool = devicePool,
              **kwArgs)
        
        if valueFormatSecond:
            obj = self.second or value.Value()
            
            obj.buildBinary(
              w,
              valueFormat = valueFormatSecond,
              devicePool = devicePool,
              **kwArgs)
        
        if doLocal:
            # we decorate-sort to ensure a repeatable, canonical ordering
            it = sorted(
              (sorted(obj.asImmutable()[1]), obj, stake)
              for obj, stake in devicePool.values())
            
            for t in it:
                t[1].buildBinary(w, stakeValue=t[2], **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairValues object from the specified walker,
        including source validation. The following keyword arguments are
        supported:
        
            logger              A logger to which messages will be sent.
            
            posBase             A StringWalker whose base is used for offsets
                                to Device objects. If not specified, the w
                                argument is used.
            
            valueFormatFirst    The mask representing which values are present
                                in the first Value. This is required.
            
            valueFormatSecond   The mask representing which values are present
                                in the second Value. This is required.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("pairvalues")
        otcd = kwArgs.get('otcommondeltas')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        r = cls()
        posBase = kwArgs.get('posBase', w)  # walker for base of PairPos table
        valueFormatFirst = kwArgs['valueFormatFirst']
        valueFormatSecond = kwArgs['valueFormatSecond']
        vfw = value.Value.fromvalidatedwalker
        
        if valueFormatFirst:
            v = vfw(
              w,
              valueFormat = valueFormatFirst,
              posBase = posBase,
              logger = logger,
              otcommondeltas=otcd)
            
            r.first = v or None
        
        if valueFormatSecond:
            v = vfw(
              w,
              valueFormat = valueFormatSecond,
              posBase = posBase,
              logger = logger,
              otcommondeltas=otcd)
            
            r.second = v or None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PairValues object from the specified walker.
        The following keyword arguments are supported:
        
            posBase             A StringWalker whose base is used for offsets
                                to Device objects. If not specified, the w
                                argument is used.
            
            valueFormatFirst    The mask representing which values are present
                                in the first Value. This is required.
            
            valueFormatSecond   The mask representing which values are present
                                in the second Value. This is required.
        
        >>> d1 = {
        ...   'posBase': "test stake",
        ...   'valueFormatFirst': 255,
        ...   'valueFormatSecond': 255}
        >>> d2 = {'valueFormatFirst': 255, 'valueFormatSecond': 255}
        >>> w = writer.LinkedWriter()
        >>> w.stakeCurrentWithValue("test stake")
        >>> _testingValues[0].buildBinary(w, **d1)
        >>> _testingValues[0] == PairValues.frombytes(w.binaryString(), **d2)
        True
        
        >>> w.reset()
        >>> w.stakeCurrentWithValue("test stake")
        >>> _testingValues[1].buildBinary(w, **d1)
        >>> _testingValues[1] == PairValues.frombytes(w.binaryString(), **d2)
        True
        
        >>> w.reset()
        >>> w.stakeCurrentWithValue("test stake")
        >>> _testingValues[2].buildBinary(w, **d1)
        >>> _testingValues[2] == PairValues.frombytes(w.binaryString(), **d2)
        True
        """
        
        otcd = kwArgs.get('otcommondeltas')
        
        r = cls()
        posBase = kwArgs.get('posBase', w)  # walker for base of PairPos table
        valFmtFirst = kwArgs['valueFormatFirst']
        valFmtSecond = kwArgs['valueFormatSecond']
        vfw = value.Value.fromwalker
        
        if valFmtFirst:
            v = vfw(w, valueFormat=valFmtFirst, posBase=posBase, otcommondeltas=otcd)
            r.first = v or None
        
        if valFmtSecond:
            v = vfw(w, valueFormat=valFmtSecond, posBase=posBase, otcommondeltas=otcd)
            r.second = v or None
        
        return r
    
    def getMasks(self):
        """
        Returns a pair with the computed mask values for first and second. Zero
        will be used for missing entries.
        
        >>> _testingValues[0].getMasks()
        (0, 1)
        >>> _testingValues[1].getMasks()
        (128, 0)
        >>> _testingValues[2].getMasks()
        (129, 48)
        """
        
        if self.first is None:
            m1 = 0
        else:
            m1 = self.first.getMask()
        
        if self.second is None:
            m2 = 0
        else:
            m2 = self.second.getMask()
        
        return m1, m2

    def writeFontWorkerSource(self, s, **kwArgs):
        """
        Write PairValue as Font Worker-style source. The following
        keyword args are required:
            lbl_first: string to use for 'first'
            lbl_second: string to use for 'second'
        """
        attr_order = (
          ('xPlacement', 'x placement'),
          ('yPlacement', 'y placement'),
          ('xAdvance', 'x advance'),
          ('yAdvance', 'y advance'),
          )

        lbl1 = kwArgs.get('lbl_first')
        lbl2 = kwArgs.get('lbl_second')

        if self.first is not None:
            self.first.writeFontWorkerSource(
              s,
              prefix="left ",
              lbl="%s\t%s" % (lbl1, lbl2))

        if self.second is not None:
            self.second.writeFontWorkerSource(
              s,
              prefix="right ",
              lbl="%s\t%s" % (lbl1, lbl2))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import writer
    
    v = value._testingValues
    
    _testingValues = (
        PairValues(None, v[0]),
        PairValues(v[1], None),
        PairValues(v[2], v[3]))
    
    del v

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
