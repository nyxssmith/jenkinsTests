#
# TSIHighLevel.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# System imports
import re

# Other imports
from fontio3.fontdata import textmeta
from fontio3.h2 import analyzer
from fontio3.TSI import TSILowLevel, TSIUtilities

# -----------------------------------------------------------------------------

#
# Constants
#

P = 'pointIndex'
C = 'cvtIndex'
O = 'optional'
G = '_generic'
K = 'kinds'

DISPATCH = {
  'align': (G, {K: ('rest', P)}),
  'call': ('_call', {}),
  'dalign': ('_align', {'atCount': 1}),
  'diagonal>>': (G, {K: (P, P, P, P, C, O, 'ppem'), 'tweaks': {5: (1, 0)}}),
  'height': (G, {K: (P, C)}),
  'intersect': ('_align', {'atCount': 2}),
  'mainstrokeangle': (G, {K: ('angle',)}),
  'stroke>>': (G, {K: (P, P, P, P, C)}),
  'xalign': ('_align', {'atCount': 1}),
  'xanchor': (G, {K: (P,)}),
  'xbdelta': ('_delta', {}),
  'xdelta': ('_delta', {}),
  'xdiagonal>>': (G, {K: (P, P, P, P, C, O, 'ppem'), 'tweaks': {5: (1, 0)}}),
  'xdist': (G, {K: (P, P, O)}),
  'xdist/': (G, {K: (P, P, O)}),
  'xdist//': (G, {K: (P, P, O)}),
  'xdoublegrid': (G, {K: ('rest', P)}),
  'xdowntogrid': (G, {K: ('rest', P)}),
  'xgdelta': ('_delta', {}),
  'xhalfgrid': (G, {K: ('rest', P)}),
  'xinterpolate': (G, {K: ('rest', P)}),
  'xipanchor': (G, {K: ('rest', P)}),
  'xlink': (G, {K: (P, P, C, O)}),
  'xlink/': (G, {K: (P, P, C, O)}),
  'xlink//': (G, {K: (P, P, C, O)}),
  'xmove': (G, {K: ('pixels', P)}),
  'xnoround': (G, {K: ('rest', P)}),
  'xshift': (G, {K: ('rest', P)}),
  'xuptogrid': (G, {K: ('rest', P)}),
  'yalign': ('_align', {'atCount': 1}),
  'yanchor': (G, {K: (P, O, C)}),
  'ybdelta': ('_delta', {}),
  'ydelta': ('_delta', {}),
  'ydiagonal>>': (G, {K: (P, P, P, P, C, O, 'ppem'), 'tweaks': {5: (1, 0)}}),
  'ydist': (G, {K: (P, P, O)}),
  'ydist/': (G, {K: (P, P, O)}),
  'ydist//': (G, {K: (P, P, O)}),
  'ydoublegrid': (G, {K: ('rest', P)}),
  'ydowntogrid': (G, {K: ('rest', P)}),
  'ygdelta': ('_delta', {}),
  'yhalfgrid': (G, {K: ('rest', P)}),
  'yinterpolate': (G, {K: ('rest', P)}),
  'yipanchor': (G, {K: ('rest', P)}),
  'ylink': (G, {K: (P, P, C, O)}),
  'ylink/': (G, {K: (P, P, C, O)}),
  'ylink//': (G, {K: (P, P, C, O)}),
  'ymove': (G, {K: ('pixels', P)}),
  'ynoround': (G, {K: ('rest', P)}),
  'yshift': (G, {K: ('rest', P)}),
  'yuptogrid': (G, {K: ('rest', P)}),
  }

del K, G, O, C, P

_srt = '|'.join(sorted(DISPATCH))
PAT_OP = re.compile(r'(%s)\s*\(\s*([^)]*)\s*\)' % (_srt,), re.I)
del _srt

PAT_COMMA = re.compile(r'([^,\s]+)')
PAT_DELTA_POINT = re.compile(r'\s*([0-9]+)')
PAT_DELTA_SPEC = re.compile(r'\s*([0-9-/]+)\s*@\s*([0-9.;]+)')
PAT_DELTA_SIZE = re.compile(r'([0-9]+)(%[0-9]+)?')
PAT_ASM = re.compile(r'asm\s*\(\s*"([^"]+)"\s*\)', re.I)
PAT_CALL = re.compile(r'([0-9-]+)')

StartStop = TSIUtilities.StartStop
LocInfo = TSIUtilities.LocInfo

