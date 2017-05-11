#
# ttstate.py
#
# Copyright © 2005-2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Classes defining objects which encapsulate TrueType state information.
"""

# System imports
import functools
import sys

# Other imports
from fontio3.hints import distancecolor, graphicsstate, statistics
from fontio3.hints.history import historygroup, historylist
from fontio3.triple import collection, triple
from fontio3.utilities import pp, stamp

# -----------------------------------------------------------------------------

#
# Constants
#

C = collection.Collection
T = triple.Triple
TC = collection.toCollection
HG = historygroup.HistoryGroup

KEYLABEL = 0
KEYINIT = 1
KEYCOMBINE = 2
KEYPPRINT = 3
KEYPPDIFF = 4
KEYDEEPCOPY = 5

any26Dot6 = C([T(None, None, 1)], 64)
anyIntSize = C([T(5, None, 1)])
zero = C([T(0, 1, 1)], 64)

# -----------------------------------------------------------------------------

#
# Private functions
#

def _collectionDecorator(obj):
    try:
        return tuple(obj.tripleIterator())
    except AttributeError:
        return obj

def _filt(d):
    r = {}

    for k, obj in d.items():
        if k[0] != '_':
            r[k] = obj

    return r

def _historyGroupDecorator(obj):
    if isinstance(obj, HG):
        return frozenset(obj)
    else:
        return obj

def _historyML(obj): return isinstance(obj, HG) and (len(obj) > 1)

# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class NoEditor(ValueError): pass
class NoGlyfTable(ValueError): pass
class NoMaxpTable(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class TrueTypeState(object):
    """
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, setAllAttrs=True):
        """
        Initializes the object if setAllAttrs is True.
        
        >>> t = TrueTypeState()
        >>> t.cvt
        {}
        >>> t = TrueTypeState(setAllAttrs=False)
        >>> t.cvt
        Traceback (most recent call last):
          ...
        AttributeError: 'TrueTypeState' object has no attribute 'cvt'
        """
        
        from fontio3.glyf import ttsimpleglyph
        self._fcg = ttsimpleglyph.TTSimpleGlyph.fromcompositeglyph
        
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
    def fromeditor(cls, editor):
        r = cls()
        r._editor = editor
        return r
    
    #
    # Special methods
    #
    
    def __deepcopy__(self, memo=None, **kwArgs):
        excludeKeys = set(kwArgs.get('excludeKeys', set()))
        r = type(self)(setAllAttrs=False)
        r._stamps = self._stamps.copy()  # NOT DEEP
        r._stamper = self._stamper
        excludeKeys.update({'_stamps', '_stamper'})
        d = self.__dict__
        rd = r.__dict__
        kd = self.keyData
        
        for k, obj in d.items():
            if k not in excludeKeys:
                rd[k] = (kd[k][KEYDEEPCOPY](obj) if k in kd else obj)
        
        return r
    
    def __eq__(self, other):
        """
        Returns True if the two TrueTypeState objects are equal. This method
        only compares items whose stamps differ, to gain speed.
        
        >>> t1 = TrueTypeState()
        >>> t2 = t1.__deepcopy__()
        >>> t1 == t2
        True
        >>> t1.assign('ppem', 36)
        >>> t1 == t2
        False
        >>> t1.assign('ppem', 12)
        >>> t1 == t2
        True
        """
        
        if self is other:
            return True
        
        dSelf = self.__dict__
        dOther = other.__dict__
        
        if dSelf['_stamper'] is dOther['_stamper']:
            selfStamps = dSelf['_stamps']
            otherStamps = dOther['_stamps']
            
            for k in dSelf:
                if k[0] != '_':
                    if selfStamps[k] != otherStamps[k]:
                        # Only do actual comparison if stamps differ
                        if dSelf[k] != dOther[k]:
                            return False
            
            return True
        
        return _filt(dSelf) == _filt(dOther)
    
