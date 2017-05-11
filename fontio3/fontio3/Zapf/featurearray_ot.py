#
# featurearray_ot.py
#
# Copyright © 2012-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for arrays of OpenType feature tags.
"""

# System imports
import itertools
import logging

# Other imports
from fontio3.fontdata import seqmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint_item(p, value, label):
    if isinstance(value, str):
        s = value
    
    else:
        try:
            s = str(value, 'ascii')
        except:
            s = repr(value)
    
    p.simple(repr(s), label=label)

def _validate(obj, **kwArgs):
    logger = kwArgs['logger']
    wasBad = False
    
    if not isinstance(obj, bytes):
        try:
            obj = obj.encode('ascii')
        except:
            wasBad = True
    
    if wasBad:
        logger.error((
          'V0750',
          (obj,),
          "The feature tag %r cannot be converted to ASCII."))
        
        return False
    
    if len(obj) != 4:
        logger.error((
          'V0751',
          (str(obj, 'ascii'),),
          "The feature tag %r is not exactly 4 bytes long."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureArray_OT(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a group of OpenType features. These are
    tuples of four-byte feature tags.
    
    >>> _testingValues[1].pprint()
    Feature 0: 'kern'
    Feature 1: 'liga'
    
    >>> logger = utilities.makeDoctestLogger("val")
    >>> e = utilities.fakeEditor(0x10000)
    >>> _testingValues[1].isValid(logger=logger, editor=e)
    True
    
    >>> _testingValues[2].isValid(logger=logger, editor=e)
    val.[0] - ERROR - The feature tag 'too long' is not exactly 4 bytes long.
    val.[1] - ERROR - The feature tag -5.375 cannot be converted to ASCII.
    False
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_pprintfunc = _pprint_item,
        item_pprintlabelfunc = (lambda n: "Feature %d" % (n,)),
        item_validatefunc = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the FeatureArray_OT object to the specified
        writer.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0000 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 0000 0002 6B65 726E  6C69 6761           |....kernliga    |
        """
        
        w.add("L", len(self))
        w.addGroup("4s", self)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureInfo object from the specified walker,
        doing source validation.
        
        >>> s = _testingValues[1].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = FeatureArray_OT.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.featurearray_ot - DEBUG - Walker has 12 remaining bytes.
        
        >>> fvb(s[:3], logger=logger)
        fvw.featurearray_ot - DEBUG - Walker has 3 remaining bytes.
        fvw.featurearray_ot - ERROR - The OT feature count is missing or incomplete.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.featurearray_ot - DEBUG - Walker has 11 remaining bytes.
        fvw.featurearray_ot - ERROR - The OT features are missing or incomplete.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("featurearray_ot")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error((
              'V0747',
              (),
              "The OT feature count is missing or incomplete."))
            
            return None
        
        otCount = w.unpack("L")
        
        if w.length() < 4 * otCount:
            logger.error((
              'V0748',
              (),
              "The OT features are missing or incomplete."))
            
            return None
        
        return cls(w.group("4s", otCount))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureArray_OT object from the specified
        walker.
        
        >>> fb = FeatureArray_OT.frombytes
        >>> for obj in _testingValues[:2]:
        ...   print(obj == fb(obj.binaryString()))
        True
        True
        """
        
        otCount = w.unpack("L")
        return cls(w.group("4s", otCount))

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

def _test():
    import doctest
    doctest.testmod()

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        FeatureArray_OT(),
        FeatureArray_OT([b'kern', b'liga']),
        
        # bad entries start here
        
        FeatureArray_OT([b'too long', -5.375]))

if __name__ == "__main__":
    if __debug__:
        _test()
