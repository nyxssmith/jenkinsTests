#
# cmap.py
#
# Copyright © 2009-2014, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module defines the ``Cmap`` class, which is the living object representing
the entire ``'cmap'`` table.
"""

# System imports
import collections
import functools
import itertools
import logging
import operator

# Other imports
from fontio3.cmap import cmapsubtable, uvs
from fontio3.fontdata import mapmeta
from fontio3.utilities import pslnames

# -----------------------------------------------------------------------------

#
# Private functions
#
def _sort_for_compaction(k, **kwArgs):
    """
    Sort subtable keys of duplicated subtables in a preferred order such
    that following the sort, the 0th item can be retained, eliminating
    duplicates but keeping the "right" ones (e.g. keep the (3,1,0) in
    *both* of the following cases: duplicated (3,1,0)/(0,3,0) and
    duplicated (3,1,0)/(3,10,0).
    """
    
    p = {(3, 1, 0): 0, (3, 10, 0): 1, (1, 0, 0): 2 }
    
    if k in p:
        return p[k]
    else:
        return len(p)

def _validateWhole(d, **kwArgs):
    """
    Do validation on the Cmap object as a whole. This is a "_partial" function,
    so other checks are automatically done below this level too.
    
    >>> e = utilities.fakeEditor(20000)
    >>> logger = utilities.makeDoctestLogger("ValTest")
    >>> cs1 = cmapsubtable.CmapSubtable({0xE200: 1234})
    >>> Cmap({(3, 1, 0): cs1}).isValid(logger=logger, editor=e)
    ValTest - WARNING - Cannot check Apple logo mapping, as Mac Roman subtable is missing.
    ValTest - WARNING - No Mac subtables present.
    ValTest - WARNING - PUA characters present in (3, 1, 0) subtable.
    ValTest - WARNING - Microsoft Unicode subtable does not contain a mapping for the Euro (U+20AC).
    True
    
    >>> e = utilities.fakeEditor(600)
    >>> Cmap({(3, 1, 0): cs1}).isValid(logger=logger, editor=e)
    ValTest - WARNING - Cannot check Apple logo mapping, as Mac Roman subtable is missing.
    ValTest - WARNING - No Mac subtables present.
    ValTest - WARNING - PUA characters present in (3, 1, 0) subtable.
    ValTest - WARNING - Microsoft Unicode subtable does not contain a mapping for the Euro (U+20AC).
    ValTest.[(3, 1, 0)].[57856] - ERROR - Glyph index 1234 too large.
    False
    """
    
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if editor is None:
        logger.error((
          'V0553',
          (),
          "Unable to validate 'cmap' because no editor was specified."))
        
        return False
    
    fName = editor.getNamer().bestNameForGlyphIndex
    macRomanKeys = d.findKeys(1, 0)
    
    if macRomanKeys:
        st = d[macRomanKeys[0]]
        
        if st.get(0xF0, 0):
            logger.warning((
              'W0300',
              (),
              "Apple logo not mapped to missing glyph in Mac Roman subtable."))
        
        macEuroGlyph = st.get(0xDB, 0)
        ok = False
        
        if macEuroGlyph:
            if fName(macEuroGlyph) == "Euro":
                ok = True
            
            else:
                gSet = {
                  d[uk][0x20AC]
                  for uk in d.getUnicodeKeys() 
                  if 0x20AC in d[uk]}
                
                if macEuroGlyph in gSet:
                    ok = True
        
        if not ok:
            logger.warning((
              'W0304',
              (),
              "Mac Roman character 219 is not the Euro."))
    
    else:
        logger.warning((
          'W0301',
          (),
          "Cannot check Apple logo mapping, as "
          "Mac Roman subtable is missing."))
        
        if not d.findKeys(1):
            logger.warning((
              'W0302',
              (),
              "No Mac subtables present."))
    
    if not d.findKeys(3):
        logger.warning((
          'W0303',
          (),
          "No Microsoft subtables present."))
    
    for k in d.getUnicodeKeys():
        dSub = d[k]
        
        if any(0xE000 <= c < 0xF900 for c in dSub):
            logger.warning((
              'W0307',
              (k,),
              "PUA characters present in %s subtable."))
        
        if k[0] == 3:
            euroglyph = dSub.get(0x20AC, 0)
            
            if euroglyph > 0:
                if (editor.post.header.format != 3.0) or (b'CFF ' in editor):
                    namer = editor.getNamer()
                    euroname = namer.bestNameForGlyphIndex(euroglyph)
                    
                    if euroname != 'Euro':
                        logger.warning((
                          'W0305',
                          (euroname,),
                          "Glyph name '%s' for U+20AC is not 'Euro'."))
                
                else:
                    logger.warning((
                      'W0305',
                      (euroglyph,),
                      "Cannot validate that the name of the Euro character "
                      "(id %d) is 'Euro' because the font does not include "
                      "glyph names."))
            
            else:
                logger.warning((
                  'W0305',
                  (),
                  "Microsoft Unicode subtable does not contain a mapping "
                  "for the Euro (U+20AC)."))


            if k[1] == 10 and dSub.originalFormat != 12:
                logger.warning((
                  'W0306',
                  (),
                  "Non-BMP Microsoft subtable not format 12."))
    
    # Check for internal conflicts in multiple Unicode maps (V0906)
    
    uKeys = d.getUnicodeKeys()
    mapSets = [{u for u in d[k] if u < 0x10000} for k in uKeys]
    r = True
    
    if len(mapSets) > 1:
        unionSet = {n for ms in mapSets for n in ms}
        
        for i, (k, ms) in enumerate(zip(uKeys, mapSets)):
            if unionSet - ms:
                logger.error((
                  'V0906',
                  (k,),
                  "The Unicode 'cmap' subtable with key %s is missing "
                  "some entries that are present in at least one other "
                  "Unicode 'cmap' subtable in this font."))
                
                r = False
        
        for u in sorted(unionSet):
            g = {d[k][u] for k in uKeys if u in d[k]}
            
            if len(g) > 1:
                logger.error((
                  'V0906',
                  (u,),
                  "The Unicode value U+%04X is mapped to different glyphs "
                  "in different Unicode 'cmap' subtables."))
                
                r = False
    
    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Cmap(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects describing whole ``'cmap'`` tables. These are dicts whose keys are
    (platform ID, platform-specific ID, language ID) triples, and whose values
    are :py:class:`~fontio3.cmap.cmapsubtable.CmapSubtable` objects. They have
    one attribute:
    
    ``unicodeVariations``
        A :py:class:`~fontio3.cmap.uvs.UVS` object.
    
    >>> cs1 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5})
    >>> cs2 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5, 0x20000: 10, 0x200AA: 11})
    >>> Cmap({(3, 1, 0): cs1, (3, 10, 0): cs2}).pprint()
    Platform: MS, Specific kind: BMP (3, 1, 0):
      0x0020: 3
      0x0021: 4
      0x0022: 5
    Platform: MS, Specific kind: Unicode (3, 10, 0):
      0x0020: 3
      0x0021: 4
      0x0022: 5
      0x020000: 10
      0x0200AA: 11
    
    >>> cs1 = cmapsubtable.CmapSubtable({32: 5, 33: 6, 50: 7})
    >>> cs2 = cmapsubtable.CmapSubtable({33: 10, 34: 11})
    >>> c1 = Cmap({(3, 1, 0): cs1})       
    >>> c2 = Cmap({(3, 1, 0): cs2})
    >>> print(c1.merged(c2, replaceWhole=True)[(3, 1, 0)])
    {0x0021: 10, 0x0022: 11}
    
    >>> print(c1.merged(c2, replaceWhole=False, conflictPreferOther=True)[(3, 1, 0)])
    {0x0020: 5, 0x0021: 10, 0x0022: 11, 0x0032: 7}
    
    >>> print(c1.merged(c2, replaceWhole=False, conflictPreferOther=False)[(3, 1, 0)])
    {0x0020: 5, 0x0021: 6, 0x0022: 11, 0x0032: 7}
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = functools.partial(
          pslnames.labelForKey,
          adjustForCmap = True),
        map_validatefunc_partial = _validateWhole,
        map_wisdom = (
          "Dicts mapping (platform, script, language) triples to CmapSubtable "
          "objects. It's OK for multiple keys to refer to the same object; in "
          "this case the data will be shared in the resulting binary table."))
    
    attrSpec = dict(
        unicodeVariations = dict(
            attr_followsprotocol = True,
            attr_initfunc = uvs.UVS,
            attr_showonlyiftrue = True,
            attr_wisdom = "A UVS object, or None."))
    
    #
    # Methods
    #
    
    def addUnicode(self, u, glyphID):
        """
        Add the specified mapping to all Unicode subtables.
        
        :param u: The Unicode value to be added
        :type u: int or str
        :param glyphID: The associated glyph index for this Unicode
        :type glyphID: int
        :return: None
        
        This method adds the specified character->glyph mapping to all Unicode
        subtables in the 'cmap' table.
        
        >>> cs1 = cmapsubtable.CmapSubtable({32: 3})
        >>> cs2 = cmapsubtable.CmapSubtable({32: 3})
        >>> c = Cmap({(3, 1, 0): cs1, (0, 4, 0): cs2})
        >>> for key in sorted(c): print("%s: %s" % (key, c[key]))
        (0, 4, 0): {0x0020: 3}
        (3, 1, 0): {0x0020: 3}
        >>> c.addUnicode(0x0021, 4)
        >>> for key in sorted(c): print("%s: %s" % (key, c[key]))
        (0, 4, 0): {0x0020: 3, 0x0021: 4}
        (3, 1, 0): {0x0020: 3, 0x0021: 4}
        """
        
        if isinstance(u, str):
            u = ord(u)
        
        keysToUpdate = self.findKeys(platform=3, script=10)
        keysToUpdate.extend(self.findKeys(platform=3, script=1))
        keysToUpdate.extend(self.findKeys(platform=0))
        
        for key in keysToUpdate:
            self[key][u] = glyphID
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for ``self`` to the specified writer.
    
        :param w: A :py:class:`~fontio3.utilities.writer.LinkedWriter`
        :param kwArgs: Optional keyword arguments (see below)
        :return: None
        
        The following ``kwArgs`` are supported:
        
        ``forceNonEmpty``
            If True, and there are no subtables in the dict, then a subtable
            mapping ``0x20`` to glyph 0 will be used for output. If False, no
            such addition will be made. Default is True.
        
        ``stakeValue``
            A stake that will be placed at the start of the binary data laid
            down by this method. One will be synthesized if not provided.
            See :py:class:`~fontio3.utilities.writer.LinkedWriter` for a
            description of stakes and how they're used.
        
        >>> cs = cmapsubtable.CmapSubtable({0x20: 3, 0x21: 4})
        >>> cs.preferredFormat = 4
        >>> utilities.hexdump(Cmap({(3, 1, 0): cs}).binaryString())
               0 | 0000 0001 0003 0001  0000 000C 0004 0020 |............... |
              10 | 0000 0004 0004 0001  0000 0021 FFFF 0000 |...........!....|
              20 | 0020 FFFF FFE3 0001  0000 0000           |. ..........    |
        
        >>> cs.preferredFormat = 6
        >>> utilities.hexdump(Cmap({(3, 1, 0): cs}).binaryString())
               0 | 0000 0001 0003 0001  0000 000C 0006 000E |................|
              10 | 0000 0020 0002 0003  0004                |... ......      |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if (not self) and kwArgs.get('forceNonEmpty', True):
            self = Cmap({(3, 1, 0): cmapsubtable.CmapSubtable({0x20: 0})})
        
        w.add("HH", 0, len(self) + (1 if self.unicodeVariations else 0))
        keyInfo = {}
        uniques = {}
        
        for key in sorted(self):
            obj = self[key]
            idObj = obj.asImmutable()
            
            if idObj not in uniques:
                keyInfo[key] = (w.getNewStake(), self[key])
                uniques[idObj] = keyInfo[key][0]
            
            else:
                keyInfo[key] = (uniques[idObj], None)
        
        if self.unicodeVariations:
            keyInfo[(0, 5, 0)] = (w.getNewStake(), self.unicodeVariations)
        
        for key in sorted(keyInfo):
            w.addGroup("H", key[:2])
            w.addUnresolvedOffset("L", stakeValue, keyInfo[key][0])
        
        for key in sorted(keyInfo):
            stake, obj = keyInfo[key]
            
            if obj is not None:
                obj.buildBinary(w, stakeValue=stake, **kwArgs)
                
    def compacted(self, **kwArgs):
        """
        Return a new object which has been compacted.
    
        :param kwArgs: Optional keyword arguments (there are none here)
        :return: A new compacted object
        :rtype: Same as ``self``
    
        Custom Protocol method to compact the full ``Cmap`` object by removing
        duplicate subtables (those with identical contents but different
        platform / encoding / language keys).
        
        >>> c = Cmap()
        >>> cs1 = cmapsubtable.CmapSubtable({32: 3, 33:4})
        >>> cs2 = cmapsubtable.CmapSubtable({32: 3, 33:4})
        >>> c[(0, 3, 0)] = cs1
        >>> c[(3, 1, 0)] = cs2
        >>> list(c.keys())
        [(0, 3, 0), (3, 1, 0)]
        >>> list(c.compacted().keys())
        [(3, 1, 0)]
        """
        
        d = collections.defaultdict(set)
        
        for key, subtable in self.items():
            # nullify originalFormat and preferredFormat;
            # we're only interested in the contents for compaction.
            stcopy = subtable.__copy__()
            stcopy.originalFormat = None
            stcopy.preferredFormat = None
            d[stcopy.asImmutable()].add(key)

        # *values* of 'd' are subtable platform/encoding/language ids
        # (i.e. keys for self). Any such values with more than one item
        # represent duplicated subtables.
        
        nc = type(self)()
        
        for st, pel in d.items():
            if len(pel) == 1:
                nc[list(pel)[0]] = self[list(pel)[0]]
            
            else:
                sk = sorted(pel, key=_sort_for_compaction)
                nc[sk[0]] = self[sk[0]]
            
        return nc
    
    def deleteUnicode(self, u):
        """
        Delete the specified Unicode from all Unicode subtables.
        
        :param u: The Unicode value to be deleted
        :type u: int or str
        
        >>> cs1 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5})
        >>> cs2 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5})
        >>> c = Cmap({(3, 1, 0): cs1, (0, 4, 0): cs2})
        >>> for key in sorted(c): print("%s: %s" % (key, c[key]))
        (0, 4, 0): {0x0020: 3, 0x0021: 4, 0x0022: 5}
        (3, 1, 0): {0x0020: 3, 0x0021: 4, 0x0022: 5}
        >>> c.deleteUnicode(0x0021)
        >>> for key in sorted(c): print("%s: %s" % (key, c[key]))
        (0, 4, 0): {0x0020: 3, 0x0022: 5}
        (3, 1, 0): {0x0020: 3, 0x0022: 5}
        """
        
        if isinstance(u, str):
            u = ord(u)
        
        keysToUpdate = self.findKeys(platform=3, script=10)
        keysToUpdate.extend(self.findKeys(platform=3, script=1))
        keysToUpdate.extend(self.findKeys(platform=0))
        
        for key in keysToUpdate:
            cs = self[key]
            
            if u in cs:
                del cs[u] 
    
    def findKeys(self, platform=None, script=None, language=None):
        """
        Return a list of all keys which match the specified values.
        
        :param platform: The platform ID
        :type platform: int, iterable(int), or ``None``
        :param script: The script ID
        :type script: int, iterable(int), or ``None``
        :param language: The language ID
        :type language: int, iterable(int), or ``None``
        
        A value of ``None`` in an argument matches everything.
        
        >>> cs = cmapsubtable.CmapSubtable({32: 3})
        >>> c = Cmap()
        >>> c[(0, 4, 0)] = cs
        >>> c[(1, 0, 0)] = cs
        >>> c[(1, 1, 0)] = cs
        >>> c[(3, 1, 0)] = cs
        >>> c[(3, 10, 0)] = cs
        >>> sorted(c.findKeys(platform=3))
        [(3, 1, 0), (3, 10, 0)]
        >>> sorted(c.findKeys(script=(1, 4)))
        [(0, 4, 0), (1, 1, 0), (3, 1, 0)]
        >>> c.findKeys(platform=(1, 3), script=1)
        [(1, 1, 0), (3, 1, 0)]
        """
        
        r = []
        
        if platform is not None:
            try: platform = set(platform)
            except TypeError: platform = set([platform])
        
        if script is not None:
            try: script = set(script)
            except TypeError: script = set([script])
        
        if language is not None:
            try: language = set(language)
            except TypeError: language = set([language])
        
        for p, s, l in self:
            pMatches = platform is None or p in platform
            sMatches = script is None or s in script
            lMatches = language is None or l in language
            
            if pMatches and sMatches and lMatches:
                r.append((p, s, l))
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates a new Cmap instance from the specified walker, performing
        validation on the correctness of the binary data.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (see below)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        The following ``kwArgs`` are supported:
        
        ``logger``
            A logger to which validation information will be posted.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('cmap')
        else:
            logger = logger.getChild('cmap')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        originalStart = w.getOffset()
        endOfWalker = w.length()
        version, numTables = w.unpack("2H")
        
        if version:
            logger.error((
              'E0322',
              (version,),
              "Unknown version 0x%04X (should be 0)."))
            
            return None
        
        logger.info(('V0071', (numTables,), "Number of subtables: %d."))
        
        if w.length() < 8 * numTables:
            logger.error(('V0072', (), "Insufficient bytes for array."))
            return None
        
        v = list(w.group("2HL", numTables))
        
        if v != sorted(v):
            logger.error((
              'E0320',
              (),
              "Records not sorted by (platform, encoding)."))
            
            return None
        
        v.sort(key=operator.itemgetter(2))  # sort by offset
        offsets = sorted(set(obj[2] for obj in v))
        nextOffset = dict(zip(offsets, offsets[1:]))
        r = cls()
        fw = cmapsubtable.CmapSubtable.fromvalidatedwalker
        pool = {}
        seenPlatScrps = set()
        offLens = set()
        
        for i, (platform, script, offset) in enumerate(v):
            isUVS = platform == 0 and script == 5
            t = (platform, script)
            logger.info(('V0073', t, "Subtable platform %d, encoding %d"))
            
            if t in seenPlatScrps:
                logger.warning((
                  'E0300',
                  t,
                  "Duplicate subtables for (%d, %d)."))
            
            seenPlatScrps.add(t)
            
            if offset < 4 + 8 * numTables:
                logger.error((
                  'V0074',
                  (),
                  "Subtable offset too small (in header)."))
                
                return None
            
            if offset not in pool:
                if offset in nextOffset:
                    nxOff = nextOffset[offset]
                    thisLen = nxOff - offset
                    subW = w.subWalker(offset, newLimit=nxOff+originalStart)
                
                else:
                    thisLen = endOfWalker - offset
                    subW = w.subWalker(offset)
                
                if isUVS:
                    pool[offset] = uvs.UVS.fromvalidatedwalker(
                      subW,
                      logger = logger,
                      **kwArgs)
                
                else:
                    pool[offset] = fw(subW, logger=logger, **kwArgs)
                    
                    if pool[offset] is None:
                        return None
                
                offLens.add((offset, thisLen))
            
            else:
                logger.info(('V0075', (), "One or more subtables are shared."))
            
            if isUVS:
                r.unicodeVariations = pool[offset]
            else:
                r[(platform, script, pool[offset].language)] = pool[offset]
        
        # Check offLens for overlaps (exact overlays already filtered out)
        offLens = sorted(offLens)
        
        if len(offLens) > 1:
            it = zip(offLens, itertools.islice(offLens, 1, None))
            
            for thisOL, nextOL in it:
                if thisOL[0] + thisOL[1] > nextOL[0]:
                    logger.error(('E0319', (), "Subtables overlap."))
                    return None
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates a new Cmap instance from the specified walker.
    
        :param w: A walker for the binary data to be consumed in making the new
            instance
        :type w: :py:class:`~fontio3.utilities.walkerbit.StringWalker`
            or equivalent
        :param kwArgs: Optional keyword arguments (see below)
        :return: The new instance
        :rtype: *cls*
    
        .. note::
        
            This is a class method!
        
        The following ``kwArgs`` are supported:
        
        ``showHexOffsets``
            If True, prints to ``stdout`` the hex offset of each subtable,
            along with its platform and script. Default is False.
        """
        
        r = cls()
        originalStart = w.getOffset()
        v = list(w.group("2HL", w.unpack("2xH")))
        
        if kwArgs.get('showHexOffsets', False):
            print("Cmap offsets:")
            
            for t in v:
                print("  platform %s script %s offset 0x%08X" % t)
        
        v.sort(key=operator.itemgetter(2))
        offsets = sorted(set(obj[2] for obj in v))
        nextOffset = dict(zip(offsets, offsets[1:]))
        fw = cmapsubtable.CmapSubtable.fromwalker
        pool = {}
        
        for i, (platform, script, offset) in enumerate(v):
            isUVS = platform == 0 and script == 5
            
            if offset not in pool:
                if offset in nextOffset:
                    subW = w.subWalker(
                      offset,
                      newLimit = nextOffset[offset]+originalStart)
                
                else:
                    subW = w.subWalker(offset)
                
                if isUVS:
                    pool[offset] = uvs.UVS.fromwalker(subW, **kwArgs)
                else:
                    pool[offset] = fw(subW, **kwArgs)
            
            if isUVS:
                r.unicodeVariations = pool[offset]
            else:
                r[(platform, script, pool[offset].language)] = pool[offset]
        
        return r

    def getSymbolMap(self):
        """
        Find the symbol map (specifically the (3, 0, \*) entry).
        
        :return: A :py:class:`~fontio3.cmap.cmapsubtable.CmapSubtable`, or
            ``None`` if there is no symbol map.
        
        >>> c = Cmap()
        >>> print(c.getSymbolMap())
        None
        >>> cs = cmapsubtable.CmapSubtable({0x40: 5, 0x41: 6})
        >>> c[(3, 0, 0)] = cs
        >>> symMap = c.getSymbolMap()
        >>> print(symMap)
        {0x0040: 5, 0x0041: 6}
        >>> cs is symMap, cs == symMap
        (False, True)
        """
        
        r = None
        
        for key in self.findKeys(platform=3, script=0):
            if r is None:
                r = cmapsubtable.CmapSubtable(self[key])
            else:
                r.update(self[key])
        
        return r
    
    def getUnicodeKeys(self):
        """
        Find the keys for all Unicode cmap subtables.
        
        :return: A list (possibly empty) with all the keys in ``self`` that
            correspond to Unicode subtables
        
        For purposes of this method the (3, 10, \*), (3, 1, \*), and
        (0, \*, \*) keys are returned.
        
        >>> cs1 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5})
        >>> cs2 = cmapsubtable.CmapSubtable({32: 3, 33: 4, 34: 5})
        >>> Cmap({(3, 1, 0): cs1, (0, 4, 0): cs2}).getUnicodeKeys()
        [(3, 1, 0), (0, 4, 0)]
        """
        
        r = self.findKeys(platform=3, script=10)
        r.extend(self.findKeys(platform=3, script=1))
        r.extend(self.findKeys(platform=0))
        return r

    def getUnicodeMap(self):
        """
        Make a :py:class:`~fontio3.cmap.cmapsubtable.CmapSubtable` with a
        union map of all Unicodes.
        
        :return: A :py:class:`~fontio3.cmap.cmapsubtable.CmapSubtable`; this
            will be a new object, which may be equal to one or more of the
            existing subtables
        
        >>> cs1 = cmapsubtable.CmapSubtable({0x20: 3})
        >>> cs10 = cmapsubtable.CmapSubtable({0x20: 3, 0x10000: 4})
        >>> uMap = Cmap({(3, 1, 0): cs1, (3, 10, 0): cs10}).getUnicodeMap()
        >>> uMap == cs10, uMap is cs10
        (True, False)
        """
        
        r = cmapsubtable.CmapSubtable()
        
        for key in self.findKeys(platform=3, script=10):
            r.update(self[key])
        
        if not r:
            for key in self.findKeys(platform=3, script=1):
                r.update(self[key])
        
        if not r:
            for key in self.findKeys(platform=0):
                r.update(self[key])
        
        # if r is still empty at this point, maybe synth from Mac?
        
        return r
    
    def mappedGlyphs(self):
        """
        Find all glyphs actually present in at least one subtable.
        
        :return: The complete group of glyph indices
        :rtype: set(int)
        
        Note that the missing glyph index, 0, will always be added to the
        returned set.
        
        >>> cs1 = cmapsubtable.CmapSubtable({32: 3})
        >>> cs2 = cmapsubtable.CmapSubtable({0x4E00: 19})
        >>> c = Cmap({(1, 0, 0): cs1, (3, 1, 0): cs2})
        >>> sorted(c.mappedGlyphs())
        [0, 3, 19]
        """
        
        unionSet = set(g for it in self.values() for g in it.values())
        unionSet.add(0)
        return unionSet

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
