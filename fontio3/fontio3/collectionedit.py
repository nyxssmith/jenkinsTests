#
# collectionedit.py
#
# Copyright © 2011-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for collections of unrelated fonts.
"""

# System imports
import functools
import logging

# Other imports
from fontio3 import fontedit
from fontio3.fontdata import deferreddictmeta, seqmeta
from fontio3.utilities import filewalkerbit

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate_item(obj, **kwArgs):
    kwArgs.pop('editor', None)
    logger = kwArgs.pop('logger')
    subLogger = logger.getChild("Collection")

    if obj.reallyHas(b'DSIG'):
        logger.warning((
          'Vxxxx',
          (),
          "TTC component font contains DSIG table."))
    
    return deferreddictmeta.M_isValid(
      obj,
      editor = obj,
      logger = subLogger,
      **kwArgs)

def _validate_sequence(seq, **kwArgs):
    """
    Dummy function to be wired up with seq_validatefunc_partial; otherwise the
    sub-Editors' .isValid don't get called.
    """
    
    pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class CollectionEditor(list, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing a group of unrelated fonts. These are lists of Editor
    objects.
    """
    
    #
    # Class definition variables
    #
    
    seqSpec = dict(
        item_followsprotocol = True,
        item_validatefunc = _validate_item,
        item_subloggernamefunc = (lambda i, obj: obj.makeLoggerName(i)),
        item_subloggernamefuncneedsobj = True,
        seq_validatefunc_partial = _validate_sequence)
    
    attrSpec = dict(
        cameFromTTC = dict(
            attr_initfunc = (lambda: False),
            attr_label = "CollectionEditor came from a TTC",
            attr_showonlyiftrue = True),
        
        hasDSIG = dict(
            attr_initfunc = (lambda: False),
            attr_label = "CollectionEditor has a DSIG",
            attr_showonlyiftrue = False),

        version = dict(
            attr_initfunc = (lambda: None),
            attr_label = "TTC Version",
            attr_showonlyiftrue = True))

    attrSorted = ()
    
    #
    # Methods
    #
    
    def _makeChangedKeys(self):
        changedKeys = [None] * len(self)
        
        for i, obj in enumerate(self):
            obj.head.checkSumAdjustment = 0
            obj._updateDependentObjects()
            changedKeys[i] = set(obj._dAdded)
        
        return changedKeys
    
    def _makeStakes(self, w):
        stakes = []
        
        for obj in self:
            stakes.append({tag: w.getNewStake() for tag in obj})
        
        return stakes
    
    def _makeUniques(self, changedKeys):
        uniques = {}  # tag -> {avatar1: set(equals), avatar2: set(equals)...}
        allTags = functools.reduce(set.union, (set(obj) for obj in self))
        
        for tag in allTags:
            uniques[tag] = d = {}
            
            for i, obj in enumerate(self):
                if tag not in obj:
                    continue
                
                objIsRaw = (
                  (tag not in changedKeys[i]) or
                  isinstance(obj[tag], (str, bytes)))
                
                for avatarIndex, otherEquals in d.items():
                    avatarIsRaw = (
                      (tag not in changedKeys[avatarIndex]) or
                      isinstance(self[avatarIndex][tag], (str, bytes)))
                    
                    if avatarIsRaw and objIsRaw:
                        av = self[avatarIndex]
                        
                        if obj.getRawTable(tag) == av.getRawTable(tag):
                            otherEquals.add(i)
                            break
                    
                    else:
                        if avatarIsRaw:
                            changedKeys[avatarIndex].add(tag)
                        
                        elif objIsRaw:
                            changedKeys[i].add(tag)
                            objIsRaw = False
                            
                        if obj[tag] == self[avatarIndex][tag]:
                            otherEquals.add(i)
                            break
                
                else:
                    d[i] = set()
        
        return uniques
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the CollectionEditor to the specified writer.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        forceVersion1 = kwArgs.get('forceVersion1', False)

        if forceVersion1 or self.version == 0x10000:
            vv = 0x10000
        else:
            vv = 0x20000

        w.add("4s2L", b'ttcf', vv, len(self))

        tStakes = [w.getNewStake() for obj in self]
        
        for tStake in tStakes:
            w.addUnresolvedOffset("L", stakeValue, tStake)  # OffsetTable
 
        if vv == 0x20000:
            w.add("3L", 0, 0, 0)  # ulDsigTag, ulDsigLength, ulDsigOffset for v2
        
        changedKeys = self._makeChangedKeys()
        uniques = self._makeUniques(changedKeys)
        stakes = self._makeStakes(w)
        headerChecksumRanges = []
        
        delKeys = {
          'baseStake',
          'changedKeys',
          'checksums',
          'familyIndex',
          'headerChecksumRanges',
          'lengths',
          'stakes',
          'uniques',
          'w'}
        
        for delKey in delKeys:
            kwArgs.pop(delKey, None)
        
        for i, obj in enumerate(self):
            startByteLength = w.byteLength
            
            obj.buildBinary_headerOnly(
              w = w,
              stakes = stakes,
              baseStake = stakeValue,
              familyIndex = i,
              stakeValue = tStakes[i],
              **kwArgs)
            
            headerChecksumRanges.append((startByteLength, w.byteLength))
        
        checksums = {(i, tag): 0 for i, obj in enumerate(self) for tag in obj}
        w.addIndexMap("checksums", checksums)
        lengths = checksums.copy()
        w.addIndexMap("lengths", lengths)
        
        for i, obj in enumerate(self):
            obj.buildBinary_tablesOnly(
              w = w,
              stakes = stakes,
              changedKeys = changedKeys,
              uniques = uniques,
              familyIndex = i,
              checksums = checksums,
              lengths = lengths,
              headerChecksumRanges = headerChecksumRanges,
              **kwArgs)
    
    @classmethod
    def frompath(cls, path, **kwArgs):
        """
        Creates and returns a new CollectionEditor for the TTC specified by
        path.
        """
        
        r = cls.fromwalker(filewalkerbit.FileWalkerBit(path), **kwArgs)
        r.cameFromTTC = True
        return r
    
    @classmethod
    def fromvalidatedpath(cls, path, **kwArgs):
        """
        """
        
        r = cls.fromvalidatedwalker(
          filewalkerbit.FileWalkerBit(path),
          **kwArgs)
        
        if r:
            r.cameFromTTC = True
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild("Collection")
        else:
            logger = logger.getChild("Collection")
        
        ttclen = w.length()
        
        logger.debug((
          'V0001',
          (ttclen,),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.critical((
              'V0004',
              (),
              "Insufficient bytes."))
            
            return None
        
        s = w.unpack("4s")
        
        if s != b'ttcf':
            logger.critical((
              'E0062',
              tuple(s),
              "Expected 'ttcf' tag, but got 0x%02X%02X%02X%02X instead."))
            
            return None
        
        if w.length() < 4:
            logger.critical((
              'V0292',
              (),
              "Insufficient bytes for version."))
            
            return None
        
        version = w.unpack("L")
        
        if version == 0x10000:
            logger.info(('I0061', (), "TTC version is 1.0."))
            isVersion2 = False
        
        elif version == 0x20000:
            logger.info(('I0062', (), "TTC version is 2.0."))
            isVersion2 = True
        
        else:
            logger.critical((
              'E0063',
              (version,),
              "Unknown version: 0x%08X."))
            
            return None
        
        if w.length() < 4:
            logger.critical((
              'V0293',
              (),
              "Insufficient bytes for offset count."))
            
            return None
        
        count = w.unpack("L")
        
        if w.length() < 4 * count:
            logger.critical((
              'E0060',
              (),
              "Not enough offsets for count."))
            
            return None
        
        else:
            logger.info((
              'I0060',
              (count,),
              "Offset count is %d."))
        
        r = cls(version=version)
        fw = fontedit.Editor.fromvalidatedwalker
        kwArgs.pop('fromTTC', None)
        
        for i, offset in enumerate(w.group("L", count)):
            if offset >= w.length():
                logger.critical((
                  'E0061',
                  (i,),
                  "Offset [%d] is past EOF."))
                
                return None
            
            if 'subloggerNameFunc' in kwArgs:
                s = kwArgs['subloggerNameFunc'](i, **kwArgs)
            else:
                s = "[%d]" % (i,)
                        
            itemLogger = logger.getChild(s)
            wSub = w.subWalker(0)
            wSub.skip(offset)
            r.append(fw(wSub, logger=itemLogger, fromTTC=True, **kwArgs))
        
        # DSIG: despite what the spec indicates, BOTH Version 1 and Version 2
        # TTCs may have a DSIG, tucked in following the OffsetTable but before
        # the first font's dirTables. We read the 4 bytes immediately following
        # the OffsetTable. If that is 'DSIG', then we have a DSIG, and there
        # should be 2 non-zero 4-byte values for Length and Offset.
        
        dsigTag = w.unpack("4s")
        
        if dsigTag == b'DSIG':
            dsigLength, dsigOffset = w.group("L", 2)
            isOK = True
            
            if dsigLength == 0:
                logger.error((
                  'V0517',
                  (),
                  "DSIG indicated in header, but length is 0."))
                
                isOK = False
            
            if dsigOffset == 0:
                logger.error((
                  'V0518',
                  (),
                  "DSIG indicated in header, but offset is 0."))
                
                isOK = False
            
            if dsigOffset + dsigLength > ttclen:
                logger.error((
                  'V0519',
                  (),
                  "DSIG offset + length exceeds file length."))
                
                isOK = False

            if isOK:
                r.hasDSIG = True
                logger.info(('V0520', (), "DSIG present."))

        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new CollectionEditor from the specified walker,
        which should point to the start of a TTC.
        """
        
        s = w.unpack("4s")
        
        if s != b'ttcf':
            raise ValueError("Unknown TTC tag: %s" % (s,))
        
        version = w.unpack("L")
        
        if version == 0x10000:
            isVersion2 = False
        elif version == 0x20000:
            isVersion2 = True
        else:
            raise ValueError("Unknown TTC version: 0x%08X" % (version,))
        
        r = cls(version=version)
        fw = fontedit.Editor.fromwalker
        kwArgs.pop('fromTTC', None)
        
        for offset in w.group("L", w.unpack("L")):
            
            # All interior offsets within the table directories of the
            # contained fonts are relative to the start of the TTC, and not to
            # the start of the individual font's header, so the "sub" walker we
            # pass down needs to anchor at the same place the original walker
            # anchors.
            
            wSub = w.subWalker(0)
            wSub.skip(offset)
            r.append(fw(wSub, fromTTC=True, **kwArgs))
        
        dsigTag = w.unpack("4s")
        
        if dsigTag == b'DSIG':
            r.hasDSIG = True
            dsigLength, dsigOffset = w.group("L", 2)
        
        return r
    
    def makeLoggerName(self, i):
        """
        Default method to generate a logger name for item[i] for .isValid
        validation. A logger for .isValid of sub-Editors will automatically be
        created and named using this method. See seqmeta.py
        item_subloggernamefunc and item_subloggernamefuncneedsobj for info.
        """
        
        if self[i] is not None and self[i].reallyHas(b'name'):
            return self[i].name.getFamilyName()
        else:
            return "[%d]" % (i,)


    def writeFont(self, path, **kwArgs):
        """
        """
        
        f = open(path, "wb")
        f.write(self.binaryString(**kwArgs))
        f.close()

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
