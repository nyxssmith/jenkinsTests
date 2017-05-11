#
# TSI3.py
#
# Copyright © 2012-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.TSI import TSILoc, TSIHighLevel

# -----------------------------------------------------------------------------

#
# Classes
#

class TSI3(dict, metaclass=mapmeta.FontDataMetaclass):
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
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for a TSI3 object to the specified LinkedWriter.

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
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new TSI3 object from the specified walker. The
        following keyword arguments are supported:
        
            analysis    The results of a fontio3.h2.analyzer.analyzeFPGM()
                        call. This may be omitted, but if it is then an Editor
                        must be provided via the editor keyword, so one can be
                        constructed.
            
            editor      An Editor; if this is not provided, the analysis must
                        be present.
            
            locObject   A TSILoc object for the associated TSI2 table.
        
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
        A TSILoc object for the associated 'TSI2' table.
        %note
        It's a good idea to provide an 'analysis' kwArg directly; if an Editor
        is provided, it will be slower since the analysis will have to be
        re-created several times.
        %end
        """
        
        r = cls()
        locObj = kwArgs['locObject']
        H = TSIHighLevel.Hints
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
        case but their definition.
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

