#
# statistics.py
#
# Copyright © 2007-2014 Monotype Imaging Inc. All Rights Reserved.
#

"""
Objects gathering statistics and histories of TrueType hint activity.
"""

# System imports
import collections
import functools
import re
import sys

# Other imports
from fontio3.hints import maxima
from fontio3.hints.history import historygroup
from fontio3.triple import collection
from fontio3.utilities import pp, stamp

# -----------------------------------------------------------------------------

#
# Constants
#

TC = collection.toCollection
HG = historygroup.HistoryGroup.fromargs
DD = collections.defaultdict

KEYLABEL = 0
KEYINIT = 1
KEYADD = 2
KEYCOMBINE = 3
KEYPPRINT = 4
KEYPPDIFF = 5
KEYDEEPCOPY = 6

# -----------------------------------------------------------------------------

#
# Private functions
#

def _combine(dSelf, dOther):
    """
    Given two dicts mapping some keys to HistoryGroup objects, combine dOther
    into dSelf by either copying the HistoryGroup (if the key is not in dSelf),
    or by combining the HistoryGroup objects via a call to their combine()
    method.
    
    >>> vHG = [HG(_makeFakeHistoryEntry_push("Fred", 19, i)) for i in range(4, 8)]
    >>> d1 = {10: vHG[0], 14: vHG[1]}
    >>> d2 = {14: vHG[2], 16: vHG[3]}
    >>> _combine(d1, d2)
    >>> pp.PP().mapping_deep_smart(d1, lambda x: len(x) > 1)
    10: Extra index 4 in PUSH opcode index 19 in Fred
    14:
      Extra index 5 in PUSH opcode index 19 in Fred
      Extra index 6 in PUSH opcode index 19 in Fred
    16: Extra index 7 in PUSH opcode index 19 in Fred
    """
    
    for key, grp in dOther.items():
        if key in dSelf:
            dSelf[key].combine(grp)
        else:
            dSelf[key] = grp

def _combineSets(dSelf, dOther):
    """
    """

    for k, otherSet in dOther.items():
        if k in dSelf:
            dSelf[k] |= otherSet
        else:
            dSelf[k] = otherSet

def _deepCopySingleDict(d):
    r = {}

    for k, g in d.items():
        r[k] = g.__deepcopy__()

    return r

def _effectNotes_combine(s, o):
    for k in ('cvt', 'function', 'jump', 'storage'):
        _combineSets(s[k], o[k])

def _effectNotes_deepcopy(d):
    r = _effectNotes_init()
    _effectNotes_combine(r, d)
    return r

def _effectNotes_init():
    return dict(cvt=DD(set), function=DD(set), jump=DD(set), storage=DD(set))

def _multiline(obj): return len(obj) > 1

