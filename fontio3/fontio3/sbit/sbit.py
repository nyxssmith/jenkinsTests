#
# sbit.py
#
# Copyright © 2009, 2011-2014, 2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for embedded bitmaps, whether Apple-flavored ('bloc' and 'bdat'),
MS-flavored ('EBLC' and 'EBDT'), or Google color-emoji-flavored ('CBLC' and
'CBDT').
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.sbit import analysis, strike
from fontio3.utilities import span2, writer

# -----------------------------------------------------------------------------

#
# Constants
#

# In the following constants, note that we're using strings, not bytestrings,
# for the tables. This is handled in fontedit.py via the dispatch mechanism.

FLAVOR_VERSIONS = {
    "bdat": 0x20000,
    "EBDT": 0x20000,
    "CBDT": 0x20000}

    # NOTE: as of 2016-02-24, the OT spec has 'CBDT' as 0x30000, but in actual
    # practice, Android seems to require v2. This structure was originally
    # devised to test against the spec. In order to retain compatibility with
    # scripts and for possible future expansion, this structure is retained,
    # even though it's kind of useless now.
    
LOCATION_TABLES = {
    "bdat": "bloc",
    "EBDT": "EBLC",
    "CBDT": "CBLC"}

# -----------------------------------------------------------------------------

#
# Classes
#

