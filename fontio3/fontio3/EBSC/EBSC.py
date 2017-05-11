#
# EBSC.py
#
# Copyright © 2012, 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the 'EBSC' table.
"""

# System imports
import logging

# Other imports
from fontio3.EBSC import table
from fontio3.fontdata import mapmeta

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(obj, **kwArgs):
    logger = kwArgs.pop('logger')
    kwArgs.pop('ppemX', None)
    kwArgs.pop('ppemY', None)
    r = True
    
    for t in obj:
        itemLogger = logger.getChild("(%d, %d)" % t)
        
        rThis = obj[t].isValid(
          logger = logger,
          ppemX = t[0],
          ppemY = t[1],
          **kwArgs)
        
        r = rThis and r
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class EBSC(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire EBSC tables. These are dicts mapping (ppemX,
    ppemY) tuples to Table objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelpresort = True,
        map_validatefunc = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the EBSC object to the specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.add("2L", 0x20000, len(self))
        kwArgs.pop('ppemX', None)
        kwArgs.pop('ppemY', None)
        
        for key in sorted(self):
            obj = self[key]
            obj.buildBinary(w, ppemX=key[0], ppemY=key[1], **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new EBSC object from the specified walker, doing
        source validation.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("EBSC")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, count = w.unpack("2L")
        
        if version != 0x20000:
            logger.error((
              'V0002',
              (version,),
              "Expected version 0x00020000, but got 0x%08X."))
            
            return None
        
        r = cls()
        
        if not count:
            logger.warning((
              'V0818',
              (),
              "The table has a count of zero, and thus has no effect."))
            
            return r
        
        fvw = table.Table.fromvalidatedwalker
        
        while count:
            if w.length() < 26:
                logger.error((
                  'V0819',
                  (),
                  "A bitmapScaleTable was missing or incomplete."))
                
                return None
                  
            t = w.unpack("24x2B", advance=False)
            itemLogger = logger.getChild("(%d, %d)" % t)
            
            if t in r:
                itemLogger.warning((
                  'V0820',
                  (t,),
                  "The (ppemX, ppemY) value %s appears more than once in "
                  "the table. Only the last one will be used."))
            
            obj = fvw(w, logger=itemLogger, **kwArgs)
            
            if obj is None:
                return None
            
            r[t] = obj
            count -= 1
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new EBSC object from the specified walker.
        """
        
        version, count = w.unpack("2L")
        
        if version != 0x20000:
            raise ValueError("Unknown 'EBSC' version: 0x%08X" % (version,))
        
        r = cls()
        fw = table.Table.fromwalker
        
        while count:
            ppemX, ppemY = w.unpack("24x2B", advance=False)
            r[(ppemX, ppemY)] = fw(w, **kwArgs)
            count -= 1
        
        return r

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
