#
# DSIG.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType 'DSIG' tables.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.DSIG import flags, signature

# -----------------------------------------------------------------------------

#
# Private functions
#


def _validate(obj, **kwArgs):
    """
    Validate entire table contents...doing this with a single .recalculated() on the whole table,
    rather than multiple individual field recalculations.
    """
    return True
    
# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class DSIG(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing TrueType 'DSIG' tables. These are simple collections
    of attributes.
    
    >>> _testingValues[0].pprint()
    Version: 1
    Flags: Counter-signatures disallowed = True
    """
    
    #
    # Class definition variables
    #

    seqSpec = dict(
        seq_validatefunc_partial = _validate,
        )
    
    attrSpec = dict(
        version = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Version"),
        flags = dict(
            attr_initfunc = (lambda: flags.Flags(cannotBeResigned=True)),
            attr_label = "Flags"),
        )
        
    attrSorted = ('version', 'flags')

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
        
        >>> l = utilities.makeDoctestLogger("test")
        >>> dmp = "00 00 00 01 00 01 00 01 00 00 00 01 00 00 00 10 00 00 00 14 00 00 00 00 00 00 00 06 30 82 1E 0F 06 09"
        >>> b = utilities.fromhex(dmp)
        >>> d = DSIG.fromvalidatedbytes(b, logger=l)
        test.DSIG - DEBUG - Walker has 34 remaining bytes.
        test.DSIG - INFO - Version 1
        test.DSIG - INFO - DSIG header indicates 1 signatures.
        test.DSIG.signature[0].signature - DEBUG - Walker has 14 remaining bytes.
        test.DSIG.signature[0].signature - DEBUG - Walker has 6 remaining bytes.
        >>> utilities.hexdump(d[0].signatureBytes)
               0 | 3082 1E0F 0609                           |0.....          |
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('DSIG')
        else:
            logger = logger.getChild('DSIG')
        
        logger.debug(('V0001', (w.length(),), "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        r = cls([])
        r.version = w.unpack("L")
        
        if r.version != 1:
            logger.error(('E1409', (r.version,), "Unknown version: 0x%08X."))
            return None
        else:
            logger.info(('V0903', (), "Version 1"))
        
        nSigs = w.unpack("H")
        logger.info(('V0904', (nSigs,), "DSIG header indicates %d signatures."))

        r.flags = flags.Flags.fromvalidatedwalker(w, logger=logger, **kwArgs)

        if w.length() < (12 * nSigs):
            logger.error(('V0004', (), "Insufficient bytes."))
            return None

        sigheaders= w.group("LLL", nSigs)
        for i,sh in enumerate(sigheaders):
            wSub = w.subWalker(0, relative=True, newLimit=sh[1])
            subLogger=logger.getChild("signature[%d]" % (i,))
            sig = signature.Signature.fromvalidatedwalker(wSub, logger=subLogger, **kwArgs)
            sig.format = sh[0]
            r.append(sig)

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new DSIG object from the data in the specified walker.
        
        >>> dmp = "00 00 00 01 00 01 00 01 00 00 00 01 00 00 00 10 00 00 00 14 00 00 00 00 00 00 00 06 30 82 1E 0F 06 09"
        >>> b = utilities.fromhex(dmp)
        >>> d = DSIG.frombytes(b)
        >>> len(d) == 1
        True
        >>> d.version == 1
        True
        >>> utilities.hexdump(d[0].signatureBytes)
               0 | 3082 1E0F 0609                           |0.....          |
        """

        r = cls([])

        r.version = w.unpack("L")
        nSigs = w.unpack("H")
        r.flags = flags.Flags.fromwalker(w, **kwArgs)

        sigheaders= w.group("LLL", nSigs)
        for sh in sigheaders:
            wSub = w.subWalker(0, relative=True, newLimit=sh[1])
            sig = signature.Signature.fromwalker(wSub, **kwArgs)
            sig.format = sh[0]
            r.append(sig)
    
        return r
    
    #
    # Public methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the DSIG object to the specified LinkedWriter.
        
        >>> d = _testingValues[0]
        >>> utilities.hexdump(d.binaryString())
               0 | 0000 0001 0000 0001                      |........        |
        >>> d = _testingValues[1]
        >>> utilities.hexdump(d.binaryString())
               0 | 0000 0001 0002 0001  0000 0001 0000 000C |................|
              10 | 0000 0020 0000 0000  0000 000F 0000 002C |... ...........,|
              20 | 0000 0000 0000 0004  DEAD BEEF 0000 0000 |................|
              30 | 0000 0007 5465 7374  696E 67             |....Testing     |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("L", self.version)
        w.add("H", len(self))
        self.flags.buildBinary(w, **kwArgs)
        
        signatureStakes=[]
        for i,sig in enumerate(self):            
            w.add("L", sig.format)
            w.add("L", len(sig.signatureBytes) + 8)
            signatureStakes.append(w.getNewStake())
            w.addUnresolvedOffset("L", stakeValue, signatureStakes[i])

        for i,sig in enumerate(self):
            w.stakeCurrentWithValue(signatureStakes[i])
            w.addString(sig.binaryString())


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    _testingValues = (
        DSIG(),  # all defaults
        
        DSIG(
          [signature.Signature(format=1, signatureBytes=b'\xDE\xAD\xBE\xEF'),
           signature.Signature(format=0, signatureBytes=b'Testing')],
          version = 1,
          flags = flags.Flags.fromnumber(19),
          ),
    )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
