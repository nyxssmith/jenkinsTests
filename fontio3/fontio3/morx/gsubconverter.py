#
# gsubconverter.py
#
# Copyright © 2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for converting OpenType GSUB Lookups into their 'morx' equivalents.
"""

# System imports
import collections
import itertools
import logging
import operator

# Other imports
from fontio3.morx import (
  classtable,
  contextual,
  entry_contextual,
  entry_insertion,
  entry_ligature,
  glyphdict,
  glyphtuple,
  glyphtupledict,
  insertion,
  ligature,
  noncontextual,
  staterow_contextual,
  staterow_insertion,
  staterow_ligature)

# -----------------------------------------------------------------------------

#
# Constants (and utility types)
#

GTI = glyphtuple.GlyphTupleInput
GTO = glyphtuple.GlyphTupleOutput

TContext = collections.namedtuple(
  "TContext",
  ['mark', 'noAdv', 'dMark', 'dCurr', 'newState'])

TInsert = collections.namedtuple(
  "TInsert",
  ['mark', 'noAdv', 'glyph', 'inMatch', 'outMatch', 'newState'])

# -----------------------------------------------------------------------------

#
# Private functions
#

def _analyze_contextual_addArray(zAll, nmbf, ct):
    d = {'Start of text': {}}
    
    for tIn, tOut in zAll:
        if tIn == tOut:
            continue
        
        currState = 'Start of text'
        marked = None
        
        for i, gIn in enumerate(tIn):
            className = nmbf(abs(gIn))
            
            ct[abs(gIn)] = className
            dThis = d.setdefault(currState, {})
            
            if i:
                if i < len(tIn) - 1:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Start of text"
            
            else:
                nextState = "Saw_%s" % (className,)
            
            if className in dThis:
                # We've done this before. That's OK, with provisos.
                t = dThis[className]
                assert t.dMark is None
                currState = nextState
                
                if not t.mark:
                    if (i < len(tIn) - 1) and (abs(gIn) != tOut[i]):
                        dThis[className] = TContext(
                          mark = True,
                          noAdv = False,
                          dMark = None,
                          dCurr = None,
                          newState = t.newState)
                        
                        marked = i
                        currState = t.newState
                
                else:
                    assert marked is None
                    marked = i
                
                continue
            
            if i < (len(tIn) - 1):
                mark = abs(gIn) != tOut[i]
                
                if mark:
                    marked = i
                
                dThis[className] = TContext(
                  mark = mark,
                  noAdv = False,
                  dMark = None,
                  dCurr = None,
                  newState = nextState)
                
                currState = nextState
            
            else:
                # we're on the last glyph
                if marked is not None:
                    markChange = ((tIn[marked], tOut[marked]),)
                else:
                    markChange = None
                
                if abs(gIn) != tOut[i]:
                    currChange = ((abs(gIn), tOut[i]),)
                else:
                    currChange = None
                
                dThis[className] = TContext(
                  mark = False,
                  noAdv = (gIn < 0),
                  dMark = markChange,
                  dCurr = currChange,
                  newState = "Start of text")
    
    return d

def _analyze_contextual_complex_addArray(zAll, nmbf, ct):
    d = {'Start of text': {}}
    
    for tIn, tOut in zAll:
        if tIn == tOut:
            continue
        
        currState = 'Start of text'
        
        for i, gIn in enumerate(tIn):
            className = (nmbf(gIn) if i else "%d" % (gIn,))
            ct[gIn] = className
            dThis = d.setdefault(currState, {})
            
            if i:
                if i < len(tIn) - 1:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Start of text"
            
            else:
                nextState = "Saw_%s" % (className,)
            
            dThis[className] = TContext(
              mark = False,
              noAdv = False,
              dMark = None,
              dCurr = ((gIn, tOut[i]),),
              newState = nextState)
            
            currState = nextState
    
    return d

def _analyze_contextual_doTransitions(d, zAll, firstGlyphs, nmbf):
    sortedStates = sorted(set(d) - {'Start of text'})
    allGlyphs = set()
    
    for tIn, tOut in zAll:
        allGlyphs.update(abs(n) for n in tIn)
    
    # Fill out the SOT missing classes.
    
    row = d['Start of text']
    
    for glyph in allGlyphs:
        className = nmbf(glyph)
        
        if className not in row:
            row[className] = TContext(
              mark = False,
              noAdv = False,
              dMark = None,
              dCurr = None,
              newState = "Start of text")
    
    # Fill out the non-SOT missing classes.
    
    for stateName in sortedStates:
        row = d[stateName]
        
        for glyph in allGlyphs:
            className = nmbf(glyph)
            
            if className not in row:
                if glyph in firstGlyphs:
                    
                    # We set mark to True here, out of convenience. To compute
                    # the actual value would be expensive here, and if we set
                    # a mark and not use it later, there's no harm, except to
                    # make the state table slightly less clear.
                    
                    row[className] = TContext(
                      mark = True,
                      noAdv = False,
                      dMark = None,
                      dCurr = None,
                      newState = "Saw_%s" % (className,))
                
                else:
                    row[className] = TContext(
                      mark = False,
                      noAdv = False,
                      dMark = None,
                      dCurr = None,
                      newState = "Start of text")
    
    return sortedStates

def _analyze_contextual_findShared_experimental(d, sortedStates, ct):
    
    # First, consolidate columns. For the purposes of column consolidation, two
    # columns are equal if for each cell in the column: the dMark dicts are
    # equal AND the dCurr states of being present or absent are equal AND all
    # other TContext fields are equal
    
    if 'Start of text' not in sortedStates:
        sortedStates = ('Start of text',) + tuple(sortedStates)
    
    consol = collections.defaultdict(set)
    
    for className in d['Start of text']:
        v = []
        
        for stateName in sortedStates:
            tc = d[stateName][className]
            
            v.append((
              tc.mark,
              tc.noAdv,
              tc.dMark,
              bool(tc.dCurr),
              tc.newState))
        
        consol[tuple(v)].add(className)
    
    for common, group in consol.items():
        if len(group) == 1:
            continue
        
        # the classes in group may be combined
        
        if len(group) == 2:
            newClassName = "%s and %s" % tuple(sorted(group))
        else:
            newClassName = "group with %s" % (next(iter(group)),)
        
        ctNew = {g: (newClassName if c in group else c) for g, c in ct.items()}
        ct.clear()
        ct.update(ctNew)
        
        # Update each state with the new combined row and remove the old
        # separate cells.
        
        for stateName, commonCell in zip(sortedStates, common):
            v = []
            vBoth = []
            
            for className in group:
                dc = d[stateName][className].dCurr
                
                if dc is not None:
                    v.extend(t[0] for t in dc)
                    vBoth.extend(dc)
            
            if len(v) != len(set(v)):
                raise ValueError("Cannot consolidate dCurr same keys!")
            
            tNew = TContext(
              commonCell[0],
              commonCell[1],
              commonCell[2],
              tuple(vBoth) or None,
              commonCell[4])
            
            d[stateName][newClassName] = tNew
            
            for className in group:
                del d[stateName][className]
        
    # Second, consolidate rows. For the purposes of row consolidation, two rows
    # are equal if for each cell in the row: the dCurr dicts are equal AND the
    # dMark states of being present or absent are equal AND all other TContext
    # fields are equal.
    
    consol = collections.defaultdict(set)
    sortedClasses = sorted(d['Start of text'])
    
    for stateName in sortedStates:
        v = []
        
        for className in sortedClasses:
            tc = d[stateName][className]
            
            v.append((
              tc.mark,
              tc.noAdv,
              bool(tc.dMark),
              tc.dCurr,
              tc.newState))
        
        consol[tuple(v)].add(stateName)
    
    nextComboIndex = 1
    
    for group in consol.values():
        if (len(group) == 1) or ('Start of text' in group):
            continue
        
        # the states in group may be combined (ct is unaffected)
        
        avatar = next(iter(group))
        newStateName = "Saw combo group %d" % (nextComboIndex,)
        nextComboIndex += 1
        d[newStateName] = d[avatar].copy()
        
        for className, cell in d[newStateName].items():
            v = []
            
            for stateName in group:
                obj = d[stateName][className]
                
                if obj.dMark is not None:
                    v.extend(obj.dMark)
            
            obj = d[newStateName][className]
            
            d[newStateName][className] = TContext(
              obj.mark,
              obj.noAdv,
              tuple(v) or None,
              obj.dCurr,
              obj.newState)
        
        for stateName in group:
            del d[stateName]
        
        groupSet = set(group)
        
        for stateName, row in d.items():
            for className, cell in row.items():
                if cell.newState in groupSet:
                    row[className] = TContext(
                      cell.mark,
                      cell.noAdv,
                      cell.dMark,
                      cell.dCurr,
                      newStateName)

def _analyze_contextual_fixUpClasses(d, addIgnores):
    nop = TContext(False, False, None, None, 'Start of text')
    
    for stateName in set(d):
        row = d[stateName]
        row['End of text'] = nop
        row['Out of bounds'] = nop
        row['Deleted glyph'] = TContext(False, False, None, None, stateName)
        
        if addIgnores:
            row['(ignore)'] = row['Deleted glyph']
        
        row['End of line'] = nop
    
    d['Start of line'] = d['Start of text']

def _analyze_insertion_addArray_pass1(zAll, nmbf, ct, nextFake):
    d = {'Start of text': {}}
    
    for tIn, tOut in zAll:
        tInAbs = tuple(abs(n) for n in tIn)
        cz = _characterizeInsertion(tInAbs, tOut)
        currState = 'Start of text'
        fence = len(tIn) - 1
        
        if cz is None:
            
            # Neither the beginning nor the end is anchored, so we replace the
            # entire sequence.
            
            for i, g in enumerate(tInAbs):
                if currState not in d:
                    d[currState] = {}
                
                if g not in ct:
                    ct[g] = nmbf(g)
                
                className = ct[g]
                
                if i:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Saw_%s" % (className,)
                
                if i < fence:
                    d[currState][className] = TInsert(
                      mark = (i == 0),
                      noAdv = False,
                      glyph = None,
                      inMatch = None,
                      outMatch = None,
                      newState = nextState)
                    
                    currState = nextState
                
                else:
                    inMatch = (nextFake,) + tInAbs[1:]
                    outMatch = tOut
                    
                    d[currState][className] = TInsert(
                      mark = False,
                      noAdv = (tIn[-1] < 0),
                      glyph = tInAbs[0],
                      inMatch = inMatch,
                      outMatch = outMatch,
                      newState = 'Start of text')
                    
                    nextFake -= 1
        
        elif cz[0]:
            
            # The starts of tIn and tOut are the same, so we only need to
            # operate on the latter parts.
            
            k = cz[1]
            
            for i, g in enumerate(tInAbs):
                if currState not in d:
                    d[currState] = {}
                
                if g not in ct:
                    ct[g] = nmbf(g)
                
                className = ct[g]
                
                if i:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Saw_%s" % (className,)
                
                if i < fence:
                    d[currState][className] = TInsert(
                      mark = (i == k),
                      noAdv = False,
                      glyph = None,
                      inMatch = None,
                      outMatch = None,
                      newState = nextState)
                    
                    currState = nextState
                
                else:
                    inMatch = (nextFake,) + tInAbs[k:]
                    outMatch = tOut[k:]
                    
                    # Note that the following allows mark to be True even if
                    # we're at the last glyph in tIn. The later logic that uses
                    # the output of this function must be aware of this in
                    # order to choose whether to change the current or the
                    # marked glyph here.
                    
                    d[currState][className] = TInsert(
                      mark = (i == k),
                      noAdv = (tIn[-1] < 0),
                      glyph = tInAbs[k],
                      inMatch = inMatch,
                      outMatch = outMatch,
                      newState = 'Start of text')
                    
                    nextFake -= 1
        
        else:
            
            # The ends of tIn and tOut are the same, so we only need to operate
            # on the starting part.
            
            for i, g in enumerate(tInAbs):
                if currState not in d:
                    d[currState] = {}
                
                if g not in ct:
                    ct[g] = nmbf(g)
                
                className = ct[g]
                
                if i:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Saw_%s" % (className,)
                
                if i < fence:
                    d[currState][className] = TInsert(
                      mark = (i == 0),
                      noAdv = False,
                      glyph = None,
                      inMatch = None,
                      outMatch = None,
                      newState = nextState)
                    
                    currState = nextState
                
                else:
                    inMatch = (nextFake,) + tInAbs[0:cz[1]]
                    outMatchLen = len(tOut) - len(tIn) + (cz[1] + 1)
                    outMatch = tOut[0:outMatchLen]
                    
                    d[currState][className] = TInsert(
                      mark = False,
                      noAdv = (tIn[-1] < 0),
                      glyph = tInAbs[0],
                      inMatch = inMatch,
                      outMatch = outMatch,
                      newState = 'Start of text')
                    
                    nextFake -= 1
    
    return d, nextFake

def _analyze_insertion_simple_addarray(zAll, nmbf, ct, fences):
    d = {'Start of text': {}}
    E = entry_insertion.Entry
    
    for (leftFence, rightFence), (tIn, tOut) in zip(fences, zAll):
        currState = 'Start of text'
        toInsert = GTO(tOut[leftFence:rightFence+1])
        
        for i, gIn in enumerate(tIn):
            className = nmbf(abs(gIn))
            
            ct[abs(gIn)] = className
            dThis = d.setdefault(currState, {})
            
            if i:
                if i < len(tIn) - 1:
                    nextState = "%s_%s" % (currState, className)
                else:
                    nextState = "Start of text"
            
            else:
                nextState = "Saw_%s" % (className,)
            
            if i < (len(tIn) - 1):
                dThis[className] = E(
                  mark = (i == (leftFence - 1)),  # insert after this one
                  newState = nextState)
                
                currState = nextState
            
            else:
                # we're on the last glyph
                dThis[className] = E(
                  markedInsertBefore = False,
                  markedInsertGlyphs = toInsert,
                  markedIsKashidaLike = True,
                  newState = "Start of text")
    
    return d

def _analyze_insertion_simple_fixUpClasses(d, hasIgnores):
    stdClasses = {
      'End of text',
      'End of line',
      'Deleted glyph',
      'Out of bounds'}
    
    if hasIgnores:
        stdClasses.add('(ignore)')
    
    stdStates = {'Start of text', 'Start of line'}
    allClasses = set(cn for row in d.values() for cn in row) | stdClasses
    E = entry_insertion.Entry
    dSOT = d['Start of text']
    
    for cn in allClasses:
        if cn not in dSOT:
            dSOT[cn] = E()
    
    d['Start of line'] = dSOT.copy()  # just dict copy
    
    for sn, row in d.items():
        for cn in allClasses:
            if cn in row:
                continue
            
            if cn in {'Deleted glyph', '(ignore)'}:
                row[cn] = E(newState=sn)
                continue
            
            row[cn] = E(noAdvance=True)

def _analyze_ligature_addArray(zAll, firstGlyphs, nmbf):
    d = {'Start of text': {}}
    
    for firstGlyph in firstGlyphs:
        z = [
          (tIn, tOut, continueMatch)
          for tIn, tOut, continueMatch in zAll
          if tIn[0] == firstGlyph]
        
        glyphState = currState = "Saw_%s" % (nmbf(firstGlyph),)
        d['Start of text'][firstGlyph] = (True, None, currState)
        
        for tIn, tOut, continueMatch in z:
            currState = glyphState
            
            for i, g in enumerate(tIn[1:], start=1):
                isLast = i == (len(tIn) - 1)
                
                if currState not in d:
                    d[currState] = {}
                
                nextState = "%s_%s" % (currState, nmbf(g))
                
                if g not in d[currState]:
                    if i < (len(tIn) - 1):
                        d[currState][g] = (
                          True,
                          None,
                          nextState)
                    
                    else:
                        nextState = continueMatch or 'Start of text'
                        inGT = GTI(tIn)
                        vWorkTemp = [None] * len(tIn)
                        vWorkTemp[0] = tOut[0]
                        outGT = GTO(vWorkTemp)
                        
                        d[currState][g] = (
                          True,
                          ((inGT,), (outGT,)),
                          nextState)
                
                elif (not isLast) and (d[currState][g][1] is None):
                    pass
                
                else:
                    raise NotImplementedError()
                
                currState = nextState
    
    return d

def _analyze_ligature_doTransitions(d, zAll, firstGlyphs, nmbf):
    sortedStates = sorted(set(d) - {'Start of text'})
    allGlyphs = set()
    
    for tIn, tOut, continueMatch in zAll:
        allGlyphs.update(tIn)
        
        if continueMatch:
            allGlyphs.update(tOut)
    
    # Fill out the SOT missing classes.
    
    row = d['Start of text']
    
    for glyph in allGlyphs:
        if glyph not in row:
            row[glyph] = (False, None, "Start of text")
    
    # Fill out the non-SOT missing classes.
    
    for stateName in sortedStates:
        row = d[stateName]
        
        for glyph in allGlyphs:
            if glyph not in row:
                if glyph in firstGlyphs:
                    row[glyph] = (True, None, "Saw_%s" % (nmbf(glyph),))
                else:
                    row[glyph] = (False, None, "Start of text")
    
    return sortedStates

def _analyze_ligature_findShared(d, sortedStates):
    dShare = collections.defaultdict(set)
    dSubst = collections.defaultdict(lambda: collections.defaultdict(dict))
    
    for glyph in d['Start of text']:
        v = []
        
        for stateName in sortedStates:
            t = d[stateName][glyph]
            
            if t[1] is not None:
                dSubst[stateName][glyph] = t[1]
                t = (t[0], 'number', t[2])
            
            v.append(t)
        
        dShare[tuple(v)].add(glyph)
    
    for key, glyphSet in dShare.items():
        if len(glyphSet) == 1:
            continue
        
        avatar = min(glyphSet)
        
        for stateName in set(d):  # not just "d" so we can change d
            t = d[stateName][avatar]
            
            if t[1] is not None:
                vIn, vOut = [], []
                
                for g in glyphSet:
                    inPart, outPart = dSubst[stateName][g]
                    vIn.extend(inPart)
                    vOut.extend(outPart)
                
                grouped = tuple([tuple(vIn), tuple(vOut)])
                t = (t[0], grouped, t[2])
            
            d[stateName][frozenset(glyphSet)] = t
            
            for g in glyphSet:
                del d[stateName][g]

def _analyze_ligature_fixUpClasses(d, addIgnores):
    for stateName in set(d):
        row = d[stateName]
        row['End of text'] = (False, None, 'Start of text')
        row['Out of bounds'] = (False, None, 'Start of text')
        row['Deleted glyph'] = (False, None, stateName)  # effectively a NOP
        
        if addIgnores:
            row['(ignore)'] = row['Deleted glyph']
        
        row['End of line'] = (False, None, 'Start of text')
    
    d['Start of line'] = d['Start of text']

def _analyze_ligature_makeCT(d, nmbf, igs):
    ct = classtable.ClassTable()
    
    for obj in d['Start of text']:
        if isinstance(obj, int):
            ct[obj] = nmbf(obj)
        
        else:
            s = "group %s" % (nmbf(min(obj)),)
            
            for g in obj:
                ct[g] = s
    
    for g in igs:
        ct[g] = "(ignore)"
    
    return ct

def _analyze_ligature_processPartials(v, nmbf):
    leftLenSet = {len(x[0]) for x in v}
    minKeyLen = min(leftLenSet)
    maxKeyLen = max(leftLenSet)
    
    if minKeyLen == maxKeyLen:
        return v
    
    for tryLen in range(minKeyLen, maxKeyLen):
        toTry = {
          tIn: tOut[0]
          for tIn, tOut, ignore in v
          if len(tIn) == tryLen}
        
        presentPartials = {
          tIn[:tryLen]
          for tIn, tOut, ignore in v
          if len(tIn) > tryLen}
        
        v2 = []
        
        for tIn, tOut, continueMatch in v:
            if len(tIn) > tryLen and tIn[:tryLen] in toTry:
                tIn = (toTry[tIn[:tryLen]],) + tIn[tryLen:]
            
            elif len(tIn) == tryLen and tIn in presentPartials:
                continueMatch = "Saw_%s" % (nmbf(tOut[0]),)
                
            v2.append((tIn, tOut, continueMatch))
        
        v[:] = v2
    
    return v

def _characterizeInsertion(tIn, tOut):
    """
    Determines where the two tuples match, thus determining the insertion zone.
    Returns a pair whose first element is a Boolean (True if the front matches,
    False if the back matches), and whose second element is the index where the
    non-matching part starts. None is returned if neither end matches.
    
    tOut must be longer than tIn.
    
    ### _characterizeInsertion((1, 2, 3), (1, 2, 7, 8))
    (True, 2)
    
    ### _characterizeInsertion((133, 94), (27, 61, 94))
    (False, 0)
    
    ### _characterizeInsertion((1, 2), (4, 5, 6))
    """
    
    assert len(tOut) > len(tIn)
    trial = 0
    
    while trial < len(tIn):
        if abs(tIn[trial]) != tOut[trial]:
            break
        
        trial += 1
    
    if trial:
        # we have a front-match
        return (True, trial)
    
    trial = -1
    
    while trial >= -len(tIn):
        if abs(tIn[trial]) != tOut[trial]:
            break
        
        trial -= 1
    
    if trial < -1:
        # we have a back-match
        return (False, trial + len(tIn))
    
    # neither end matched (later can add middle tests here)
    
    return None

def _collisionCheck(inTuples, outTuples):
    """
    Returns True if at least one outTuple's ending (one or more glyphs, but not
    the entire outTuple) matches at least one earlier inTuples's beginning
    (again, up to but not including the entire inTuple). Since the tuple groups
    are ordered and state tables are not, this is a clue that the processing
    needs to be handled specially.
    """
    
    ins = set()
    
    for tIn, tOut in zip(inTuples, outTuples):
        outs = _tupleBackPartials(tOut)
        
        if outs & ins:
            return True
        
        ins.update(_tupleFrontPartials(tIn))
    
    return False

def _findKind(inTuples, outTuples):
    """
    Returns a string describing what kind of subtable is needed for the
    specified inTuples.
    """
    
    # If any of the inTuple values are negative, this is chaining contextual.
    
    if any(n < 0 for t in inTuples for n in t):
        if all(t[-1] >= 0 for t in inTuples):
            return 'chaining_backtrackonly'
        
        if all(t[0] >= 0 for t in inTuples):
            return 'chaining_lookaheadonly'
        
        return 'chaining_both'
    
    # If all outTuples are length 1, this is either single, alternate, or lig.
    
    if all(len(t) == 1 for t in outTuples):
        
        # If any inTuple is length >1, this is lig.
        
        if any(len(t) > 1 for t in inTuples):
            
            # If all the inTuples are length 2, we will do this as
            # a contextual subtable (much faster and smaller).
            
            if all(len(t) == 2 for t in inTuples):
                
                return 'contextual_ligature'
            
            return 'ligature'
        
        # If there are repetitions in inTuples, this is alternate.
        
        if len(set(t[0] for t in inTuples)) != len(inTuples):
            return 'alternate'
        
        return 'single'
    
    # At least one outTuple is length >1 if we get here. If all the inTuples
    # are length 1, this is multiple.
    
    if all(len(t) == 1 for t in inTuples):
        return 'multiple'
    
    # If all the inTuples' and outTuples' lengths match, this is contextual.
    
    if all(len(tIn) == len(tOut) for tIn, tOut in zip(inTuples, outTuples)):
        return 'contextual'
    
    # Finally, if we get here it's a composite.
    
    return 'composite'

def _kindSort(inGroup, outGroup):
    """
    Note the "kind" referred to here is returned by _simpleKind, not _findKind.
    Returns a generator over (kind, newInPiece, newOutPiece) triples.
    
    ### ins = ((3, 4), (10, 11), (8, 1), (8, 2), (15, 16))
    ### outs = ((3, 5), (10, 19), (41,), (42,), (91, 16))
    ### for kind, inTuples, outTuples in _kindSort(ins, outs):
    ...   print(kind)
    ...   for tIn, tOut in itertools.izip(inTuples, outTuples):
    ...     print("  ", tIn, "->", tOut)
    context
       (3, 4) -> (3, 5)
       (10, 11) -> (10, 19)
       (15, 16) -> (91, 16)
    ligature
       (8, 1) -> (41,)
       (8, 2) -> (42,)
    """
    
    it = (
      (_simpleKind(tIn, tOut), tIn, tOut)
      for tIn, tOut in zip(inGroup, outGroup))
    
    for k, g in itertools.groupby(sorted(it), key=operator.itemgetter(0)):
        v = list(g)
        yield (k, [x[1] for x in v], [x[2] for x in v])

def _makeIns(d, igs):
    """
    Given a dict mapping trigger glyphs to to-be-inserted sequences, returns an
    Insertion subtable that does this. This is a simple table, with only the
    two fixed states.
    
    ### d = {20: (50, 51), 21: (52, 53, 54, 55)}
    ### _makeIns(d, set()).pprint(onlySignificant=True)
    State 'Start of text':
      Class 'glyph 20':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 50
          1: 51
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 21':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 52
          1: 53
          2: 54
          3: 55
        Current insertion is kashida-like: True
        Name of next state: Start of text
    State 'Start of line':
      Class 'glyph 20':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 50
          1: 51
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 21':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 52
          1: 53
          2: 54
          3: 55
        Current insertion is kashida-like: True
        Name of next state: Start of text
    Class table:
      20: glyph 20
      21: glyph 21
    Mask value: (no data)
    Coverage: (no data)
    """
    
    ct = classtable.ClassTable({g: "glyph %d" % (g,) for g in d})
    ct.update({g: "(ignore)" for g in igs})
    sot = staterow_insertion.StateRow()
    entryNOP = entry_insertion.Entry()
    sot["End of text"] = entryNOP
    sot["Out of bounds"] = entryNOP
    sot["Deleted glyph"] = entryNOP
    sot["End of line"] = entryNOP
    
    if igs:
        sot["(ignore)"] = entryNOP
    
    for g, v in d.items():
        sot["glyph %d" % (g,)] = entry_insertion.Entry(
          currentInsertBefore = False,
          currentInsertGlyphs = GTO(v),
          currentIsKashidaLike = True)
    
    r = insertion.Insertion({}, classTable=ct)
    r["Start of text"] = sot
    r["Start of line"] = sot
    return r

def _reorderTuples(inTuples, outTuples):
    """
    Do an analysis of the tuples, looking for spans which could be reordered
    without order-based ill effects. Returns a generator over new (kind,
    inTuples, outTuples) tuples which have been optimized for use by
    analyze_composite().
    """
    
    changers = {}
    inGroup = []
    outGroup = []
    
    for tIn, tOut in zip(inTuples, outTuples):
        if (tIn[0] in changers) and changers[tIn[0]] != {tIn[0]}:
            for kind, newIns, newOuts in _kindSort(inGroup, outGroup):
                yield (kind, newIns, newOuts)
            
            changers = {}
            inGroup[:] = []
            outGroup[:] = []
        
        for newChanger in set(tIn) - set(tOut):
            changers.setdefault(newChanger, set()).add(tIn[0])
        
        inGroup.append(tIn)
        outGroup.append(tOut)
    
    # dump the final group
    for kind, newIns, newOuts in _kindSort(inGroup, outGroup):
        yield (kind, newIns, newOuts)

def _simpleKind(tIn, tOut):
    if len(tOut) == 1:
        return 'ligature'
    
    if len(tIn) == len(tOut):
        return 'context'
    
    if len(tIn) < len(tOut):
        return 'insert'
    
    return 'special'

def _tupleFrontPartials(t):
    """
    Given a tuple, returns a set of sub-tuples anchored at the start, up to but
    not including the entirety of t. See the doctest for an example.
    
    ### sorted(_tupleFrontPartials((1, 2, 3, 4)), key=len)
    [(1,), (1, 2), (1, 2, 3)]
    """
    
    if len(t) < 2:
        return set()
    
    return set(t[:i] for i in range(1, len(t)))

def _tupleBackPartials(t):
    """
    Given a tuple, returns a set of sub-tuples anchored at the end, up to but
    not including the entirety of t. See the doctest for an example.
    
    ### sorted(_tupleBackPartials((1, 2, 3, 4)), key=len)
    [(4,), (3, 4), (2, 3, 4)]
    """
    
    if len(t) < 2:
        return set()
    
    return set(t[i:] for i in range(1, len(t)))

# -----------------------------------------------------------------------------

#
# Public functions
#

if 0:
    def __________________(): pass

def analyze(inTuples, outTuples, **kwArgs):
    """
    Given a list of input glyph index tuples and the corresponding list of
    output glyph tuples, perform an analysis that breaks out the results into
    the various kinds of AAT subtables. Note that order is important in the
    lists; for example, if the following two rules are present in this order:
    
        a b -> c d
        d e -> f g h
    
    then we need to emulate what OpenType does here. By default:
    
        OpenType:
        
            a b e -> c d e
        
        AAT:
        
            a b e -> c f g h (via a b e -> c d e, then c d e -> c f g h)
    
    This is a result of splitting out the list of effects across multiple AAT
    subtables. a split which is necessary because the AAT contextual effect
    cannot increase the number of glyphs. We can handle this by using some fake
    glyphs, so the AAT tables for these two rules would be:
    
        Table 1: a b -> c %
        Table 2: d e -> f g h
        Table 3: % -> d
    
    So we can get the OpenType effect through the judicious use of fake glyphs.
    """
    
    kind = _findKind(inTuples, outTuples)
    
    if kind == 'contextual_ligature':
        outTuples = tuple(t + (65535,) for t in outTuples)
        kind = 'contextual'
    
    return _dispatch[kind](inTuples, outTuples, **kwArgs)

def analyze_alternate(inTuples, outTuples, **kwArgs):
    """
    Returns a list of Noncontextual objects mapping successive elements of all
    the output lists. These could then be used in an exclusive feature of
    character alternatives, with each Noncontextual in the list working for one
    particular selector value.
    
    ### logger = utilities.makeDoctestLogger("alternate")
    ### v = analyze_alternate(
    ...   ((3,), (3,), (5,)),
    ...   ((25,), (19,), (22,)),
    ...   logger=logger)
    ### len(v)
    2
    ### v[0].pprint()
    3: 19
    5: 22
    Mask value: 00000001
    Coverage:
      Subtable kind: 4
    ### v[1].pprint()
    3: 25
    Mask value: 00000001
    Coverage:
      Subtable kind: 4
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    d = collections.defaultdict(list)
    dCount = collections.defaultdict(int)
    
    for tIn, tOut in zip(inTuples, outTuples):
        if len(tIn) != 1:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s is not length 1, which is incorrect for "
              "calls to analyze_alternate()."))
            
            return None
        
        if len(tOut) != 1:
            logger.error((
              'Vxxxx',
              (tOut,),
              "Output tuple %s is not length 1, which is incorrect for "
              "calls to analyze_alternate()."))
            
            return None
        
        if tIn[0] < 0:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s has a negative value, which should only "
              "occur for chaining."))
            
            return None
        
        if tIn[0] == tOut[0]:
            logger.warning((
              'Vxxxx',
              (tIn[0],),
              "Input glyph %s maps to the same output glyph; this rule may "
              "be omitted with no effect on the output."))
            
            continue
        
        d[tIn[0]].append(tOut[0])
        dCount[tIn[0]] += 1
    
    count = max(dCount.values())
    rv = [noncontextual.Noncontextual() for i in range(count)]
    
    for g, v in d.items():
        for i, n in enumerate(sorted(v)):
            rv[i][g] = n
    
    return rv

