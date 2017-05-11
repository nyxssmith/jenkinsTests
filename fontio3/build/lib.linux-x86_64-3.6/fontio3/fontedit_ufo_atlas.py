#
# fontedit_ufo_atlas.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Subclass of fontedit.Editor to read and write UFOs to/from sfnt with Atlas quirks.
"""

# System imports
import itertools
import os
import plistlib
import stat
import struct
import time
from datetime import datetime, timedelta
from xml.dom import minidom
from xml.etree import cElementTree as ET

# Other imports
from fontio3 import(
  fontedit,
  fontedit_ufo,
  gasp,
  head,
  hhea,
  )

from fontio3.utilities import namer, fakeEditor, explode, onAMac

# -----------------------------------------------------------------------------

#
# Private functions
#


def _editorToGLIFsAtlas(e, glyphpath, **kwArgs):
    """
    Write the glyphs of editor 'e' in UFO2/GLIF format at 'glyphpath'
    (path to the UFO's "glyphs" folder).
        
    kwArgs:
        'groupNamerFunc': a function that returns a group name (string),
        given a glyphID. If none; will use default 'Other'
    """
    umap = e.cmap.getUnicodeMap()
    umapRevT = umap.getReverseMapTuple()
    contents = {}
    nmr = fontedit.Editor.getNamer(e)
    grpnmr = kwArgs.get('groupNamerFunc', None)
    if grpnmr is None: grpnmr = lambda x:'AnyGroup'

    for gid in range(e.maxp.numGlyphs):
        gname = nmr.bestNameForGlyphIndex(gid)
        glyphxml = ET.Element('glyph')
        glyphxml.set('name', gname)
        glyphxml.set('format', "1") # the only defined *GLIF* format as of UFO2
        
        glyphxml.set('id', str(gid))
        glyphxml.set('chargroup', grpnmr(gid))
    
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
                        if pnt.onCurve:
                            point.set('type', 'qcurve')
                            
        else:
            raise NotImplementedError("Atlas supports only TrueType/quadratic curves.")

        contents[glyphxml.get('name')] = "%05d_%s.glif" % (gid, gname)
        xmltxt = ET.tostring(glyphxml)
        xml = minidom.parseString(xmltxt)
        gfile = open(os.path.join(glyphpath, "%05d_%s.glif" % (gid, gname)), "w+b")
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

class Editor_UFO_Atlas(fontedit_ufo.Editor_UFO):
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
        Synthesize an Editor_UFO_Atlas from reading an Atlas UFO "file"
        (which is actually a folder structure).
        """
        raise NotImplementedError("Reading UFOs is not currently supported, sorry!")


    @classmethod
    def fromvalidatedfolder(cls, path, **kwArgs):
        """
        """
        raise NotImplementedError("Reading UFOs with validation is not currently supported, sorry!")
        

    def writeFolderAtlas(self, path, atlasPath, **kwArgs):
        """
        Write an Editor as UFO folder with Atlas quirks. UFO is a folder
        structure, so 'path' names the top-level folder. 'atlasPath'
        specifies the path to the Atlas folder containing atlas_9.jar.
        We will write additional files within 'path' according to the
        UFO spec.
        """
        os.mkdir(path)
        

        ### -----------------------------
        ### metainfo
        meta = dict(
          creator='com.monotype.fontio3',
          formatVersion=1,
          )
        plistlib.writePlist(meta, os.path.join(path, "metainfo.plist"))

        if 'ASCP' in self:
            """
            Presence of an ASCP table indicates that Atlas has already
            been run on this font. So we dump it to a .atlas file inside
            the ufo folder.
            """
            ascp = ET.fromstring(self.ASCP)
            ascpd = ET.ElementTree(ascp)
            ascfpath = os.path.join(path, "%s.atlas" % (ascp.get('fontname'),))
            ascpf = open(ascfpath, "w+b")
            ascpd.write(ascpf, encoding='utf-8', xml_declaration=True)
            ascpf.close()
            
            if 'ASCH' in self:
                """
                Note: this is purposely nested inside the test for
                presence of 'ASCP', which we need for the 'fontname'
                key. Incidence of ASCH without ASCP should be considered
                a font bug.
                """
                aschd = ET.ElementTree(ET.fromstring(self.ASCH))
                ascfpath = os.path.join(path, "%s.xml" % (ascp.get('fontname'),))                
                aschf = open(ascfpath, "w+b")
                aschd.write(aschf, encoding='utf-8', xml_declaration=True)
                aschf.close()

        else:
            """
            No ASCP means the font has not yet been run through Atlas,
            so create a batch/shell command file to run atlas.
            'atlasPath' should indicate the path to the Atlas folder
            containing atlas_9.jar.
            """
            onMac = onAMac()
            batname = "runAtlas.command" if onMac else "runAtlas.bat"
            batpath = os.path.join(path, batname)
            batfile = open(batpath, "w")
            fontinfopath = os.path.abspath(os.path.join(path, "fontinfo.plist"))
            if onMac:
                batfile.writelines( (
                  "#!\n",
                  'ATLASDIR="%s" # Path to Atlas Folder\n' % (atlasPath,),
                  'LAUNCHDIR=${0%/*}\n', 
                  "cd $ATLASDIR\n",
                  'java -jar atlas_9.jar viewer -fontinfo "$LAUNCHDIR/fontinfo.plist" -atlas "$ATLASDIR/simple.atlas" -run -height-defaults\n',
                  ) )

            else:
                batfile.writelines( (
                  'set "ATLASDIR=%s"\n' % (atlasPath,),
                  'set "LAUNCHDIR=%~dp0\n',
                  'cd %ATLASDIR%\n',
                  'java -jar atlas_9.jar viewer -fontinfo "%LAUNCHDIR%/fontinfo.plist" -atlas "%ATLASDIR%/simple.atlas" -run -height-defaults\n',
                  ) )

            batfile.close()
            # Following is equivalent of "chmod +x" using os and stat:
            st = os.stat(batpath)
            os.chmod(batpath, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        ### -----------------------------
        ### fontinfo
        
        fontinfo = dict()

        assert 'name' in self
        assert 'OS/2' in self

        # Atlas fontinfo dict
        fontinfo['ascender'] = self.hhea.ascent
        fontinfo['descender'] = self.hhea.descent
        fontinfo['weightValue'] = self['OS/2'].usWeightClass
        fontinfo['capHeight'] = self['OS/2'].sCapHeight
        fontinfo['xHeight'] = self['OS/2'].sxHeight

        fontinfo['copyright'] = self.name.getNameFromID(0)
        fontinfo['familyName'] = self.name.getNameFromID(1)
        fontinfo['fontName'] = self.name.getNameFromID(6)
        fontinfo['fullName'] = self.name.getNameFromID(4)
        fontinfo['styleName'] = self.name.getNameFromID(2)

        fontinfo['ttUniqueID'] = self.name.getNameFromID(3)
        fontinfo['ttVersion'] = self.name.getNameFromID(5)

        fontinfo['fontstyle'] = 1
        
        fontinfo['unitsPerEm'] = self.head.unitsPerEm

        fvs = "%0.3f" % (self.head.fontRevision/65536.0)
        fvss = fvs.split('.')
        fontinfo['versionMajor'] = int(fvss[0])
        fontinfo['versionMinor'] = int(fvss[1])
        fontinfo['italicAngle'] = self.post.header.italicAngle
        
        plistlib.writePlist(fontinfo, os.path.join(path, "fontinfo.plist"))


        ### -----------------------------
        ### groups
        
        # not implemented in Atlas
        

        ### -----------------------------
        ### kerning
        
        # not implemented in Atlas


        ### -----------------------------
        ### features.fea

        # not implemented in Atlas


        ### -----------------------------
        ### lib

        # not implemented in Atlas


        ### -----------------------------
        ### glyphs folder and contents
        glyphspath = os.path.join(path, "glyphs")
        os.mkdir(glyphspath)
        _editorToGLIFsAtlas(self, glyphspath, **kwArgs)


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
