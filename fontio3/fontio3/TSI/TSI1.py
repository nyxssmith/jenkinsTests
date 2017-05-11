#
# TSI1.py
#
# Copyright © 2012-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# System imports
import collections

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.fontmath import matrix
from fontio3.h2 import analyzer, hints_tt
from fontio3.hints import hints_tt as hints_tt_old
from fontio3.TSI import TSILoc, TSILowLevel

# -----------------------------------------------------------------------------

#
# Constants
#

# The following is to get around a computed CALL. Grrrr.....

_fdef17_orig = utilities.fromhex(
  "20 69 B0 40 61 B0 00 8B "
  "20 B1 2C C0 8A 8C B8 10 "
  "00 62 60 2B 0C 64 23 64 "
  "61 5C 58 B0 03 61 59")

_fdef17_rewrite = utilities.fromhex(
  "20 69 20 B0 01 51 58 B0 "
  "2C 1B 20 B0 02 54 58 B0 "
  "2D 1B 20 B0 03 54 58 B0 "
  "2E 1B B0 2F 59 59 59 2B "
  "0C 64 23 64 61 5C 58 B0 "
  "03 61 59")

_fdef49_orig = utilities.fromhex(
  "4B 53 58 20 B0 03 25 49 "
  "64 69 20 B0 05 26 B0 06 "
  "25 49 64 23 61 B0 80 62 "
  "B0 20 61 6A B0 0E 23 44 "
  "B0 04 26 10 B0 0E F6 8A "
  "10 B0 0E 23 44 B0 0E F6 "
  "B0 0E 23 44 B0 0E ED 1B "
  "8A B0 04 26 11 12 20 39 "
  "23 20 39 2F 2F 59")

_fdef49_rewrite = bytes([1])  # SVTCA[x] by default

# -----------------------------------------------------------------------------

#
# Classes
#