def analyze_chaining_backtrackonly(inTuples, outTuples, **kwArgs):
    """
    """
    
    # For cases where only backtrack is used, there is no difference between a
    # chaining and a non-chaining table in the AAT context, so we just convert
    # all the negative values to positive values and then call analyze().
    
    inTuplesNew = tuple(tuple(abs(n) for n in t) for t in inTuples)
    return analyze(inTuplesNew, outTuples, **kwArgs)

def analyze_chaining_both(inTuples, outTuples, **kwArgs):
    """
    """
    
    # If there are negative values at both ends of members of inTuples, we
    # change the backtrack set to positives. Then we pass the modified inTuples
    # to analyze_chaining_lookaheadonly().
    
    changedInTuples = []
    
    for tIn in inTuples:
        v = list(tIn)
        
        for i, n in enumerate(v):
            if n >= 0:
                break
            
            v[i] = abs(n)
        
        changedInTuples.append(tuple(v))
    
    return analyze_chaining_lookaheadonly(
      tuple(changedInTuples),
      outTuples,
      **kwArgs)

def analyze_chaining_lookaheadonly(inTuples, outTuples, **kwArgs):
    """
    ### v = analyze_chaining_lookaheadonly(
    ...   ((3, 4, -5),),
    ...   ((3, 10, 5),))
    ### len(v)
    1
    ### v[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '3':
        Go to state 'Saw_3'
    State 'Start of line':
      Class '3':
        Go to state 'Saw_3'
    State 'Saw_3':
      Class 'Deleted glyph':
        Go to state 'Saw_3'
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
      Class '4':
        Mark this glyph, then go to state 'Saw_3_4'
    State 'Saw_3_4':
      Class 'Deleted glyph':
        Go to state 'Saw_3_4'
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
      Class '5':
        Go to state 'Start of text' (without advancing the glyph pointer) after changing the marked glyph thus:
          4: 10
    Class table:
      3: 3
      4: 4
      5: 5
    Mask value: (no data)
    Coverage: (no data)
    """
    
    # If any rule ends in two or more negative values, this is a complex case.
    # The best we can do in cases like this is to give each rule its own
    # subtable. Yeesh.
    
    if any(len(t) > 2 and t[-1] < 0 and t[-2] < 0 for t in inTuples):
        return analyze_chaining_lookaheadonly_separated(
          inTuples,
          outTuples,
          **kwArgs)
    
    # If we get here, there are at most single lookahead glyphs in all the
    # rules. We handle this more or less like a regular contextual case, with
    # the one major difference of leaving the lookahead glyph with noAdvance
    # set to True, so it can be processed in turn.
    
    tempTuples = tuple(tuple(abs(n) for n in t) for t in inTuples)
    kind = _findKind(tempTuples, outTuples)
    
    if kind == 'contextual_ligature':
        outTuples = tuple(t + (65535,) for t in outTuples)
        kind = 'contextual'
    
    inTuples = tuple(
      tuple(abs(n) for n in t[:-1]) + (t[-1],)
      for t in inTuples)
    
    return _dispatch[kind](inTuples, outTuples, **kwArgs)

