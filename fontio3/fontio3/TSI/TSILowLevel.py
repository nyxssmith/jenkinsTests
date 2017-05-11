#
# TSILowLevel.py
#
# Copyright © 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for analysis of low-level TSI1-style hints.
"""

# System imports
import collections
import functools
import operator
import re

# Other imports
from fontio3.fontdata import textmeta
from fontio3.h2 import analyzer, common, opcode_tt
from fontio3.TSI import TSIUtilities
from fontio3.utilities import span2, writer

# -----------------------------------------------------------------------------

#
# Constants
#

# We put the dispatch table here, rather than in the class itself, because we
# use its keys to construct the pattern matcher for opcodes.

DISPATCH = {
  '#PUSH': ('_popPush', {'kinds': ()}),
  'AA': ('_popPush', {'kinds': ('aaIndex',)}),
  'ABS': ('_popPush', {'monadic': operator.abs}),
  'ADD': ('_popPush', {'dyadic': operator.add}),
  'ALIGNPTS': ('_popPush', {'kinds': ('pointIndex', 'pointIndex')}),
  'ALIGNRP': ('_popPush', {'kinds': ('loop', 'pointIndex')}),
  # we CANNOT use operator.and_ here: that is a bitwise AND, so op(2,1) is 0.
  'AND': ('_popPush', {'dyadic': (lambda a, b: bool(a and b))}),
  'CALL': ('_handleCALL', {}),
  'CEILING': ('_popPush', {'monadic': (lambda x: ((x + 63) >> 6) << 6)}),
  'CINDEX': ('_cmIndex', {'copy': True}),
  'CLEAR': ('_popPush', {'kinds': ('all',)}),
  'DEBUG': ('_popPush', {'kinds': ('debugCode',)}),
  'DELTAC1': ('_handleDelta', {'band': 1, 'kind': 'cvtIndex'}),
  'DELTAC2': ('_handleDelta', {'band': 2, 'kind': 'cvtIndex'}),
  'DELTAC3': ('_handleDelta', {'band': 3, 'kind': 'cvtIndex'}),
  'DELTAP1': ('_handleDelta', {'band': 1}),
  'DELTAP2': ('_handleDelta', {'band': 2}),
  'DELTAP3': ('_handleDelta', {'band': 3}),
  'DEPTH': ('_handleDepth', {}),
  'DIV': ('_popPush', {'dyadic': (lambda a, b: (a * 64) // b)}),
  'DLTC1': ('_handleDelta', {'band': 1, 'kind': 'cvtIndex'}),
  'DLTC2': ('_handleDelta', {'band': 2, 'kind': 'cvtIndex'}),
  'DLTC3': ('_handleDelta', {'band': 3, 'kind': 'cvtIndex'}),
  'DLTP1': ('_handleDelta', {'band': 1}),
  'DLTP2': ('_handleDelta', {'band': 2}),
  'DLTP3': ('_handleDelta', {'band': 3}),
  'DUP': ('_cmIndex', {'copy': True, 'relIndex': 1}),
  'EIF': ('_handleEIF', {}),
  'ELSE': ('_handleELSE', {}),
  'EQ': ('_popPush', {'dyadic': operator.eq}),
  # EVEN and ODD just convert to True, since we don't use IFs here.
  'EVEN': ('_popPush', {'monadic': (lambda x: True)}),
  'FDEF': ('_handleFDEF', {'kinds': ('fdefIndex',)}),
  'FLIPOFF': ('_popPush', {'niladic': None}),
  'FLIPON': ('_popPush', {'niladic': None}),
  'FLIPPT': ('_popPush', {'kinds': ('loop', 'pointIndex')}),
  'FLIPRGOFF': ('_popPush', {'kinds': ('pointIndex', 'pointIndex')}),
  'FLIPRGON': ('_popPush', {'kinds': ('pointIndex', 'pointIndex')}),
  'FLOOR': ('_popPush', {'monadic': (lambda x: (x >> 6) << 6)}),
  'GC': ('_popPush', {'kinds': ('pointIndex',), 'outCount': 1}),
  'GETINFO': ('_popPush', {'kinds': ('getInfoSelector',), 'outCount': 1}),
  'GFV': ('_popPush', {'kinds': (), 'outCount': 2}),
  'GPV': ('_popPush', {'kinds': (), 'outCount': 2}),
  'GT': ('_popPush', {'dyadic': operator.gt}),
  'GTEQ': ('_popPush', {'dyadic': operator.ge}),
  'IDEF': ('_popPush', {'kinds': ('IDEFopcode',)}),
  'IF': ('_handleIF', {}),
  'INSTCTRL': ('_popPush', {'kinds': (None, None)}),
  'IP': ('_popPush', {'kinds': ('loop', 'pointIndex')}),
  'ISECT': ('_popPush', {'kinds': ('pointIndex',) * 5}),
  'JMPR': ('_popPush', {'kinds': ('jumpOffset',)}),
  'JROF': ('_popPush', {'kinds': ('jumpOffset', 'conditional')}),
  'JROT': ('_popPush', {'kinds': ('jumpOffset', 'conditional')}),
  'LOOPCALL': ('_handleCALL', {'useCount': True}),
  'LT': ('_popPush', {'dyadic': operator.lt}),
  'LTEQ': ('_popPush', {'dyadic': operator.le}),
  'MAX': ('_popPush', {'dyadic': (lambda a, b: max(a, b))}),
  'MD': ('_popPush', {'kinds': ('pointIndex',) * 2, 'outCount': 1}),
  'MDAP': ('_popPush', {'kinds': ('pointIndex',)}),
  'MDRP': ('_popPush', {'kinds': ('pointIndex',)}),
  'MIAP': ('_popPush', {'kinds': ('pointIndex', 'cvtIndex')}),
  'MIN': ('_popPush', {'dyadic': (lambda a, b: min(a, b))}),
  'MINDEX': ('_cmIndex', {'copy': False}),
  'MIRP': ('_popPush', {'kinds': ('pointIndex', 'cvtIndex')}),
  'MPPEM': ('_popPush', {'kinds': (), 'outCount': 1}),
  'MPS': ('_popPush', {'kinds': (), 'outCount': 1}),
  'MSIRP': ('_popPush', {'kinds': ('pointIndex', 'pixels')}),
  'MUL': ('_popPush', {'dyadic': (lambda a, b: (a * b) // 64)}),
  'NEG': ('_popPush', {'monadic': operator.neg}),
  'NEQ': ('_popPush', {'dyadic': operator.ne}),
  'NOT': ('_popPush', {'monadic': operator.not_}),
  'NROUND': ('_popPush', {'kinds': ('pixels',), 'outCount': 1}),
  'ODD': ('_popPush', {'monadic': (lambda x: True)}),
  'OFFSET': ('_popPush', {'kinds': ('glyphIndex', 'FUnits', 'FUnits')}),
  'OR': ('_popPush', {'dyadic': (lambda a, b: bool(a or b))}),
  'POP': ('_popPush', {'kinds': (None,)}),
  'RCVT': ('_popPush', {'kinds': ('cvtIndex',), 'outCount': 1}),
  'ROLL': ('_cmIndex', {'copy': False, 'relIndex': 3}),
  'ROUND': ('_popPush', {'kinds': ('pixels',), 'outCount': 1}),
  'RS': ('_popPush', {'kinds': ('storageIndex',), 'outCount': 1}),
  'S45ROUND': ('_popPush', {'kinds': (None,)}),
  'SCANCTRL': ('_popPush', {'kinds': (None,)}),
  'SCANTYPE': ('_popPush', {'kinds': (None,)}),
  'SCFS': ('_popPush', {'kinds': ('pointIndex', 'pixels')}),
  'SCVTCI': ('_popPush', {'kinds': ('pixels',), 'isState': True}),
  'SDB': ('_popPush', {'setState': 'deltaBase'}),
  'SDPVTL': ('_popPush', {'kinds': ('pointIndex',) * 2}),
  'SDS': ('_popPush', {'setState': 'deltaShift'}),
  'SFVFS': ('_popPush', {'kinds': (None, None)}),
  'SFVTL': ('_popPush', {'kinds': ('pointIndex',) * 2}),
  'SHC': ('_popPush', {'kinds': ('contourIndex',)}),
  'SHP': ('_popPush', {'kinds': ('loop', 'pointIndex')}),
  'SHPIX': ('_popPush', {'kinds': ('loop', 'pointIndex', 'pixels')}),
  'SHZ': ('_popPush', {'kinds': ('zoneIndex',)}),
  'SLOOP': ('_popPush', {'setState': 'loop'}),
  'SMD': ('_popPush', {'kinds': ('pixels',)}),
  'SOFFSET': ('_popPush', {'kinds': ('glyphIndex', 'FUnits', 'FUnits', '2x2', '2x2', '2x2', '2x2')}),
  'SPVFS': ('_popPush', {'kinds': (None, None)}),
  'SPVTL': ('_popPush', {'kinds': ('pointIndex',) * 2}),
  'SROUND': ('_popPush', {'kinds': (None,)}),
  'SRP0': ('_popPush', {'kinds': ('pointIndex',)}),
  'SRP1': ('_popPush', {'kinds': ('pointIndex',)}),
  'SRP2': ('_popPush', {'kinds': ('pointIndex',)}),
  'SSW': ('_popPush', {'kinds': ('FUnits',)}),
  'SSWCI': ('_popPush', {'kinds': ('pixels',)}),
  'SUB': ('_popPush', {'dyadic': operator.sub}),
  'SVTCA': ('_handleSVTCA', {}),
  'SWAP': ('_cmIndex', {'copy': False, 'relIndex': 2}),
  'SZP0': ('_popPush', {'kinds': ('zoneIndex',)}),
  'SZP1': ('_popPush', {'kinds': ('zoneIndex',)}),
  'SZP2': ('_popPush', {'kinds': ('zoneIndex',)}),
  'SZPS': ('_popPush', {'kinds': ('zoneIndex',)}),
  'UTP': ('_popPush', {'kinds': ('pointIndex',)}),
  'WCVTF': ('_popPush', {'kinds': ('cvtIndex', 'FUnits')}),
  'WCVTP': ('_popPush', {'kinds': ('cvtIndex', 'pixels')}),
  'WS': ('_popPush', {'kinds': ('storageIndex', None)})}

_srt = '|'.join(sorted(DISPATCH, reverse=True, key=len))
PAT_OP = re.compile(r'(%s)\[([^]]*)\]((\s*,\s*[0-9-.]+)*)' % (_srt,))
del _srt

PAT_PUSH = re.compile(r'(#PUSH)((\s*,\s*[0-9-]+)*)')
PAT_NUMBER = re.compile(r'([0-9-.]+)')
PAT_DELTA = re.compile(r'\(\s*([0-9]+)\s*@([0-9]+)\s*([0-9-]+)\s*(/[0-9]+)?\)')
PAT_IF = re.compile(r'(IF|ELSE|EIF)\[\]')
PAT_CVT = re.compile(r'([0-9]+)\s*:\s*([0-9-]+)')
DELTAS = frozenset({0x5D, 0x71, 0x72, 0x73, 0x74, 0x75})

StartStop = TSIUtilities.StartStop
LocInfo = TSIUtilities.LocInfo

NAMEMAP = common.rawOpcodeToNameMap

INVNAMEMAP = {s: k for k, s in NAMEMAP.items()}
INVNAMEMAP['DLTC1[]'] = INVNAMEMAP['DELTAC1[]']
INVNAMEMAP['DLTC2[]'] = INVNAMEMAP['DELTAC2[]']
INVNAMEMAP['DLTC3[]'] = INVNAMEMAP['DELTAC3[]']
INVNAMEMAP['DLTP1[]'] = INVNAMEMAP['DELTAP1[]']
INVNAMEMAP['DLTP2[]'] = INVNAMEMAP['DELTAP2[]']
INVNAMEMAP['DLTP3[]'] = INVNAMEMAP['DELTAP3[]']

PAT_LOW_DELTA = re.compile(r'\(\s*([0-9]+)\s*@([0-9]+)\s+([0-9-]+)\)')

# -----------------------------------------------------------------------------

#
# Functions
#

def _cvtHelper(obj, **kwArgs):
    """
    Helper function that returns a generator over (start, length) pairs which
    identify locations of cvtIndex values in the string. Note that the actual
    argument passed in here is ignored.
    
    The following keyword arguments are supported:
    
        origObj     The original Hints object (this being passed in is
                    automatically handled by the protocol cvtsRenumbered()
                    method).
    
    >>> obj = Hints("RCVT[], 14")
    >>> for t in _cvtHelper(None, origObj=obj):
    ...   print(t)
    (8, 2)
    """
    
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'cvtIndex':
            yield (start, stop - start)

def _fdefHelper(obj, **kwArgs):
    """
    Helper function that returns a generator over (start, length) pairs which
    identify locations of fdefIndex values in the string. Note that the actual
    argument passed in here is ignored.
    
    The following keyword arguments are supported:
    
        origObj     The original Hints object (this being passed in is
                    automatically handled by the protocol fdefsRenumbered()
                    method).
    
    >>> a = {14: ({}, 0, 0, None, {}, 0)}
    >>> obj = Hints("/* ignored */ FDEF[], 14", analysis=a)
    >>> for t in _fdefHelper(None, origObj=obj):
    ...   print(t)
    (22, 2)
    """
    
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'fdefIndex':
            yield (start, stop - start)

def _frombinary_call(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for a CALL. Note that
    LOOPCALL is handled in its own, separate method.
    
    >>> a = {14: ({}, 1, 1, None, {}, 1)}
    >>> stk = [(9, 81), (14, 76)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 0,
    ...   'pushOn': True,
    ...   'pushesToDelete': set(),
    ...   'fdefAnalysis': a}
    >>> _frombinary_call(0x2B, state, NAMEMAP)
    ['CALL[], 9, 14']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    fdefAnalysis {14: ({}, 1, 1, None, {}, 1)}
    ifDepth 0
    loop 1
    pushOn True
    pushesToDelete {81, 76}
    stack [('data', None)]
    
    >>> state['pushOn'] = False
    >>> state['stack'] = list(stk)
    >>> _frombinary_call(0x2B, state, NAMEMAP)
    ['#PUSHON', 'CALL[], 9, 14']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    fdefAnalysis {14: ({}, 1, 1, None, {}, 1)}
    ifDepth 0
    loop 1
    pushOn True
    pushesToDelete {81, 76}
    stack [('data', None)]
    
    >>> state['pushOn'] = False
    >>> state['stack'] = list(stk)
    >>> state['ifDepth'] = 1
    >>> _frombinary_call(0x2B, state, NAMEMAP)
    ['CALL[]']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    fdefAnalysis {14: ({}, 1, 1, None, {}, 1)}
    ifDepth 1
    loop 1
    pushOn False
    pushesToDelete {81, 76}
    stack [('data', None)]
    """
    
    r = []
    stk = state['stack']
    addPTD = not bool(state['ifDepth'])
    statePTD = state['pushesToDelete']
    
    if addPTD and (not state['pushOn']):
        r.append("#PUSHON")
        state['pushOn'] = True
    
    a = state['fdefAnalysis']
    fdefIndex, fdefIndexPTD = stk.pop()
    
    if addPTD and (fdefIndexPTD is not None):
        statePTD.add(fdefIndexPTD)
    
    inArgs, inCount, inDeepest, ops, outArgs, outCount = a[fdefIndex]
    
    if inCount:
        v, ptds = list(zip(*stk[-inCount:]))
        v = list(v)
        
        if addPTD:
            statePTD.update(i for i in ptds if i is not None)
        
        del stk[-inCount:]

    else:
        v = []

    if outCount:
        stk.extend([('data', None)] * outCount)

    v.append(fdefIndex)
    
    if state['pushOn']:
        r.append(", ".join([nameMap[code]] + [str(x) for x in v]))
    else:
        r.append(nameMap[code])
    
    state['loop'] = 1
    return r

