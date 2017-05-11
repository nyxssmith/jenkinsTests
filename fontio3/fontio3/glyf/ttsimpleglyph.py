#
# ttsimpleglyph.py
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for simple (i.e. non-composite) TrueType glyphs.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.glyf import ttbounds, ttcontour, ttcontours, ttpoint
from fontio3.hints import hints_tt
from fontio3.SparkHints import hints as sparkhints

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pf(p, s, label, **kwArgs):
    p.label = label
    kwArgs.pop('p', None)
    
    if utilities.hintKind(s) == 'Spark':
        obj = sparkhints.Hints.frombytes(s)
    else:
        obj = hints_tt.Hints.frombytes(s)
    
    obj.pprint(p=p, **kwArgs)

def _recalc(obj, **kwArgs):
    newObj = obj.__copy__()
    newObj.bounds = ttbounds.TTBounds.fromcontours(obj.contours or [])
    return newObj != obj, newObj

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    actualBounds = ttbounds.TTBounds.fromcontours(obj.contours or None)
    
    if obj.bounds != actualBounds:
        if obj.bounds:
            objlist = obj.bounds.asList()
        else:
            objlist = None

        if actualBounds: 
            actlist = actualBounds.asList()
        else:
            actlist = None
            
        logger.error((
          'E1112',
          (actlist, objlist),
          "Bounds should be %s, but are %s."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TTSimpleGlyph(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire simple (non-composite) TrueType glyphs. These
    are simple objects with the following attributes:
    
        bounds          A TTBounds object.
        contours        A TTContours object.
        hintBytes       A bytes object with the raw hints.
    
    >>> _testingValues[1].pprint()
    Bounds: (no data)
    Contours:
    Hints:
      0000 (0x000000): SVTCA[y]
      0001 (0x000001): SVTCA[x]
    
    >>> _testingValues[2].pprint()
    Bounds:
      Minimum X: 620
      Minimum Y: 610
      Maximum X: 980
      Maximum Y: 1090
    Contours:
      Contour 0:
        Point 0: (620, 610), on-curve
        Point 1: (620, 1090), on-curve
        Point 2: (980, 1090), on-curve
        Point 3: (980, 610), on-curve
      Contour 1:
        Point 0: (750, 750), on-curve
        Point 1: (850, 700), off-curve
        Point 2: (950, 750), on-curve
        Point 3: (850, 1000), on-curve
    Hints:
      0000 (0x000000): SVTCA[y]
      0001 (0x000001): SVTCA[x]
    
    >>> g = _testingValues[2].__deepcopy__()
    >>> g.bounds.yMax = 1050
    >>> e = utilities.fakeEditor(0x10000)
    >>> logger = utilities.makeDoctestLogger("test2")
    >>> g.isValid(logger=logger, editor=e)
    test2 - ERROR - Bounds should be [620, 610, 980, 1090], but are [620, 610, 980, 1050].
    test2.contours.contour 1 - WARNING - Not all extrema are marked with on-curve points.
    False
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        bounds = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: None),
            attr_label = "Bounds",
            attr_strneedsparens = True),
        
        contours = dict(
            attr_followsprotocol = True,
            attr_initfunc = ttcontours.TTContours,
            attr_label = "Contours"),
        
        hintBytes = dict(
            attr_label = "Hints",
            attr_initfunc = (lambda: b''),
            attr_pprintfunc = _pf))
    
    isComposite = False
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TTSimpleGlyph object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0000 0000 0000  0000 0002 0001      |..............  |
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0002 026C 0262 03D4  0442 0003 0007 0002 |...l.b...B......|
              10 | 0001 0111 2111 2716  3727 026C 0168 E664 |....!.'.7'.l.h.d|
              20 | 6464 0262 01E0 FE20  8C32 32FA           |dd.b... .22.    |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self.contours = self.contours.compacted()
        
        if self.contours or self.hintBytes:
            w.add("H", len(self.contours))
            
            if self.bounds:
                self.bounds.buildBinary(w, **kwArgs)
            else:
                w.add("HHHH", 0, 0, 0, 0)  # *must* have data for 'bounds'
            
            if self.contours:
                it = map(len, iter(self.contours))
                w.addGroup("H", utilities.cumulCount(it, wantEndIndices=True))
            
            w.add("H", len(self.hintBytes))
            w.addString(self.hintBytes)
            
            if self.contours:
                self.contours.buildBinary(w, **kwArgs)
            
            w.alignToByteMultiple(2)
    
    @classmethod
    def fromcompositeglyph(cls, compositeGlyph, **kwArgs):
        """
        Constructs and returns a TTSimpleGlyph using the specified composite
        glyph as a "template." The kwArgs must contain an editor.
        """
        
        try:
            v = list(compositeGlyph.pieceIterator(**kwArgs))
        except:
            v = None
        
        if v is None:
            return cls()
        
        vx = [c.transformed(m) for obj, m in v for c in obj]
        
        return cls(
          bounds = ttbounds.TTBounds.fromcontours(vx),
          contours = ttcontours.TTContours(vx),
          hintBytes = compositeGlyph.hintBytes)


    @classmethod
    def fromscaleroutline(cls, outl, **kwArgs):
        """
        Constructs and returns a TTSimpleglyph using the specified outline
        data. The outline data must conform to the ScalerInterface outline
        format (see ScalerInterface.getOutline() for details).
        
        Accepts kwArg 'hints', which will be stored as hintBytes if present.
        """

        ctrs = []
        ctr = None

        ird = lambda x: int(round(x))
        TTP = ttpoint.TTPoint
        n = len(outl) - 1
        
        hintBytes = kwArgs.get('hints') or ''

        for i, pt in enumerate(outl):
            last = (i == n) or (i < n and outl[i+1].kind == 'move')

            if pt.kind == 'move':
                if ctr:
                    ctrs.append(ctr)
                npt = TTP(ird(pt.x), ird(pt.y), onCurve=True)
                ctr = ttcontour.TTContour()
                ctr.append(npt)

            if pt.kind == 'line':
                npt = TTP(ird(pt.x), ird(pt.y), onCurve=True)
                if last and npt.x == ctr[0].x and npt.y == ctr[0].y:
                    pass  # explicit contour close; don't add
                else:
                    ctr.append(npt)

            if pt.kind == 'quad':
                offpt = TTP(
                  ird(pt.offCurvePoint.x),
                  ird(pt.offCurvePoint.y),
                  onCurve=False)

                onpt = TTP(
                  ird(pt.onCurvePoint.x),
                  ird(pt.onCurvePoint.y),
                  onCurve=True)

                ctr.append(offpt)

                if last and onpt.x == ctr[0].x and onpt.y == ctr[0].y:
                    pass  # explicit contour close; don't add.
                else:
                    ctr.append(onpt)

        if ctr:
            ctrs.append(ctr)

        return cls(
          bounds=ttbounds.TTBounds.fromcontours(ctrs),
          contours=ttcontours.TTContours(ctrs),
          hintBytes=hintBytes)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTSimpleGlyph. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[2].binaryString()
        >>> TTSimpleGlyph.fromvalidatedbytes(s, logger=logger).pprint()
        test.ttsimpleglyph - DEBUG - Walker has 44 remaining bytes.
        test.ttsimpleglyph.ttbounds - DEBUG - Walker has 42 remaining bytes.
        test.ttsimpleglyph.ttcontours - DEBUG - Walker has 26 remaining bytes.
        Bounds:
          Minimum X: 620
          Minimum Y: 610
          Maximum X: 980
          Maximum Y: 1090
        Contours:
          Contour 0:
            Point 0: (620, 610), on-curve
            Point 1: (620, 1090), on-curve
            Point 2: (980, 1090), on-curve
            Point 3: (980, 610), on-curve
          Contour 1:
            Point 0: (750, 750), on-curve
            Point 1: (850, 700), off-curve
            Point 2: (950, 750), on-curve
            Point 3: (850, 1000), on-curve
        Hints:
          0000 (0x000000): SVTCA[y]
          0001 (0x000001): SVTCA[x]
        
        >>> fvb = TTSimpleGlyph.fromvalidatedbytes
        >>> obj = fvb(s[:-1], logger=logger)
        test.ttsimpleglyph - DEBUG - Walker has 43 remaining bytes.
        test.ttsimpleglyph.ttbounds - DEBUG - Walker has 41 remaining bytes.
        test.ttsimpleglyph.ttcontours - DEBUG - Walker has 25 remaining bytes.
        test.ttsimpleglyph.ttcontours - ERROR - Insufficient bytes for y-delta.

        >>> _testingValues[1] == fvb(_testingValues[1].binaryString(), logger=logger)
        test.ttsimpleglyph - DEBUG - Walker has 14 remaining bytes.
        test.ttsimpleglyph.ttbounds - DEBUG - Walker has 12 remaining bytes.
        True
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ttsimpleglyph')
        else:
            logger = logger.getChild('ttsimpleglyph')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        numContours = w.unpack("H")
        
        if numContours == 0xFFFF:
            logger.error((
              'V0002',
              (),
              "Composite glyph passed to TTSimpleGlyph."))
            
            return None
        
        b = ttbounds.TTBounds.fromvalidatedwalker(w, logger=logger, **kwArgs)
        
        if b is None:
            return None
        
        if numContours == 0 and b == ttbounds.TTBounds():  # special-case
            b = None

        if numContours:
            if w.length() < 2 * numContours:
                logger.error(('V0187', (), "Insufficient bytes for endPoints."))
                return None
        
            endPoints = w.group("H", numContours)
        
            if sorted(set(endPoints)) != list(endPoints):
                logger.error((
                  'V0987',
                  (),
                  "Endpoints have duplicates or are out-of-order."))
            
                return None
        
        if w.length() < 2:
            logger.error(('V0188', (), "Insufficient bytes for hint length."))
            return None
        
        hintLength = w.unpack("H")
        
        if hintLength:
            if w.length() < hintLength:
                logger.error(('V0189', (), "Insufficient bytes for hints."))
                return None
            
            h = w.chunk(hintLength)
        
        else:
            h = b''
        
        if numContours:
            kwArgs.pop('endPoints', None)
            
            c = ttcontours.TTContours.fromvalidatedwalker(
              w,
              endPoints = endPoints,
              logger = logger,
              **kwArgs)
            
            if c is None:
                c = ttcontours.TTContours()
        
        else:
            c = ttcontours.TTContours()
        
        if w.length():
            pad = w.rest()
            
            if len(pad) > 3:
                logger.error(('V1007', (), "More than 3 pad bytes following glyph data."))
            
            if any(pad):
                logger.error(('V1008', (), "Non-zero pad bytes following glyph data."))

        return cls(b, c, h)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a TTSimpleGlyph object from the specified walker.
        
        >>> _testingValues[1] == TTSimpleGlyph.frombytes(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == TTSimpleGlyph.frombytes(_testingValues[2].binaryString())
        True
        """
        
        numContours = w.unpack("H")
        assert numContours != 0xFFFF, "Composite glyph passed to simple glyph walker!"
        b = ttbounds.TTBounds.fromwalker(w, **kwArgs)

        if numContours == 0 and b == ttbounds.TTBounds():  # special case
            b = None

        if numContours:
            endPoints = w.group("H", numContours)

        h = w.chunk(w.unpack("H"))
        
        if numContours:
            kwArgs.pop('endPoints', None)
            c = ttcontours.TTContours.fromwalker(w, endPoints=endPoints, **kwArgs)
        else:
            c = ttcontours.TTContours()
        
        return cls(b, c, h)
    
    
    def pointCount(self, **kwArgs):
        """
        Returns the number of points in the (unnormalized) glyph. The following
        keyword arguments are supported but ignored (they are used in the
        pointCount() method for composite glyphs):
        
            editor      This is ignored here.
            runCheck    This is ignored here.
        """
        
        return sum(len(c) for c in self.contours)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _cstv = ttcontours._testingValues
    
    _testingValues = [
        TTSimpleGlyph(),
        TTSimpleGlyph(hintBytes=utilities.fromhex("00 01")),
        
        TTSimpleGlyph(
          contours = _cstv[1],
          hintBytes=utilities.fromhex("00 01"))]
    
    _testingValues[2] = _testingValues[2].recalculated()
    _testingValues = tuple(_testingValues)
    del _cstv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
