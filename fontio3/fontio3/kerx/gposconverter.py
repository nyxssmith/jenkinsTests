#
# gposconverter.py
#
# Copyright © 2013-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for converting OpenType GPOS Lookups into their 'kerx' equivalents.
"""

# System imports
import collections
import itertools
import operator

# Other imports
from fontio3 import utilities
from fontio3.GPOS import effect

from fontio3.kerx import (
  classtable,
  coordentry,
  coverage,
  entry,
  entry4,
  format0,
  format1,
  format2,
  format4,
  glyphpair,
  staterow,
  valuetuple)

from fontio3.statetables import namestash

# -----------------------------------------------------------------------------

#
# Functions
#

def analyze(glyphTuples, effectTuples, **kwArgs):
    """
    """
    # This code needs to be pretty massively rewritten, given the changes to
    # the GPOS Effect() object. So for now I'm raising a NotImplementedError()
    # if this entry-point is called.
    
    raise NotImplementedError("Functionality needs to be updated; bug Dave!")
    
    rv = []
    e = kwArgs.pop('editor', None)
    
    if e is None:
        return None
    
    if 'namer' in kwArgs:
        nm = kwArgs.pop('namer', None)
    else:
        nm = e.getNamer()
    
    nmbf = (str if nm is None else nm.bestNameForGlyphIndex)
    horiz = kwArgs.pop('lineIsHorizontal', True)
    hmtxObj = e.get(b'hmtx')
    
    for kind, gv, ev in subdivide(glyphTuples, effectTuples, **kwArgs):
        if kind == 'kern-x':
            agf = operator.attrgetter('xShift')
            
            if horiz:
                rv.extend(analyze_kern_with(gv, ev, agf, False))
            else:
                rv.extend(analyze_kern_cross(gv, ev, agf, True))
        
        elif kind == 'kern-y':
            agf = operator.attrgetter('yShift')
            
            if horiz:
                rv.extend(analyze_kern_cross(gv, ev, agf, False))
            else:
                rv.extend(analyze_kern_with(gv, ev, agf, True))
        
        elif kind == 'shift-x':
            agf = operator.attrgetter('xShift')
            
            if horiz:
                rv.extend(analyze_shift_with(gv, ev, nmbf, agf))
            else:
                rv.extend(analyze_shift_cross(gv, ev, nmbf, agf))
        
        elif kind == 'shift-y':
            agf = operator.attrgetter('yShift')
            
            if horiz:
                rv.extend(analyze_shift_cross(gv, ev, nmbf, agf))
            else:
                rv.extend(analyze_shift_with(gv, ev, nmbf, agf))
        
        elif kind == 'attach' or kind == 'attachDelta':
            rv.extend(analyze_attach(gv, ev, nmbf, hmtxObj))
        
        else:
            raise ValueError("Unknown kind!")
    
    return rv

def analyze_attach(glyphTuples, effectTuples, nmbf, hmtxObj):
    """
    """
    
    ct = analyze_attach_makeClasses(glyphTuples, effectTuples, nmbf, hmtxObj)
    r = format4.Format4({}, classTable=ct, coverage=coverage.Coverage())
    Entry = entry4.Entry
    SR = staterow.StateRow
    r['Start of text'] = SR()
    
    for gt, et in zip(glyphTuples, effectTuples):
        if len(gt) > 2:
            vGT, vET = [], []
            
            for g, e in zip(gt, et):
                if g is None:
                    if e:
                        raise ValueError("Bad mark-to-ligature data!")
                
                else:
                    vGT.append(g)
                    vET.append(e)
            
            gt = tuple(vGT)
            et = tuple(vET)
        
        gBase, gMark = gt
        eBase, eMark = et
        baseRow = r['Start of text']
        baseClass = ct[gBase]
        secondState = "Saw %s" % (nmbf(gBase),)
        
        if baseClass not in baseRow:
            baseRow[baseClass] = Entry(mark=True, newState=secondState)
        
        if secondState not in r:
            r[secondState] = SR()
        
        markRow = r[secondState]
        markClass = ct[gMark]
        
        if markClass not in markRow:
            aw = hmtxObj[gBase].advance
            bx = aw + eMark.xAttach
            by = eMark.yAttach
            action = coordentry.CoordEntry(bx, by, 0, 0)
            markRow[markClass] = Entry(action=action, newState='Start of text')
    
    r.normalize()
    return [r]

def analyze_attach_makeClasses(glyphTuples, effectTuples, nmbf, hmtxObj):
    """
    Creates and returns the ClassTable for the specified glyphs and effects.
    
    ### ed = _fakeEditor()
    ### E = effect.Effect
    ### nmbf = (lambda n: "class %d" % (n,))
    ### e0 = E()
    ### e1 = E(xAttach=-34)
    ### e2 = E(xAttach=-74)
    ### gt = ((20, 10),)
    ### et = ((e0, e1),)
    ### analyze_attach_makeClasses(gt, et, nmbf, ed.hmtx).pprint()
    10: class 10
    20: class 20
    
    ### gt = ((20, 10), (20, 11))
    ### et = ((e0, e1), (e0, e1))
    ### analyze_attach_makeClasses(gt, et, nmbf, ed.hmtx).pprint()
    10: mark group class 10
    11: mark group class 10
    20: class 20
    
    ### gt = ((20, 10), (20, 11))
    ### et = ((e0, e1), (e0, e2))
    ### analyze_attach_makeClasses(gt, et, nmbf, ed.hmtx).pprint()
    10: class 10
    11: class 11
    20: class 20
    
    ### gt = ((20, 10), (21, 11))
    ### et = ((e0, e1), (e0, e2))
    ### analyze_attach_makeClasses(gt, et, nmbf, ed.hmtx).pprint()
    10: mark group class 10
    11: mark group class 10
    20: base group class 20
    21: base group class 20
    """
    
    # The coordObjPool is a dict mapping the base glyph's (x, y) to a
    # corresponding CoordEntry. Note that the attaching glyph's coordinates
    # will always be (0, 0) in this model!
    
    coordObjPool = {}
    
    # The commonEffects variable is a dict mapping a base glyph's (x, y) to a
    # set of mark glyph indices that use that particular effect.
    #
    # The baseCollection variable is a dict mapping base glyph indices to a set
    # of (x, y) values. Two base glyphs can be combined into the same class
    # only if their sets are equal.
    
    commonEffects = collections.defaultdict(set)
    baseCollection = collections.defaultdict(set)
    CE = coordentry.CoordEntry
    allBases, allMarks = set(), set()
    
    for gt, et in zip(glyphTuples, effectTuples):
        if len(gt) > 2:
            vGT, vET = [], []
            
            for g, e in zip(gt, et):
                if g is None:
                    if e:
                        raise ValueError("Bad mark-to-ligature data!")
                
                else:
                    vGT.append(g)
                    vET.append(e)
            
            gt = tuple(vGT)
            et = tuple(vET)
        
        gBase, gMark = gt
        eBase, eMark = et
        assert (not eBase)
        aw = hmtxObj[gBase].advance
        t = (aw + eMark.xAttach, eMark.yAttach)
        baseCollection[gBase].add(t)
        
        if t not in coordObjPool:
            co = CE(t[0], t[1], 0, 0)
            coordObjPool[t] = co
        
        co = coordObjPool[t]
        commonEffects[t].add(gMark)
        allBases.add(gBase)
        allMarks.add(gMark)
    
    # The inWhich variable is a dict mapping glyphs to sets of all the keys in
    # commonEffects in whose corresponding sets the glyph appears.
    
    inWhich = collections.defaultdict(set)
    
    for k, s in commonEffects.items():
        for g in s:
            inWhich[g].add(k)
    
    # The inWhichRev variable is a dict with the inverse map of inWhich: that
    # is to say, mapping frozenset versions of inWhich's values to sets of
    # glyphs that share those values.
    
    inWhichRev = collections.defaultdict(set)
    
    for g, keySet in inWhich.items():
        inWhichRev[frozenset(keySet)].add(g)
    
    ct = classtable.ClassTable()
    
    for glyphSet in inWhichRev.values():
        # Remove any baseforms (probably won't be any)
        glyphSet -= allBases
        
        if not glyphSet:
            continue
        
        avatar = nmbf(min(glyphSet))
        
        if len(glyphSet) == 1:
            groupName = avatar
        else:
            groupName = "mark group %s" % (avatar,)
        
        for glyph in glyphSet:
            ct[glyph] = groupName
    
    # Now combine (where possible) bases, using the baseCollection dict created
    # above in the main walker loop.
    
    bcRev = collections.defaultdict(set)
    
    for g, xyGroup in baseCollection.items():
        bcRev[frozenset(xyGroup)].add(g)
    
    for xyGroup, glyphSet in bcRev.items():
        if len(xyGroup) > 1 or len(glyphSet) < 2:
            continue
        
        avatar = nmbf(min(glyphSet))
        groupName = "base group %s" % (avatar,)
        
        for glyph in glyphSet:
            ct[glyph] = groupName
    
    # Finally, any glyphs not yet in the class table at this point are just
    # given a class to themselves.
    
    leftToDo = (allBases | allMarks) - set(ct)
    
    for glyph in leftToDo:
        ct[glyph] = nmbf(glyph)
    
    return ct

def analyze_kern_cross(glyphTuples, effectTuples, agf, vert):
    """
    """
    
    r = format0.Format0()
    
    for tG, tE in zip(glyphTuples, effectTuples):
        key = glyphpair.GlyphPair(abs(n) for n in tG)
        r[key] = agf(tE[1])
    
    rSize = len(r.binaryString())
    f2 = format2.Format2.fromformat0(r)
    
    if len(f2.binaryString()) < rSize:
        r = f2
    
    r.coverage = coverage.Coverage(crossStream=True, vertical=vert)
    return [r]

def analyze_kern_with(glyphTuples, effectTuples, agf, vert):
    """
    """
    
    r = format0.Format0()
    
    for tG, tE in zip(glyphTuples, effectTuples):
        key = glyphpair.GlyphPair(abs(n) for n in tG)
        r[key] = agf(tE[1])
    
    rSize = len(r.binaryString())
    f2 = format2.Format2.fromformat0(r)
    
    if len(f2.binaryString()) < rSize:
        r = f2
    
    r.coverage = coverage.Coverage(crossStream=False, vertical=vert)
    return [r]

def analyze_shift_cross(glyphTuples, effectTuples, nmbf, agf):
    """
    Do non-kerning generic cross-stream shifts.
    
    ### E = effect.Effect
    ### e0 = E()
    ### e1 = E(yShift=250)
    ### e2 = E(yShift=120)
    ### gt = ((2, 4, 6, 8),)
    ### et = ((e0, e1, e2, e0),)
    ### r = analyze_shift_cross(gt, et, str, operator.attrgetter('yShift'))
    ### len(r)
    1
    ### r[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '2':
        Go to state 'Saw 2'
    State 'Start of line':
      Class '2':
        Go to state 'Saw 2'
    State 'Saw 2':
      Class 'Deleted glyph':
        Go to state 'Saw 2'
      Class '2':
        Go to state 'Saw 2'
      Class '4':
        Push this glyph, then go to state 'Saw 2_4'
    State 'Saw 2_4':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4'
      Class '2':
        Go to state 'Saw 2'
      Class '6':
        Push this glyph, then go to state 'Saw 2_4_6'
    State 'Saw 2_4_6':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4_6'
      Class '2':
        Go to state 'Saw 2'
      Class '8':
        Reset kerning, then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: -130
          Pop #2: 250
    Class table:
      2: 2
      4: 4
      6: 6
      8: 8
    Header information:
      Horizontal
      Cross-stream
      No variation kerning
    """
    
    ct = analyze_shift_makeClasses(glyphTuples, effectTuples, nmbf)
    
    r = format1.Format1(
      {},
      classTable = ct,
      coverage = coverage.Coverage(crossStream=True))
    
    SR = staterow.StateRow
    Entry = entry.Entry
    specialShifts = set()
    
    for tG, tE in zip(glyphTuples, effectTuples):
        currState = 'Start of text'
        vtv = []
        runningShift = 0
        
        for i, (g, e) in enumerate(zip(tG, tE)):
            currClass = ct[g]
            
            if i == len(tG) - 1:
                nextState = 'Start of text'
            elif i:
                nextState = '%s_%s' % (currState, currClass)
            else:
                nextState = 'Saw %s' % (currClass,)
            
            if currState not in r:
                r[currState] = SR()
            
            thisRow = r[currState]
            d = {'newState': nextState}
            
            if currClass not in thisRow:
                if not e:
                    if runningShift:
                        d['reset'] = True
                        runningShift = 0
                
                else:
                    delta = agf(e) - runningShift
                    
                    if delta:
                        vtv.append(delta)
                        runningShift = agf(e)
                        d['push'] = True
            
            if i == len(tG) - 1:
                d['values'] = valuetuple.ValueTuple(reversed(vtv))
            
            thisRow[currClass] = Entry(**d)
            currState = nextState
    
    r.normalize()
    return [r]

def analyze_shift_with(glyphTuples, effectTuples, nmbf, agf):
    """
    Do non-kerning generic with-stream shifts.
    
    ### E = effect.Effect
    ### e0 = E()
    ### e1 = E(xShift=-40)
    ### e2 = E(xShift=25)
    ### gt = ((2, 4, 6, 8),)
    ### et = ((e0, e1, e0, e2),)
    ### r = analyze_shift_with(gt, et, str, operator.attrgetter('xShift'))
    ### len(r)
    1
    ### r[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '2':
        Go to state 'Saw 2'
    State 'Start of line':
      Class '2':
        Go to state 'Saw 2'
    State 'Saw 2':
      Class 'Deleted glyph':
        Go to state 'Saw 2'
      Class '2':
        Go to state 'Saw 2'
      Class '4':
        Push this glyph, then go to state 'Saw 2_4'
    State 'Saw 2_4':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4'
      Class '2':
        Go to state 'Saw 2'
      Class '6':
        Go to state 'Saw 2_4_6'
    State 'Saw 2_4_6':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4_6'
      Class '2':
        Go to state 'Saw 2'
      Class '8':
        Push this glyph, then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
          Pop #2: -40
    Class table:
      2: 2
      4: 4
      6: 6
      8: 8
    Header information:
      Horizontal
      With-stream
      No variation kerning
    
    ### gt = ((2, 4, 6, 8, None),)
    ### et = ((e0, e0, e1, e0, e2),)
    ### r = analyze_shift_with(gt, et, str, operator.attrgetter('xShift'))
    ### len(r)
    1
    ### r[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '2':
        Go to state 'Saw 2'
    State 'Start of line':
      Class '2':
        Go to state 'Saw 2'
    State 'Saw 2':
      Class 'Deleted glyph':
        Go to state 'Saw 2'
      Class '2':
        Go to state 'Saw 2'
      Class '4':
        Go to state 'Saw 2_4'
    State 'Saw 2_4':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4'
      Class '2':
        Go to state 'Saw 2'
      Class '6':
        Push this glyph, then go to state 'Saw 2_4_6'
    State 'Saw 2_4_6':
      Class 'Deleted glyph':
        Go to state 'Saw 2_4_6'
      Class '2':
        Go to state 'Saw 2'
      Class '8':
        Go to state 'Shift 25'
    State 'Shift 25':
      Class 'Out of bounds':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
      Class 'Deleted glyph':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
      Class '2':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
      Class '4':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
      Class '6':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
      Class '8':
        Push this glyph (without advancing), then go to state 'Start of text' after applying these kerning shifts to the popped glyphs:
          Pop #1: 25
    Class table:
      2: 2
      4: 4
      6: 6
      8: 8
    Header information:
      Horizontal
      With-stream
      No variation kerning
    """
    
    ct = analyze_shift_makeClasses(glyphTuples, effectTuples, nmbf)
    
    r = format1.Format1(
      {},
      classTable = ct,
      coverage = coverage.Coverage())
    
    SR = staterow.StateRow
    Entry = entry.Entry
    specialShifts = set()
    
    for tG, tE in zip(glyphTuples, effectTuples):
        currState = 'Start of text'
        vtv = []
        isSpecial = 0
        
        if tG[-1] is None:
            tG = tG[:-1]
            
            if agf(tE[-1]):
                isSpecial = agf(tE[-1])
                specialShifts.add(isSpecial)
            
            tE = tE[:-1]
        
        for i, (g, e) in enumerate(zip(tG, tE)):
            currClass = ct[g]
            
            if i == len(tG) - 1:
                if isSpecial:
                    nextState = "Shift %d" % (isSpecial,)
                else:
                    nextState = 'Start of text'
            
            elif i:
                nextState = '%s_%s' % (currState, currClass)
            
            else:
                nextState = 'Saw %s' % (currClass,)
            
            if currState not in r:
                r[currState] = SR()
            
            thisRow = r[currState]
            
            if currClass not in thisRow:
                if not e:
                    thisRow[currClass] = Entry(newState=nextState)
                
                elif i < len(tG) - 1:
                    thisRow[currClass] = Entry(
                      newState = nextState,
                      push = True)
                    
                    vtv.append(agf(e))
                
                else:
                    thisRow[currClass] = Entry(
                      push = True,
                      values = valuetuple.ValueTuple(
                        reversed(vtv + [agf(e)])),
                      newState = nextState)
                    
                    break
            
            currState = nextState
    
    # Now add the special shifts (if any)
    
    r.normalize()
    allClasses = set(r['Start of text'])
    ignore = {'End of text', 'End of line'}
    
    for specialShift in sorted(specialShifts):
        cell = Entry(
          push = True,
          newState = 'Start of text',
          noAdvance = True,
          values = valuetuple.ValueTuple([specialShift]))
        
        currState = "Shift %d" % (specialShift,)
        r[currState] = SR()
        
        for c in allClasses:
            r[currState][c] = (Entry() if c in ignore else cell)
    
    return [r]

def analyze_shift_makeClasses(glyphTuples, effectTuples, nmbf):
    """
    Creates a ClassTable based on an analysis of the specified glyphs and
    effects.
    
    ### E = effect.Effect
    ### e0 = E()
    ### e1 = E(xShift=-40)
    ### e2 = E(xShift=25)
    ### gt = ((15, 39), (28, 50), (56, 84))
    ### et = ((e0, e1), (e0, e2), (e0, e1))
    ### analyze_shift_makeClasses(gt, et, str).pprint()
    15: 15
    28: 28
    39: like 39
    50: 50
    56: 56
    84: like 39
    """
    
    ct = classtable.ClassTable()
    d = collections.defaultdict(set)
    
    for tG, tE in zip(glyphTuples, effectTuples):
        for g, e in zip(tG, tE):
            if e:
                d[g].add((e.xShift, e.yShift))
            elif g not in ct:
                ct[g] = nmbf(g)
    
    d = {g: frozenset(s) for g, s in d.items()}
    dInv = utilities.invertDictFull(d, asSets=True)
    
    for eGroup, gSet in dInv.items():
        gv = sorted(gSet - {None})
        
        if not gv:
            continue
        
        if len(gv) == 1:
            ct[gv[0]] = nmbf(gv[0])
        
        else:
            s = "like %s" % (nmbf(gv[0]),)
            
            for g in gv:
                ct[g] = s
    
    return ct

def splitEffects(glyphTuples, effectTuples):
    """
    """
    
    rG, rE = [], []
    
    for tG, tE in zip(glyphTuples, effectTuples):
        kinds = set(eff.kind() for eff in tE) - {'empty'}
        
        if not kinds:
            continue
        
        if 'bad' in kinds:
            raise ValueError("Bad mixed Effect")
        
        for kind in kinds:
            rG.append(tG)
            rE.append(tuple(obj.filteredByKind(kind) for obj in tE))
    
    return rG, rE

def subdivide(glyphTuples, effectTuples, **kwArgs):
    """
    Returns an iterator over (kind, glyphTupleIterator, effectTupleIterator)
    triples.
    """
    
    glyphTuples, effectTuples = splitEffects(glyphTuples, effectTuples)
    dKinds = collections.defaultdict(list)
    
    for i, (tG, tE) in enumerate(zip(glyphTuples, effectTuples)):
        rawKinds = [eff.kind() for eff in tE]
        kinds = set(rawKinds) - {'empty'}
        
        if not kinds:
            continue  # handle Effects with zero shifts gracefully
        
        if 'bad' in kinds:
            raise ValueError("Bad mixed Effect found!")
        
        assert len(kinds) == 1
        
        if 'shift-both' in kinds:
            kinds.discard('shift-both')
            kinds.update({'shift-x', 'shift-y'})
        
        for kind in kinds:
            if kind.startswith('shift'):
                if len(tE) == 2 and (not tE[0]) and (tG[1] is not None):
                    kind = 'kern' + kind[5:]
        
            dKinds[kind].append(i)
    
    for kind in sorted(dKinds):
        indexSet = set(dKinds[kind])
        gv = [tG for i, tG in enumerate(glyphTuples) if i in indexSet]
        ev = [tE for i, tE in enumerate(effectTuples) if i in indexSet]
        yield (kind, gv, ev)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _fakeEditor():
        """
        For purposes of test cases, glyphs 10-19 are marks with zero advance,
        and glyphs 20-39 are bases, with advances equal to 40 times the glyph
        index.
        """
        
        from fontio3 import hmtx
        
        e = utilities.fakeEditor(0x10000)
        h = e.hmtx = hmtx.Hmtx()
        ME = hmtx.MtxEntry
        
        for g in range(10, 20):
            h[g] = ME(0, 50)
        
        for g in range(20, 40):
            h[g] = ME(g * 40, 30)
        
        return e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
