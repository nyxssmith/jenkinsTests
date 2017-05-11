#
# TSIDat.py
#
# Copyright © 2012-15 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for TSI data tables such as TSI1 and TSI3, indexed by a TSILoc.
"""

# System imports
import itertools
import logging
import operator
import re
from urllib.parse import unquote_plus

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.TSI import TSILoc, TSIText
from fontio3.utilities import walker

# -----------------------------------------------------------------------------

#
# Functions
#

def _findglyphnames(s, **kwArgs):
    """
    Utility function to find glyph names in text. This is only useful in items
    of TSI1 tables, since only the composite OFFSET command refers to glyph
    names.
    """

    pat = re.compile(r"S?OFFSET\s*\[\s*[R|r]\s*\]\s*,\s*([a-zA-Z0-9\.\-\_]+)\s*,")
    x = pat.search(s)

    while x is not None:
        start, end = x.start(1), x.end(1)
        yield (start, end - start)
        x = pat.search(s, end)


def _getglyphnames(s, **kwArgs):
    """
    Utility function to return glyph names in text. This basically iterates over
    the results of _findglyphnames, returning the names as a list of strings.

    >>> st = 'OFFSET[R], caron, 100,100'
    >>> _getglyphnames(st)
    ['caron']
    >>> _getglyphnames("asdfasdfasdfasdf")
    []
    """
    
    return [s[st:st+ed] for st,ed in _findglyphnames(s)]

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TSIDat(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing TSI data.
    
    This is a dict of sourceTexts, indexed by glyphID. "Extra" records (for
    'prep', 'cvt ', 'fpgm' text sources) are stored as class attributes.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_pprintlabelfunc=(lambda i: "GlyphID %d" % (i,)),
        item_renumberdirectkeys=True,
        item_followsprotocol=True)

    attrSpec = dict(
        cvt=dict(),
        prep=dict(),
        fpgm=dict())

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for a TSIDat object to the specified LinkedWriter.
        
        Keyword arguments:
        
            locCallback     If the client is interested in getting the TSILoc
                            table constructed during this method's execution,
                            then a callback should be provided. If present,
                            this callback will be called with the new TSILoc
                            object as the sole parameter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 4142 4344 4546 7879  7A                  |ABCDEFxyz       |
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
            
        locObj = TSILoc.TSILoc()

        # normal (glyph) records
        
        walkOffset = 0
        
        for i in range(len(self)):
            item = self.get(i, None)
            
            if item:
                itemText = item.encode('ascii', errors='replace')
            else:
                itemText = b''
            
            itemLen = len(itemText)
            locObj[i] = (itemLen, walkOffset)
            
            if itemText is not None:
                w.addString(itemText)
            
            walkOffset += itemLen

        # extra records: magic, prep, fpgm, cvt, reserved
        locObj.magic = (0, 0xABFC1F34)

        for attr in ['prep', 'fpgm', 'cvt']:
            item = self.__dict__.get(attr, None)
            
            if item:
                itemText = item.encode('ascii', errors='replace')
            else:
                itemText = b''
            
            itemLen = len(itemText)
            locObj.__dict__[attr] = (itemLen, walkOffset)
            
            if itemText is not None:
                w.addString(itemText)
            
            walkOffset += itemLen

        locObj.reserved = (0, walkOffset)
        
        if 'locCallback' in kwArgs:
            kwArgs['locCallback'](locObj)

    @classmethod
    def fromatlasxml(cls, et, **kwArgs):
        """
        Initializes a TSIDat object from the specified [c]ElementTree,
        which should be initialized with the root of an Atlas XML
        document.

        The following keyword arguments are supported:

            editor          An editor for mapping glyphnames to
                            glyphIDs. This is required.

            flavor          'TSI0' or 'TSI2', indicating which table the
                            indexer is. This is required.

            TSILocTable     The index table (TSI0 or TSI2). This is
                            required.
        """

        editor = kwArgs['editor']
        nameToID = editor.post.getReverseMap() if editor.reallyHas(b'post') else {}
        flavor = kwArgs['flavor']
        datTblName = ('TSI1' if flavor == 'TSI0' else 'TSI3')
        r = cls()

        for gl in et.iter('glyph-info'):
            atlasGlyphName = gl.attrib['name']  # try to match to glyphID
            ourGlyphIndex = nameToID.get(atlasGlyphName, None)
            
            if ourGlyphIndex is None:
                # use 'glyph-id' attribute; less reliable,
                # but better than nothing.
                ourGlyphIndex = int(gl.attrib['glyph-id'])

            vtttxt = []
            vttel = gl.find('vtt')
            
            for el in vttel.getchildren():
                if el.tag == "VTTComment":
                    vtttxt.append("/* %s */" % (unquote_plus(el.attrib['text'])))

                elif el.tag == "YAnchor":
                    status = el.attrib['zone-status']
                    
                    if status == "HIT":
                        vtttxt.append("YAnchor(%s, %s) /* %s */" % (
                          el.find('pt').text,
                          el.attrib['cvt'],
                          el.attrib['zone']))
                    
                    elif status == "NEAR":
                        vtttxt.append("YAnchor(%s) /* NEAR %s */" % (
                          el.find('pt').text,
                          el.attrib['zone']))
                    
                    else:
                        vtttxt.append("YAnchor(%s) /* MISS */" % (
                          el.find('pt').text))

                elif el.tag in {"YLink", "YDist", "YShift", "XAnchor",
                  "XLink", "XDist", "XShift", "XNoRound", "YNoRound"}:
                    
                    cnst = {"ge": ", >=", "lt": ", <"}.get(el.get('constraint'), "")
                    ptsstr = ", ".join([p.text for p in el.findall('pt')])
                    vtttxt.append("%s(%s%s)" % (el.tag, ptsstr, cnst))

                elif el.tag in {"YIPAnchor", "YInterpolate", "XIPAnchor",
                  "XInterpolate"}:
                    
                    if el.get('constraint'):
                        vtttxt.append(
                          "/***** constraint unexpected on IPAnchor "
                          "or Interpolate */")
                    
                    pts = [p.text for p in el.findall('pt')]
                    start = pts[0]
                    end = pts[-1]
                    pts.remove(start)
                    pts.remove(end)
                    
                    # split into groups of 29 or less (VTT contsraint)
                    for pt in range(0, len(pts), 29):
                        vtttxt.append("%s(%s, %s, %s)" %
                          (el.tag, start, ", ".join(pts[pt:pt+29]), end))

                elif el.tag == "Inline":
                    vtttxt.append('Inline("')
                    
                    for i in el.getchildren():
                        if i.tag == "call":
                            vtttxt.append(i.attrib['i'])
                    
                    vtttxt.append('")')

                elif el.tag == "Smooth":
                    vtttxt.append("Smooth()")

                else:
                    vtttxt.append("/***** %s: %s */" % (el, el.attrib))

            gTxt = TSIText.TSIText("\r".join(vtttxt))  # Force Mac line endings
            r[ourGlyphIndex] = gTxt

        return r
    
    @classmethod
    def fromValidatedFontChefSource(cls, s, **kwArgs):
        """
        Build a TSIDat from Font Chef source format, with validation.
        The following keyword arguments are required:

            flavor          'VTTTalk' or 'VTTLL' (high-level or low-level)

            logger          A logger to which notices will be posted. This is
                            optional; the default logger will be used if this
                            is not provided.

            namer           A namer-like object with 'glyphIndexFromString'
                            method for resolving glyphname strings to glyph
                            indices.
        """
        
        flavor = kwArgs.get('flavor')
        logger = kwArgs.get('logger')
        namer = kwArgs.get('namer')
        r = cls()
        hdrtoken = s.readline()
        
        if hdrtoken.strip().lower() == 'font chef table %s' % (flavor.lower(),):
            numberedlines = list(enumerate(s.readlines()))
            starts = []
            ends = []
            
            for nline in numberedlines:
                if nline[1].startswith('%s begin ' % (flavor,)):
                    starts.append(nline[0])
                
                if nline[1].startswith('%s end' % (flavor,)):
                    ends.append(nline[0])

            if len(starts) != len(ends):
                logger.error((
                  'Vxxxx',
                  (),
                  "Unequal 'begin' and 'end' tags; aborting."))
                
                return None

            fvw = TSIText.TSIText.fromvalidatedwalker
            
            for tstart, tend in zip(starts, ends):
                gname = numberedlines[tstart][1].replace(
                    "%s begin " % (flavor,), "").strip()
                
                gid = namer.glyphIndexFromString(gname)
                
                if gid is None:
                    logger.warning((
                      'Vxxxx',
                      (gname,),
                      "Could not resolve '%s' to a glyph index in the font; "
                      "skipping this entry."))
                    
                    continue

                txtlines = [nl[1] for nl in numberedlines[tstart + 1: tend]]
                txt = "".join(txtlines).strip()
                
                if flavor == 'VTTLL' and 'OFFSET' in txt:
                    slices = []
                    cgnames = _findglyphnames(txt)
                    curpos = 0
                    
                    for cgstart, cglen in cgnames:
                        slices.append(txt[curpos: cgstart])
                        cgname = txt[cgstart: cgstart + cglen]
                        cgid = namer.glyphIndexFromString(cgname)
                        
                        if cgid is None:
                            logger.warning((
                              'Vxxxx',
                              (cgname, gname, gid),
                              "Glyphname '%s', used in composite glyph %s "
                              "(%d) OFFSET code not found in font. The name "
                              "will be left in the text, but this will fail "
                              "to compile."))
                            
                            slices.append(cgname)
                        
                        else:
                            slices.append(str(cgid))

                        curpos = cgstart + cglen

                    slices.append(txt[curpos:])
                    txt = "".join(slices)

                ttxt = fvw(
                    walker.StringWalker(
                      txt.encode('mac-roman', errors='ignore')))
                
                r[gid] = ttxt

            return r

        else:
            logger.error((
              'Vxxxx',
              (flavor,),
              "Does not appear to be a Font Chef %s dump."))
            
            return None

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker, but with validation.
        
        The following keyword arguments are supported:
        
            flavor              'TSI0' or 'TSI2', indicating which table the
                                indexer is. This is required.
            
            logger              A logger to which notices will be posted. This
                                is optional; the default logger will be used if
                                this is not provided.

            TSILocTable         The index table (TSI0 or TSI2). This is
                                required.
            
        >>> fvb = TSIDat.fromvalidatedbytes
        >>> l = utilities.makeDoctestLogger("test")
        >>> obj = fvb(
        ...   b'ABCDEF',
        ...   TSILocTable = TSILoc.TSILoc({0:(3,0), 1:(3,3)}),
        ...   flavor = 'TSI0')
        >>> obj.pprint()
        GlyphID 0:
          ABC
        GlyphID 1:
          DEF
        cvt: 
        fpgm: 
        prep: 
        """
        
        TSILocTable = kwArgs['TSILocTable']
        flavor = kwArgs['flavor']
        logger = kwArgs.pop('logger', None)
        w_len = w.length()
        datTblName = ('TSI1' if flavor == 'TSI0' else 'TSI3')
        
        if logger is None:
            logger = logging.getLogger().getChild(datTblName)
        else:
            logger = logger.getChild(datTblName)
        
        logger.debug((
          'V0001',
          (w_len,),
          "Walker has %d remaining bytes."))
        
        r = cls()
        fvw = TSIText.TSIText.fromvalidatedwalker
        fvb = TSIText.TSIText.fromvalidatedbytes

        for key in TSILocTable:
            length, offset = TSILocTable[key]
            
            if offset + length > w_len:
                logger.error((
                  'V0488',
                  (offset, length, key, w_len),
                  "Offset/length pair %d,%d for glyph %d exceeds "
                  "table length %d"))

