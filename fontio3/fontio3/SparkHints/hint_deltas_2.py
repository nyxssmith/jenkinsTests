#
# hint_deltas_2.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

# System imports
import collections
import fractions
import logging

# Other imports
from fontio3.fontdata import setmeta
from fontio3.SparkHints import hint_deltaspec
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Classes
#

class Hint_DELTAS_2(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing Spark DELTAS2 opcodes. These are sets of DeltaSpec
    objects.
    """
    
    kindString = 'DELTAS'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> obj = Hint_DELTAS_2({
        ...   hint_deltaspec.DeltaSpec(28, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(31, 31, 0.25)})
        >>> print(obj)
        DELTAS: Point 31 -1/8@28, 1/4@31
        """
        
        d = self._makeDict()
        sv = []
        F = fractions.Fraction
        
        for pointIndex in sorted(d):
            dSub = d[pointIndex]
            svSub = []
            
            for ppem in sorted(dSub):
                shift = dSub[ppem]
                svSub.append("%s@%d" % (F(shift), ppem))
            
            sv.append("Point %d %s" % (pointIndex, ', '.join(svSub)))
        
        return "DELTAS: %s" % ('; '.join(sv),)
    
    def _makeDict(self):
        """
        Returns a working dict whose top-level keys are point numbers, and
        whose top-level items are, in turn, dicts whose keys are ppem values
        and whose values are floating-point pixel distances.
        """
        
        d = collections.defaultdict(dict)
        
        for obj in self:
            d[obj.pointIndex][obj.ppem] = obj.shift
        
        assert len(d) == 1  # only one point supported for DELTAS
        return d
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
        
        >>> obj = Hint_DELTAS_2({
        ...   hint_deltaspec.DeltaSpec(28, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(31, 31, 0.25)})
        >>> d = {'deltaBase': 9, 'deltaShift': 3}
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | AE00 1F02 3769                           |....7i          |
        """
        
        band = 2  # hardwired for Hint_DELTAS_2
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        d = self._makeDict()
        w.add("BH", 0xAE, next(iter(d)))
        
        for pointIndex in sorted(d):
            dSub = d[pointIndex]
            w.add("B", len(dSub))
            
            for ppem in sorted(dSub):
                shift = dSub[ppem]
                fSteps = shift / grain
                nSteps = int(fSteps)
                
                if nSteps != fSteps:
                    raise ValueError("Shift cannot be represented!")
                
                codedSteps = nSteps + 8 - (nSteps > 0)
                
                if not (0 <= codedSteps <= 15):
                    raise ValueError("Shift cannot be represented!")
                
                codedPPEM = ppem - deltaBase
                
                if not (0 <= codedPPEM <= 15):
                    raise ValueError("PPEM cannot be represented!")
                
                w.add("B", (16 * codedPPEM) + codedSteps)
    
    def decompose(self):
        """
        Returns a list of Hint_DELTAS_2 objects matching self, but where each
        only has a single spec. This is used in hint analysis for compression.
        
        >>> obj = Hint_DELTAS_2({
        ...   hint_deltaspec.DeltaSpec(28, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(31, 31, 0.25)})
        >>> print(obj)
        DELTAS: Point 31 -1/8@28, 1/4@31
        
        >>> for part in obj.decompose():
        ...     print(part)
        DELTAS: Point 31 -1/8@28
        DELTAS: Point 31 1/4@31
        """
        
        f = type(self)
        r = []
        
        for obj in sorted(self):
            r.append(f([obj]))
        
        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_DELTAS_2 from the specified walker, with validation.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
            
            logger          The logger to which messages will be posted.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_DELTAS_2.fromvalidatedbytes
        >>> bs = utilities.fromhex("AE 00 1F 02 37 69")
        >>> d = {'deltaBase': 9, 'deltaShift': 3, 'logger': logger}
        >>> print((fvb(bs, **d)))
        test.DELTAS1 - DEBUG - Remaining walker bytes: 6
        DELTAS: Point 31 -1/8@28, 1/4@31
        
        >>> fvb(bs[:-1], **d)
        test.DELTAS1 - DEBUG - Remaining walker bytes: 5
        test.DELTAS1 - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('DELTAS1')
        else:
            logger = logger.getChild('DELTAS1')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        band = 2  # hardwired for Hint_DELTAS_2
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        op, pointIndex, count = w.unpack("BHB")
        
        if op != 0xAE:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0xAE, but got 0x%02X instead"))
            
            return None
        
        if w.length() < count:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        specs = w.group("B", count)
        r = cls()
        DS = hint_deltaspec.DeltaSpec
        
        for spec in specs:
            codedPPEM, codedSteps = divmod(spec, 16)
            ppem = codedPPEM + deltaBase
            uncodedSteps = codedSteps - 8 + (codedSteps >= 8)
            shift = grain * uncodedSteps
            r.add(DS(ppem, pointIndex, shift))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_DELTAS_2 from the specified walker.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
        
        >>> fb = Hint_DELTAS_2.frombytes
        >>> bs = utilities.fromhex("AE 00 1F 02 37 69")
        >>> d = {'deltaBase': 9, 'deltaShift': 3}
        >>> print((fb(bs, **d)))
        DELTAS: Point 31 -1/8@28, 1/4@31
        """
        
        band = 2  # hardwired for Hint_DELTAS_2
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        op, pointIndex, count = w.unpack("BHB")
        assert op == 0xAE
        specs = w.group("B", count)
        r = cls()
        DS = hint_deltaspec.DeltaSpec
        
        for spec in specs:
            codedPPEM, codedSteps = divmod(spec, 16)
            ppem = codedPPEM + deltaBase
            uncodedSteps = codedSteps - 8 + (codedSteps >= 8)
            shift = grain * uncodedSteps
            r.add(DS(ppem, pointIndex, shift))
        
        return r
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints self.
        """
        
        if 'p' in kwArgs:
            p = kwArgs.pop('p')
        else:
            p = pp.PP(**kwArgs)
        
        p(str(self))

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
    _test()