def analyze_chaining_lookaheadonly_separated(inTuples, outTuples, **kwArgs):
    raise NotImplementedError()

def analyze_composite(inTuples, outTuples, **kwArgs):
    """
    """
    
    # If there are no collisions, we can separate the effects into groupings
    # based on the comparative lengths of the input and output tuples. However,
    # if there are collisions, we will have to handle this more laboriously.
    
    if _collisionCheck(inTuples, outTuples):
        return analyze_composite_complex(inTuples, outTuples, **kwArgs)
    
    # Now that we know there are no collisions, it's safe to subdivide the
    # input and output tuples. We divide them into four different categories:
    # ligatures (where the outTuple is length 1); contextual (where the in and
    # out tuples are the same length); insertion (where the outTuples are
    # longer than the inTuples); and contextual_removal (where the outTuples
    # are shorter than the inTuples).
    #
    # The first version of this code accumulated each of the separate types,
    # and processed the whole groups at once. This was a mistake, because it
    # did not respect the ordering of the inTuples and outTuples effects, which
    # is critical. This newer version therefore gathers like effects until
    # there's a change of kind, at which point it dumps them out. It may result
    # in more tables being created, but it respects the ordering.
    #
    # Actually, ignore that previous paragraph. I've figured out how to
    # determine whether or not it's safe to combine entries. See the new code
    # in _reorderTuples() to see how this is done.
    
    rv = []
    
    for kind, inPiece, outPiece in _reorderTuples(inTuples, outTuples):
        if kind == 'ligature':
            rv.extend(analyze_ligature(inPiece, outPiece, **kwArgs))
        elif kind == 'context':
            rv.extend(analyze_contextual(inPiece, outPiece, **kwArgs))
        elif kind == 'insert':
            rv.extend(analyze_insertion(inPiece, outPiece, **kwArgs))
        else:
            rv.extend(analyze_special(inPiece, outPiece, **kwArgs))
    
    return rv

