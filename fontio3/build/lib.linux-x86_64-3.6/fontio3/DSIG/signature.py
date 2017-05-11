#
# signature.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for Signature Blocks in OpenType 'DSIG' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Private functions
#


def _validate(obj, **kwArgs):
    """
    Validation of the signature
    """
    return True
    
# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Signature(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing signature blocks of DSIG tables.
    
    >>> _testingValues[1].pprint()
    Format: 1
    Signature Bytes: b'testbytes'
    """
    
    #
    # Class definition variables
    #

    objSpec = dict(
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        format = dict(
            attr_initfunc = (lambda:1),
            attr_label = "Format"),
        signatureBytes = dict(
            attr_label = "Signature Bytes"),        
        )

    #
    # Class methods
    #
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new DSIG. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).

        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('signature')
        else:
            logger = logger.getChild('signature')
        
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        r = cls()
        
        r1, r2 = w.unpack("HH")
        if r1 != r2 != 0:
            logger.warning(('V0905', (), "Reserved fields set to non-zero value."))
        
        sLen = w.unpack("L")
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < sLen:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
            
        r.signatureBytes = w.chunk(sLen)
        
        return r

    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Signature object from the data in the specified walker.
        
        >>> h = Signature()
        """
        
        r = cls()
        
        r1, r2, sLen = w.unpack("HHL")
        r.signatureBytes = w.chunk(sLen)
        
        return r
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Signature object to the specified LinkedWriter.
        
        >>> s = b'abcdef012345XYZ'
        >>> utilities.hexdump(Signature(signatureBytes=s).binaryString())
               0 | 0000 0000 0000 000F  6162 6364 6566 3031 |........abcdef01|
              10 | 3233 3435 5859 5A                        |2345XYZ         |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("HH", 0, 0) # reserved1 & 2
        w.add("L", len(self.signatureBytes))
        w.addString(self.signatureBytes)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
      Signature(),
      Signature(signatureBytes=b'testbytes'),
    )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
