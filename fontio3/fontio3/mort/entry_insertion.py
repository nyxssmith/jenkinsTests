#
# entry_insertion.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single insertion action for a 'mort' insertion subtable.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.mort import glyphtuple

# -----------------------------------------------------------------------------

#
# Classes
#

class Entry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single entries in an entry table for an insertion
    subtable. These are (effectively) the contents of a single cell in the
    state array.
    
    These are simple objects with the following attributes:
    
        currentInsertBefore     This flag has no effect if currentInsertGlyphs
                                is empty. If it is not empty, then this flag
                                controls whether the insertions will be done
                                upstream (True) or downstream (False).
        
        currentInsertGlyphs     A GlyphTupleOutput object containing the glyphs
                                to be inserted at the current location. Other
                                flags control whether they will be inserted
                                upstream or downstream of the current glyph,
                                and whether the insertion will be kashida-like
                                or split-vowel-like.
        
        currentIsKashidaLike    This flag has no effect if currentInsertGlyphs
                                is empty. If it is not empty, then if this flag
                                is True, then glyphs inserted at the current
                                location will be kashida-like. If False, then
                                the glyphs will be inserted split-vowel-like.
        
        mark                    If True, the current location will be marked
                                for possible subsequent action.
        
        markedInsertBefore      This flag has no effect if markedInsertGlyphs
                                is empty. If it is not empty, then this flag
                                controls whether the insertions will be done
                                upstream (True) or downstream (False).
        
        markedInsertGlyphs      A GlyphTupleOutput object containing the glyphs
                                to be inserted at the marked location. Other
                                flags control whether they will be inserted
                                upstream or downstream of the current glyph,
                                and whether the insertion will be kashida-like
                                or split-vowel-like.
        
        markedIsKashidaLike     This flag has no effect if markedInsertGlyphs
                                is empty. If it is not empty, then if this flag
                                is True, then glyphs inserted at the marked
                                location will be kashida-like. If False, then
                                the glyphs will be inserted split-vowel-like.
        
        newState                A string containing the name of the state to go
                                to after this action is finished.
        
        noAdvance               If True, the glyph pointer won't advance to the
                                next glyph after this action is finished.
    
    >>> _testingValues[0].pprint()
    Name of next state: Start of text
    
    >>> _testingValues[1].pprint()
    Mark current location: True
    Name of next state: SawVowel
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Insert glyphs before current: True
    Glyphs to insert at current:
      0: xyz42
      1: xyz13
      2: xyz45
    Current insertion is kashida-like: False
    Insert glyphs before mark: False
    Glyphs to insert at mark:
      0: xyz72
      1: afii60001
    Marked insertion is kashida-like: False
    Name of next state: DidFirstInsertion
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        currentInsertBefore = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Insert glyphs before current",
            attr_showonlyiffuncobj = (
              lambda value, obj: bool(obj.currentInsertGlyphs))),
        
        currentInsertGlyphs = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphtuple.GlyphTupleOutput,
            attr_label = "Glyphs to insert at current",
            attr_showonlyiftrue = True),
        
        currentIsKashidaLike = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Current insertion is kashida-like",
            attr_showonlyiffuncobj = (
              lambda value, obj: bool(obj.currentInsertGlyphs))),
        
        mark = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Mark current location",
            attr_showonlyiftrue = True),
        
        markedInsertBefore = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Insert glyphs before mark",
            attr_showonlyiffuncobj = (
              lambda value, obj: bool(obj.markedInsertGlyphs))),
        
        markedInsertGlyphs = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphtuple.GlyphTupleOutput,
            attr_label = "Glyphs to insert at mark",
            attr_showonlyiftrue = True),
        
        markedIsKashidaLike = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Marked insertion is kashida-like",
            attr_showonlyiffuncobj = (
              lambda value, obj: bool(obj.markedInsertGlyphs))),
        
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state"),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True))
    
    #
    # Public methods
    #
    
    def isSignificant(self):
        """
        Returns False if the Entry goes to "Start of text" and has no other
        effects. Returns True otherwise.
        
        Note specifically that the currentInsertGlyphs and markedInsertGlyphs
        fields are checked, but not the "InsertBefore" or "IsKashidaLike"
        bits. This is because in the absence of glyph data, those flags are
        effectively NOPs.
        
        >>> _testingValues[0].isSignificant()
        False
        >>> _testingValues[1].isSignificant()
        True
        """
        
        if self.newState != "Start of text":
            return True
        
        if self.mark or self.noAdvance:
            return True
        
        if self.currentInsertGlyphs or self.markedInsertGlyphs:
            return True
        
        return False

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    GT = glyphtuple.GlyphTupleOutput
    
    _testingValues = (
        Entry(),
        
        Entry(newState="SawVowel", mark=True),
        
        Entry(
          newState = "DidFirstInsertion",
          currentInsertGlyphs = GT([41, 12, 44]),
          currentInsertBefore = True,
          markedInsertGlyphs = GT([71, 96])))
    
    del GT

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