def analyze_composite_complex(inTuples, outTuples, **kwArgs):
    raise NotImplementedError()

def analyze_contextual(inTuples, outTuples, **kwArgs):
    """
    ### inTuples = ((5, 6), (5, 10), (9, 6), (9, 10))
    ### outTuples = ((30, 31), (30, 31), (32, 31), (32, 31))
    ### r = analyze_contextual(inTuples, outTuples)
    ### len(r)
    1
    ### r[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '5':
        Mark this glyph, then go to state 'Saw combo group 1'
      Class '9':
        Mark this glyph, then go to state 'Saw combo group 1'
    State 'Start of line':
      Class '5':
        Mark this glyph, then go to state 'Saw combo group 1'
      Class '9':
        Mark this glyph, then go to state 'Saw combo group 1'
    State 'Saw combo group 1':
      Class 'Deleted glyph':
        Go to state 'Saw combo group 1'
      Class '10 and 6':
        Go to state 'Start of text' after changing the marked glyph thus:
          5: 30
          9: 32
        and changing the current glyph thus:
          6: 31
          10: 31
      Class '5':
        Mark this glyph, then go to state 'Saw combo group 1'
      Class '9':
        Mark this glyph, then go to state 'Saw combo group 1'
    Class table:
      5: 5
      6: 10 and 6
      9: 9
      10: 10 and 6
    Mask value: (no data)
    Coverage: (no data)
    """
    
    # Before proceeding, we need to ascertain if this is a complex case (i.e. a
    # case where >2 items change, or where 2 change and neither is the last
    # glyph). If it is complex, we handle it via analyze_contextual_complex.
    
    zAll = list(zip(inTuples, outTuples))
    
    for tIn, tOut in zAll:
        changes = [x != y for x, y in zip(tIn, tOut)]
        count = sum(changes)
        
        if (count > 2) or ((count == 2) and (not changes[-1])):
            return analyze_contextual_complex(inTuples, outTuples, **kwArgs)
    
    # If we get here, this effect can be done via a single normal contextual
    # subtable.
    
    logger = kwArgs.pop('logger', logging.getLogger())
    nm = kwArgs.pop('namer', None)
    
    if nm is not None:
        nmbf = nm.bestNameForGlyphIndex
    else:
        nmbf = str
    
    # Build the initial version of the state array and the class table.
    
    ct = classtable.ClassTable()
    d = _analyze_contextual_addArray(zAll, nmbf, ct)
    igs = kwArgs.get('ignores', set())
    
    for g in igs:
        ct[g] = "(ignore)"
    
    # Fill in the transitions.
    
    firsts = set(t[0][0] for t in zAll)
    sortedStates = _analyze_contextual_doTransitions(d, zAll, firsts, nmbf)
    
    # Find matches and coalesce into shared entries, where possible. The
    # consolidation into groups might cause changes to the class table too.
    
    _analyze_contextual_findShared_experimental(d, sortedStates, ct)
    
    # Add the 4 fixed classes to all states and copy the Start of text state
    # to the Start of line state.
    
    _analyze_contextual_fixUpClasses(d, bool(igs))
    
    # At this point we're ready to convert d into our final state array.
    
    r = contextual.Contextual({}, classTable=ct)
    
    for stateName, row in d.items():
        r[stateName] = entryRow = staterow_contextual.StateRow()
        
        for className, t in row.items():
            if t.dMark is None:
                md = None
            
            else:
                md = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dMark:
                    md[gIn] = gOut
            
            if t.dCurr is None:
                cd = None
            
            else:
                cd = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dCurr:
                    cd[gIn] = gOut
            
            entryRow[className] = entry_contextual.Entry(
              mark = t.mark,
              noAdvance = t.noAdv,
              markSubstitutionDict = md,
              currSubstitutionDict = cd,
              newState = t.newState)
    
    return [r]

