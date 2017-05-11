#
# minmax.py
#
# Copyright © 2010-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to MinMax subtables in OpenType 'BASE' tables.
"""

# System imports
import functools
import logging
import operator

# Other imports
from fontio3.BASE import coordinate, minmax_record, minmax_recorddict
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class MinMax(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing minimum and maximum extent values. These are simple
    collections of the following attributes:
    
        minCoord
        maxCoord
        featRecs
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Minimum coordinate:
      Coordinate: -10
      Device table:
        Tweak at 12 ppem: -5
        Tweak at 13 ppem: -3
        Tweak at 14 ppem: -1
        Tweak at 18 ppem: 2
        Tweak at 20 ppem: 3
    Maximum coordinate:
      Coordinate: 0
      Glyph: xyz26
      Point: 9
    Feature-specific MinMax values:
      Feature 'abcd':
        Minimum coordinate:
          Coordinate: 0
        Maximum coordinate:
          Coordinate: 15
          Device table:
            Tweak at 12 ppem: -2
            Tweak at 14 ppem: -1
            Tweak at 18 ppem: 1
      Feature 'wxyz':
        Maximum coordinate:
          Coordinate: -10
          Glyph: xyz15
          Point: 12
    
    >>> obj = _testingValues[1].__deepcopy__()
    >>> CS = coordinate_simple.Coordinate_simple
    >>> obj.minCoord = CS(-20000)
    >>> obj.maxCoord = CS(20000)
    >>> logger = utilities.makeDoctestLogger("minmax_test")
    >>> e = _fakeEditor()
    >>> obj.isValid(logger=logger, editor=e)
    minmax_test.maxCoord - WARNING - The FUnit value 20000 is more than two ems away from the origin, which seems unlikely.
    minmax_test.minCoord - WARNING - The FUnit value -20000 is more than two ems away from the origin, which seems unlikely.
    True
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        minCoord = dict(
            attr_followsprotocol = True,
            attr_label = "Minimum coordinate"),
        
        maxCoord = dict(
            attr_followsprotocol = True,
            attr_label = "Maximum coordinate"),
        
        featRecs = dict(
            attr_followsprotocol = True,
            attr_initfunc = minmax_recorddict.RecordDict,
            attr_label = "Feature-specific MinMax values",
            attr_showonlyiftrue = True))
    
    attrSorted = ('minCoord', 'maxCoord', 'featRecs')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the MinMax object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0016 002A 0002 6162  6364 0032 001C 7778 |...*..abcd.2..wx|
              10 | 797A 0000 0022 0003  FFF6 0020 0003 000F |yz..."..... ....|
              20 | 0026 0002 FFF6 000E  000C 0002 0000 0019 |.&..............|
              30 | 0009 0001 0000 000C  0014 0002 BDF0 0020 |............... |
              40 | 3000 000C 0012 0001  8C04                |0.........      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        coordPool = kwArgs.get('coordinatePool', {})
        doLocalCoords = 'coordinatePool' not in kwArgs
        devPool = kwArgs.pop('devicePool', {})
        doLocalDevs = 'devicePool' not in kwArgs
        
        for obj in (self.minCoord, self.maxCoord):
            if obj is not None:
                immut = obj.asImmutable(**kwArgs)
                
                if immut not in coordPool:
                    coordPool[immut] = (obj, w.getNewStake())
                
                w.addUnresolvedOffset("H", stakeValue, coordPool[immut][1])
            
            else:
                w.add("H", 0)
        
        w.add("H", len(self.featRecs))
        ig0 = operator.itemgetter(0)
        
        for key, rec in sorted(self.featRecs.items(), key=ig0):
            w.add("4s", key)
            
            for obj in (rec.minCoord, rec.maxCoord):
                if obj is not None:
                    immut = obj.asImmutable(**kwArgs)
                    
                    if immut not in coordPool:
                        coordPool[immut] = (obj, w.getNewStake())
                    
                    w.addUnresolvedOffset("H", stakeValue, coordPool[immut][1])
                
                else:
                    w.add("H", 0)
        
        if doLocalCoords:
            for immut, (obj, stake) in sorted(coordPool.items(), key=ig0):
                obj.buildBinary(
                  w,
                  stakeValue = stake,
                  devicePool = devPool,
                  **kwArgs)
        
        if doLocalDevs:
            keyFunc = (lambda x: sorted(x[0][1]))
            
            for immut, (obj, stake) in sorted(devPool.items(), key=keyFunc):
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new MinMax object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[2].binaryString()
        >>> logger = utilities.makeDoctestLogger("minmax_fvw")
        >>> fvb = MinMax.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        minmax_fvw.minmax - DEBUG - Walker has 74 remaining bytes.
        minmax_fvw.minmax.minimum.coordinate - DEBUG - Coordinate format 3.
        minmax_fvw.minmax.minimum.coordinate_device - DEBUG - Walker has 52 remaining bytes.
        minmax_fvw.minmax.minimum.coordinate_device.device - DEBUG - Walker has 20 remaining bytes.
        minmax_fvw.minmax.minimum.coordinate_device.device - DEBUG - StartSize=12, endSize=20, format=2
        minmax_fvw.minmax.minimum.coordinate_device.device - DEBUG - Data are (48624, 32, 12288)
        minmax_fvw.minmax.maximum.coordinate - DEBUG - Coordinate format 2.
        minmax_fvw.minmax.maximum.coordinate_point - DEBUG - Walker has 32 remaining bytes.
        minmax_fvw.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 1.
        minmax_fvw.minmax.tag 'abcd'.coordinate_simple - DEBUG - Walker has 24 remaining bytes.
        minmax_fvw.minmax.tag 'abcd'.coordinate - DEBUG - Coordinate format 3.
        minmax_fvw.minmax.tag 'abcd'.coordinate_device - DEBUG - Walker has 46 remaining bytes.
        minmax_fvw.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Walker has 8 remaining bytes.
        minmax_fvw.minmax.tag 'abcd'.coordinate_device.device - DEBUG - StartSize=12, endSize=18, format=1
        minmax_fvw.minmax.tag 'abcd'.coordinate_device.device - DEBUG - Data are (35844,)
        minmax_fvw.minmax.tag 'wxyz'.coordinate - DEBUG - Coordinate format 2.
        minmax_fvw.minmax.tag 'wxyz'.coordinate_point - DEBUG - Walker has 40 remaining bytes.
        >>> obj == _testingValues[2]
        True
        
        >>> fvb(s[:3], logger=logger)
        minmax_fvw.minmax - DEBUG - Walker has 3 remaining bytes.
        minmax_fvw.minmax - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("minmax")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 6:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        minOffset, maxOffset, featCount = w.unpack("3H")
        d = {}
        fvw = coordinate.Coordinate_validated
        
        if minOffset:
            obj = fvw(
              w.subWalker(minOffset),
              logger = logger.getChild("minimum"),
              **kwArgs)
            
            if obj is None:
                return None
            
            d['minCoord'] = obj
        
        if maxOffset:
            obj = fvw(
              w.subWalker(maxOffset),
              logger = logger.getChild("maximum"),
              **kwArgs)
            
            if obj is None:
                return None
            
            d['maxCoord'] = obj
        
        if featCount:
            if w.length() < 8 * featCount:
                logger.error((
                  'V0640',
                  (),
                  "The feature records are missing or incomplete."))
                
                return None
            
            featDict = minmax_recorddict.RecordDict()
            
            for tag, minOffset, maxOffset in w.group("4s2H", featCount):
                dd = {}
                itemLogger = logger.getChild(
                  "tag '%s'" % (utilities.ensureUnicode(tag),))
                
                if minOffset:
                    obj = fvw(
                      w.subWalker(minOffset),
                      logger = itemLogger,
                      **kwArgs)
                    
                    if obj is None:
                        return None
                    
                    dd['minCoord'] = obj
                
                if maxOffset:
                    obj = fvw(
                      w.subWalker(maxOffset),
                      logger = itemLogger,
                      **kwArgs)
                    
                    if obj is None:
                        return None
                    
                    dd['maxCoord'] = obj
                
                if dd:
                    featDict[tag] = minmax_record.Record(**dd)
            
            d['featRecs'] = featDict
        
        return cls(**d)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a MinMax object from the specified walker.
        
        >>> for i in range(3):
        ...     obj = _testingValues[i]
        ...     obj == MinMax.frombytes(obj.binaryString())
        True
        True
        True
        """
        
        minOffset, maxOffset, featCount = w.unpack("3H")
        d = {}
        fw = coordinate.Coordinate
        
        if minOffset:
            d['minCoord'] = fw(w.subWalker(minOffset), **kwArgs)
        
        if maxOffset:
            d['maxCoord'] = fw(w.subWalker(maxOffset), **kwArgs)
        
        if featCount:
            d['featRecs'] = featDict = minmax_recorddict.RecordDict()
            
            for tag, minOffset, maxOffset in w.group("4s2H", featCount):
                dd = {}
                
                if minOffset:
                    dd['minCoord'] = fw(w.subWalker(minOffset), **kwArgs)
                
                if maxOffset:
                    dd['maxCoord'] = fw(w.subWalker(maxOffset), **kwArgs)
                
                featDict[tag] = minmax_record.Record(**dd)
        
        return cls(**d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.BASE import coordinate_simple
    from fontio3.utilities import namer
    
    def _fakeEditor():
        from fontio3.head import head
        
        e = utilities.fakeEditor(0x10000)
        e.head = head.Head()
        return e
    
    _cv = coordinate._testingValues
    _dv = minmax_recorddict._testingValues
    
    _testingValues = (
        MinMax(),
        MinMax(minCoord=_cv[2], maxCoord=_cv[3]),
        MinMax(minCoord=_cv[6], maxCoord=_cv[3], featRecs=_dv[1]))
    
    del _cv, _dv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
