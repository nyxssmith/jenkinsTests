#
# hhea.py
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for 'hhea' tables.
"""

# System imports
import math

# Other imports
from fontio3 import utilities

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
            sg = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(
              obj,
              editor = editor)
            
            return sg and getattr(sg, 'contours', None)
        
        elif isinstance(obj, cffcompositeglyph.CFFCompositeGlyph):
            bg = editor[b'CFF '].get(obj.baseGlyph)
            ag = editor[b'CFF '].get(obj.accentGlyph)
            
            return (
              getattr(ag, 'contours', None) and
              getattr(bg, 'contours', None))
        
        else:
            return False
    
    else:
        return obj and getattr(obj, 'contours', None)

def _recalc(obj, **kwArgs):
    """
    Combined recalculation. Per spec, ignores glyphs with no contours for
    calculation of minLeftSidebearing, minRightSidebearing, and xMaxExtent.

    'editor' kwArg is required and editor must contain 'hmtx' and one of
    {'glyf', 'CFF '}.
    """
    
    editor = kwArgs.get('editor')

    if editor is None:
        raise NoEditor()

    if not editor.reallyHas(b'hmtx'):
        raise NoHmtx()

    if editor.reallyHas(b'glyf'):
        glyphTbl = editor.glyf
    elif editor.reallyHas(b'CFF '):
        glyphTbl = editor['CFF ']
    else:
        raise NoGlyf()

    obj2 = obj.__copy__()
    hmtxTable = editor.hmtx
    newMaxAW = 0
    newMinLSB = 32767
    newMinRSB = 32767
    newMaxExt = -32767

    for i, d in glyphTbl.items():
        mtxEntry = hmtxTable.get(i)

        if mtxEntry:
            newMaxAW = max(newMaxAW, mtxEntry.advance)

        if d:
            if mtxEntry and _hasContours(d, editor=editor):
                bounds = d.bounds
                boxWidth = bounds.xMax - bounds.xMin

                newMinLSB = min(newMinLSB, mtxEntry.sidebearing)

                newMinRSB = min(
                    newMinRSB,
                    mtxEntry.advance - mtxEntry.sidebearing - boxWidth)

                newMaxExt = max(
                    newMaxExt,
                    mtxEntry.sidebearing + boxWidth)

    obj2.advanceWidthMax = newMaxAW
    obj2.minLeftSidebearing = newMinLSB
    obj2.minRightSidebearing = newMinRSB
    obj2.xMaxExtent = newMaxExt

    return obj2 != obj, obj2

def _validate(obj, **kwArgs):
    """
    Validate entire table contents...doing this with a single .recalculated()
    on the whole table, rather than multiple individual field recalculations.
    """

    logger = kwArgs['logger']
    editor = kwArgs['editor']

    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'hhea' table because no Editor is present."))

        return False

    r = True

    # Ascender/Descender/LineGap

    if (obj.ascent < 0):
        logger.error((
          'E1414',
          (obj.ascent,),
          "The Ascender value must be greater than zero (actual: %d)"))

        r = False

    else:
        logger.info((
          'P1409',
          (),
          "The Ascender value is greater than zero"))

    if obj.descent > 0:
        logger.error((
          'E1415',
          (obj.descent,),
          "The Descender value must be less than zero (actual: %d)"))

        r = False

    else:
        logger.info((
          'P1411',
          (),
          "The Descender value is less than zero"))

    if editor.reallyHas(b'OS/2'):
        os2 = editor[b'OS/2']

        if obj.ascent != os2.usWinAscent:
            logger.warning((
              'W1405',
              (obj.ascent, os2.usWinAscent),
              "Ascender (%d) is different than OS/2.usWinAscent "
              "(%d). Different line heights on Windows vs Apple"))

        if obj.descent != -os2.usWinDescent:
            logger.warning((
              'W1406',
              (obj.descent, os2.usWinDescent),
              "Descender (%d) is different than -OS/2.usWinDescent "
              "(-%d). Different line heights on Windows vs Apple"))

    else:
        logger.warning((
          'W0050',
          (),
          "Cannot perform hhea-to-OS/2 metrics tests because "
          "the OS/2 table is missing"))

    # "must be":

    if obj.metricDataFormat:
        logger.error((
          'E1401',
          (obj.metricDataFormat,),
          "The metricDataFormat field (%d) is not 0"))

        r = False

    else:
        logger.info((
          'P1401',
          (),
          "The metricDataFormat field is 0"))

    # caret slope consistency checks
    # calculation adapted from MS Font Validator

    actualAngle = (
      (math.atan2(obj.caretSlopeRise, obj.caretSlopeRun)) *
      (180 / math.pi))

    if editor.reallyHas(b'post'):
        if editor.post.header.italicAngle:
            # In the following line, the tolerance is from MS Font Validator:
            expectedAngle = 90 + editor.post.header.italicAngle

            if abs(actualAngle - expectedAngle) >= 1:
                logger.error((
                  'E1411',
                  (obj.caretSlopeRise,
                   obj.caretSlopeRun,
                   actualAngle,
                   editor.post.header.italicAngle),
                  "The caretSlopeRise/caretSlopeRun (%d/%d) angle (%5.1f) "
                  "is not consistent with post.italicAngle (%5.1f)"))

                r = False

            else:
                logger.info((
                  'P1408',
                  (),
                  "The caretSlopeRise/caretSlopeRun angle is "
                  "consistent with post.italicAngle"))

            if not obj.caretSlopeRun:
                logger.error((
                  'E1413',
                  (editor.post.header.italicAngle,),
                  "The caretSlopeRun is zero, but the post.italicAngle "
                  "is nonzero (%5.1f)"))

        else:
            # caretSlopeRun should == 0 for upright
            if obj.caretSlopeRun:
                logger.error((
                  'E1412',
                  (obj.caretSlopeRun,),
                  "The caretSlopeRun is non-zero (%d) but the "
                  "post.italicAngle is zero"))

                r = False

            if obj.caretOffset:
                logger.warning((
                  'V0256',
                  (obj.caretOffset,),
                  "The caretOffset (%d) is non-zero but the "
                  "post.italicAngle is zero"))

    if not editor.reallyHas(b'head'):
        logger.error((
          'V0553',
          (),
          "Unable to complete 'hhea' validation because the 'head' table "
          "is missing or empty."))

        r = False

    else:
        headTbl = editor.head
        
        if actualAngle != 90:
            if not headTbl.macStyle.italic:
                logger.warning((
                  'V0258',
                  (actualAngle,),
                  "The caretSlopeRise/caretSlopeRun angle (%5.1f) "
                  "indicates italic, but head.macStyle.italic is False"))

            else:
                logger.info((
                  'V0259',
                  (),
                  "The caretSlopeRise/caretSlopeRun angle is "
                  "consistent with the head.macStyle.italic setting"))

        else:
            if headTbl.macStyle.italic:
                logger.warning((
                  'V0260',
                  (),
                  "The caretSlopeRise/caretSlopeRun angle indicates "
                  "upright, but head.macStyle.italic is True"))

            else:
                logger.info((
                  'V0259',
                  (),
                  "The caretSlopeRise/caretSlopeRun angle is consistent "
                  "with the head.macStyle.italic setting"))

            if obj.caretOffset:
                logger.warning((
                  'V0257',
                  (obj.caretOffset,),
                  "The caretOffset (%d) is non-zero but the "
                  "caretSlopeRise/caretSlopeRun angle indicates upright"))


        if obj.ascent < headTbl.yMax:
            logger.warning((
              'V0916',
              (headTbl.yMax, obj.ascent),
              "The font-wide head.yMax %d exceeds the ascent %d. "
              "Clipping may occur."))

        if obj.descent > headTbl.yMin:
            logger.warning((
              'V0917',
              (headTbl.yMin, obj.descent),
              "The font-wide head.yMin %d exceeds the descent %d. "
              "Clipping may occur."))

    # values based on 'hmtx'...check against recalc'ed...if hmtx present!

    if not editor.reallyHas(b'hmtx'):
        logger.critical((
          'E1408',
          (),
          "The advanceWidthMax, minLeftSideBearing, minRightSideBearing, "
          "and xMaxExtent fields can not be validated because the 'hmtx' "
          "table is missing or empty."))

        return False

    try:
        recalc = obj.recalculated(editor=editor)

    except NoGlyf:  # note we've already checked for NoEditor and NoHmtx
        logger.error((
          'V0553',
          (),
          "Unable to recalculate (and thus validate) the 'hhea' table "
          "because the Glyf table is missing or empty."))

        return False

    attrs = (
      'advanceWidthMax',
      'minLeftSidebearing',
      'minRightSidebearing',
      'xMaxExtent')

    eMsgs = ('E1400', 'E1402', 'E1403', 'E1410')
    pMsgs = ('P1400', 'P1402', 'P1403', 'P1407')

    for attr, eMsg, pMsg in zip(attrs, eMsgs, pMsgs):
        o = getattr(obj, attr)
        n = getattr(recalc, attr)

        if o != n:
            logger.error((
              eMsg,
              (attr, o, n),
              "The %s value (%d) does not match the expected value (%d)"))

            r = False

        else:
            logger.info((
              pMsg,
              (attr,),
              "The %s value equals the expected value"))

    # numLongMetrics; note we only check this if there is a "raw" version of
    # the 'hmtx' table to check against. If there isn't, it means the font was
    # reconstructed, and so different reality checks are in place.

    rawHmtx = editor.getRawTable(b'hmtx')

    if rawHmtx is not None:
        expectedHmtxLength = (
          (obj.numLongMetrics * 4) +
          ((editor.maxp.numGlyphs - obj.numLongMetrics) * 2))

        if expectedHmtxLength != len(rawHmtx):
            logger.error((
              'E1404',
              (),
              "The numberOfHMetrics value is not consistent with the "
              "length of the 'hmtx' table"))

            r = False

        else:
            logger.info((
              'P1404',
              (),
              "The numberOfHMetrics value is consistent with the "
              "length of the hmtx table"))

    return r

# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class NoEditor(ValueError): pass
class NoGlyf(ValueError): pass
class NoHmtx(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hhea(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing TrueType 'hhea' tables. These are simple collections
    of attributes.

    >>> _testingValues[1].pprint()
    Version: 1.0
    Ascent: 1536
    Descent: -462
    Line gap (leading): 50
    Maximum advance width: 1800
    Minimum left sidebearing: -150
    Minimum right sidebearing: 80
    Maximum extent in x: 1650
    Caret slope rise: 20
    Caret slope run: 1
    Caret offset: 9
    Metric data format: 0
    Number of long metrics: 625
    """

    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)

    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 1.0),
            attr_label = "Version"),

        ascent = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Ascent",
            attr_mergefunc = (lambda a, b, **k: (max(a, b) != a, max(a, b))),
            attr_representsy = True,
            attr_scaledirect = True),

        descent = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Descent",
            attr_mergefunc = (lambda a, b, **k: (min(a, b) != a, min(a, b))),
            attr_representsy = True,
            attr_scaledirect = True),

        lineGap = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Line gap (leading)",
            attr_representsy = True,
            attr_scaledirect = True),

        advanceWidthMax = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeUshort,
            attr_label = "Maximum advance width",
            attr_representsx = True,
            attr_scaledirect = True),

        minLeftSidebearing = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Minimum left sidebearing",
            attr_representsx = True,
            attr_scaledirect = True),

        minRightSidebearing = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Minimum right sidebearing",
            attr_representsx = True,
            attr_scaledirect = True),

        xMaxExtent = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Maximum extent in x",
            attr_representsx = True,
            attr_scaledirect = True),

        caretSlopeRise = dict(
            attr_initfunc = (lambda: 1),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Caret slope rise"),

        caretSlopeRun = dict(
            attr_initfunc = (lambda: 0),
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_label = "Caret slope run"),

        caretOffset = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Caret offset",
            attr_inputcheckfunc = utilities.inRangeShort,
            attr_representsx = True,
            attr_scaledirect = True),

        metricDataFormat = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Metric data format"),

        numLongMetrics = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Number of long metrics"))

    attrSorted = (
      'version',
      'ascent',
      'descent',
      'lineGap',
      'advanceWidthMax',
      'minLeftSidebearing',
      'minRightSidebearing',
      'xMaxExtent',
      'caretSlopeRise',
      'caretSlopeRun',
      'caretOffset',
      'metricDataFormat',
      'numLongMetrics')

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Hhea object to the specified LinkedWriter.

        >>> utilities.hexdump(Hhea().binaryString())
               0 | 0001 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0001 0000 0000  0000 0000 0000 0000 |................|
              20 | 0000 0001                                |....            |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add(
          'L3hH11hH',
          int(self.version * 65536),
          self.ascent,
          self.descent,
          self.lineGap,
          self.advanceWidthMax,
          self.minLeftSidebearing,
          self.minRightSidebearing,
          self.xMaxExtent,
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
        Like fromwalker(), this method returns a new Hhea. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Hhea.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        test.hhea - DEBUG - Walker has 36 remaining bytes.
        >>> obj == _testingValues[1]
        True

        >>> fvb(s[:1], logger=logger)
        test.hhea - DEBUG - Walker has 1 remaining bytes.
        test.hhea - ERROR - Insufficient bytes.

        >>> fvb(b'AAAA' + s[4:], logger=logger)
        test.hhea - DEBUG - Walker has 36 remaining bytes.
        test.hhea - ERROR - Unknown version: 0x41414141.

        >>> fvb(s[:10], logger=logger)
        test.hhea - DEBUG - Walker has 10 remaining bytes.
        test.hhea - ERROR - Insufficient bytes for content.

        >>> obj = fvb(s[:28] + b'AA' + s[30:], logger=logger)
        test.hhea - DEBUG - Walker has 36 remaining bytes.
        test.hhea - WARNING - Reserved field #2 is nonzero.
        """

        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('hhea')
        else:
            logger = logger.getChild('hhea')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        version = w.unpack("L")

        if version != 0x10000:
            logger.error(('E1409', (version,), "Unknown version: 0x%08X."))
            return None

        if w.length() < w.calcsize("3hH6h8xhH"):
            logger.error(('V0134', (), "Insufficient bytes for content."))
            return None

        t = w.unpack("3hH6h4HhH")

        if t[11]:
            logger.warning(("E1405", (), "Reserved field #1 is nonzero."))

        if t[12]:
            logger.warning(("E1406", (), "Reserved field #2 is nonzero."))

        if t[13]:
            logger.warning(("E1407", (), "Reserved field #3 is nonzero."))

        if t[14]:
            logger.warning(("E1408", (), "Reserved field #4 is nonzero."))

        # Note that any consistency checks (like ascent > descent) are left to
        # the isValid() method and its validators.

        return cls(
          version = version / 65536.0,
          ascent = t[0],
          descent = t[1],
          lineGap = t[2],
          advanceWidthMax = t[3],
          minLeftSidebearing = t[4],
          minRightSidebearing = t[5],
          xMaxExtent = t[6],
          caretSlopeRise = t[7],
          caretSlopeRun = t[8],
          caretOffset = t[9],
          metricDataFormat = t[14],
          numLongMetrics = t[15])

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hhea object from the data in the specified walker.

        >>> h = Hhea()
        >>> h.caretOffset = 10
        >>> h == Hhea.frombytes(h.binaryString())
        True
        """

        t = w.unpack("L3hH6h8xhH")

        return cls(
          version = t[0] / 65536.0,
          ascent = t[1],
          descent = t[2],
          lineGap = t[3],
          advanceWidthMax = t[4],
          minLeftSidebearing = t[5],
          minRightSidebearing = t[6],
          xMaxExtent = t[7],
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

    _testingValues = (
        Hhea(),  # all defaults

        Hhea(
          version = 1.0,
          ascent = 1536,
          descent = -462,
          lineGap = 50,
          advanceWidthMax = 1800,
          minLeftSidebearing = -150,
          minRightSidebearing = 80,
          xMaxExtent = 1650,
          caretSlopeRise = 20,
          caretSlopeRun = 1,
          caretOffset = 9,
          metricDataFormat = 0,
          numLongMetrics = 625))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

