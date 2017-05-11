#
# langsysdict.py
#
# Copyright © 2010-2013, 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for OpenType ScriptTables (in a slightly altered form).
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.opentype import langsys

# -----------------------------------------------------------------------------

#
# Classes
#

class LangSysDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing OpenType ScriptTables. These are dicts mapping langsys
    codes to LangSys objects. There is one attribute:
    
        defaultLangSys  A default LangSys object for the script. May be None.
    
    >>> _testingValues[0].pprint()
    
    >>> _testingValues[1].pprint()
    LangSys object enUS:
      Optional feature tags:
        abcd0001
        size0002
    
    >>> _testingValues[2].pprint()
    LangSys object enGB:
      Required feature tag: wxyz0003
    LangSys object enUS:
      Optional feature tags:
        abcd0001
        size0002
    Default LangSys object:
      Required feature tag: wxyz0003
      Optional feature tags:
        abcd0001
        size0002
    
    >>> _testingValues[3].pprint()
    Default LangSys object:
      Optional feature tags:
        abcd0001
        size0002
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (
          lambda k:
          "LangSys object %s" % (ascii(k)[2:-1],)))
    
    attrSpec = dict(
        defaultLangSys = dict(
            attr_followsprotocol = True,
            attr_label = "Default LangSys object",
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the LangSysDict to the specified LinkedWriter.
        The following keyword arguments are supported:
        
            stakeValue          The stake value to use for the start of the
                                LangSys.
            
            tagToFeatureIndex   A dict mapping feature tags to their equivalent
                                index values within the FeatureList. This
                                argument is required.
        
        >>> ttfi = {b'abcd0001': 4, b'wxyz0003': 5, b'size0002': 9}
        >>> d = {'tagToFeatureIndex': ttfi}
        >>> utilities.hexdump(_testingValues[0].binaryString(**d))
               0 | 0000 0000                                |....            |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0000 0001 656E 5553  000A 0000 FFFF 0002 |....enUS........|
              10 | 0004 0009                                |....            |
        
        >>> utilities.hexdump(_testingValues[2].binaryString(**d))
               0 | 0010 0002 656E 4742  001A 656E 5553 0020 |....enGB..enUS. |
              10 | 0000 0005 0002 0004  0009 0000 0005 0000 |................|
              20 | 0000 FFFF 0002 0004  0009                |..........      |
        
        >>> utilities.hexdump(_testingValues[3].binaryString(**d))
               0 | 0004 0000 0000 FFFF  0002 0004 0009      |..............  |
        """
        
        assert 'tagToFeatureIndex' in kwArgs
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self.defaultLangSys is not None:
            dlsStake = w.getNewStake()
            w.addUnresolvedOffset("H", stakeValue, dlsStake)
        else:
            w.add("H", 0)
        
        sortedTags = sorted(self)
        w.add("H", len(sortedTags))
        lsStakes = list(w.getNewStake() for obj in sortedTags)
        
        for i, tag in enumerate(sortedTags):
            w.add("4s", tag)
            w.addUnresolvedOffset("H", stakeValue, lsStakes[i])
        
        if self.defaultLangSys is not None:
            self.defaultLangSys.buildBinary(w, stakeValue=dlsStake, **kwArgs)
        
        for i, tag in enumerate(sortedTags):
            self[tag].buildBinary(w, stakeValue=lsStakes[i], **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LangSysDict object from the specified walker,
        doing source validation. The following keyword arguments are supported:
        
            logger              A logger to which messages will be posted.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('langsysdict')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        defOffset, lsCount = w.unpack("2H")
        
        logger.debug((
          'Vxxxx',
          (defOffset, lsCount),
          "Default offset is %d; langSys count is %d"))
        
        fvw = langsys.LangSys.fromvalidatedwalker
        
        if defOffset:
            defLS = fvw(
              w.subWalker(defOffset),
              logger = logger.getChild("default"),
              **kwArgs)
            
            if defLS is None:
                return None
        
        else:
            defLS = None
        
        r = cls({}, defaultLangSys=defLS)
        
        if w.length() < 6 * lsCount:
            logger.error((
              'V0412',
              (),
              "The LangSys records are missing or incomplete."))
            
            return None
        
        lsRecs = w.group("4sH", lsCount)
        
        for tag, offset in lsRecs:
            logger.debug((
              'Vxxxx',
              (utilities.ensureUnicode(tag), offset),
              "LangSys tag '%s' has offset %d"))
            
            obj = fvw(
              w.subWalker(offset),
              logger = logger.getChild("tag %s" % (utilities.ensureUnicode(tag),)),
              **kwArgs)
            
            if obj is None:
                return None
            
            r[tag] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LangSysDict object from the specified walker.
        The following keyword arguments are supported:
        
            featureIndexToTag   A list, whose indices are original feature list
                                indices and whose values are the feature tags.
                                This argument is required.
        
        >>> fitt = [
        ...   b'aaaa0008',
        ...   b'bbbb0006',
        ...   b'cccc0004',
        ...   b'dddd0005',
        ...   b'abcd0001',
        ...   b'wxyz0003',
        ...   b'eeee0007',
        ...   b'ffff0009',
        ...   b'gggg0010',
        ...   b'size0002']
        >>> ttfi = dict((tag, i) for i, tag in enumerate(fitt))
        >>> d = {'featureIndexToTag': fitt}
        
        >>> bs = _testingValues[0].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[0] == LangSysDict.frombytes(bs, **d)
        True
        
        >>> bs = _testingValues[1].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[1] == LangSysDict.frombytes(bs, **d)
        True
        
        >>> bs = _testingValues[2].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[2] == LangSysDict.frombytes(bs, **d)
        True
        
        >>> bs = _testingValues[3].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[3] == LangSysDict.frombytes(bs, **d)
        True
        """
        
        assert 'featureIndexToTag' in kwArgs
        defOffset = w.unpack("H")
        f = langsys.LangSys.fromwalker
        
        if defOffset:
            defLS = f(w.subWalker(defOffset), **kwArgs)
        else:
            defLS = None
        
        r = cls({}, defaultLangSys=defLS)
        
        for tag, offset in w.group("4sH", w.unpack("H")):
            r[tag] = f(w.subWalker(offset), **kwArgs)
        
        return r
    
    def tagsRenamed(self, oldToNew):
        """
        Returns a new LangSysDict object where feature tags are changed as in
        the specified dict. If a tag is not in the dict, it is not modified.
        """
        
        d = {}
        
        for tag, obj in self.items():
            d[tag] = obj.tagsRenamed(oldToNew)
        
        r = type(self)(d)
        
        if self.defaultLangSys is not None:
            r.defaultLangSys = self.defaultLangSys.tagsRenamed(oldToNew)
        
        return r
    
    def trimToValidFeatures(self, validSet):
        """
        Walks down all contained objects and prunes out any whose feature tags
        are not contained in the specified validSet.
        """
        
        keysToDelete = set()
        
        for key, lsObj in self.items():
            lsObj.trimToValidFeatures(validSet)
            
            if not lsObj:
                keysToDelete.add(key)
        
        for key in keysToDelete:
            del self[key]
        
        if self.defaultLangSys is not None:
            self.defaultLangSys.trimToValidFeatures(validSet)
            
            if not self.defaultLangSys:
                self.defaultLangSys = None

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    lstv = langsys._testingValues
    
    _testingValues = (
        LangSysDict(),
        LangSysDict({b'enUS': lstv[1]}),
        LangSysDict(
          {b'enUS': lstv[1], b'enGB': lstv[2]},
          defaultLangSys=lstv[3]),
        LangSysDict({}, defaultLangSys=lstv[1]),
        LangSysDict({b'enGB': lstv[4]}))
    
    del lstv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