class TSI1(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    """
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda i: "Glyph %d" % (i,)),
        item_pprintlabelpresort = True,
        item_renumberdirectkeys = True)
    
    attrSpec = dict(
        cvt = dict(
            attr_followsprotocol = True,
            attr_label = "Control Value Table"),
        
        fpgm = dict(
            attr_followsprotocol = True,
            attr_label = "Function definitions"),
        
        prep = dict(
            attr_followsprotocol = True,
            attr_label = "Pre-program"))
    
    #
    # Methods
    #
    
    def _hintObjectIterator(self):
        """
        Returns a generator over all the Hints objects, either in glyphs or in
        one of the special attributes.
        """
        
        for obj in self.values():
            if obj:
                yield obj
        
        if self.cvt:
            yield self.cvt
        
        if self.fpgm:
            yield self.fpgm
        
        if self.prep:
            yield self.prep
    
    @staticmethod
    def _phasedDecoder(s):
        """
        """
        
        try:
            r = str(s, 'utf-8')
        except UnicodeDecodeError:
            r = None
        
        if r is not None:
            return r
        
        try:
            r = str(s, 'ascii')
        except UnicodeDecodeError:
            r = None
        
        if r is not None:
            return r
        
        try:
            r = str(s, 'mac-roman')
        except UnicodeDecodeError:
            r = None
        
        if r is None:
            raise ValueError("Unable to convert to Unicode: '%s'" % (s,))
        
        return r
    
    @staticmethod
    def _processComposite(obj):
        sv = []
        
        for comp in obj.components:
            if comp.useMyMetrics:
                sv.append("USEMYMETRICS[]")
            
            letter = ('R' if comp.roundToGrid else 'r')
            m = comp.transformationMatrix
            mShift, mScale = m.toShiftAndScale(not comp.offsetsAreScaled)
            
            if mScale == matrix.identityMatrix:
                t = (letter, comp.glyphIndex, mShift[2][0], mShift[2][1])
                sv.append("OFFSET[%s], %d, %d, %d" % t)
            
            else:
                if mScale.is2by2Equivalent():
                    t = (
                      letter,
                      comp.glyphIndex,
                      mShift[2][0],
                      mShift[2][1],
                      mScale[0][0],
                      mScale[0][1],
                      mScale[1][0],
                      mScale[1][1])
                
                    fmt = "SOFFSET[%d], %d, %d, %6.4f, %6.4f, %6.4f, %6.4f"
                    sv.append(fmt % t)
                
                else:
                    raise ValueError("Perspective not supported!")
        
        return sv
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for a TSI1 object to the specified LinkedWriter.

        Keyword arguments:

            locCallback     If the client is interested in getting the TSILoc
                            table constructed during this method's execution,
                            then a callback should be provided. If present,
                            this callback will be called with the new TSILoc
                            object as the sole parameter.
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()

        locObj = TSILoc.TSILoc()

        # Add the glyph records

        walkOffset = 0

        for i in range(len(self)):
            item = self.get(i, None)

            if item:
                itemText = item.encode('ascii', errors='replace')
            else:
                itemText = b''

            itemLen = len(itemText)
            locObj[i] = (itemLen, walkOffset)

            if itemText is not None:
                w.addString(itemText)

            walkOffset += itemLen

        # Add the extra records: magic, prep, fpgm, cvt, reserved
        
        locObj.magic = (0, 0xABFC1F34)
        
        for attr, item in ((b'prep', self.prep), (b'fpgm', self.fpgm), (b'cvt ', self.cvt)):
            if item:
                itemText = item.encode('ascii', errors='replace')
            else:
                itemText = b''

            itemLen = len(itemText)
            locObj.__dict__[attr] = (itemLen, walkOffset)

            if itemText is not None:
                w.addString(itemText)

            walkOffset += itemLen

        locObj.reserved = (0, walkOffset)

        if 'locCallback' in kwArgs:
            kwArgs['locCallback'](locObj)
    
    def compile(self, editor, **kwArgs):
        """
        Takes all the data from self and recompiles it into TrueType binary,
        and replaces the relevant portions of the specified Editor.
        """
        
        from fontio3 import cvt, fpgm, prep
        
        if self.cvt:
            bs = self.cvt.toTTBinary_cvt()
            editor[b'cvt '] = cvt.Cvt.frombytes(bs)
        
        elif b'cvt ' in editor:
            del editor[b'cvt ']
        
        if self.fpgm:
            bs = self.fpgm.toTTBinary_fpgm()
            editor.fpgm = fpgm.Fpgm.frombytes(bs)
        
        elif b'fpgm' in editor:
            del editor.fpgm
        
        if self.prep:
            bs = self.prep.toTTBinary()
            editor.prep = prep.Prep.frombytes(bs)
        
        elif b'prep' in editor:
            del editor.prep
        
        for glyphIndex, s in self.items():
            if s:
                editor.glyf[glyphIndex].hintBytes = s.toTTBinary()
            else:
                editor.glyf[glyphIndex].hintBytes = b''
        
        editor.changed(b'glyf')
    
    @classmethod
    def fromeditor(cls, editor, **kwArgs):
        """
        Creates and returns a TSI1 object from the binary data in the specified
        Editor's 'prep', 'fpgm', 'cvt ', and 'glyf' tables. This is done using
        the TSILowLevel module's functionality.
        
        Note that this is essentially decompilation (and, in fact, a synonym
        for this method is decompile()). If you want to create a TSI1 object
        from the actual contents of the b'TSI1' table, use fromwalker() or its
        kin, as usual.
        """
        
        r = cls()
        fb = hints_tt.Hints.frombytes
        doPrepExtraInfo = kwArgs.pop('doPrepExtraInfo', False)
        
        if editor.reallyHas(b'fpgm'):
            a = analyzer.analyzeFPGM(editor.fpgm, useDictForm=True)
            sd = {}
            func = TSILowLevel.Hints.frombinary_f
            
            for fdefIndex, obj in editor.fpgm.items():
                bsOld = obj.binaryString()
                
                if bsOld == _fdef17_orig:
                    bsOld = _fdef17_rewrite
                elif bsOld == _fdef49_orig:
                    bsOld = _fdef49_rewrite
                
                obj = fb(bsOld)  # into h2 space...
                sd[fdefIndex] = func(obj, fdefIndex, analysis=a, **kwArgs)
            
            r.fpgm = TSILowLevel.Hints.fromparts([sd[i] for i in sorted(sd)])
        
        else:
            a = {}
            r.fpgm = ''
        
        if editor.reallyHas(b'prep'):
            if doPrepExtraInfo:
                r.prep = TSILowLevel.Hints.frombinary_gp(
                  editor.prep,
                  analysis = a,
                  extraInfo = collections.defaultdict(dict),
                  **kwArgs)
            
            else:
                r.prep = TSILowLevel.Hints.frombinary_gp(
                  editor.prep,
                  analysis = a,
                  **kwArgs)
        
        else:
            r.prep = ''
        
        if editor.reallyHas(b'cvt '):
            r.cvt = TSILowLevel.Hints.frombinary_c(editor[b'cvt '], **kwArgs)
        else:
            r.cvt = ''
        
        H = TSILowLevel.Hints
        fbOld = hints_tt_old.Hints.frombytes
        funcNew = TSILowLevel.Hints.frombinary_gp
        
        for glyphIndex, obj in editor.glyf.items():
            if (not obj) or (not obj.hintBytes):
                r[glyphIndex] = funcNew('')
                continue
            
            if obj.isComposite:
                sv = cls._processComposite(obj)
                
                if obj.hintBytes:
                    hOld = fbOld(obj.hintBytes)
                    hNew = funcNew(hOld, analysis=a, **kwArgs)
                    sv.append(str(hNew.encode('utf-8'), 'utf-8'))
                
                r[glyphIndex] = H('\r'.join(sv), analysis=a, **kwArgs)
            
            elif obj.hintBytes:
                hOld = fbOld(obj.hintBytes)
                r[glyphIndex] = funcNew(hOld, analysis=a, **kwArgs)
            
            else:
                r[glyphIndex] = H('')
        
        return r
    
    decompile = fromeditor
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TSI1 object from the specified walker. The
        following keyword arguments are supported:
        
            analysis    The results of a fontio3.h2.analyzer.analyzeFPGM()
                        call. This may be omitted, but if it is then an Editor
                        must be provided via the editor keyword, so one can be
                        constructed.
            
            editor      An Editor; if this is not provided, the analysis must
                        be present.
            
            locObject   A TSILoc object for the associated TSI0 table.
        
        %start
        %kind
        protocol method
        %return
        A new PostHeader object unpacked from the data in the specified walker.
        %pos
        w
        A walker with the data to unpack.
        %kw
        analysis
        The results of a fontio3.h2.analyzer.analyzeFPGM() call. This may be
        omitted, but if it is then an Editor must be provided via the 'editor'
        kwArg.
        %kw
        editor
        An Editor-class object, used to construct the 'fpgm' analysis. If this
        is not provided, then the 'analysis' kwArg must be present.
        %kw
        locObject
        A TSILoc object for the associated 'TSI0' table.
        %note
        It's a good idea to provide an 'analysis' kwArg directly; if an Editor
        is provided, it will be slower since the analysis will have to be
        re-created several times.
        %end
        """
        
        r = cls()
        locObj = kwArgs['locObject']
        H = TSILowLevel.Hints
        _pd = cls._phasedDecoder
        
        for glyphIndex, (length, offset) in locObj.items():
            if length:
                s = w.subWalker(offset, relative=True, newLimit=length).rest()
            else:
                s = b''
            
            r[glyphIndex] = H(_pd(s), **kwArgs)
        
        length, offset = locObj.cvt
        
        if length:
            s = w.subWalker(offset, relative=True, newLimit=length).rest()
        else:
            s = b''
        
        r.cvt = H(_pd(s), cvtCase=True, **kwArgs)
        
        length, offset = locObj.fpgm
        
        if length:
            s = w.subWalker(offset, relative=True, newLimit=length).rest()
        else:
            s = b''
        
        r.fpgm = H(_pd(s), **kwArgs)
        
        length, offset = locObj.prep
        
        if length:
            s = w.subWalker(offset, relative=True, newLimit=length).rest()
        else:
            s = b''
        
        r.prep = H(_pd(s), **kwArgs)
        return r
    
    def usage(self):
        """
        Walks all the hints and determines the actual set of used FDEFs,
        storage locations, and CVT indices, and returns a tuple with frozensets
        (allFDEFs, allCVTs, allStorage). Note that these may not be used in any
        case but where they're defined.
        """
        
        f, c, s = set(), set(), set()
        t = (('cvtIndex', c), ('storageIndex', s), ('fdefIndex', f))
        
        for obj in self._hintObjectIterator():
            for (start, stop), kind in obj.locInfo.items():
                for test, d in t:
                    if kind == test:
                        d.add(int(obj[start:stop]))
        
        return (frozenset(f), frozenset(c), frozenset(s))

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

