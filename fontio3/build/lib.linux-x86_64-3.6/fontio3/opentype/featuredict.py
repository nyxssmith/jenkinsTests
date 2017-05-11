#
# featuredict.py
#
# Copyright © 2010-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for feature lists, a top-level construct of GPOS and GSUB tables. Note
that the class defined here derives from dict, not list. This allows random
access by feature tag.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.opentype import featureparams, featuretable, lookup

# -----------------------------------------------------------------------------

#
# Private functions
#

def _mergeKeyFunc(key, inUse, **kwArgs):
    """
    >>> _mergeKeyFunc(b'abcd0001', {b'abcd0002', b'abcd0003'})
    b'abcd0004'
    """
    
    n = int(key[4:8]) + 1
    
    while (key[0:4] + bytes("%04d" % (n,), 'ascii')) in inUse:
        n += 1
    
    return key[0:4] + bytes("%04d" % (n,), 'ascii')

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class FeatureDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects used in place of OpenType FeatureLists. These are dicts instead of
    lists to allow random access by feature tag. They map feature tags to
    FeatureTable objects.
    
    >>> _testingValues[1].pprint(namer=namer.testingNamer())
    Feature 'abcd0001':
      Lookup 0:
        Subtable 0 (Pair (glyph) positioning table):
          (xyz11, xyz21):
            First adjustment:
              FUnit adjustment to origin's x-coordinate: 30
              Device for vertical advance:
                Tweak at 12 ppem: -2
                Tweak at 14 ppem: -1
                Tweak at 18 ppem: 1
            Second adjustment:
              Device for origin's x-coordinate:
                Tweak at 12 ppem: -2
                Tweak at 14 ppem: -1
                Tweak at 18 ppem: 1
              Device for origin's y-coordinate:
                Tweak at 12 ppem: -5
                Tweak at 13 ppem: -3
                Tweak at 14 ppem: -1
                Tweak at 18 ppem: 2
                Tweak at 20 ppem: 3
          (xyz9, xyz16):
            Second adjustment:
              FUnit adjustment to origin's x-coordinate: -10
          (xyz9, xyz21):
            First adjustment:
              Device for vertical advance:
                Tweak at 12 ppem: -2
                Tweak at 14 ppem: -1
                Tweak at 18 ppem: 1
        Lookup flags:
          Right-to-left for Cursive: False
          Ignore base glyphs: True
          Ignore ligatures: False
          Ignore marks: False
        Sequence order (lower happens first): 1
    Feature 'size0002':
      Feature parameters object:
        Design size in decipoints: 80
        Subfamily value: 4
        Name table index of common subfamily: 300
        Small end of usage range in decipoints: 80
        Large end of usage range in decipoints: 120
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_mergekeyfunc = _mergeKeyFunc,
        item_pprintlabelfunc = (lambda k: "Feature '%s'" % (str(k, 'ascii'),)),
        map_compactremovesfalses = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> ll = _getLL()._testingValues[1]
        >>> utilities.hexdump(_testingValues[1].binaryString(lookupList=ll))
               0 | 0002 6162 6364 000E  7369 7A65 0014 0000 |..abcd..size....|
              10 | 0001 0001 0004 0000  0050 0004 012C 0050 |.........P...,.P|
              20 | 0078                                     |.x              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        assert 'lookupList' in kwArgs
        w.add("H", len(self))
        sortedKeys = sorted(self)
        objStakes = list(w.getNewStake() for tag in sortedKeys)
        
        for i, tag in enumerate(sortedKeys):
            w.add("4s", tag)
            w.addUnresolvedOffset("H", stakeValue, objStakes[i])
        
        for i, tag in enumerate(sortedKeys):
            self[tag].buildBinary(w, stakeValue=objStakes[i], **kwArgs)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Creates and returns a new FeatureDict from the specified
        FontWorkerSource with source validation. The following keyword arguments
        are used:
        
            featureIndexToTag   If the client provides this argument, it should
                                be an empty dictionary. When this method
                                returns, the dictionary's contents will be the
                                feature tags. This is used to be able to map
                                from a feature list index to a tag.
            
            forGPOS             True if this FeatureDict is part of the 'GPOS'
                                table; False if it's part of the 'GSUB' table.
                                This keyword argument must be present.
            
            lookupDict          The lookupDict (not used directly in this
                                method, but passed down to the FeatureTable
                                fromwalker() method). This keyword argument
                                must be present.

            lookupLineNumbers   A dictionary mapping lookup names to their
                                corresponding line numbers in the
                                FontWorkerSource.

            lookupSequenceOrder A dictionary mapping lookup names to
                                their corresponding sequence order.
                                
            namer               A Namer object, used for resolving source strings
                                to glyph ids.

            logger              A logger to which messages will be logged. This
                                is optional; one will be created if needed.

        >>> logger = utilities.makeDoctestLogger("FW_test")
        >>> _test_FW_lookupDict = {}
        >>> fd = FeatureDict.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, lookupLineNumbers=_test_FW_lookupLineNumbers, featureIndexToTag=_test_FW_featureIndexToTag, forGPOS=True, lookupDict=_test_FW_lookupDict, lookupSequenceOrder=_test_FW_lookupSequenceOrder, logger=logger, editor={})
        FW_test.featuredict - WARNING - line 7 -- incorrect number of tokens, expected 3, found 1
        FW_test.featuredict.lookup.single - ERROR - line 2 -- incorrect number of tokens, expected 3, found 1
        FW_test.featuredict - WARNING - line 6 -- did not find matching 'feature table end'
        >>> fd.pprint()
        Feature 'kern0001':
          Lookup 0:
            Subtable 0 (Single positioning table):
              1:
                FUnit adjustment to origin's x-coordinate: -456
            Lookup flags:
              Right-to-left for Cursive: False
              Ignore base glyphs: False
              Ignore ligatures: False
              Ignore marks: False
            Lookup name: testSingle
            Sequence order (lower happens first): 7
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('featuredict')
        else:
            logger = logger.getChild('featuredict')

        r = cls()
        featureIndexToTag = kwArgs['featureIndexToTag']
        lookupLineNumbers = kwArgs['lookupLineNumbers']
        terminalString = 'feature table end'
        startingLineNumber= fws.lineNumber

        for line in fws:
            if line.lower() == terminalString:
                return r
            
            if len(line) > 0:
                tokens = line.split('\t')
                
                if len(tokens) != 3:
                    logger.warning((
                      'V0957',
                      (fws.lineNumber, len(tokens)), 
                      'line %d -- incorrect number of tokens, expected 3, '
                      'found %d'))
                    
                    continue
                
                featureIndex = tokens[0]
                featureTag = tokens[1] + '%04d' % (int(featureIndex) + 1)
                featureTag = featureTag.encode('ascii')
                lookupNameList = [x.strip() for x in tokens[2].split(',')]
                
                if (
                  len(lookupNameList) == 1 and
                  lookupNameList[0].isdigit() and
                  lookupNameList[0] not in lookupLineNumbers):
                    
                    # This seems weird, but it is needed to match FontWorker's
                    # output with a GPOS file for the Noori Nastaliq font.
                    # Kamal said he thinks it was an error in the source file.
                    r[featureTag] = r[featureIndexToTag[lookupNameList[0]]]
                
                else:
                    fvfws = lookup.Lookup.fromValidatedFontWorkerSource
                    
                    lookupList = [
                        fvfws(fws, lookupName, logger=logger, **kwArgs)
                        for lookupName in lookupNameList]
                    
                    r[featureTag] = featuretable.FeatureTable(lookupList)
                
                featureIndexToTag[featureIndex] = featureTag
        
        logger.warning((
            'V0958',
            (startingLineNumber, terminalString),
            "line %d -- did not find matching '%s'"))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureDict from the specified walker, doing
        validation of the input source along the way. The following keyword
        arguments are used:
        
            featureIndexToTag   If the client provides this argument, it should
                                be an empty list. When this method returns, the
                                list's contents will be the feature tags. This
                                is used to be able to map from a feature list
                                index to a tag.
            
            forGPOS             True if this FeatureDict is part of the 'GPOS'
                                table; False if it's part of the 'GSUB' table.
                                This keyword argument must be present.
            
            logger              A logger to which messages will be logged. This
                                is optional; one will be created if needed.
            
            lookupList          The LookupList (not used directly in this
                                method, but passed down to the FeatureTable
                                fromwalker() method). This keyword argument
                                must be present.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('featuredict')
        else:
            logger = logger.getChild('featuredict')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        forGPOS = kwArgs['forGPOS']
        assert 'lookupList' in kwArgs
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        count = w.unpack("H")
        logger.debug(('Vxxxx', (count,), "Count is %d"))
        
        if w.length() < 6 * count:
            logger.error((
              'V0316',
              (),
              "Insufficient bytes for FeatureRecords based on count."))
            
            return None
        
        recs = w.group("4sH", count)
        r = cls()
        
        if forGPOS:
            fpMakers = featureparams.dispatchTableGPOS_validated
        else:
            fpMakers = featureparams.dispatchTableGSUB_validated
        
        fvw = featuretable.FeatureTable.fromvalidatedwalker
        v = [None] * len(recs)
        
        for i, t in enumerate(recs):
            subLogger = logger.getChild("feature table %d" % (i,))
            tag, offset = t
            
            logger.debug((
              'Vxxxx',
              (i, utilities.ensureUnicode(tag), offset),
              "Feature %d: tag is '%s', offset is %d"))
            
            tag += (("%04d" % (i + 1,)).encode("ascii"))
            v[i] = tag
            maker = fpMakers.get(tag[:4], None)
            
            obj = fvw(
              w.subWalker(offset),
              fpMaker = maker,
              logger = subLogger,
              **kwArgs)
            
            if obj is not None:
                r[tag] = obj
        
        if 'featureIndexToTag' in kwArgs:
            kwArgs['featureIndexToTag'][:] = v
        
        return r or None
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new FeatureDict from the specified walker. The
        following keyword arguments are used:
        
            featureIndexToTag   If the client provides this argument, it should
                                be an empty list. When this method returns, the
                                list's contents will be the feature tags. This
                                is used to be able to map from a feature list
                                index to a tag.
            
            forGPOS             True if this FeatureDict is part of the 'GPOS'
                                table; False if it's part of the 'GSUB' table.
                                This keyword argument must be present.
            
            lookupList          The LookupList (not used directly in this
                                method, but passed down to the FeatureTable
                                fromwalker() method). This keyword argument
                                must be present.
        
        >>> ll = _getLL()._testingValues[1]
        >>> bs = _testingValues[1].binaryString(lookupList=ll)
        >>> v = []
        >>> _testingValues[1] == FeatureDict.frombytes(
        ...   bs,
        ...   forGPOS = True,
        ...   lookupList = ll,
        ...   featureIndexToTag = v)
        True
        >>> print(v)
        [b'abcd0001', b'size0002']
        """
        
        forGPOS = kwArgs['forGPOS']
        assert 'lookupList' in kwArgs
        recs = w.group("4sH", w.unpack("H"))
        r = cls()
        
        if forGPOS:
            fpMakers = featureparams.dispatchTableGPOS
        else:
            fpMakers = featureparams.dispatchTableGSUB
        
        f = featuretable.FeatureTable.fromwalker
        v = [None] * len(recs)
        
        for i, t in enumerate(recs):
            tag, offset = t
            tag += (("%04d" % (i + 1,)).encode("ascii"))
            v[i] = tag
            maker = fpMakers.get(tag[:4], None)
            r[tag] = f(w.subWalker(offset), fpMaker=maker, **kwArgs)
        
        if 'featureIndexToTag' in kwArgs:
            kwArgs['featureIndexToTag'][:] = v
        
        return r
    
    def subtableIterator(self, kindStringSet=None, **kwArgs):
        """
        Returns a generator over subtables (i.e. Lookup members). If a
        kindStringSet is specified then only subtables with kindString values
        in the set will be included. By default, all subtables will be
        included.
        
        No order is implied here!
        """
        
        kss = kindStringSet
        
        for featTag, featTable in self.items():
            for lookupObj in featTable:
                for subtable in lookupObj:
                    if (kss is None) or (subtable.kindString in kss):
                        yield subtable
    
    def tagsRenamed(self, oldToNew):
        """
        Returns a new FeatureDict object where feature tags are changed as in
        the specified dict. If a tag is not in the dict, it is not modified.
        
        >>> _testingValues[1].tagsRenamed({b'abcd0001': b'abcd0006'}).pprint()
        Feature 'abcd0006':
          Lookup 0:
            Subtable 0 (Pair (glyph) positioning table):
              Key((8, 15)):
                Second adjustment:
                  FUnit adjustment to origin's x-coordinate: -10
              Key((8, 20)):
                First adjustment:
                  Device for vertical advance:
                    Tweak at 12 ppem: -2
                    Tweak at 14 ppem: -1
                    Tweak at 18 ppem: 1
              Key((10, 20)):
                First adjustment:
                  FUnit adjustment to origin's x-coordinate: 30
                  Device for vertical advance:
                    Tweak at 12 ppem: -2
                    Tweak at 14 ppem: -1
                    Tweak at 18 ppem: 1
                Second adjustment:
                  Device for origin's x-coordinate:
                    Tweak at 12 ppem: -2
                    Tweak at 14 ppem: -1
                    Tweak at 18 ppem: 1
                  Device for origin's y-coordinate:
                    Tweak at 12 ppem: -5
                    Tweak at 13 ppem: -3
                    Tweak at 14 ppem: -1
                    Tweak at 18 ppem: 2
                    Tweak at 20 ppem: 3
            Lookup flags:
              Right-to-left for Cursive: False
              Ignore base glyphs: True
              Ignore ligatures: False
              Ignore marks: False
            Sequence order (lower happens first): 1
        Feature 'size0002':
          Feature parameters object:
            Design size in decipoints: 80
            Subfamily value: 4
            Name table index of common subfamily: 300
            Small end of usage range in decipoints: 80
            Large end of usage range in decipoints: 120
        """
        
        d = {}
        
        for tag, obj in self.items():
            d[oldToNew.get(tag, tag)] = obj.__deepcopy__()
        
        return type(self)(d)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    from fontio3.opentype.fontworkersource import FontWorkerSource
    from io import StringIO
    
    def _getLL():
        from fontio3.opentype import lookuplist
        return lookuplist
    
    fttv = featuretable._testingValues
    
    _testingValues = (
        FeatureDict(),
        FeatureDict({b'abcd0001': fttv[0], b'size0002': fttv[2]}),
        
        FeatureDict({
          b'abcd0001': fttv[0],
          b'wxyz0003': fttv[4],
          b'size0002': fttv[2]}),
        
        FeatureDict({b'efgh0001': fttv[5]}))
    
    del fttv

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'A': 1
    }
    _test_FW_namer._initialized = True
    
    _test_FW_lookupLineNumbers = {
        'testSingle': [1]
    }

    _test_FW_lookupSequenceOrder = {
        'testSingle': 7
    }

    _test_FW_featureIndexToTag = {
    }

    _test_FW_fws = FontWorkerSource(StringIO(
        """lookup	testSingle	single
        x placement	A	-123
        lookup end
        
        feature table begin
        0	kern	testSingle
        feature table end
        """))

    _test_FW_fws.lineNumber = 5

    _test_FW_fws2 = FontWorkerSource(StringIO(
        """lookup	testSingle	single
        foo
        x placement	A	-456
        lookup end
        
        feature table begin
        bar
        0	kern	testSingle
        
        """))

    _test_FW_fws2.lineNumber = 6
    

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
