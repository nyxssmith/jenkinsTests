#
# fontedit_svg.py
#
# Copyright © 2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Subclass of fontedit.Editor to read and write SVG-based fonts.
"""

# System imports
from collections import Counter
from xml.dom import minidom
from xml.etree import cElementTree as ET

from fontio3 import fontedit
from fontio3.glyf.ttsimpleglyph import TTSimpleGlyph

# -----------------------------------------------------------------------------

#
# Private functions
#

def _editorTT2SVG(editor, fontETree):
    """
    Convert TrueType glyphs of 'editor' to SVG <glyph> elements,
    as SubElements of fontETree.
    """
    umap = editor.cmap.getUnicodeMap()
    for i in range(32):
        if i in umap: del(umap[i]) # remove mappings <= 0x1F; invalid for XML.
    uitems = sorted(umap.items())
    uitems.insert(0, (None, 0)) # for missing-glyph
    hmtxTbl = editor.hmtx

    advances = Counter([hmtxTbl[g].advance for g in umap.values()])
    fontadvance = advances.most_common(1)[0][0]
    fontETree.set('horiz-adv-x', str(fontadvance))

    for u,g in uitems:
        if u is None:
            elGlyph = ET.SubElement(fontETree, 'missing-glyph')
        else:
            elGlyph = ET.SubElement(fontETree, 'glyph')
            elGlyph.set('unicode', chr(u))

        gwx = hmtxTbl[g].advance
        if gwx != fontadvance:
            elGlyph.set('horiz-adv-x', str(gwx))

        gObj = editor.glyf[g]
        if gObj.isComposite:
            gObj = TTSimpleGlyph.fromcompositeglyph(editor.glyf[g], editor=editor)
        
        dArr = []
        for c in range(len(gObj.contours)):
            cntr = gObj.contours[c].normalized(topLeftFirst=True)
            n = 0
            while n < len(cntr):
                if n == 0:
                    dArr.append("M%d %d" % (cntr[n].x, cntr[n].y))
                    n += 1

                else:
                    ptCurr = cntr[n]
                    ptPrev = cntr[n-1]
                    if n >= 2:
                        ptPrevPrev = cntr[n-2]
                    elif n == 1:
                        ptPrevPrev = cntr[-1]
                    else:
                        print("can't be: ptPrevPrev = 0")
                    ptNext = cntr[n+1] if n < len(cntr)-1 else cntr[0]

                    if ptCurr.onCurve:
                        if ptPrev.x == ptCurr.x:
                            dArr.append("V%d" % (ptCurr.y,))
                        elif ptPrev.y == ptCurr.y:
                            dArr.append("H%d" % (ptCurr.x,))
                        else:
                            dArr.append("L%d %d" % (ptCurr.x, ptCurr.y))
                        n += 1
                            
                    else:
                        pdx = ptPrev.x - ptPrevPrev.x
                        pdy = ptPrev.y - ptPrevPrev.y
                        pcx = ptCurr.x - ptPrev.x
                        pcy = ptCurr.y - ptPrev.y
                        if pdx and pdy and (pdx == pcx) and (pdy == pcy):
                            dArr.append("T%d %d" % (ptNext.x, ptNext.y))
                        else:
                            dArr.append("Q%d %d %d %d" % 
                              (ptCurr.x, ptCurr.y, ptNext.x, ptNext.y))
                        n += 2

            dArr.append("Z")

        elGlyph.set('d', "".join(dArr))

    return fontadvance                    


def _editorCFF2SVG(editor, fontETree):
    """
    Convert CFF glyphs of 'editor' to SVG <glyph> elements,
    as SubElements of fontETree.
    """
    umap = editor.cmap.getUnicodeMap()
    for i in range(32):
        if i in umap: del(umap[i]) # remove mappings <= 0x1F; invalid for XML.
    uitems = sorted(umap.items())
    uitems.insert(0, (None, 0)) # for missing-glyph
    hmtxTbl = editor.hmtx

    advances = Counter([hmtxTbl[g].advance for g in umap.values()])
    fontadvance = advances.most_common(1)[0][0]
    fontETree.set('horiz-adv-x', str(fontadvance))

    for u,g in uitems:
        if u is None:
            elGlyph = ET.SubElement(fontETree, 'missing-glyph')
        else:
            elGlyph = ET.SubElement(fontETree, 'glyph')
            elGlyph.set('unicode', chr(u))

        gwx = hmtxTbl[g].advance
        if gwx != fontadvance:
            elGlyph.set('horiz-adv-x', str(gwx))

        gObj = editor[b'CFF '][g]

#         if gObj.isComposite:
#             gObj = TTSimpleGlyph.fromcompositeglyph(editor.glyf[g], editor=editor)
        
        dArr = []
        if gObj.contours is None: gObj.contours = []
        for c in range(len(gObj.contours)):
            cntr = gObj.contours[c]
            n = 0
            while n < len(cntr):
                if n == 0:
                    dArr.append("M%d %d" % (cntr[n].x, cntr[n].y))
                    n += 1

                else:
                    ptCurr = cntr[n]
                    ptPrev = cntr[n-1]
                    if n >= 2:
                        ptPrevPrev = cntr[n-2]
                    elif n == 1:
                        ptPrevPrev = cntr[-1]
                    else:
                        print("can't be: ptPrevPrev = 0")
                    if n < len(cntr) - 2:
                        ptNext = cntr[n+1]
                        ptNextNext = cntr[n+2]
                    elif n == len(cntr) - 2:
                        ptNext = cntr[n+1]
                        ptNextNext = cntr[0]
                    elif n == len(cntr) - 1:
                        ptNext = cntr[0]
                        ptNextNext = cntr[1]

                    if ptCurr.onCurve:
                        if ptPrev.x == ptCurr.x:
                            dArr.append("V%d" % (ptCurr.y,))
                        elif ptPrev.y == ptCurr.y:
                            dArr.append("H%d" % (ptCurr.x,))
                        else:
                            dArr.append("L%d %d" % (ptCurr.x, ptCurr.y))
                        n += 1
                            
                    else:
                        # need to figure out reflection for Cubic
                        dArr.append("C%d %d %d %d %d %d" %
                          (ptCurr.x,
                          ptCurr.y,
                          ptNext.x,
                          ptNext.y,
                          ptNextNext.x,
                          ptNextNext.y))
                        n += 3

            dArr.append("Z")

        elGlyph.set('d', "".join(dArr))

    return fontadvance                    

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Editor_SVG(fontedit.Editor):
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
    def frompath(cls, path, **kwArgs):
        """
        Synthesize an Editor_SVG from reading a SVG file.
        """
        raise NotImplementedError("Reading SVGs is not currently supported, sorry!")
    
    @classmethod
    def fromvalidatedpath(cls, path, **kwArgs):
        """
        Synthesize an Editor_SVG from reading a SVG file with validation.
        """
        raise NotImplementedError("Reading SVGs with validation is not "
          "currently supported, sorry!")
            

    def writeFont(self, path, fontid, **kwArgs):
        """
        Write an Editor_SVG as SVG font file.
        """
        f = open(path, "wb")

        #--------------
        # <svg> element
        elSVG = ET.Element('svg')
        elSVG.set('xmlns','http://www.w3.org/2000/svg')
        elSVG.set('width', '100%')
        elSVG.set('height', '100%')


        #---------------
        # <defs> element
        elDefs = ET.SubElement(elSVG, 'defs')


        #---------------
        # <font> element
        elFont = ET.SubElement(elDefs, 'font')
        elFont.set('id', fontid)
        

        #--------------------
        # <font-face> element
        elFontFace = ET.SubElement(elFont, 'font-face')
        elFontFace.set('font-family', self.name.getFamilyName())
        if self.head.unitsPerEm != 1000:
            elFontFace.set('units-per-em', str(self.head.unitsPerEm))
        
        pb = self['OS/2'].panoseArray.binaryString()
        ps = [str(b) for b in iter(bytes(pb))]
        elFontFace.set('panose-1', " ".join(ps))
        
        elFontFace.set('ascent', str(self.hhea.ascent))
        elFontFace.set('descent', str(self.hhea.descent))
        elFontFace.set('alphabetic', "0") # baseline position

        #-----------------
        # <glyph> elements
        if b'glyf' in self:
            _editorTT2SVG(self, elFont)
        elif b'CFF ' in self:
            _editorCFF2SVG(self, elFont)
        
        #---------------
        # write svg file
        svgtxt = ET.tostring(elSVG, encoding='utf-8')
        svg = minidom.parseString(svgtxt)
        f.write(svg.toprettyxml(encoding="UTF-8"))
        f.close()        

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
