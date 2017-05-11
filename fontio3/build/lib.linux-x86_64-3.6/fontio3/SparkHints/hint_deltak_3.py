#
# hint_deltak_3.py
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

class Hint_DELTAK_3(set, metaclass=setmeta.FontDataMetaclass):
    """
    Objects representing Spark DELTAK3 opcodes. These are sets of DeltaSpec
    objects.
    """
    
    kindString = 'DELTAK'
    
    #
    # Methods
    #
    
    def __str__(self):
        """
        Returns a string representation of self.
        
        >>> obj = Hint_DELTAK_3({
        ...   hint_deltaspec.DeltaSpec(44, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 31, 0.25),
        ...   hint_deltaspec.DeltaSpec(44, 38, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 38, 0.25)})
        >>> print(obj)
        DELTAK: Point 31 -1/8@44, 1/4@47; Point 38 -1/8@44, 1/4@47
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
        
        return "DELTAK: %s" % ('; '.join(sv),)
    
    def _makeDict(self):
        """
        Returns a working dict whose top-level keys are point numbers, and
        whose top-level items are, in turn, dicts whose keys are ppem values
        and whose values are floating-point pixel distances.
        
        A ValueError is raised if the ppem/distance mappings are not identical
        for all points.
        
        >>> obj = Hint_DELTAK_3({
        ...   hint_deltaspec.DeltaSpec(44, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 31, 0.25),
        ...   hint_deltaspec.DeltaSpec(44, 38, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 38, 0.25)})
        >>> d = obj._makeDict()
        >>> sorted(d)
        [31, 38]
        >>> obj.add(hint_deltaspec.DeltaSpec(29, 31, -0.125))
        >>> d = obj._makeDict()
        Traceback (most recent call last):
          ...
        ValueError: Non-matching specs in DELTAK points!
        """
        
        d = collections.defaultdict(dict)
        
        for obj in self:
            d[obj.pointIndex][obj.ppem] = obj.shift
        
        # The ppem/shift values must be the same for all points for DELTAK
        checkSet = set(frozenset(iter(dSub.items())) for dSub in d.values())
        
        if len(checkSet) != 1:
            raise ValueError("Non-matching specs in DELTAK points!")
        
        return d
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content of self to the specified LinkedWriter.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
        
        >>> obj = Hint_DELTAK_3({
        ...   hint_deltaspec.DeltaSpec(44, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 31, 0.25),
        ...   hint_deltaspec.DeltaSpec(44, 38, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 38, 0.25)})
        >>> d = {'deltaBase': 9, 'deltaShift': 3}
        >>> utilities.hexdump(obj.binaryString(**d))
               0 | A902 001F 0026 0237  69                  |.....&.7i       |
        """
        
        band = 3  # hardwired for Hint_DELTAK_3
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        d = self._makeDict()
        points = sorted(d)
        ppemDists = sorted(d[points[0]].items())
        w.add("BB", 0xA9, len(points))
        w.addGroup("H", points)
        w.add("B", len(ppemDists))
        
        for ppem, shift in ppemDists:
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
        Returns a list of Hint_DELTAK_3 objects matching self, but where each
        only has a single spec. This is used in hint analysis for compression.
        
        >>> obj = Hint_DELTAK_3({
        ...   hint_deltaspec.DeltaSpec(44, 31, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 31, 0.25),
        ...   hint_deltaspec.DeltaSpec(44, 38, -0.125),
        ...   hint_deltaspec.DeltaSpec(47, 38, 0.25)})
        >>> print(obj)
        DELTAK: Point 31 -1/8@44, 1/4@47; Point 38 -1/8@44, 1/4@47
        
        >>> for part in obj.decompose():
        ...     print(part)
        DELTAK: Point 31 -1/8@44
        DELTAK: Point 38 -1/8@44
        DELTAK: Point 31 1/4@47
        DELTAK: Point 38 1/4@47
        """
        
        f = type(self)
        r = []
        
        for obj in sorted(self):
            r.append(f([obj]))
        
        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_DELTAK_3 from the specified walker, with validation.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
            
            logger          The logger to which messages will be posted.
        
        >>> logger = utilities.makeDoctestLogger("test")
        >>> fvb = Hint_DELTAK_3.fromvalidatedbytes
        >>> bs = utilities.fromhex("A9 02 00 1F 00 26 02 37 69")
        >>> d = {'deltaBase': 9, 'deltaShift': 3, 'logger': logger}
        >>> print((fvb(bs, **d)))
        test.DELTAK1 - DEBUG - Remaining walker bytes: 9
        DELTAK: Point 31 -1/8@44, 1/4@47; Point 38 -1/8@44, 1/4@47
        
        >>> fvb(bs[:-1], **d)
        test.DELTAK1 - DEBUG - Remaining walker bytes: 8
        test.DELTAK1 - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('DELTAK1')
        else:
            logger = logger.getChild('DELTAK1')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Remaining walker bytes: %d"))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        band = 3  # hardwired for Hint_DELTAK_3
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        op, pointCount = w.unpack("BB")
        
        if op != 0xA9:
            logger.error((
              'V0002',
              (op,),
              "Was expecting opcode 0xA9, but got 0x%02X instead"))
            
            return None
        
        if w.length() < 2 * pointCount:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        points = w.group("H", pointCount)
        
        if w.length() < 1:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        specCount = w.unpack("B")
        
        if w.length() < specCount:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        specs = w.group("B", specCount)
        r = cls()
        DS = hint_deltaspec.DeltaSpec
        
        for spec in specs:
            codedPPEM, codedSteps = divmod(spec, 16)
            ppem = codedPPEM + deltaBase
            uncodedSteps = codedSteps - 8 + (codedSteps >= 8)
            shift = grain * uncodedSteps
            
            for pointIndex in points:
                r.add(DS(ppem, pointIndex, shift))
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new Hint_DELTAK_3 from the specified walker.
        
        The following keyword arguments are supported:
            
            deltaBase       The SDB value; default is 9.
            
            deltaShift      The SDS value; default is 3 (i.e. 2**(-3) pixels).
        
        >>> fb = Hint_DELTAK_3.frombytes
        >>> bs = utilities.fromhex("A9 02 00 1F 00 26 02 37 69")
        >>> d = {'deltaBase': 9, 'deltaShift': 3}
        >>> print((fb(bs, **d)))
        DELTAK: Point 31 -1/8@44, 1/4@47; Point 38 -1/8@44, 1/4@47
        """
        
        band = 3  # hardwired for Hint_DELTAK_3
        deltaBase = kwArgs.get('deltaBase', 9) + (16 * (band - 1))
        deltaShift = kwArgs.get('deltaShift', 3)
        grain = 2 ** (-deltaShift)
        op, pointCount = w.unpack("BB")
        assert op == 0xA9
        points = w.group("H", pointCount)
        specCount = w.unpack("B")
        specs = w.group("B", specCount)
        r = cls()
        DS = hint_deltaspec.DeltaSpec
        
        for spec in specs:
            codedPPEM, codedSteps = divmod(spec, 16)
            ppem = codedPPEM + deltaBase
            uncodedSteps = codedSteps - 8 + (codedSteps >= 8)
            shift = grain * uncodedSteps
            
            for pointIndex in points:
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

