#
# glyphclass.py
#
# Copyright © 2009-2012, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to glyph classes.
"""

# Other imports
from fontio3 import utilities
from fontio3.opentype import classdef
from fontio3.utilities import span

# -----------------------------------------------------------------------------

#
# Constants
#

classLabels = {
  0: "(No glyph class)",
  1: "Base glyph",
  2: "Ligature glyph",
  3: "Mark glyph",
  4: "Component glyph"}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, obj, **kwArgs):
    if not obj:
        p.simple("No glyph is assigned a class.", **kwArgs)
        return
    
    nm = kwArgs.get('namer', obj.getNamer())
    
    for i in sorted(classLabels):
        if not i:
            continue
        
        s = {gi for gi, c in obj.items() if c == i}
        
        if not s:
            continue
        
        s = span.Span(s)
        
        if nm is not None:
            sv = []
            nf = nm.bestNameForGlyphIndex
            
            for first, last in s:
                if first == last:
                    sv.append(nf(first))
                else:
                    sv.append("%s - %s" % (nf(first), nf(last)))
            
            p.simple(
              ', '.join(sv),
              label = classLabels[i],
              multilineExtraIndent = 0)
        
        else:
            p.simple(
              str(s),
              label = classLabels[i],
              multilineExtraIndent = 0)

# def _recalc(obj, **kwArgs):
#   It should be possible to define this at some point.

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    # We don't even want a warning if there are gaps, because (for instance)
    # some fonts just don't have ligatures.
    
    allValues = set(obj.values())
    
    if 0 in allValues:
        logger.warning((
          'V0305',
          (),
          "One or more glyphs unnecessarily mapped explicitly to class zero."))
    
    allValues -= set(classLabels)
    
    if allValues:
        logger.error((
          'V0743',
          (sorted(allValues),),
          "The following glyph classes were included but are not valid: %s."))
        
        return False
    
    if editor.reallyHas(b'hmtx'):
        allMarks = {g for g, c in obj.items() if c == 3}
        mtx = editor.hmtx
        badMarks = {g for g in allMarks if mtx[g].advance}
        
        if badMarks:
            logger.error((
              'V1102',
              (sorted(badMarks),),
              "The following mark glyphs have nonzero advances: %s"))
            
            return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GlyphClassTable(classdef.ClassDef):
    """
    Objects identifying glyph classes. These are simple ClassDefTables with a
    slightly different item_pprintfunc.
    
    >>> _testingValues[1].pprint()
    Base glyph: 7
    Ligature glyph: 4-6, 10-11, 15
    
    >>> nm = namer.testingNamer()
    >>> _testingValues[1].pprint(namer=nm)
    Base glyph: xyz8
    Ligature glyph: xyz5 - xyz7, xyz11 - xyz12, xyz16
    
    >>> nm.annotate = True
    >>> _testingValues[1].pprint(namer=nm)
    Base glyph: xyz8 (glyph 7)
    Ligature glyph: xyz5 (glyph 4) - xyz7 (glyph 6), xyz11 (glyph 10) - xyz12 (glyph 11), xyz16 (glyph 15)
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        map_pprintfunc = _pprint,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    @staticmethod
    def _fromeditor_comps_from_glyf(glyfObj, cmapObj):
        r = set()
        uMap = cmapObj.getUnicodeMap()
        allMapped = set(uMap.values())
        
        for d in glyfObj.values():
            if (not d) or (not d.isComposite):
                continue
            
            components = {c.glyphIndex for c in d.components}
            r.update(components - allMapped)
        
        return r
    
    @staticmethod
    def _fromeditor_ligs_from_GSUB(gsubObj):
        r = set()
        wantKindStrings = {"Ligature substitution table"}
        it = gsubObj.features.subtableIterator(kindStringSet = wantKindStrings)
        
        for subtable in it:
            r.update(subtable.gatheredOutputGlyphs())
        
        return r
    
    @staticmethod
    def _fromeditor_marks_from_GPOS(gposObj):
        r = set()
        
        wantKindStrings = (
          "Mark-to-base positioning table",
          "Mark-to-ligature positioning table",
          "Mark-to-mark positioning table")
        
        it = gposObj.features.subtableIterator(
          kindStringSet = set(wantKindStrings))
        
        for subtable in it:
            if subtable.kindString != wantKindStrings[2]:
                # mark-to-base and mark-to-ligature
                r.update(subtable.mark)
            
            else:
                # mark-to-mark
                r.update(subtable.attachingMark)
                r.update(subtable.baseMark)
        
        return r
    
    @classmethod
    def fromeditor(cls, e, **kwArgs):
        """
        Synthesize a new GlyphClassTable from the information in the specified
        Editor. This includes the 'maxp', 'cmap', 'GSUB', 'GPOS', and 'glyf'
        (for TrueType fonts) tables.
        """
        
        kwArgs['editor'] = e
        numGlyphs = utilities.getFontGlyphCount(**kwArgs)
        r = cls({n: 1 for n in range(numGlyphs)})
        allOTGlyphs = set()
        
        if e.reallyHas(b'hmtx'):
            zeroAdvs = {i for i, obj in e.hmtx.items() if not obj.advance}
        else:
            zeroAdvs = set()
        
        if e.reallyHas(b'GPOS'):
            gposMarks = cls._fromeditor_marks_from_GPOS(e.GPOS)
            allOTGlyphs.update(e.GPOS.gatheredInputGlyphs())
            allOTGlyphs.update(e.GPOS.gatheredOutputGlyphs())
        
        else:
            gposMarks = set()
        
        if e.reallyHas(b'GSUB'):
            gsubLigs = cls._fromeditor_ligs_from_GSUB(e.GSUB)
            allOTGlyphs.update(e.GSUB.gatheredInputGlyphs())
            allOTGlyphs.update(e.GSUB.gatheredOutputGlyphs())
        
        else:
            gsubLigs = set()
        
        if e.reallyHas(b'glyf') and e.reallyHas(b'cmap'):
            compGlyphs = cls._fromeditor_comps_from_glyf(e.glyf, e.cmap)
        else:
            compGlyphs = set()
        
        # Now that the various data sources have been gathered, update the
        # new object.
        
        for i in zeroAdvs & gposMarks:
            r[i] = 3  # mark
        
        for i in gsubLigs:
            r[i] = 2  # ligature
        
        for i in compGlyphs - allOTGlyphs:
            r[i] = 4  # component only
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        GlyphClassTable(),
        GlyphClassTable({4: 2, 5: 2, 6: 2, 7: 1, 10: 2, 11: 2, 15: 2}))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
