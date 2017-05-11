#
# runningglyphs.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

# Future imports


# Other imports
from fontio3.fontdata import seqmeta, valuemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Glyph(int, metaclass=valuemeta.FontDataMetaclass):
    """
    Objects representing single glyph indices to be run via the various
    OpenType run() methods. There is one attribute:
    
        originalOffset      The original offset of the glyph. For cases where
                            the glyph is contained in a simple list, this can
                            be the list index.
    
    >>> obj = Glyph(15, originalOffset=4)
    >>> print(obj)
    15, originalOffset = 4
    >>> print(repr(obj))
    Glyph(15, originalOffset=4)
    >>> nm = namer.testingNamer()
    >>> nm.annotate = True
    >>> obj.setNamer(nm)
    >>> print(obj)
    xyz16 (glyph 15), originalOffset = 4
    >>> print((obj.originalOffset))
    4
    >>> obj.shaperClass = 'VMpre'
    >>> print(obj)
    xyz16 (glyph 15), originalOffset = 4, shaperClass = VMpre
    >>> print(repr(obj))
    Glyph(15, originalOffset=4, shaperClass=VMpre)
    """
    
    valueSpec = dict(
        value_isglyphindex = True,
        value_usenamerforstr = True)
    
    attrSpec = dict(
        originalOffset = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: 0)),

        shaperClass = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: None),
            attr_showonlyiftrue = True),
        
        ligInputOffsets = dict(
            attr_ignoreforcomparisons = True,
            attr_showonlyiftrue = True))

    attrSorted = ['originalOffset', 'shaperClass']
    
    #
    # Methods
    #
    
    def __repr__(self):
        """
        """
        
        if self.shaperClass:
            fmt = "Glyph(%d, originalOffset=%s, shaperClass=%s)"
            return fmt % (int(self), self.originalOffset, self.shaperClass)
        
        else:
            fmt = "Glyph(%d, originalOffset=%s)"
            return fmt % (int(self), self.originalOffset)

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class GlyphList(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing sequences of Glyphs. These are what get passed into
    the various run() methods, so the original offset can be tracked.
    """
    
    seqSpec = dict(
        item_followsprotocol = True)
    
    #
    # Methods
    #
    
    def asSimpleTuple(self):
        """
        Returns a simple tuple of simple ints.
        
        >>> obj = GlyphList.fromiterable([36, 36, 15, 98])
        >>> obj.asSimpleTuple()
        (36, 36, 15, 98)
        """
        
        return tuple(int(i) for i in self)
    
    @classmethod
    def fromiterable(cls, it, **kwArgs):
        """
        Returns a new GlyphList from the specified list, which should contain
        integral glyph indices.
        
        Note that if an existing GlyphList is passed in as the iterable, its
        original offsets will be used, and NOT the list indices. You can
        override this behavior by setting the "forceUseSeqIndices" flag in the
        kwArgs to True.
        
        >>> nm = namer.testingNamer()
        >>> nm.annotate = True
        >>> obj = GlyphList.fromiterable([36, 36, 15, 98])
        >>> obj.pprint(namer=nm)
        0:
          Value: xyz37 (glyph 36)
          originalOffset: 0
        1:
          Value: xyz37 (glyph 36)
          originalOffset: 1
        2:
          Value: xyz16 (glyph 15)
          originalOffset: 2
        3:
          Value: afii60003 (glyph 98)
          originalOffset: 3
        
        >>> obj = GlyphList.fromiterable([36, 36, 15, 98], startFrom=35)
        >>> obj.pprint(namer=nm)
        0:
          Value: xyz37 (glyph 36)
          originalOffset: 35
        1:
          Value: xyz37 (glyph 36)
          originalOffset: 36
        2:
          Value: xyz16 (glyph 15)
          originalOffset: 37
        3:
          Value: afii60003 (glyph 98)
          originalOffset: 38
        """
        
        r = cls()
        force = kwArgs.pop('forceUseSeqIndices', False)
        startFrom = kwArgs.pop('startFrom', 0)
        
        for i, n in enumerate(it, start = startFrom):
            if hasattr(n, 'originalOffset') and (not force):
                r.append(n)
            else:
                r.append(Glyph(n, originalOffset=i))
        
        return r

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

