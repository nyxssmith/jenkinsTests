#
# entry_ligature.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single ligature action for a 'morx' ligature subtable.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.morx import glyphtupledict

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    if obj.push:
        sv = ["Remember this glyph, then go to state "]
    else:
        sv = ["Go to state "]
    
    sv.append("'%s'" % (obj.newState,))
    
    if obj.noAdvance:
        sv.append(" (without advancing the glyph pointer)")
    
    if obj.actions:
        sv.append(" after doing these substitutions")
        p.deep(obj.actions, label=''.join(sv), **k)
    
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
    Objects representing single cells in a ligature subtable's state array.
    These are simple objects with the following attributes:
    
        actions         A GlyphTupleDict containing the substitution rules for
                        one or more stack levels.
        
        push            A Boolean which, if True, causes the current glyph to
                        be pushed. A pushed glyph may be affected by the
                        actions of some later Entry. Default is False.
        
        newState        A string representing the new state to go to after this
                        Entry is finished. Default is "Start of text".
        
        noAdvance       A Boolean which, if True, prevents the glyph pointer
                        from advancing to the next glyph after this Entry is
                        finished. Default is False.
    
    Note that for 'morx' tables, there is an additional implied flag, the
    performAction flag. This flag's setting is forced to bool(actions).
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Remember this glyph, then go to state 'Saw interesting'
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    Remember this glyph, then go to state 'Start of text' after doing these substitutions:
      (xyz10, xyz16, xyz24) becomes (afii60002, None, None)
      (xyz10, xyz16, xyz31) becomes (afii60003, None, None)
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        actions = dict(
            attr_followsprotocol = True,
            attr_initfunc = glyphtupledict.GlyphTupleDict,
            attr_label = "Actions to perform",
            attr_showonlyiftrue = True),
        
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state"),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True),
        
        push = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Remember this glyph",
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
        
        if self.push or self.noAdvance:
            return True
        
        if self.actions:
            return True
        
        return False
    
    def trimmedToValidEntries(self, lastInputGlyphSet):
        """
        Returns self if all keys in self.actions end with a glyph index that is
        present in lastInputGlyphSet; otherwise returns a new Entry object with
        those entries that don't match trimmed. This may result in an empty
        actions dict.
        
        Important note: we do not trim if self.push is False; in this case, if
        we were to trim we'd be throwing away useful data.
        
        >>> _testingValues[2].trimmedToValidEntries({23, 30}).pprint()
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (9, 15, 23) becomes (97, None, None)
          (9, 15, 30) becomes (98, None, None)
        
        >>> _testingValues[2].trimmedToValidEntries({23, 25}).pprint()
        Remember this glyph, then go to state 'Start of text' after doing these substitutions:
          (9, 15, 23) becomes (97, None, None)
        """
        
        if not self.push:
            return self
        
        dNew = glyphtupledict.GlyphTupleDict()
        
        for key, value in self.actions.items():
            if key[-1] in lastInputGlyphSet:
                dNew[key] = value
        
        if len(dNew) == len(self.actions):
            return self
        
        return type(self)(
          actions = dNew,
          newState = self.newState,
          noAdvance = self.noAdvance,
          push = self.push)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _gtdv = glyphtupledict._testingValues
    
    _testingValues = (
        Entry(),
        Entry(newState="Saw interesting", push=True),
        Entry(newState="Start of text", push=True, actions=_gtdv[2]))
    
    del _gtdv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