#     def __ne__(self, other):
#         return self is not other and _filt(self.__dict__) != _filt(other.__dict__)
    
    #
    # Private methods
    #
    
    def _editorCheck(self):
        """
        This method is called by any of the run-time public methods, and if an
        editor is not actually present then a ValueError is raised.
        """
        
        e = self.__dict__.get('_editor', None)
        
        if e is None:
            raise NoEditor()
        
        if b'glyf' not in e or e.glyf is None:
            raise NoGlyfTable()
        
        if b'maxp' not in e or e.maxp is None:
            raise NoMaxpTable()
        
        return e
    
    #
    # Public methods
    #
    
    #def asDict(self): return _filt(self.__dict__).copy()
    
    def append(self, key, value):
        """
        Appends the specified value to self.__dict__[key], which must be a list
        or other object that understands the append() call. The stamp will
        always be updated, since the new list will have a different length than
        the original one.
        """
        
        d = self.__dict__
        d[key].append(value)
        d['_stamps'][key] = d['_stamper'].stamp()
    
    def assign(self, key, value):
        """
        Sets the specified value, adjusting stamps if needed.
        """
        
        d = self.__dict__
        
        if d[key] != value:
            d[key] = value
            d['_stamps'][key] = d['_stamper'].stamp()
    
    def assignDeep(self, key1, key2, value):
        """
        Sets the specified value of self.key1.key2, adjusting stamps if needed.
        """
        
        objDeep = self.__dict__[key1]
        dDeep = objDeep.__dict__
        
        if dDeep[key2] != value:
            objDeep.assign(key2, value)
            self._stamps[key1] = self._stamper.stamp()
    
    def changed(self, key):
        """
        This method is called when a client changes one of the attributes; it
        updates the stamp for that attribute.
        """
        
        self._stamps[key] = self._stamper.stamp()
    
    def combine(self, other):
        """
        Combines other into self, paying attention to the stamps (i.e. there
        will be no effect on attributes where the stamps match (and the
        stampers are the same).
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
                
                f, needAssignment = kd[k][KEYCOMBINE]
                
                if f is None:
                    continue
                
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                if needAssignment:
                    dSelf[k] = f(valueSelf, valueOther)
                else:
                    f(valueSelf, valueOther)
                
                selfStamps[k] = dSelf['_stamper'].stamp()
        
        else:
            for k in kd:
                f, needAssignment = kd[k][KEYCOMBINE]
                
                if f is None:
                    continue
                
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                if needAssignment:
                    dSelf[k] = f(valueSelf, valueOther)
                else:
                    f(valueSelf, valueOther)
                
                selfStamps[k] = dSelf['_stamper'].stamp()
    
    def convertFromFUnits(self, n, basis=64, toNumber=True):
        """
        Converts FUnits into scaled values and returns the scaled result. This may be either
        a simple number or a Lattice.
        
        >>> h = TrueTypeState()
        >>> h.convertFromFUnits(500)
        2.921875
        >>> h.convertFromFUnits(500, 16384)
        2.9296875
        >>> h.convertFromFUnits(TC(500), 2)
        2.5
        >>> h.convertFromFUnits(-500)
        -2.9375
        >>> h.convertFromFUnits(-500, 16384)
        -2.9296875
        """
        
        n = TC(n).convertToBasis(basis)
        ps = TC(self.pointSize).convertToBasis(basis)
        
        if None in n or None in ps:
            result = C([T(None, None, 1)], basis)
        else:
            result = (n * self.pointSize * self.resolution) / (72 * self.unitsPerEm)
        
        return result.toNumber() if toNumber else result
    
    def convertToFUnits(self, n, toNumber=True):
        """
        Given a scaled value, convert it to a simple integral number of FUnits.
        
        >>> h = TrueTypeState()
        >>> h.convertToFUnits(2.9296875)
        500
        >>> h.convertToFUnits(-2.9296875)
        -500
        """
        
        n = TC(n).convertToBasis(16384)
        result = ((n * 72 * self.unitsPerEm) / (self.pointSize * self.resolution)).round()
        
        if toNumber and (None not in result) and (len(result) == 1):
            return int(result)
        
        return result
    
    def merged(self, other):
        """
        Returns a new TrueTypeState object representing the merger of both the
        input objects.
        """
        
        r = self.__deepcopy__()
        r.combine(other)
        return r
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object to the specified stream. Note that empty
        simple objects like lists or dicts are not printed.
        
        >>> s = TrueTypeState()
        >>> s.pprint()
        Color distances:
          Black distance: Singles: [0.0]
          Gray distance: Singles: [0.0]
          White distance: Singles: [0.0]
        Graphics state:
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
        Pixels-per-em: 12
        Reference point history:
          0: (no data)
          1: (no data)
          2: (no data)
        Statistics:
          Maxima values:
            Highest CVT index referred to: (no data)
            Highest function number referred to: (no data)
            Byte size of the binary hints: (no data)
            Highest point index in the glyph zone: (no data)
            Highest moved point index in the glyph zone: (no data)
            Deepest stack attained: (no data)
            Highest storage index referred to: (no data)
            Highest point index in the twilight zone: (no data)
        >>> s.cvt[129] = TC(0.75)
        >>> s.pprint(keys=('ppem', 'cvt'))
        Pixels-per-em: 12
        CVT values:
          129: Singles: [0.75]
        """
        
        p = pp.PP(**kwArgs)
        d = self.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.pprintNormalKeys):
            obj = d[k]
            
            if obj:
                if k[0] == '_':
                    p.simple(id(obj), k)
                
                else:
                    t = kd[k]
                    f = t[KEYPPRINT]
                    
                    if f is not None:
                        f(p, obj, label=t[KEYLABEL])
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Pretty-prints the differences from prior to self.
        
        >>> s1 = TrueTypeState()
        >>> s2 = TrueTypeState()
        >>> s2.statistics = s1.statistics  # hack for doctests
        >>> s2.colorDistances.white = TC(64, 64)
        >>> s2.cvt[4] = TC(48, 64)
        >>> s2.graphicsState.loop = 2
        >>> s2.stack.extend([4, 5, 6])
        >>> s2.storage[8] = TC(0, 64)
        >>> s2.pprint_changes(s1)
        Color distances:
          White distance changed from Singles: [0.0] to Singles: [1.0]
        CVT values:
          Added records:
            4: Singles: [0.75]
        Graphics state:
          Loop counter changed from 1 to 2
        Stack:
          Inserted at the start:
            4
            5
            6
        Storage:
          Added records:
            8: Singles: [0.0]
        """
        
        p = pp.PP(**kwArgs)
        dSelf = self.__dict__
        dPrior = prior.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.sortedKeys):
            if k[0] != '_':
                selfValue = dSelf[k]
                priorValue = dPrior[k]
                t = kd[k]
                f, extras = t[KEYPPDIFF]
                
                if f is not None and selfValue != priorValue:
                    f(p, selfValue, priorValue, label=t[KEYLABEL], **extras)
    
    def runGlyphSetup(self, glyphIndex):
        """
        Prepares for running a single glyph's hints.
        
        Returns a pair: (hints, state), where hints is a Hints-class objects
        containing the glyph's hints, and state is the TrueTypeState object
        with the 'prep' results already factored in.
        """
        
        e = self._editorCheck()
        g = e.glyf
        d = dOrig = g[glyphIndex]
        
        if not d:
            return ('', None)
        
        if not d.hintBytes:
            return ('', None)
        
        runState = self._postPrepRun.__deepcopy__(excludeKeys=self._limitedCaseExcludedKeys)
        kd = self.keyData
        rd = runState.__dict__
        
        if d.isComposite:
            d = self._fcg(d, editor=e)
        
        rd['_numPoints'] = {0: e.maxp.maxTwilightPoints, 1: d.pointCount()}
        rd['_numContours'] = {0: 0, 1: len(d.contours)}
        rd['_inPreProgram'] = False
        
        for k in self._limitedCaseExcludedKeys:
            rd[k] = kd[k][KEYINIT]()
        
        s = "Glyph %d hints" % (glyphIndex,)
        return (hints_tt.Hints.frombytes(dOrig.hintBytes, infoString=s), runState)
    
    def runPreProgram(self, **kwArgs):
        e = self._editorCheck()
        c = self.cvt
        c.clear()
        
        if e.reallyHas(b'cvt '):
            for i, n in enumerate(e[b'cvt ']):
                c[i] = (C([T(None, None, 1)], 64) if n else C([T(0, 1, 1)], 64))
        
        self.pointSize = C([T(5, None, 1)])
        self.ppem = C([T(5, None, 1)])
        failed = False
        
        if b'prep' in e:
            d = self.__dict__
            d['_numPoints'] = {0: e.maxp.maxTwilightPoints, 1: 0}
            d['_numContours'] = {0: 0, 1: 0}
            d['_inPreProgram'] = True
            self._validationFailed = False
            e.prep.run(self, **kwArgs)
            failed = self._validationFailed
        
        self._postPrepRun = self.__deepcopy__()
        self._postPrepRun._validationFailed = failed
        gs = self._postPrepRun.graphicsState
        gs.zonePointer0 = gs.zonePointer1 = gs.zonePointer2 = 1
        gs.referencePoint0 = gs.referencePoint1 = gs.referencePoint2 = 0
        gs.dualVector = graphicsstate.xAxis
        gs.freedomVector = graphicsstate.xAxis
        gs.projectionVector = graphicsstate.xAxis
    
    #
    # Dispatch table
    #
    
    # keyData is a dict of tuples, each of which has the following items:
    #   [0]  label
    #   [1]  initial item creation function
    #   [2]  item combination function and a Boolean indicating whether merge
    #        is needed instead of combine for the item
    #   [3]  item pprint function or None
    #   [4]  item pprint-changes function or None, and extras keyword dict
    #   [5]  item deep copy function
    
    f = functools.partial
    idem = lambda x: x
    
    keyData = {
        'colorDistances': (
            "Color distances",
            distancecolor.DistanceColor,
            (distancecolor.DistanceColor.combine, False),
            pp.PP.deep,
            (pp.PP.diff_deep, {}),
            distancecolor.DistanceColor.__deepcopy__),
        
        'cvt': (
            "CVT values",
            dict,
            (collection.combineDicts, False),
            pp.PP.mapping,
            (pp.PP.diff_mapping, {}),
            dict),
        
        'graphicsState': (
            "Graphics state",
            graphicsstate.GraphicsState,
            (graphicsstate.GraphicsState.combine, False),
            pp.PP.deep,
            (pp.PP.diff_deep, {}),
            graphicsstate.GraphicsState.__deepcopy__),
        
        'inhibitHints': (
            "Inhibit hints",
            lambda: False,
            (collection.cluster, True),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem),
        
        'nextAnnotation': (
            "Next jump annotation",
            lambda: [0],
            (None, None),
            None,
            (None, {}),
            idem),
        
#         'originalPoints': (
#             "Original points",
#             list,
#             (None, None),  # xxx eventually these will be real functions
#             pp.PP.simple,
#             (pp.PP.diff_sequence, ???),
#             idem),
        
        'pc': (
            "Program Counter",
            lambda: 0,
            (None, None),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem),
        
        'pointSize': (
            "Pointsize",
            lambda: 12,
            (None, None),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem),
        
        'ppem': (
            "Pixels-per-em",
            lambda: 12,
            (None, None),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem),
        
        'pushHistory': (
            "Push history",
            historylist.HistoryList,
            (historylist.HistoryList.combine, False),
            f(pp.PP.sequence_deep_tag_smart, isMultilineFunc=_historyML),
            (pp.PP.diff_sequence_deep, {'decorator': _historyGroupDecorator}),
            historylist.HistoryList.__deepcopy__),
        
        'refPtHistory': (
            "Reference point history",
            lambda: {0: None, 1: None, 2: None},
            (historygroup.combineDicts, False),
            f(pp.PP.mapping_deep_smart, isMultilineFunc=_historyML),
            (pp.PP.diff_mapping_deep, {}),
            dict),
        
        'resolution': (
            "Resolution",
            lambda: 72,
            (None, None),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem),
        
        'stack': (
            "Stack",
            list,
            (collection.combineLists, False),
            pp.PP.sequence_tag,
            (pp.PP.diff_sequence, {'decorator': _collectionDecorator}),
            list),
        
        'statistics': (
            "Statistics",
            statistics.Statistics,
            (statistics.Statistics.combine, False),
            pp.PP.deep,
            (pp.PP.diff_deep, {}),
            statistics.Statistics.__deepcopy__),
        
        'storage': (
            "Storage",
            dict,
            (collection.combineDicts, False),
            pp.PP.mapping,
            (pp.PP.diff_mapping, {}),
            dict),
        
        'storageHistory': (
            "Storage history",
            dict,
            (historygroup.combineDicts, False),
            f(pp.PP.mapping_deep_smart, isMultilineFunc=_historyML),
            (pp.PP.diff_mapping_deep, {}),
            dict),
        
        'unitsPerEm': (
            "Units-per-em",
            lambda: 2048,
            (None, None),
            pp.PP.simple,
            (pp.PP.diff, {}),
            idem)
        
#         'zones': (
#             "Zones",
#             lambda: [[], []],
#             (None, None),  # eventually this will be a real function
#             pp.PP.sequence,
#             (pp.PP.diff_sequence, ???),  # may need to add "sequence of sequence" support to pp
#             idem)
        
        }
    
    del f, idem
    sortedKeys = sorted(keyData.keys())
    
    pprintNormalKeys = (
      'colorDistances',
      'cvt',
      'graphicsState',
      'ppem',
      'pushHistory',
      'refPtHistory',
      'stack',
      'statistics',
      'storage',
      'storageHistory')
    
    _limitedCaseExcludedKeys = set([
      'pc',
      'pushHistory',
      'refPtHistory',
      'stack',
      'statistics',
      'storageHistory'])

# -----------------------------------------------------------------------------

#
# Deferred imports and other debugging support code
#

if 0:
    def __________________(): pass

from fontio3.hints import hints_tt

if __debug__:
    # Other imports
    from fontio3.hints.history import push
    
    class _Fake(object):
        def __init__(self, s): self.infoString = s
        
    def _makeFakeHintObj(infoString, fakeID=99):
        return (fakeID, _Fake(infoString))
    
    def _makeFakeHistoryEntry_push(infoString, PC, extra):
        return push.HistoryEntry_push(_makeFakeHintObj(infoString), PC, extra)

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
