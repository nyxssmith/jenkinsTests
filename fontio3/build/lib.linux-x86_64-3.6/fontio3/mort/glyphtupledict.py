#
# glyphtupledict.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for mappings from an input sequence of glyphs to an output sequence.
"""

# System imports
import operator

# Other imports
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, d, **kwArgs):
    nm = kwArgs.get('namer', d.getNamer())
    
    for tIn, tOut in sorted(d.items(), key=operator.itemgetter(0)):
        tInCopy = tIn.__copy__()
        tInCopy.setNamer(nm)
        tOutCopy = tOut.__copy__()
        tOutCopy.setNamer(nm)
        p("%s becomes %s" % (tInCopy, tOutCopy))

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GlyphTupleDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    A GlyphTupleDict maps GlyphTupleInput objects to GlyphTupleOutput objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    (xyz14, xyz41) becomes (xyz26, None)
    
    >>> _testingValues[2].pprint(namer=namer.testingNamer())
    (xyz10, xyz16, xyz24) becomes (afii60002, None, None)
    (xyz10, xyz16, xyz31) becomes (afii60003, None, None)
    
    Note that tuples are tuples, so it's OK to index with a raw tuple:
    
    >>> _testingValues[1][(13, 40)]
    GlyphTupleOutput((25, None))
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_keyfollowsprotocol = True,
        item_usenamerforstr = True,
        map_pprintfunc = _ppf)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.mort import glyphtuple
    from fontio3.utilities import namer
    
    GTI = glyphtuple.GlyphTupleInput
    GTO = glyphtuple.GlyphTupleOutput
    
    _testingValues = (
        GlyphTupleDict(),
        
        GlyphTupleDict({GTI((13, 40)): GTO((25, None))}),
        
        GlyphTupleDict({
            GTI((9, 15, 23)): GTO((97, None, None)),
            GTI((9, 15, 30)): GTO((98, None, None))}))
    
    del GTO, GTI

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
