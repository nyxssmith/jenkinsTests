#
# matrix_row.py
#
# Copyright © 2007, 2011-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single rows in a Matrix object.
"""

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Classes
#

class Matrix_row(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing single rows in a Matrix. These are lists of exactly
    three values.
    
    >>> print(Matrix_row([1, 2, -1.5]))
    [1, 2, -1.5]
    
    >>> m = Matrix_row([3, 2])
    Traceback (most recent call last):
      ...
    ValueError: Incorrect length for fixed-length object!
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        seq_fixedlength = 3)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