def analyze_contextual_complex(inTuples, outTuples, **kwArgs):
    """
    This handles cases where the tuples are the same lengths, but the number of
    elements changing and/or their positions within the tuple preclude the use
    of a single Contextual table. The approach here is two-pass: first we use
    a fake glyph to trigger; and second we do one-by-one replacements, based on
    the fake trigger.
    
    If the alreadyFaked keyword argument is True (as it will be if we came here
    via analyze_special), the first step is omitted; the trigger in this case
    will be the first glyph in tIn.
    
    ### inTuples = ((1, 2, 3),)
    ### outTuples = ((4, 5, 6),)
    ### rv = analyze_contextual_complex(inTuples, outTuples)
    ### len(rv)
    2
    
    ### rv[0].pprint(onlySignificant=True)
    State 'Start of text':
      Class '1':
        Mark this glyph, then go to state 'Saw_1'
    State 'Start of line':
      Class '1':
        Mark this glyph, then go to state 'Saw_1'
    State 'Saw_1':
      Class 'Deleted glyph':
        Go to state 'Saw_1'
      Class '1':
        Mark this glyph, then go to state 'Saw_1'
      Class '2':
        Go to state 'Saw_1_2'
    State 'Saw_1_2':
      Class 'Deleted glyph':
        Go to state 'Saw_1_2'
      Class '1':
        Mark this glyph, then go to state 'Saw_1'
      Class '3':
        Go to state 'Start of text' after changing the marked glyph thus:
          1: 65533
    Class table:
      1: 1
      2: 2
      3: 3
    Mask value: (no data)
    Coverage: (no data)
    
    ### rv[1].pprint(onlySignificant=True)
    State 'Start of text':
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 4
    State 'Start of line':
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 4
    State 'Saw_65533':
      Class 'Deleted glyph':
        Go to state 'Saw_65533'
      Class '2':
        Go to state 'Saw_65533_2' after changing the current glyph thus:
          2: 5
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    State 'Saw_65533_2':
      Class 'Deleted glyph':
        Go to state 'Saw_65533_2'
      Class '3':
        Go to state 'Start of text' after changing the current glyph thus:
          3: 6
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    Class table:
      2: 2
      3: 3
      65533: 65533
    Mask value: (no data)
    Coverage: (no data)
    
    ### inTuples = ((65533, 1428, 1357),)
    ### outTuples = ((1537, 1357, 65535),)
    ### v = analyze_contextual_complex(inTuples, outTuples, alreadyFaked=True)
    ### bs = v[-1].binaryString()
    ### v[-1].pprint(onlySignificant=True)
    State 'Start of text':
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 1537
    State 'Start of line':
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 1537
    State 'Saw_65533':
      Class 'Deleted glyph':
        Go to state 'Saw_65533'
      Class '1428':
        Go to state 'Saw_65533_1428' after changing the current glyph thus:
          1428: 1357
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    State 'Saw_65533_1428':
      Class 'Deleted glyph':
        Go to state 'Saw_65533_1428'
      Class '1357':
        Go to state 'Start of text' after changing the current glyph thus:
          1357: Deleted glyph
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    Class table:
      1357: 1357
      1428: 1428
      65533: 65533
    Mask value: (no data)
    Coverage: (no data)
    """
    
    rv = []
    
    # First pass (elided if already done)
    
    if kwArgs.pop('alreadyFaked', False):
        tempIn = inTuples
    
    else:
        # do the first pass
        nextFake = kwArgs.pop('fakeBase', 0xFFFD)
        v = []
        
        for tIn in inTuples:
            v.append((nextFake,) + tIn[1:])
            nextFake -= 1
        
        tempIn = tuple(v)
        
        rv.extend(
          analyze_contextual(inTuples, tempIn, fakeBase=nextFake, **kwArgs))
    
    # Second pass
    
    zAll = list(zip(tempIn, outTuples))
    ct = classtable.ClassTable()
    nm = kwArgs.pop('namer', None)
    igs = kwArgs.get('ignores', set())
    
    for g in igs:
        ct[g] = "(ignore)"
    
    if nm is not None:
        nmbf = nm.bestNameForGlyphIndex
    else:
        nmbf = str
    
    d = _analyze_contextual_complex_addArray(zAll, nmbf, ct)
    
    # Fill in the transitions.
    
    firsts = set(t[0][0] for t in zAll)
    sortedStates = _analyze_contextual_doTransitions(d, zAll, firsts, nmbf)
    
    # Add the 4 fixed classes to all states and copy the Start of text state
    # to the Start of line state.
    
    _analyze_contextual_fixUpClasses(d, bool(igs))
    
    # At this point we're ready to convert d into our final state array.
    
    r = contextual.Contextual({}, classTable=ct)
    
    for stateName, row in d.items():
        r[stateName] = entryRow = staterow_contextual.StateRow()
        
        for className, t in row.items():
            if t.dMark is None:
                md = None
            
            else:
                md = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dMark:
                    md[gIn] = gOut
            
            if t.dCurr is None:
                cd = None
            
            else:
                cd = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dCurr:
                    cd[gIn] = gOut
            
            entryRow[className] = entry_contextual.Entry(
              mark = t.mark,
              noAdvance = t.noAdv,
              markSubstitutionDict = md,
              currSubstitutionDict = cd,
              newState = t.newState)
    
    rv.append(r)
    return rv