# -----------------------------------------------------------------------------

#
# Functions
#

def _cvtHelper(obj, **kwArgs):
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'cvtIndex':
            yield (start, stop - start)

def _fdefHelper(obj, **kwArgs):
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'fdefIndex':
            yield (start, stop - start)

def _glyphHelper(obj, **kwArgs):
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'glyphIndex':
            yield (start, stop - start)

def _pointHelper(obj, **kwArgs):
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'pointIndex':
            yield (start, stop - start, kwArgs.get('glyphIndex', None))

def _storageHelper(obj, **kwArgs):
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'storageIndex':
            yield (start, stop - start)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hints(str, metaclass=textmeta.FontDataMetaclass):
    """
    """
    
    textSpec = dict(
        text_findcvtsfunc = _cvtHelper,
        text_findfdefsfunc = _fdefHelper,
        text_findglyphsfunc = _glyphHelper,
        text_findpointsfunc = _pointHelper,
        text_findstoragefunc = _storageHelper)
    
    attrSpec = dict(
        locInfo = dict(
            attr_followsprotocol = True))
    
    #
    # Methods
    #
    
    def __new__(cls, s, **kwArgs):
        """
        Create and return a new Hints. Keyword arguments are:
        
            analysis
            editor
        
        >>> s = "/* a comment */ XAnchor(/*blah*/ 12 )"
        >>> utilities.hexdump(s.encode('ascii'))
               0 | 2F2A 2061 2063 6F6D  6D65 6E74 202A 2F20 |/* a comment */ |
              10 | 5841 6E63 686F 7228  2F2A 626C 6168 2A2F |XAnchor(/*blah*/|
              20 | 2031 3220 29                             | 12 )           |
        >>> Hints(s).pprint()
        /* a comment */ XAnchor(/*blah*/ 12 )
        locInfo:
          (33, 35): pointIndex
        
        >>> Hints('YAnchor(40)').pprint()
        YAnchor(40)
        locInfo:
          (8, 10): pointIndex
        
        >>> Hints('YAnchor(10,11)').pprint()
        YAnchor(10,11)
        locInfo:
          (8, 10): pointIndex
          (11, 13): cvtIndex
        
        >>> Hints('XDiagonal>>(1,2,3,4,5,@6)').pprint()
        XDiagonal>>(1,2,3,4,5,@6)
        locInfo:
          (12, 13): pointIndex
          (14, 15): pointIndex
          (16, 17): pointIndex
          (18, 19): pointIndex
          (20, 21): cvtIndex
          (23, 24): ppem
        
        >>> Hints('XAlign(1, 2, 3)').pprint()
        XAlign(1, 2, 3)
        locInfo:
          (7, 8): pointIndex
          (10, 11): pointIndex
          (13, 14): pointIndex
        
        >>> Hints('XAlign(1, 2, @3)').pprint()
        XAlign(1, 2, @3)
        locInfo:
          (7, 8): pointIndex
          (10, 11): pointIndex
          (14, 15): ppem
        
        >>> Hints('Intersect(1,2,3,4,5)').pprint()
        Intersect(1,2,3,4,5)
        locInfo:
          (10, 11): pointIndex
          (12, 13): pointIndex
          (14, 15): pointIndex
          (16, 17): pointIndex
          (18, 19): pointIndex
        
        >>> Hints('Intersect(1,2,3,4,@5)').pprint()
        Intersect(1,2,3,4,@5)
        locInfo:
          (10, 11): pointIndex
          (12, 13): pointIndex
          (14, 15): pointIndex
          (16, 17): pointIndex
          (19, 20): ppem
        
        >>> Hints('Intersect(1,2,3,@4,@5)').pprint()
        Intersect(1,2,3,@4,@5)
        locInfo:
          (10, 11): pointIndex
          (12, 13): pointIndex
          (14, 15): pointIndex
          (17, 18): ppem
          (20, 21): ppem
        
        >>> Hints('YBDelta(55,1/8@26,1/4@14;22..25;49..51%6)').pprint()
        YBDelta(55,1/8@26,1/4@14;22..25;49..51%6)
        locInfo:
          (8, 10): pointIndex
          (11, 14): pixels
          (15, 17): ppem
          (18, 21): pixels
          (22, 24): ppem
          (25, 27): ppem
          (29, 31): ppem
          (32, 34): ppem
          (36, 38): ppem
        
        >>> Hints('XAnchor(19)  ASM("#PUSH, 38  RS[]")').pprint()
        XAnchor(19)  ASM("#PUSH, 38  RS[]")
        locInfo:
          (8, 10): pointIndex
          (25, 27): storageIndex
        """
        
        if not isinstance(s, str):
            # Convert s into a Unicode string
            for enc in ('ascii', 'utf-8', 'macroman'):
                sConv = None
                
                try:
                    sConv = str(s, enc)
                except UnicodeDecodeError:
                    pass
                
                if sConv is not None:
                    s = sConv
                    break
            
            else:
                raise ValueError("Unknown encoding!")
        
        r = str.__new__(cls, s)
        r.locInfo = LocInfo()  # suborn __init__'s role here, since we need it
        r.state = {}
        r._getOrMakeAnalysis(**kwArgs)
        r._makeLocInfo(**kwArgs)
        del r.state
        return r
    
    def _align(self, s, startOffset, **kwArgs):
        """
        """
        
        # We do a quick-and-dirty look at the presence or absence of a '@'
        # marker on the final argument(s).
        
        atCount = kwArgs.pop('atCount')
        sv = [x.strip() for x in s.split(',')]
        i = 1
        
        while (i <= len(sv)) and (sv[-i].startswith('@')):
            i += 1
        
        i -= 1
        assert i <= atCount
        
        if i:
            kinds = ('pointIndex',) * (len(sv) - i) + ('ppem',) * i
            tweaks = {len(sv) - x - 1: (1, 0) for x in range(i)}
        
        else:
            kinds = ('rest', 'pointIndex')
            tweaks = {}
        
        self._generic(s, startOffset, kinds=kinds, tweaks=tweaks)
    
    def _asm(self, s, startOffset, **kwArgs):
        """
        """
        
        h = TSILowLevel.Hints(s, analysis=self.state['fdefAnalysis'])
        li = self.locInfo
        
        for ssLow, kind in h.locInfo.items():
            ssHigh = StartStop(
              ssLow.start + startOffset,
              ssLow.stop + startOffset)
            
            li[ssHigh] = kind
    
    def _call(self, s, startOffset, **kwArgs):
        """
        """
        
        li = self.locInfo
        a = self.state['fdefAnalysis']
        v = []
        
        for m in PAT_CALL.finditer(s):
            v.append((int(m.group(1)), m.start(1), m.end(1)))
        
        fdefIndex, start, stop = v.pop()
        v.reverse()
        
        if fdefIndex not in a:
            raise ValueError("Unknown FDEF: %d" % (fdefIndex,))
        
        ss = StartStop(startOffset + start, startOffset + stop)
        li[ss] = 'fdefIndex'
        d = {i: t[0] for i, t in a[fdefIndex][0].items()}
        
        for i, (s, start, stop) in enumerate(v):
            if i not in d:
                continue
            
            ss = StartStop(startOffset + start, startOffset + stop)
            li[ss] = d[i]
    
    def _delta(self, s, startOffset, **kwArgs):
        """
        """
        
        li = self.locInfo
        m = PAT_DELTA_POINT.match(s)
        assert m is not None
        ss = StartStop(m.start(1) + startOffset, m.end(1) + startOffset)
        li[ss] = 'pointIndex'
        
        for m in PAT_DELTA_SPEC.finditer(s):
            ss = StartStop(m.start(1) + startOffset, m.end(1) + startOffset)
            li[ss] = 'pixels'
            
            for mSub in PAT_DELTA_SIZE.finditer(m.group(2)):
                start = m.start(2) + mSub.start(1) + startOffset
                stop = m.start(2) + mSub.end(1) + startOffset
                ss = StartStop(start, stop)
                li[ss] = 'ppem'
    
    @staticmethod
    def _expandKinds(count, oldKinds):
        """
        """
        
        rv = []
        i = 0
        optionalCase = False
        
        while (i < len(oldKinds)) and (count > 0):
            kind = oldKinds[i]
            
            if kind == 'rest':
                rv.extend([oldKinds[i+1]] * (count - len(rv)))
                i = len(oldKinds)
                count = 0
            
            elif kind == 'optional':
                optionalCase = True
            
            else:
                rv.append(kind)
                count -= 1
            
            i += 1
        
        assert ((count == 0) or optionalCase)
        return tuple(rv)
    
    def _generic(self, s, startOffset, **kwArgs):
        """
        """
        
        li = self.locInfo
        v = []
        tweaks = kwArgs.get('tweaks', {})
        
        for m in PAT_COMMA.finditer(s):
            v.append((m.group(1), m.start(1) + startOffset))
        
        kinds = self._expandKinds(len(v), kwArgs.get('kinds', ()))
        
        for i, (t, kind) in enumerate(zip(v, kinds)):
            if kind is None:
                continue
            
            x, offset = t
            startTweak, stopTweak = tweaks.get(i, (0, 0))
            start = offset + startTweak
            stop = offset + len(x) + stopTweak
            ss = StartStop(start, stop)
            li[ss] = kind
    
    def _getOrMakeAnalysis(self, **kwArgs):
        """
        Fills in self.state['fdefAnalysys'].
        """
        
        a = None
        
        if 'analysis' in kwArgs:
            a = kwArgs['analysis']
        
        elif 'editor' in kwArgs:
            e = kwArgs['editor']
            
            if e.reallyHas('fpgm'):
                a = analyzer.analyzeFPGM(e.fpgm, useDictForm=True)
        
        self.state['fdefAnalysis'] = a
    
    def _makeLocInfo(self, **kwArgs):
        """
        """
        
        decommented = TSIUtilities.stripComments(str(self))[0]
        
        # We do ASM() blocks first, because of their special parsing needs.
        # We also change the ASM block to spaces, so it won't interfere with
        # the regular PAT_OP parsing.
        
        asmLocs = []
        
        for m in PAT_ASM.finditer(decommented):
            asmLocs.append((m.start(0), m.end(0)))
            self._asm(m.group(1), m.start(1))
        
        if asmLocs:
            sv = list(decommented)
            
            for start, stop in reversed(asmLocs):
                sv[start:stop] = [" "] * (stop - start)
            
            decommented = ''.join(sv)
        
        # Now that the ASM() blocks are done, do the normal PAT_OP parsing.
        
        for m in PAT_OP.finditer(decommented):
            mString, kwd = DISPATCH[m.group(1).lower()]
            getattr(self, mString)(m.group(2), m.start(2), **kwd)
    
    def _renumberHelper(self, func, *args, **kwArgs):
        td = {}
        kwArgs['trackDeltas'] = td
        r = func(self, *args, **kwArgs)
        
        cumulDelta = 0
        liOld = r.locInfo
        liNew = {}
        
        for ssOld in sorted(liOld):
            tTest = (ssOld.start, ssOld.stop - 1)
            
            if tTest in td:
                ssNew = StartStop(
                  ssOld.start + cumulDelta,
                  ssOld.stop + cumulDelta + td[tTest])
                
                cumulDelta += td[tTest]
            
            else:
                ssNew = StartStop(
                  ssOld.start + cumulDelta,
                  ssOld.stop + cumulDelta)
            
            liNew[ssNew] = liOld[ssOld]
        
        r.locInfo.clear()
        r.locInfo.update(liNew)
        return r
    
    def cvtsRenumbered(self, **kwArgs):
        """
        A front end for the metaclass's method, using the trackDeltas feature
        to make changes to locInfo after the renumbering is done.
        """
        
        return self._renumberHelper(textmeta.M_cvtsRenumbered, **kwArgs)
    
    def fdefsRenumbered(self, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(textmeta.M_fdefsRenumbered, **kwArgs)
    
    @classmethod
    def fromparts(cls, parts):
        """
        Given a collection of Hints objects, combine them into a single Hints
        object and return it. This code adjusts all the locInfo offsets to
        match the new, single aggregated string.
        """
        
        cumulLen = 0
        sv = []
        li = LocInfo()
        
        for part in parts:
            sRaw = str(part.encode('utf-8'), 'utf-8')
            
            for ssOld, s in part.locInfo.items():
                ssNew = StartStop(ssOld[0] + cumulLen, ssOld[1] + cumulLen)
                li[ssNew] = s
            
            sv.append(sRaw)
            cumulLen += (len(sRaw) + 1)  # the +1 is for the \r added below...
        
        return cls('\r'.join(sv), locInfo=li)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        return cls(w.rest(), **kwArgs)
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(
          textmeta.M_glyphsRenumbered,
          oldToNew,
          **kwArgs)
    
    def pointsRenumbered(self, mapData, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(
          textmeta.M_pointsRenumbered,
          mapData,
          **kwArgs)
    
    def storageRenumbered(self, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(textmeta.M_storageRenumbered, **kwArgs)

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

