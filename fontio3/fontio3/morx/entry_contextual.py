#
# entry_contextual.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Single entries for a contextual substitution 'morx' subtable.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.morx import glyphdict

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    if obj.mark:
        sv = ["Mark this glyph, then go to state "]
    else:
        sv = ["Go to state "]
    
    sv.append("'%s'" % (obj.newState,))
    
    if obj.noAdvance:
        sv.append(" (without advancing the glyph pointer)")
    
    if obj.markSubstitutionDict:
        sv.append(" after changing the marked glyph thus")
        p.deep(obj.markSubstitutionDict, label=''.join(sv), **k)
        
        if obj.currSubstitutionDict:
            p.deep(
              obj.currSubstitutionDict,
              label = "and changing the current glyph thus",
              **k)
    
    elif obj.currSubstitutionDict:
        sv.append(" after changing the current glyph thus")
        p.deep(obj.currSubstitutionDict, label=''.join(sv), **k)
    
    else:
        p(''.join(sv))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Entry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single entries in an entry table. These are the
    contents of a single cell in the state array.

    These are simple objects with the following attributes:
    
        currSubstitutionDict    A GlyphDict representing how the current glyph
                                should change.
        
        mark                    A Boolean which, if True, causes the current
                                glyph to be marked. A marked glyph may be
                                affected by the markSubstitutionDict of some
                                later Entry. Default is False.
        
        markSubstitutionDict    A GlyphDict representing how the marked glyph
                                should change.
        
        newState                A string representing the new state to go to
                                after this Entry is finished. Default is "Start
                                of text".
        
        noAdvance               A Boolean which, if True, prevents the glyph
                                pointer from advancing to the next glyph after
                                this Entry is finished. Default is False.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Mark this glyph, then go to state 'Saw interesting'
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Go to state 'Start of text' after changing the marked glyph thus:
      xyz16: xyz42
    
    >>> _testingValues[3].pprint(namer=namer.testingNamer())
    Go to state 'Start of text' after changing the current glyph thus:
      xyz62: afii60002
    
    >>> _testingValues[4].pprint(namer=namer.testingNamer())
    Go to state 'Start of text' after changing the marked glyph thus:
      xyz16: xyz42
    and changing the current glyph thus:
      xyz62: afii60002
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        mark = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Mark this glyph",
            attr_showonlyiftrue = True),
        
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state"),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True),
        
        markSubstitutionDict = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphdict.GlyphDict,
            attr_label = "Marked-glyph substitutions",
            attr_showonlyiftrue = True),
        
        currSubstitutionDict = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphdict.GlyphDict,
            attr_label = "Current-glyph substitutions",
            attr_showonlyiftrue = True))
    
    objSpec = dict(
        obj_pprintfunc = _ppf)
    
    #
    # Public methods
    #
    
    def isSignificant(self):
        """
        Returns False if the Entry goes to "Start of text" and has no other
        effects. Returns True otherwise.
        
        >>> _testingValues[0].isSignificant()
        False
        >>> _testingValues[1].isSignificant()
        True
        """
        
        if self.newState != "Start of text":
            return True
        
        if self.mark or self.noAdvance:
            return True
        
        if self.currSubstitutionDict or self.markSubstitutionDict:
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
    
    _testingValues = (
        Entry(),
        
        Entry(newState="Saw interesting", mark=True),
        
        Entry(
          newState = "Start of text",
          markSubstitutionDict = glyphdict.GlyphDict({15: 41})),
        
        Entry(
          newState = "Start of text",
          currSubstitutionDict = glyphdict.GlyphDict({61: 97})),
        
        Entry(
          newState = "Start of text",
          markSubstitutionDict = glyphdict.GlyphDict({15: 41}),
          currSubstitutionDict = glyphdict.GlyphDict({61: 97})))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