def analyze_insertion(inTuples, outTuples, **kwArgs):
    """
    ### obj, nm = _makeTestInsert()
    ### inTuples, outTuples = obj.effects()
    ### r = analyze(inTuples, outTuples, namer=nm)
    ### obj, nm = _makeTestInsert2()
    ### inTuples, outTuples = obj.effects()
    ### nm.annotate = True
    ### r = analyze(inTuples, outTuples, namer=nm)
    """
    
    rv = analyze_insertion_trysimple(inTuples, outTuples, **kwArgs)
    
    if rv is not None:
        return rv
    
    # If we get here, it's not a pure insertion
    
    logger = kwArgs.pop('logger', logging.getLogger())
    nm = kwArgs.pop('namer', None)
    fakeBase = kwArgs.pop('fakeBase', 0xFFFD)
    
    if nm is not None:
        nmbf = nm.bestNameForGlyphIndex
    else:
        nmbf = str
    
    zAll = list(zip(inTuples, outTuples))
    ct = classtable.ClassTable()
    igs = kwArgs.get('ignores', set())
    
    for g in igs:
        ct[g] = "(ignore)"
    
    d, nextFake = _analyze_insertion_addArray_pass1(zAll, nmbf, ct, fakeBase)
    rv = []
    
    # The dict d we just got back has the necessary information for us to now
    # create three separate subtables: a contextual subtable (to change the
    # glyph to a fake trigger glyph); an insertion subtable (to insert all but
    # the first output glyphs); and a ligature subtable (to change the fake
    # glyph into the first of the output glyphs).
    #
    # First we make the initial contextual subtable.
    
    dCont1 = {}
    
    for stateName, row in d.items():
        if stateName not in dCont1:
            dCont1[stateName] = {}
        
        for className, t in row.items():
            if t.glyph is not None:
                if t.mark:
                    tNew = TContext(
                      mark = False,
                      noAdv = t.noAdv,
                      dMark = None,
                      dCurr = ((t.glyph, t.inMatch[0]),),
                      newState = t.newState)
                
                else:
                    tNew = TContext(
                      mark = False,
                      noAdv = t.noAdv,
                      dMark = ((t.glyph, t.inMatch[0]),),
                      dCurr = None,
                      newState = t.newState)
            
            else:
                tNew = TContext(
                  mark = t[0],
                  noAdv = False,
                  dMark = None,
                  dCurr = None,
                  newState = t.newState)
            
            dCont1[stateName][className] = tNew
    
    sortedStates = _analyze_contextual_doTransitions(
      dCont1,
      zAll,
      set(t[0][0] for t in zAll),
      nmbf)
    
    _analyze_contextual_findShared_experimental(dCont1, sortedStates, ct)
    _analyze_contextual_fixUpClasses(dCont1, bool(igs))
    r = contextual.Contextual({}, classTable=ct)
    
    for stateName, row in dCont1.items():
        r[stateName] = entryRow = staterow_contextual.StateRow()
        
        for className, t in row.items():
            if t.dMark is None:
                md = None
            
            else:
                md = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dMark:
                    md[gIn] = gOut
            
            if t.dCurr is None:
                cd = None
            
            else:
                cd = glyphdict.GlyphDict({})
                
                for gIn, gOut in t.dCurr:
                    cd[gIn] = gOut
            
            entryRow[className] = entry_contextual.Entry(
              mark = t.mark,
              noAdvance = t.noAdv,
              markSubstitutionDict = md,
              currSubstitutionDict = cd,
              newState = t.newState)
    
    rv.append(r)
    
    # Next we make the insertion subtable.
    
    dIns = {}
    
    for row in d.values():
        for t in row.values():
            if (t.glyph is not None) and t.inMatch and t.outMatch:
                dIns[t.inMatch[0]] = t.outMatch[1:]
    
    rv.append(_makeIns(dIns, igs))
    
    # Finally we make the ligature and/or noncontextual subtables.
    
    nct = {}
    ligIn, ligOut = [], []
    
    for row in d.values():
        for t in row.values():
            if (t.glyph is not None) and t.inMatch and t.outMatch:
                if len(t.inMatch) == 1:
                    nct[t.inMatch[0]] = t.outMatch[0]
                else:
                    ligIn.append(t.inMatch)
                    ligOut.append((t.outMatch[0],))
    
    if nct:
        rv.append(noncontextual.Noncontextual(nct))
    
    if ligIn:
        rv.extend(
          analyze_ligature(
            ligIn,
            ligOut,
            logger = logger,
            namer = nm,
            ignores = igs))
    
    return rv

def analyze_insertion_trysimple(inTuples, outTuples, **kwArgs):
    """
    If all the insertions for this set of parameters are purely internal, then
    we can just do a single insertion subtable.
    
    ### inTuples = [(5, 6, 7), (15, 16, 7)]
    ### outTuples = [(5, 6, 21, 22, 7), (15, 16, 21, 22, 7)]
    ### obj = analyze_insertion_trysimple(inTuples, outTuples)
    ### obj is None
    False
    """
    
    zAll = list(zip(inTuples, outTuples))
    fences = []
    
    for tIn, tOut in zAll:
        tryLeft = 0
    
        while tryLeft < len(tIn):
            if abs(tIn[tryLeft]) != tOut[tryLeft]:
                break
        
            tryLeft += 1
    
        tryRight = -1
    
        while tryRight >= -len(tIn):
            if abs(tIn[tryRight]) != tOut[tryRight]:
                break
        
            tryRight -= 1
    
        if not (tryLeft and (tryRight < -1)):
            return None
        
        fences.append((tryLeft, tryRight))
    
    # If we get here, all the insertions are purely internal, so we only need
    # a single insertion subtable to get this effect.
    
    nm = kwArgs.pop('namer', None)
    
    if nm is not None:
        nmbf = nm.bestNameForGlyphIndex
    else:
        nmbf = str
    
    # Build the initial version of the state array and the class table.
    
    ct = classtable.ClassTable()
    d = _analyze_insertion_simple_addarray(zAll, nmbf, ct, fences)
    igs = kwArgs.get('ignores', set())
    
    for g in igs:
        ct[g] = "(ignore)"
    
    _analyze_insertion_simple_fixUpClasses(d, bool(igs))  # changes d in-place
    SR = staterow_insertion.StateRow
    
    r = insertion.Insertion(
      {sn: SR(row) for sn, row in d.items()},
      classTable = ct)
    
    return [r]

