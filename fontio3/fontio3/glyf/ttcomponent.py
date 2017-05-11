#
# ttcomponent.py
#
# Copyright © 2009-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single components in a TrueType composite glyph.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import mathutilities, matrix
from fontio3.glyf import ttcomponentflags

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_matrix(p, obj, label, **kwArgs):
    parentObj = kwArgs['parent']
    d = obj.__dict__.setdefault('kwArgs', {})
    d['shiftBeforeScale'] = parentObj.offsetsAreScaled
    p.simple(obj, label=label)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    m = obj.transformationMatrix
    ZE = mathutilities.zeroEnough
    CE = mathutilities.closeEnough
    r = True
    
    if ZE(m[0][0]) and ZE(m[0][1]):
        logger.error((
          'E1116',
          (),
          "Component matrix collapses to zero in x."))
        
        r = False
    
    if ZE(m[1][0]) and ZE(m[1][1]):
        logger.error((
          'E1116',
          (),
          "Component matrix collapses to zero in y."))
        
        r = False
    
    if (obj.compoundAnchor is None) != (obj.componentAnchor is None):
        logger.error((
          'E1117',
          (),
          "Either both anchors or neither should be specified."))
        
        r = False
    
    if (
      (obj.compoundAnchor is not None) and
      (obj.transformationMatrix != matrix.Matrix())):
        
        logger.error((
          'E1117',
          (),
          "Matrix must be identity if anchors are used."))
        
        r = False
    
    x = abs(m[0][0])
    y = abs(m[1][1])
    
    if (
      (x != 1 and CE(x, 1, delta=1.0e-3)) or
      (y != 1 and CE(y, 1, delta=1.0e-3))):
        
        logger.warning((
          'V0816',
          (),
          "The x-scale and/or y-scale for this component is close to +1 "
          "or -1, but not exactly equal to +1 or -1."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TTComponent(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single component of a TrueType composite glyph.
    These are simple collections of attributes.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Component glyph: xyz81
    Transformation matrix: Shift Y by -40
    Round to grid: True
    
    >>> _testingValues[2].pprint()
    Component glyph: 100
    Transformation matrix: [[1.25, 0.75, 0.0], [0.0, 1.5, 0.0], [300.0, 0.0, 1.0]]
    This component's metrics will be used: True
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        glyphIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Component glyph",
            attr_renumberdirect = True,
            attr_usenamerforstr = True,
            attr_validatecode_toolargeglyph = 'E1113'),
        
        transformationMatrix = dict(
            attr_asimmutabledeep = True,
            attr_initfunc = matrix.Matrix,
            attr_label = "Transformation matrix",
            attr_pprintfunc = _pprint_matrix,
            attr_pprintfuncneedsobj = True),
        
        compoundAnchor = dict(  # in this glyph
            attr_label = "Compound anchor",
            attr_renumberpointsdirect = True,
            attr_showonlyiftrue = True),
        
        componentAnchor = dict(  # in component glyph
            attr_label = "Component anchor",
            attr_renumberpointsdirect = True,
            attr_showonlyiftrue = True),
        
        roundToGrid = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Round to grid",
            attr_showonlyiftrue = True),
        
        obsoleteBit4 = dict(
            attr_initfunc = (lambda: False),
            attr_label = "(obsolete bit 4)",
            attr_showonlyiftrue = True),
        
        useMyMetrics = dict(
            attr_initfunc = (lambda: False),
            attr_label = "This component's metrics will be used",
            attr_showonlyiftrue = True),
        
        overlapCompound = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Component overlaps",
            attr_showonlyiftrue = True),
        
        offsetsAreScaled = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Scaled offsets (Apple)",
            attr_showonlyiftrue = True))
    
    attrSorted = (
      'glyphIndex',
      'transformationMatrix',
      'compoundAnchor',
      'componentAnchor',
      'roundToGrid',
      'useMyMetrics',
      'overlapCompound',
      'offsetsAreScaled')
    
    #
    # Methods
    #
    
    def _flagsForMatrix(self):
        """
        Given the transformationMatrix and other flags associated with this
        object, creates an initial version of the component flags, and also the
        offsets and a flat matrix suitable for direct inclusion in the binary
        component data.
        """
        
        mShift, mScale = self.transformationMatrix.toShiftAndScale(
          self.offsetsAreScaled)
        
        xOffset, yOffset = [mShift[2][0], mShift[2][1]]
        flatMatrix = [mScale[0][0], mScale[0][1], mScale[1][0], mScale[1][1]]
        f = ttcomponentflags.TTComponentFlags()
        
        # Determine argsAreXYValues and argsAreWords
        if self.compoundAnchor is None and self.componentAnchor is None:
            f.argsAreXYValues = True
            
            if (-128 <= xOffset < 128) and (-128 <= yOffset < 128):
                f.argsAreWords = False
            else:
                f.argsAreWords = True
        
        else:
            f.argsAreXYValue = False
            
            if (
              (0 <= self.compoundAnchor < 256) and
              (0 <= self.componentAnchor < 256)):
                
                f.argsAreWords = False
            
            else:
                f.argsAreWords = True
        
        # Determine hasSimpleScale, hasXYScale, and hasMatrix
        f.hasSimpleScale = f.hasXYScale = f.hasMatrix = False
        
        if flatMatrix != [1.0, 0.0, 0.0, 1.0]:
            if flatMatrix[1:3] == [0.0, 0.0]:
                if flatMatrix[0] == flatMatrix[3]:
                    f.hasSimpleScale = True
                
                else:
                    f.hasXYScale = True
            
            else:
                f.hasMatrix = True
        
            if self.offsetsAreScaled:
                f.scaledComponentOffset = True
            else:
                f.unscaledComponentOffset = True
        
        else:
            f.scaledComponentOffset = f.unscaledComponentOffset = False
        
        return f, xOffset, yOffset, flatMatrix
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TTComponent object to the specified
        LinkedWriter. There are two keyword arguments whose values must be
        provided if they are True (they will default to False):
        
            hasHints
            moreComponents
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0006 0050 00D8                           |...P..          |
        
        >>> d = {'hasHints': True, 'moreComponents': True}
        >>> utilities.hexdump(_testingValues[2].binaryString(**d))
               0 | 13A3 0064 012C 0000  5000 3000 0000 6000 |...d.,..P.0...`.|
        """
        
        f, xOffset, yOffset, flatMatrix = self._flagsForMatrix()
        f.roundToGrid = self.roundToGrid
        f.moreComponents = kwArgs.get('moreComponents', False)
        f.hasHints = kwArgs.get('hasHints', False)
        f.useMyMetrics = self.useMyMetrics
        f.overlapCompound = self.overlapCompound
        f.buildBinary(w)
        w.add("H", self.glyphIndex)
        
        if f.argsAreXYValues:
            if f.argsAreWords:
                w.add("hh", xOffset, yOffset)
            else:
                w.add("bb", xOffset, yOffset)
        
        elif f.argsAreWords:
            w.add("HH", self.compoundOffset, self.componentOffset)
        
        else:
            w.add("BB", self.compoundOffset, self.componentOffset)
        
        oldRound = utilities.oldRound
        
        if f.hasSimpleScale:
            w.add("h", int(oldRound(flatMatrix[0] * 16384)))
        
        elif f.hasXYScale:
            w.add("h", int(oldRound(flatMatrix[0] * 16384)))
            w.add("h", int(oldRound(flatMatrix[3] * 16384)))
        
        elif f.hasMatrix:
            w.add("4h", *[int(oldRound(n * 16384)) for n in flatMatrix])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTComponent. However, it
        also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> TTComponent.fromvalidatedbytes(s, logger=logger).pprint()
        test.ttcomponent - DEBUG - Walker has 6 remaining bytes.
        Component glyph: 80
        Transformation matrix: Shift Y by -40.0
        Round to grid: True
        
        >>> obj = TTComponent.fromvalidatedbytes(s[:1], logger=logger)
        test.ttcomponent - DEBUG - Walker has 1 remaining bytes.
        test.ttcomponent - ERROR - Insufficient bytes
        
        >>> obj = TTComponent.fromvalidatedbytes(s[:3], logger=logger)
        test.ttcomponent - DEBUG - Walker has 3 remaining bytes.
        test.ttcomponent - ERROR - Insufficient bytes for component glyph index
        
        >>> obj = TTComponent.fromvalidatedbytes(s[:-1], logger=logger)
        test.ttcomponent - DEBUG - Walker has 5 remaining bytes.
        test.ttcomponent - ERROR - Insufficient bytes for x- and y-offset arguments.
        """
        
        M = matrix.Matrix
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ttcomponent')
        else:
            logger = logger.getChild('ttcomponent')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        flags = ttcomponentflags.TTComponentFlags.fromvalidatednumber(
          w.unpack("H"),
          logger=logger)
        
        if w.length() < 2:
            logger.error((
              'V0190',
              (),
              "Insufficient bytes for component glyph index"))
            
            return None
        
        r = cls(
          glyphIndex = w.unpack("H"),
          roundToGrid = flags.roundToGrid,
          obsoleteBit4 = flags.obsoleteBit4,
          useMyMetrics = flags.useMyMetrics,
          overlapCompound = flags.overlapCompound)
        
        if flags.argsAreXYValues:
            if flags.argsAreWords:
                if w.length() < 4:
                    logger.error((
                      'V0191',
                      (),
                      "Insufficient bytes for x- and y-offset arguments."))
                    
                    return None
                
                shiftMatrix = M.forShift(*w.unpack("2h"))
            
            else:
                if w.length() < 2:
                    logger.error((
                      'V0191',
                      (),
                      "Insufficient bytes for x- and y-offset arguments."))
                    
                    return None
                
                shiftMatrix = M.forShift(*w.unpack("2b"))
        
        elif flags.argsAreWords:
            if w.length() < 4:
                logger.error((
                  'V0192',
                  (),
                  "Insufficient bytes for anchor information."))
                
                return None
            
            shiftMatrix = M()
            r.compoundAnchor, r.componentAnchor = w.unpack("2H")
        
        else:
            if w.length() < 2:
                logger.error((
                  'V0192',
                  (),
                  "Insufficient bytes for anchor information."))
                
                return None
            
            shiftMatrix = M()
            r.compoundAnchor, r.componentAnchor = w.unpack("2B")
        
        if (flags.hasSimpleScale + flags.hasXYScale + flags.hasMatrix) > 1:
            logger.error((
              'E1100',
              (),
              "More than one of the simple scale, XY scale, and matrix "
              "flag bits are set. At most, one of these should be set."))
            
            return None
        
        if flags.hasSimpleScale:
            if w.length() < 2:
                logger.error((
                  'V0193',
                  (),
                  "Insufficient bytes for simple scale value."))
                
                return None
            
            n = w.unpack("h") / 16384
            scaleMatrix = M.forScale(n, n)
        
        elif flags.hasXYScale:
            if w.length() < 4:
                logger.error((
                  'V0194',
                  (),
                  "Insufficient bytes for x- and y-scale values."))
                
                return None
            
            xScale, yScale = [n / 16384 for n in w.unpack("2h")]
            scaleMatrix = M.forScale(xScale, yScale)
        
        elif flags.hasMatrix:
            if w.length() < 8:
                logger.error((
                  'V0195',
                  (),
                  "Insufficient bytes for transformation matrix."))
                
                return None
            
            t = [n / 16384 for n in w.unpack("4h")]
            scaleMatrix = M([[t[0], t[1], 0], [t[2], t[3], 0], [0, 0, 1]])
        
        else:
            scaleMatrix = M()
        
        # now multiply the matrices, order dependent on the Apple/MS state
        if flags.scaledComponentOffset:
            r.transformationMatrix = shiftMatrix.multiply(scaleMatrix)  # Apple
            r.offsetsAreScaled = True
        
        else:
            r.transformationMatrix = scaleMatrix.multiply(shiftMatrix)  # MS

        if flags.obsoleteBit4:
            logger.error((
                'G0014',
                (),
                "Obsolete bit #4 of flags is set."))
        
        d = kwArgs.get('componentInfo', {})
        d['hasHints'] = flags.hasHints
        d['moreComponents'] = flags.moreComponents
        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TTComponent object from the specified walker.
        In addition, the hasHints and moreComponents values are set in the
        componentInfo dict that is passed in via kwArgs.
        
        >>> fb = TTComponent.frombytes
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        
        >>> d = {'hasHints': True, 'moreComponents': True}
        >>> _testingValues[2] == fb(_testingValues[2].binaryString(**d))
        True
        """
        
        M = matrix.Matrix
        flags = ttcomponentflags.TTComponentFlags.fromnumber(w.unpack("H"))
        
        r = cls(
          glyphIndex = w.unpack("H"),
          roundToGrid = flags.roundToGrid,
          obsoleteBit4 = flags.obsoleteBit4,
          useMyMetrics = flags.useMyMetrics,
          overlapCompound = flags.overlapCompound)
        
        if flags.argsAreXYValues:
            if flags.argsAreWords:
                shiftMatrix = M.forShift(*w.unpack("2h"))
            else:
                shiftMatrix = M.forShift(*w.unpack("2b"))
        
        elif flags.argsAreWords:
            shiftMatrix = M()
            r.compoundAnchor, r.componentAnchor = w.unpack("HH")
        
        else:
            shiftMatrix = M()
            r.compoundAnchor, r.componentAnchor = w.unpack("BB")
        
        if flags.hasSimpleScale:
            n = w.unpack("h") / 16384
            scaleMatrix = M.forScale(n, n)
        
        elif flags.hasXYScale:
            xScale, yScale = [n / 16384 for n in w.unpack("2h")]
            scaleMatrix = M.forScale(xScale, yScale)
        
        elif flags.hasMatrix:
            t = [n / 16384 for n in w.unpack("4h")]
            scaleMatrix = M([[t[0], t[1], 0], [t[2], t[3], 0], [0, 0, 1]])
        
        else:
            scaleMatrix = M()
        
        # now multiply the matrices, order dependent on the Apple/MS state
        if flags.scaledComponentOffset:
            r.transformationMatrix = shiftMatrix.multiply(scaleMatrix)  # Apple
            r.offsetsAreScaled = True
        else:
            r.transformationMatrix = scaleMatrix.multiply(shiftMatrix)  # MS
        
        d = kwArgs.get('componentInfo', {})
        d['hasHints'] = flags.hasHints
        d['moreComponents'] = flags.moreComponents
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _m1 = matrix.Matrix.forShift(0, -40)
    
    _m2 = matrix.Matrix([
      [1.25, 0.75, 0.0],
      [0.0, 1.5, 0.0],
      [300.0, 0.0, 1.0]])
    
    _testingValues = (
        TTComponent(),
        TTComponent(glyphIndex=80, transformationMatrix=_m1, roundToGrid=True),
        
        TTComponent(
          glyphIndex = 100,
          transformationMatrix = _m2,
          useMyMetrics = True),
        
        TTComponent(glyphIndex=901),
        TTComponent(glyphIndex=902),
        TTComponent(glyphIndex=903),
        TTComponent(glyphIndex=904),
        TTComponent(glyphIndex=905))
    
    del _m1, _m2

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
