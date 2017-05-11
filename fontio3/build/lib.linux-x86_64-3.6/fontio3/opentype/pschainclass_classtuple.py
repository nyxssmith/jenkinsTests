#
# pschainclass_classtuple.py
#
# Copyright © 2009-2010, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for tuples of class indices, which are components of Keys used in
PSChainClass objects.
"""

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Classes
#

class ClassTuple(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    This is a tuple of class indices. It is one of the components in a Key.
    
    There are not fromwalker or buildBinary methods; that is handled at the
    higher level of the PSChainClass object itself.
    
    >>> _testingValues[3].pprint()
    0: Class 1
    1: Class 3
    """
    
    #
    # Class definition variables
    #
    
    __hash__ = tuple.__hash__
    
    seqSpec = dict(
        item_pprintfunc = (
          lambda p, x, label:
          p.simple("Class %d" % (x,), label=label)),
        item_validatefunc = valassist.isFormat_H,
        seq_fixedlength = True)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        ClassTuple([]),
        ClassTuple([1, 2]),
        ClassTuple([1]),
        ClassTuple([1, 3]),
        ClassTuple([4, 5, 4]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
