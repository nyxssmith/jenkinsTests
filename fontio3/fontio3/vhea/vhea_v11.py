#
# vhea_v11.py
#
# Copyright © 2004-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'vhea' tables, version 1.1.
"""

# Other imports
from fontio3.CFF import cffcompositeglyph
from fontio3.fontdata import simplemeta
from fontio3.glyf import ttcompositeglyph, ttsimpleglyph

# -----------------------------------------------------------------------------

#
# Private functions
#

def _hasContours(obj, **kwArgs):
    """
    Convenience function to return boolean as to whether a glyph ('glyf' or
    'CFF ') has "contours"...meaning it's either a simple glyph with contours
    or a non-empty composite glyph whose components have contours.

    'editor' kwArg is required.
    """
    editor = kwArgs.get('editor')

    if obj and getattr(obj, 'isComposite', False):
        if isinstance(obj, ttcompositeglyph.TTCompositeGlyph):
            sg = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(obj, editor=editor)
            return sg and getattr(sg, 'contours', None)
        elif isinstance(obj, cffcompositeglyph.CFFCompositeGlyph):
            bg = editor[b'CFF '].get(obj.baseGlyph)
            ag = editor[b'CFF '].get(obj.accentGlyph)
            return getattr(ag, 'contours', None) and getattr(bg, 'contours', None)
        else:
            return False
    else:
        return obj and getattr(obj, 'contours', None)


def _recalc(obj, **kwArgs):
    """
    Combined recalculation. Although it is not explicitly stated in the spec,
    we assume the calculation of minTopSidebearing, minBottomSidebearing, and
    yMaxExtent should be done as the hhea table, i.e. ignoring glyphs with no
    contours.

    'editor' kwArg is required and editor must contain 'vmtx' and one of
    {'glyf', 'CFF '}.
    """
    editor = kwArgs['editor']
    
    if editor is None:
        raise NoEditor()
    
    if not editor.reallyHas(b'vmtx'):
        raise NoVmtx()

    if editor.reallyHas(b'glyf'):
        glyphTbl = editor.glyf
    elif editor.reallyHas(b'CFF '):
        glyphTbl = editor['CFF ']
    else:
        raise NoGlyf()

    obj2 = obj.__copy__()
    vmtxTable = editor.vmtx

    newMaxAH = 0
    newMinTSB = 32767
    newMinBSB = 32767
    newMaxExt = -32767

    for i, d in glyphTbl.items():
        mtxEntry = vmtxTable.get(i)

        if mtxEntry:
            newMaxAH = max(newMaxAH, mtxEntry.advance)

        if d:
            if mtxEntry and _hasContours(d, editor=editor):
                bounds = d.bounds
                boxHeight = bounds.yMax - bounds.yMin

                newMinTSB = min(newMinTSB, mtxEntry.sidebearing)

                newMinBSB = min(
                    newMinBSB,
                    mtxEntry.advance - mtxEntry.sidebearing - boxHeight)

                newMaxExt = max(
                    newMaxExt,
                    mtxEntry.sidebearing + boxHeight)


    obj2.advanceHeightMax = newMaxAH
    obj2.minTopSidebearing = newMinTSB
    obj2.minBottomSidebearing = newMinBSB
    obj2.yMaxExtent = newMaxExt

    return obj != obj2, obj2

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'vhea' table because the Editor is "
          "missing or empty."))
        
        return False
    
    r = True
    
    if obj.vertTypoAscender < 0:
        logger.warning((
          'V0280',
          (obj.vertTypoAscender,),
          "The vertTypoAscender %d is negative; it should be negative."))
    
    if obj.vertTypoDescender > 0:
        logger.warning((
          'V0281',
          (obj.vertTypoDescender,),
          "The vertTypoDescender %d is positive; it should be negative."))
    
    if obj.vertTypoLineGap:
        logger.error((
          'V0282',
          (obj.vertTypoLineGap,),
          "The vertTypoLineGap is %d, but zero is required."))
        
        r = False
    
    if obj.metricDataFormat:
        logger.error((
          'E2600',
          (obj.metricDataFormat,),
          "The metricDataFormat is %d, but zero is required."))
        
        r = False
    
    else:
        logger.info((
          'P2600',
          (),
          "The metricDataFormat is correctly set to zero."))
    
    if not editor.reallyHas(b'vmtx'):
        logger.critical((
          'V0283',
          (),
          "There is no 'vmtx' table in the font!"))
        
        # We short-circuit the rest of validation if there is no 'vmtx' table,
        # since the rest of this method depends on its presence.
        
        return False
    
    changed, obj2 = _recalc(obj, **kwArgs)
    
    if changed:
        if obj.advanceHeightMax != obj2.advanceHeightMax:
            logger.error((
              'V0284',
              (obj2.advanceHeightMax, obj.advanceHeightMax),
              "The advanceHeightMax value should be %d, but the actual value "
              "is %d."))
            
            r = False
        
        if obj.minTopSidebearing != obj2.minTopSidebearing:
            logger.error((
              'V0285',
              (obj2.minTopSidebearing, obj.minTopSidebearing),
              "The minTopSidebearing value should be %d, but the actual "
              "value is %d."))
            
            r = False
        
        if obj.yMaxExtent != obj2.yMaxExtent:
            logger.error((
              'V0286',
              (obj2.yMaxExtent, obj.yMaxExtent),
              "The yMaxExtent value should be %d, but the actual value "
              "is %d."))
            
            r = False
        
        if obj.minBottomSidebearing != obj2.minBottomSidebearing:
            logger.error((
              'V0287',
              (obj2.minBottomSidebearing, obj.minBottomSidebearing),
              "The minBottomSidebearing value should be %d, but the actual "
              "value is %d."))
            
            r = False
    
    countWithCompacting = editor.vmtx.getLongMetricsCount(True)
    countWithoutCompacting = editor.vmtx.getLongMetricsCount(False)
    
    if countWithCompacting == countWithoutCompacting:
        if obj.numLongMetrics == countWithCompacting:
            logger.info((
              'V0289',
              (obj.numLongMetrics,),
              "The font's %d metrics are all long."))
        
        else:
            logger.error((
              'V0291',
              (obj.numLongMetrics,
               countWithCompacting, countWithoutCompacting),
              "The numLongMetrics value of %d matches neither the expected "
              "compacted count (%d) nor the uncompacted count (%d)."))
            
            r = False
    
    elif obj.numLongMetrics == countWithCompacting:
        if not editor.reallyHas(b'maxp'):
            logger.error((
              'V0553',
              (),
              "Cannot complete validation of 'vhea' table because the "
              "'maxp' table is missing or empty."))
            
            r = False
        
        else:
            logger.info((
              'V0288',
              (countWithCompacting,
               editor.maxp.numGlyphs - countWithCompacting),
              "The font has %d long metrics, and %d compacted "
              "monospace metrics."))
    
    elif obj.numLongMetrics == countWithoutCompacting:
        shortCount = countWithoutCompacting - countWithCompacting
        
        logger.warning((
          'V0290',
          (shortCount,),
          "All metrics are long, although the final %d could be shared."))
    
    else:
        logger.error((
          'V0291',
          (obj.numLongMetrics, countWithCompacting, countWithoutCompacting),
          "The numLongMetrics value of %d matches neither the expected "
          "compacted count (%d) nor the uncompacted count (%d)."))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class NoEditor(ValueError): pass
class NoGlyf(ValueError): pass
class NoVmtx(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Vhea(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing TrueType 'vhea' tables. These are simple collections
    of attributes.
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        vertTypoAscender = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Ascent",
            attr_scaledirect = True,
            attr_representsx = True),
        
        vertTypoDescender = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Descent",
            attr_scaledirect = True,
            attr_representsx = True),
        
        vertTypoLineGap = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Line gap (leading)",
            attr_scaledirect = True,
            attr_representsx = True),
        
        advanceHeightMax = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum advance height",
            attr_scaledirect = True,
            attr_representsy = True),
        
        minTopSidebearing = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum top sidebearing",
            attr_scaledirect = True,
            attr_representsy = True),
        
        minBottomSidebearing = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Minimum bottom sidebearing",
            attr_scaledirect = True,
            attr_representsy = True),
        
        yMaxExtent = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Maximum extent in y",
            attr_scaledirect = True,
            attr_representsy = True),
        
        caretSlopeRise = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Caret slope rise"),
        
        caretSlopeRun = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Caret slope run"),
        
        caretOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Caret offset",
            attr_scaledirect = True,
            attr_representsy = True),
        
        metricDataFormat = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Metric data format"),
        
        numLongMetrics = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Number of long metrics"))
    
    attrSorted = (
      'vertTypoAscender',
      'vertTypoDescender',
      'vertTypoLineGap',
      'advanceHeightMax',
      'minTopSidebearing',
      'minBottomSidebearing',
      'yMaxExtent',
      'caretSlopeRise',
      'caretSlopeRun',
      'caretOffset',
      'metricDataFormat',
      'numLongMetrics')
    
    version = 0x11000  # class constant
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Vhea object to the specified LinkedWriter.
        
        >>> utilities.hexdump(Vhea().binaryString())
               0 | 0001 1000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0001 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0001                                |....            |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add(
          "L3hH11hH",
          self.version,
          self.vertTypoAscender,
          self.vertTypoDescender,
          self.vertTypoLineGap,
          self.advanceHeightMax,
          self.minTopSidebearing,
          self.minBottomSidebearing,
          self.yMaxExtent,
          self.caretSlopeRise,
          self.caretSlopeRun,
          self.caretOffset,
          0,
          0,
          0,
          0,
          self.metricDataFormat,
          self.numLongMetrics)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Vhea object from the data in the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('vhea')
        else:
            logger = logger.getChild('vhea')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() != 36:  # 'vhea' is fixed-length
            logger.error((
              'E2700',
              (w.length(),),
              "The length of the 'vhea' table should be 36 bytes, "
              "but is incorrectly %d bytes instead."))
            
            return None
        
        okToReturn = True
        t1 = w.unpack("L3hH6h")
        
        if t1[0] != cls.version:
            logger.error((
              'V0002',
              (t1[0],),
              "Unexpected version 0x%08X."))
            
            return None
        
        t2 = w.group("H", 4)
        
        if any(t2):
            logger.error((
              'E2601',
              (),
              "One or more reserved fields not set to zero."))
            
            okToReturn = False
        
        t = t1 + w.unpack("hH")
        
        r = cls(
          vertTypoAscender = t[1],
          vertTypoDescender = t[2],
          vertTypoLineGap = t[3],
          advanceHeightMax = t[4],
          minTopSidebearing = t[5],
          minBottomSidebearing = t[6],
          yMaxExtent = t[7],
          caretSlopeRise = t[8],
          caretSlopeRun = t[9],
          caretOffset = t[10],
          metricDataFormat = t[11],
          numLongMetrics = t[12])
        
        return (r if okToReturn else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Vhea object from the data in the specified walker.
        
        >>> h = Vhea()
        >>> h.caretOffset = 10
        >>> h == Vhea.frombytes(h.binaryString())
        True
        """
        
        t = w.unpack("L3hH6h8xhH")
        
        if t[0] != cls.version:
            raise ValueError(
              "Expected version 1.0; got 0x%08X instead." % (t[0],))
        
        return cls(
          vertTypoAscender = t[1],
          vertTypoDescender = t[2],
          vertTypoLineGap = t[3],
          advanceHeightMax = t[4],
          minTopSidebearing = t[5],
          minBottomSidebearing = t[6],
          yMaxExtent = t[7],
          caretSlopeRise = t[8],
          caretSlopeRun = t[9],
          caretOffset = t[10],
          metricDataFormat = t[11],
          numLongMetrics = t[12])

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
