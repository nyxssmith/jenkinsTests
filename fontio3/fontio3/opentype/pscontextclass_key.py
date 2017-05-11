#
# pscontextclass_key.py
#
# Copyright © 2009-2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for keys used in a PSContextClass object.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing keys in a PSContextClass dict. These are tuples of
    class indices, with one attribute: ruleOrder, a number that indicates the
    relative positioning of those Key tuples with the same first element (lower
    ruleOrders will be written before higher ones).
    
    This class has no fromwalker() or buildBinary() methods; that functionality
    is handled at a higher level.
    
    >>> _testingValues[0].pprint()
    0: Class 1
    1: Class 2
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
        item_pprintfunc = (
          lambda p, n, label:
          p.simple("Class %d" % (n,), label=label)),
        item_validatefunc = valassist.isFormat_H,
        seq_fixedlength = True)
    
    attrSpec = dict(
        ruleOrder = dict(
            attr_ignoreforbool = True,
            attr_initfunc = (lambda: 0),
            attr_label = "Relative order",
            attr_validatefunc = valassist.isNumber))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    
    _testingValues = (
        Key([1, 2], ruleOrder=1),
        Key([1, 3], ruleOrder=0),
        Key([4, 5, 4], ruleOrder=0),
        Key([], ruleOrder=1))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
