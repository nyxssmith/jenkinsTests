#
# kindnames.py
#
# Copyright © 2010-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definition relating to the 'Zapf' table's KindNames.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.Zapf import kindnamesenum

# -----------------------------------------------------------------------------

#
# Classes
#

class KindNames(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects gathering all sorts of name information for a single glyph. These
    are dicts whose keys are KindNamesEnum objects and whose values are either
    strings or integer values.
    
    >>> _testingValues[0].pprint()
    Adobe name (2): 'ABCD'
    Japanese CID (64): 12288
    Version history note index in 'name' table (68): 272
    
    >>> 2 in _testingValues[0]
    True
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_keyfollowsprotocol = True,
        item_pprintlabelfunc = str,
        item_pprintlabelpresort = True,
        item_strusesrepr = True)
    
    #
    # Methods
    #
    
    def bestName(self):
        """
        Returns a string name from the collection using the most descriptive
        available name. This name will be (in order of preference):
        
            1.  One of the actual names (kindNameEnums 0-63); or
            2.  One of the CID values (with prefatory label); or
            3.  None
        
        >>> KNE = kindnamesenum.KindNamesEnum
        >>> KindNames({KNE(0): "Fred", KNE(64): 12345}).bestName()
        'Fred'
        >>> KindNames({KNE(64): 12345}).bestName()
        'Japanese CID 12345'
        >>> print(KindNames({}).bestName())
        None
        """
        
        availKeys = set(self)
        
        for i in range(5):
            if i in self:
                return self[i]
        
        if 64 in self:
            return "Japanese CID %d" % (self[64],)
        
        if 65 in self:
            return "Traditional Chinese CID %d" % (self[64],)
        
        if 66 in self:
            return "Simplified Chinese CID %d" % (self[64],)
        
        if 67 in self:
            return "Korean CID %d" % (self[64],)
        
        return None
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the KindNames object to the specified
        LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[0].binaryString())
               0 | 0003 0204 4142 4344  4030 0044 0110      |....ABCD@0.D..  |
        """
        
        assert len(self) < 256
        w.add("H", len(self))
        
        for key in sorted(self):
            value = self[key]
            w.add("B", key)
            
            if key < 64:
                b = value.encode('utf-8')
                w.add("B", len(b))
                w.addString(b)
            
            else:
                w.add("H", value)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new KindNames object from the specified walker,
        doing source validation. The walker should point to the nNames field in
        the GlyphInfo structure.
        
        >>> s = _testingValues[0].binaryString()
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> fvb = KindNames.fromvalidatedbytes
        >>> obj = fvb(s, logger=logger)
        fvw.kindnames - DEBUG - Walker has 14 remaining bytes.
        >>> obj == _testingValues[0]
        True
        
        >>> fvb(s[:1], logger=logger)
        fvw.kindnames - DEBUG - Walker has 1 remaining bytes.
        fvw.kindnames - ERROR - Insufficient bytes.
        
        >>> fvb(s[:-1], logger=logger)
        fvw.kindnames - DEBUG - Walker has 13 remaining bytes.
        fvw.kindnames.entry 2 - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("kindnames")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        r = cls()
        KNE = kindnamesenum.KindNamesEnum
        
        for i in range(count):
            itemLogger = logger.getChild("entry %d" % (i,))
            
            if w.length() < 1:
                itemLogger.error(('V0004', (), "Insufficient bytes."))
                return None
            
            key = KNE(w.unpack("B"))
            
            if key > 127:
                itemLogger.error((
                  'V0757',
                  (key,),
                  "KindName code %d is out of range (must be <128)."))
                
                return None
            
            if key < 64:
                if w.length() < 1:
                    itemLogger.error(('V0004', (), "Insufficient bytes"))
                    return None
                
                pLength = w.unpack("B", advance=False)
                
                if w.length() < pLength + 1:
                    itemLogger.error(('V0004', (), "Insufficient bytes"))
                    return None
                
                try:
                    value = str(w.pascalString(), 'utf-8')
                    wasOK = True
                
                except UnicodeDecodeError:
                    wasOK = False
                
                if not wasOK:
                    itemLogger.error((
                      'V0758',
                      (),
                      "Unable to decode string as UTF-8."))
                    
                    return None
            
            else:
                if w.length() < 2:
                    itemLogger.error(('V0004', (), "Insufficient bytes."))
                    return None
                
                value = w.unpack("H")
            
            r[key] = value
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new KindNames object from the data in the
        specified walker, which should point to the nNames field in the
        GlyphInfo structure.
        
        >>> _testingValues[0] == KindNames.frombytes(_testingValues[0].binaryString())
        True
        """
        
        count = w.unpack("H")
        r = cls()
        KNE = kindnamesenum.KindNamesEnum
        
        while count:
            key = KNE(w.unpack("B"))
            
            if key < 64:
                value = str(w.pascalString(), 'utf-8')
            elif key < 128:
                value = w.unpack("H")
            else:
                raise ValueError("KindName kinds above 127 are undefined!")
            
            r[key] = value
            count -= 1
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    KNE = kindnamesenum.KindNamesEnum
    
    _testingValues = (
        KindNames({
            KNE(2): "ABCD",
            KNE(64): 12288,
            KNE(68): 272}),)
    
    del KNE

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