#                 r[key] = None

            elif length > 0:
                itemlogger = logger.getChild("glyph %d" % (key,))
                wSub = w.subWalker(offset, relative=True, newLimit=length)
                r[key] = fvw(wSub, logger=itemlogger)
            
        for attr in ['cvt', 'fpgm', 'prep']:
            length, offset = TSILocTable.__dict__[attr]
            
            if offset + length > w_len:
                logger.error((
                  'V0488',
                  (offset, length, attr, w_len),
                  "Offset/length pair %d,%d for %s exceeds table length %d"))
                r.__dict__[attr] = fvb(b'')

            elif length > 0:
                itemlogger = logger.getChild(attr)
                wSub = w.subWalker(offset, relative=True, newLimit=length)
                r.__dict__[attr] = fvw(wSub, logger=itemlogger, type=attr)

            else:
                r.__dict__[attr] = fvb(b'')


        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Initializes a TSIDat object from the specified walker, using a TSILoc
        object.
        
        The following keyword arguments are supported:
        
            flavor          'TSI0' or 'TSI2', indicating which table the
                            indexer is. This is required.
            
            TSILocTable     The index table (TSI0 or TSI2). This is required.
        """
        
        TSILocTable = kwArgs['TSILocTable']
        flavor = kwArgs['flavor']
        datTblName = ('TSI1' if flavor == 'TSI0' else 'TSI3')
        r = cls()
        fw = TSIText.TSIText.fromwalker
        fb = TSIText.TSIText.frombytes

        for key in TSILocTable:
            length, offset = TSILocTable[key]
            
            if length > 0:
                wSub = w.subWalker(offset, relative=True, newLimit=length)
                r[key] = fw(wSub)
            
            else:
                r[key] = fb(b'')

        for attr in ['cvt', 'fpgm', 'prep']:
            length, offset = TSILocTable.__dict__[attr]
            
            if length > 0:
                wSub = w.subWalker(offset, relative=True, newLimit=length)
                r.__dict__[attr] = fw(wSub, type=attr)

        return r
        
        
    def writeFontChefSource(self, s, **kwArgs):
        """
        Writes the binary data for items to stream 's'. For flavor 'VTTLL',
        replaces glyph indices with glyph names, using the namer object
        specified through kwArgs.
        """
        
        flavor = kwArgs.get('flavor')
        namer = kwArgs.get('namer')

        if namer:
            bnfgi = namer.bestNameForGlyphIndex
        else:
            bnfgi = lambda x: "\#%d" % (x,)

        for i in self:
            gname = bnfgi(i)
            texttowrite = self[i]
            
            if flavor == 'VTTLL' and 'OFFSET' in texttowrite:
                slices = []
                gidlocs = TSIText._findglyphids(texttowrite)
                curpos = 0
                
                for gstart, glen in gidlocs:
                    slices.append(self[i][curpos: gstart])
                    cgidstr = int(self[i][gstart: gstart + glen])
                    cgname = bnfgi(cgidstr)
                    slices.append(cgname)
                    curpos = gstart + glen
                
                slices.append(self[i][curpos:])
                texttowrite = "".join(slices)

            s.write(
              '%s begin %s\n%s\n%s end\n\n' %
              (flavor, gname, texttowrite, flavor))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        TSIDat({0: 'ABCDEF', 1: 'xyz'}),
        )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
