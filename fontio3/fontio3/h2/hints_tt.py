#
# hints_tt.py
#
# Copyright © 2005-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Contiguous sequences of opcode objects.
"""

# System imports
import itertools
import operator

# Other imports
from fontio3.fontdata import seqmeta
from fontio3.h2 import opcode_tt
from fontio3.utilities import pp, span2
from functools import reduce

# -----------------------------------------------------------------------------

#
# Functions
#

def _pprint(p, obj, **kwArgs):
    cumulOffset = 0
    currIndentSpaces = ""
    preIndenters = {0x59, 0x1B}  # EIF, ELSE
    postIndenters = {0x1B, 0x58}  # ELSE, IF
    p(obj.infoString)
    
    for i, opObj in enumerate(obj):
        label = "%04d (0x%06X): " % (i, cumulOffset)
        
        if opObj.isPush:
            p(''.join([label, currIndentSpaces, "PUSH"]))
            extra = p.indent + p.indentDelta + 17 + len(currIndentSpaces)
            p2 = pp.PP(indent=extra, stream=p.stream, maxWidth=p.maxWidth)
            p2.sequence_tag_long(list(opObj))
        
        else:
            if opObj in preIndenters:
                currIndentSpaces = currIndentSpaces[p.indentDelta:]
            
            p(''.join([label, currIndentSpaces, str(opObj)]))
            
            if opObj in postIndenters:
                currIndentSpaces += " " * p.indentDelta
        
        cumulOffset += opObj.getOriginalLength()

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hints(tuple, metaclass=seqmeta.FontDataMetaclass):
    """
    Objects representing sequences of TrueType opcode objects.
    
    >>> s = utilities.fromhex("4B B0 0C 53 58 B0 27 1B B0 0E 59")
    >>> h = Hints.frombytes(s, infoString="Test hints")
    >>> h.pprint()
    Test hints
    0000 (0x000000): MPPEM[]
    0001 (0x000001): PUSH
                       [12]
    0002 (0x000003): GTEQ[]
    0003 (0x000004): IF[]
    0004 (0x000005):   PUSH
                         [39]
    0005 (0x000007): ELSE[]
    0006 (0x000008):   PUSH
                         [14]
    0007 (0x00000A): EIF[]
    
    >>> print(h)
    (MPPEM[], PUSH [12], GTEQ[], IF[], PUSH [39], ELSE[], PUSH [14], EIF[])
    """
    
    seqSpec = dict(
        item_followsprotocol = True,
        seq_pprintfunc = _pprint)
    
    attrSpec = dict(
        infoString = dict(
            attr_ignoreforcomparisons = True,
            attr_initfunc = (lambda: "Generic hints")))
    
    attrSorted = ()
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified writer. The following
        keyword arguments are supported:
        
            indexToByteOffset       An optional list which will be filled with
                                    byte offsets at which each discrete TT
                                    instruction began.
        
        >>> s = utilities.fromhex("4B B0 0C 53 58 B0 27 1B B0 0E 59")
        >>> h = Hints.frombytes(s, infoString="Test hints")
        >>> print(h)
        (MPPEM[], PUSH [12], GTEQ[], IF[], PUSH [39], ELSE[], PUSH [14], EIF[])
        >>> itbo = []
        >>> utilities.hexdump(h.binaryString(indexToByteOffset=itbo))
               0 | 4BB0 0C53 58B0 271B  B00E 59             |K..SX.'...Y     |
        >>> print(itbo)
        [0, 1, 3, 4, 5, 7, 8, 10]
        """
        
        itbo = kwArgs.get('indexToByteOffset', None)
        
        if itbo is None:
            for opObj in self:
                opObj.buildBinary(w, **kwArgs)
        
        else:
            startLen = w.byteLength
            
            for opObj in self:
                itbo.append(int(w.byteLength - startLen))
                opObj.buildBinary(w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Hints object from the data in the specified
        walker, doing validation.
        
        >>> s = utilities.fromhex("4B B0 0C 53 58 B0 27 1B B0 0E 59")
        >>> h = Hints.fromvalidatedbytes(s, infoString="Test")
        hints - DEBUG - Walker has 11 remaining bytes.
        hints.opcode 0 - DEBUG - Walker has 11 remaining bytes.
        hints.opcode 1 - DEBUG - Walker has 10 remaining bytes.
        hints.opcode 2 - DEBUG - Walker has 8 remaining bytes.
        hints.opcode 3 - DEBUG - Walker has 7 remaining bytes.
        hints.opcode 4 - DEBUG - Walker has 6 remaining bytes.
        hints.opcode 5 - DEBUG - Walker has 4 remaining bytes.
        hints.opcode 6 - DEBUG - Walker has 3 remaining bytes.
        hints.opcode 7 - DEBUG - Walker has 1 remaining bytes.
        
        >>> h.pprint()
        Test
        0000 (0x000000): MPPEM[]
        0001 (0x000001): PUSH
                           [12]
        0002 (0x000003): GTEQ[]
        0003 (0x000004): IF[]
        0004 (0x000005):   PUSH
                             [39]
        0005 (0x000007): ELSE[]
        0006 (0x000008):   PUSH
                             [14]
        0007 (0x00000A): EIF[]
        """
        
        if 'logger' in kwArgs:
            logger = kwArgs.pop('logger').getChild('hints')
        else:
            logger = utilities.makeDoctestLogger('hints')
        
        logger.debug((
          'V0001',
          int(w.length()),
          "Walker has %d remaining bytes."))
        
        v = []
        fvw = opcode_tt.fromvalidatedwalker
        
        while w.stillGoing():
            subLogger = logger.getChild("opcode %d" % (len(v),))
            v.append(fvw(w, logger=subLogger))
        
        return cls(v, **kwArgs)
        
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Hints object from the data in the specified
        walker.
        
        >>> s = utilities.fromhex("00")
        >>> h = Hints.frombytes(s, infoString="Test hints")
        """
        
        v = []
        fw = opcode_tt.fromwalker
        sawJump = False
        
        while w.stillGoing():
            v.append(fw(w))
        
        return cls(v, **kwArgs)
    
    def removeIFs(self):
        """
        Given a Hints object, returns a tuple of derived Hints objects. These
        derived objects will have the IFs "removed", so the analysis code can
        do its work without having to worry about quantum fissioning.
        
        >>> s = utilities.fromhex("4B B0 0C 53 58 B0 27 1B B0 0E 59 01")
        >>> h = Hints.frombytes(s, infoString="Test hints")
        >>> h.pprint()
        Test hints
        0000 (0x000000): MPPEM[]
        0001 (0x000001): PUSH
                           [12]
        0002 (0x000003): GTEQ[]
        0003 (0x000004): IF[]
        0004 (0x000005):   PUSH
                             [39]
        0005 (0x000007): ELSE[]
        0006 (0x000008):   PUSH
                             [14]
        0007 (0x00000A): EIF[]
        0008 (0x00000B): SVTCA[X]
        
        >>> for hSub in h.removeIFs():
        ...     hSub.pprint()
        Test hints
        0000 (0x000000): MPPEM[]
        0001 (0x000001): PUSH
                           [12]
        0002 (0x000003): GTEQ[]
        0003 (0x000004): POP[]
        0004 (0x000005): PUSH
                           [39]
        0005 (0x000007): SVTCA[X]
        Test hints
        0000 (0x000000): MPPEM[]
        0001 (0x000001): PUSH
                           [12]
        0002 (0x000003): GTEQ[]
        0003 (0x000004): POP[]
        0004 (0x000005): PUSH
                           [14]
        0005 (0x000007): SVTCA[X]
        """
        
        depth = 0
        specials = frozenset({0x1B, 0x58, 0x59})
        topIFs = []
        topELSEs = []
        topEIFs = []
        
        for i, op in enumerate(self):
            if op.isPush or op not in specials:
                continue
            
            if op == 0x58:  # IF
                if not depth:
                    topIFs.append(i)
                
                depth += 1
            
            elif op == 0x1B:  # ELSE
                if not depth:
                    raise ValueError("ELSE without IF at PC %d" % (i,))
                
                if depth == 1:
                    topELSEs.append(i)
            
            else:  # EIF
                if not depth:
                    raise ValueError("EIF without ELSE at PC %d" % (i,))
                
                if depth == 1:
                    topEIFs.append(i)
                    
                    if len(topELSEs) < len(topIFs):
                        topELSEs.append(None)
                
                depth -= 1
        
        if depth:  # unclosed IFs
            topEIFs.append(len(self))
            
            if len(topELSEs) < len(topIFs):
                topELSEs.append(None)
            
            depth = 0
        
        if not topIFs:
            return (self,)
        
        ifRanges = tuple(zip(topIFs, topEIFs))
        otherSpan = span2.Span.fromranges(ifRanges).inverted(0, len(self))
        
        allRanges = sorted(
          ifRanges + tuple(otherSpan.ranges()),
          key=operator.itemgetter(0))
        
        ifDict = {t: topELSEs[i] for i, t in enumerate(ifRanges)}
        vv = []
        popOp = opcode_tt.Opcode_nonpush(0x21)
        
        for t in allRanges:
            iIF, iEIF = t
            
            if t in ifDict:
                iELSE = ifDict[t]
                vv.append(((popOp,),))
                
                if iELSE is None:
                    h = type(self)(self[iIF+1:iEIF])
                    vv.append(h.removeIFs())
                
                else:
                    h1 = type(self)(self[iIF+1:iELSE])
                    h2 = type(self)(self[iELSE+1:iEIF])
                    vv.append(h1.removeIFs() + h2.removeIFs())
            
            else:
                vv.append((self[iIF:iEIF+1],))
        
        r = []
        sis = self.infoString
        
        for t in itertools.product(*vv):
            r.append(type(self)(reduce(operator.add, t), infoString=sis))
        
        return tuple(r)

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


