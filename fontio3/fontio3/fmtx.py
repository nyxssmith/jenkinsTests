#
# fmtx.py
#
# Copyright © 2010, 2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the AAT 'fmtx' table.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.glyf import ttsimpleglyph, ttcontour, ttpoint


# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(d, **kwArgs):
    """
    Do validation on the entire Fmtx object.
    
    >>> l = utilities.makeDoctestLogger("fmtx")
    >>> x = Fmtx()
    >>> x.isValid(logger=l)
    fmtx - ERROR - Unable to validate 'fmtx' because no Editor was specified.
    False
    
    >>> fe = utilities.fakeEditor(5)
    >>> x.isValid(editor=fe, logger=l)
    fmtx - ERROR - Unable to validate 'fmtx' because the 'glyf' table is missing or damaged.
    False
    
    >>> fe.glyf = {v: None for v in range(5)}
    >>> fe.glyf[3] = ttsimpleglyph.TTSimpleGlyph()
    >>> x.glyph = 3
    >>> x.isValid(editor=fe, logger=l)
    fmtx - ERROR - The magic glyph is empty (no contours/no points).
    False
    
    >>> x.glyph = 4
    >>> fe.glyf[4] = ttcompositeglyph.TTCompositeGlyph()
    >>> x.isValid(editor=fe, logger=l)
    fmtx - WARNING - The magic glyph is a composite.
    fmtx - ERROR - The magic glyph is empty (no contours/no points).
    False
    
    >>> x.glyph = 0x10000
    >>> x.isValid(editor=fe, logger=l)
    fmtx - ERROR - Glyph index 65536 out of range for font.
    fmtx.glyph - ERROR - The glyph index 65536 does not fit in 16 bits.
    False
    
    >>> x.glyph = 3
    >>> fe.glyf[3].contours.append([ttpoint.TTPoint(0,0), ttpoint.TTPoint(1,1)])
    >>> x.horizCaretBase = 1
    >>> x.vertCaretBase = 1
    >>> x.horizBefore = 0
    >>> x.horizAfter = 0
    >>> x.horizCaretHead = 0
    >>> x.vertBefore = 0
    >>> x.vertAfter = 0
    >>> x.vertCaretHead = 0
    >>> x.isValid(editor=fe, logger=l)
    fmtx - ERROR - Y-coordinate of horizontalCaretBase must be 0 (is 1)
    fmtx - ERROR - X-coordinate of verticalCaretBase must be 0 (is 1)
    False
    
    >>> x.horizBefore = 213
    >>> x.isValid(editor=fe, logger=l)
    fmtx - ERROR - Point index 213 for horizBefore is out of range for the specified magic glyph (index 3).
    False
    """
    
    logger = kwArgs['logger']
    editor = kwArgs.get('editor')

    if editor is None:
        logger.error((
          'V1027',
          (),
          "Unable to validate 'fmtx' because no Editor was specified."))

        return False

    for reqtbl in (b'maxp', b'glyf'):
        if not editor.reallyHas(reqtbl):
            logger.error((
              'V1028',
              (str(reqtbl, 'ascii'),),
              "Unable to validate 'fmtx' because the '%s' table "
              "is missing or damaged."))

            return False

    # check glyph in range for font
    if not 0 < d.glyph < editor.maxp.numGlyphs:
        logger.error((
          'V1029',
          (d.glyph,),
          "Glyph index %d out of range for font."))

        return False

    # get glyph and check characteristics
    gl = editor.glyf[d.glyph]

    # is it a composite? i.e. is the designer high?
    if gl.isComposite:
        logger.warning((
          'V1031',
          (),
          "The magic glyph is a composite."))
        
        gl = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph(
            gl,
            editor = editor)

    # get points and check in range
    numPoints = gl.pointCount(editor=editor)

    if numPoints < 1:
        logger.error((
          'Vxxxx',
          (),
          "The magic glyph is empty (no contours/no points)."))
        
        return False
    
    flatpoints = [p for c in gl.contours for p in c]
    isOK = True
    
    attrNames = (
      'horizBefore',
      'horizAfter',
      'horizCaretHead',
      'horizCaretBase',
      'vertBefore',
      'vertAfter',
      'vertCaretHead',
      'vertCaretBase')

    for attr in attrNames:
        x = getattr(d, attr)
        
        if x is None:
            logger.error((
              'Vxxxx',
              (attr,),
              "The '%s' attribute is missing."))
            
            isOK = False
            continue
        
        if x > numPoints:
            logger.error((
              'V1030',
              (x, attr, d.glyph),
              "Point index %d for %s is out of range "
              "for the specified magic glyph (index %d)."))
            
            isOK = False

    if isOK:
        # check against spec requirements
        pt = flatpoints[d.horizCaretBase]
        
        if pt.y != 0:
            logger.error((
              'V1032',
              (pt.y,),
              "Y-coordinate of horizontalCaretBase must be 0 (is %d)"))
            
            isOK = False

        pt = flatpoints[d.vertCaretBase]
        
        if pt.x != 0:
            logger.error((
              'V1033',
              (pt.x,),
              "X-coordinate of verticalCaretBase must be 0 (is %d)"))
            
            isOK = False

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Fmtx(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing entire 'fmtx' tables. These are simple objects with
    the following attributes:

        glyph
        horizBefore
        horizAfter
        horizCaretHead
        horizCaretBase
        vertBefore
        vertAfter
        vertCaretHead
        vertCaretBase

    >>> _testingValues[0].pprint()
    Metrics glyph index: 14
    Ascent for horizontal text: 1
    Descent for horizontal text: 4
    Caret head for horizontal text: 3
    Caret base for horizontal text: 2
    Ascent for vertical text: 5
    Descent for vertical text: 8
    Caret head for vertical text: 7
    Caret base for vertical text: 6
    """
    
    #
    # Class definition variables
    #
    
    objSpec = dict(
        obj_validatefunc_partial = _validate)

    attrSpec = dict(

        # This is one of those relatively rare cases where a glyph index
        # attribute does NOT get attr_usenamerforstr set, since the glyph
        # in question is usually a synthetic glyph with no other purpose.

        glyph = dict(
            attr_label = "Metrics glyph index",
            attr_renumberdirect = True),

        horizBefore = dict(
            attr_label = "Ascent for horizontal text",
            attr_renumberpointsdirect = True),

        horizAfter = dict(
            attr_label = "Descent for horizontal text",
            attr_renumberpointsdirect = True),

        horizCaretHead = dict(
            attr_label = "Caret head for horizontal text",
            attr_renumberpointsdirect = True),

        horizCaretBase = dict(
            attr_label = "Caret base for horizontal text",
            attr_renumberpointsdirect = True),

        vertBefore = dict(
            attr_label = "Ascent for vertical text",
            attr_renumberpointsdirect = True),

        vertAfter = dict(
            attr_label = "Descent for vertical text",
            attr_renumberpointsdirect = True),

        vertCaretHead = dict(
            attr_label = "Caret head for vertical text",
            attr_renumberpointsdirect = True),

        vertCaretBase = dict(
            attr_label = "Caret base for vertical text",
            attr_renumberpointsdirect = True))

    attrSorted = (
      'glyph',
      'horizBefore',
      'horizAfter',
      'horizCaretHead',
      'horizCaretBase',
      'vertBefore',
      'vertAfter',
      'vertCaretHead',
      'vertCaretBase')
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the xxx object to the specified LinkedWriter.

        >>> obj = _testingValues[0]
        >>> utilities.hexdump(obj.binaryString())
               0 | 0002 0000 0000 000E  0104 0302 0508 0706 |................|
        
        >>> obj = _testingValues[1]
        >>> utilities.hexdump(obj.binaryString(stakeValue=0))
        Traceback (most recent call last):
            ...
        ValueError: All fields in Fmtx object must have non-None values!
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        w.add("L", 0x20000)  # version
        d = self.__dict__
        v = [d[key] for key in self.getSortedAttrNames()]

        if any(obj is None for obj in v):
            raise ValueError(
              "All fields in Fmtx object must have non-None values!")

        w.add("L8B", *v)

    @classmethod
    def fromfontmetrics(cls, editor, **kwArgs):
        """
        Creates and returns a Fmtx object AND magic glyph (TTSimpleGlyph) from
        the specified Editor. The Fmtx is set up with the assumption that the
        table will be added to the end of the existing editor's glyph
        repertoire, but does not actually perform this action, i.e. the caller
        is responsible for adding the table and the glyph if applicable (and/or
        adjusting fmtx.glyph if for example the result is being used to modify
        an existing fmtx + magic glyph).

        The following kwArg, if supplied, modifies the behavior of the metric
        calculations for horizBefore and horizAfter:

            'preferWinMetrics'  If this evaluates to True, Windows metrics
                                (OS/2 table) will be preferred over "Mac" (hhea
                                table).
        
        >>> fe = utilities.fakeEditor(5)
        >>> fe.hhea = hhea.Hhea()
        >>> fe.head = head.Head()
        >>> x = Fmtx.fromfontmetrics(fe)
        >>> fe['OS/2'] = OS_2_v4.OS_2()
        >>> x = Fmtx.fromfontmetrics(fe, preferWinMetrics=True)
        >>> fe.hhea.caretSlopeRun = 9
        >>> x = Fmtx.fromfontmetrics(fe)
        """
        
        magicglyphobj = ttsimpleglyph.TTSimpleGlyph()
        magicglyphobj.contours.append(ttcontour.TTContour())
        hheaTbl = editor[b'hhea']
        
        useWin = (
          kwArgs.get('preferWinMetrics', False) and
          editor.reallyHas(b'OS/2'))

        if useWin:
            os2Tbl = editor[b'OS/2']
            hBeforeY =  os2Tbl.usWinAscent
            hAfterY  = -os2Tbl.usWinDescent
        
        else:
            hBeforeY = hheaTbl.ascent
            hAfterY  = hheaTbl.descent

        # other metrics have to come from the hhea and vhea (if present)
        hCaretBaseX = hheaTbl.caretOffset
        
        if hheaTbl.caretSlopeRun != 0:
            caret_m = hheaTbl.caretSlopeRise / hheaTbl.caretSlopeRun
            caret_x_at_ascent = hBeforeY / caret_m
            hCaretHeadX = caret_x_at_ascent + hCaretBaseX
        
        else:
            hCaretHeadX = 0
        
        hCaretHeadY = hBeforeY

        if editor.reallyHas(b'vhea'):
            vheaTbl = editor[b'vhea']
            
            if vheaTbl.version == 0x11000:
                vBeforeX = vheaTbl.vertTypoAscender
                vAfterX  = vheaTbl.vertTypoDescender
            
            vCaretBaseY = vheaTbl.caretOffset
            
            if vheaTbl.caretSlopeRun != 0:
                caret_m = vheaTbl.caretSlopeRise / vheaTbl.caretSlopeRun
                caret_y_at_ascent = vBeforeX * caret_m
                vCaretHeadY = caret_y_at_ascent + vCaretBaseY
            
            else:
                vCaretHeadY = 0
            
            vCaretHeadX = vBeforeX

        else:
            # no 'vhea' table; use defaults
            vBeforeX = int(editor.head.unitsPerEm / 2)
            vAfterX = -vBeforeX
            vCaretHeadX = vBeforeX
            vCaretHeadY = 0
            vCaretBaseY = 0

        # now modify the glyph...
        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(0, hBeforeY))  # horizontalBefore

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(0, hAfterY))  # horizontalAfter

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(hCaretHeadX, hCaretHeadY))  # horizontalCaretHead

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(hCaretBaseX, 0))  # horizontalCaretBase

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(vBeforeX, 0))  # verticalBefore

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(vAfterX, 0))  # verticalAfter

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(vCaretHeadX, vCaretHeadY))  # verticalCaretHead

        magicglyphobj.contours[0].append(
            ttpoint.TTPoint(0, vCaretBaseY))  # verticalCaretBase

        # finally, create the Fmtx object and return
        r = cls()
        r.glyph = editor.maxp.numGlyphs  # assume will be added to end of order
        r.horizBefore = 0
        r.horizAfter = 1
        r.horizCaretHead = 2
        r.horizCaretBase = 3
        r.vertBefore = 4
        r.vertAfter = 5
        r.vertCaretHead = 6
        r.vertCaretBase = 7
        return r, magicglyphobj.recalculated()  # recalc for bounds

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a Fmtx object from the specified walker with validation

        >>> logger = utilities.makeDoctestLogger("test")
        >>> s = _testingValues[0].binaryString()
        >>> obj = Fmtx.fromvalidatedbytes(s, logger=logger)
        test.fmtx - DEBUG - Walker has 16 remaining bytes.

        >>> s_bad = s[0:12]
        >>> obj = Fmtx.fromvalidatedbytes(s_bad, logger=logger)
        test.fmtx - DEBUG - Walker has 12 remaining bytes.
        test.fmtx - ERROR - Insufficient bytes.

        >>> s_bad2 = s + b'\x02\x11\x19\x70'
        >>> obj = Fmtx.fromvalidatedbytes(s_bad2, logger=logger)
        test.fmtx - DEBUG - Walker has 20 remaining bytes.
        test.fmtx - WARNING - Expected length 16 bytes but got 20 bytes.

        >>> s_badv = b'\x05' + s[1:]
        >>> obj = Fmtx.fromvalidatedbytes(s_badv, logger=logger)
        test.fmtx - DEBUG - Walker has 16 remaining bytes.
        test.fmtx - ERROR - Unknown version 0x05020000 for 'fmtx' table; 0x00020000 required.
        """

        logger = kwArgs.pop('logger')

        if logger is None:
            logger = logging.getLogger().getChild('fmtx')
        else:
            logger = logger.getChild('fmtx')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        tbllen = w.length()
        
        if tbllen < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        if tbllen != 16:
            logger.warning((
              'V1025',
              (tbllen,),
              "Expected length 16 bytes but got %d bytes."))

        version = w.unpack("L")

        if version != 0x20000:
            logger.error((
              'V1026',
              (version,),
              "Unknown version 0x%08X for 'fmtx' table; 0x00020000 required."))
            
            return None

        r = cls(*w.unpack("L8B"))

        # NOTE: check for r.glyph not necessary since attr_renumberdirect is
        # set; metaclass validation will take care of this automatically.

        return r

    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a Fmtx object from the specified walker.

        >>> obj = _testingValues[0]
        >>> s = obj.binaryString()
        >>> obj == Fmtx.frombytes(s)
        True
        
        >>> s1 = b'\x55' + s[1:]
        >>> obj = Fmtx.frombytes(s1)
        Traceback (most recent call last):
            ...
        ValueError: Unknown version for 'fmtx' table: 0x55020000
        """

        version = w.unpack("L")

        if version != 0x20000:
            raise ValueError(
              "Unknown version for 'fmtx' table: 0x%08X" % (version,))

        return cls(*w.unpack("L8B"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.glyf import ttcompositeglyph, ttpoint
    from fontio3.head import head
    from fontio3 import hhea
    from fontio3.OS_2 import OS_2_v4

    _testingValues = (
        Fmtx(14, 1, 4, 3, 2, 5, 8, 7, 6),
        Fmtx(1, None, 2, 3, 4, 5, 6, 7, 8),)

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

