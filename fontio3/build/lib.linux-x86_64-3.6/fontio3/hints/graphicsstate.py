#
# graphicsstate.py
#
# Copyright © 2007-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Objects representing the graphics state used during interpretation of TrueType
hints.
"""

# System imports
import functools
import sys

# Other imports
from fontio3.triple import collection, triple
from fontio3.utilities import pp, stamp

# -----------------------------------------------------------------------------

#
# Constants
#

T = triple.Triple
C = collection.Collection

# zero2Dot14 = C([T(0, 16384, 16384)], 16384)
# one2Dot14 = C([T(16384, 32768, 16384)], 16384)

zero2Dot14 = C([T(0, 1, 1)])
one2Dot14 = C([T(1, 2, 1)])

xAxis = (one2Dot14, zero2Dot14)
yAxis = (zero2Dot14, one2Dot14)

zero26Dot6 = C([T(0, 64, 64)], 64)
quarter26Dot6 = C([T(16, 80, 64)], 64)
half26Dot6 = C([T(32, 96, 64)], 64)
one26Dot6 = C([T(64, 128, 64)], 64)

cvtCutInDefault26Dot6 = C([T(68, 132, 64)], 64)

KEYLABEL = 0
KEYINIT = 1
KEYCOMBINE = 2
KEYDEEPCOPY = 3
KEYASIMMUTABLE = 4

# -----------------------------------------------------------------------------

#
# Private functions
#

def _seqCombine(v1, v2, coerce=False, n=2):
    c = collection.cluster
    return tuple(c(v1[i], v2[i], coerce) for i in range(n))

def _seqCombine_list(v1, v2, coerce=False, n=2):
    c = collection.cluster
    return list(c(v1[i], v2[i], coerce) for i in range(n))

def _seqCombine_special(v1, v2, coerce=False, n=2):
    if v1 != v2:
        c = C([T(None, None, 1)])
        return tuple(c for i in range(n))
    else:
        c = collection.cluster
        return tuple(v1)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class GraphicsState(object):
    """
    Objects representing the graphics state used during interpretation of
    TrueType hints.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, setAllAttrs=True):
        """
        Creates a graphics state with all values at their default initial values.
        
        >>> gs = GraphicsState()
        >>> gs.roundState
        [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
        >>> gs.scanControl
        0
        """
        
        if setAllAttrs:
            d = self.__dict__
            kd = self.keyData
            self._stamps = dict.fromkeys(kd, -1)
            self._stamper = stamp.Stamper()
            
            for key, t in kd.items():
                d[key] = t[KEYINIT]()
    
    #
    # Class methods
    #
    
    @classmethod
    def fromargs(cls, **kwArgs):
        """
        Class method that can be used as an alternative constructor when actual
        values (as opposed to defaults) are needed.
        
        >>> g = GraphicsState.fromargs(loop=19)
        >>> g.loop, g.autoFlip
        (19, True)
        """
        
        r = GraphicsState()
        r.__dict__.update(kwArgs)
        return r
    
    #
    # Special methods
    #
    
#     def __copy__(self):
#         r = GraphicsState(setAllAttrs=False)
#         r.__dict__ = self.__dict__.copy()
#         return r
    
    def __deepcopy__(self, memo=None):
        r = GraphicsState(setAllAttrs=False)
        r._stamps = self._stamps.copy()  # NOT DEEP
        r._stamper = self._stamper
        d = self.__dict__
        rd = r.__dict__
        
        for k, t in self.keyData.items():
            rd[k] = t[KEYDEEPCOPY](d[k])
        
        return r
    
    def __eq__(self, other):
        """
        Returns True if the two GraphicsState objects are equal. This method
        only compares items whose stamps differ, to gain speed.
        
        >>> t1 = GraphicsState()
        >>> t2 = t1.__deepcopy__()
        >>> t1 == t2
        True
        >>> t1.assign('deltaShift', 2)
        >>> t1 == t2
        False
        >>> t1.assign('deltaShift', 3)
        >>> t1 == t2
        True
        """
        
        if self is other:
            return True
        
        dSelf = self.__dict__
        dOther = other.__dict__
        
        if self._stamper is other._stamper:
            selfStamps = self._stamps
            otherStamps = other._stamps
            
            for k in dSelf:
                if k[0] != '_':
                    if selfStamps[k] != otherStamps[k]:
                        # Only do actual comparison if stamps differ
                        if dSelf[k] != dOther[k]:
                            return False
            
            return True
        
        return all(dSelf[k] == dOther[k] for k in self.keyData)
    
#     def __ne__(self, other): return self is not other and self.__dict__ != other.__dict__
    
    #
    # Public methods
    #
    
