#
# ttcompositeglyph.py
#
# Copyright © 2004-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for composite TrueType glyphs.
"""

# System imports
import functools
import itertools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import simplemeta
from fontio3.fontmath import matrix, rectangle

from fontio3.glyf import (
  ttbounds,
  ttcomponent,
  ttcomponents,
  ttcontour,
  ttsimpleglyph)

from fontio3.hints import hints_tt
from fontio3.SparkHints import hints as sparkhints

try:
    import intersectionlibbackend
    useIntLibOK = True

except ImportError:
    useIntLibOK = False

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
    origBounds = obj.bounds
    
    try:
        simples, matrices = zip(*list(obj.pieceIterator(**kwArgs)))
    except (BadOrCircularComponents, BadEditorOrGlyf):
        return False, obj
    
    fc = ttcontour.TTContour
    
    obj.bounds = ttbounds.TTBounds.fromcontours(
      [fc(x.pointIterator()) for x in simples],
      mxIter=matrices)
    
    return origBounds != obj.bounds, obj

def _simplify(obj, **kwArgs):
    """
    Return list of simple glyph composite components representing a
    (possibly nested) TTCompositeGlyph.
    """
    editor = kwArgs['editor']
    newcomponents = []
    for cmp in obj.components:
        if editor.glyf[cmp.glyphIndex].isComposite:
            tmpcomponents = _simplify(editor.glyf[cmp.glyphIndex], editor=editor)
            for tc in tmpcomponents:
                nm = tc.transformationMatrix.multiplied(cmp.transformationMatrix)
                nc = ttcomponent.TTComponent(
                  glyphIndex = tc.glyphIndex, 
                  transformationMatrix = nm)
                newcomponents.append(nc)
        else:
            newcomponents.append(cmp)
            
    return newcomponents


def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    badCycles, badGlyphs = set(), set()
    
    try:
        obj.allReferencedGlyphs(
          set(),
          badCycles = badCycles,
          badGlyphs = badGlyphs,
          editor = editor)
    
    except BadEditorOrGlyf:
        logger.error((
          'V0553',
          (),
          "Unable to validate composite glyph because either an editor or "
          "a 'glyf' table was not specified."))
        
        return False
    
    if badCycles:
        logger.error((
          'E1118',
          (sorted(badCycles),),
          "Circular component at or below these glyphs: %s"))
        
        return False
    
    if badGlyphs:
        logger.error((
          'E1113',
          (badCycles,),
          "Bad glyph indices: %s"))
        
        return False
    
    overlapReportThreshold = kwArgs.get('overlapReportThreshold', 0.95)
    f = ttbounds.TTBounds.fromcontours
    kwArgs.pop('runCheck', None)
    
    pieceRects = [
      f(c.transformed(mx))
      for c, mx in obj.pieceIterator(runCheck=False, **kwArgs)]
    
    badPieceRects = (None in pieceRects)
    
    if badPieceRects or (any(r.isEmpty() for r in pieceRects)):
        logger.warning((
          'E1123',
          (),
          "Composite glyph has empty component(s)."))
    
    if not badPieceRects:
        for r1, r2 in itertools.combinations(pieceRects, 2):
            if min(r1.overlapDegrees(r2)) >= overlapReportThreshold:
                logger.warning((
                  'E1121',
                  (),
                  "Composite glyph has overlapping components."))
            
                break  # only need to report this once per glyph
    
        uRect = functools.reduce(rectangle.Rectangle.unioned, pieceRects)
        r = True
    
        if uRect != obj.bounds:
            logger.error((
              'E1112',
              (uRect.asList(), obj.bounds.asList()),
              "Bounds should be %s, but are %s."))
        
            r = False
    
    else:
        r = False
    
    thisAsSimple = None
    fsg = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph
    thisAsSimple = fsg(obj, **kwArgs)
    
    if thisAsSimple is None:
        return False
    
    thisPointCount = sum(len(c) for c in thisAsSimple.contours)
    
    for c in obj.components:
        if c.compoundAnchor is not None:
            if c.compoundAnchor >= thisPointCount:
                logger.error((
                  'E1114',
                  (c.compoundAnchor,),
                  "Compound anchor point index %d is invalid."))
                
                r = False
        
        if c.componentAnchor is not None:
            g = editor.glyf[c.glyphIndex]
            
            if g.isComposite:
                try:
                    g = fsg(g, **kwArgs)
                except ValueError:
                    g = None
            
            if g is not None:
                count = sum(len(c) for c in g.contours)
                
                if c.componentAnchor >= count:
                    logger.error((
                      'E1114',
                      (c.glyphIndex, c.componentAnchor),
                      "On component glyph %d anchor point %d is invalid."))
                    
                    r = False
    
    hasIntersections = False
    
    cv = [
      tuple((float(p.x), float(p.y), (not p.onCurve)) for p in c)
      for c in thisAsSimple.contours]
    
    if useIntLibOK:
        if intersectionlibbackend.VerifyQuadOutline(cv)[0]:
            hasIntersections = True
    
    else:
        for c1, c2 in itertools.combinations(thisAsSimple.contours, 2):
            if c1.intersects(c2):
                hasIntersections = True
                break
    
    if hasIntersections:
        logger.warning((
          'W1110',
          (),
          "Composite has intersecting contours."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class BadEditorOrGlyf(ValueError): pass
class BadOrCircularComponents(ValueError): pass

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class TTCompositeGlyph(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single composite TrueType glyphs.
    
    >>> _testingValues[1].pprint()
    Bounds:
      Minimum X: 5
      Minimum Y: 5
      Maximum X: 120
      Maximum Y: 80
    Components:
      Component 1:
        Component glyph: 100
        Transformation matrix: [[1.25, 0.75, 0.0], [0.0, 1.5, 0.0], [300.0, 0.0, 1.0]]
        This component's metrics will be used: True
      Component 2:
        Component glyph: 80
        Transformation matrix: Shift Y by -40
        Round to grid: True
    Hints:
      0000 (0x000000): SVTCA[y]
      0001 (0x000001): SVTCA[x]
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        bounds = dict(
            attr_followsprotocol = True,
            attr_initfunc = ttbounds.TTBounds,
            attr_label = "Bounds",
            attr_strneedsparens = True),
        
        components = dict(
            attr_followsprotocol = True,
            attr_initfunc = ttcomponents.TTComponents,
            attr_label = "Components"),
        
        hintBytes = dict(
            attr_initfunc = (lambda: b''),
            attr_label = "Hints",
            attr_pprintfunc = _pf))
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    isComposite = True
    
    #
    # Methods
    #
    
    def allReferencedGlyphs(self, setToFill, **kwArgs):
        """
        Adds to a set containing all component glyph indices, recursively
        nested as needed.
        
        Supported keyword arguments are:
            
            badCycles   A set which, on output, contains any glyphs containing
                        circular references. This is optional.
            
            badGlyphs   A set which, on output, contains any out-of-bounds (or
                        otherwise invalid) glyph indices that were encountered
                        during the recursive walk. This is optional.
            
            editor      An Editor. This is required.
        
        This call may raise one of these exceptions:
        
            BadEditorOrGlyf
        
        >>> g, bc, bg = set(), set(), set()
        >>> _testingValues[1].allReferencedGlyphs(
        ...   g, badCycles=bc, badGlyphs=bg, editor=_fakeEditor_1)
        >>> print(g, bc, bg)
        {80, 100} set() set()
        
        >>> g.clear()
        >>> _testingValues[2].allReferencedGlyphs(
        ...   g, badCycles=bc, badGlyphs=bg, editor=_fakeEditor_2)
        >>> print(g, bc, bg)
        set() set() {901}
        
        >>> bg.clear()
        >>> _testingValues[2].allReferencedGlyphs(
        ...   g, badCycles=bc, badGlyphs=bg, editor=_fakeEditor_3)
        >>> print(sorted(g), bc, bg)
        [901, 902, 903, 904, 905] set() set()
        
        >>> g.clear()
        >>> _testingValues[2].allReferencedGlyphs(
        ...   g, badCycles=bc, badGlyphs=bg, editor=_fakeEditor_4)
        >>> print(sorted(g), bc, bg)
        [901, 902, 903, 904, 905] {901} set()
        """
        
        editor = kwArgs.get('editor')
        
        if not editor:
            raise BadEditorOrGlyf()
        
        g = editor.get(b'glyf')
        
        if not g:
            raise BadEditorOrGlyf()
        
        newAdditions = set()
        badGlyphs = kwArgs.get('badGlyphs', set())
        badCycles = kwArgs.get('badCycles', set())
        subGlyphs = {c.glyphIndex for c in self.components}
        
        for pieceIndex in subGlyphs:
            if pieceIndex in setToFill:
                badCycles.add(pieceIndex)  # circular
            
            elif pieceIndex in g:
                newAdditions.add(pieceIndex)
                subGlyph = g[pieceIndex]
                
                if subGlyph is not None:
                    if subGlyph.isComposite:
                        tempSet = setToFill | newAdditions
                        subGlyph.allReferencedGlyphs(tempSet, **kwArgs)
                        newAdditions.update(tempSet - setToFill)
                
                else:
                    badGlyphs.add(pieceIndex)  # referenced glyph was bad
            
            else:
                badGlyphs.add(pieceIndex)  # out of bounds
        
        setToFill.update(newAdditions)
    

    def asSimplifiedComposite(self, **kwArgs):
        """
        Return a new TTCompositeGlyph from self consisting only of TTSimpleGlyph
        (non-recursive) components.
        """
        components = ttcomponents.TTComponents(_simplify(self, **kwArgs))
        r = TTCompositeGlyph(
          bounds=self.bounds,
          components=components,
          hints=self.hintBytes)

        return r

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the TTCompositeGlyph object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | FFFF 0005 0005 0078  0050 12A3 0064 012C |.......x.P...d.,|
              10 | 0000 5000 3000 0000  6000 0106 0050 00D8 |..P.0...`....P..|
              20 | 0002 0001                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("h", -1)  # flag to indicate composite
        self.bounds.buildBinary(w, **kwArgs)
        hasHints = bool(self.hintBytes)
        kwArgs.pop('hasHints', None)
        self.components.buildBinary(w, hasHints=hasHints, **kwArgs)
        
        if hasHints:
            w.add("H", len(self.hintBytes))
            w.addString(self.hintBytes)
        
        w.alignToByteMultiple(2)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new TTCompositeGlyph. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = TTCompositeGlyph.fromvalidatedbytes
        >>> fvb(s, logger=logger).pprint()
        test.ttcompositeglyph - DEBUG - Walker has 36 remaining bytes.
        test.ttcompositeglyph.ttbounds - DEBUG - Walker has 34 remaining bytes.
        test.ttcompositeglyph.ttcomponents - DEBUG - Walker has 26 remaining bytes.
        test.ttcompositeglyph.ttcomponents.[0].ttcomponent - DEBUG - Walker has 26 remaining bytes.
        test.ttcompositeglyph.ttcomponents.[1].ttcomponent - DEBUG - Walker has 10 remaining bytes.
        Bounds:
          Minimum X: 5
          Minimum Y: 5
          Maximum X: 120
          Maximum Y: 80
        Components:
          Component 1:
            Component glyph: 100
            Transformation matrix: [[1.25, 0.75, 0.0], [0.0, 1.5, 0.0], [300, 0, 1]]
            This component's metrics will be used: True
          Component 2:
            Component glyph: 80
            Transformation matrix: Shift Y by -40.0
            Round to grid: True
        Hints:
          0000 (0x000000): SVTCA[y]
          0001 (0x000001): SVTCA[x]
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('ttcompositeglyph')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.debug(('V0004', (), "Insufficient bytes"))
            return None
        
        numContours = w.unpack("h")
        
        if numContours != -1:
            logger.error((
              'V0002',
              (),
              "Simple glyph passed to TTCompositeGlyph."))
            
            return None
        
        b = ttbounds.TTBounds.fromvalidatedwalker(w, logger=logger, **kwArgs)
        
        if b is None:
            return None
        
        componentInfo = {}
        kwArgs.pop('componentInfo', None)
        
        c = ttcomponents.TTComponents.fromvalidatedwalker(
          w,
          componentInfo = componentInfo,
          logger = logger,
          **kwArgs)
        
        if c is None:
            return None
        
        if componentInfo['hasHints']:
            if w.length() < 2:
                logger.error(('V0189', (), "Insufficient bytes for hints."))
                return None
            
            hintLength = w.unpack("H")
            
            if hintLength:
                if w.length() < hintLength:
                    logger.error(('V0189', (), "Insufficient bytes for hints."))
                    return None
                
                h = w.chunk(hintLength)
            
            else:
                h = b''
        
        else:
            h = b''
        
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
        Creates and returns a TTCompositeGlyph object from the specified
        walker.
        
        >>> _testingValues[1] == TTCompositeGlyph.frombytes(
        ...   _testingValues[1].binaryString())
        True
        """
        
        numContours = w.unpack("h")
        assert numContours == -1
        b = ttbounds.TTBounds.fromwalker(w)
        componentInfo = {}
        
        c = ttcomponents.TTComponents.fromwalker(
          w,
          componentInfo=componentInfo)
        
        if componentInfo['hasHints']:
            h = w.chunk(w.unpack("H"))
        else:
            h = b''
        
        return cls(b, c, h)
    
    def pieceIterator(self, **kwArgs):
        """
        Returns a generator over (TTContours, Matrix) pairs, where the matrix
        is fully resolved, even for deeply nested composite glyphs. There are
        two keyword arguments:
        
            currMatrix      The matrix on entry to this level. If not
                            specified, the identity matrix will be used.
            
            editor          The Editor object, from which the Glyf object is
                            obtained. This is required.
            
            runCheck        A Boolean controlling whether the pre-flight check
                            for bad glyphs or circular references will be run.
                            Default is True.
        
        This call may raise one of these exceptions:
        
            BadEditorOrGlyf
            BadOrCircularComponents
        """
        
        if kwArgs.get('runCheck', True):
            arg, b1, b2 = set(), set(), set()
            kwArgs.pop('badCycles', None)
            kwArgs.pop('badGlyphs', None)
            self.allReferencedGlyphs(arg, badCycles=b1, badGlyphs=b2, **kwArgs)
            
            if not arg:
                raise BadEditorOrGlyf()
            
            if b1 or b2:
                raise BadOrCircularComponents()
        
        currMatrix = kwArgs.get('currMatrix', None)
        e = kwArgs['editor']
        glyfTable = e.glyf
        
        if currMatrix is None:
            currMatrix = matrix.Matrix()
        
        for piece in self.components:
            thisMatrix = currMatrix.multiply(piece.transformationMatrix)
            obj = glyfTable[piece.glyphIndex]
            
            if obj.isComposite:
                for t in obj.pieceIterator(
                  currMatrix = thisMatrix,
                  editor = e,
                  runCheck = False):
                    
                    yield t
            
            else:
                yield (obj.contours, thisMatrix)
    
    def pointCount(self, **kwArgs):
        """
        Returns the number of points in the (unnormalized) glyph. The following
        keyword arguments are supported:
        
            editor      An Editor-class object which is used to get the glyphs
                        representing the components. This is required.
            
            runCheck    A Boolean. If True, a circularity and bad-index check
                        will be run before doing the point count accumulation.
                        Default is True, for the first entry here; thereafter
                        the recursive calls pass this as False.
        
        This call may raise one of these exceptions:
        
            BadEditorOrGlyf
            BadOrCircularComponents
        """
        
        if kwArgs.pop('runCheck', True):
            arg, b1, b2 = set(), set(), set()
            kwArgs.pop('badCycles', None)
            kwArgs.pop('badGlyphs', None)
            
            self.allReferencedGlyphs(
              arg,
              badCycles = b1,
              badGlyphs = b2,
              **kwArgs)
            
            if not arg:
                raise BadEditorOrGlyf()
            
            if b1 or b2:
                raise BadOrCircularComponents()
        
        sum = 0
        editor = kwArgs['editor']
        glyfTable = editor.glyf
        
        for piece in self.components:
            sum += glyfTable[piece.glyphIndex].pointCount(
              runCheck = False,
              **kwArgs)
        
        return sum

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _cstv = ttcomponents._testingValues
    _stv = ttsimpleglyph._testingValues
    
    _testingValues = (
        TTCompositeGlyph(),
        
        TTCompositeGlyph(
          bounds = ttbounds._testingValues[2],
          components = _cstv[1],  # glyphs 100, 80
          hintBytes = utilities.fromhex("00 01")),
        
        TTCompositeGlyph(components=_cstv[2]),  # glyph 901
        TTCompositeGlyph(components=_cstv[3]),  # glyphs 902, 903
        TTCompositeGlyph(components=_cstv[4]),  # glyph 904
        TTCompositeGlyph(components=_cstv[5]))  # glyph 905
    
    class _FakeEditor:
        def __init__(self, g): self.glyf = g
        def get(self, key): return self.glyf
    
    _fakeGlyf_1 = {
      5: _testingValues[1],
      80: _stv[1],
      100: _stv[1]}
    
    _fakeEditor_1 = _FakeEditor(_fakeGlyf_1)
    
    _fakeGlyf_2 = {
      12: _testingValues[2]}  # note glyph 901 is missing
    
    _fakeEditor_2 = _FakeEditor(_fakeGlyf_2)
    
    _fakeGlyf_3 = {  # deeply nested example, no circularity
      12: _testingValues[2],
      901: _testingValues[3],
      902: _stv[1],
      903: _testingValues[4],
      904: _testingValues[5],
      905: _stv[1]}
    
    _fakeEditor_3 = _FakeEditor(_fakeGlyf_3)
    
    _fakeGlyf_4 = {  # deeply nested example, circularity
      12: _testingValues[2],
      901: _testingValues[3],
      902: _stv[1],
      903: _testingValues[4],
      904: _testingValues[5],
      905: _testingValues[2]}
    
    _fakeEditor_4 = _FakeEditor(_fakeGlyf_4)
    
    del _cstv, _stv, _FakeEditor

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
