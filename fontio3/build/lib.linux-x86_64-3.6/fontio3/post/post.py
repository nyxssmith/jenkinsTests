#
# post.py -- TrueType 'post' tables
#
# Copyright © 2004-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions for TrueType 'post' tables.
"""

# System imports
import logging
import math
import operator
import re

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.post import postheader, standardnames
from fontio3.utilities import convertertoken, writer

# -----------------------------------------------------------------------------

#
# Private functions
#
def _asFormat(obj, f, **kwArgs):
    """
    Return a new Post from 'obj' in format 'f'.
    
    >>> f2 = _testingValues[2]
    >>> f2.header.format
    2.0
    >>> f3 = _asFormat(f2, 3.0)
    >>> f3.header.format
    3.0
    """
    
    objN = obj.__copy__()
    
    if f == 2.0 and len(objN) == 0:
        objN[0] = ".notdef" # at least one item for format 2.0
    
    objN.setPreferredFormat(f)
    return Post.frombytes(objN.binaryString())
    
def _validate(d, **kwArgs):
    """
    'isValid' validation for the 'post' table.
    """
    
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    fmt = d.header.format
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'post' table because Editor is missing."))
        
        return False
    
    r = True

    if b'CFF ' in editor and fmt != 3:
        logger.error((
          'V0991',
          (fmt,),
          "CFF font with format %d post table (expected format 3)."))
        r = False
    
    if editor.reallyHas(b'hmtx'):
        allAdvances = {obj.advance for obj in editor.hmtx.values()}
        allAdvances.discard(0)
    
    elif editor.reallyHas(b'vmtx'):
        allAdvances = {obj.advance for obj in editor.vmtx.values()}
        allAdvances.discard(0)
    
    else:
        allAdvances = None
    
    if allAdvances is not None:
        if not editor.reallyHas(b'OS/2'):
            logger.error((
              'V0553',
              (),
              "Unable to validate 'post' table because the 'OS/2' table is "
              "missing or empty."))
            
            return False
        
        if hasattr(editor[b'OS/2'].panoseArray, 'proportion'):
            pro = editor[b'OS/2'].panoseArray.proportion
        else:
            pro = None
        
        if d.header.isFixedPitch:
            if len(allAdvances) > 1:
                logger.error((
                  'E2302',
                  (),
                  "Header says isFixedPitch, but advances vary."))
                
                r = False
            
            if pro is not None and pro != "Monospaced":
                logger.error((
                  'E2303',
                  (),
                  "Header disagrees with PANOSE on fixed-pitch."))
            
                r = False
        
        else:
            if len(allAdvances) == 1:
                logger.error((
                  'E2304',
                  (),
                  "Header says non-isFixedPitch, but advances are constant."))
                
                r = False
            
            if pro is not None and pro == "Monospaced":
                logger.error((
                  'E2305',
                  (),
                  "Header disagrees with PANOSE on fixed-pitch."))
            
                r = False
    
    if (not editor.reallyHas(b'hhea')) or (not editor.reallyHas(b'head')):
        logger.error((
          'V0553',
          (),
          "Unable to validate 'post' table because 'hhea' and/or 'head' "
          "tables are missing or empty."))
        
        return False
    
    rise = editor.hhea.caretSlopeRise
    run = editor.hhea.caretSlopeRun
    computedAngle = (round(65536 * ((math.atan2(rise, run) * 180) / math.pi)) / 65536) - 90
    
    if d.header.italicAngle:
        if not run:
            logger.error((
              'E2306',
              (),
              "Nonzero italic angle but zero hhea.caretSlopeRun"))
            
            r = False
        
        if not editor.head.macStyle.italic:
            logger.error((
              'E2308',
              (),
              "Nonzero italic angle but head.macStyle.italic is False."))
            
            r = False
    
    else:
        if run:
            logger.error((
              'E2309',
              (),
              "Zero italic angle but nonzero hhea.caretSlopeRun"))
            
            r = False
        
        if editor.head.macStyle.italic:
            logger.error((
              'E2310',
              (),
              "Zero italic angle but head.macStyle.italic is True."))
            
            r = False
    
    if computedAngle != d.header.italicAngle:
        diff = abs(computedAngle - d.header.italicAngle)
        if diff > 0.5:
            logger.error((
              'E2307',
              (d.header.italicAngle),
              "The slope of the hhea caretSlopeRise/Run deviates from "
              "the italic angle of %s by more than 0.5 degrees."))
        
        r = False
    
    if len(d) and (set(d) != set(range(max(d) + 1))):
        logger.error((
          'V0234',
          (),
          "The keys are not dense."))
        
        r = False
    
    if not editor.reallyHas(b'maxp'):
        logger.error((
          'V0553',
          (),
          "Unable to validate 'post' table because 'maxp' table is "
          "missing or empty."))
        
        return False
    
    if len(d) and (len(d) != editor.maxp.numGlyphs):
        logger.error((
          'E2314',
          (len(d), editor.maxp.numGlyphs),
          "Number of entries %d doesn't match maxp.numGlyphs %d."))
        
        r = False
    
    # I don't really know what MS intends as "unlikely" for W2300, so for the
    # time being I'll use a 30-degree slope.
    
    if abs(d.header.italicAngle) >= 30:
        logger.warning((
          'W2300',
          (d.header.italicAngle,),
          "Italic angle is %d degrees, which seems unlikely."))
    
    if abs(d.header.underlinePosition) > abs(editor.hhea.descent):
        logger.warning((
          'W2301',
          (d.header.underlinePosition, editor.hhea.descent),
          "Underline position %d is under the descender %d."))
    
    if not (0 <= d.header.underlineThickness <= (editor.head.unitsPerEm // 2)):
        logger.warning((
          'W2302',
          (d.header.underlineThickness),
          "Underline thickness %d is negative or implausibly large."))

    dup = d.detectDuplicates()
    
    if dup:
        for k in dup:
            logger.error((
              'V0932',
              (k, dup[k]),
              "Glyphname '%s' is used in multiple glyphs: %s"))
        
        r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Post(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing the header information for any 'post' table. These are
    dicts mapping glyph indices to names.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelpresort = True,
        item_renumberdirectkeys = True,  # do not set item_usenamerforstr!
        map_validatefunc_partial = _validate)
    
    attrSpec = dict(
        header = dict(
            attr_followsprotocol = True,
            attr_ignoreforbool = True,
            attr_initfunc = postheader.PostHeader,
            attr_label = "Header"),
        
        preferredFormat = dict(
            attr_ignoreforbool = True,
            attr_label = "Preferred format"))
    
    #
    # Methods
    #
    
    def _addFormat2(self, w):
        """
        Adds the data in format 2 to the specified LinkedWriter.
        """
        
        w.add("H", len(self))
        nd = standardnames.nameDict
        dAdded = {}
        
        for k in range(len(self)):
            s = self[k]
            
            if s in nd:
                w.add("H", nd[s])
            elif s in dAdded:
                w.add("H", dAdded[s])
            else:
                newIndex = len(dAdded) + 258
                dAdded[s] = newIndex
                w.add("H", newIndex)
        
        for s, i in sorted(dAdded.items(), key=operator.itemgetter(1)):
            s = s.encode('ascii')
            
            if len(s) > 255:
                raise ValueError("String too long for format 2 'post' table!")
            
            w.add("B", len(s))
            w.addString(s)
    
    def _addFormat25(self, w):
        """
        Adds the data in format 2.5 to the specified LinkedWriter.
        """
        
        w.add("H", len(self))
        nd = standardnames.nameDict
        
        for i in range(len(self)):
            s = self[i]
            stdIndex = nd[s]
            w.add("b", stdIndex - i)
    
    def _addFormat4(self, w):
        """
        Adds the data in format 2.5 to the specified LinkedWriter.
        """
        
        for i in range(len(self)):
            s = self[i]
            w.add("H", int(s[1:], 16))
    
    def _findBestFormat(self):
        """
        Returns the best format for the current dataset. Raises an IndexError
        if the dict is not empty but there are holes in the key set.
        
        >>> _testingValues[0]._findBestFormat()
        3.0
        
        >>> _testingValues[1]._findBestFormat()
        1.0
        
        >>> _testingValues[2]._findBestFormat()
        2.0
        
        >>> _testingValues[3]._findBestFormat()
        2.0
        >>> # NOTE: this was formerly 2.5 but since 2.5 is now deprecated, 
        >>> # _findBestFormat never returns 2.5
        
        >>> force = _testingValues[3].__deepcopy__()
        >>> force.preferredFormat = 2.0  # allowed for this dataset, so honored
        >>> force._findBestFormat()
        2.0
        >>> force.preferredFormat = 1.0  # not allowed for this dataset, so will be ignored
        >>> force._findBestFormat()
        2.0
        >>> # See note above regarding format 2.5
        
        >>> _testingValues[4]._findBestFormat()
        4.0
        """
        
        validSet = set()
        
        if len(self) == 0 or self.preferredFormat == 3.0:
            validSet.add(3.0)
        
        if any(k not in self for k in range(len(self))):
            raise IndexError("There are holes in the key set!")
        
        else:
            validSet.add(2.0)
            allValues = set(self.values())
            
            if allValues - standardnames.nameSet:
                # there are names not in the standard list, so we need 2 or 4
                pat = re.compile('^a[0-9A-Fa-f]{4,4}$')
                
                if all(pat.match(value) for value in allValues):
                    validSet.add(4.0)
            
            elif standardnames.nameSet - allValues:
                # there is at least one name not present, so use 2.0 (formerly 2.5)
                validSet.add(2.0)
            
            elif all(s == self[i] for i, s in enumerate(standardnames.names)):
                validSet = set([1.0])
        
        if self.preferredFormat is not None and self.preferredFormat in validSet:
            return self.preferredFormat
        
        return max(validSet)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Post object to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0001 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
        
        >>> utilities.hexdump(_testingValues[2].binaryString())
               0 | 0002 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0003 0024 0025 0102  0642 2E61 6C74 31   |...$.%...B.alt1 |
        
        >>> utilities.hexdump(_testingValues[3].binaryString())
               0 | 0002 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 0003 0026 0025 0024                      |...&.%.$        |
        
        NOTE: the above example formerly used format 2.5, but since that format
        is deprecated, format 2.0 is used instead.
        
        >>> utilities.hexdump(_testingValues[4].binaryString())
               0 | 0004 0000 0000 0000  0000 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  0000 0000 0000 0000 |................|
              20 | 4E00 4E01                                |N.N.            |
        
        %start
        %kind
        protocol method
        %return
        None
        %pos
        w
        A LinkedWriter object to which the binary content for the object will
        be added.
        %kw
        stakeValue
        An optional stake value that will be set at the start of the binary
        data for this object. This can be useful if some higher-level object
        needs to have an offset to this object's data start.
        %end
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self.header.format = formatToUse = self._findBestFormat()
        self.header.buildBinary(w, **kwArgs)
        
        if formatToUse == 1.0 or formatToUse == 3.0:
            pass  # there are no additional data for formats 1 or 3
        
        elif formatToUse == 2.0:
            self._addFormat2(w)
        
        elif formatToUse == 2.5:
            self._addFormat25(w)
        
        else:
            self._addFormat4(w)

    def converted(self, **kwArgs):
        """
        Implementation of 'converted' protocol method.
        
        %start
        %kind
        protocol method
        %return
        A Post object of a different format, converted from self.
        %kw
        returnTokens
        An optional Boolean, default False. If True, returns a tuple of
        ConverterToken objects representing the kinds of conversion valid for
        self.
        %kw
        useToken
        If a token (a ConverterToken object) is provided here, then the actual
        conversion will be done, and the result returned.
        %note
        Use this method to convert the Post object to another format. Note that
        it doesn't make sense to provide both the 'returnTokens' and 'useToken'
        keywords in the same call.
        %end
        """
        
        if kwArgs.get('returnTokens', False):
            CT = convertertoken.ConverterToken
            
            if self.header.format in {1.0, 2.5, 4.0}:
                return (
                  CT('To post format 2.0', lambda x:_asFormat(x, 2.0)),
                  CT('To post format 3.0', lambda x:_asFormat(x, 3.0)))
            
            elif self.header.format == 2.0:
                return (
                  CT('To post format 3.0', lambda x:_asFormat(x, 3.0)),)
            
            elif self.header.format == 3.0:
                return (
                  CT('To post format 2.0', lambda x:_asFormat(x, 2.0)),)
            
        ctk = kwArgs.get('useToken', None)
        
        if ctk:
            return ctk.func(self)

    def detectDuplicates(self):
        """
        Checks for duplicated values. Returns a dict mapping names to lists of
        glyph indices of any duplicates found.
        
        >>> dBad = Post({1:'a', 2:'b', 3:'a'})
        >>> dBad.detectDuplicates()
        {'a': [1, 3]}
        """
        
        dInv = utilities.invertDictFull(self, asSets=True)
        return {k: sorted(list(v)) for k, v in dInv.items() if len(v) > 1}
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Post. However, it
        also does validation via the logging module (the client should have
        done a logging.basicConfig call prior to calling this method, unless a
        logger is passed in via the 'logger' keyword argument).
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = _testingValues[1].binaryString()
        >>> fvb = Post.fromvalidatedbytes
        
        >>> obj = fvb(s, logger=logger)
        test.post - DEBUG - Walker has 32 remaining bytes.
        test.post.postheader - DEBUG - Walker has 32 remaining bytes.
        test.post - INFO - 'post' table is format 1.
        
        >>> fvb(s[0:4], logger=logger)
        test.post - DEBUG - Walker has 4 remaining bytes.
        test.post.postheader - DEBUG - Walker has 4 remaining bytes.
        test.post.postheader - ERROR - Insufficient bytes.
        
        >>> fvb(b'AB' + s[2:], logger=logger)
        test.post - DEBUG - Walker has 32 remaining bytes.
        test.post.postheader - DEBUG - Walker has 32 remaining bytes.
        test.post - ERROR - Unknown 'post' table format 16706.0.
        
        >>> s = _testingValues[2].binaryString()
        >>> fvb(s[:32], logger=logger)
        test.post - DEBUG - Walker has 32 remaining bytes.
        test.post.postheader - DEBUG - Walker has 32 remaining bytes.
        test.post - INFO - 'post' table is format 2.
        test.post - ERROR - Insufficient bytes for format 2 count.
        
        >>> fvb(s[:34], logger=logger)
        test.post - DEBUG - Walker has 34 remaining bytes.
        test.post.postheader - DEBUG - Walker has 34 remaining bytes.
        test.post - INFO - 'post' table is format 2.
        test.post - DEBUG - 'post' count 3
        test.post - ERROR - Insufficient bytes for format 2 data.
        
        >>> fvb(s[:40], logger=logger)
        test.post - DEBUG - Walker has 40 remaining bytes.
        test.post.postheader - DEBUG - Walker has 40 remaining bytes.
        test.post - INFO - 'post' table is format 2.
        test.post - DEBUG - 'post' count 3
        test.post - ERROR - Insufficient bytes for Pascal string length in extra index 0.
        
        >>> fvb(s[:41], logger=logger)
        test.post - DEBUG - Walker has 41 remaining bytes.
        test.post.postheader - DEBUG - Walker has 41 remaining bytes.
        test.post - INFO - 'post' table is format 2.
        test.post - DEBUG - 'post' count 3
        test.post - ERROR - Insufficient bytes for Pascal string in extra index 0.
        
        >>> fvb(s[:41] + utilities.fromhex("A0") + s[42:], logger=logger)
        test.post - DEBUG - Walker has 47 remaining bytes.
        test.post.postheader - DEBUG - Walker has 47 remaining bytes.
        test.post - INFO - 'post' table is format 2.
        test.post - DEBUG - 'post' count 3
        test.post - INFO - The glyph name 'A' for glyph 0 appears to be valid.
        test.post - INFO - The glyph name 'B' for glyph 1 appears to be valid.
        test.post - ERROR - Non-ASCII in name for glyph 2.
        
        <<< s = _testingValues[3].binaryString()
        <<< fvb(s[:32], logger=logger)
        test.post - DEBUG - Walker has 32 remaining bytes.
        test.post.postheader - DEBUG - Walker has 32 remaining bytes.
        test.post - INFO - 'post' table is format 2.5.
        test.post - WARNING - Format 2.5 is deprecated.
        test.post - INFO - Insufficient bytes for format 2.5 count.
        
        <<< fvb(s[:34], logger=logger)
        test.post - DEBUG - Walker has 34 remaining bytes.
        test.post.postheader - DEBUG - Walker has 34 remaining bytes.
        test.post - INFO - 'post' table is format 2.5.
        test.post - WARNING - Format 2.5 is deprecated.
        test.post - INFO - Insufficient bytes for format 2.5 data.
        
        <<< fvb(s[:34] + utilities.fromhex("80") + s[35:], logger=logger)
        test.post - DEBUG - Walker has 37 remaining bytes.
        test.post.postheader - DEBUG - Walker has 37 remaining bytes.
        test.post - INFO - 'post' table is format 2.5.
        test.post - WARNING - Format 2.5 is deprecated.
        test.post - ERROR - Standard name index <0 for format 2.5 glyph 0.

        >>> s = _testingValues[0].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.post - DEBUG - Walker has 32 remaining bytes.
        test.post.postheader - DEBUG - Walker has 32 remaining bytes.
        test.post - INFO - 'post' table is format 3.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('post')
        else:
            logger = logger.getChild('post')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        hdr = postheader.PostHeader.fromvalidatedwalker(
          w,
          logger=logger,
          **kwArgs)
        
        if hdr is None:
            return None
        
        r = cls(header=hdr)
        stdNames = standardnames.names
        
        if hdr.format == 1.0:
            logger.info(('V0121', (), "'post' table is format 1."))
            
            for i, s in enumerate(stdNames):
                r[i] = s
        
        elif hdr.format == 2.0:
            logger.info(('V0121', (), "'post' table is format 2."))
            
            # V0122 and V0123 can be mapped to E2301
            
            if w.length() < 2:
                logger.error(('V0122', (), "Insufficient bytes for format 2 count."))
                return None
            
            count = w.unpack("H")
            logger.debug(('V0123', (count,), "'post' count %d"))
            
            if w.length() < count * 2:
                logger.error(('V0124', (), "Insufficient bytes for format 2 data."))
                return None
            
            indices = w.group("H", count)
            extraCount = max(0, max(indices) - 257)
            pStrings = [None] * extraCount
            
            for i in range(extraCount):
                
                # V0125 and V0126 can be mapped to E2300, E2312, or E2313
                
                if w.length() < 1:
                    logger.error((
                      'V0125',
                      (i,),
                      "Insufficient bytes for Pascal string length in extra index %d."))
                    
                    return None
                
                else:
                    length = w.unpack("B", advance=False)
                    
                    if w.length() < length + 1:  # the +1 because the length byte is still there
                        logger.error(('V0126', (i,), "Insufficient bytes for Pascal string in extra index %d."))
                        return None
                    
                    else:
                        pStrings[i] = w.pascalString()
            
            sawBad = False
            
            for i, sIndex in enumerate(indices):
                try:
                    r[i] = (stdNames[sIndex] if sIndex < 258 else str(pStrings[sIndex - 258], 'ascii'))

                    if utilities.isValidPSName(r[i]):
                        logger.info((
                          'V0929',
                          (r[i], i),
                          "The glyph name '%s' for glyph %d appears to be valid."))
                    else:
                        logger.warning((
                          'V0930',
                          (r[i], i),
                          "The glyph name '%s' for glyph %d is not valid."))
                
                except UnicodeDecodeError:
                    # This is somewhat redundant because of the .isValidPSName
                    # check but has been left in place to keep the 'try' block
                    # intact. """
                    logger.error(('V0127', (i,), "Non-ASCII in name for glyph %d."))
                    sawBad = True
            
            if sawBad:
                return None
        
        elif hdr.format == 2.5:
            logger.info(('V0121', (), "'post' table is format 2.5."))
            logger.warning(('W2303', (), "Format 2.5 is deprecated."))
            
            if w.length() < 2:
                logger.info(('V0128', (), "Insufficient bytes for format 2.5 count."))
                return None
            
            count = w.unpack("H")
            
            if w.length() < count:
                logger.info(('V0129', (), "Insufficient bytes for format 2.5 data."))
                return None
            
            deltas = w.group("b", count)
            sawBad = False
            
            for i, delta in enumerate(deltas):
                actualIndex = i + delta
                
                if actualIndex < 0:
                    logger.error(('V0130', (i,), "Standard name index <0 for format 2.5 glyph %d."))
                    sawBad = True
                
                elif actualIndex >= len(stdNames):
                    logger.error(('V0131', (i,), "Standard name index >257 for format 2.5 glyph %d."))
                    sawBad = True
                
                else:
                    r[i] = stdNames[actualIndex]
            
            if sawBad:
                return None
        
        elif hdr.format == 3.0:
            logger.info(('V0121', (), "'post' table is format 3."))
        
        elif hdr.format == 4.0:
            logger.info(('V0121', (), "'post' table is format 4."))
            
            if w.length() % 2:
                logger.warning(('V0132', (), "'post' format 4 remaining data length is odd."))
            
            t = w.unpackRest("H", strict=False)
            
            for i, x in enumerate(t):
                if x != 0xFFFF:
                    r[i] = "a%0.4X" % (x,)
        
        else:
            logger.error(('E2315', (hdr.format,), "Unknown 'post' table format %s."))
            return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Post object from the specified walker.
        
        >>> _testingValues[1] == Post.frombytes(_testingValues[1].binaryString())
        True
        
        >>> _testingValues[2] == Post.frombytes(_testingValues[2].binaryString())
        True
        
        >>> _testingValues[3] == Post.frombytes(_testingValues[3].binaryString())
        True
        
        >>> _testingValues[4] == Post.frombytes(_testingValues[4].binaryString())
        True
        """
        
        hdr = postheader.PostHeader.fromwalker(w, **kwArgs)
        r = cls(header=hdr)
        stdNames = standardnames.names
        
        if hdr.format == 1.0:
            for i, s in enumerate(stdNames):
                r[i] = s
        
        elif hdr.format == 2.0:
            indices = w.group("H", w.unpack("H"))
            extraCount = max(0, max(indices) - 257)
            pStrings = list(w.pascalString() for i in range(extraCount))
            
            for i, sIndex in enumerate(indices):
                r[i] = (stdNames[sIndex] if sIndex < 258 else str(pStrings[sIndex - 258], 'ascii'))
        
        elif hdr.format == 2.5:
            deltas = w.group("b", w.unpack("H"))
            
            for i, delta in enumerate(deltas):
                r[i] = stdNames[i + delta]
        
        elif hdr.format == 3.0:
            pass
        
        elif hdr.format == 4.0:
            t = w.unpackRest("H", strict=False)
            
            for i, x in enumerate(t):
                if x != 0xFFFF:
                    r[i] = "a%0.4X" % (x,)
        
        else:
            raise ValueError("Unknown 'post' format: %s" % (hdr.format,))
        
        return r
    
    def getReverseMap(self):
        """
        Returns a simple dict mapping names to glyph indices.
        """
        
        return dict(zip(self.values(), self.keys()))
    
    def setPreferredFormat(self, newPreferredFormat):
        """
        Sets the preferred format as indicated. Note that this might be ignored
        if the data do not support a table of the specified format.

        As assertion is made if the preferred format is set to 2.5, as that
        format is now officially obsolete.
        """
        
        assert newPreferredFormat != 2.5
        
        if newPreferredFormat not in frozenset([1.0, 2.0, 3.0, 4.0]):
            raise ValueError("Unsupported format for 'post' table: %s" % (newPreferredFormat,))
        
        self.preferredFormat = newPreferredFormat

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        Post(),  # format 3, essentially
        Post(dict(enumerate(standardnames.names))),  # format 1
        Post({0: 'A', 1: 'B', 2: 'B.alt1'}),  # format 2
        Post({0: 'C', 1: 'B', 2: 'A'}),  # format 2.5
        Post({0: "a4E00", 1: "a4E01"}))  # format 4

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
