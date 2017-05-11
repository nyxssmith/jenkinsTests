#
# maxp_tt.py
#
# Copyright © 2004-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TrueType 'maxp' tables.
"""

# System imports
import logging
import sys

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.hints import hints_tt

# -----------------------------------------------------------------------------

#
# Private functions
#

def _deepwalk(n, depth, simpleCount, glyfTable):
    """
    Counts points and contours for both simple and compound glyphs.
    """
    
    retDepth = depth
    d = glyfTable[n]
    
    if d.isComposite:
        totalPoints = totalContours = 0
        simpleCount = max(len(d.components), simpleCount)
        
        for c in d.components:
            nPoints, nContours, newDepth, simpleCount = _deepwalk(
              c.glyphIndex,
              depth + 1,
              simpleCount,
              glyfTable)
            
            totalPoints += nPoints
            totalContours += nContours
            
            if newDepth > retDepth:
                retDepth = newDepth
        
        return totalPoints, totalContours, retDepth, simpleCount
    
    return (
      sum([len(c) for c in d.contours]),
      len(d.contours),
      retDepth,
      max(1, simpleCount))

def _recalc(obj, **kwArgs):
    """
    """
    
    results = kwArgs.pop('results', {})
    e = kwArgs.get('editor', None)
    
    if e is None:
        raise NoEditor()
    
    if not e.reallyHas(b'glyf'):
        raise NoGlyf()
    
    isSpark = b'SPRK' in e
    obj2 = type(obj)()  # zeroes everything
    obj2.numGlyphs = max(e.glyf) + 1
    obj2.maxFunctionDefs = (max(e.fpgm) + 1 if e.reallyHas(b'fpgm') else 0)
    
    hasJumps = False
    badGlyphs = set()
    
    for i, d in e.glyf.items():
        if not d:
            continue
        
        if d.isComposite:
            cBad, gBad = set(), set()
            
            d.allReferencedGlyphs(
              set(),
              badCycles = cBad,
              badGlyphs = gBad,
              editor = e)
            
            if cBad or gBad:
                badGlyphs.update(cBad | gBad)
                continue
            
            nPoints, nContours, depth, simpleCount = _deepwalk(i, 0, 0, e.glyf)
            obj2.maxComponentPoints = max(obj2.maxComponentPoints, nPoints)
            obj2.maxComponentDepth = max(obj2.maxComponentDepth, depth)
            
            obj2.maxComponentContours = max(
              obj2.maxComponentContours,
              nContours)
            
            obj2.maxComponentElements = max(
              obj2.maxComponentElements,
              simpleCount)
        
        else:
            obj2.maxPoints = max(
              obj2.maxPoints,
              sum(len(c) for c in d.contours))
            
            obj2.maxContours = max(obj2.maxContours, len(d.contours))
        
        h = d.hintBytes
        
        obj2.maxSizeOfInstructions = max(
          obj2.maxSizeOfInstructions,
          len(h))
          
        if h and (not isSpark) and hints_tt.Hints.frombytes(h).containsJumps():
            hasJumps = True
    
    if badGlyphs:
        results['badGlyphs'] = badGlyphs
        raise BadGlyphs()
    
    if isSpark:
        obj2.maxZones = obj.maxZones
        obj2.maxTwilightPoints = obj.maxTwilightPoints
        obj2.maxStorage = obj.maxStorage
        obj2.maxStackElements = obj.maxStackElements
        results['hasJumps'] = False
    
    else:
        if (not hasJumps) and e.reallyHas(b'prep') and e.prep.containsJumps():
            hasJumps = True

        if (
          (not hasJumps) and
          e.reallyHas(b'fpgm') and
          any(x.containsJumps() for x in e.fpgm.values())):
        
            hasJumps = True
    
        if e.reallyHas(b'prep') or obj2.maxSizeOfInstructions:
            logger = kwArgs.get('logger', logging.getLogger())
        
            try:
                oldLevel = logger.getEffectiveLevel()
                logger.setLevel(60)
                indirectLevel = False
        
            except AttributeError:
                oldLevel = logger.logger.getEffectiveLevel()
                logger.logger.setLevel(60)
                indirectLevel = True
        
            from fontio3.hints import ttstate
            t = ttstate.TrueTypeState.fromeditor(e)
            t._validationFailed = False
            t.runPreProgram(logger=logger)
            m = t.statistics.maxima.__copy__()
        
            for i in e.glyf:
                h, tGlyph = t.runGlyphSetup(i)
            
                if h:
                    h.run(tGlyph, logger=logger)
                    m.combine(tGlyph.statistics.maxima)
        
            if indirectLevel:
                logger.logger.setLevel(oldLevel)
            else:
                logger.setLevel(oldLevel)
        
            obj2.maxZones = 1 + (m.tzPoint != -1)
            obj2.maxTwilightPoints = 1 + m.tzPoint
            obj2.maxStorage = 1 + m.storage
            obj2.maxStackElements = max(m.stack, kwArgs.get('minStack', 100))
    
        results['hasJumps'] = hasJumps

        if hasJumps:
            # recalc of some fields is currently not reliable when font contains
            # jump hints, so take max(ourRecalculated, existingValue):
            obj2.maxZones = max(obj.maxZones, obj2.maxZones)
            obj2.maxTwilightPoints = max(obj.maxTwilightPoints, obj2.maxTwilightPoints)
            obj2.maxStorage = max(obj.maxStorage, obj2.maxStorage)
            obj2.maxStackElements = max(obj.maxStackElements, obj2.maxStackElements)

    return obj != obj2, obj2

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'maxp' table because the Editor is missing."))
        
        return False
    
    if not editor.reallyHas(b'glyf'):
        logger.error((
          'E1907',
          (),
          "Font has version 1.0 'maxp' table, "
          "but no 'glyf' table is present."))
        
        return False
    
    if editor.reallyHas(b'CFF '):
        logger.error((
          'E1906',
          (),
          "Font has version 1.0 'maxp' table, "
          "but a 'CFF ' table is present."))
        
        return False
    
    results = {}
    kwArgs.pop('results', None)

    try:
        changed, goodObj = _recalc(obj, results=results, **kwArgs)
    
    except BadGlyphs:
        logger.error((
          'V0555',
          (sorted(results['badGlyphs']),),
          "The following glyphs had improperly constructed composite "
          "information, and could not be used in validating the 'maxp' "
          "table: %s"))
        
        return False
    
    except NoGlyf:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'maxp' table because the 'glyf' "
          "table is missing or empty."))
        
        return False
    
    except:
        type, value = sys.exc_info()[0:2]
        
        logger.error((
          'V0246',
          (type.__name__, value),
          'Encountered an error during validation: %s: %s'))
        
        return False
    
    hasJumps = results['hasJumps']
    r = True
    
    if not changed:
        return r
    
    if obj.numGlyphs != goodObj.numGlyphs:
        logger.error((
          'V0235',
          (goodObj.numGlyphs, obj.numGlyphs),
          "The numGlyphs should be %d, but is %d."))
        
        r = False
    
    if obj.maxPoints != goodObj.maxPoints:
        if obj.maxPoints < goodObj.maxPoints:
            logger.error((
              'V0236',
              (goodObj.maxPoints, obj.maxPoints),
              "The maxPoints should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0248',
              (obj.maxPoints, goodObj.maxPoints),
              "The maxPoints value is %d, which is larger than is needed. "
              "It may be reduced to %d."))
    
    if obj.maxContours != goodObj.maxContours:
        if obj.maxContours < goodObj.maxContours:
            logger.error((
              'V0237',
              (goodObj.maxContours, obj.maxContours),
              "The maxContours should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0249',
              (obj.maxContours, goodObj.maxContours),
              "The maxContours value is %d, which is larger than is needed. "
              "It may be reduced to %d."))
    
    if obj.maxComponentPoints != goodObj.maxComponentPoints:
        if obj.maxComponentPoints < goodObj.maxComponentPoints:
            logger.error((
              'V0238',
              (goodObj.maxComponentPoints, obj.maxComponentPoints),
              "The maxComponentPoints should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0250',
              (obj.maxComponentPoints, goodObj.maxComponentPoints),
              "The maxComponentPoints value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if obj.maxComponentContours != goodObj.maxComponentContours:
        if obj.maxComponentContours < goodObj.maxComponentContours:
            logger.error((
              'V0239',
              (goodObj.maxComponentContours, obj.maxComponentContours),
              "The maxComponentContours should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0251',
              (obj.maxComponentContours, goodObj.maxComponentContours),
              "The maxComponentContours value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if obj.maxFunctionDefs != goodObj.maxFunctionDefs:
        if obj.maxFunctionDefs < goodObj.maxFunctionDefs:
            logger.error((
              'V0240',
              (goodObj.maxFunctionDefs, obj.maxFunctionDefs),
              "The maxFunctionDefs should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0252',
              (obj.maxFunctionDefs, goodObj.maxFunctionDefs),
              "The maxFunctionDefs value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    rawPrep = editor.getRawTable(b'prep')
    prepLen = (0 if rawPrep is None else len(rawPrep))
    rawFpgm = editor.getRawTable(b'fpgm')
    fpgmLen = (0 if rawFpgm is None else len(rawFpgm))
    nonGlyphMax = max(prepLen, fpgmLen)
    combined = max(goodObj.maxSizeOfInstructions, nonGlyphMax)
    
    if obj.maxSizeOfInstructions == goodObj.maxSizeOfInstructions:
        if obj.maxSizeOfInstructions < nonGlyphMax:
            logger.warning((
              'V0270',
              (obj.maxSizeOfInstructions, nonGlyphMax),
              "The maxSizeOfInstructions, %d, correctly matches the size "
              "of the glyph hints, but is less than %d, the larger of the "
              "sizes of the 'fpgm' and 'prep' tables."))
        
        else:
            logger.info((
              'V0268',
              (),
              "The maxSizeOfInstructions correctly matches the size of the "
              "largest glyph instructions."))
    
    else:
        if obj.maxSizeOfInstructions == combined:
            logger.info((
              'V0269',
              (),
              "The maxSizeOfInstructions correctly matches the maximum "
              "of the largest glyph hints, size of prep, and size of fpgm."))
        
        elif obj.maxSizeOfInstructions < goodObj.maxSizeOfInstructions:
            logger.error((
              'V0241',
              (goodObj.maxSizeOfInstructions, obj.maxSizeOfInstructions),
              "The maxSizeOfInstructions should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0271',
              (obj.maxSizeOfInstructions,
               goodObj.maxSizeOfInstructions,
               nonGlyphMax),
              "The maxSizeOfInstructions %d does not match either the font's "
              "actual largest glyph hint size (%d) nor the larger of the "
              "sizes of the 'fpgm' and 'prep' tables (%d)."))
    
    if obj.maxComponentElements != goodObj.maxComponentElements:
        if obj.maxComponentElements < goodObj.maxComponentElements:
            logger.error((
              'V0242',
              (goodObj.maxComponentElements, obj.maxComponentElements),
              "The maxComponentElements should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0254',
              (obj.maxComponentElements, goodObj.maxComponentElements),
              "The maxComponentElements value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if obj.maxComponentDepth != goodObj.maxComponentDepth:
        if obj.maxComponentDepth < goodObj.maxComponentDepth:
            logger.error((
              'V0243',
              (goodObj.maxComponentDepth, obj.maxComponentDepth),
              "The maxComponentDepth should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0255',
              (obj.maxComponentDepth, goodObj.maxComponentDepth),
              "The maxComponentDepth value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if hasJumps:
        logger.warning(('V0300', (), "Font has jump hints."))
    
    if obj.maxZones != goodObj.maxZones:
        if obj.maxZones < goodObj.maxZones:
            logger.error((
              'V0272',
              (goodObj.maxZones, obj.maxZones),
              "The maxZones value should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0273',
              (obj.maxZones, goodObj.maxZones),
              "The maxZones value is %d, which is larger than is needed. "
              "It may be reduced to %d."))
    
    if obj.maxTwilightPoints != goodObj.maxTwilightPoints:
        if obj.maxTwilightPoints < goodObj.maxTwilightPoints:
            logger.error((
              'V0274',
              (goodObj.maxTwilightPoints, obj.maxTwilightPoints),
              "The maxTwilightPoints value should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0275',
              (obj.maxTwilightPoints, goodObj.maxTwilightPoints),
              "The maxTwilightPoints value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if obj.maxStorage != goodObj.maxStorage:
        if obj.maxStorage < goodObj.maxStorage:
            logger.error((
              'V0276',
              (goodObj.maxStorage, obj.maxStorage),
              "The maxStorage value should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0277',
              (obj.maxStorage, goodObj.maxStorage),
              "The maxStorage value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    if obj.maxStackElements != goodObj.maxStackElements:
        if obj.maxStackElements < goodObj.maxStackElements:
            logger.error((
              'V0278',
              (goodObj.maxStackElements, obj.maxStackElements),
              "The maxStackElements value should be %d, but is %d."))
            
            r = False
        
        else:
            logger.warning((
              'V0279',
              (obj.maxStackElements, goodObj.maxStackElements),
              "The maxStackElements value is %d, which is larger than is "
              "needed. It may be reduced to %d."))
    
    return r

# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class BadGlyphs(ValueError): pass
class NoEditor(ValueError): pass
class NoGlyf(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Maxp_TT(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'maxp' tables for TrueType fonts. These are
    simple objects with various attributes.
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        numGlyphs = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of glyphs"),
        
        maxPoints = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of points in any non-composite glyph"),
        
        maxContours = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of contours in any non-composite glyph"),
        
        maxComponentPoints = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of points in any composite glyph"),
        
        maxComponentContours = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of contours in any composite glyph"),
        
        maxZones = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Number of zones used"),
        
        maxTwilightPoints = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of points in zone "
                         "0 (the twilight zone)"),
        
        maxStorage = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of storage locations used"),
        
        maxFunctionDefs = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of function definitions (FDEFs)"),
        
        maxInstructionDefs = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of instruction definitions (IDEFs)"),
        
        maxStackElements = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Number of stack elements used"),
        
        maxSizeOfInstructions = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Largest size of any glyph hints (in bytes)"),
        
        maxComponentElements = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of components in any composite glyph"),
        
        maxComponentDepth = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Most number of nesting levels in any "
                         "composite glyph"))
    
    attrSorted = (
      'numGlyphs',
      'maxPoints',
      'maxContours',
      'maxComponentPoints',
      'maxComponentContours',
      'maxZones',
      'maxTwilightPoints',
      'maxStorage',
      'maxFunctionDefs',
      'maxInstructionDefs',
      'maxStackElements',
      'maxSizeOfInstructions',
      'maxComponentElements',
      'maxComponentDepth')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Maxp_TT object to the specified
        LinkedWriter.
        
        >>> h = utilities.hexdump
        >>> h(_testingValues[0].binaryString())
               0 | 0001 0000 0000 0000  0000 0000 0000 0001 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        
        >>> h(_testingValues[1].binaryString())
               0 | 0001 0000 0258 0000  0000 0000 0000 0001 |.....X..........|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", 0x10000)
        d = self.__dict__
        w.addGroup("H", (d[k] for k in self._ATTRSORT))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Maxp. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Maxp_TT.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.maxp - DEBUG - Walker has 32 remaining bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.maxp - DEBUG - Walker has 2 remaining bytes.
        test.maxp - ERROR - Insufficient bytes.
        
        >>> fvb(s[3:8], logger=logger)
        test.maxp - DEBUG - Walker has 5 remaining bytes.
        test.maxp - ERROR - Invalid format (0x00025800).
        
        >>> fvb(s[:16], logger=logger)
        test.maxp - DEBUG - Walker has 16 remaining bytes.
        test.maxp - ERROR - Insufficient bytes for content.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('maxp')
        else:
            logger = logger.getChild('maxp')
        
        endOfWalker = w.length()
        
        logger.debug((
          'V0001',
          (endOfWalker,),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L")
        
        if version != 0x10000:
            logger.error(('V0002', (version,), "Invalid format (0x%08X)."))
            return None
        
        if w.length() < 28:
            logger.error(('E1902', (), "Insufficient bytes for content."))
            return None
        
        t = w.unpack("14H")
        return cls(*t)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Maxp_TT object from the data in the specified walker.
        
        >>> fb = Maxp_TT.frombytes
        >>> _testingValues[0] == fb(_testingValues[0].binaryString())
        True
        
        >>> _testingValues[1] == fb(_testingValues[1].binaryString())
        True
        """
        
        t = w.unpack("L14H")
        assert t[0] == 0x10000
        return cls(*t[1:])

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Maxp_TT(),
        Maxp_TT(numGlyphs=600))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