#     def asDict(self):
#         """
#         Sometimes it's useful to have the contents of a GraphicsState object as
#         a dict. Remember, though, for regular processing the object and
#         attribute approach is much, much faster.
#         
#         >>> g = GraphicsState()
#         >>> d = g.asDict()
#         >>> for key in sorted(d): print(key, d[key])
#         autoFlip True
#         cvtCutIn Singles: [1.0625]
#         deltaBase 9
#         deltaShift 3
#         dualVector (Singles: [1.0], Singles: [0.0])
#         freedomVector (Singles: [1.0], Singles: [0.0])
#         instructControl 0
#         loop 1
#         minimumDistance Singles: [1.0]
#         projectionVector (Singles: [1.0], Singles: [0.0])
#         referencePoint0 0
#         referencePoint1 0
#         referencePoint2 0
#         roundState [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
#         scanControl 0
#         scanType 0
#         singleWidthCutIn Singles: [1.0]
#         singleWidthValue 0
#         zonePointer0 1
#         zonePointer1 1
#         zonePointer2 1
#         """
#         
#         return self.__dict__.copy()
    
    def asImmutable(self):
        """
        Returns an immutable version of the object.
        """
        
        kd = self.keyData
        d = self.__dict__
        v = []
        
        for k in self.sortedKeys:
            t = kd[k]
            v.append((k, t[KEYASIMMUTABLE](d[k])))
        
        return tuple(v)
    
    def assign(self, key, value):
        """
        Sets the specified value, adjusting stamps if needed.
        """
        
        d = self.__dict__
        
        if d[key] != value:
            d[key] = value
            d['_stamps'][key] = d['_stamper'].stamp()
    
    def changed(self, key):
        """
        This method is called when a client changes one of the attributes; it
        updates the stamp for that attribute.
        """
        
        self._stamps[key] = self._stamper.stamp()
    
    def combine(self, other):
        """
        Merges other into self.
        
        >>> g1 = GraphicsState()
        >>> g2 = GraphicsState.fromargs(deltaBase=12, freedomVector=yAxis)
        >>> g1.combine(g2)
        >>> g1.pprint()
        Auto-flip: True
        CVT cut-in: Singles: [1.0625]
        DELTA base: Singles: [9, 12]
        DELTA shift: 3
        Dual projection vector: (Singles: [1], Singles: [0])
        Freedom vector: (Ranges: [(*, *, 1, phase=0)], Ranges: [(*, *, 1, phase=0)])
        Instruction control: 0
        Loop counter: 1
        Minimum distance: Singles: [1.0]
        Projection vector: (Singles: [1], Singles: [0])
        Reference point 0: 0
        Reference point 1: 0
        Reference point 2: 0
        Round state: [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
        Scan control: 0
        Scan type: 0
        Single width cut-in: Singles: [1.0]
        Single width value: 0
        Zone pointer 0: 1
        Zone pointer 1: 1
        Zone pointer 2: 1
        """
        
        dSelf = self.__dict__
        dOther = other.__dict__
        selfStamps = dSelf['_stamps']
        kd = self.keyData
        
        if dSelf['_stamper'] is dOther['_stamper']:
            otherStamps = dOther['_stamps']
            
            for k in kd:
                if selfStamps[k] == otherStamps[k]:
                    continue
                
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                dSelf[k] = kd[k][KEYCOMBINE](valueSelf, valueOther)
                selfStamps[k] = dSelf['_stamper'].stamp()
        
        else:
            for k in kd:
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                dSelf[k] = kd[k][KEYCOMBINE](valueSelf, valueOther)
                selfStamps[k] = dSelf['_stamper'].stamp()
    
    def merged(self, other):
        """
        Returns a new GraphicsState object whose contents are the merger of the
        contents of the two input GraphicsState objects, creating Collections
        where needed.
        
        >>> g1 = GraphicsState()
        >>> g2 = GraphicsState.fromargs(deltaBase=12, freedomVector=yAxis)
        >>> g1.merged(g2).pprint()
        Auto-flip: True
        CVT cut-in: Singles: [1.0625]
        DELTA base: Singles: [9, 12]
        DELTA shift: 3
        Dual projection vector: (Singles: [1], Singles: [0])
        Freedom vector: (Ranges: [(*, *, 1, phase=0)], Ranges: [(*, *, 1, phase=0)])
        Instruction control: 0
        Loop counter: 1
        Minimum distance: Singles: [1.0]
        Projection vector: (Singles: [1], Singles: [0])
        Reference point 0: 0
        Reference point 1: 0
        Reference point 2: 0
        Round state: [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
        Scan control: 0
        Scan type: 0
        Single width cut-in: Singles: [1.0]
        Single width value: 0
        Zone pointer 0: 1
        Zone pointer 1: 1
        Zone pointer 2: 1
        """
        
        r = self.__deepcopy__()
        r.combine(other)
        return r
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object to the specified stream. Two keyword arguments
        are used:
        
            indent      How many spaces to indent on left (default 0)
            keys        Which keys to report (default all)
            stream      Stream to receive output (default sys.stdout)
        
        >>> g = GraphicsState()
        >>> g.pprint()
        Auto-flip: True
        CVT cut-in: Singles: [1.0625]
        DELTA base: 9
        DELTA shift: 3
        Dual projection vector: (Singles: [1], Singles: [0])
        Freedom vector: (Singles: [1], Singles: [0])
        Instruction control: 0
        Loop counter: 1
        Minimum distance: Singles: [1.0]
        Projection vector: (Singles: [1], Singles: [0])
        Reference point 0: 0
        Reference point 1: 0
        Reference point 2: 0
        Round state: [Singles: [1.0], Singles: [0.0], Singles: [0.5]]
        Scan control: 0
        Scan type: 0
        Single width cut-in: Singles: [1.0]
        Single width value: 0
        Zone pointer 0: 1
        Zone pointer 1: 1
        Zone pointer 2: 1
        >>> g.pprint(indent=3, keys=('loop', 'autoFlip'))
           Loop counter: 1
           Auto-flip: True
        """
        
        p = pp.PP(**kwArgs)
        f = p.simple
        d = self.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            if k[0] != '_':
                f(d[k], kd[k][KEYLABEL])
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Prints nothing if the two objects are equal. Otherwise prints a label
        (if specified) and what changed. Keyword arguments used are:
        
            indent          How many spaces to indent on left (default 0)
            indentDelta     Extra spaces per new indent (default 2)
            keys            Which keys to report (default all)
            label           Header label (no default)
            stream          Stream to receive output (default sys.stdout)
        
        >>> gs1 = GraphicsState()
        >>> gs2 = GraphicsState.fromargs(loop=4, freedomVector=yAxis, zonePointer1=0)
        >>> gs2.pprint_changes(gs1)
        Freedom vector changed from (Singles: [1], Singles: [0]) to (Singles: [0], Singles: [1])
        Loop counter changed from 1 to 4
        Zone pointer 1 changed from 1 to 0
        >>> gs2.pprint_changes(gs1, label="Graphics state changes", keys=('loop',))
        Graphics state changes:
          Loop counter changed from 1 to 4
        """
        
        p = pp.PP(**kwArgs)
        f = p.diff
        dSelf = self.__dict__
        dPrior = prior.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            selfValue = dSelf[k]
            priorValue = dPrior[k]
            
            if selfValue != priorValue:
                f(selfValue, priorValue, kd[k][KEYLABEL])
    
    #
    # Dispatch table
    #
    
    # keyData is a dict of tuples, indexed by key:
    #   [0]  label
    #   [1]  item initialization function (no args)
    #   [2]  item combine function (two args)
    #   [3]  item deepcopy function (one arg)
    #   [4]  item asImmutable function (one arg)
    
    f = functools.partial
    c = collection.cluster
    idem = lambda x: x
    asImm = lambda x: collection.toCollection(x).asImmutable()
    
    asImmSeq = (
      lambda x:
      tuple(collection.toCollection(obj).asImmutable() for obj in x))
    
    keyData = {
      'autoFlip': (
        "Auto-flip",
        lambda: True,
        lambda x, y: collection.toCollection([0, 1]),
        idem,
        asImm),
      
      'cvtCutIn': (
        "CVT cut-in",
        lambda: cvtCutInDefault26Dot6,
        f(c, coerceToNumber=False),
        idem,
        asImm),
      
      'deltaBase': (
        "DELTA base",
        lambda: 9,
        c,
        idem,
        asImm),
      
      'deltaShift': (
        "DELTA shift",
        lambda: 3,
        c,
        idem,
        asImm),
      
      'dualVector': (
        "Dual projection vector",
        lambda: xAxis,
        _seqCombine_special,
        idem,
        asImmSeq),
      
      'freedomVector': (
        "Freedom vector",
        lambda: xAxis,
        _seqCombine_special,
        idem,
        asImmSeq),
      
      'instructControl': (
        "Instruction control",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'loop': (
        "Loop counter",
        lambda: 1,
        c,
        idem,
        asImm),
      
      'minimumDistance': (
        "Minimum distance",
        lambda: one26Dot6,
        c,
        idem,
        asImm),
      
      'projectionVector': (
        "Projection vector",
        lambda: xAxis,
        _seqCombine_special,
        idem,
        asImmSeq),
      
      'referencePoint0': (
        "Reference point 0",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'referencePoint1': (
        "Reference point 1",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'referencePoint2': (
        "Reference point 2",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'roundState': (
        "Round state",
        lambda: [one26Dot6, zero26Dot6, half26Dot6],
        f(_seqCombine_list, n=3),
        list,
        asImmSeq),
      
      'scanControl': (
        "Scan control",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'scanType': (
        "Scan type",
        lambda: 0,
        c,
        idem,
        asImm),
      
      'singleWidthCutIn': (
        "Single width cut-in",
        lambda: one26Dot6,
        f(c, coerceToNumber=False),
        idem,
        asImm),
      
      'singleWidthValue': (
        "Single width value",
        lambda: 0,  # 0 is FUnits, not 26.6
        c,
        idem,
        asImm),
      
      'zonePointer0': (
        "Zone pointer 0",
        lambda: 1,
        c,
        idem,
        asImm),
      
      'zonePointer1': (
        "Zone pointer 1",
        lambda: 1,
        c,
        idem,
        asImm),
      
      'zonePointer2': (
        "Zone pointer 2",
        lambda: 1,
        c,
        idem,
        asImm)}
    
    sortedKeys = sorted(keyData)
    del f, c, idem, asImm, asImmSeq
    
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
