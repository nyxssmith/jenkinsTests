#
# pscontextglyph_key.py
#
# Copyright © 2009-2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys in a PSContextGlyph dict.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing keys in a PSContextGlyph dict. These are tuples of
    glyph index values, with one attribute: ruleOrder, a number that indicates
    the relative positioning of those Key tuples with the same first element
    (lower ruleOrders will be written before higher ones).
    
    This class has no fromwalker() or buildBinary() methods; that functionality
    is handled at a higher level.
    
    >>> _testingValues[0].pprint(namer=namer.testingNamer())
    0: xyz26
    1: xyz41
    Relative order: 1
    
    Note the ruleOrder attribute is ignored for bool() calls:
    
    >>> _testingValues[3].pprint(namer=namer.testingNamer())
    Relative order: 1
    >>> bool(_testingValues[3])
    False
    """
    
    #
    # Class definition variables
    #
    
    __hash__ = tuple.__hash__
    
    seqSpec = dict(
        item_renumberdirect = True,
        item_usenamerforstr = True,
        seq_fixedlength = True)
    
    attrSpec = dict(
        ruleOrder = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Relative order"))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Key([25, 40], ruleOrder=1),
        Key([25, 50], ruleOrder=0),
        Key([30, 10, 30], ruleOrder=0),
        Key([], ruleOrder=1))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