def _frombinary_cmindex(code, state, nameMap, **kwArgs):
    """
    Returns a list of Unicode strings comprising the code for one of the stack
    operation that moves things around. While this method is generic, and can
    do things not provided for in the TrueType instruction set, it is used for
    the following opcodes: DUP, SWAP, CINDEX, MINDEX, ROLL.
    
    >>> stk = [(1, 9), (2, 10), (9, 81), (3, 76)]
    >>> state = {'stack': list(stk), 'pushOn': True}
    
    DUP:
    
    >>> _frombinary_cmindex(0x20, state, NAMEMAP, relIndex=1, copy=True)
    ['#PUSHOFF', 'DUP[]']
    >>> state['stack']
    [(1, 9), (2, 10), (9, 81), (3, 76), (3, 76)]
    
    SWAP:
    
    >>> state = {'stack': list(stk), 'pushOn': True}
    >>> _frombinary_cmindex(0x23, state, NAMEMAP, relIndex=2, copy=False)
    ['#PUSHOFF', 'SWAP[]']
    >>> state['stack']
    [(1, 9), (2, 10), (3, 76), (9, 81)]
    
    CINDEX:
    
    >>> state = {'stack': list(stk), 'pushOn': True}
    >>> _frombinary_cmindex(0x25, state, NAMEMAP, copy=True)
    ['#PUSHOFF', 'CINDEX[]']
    >>> state['stack']
    [(1, 9), (2, 10), (9, 81), (1, 9)]
    
    MINDEX:
    
    >>> state = {'stack': list(stk), 'pushOn': True}
    >>> _frombinary_cmindex(0x26, state, NAMEMAP, copy=False)
    ['#PUSHOFF', 'MINDEX[]']
    >>> state['stack']
    [(2, 10), (9, 81), (1, 9)]
    
    ROLL:
    
    >>> state = {'stack': list(stk), 'pushOn': True}
    >>> _frombinary_cmindex(0x8A, state, NAMEMAP, relIndex=3, copy=False)
    ['#PUSHOFF', 'ROLL[]']
    >>> state['stack']
    [(1, 9), (9, 81), (3, 76), (2, 10)]
    """
    
    stk = state['stack']
    r = []
    
    if state['pushOn']:
        r.append("#PUSHOFF")
        state['pushOn'] = False
    
    if 'relIndex' in kwArgs:
        n = kwArgs['relIndex']
    else:
        n = stk.pop()[0]
    
    assert n
    moveObj = stk[-n]
    
    if not kwArgs['copy']:
        del stk[-n]
    
    stk.append(moveObj)
    r.append(nameMap[code])
    state['loop'] = 1
    return r

def _frombinary_delta(code, state, nameMap, prefix='P1'):
    """
    Returns a list of Unicode strings comprising the code for one of the DELTA
    hints.
    
    >>> stk = [(31, 31), (14, 30), (15, 29), (14, 28), (2, 27)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 0,
    ...   'pushOn': True,
    ...   'pushesToDelete': set()}
    >>> _frombinary_delta(0x5D, state, NAMEMAP)
    ['DLTP1[(14 @0 8)(14 @1 8)]']
    >>> state['stack']
    []
    
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 1,
    ...   'pushOn': False,
    ...   'pushesToDelete': set()}
    >>> _frombinary_delta(0x5D, state, NAMEMAP)
    ['DELTAP1[]']
    >>> state['stack']
    []
    """
    
    r = []
    stk = state['stack']
    addPTD = not bool(state['ifDepth'])
    statePTD = state['pushesToDelete']
    
    if addPTD and (not state['pushOn']):
        r.append("#PUSHON")
        state['pushOn'] = True
    
    count, countPTD = stk.pop()
    
    if count == 'data':
        raise ValueError("Computed DELTA count!")
    
    if addPTD and (countPTD is not None):
        statePTD.add(countPTD)
    
    if state['pushOn']:
        sv = []
    
        while count:
            rawArg, rawPoint = stk[-2:]
            del stk[-2:]
            
            if addPTD:
                if rawArg[1] is not None:
                    statePTD.add(rawArg[1])
                
                if rawPoint[1] is not None:
                    statePTD.add(rawPoint[1])
            
            ppem, shift = divmod(rawArg[0], 16)
            shift -= (7 + (shift < 8))
            sv.append("(%d @%d %d)" % (rawPoint[0], ppem, shift))
            count -= 1
    
        r.append("DLT%s[%s]" % (prefix, ''.join(sv)))
    
    else:
        del stk[-2*count:]
        r.append(nameMap[code])
    
    state['loop'] = 1
    return r