def _pprint_pointlike(p, d, label):
    dGlyph = dict((t[1], d[t]) for t in d.keys() if t[0] == 1)
    dTZ = dict((t[1], d[t]) for t in d.keys() if t[0] == 0)
    
    if dGlyph:
        s = "%s (glyph zone)" % (label,)
        p.mapping_deep_smart(dGlyph, isMultilineFunc=_multiline, label=s)
    
    if dTZ:
        s = "%s (twilight zone)" % (label,)
        p.mapping_deep_smart(dTZ, isMultilineFunc=_multiline, label=s)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Statistics(object):
    """
    Statistics objects are collections of HistoryEntry objects representing how
    values came to be on the TrueType stack. They also include information on
    extrema for various font measures via a Maxima object.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, setAllAttrs=True):
        """
        Statistics objects are always initialized empty.
        
        >>> s = Statistics()
        >>> s.aa
        {}
        >>> s = Statistics(setAllAttrs=False)
        >>> s.aa
        Traceback (most recent call last):
          ...
        AttributeError: 'Statistics' object has no attribute 'aa'
        """
        
        if setAllAttrs:
            d = self.__dict__
            kd = self.keyData
            self._stamps = dict.fromkeys(kd, -1)
            self._stamper = stamp.Stamper()
            
            for key, t in kd.items():
                d[key] = t[KEYINIT]()
    
    #
    # Special methods
    #
    
    def __copy__(self):
        r = type(self)(setAllAttrs=False)
        r.__dict__ = self.__dict__.copy()
        r._stamps = self._stamps.copy()
        return r
    
    def __deepcopy__(self, memo=None):
        r = Statistics(setAllAttrs=False)
        d = self.__dict__
        rd = r.__dict__
        
        for k, t in self.keyData.items():
            rd[k] = t[KEYDEEPCOPY](d[k])
        
        rd['_stamper'] = d['_stamper']
        rd['_stamps'] = d['_stamps'].copy()
        return r
    
    def __eq__(self, other):
        """
        Returns True if the two Statistics objects are equal. This method
        only compares items whose stamps differ, to gain speed.
        
        >>> t1 = Statistics()
        >>> t2 = t1.__deepcopy__()
        >>> t1 == t2
        True
        >>> t1.assign('debug', {'x': 1})
        >>> t1 == t2
        False
        >>> t1.assign('debug', {})
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
        
        return dSelf == dOther
    
    #
    # Private functions
    #
    
    def _addHistory_contour(self, indexObj, history):
        d = self.contour
        
        try:
            for zoneIndex in TC(indexObj[0]):
                for contourIndex in TC(indexObj[1]):
                    t = (zoneIndex, contourIndex)
                    
                    if t in d:
                        d[t].combine(history)
                    else:
                        d[t] = HG(history)
            
            self._stamps['contour'] = self._stamper.stamp()
        
        except ValueError:
            raise ValueError(
              "Open-ended collection passed to _addHistory_contour!")
    
    def _addHistory_generic1(self, indexObj, history, key, doMaxima=False):
        """
        This handles aa, cvt, debug, function, storage, and zone.
        """
        
        d = self.__dict__[key]
        tcIndexObj = TC(indexObj)
        
        try:
            for n in tcIndexObj:
                if n in d:
                    d[n].combine(history)
                else:
                    d[n] = HG(history)
            
            self._stamps[key] = self._stamper.stamp()
        
        except ValueError:
            raise ValueError(
              "Open-ended collection passed to _addHistory_generic1!")
        
        if doMaxima:
            m = self.maxima.__dict__
            newMax = tcIndexObj.max()
            
            if newMax > m[key]:
                m[key] = newMax
                self._stamps['maxima'] = self._stamper.stamp()
    
    def _addHistory_generic2(self, indexObj, history, key, **kwArgs):
        """
        This handles point and refPt.
        """
        
        d = self.__dict__[key]
        v = [-1, -1]
        
        try:
            for zoneIndex in TC(indexObj[0]):
                assert 0 <= zoneIndex < 2
                
                tc = TC(indexObj[1])
                
                if None in tc:
                    tc = set([-1])
                
                for pointIndex in tc:
                    t = (zoneIndex, pointIndex)
                    
                    if t in d:
                        d[t].combine(history)
                    else:
                        d[t] = HG(history)
                
                v[zoneIndex] = pointIndex
            
            self._stamps[key] = self._stamper.stamp()
        
        except ValueError:
            raise ValueError(
              "Open-ended collection passed to _addHistory_generic2!")
        
        m = self.maxima
        newMaxTZPoint = max(m.tzPoint, v[0])
        newMaxPoint = max(m.point, v[1])
        needStamp = newMaxTZPoint != m.tzPoint or newMaxPoint != m.point
        
        m.tzPoint = newMaxTZPoint
        m.point = newMaxPoint
        
        if kwArgs.get('moved', False):
            newMaxPointMoved = max(m.pointMoved, v[1])
            needStamp = needStamp or (newMaxPointMoved != m.pointMoved)
            m.pointMoved = newMaxPointMoved
        
        if needStamp:
            self._stamps['maxima'] = self._stamper.stamp()
    
    def _addHistory_jump(self, indexObj, history):
        """
        This handles jump histories, where the indexObj is actually a triple of
        (infoString, pc, relStack).
        """
        
        d = self.jump
        
        if indexObj in d:
            d[indexObj].combine(history)
        else:
            d[indexObj] = HG(history)
        
        self._stamps['jump'] = self._stamper.stamp()
    
    #
    # Public functions
    #
    
    def addHistory(self, kind, indexObj, history):
        """
        Adds the specified history to the indexObj position(s) for the
        specified kind. Also makes the appropriate updates to the maxima.
        
        >>> s = Statistics()
        >>> he = _makeFakeHistoryEntry_push("Fred", 2, 14)
        >>> s.addHistory('aa', 253, he)
        >>> s.addHistory('contour', (1, 4), he)
        >>> s.addHistory('cvt', 215, he)
        >>> s.addHistory('debug', 12, he)
        >>> s.addHistory('function', 82, he)
        >>> s.addHistory('point', (1, 15), he)
        >>> s.addHistory('refPt', (0, 19), he)
        >>> s.addHistory('storage', 18, he)
        >>> s.addHistory('zone', 1, he)
        >>> s.maxima.asList()
        [215, 82, -1, 15, -1, -1, 18, 19]
        """
        
        if kind == 'pointMoved':
            kind = 'point'
            d = {'moved': True}
        
        else:
            d = {}
        
        t = self.keyData[kind]
        f = t[KEYADD]
        
        if f is not None:
            # note that stamp adjustment happens in this call
            f(self, indexObj, history, **d)
    
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
    
    def combine(self, other, **kwArgs):
        """
        Combines other into self. All keys are combined, unless a 'keys'
        iterable is included in the keyword arguments, in which case only the
        specified keys will be combined.
        """
        
        dSelf = self.__dict__
        dOther = other.__dict__
        selfStamps = dSelf['_stamps']
        selfStamper = dSelf['_stamper']
        st = selfStamper.stamp
        kd = self.keyData
        wantKeys = kwArgs.pop('keys', set(kd))
        
        if selfStamper is dOther['_stamper']:
            otherStamps = dOther['_stamps']
            
            for k in wantKeys:
                if selfStamps[k] == otherStamps[k]:
                    continue
                
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                kd[k][KEYCOMBINE](dSelf[k], dOther[k])
                selfStamps[k] = st()
        
        else:
            for k in wantKeys:
                valueSelf = dSelf[k]
                valueOther = dOther[k]
                
                if valueSelf is valueOther or valueSelf == valueOther:
                    continue
                
                kd[k][KEYCOMBINE](dSelf[k], dOther[k])
                selfStamps[k] = st()
    
    def directIndirect(self):
        """
        Returns two sets, both of which comprise (objectID, kind, optional
        qualifier, pc, extra) tuples referring to PUSH opcodes for cvts or
        storage indices. The first set has entries for those values used
        directly (i.e. without any further operations having been done on them)
        in cvt or storage operations. The second set has entries for those
        values used indirectly (i.e. they are operated on arithmetically or
        otherwise before being used to refer to a cvt or storage location).

        If a tuple is common to both sets, the associated value CANNOT be
        modified directly in the originating PUSH, but rather has to be
        "tweaked" just before the opcode that uses it.
        """
        
        def hintIDList(leaf):
            hintObj = leaf.hintsObj[1]
            s = hintObj.infoString
            
            if s == "Prep table":
                return (id(hintObj), "Prep", leaf.hintsPC, leaf.extraIndex)
            if s.startswith("FDEF "):
                return (id(hintObj), "FDEF", int(s[5:]), leaf.hintsPC, leaf.extraIndex)
            if s.startswith("Glyph "):
                return (id(hintObj), "Glyph", int(s[:-6][6:]), leaf.hintsPC, leaf.extraIndex)
            raise ValueError()
        
        sDirect, sIndirect = set(), set()
        
        for it in [iter(self.cvt.values()), iter(self.storage.values())]:
            for group in it:
                for entry in group:
                    if entry.kind == 'push':
                        # direct reference to a cvt or storage index in the hint object
                        sDirect.add(hintIDList(entry))
                    
                    elif entry.kind == 'op':
                        # indirect reference to a cvt or storage index in the hint object
                        for leaf in entry.leafIterator():
                            sIndirect.add(hintIDList(leaf))
        
        return sDirect, sIndirect
    
    def effects(self):
        """
        Determines the effects of all the entries in the cvt, storage and
        function statistics and returns three dicts (prep, glyph, and fdef).
        """
        
        dPrep = {}
        dGlyph = {}
        dFunc = {}
        
        for sourceKey in ('cvt', 'function', 'storage'):
            sourceDict = self.__dict__[sourceKey]
            
            for sourceIndex, sourceGroup in sourceDict.items():
                for entry in sourceGroup:
                    s = entry.hintsObj[1].infoString
                    
                    if s == "Prep table":
                        d, pgfIndex = dPrep, None
                    elif s.startswith("FDEF "):
                        d, pgfIndex = dFunc, int(s[5:])
                    elif s.startswith("Glyph "):
                        d, pgfIndex = dGlyph, int(s[:-6][6:])
                    else:
                        raise ValueError("Unknown hint! %s" % (s,))
                    
                    if pgfIndex is not None:
                        d = d.setdefault(pgfIndex, {})
                    
                    v = d.setdefault(sourceKey, {}).setdefault(sourceIndex, [[], set()])
                    
                    if entry.kind == 'push':
                        v[0].append((entry.hintsPC, entry.extraIndex))
                    elif entry.kind == 'op':
                        v[1].add(entry.hintsPC)
                    else:
                        raise ValueError("Unexpected history entry kind!")
        
        return dPrep, dGlyph, dFunc
    
    def merged(self, other):
        r = self.__deepcopy__()
        r.combine(other)
        return r
    
    def noteEffect(self, kind, value, infoString, pc, relStackIndex):
        """
        """
        
        try:
            s = set(value)
        except TypeError:
            s = set([value])
        
        self.effectNotes[kind][(infoString, pc, relStackIndex)].update(s)
        self._stamps['effectNotes'] = self._stamper.stamp()
    
    def noteGSEffect(self, infoTuple, pc):
        """
        Note the specified pc in the executing hint made a change to the
        graphics state. The specific code is identified thus: if the infoTuple
        is empty, it is the originating code; otherwise, the infoTuple is a
        call chain of FDEFs, where the [-1] entry is the currently executing
        one.
        """
        
        t = (infoTuple, pc)
        
        if t not in self.gsEffectNotes:
            self.gsEffectNotes.add((infoTuple, pc))
            self._stamps['gsEffectNotes'] = self._stamper.stamp()
    
    def pprint(self, **kwArgs):
        """
        Pretty-prints the object to the specified stream. Three keyword
        arguments are used:
        
            indent      How many spaces to indent on left (default 0)
            keys        Which keys to report (default all)
            stream      Stream to receive output (default sys.stdout)
        
        >>> s = Statistics()
        >>> he = _makeFakeHistoryEntry_push("fake hint object", 2, 14)
        >>> s.addHistory('aa', 253, he)
        >>> s.addHistory('contour', (1, 4), he)
        >>> s.addHistory('cvt', 215, he)
        >>> s.addHistory('debug', 12, he)
        >>> s.addHistory('function', 82, he)
        >>> s.addHistory('point', (1, 15), he)
        >>> s.addHistory('refPt', (0, 19), he)
        >>> s.addHistory('storage', 18, he)
        >>> s.addHistory('zone', 1, he)
        >>> s.pprint()
        Maxima values:
          Highest CVT index referred to: 215
          Highest function number referred to: 82
          Byte size of the binary hints: (no data)
          Highest point index in the glyph zone: 15
          Highest moved point index in the glyph zone: (no data)
          Deepest stack attained: (no data)
          Highest storage index referred to: 18
          Highest point index in the twilight zone: 19
        History for AA opcodes:
          253: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for SHC contours (glyph zone):
          4: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for CVT values:
          215: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for DEBUG opcodes:
          12: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for function calls:
          82: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for outline points (glyph zone):
          15: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for reference points (twilight zone):
          19: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for storage locations:
          18: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for SHZ zones:
          1: Extra index 14 in PUSH opcode index 2 in fake hint object
        >>> s.pprint(keys=('function', 'aa'))
        History for function calls:
          82: Extra index 14 in PUSH opcode index 2 in fake hint object
        History for AA opcodes:
          253: Extra index 14 in PUSH opcode index 2 in fake hint object
        """
        
        p = pp.PP(**kwArgs)
        d = self.__dict__
        kd = self.keyData
        
        for k in kwArgs.get('keys', self.printOrderKeys):
            value = d[k]
            
            if value:
                t = kd[k]
                t[KEYPPRINT](p, value, label=t[KEYLABEL])
    
    def pprint_changes(self, prior, **kwArgs):
        """
        Prints nothing if the two objects are equal. Otherwise prints a label
        (if specified) and what changed. Keyword arguments used are:
        
            indent          How many spaces to indent on left (default 0)
            indentDelta     Extra spaces per new indent (default 2)
            keys            Which keys to report (default all)
            label           Header label (no default)
            stream          Stream to receive output (default sys.stdout)
        
        >>> s = Statistics()
        >>> he = _makeFakeHistoryEntry_push("fake hint object", 2, 14)
        >>> s.addHistory('storage', 18, he)
        >>> s.pprint_changes(Statistics(), label="Summary of changes")
        Summary of changes:
          Maxima values (changes):
            Highest storage index referred to changed from (no data) to 18
          History for storage locations (changes):
            Added records:
              18:
                Extra index 14 in PUSH opcode index 2 in fake hint object
        """
        
        poKeys = kwArgs.pop('keys', self.printOrderKeys)
        p = pp.PP(**kwArgs)
        dSelf = self.__dict__
        dPrior = prior.__dict__
        kd = self.keyData
        
        for k in poKeys:
            t = kd[k]
            selfValue = dSelf[k]
            priorValue = dPrior[k]
            
            if selfValue != priorValue:
                s = "%s (changes)" % (t[KEYLABEL],)
                t[KEYPPDIFF](p, selfValue, priorValue, label=s)
    
    def stackCheck(self, stack):
        """
        Does a maxima check on the stack length.
        
        >>> s = Statistics()
        >>> s.maxima.stack
        -1
        >>> s.stackCheck(list(range(10)))
        >>> s.maxima.stack
        10
        """
        
        m = self.maxima
        newMax = max(m.stack, len(stack))
        
        if newMax != m.stack:
            m.stack = max(m.stack, len(stack))
            self._stamps['maxima'] = self._stamper.stamp()
    
    #
    # Dispatch table
    #
    
    # keyData is a dict of tuples, each of which has the following items:
    #   [0]  label
    #   [1]  initial item creation function (no args)
    #   [2]  item addHistory function (three args)
    #   [3]  item combine function (two args)
    #   [4]  item pprint function (one arg plus std. pprint three args)
    #   [5]  item pprint_changes function (two args plus std. pprint three args)
    #   [6]  item deep copy function
    
    f = functools.partial
    
    keyData = {
      'aa': (
        "History for AA opcodes",
        dict,
        f(_addHistory_generic1, key='aa'),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'contour': (
        "History for SHC contours",
        dict,
        _addHistory_contour,
        _combine,
        _pprint_pointlike,
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'cvt': (
        "History for CVT values",
        dict,
        f(_addHistory_generic1, key='cvt', doMaxima=True),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'debug': (
        "History for DEBUG opcodes",
        dict,
        f(_addHistory_generic1, key='debug'),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'effectNotes': (
        "Effects on CVT, Storage and Functions",
        _effectNotes_init,
        None,
        _effectNotes_combine,
        pp.PP.generic,
        lambda *a,**k: None,
        _effectNotes_deepcopy),
      
      'function': (
        "History for function calls",
        dict,
        f(_addHistory_generic1, key='function', doMaxima=True),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
        
      'gsEffectNotes': (
        "Effects on the graphics state",
        set,
        None,
        set.update,
        pp.PP.generic,
        lambda *a, **k: None,
        set),
      
      'jump': (
        "History for jump opcodes",
        dict,
        _addHistory_jump,
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'maxima': (
        "Maxima values",
        maxima.Maxima,
        None,
        maxima.Maxima.combine,
        pp.PP.deep,
        pp.PP.diff_deep,
        maxima.Maxima.__deepcopy__),
      
      'point': (
        "History for outline points",
        dict,
        f(_addHistory_generic2, key='point'),
        _combine,
        _pprint_pointlike,
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'refPt': (
        "History for reference points",
        dict,
        f(_addHistory_generic2, key='refPt'),
        _combine,
        _pprint_pointlike,
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'storage': (
        "History for storage locations",
        dict,
        f(_addHistory_generic1, key='storage', doMaxima=True),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict),
      
      'zone': (
        "History for SHZ zones",
        dict,
        f(_addHistory_generic1, key='zone'),
        _combine,
        f(pp.PP.mapping_deep_smart, isMultilineFunc=_multiline),
        pp.PP.diff_mapping_deep,
        _deepCopySingleDict)}
    
    del f
    printOrderKeys = ['maxima'] + sorted(set(keyData) - set(['effectNotes', 'maxima']))

# -----------------------------------------------------------------------------

#
# Debugging support code
#

if 0:
    def __________________(): pass

if __debug__:
    # Sibling imports
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

def _test_main():
    """
    Run integrated tests for the whole module.
    
    >>> s1 = Statistics()
    >>> he = _makeFakeHistoryEntry_push("fake hint object", 2, 14)
    >>> s1.addHistory('aa', 253, he)
    >>> s2 = s1.__copy__()
    >>> s1 == s2, s1 is s2
    (True, False)
    >>> s1.aa is s2.aa
    True
    >>> s2 = s1.__deepcopy__()
    >>> s1 == s2, s1 is s2
    (True, False)
    >>> s1.aa is s2.aa
    False
    >>> s1.aa[253] is s2.aa[253]
    False
    """
    
    pass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
        _test_main()

