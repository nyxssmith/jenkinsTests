#
# ppemdict.py
#
# Copyright © 2007-2008, 2011-2013, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for component dicts that make up Hdmx objects.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import ScalerError

# -----------------------------------------------------------------------------

#
# Private functions
#

def _recalc(d, **kwArgs):
    editor = kwArgs['editor']
    
    if editor is None or (not editor.reallyHas(b'maxp')):
        return False, d
    
    fontGlyphCount = editor.maxp.numGlyphs
    scaler = kwArgs.get('scaler', None)
    r = d
    
    if (scaler is not None) and (editor.reallyHas(b'glyf')):
        r = type(d)({}, ppem=d.ppem)
        
        try:
            f = scaler.getBitmapMetrics
        except AttributeError:
            f = scaler.getBitmap
        
        try: scaler.setPointsize(d.ppem)
        except: raise ScalerError()
        
        for glyph in range(fontGlyphCount):
            t = f(glyph)
            #r[glyph] = t.i_dx ### see Jira ITP-2133
            r[glyph] = round(t.dx)
    
    return (r != d, r)

def _validate(d, **kwArgs):
    editor = kwArgs['editor']
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        logger = logging.getLogger().getChild('hdmx.%d ppem' % (d.ppem,))
    else:
        logger = logger.getChild("%d ppem" % (d.ppem,))

    if editor is None or (not editor.reallyHas(b'maxp')):
        logger.error((
          'V0553',
          (),
          "Unable to validate PPEM dict because the editor and/or "
          "the 'maxp' table is missing."))
        
        return False
    
    fontGlyphCount = editor.maxp.numGlyphs
    
    if set(d) != set(range(fontGlyphCount)):
        logger.error((
          'V0230',
          (),
          "Keys do not match font's glyph count"))
        
        return False
    
    dNew = kwArgs.get('recalculateditem', None)
    if dNew is None:
        if 'scaler' in kwArgs:
            try:
                dNew = d.recalculated(**kwArgs)
            except ScalerError:
                logger.error((
                  'V0554',
                  (),
                  "An error occured in the scaler during device metrics "
                  "calculation, preventing validation."))

                return False

        else:
            logger.warning((
              'V0785',
              (),
              "Device metrics will not be tested against scaler results "
              "because a scaler was not supplied."))
            return False

    r = True
    for glyph in range(fontGlyphCount):
        if glyph not in dNew:
            logger.error((
              'V0554',
              (glyph,),
              "Value for glyph %d could not validated because of an "
              "error calculating the expected value."))
            return False
            
        if glyph not in d:
            logger.error((
              'V0000',
              (glyph,),
              "Value for glyph %d could not be validated because "
              "it was empty, missing, or corrupted."))
            return False
        
        if dNew[glyph] != d[glyph]:
            if dNew[glyph] < 0:
                logger.error((
                  'V0810',
                  (glyph,),
                  "Glyph %d's recalculated advance was negative"))
            else:
                logger.error((
                  'E1207',
                  (glyph, dNew[glyph], d[glyph]),
                  "Glyph %d's value should be %d, but is %d"))
            r = False

    if r:
        logger.info((
            'V0898',
            (),
            "All entries matched the calculated values."))
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class PPEMDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing the widths for a single PPEM. These are dicts mapping
    glyph indices to widths.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    xyz1: 12
    xyz2: 13
    xyz3: 12
    xyz4: 11
    xyz5: 12
    xyz6: 11
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_scaledirectvalues = True,
        item_usenamerforstr = True,
        item_valuerepresentsx = True,
        map_recalculatefunc = _recalc,
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        ppem = dict(
            attr_label = "PPEM"))
    
    attrSorted = ()  # parent key is displayed instead
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the PPEMDict to the specified writer.
        
        >>> utilities.hexdump(_testingValues[1].binaryString(fontGlyphCount=6))
               0 | 0C0D 0C0D 0C0B 0C0B                      |........        |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(fontGlyphCount=5))
               0 | 0C0D 0C0D 0C0B 0C00                      |........        |
        
        >>> utilities.hexdump(_testingValues[3].binaryString(fontGlyphCount=5))
        Traceback (most recent call last):
          ...
        ValueError: Keys not dense!
        """
        
        sortedKeys = sorted(self)
        
        if sortedKeys != list(range(kwArgs['fontGlyphCount'])):
            raise ValueError("Keys not dense!")
        
        if not all(0 <= n < 256 for n in self.values()):
            raise ValueError("Values out of range!")
        
        w.add("2B", self.ppem, max(self.values()))
        w.addGroup("B", (self[i] for i in sortedKeys))
        w.alignToByteMultiple(4)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new PPEMDict. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[2].binaryString(fontGlyphCount=5)
        >>> kw = {'logger': logger, 'fontGlyphCount': 5, 'sizeDeviceRecord': 8}
        >>> obj = PPEMDict.fromvalidatedbytes(s, **kw)
        test.ppemdict - DEBUG - Walker has 8 remaining bytes.
        
        >>> obj = PPEMDict.fromvalidatedbytes(s[:-1], **kw)
        test.ppemdict - DEBUG - Walker has 7 remaining bytes.
        test.ppemdict - ERROR - Insufficient bytes
        
        >>> obj = PPEMDict.fromvalidatedbytes(s[:-1] + b'\x14', **kw)
        test.ppemdict - DEBUG - Walker has 8 remaining bytes.
        test.ppemdict - ERROR - Nonzero pad bytes found
        
        >>> obj = PPEMDict.fromvalidatedbytes(
        ...   s[0:1] + b'\x14' + s[2:],
        ...   **kw)
        test.ppemdict - DEBUG - Walker has 8 remaining bytes.
        test.ppemdict - WARNING - The max width is reported as 20, but is actually 13
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('ppemdict')
        else:
            logger = logger.getChild('ppemdict')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        fontGlyphCount = kwArgs['fontGlyphCount']
        
        if not fontGlyphCount:
            logger.warning((
              'V0552',
              (),
              "The 'glyf' table is empty, so no actual 'hdmx' data can be "
              "created."))
            
            return None
        
        sizeDevRec = kwArgs['sizeDeviceRecord']
        padSize = sizeDevRec - (fontGlyphCount + 2)
        
        if w.length() < sizeDevRec:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        if padSize < 0:
            logger.error((
              'V0892',
              (),
              "The size of the device record is too small "
              "for the number of glyphs in the font."))
            
            return None
        
        ppem, maxWidth = w.unpack("2B")
        t = w.group("B", fontGlyphCount)
        
        if maxWidth != max(t):
            logger.warning((
              'V0229',
              (maxWidth, max(t)),
              "The max width is reported as %d, but is actually %d"))

        if padSize:
            rest = w.group("B", padSize)
            
            if any(rest):
                logger.error(('E1200', (), "Nonzero pad bytes found"))
                return None
        
        return cls(
          {i: obj for i, obj in enumerate(t)},
          ppem = ppem)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new PPEMDict from the specified walker.
        
        >>> obj = _testingValues[1]
        >>> obj == PPEMDict.frombytes(
        ...   obj.binaryString(fontGlyphCount=6),
        ...   fontGlyphCount=6)
        True
        """
        
        ppem = w.unpack("Bx")  # ignore maxWidth
        t = w.group("B", kwArgs['fontGlyphCount'])
        w.align(4)
        
        return cls(
          {i: obj for i, obj in enumerate(t)},
          ppem = ppem)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.utilities import namer
    
    _testingValues = (
        PPEMDict(),
        
        PPEMDict(
          {
            0: 12,
            1: 13,
            2: 12,
            3: 11,
            4: 12,
            5: 11},
          ppem = 12),
        
        PPEMDict(
          {
            0: 12,
            1: 13,
            2: 12,
            3: 11,
            4: 12},
          ppem = 12),
        
        # this one is bad (non-dense keys)
        PPEMDict(
          {
            0: 12,
            1: 13,
            2: 12,
            3: 11,
            5: 11},
          ppem = 12))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