def _frombinary_depth(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for one of the DELTA
    hints.
    
    >>> stk = [(31, 31), (14, 30), (15, 29), (14, 28), (2, 27)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'pushOn': True}
    >>> _frombinary_depth(0x24, state, NAMEMAP)
    ['#PUSHOFF', 'DEPTH[]']
    >>> state['stack']
    [(31, 31), (14, 30), (15, 29), (14, 28), (2, 27), (5, None)]
    """
    
    r = []
    stk = state['stack']
    
    if state['pushOn']:
        r.append("#PUSHOFF")
        state['pushOn'] = False
    
    stk.append((len(stk), None))
    r.append(nameMap[code])
    state['loop'] = 1
    return r

def _frombinary_dostack(code, state):
    """
    This is the dispatcher to the individual _frombinary_xxx methods. It
    returns a list of Unicode strings comprising the code for a single hint.
    """
    
    nameMap = NAMEMAP
    func = _frombinary_dispatch.get(code, None)
    
    if func is None:
        return [nameMap[code]]
    
    return func(code, state, nameMap)

def _frombinary_eif(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for an EIF.
    
    >>> stk = [(1, 30), (-1, 29)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 1,
    ...   'pushOn': False,
    ...   'stackStack': [[], []]}
    >>> _frombinary_eif(0x59, state, NAMEMAP)
    ['EIF[]']
    
    Note that the 'stateState' list has been popped:
    
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 0
    loop 1
    pushOn False
    stack [(1, 30), (-1, 29)]
    stackStack [[]]
    """
    
    assert state['ifDepth']
    r = [nameMap[code]]
    state['ifDepth'] -= 1
    del state['stackStack'][-1]
    state['loop'] = 1
    return r

def _frombinary_else(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for an ELSE.
    
    >>> stk = [(1, 30), (-1, 29)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 1,
    ...   'pushOn': False,
    ...   'stackStack': [[], [(14, 23)]]}
    >>> _frombinary_else(0x1B, state, NAMEMAP)
    ['ELSE[]']
    
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 1
    loop 1
    pushOn False
    stack [(14, 23)]
    stackStack [[], [(14, 23)]]
    """
    
    assert state['ifDepth']
    r = [nameMap[code]]
    state['stack'][:] = state['stackStack'][-1][:]
    state['loop'] = 1
    return r

def _frombinary_if(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for an IF.
    
    >>> stk = [(1, 30), (-1, 29)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 0,
    ...   'pushOn': True,
    ...   'stackStack': []}
    >>> _frombinary_if(0x58, state, NAMEMAP)
    ['#PUSHOFF', 'IF[]']
    
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 1
    loop 1
    pushOn False
    stack [(1, 30)]
    stackStack [[(1, 30)]]
    """
    
    r = []
    stk = state['stack']
    del stk[-1]  # cond
    
    if state['pushOn']:
        r.append("#PUSHOFF")
        state['pushOn'] = False
    
    state['ifDepth'] += 1
    state['stackStack'].append(list(stk))
    r.append(nameMap[code])
    state['loop'] = 1
    return r

def _frombinary_invalid(code, state, nameMap):
    """
    This method is called for undefined TrueType opcodes. It raises a
    ValueError.
    
    >>> _frombinary_invalid(0x6B, {}, NAMEMAP)
    Traceback (most recent call last):
      ...
    ValueError: The 0x6B opcode is not a valid TrueType hints
    """
    
    s = "The 0x%02X opcode is not a valid TrueType hints" % (code,)
    raise ValueError(s)

def _frombinary_loopcall(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for a LOOPCALL.
    
    >>> a = {14: ({}, 1, 1, None, {}, 1)}
    >>> stk = [(-9, 82), (9, 81), (14, 76), (2, 86)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 0,
    ...   'pushOn': True,
    ...   'pushesToDelete': set(),
    ...   'fdefAnalysis': a}
    >>> _frombinary_loopcall(0x2A, state, NAMEMAP)
    ['#PUSHOFF', 'LOOPCALL[]']
    
    >>> for key in sorted(state):
    ...   print(key, state[key])
    fdefAnalysis {14: ({}, 1, 1, None, {}, 1)}
    ifDepth 0
    loop 1
    pushOn False
    pushesToDelete set()
    stack [(-9, 82), ('data', None)]
    """
    
    r = []
    stk = state['stack']
    
    if state['pushOn']:
        r.append("#PUSHOFF")
        state['pushOn'] = False
    
    count = stk.pop()[0]
    saveCount = count
    a = state['fdefAnalysis']
    fdefIndex = stk.pop()[0]
    inArgs, inCount, inDeepest, ops, outArgs, outCount = a[fdefIndex]
    
    while count:
        count -= 1
        
        if inCount:
            del stk[-inCount:]
    
        if outCount:
            stk.extend([('data', None)] * outCount)
    
    r.append(nameMap[code])
    state['loop'] = 1
    return r

def _frombinary_poppush(code, state, nameMap, popCount=1, pushCount=0):
    """
    Returns a list of Unicode strings comprising the code for many common
    opcodes. This method handles generic pushes and/or pops; the values for the
    popCount and pushCount parameters are added to the dispatch table via the
    Python functools.partial() function.
    
    >>> stk = [(10, 31), (5, 32), (19, 33)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'pushOn': True,
    ...   'ifDepth': 0,
    ...   'loop': 1,
    ...   'pushesToDelete': set()}
    >>> _frombinary_poppush(0x32, state, NAMEMAP)
    ['SHP[2], 19']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 0
    loop 1
    pushOn True
    pushesToDelete {33}
    stack [(10, 31), (5, 32)]
    
    If popCount is 'loop' then state['loop'] will be used to determine how many
    items to pop from the stack:
    
    >>> state = {
    ...   'stack': list(stk),
    ...   'pushOn': True,
    ...   'ifDepth': 0,
    ...   'loop': 2,
    ...   'pushesToDelete': set()}
    >>> _frombinary_poppush(0x39, state, NAMEMAP, popCount='loop')
    ['IP[], 5, 19']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 0
    loop 1
    pushOn True
    pushesToDelete {32, 33}
    stack [(10, 31)]
    
    If pushCount is nonzero, that number of 'data' strings will be added to the
    end of the stack (after any values are popped first). Note that no attempt
    is made to actually execute an instruction (i.e. ADD pops 2 and pushes a
    single 'data' string, even if the popped values could easily be added):
    
    >>> state = {
    ...   'stack': list(stk),
    ...   'pushOn': True,
    ...   'ifDepth': 0,
    ...   'loop': 1,
    ...   'pushesToDelete': set()}
    >>> _frombinary_poppush(0x0C, state, NAMEMAP, popCount=0, pushCount=2)
    ['GPV[]']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 0
    loop 1
    pushOn True
    pushesToDelete set()
    stack [(10, 31), (5, 32), (19, 33), ('data', None), ('data', None)]
    """
    
    r = []
    stk = state['stack']
    addPTD = not bool(state['ifDepth'])
    statePTD = state['pushesToDelete']
    
    if addPTD and (not state['pushOn']):
        r.append("#PUSHON")
        state['pushOn'] = True
    
    if popCount:
        if popCount == 'loop':
            popCount = state['loop']
        elif popCount == 'loop+1':
            popCount = state['loop'] + 1
        elif popCount == 'all':
            popCount = len(stk)
        
        v, ptds = list(zip(*stk[-popCount:]))
        
        if state['pushOn'] and ('data' in v):
            if r:
                # If we changed to PUSHON, we need to undo that, since we
                # now know there's one or more 'data' entries present.
                del r[0]
                state['pushOn'] = False
            
            else:
                r.append("#PUSHOFF")
                state['pushOn'] = False
        
        elif addPTD:
            for i in ptds:
                if i is not None:
                    statePTD.add(i)
        
        del stk[-popCount:]
        
        if state['pushOn']:
            r.append(", ".join([nameMap[code]] + [str(x) for x in v]))
        
        else:
            r.append(nameMap[code])
    
    else:
        r.append(nameMap[code])
    
    if pushCount:
        stk.extend([('data', None)] * pushCount)
    
    state['loop'] = 1
    return r

def _frombinary_postprocess(sv, **kwArgs):
    """
    Given a list of all the Unicode strings representing the hint stream, do
    simplifications and other post-processing steps. To see the process at work
    set debugPrint to True. You can restrict to debugPrinting just relevant
    phases using the debugPhases kwArg (a set). The following phases are
    defined:
    
        prolog
        contigOnOff
        pushes
        initialOn
        countZeroCases      
        redundancies
        indenting
    
    Note that the phases just affect debugPrint cases; the returned list has
    always had all phases run.
    
    >>> sv = ['#PUSHOFF', '#PUSHON', 'SRP0[], 19']
    >>> _pp = _frombinary_postprocess
    >>> ignore = _pp(sv, debugPrint=True, debugPhases={'contigOnOff'})
    Postprocess: after collapsing contiguous ON/OFF groups
    [0000] #PUSHON
    [0001] SRP0[], 19
    
    >>> ignore = _pp(sv, debugPrint=True, debugPhases={'initialOn'})
    Postprocess: after removing initial ON
    [0000] SRP0[], 19
    
    >>> sv = ['#PUSHOFF', '#PUSH, 12', '#PUSH, -5', '#PUSH, 18']
    >>> ignore = _pp(sv, debugPrint=True, debugPhases={'pushes'})
    Postprocess: after combining adjacent pushes
    [0000] #PUSHOFF
    [0001] #PUSH, 12, -5, 18
    
    >>> sv = ['#PUSHOFF', '#PUSH, 5', '#PUSHON', 'SVTCA[X]', '#PUSHOFF']
    >>> ignore = _pp(sv, debugPrint=True, debugPhases={'countZeroCases'})
    Postprocess: after trimming redundant ON/.../OFF groups
    [0000] #PUSHOFF
    [0001] #PUSH, 5
    [0002] SVTCA[X]
    """
    
    debugPrint = kwArgs.pop('debugPrint', False)
    dpPhases = kwArgs.pop('debugPhases', {'all'})
    
    if debugPrint and ({'all', 'prolog'} & dpPhases):
        print("Postprocess: start")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # Simpify adjacent #PUSHON/#PUSHOFF blocks
    
    gOnOffs = (i for i, s in enumerate(sv) if s.startswith('#PUSHO'))
    spn = span2.Span(gOnOffs)
    toDel = set()
    
    for (first, last) in sorted(spn.ranges(), reverse=True):
        if last > first:
            toDel.update(range(first, last))  # doesn't include last
    
    for i in sorted(toDel, reverse=True):
        del sv[i]
    
    if debugPrint and ({'all', 'contigOnOff'} & dpPhases):
        print("Postprocess: after collapsing contiguous ON/OFF groups")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # Combine adjacent #PUSHes
    
    gPushes = (i for i, s in enumerate(sv) if s.startswith("#PUSH, "))
    spn = span2.Span(gPushes)
    toCombine = {}
    
    for (first, last) in sorted(spn.ranges(), reverse=True):
        if last > first:
            v = [sv[n][7:] for n in range(first, last + 1)]
            s = "#PUSH, %s" % (', '.join(v),)
            toCombine[(first, last)] = s
    
    for t in sorted(toCombine, reverse=True):
        sv[t[0]:t[1]+1] = [toCombine[t]]
    
    if debugPrint and ({'all', 'pushes'} & dpPhases):
        print("Postprocess: after combining adjacent pushes")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # Since #PUSHON is the default, remove an initial redundant #PUSHON
    
    if sv[0] == "#PUSHON":
        del sv[0]
    
    if debugPrint and ({'all', 'initialOn'} & dpPhases):
        print("Postprocess: after removing initial ON")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # Trim PUSHON, non-DLT hints with inCount==0, PUSHOFF cases
    
    groups = []
    
    for i, s in enumerate(sv):
        if s != "#PUSHON":
            continue
        
        for j in range(i + 1, len(sv)):
            if sv[j] == "#PUSHOFF":
                found = j
                break
        else:
            found = None
        
        if found is not None:
            groups.append((i, found))
    
    for g in reversed(groups):
        for i in range(g[0] + 1, g[1]):
            s = sv[i]
            
            if s.startswith("DLT") or (',' in s):
                break
        
        else:
            del sv[g[1]]
            del sv[g[0]]
    
    if debugPrint and ({'all', 'countZeroCases'} & dpPhases):
        print("Postprocess: after trimming redundant ON/.../OFF groups")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # Trim initial PUSHOFF, non-DLT hints with inCount==0, PUSHON case
    
    if sv[0] == "#PUSHOFF":
        for i in range(1, len(sv)):
            if sv[i] == "#PUSHON":
                found = i
                break
        else:
            found = None
        
        if found is not None:
            for i in range(1, found):
                s = sv[i]
                
                if s.startswith("DLT") or (',' in s):
                    break
            
            else:
                del sv[found]
                del sv[0]
    
    if debugPrint and ({'all', 'redundancies'} & dpPhases):
        print("Postprocess: after trimming redundant leading OFF/.../ON group")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))
    
    # THIS HAS TO COME LAST
    # Do indenting of IF-EIF blocks
    
    currLevel = 0
    indent = '   '
    
    for i, s in enumerate(sv):
        if s.startswith("IF[]"):
            if currLevel:
                sv[i] = (indent * currLevel) + s
            
            currLevel += 1
        
        elif s.startswith("ELSE[]"):
            assert currLevel
            
            if currLevel > 1:
                sv[i] = (indent * (currLevel - 1)) + s
        
        elif s.startswith("EIF[]"):
            assert currLevel
            currLevel -= 1
            
            if currLevel:
                sv[i] = (indent * currLevel) + s
        
        elif currLevel:
            sv[i] = (indent * currLevel) + s
    
    if debugPrint and ({'all', 'indenting'} & dpPhases):
        print("Postprocess: after indenting IF-EIF blocks")
        
        for i, s in enumerate(sv):
            print("[%04d] %s" % (i, s))

def _frombinary_sloop(code, state, nameMap):
    """
    Returns a list of Unicode strings comprising the code for a SLOOP.
    
    >>> stk = [(-9, 82), (9, 81), (14, 76), (2, 86)]
    >>> state = {
    ...   'stack': list(stk),
    ...   'ifDepth': 0,
    ...   'pushOn': True,
    ...   'pushesToDelete': set(),
    ...   'loop': 1}
    >>> _frombinary_sloop(0x17, state, NAMEMAP)
    ['SLOOP[], 2']
    >>> for key in sorted(state):
    ...   print(key, state[key])
    ifDepth 0
    loop 2
    pushOn True
    pushesToDelete {86}
    stack [(-9, 82), (9, 81), (14, 76)]
    """
    
    r = []
    stk = state['stack']
    addPTD = not bool(state['ifDepth'])
    statePTD = state['pushesToDelete']
    
    if addPTD and (not state['pushOn']):
        r.append("#PUSHON")
        state['pushOn'] = True
    
    n, nptd = stk.pop()
    
    if n == 'data':
        raise ValueError("Computed SLOOP!")
    
    if addPTD and (nptd is not None):
        statePTD.add(nptd)
    
    if state['pushOn']:
        r.append("%s, %d" % (nameMap[code], n))
    else:
        r.append(nameMap[code])
    
    state['loop'] = n
    return r

def _frombinary_unsupported(code, state, nameMap, **kwArgs):
    """
    Returns a list of Unicode strings comprising the code
    """
    
    r = []
    stk = state['stack']
    
    if state['pushOn']:
        r.append("#PUSHOFF")
        state['pushOn'] = False
    
    popCount = kwArgs.get('popCount', 0)
    pushCount = kwArgs.get('pushCount', 0)
    
    if popCount:
        if popCount == 'all':
            popCount = len(stk)
        
        del stk[-popCount:]
    
    if pushCount:
        stk.extend([('data', None)] * pushCount)
    
    r.append(nameMap[code])
    state['loop'] = 1
    return r

f = functools.partial

_frombinary_dispatch = {  # not here means no effect
  0x06: f(_frombinary_poppush, popCount=2),  # SPVTL[r]
  0x07: f(_frombinary_poppush, popCount=2),  # SPVTL[R]
  0x08: f(_frombinary_poppush, popCount=2),  # SFVTL[r]
  0x09: f(_frombinary_poppush, popCount=2),  # SFVTL[R]
  0x0A: f(_frombinary_poppush, popCount=2),  # SPVFS[]
  0x0B: f(_frombinary_poppush, popCount=2),  # SFVFS[]
  0x0C: f(_frombinary_poppush, popCount=0, pushCount=2),  # GPV[]
  0x0D: f(_frombinary_poppush, popCount=0, pushCount=2),  # GFV[]
  0x0F: f(_frombinary_poppush, popCount=5),  # ISECT
  0x10: _frombinary_poppush,  # SRP0[]
  0x11: _frombinary_poppush,  # SRP1[]
  0x12: _frombinary_poppush,  # SRP2[]
  0x13: _frombinary_poppush,  # SZP0[]
  0x14: _frombinary_poppush,  # SZP1[]
  0x15: _frombinary_poppush,  # SZP2[]
  0x16: _frombinary_poppush,  # SZPS[]
  0x17: _frombinary_sloop,  # SLOOP[]
  0x1A: _frombinary_poppush,  # SMD[]
  0x1B: _frombinary_else,  # ELSE[]
  0x1C: f(_frombinary_unsupported, popCount=1),  # JMPR[]
  0x1D: _frombinary_poppush,  # SCVTCI[]
  0x1E: _frombinary_poppush,  # SSWCI[]
  0x1F: _frombinary_poppush,  # SSW[]
  0x20: f(_frombinary_cmindex, relIndex=1, copy=True),  # DUP[]
  0x21: f(_frombinary_unsupported, popCount=1),  # POP[]
  0x22: f(_frombinary_unsupported, popCount='all'),  # CLEAR[]
  0x23: f(_frombinary_cmindex, relIndex=2, copy=False),  # SWAP[]
  0x24: _frombinary_depth,  # DEPTH[]
  0x25: f(_frombinary_cmindex, copy=True),  # CINDEX[]
  0x26: f(_frombinary_cmindex, copy=False),  # MINDEX[]
  0x27: f(_frombinary_poppush, popCount=2),  # ALIGNPTS
  0x28: f(_frombinary_poppush, popCount=0, pushCount=1),  # RAW[]
  0x29: _frombinary_poppush,  # UTP[]
  0x2A: _frombinary_loopcall,  # LOOPCALL[]
  0x2B: _frombinary_call,  # CALL[]
  0x2C: f(_frombinary_unsupported, popCount=1),  # FDEF[]
  0x2D: _frombinary_unsupported,  # ENDF[]
  0x2E: _frombinary_poppush,  # MDAP[r]
  0x2F: _frombinary_poppush,  # MDAP[R]
  0x32: f(_frombinary_poppush, popCount='loop'),  # SHP[2]
  0x33: f(_frombinary_poppush, popCount='loop'),  # SHP[1]
  0x34: _frombinary_poppush,  # SHC[2]
  0x35: _frombinary_poppush,  # SHC[1]
  0x36: _frombinary_poppush,  # SHZ[2]
  0x37: _frombinary_poppush,  # SHZ[1]
  0x38: f(_frombinary_poppush, popCount='loop+1'),  # SHPIX
  0x39: f(_frombinary_poppush, popCount='loop'),  # IP[]
  0x3A: f(_frombinary_poppush, popCount=2),  # MSIRP[m]
  0x3B: f(_frombinary_poppush, popCount=2),  # MSIRP[M]
  0x3C: f(_frombinary_poppush, popCount='loop'),  # ALIGNRP[]
  0x3E: f(_frombinary_poppush, popCount=2),  # MIAP[r]
  0x3F: f(_frombinary_poppush, popCount=2),  # MIAP[R]
  0x42: f(_frombinary_poppush, popCount=2),  # WS[]
  0x43: f(_frombinary_poppush, pushCount=1),  # RS[]
  0x44: f(_frombinary_poppush, popCount=2),  # WCVTP[]
  0x45: f(_frombinary_poppush, pushCount=1),  # RCVT[]
  0x46: f(_frombinary_poppush, pushCount=1),  # GC[N]
  0x47: f(_frombinary_poppush, pushCount=1),  # GC[O]
  0x48: f(_frombinary_poppush, popCount=2),  # SCFS[]
  0x49: f(_frombinary_poppush, popCount=2, pushCount=1),  # MD[N]
  0x4A: f(_frombinary_poppush, popCount=2, pushCount=1),  # MD[O]
  0x4B: f(_frombinary_poppush, popCount=0, pushCount=1),  # MPPEM[]
  0x4C: f(_frombinary_poppush, popCount=0, pushCount=1),  # MPS[]
  0x4F: f(_frombinary_unsupported, popCount=1),  # DEBUG[]
  0x50: f(_frombinary_unsupported, popCount=2, pushCount=1),  # LT[]
  0x51: f(_frombinary_unsupported, popCount=2, pushCount=1),  # LTEQ[]
  0x52: f(_frombinary_unsupported, popCount=2, pushCount=1),  # GT[]
  0x53: f(_frombinary_unsupported, popCount=2, pushCount=1),  # GTEQ[]
  0x54: f(_frombinary_unsupported, popCount=2, pushCount=1),  # EQ[]
  0x55: f(_frombinary_unsupported, popCount=2, pushCount=1),  # NEQ[]
  0x56: f(_frombinary_unsupported, popCount=1, pushCount=1),  # ODD[]
  0x57: f(_frombinary_unsupported, popCount=1, pushCount=1),  # EVEN[]
  0x58: _frombinary_if,  # IF[]
  0x59: _frombinary_eif,  # EIF[]
  0x5A: f(_frombinary_unsupported, popCount=2, pushCount=1),  # AND[]
  0x5B: f(_frombinary_unsupported, popCount=2, pushCount=1),  # OR[]
  0x5C: f(_frombinary_unsupported, popCount=1, pushCount=1),  # NOT[]
  0x5D: _frombinary_delta,  # DELTAP1[]
  0x5E: _frombinary_poppush,  # SDB[]
  0x5F: _frombinary_poppush,  # SDS[]
  0x60: f(_frombinary_unsupported, popCount=2, pushCount=1),  # ADD[]
  0x61: f(_frombinary_unsupported, popCount=2, pushCount=1),  # SUB[]
  0x62: f(_frombinary_unsupported, popCount=2, pushCount=1),  # DIV[]
  0x63: f(_frombinary_unsupported, popCount=2, pushCount=1),  # MUL[]
  0x64: f(_frombinary_unsupported, popCount=1, pushCount=1),  # ABS[]
  0x65: f(_frombinary_unsupported, popCount=1, pushCount=1),  # NEG[]
  0x66: f(_frombinary_unsupported, popCount=1, pushCount=1),  # FLOOR[]
  0x67: f(_frombinary_unsupported, popCount=1, pushCount=1),  # CEILING[]
  0x68: f(_frombinary_poppush, pushCount=1),  # ROUND[Gr]
  0x69: f(_frombinary_poppush, pushCount=1),  # ROUND[Bl]
  0x6A: f(_frombinary_poppush, pushCount=1),  # ROUND[Wh]
  0x6B: _frombinary_invalid,
  0x6C: f(_frombinary_poppush, pushCount=1),  # NROUND[Gr]
  0x6D: f(_frombinary_poppush, pushCount=1),  # NROUND[Bl]
  0x6E: f(_frombinary_poppush, pushCount=1),  # NROUND[Wh]
  0x6F: _frombinary_invalid,
  0x70: f(_frombinary_poppush, popCount=2),  # WCVTP[]
  0x71: f(_frombinary_delta, prefix='P2'),  # DELTAP2[]
  0x72: f(_frombinary_delta, prefix='P3'),  # DELTAP3[]
  0x73: f(_frombinary_delta, prefix='C1'),  # DELTAC1[]
  0x74: f(_frombinary_delta, prefix='C2'),  # DELTAC2[]
  0x75: f(_frombinary_delta, prefix='C3'),  # DELTAC3[]
  0x76: _frombinary_poppush,  # SROUND[]
  0x77: _frombinary_poppush,  # S45ROUND[]
  0x78: f(_frombinary_unsupported, popCount=2),  # JROT[]
  0x79: f(_frombinary_unsupported, popCount=2),  # JROF[]
  0x7B: _frombinary_invalid,
  0x7F: _frombinary_poppush,  # AA[]
  0x80: f(_frombinary_poppush, popCount='loop'),  # FLIPPT[]
  0x81: f(_frombinary_poppush, popCount=2),  # FLIPRGON[]
  0x82: f(_frombinary_poppush, popCount=2),  # FLIPRGOFF[]
  0x83: _frombinary_invalid,
  0x84: _frombinary_invalid,
  0x85: _frombinary_poppush,  # SCANCTRL[]
  0x86: f(_frombinary_poppush, popCount=2),  # SDPVTL[r]
  0x87: f(_frombinary_poppush, popCount=2),  # SDPVTL[R]
  0x88: f(_frombinary_poppush, pushCount=1),  # GETINFO[]
  0x89: f(_frombinary_unsupported, popCount=1),  # IDEF[]
  0x8A: f(_frombinary_cmindex, relIndex=3, copy=False),  # ROLL[]
  0x8B: f(_frombinary_unsupported, popCount=2, pushCount=1),  # MAX[]
  0x8C: f(_frombinary_unsupported, popCount=2, pushCount=1),  # MIN[]
  0x8D: _frombinary_poppush,  # SCANTYPE[]
  0x8E: f(_frombinary_poppush, popCount=2),  # INSTCTRL[]
  0x8F: _frombinary_invalid,  # actually ADJUST[0]
  0x90: _frombinary_invalid,  # actually ADJUST[1]
  0x91: _frombinary_invalid,
  0x92: _frombinary_invalid,
  0x93: _frombinary_invalid,
  0x94: _frombinary_invalid,
  0x95: _frombinary_invalid,
  0x96: _frombinary_invalid,
  0x97: _frombinary_invalid,
  0x98: _frombinary_invalid,
  0x99: _frombinary_invalid,
  0x9A: _frombinary_invalid,
  0x9B: _frombinary_invalid,
  0x9C: _frombinary_invalid,
  0x9D: _frombinary_invalid,
  0x9E: _frombinary_invalid,
  0x9F: _frombinary_invalid,
  0xA0: _frombinary_invalid,
  0xA1: _frombinary_invalid,
  0xA2: _frombinary_unsupported,  # MAZDELTA1[]
  0xA3: _frombinary_unsupported,  # MAZDELTA2[]
  0xA4: _frombinary_unsupported,  # MAZDELTA3[]
  0xA5: _frombinary_unsupported,  # MAZMODE[]
  0xA6: _frombinary_unsupported,  # MAZSTROKE[]
  0xA7: _frombinary_unsupported,  # DELTAK1[]
  0xA8: _frombinary_unsupported,  # DELTAK2[]
  0xA9: _frombinary_unsupported,  # DELTAK3[]
  0xAA: _frombinary_unsupported,  # DELTAL1[]
  0xAB: _frombinary_unsupported,  # DELTAL2[]
  0xAC: _frombinary_unsupported,  # DELTAL3[]
  0xAD: _frombinary_unsupported,  # DELTAS1[]
  0xAE: _frombinary_unsupported,  # DELTAS2[]
  0xAF: _frombinary_unsupported,  # DELTAS3[]
  0xC0: _frombinary_poppush,  # MDRP[m<rGr]
  0xC1: _frombinary_poppush,  # MDRP[m<rBl]
  0xC2: _frombinary_poppush,  # MDRP[m<rWh]
  0xC4: _frombinary_poppush,  # MDRP[m<RGr]
  0xC5: _frombinary_poppush,  # MDRP[m<RBl]
  0xC6: _frombinary_poppush,  # MDRP[m<RWh]
  0xC8: _frombinary_poppush,  # MDRP[m>rGr]
  0xC9: _frombinary_poppush,  # MDRP[m>rBl]
  0xCA: _frombinary_poppush,  # MDRP[m>rWh]
  0xCC: _frombinary_poppush,  # MDRP[m>RGr]
  0xCD: _frombinary_poppush,  # MDRP[m>RBl]
  0xCE: _frombinary_poppush,  # MDRP[m>RWh]
  0xD0: _frombinary_poppush,  # MDRP[M<rGr]
  0xD1: _frombinary_poppush,  # MDRP[M<rBl]
  0xD2: _frombinary_poppush,  # MDRP[M<rWh]
  0xD4: _frombinary_poppush,  # MDRP[M<RGr]
  0xD5: _frombinary_poppush,  # MDRP[M<RBl]
  0xD6: _frombinary_poppush,  # MDRP[M<RWh]
  0xD8: _frombinary_poppush,  # MDRP[M>rGr]
  0xD9: _frombinary_poppush,  # MDRP[M>rBl]
  0xDA: _frombinary_poppush,  # MDRP[M>rWh]
  0xDC: _frombinary_poppush,  # MDRP[M>RBl]
  0xDD: _frombinary_poppush,  # MDRP[M>RGr]
  0xDE: _frombinary_poppush,  # MDRP[M>RWh]
  0xE0: f(_frombinary_poppush, popCount=2),  # MIRP[m<rGr]
  0xE1: f(_frombinary_poppush, popCount=2),  # MIRP[m<rBl]
  0xE2: f(_frombinary_poppush, popCount=2),  # MIRP[m<rWh]
  0xE3: _frombinary_invalid,
  0xE4: f(_frombinary_poppush, popCount=2),  # MIRP[m<RGr]
  0xE5: f(_frombinary_poppush, popCount=2),  # MIRP[m<RBl]
  0xE6: f(_frombinary_poppush, popCount=2),  # MIRP[m<RWh]
  0xE7: _frombinary_invalid,
  0xE8: f(_frombinary_poppush, popCount=2),  # MIRP[m>rGr]
  0xE9: f(_frombinary_poppush, popCount=2),  # MIRP[m>rBl]
  0xEA: f(_frombinary_poppush, popCount=2),  # MIRP[m>rWh]
  0xEB: _frombinary_invalid,
  0xEC: f(_frombinary_poppush, popCount=2),  # MIRP[m>RGr]
  0xED: f(_frombinary_poppush, popCount=2),  # MIRP[m>RBl]
  0xEE: f(_frombinary_poppush, popCount=2),  # MIRP[m>RWh]
  0xEF: _frombinary_invalid,
  0xF0: f(_frombinary_poppush, popCount=2),  # MIRP[M<rGr]
  0xF1: f(_frombinary_poppush, popCount=2),  # MIRP[M<rBl]
  0xF2: f(_frombinary_poppush, popCount=2),  # MIRP[M<rWh]
  0xF3: _frombinary_invalid,
  0xF4: f(_frombinary_poppush, popCount=2),  # MIRP[M<RGr]
  0xF5: f(_frombinary_poppush, popCount=2),  # MIRP[M<RBl]
  0xF6: f(_frombinary_poppush, popCount=2),  # MIRP[M<RWh]
  0xF7: _frombinary_invalid,
  0xF8: f(_frombinary_poppush, popCount=2),  # MIRP[M>rGr]
  0xF9: f(_frombinary_poppush, popCount=2),  # MIRP[M>rBl]
  0xFA: f(_frombinary_poppush, popCount=2),  # MIRP[M>rWh]
  0xFB: _frombinary_invalid,
  0xFC: f(_frombinary_poppush, popCount=2),  # MIRP[M>RBl]
  0xFD: f(_frombinary_poppush, popCount=2),  # MIRP[M>RGr]
  0xFE: f(_frombinary_poppush, popCount=2),  # MIRP[M>RWh]
  0xFF: _frombinary_invalid}

del f

def _glyphHelper(obj, **kwArgs):
    """
    Helper function that returns a generator over (start, length) pairs which
    identify locations of glyphIndex values in the string. Note that the actual
    argument passed in here is ignored.
    
    The following keyword arguments are supported:
    
        origObj     The original Hints object (this being passed in is
                    automatically handled by the protocol glyphsRenumbered()
                    method).
    
    >>> obj = Hints("OFFSET[], 123, -50, 50")
    >>> for t in _glyphHelper(None, origObj=obj):
    ...   print(t)
    (10, 3)
    """
    
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'glyphIndex':
            yield (start, stop - start)

def _pointHelper(obj, **kwArgs):
    """
    Helper function that returns a generator over (start, length, glyphIndex)
    triples which identify locations of pointIndex values in the string. Note
    that the actual argument passed in here is ignored.
    
    The following keyword arguments are supported:
    
        glyphIndex  The glyph index associated with the specified point index
                    values. This is used as a key into the mapData that is
                    passed into pointsRenumbered(); the protocol handles this.
        
        origObj     The original Hints object (this being passed in is
                    automatically handled by the protocol pointsRenumbered()
                    method).
    
    >>> obj = Hints("SLOOP[], 2  IP[], 14, 6")
    >>> for t in sorted(_pointHelper(None, origObj=obj, glyphIndex=39)):
    ...   print(t)
    (18, 2, 39)
    (22, 1, 39)
    """
    
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'pointIndex':
            yield (start, stop - start, kwArgs.get('glyphIndex', None))

def _storageHelper(obj, **kwArgs):
    """
    Helper function that returns a generator over (start, length) pairs which
    identify locations of storageIndex values in the string. Note that the
    actual argument passed in here is ignored.
    
    The following keyword arguments are supported:
    
        origObj     The original Hints object (this being passed in is
                    automatically handled by the protocol storageRenumbered()
                    method).
    
    >>> obj = Hints("RS[], 9")
    >>> for t in _storageHelper(None, origObj=obj):
    ...   print(t)
    (6, 1)
    """
    
    origObj = kwArgs['origObj']
    
    for (start, stop), kind in origObj.locInfo.items():
        if kind == 'storageIndex':
            yield (start, stop - start)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Hints(str, metaclass=textmeta.FontDataMetaclass):
    """
    Objects representing entire low-level (i.e. TSI1-style) hint streams. These
    are Unicode strings.
    
    Since we get the FDEF analysis from the binary (where it's easier to do
    things like separating out the IF-streams), this class can also be used to
    capture code in the FPGM portion of the TSI1 object. This basically allows
    us to completely ignore IF-ELSE-EIF blocks, since #PUSHOFF is almost always
    in effect for these, and so usage is strictly localized.
    """
    
    textSpec = dict(
        text_findcvtsfunc = _cvtHelper,
        text_findfdefsfunc = _fdefHelper,
        text_findglyphsfunc = _glyphHelper,
        text_findpointsfunc = _pointHelper,
        text_findstoragefunc = _storageHelper)
    
    attrSpec = dict(
        locInfo = dict(
            attr_followsprotocol = True,
            attr_showonlyiftrue = True))
    
    #
    # Methods
    #
    
    def __new__(cls, s, **kwArgs):
        r"""
        Create and return a new Hints. Keyword arguments are:
        
            analysis
            cvtCase
            editor
            extraInfo
        
        >>> d = collections.defaultdict(dict)
        >>> obj = Hints('SRP2[], 9\nMIAP[R], 12, 23\n', extraInfo=d)
        >>> obj.pprint()
        SRP2[], 9
        MIAP[R], 12, 23
        locInfo:
          (8, 9): pointIndex
          (19, 21): pointIndex
          (23, 25): cvtIndex
        
        >>> for key in sorted(obj.extraInfo):
        ...   print(key)
        ...   dSub = obj.extraInfo[key]
        ...   for subKey in sorted(dSub):
        ...     print("  ", subKey, dSub[subKey])
        (8, 9)
           argIndex 0
           inY False
           opString SRP2
        (19, 21)
           argIndex 1
           inY False
           opString MIAP
        (23, 25)
           argIndex 0
           inY False
           opString MIAP
        
        >>> obj.cvtsRenumbered(oldToNew={23: 8, 8: 23}).pprint()
        SRP2[], 9
        MIAP[R], 12, 8
        locInfo:
          (8, 9): pointIndex
          (19, 21): pointIndex
          (23, 24): cvtIndex
        
        >>> obj = Hints('DLTP1[(12 @4 -8)(12 @5 -4)]\nDLTP3[(9 @1 6)]\n')
        >>> obj.pprint()
        DLTP1[(12 @4 -8)(12 @5 -4)]
        DLTP3[(9 @1 6)]
        locInfo:
          (7, 9): pointIndex
          (11, 12): deltaCodedPPEM_13
          (13, 15): deltaCodedShift_-1.0
          (17, 19): pointIndex
          (21, 22): deltaCodedPPEM_14
          (23, 25): deltaCodedShift_-0.5
          (35, 36): pointIndex
          (38, 39): deltaCodedPPEM_42
          (40, 41): deltaCodedShift_0.75
        
        >>> d = {0: ('pointIndex', None), 1: None, 2: ('cvtIndex', None)}
        >>> d = {14: (d, 3, 3, (), {}, 0)}
        >>> obj = Hints('CALL[], 11, 22, 33, 14\n', analysis=d)
        >>> obj.pprint()
        CALL[], 11, 22, 33, 14
        locInfo:
          (8, 10): cvtIndex
          (16, 18): pointIndex
          (20, 22): fdefIndex
        
        >>> obj = Hints('#PUSH, 19\nRS[]\n')
        >>> obj.pprint()
        #PUSH, 19
        RS[]
        locInfo:
          (7, 9): storageIndex
        
        In interpreting the TSI1 cvt object, pass in cvtCase=True:
        
        >>> obj = Hints('13: 129 0x1093\n14: -55\n', cvtCase=True)
        >>> obj.pprint()
        13: 129 0x1093
        14: -55
        locInfo:
          (0, 2): cvtIndex
          (4, 7): FUnits
          (15, 17): cvtIndex
          (19, 22): FUnits
        """
        
        r = str.__new__(cls, s)
        
        if 'extraInfo' in kwArgs:
            r.extraInfo = kwArgs['extraInfo']
        
        if 'locInfo' in kwArgs:
            r.locInfo = kwArgs['locInfo']
            return r
        
        r.locInfo = LocInfo()  # suborn __init__'s role here, since we need it
        
        if kwArgs.get('cvtCase', False):
            r._makeLocInfo_CVT(**kwArgs)
        
        else:
            r.state = {}
            r._getOrMakeAnalysis(**kwArgs)
            r._makeLocInfo(**kwArgs)
            del r.state
        
        if r.locInfo and ((-1, -1) in r.locInfo):
            del r.locInfo[(-1, -1)]
        
        if r.locInfo and (None in r.locInfo):
            del r.locInfo[None]
        
        return r
    
    def _cmIndex(self, t, **kwArgs):
        """
        """
        
        stk = self.state['stack']
        
        if 'relIndex' in kwArgs:
            n = kwArgs['relIndex']
        else:
            n = stk.pop()[0]
        
        assert n
        moveObj = stk[-n]
        
        if not kwArgs['copy']:
            del stk[-n]
        
        stk.append(moveObj)
    
    def _expandKinds(self, oldKinds):
        """
        Uses self.state['loop'] to expand any 'loop' constructs. Returns a new
        tuple with the expanded results.
        """
        
        if not oldKinds:
            return ()
        
        if oldKinds[0] == 'all':
            return (None,) * len(self.state['stack'])
        
        r = []
        i = 0
        lp = self.state['loop']
        
        while i < len(oldKinds):
            s = oldKinds[i]
            
            if s == 'loop':
                r.extend([oldKinds[i + 1]] * lp)
                i += 1
            
            else:
                r.append(s)
            
            i += 1
        
        return tuple(r)
    
    def _getOrMakeAnalysis(self, **kwArgs):
        """
        Fills in self.state['fdefAnalysis'].
        """
        
        a = {}
        
        if 'analysis' in kwArgs:
            a = kwArgs['analysis']
        
        elif 'editor' in kwArgs:
            e = kwArgs['editor']
            
            if e.reallyHas('fpgm'):
                a = analyzer.analyzeFPGM(e.fpgm, useDictForm=True)
        
        self.state['fdefAnalysis'] = a
    
    def _handleCALL(self, t, **kwArgs):
        """
        """
        
        if t[2][0]:
            self._push(*t[2])
        
        stk = self.state['stack']
        a = self.state['fdefAnalysis']
        wo = kwArgs.get('extraInfo', collections.defaultdict(dict))
        fdefIndex, ssObj = stk.pop()
        opString = "%s %d" % (kwArgs['opString'], fdefIndex)
        
        if fdefIndex not in a:
            raise ValueError("Unknown function: %d" % (fdefIndex,))
        
        self.locInfo[ssObj] = 'fdefIndex'
        wo[ssObj]['opString'] = opString
        dIn, inCount, inDeepest, ops, dOut, outCount = a[fdefIndex]
        
        if kwArgs.get('useCount', False):
            # The following is a hack to get around FDEF 63, which pops from
            # a seemingly empty stack.
            try:
                count = stk.pop()[0]
            except IndexError:
                count = 1
        
        else:
            count = 1
        
        ssSet = set()
        
        while count:
            count -= 1
        
            for i, t in enumerate(reversed(stk[-inCount:])):
                if (t is not None) and (dIn.get(i, None) is not None):
                    ssObj = t[1]
                    ssSet.add(ssObj)
                    self.locInfo[ssObj] = dIn[i][0]
                    wo[ssObj]['opString'] = opString
                    wo[ssObj]['argIndex'] = i
                    wo[ssObj]['inY'] = self.state['inY']
        
            if ops:
                for op, start, stop in ops:
                    if op == 'equal':
                        continue
                
                    if op == 'delete':
                        del stk[start:stop]
        
            else:
                if inCount:
                    del stk[-inCount:]
        
            if outCount:
                stk.extend(((0, StartStop(-1, -1)),) * outCount)
        
        if len(ssSet) > 1:
            for ssObj in ssSet:
                wo[ssObj]['otherArgs'] = frozenset(ssSet - {ssObj})
        
        self.state['loop'] = 1
    
    def _handleDelta(self, t, **kwArgs):
        """
        """
        
        globalStart = t[1][1]
        li = self.locInfo
        band = self.state['deltaBase'] + ((kwArgs['band'] - 1) * 16)
        fBase = 1.0 / (2.0 ** self.state['deltaShift'])
        kind = kwArgs.get('kind', 'pointIndex')
        wo = kwArgs.get('extraInfo', collections.defaultdict(dict))
        opString = kwArgs['opString']
        ssSet = set()
        argIndex = 0
        
        for m in PAT_DELTA.finditer(t[1][0]):
            start = globalStart + m.start(1)
            stop = globalStart + m.end(1)
            ssObj = StartStop(start, stop)
            ssSet.add(ssObj)
            li[ssObj] = kind
            wo[ssObj]['opString'] = opString
            wo[ssObj]['argIndex'] = argIndex
            wo[ssObj]['inY'] = self.state['inY']
            
            start = globalStart + m.start(2)
            stop = globalStart + m.end(2)
            ssObj = StartStop(start, stop)
            ssSet.add(ssObj)
            li[ssObj] = 'deltaCodedPPEM_%d' % (int(m.group(2)) + band,)
            wo[ssObj]['opString'] = opString
            wo[ssObj]['argIndex'] = argIndex + 1
            wo[ssObj]['inY'] = self.state['inY']
            
            if m.group(4):
                start = globalStart + m.start(3)
                stop = globalStart + m.end(4)
                ssObj = StartStop(start, stop)
                ssSet.add(ssObj)
                num = float(m.group(3))
                den = float(m.group(4)[1:])
                li[ssObj] = 'deltaCodedShift_%s' % (num / den,)
                wo[ssObj]['opString'] = opString
                wo[ssObj]['argIndex'] = argIndex + 2
                wo[ssObj]['inY'] = self.state['inY']
            
            else:
                start = globalStart + m.start(3)
                stop = globalStart + m.end(3)
                ssObj = StartStop(start, stop)
                ssSet.add(ssObj)
                li[ssObj] = 'deltaCodedShift_%s' % (int(m.group(3)) * fBase,)
                wo[ssObj]['opString'] = opString
                wo[ssObj]['argIndex'] = argIndex + 2
                wo[ssObj]['inY'] = self.state['inY']
            
            argIndex += 3
        
        if len(ssSet) > 1:
            for ssObj in ssSet:
                wo[ssObj]['otherArgs'] = frozenset(ssSet - {ssObj})
        
        self.state['loop'] = 1
    
    def _handleDepth(self, t, **kwArgs):
        """
        """
        
        stk = self.state['stack']
        n = len(stk)
        stk.append((n, None))
    
    def _handleEIF(self, t, **kwArgs):
        """
        """
        
        self.state['stackStack'].pop()
        self.state['loop'] = 1
    
    def _handleELSE(self, t, **kwArgs):
        """
        """
        
        self.state['stack'] = self.state['stackStack'][-1]
        self.state['loop'] = 1
    
    def _handleFDEF(self, t, **kwArgs):
        """
        """
        
        if t[2][0]:
            self._push(*t[2])
        
        stk = self.state['stack']
        a = self.state['fdefAnalysis']
        fdefIndex, ssObj = stk.pop()
        wo = kwArgs.get('extraInfo', collections.defaultdict(dict))
        opString = kwArgs['opString']
        #print("Starting FDEF", fdefIndex)
        
        if fdefIndex not in a:
            raise ValueError("Unknown function: %d" % (fdefIndex,))
        
        self.locInfo[ssObj] = 'fdefIndex'
        wo[ssObj]['opString'] = opString
        dIn, inCount, inDeepest, ops, dOut, outCount = a[fdefIndex]
        
        if inDeepest:
            stk.extend(((0, StartStop(-1, -1)),) * inDeepest)
    
    def _handleIF(self, t, **kwArgs):
        """
        """
        
        self.state['stack'].pop()
        self.state['stackStack'].append(list(self.state['stack']))
        self.state['loop'] = 1
    
    def _handleSVTCA(self, t, **kwArgs):
        """
        """
        
        self.state['inY'] = (t[1][0] in {'y', 'Y'})
    
    def _makeLocInfo(self, **kwArgs):
        """
        Runs the analysis and fills in self.locInfo.
        """
        
        decommented = TSIUtilities.stripComments(str(self))[0]
        dFound = {}
        
        for m in PAT_OP.finditer(decommented):
            t = tuple((m.group(i), m.start(i)) for i in (1, 2, 3))
            dFound[m.start(1)] = t
        
        for m in PAT_PUSH.finditer(decommented):
            if not m.group(2):
                continue
            
            t = ((m.group(1), m.start(1)), ('', 0), (m.group(2), m.start(2)))
            dFound[m.start(1)] = t
        
        self.state['stack'] = []
        self.state['stackStack'] = []
        self.state['loop'] = 1
        self.state['deltaShift'] = 3
        self.state['deltaBase'] = 9
        self.state['inY'] = False
        self._run(dFound, **kwArgs)
    
    def _makeLocInfo_CVT(self, **kwArgs):
        """
        """
        
        decommented = TSIUtilities.stripComments(str(self))[0]
        li = self.locInfo
        
        for m in PAT_CVT.finditer(decommented):
            ss = StartStop(m.start(1), m.end(1))
            li[ss] = 'cvtIndex'
            ss = StartStop(m.start(2), m.end(2))
            li[ss] = 'FUnits'
    
    def _popPush(self, t, **kwArgs):
        """
        """
        
        if t[2][0]:
            self._push(*t[2])
        
        stk = self.state['stack']
        ss = kwArgs.get('setState', None)
        wo = kwArgs.get('extraInfo', collections.defaultdict(dict))
        opString = kwArgs['opString']
        
        if ss is not None:
            if len(stk) < 1:
                raise IndexError("Stack underflow!")
        
            value, ssObj = stk.pop()
            self.state[ss] = value
            wo[ssObj]['opString'] = opString
            wo[ssObj]['isState'] = True
            return
        
        if 'niladic' in kwArgs:
            
            # As a special case, niladic opcodes like FLIPOFF[] need to be
            # tracked in order to ascertain their 'prep' presence and effects,
            # in order to notify the user about potential graphics-state
            # inconsistencies.
            #
            # To handle this, we make annotations in the extraInfo but not in
            # the actual locInfo. The annotation will use a zero-length
            # StartStop as a clue that this is a special entry (which can also
            # be deduced because the StartStop won't appear in the locInfo).
            
            ssObj = StartStop(t[0][1], t[0][1])  # zero-length
            wo[ssObj]['opString'] = opString
            wo[ssObj]['argIndex'] = -1
            wo[ssObj]['inY'] = self.state['inY']
            wo[ssObj]['isState'] = True
            return
        
        if 'monadic' in kwArgs:
            value, ssObj = stk[-1]
            stk[-1] = (kwArgs['monadic'](value), ssObj)
            return
        
        if 'dyadic' in kwArgs:
            (v2, ss2) = stk.pop()
            (v1, ss1) = stk.pop()
            # We're arbitrarily choosing ss1 here; I don't think it matters...
            stk.append((kwArgs['dyadic'](v1, v2), ss1))
            return
        
        kinds = self._expandKinds(kwArgs.get('kinds', ()))
        
        if len(stk) < len(kinds):
            raise IndexError("Stack underflow!")
        
        if kinds:
            ssSet = set()
            
            for i, stackEntry in enumerate(stk[-len(kinds):]):
                value, ssObj = stackEntry
            
                if kinds[i] is not None:
                    self.locInfo[ssObj] = kinds[i]
                    wo[ssObj]['opString'] = opString
                    wo[ssObj]['argIndex'] = len(kinds) - 1 - i
                    wo[ssObj]['inY'] = self.state['inY']
                    
                    if kwArgs.get('isState', False):
                        wo[ssObj]['isState'] = True
        
            del stk[-len(kinds):]
            
            if len(ssSet) > 1:
                for ssObj in ssSet:
                    wo[ssObj]['otherArgs'] = frozenset(ssSet - {ssObj})
        
        outCount = kwArgs.get('outCount', 0)
        
        if outCount:
            stk.extend(((0, None),) * outCount)
        
        self.state['loop'] = 1
    
    def _push(self, s, startOffset):
        """
        """
        
        stk = self.state['stack']
        
        for m in PAT_NUMBER.finditer(s):
            start = m.start(1) + startOffset
            stop = m.end(1) + startOffset
            ssObj = StartStop(start, stop)
            f = (float if '.' in m.group(1) else int)
            stk.append((f(m.group(1)), ssObj))
    
    def _renumberHelper(self, func, *args, **kwArgs):
        td = {}
        kwArgs['trackDeltas'] = td
        r = func(self, *args, **kwArgs)
        
        cumulDelta = 0
        liOld = r.locInfo
        liNew = {}
        
        for ssOld in sorted(liOld):
            tTest = (ssOld.start, ssOld.stop - 1)
            
            if tTest in td:
                ssNew = StartStop(
                  ssOld.start + cumulDelta,
                  ssOld.stop + cumulDelta + td[tTest])
                
                cumulDelta += td[tTest]
            
            else:
                ssNew = StartStop(
                  ssOld.start + cumulDelta,
                  ssOld.stop + cumulDelta)
            
            liNew[ssNew] = liOld[ssOld]
        
        r.locInfo.clear()
        r.locInfo.update(liNew)
        return r
    
    def _run(self, dFound, **kwArgs):
        """
        """
        
        if hasattr(self, 'extraInfo'):
            dBase = {'extraInfo': self.extraInfo}
        else:
            dBase = {}
        
        for startOffset in sorted(dFound):
            t = dFound[startOffset]
            opString = t[0][0]
            
            if opString in DISPATCH:
                mString, kwd = DISPATCH[opString]
                d = dBase.copy()
                d['opString'] = opString
                d.update(kwd)
                getattr(self, mString)(t, **d)
    
    def annotate(self, kind, **kwArgs):
        r"""
        Returns a string with occurrences of kind highlighted.
        
        >>> obj = Hints('SRP2[], 9\nMIAP[R], 12, 23\n')
        >>> obj.pprint()
        SRP2[], 9
        MIAP[R], 12, 23
        locInfo:
          (8, 9): pointIndex
          (19, 21): pointIndex
          (23, 25): cvtIndex
        
        >>> print(obj.annotate('pointIndex'), end='')
        SRP2[], >>>9<<<
        MIAP[R], >>>12<<<, 23
        
        >>> print(obj.annotate('cvtIndex'), end='')
        SRP2[], 9
        MIAP[R], 12, >>>23<<<
        """
        
        g = (t for t, k in self.locInfo.items() if k==kind)
        annotationPoints = sorted(g)
        sv = list(self)
        
        for start, stop in reversed(annotationPoints):
            sv[stop:stop] = ['<'] * 3
            sv[start:start] = ['>'] * 3
        
        return ''.join(sv)
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary content for the Hints object to the specified writer.
        Note that this is just a conversion of the string into ASCII; if you
        need to convert an object into actual binary TrueType instructions,
        use the toTTBinary() method.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        w.addString(self.encode('utf-8'))
    
    def cvtsRenumbered(self, **kwArgs):
        """
        A front end for the metaclass's method, using the trackDeltas feature
        to make changes to locInfo after the renumbering is done.
        
        >>> s = "abc 12 def 34"
        >>> li = LocInfo({
        ...   StartStop(4, 6): 'cvtIndex',
        ...   StartStop(11, 13): 'cvtIndex'})
        >>> obj = Hints(s, locInfo=li)
        >>> obj.pprint()
        abc 12 def 34
        locInfo:
          (4, 6): cvtIndex
          (11, 13): cvtIndex
        
        >>> obj.cvtsRenumbered(cvtDelta=1000).pprint()
        abc 1012 def 1034
        locInfo:
          (4, 8): cvtIndex
          (13, 17): cvtIndex
        """
        
        return self._renumberHelper(textmeta.M_cvtsRenumbered, **kwArgs)
    
    def fdefsRenumbered(self, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(textmeta.M_fdefsRenumbered, **kwArgs)
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(
          textmeta.M_glyphsRenumbered,
          oldToNew,
          **kwArgs)
    
    def pointsRenumbered(self, mapData, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(
          textmeta.M_pointsRenumbered,
          mapData,
          **kwArgs)
    
    def storageRenumbered(self, **kwArgs):
        """
        See cvtsRenumbered() above for a description why these are all needed.
        """
        
        return self._renumberHelper(textmeta.M_storageRenumbered, **kwArgs)
    
    @classmethod
    def frombinary_c(cls, cvtObj, **kwArgs):
        """
        Given a fontio3 CVT object, create and return a Hints object.
        """
        
        sv = ["%d: %d" % (i, n) for i, n in enumerate(cvtObj)]
        #sv.append('')  # ensure a final linefeed gets written
        return cls('\r'.join(sv), cvtCase=True, **kwArgs)
    
    @classmethod
    def frombinary_f(cls, oldHintObj, fdefIndex, **kwArgs):
        """
        Given a fontio3.hints.hints_tt.Hints object, create and return a Hints
        object. Note that this code should be used for FDEFs only.
        """
        
        sv = ['FDEF[], %d' % (fdefIndex,), '#BEGIN', '#PUSHOFF']
        debugPrint = kwArgs.get('debugPrint', False)
        nameMap = NAMEMAP
        
        for i, op in enumerate(oldHintObj):
            svPiece = []
            
            if op.isPush:
                for j, value in enumerate(op):
                    svPiece.append("#PUSH, %d" % (value,))
            
            else:
                svPiece.append(nameMap[op])
            
            sv.extend(svPiece)
        
        _frombinary_postprocess(sv, debugPrint=debugPrint)  # works in-place
        sv.extend(['#END', '#PUSHON', 'ENDF[]'])
        
        if debugPrint:
            print()
            print("Final stream:")
            
            for s in sv:
                print("   ", s)
        
        #sv.append('')  # ensure a final linefeed gets written
        return cls('\r'.join(sv), **kwArgs)
    
    @classmethod
    def frombinary_gp(cls, oldHintObj, **kwArgs):
        """
        Given a fontio3.hints.hints_tt.Hints object, create and return a Hints
        object. Note that this code should not be used for FDEFs; just for
        glyph hints or other self-contained streams of hints (like 'prep').
        
        >>> Hints.frombinary_gp(_makeOldHints(0)).pprint()
        SPVTL[r], 9, 5
        locInfo:
          (10, 11): pointIndex
          (13, 14): pointIndex
        
        >>> Hints.frombinary_gp(_makeOldHints(1)).pprint()
        SLOOP[], 5
        
        >>> Hints.frombinary_gp(_makeOldHints(2)).pprint()
        #PUSHOFF
        #PUSH, 42
        POP[]
        
        >>> a = {49: ({1: ('cvtIndex', ())}, 3, 3, None, {}, 0)}
        >>> hOld = _makeOldHints(3)
        >>> Hints.frombinary_gp(hOld, analysis=a).pprint()
        CALL[], 25, 5, 15, 49
        locInfo:
          (12, 13): cvtIndex
          (19, 21): fdefIndex
        
        >>> Hints.frombinary_gp(_makeOldHints(4)).pprint()
        DLTP1[(54 @0 8)(54 @1 8)]
        locInfo:
          (7, 9): pointIndex
          (11, 12): deltaCodedPPEM_9
          (13, 14): deltaCodedShift_1.0
          (16, 18): pointIndex
          (20, 21): deltaCodedPPEM_10
          (22, 23): deltaCodedShift_1.0
        """
        
        sv = ['#PUSHOFF']
        state = {}
        stk = state['stack'] = []
        state['stackStack'] = []
        state['loop'] = 1
        state['fdefAnalysis'] = kwArgs.get('analysis', {})
        state['ifDepth'] = 0
        state['pushOn'] = False
        state['pushesToDelete'] = set()
        debugPrint = kwArgs.get('debugPrint', False)
        inFirstPushes = True
        nameMap = NAMEMAP
        
        for i, op in enumerate(oldHintObj):
            svPiece = []
            
            if op.isPush():
                if (not inFirstPushes) and state['pushOn']:
                    svPiece.append("#PUSHOFF")
                    state['pushOn'] = False
                    extra = 1
                
                else:
                    extra = 0
                
                for j, value in enumerate(op.data):
                    stk.append((value, len(sv) + j + extra))
                    svPiece.append("#PUSH, %d" % (value,))
                
                opString = '(PUSH)'
            
            else:
                inFirstPushes = False
                opString = nameMap[op.opcode]
                v = _frombinary_dostack(op.opcode, state)
                svPiece.extend(v)
            
            if debugPrint:
                print()
                print("PC", i)
                print("    Hint:", opString)
                print("   Stack:", state['stack'])
                print("     Out:", svPiece)
                print("  PushOn:", state['pushOn'])
                print()
            
            sv.extend(svPiece)
        
        if debugPrint:
            print("Main: before removing pushesToDelete")
        
            for i, s in enumerate(sv):
                print("[%04d] %s" % (i, s))
        
        for i in sorted(state['pushesToDelete'], reverse=True):
            del sv[i]
        
        _frombinary_postprocess(sv, **kwArgs)  # works in-place
        
        if debugPrint:
            print()
            print("Final stream:")
            
            for s in sv:
                print("   ", s)
        
        #sv.append('')  # ensure a final linefeed gets written
        return cls('\r'.join(sv), **kwArgs)
    
    @classmethod
    def fromparts(cls, parts, **kwArgs):
        """
        Given a iterable over Hints objects, combine them into a single Hints
        object and return it. This code adjusts all the locInfo offsets to
        match the new, single aggregated string.
        
        If any element of parts has an associated extraInfo attribute, it will
        be renumbered in an extraInfo that is put into the final returned
        object.
        """
        
        parts = list(parts)  # might be an iterator, and we iterate multiply
        cumulLen = 0
        sv = []
        li = LocInfo()
        
        if any(hasattr(part, 'extraInfo') for part in parts):
            ei = collections.defaultdict(dict)
        else:
            ei = None
        
        for part in parts:
            sRaw = str(part.encode('utf-8'), 'utf-8')
            
            if hasattr(part, 'extraInfo'):
                eiOld = part.extraInfo
                
                for ssOld, s in part.locInfo.items():
                    ssNew = StartStop(ssOld[0] + cumulLen, ssOld[1] + cumulLen)
                    li[ssNew] = s
                    ei[ssNew] = eiOld[ssOld].copy()
            
            else:
                for ssOld, s in part.locInfo.items():
                    ssNew = StartStop(ssOld[0] + cumulLen, ssOld[1] + cumulLen)
                    li[ssNew] = s
            
            sv.append(sRaw)
            cumulLen += (len(sRaw) + 1)  # the +1 is for the \r added below...
        
        if ei is not None:
            return cls('\r'.join(sv), locInfo=li, extraInfo=ei, **kwArgs)
        
        else:
            return cls('\r'.join(sv), locInfo=li, **kwArgs)
    
    def toTTBinary(self, **kwArgs):
        r"""
        Returns a binary string with the actual compiled hints.
        
        >>> obj = Hints("DLTP1[(18 @0 8)(18 @1 8)]")
        >>> utilities.hexdump(obj.toTTBinary())
               0 | B40F 121F 1202 5D                        |......]         |
        """
        
        return self.toTTBinary_fromRawString(self, **kwArgs)
    
    def toTTBinary_cvt(self, **kwArgs):
        r"""
        Like toTTBinary(), but for CVT tables.
        
        >>> s = "12: -50  /* 4:4 */\r  13  :90\r"
        >>> obj = Hints(s, cvtCase=True)
        >>> obj.pprint()
        12: -50  /* 4:4 */
          13  :90
        locInfo:
          (0, 2): cvtIndex
          (4, 7): FUnits
          (21, 23): cvtIndex
          (26, 28): FUnits
        
        >>> utilities.hexdump(obj.toTTBinary_cvt())
               0 | 0000 0000 0000 0000  0004 0000 0000 0000 |................|
              10 | 0000 0000 0000 0000  FFCE 005A           |...........Z    |
        """
        
        decommented = TSIUtilities.stripComments(self)[0]
        d = {}
        
        for m in PAT_CVT.finditer(self):
            d[int(m.group(1))] = int(m.group(2))
        
        w = writer.LinkedWriter()
        w.addGroup("h", (d.get(i, 0) for i in range(1 + max(d))))
        return w.binaryString()
    
    def toTTBinary_fpgm(self, **kwArgs):
        """
        """
        
        decommented = TSIUtilities.stripComments(self)[0]
        state = 'ground'
        bss = {}
        
        for line in decommented.splitlines():
            line = line.strip()
            
            if state == 'ground':
                if not line.startswith("FDEF"):
                    raise ValueError("FDEF statement not found!")
                
                comma = line.index(',')
                fdefIndex = int(line[comma+1:])
                state = "awaiting #BEGIN"
            
            elif state == "awaiting #BEGIN":
                if not line.startswith("#BEGIN"):
                    continue
                
                sv = []
                state = "awaiting ENDF"
            
            elif state == "awaiting ENDF":
                if not line.startswith("ENDF[]"):
                    sv.append(line)
                    continue
                
                bss[fdefIndex] = self.toTTBinary_fromRawString('\r'.join(sv))
                del fdefIndex
                del sv
                state = "ground"
        
        allIndices = sorted(bss)
        sv = [opcode_tt.Opcode_push(reversed(allIndices)).binaryString()]
        
        for fdefIndex in allIndices:
            sv.append(bytes([0x2C]))
            sv.append(bss[fdefIndex])
            sv.append(bytes([0x2D]))
        
        return b''.join(sv)
    
    @staticmethod
    def toTTBinary_fromRawString(s, **kwArgs):
        stackPart = []  # just values, not the associated PUSH opcodes...
        hintPart = []
        insertPushAt = 0
        decommented = TSIUtilities.stripComments(s)[0]
        pushOn = True
        Op = opcode_tt.Opcode_push
        INM = INVNAMEMAP
        markFirstPush = False
        ignores = {"#BEGIN", "#END", "OFFSET", "SOFFSET", "USEMYMETRICS"}
        
        for line in decommented.splitlines():
            line = line.strip()
            
            if not line:
                continue
            
            if line.startswith("#PUSHON"):
                if not pushOn:
                    pushOn = True
                    markFirstPush = True
            
            elif line.startswith("#PUSHOFF"):
                if pushOn:
                    pushOn = False
                    
                    if stackPart:
                        hintPart.insert(
                          insertPushAt,
                          Op(reversed(stackPart)).binaryString())
                        
                        stackPart[:] = []
            
            elif any(line.startswith(s) for s in ignores):
                continue
            
            else:
                try:
                    comma = line.index(',')
                except ValueError:
                    comma = None
                
                if line.startswith("#PUSH"):
                    assert (not pushOn)
                    assert (comma is not None)
                    obj = Op(int(s.strip()) for s in line[comma+1:].split(','))
                    hintPart.append(obj.binaryString())
                
                elif line.startswith("DLT") or line.startswith("DELTA"):
                    vRaw = []
                    
                    for m in PAT_LOW_DELTA.finditer(line):
                        vRaw.append((
                          int(m.group(1)),
                          int(m.group(2)),
                          int(m.group(3))))
                    
                    v = []
                    
                    for pt, ppem, delta in sorted(vRaw):
                        delta += (7 + (delta < 0))
                        v.append(ppem * 16 + delta)
                        v.append(pt)
                    
                    v.append(len(vRaw))
                    
                    if pushOn and markFirstPush:
                        insertPushAt = len(hintPart)
                        markFirstPush = False
                    
                    stackPart.extend(reversed(v))
                    hintPart.append(bytes([INM[line[:line.index('[')] + '[]']]))
                
                elif comma is not None:
                    v = [int(s.strip()) for s in line[comma+1:].split(',')]
                    
                    if pushOn:
                        if markFirstPush:
                            insertPushAt = len(hintPart)
                            markFirstPush = False
                        
                        stackPart.extend(reversed(v))
                    
                    else:
                        hintPart.append(Op(v).binaryString())
                    
                    hintPart.append(bytes([INM[line[:comma]]]))
            
                elif line in INM:
                    hintPart.append(bytes([INM[line]]))
            
                else:
                    raise ValueError("Unknown hint: '%s'" % (line,))
        
        if pushOn and stackPart:
            assert (not markFirstPush)
            hintPart.insert(insertPushAt, Op(reversed(stackPart)).binaryString())
        
        return b''.join(hintPart)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    
    def _makeOldHints(n):
        from fontio3.hints import hints_tt
        
        fh = utilities.fromhex
        fb = hints_tt.Hints.frombytes
        
        if n == 0:
            r = fb(fh("B1 09 05 06"))
        elif n == 1:
            r = fb(fh("B0 05 17"))
        elif n == 2:
            r = fb(fh("B0 2A 21"))
        elif n == 3:
            r = fb(fh("B3 19 05 0F 31 2B"))
        elif n == 4:
            r = fb(fh("B4 1F 36 0F 36 02 5D"))
        
        return r

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