def analyze_ligature(inTuples, outTuples, **kwArgs):
    """
    ### inTuples = (
    ...   (160, 39), (164, 50), (166, 50), (170, 34), (170, 35), (170, 50),
    ...   (171, 35), (171, 50), (172, 36), (172, 37), (172, 50), (173, 37),
    ...   (173, 50), (175, 39), (177, 26), (177, 27), (177, 41), (177, 42),
    ...   (177, 47), (177, 48), (177, 49), (177, 50), (177, 56),
    ...   (177, 178, 50), (189, 50), (190, 29), (190, 43), (190, 53),
    ...   (190, 56), (191, 34), (191, 35), (191, 240), (191, 241), (192, 43),
    ...   (193, 49), (193, 50), (532, 29), (532, 43), (532, 53), (532, 56),
    ...   (532, 526))
    ### outTuples = (
    ...   (430,), (431,), (432,), (433,), (434,), (435,), (436,), (437,),
    ...   (439,), (438,), (440,), (441,), (442,), (443,), (446,), (445,),
    ...   (452,), (450,), (447,), (448,), (453,), (454,), (449,), (451,),
    ...   (457,), (458,), (463,), (462,), (460,), (464,), (466,), (465,),
    ...   (467,), (468,), (470,), (471,), (458,), (463,), (462,), (460,),
    ...   (530,))
    ### v = analyze_ligature(inTuples, outTuples)
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    nm = kwArgs.pop('namer', None)
    
    if nm is not None:
        nmbf = nm.bestNameForGlyphIndex
    else:
        nmbf = str
    
    igs = kwArgs.pop('ignores', set())
    
    # Walk the inTuples and outTuples to pre-work any initial ligatures that
    # contribute to other, larger ligatures (like "f + f -> ff" changing the
    # rule "f + f + i -> ffi" into "ff + i -> ffi").
    
    zAll = _analyze_ligature_processPartials([
      (tIn, tOut, False)
      for tIn, tOut in zip(inTuples, outTuples)],
      nmbf)
    
    # Build the working version of the state array, called "d". This is a dict
    # mapping state names to dicts which map glyph indices to triples: (push,
    # None or a GTDPair, new state). A GTDPair is a tuple of two tuples: GTIs
    # and GTOs. We do this as a tuple, instead of a regular GTD, so these
    # triples can be used as dict keys during processing.
    
    firstGlyphs = set(t[0][0] for t in zAll)
    d = _analyze_ligature_addArray(zAll, firstGlyphs, nmbf)
    
    # Now that the working version of the state array is filled out, we need to
    # add in all the cross-class transitions.
    
    sortedStates = _analyze_ligature_doTransitions(d, zAll, firstGlyphs, nmbf)
    
    # Analyze the columns to find glyphs that can share a class. These columns
    # will be the same for non-ligaturing entries, and the same except for the
    # actual ligature for ligaturing entries. To avoid having to do an O(n log
    # n) search, we convert the columns into dict keys and consolidate those.
    
    _analyze_ligature_findShared(d, sortedStates)
    
    # Build the class table.
    
    ct = _analyze_ligature_makeCT(d, nmbf, igs)
    
    # Add the 4 fixed classes to all states and copy the Start of text state
    # to the Start of line state.
    
    _analyze_ligature_fixUpClasses(d, bool(igs))
    
    # At this point we're ready to directly convert d into our final state
    # array.
    
    r = ligature.Ligature({}, classTable=ct)
    
    for stateName, row in d.items():
        r[stateName] = entryRow = staterow_ligature.StateRow()
        
        for trigger, t in row.items():
            if isinstance(trigger, str):
                className = trigger
            elif isinstance(trigger, int):
                className = ct[trigger]
            else:
                className = ct[next(iter(trigger))]
            
            if t[1] is None:
                ad = None
            
            else:
                ad = glyphtupledict.GlyphTupleDict({})
                
                for inGT, outGT in zip(*t[1]):
                    ad[inGT] = outGT
            
            entryRow[className] = entry_ligature.Entry(
              push = t[0],
              actions = ad,
              newState = t[2])
    
    return [r]

def analyze_multiple(inTuples, outTuples, **kwArgs):
    """
    Given inTuples (which must all be length 1 and non-negative) and outTuples,
    returns a list with either one or three elements: if all the outTuples
    start with the same glyph as their corresponding inTuple, then the returned
    list simply comprises a single Insertion subtable. Otherwise it will be a
    Noncontextual, Insertion, Noncontextual group.
    
    It is not technically an error if there are outTuples whose lengths are 1;
    if any of these are present, they are done in a Noncontextual table that
    precedes any other table in the returned list.
    
    It *is* officially illegal to have outTuples whose lengths are zero (i.e.
    the Multiple feature is deleting glyphs). However, we do see some fonts
    that do this, and accommodate this by changing the input glyphs in these
    cases into the deleted glyph. (If this messes up the back-mapping to the
    original character code, well, too bad. Fix the freakin' font.)
    
    ### logger = utilities.makeDoctestLogger("multiple")
    ### v = analyze_multiple(
    ...   ((20,), (30,), (31,)),
    ...   ((20, 91, 92), (40, 41), (42, 43)),
    ...   logger = logger)
    ### len(v)
    3
    ### v[0].pprint()
    30: 65533
    31: 65532
    Mask value: 00000001
    Coverage:
      Subtable kind: 4
    
    ### v[1].pprint(onlySignificant=True)
    State 'Start of text':
      Class 'glyph 20':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 91
          1: 92
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 65532':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 43
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 65533':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 41
        Current insertion is kashida-like: True
        Name of next state: Start of text
    State 'Start of line':
      Class 'glyph 20':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 91
          1: 92
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 65532':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 43
        Current insertion is kashida-like: True
        Name of next state: Start of text
      Class 'glyph 65533':
        Insert glyphs before current: False
        Glyphs to insert at current:
          0: 41
        Current insertion is kashida-like: True
        Name of next state: Start of text
    Class table:
      20: glyph 20
      65532: glyph 65532
      65533: glyph 65533
    Mask value: (no data)
    Coverage: (no data)
    
    ### v[2].pprint()
    65532: 42
    65533: 40
    Mask value: 00000001
    Coverage:
      Subtable kind: 4
    
    ### v = analyze_multiple(((19,),), ((),), logger=logger)
    multiple - WARNING - Input tuple (19,) maps to empty output; this is explicitly prohibited by the OpenType spec.
    ### len(v)
    1
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    z, zSpecial = [], []
    r = []
    
    for tIn, tOut in zip(inTuples, outTuples):
        if len(tIn) != 1:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s is not length 1, which is incorrect for "
              "calls to analyze_multiple()."))
            
            return None
        
        if tIn[0] < 0:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s has a negative value, which should only "
              "occur for chaining."))
            
            return None
        
        if len(tOut) > 1:
            z.append((tIn, tOut))
        
        elif tOut:
            if tIn[0] == tOut[0]:
                logger.warning((
                  'Vxxxx',
                  (tIn[0],),
                  "Input glyph %s maps to the same output glyph; this rule "
                  "may be omitted with no effect on the output."))
            
            else:
                zSpecial.append((tIn, tOut))
        
        else:
            logger.warning((
              'Vxxxx',
              (tIn,),
              "Input tuple %s maps to empty output; this is explicitly "
              "prohibited by the OpenType spec."))
            
            zSpecial.append((tIn, (0xFFFF,)))
    
    if zSpecial:
        obj = analyze_single(
          tuple(t[0] for t in zSpecial),
          tuple(t[1] for t in zSpecial),
          logger = logger,
          **kwArgs)
        
        if obj is not None:
            r.extend(obj)
    
    if not z:
        return r
    
    if all(k[0] == v[0] for k, v in z):
        dIns = {k[0]: v[1:] for k, v in z}
        return [_makeIns(dIns, kwArgs.get('ignores', set()))]
    
    # If we get here there is at least one entry for which the replacement
    # sequence does NOT start with the key. In this case we need to make a
    # fake swash map to create the trigger values, then build the insertion
    # subtable, and finally another fake swash to do the final replacement
    # of the initial glyph.
    #
    # For example, suppose multipleObj maps 'a' to the new sequence 'bcd'. The
    # first fake swash will change 'a' to a fake value 0xFFFD. Then the
    # insertion subtable adds 'cd' to this fake glyph. Finally, a second
    # fake swash will change the 0xFFFD to 'b'.
    
    nextAvail = kwArgs.get('fakeBase', 0xFFFD)
    dIns = {}
    dSwash1 = {}
    dSwash2 = {}
    
    for k, v in z:
        if k[0] == v[0]:
            dIns[k[0]] = v[1:]
        
        else:
            dSwash1[k[0]] = nextAvail
            dIns[nextAvail] = v[1:]
            dSwash2[nextAvail] = v[0]
            nextAvail -= 1
    
    r.extend([
      noncontextual.Noncontextual_allowFakeGlyphs(dSwash1),
      _makeIns(dIns, kwArgs.get('ignores', set())),
      noncontextual.Noncontextual_allowFakeGlyphs(dSwash2)])
    
    return r

