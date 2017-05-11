#
# pairclasses_key.py
#
# Copyright © 2009-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for format 2 GPOS pair positioning tables.
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
    Objects used as keys in a PairClasses dict; these are pairs of class
    indices.

    Objects of this class don't have fromwalker() or buildBinary() methods;
    those are handled at the higher level of the PairGlyphs object itself.
    
    >>> _testingValues[0].pprint()
    0: Class 1
    1: Class 1
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintfunc = (
          lambda p, n, label:
          p.simple("Class %d" % (n,), label=label)),
        item_validatefunc = valassist.isFormat_H,
        seq_fixedlength = 2)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
      Key([1, 1]),
      Key([2, 0]),
      Key([2, 1]))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
