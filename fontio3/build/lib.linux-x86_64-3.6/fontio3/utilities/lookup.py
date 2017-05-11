#
# lookup.py
#
# Copyright © 2011-2013, 2015-2016 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities to help in producing the smallest possible AAT-style LookupTable for
a given dict mapping glyph indices to some other numeric value (other glyph
indices, class indices, etc.)
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities, utilitiesbackend
from fontio3.fontdata import mapmeta
from fontio3.utilities import bsh, span, valassist, writer, walker

# -----------------------------------------------------------------------------

#
# Public functions
#

def bestFromDict(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, returns a binary
    string representing the smallest lookup table describing the dict's
    contents.
    
    The following keyword arguments are supported:
    
        logger              A logger (optional) to which messages may be
                            posted. If no logger is provided and a message
                            would otherwise have been posted at the ERROR
                            level, then a ValueError will be raised instead.
    
        noGaps              A Boolean, default False. If True, the keys will be
                            checked first to make sure there are no gaps in
                            coverage; if such gaps exist, then formats 0 and 8
                            will not be tried, and format 4 will have the
                            format4NoGaps flag forced True.
        
        preferredFormat     A number which will force the format; this disables
                            the normal optimization.
        
        sentinelValue       A numeric value to be used as the sentinel output
                            value for the final 0xFFFF entry. Default is
                            0xFFFF. The sentinel will be emitted for formats
                            2, 4, and 6.
    
    Format 0 will be chosen for very small fonts with low glyph indices:
    
    >>> d = {0: 4, 1: 2}
    >>> utilities.hexdump(bestFromDict(d))
           0 | 0000 0004 0002                           |......          |
    
    Format 2 works best when there's lots of repeated values in contiguous
    groupings of glyphs:
    
    >>> d[23] = d[24] = d[25] = d[26] = d[27] = 5
    >>> utilities.hexdump(bestFromDict(d, sentinelValue=1))
           0 | 0002 0006 0003 000C  0001 0006 0000 0000 |................|
          10 | 0004 0001 0001 0002  001B 0017 0005 FFFF |................|
          20 | FFFF 0001                                |....            |
    
    Format 4 is useful for contiguous ranges of glyphs with varying mapped
    values:
    
    >>> d = {i: 4 + (i % 2) for i in range(50, 70)}
    >>> d.update({i: 4 + (i % 2) for i in range(150, 170)})
    >>> utilities.hexdump(bestFromDict(d))
           0 | 0004 0006 0002 000C  0001 0000 0045 0032 |.............E.2|
          10 | 001E 00A9 0096 0046  FFFF FFFF FFFF 0004 |.......F........|
          20 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
          30 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
          40 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
          50 | 0005 0004 0005 0004  0005 0004 0005 0004 |................|
          60 | 0005 0004 0005 0004  0005 0004 0005      |..............  |
    
    Format 6 comes in handy with small tables (not necessarily small fonts):
    
    >>> d = {12: 4, 90: 4}
    >>> utilities.hexdump(bestFromDict(d, sentinelValue=1))
           0 | 0006 0004 0002 0008  0001 0000 000C 0004 |................|
          10 | 005A 0004 FFFF 0001                      |.Z......        |
    
    Format 8 emulates the old 'kern' state table format, and is useful for very
    short contiguous runs of affected glyphs:
    
    >>> d = {12: 4}
    >>> utilities.hexdump(bestFromDict(d))
           0 | 0008 000C 0001 0004                      |........        |
    
    Note you can force the format:
    
    >>> utilities.hexdump(bestFromDict(d, preferredFormat=6))
           0 | 0006 0004 0001 0004  0000 0000 000C 0004 |................|
          10 | FFFF FFFF                                |....            |
    
    You can prevent coverage gaps using the noGaps flag:
    
    >>> d = {114: 537, 116: 539}
    >>> utilities.hexdump(bestFromDict(d))
           0 | 0008 0072 0003 0219  0001 021B           |...r........    |
    >>> utilities.hexdump(bestFromDict(d, noGaps=True))
           0 | 0006 0004 0002 0008  0001 0000 0072 0219 |.............r..|
          10 | 0074 021B FFFF FFFF                      |.t......        |
    """
    
    logger = kwArgs.get('logger', None)
    
    try:
        allOK = all(i == int(i) and i >= 0 and i < 65536 for i in d.values())
    except:
        allOK = False
    
    if not allOK:
        if logger is not None:
            logger.error((
              'V0700',
              (),
              "One or more lookup values are bad."))
            
            return None
        
        else:
            raise ValueError("One or more lookup values are bad.")
    
    prefFormat = kwArgs.get('preferredFormat', None)
    
    if 'baseStake' in kwArgs:
        assert prefFormat is not None
        assert 'w' in kwArgs
        _makers[prefFormat](d, **kwArgs)
        return None
    
    if prefFormat is None:
        toTry = {0, 2, 4, 6, 8}
        
        if kwArgs.get('noGaps', False):
            kwArgs['format4NoGaps'] = True
            
            if len(span.Span(d)) > 1:
                toTry = {2, 4, 6}
            elif min(d):
                toTry.discard(0)
    
    else:
        toTry = {prefFormat}
    
    if 'w' in kwArgs:
        wSave = kwArgs.pop('w')
    else:
        wSave = None
    
    best = None
    
    for format in toTry:
        s = _makers[format](d, **kwArgs)
    
        if (best is None) or (len(s) < len(best)):
            best = s
    
    if wSave is None:
        return best
    
    wSave.addString(best)
    return None

def bestFromDict_0(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 0 lookup, or else it adds
    the binary data representing the format 0 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d, which must start from
                        zero. A ValueError will be raised if this is not true.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 0 data will be returned.
    
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 18: 5, 29: 4}
    >>> utilities.hexdump(bestFromDict_0(d))
           0 | 0000 0001 0001 0001  0001 0001 0001 0001 |................|
          10 | 0001 0001 0001 0001  0001 0004 0004 0001 |................|
          20 | 0001 0004 0005 0005  0001 0001 0001 0001 |................|
          30 | 0001 0001 0001 0001  0001 0001 0004      |..............  |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[0] = w.getNewStake()
    >>> d[1] = w.getNewStake()
    >>> bestFromDict_0(d, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[1])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[0])
    >>> w.add("H", 11)
    >>> utilities.hexdump(w.binaryString())
           0 | FFFF FFFF 0000 0010  000E FEFE FEFE 000A |................|
          10 | 000B                                     |..              |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 0)  # format
    baseStake = kwArgs.pop('baseStake', None)
    numGlyphs = max(d) + 1
    
    if baseStake is None:
        w.addGroup("H", (d.get(i, 1) for i in range(numGlyphs)))
    
    else:
        for i in range(numGlyphs):
            
            # We use d[i] in the following line, instead of d.get(...), because
            # all entries must be present in the offset case; no gaps are
            # permitted.
            
            w.addUnresolvedOffset("H", baseStake, d[i])
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_2(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 2 lookup, or else it adds
    the binary data representing the format 2 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values. Note that in this case, if 0xFFFF is explicitly
                        present as a value in d, then nUnits will include that
                        entry. In this case, the sentinel will NOT be added.
                        Otherwise the sentinel value will be added.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d. A ValueError will be
                        raised if this is not true.
        
        sentinelValue   A numeric value to be used as the sentinel output value
                        for the final 0xFFFF entry. Default is 0xFFFF.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 2 data will be returned.
    
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 18: 5, 29: 4}
    >>> utilities.hexdump(bestFromDict_2(d, sentinelValue=1))
           0 | 0002 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> d[65535] = 1
    >>> utilities.hexdump(bestFromDict_2(d, sentinelValue=1))
           0 | 0002 0006 0005 0018  0002 0006 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_2(d, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> utilities.hexdump(w.binaryString())
           0 | FFFF FFFF 0002 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 002A 0032  0032 002C FFFF FFFF |.#. .*.2.2.,....|
          20 | FFFF FFFF FFFF FEFE  FEFE 000A 000B      |..............  |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 2)  # format
    baseStake = kwArgs.pop('baseStake', None)
    it = range(min(d), max(d) + 1)
    vSorted = [(glyph, d.get(glyph, None)) for glyph in it]
    groups = []
    
    for k, g in itertools.groupby(vSorted, operator.itemgetter(1)):
        if k is not None:  # don't bother with out-of-bounds glyphs
            v = list(g)
            groups.append((v[-1][0], v[0][0], k))  # (last, first, mappedValue)
    
    bsh.BSH(nUnits=len(groups), unitSize=6).buildBinary(w)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        groups.append((0xFFFF, 0xFFFF, sentinelValue))  # not counted in nUnits
    
    if baseStake is None:
        w.addGroup("3H", groups)  # it's already sorted correctly
    
    else:
        for last, first, stake in groups:
            w.add("2H", last, first)
            
            if last == first == 0xFFFF:
                w.add("3H", last, first, stake)
            else:
                w.addUnresolvedOffset("H", baseStake, stake)
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_2_mix(d, lastLessThanFirst, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 2 lookup, or else it adds
    the binary data representing the format 2 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values. Note that in this case, if 0xFFFF is explicitly
                        present as a value in d, then nUnits will include that
                        entry. In this case, the sentinel will NOT be added.
                        Otherwise the sentinel value will be added.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d. A ValueError will be
                        raised if this is not true.
        
        sentinelValue   A numeric value to be used as the sentinel output value
                        for the final 0xFFFF entry. Default is 0xFFFF.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 2 data will be returned.
    
    >>> h = utilities.hexdump
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 18: 5, 29: 4}
    >>> h(bestFromDict_2_mix(d, 0, sentinelValue=1))
           0 | 0002 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> d[65535] = 1
    >>> h(bestFromDict_2_mix(d, 0, sentinelValue=1))
           0 | 0002 0006 0005 0018  0002 0006 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_2_mix(d, 0, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> h(w.binaryString())
           0 | FFFF FFFF 0002 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 002A 0032  0032 002C FFFF FFFF |.#. .*.2.2.,....|
          20 | FFFF FFFF FFFF FEFE  FEFE 000A 000B      |..............  |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 2)  # format
    baseStake = kwArgs.pop('baseStake', None)
    it = range(min(d), max(d) + 1)
    vSorted = [(glyph, d.get(glyph, None)) for glyph in it]
    groups = []
    
    for k, g in itertools.groupby(vSorted, operator.itemgetter(1)):
        if k is not None:  # don't bother with out-of-bounds glyphs
            v = list(g)
            
            groups.append((
              v[-1][0] - lastLessThanFirst,
              v[0][0] + lastLessThanFirst,
              k))  # (last, first, mappedValue)
    
    bsh.BSH(nUnits=len(groups), unitSize=6).buildBinary(w)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        groups.append((0xFFFF, 0xFFFF, sentinelValue))  # not counted in nUnits
    
    if baseStake is None:
        w.addGroup("3H", groups)  # it's already sorted correctly
    
    else:
        for last, first, stake in groups:
            w.add("2H", last, first)
            
            if last == first == 0xFFFF:
                w.add("3H", last, first, stake)
            else:
                w.addUnresolvedOffset("H", baseStake, stake)
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_2_unitSize(d, s, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 2 lookup, or else it adds
    the binary data representing the format 2 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values. Note that in this case, if 0xFFFF is explicitly
                        present as a value in d, then nUnits will include that
                        entry. In this case, the sentinel will NOT be added.
                        Otherwise the sentinel value will be added.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d. A ValueError will be
                        raised if this is not true.
        
        sentinelValue   A numeric value to be used as the sentinel output value
                        for the final 0xFFFF entry. Default is 0xFFFF.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 2 data will be returned.
    
    >>> h = utilities.hexdump
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 18: 5, 29: 4}
    >>> h(bestFromDict_2_unitSize(d, 6, sentinelValue=1))
           0 | 0002 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> d[65535] = 1
    >>> h(bestFromDict_2_unitSize(d, 6, sentinelValue=1))
           0 | 0002 0006 0005 0018  0002 0006 000D 000C |................|
          10 | 0004 0010 0010 0004  0012 0011 0005 001D |................|
          20 | 001D 0004 FFFF FFFF  0001                |..........      |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_2_unitSize(d, 6, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> h(w.binaryString())
           0 | FFFF FFFF 0002 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 002A 0032  0032 002C FFFF FFFF |.#. .*.2.2.,....|
          20 | FFFF FFFF FFFF FEFE  FEFE 000A 000B      |..............  |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 2)  # format
    baseStake = kwArgs.pop('baseStake', None)
    it = range(min(d), max(d) + 1)
    vSorted = [(glyph, d.get(glyph, None)) for glyph in it]
    groups = []
    
    for k, g in itertools.groupby(vSorted, operator.itemgetter(1)):
        if k is not None:  # don't bother with out-of-bounds glyphs
            v = list(g)
            groups.append((v[-1][0], v[0][0], k))  # (last, first, mappedValue)
    
    bsh.BSH(nUnits=len(groups), unitSize=s).buildBinary(w)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        groups.append((0xFFFF, 0xFFFF, sentinelValue))  # not counted in nUnits
    
    if baseStake is None:
        w.addGroup("3H", groups)  # it's already sorted correctly
    
    else:
        for last, first, stake in groups:
            w.add("2H", last, first)
            
            if last == first == 0xFFFF:
                w.add("3H", last, first, stake)
            else:
                w.addUnresolvedOffset("H", baseStake, stake)
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_4(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 4 lookup, or else it adds
    the binary data representing the format 4 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake           A stake value representing the base position from
                            which the offsets will be measured. This is
                            optional.

                            If present, values in d are interpreted as stakes
                            (measured from baseStake), and will be added via
                            the addUnresolvedOffset() call.

                            If absent, the 16-bit values will be written as
                            actual values. Note that in this case, if 0xFFFF is
                            explicitly present as a value in d, then nUnits
                            will include that entry. In this case, the sentinel
                            will NOT be added. Otherwise the sentinel value
                            will be added.

                            Important note: if baseStake is not None, then
                            there can be no gaps in the keys in d. A ValueError
                            will be raised if this is not true.
        
        format4GapValue     If format4NoGaps is False (the default), this value
                            will be used for missing keys. Default is 1.
        
        format4NoGaps       A Boolean, default False. If True, the segments
                            will be arranged so that only the keys present in d
                            will appear in the binary string. If False, gaps
                            may appear; those gaps will be filled with the
                            format4GapValue (q.v.)
                            
                            Note that if a baseStake is provided, then this
                            format4NoGaps value is forced True, irrespective of
                            its specified value in the kwArgs.
    
        sentinelValue       A numeric value to be used as the sentinel output
                            value for the final 0xFFFF entry. Default is
                            0xFFFF.
        
        w                   If present, this specifies a LinkedWriter to which
                            the data will be added, and None will be returned
                            by this method. If absent, a local writer will be
                            used, and a binary string with the format 4 data
                            will be returned.
    
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 20: 5, 29: 4}
    >>> utilities.hexdump(bestFromDict_4(d))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004                                     |..              |
    
    >>> utilities.hexdump(bestFromDict_4(d, format4NoGaps=True))
           0 | 0004 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 002A 0011 0010 002E  0014 0014 0032 001D |.*...........2..|
          20 | 001D 0034 FFFF FFFF  FFFF 0004 0004 0004 |...4............|
          30 | 0005 0005 0004                           |......          |
    
    >>> utilities.hexdump(bestFromDict_4(d, format4GapValue=0xFFFF))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 FFFF FFFF 0004  0005 FFFF FFFF 0005 |................|
          30 | 0004                                     |..              |
    
    >>> d[65535] = 12
    >>> utilities.hexdump(bestFromDict_4(d))
           0 | 0004 0006 0003 000C  0001 0006 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF 0032 0004 |.......0.....2..|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004 000C                                |....            |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_4(d, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> utilities.hexdump(w.binaryString())
           0 | FFFF FFFF 0004 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 001E 0032  0032 0026 FFFF FFFF |.#. ...2.2.&....|
          20 | FFFF 0030 0030 0030  0030 0032 FEFE FEFE |...0.0.0.0.2....|
          30 | 000A 000B                                |....            |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    startStake = w.stakeCurrent()
    baseStake = kwArgs.pop('baseStake', None)
    w.add("H", 4)  # format
    groups = []
    
    if kwArgs.get('format4NoGaps', False) or (baseStake is not None):
        for start, stop, x in utilities.monotonicGroupsGenerator(sorted(d)):
            groups.append((start, stop - 1))
    
    else:
        v = sorted(d)
        last = first = v[0]
        
        for n in v:
            if n - last < 4:  # heuristic; that's the break-even point
                last = n
            
            else:
                groups.append((first, last))
                first = last = n
        
        groups.append((first, last))
    
    bsh.BSH(nUnits=len(groups), unitSize=6).buildBinary(w)
    stakes = [w.getNewStake() for obj in groups]
    
    for (first, last), stake in zip(groups, stakes):
        w.add("2H", last, first)
        w.addUnresolvedOffset("H", startStake, stake)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        w.add("3H", 0xFFFF, 0xFFFF, sentinelValue)
    
    if baseStake is None:
        gapDefault = kwArgs.get('format4GapValue', 1)
        
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            g = (d.get(i, gapDefault) for i in range(first, last + 1))
            w.addGroup("H", g)
    
    else:
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            
            for i in range(first, last + 1):
                w.addUnresolvedOffset("H", baseStake, d[i])
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_4_mix(d, mix, lastLessThanFirst, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 4 lookup, or else it adds
    the binary data representing the format 4 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake           A stake value representing the base position from
                            which the offsets will be measured. This is
                            optional.

                            If present, values in d are interpreted as stakes
                            (measured from baseStake), and will be added via
                            the addUnresolvedOffset() call.

                            If absent, the 16-bit values will be written as
                            actual values. Note that in this case, if 0xFFFF is
                            explicitly present as a value in d, then nUnits
                            will include that entry. In this case, the sentinel
                            will NOT be added. Otherwise the sentinel value
                            will be added.

                            Important note: if baseStake is not None, then
                            there can be no gaps in the keys in d. A ValueError
                            will be raised if this is not true.
        
        format4GapValue     If format4NoGaps is False (the default), this value
                            will be used for missing keys. Default is 1.
        
        format4NoGaps       A Boolean, default False. If True, the segments
                            will be arranged so that only the keys present in d
                            will appear in the binary string. If False, gaps
                            may appear; those gaps will be filled with the
                            format4GapValue (q.v.)
                            
                            Note that if a baseStake is provided, then this
                            format4NoGaps value is forced True, irrespective of
                            its specified value in the kwArgs.
    
        sentinelValue       A numeric value to be used as the sentinel output
                            value for the final 0xFFFF entry. Default is
                            0xFFFF.
        
        w                   If present, this specifies a LinkedWriter to which
                            the data will be added, and None will be returned
                            by this method. If absent, a local writer will be
                            used, and a binary string with the format 4 data
                            will be returned.
    
    >>> h = utilities.hexdump
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 20: 5, 29: 4}
    >>> h(bestFromDict_4_mix(d, False, 0))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004                                     |..              |
    
    >>> h(bestFromDict_4_mix(d, False, 0, format4NoGaps=True))
           0 | 0004 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 002A 0011 0010 002E  0014 0014 0032 001D |.*...........2..|
          20 | 001D 0034 FFFF FFFF  FFFF 0004 0004 0004 |...4............|
          30 | 0005 0005 0004                           |......          |
    
    >>> h(bestFromDict_4_mix(d, False, 0, format4GapValue=0xFFFF))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 FFFF FFFF 0004  0005 FFFF FFFF 0005 |................|
          30 | 0004                                     |..              |
    
    >>> d[65535] = 12
    >>> h(bestFromDict_4_mix(d, False, 0))
           0 | 0004 0006 0003 000C  0001 0006 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF 0032 0004 |.......0.....2..|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004 000C                                |....            |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_4_mix(d, False, 0, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> h(w.binaryString())
           0 | FFFF FFFF 0004 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 001E 0032  0032 0026 FFFF FFFF |.#. ...2.2.&....|
          20 | FFFF 0030 0030 0030  0030 0032 FEFE FEFE |...0.0.0.0.2....|
          30 | 000A 000B                                |....            |
    >>> print((str(len(bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6, 8:9, 25:26, 11:12, 22:23, 14:15, 17:18, 20:21  }, True, 0)))))
    24
    >>> print((str(len(bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6, 8:9, 25:26, 11:12, 22:23, 14:15, 17:18, 20:21  }, False, 0)))))
    84
    >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 0)))))
    50
    >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, True, 0)))))
    24
    >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 7)))))
    42
    >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, True, 7)))))
    24
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    startStake = w.stakeCurrent()
    baseStake = kwArgs.pop('baseStake', None)
    w.add("H", 4)  # format
    groups = []
    
    if kwArgs.get('format4NoGaps', False) or (baseStake is not None):
        for start, stop, x in utilities.monotonicGroupsGenerator(sorted(d)):
            groups.append((start, stop - 1))
    
    else:
        if(mix):
            v = sorted(d, reverse=True)
        else:
            v = sorted(d)
        
        last = first = v[0]
        
        for n in v:
            if n - last < 4:  # heuristic; that's the break-even point
                last = n
            
            else:
                groups.append((first, last))
                first = last = n
        
        groups.append((first, last))
    
    bsh.BSH(nUnits=len(groups), unitSize=6).buildBinary(w)
    stakes = [w.getNewStake() for obj in groups]
    
    for (first, last), stake in zip(groups, stakes):
        w.add("2H", last, first)
        w.addUnresolvedOffset("H", startStake, stake)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        w.add("3H", 0xFFFF, 0xFFFF, sentinelValue)
    
    if baseStake is None:
        gapDefault = kwArgs.get('format4GapValue', 1)
        
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            
            g = (
              d.get(i, gapDefault)
              for i in range(first, last + 1-lastLessThanFirst))
            
            w.addGroup("H", g)
    
    else:
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            
            for i in range(first, last + 1):
                w.addUnresolvedOffset("H", baseStake, d[i]-lastLessThanFirst)
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_4_unitSize(d, uS, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 4 lookup, or else it adds
    the binary data representing the format 4 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake           A stake value representing the base position from
                            which the offsets will be measured. This is
                            optional.

                            If present, values in d are interpreted as stakes
                            (measured from baseStake), and will be added via
                            the addUnresolvedOffset() call.

                            If absent, the 16-bit values will be written as
                            actual values. Note that in this case, if 0xFFFF is
                            explicitly present as a value in d, then nUnits
                            will include that entry. In this case, the sentinel
                            will NOT be added. Otherwise the sentinel value
                            will be added.

                            Important note: if baseStake is not None, then
                            there can be no gaps in the keys in d. A ValueError
                            will be raised if this is not true.
        
        format4GapValue     If format4NoGaps is False (the default), this value
                            will be used for missing keys. Default is 1.
        
        format4NoGaps       A Boolean, default False. If True, the segments
                            will be arranged so that only the keys present in d
                            will appear in the binary string. If False, gaps
                            may appear; those gaps will be filled with the
                            format4GapValue (q.v.)
                            
                            Note that if a baseStake is provided, then this
                            format4NoGaps value is forced True, irrespective of
                            its specified value in the kwArgs.
    
        sentinelValue       A numeric value to be used as the sentinel output
                            value for the final 0xFFFF entry. Default is
                            0xFFFF.
        
        w                   If present, this specifies a LinkedWriter to which
                            the data will be added, and None will be returned
                            by this method. If absent, a local writer will be
                            used, and a binary string with the format 4 data
                            will be returned.
    
    >>> h = utilities.hexdump
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 20: 5, 29: 4}
    >>> h(bestFromDict_4_unitSize(d, 6))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004                                     |..              |
    
    >>> h(bestFromDict_4_unitSize(d, 6, format4NoGaps=True))
           0 | 0004 0006 0004 0018  0002 0000 000D 000C |................|
          10 | 002A 0011 0010 002E  0014 0014 0032 001D |.*...........2..|
          20 | 001D 0034 FFFF FFFF  FFFF 0004 0004 0004 |...4............|
          30 | 0005 0005 0004                           |......          |
    
    >>> h(bestFromDict_4_unitSize(d, 6, format4GapValue=0xFFFF))
           0 | 0004 0006 0002 000C  0001 0000 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF FFFF 0004 |.......0........|
          20 | 0004 FFFF FFFF 0004  0005 FFFF FFFF 0005 |................|
          30 | 0004                                     |..              |
    
    >>> d[65535] = 12
    >>> h(bestFromDict_4_unitSize(d, 6))
           0 | 0004 0006 0003 000C  0001 0006 0014 000C |................|
          10 | 001E 001D 001D 0030  FFFF FFFF 0032 0004 |.......0.....2..|
          20 | 0004 0001 0001 0004  0005 0001 0001 0005 |................|
          30 | 0004 000C                                |....            |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_4_unitSize(d, 6, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> h(w.binaryString())
           0 | FFFF FFFF 0004 0006  0002 000C 0001 0000 |................|
          10 | 0023 0020 001E 0032  0032 0026 FFFF FFFF |.#. ...2.2.&....|
          20 | FFFF 0030 0030 0030  0030 0032 FEFE FEFE |...0.0.0.0.2....|
          30 | 000A 000B                                |....            |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    startStake = w.stakeCurrent()
    baseStake = kwArgs.pop('baseStake', None)
    w.add("H", 4)  # format
    groups = []
    
    if kwArgs.get('format4NoGaps', False) or (baseStake is not None):
        for start, stop, x in utilities.monotonicGroupsGenerator(sorted(d)):
            groups.append((start, stop - 1))
    
    else:
        v = sorted(d)
        last = first = v[0]
        
        for n in v:
            if n - last < 4:  # heuristic; that's the break-even point
                last = n
            
            else:
                groups.append((first, last))
                first = last = n
        
        groups.append((first, last))
    
    bsh.BSH(nUnits=len(groups), unitSize=uS).buildBinary(w)
    stakes = [w.getNewStake() for obj in groups]
    
    for (first, last), stake in zip(groups, stakes):
        w.add("2H", last, first)
        w.addUnresolvedOffset("H", startStake, stake)
    
    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        w.add("3H", 0xFFFF, 0xFFFF, sentinelValue)
    
    if baseStake is None:
        gapDefault = kwArgs.get('format4GapValue', 1)
        
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            g = (d.get(i, gapDefault) for i in range(first, last + 1))
            w.addGroup("H", g)
    
    else:
        for (first, last), stake in zip(groups, stakes):
            w.stakeCurrentWithValue(stake)
            
            for i in range(first, last + 1):
                w.addUnresolvedOffset("H", baseStake, d[i])
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_6(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 6 lookup, or else it adds
    the binary data representing the format 6 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values. Note that in this case, if 0xFFFF is explicitly
                        present as a value in d, then nUnits will include that
                        entry. In this case, the sentinel will NOT be added.
                        Otherwise the sentinel value will be added.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d. A ValueError will be
                        raised if this is not true.
        
        sentinelValue   A numeric value to be used as the sentinel output value
                        for the final 0xFFFF entry. Default is 0xFFFF.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 6 data will be returned.
    
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 20: 5, 29: 4}
    >>> utilities.hexdump(bestFromDict_6(d, sentinelValue=1))
           0 | 0006 0004 0006 0010  0002 0008 000C 0004 |................|
          10 | 000D 0004 0010 0004  0011 0005 0014 0005 |................|
          20 | 001D 0004 FFFF 0001                      |........        |
    
    In the following example, note the only difference with the previous
    binary content is that the 0xFFFF entry is added to nUnits:
    
    >>> d[65535] = 1
    >>> utilities.hexdump(bestFromDict_6(d))
           0 | 0006 0004 0007 0010  0002 000C 000C 0004 |................|
          10 | 000D 0004 0010 0004  0011 0005 0014 0005 |................|
          20 | 001D 0004 FFFF 0001                      |........        |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[32] = w.getNewStake()
    >>> d[33] = d[34] = d[35] = d[32]
    >>> d[50] = w.getNewStake()
    >>> bestFromDict_6(d, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[32])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[50])
    >>> w.add("H", 11)
    >>> utilities.hexdump(w.binaryString())
           0 | FFFF FFFF 0006 0004  0005 0010 0002 0004 |................|
          10 | 0020 002C 0021 002C  0022 002C 0023 002C |. .,.!.,.".,.#.,|
          20 | 0032 002E FFFF FFFF  FEFE FEFE 000A 000B |.2..............|
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 6)  # format
    baseStake = kwArgs.pop('baseStake', None)
    bsh.BSH(nUnits=len(d), unitSize=4).buildBinary(w)
    
    if baseStake is None:
        w.addGroup("2H", sorted(d.items()))
    
    else:
        for glyph in sorted(d):
            w.add("H", glyph)
            w.addUnresolvedOffset("H", baseStake, d[glyph])

    if 0xFFFF not in d:
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        w.add("2H", 0xFFFF, sentinelValue)
    
    return (w.binaryString() if isLocal else None)

def bestFromDict_8(d, **kwArgs):
    """
    Given a dict mapping glyph indices to numeric values, this method either
    returns a binary string representing the format 8 lookup, or else it adds
    the binary data representing the format 8 lookup to a writer. This is all
    controlled by the following keyword arguments:
    
        baseStake       A stake value representing the base position from
                        which the offsets will be measured. This is optional.
                        
                        If present, values in d are interpreted as stakes
                        (measured from baseStake), and will be added via the
                        addUnresolvedOffset() call.

                        If absent, the 16-bit values will be written as actual
                        values.

                        Important note: if baseStake is not None, then there
                        can be no gaps in the keys in d. A ValueError will be
                        raised if this is not true.
        
        w               If present, this specifies a LinkedWriter to which the
                        data will be added, and None will be returned by this
                        method. If absent, a local writer will be used, and a
                        binary string with the format 8 data will be returned.
    
    Given a dict mapping glyph indices to numeric values, returns a binary
    string representing the format 8 LookupTable for it.
    
    >>> d = {12: 4, 13: 4, 16: 4, 17: 5, 20: 5, 29: 4}
    >>> utilities.hexdump(bestFromDict_8(d))
           0 | 0008 000C 0012 0004  0004 0001 0001 0004 |................|
          10 | 0005 0001 0001 0005  0001 0001 0001 0001 |................|
          20 | 0001 0001 0001 0001  0004                |..........      |
    
    >>> w = writer.LinkedWriter()
    >>> baseStake = w.stakeCurrent()
    >>> w.add("l", -1)
    >>> d = {}
    >>> d[80] = w.getNewStake()
    >>> d[81] = w.getNewStake()
    >>> bestFromDict_8(d, baseStake=baseStake, w=w)
    >>> w.add("4B", 254, 254, 254, 254)
    >>> w.stakeCurrentWithValue(d[80])
    >>> w.add("H", 10)
    >>> w.stakeCurrentWithValue(d[81])
    >>> w.add("H", 11)
    >>> utilities.hexdump(w.binaryString())
           0 | FFFF FFFF 0008 0050  0002 0012 0014 FEFE |.......P........|
          10 | FEFE 000A 000B                           |......          |
    """
    
    if 'w' in kwArgs:
        w = kwArgs.pop('w')
        isLocal = False
    
    else:
        w = writer.LinkedWriter()
        isLocal = True
    
    w.add("H", 8)  # format
    baseStake = kwArgs.pop('baseStake', None)
    firstGlyph = min(d)
    glyphCount = (max(d) - firstGlyph) + 1
    w.add("2H", firstGlyph, glyphCount)
    
    if baseStake is None:
        w.addGroup(
          "H",
          (d.get(i, 1) for i in range(firstGlyph, firstGlyph + glyphCount)))
    
    else:
        for glyph in range(firstGlyph, firstGlyph + glyphCount):
            w.addUnresolvedOffset("H", baseStake, d[glyph])
    
    return (w.binaryString() if isLocal else None)

_makers = {
  0: bestFromDict_0,
  2: bestFromDict_2,
  4: bestFromDict_4,
  6: bestFromDict_6,
  8: bestFromDict_8}

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Lookup(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing mapping from glyph indices to some arbitrary numeric
    value.
    
    >>> logger = utilities.makeDoctestLogger("lookup_val")
    >>> e = utilities.fakeEditor(300)
    >>> Lookup({5: 19}).isValid(logger=logger, editor=e)
    True
    
    >>> Lookup({400: -12}).isValid(logger=logger, editor=e)
    lookup_val.[400] - ERROR - Glyph index 400 too large.
    lookup_val.[400] - ERROR - The negative value -12 cannot be used in an unsigned field.
    False
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        item_validatefunc = valassist.isFormat_H)
    
    attrSpec = dict(
        _preferredFormat = dict())
    
    attrSorted = ()
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the Lookup to the specified writer. The
        following keyword arguments are supported:
        
        noGaps              A Boolean, default False. If True, the keys will be
                            checked first to make sure there are no gaps in
                            coverage; if such gaps exist, then formats 0 and 8
                            will not be tried, and format 4 will have the
                            format4NoGaps flag forced True.
        
        sentinelValue       A numeric value to be used as the sentinel output
                            value for the final 0xFFFF entry. Default is
                            0xFFFF.
        >>> a = Lookup({1:10})
        >>> b = Lookup({1:10}, _preferredFormat = 0xFF)
        >>> w = writer.LinkedWriter()
        >>> myStake = w.getNewStake()
        >>> a.buildBinary(w)
        >>> a
        Lookup({1: 10}, _preferredFormat=None)
        >>> a.buildBinary(w, stakeValue = myStake)
        >>> a
        Lookup({1: 10}, _preferredFormat=None)
        >>> b.buildBinary(w)
        Traceback (most recent call last):
        ...
        KeyError: 255
        >>> b
        Lookup({1: 10}, _preferredFormat=255)
        """
        
        # unable to set preferredFormat as 6
        #>>> b = Lookup({9:10})
        #>>> b
        #Lookup({9: 10}, _preferredFormat=None)        
        #>>> b.buildBinary(w, preferredFormat = 6)
        #>>> b
        #Lookup({9: 10}, _preferredFormat=6)
        #>>> c = Lookup({9:10})
        #>>> c.buildBinary(w, _preferredFormat = 6, preferredFormat = 6)
        #>>> c
        #Lookup({9: 10}, _preferredFormat=6)
        #"""
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        if self._preferredFormat is not None:
            kwArgs['preferredFormat'] = self._preferredFormat
        
        bestFromDict(self, w=w, **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Logger from the specified walker, doing
        source validation.
        
        The following keyword arguments are supported:
        
            logger          A logger to which messages will be logged.
        
            sentinelValue   A value that is expected as the value for any
                            0xFFFF glyph sentinel entry (formats 2, 4, and 6).
                            If the 0xFFFF glyph is included in nUnits, this
                            value is ignored; otherwise it is checked, and a
                            warning is issued if it does not match. Default is
                            0xFFFF.
                            
                            If None is specified, then no sentinel is expected
                            for formats 2, 4, and 6; if one is present, a
                            warning will be logged.
        
        >>> d = {12: 4, 90: 4}
        >>> s6 = bestFromDict_6(d)
        >>> logger = utilities.makeDoctestLogger("fvw")
        >>> logger4 = utilities.makeDoctestLogger("fvw", _format = 4)
        >>> fvb = Lookup.fromvalidatedbytes
        >>> obj = fvb(s6, logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        >>> dict(obj) == d
        True
        
        >>> obj = fvb(s6, logger=logger, sentinelValue=None)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - WARNING - Was not expecting a sentinel, but there appears to be one there anyway.
        
        >>> obj = fvb(s6[:-4], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 20 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat - WARNING - Expected a sentinel but one is not present.
        
        >>> obj = fvb(s6[:-4] + s6[:4], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.
        
        >>> obj = fvb(s6[:-4] + s6[:4], logger=logger, _preferredFormat = 6)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.

        >>> obj = fvb(s6[1:2], logger=logger, _preferredFormat = 6)
        fvw.lookup_aat - DEBUG - Walker has 1 remaining bytes.
        fvw.lookup_aat - ERROR - Insufficient bytes.
        
        >>> logger3 = utilities.makeDoctestLogger("fvw", _format = 3)
        >>> obj = fvb(s6[1:3], logger=logger3, _preferredFormat = 6)
        fvw.lookup_aat - DEBUG - Walker has 2 remaining bytes.
        fvw.lookup_aat - ERROR - The Lookup format (1536) is not recognized.
        
        >>> s = bestFromDict({1:20}, sentinelValue = 4)        
        >>> obj = fvb(s[:4], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 4 remaining bytes.
        
        >>> s0 = bestFromDict_0({1:20}, sentinelValue = 4)        
        >>> obj = fvb(s0[:4], logger=logger4)
        fvw.lookup_aat - DEBUG - Walker has 4 remaining bytes.
        
        >>> s2 = bestFromDict_2({1:200})   
        >>> s2_sv7 = bestFromDict_2({1:20}, sentinelValue = 7)      
        >>> s2_badIndices = bestFromDict_2_mix({50:40, 7:11, 25:13, 35:28}, 5)
        >>> obj = fvb(s2[:18], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 16 remaining bytes.
        fvw.lookup_aat - WARNING - Expected a sentinel but one is not present.
        
        
        >>> obj = fvb(s2[:6], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 6 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 4 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.
        
        >>> obj = fvb(s2[:20], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 20 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat - WARNING - Expected a sentinel but one is not present.
        
        >>> obj = fvb(s2_sv7[:20], logger=logger4)
        fvw.lookup_aat - DEBUG - Walker has 20 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat - WARNING - Expected a sentinel but one is not present.
        
        >>> obj = fvb(s2[:17], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 17 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 15 remaining bytes.
        fvw.lookup_aat - ERROR - The data for the format 2 Lookup are missing or incomplete.
        
        >>> obj = fvb(s2_sv7, logger = logger, sentinelValue = None)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - WARNING - Was not expecting a sentinel, but there appears to be one there anyway.
        
        >>> obj = fvb(s2_sv7, logger = logger, sentinelValue = 17)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.
        
        >>> obj = fvb(s2_sv7, logger = logger, sentinelValue = 7)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        
        
        >>> obj = fvb(s2_badIndices, logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 42 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 40 remaining bytes.
        fvw.lookup_aat - ERROR - The following glyph ranges have their start and end glyph indices swapped: [(2, 12), (20, 30), (30, 40), (45, 55)]

        >>> s2_uS3 = bestFromDict_2_unitSize({1:200},3 , sentinelValue = 70)
        >>> obj = fvb(s2_uS3[:6], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 6 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 4 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.

        >>> obj = fvb(s2_uS3[:17], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 17 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 15 remaining bytes.
        fvw.lookup_aat - ERROR - Was expecting a unitSize of 6 in the binary search header for a format 2 class table, but got 3 instead.
        
        >>> s4 = bestFromDict_4({10:200} )
        >>> s4_uS7 = bestFromDict_4_unitSize({1:250},7 )
        >>> s4_sent7 = bestFromDict_4({1:80}, sentinelValue = 7)        
        >>> s4_2 = bestFromDict_4({1:80, 0xFF0A:0xFFEE})
        >>> s4_2_sent7 = bestFromDict_4({1:80, 0xFF0A:0xFFEE}, sentinelValue = 7)        
        >>> s4_FF = bestFromDict_4({0xFFFF:0xFFFF, 0xFFEA:0xFFFE})
        >>> s4_FF_sv7 = bestFromDict_4({0xFFFF:0xFFFF, 0xFFEA:0xFFFE}, sentinelValue = 7)        
        >>> s4_badIndices = bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6, 8:9, 25:26, 11:12, 22:23, 14:15, 17:18, 20:21  }, True, 0)
                
        >>> obj = fvb(s4_uS7[:20], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 20 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat - ERROR - Was expecting a unitSize of 6 in the binary search header for a format 4 class table, but got 7 instead.
        
        >>> obj = fvb(s4, logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 26 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 24 remaining bytes.
        
        >>> obj = fvb(s4[:6], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 6 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 4 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.

        >>> obj = fvb(s4[:20], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 20 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 18 remaining bytes.
        fvw.lookup_aat - ERROR - The segment data at the specified offset are missing or incomplete.

        >>> obj = fvb(s4[:17], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 17 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 15 remaining bytes.
        fvw.lookup_aat - ERROR - The data for the format 4 Lookup are missing or incomplete.
        
        >>> obj = fvb(s4_sent7, logger = logger, sentinelValue = None)
        fvw.lookup_aat - DEBUG - Walker has 26 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat - WARNING - Was not expecting a sentinel, but there appears to be one there anyway.
        
        >>> obj = fvb(s4_sent7, logger = logger, sentinelValue = 17)
        fvw.lookup_aat - DEBUG - Walker has 26 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.
        
        >>> obj = fvb(s4_2, logger = logger, sentinelValue = 7)
        fvw.lookup_aat - DEBUG - Walker has 34 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 32 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.

        >>> obj = fvb(s4_FF_sv7, logger = logger, sentinelValue = 7)
        fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        
        >>> obj = fvb(s4_2, logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 34 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 32 remaining bytes.
        
        >>> obj = fvb(s4_2_sent7, logger = logger, sentinelValue = 7)
        fvw.lookup_aat - DEBUG - Walker has 34 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 32 remaining bytes.
        
        >>> obj = fvb(s4_2_sent7, logger = logger, sentinelValue = 17)
        fvw.lookup_aat - DEBUG - Walker has 34 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 32 remaining bytes.
        fvw.lookup_aat - WARNING - Sentinel values do not match expectations.
                
        >>> obj = fvb(s4_FF_sv7, logger = logger, sentinelValue = 17)
        fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        
        >>> obj = fvb(s4_FF_sv7, logger = logger, sentinelValue = 7)
        fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        
        >>> obj = fvb(s4_FF_sv7, logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        
        >>> obj = fvb(s4_FF_sv7, logger = logger, sentinelValue = 17)
        fvw.lookup_aat - DEBUG - Walker has 28 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 26 remaining bytes.
        
        #Test case for if offset < 12 + 6 * len(v):
        >>> obj = fvb(s4_badIndices, logger = logger, sentinelValue = 10)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - ERROR - The following glyph ranges have their start and end glyph indices swapped: [(0, 42)]
        
        >>> print((str(len(bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6, 8:9, 25:26, 11:12, 22:23, 14:15, 17:18, 20:21  }, False, 0)))))
        84
        >>> obj = fvb(bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6, 8:9, 25:26, 11:12, 22:23, 14:15, 17:18, 20:21  }, False, 0), logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 84 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 82 remaining bytes.

        >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 0)))))
        50
        >>> obj = fvb(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 0), logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 50 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 48 remaining bytes.

        >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, True, 0)))))
        24
        >>> obj = fvb(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, True, 0), logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 24 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 22 remaining bytes.
        fvw.lookup_aat - ERROR - The following glyph ranges have their start and end glyph indices swapped: [(16, 42)]
        
        >>> print((str(len(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 7)))))
        42
        >>> obj = fvb(bestFromDict_4_mix({ 42:43,16:20, 32:33, 25:26 }, False, 7), logger = logger)
        fvw.lookup_aat - DEBUG - Walker has 42 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 40 remaining bytes.
        fvw.lookup_aat - ERROR - The segment data at the specified offset are missing or incomplete.

        >>> s8 = bestFromDict_8({1:100})
        >>> obj = fvb(s8[:6], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 6 remaining bytes.
        fvw.lookup_aat - ERROR - The format 8 data is missing or incomplete.

        >>> obj = fvb(s8[:20], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 8 remaining bytes.
        
        >>> obj = fvb(s8[:20], logger=logger4, sentinelValue=None)
        fvw.lookup_aat - DEBUG - Walker has 8 remaining bytes.
        
        >>> obj = fvb(s8[-8:-77], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 0 remaining bytes.
        fvw.lookup_aat - ERROR - Insufficient bytes.

        >>> s_gen = bestFromDict(d)
        >>> obj = fvb(s_gen[:6], logger=logger)
        fvw.lookup_aat - DEBUG - Walker has 6 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - DEBUG - Walker has 4 remaining bytes.
        fvw.lookup_aat.binsearch.binsrch header - ERROR - Insufficient bytes.
        
        """
        
        #>>> lw = writer.LinkedWriter()
        #>>> baseStake1 = lw.stakeCurrent()
        #>>> logger = utilities.makeDoctestLogger("fvw")
        #>>> fvb = Lookup.fromvalidatedbytes
        #>>> s4 = bestFromDict_4_mix({0:1, 42:43, 2:3, 5:6 }, True, 0,  format4NoGaps=True , format4GapValue=100 )
        #>>> obj = fvb(s4, logger = logger, sentinelValue = 10)
        
        #>>> s4 = bestFromDict_4_mix({ 42:43, 16:20, 32:33, 25:26 }, True, 8, format4NoGaps=True , format4GapValue=100 )
        #>>> obj = fvb(s4, logger = logger, sentinelValue = 10)
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("lookup_aat")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        sentinelValue = kwArgs.get('sentinelValue', 0xFFFF)
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        if '_preferredFormat' in kwArgs:
            r._preferredFormat = kwArgs['_preferredFormat']
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        format = w.unpack("H")
        
        if format not in {0, 2, 4, 6, 8}:
            logger.error((
              'V0701',
              (format,),
              "The Lookup format (%d) is not recognized."))
            
            return None
        
        if format == 0:
            v = w.unpackRest("H")
            
            if not v:
                logger.warning((
                  'V0702',
                  (),
                  "The format 0 Lookup has no actual data."))
                
                return r
            
            r.update(dict(zip(itertools.count(), v)))
        
        elif format == 2:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 6:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 6 in the binary search "
                  "header for a format 2 class table, but got %d instead."))
                
                return None
            
            if w.length() < 6 * b.nUnits:
                logger.error((
                  'V0704',
                  (),
                  "The data for the format 2 Lookup are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("3H", b.nUnits)
            badIndices = {t[:2] for t in v if t[1] > t[0]}
            
            if badIndices:
                logger.error((
                  'V0705',
                  (sorted(badIndices),),
                  "The following glyph ranges have their start and end "
                  "glyph indices swapped: %s"))
                
                return None
            
            if list(v) != sorted(v, key=operator.itemgetter(1)):
                logger.error((
                  'V0715',
                  (),
                  "The segments are not sorted by first glyph."))
                
                return None
            
            countByRange = sum(t[0] - t[1] + 1 for t in v)
            countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
            
            if countByRange != countBySet:
                logger.error((
                  'V0716',
                  (),
                  "The segments have overlaps in glyph coverage."))
                
                return None
            
            for last, first, n in v:
                for glyph in range(first, last + 1):
                    r[glyph] = n
            
            if sentinelValue is None:
                if w.length() >= 4:
                    a, b = w.unpack("2H", advance=False)
                    
                    if a == b == 0xFFFF:
                        logger.warning((
                          'V0761',
                          (),
                          "Was not expecting a sentinel, but there appears "
                          "to be one there anyway."))
            
            elif 0xFFFF not in r:
                if w.length() < 6:
                    logger.warning((
                      'V0762',
                      (),
                      "Expected a sentinel but one is not present."))
                 
                else:
                    a, b, c = w.unpack("3H", advance=False)
                    
                    if a != 0xFFFF or b != 0xFFFF or c != sentinelValue:
                        logger.warning((
                          'V0763',
                          (),
                          "Sentinel values do not match expectations."))
        
        elif format == 4:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 6:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 6 in the binary search "
                  "header for a format 4 class table, but got %d instead."))
                
                return None
            
            if w.length() < 6 * b.nUnits:
                logger.error((
                  'V0706',
                  (),
                  "The data for the format 4 Lookup are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("3H", b.nUnits)
            badOrder = sorted(t[:2] for t in v if t[1] > t[0])
            
            if badOrder:
                logger.error((
                  'V0705',
                  (sorted(badOrder),),
                  "The following glyph ranges have their start and end "
                  "glyph indices swapped: %s"))
                
                return None
            
            if list(v) != sorted(v, key=operator.itemgetter(1)):
                logger.error((
                  'V0715',
                  (),
                  "The segments are not sorted by first glyph."))
                
                return None
            
            countByRange = sum(t[0] - t[1] + 1 for t in v)
            countBySet = len({n for t in v for n in range(t[1], t[0] + 1)})
            
            if countByRange != countBySet:
                logger.error((
                  'V0716',
                  (),
                  "The segments have overlaps in glyph coverage."))
                
                return None
            
            if v and (v[-1][:2] == (0xFFFF, 0xFFFF)):
                v = v[:-1]
                sentinelValue = None
            
            for last, first, offset in v:
                count = last - first + 1
                
                if offset < (12 + (6 * len(v))):
                    logger.error((
                      'V0708',
                      (first, last, offset),
                      "The segment offset for the (%d, %d) group is %d, "
                      "which places it within the segment index data. This "
                      "is probably incorrect."))
                    
                    return None
                
                wSub = w.subWalker(offset)
                
                if wSub.length() < 2 * count:
                    logger.error((
                      'V0707',
                      (),
                      "The segment data at the specified offset are missing "
                      "or incomplete."))
                    
                    return None
                
                vSub = wSub.group("H", count)
                
                for glyph, n in zip(range(first, last + 1), vSub):
                    r[glyph] = n
            
            if sentinelValue is None:
                if w.length() >= 4:
                    a, b = w.unpack("2H", advance=False)
                    
                    if a == b == 0xFFFF:
                        logger.warning((
                          'V0761',
                          (),
                          "Was not expecting a sentinel, but there appears "
                          "to be one there anyway."))
            
            elif 0xFFFF not in r:
                if w.length() < 6:
                    logger.warning((
                      'V0762',
                      (),
                      "Expected a sentinel but one is not present."))
                 
                else:
                    a, b, c = w.unpack("3H", advance=False)
                    
                    if a != 0xFFFF or b != 0xFFFF or c != sentinelValue:
                        logger.warning((
                          'V0763',
                          (),
                          "Sentinel values do not match expectations."))
        
        elif format == 6:
            b = bsh.BSH.fromvalidatedwalker(
              w,
              logger = logger.getChild("binsearch"))
            
            if b is None:
                return None
            
            if b.unitSize != 4:
                logger.error((
                  'V0709',
                  (b.unitSize,),
                  "Was expecting a unitSize of 4 in the binary search "
                  "header for a format 6 class table, but got %d instead."))
                
                return None
            
            if w.length() < 4 * b.nUnits:
                logger.error((
                  'V0710',
                  (),
                  "The data for the format 6 Lookup are missing "
                  "or incomplete."))
                
                return None
            
            v = w.group("2H", b.nUnits)
            
            if len({t[0] for t in v}) != len(v):
                logger.error((
                  'V0713',
                  (),
                  "There are duplicate glyphs in the format 6 data."))
                
                return None
            
            elif list(v) != sorted(v):
                logger.error((
                  'V0714',
                  (),
                  "The glyphs are not sorted."))
                
                return None
        
            for glyph, n in v:
                r[glyph] = n
            
            if sentinelValue is None:
                if w.length() >= 2:
                    a = w.unpack("H", advance=False)
                    
                    if a == 0xFFFF:
                        logger.warning((
                          'V0761',
                          (),
                          "Was not expecting a sentinel, but there appears "
                          "to be one there anyway."))
            
            elif 0xFFFF not in r:
                if w.length() < 4:
                    logger.warning((
                      'V0762',
                      (),
                      "Expected a sentinel but one is not present."))
                 
                else:
                    a, b = w.unpack("2H", advance=False)
                    
                    if a != 0xFFFF or b != sentinelValue:
                        logger.warning((
                          'V0763',
                          (),
                          "Sentinel values do not match expectations."))
        
        else:  # safe, since full check was made above
            if w.length() < 4:
                logger.error((
                  'V0711',
                  (),
                  "The format 8 header is missing or incomplete."))
                
                return None
            
            first, count = w.unpack("2H")
            
            if w.length() < 2 * count:
                logger.error((
                  'V0712',
                  (),
                  "The format 8 data is missing or incomplete."))
                
                return None
            
            v = w.group("H", count)
            
            for glyph, n in enumerate(v, start=first):
                r[glyph] = n
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new Lookup object from the specified walker.
        >>> d = {1:100}
        >>> s = bestFromDict(d)
        >>> s0 = bestFromDict_0(d)
        >>> s2 = bestFromDict_2(d)
        >>> s4 = bestFromDict_4(d)
        >>> s6 = bestFromDict_6(d)
        >>> s8 = bestFromDict_8(d)
        >>> logger = utilities.makeDoctestLogger("fw")        
        >>> fw = Lookup.fromwalker
        >>> w = walker.StringWalker(s)
        >>> obj = fw(w, logger=logger)
        >>> w0 = walker.StringWalker(s0)
        >>> obj = fw(w0, logger=logger)
        >>> w2 = walker.StringWalker(s2)
        >>> obj = fw(w2, logger=logger)
        >>> w4 = walker.StringWalker(s4)
        >>> obj = fw(w4, logger=logger)
        >>> w6 = walker.StringWalker(s6)
        >>> obj = fw(w6, logger=logger)
        >>> w8 = walker.StringWalker(s8)
        >>> obj = fw(w8, logger=logger)
        >>> obj = fw(w6, logger=logger , _preferredFormat=6)
        Traceback (most recent call last):
        ...
        ValueError: Unknown lookup format 65535
        >>> dFF = {1:20, 65535:65534, 22:30}
        >>> s4FF = bestFromDict_4(dFF)
        >>> w4FF = walker.StringWalker(s4FF)
        >>> obj = fw(w4FF, logger=logger)
        """
        
        r = cls({}, **utilities.filterKWArgs(cls, kwArgs))
        
        if '_preferredFormat' in kwArgs:
            r._preferredFormat = kwArgs['_preferredFormat']
        
        format = w.unpack("H")
        
        if format == 0:
            r.update({i: n for i, n in enumerate(w.unpackRest("H"))})
        
        elif format == 2:
            for last, first, n in w.group("3H", w.unpack("2xH6x")):
                for i in range(first, last + 1):
                    r[i] = n
        
        elif format == 4:
            for last, first, offset in w.group("3H", w.unpack("2xH6x")):
                if first == last == 0xFFFF:
                    continue
                
                wSub = w.subWalker(offset)
                count = last - first + 1
                
                for i, n in enumerate(wSub.group("H", count), start=first):
                    r[i] = n
        
        elif format == 6:
            for i, n in w.group("2H", w.unpack("2xH6x")):
                r[i] = n
        
        elif format == 8:
            first, count = w.unpack("2H")
            
            for i, n in enumerate(w.group("H", count), start=first):
                r[i] = n
        
        else:
            raise ValueError("Unknown lookup format %d" % (format,))
        
        return r

# -----------------------------------------------------------------------------

if 0:
    def __________________(): pass

class Lookup_OutGlyph(Lookup):
    """
    A slight variation on the Lookup class where the values are also glyph
    indices.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_prevalidatedglyphsetvalues = {0xFFFF},
        item_renumberdirectvalues = True,
        item_valueisoutputglyph = True)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        This method calls the parent method, but ensures the noGaps keyword
        argument is set to True. This is required to prevent optimizations from
        causing incorrect output glyph mappings.
    
        >>> set = {4:20}
        >>> w = writer.LinkedWriter()
        >>> myStake = w.getNewStake()
        >>> a = Lookup_OutGlyph(set)
        >>> b = a.buildBinary(w)
        >>> c = a.buildBinary(w, _noGaps = True)
        
        """
        
        kwArgs['noGaps'] = True
        super(Lookup_OutGlyph, self).buildBinary(w, **kwArgs)

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
