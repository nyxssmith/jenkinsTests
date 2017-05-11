#
# effects.py
#
# Copyright © 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the values returned by all the GSUB subtables' effectsSummary()
methods.
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.opentype import glyphset

# -----------------------------------------------------------------------------

#
# Classes
#

class _GS(glyphset.GlyphSet):
    """
    Subclass of GlyphSet with item_isoutputglyph set True.
    """
    
    #
    # Class definition variables
    #
    
    setSpec = dict(
        item_isoutputglyph = True,
        set_showpresorted = True)  # also inherits all others from GlyphSet

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class _DD(collections.defaultdict):
    def __missing__(self, key):
        v = self[key] = _GS()
        return v

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class EffectsSummary(_DD, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects used to hold the results of a call to a GSUB subtable's
    effectsSummary() method. These are dicts mapping input glyph indices to
    sets of output glyph indices.
    
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> es = EffectsSummary()
    >>> es[19].add(4)
    >>> es[19].add(6)
    >>> es[23].update({10, 11, 97})
    >>> es.pprint(namer=nm)
    xyz20 (glyph 19):
      xyz5 (glyph 4)
      xyz7 (glyph 6)
    xyz24 (glyph 23):
      xyz11 (glyph 10)
      xyz12 (glyph 11)
      afii60002 (glyph 97)
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_makefunc = (lambda s, *a, **k: type(s)(_DD, *a, **k)))
    
    #
    # Methods
    #
    
    def updateSets(self, other, onlyWant=None):
        """
        Update self with other, which should also be an EffectsSummary object.
        If onlyWant is not None, it should be a set containing glyph indices,
        which will be the only ones merged over (input-side only).
        
        >>> es1 = EffectsSummary()
        >>> es1[19].add(4)
        >>> es1[19].add(6)
        >>> es1[23].update({10, 11, 97})
        >>> es1Copy = es1.__deepcopy__()
        >>> es2 = EffectsSummary()
        >>> es2[19].add(25)
        >>> es2[21].add(27)
        >>> es1.updateSets(es2)
        >>> es1.pprint()
        19:
          4
          6
          25
        21:
          27
        23:
          10
          11
          97
        
        >>> es1Copy.updateSets(es2, onlyWant={21, 39})
        >>> es1Copy.pprint()
        19:
          4
          6
        21:
          27
        23:
          10
          11
          97
        """
        
        if onlyWant is None:
            for g, s in other.items():
                self[g].update(s)
        
        else:
            for g, s in other.items():
                if g in onlyWant:
                    self[g].update(s)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