def analyze_single(inTuples, outTuples, **kwArgs):
    """
    Given inTuples (which must all be length 1 and non-negative) and outTuples
    (which must all be length 1), returns a list with one element, a
    Noncontextual object.
    
    ### logger = utilities.makeDoctestLogger("single")
    ### v = analyze_single(((35,), (19,)), ((4,), (5,)), logger=logger)
    ### len(v)
    1
    ### v[0].pprint()
    19: 5
    35: 4
    Mask value: 00000001
    Coverage:
      Subtable kind: 4
    
    ### analyze_single((), (), logger=logger)
    single - WARNING - No input or output in call to analyze_single().
    []
    
    ### analyze_single(((9,),), ((9,),), logger=logger)
    single - WARNING - Input glyph 9 maps to the same output glyph; this rule may be omitted with no effect on the output.
    []
    
    ### analyze_single(((-9,),), ((9,),), logger=logger)
    single - ERROR - Input tuple (-9,) has a negative value, which should only occur for chaining.
    
    ### analyze_single(((9, 10),), ((9,),), logger=logger)
    single - ERROR - Input tuple (9, 10) is not length 1, which is incorrect for calls to analyze_single().
    
    ### analyze_single(((9,),), ((9, 10),), logger=logger)
    single - ERROR - Output tuple (9, 10) is not length 1, which is incorrect for calls to analyze_single().
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    z = tuple(zip(inTuples, outTuples))
    alreadyWarned = False
    
    for tIn, tOut in z:
        if len(tIn) != 1:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s is not length 1, which is incorrect for "
              "calls to analyze_single()."))
            
            return None
        
        if len(tOut) != 1:
            logger.error((
              'Vxxxx',
              (tOut,),
              "Output tuple %s is not length 1, which is incorrect for "
              "calls to analyze_single()."))
            
            return None
        
        if tIn[0] < 0:
            logger.error((
              'Vxxxx',
              (tIn,),
              "Input tuple %s has a negative value, which should only "
              "occur for chaining."))
            
            return None
        
        if tIn[0] == tOut[0]:
            logger.warning((
              'Vxxxx',
              (tIn[0],),
              "Input glyph %s maps to the same output glyph; this rule may "
              "be omitted with no effect on the output."))
            
            alreadyWarned = True
    
    d = {tIn[0]: tOut[0] for tIn, tOut in z if tIn != tOut}
    
    if not d:
        if not alreadyWarned:
            logger.warning((
              'Vxxxx',
              (),
              "No input or output in call to analyze_single()."))
        
        return []
    
    return [noncontextual.Noncontextual(d)]

def analyze_special(inTuples, outTuples, **kwArgs):
    """
    This method is used when the outTuples are shorter than the inTuples.
    
    ### inTuples = ((3, 4, 5), (3, 4, 7))
    ### outTuples = ((19, 21), (19, 22))
    ### for i, s in enumerate(analyze_special(inTuples, outTuples)):
    ...     print("Subtable", i)
    ...     s.pprint(onlySignificant=True)
    Subtable 0
    State 'Start of text':
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
    State 'Start of line':
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
    State 'Saw_3':
      Class 'Deleted glyph':
        Go to state 'Saw_3'
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
      Class '4':
        Go to state 'Saw_3_4'
    State 'Saw_3_4':
      Class 'Deleted glyph':
        Go to state 'Saw_3_4'
      Class '3':
        Mark this glyph, then go to state 'Saw_3'
      Class '5':
        Go to state 'Start of text' after changing the marked glyph thus:
          3: 65533
      Class '7':
        Go to state 'Start of text' after changing the marked glyph thus:
          3: 65532
    Class table:
      3: 3
      4: 4
      5: 5
      7: 7
    Mask value: (no data)
    Coverage: (no data)
    Subtable 1
    State 'Start of text':
      Class '65532':
        Go to state 'Saw_65532' after changing the current glyph thus:
          65532: 19
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 19
    State 'Start of line':
      Class '65532':
        Go to state 'Saw_65532' after changing the current glyph thus:
          65532: 19
      Class '65533':
        Go to state 'Saw_65533' after changing the current glyph thus:
          65533: 19
    State 'Saw_65532':
      Class 'Deleted glyph':
        Go to state 'Saw_65532'
      Class '4':
        Go to state 'Saw_65532_4' after changing the current glyph thus:
          4: 22
      Class '65532':
        Mark this glyph, then go to state 'Saw_65532'
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    State 'Saw_65532_4':
      Class 'Deleted glyph':
        Go to state 'Saw_65532_4'
      Class '65532':
        Mark this glyph, then go to state 'Saw_65532'
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
      Class '7':
        Go to state 'Start of text' after changing the current glyph thus:
          7: Deleted glyph
    State 'Saw_65533':
      Class 'Deleted glyph':
        Go to state 'Saw_65533'
      Class '4':
        Go to state 'Saw_65533_4' after changing the current glyph thus:
          4: 21
      Class '65532':
        Mark this glyph, then go to state 'Saw_65532'
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    State 'Saw_65533_4':
      Class 'Deleted glyph':
        Go to state 'Saw_65533_4'
      Class '5':
        Go to state 'Start of text' after changing the current glyph thus:
          5: Deleted glyph
      Class '65532':
        Mark this glyph, then go to state 'Saw_65532'
      Class '65533':
        Mark this glyph, then go to state 'Saw_65533'
    Class table:
      4: 4
      5: 5
      7: 7
      65532: 65532
      65533: 65533
    Mask value: (no data)
    Coverage: (no data)
    """
    
    nextFake = kwArgs.pop('fakeBase', 0xFFFD)
    v = []
    
    for t in inTuples:
        v.append((nextFake,) + t[1:])
        nextFake -= 1
    
    tempIn = tuple(v)
    rv = analyze_contextual(inTuples, tempIn, fakeBase=nextFake, **kwArgs)
    vOut = []
    
    for tIn, tOut in zip(tempIn, outTuples):
        vOut.append(tOut + (65535,) * (len(tIn) - len(tOut)))
    
    kwArgs.pop('alreadyFaked', None)
    
    rv.extend(
      analyze_contextual(
        tempIn,
        tuple(vOut),
        alreadyFaked = True,
        **kwArgs))
    
    return rv

# The dispatch table used in analyze()

_dispatch = {
  'alternate': analyze_alternate,
  'chaining_backtrackonly': analyze_chaining_backtrackonly,
  'chaining_both': analyze_chaining_both,
  'chaining_lookaheadonly': analyze_chaining_lookaheadonly,
  'composite': analyze_composite,
  'contextual': analyze_contextual,
  'ligature': analyze_ligature,
  'multiple': analyze_multiple,
  'single': analyze_single}

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    
    # All the doctests in this module have been temporarily disabled, until
    # they can be moved to unit tests (appropriate in this case because of
    # dependencies on an external font).
    
    from fontio3 import utilities
    
    def _makeTestContext():
        from fontio3 import fontedit
        
        e = fontedit.Editor.frompath(
          "/Users/OpstadD/Desktop/WTLE AAT Fonts/Repaired.ttf")
        
        g = e.GSUB
        nm = e.getNamer()
        #nm.annotate = True
        return g.features[b'abvs0001'][2][0], nm
    
    def _makeTestInsert():
        from fontio3 import fontedit
        
        e = fontedit.Editor.frompath(
          "/Users/OpstadD/Desktop/WTLE AAT Fonts/Repaired.ttf")
        
        g = e.GSUB
        nm = e.getNamer()
        #nm.annotate = True
        return g.features[b'blws0021'][0][0], nm
    
    def _makeTestInsert2():
        from fontio3 import fontedit
        
        e = fontedit.Editor.frompath(
          "/Users/OpstadD/Desktop/WTLE AAT Fonts/Repaired.ttf")
        
        g = e.GSUB
        nm = e.getNamer()
        #nm.annotate = True
        return g.features[b'vatu0069'][2][0], nm

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
