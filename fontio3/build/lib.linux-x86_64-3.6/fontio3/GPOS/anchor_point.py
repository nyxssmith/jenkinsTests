#
# anchor_point.py
#
# Copyright © 2007-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for anchored locations, specified as FUnit deltas from an anchor point.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.glyf import ttcompositeglyph
from fontio3.GPOS import anchor_coord

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    r = True
    logger = kwArgs['logger']
    
    if obj.glyphIndex is not None:
        editor = kwArgs.get('editor')

        if editor is None:
            logger.error((
              'V0553',
              (),
              "Unable to validate Anchor_Point because "
              "no editor was specified."))
            
            return False

        if editor.reallyHas(b'glyf'):
            glyfTable = editor.glyf
        
        elif editor.reallyHas(b'CFF '):
            glyfTable = editor['CFF ']
        
        else:
            logger.error((
              'V0553',
              (),
              "Unable to validate Anchor_Point because there is "
              "no 'glyf' or 'CFF ' table."))
            
            return False        
        
        if obj.glyphIndex in glyfTable:
            thisGlyph = glyfTable[obj.glyphIndex]
        
        else:
            logger.error((
              'V0553',
              (obj.glyphIndex,),
              "Unable to validate Anchor_Point because the specified "
              "glyph index (%r) does not exist."))
            
            return False

        try:
            count = thisGlyph.pointCount(editor=editor)        
        
        except ttcompositeglyph.BadOrCircularComponents:
            logger.error((
              'V0553',
              (obj.glyphIndex,),
              "Unable to validate Anchor_Point because the specified "
              "glyph index (%d) is a composite which references unknown "
              "or circular component glyph indices."))
            
            return False
        
        try:
            if obj.pointIndex >= count:
                logger.error((
                  'V0320',
                  (obj.glyphIndex, count, obj.pointIndex),
                  "Glyph %d only contains %d points; point "
                  "index %d is out of range."))
                
                r = False
            
            testIndex = kwArgs.get('glyphIndex', None)
            
            if testIndex is not None and obj.glyphIndex != testIndex:
                logger.error((
                  'V0337',
                  (testIndex, obj.glyphIndex),
                  "The glyph index should be %d, but is %d."))
                
                r = False
        
        except (TypeError, ValueError):
            pass  # partial is done before item, so number might not be valid
        
        # Finally, we check that the point specified has coordinates that
        # actually match the explicitly provided coordinates.
        
        if r:  # don't do this check if something failed above
            if thisGlyph.isComposite:
                # TrueType composite
                assert b'CFF ' not in editor
                from fontio3.glyf import ttsimpleglyph
                
                simple = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(
                  thisGlyph,
                  editor = editor)
                
                cs = simple.contours
            
            else:
                # Either TrueType or CFF non-composite
                cs = thisGlyph.contours
            
            pi = obj.pointIndex
            contourIndex = 0
            
            while pi >= len(cs[contourIndex]):
                pi -= len(cs[contourIndex])
                contourIndex += 1
            
            p = cs[contourIndex][pi]
            
            if p.x != obj.x or p.y != obj.y:
                logger.warning((
                  'V1074',
                  (obj.pointIndex, obj.glyphIndex, p.x, p.y, obj.x, obj.y),
                  "Point %d in glyph %d has coordinates (%d, %d), "
                  "but the Anchor data in this object are (%d, %d)."))
    
    else:
        logger.warning((
          'V0319',
          (),
          "No glyph index specified to go along with the "
          "anchor point indices."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Anchor_Point(anchor_coord.Anchor_Coord):
    """
    Objects representing anchored locations, FUnit values only and a contour
    point.
    
    >>> _testingValues[0].pprint()
    x-coordinate: -40
    y-coordinate: 18
    Contour point index: 6
    Glyph index: 40
    
    >>> _testingValues[0].anchorKind
    'point'
    
    # A special case for objects of this type:
    >>> bool(Anchor_Point(0, 0, pointIndex=0, glyphIndex=None))
    True
    
    >>> logger = utilities.makeDoctestLogger("ivtest")
    >>> e = _fakeEditor()
    >>> _testingValues[0].isValid(logger=logger, editor=e)
    ivtest - WARNING - Point 6 in glyph 40 has coordinates (950, 750), but the Anchor data in this object are (-40, 18).
    True
    
    >>> _testingValues[4].isValid(logger=logger, editor=e)
    ivtest - ERROR - Glyph 40 only contains 8 points; point index 16 is out of range.
    False
    
    >>> _testingValues[5].isValid(logger=logger, editor=e)
    ivtest - ERROR - Unable to validate Anchor_Point because the specified glyph index (-5) does not exist.
    ivtest.[0] - ERROR - The value -4.5 is not an integer.
    ivtest.[1] - ERROR - The signed value 45000 does not fit in 16 bits.
    ivtest.glyphIndex - ERROR - The glyph index -5 cannot be used in an unsigned field.
    ivtest.pointIndex - ERROR - The point index 'x' is not a real number.
    False
    """
    
    #
    # Class definition variables
    #
    
    # Since we inherit from Anchor_Coord, we only need define the extra attrs
    
    seqSpec = dict(
        seq_validatefunc_partial = _validate)
    
    attrSpec = dict(
        pointIndex = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Contour point index",
            attr_renumberpointsdirect = True),
        
        glyphIndex = dict(
            attr_label = "Glyph index",
            attr_renumberdirect = True))
    
    attrSorted = ('pointIndex', 'glyphIndex')
    anchorKind = 'point'
    
    #
    # Methods
    #
    
    # Point zero with a (0, 0) delta is still a valid record.
    def __bool__(self): return True
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0002 FFD8 0012 0006                      |........        |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("H3h", 2, self.x, self.y, self.pointIndex)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Point object, including validation of the input
        source.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> e = _fakeEditor()
        >>> s = _testingValues[0].binaryString()
        >>> fvb = Anchor_Point.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger, editor=e, glyphIndex=40)
        test.anchor_point - DEBUG - Walker has 8 remaining bytes.
        
        >>> fvb(s[:7], logger=logger, editor=e, glyphIndex=40)
        test.anchor_point - DEBUG - Walker has 7 remaining bytes.
        test.anchor_point - ERROR - Insufficient bytes.
        
        >>> fvb(s[2:8] + s[0:2], logger=logger, editor=e, glyphIndex=40)
        test.anchor_point - DEBUG - Walker has 8 remaining bytes.
        test.anchor_point - ERROR - Was expecting format 2, but got 65496 instead.
        """
        
        logger = kwArgs.get('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('anchor_point')
        else:
            logger = logger.getChild('anchor_point')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format != 2:
            logger.error((
              'V0002',
              (format,),
              "Was expecting format 2, but got %d instead."))
            
            return None
        
        glyphIndex = kwArgs.get('glyphIndex', None)
        
        if glyphIndex is None:
            logger.warning((
              'V0319',
              (),
              "No glyph index specified to go along with the "
              "anchor point indices."))
        
        x, y, p = w.unpack("2hH")
        return cls(x, y, pointIndex=p, glyphIndex=glyphIndex)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Anchor_Point object from the specified walker.
        
        >>> atp = _testingValues[0]
        >>> atp == Anchor_Point.frombytes(atp.binaryString(), glyphIndex=40)
        True
        """
        
        format = w.unpack("H")
        
        if format != 2:
            raise ValueError("Unknown format for Anchor_Point: %d" % (format,))
        
        x, y, p = w.unpack("2hH")
        return cls(x, y, pointIndex=p, **utilities.filterKWArgs(cls, kwArgs))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _fakeEditor():
        from fontio3.glyf import glyf, ttsimpleglyph
        
        e = utilities.fakeEditor(0x10000)
        e.glyf = glyf.Glyf()
        e.glyf[40] = ttsimpleglyph._testingValues[2]
        return e
    
    _testingValues = (
        Anchor_Point(-40, 18, pointIndex=6, glyphIndex=40),
        Anchor_Point(0, 0, pointIndex=4, glyphIndex=99),
        Anchor_Point(0, 48, pointIndex=0, glyphIndex=16),
        Anchor_Point(-10, 0, pointIndex=9, glyphIndex=16),
        Anchor_Point(-40, 18, pointIndex=16, glyphIndex=40),
        
        # bad entries start here
        
        Anchor_Point(-4.5, 45000, pointIndex='x', glyphIndex=-5))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
