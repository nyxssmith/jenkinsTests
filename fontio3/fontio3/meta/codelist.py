 #
# codelist.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for comma-separated lists of Unicode strings in 'meta' table data.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.meta import metautils

# -----------------------------------------------------------------------------

#
# Classes
#

class Codelist(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing lists of Unicode strings, as might be found in the
    'dlng' or 'slng' tags of a Meta object.
    """
    
    seqSpec = dict()
    
    #
    # Methods
    #
    
    def asScriptSet(self):
        """
        Returns CodeList as a tuple of:
            set of invalid ScriptLangTags (may be empty)
            set of script tags extracted from valid ScriptLangTags

        Validity is determined by a regex in metautils, derived from BCP 47 and
        supplied ABNF for ScriptLangTag, from 'meta' spec:
        ScriptLangTag = [language "-"]
                script
                ["-" region]
                *("-" variant)
                *("-" extension)
                ["-" privateuse]
                
        >>> obj = Codelist(['Latn', 'zh-cmn-Hant', 'zh-yue-hant-HK', 'foo-bar-baz'])
        >>> invalid, tagset = obj.asScriptSet()
        >>> sorted(invalid), sorted(tagset)
        (['foo-bar-baz'], ['Hant', 'Latn'])
        """
        
        invalid = set()
        tagset = set()

        for sltag in self:
            scrtag = metautils.scriptfromscriptlangtag(sltag)
            
            if scrtag is not None:
                tagset.update([scrtag.title()])
            else:
                invalid.update([sltag])

        return invalid, tagset
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Codelist object to the specified writer.
        
        >>> obj = Codelist(['abc', 'de', 'fghij'])
        >>> utilities.hexdump(obj.binaryString())
               0 | 6162 632C 2064 652C  2066 6768 696A      |abc, de, fghij  |
        >>> obj = Codelist(['', 'foo'])
        >>> utilities.hexdump(obj.binaryString())
               0 | 666F 6F                                  |foo             |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # remove blank entries
        trimmed = [s for s in self if s.strip() != '']
        
        uStr = ', '.join(trimmed)
        s = uStr.encode('utf-8')
        w.addString(s)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Codelist object from the specified walker,
        doing validation.
        
        >>> s = b'ab,     d,e,  fg  '
        >>> logger = utilities.makeDoctestLogger("test")
        >>> obj = Codelist.fromvalidatedbytes(s, logger=logger)
        test.codelist - DEBUG - Walker has 18 remaining bytes.
        test.codelist - INFO - List contains 4 items
        
        >>> obj.pprint()
        0: ab
        1: d
        2: e
        3: fg
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('codelist')
        else:
            logger = logger.getChild('codelist')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        uStr = str(w.rest(), 'utf-8')
        v = uStr.split(',')
        
        logger.info((
          'Vxxxx',
          (len(v),),
          "List contains %d items"))
        
        return cls(s.strip() for s in v)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Codelist object from the specified walker.
        
        >>> obj = Codelist.frombytes(b'ab,     d,e,  fg  ')
        >>> obj.pprint()
        0: ab
        1: d
        2: e
        3: fg
        """
        
        uStr = str(w.rest(), 'utf-8')
        v = uStr.split(',')
        return cls(s.strip() for s in v)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