class Sbit(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing all embedded bitmaps in a font. These are dicts
    mapping (xPPEM, yPPEM, bitDepth) tuples to Strike objects. From an Editor's
    perspective, the data table (bdat, EBDT, or CBDT) will map to one of these
    Sbit objects.
    
    Note that the buildBinary() method here handles everything for the strikes
    (except the actual bitmap output into the dat table). It's just easier to
    do it this way, especially given the degree of analysis entailed by the
    optimizations done here. However, the Strike object is still responsible
    for its own fromwalker() and fromvalidatedwalker() methods.
    
    There is one attribute:
    
        flavor      A string: 'bdat', 'EBDT', or 'CBDT'. Default is 'EBDT'.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True)
    
    attrSpec = dict(
        flavor = dict(
            attr_initfunc = (lambda: 'EBDT')))
    
    attrSorted = ()
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Sbit object to two walkers: the specified
        walker (for the dat output), and another walker (for the loc output).
        This other walker will be converted to a binary string and then passed
        into the locCallback keyword argument, a function.
        """
        
        wDat = writer.LinkedWriter()
        wDat.add("L", FLAVOR_VERSIONS.get(self.flavor, 0))
        wLoc = writer.LinkedWriter()
        stakeValue = wLoc.stakeCurrent()
        wLoc.add("2L", FLAVOR_VERSIONS.get(self.flavor, 0), len(self))
        istaStartStake = {}
        istaLengthStake = {}
        istaCountStake = {}
        
        for ppemKey in sorted(self):
            stk = self[ppemKey]
            istaStartStake[ppemKey] = wLoc.getNewStake()
            wLoc.addUnresolvedOffset("L", stakeValue, istaStartStake[ppemKey])
            istaLengthStake[ppemKey] = wLoc.addDeferredValue("L")
            istaCountStake[ppemKey] = wLoc.addDeferredValue("L")
            wLoc.add("L", stk.colorRef)
            stk.horiLineMetrics.buildBinary(wLoc, **kwArgs)
            stk.vertLineMetrics.buildBinary(wLoc, **kwArgs)
            actuals = {n for n in stk if stk[n] is not None}
            wLoc.add("2H", min(actuals), max(actuals))
            wLoc.addGroup("B", ppemKey)
            wLoc.add("B", stk.flags)
        
        a = analysis.Analysis.fromSbit(self, **kwArgs)
        doWalk = [4]  # base offset is past the 0x20000 version
        datPool = {}

        if self.flavor != 'CBDT':
            ss = self.findSizeSharers()
        else:
            ss = {}

        writtenOffsets = set()
            
        for ppemKey in sorted(self):
            stk = self[ppemKey]
            wLoc.stakeCurrentWithValue(istaStartStake[ppemKey])
            istaStartLength = wLoc.byteLength
            
            v = list(a.iterateSize(
              ppemKey,
              datOffset = doWalk,
              datPool = datPool,
              sizeSharers = ss,
              **kwArgs))
            
            dp = datPool[ppemKey]  # key will be there now
            wLoc.setDeferredValue(istaCountStake[ppemKey], "L", len(v))
            headerStakes = [wLoc.getNewStake() for t in v]
            
            for t, stake in zip(v, headerStakes):
                wLoc.add("2H", *t[0:2])  # firstGlyph and lastGlyph
                wLoc.addUnresolvedOffset("L", istaStartStake[ppemKey], stake)
            
            for t, stake in zip(v, headerStakes):
                wLoc.stakeCurrentWithValue(stake)
                firstGlyph, lastGlyph, indexFormat, datOffset = t
                assert datOffset == dp[firstGlyph]
                actuals = set(stk.actualIterator(firstGlyph, lastGlyph))
                g = stk[firstGlyph]
                wLoc.add("2HL", indexFormat, g.imageFormat, datOffset)
                assert indexFormat != 1
                
                if indexFormat == 2:
                    wLoc.add("L", g.binarySize())
                    g.metrics.buildBinary(wLoc)
                
                elif indexFormat == 3:
                    v = [None] * (lastGlyph - firstGlyph + 1)
                    
                    for i in range(len(v)):
                        if i + firstGlyph in actuals:
                            v[i] = dp[i + firstGlyph] - datOffset
                        else:
                            v[i] = v[i - 1]
                    
                    wLoc.addGroup("H", v)
                    
                    wLoc.add(
                      "H",
                      dp[lastGlyph] + stk[lastGlyph].binarySize() - datOffset)
                    
                    wLoc.alignToByteMultiple(4)
                
                elif indexFormat == 4:
                    wLoc.add("L", len(actuals))
                    
                    for i in sorted(actuals):
                        wLoc.add("2H", i, dp[i] - datOffset)
                
                elif indexFormat == 5:
                    wLoc.add("L", g.binarySize())
                    g.metrics.buildBinary(wLoc)
                    wLoc.add("L", len(actuals))
                    wLoc.addGroup("H", sorted(actuals))
                    wLoc.alignToByteMultiple(4)
                
                for offset, i in sorted((dp[i], i) for i in actuals):
                    if offset not in writtenOffsets:
                        assert wDat.byteLength == offset
                        stk[i].buildBinary(wDat)
                        writtenOffsets.add(offset)
            
            wLoc.setDeferredValue(
              istaLengthStake[ppemKey],
              "L",
              wLoc.byteLength - istaStartLength)
        
        if 'locCallback' in kwArgs:
            kwArgs['locCallback'](wLoc.binaryString())
        
        w.addString(wDat.binaryString())
    
    def findSizeSharers(self):
        """
        Find potential re-use cases across PPEMs. This method returns a dict
        whose keys are (ppem, ppem+1) tuples and whose values are Spans with
        all the glyphs whose images are identical in those two ppems.
        
        This information is necessary, but not sufficient. The sharing can
        really only happen for monospace ranges (since the non-monospace ranges
        include advance in their metrics, which are not shared). So the dict
        returned by this method needs to be intersected (as it were) with the
        monospace glyph ranges, as it only applies there.
        """
        
        # make the dict of image hashes
        dSizeGlyphToHash = {}
        
        for ppem, stk in self.items():
            d = dSizeGlyphToHash.setdefault(ppem, {})
            
            for glyphIndex, data in stk.items():
                if data is not None and data.imageFormat == 5:
                    d[glyphIndex] = hash(tuple(tuple(v) for v in data.image))
        
        # walk the dict
        sortedSizes = sorted(dSizeGlyphToHash)
        dOutput = {}  # (smaller, larger) -> set of glyphs
        
        for smaller, larger in zip(sortedSizes, sortedSizes[1:]):
            if (
              (smaller[0] != (larger[0] - 1)) or
              (smaller[1] != (larger[1] - 1)) or
              (smaller[2] != larger[2])):
                
                continue
            
            thisSet = (smaller, larger)
            d = dOutput.setdefault(thisSet, set())
            dSmaller = dSizeGlyphToHash[smaller]
            dLarger = dSizeGlyphToHash[larger]
            commonKeys = set(dSmaller) & set(dLarger)
            
            for key in commonKeys:
                if dSmaller[key] == dLarger[key]:
                    
                    # I tested tens of thousands of glyphs at lots of PPEMs and
                    # the hash test suffices; image comparison isn't needed.
                    
                    d.add(key)
        
        toDel = set()
        
        for key in dOutput:
            d = dOutput[key]
            
            if d:
                dOutput[key] = span2.Span(d)
            else:
                toDel.add(key)
        
        for key in toDel:
            del dOutput[key]
        
        return dOutput
    
    @classmethod
    def fromscaler(cls, s, ppemList, **kwArgs):
        """
        Creates a new Sbit object from the specified scaler using ppemList (a
        list of (xPPEM, yPPEM, bitDepth) tuples).

        The scaler needs to have ben initialized and had 'setFont' called on
        the desired source for bitmap images.

        Though merely passed through here, if you want to limit the generation
        to specific glyphs, pass in the iterable with the 'glyphList' kwArg. If
        you do not do that, you MUST pass in the 'editor' kwArg (to generate
        all glyphs).        
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        for p in ppemList:
            tstrike = strike.Strike.fromscaler(s, *p, **kwArgs)
            d, r[p] = strike._recalc_lineMetrics(tstrike)
            
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Sbit object from the specified walker (which
        will be for a dat table), with source validation. There is one required
        keyword argument:

            flavor  One of 'bloc', 'EBDT', or 'CBLC' to indicate the type

            wLoc    A walker for the corresponding loc table (bloc for bdat,
                    EBLC for EBDT, CBLC for CBDT).
        """

        flavor = kwArgs.get('flavor', 'sbits')
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild(flavor)

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version = w.unpack("L", advance=False)
        expectedversion = FLAVOR_VERSIONS.get(flavor, 0)

        if version != expectedversion:
            logger.error((
              'E0600',
              (expectedversion, version,),
              "Expected version 0x%08X, but got 0x%08X."))

            if flavor == 'CBDT' and version == 0x00030000:
                logger.warning((
                  'Vxxxx',
                  (),
                  "CBDT uses v3 which is correct per spec, but "
                  "in actual practice, v2 is required."))
            else:
                # don't allow other version-flavor mismatches.
                return None

        wLoc = kwArgs['wLoc']
        wLocWalk = wLoc.subWalker(0)
        
        if wLocWalk.length() < 8:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        version, bstCount = wLocWalk.unpack("2L")

        if version != expectedversion:
            logger.error((
              'E0702',
              (expectedversion, version,),
              "Location table version should be 0x%08X but is 0x%08X."))

            if flavor == 'CBDT' and version == 0x00030000:
                logger.warning((
                  'Vxxxx',
                  (),
                  "CBLC uses v3 which is correct per spec, but "
                  "in actual practice, v2 is required."))
            else:
                # don't allow other version-flavor mismatches.
                return None

        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        fvw = strike.Strike.fromvalidatedwalker
        
        for i in range(bstCount):
            stk = fvw(
              wLocWalk,
              wDat = w,
              logger = logger.getChild("bitmapSizeTable %d" % (i,)),
              **kwArgs)
            
            if stk is None:
                return None
            
            r[(stk.ppemX, stk.ppemY, stk.bitDepth)] = stk
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Sbit object from the specified walker (which
        will be for a dat table). There are two required keyword arguments:

            flavor  One of 'bloc', 'EBDT', or 'CBLC' to indicate the type

            wLoc    A walker for the corresponding loc table (bloc for bdat,
                    EBLC for EBDT, CBLC for CBDT).
        """

        flavor = kwArgs.get('flavor')
        version = w.unpack("L", advance=False)

        wLoc = kwArgs['wLoc']
        wLocWalk = wLoc.subWalker(0)
        locversion = wLocWalk.unpack("L")

        expectedversion = FLAVOR_VERSIONS.get(flavor, 0)

        if version != expectedversion:
            if flavor == 'CBDT' and version == 0x00030000:
                # allow this, since the spec currently calls for v3 for CBDT
                pass
            else:
                # but no other flavor-version mismatches.
                raise ValueError("Unknown %s version: 0x%08X "
                  "(expected 0x%08X)" % (flavor, version, expectedversion))

        if locversion != expectedversion:
            if flavor == 'CBDT' and locversion == 0x00030000:
                # allow this, since the spec currently calls for v3 for CBDT
                pass
            else:
                # but no other flavor-version mismatches.
                raise ValueError("Unknown location table version: "
                    "0x%08X (expected 0x%08X)" % (locversion, expectedversion))

        count = wLocWalk.unpack("L")
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        while count:
            stk = strike.Strike.fromwalker(wLocWalk, wDat=w, **kwArgs)
            key = (stk.ppemX, stk.ppemY, stk.bitDepth)
            r[key] = stk
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
        #_myTest()
