#
# analysis.py
#
# Copyright © 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Code that analyzes Sbit objects in order to produce size-optimized results for
writing binary strings.
"""

# System imports
import itertools
import operator

# Other imports
from fontio3.utilities import span2

# -----------------------------------------------------------------------------

#
# Classes
#

class Analysis(dict):
    """
    A dict mapping (xPPEM, yPPEM, depth) tuple keys to lists of (firstGlyph,
    lastGlyph, metricsOrNone) tuples.
    """
    
    #
    # Class methods
    #
    
    @classmethod
    def fromSbit(cls, sbitObj, **kwArgs):
        """
        Creates and returns a new Analysis object from the specified Sbit
        object. This is a simple non-optimized version; further optimizations
        can be done by calling the various public methods.
        """
        
        r = cls()
        r.sbitObj = sbitObj
        
        for ppemKey, stk in sbitObj.items():
            monoGlyphToMetricsBS = {
              glyph: (mbs, stk[glyph].imageFormat)
              for mbs, s in stk.findMonospaceCandidates().items()
              for glyph in s}
            
            for glyph, obj in stk.items():
                if (glyph not in monoGlyphToMetricsBS) and (obj is not None):
                    monoGlyphToMetricsBS[glyph] = (None, obj.imageFormat)
            
            currFirst = currLast = currMBS = None
            v = []
            
            for glyph in sorted(stk):
                if stk[glyph] is None:
                    if currFirst is not None:
                        v.append((currFirst, currLast, currMBS))
                        currFirst = currLast = currMBS = None
                    
                    continue
                
                if currFirst is None:
                    currFirst = currLast = glyph
                    currMBS = monoGlyphToMetricsBS.get(glyph)
                    continue
                
                thisMBS = monoGlyphToMetricsBS.get(glyph)
                
                if thisMBS == currMBS:
                    if (thisMBS[0] is not None) and (glyph != (currLast + 1)):
                        
                        # This special case first arose as the result of a
                        # merge, where the last glyph in the base font and the
                        # first glyph in the merging font have the same mbs and
                        # imageFormat, but are separated by a glyph gap.
                        
                        v.append((currFirst, currLast, currMBS))
                        currFirst = currLast = glyph
                    
                    else:
                        currLast = glyph
                
                else:
                    v.append((currFirst, currLast, currMBS))
                    currFirst = currLast = glyph
                    currMBS = thisMBS
            
            if currFirst is not None:
                v.append((currFirst, currLast, currMBS))
            
            r[ppemKey] = v
        
        return r
    
    #
    # Public methods
    #
    
    def iterateSize(self, ppemKey, **kwArgs):
        """
        Given a key (xPPEM, yPPEM, depth), returns a generator over tuples of
        the form (firstGlyph, lastGlyph, indexFormat, datOffset) for the
        entries matching that key. The tuples are yielded sorted in firstGlyph
        order. Note that there may be holes between firstGlyph and lastGlyph.
        
        The following keyword arguments are used:
            
            datOffset       A list of length one, containing the offset to the
                            next available dat offset. It's done this way so
                            any changes to this value can be communicated back
                            to the caller.
            
            datPool         A dict mapping ppemKeys to dicts, which in turn map
                            glyph indices to base offsets in the related data
                            table ('bdat' or 'EBDT').
        
            forApple        If the forApple flag is True, the index formats
                            will be limited to 2 and 3. If the flag is False
                            (the default), index formats 2 through 5 will be
                            used. Index format 1 is never used, as the size is
                            too big.
            
            sizeSharers     The output from a call to the Sbit object's
                            findSizeSharers() method. If not specified, an
                            empty dict will be used.
        """
        
        forApple = kwArgs.get('forApple', False)
        sizeSharers = kwArgs.get('sizeSharers', {})
        datPool = kwArgs.get('datPool', {})
        datOffset = kwArgs.get('datOffset', [0])
        r = []
        
        for k, g in itertools.groupby(
          self[ppemKey],
          key = operator.itemgetter(2)):
            
            v = list(g)
            
            if k[0] is None:
                # it's a non-monospace group
                if len(v) == 1:
                    # emit a single index3 group
                    r.append((v[0][0], v[0][1], 3))
                    continue
                
                gapList = []
                
                for thisEntry, nextEntry in zip(v, v[1:]):
                    gapList.append(thisEntry[1] - thisEntry[0] + 1)
                    gapList.append(nextEntry[0] - thisEntry[1] - 1)
                
                gapList.append(v[-1][1] - v[-1][0] + 1)
                currSize = ('3', 18 + 2 * gapList[0])
                i = 3
                
                while i <= len(gapList):
                    vSub = gapList[:i]
                    size_3 = 18 + 2 * sum(vSub)
                    size_3s = sum(18 + 2 * n for n in vSub[0::2])
                    size_prior_plus_3 = currSize[1] + (18 + 2 * vSub[-1])
                    
                    if not forApple:
                        size_4 = 20 + 4 * sum(vSub[0::2])
                        best = min(size_3, size_4, size_3s, size_prior_plus_3)
                    
                    else:
                        best = min(size_3, size_3s, size_prior_plus_3)
                    
                    if size_3 == best:
                        currSize = ('3', size_3)
                        i += 2
                    
                    elif (not forApple) and (size_4 == best):
                        currSize = ('4', size_4)
                        i += 2
                    
                    elif size_3s == best:
                        currSize = ('3s', size_3s)
                        i += 2
                    
                    else:
                        
                        # If we get here, we yield the current cumulation as a
                        # block and then start a new cumulation.
                        
                        i -= 1  # now indexes first of new gapList
                        
                        if currSize[0] == '3':
                            r.append((v[0][0], v[(i // 2) - 1][1], 3))
                        
                        elif currSize[0] == '4':
                            
                            # It never makes sense to split an index4 group, so
                            # if the last group added was a 4, just meld them.
                            
                            if r and r[-1][-1] == 4:
                                oldLast = r.pop()
                                r.append((oldLast[0], v[(i // 2) - 1][1], 4))
                            
                            else:
                                r.append((v[0][0], v[(i // 2) - 1][1], 4))
                        
                        else:
                            assert currSize[0] == '3s'
                            
                            for t in v[0:(i // 2)]:
                                r.append((t[0], t[1], 3))
                        
                        gapList = gapList[i:]
                        v = v[(i // 2):]
                        currSize = ('3', 18 + 2 * gapList[0])
                        i = 3
                        
                        if len(v) == 1:
                            break
                
                # Handle the final block
                
                i -= 1
                
                if currSize[0] == '3':
                    r.append((v[0][0], v[(i // 2) - 1][1], 3))
                
                elif currSize[0] == '4':
                    if r and r[-1][-1] == 4:
                        oldLast = r.pop()
                        r.append((oldLast[0], v[(i // 2) - 1][1], 4))
                    
                    else:
                        r.append((v[0][0], v[(i // 2) - 1][1], 4))
                
                else:
                    assert currSize[0] == '3s'
                    
                    for t in v[0:(i // 2)]:
                        r.append((t[0], t[1], 3))
            
            else:
                # it's a monospace group
                nGroups = len(v)
                nGlyphs = sum(t[1] - t[0] + 1 for t in v)
                
                if forApple or (((14 * nGroups) - 16) < nGlyphs):
                    for t in v:
                        r.append((t[0], t[1], 2))
                
                else:
                    r.append((v[0][0], v[-1][1], 5))
        
        sbitObj = self.sbitObj
        stk = sbitObj[ppemKey]
        dp = datPool.setdefault(ppemKey, {})
        
        for t in r:
            
            # Before yielding the entries, we need to do some checks for size
            # limitations of the corresponding bitmaps (since we never want to
            # have to use index format 1). We'll subdivide ranges where needed.
            
            actuals = span2.Span(stk.actualIterator(*t[:2]))
            ppemSmallerKey = (ppemKey[0] - 1, ppemKey[1] - 1, ppemKey[2])
            bSizes = {i: stk[i].binarySize() for i in actuals}
            
            if t[2] in {2, 5}:
                
                # Index formats 2 and 5 are used with monospace ranges, so we
                # need to check for sharing of data with the next smaller PPEM.
                
                assert len(set(iter(bSizes.values()))) == 1
                imageSize = bSizes[next(iter(actuals))]  # constant for mono
                ssKey = (ppemSmallerKey, ppemKey)
                
                if ssKey in sizeSharers:
                    ssSmaller = sizeSharers[ssKey]
                    dpSmaller = datPool[ppemSmallerKey]  # has to be there
                    
                    # The following list contains tuples. For tuples of shared
                    # images, there are 5 elements:
                    #
                    #       True,
                    #       firstGlyph,
                    #       lastGlyph,
                    #       firstGlyph's datOffset
                    #       lastGlyph's datOffset
                    #
                    # For tuples of non-shared images, there are only 4
                    # elements per tuple:
                    #
                    #       False,
                    #       firstGlyph,
                    #       lastGlyph,
                    #       firstGlyph's datOffset
                    
                    v = []
                    
                    for glyph in sorted(actuals):
                        if not v:
                            if glyph in ssSmaller:
                                v.append((
                                  True,
                                  glyph,
                                  glyph,
                                  dpSmaller[glyph],
                                  dpSmaller[glyph]))
                                
                                dp[glyph] = dpSmaller[glyph]
                            
                            else:
                                v.append((False, glyph, glyph, datOffset[0]))
                                dp[glyph] = datOffset[0]
                                datOffset[0] += imageSize
                        
                        else:
                            tLast = v[-1]
                            
                            if glyph in ssSmaller:
                                if tLast[0]:
                                    expectNewOffset = tLast[-1] + imageSize
                                    
                                    if expectNewOffset == dpSmaller[glyph]:
                                        v[-1] = (
                                          True,
                                          tLast[1],
                                          glyph,
                                          tLast[3],
                                          expectNewOffset)
                                    
                                    else:
                                        v.append((
                                          True,
                                          glyph,
                                          glyph,
                                          dpSmaller[glyph],
                                          dpSmaller[glyph]))
                                
                                else:
                                    v.append((
                                      True,
                                      glyph,
                                      glyph,
                                      dpSmaller[glyph],
                                      dpSmaller[glyph]))
                                    
                                dp[glyph] = dpSmaller[glyph]
                            
                            else:
                                if tLast[0]:
                                    v.append((
                                      False,
                                      glyph,
                                      glyph,
                                      datOffset[0]))
                                
                                else:
                                    v[-1] = ((
                                      False,
                                      tLast[1],
                                      glyph,
                                      tLast[3]))
                                
                                dp[glyph] = datOffset[0]    
                                datOffset[0] += imageSize
                    
                    # Note that in the following, I'm not doing anything to
                    # check to see if there was an untoward proliferation of
                    # little blocks, in an alternating "sharing/not-sharing"
                    # configuration. At some point, if that case arises often
                    # enough, we can optimize for it.
                    
                    for tSub in v:
                        yield (tSub[1], tSub[2], t[2], tSub[3])
                
                else:
                    yield((t[0], t[1], t[2], datOffset[0]))
                    
                    for glyph in sorted(actuals):
                        dp[glyph] = datOffset[0]
                        datOffset[0] += imageSize
            
            elif t[2] in {3, 4}:
                
                # Index formats 3 and 4 deals with non-monospace glyphs with an
                # offset per glyph (including adjacent identical offsets for
                # empty glyphs). Here we check that the offsets from a relative
                # zero (at the start of the dat group for this index3 entry)
                # don't exceed 64K bytes by the end. The group will be
                # subdivided if that happens (without optimization).
                
                if sum(bSizes[i] for i in actuals) < 65536:
                    yield ((t[0], t[1], t[2], datOffset[0]))
                    
                    for glyph in sorted(actuals):
                        dp[glyph] = datOffset[0]
                        datOffset[0] += bSizes[glyph]
                
                else:  # we need to subdivide here
                    v = []
                    cumulSize = 0
                    
                    for glyph in sorted(actuals):
                        thisSize = bSizes[glyph]
                        
                        if not v:
                            v.append([glyph, glyph])
                            cumulSize = thisSize
                        
                        elif cumulSize + thisSize > 65535:
                            v.append([glyph, glyph])
                            cumulSize = thisSize
                        
                        else:
                            v[-1][1] = glyph
                            cumulSize += thisSize
                        
                        dp[glyph] = datOffset[0]
                        datOffset[0] += thisSize
                    
                    for firstGlyph, lastGlyph in v:
                        yield ((firstGlyph, lastGlyph, t[2], dp[firstGlyph]))

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
