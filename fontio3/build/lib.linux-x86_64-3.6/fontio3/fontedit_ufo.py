#
# fontedit_ufo.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Subclass of fontedit.Editor to read and write UFOs to/from sfnt.
"""

# System imports
import itertools
import os
import plistlib
import struct
import time
from datetime import datetime, timedelta
from xml.dom import minidom
from xml.etree import cElementTree as ET

# Other imports
from fontio3 import(
  fontedit,
  gasp,
  head,
  hhea,
  )
from fontio3.CFF.cffcompositeglyph import CFFCompositeGlyph
from fontio3.utilities import namer, fakeEditor, explode

# -----------------------------------------------------------------------------

#
# Constants (including dispatch tables)
#

_ufoKeyToNameIDMap = (
    ('openTypeNameDesigner', 9),
    ('openTypeNameDesignerURL', 12),
    ('openTypeNameManufacturer', 8),
    ('openTypeNameManufacturerURL', 11),
    ('openTypeNameLicense', 13),
    ('openTypeNameLicenseURL', 14),
    ('openTypeNameVersion', 5),
    ('openTypeNameUniqueID', 3),
    ('openTypeNameDescription', 10),
    ('openTypeNamePreferredFamilyName', 16),
    ('openTypeNamePreferredSubfamilyName', 17),
    ('openTypeNameCompatibleFullName', 18),
    ('openTypeNameSampleText', 19),
    ('openTypeNameWWSFamilyName', 21),
    ('openTypeNameWWSSubfamilyName', 22),
)
  
# -----------------------------------------------------------------------------

#
# Private functions
#

def _maskToBitsList(f):
    """
    NOTE: alternative suggested by Dave below...nicer but needs some
    finagling to work with ulCodePage and UnicodeRanges:
    v = explode(obj.binaryString())
    return list(itertools.compress(list(range(len(v))), reversed(v)))

    Return a list of numbers indicating the bit #s that are set in mask
    'f'. This is accomplished semi-generically for mask types that we
    find in OpenType, e.g. 16-, 32-, 64-, and 128-bit Integers packed in
    Big Endian order.
    
    The [abstract/fontio3] mask is first converted to its binaryString,
    then unpacked and the bits examined.
    
    >>> h = head.head.Head()
    >>> s = h.macStyle
    >>> s.bold = True
    >>> s.italic = True
    >>> _maskToBitsList(s)
    [0, 1]
    """
    v = []
    fbs = f.binaryString()
    if len(fbs) == 2:
        fvi = struct.unpack(">H", fbs)[0]
        nb = 16
    elif len(fbs) == 4:
        fvi = struct.unpack(">I", fbs)[1]
        nb = 32
    elif len(fbs) == 8:
        t = struct.unpack(">II", fbs)
        fvi = (t[1] << 32) + t[0]
        nb = 64
    elif len(fbs) == 16:
        t = struct.unpack(">IIII", fbs)
        fvi = (t[3] << 96) + (t[2] << 64) + (t[1] << 32) + t[0]
        nb = 128
    for b in range(nb):
        p2 = pow(2, b)
        if p2 & fvi == p2:
            v.append(b)
    return v
    
def _macStyleInt(ms):
    """
    Return head.MacStyle 'ms' as an Integer.

    >>> h = head.head.Head()
    >>> s = h.macStyle
    >>> s.bold = True
    >>> s.italic = True
    >>> _macStyleInt(s)
    3
    """
    v = 0
    for k in ms._MASKSORT:
        if ms.__dict__[k]:
            v += pow(2, ms._MASKSPEC[k]['mask_rightmostbitindex'])
    return v
    
def _editorToGLIFs(e, glyphpath, **kwArgs):
    """
    Write the glyphs of editor 'e' in UFO2/GLIF format at 'glyphpath'
    (path to the UFO's "glyphs" folder).
    
    See http://unifiedfontobject.org/versions/ufo2/glif.html
    """
    umap = e.cmap.getUnicodeMap()
    umapRevT = umap.getReverseMapTuple()
    contents = {}
    nmr = fontedit.Editor.getNamer(e)
    
    for gid in range(e.maxp.numGlyphs):
        glyphxml = ET.Element('glyph')
        glyphxml.set('name', nmr.bestNameForGlyphIndex(gid))
        glyphxml.set('format', "1") # the only defined *GLIF* format as of UFO2
    
        advance = ET.SubElement(glyphxml, 'advance')
        advance.set('width', str(e.hmtx[gid].advance))
        if 'vmtx' in e:
            advance.set('height', str(e.vmtx[gid].advance))                        

        if gid in umapRevT:
            for u in umapRevT[gid]:
                # 'unicode' element may appear "any number of times", according to the UFO spec.
                unicode = ET.SubElement(glyphxml, 'unicode')
                unicode.set('hex', "%04X" % (u,))
        
        outline = ET.SubElement(glyphxml, 'outline')
        
        if e.reallyHas('glyf'):
            if e.glyf[gid].isComposite:
                for cmp in e.glyf[gid].components:
                    cmpname = nmr.bestNameForGlyphIndex(cmp.glyphIndex)
                    component = ET.SubElement(outline, 'component')
                    component.set('base', cmpname)
                    if cmp.transformationMatrix[2][0]:
                        component.set('xOffset', str(cmp.transformationMatrix[2][0]))
                    if cmp.transformationMatrix[2][1]:
                        component.set('yOffset', str(cmp.transformationMatrix[2][1]))
                    if cmp.transformationMatrix[0][0] != 1.0:
                        component.set('xScale', str(cmp.transformationMatrix[0][0]))
                    if cmp.transformationMatrix[1][1] != 1.0:
                        component.set('yScale', str(cmp.transformationMatrix[1][1]))
                    if cmp.transformationMatrix[0][1]:
                        component.set('xyScale', str(cmp.transformationMatrix[0][1]))
                    if cmp.transformationMatrix[1][0]:
                        component.set('yxScale', str(cmp.transformationMatrix[1][0]))
            else:
                isStroke = e.glyf[gid].contours.highBit
                for cntr in e.glyf[gid].contours:
                    contour = ET.SubElement(outline, 'contour')
                    for i, pnt in enumerate(cntr):
                        point = ET.SubElement(contour, 'point')
                        point.set('x', str(pnt.x))
                        point.set('y', str(pnt.y))
                        point.set('name', str(i))
                        pntPrev = cntr[i - 1]
                        if isStroke:
                            if i == 0: point.set('type', 'move') # open contour
                            if pnt.onCurve: point.set('type', 'line')
                        else:
                            if pnt.onCurve:
                                if pntPrev.onCurve:
                                    point.set('type', 'line')
                                else:
                                    point.set('type', 'qcurve')
                                    
        elif e.reallyHas('CFF '):
            if isinstance(e['CFF '][gid], CFFCompositeGlyph):
                pass # use same logic as TT?
            elif e['CFF '][gid]:
                for cntr in e['CFF '][gid].contours:
                    contour = ET.SubElement(outline, 'contour')
                    for i, pnt in enumerate(cntr):
                        point = ET.SubElement(contour, 'point')
                        point.set('x', str(pnt.x))
                        point.set('y', str(pnt.y))
                        point.set('name', str(i))
                        pntPrev0 = cntr[i - 1]
                        pntPrev1 = cntr[i - 2]
                        if pnt.onCurve:
                            if pntPrev0.onCurve:
                                point.set('type', 'line')
                            else:
                                assert pntPrev1.onCurve == False # test the following assumption
                                point.set('type', 'curve')

        #lib ?

        contents[glyphxml.get('name')] = "%05d.glif" % (gid,)
        xmltxt = ET.tostring(glyphxml)
        xml = minidom.parseString(xmltxt)
        gfile = open(os.path.join(glyphpath, "%05d.glif" % (gid,)), "w+b")
        gfile.write(xml.toprettyxml(encoding="UTF-8"))

    plistlib.writePlist(contents, os.path.join(glyphpath, "contents.plist"))
    
def _GLIFsToEditor(e, glyphpath, **kwArgs):
    """
    Read the "glyphs" folder and fill out Editor 'e' with the results.
    
    NOT CURRENTLY IMPLEMENTED.
    """
    raise NotImplementedError("Reading UFOs is not currently implemented, sorry!")

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Editor_UFO(fontedit.Editor):
    """
    Editors are the fundamental object allowing access to all font data. They
    are dictionaries mapping keys representing table tags to the living table
    objects.
    
    You may also access tables using attribute notation, except for those
    tables (like 'OS/2' or 'cvt ') that have characters that Python does not
    allow in attribute names.
    """
    
    #
    # Class definition variables
    #

    #
    # Methods
    #
    
    @classmethod
    def fromfolder(cls, path, **kwArgs):
        """
        Synthesize an Editor_UFO from reading a UFO "file" (which is
        actually a folder structure).
        """
        raise NotImplementedError("Reading UFOs is not currently supported, sorry!")

        e = fakeEditor(4, name=True)
        e.head = head.head.Head()
        e.hhea = hhea.Hhea()
        
        #
        # metainfo: http://unifiedfontobject.org/versions/ufo3/metainfo.html
        # ------------------------------------------------------------------
        metainfopath = os.path.join(path, "metainfo.plist")
        metainfo = plistlib.readPlist(metainfopath)
        
        # 
        # fontinfo: http://unifiedfontobject.org/versions/ufo3/fontinfo.html
        # ------------------------------------------------------------------
        fontinfopath = os.path.join(path, "fontinfo.plist")
        if os.path.exists(fontinfopath):
            fontinfo = plistlib.readPlist(fontinfopath)

            # Generic Identification Information
            e.name[(3,1,1033,1)] = fontinfo.get('familyName', 'Unknown')
            e.name[(3,1,1033,2)] = fontinfo.get('styleName', 'Regular')
            if e.name[(3,1,1033,2)] == 'Regular':
                e.name[(3,1,1033,4)] = e.name[(3,1,1033,2)]
            else:
                e.name[(3,1,1033,4)] = "%s %s" % (e.name[(3,1,1033,1)], e.name[(3,1,1033,2)])
            if 'styleMapFamilyName' in fontinfo: pass
            # e.head.macStyle = fontinfo.get('styleMapStyleName', 'Regular')
            vMaj = fontinfo.get('versionMajor', 1)
            vMin = fontinfo.get('versionMinor', 0)
            e.name[(3,1,1033,5)] = "Version %d.%d - imported by fontio3" % (vMaj, vMin)
            e.head.fontRevision = (vMaj * 65536) + (vMin / 65536)

            # Generic Legal Information
            if 'copyright' in fontinfo: e.name[(3,1,1033,0)] = fontinfo['copyright']
            if 'trademark' in fontinfo: e.name[(3,1,1033,7)] = fontinfo['trademark']

            # Generic Dimension Information
            e.head.unitsPerEm = fontinfo.get('unitsPerEm', 2048)
            e.head.descent = fontinfo.get('descender', -410)
            if 'xHeight' in fontinfo: pass
            if 'capHeight' in fontinfo: pass
            e.head.ascent = fontinfo.get('ascender', 1634)
            if 'italicAngle' in fontinfo: pass
            
            # Generic Miscellaneous Information
            if 'note' in fontinfo: pass
            
            # OpenType gasp Table Fields
            if 'openTypeGaspRangeRecords' in fontinfo:
                e.gasp = gasp.gasp.Gasp()
                for rec in fontinfo['openTypeGaspRangeRecords']:
                    pass
                    
            # OpenType head Table Fields
            if 'openTypeHeadCreated' in fontinfo:
                e.head.created = time.strptime(fontinfo['openTypeHeadCreated'], "%Y/%m/%d %H:%M:%S")
            e.head.lowestRecPPEM = fontinfo.get('openTypeHeadLowestRecPPEM', 9)
            if 'openTypeHeadFlags' in fontinfo:
                for bitnum in fontinfo:
                    e.head.flags[
                        { 0: 'baselineAtY0',
                          1: 'sidebearingAtX0',
                          2: 'opticalScalingViaHints',
                          3: 'forcePPEMToInteger',
                          4: 'opticalAdvanceViaHints',
                          5: 'verticalBaselineAtX0',
                          6: 'layoutRequired',
                          7: 'hasDefaultLayoutFeatures',
                          8: 'requiresReordering',
                          9: 'requiresRearrangement',
                          10:'isMicrotypeLossless',
                          11:'isConverted',
                          12:'isClearType'}.get(bitnum)] = True
            
            # OpenType hhea Table Fields
            if 'openTypeHheaAscender' in fontinfo: e.hhea.ascent = fontinfo['openTypeHheaAscender']
            if 'openTypeHheaDescender' in fontinfo: e.hhea.descent = fontinfo['openTypeHheaDescender']
            if 'openTypeHheaLineGap' in fontinfo: e.hhea.lineGap = fontinfo['openTypeHheaLineGap']
            if 'openTypeHheaCaretSlopeRise' in fontinfo: e.hhea.caretSlopeRise = fontinfo['openTypeHheaCaretSlopeRise']
            if 'openTypeHheaCaretSlopeRun' in fontinfo: e.hhea.caretSlopeRun = fontinfo['openTypeHheaCaretSlopeRise']
            if 'openTypeHheaCaretOffset' in fontinfo: e.hhea.caretOffset = fontinfo['openTypeHheaCaretOffset']
            
            # OpenType Name Table Fields
            for k in _ufoKeyToNameIDMap:
                if k[0] in fontinfo: e.name[(3,1,1033,k[1])] = fontinfo[k[0]]
            if 'openTypeNameRecords' in fontinfo:
                for d in fontinfo['openTypeNameRecords']:
                    k = (d['platformID'], d['encodingID'], d['languageID'], d['nameID'])
                    e.name[k] = d['string']


        return e
    
    @classmethod
    def fromvalidatedfolder(cls, path, **kwArgs):
        """
        """
        raise NotImplementedError("Reading UFOs with validation is not currently supported, sorry!")
        

    def writeFolder(self, path, **kwArgs):
        """
        Write an Editor as UFO folder. UFO is a folder structure, so
        'path' names the top-level folder. We will write additional
        files within 'path' according to the UFO spec.
        """
        os.mkdir(path)
        

        ### -----------------------------
        ### metainfo
        meta = dict(
          creator='com.monotype.fontio3',
          formatVersion=2,
          )
        plistlib.writePlist(meta, os.path.join(path, "metainfo.plist"))


        ### -----------------------------
        ### fontinfo
        fvs = "%0.3f" % (self.head.fontRevision/65536.0)
        fvss = fvs.split('.')
        
        fontinfo = dict()

        assert 'name' in self # gotta have a 'name' table...

        # Generic Identification Information
        fontinfo['familyName'] = self.name.getNameFromID(1)
        fontinfo['styleName'] = self.name.getNameFromID(2)
        # fontinfo['styleMapFamilyName'] = "??" # Mac Preferred Family Name?
        # fontinfo['styleMapStyleName'] = "??" # Mac Preferred Family Name?
        fontinfo['versionMajor'] = int(fvss[0])
        fontinfo['versionMinor'] = int(fvss[1])

        # Generic Legal Information
        fontinfo['copyright'] = self.name.getNameFromID(0)
        fontinfo['trademark'] = self.name.getNameFromID(7)
        
        # Generic Dimension Information
        fontinfo['unitsPerEm'] = self.head.unitsPerEm
        fontinfo['descender'] = self.hhea.descent
        if 'OS/2' in self:
            os2 = self['OS/2']
            if os2.version > 1:
                fontinfo['xHeight'] = os2.sxHeight
                fontinfo['capHeight'] = os2.sCapHeight
        fontinfo['ascender'] = self.hhea.ascent
        if 'post' in self: fontinfo['italicAngle'] = self.post.header.italicAngle

        # Generic Miscellaneous Information
        fontinfo['note'] = "Generated by fontio3."
        
        # OpenType head Table Fields
        crd = datetime(1904, 1, 1) + timedelta(seconds = self.head.created)
        fontinfo['openTypeHeadCreated'] = crd.strftime("%Y/%m/%d %H:%M:%S") # "YYYY/MM/DD HH:MM:SS"
        fontinfo['openTypeHeadLowestRecPPEM'] = self.head.lowestRecPPEM
        fontinfo['openTypeHeadFlags'] = _maskToBitsList(self.head.flags)
        
        # OpenType hhea Table Fields
        fontinfo['openTypeHheaAscender'] = self.hhea.ascent
        fontinfo['openTypeHheaDescender'] = self.hhea.descent
        fontinfo['openTypeHheaLineGap'] = self.hhea.lineGap
        fontinfo['openTypeHheaCaretSlopeRise'] = self.hhea.caretSlopeRise
        fontinfo['openTypeHheaCaretSlopeRun'] = self.hhea.caretSlopeRun
        fontinfo['openTypeHheaCaretOffset'] = self.hhea.caretOffset        
        
        # OpenType Name Table Fields
        for k in _ufoKeyToNameIDMap:
            """ Note that fontinfo['openTypeName*'] entries are only made if the
            nameID in question is present in the Editor."""
            if self.name.hasNameID(k[1]) : fontinfo[k[0]] = self.name.getNameFromID(k[1])
        
        # OpenType OS/2 Table Fields
        if 'OS/2' in self:
            os2 = self['OS/2']
            fontinfo['openTypeOS2WidthClass'] = os2.usWidthClass
            fontinfo['openTypeOS2WeightClass'] = os2.usWeightClass
            fss = _maskToBitsList(os2.fsSelection)
            fontinfo['openTypeOS2Selection'] =  list(set(fss) - {0, 5, 6}) # per spec(?), don't set 0, 5 & 6 here
            fontinfo['openTypeOS2VendorID'] = os2.achVendID.decode("ascii")
            fontinfo['openTypeOS2Panose'] = [b for b in os2.panoseArray.binaryString()]
            fontinfo['openTypeOS2FamilyClass'] = (os2.sFamilyClass // 256, os2.sFamilyClass % 256)
            fontinfo['openTypeOS2UnicodeRanges'] = _maskToBitsList(os2.unicodeRanges)
            fontinfo['openTypeOS2CodePageRanges'] = _maskToBitsList(os2.codePageRanges)
            fontinfo['openTypeOS2TypoAscender'] = os2.sTypoAscender
            fontinfo['openTypeOS2TypoDescender'] = os2.sTypoDescender
            fontinfo['openTypeOS2TypoLineGap'] = os2.sTypoLineGap
            fontinfo['openTypeOS2WinAscent'] = os2.usWinAscent
            fontinfo['openTypeOS2WinDescent'] = os2.usWinDescent
            fontinfo['openTypeOS2Type'] = _maskToBitsList(os2.fsType)
            fontinfo['openTypeOS2SubscriptXSize'] = os2.ySubscriptXSize
            fontinfo['openTypeOS2SubscriptYSize'] = os2.ySubscriptYSize
            fontinfo['openTypeOS2SubscriptXOffset'] = os2.ySubscriptXOffset
            fontinfo['openTypeOS2SubscriptYOffset'] = os2.ySubscriptYOffset
            fontinfo['openTypeOS2SuperscriptXSize'] = os2.ySuperscriptXSize
            fontinfo['openTypeOS2SuperscriptYSize'] = os2.ySuperscriptYSize
            fontinfo['openTypeOS2SuperscriptXOffset'] = os2.ySuperscriptXOffset
            fontinfo['openTypeOS2SuperscriptYOffset'] = os2.ySuperscriptYOffset
            fontinfo['openTypeOS2StrikeoutSize'] = os2.yStrikeoutSize
            fontinfo['openTypeOS2StrikeoutPosition'] = os2.yStrikeoutPosition
        
        # OpenType vhea Table Fields
        if 'vhea' in self:
            fontinfo['openTypeVheaVertTypoAscender'] = self.vhea.ascent
            fontinfo['openTypeVheaVertTypoDescender'] = self.vhea.descent
            fontinfo['openTypeVheaVertTypoLineGap'] = self.vhea.lineGap
            fontinfo['openTypeVheaCaretSlopeRise'] = self.vhea.caretSlopeRise
            fontinfo['openTypeVheaCaretSlopeRun'] = self.vhea.caretSlopeRun
            fontinfo['openTypeVheaCaretOffset'] = self.vhea.caretOffset        
        
        # PostScript Specific Data
        if 'CFF ' in self:
            rawCFFObj = self['CFF ']._creationExtras['_CFFObj']
            rawPriv = rawCFFObj[0].private
            fontinfo['postscriptFontName'] = rawCFFObj[0].name.decode("ascii")
            fontinfo['postscriptFullName'] = rawCFFObj[0]['fullName'].decode("ascii")
            # fontinfo['postscriptSlantAngle'] = 
            fontinfo['postscriptUniqueID'] = rawCFFObj[0]['uniqueID']
            # fontinfo['postscriptUnderlineThickness'] = 
            # fontinfo['postscriptUnderlinePosition'] = 
            # fontinfo['postscriptIsFixedPitch'] = 
            if 'BlueValues' in rawPriv: 
                fontinfo['postscriptBlueValues'] = rawPriv['BlueValues']
            if 'OtherBlues' in rawPriv: 
                fontinfo['postscriptOtherBlues'] = rawPriv['OtherBlues']
            # fontinfo['postscriptFamilyBlues'] = 
            # fontinfo['postscriptFamilyOtherBlues'] = 
            # fontinfo['postscriptStemSnapH'] = 
            # fontinfo['postscriptStemSnapV'] = 
            # fontinfo['postscriptBlueFuzz'] = 
            # fontinfo['postscriptBlueShift'] = 
            # fontinfo['postscriptBlueScale'] = 
            # fontinfo['postscriptForceBold'] = 
            if 'defaultWidthX' in rawPriv: 
                fontinfo['postscriptDefaultWidthX'] = rawPriv['defaultWidthX']
            if 'nominalWidthX' in rawPriv: 
                fontinfo['postscriptNominalWidthX'] = rawPriv['nominalWidthX']
            # fontinfo['postscriptWeightName'] = 
            # fontinfo['postscriptDefaultCharacter'] = 
            # fontinfo['postscriptWindowsCharacterSet'] = 
        
        # Macintosh FOND Resource Data...er, maybe not :-)
        
        plistlib.writePlist(fontinfo, os.path.join(path, "fontinfo.plist"))


        ### -----------------------------
        ### groups
        
        # not yet supported
        

        ### -----------------------------
        ### kerning
        
        if 'kern' in self:
            nmr = fontedit.Editor.getNamer(self)
            kernd = {}
            ksort = sorted(self.kern[0].keys())
            curL = -1

            for k in ksort:
                if k[0] != curL:
                    curL = k[0]
                    curR = {}
                    kernd[nmr.bestNameForGlyphIndex(curL)] = curR
                curR[nmr.bestNameForGlyphIndex(k[1])] = self.kern[0][k]
                
            plistlib.writePlist(kernd, os.path.join(path, "kerning.plist"))
                    
        
        ### -----------------------------
        ### features.fea

        # not yet supported


        ### -----------------------------
        ### lib
        libd = {
          'com.monotype.fontio3':1,
          }
        plistlib.writePlist(libd, os.path.join(path, "lib.plist"))


        ### -----------------------------
        ### glyphs folder and contents
        glyphspath = os.path.join(path, "glyphs")
        os.mkdir(glyphspath)
        _editorToGLIFs(self, glyphspath)
        

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
