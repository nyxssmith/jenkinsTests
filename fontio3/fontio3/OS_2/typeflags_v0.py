#
# typeflags_v1.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the embedding and subsetting flags in a Version 1 OS/2 table.
"""

# System imports
import collections

# Other imports
from fontio3.fontdata import maskmeta

# -----------------------------------------------------------------------------

#
# Private constants
#

_levelNames = collections.defaultdict(lambda: "Invalid embedding level", {
  0x0000: "Installable Embedding",
  0x0002: "Restricted License Embedding",
  0x0004: "Preview & Print Embedding",
  0x0006: "Preview & Print Embedding (flags 0x0006)",
  0x0008: "Editable Embedding",
  0x000A: "Editable Embedding (flags 0x000A)",
  0x000C: "Editable Embedding (flags 0x000C)",
  0x000E: "Editable Embedding (flags 0x000E)"})
  
# -----------------------------------------------------------------------------

#
# Classes
#

class TypeFlags(object, metaclass=maskmeta.FontDataMetaclass):
    """
    >>> TypeFlags.fromnumber(0).pprint()
    Embedding Level: Installable Embedding
    
    >>> TypeFlags.fromnumber(0x0304).pprint()
    Embedding Level: Preview & Print Embedding
    """
    
    #
    # Class definition variables
    #
    
    maskByteLength = 2
    
    maskControls = dict(
        loggername = "fstype",
        validatecode_notsettozero = "E2102")
    
    maskSpec = dict(
        embeddingLevel = dict(
            mask_bitcount = 4,
            mask_enumstringsdict = _levelNames,
            mask_isenum = True,
            mask_label = "Embedding Level",
            mask_rightmostbitindex = 0))

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
    if __debug__:
        _test()
