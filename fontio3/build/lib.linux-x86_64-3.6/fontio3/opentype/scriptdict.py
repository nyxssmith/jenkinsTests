#
# scriptdict.py
#
# Copyright © 2010-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the script list, a top-level construct in GPOS and GSUB tables.
Note that the class defined in this module is a dict, not a list; this allows
random-access by script tag.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta

from fontio3.opentype import (
  langsys,
  langsysdict,
  langsys_optfeatset,
  scriptutilities)

# -----------------------------------------------------------------------------

#
# Functions
#

def _validate(obj, **kwArgs):
    """
    Partial validation of the ScriptList.
    """
    
    logger = kwArgs.get('logger')
    dfltOK = True
    dfltscript = obj.get('DFLT')
    
    if dfltscript:
        if len(dfltscript):
            logger.error((
              'V1000',
              (),
              "DFLT script with non-zero LangSysCount."))
            
            dfltOK = False

        if dfltscript.defaultLangSys is None:
            logger.error((
              'V1001',
              (),
              "DFLT script with NULL DefaultLangSys."))
            
            dfltOK = False

    scriptsOK = True
    
    for scripttag in obj:
        if not scriptutilities.isValidScriptTag(scripttag, logger=logger):
            scriptsOK = False
        
        for langtag in obj[scripttag]:
            if not scriptutilities.isValidLangTag(langtag, logger=logger):
                scriptsOK = False

    return dfltOK and scriptsOK

# -----------------------------------------------------------------------------

#
# Classes
#

class ScriptDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Top-level objects representing OpenType ScriptLists translated into dict
    form, mapping script tags to LangSysDict objects.
    
    >>> _testingValues[0].pprint()
    
    >>> _testingValues[1].pprint()
    Script object latn:
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
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        map_compactremovesfalses = True,
        map_validatefunc_partial = _validate,
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda k: "Script object %s" % (str(k, 'ascii'),)))

    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ScriptDict to the specified LinkedWriter.
        The following keyword arguments are supported:
        
            stakeValue          The stake value to use for the start of the
                                LangSys.
            
            tagToFeatureIndex   A dict mapping feature tags to their equivalent
                                index values within the FeatureList. This
                                argument is required.
        
        >>> ttfi = {b'abcd0001': 4, b'wxyz0003': 5, b'size0002': 9}
        >>> d = {'tagToFeatureIndex': ttfi}
        >>> utilities.hexdump(_testingValues[0].binaryString(**d))
               0 | 0000                                     |..              |
        
        >>> utilities.hexdump(_testingValues[1].binaryString(**d))
               0 | 0001 6C61 746E 0008  0010 0002 656E 4742 |..latn......enGB|
              10 | 001A 656E 5553 0020  0000 0005 0002 0004 |..enUS. ........|
              20 | 0009 0000 0005 0000  0000 FFFF 0002 0004 |................|
              30 | 0009                                     |..              |
        """
        
        assert 'tagToFeatureIndex' in kwArgs
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        sortedTags = sorted(self)
        w.add("H", len(sortedTags))
        objStakes = list(w.getNewStake() for obj in sortedTags)
        
        for i, tag in enumerate(sortedTags):
            w.add("4s", tag)
            w.addUnresolvedOffset("H", stakeValue, objStakes[i])
        
        for i, tag in enumerate(sortedTags):
            self[tag].buildBinary(w, stakeValue=objStakes[i], **kwArgs)

    def featureIndex(self, **kwArgs):
        """
        Returns a dict whose keys are strings identifying a particular script,
        language combination, and whose values are pairs. The first element in
        one of these pairs is a set of required feature tags; the second
        element is a set of optional feature tags.

        Note that the feature tags in the sets are the full 8-byte versions.

        >>> d = _testingValues[2].featureIndex()
        >>> for key in sorted(d):
        ...     print(key, d[key])
        latn/enGB ({b'efgh0001'}, set())
        """

        r = {}

        for scriptTag, lsDict in self.items():
            if lsDict.defaultLangSys is not None:
                ls = lsDict.defaultLangSys

                if ls.requiredFeature is not None:
                    req = {ls.requiredFeature}
                else:
                    req = set()

                pair = (req, set(ls.optionalFeatures))
                r["%s/default" % (str(scriptTag, 'ascii'),)] = pair

            for lsTag, ls in lsDict.items():
                if ls.requiredFeature is not None:
                    req = {ls.requiredFeature}
                else:
                    req = set()

                pair = (req, set(ls.optionalFeatures))
                r["%s/%s" % (str(scriptTag, 'ascii'), str(lsTag, 'ascii'))] = pair

        return r

    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new ScriptDict object from the specified
        FontWorkerSource, with source validation.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> sd = ScriptDict.fromValidatedFontWorkerSource(
        ...   _test_FW_fws2,
        ...   featureIndexToTag = _test_FW_featureIndexToTag,
        ...   logger = logger)
        FW_test.scriptdict - ERROR - line 3 -- incorrect number of tokens, expected 4, found 1
        FW_test.scriptdict - ERROR - line 1 -- did not find matching 'script table end'
        >>> sd.pprint()
        Script object thai:
          LangSys object SAN :
            Optional feature tags:
              mark0002
              mkmk0003
          Default LangSys object:
            Optional feature tags:
              kern0001
              mark0002
              mkmk0003
        """

        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('scriptdict')
        r = cls()
        featureIndexToTag = kwArgs['featureIndexToTag']
        startingLineNumber = fws.lineNumber
        terminalString = 'script table end'

        for line in fws:
            if line.lower() == terminalString:
                return r

            elif len(line) > 0:
                tokens = line.split('\t')

                if len(tokens) != 4:
                    logger.error((
                      'V0957',
                      (fws.lineNumber, len(tokens)),
                      'line %d -- incorrect number of tokens, expected 4, '
                      'found %d'))

                    continue

                scriptTag = tokens[0].strip().encode('ascii')
                langTag = tokens[1].strip().encode('ascii')
                requiredFeatureIndex = tokens[2].strip()

                optionalFeaturesIndicesList = [
                    x.strip()
                    for x in tokens[3].split(',')]

                if requiredFeatureIndex != '':
                    requiredFeature = featureIndexToTag[requiredFeatureIndex]
                else:
                    requiredFeature = None

                optionalFeaturesList = [
                  featureIndexToTag[featureIndex]
                  for featureIndex in optionalFeaturesIndicesList]

                if scriptTag not in r:
                    r[scriptTag] = langsysdict.LangSysDict()

                if langTag == b'default':
                    r[scriptTag].defaultLangSys = langsys.LangSys(
                      requiredFeature = requiredFeature,
                      optionalFeatures = langsys_optfeatset.OptFeatSet(
                        optionalFeaturesList))

                else:
                    langTag += b' '

                    r[scriptTag][langTag] = langsys.LangSys(
                      requiredFeature = requiredFeature,
                      optionalFeatures = langsys_optfeatset.OptFeatSet(
                        optionalFeaturesList))

        logger.error((
          'V0958',
          (startingLineNumber, terminalString),
          "line %d -- did not find matching '%s'"))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ScriptDict object from the specified walker,
        doing source validation. The following keyword arguments are supported:
            
            logger              A logger to which messages will be posted.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild('scriptdict')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        groupCount = w.unpack("H")
        logger.debug(('Vxxxx', (groupCount,), "Group count is %d"))

        if w.length() < 6 * groupCount:
            logger.error((
              'V0413',
              (),
              "The ScriptRecords are missing or incomplete."))
            
            return None
        
        scriptRecs = w.group("4sH", groupCount)
        r = cls()
        fvw = langsysdict.LangSysDict.fromvalidatedwalker
        
        for tag, offset in scriptRecs:
            logger.debug((
              'Vxxxx',
              (utilities.ensureUnicode(tag), offset),
              "Script rec for tag '%s' at offset %d"))

            obj = fvw(
              w.subWalker(offset),
              logger = logger.getChild("script %s" % (utilities.ensureUnicode(tag),)),
              **kwArgs)
            
            if obj is None:
                return None
            
            r[tag] = obj
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ScriptDict object from the specified walker.
        
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
        
        >>> bs = _testingValues[0].binaryString(tagToFeatureIndex=ttfi)
        >>> d = {'featureIndexToTag': fitt}
        >>> _testingValues[0] == ScriptDict.frombytes(bs, **d)
        True
        
        >>> bs = _testingValues[1].binaryString(tagToFeatureIndex=ttfi)
        >>> _testingValues[1] == ScriptDict.frombytes(bs, **d)
        True
        """
        
        r = cls()
        f = langsysdict.LangSysDict.fromwalker
        
        for tag, offset in w.group("4sH", w.unpack("H")):
            r[tag] = f(w.subWalker(offset), **kwArgs)
        
        return r
    
    def tagsRenamed(self, oldToNew):
        """
        Returns a new ScriptDict object where feature tags are changed as in
        the specified dict. If a tag is not in the dict, it is not modified.
        """
        
        d = {}
        
        for tag, obj in self.items():
            d[tag] = obj.tagsRenamed(oldToNew)
        
        return type(self)(d)
    
    def trimToValidFeatures(self, validSet):
        """
        Walks down all contained objects and prunes out any whose feature tags
        are not contained in the specified validSet.
        """
        
        keysToDelete = set()
        
        for key, lsDict in self.items():
            lsDict.trimToValidFeatures(validSet)
            
            if not lsDict:
                keysToDelete.add(key)
        
        for key in keysToDelete:
            del self[key]

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from fontio3.utilities import namer
    from io import StringIO

    lsdtv = langsysdict._testingValues
    
    _testingValues = (
        ScriptDict(),
        ScriptDict({b'latn': lsdtv[2]}),
        ScriptDict({b'latn': lsdtv[4]}))

    del lsdtv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1
    }
    _test_FW_namer._initialized = True

    _test_FW_lookupLineNumbers = {
        'testSingle': 1
    }

    _test_FW_lookupSequenceOrder = {
        'testSingle': 7
    }

    _test_FW_featureIndexToTag = {
        '0': b'kern0001',
        '1': b'mark0002',
        '2': b'mkmk0003',
    }

    _test_FW_fws = FontWorkerSource(StringIO(
        """script table begin
        thai	default		0,1,2
        thai	SAN		1,2
        script table end
        """))

    _test_FW_fws.lineNumber = 1

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """script table begin
        thai	default		0,1,2
        foo
        thai	SAN		1,2
        """))

    _test_FW_fws2.lineNumber = 1

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
