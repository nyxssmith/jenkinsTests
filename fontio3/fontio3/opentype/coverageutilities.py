#
# coverageutilities.py
#
# Copyright © 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Utilities for reconciling a set of keys, a Coverage, and one or more ClassDef
objects. This is used for any subtable involving classes.
"""

# System imports
import collections

# -----------------------------------------------------------------------------

#
# Functions
#

def _handler_FFFF(glyphSet, covSet, cds, **kwArgs):
    # If a glyph falls in the font and nobody is there, does it exist?
    assert False, "This case can never arise!"

def _handler_FFFT(glyphSet, covSet, cds, **kwArgs):
    # If a glyph falls in the font and nobody is there, does it exist?
    assert False, "This case can never arise!"

def _handler_FFTF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.info((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in non-first ClassDefs only, "
          "and are not in the Coverage: %s"))
    
    return True

def _handler_FFTT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.info((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in non-first ClassDefs only, "
          "and are not in the Coverage. Note this table includes "
          "class-zero rules; these glyphs will not trigger them: %s"))
    
    return True

def _handler_FTFF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear only in the first ClassDef but "
              "are not present in the Coverage. They will be removed "
              "from the first ClassDef: %s"))
        
        else:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear only in the ClassDef and "
              "are not present in the Coverage: %s"))
            
            glyphSet = set()
    
        for g in glyphSet:
            del cds[0][g]
    
    return len(cds[0]) > 0

def _handler_FTFT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear only in the first ClassDef but "
              "are not present in the Coverage. They will be removed "
              "from the first ClassDef: %s"))
        
        else:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear only in the ClassDef and "
              "are not present in the Coverage: %s"))
            
            glyphSet = set()
    
    for g in glyphSet:
        del cds[0][g]
    
    return len(cds[0]) > 0

def _handler_FTTF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.warning((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in both the first ClassDef "
          "and at least one subsequent ClassDef, but "
          "are not present in the Coverage. They will be removed "
          "from the first ClassDef: %s"))
    
    for g in glyphSet:
        del cds[0][g]
    
    return len(cds[0]) > 0

def _handler_FTTT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.warning((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in both the first ClassDef "
          "and at least one subsequent ClassDef, but "
          "are not present in the Coverage. They will be removed "
          "from the first ClassDef; note that since there are "
          "keys with class 0 first, these glyphs may still end up "
          "participating in actions: %s"))
    
    for g in glyphSet:
        del cds[0][g]
    
    return len(cds[0]) > 0

def _handler_TFFF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage but are not in "
              "either ClassDef, and there are no class 0 keys. They will be "
              "removed from the Coverage: %s"))
        
        else:
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage but are not in "
              "the ClassDef, and there are no class 0 keys. They will be "
              "removed from the Coverage: %s"))
    
    covSet -= glyphSet
    return len(covSet) > 0

def _handler_TFFT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage but are not in "
              "either ClassDef, but this is OK since there are class 0 keys "
              "and all these glyphs will be mapped to class 0 for purposes "
              "of matching the first glyph: %s"))
        
        else:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage but are not in "
              "the ClassDef, but this is OK since there are class 0 keys "
              "and all these glyphs will be mapped to class 0 for purposes "
              "of matching the first glyph: %s"))
    
    return True

def _handler_TFTF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.warning((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in the Coverage but are not in "
          "the first ClassDef (though they do appear in one or more "
          "subsequent classes), and there are no class 0 keys. They will be "
          "removed from the Coverage: %s"))
    
    covSet -= glyphSet
    return len(covSet) > 0

def _handler_TFTT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.info((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in the Coverage but are not in "
          "the first ClassDef (though they do appear in one or more "
          "subsequent classes), but this is OK since there are class 0 keys "
          "and all these glyphs will be mapped to class 0 for purposes "
          "of matching the first glyph: %s"))
    
    return True

def _handler_TTFF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage and in only the "
              "first ClassDef: %s"))
        
        else:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage and the "
              "ClassDef: %s"))
    
    return True

def _handler_TTFT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        if len(cds) > 1:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage and in only the "
              "first ClassDef: %s"))
        
        else:
            logger.info((
              'Vxxxx',
              (loggerprefix, sorted(glyphSet),),
              "%sThe following glyphs appear in the Coverage and the "
              "ClassDef: %s"))
    
    return True

def _handler_TTTF(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.info((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in the Coverage and in both the "
          "first and subsequent ClassDefs: %s"))
    
    return True

def _handler_TTTT(glyphSet, covSet, cds, **kwArgs):
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    if logger is not None:
        logger.info((
          'Vxxxx',
          (loggerprefix, sorted(glyphSet),),
          "%sThe following glyphs appear in the Coverage and in both the "
          "first and subsequent ClassDefs: %s"))
    
    return True

_handlers = {
  (False, False, False, False): _handler_FFFF,
  (False, False, False, True): _handler_FFFT,
  (False, False, True, False): _handler_FFTF,
  (False, False, True, True): _handler_FFTT,
  (False, True, False, False): _handler_FTFF,
  (False, True, False, True): _handler_FTFT,
  (False, True, True, False): _handler_FTTF,
  (False, True, True, True): _handler_FTTT,
  (True, False, False, False): _handler_TFFF,
  (True, False, False, True): _handler_TFFT,
  (True, False, True, False): _handler_TFTF,
  (True, False, True, True): _handler_TFTT,
  (True, True, False, False): _handler_TTFF,
  (True, True, False, True): _handler_TTFT,
  (True, True, True, False): _handler_TTTF,
  (True, True, True, True): _handler_TTTT}

def _removeSuperfluousZeroes(cds, **kwArgs):
    """
    Given a sequence of ClassDef objects, go through each one and remove any
    explicit mappings to zero. These are always redundant.
    
    If a logger is provided it will be used to note any glyphs thus removed.
    
    >>> logger = utilities.makeDoctestLogger("rsz_test")
    >>> cd1 = classdef.ClassDef({15: 1, 38: 2, 39: 2})
    >>> cd2 = classdef.ClassDef({25: 1, 26: 1, 27: 2, 28: 0, 29: 2})
    >>> _removeSuperfluousZeroes([cd1, cd2], logger=logger)
    rsz_test - WARNING - The following glyphs explicitly mapped to class zero in the second ClassDef; they will be ignored: [28]
    >>> sorted(cd1)
    [15, 38, 39]
    >>> sorted(cd2)
    [25, 26, 27, 29]
    """
    
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    
    for i, cd in enumerate(cds):
        toDel = {k for k, v in cd.items() if not v}
        
        if toDel:
            if logger is not None:
                s = ("first", "second", "third", "%dth" % (i + 1,))[min(i, 3)]
                
                logger.warning((
                  'V0305',
                  (loggerprefix, s, sorted(toDel),),
                  "%sThe following glyphs explicitly mapped to class zero in "
                  "the %s ClassDef; they will be ignored: %s"))
            
            for k in toDel:
                del cd[k]

def _removeUnusedClasses_paired(keys, cds, **kwArgs):
    """
    Remove any key-value pairs from all the ClassDefs in cds if they're not
    represented at least one in the corresponding place in any key in keys.
    
    Returns True if caller is OK to proceed; False if one or more fatal errors
    occurred.
    
    >>> logger = utilities.makeDoctestLogger("rucp_test")
    >>> cd1 = classdef.ClassDef({15: 1, 38: 2, 39: 2, 40: 3})
    >>> cd2 = classdef.ClassDef({25: 1, 26: 1, 27: 2, 29: 2, 45: 3})
    >>> keys = {(1, 1), (2, 1), (1, 3)}
    >>> okToProceed = _removeUnusedClasses_paired(keys, [cd1, cd2], logger=logger)
    rucp_test - WARNING - The classes [3] in the first ClassDef are not used by any key, so they will be removed. This affects these glyphs: [40]
    rucp_test - WARNING - The classes [2] in the second ClassDef are not used by any key, so they will be removed. This affects these glyphs: [27, 29]
    
    >>> cd1.pprint()
    15: 1
    38: 2
    39: 2
    
    >>> cd2.pprint()
    25: 1
    26: 1
    45: 3
    """
    
    if not keys:
        return True
    
    logger = kwArgs.get('logger', None)
    loggerprefix = kwArgs.get('loggerprefix', '')
    keyLens = {len(k) for k in keys}
    
    if len(keyLens) != 1:
        if logger is not None:
            logger.error((
              'Vxxxx',
              (),
              "Keys are of inconsistent lengths"))
        
        return False
    
    if keyLens.pop() != len(cds):
        if logger is not None:
            logger.error((
              'Vxxxx',
              (),
              "Key lengths do not match the number of ClassDefs"))
        
        return False
    
    for i, cd in enumerate(cds):
        usedClasses = {k[i] for k in keys}
        toDelClasses = set(cd.values()) - usedClasses
        
        if not toDelClasses:
            continue
        
        toDelKeys = {k for k, v in cd.items() if v in toDelClasses}
        
        if logger is not None:
            s = ("first", "second", "third", "%dth" % (i + 1,))[min(i, 3)]
            
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(toDelClasses), s, sorted(toDelKeys)),
              "%sThe classes %s in the %s ClassDef are not used by any key, "
              "so they will be removed. This affects these glyphs: %s"))
        
        for k in toDelKeys:
            del cd[k]
    
    return True

def _removeUnusedClasses_single(keys, cd, **kwArgs):
    """
    """
    
    if not keys:
        return True
    
    allUsedClasses = {n for k in keys for n in k}
    allDefClasses = set(cd.values())
    unusedClasses = allDefClasses - allUsedClasses
    
    if unusedClasses:
        logger = kwArgs.get('logger', None)
        loggerprefix = kwArgs.get('loggerprefix', '')
        delGlyphs = {g for g, c in cd.items() if c in unusedClasses}
        
        if logger is not None:
            logger.warning((
              'Vxxxx',
              (loggerprefix, sorted(unusedClasses), sorted(delGlyphs)),
              "%sThe classes %s in the ClassDef are not used in any key, "
              "so the corresponding glyphs %s will be removed from it."))
        
        for g in delGlyphs:
            del cd[g]
    
    return True

def reconcile(covIter, keys, cds, **kwArgs):
    """
    
    >>> logger = utilities.makeDoctestLogger("reconcile_test")
    >>> cd1 = classdef.ClassDef({11: 1, 13: 2, 15: 3})
    >>> cd2 = classdef.ClassDef({12: 1, 14: 2, 16: 3})
    >>> keys = {(1, 2), (2, 2), (2, 3)}
    >>> covSet = set(cd1) | {17}
    >>> okToProceed, covSet = reconcile(covSet, keys, [cd1, cd2], logger=logger)
    reconcile_test - WARNING - The classes [3] in the first ClassDef are not used by any key, so they will be removed. This affects these glyphs: [15]
    reconcile_test - WARNING - The classes [1] in the second ClassDef are not used by any key, so they will be removed. This affects these glyphs: [12]
    reconcile_test - INFO - The following glyphs appear in non-first ClassDefs only, and are not in the Coverage: [14, 16]
    reconcile_test - WARNING - The following glyphs appear in the Coverage but are not in either ClassDef, and there are no class 0 keys. They will be removed from the Coverage: [15, 17]
    reconcile_test - INFO - The following glyphs appear in the Coverage and in only the first ClassDef: [11, 13]
    >>> okToProceed
    True
    >>> sorted(covSet)
    [11, 13]
    >>> cd1.pprint()
    11: 1
    13: 2
    >>> cd2.pprint()
    14: 2
    16: 3
    
    Now we set up exactly the same case, but this time we include a class 0
    key. Note the differences.
    
    >>> cd1 = classdef.ClassDef({11: 1, 13: 2, 15: 3})
    >>> cd2 = classdef.ClassDef({12: 1, 14: 2, 16: 3})
    >>> keys = {(0, 2), (1, 2), (2, 2), (2, 3)}
    >>> covSet = set(cd1) | {17}
    >>> okToProceed, covSet = reconcile(covSet, keys, [cd1, cd2], logger=logger)
    reconcile_test - INFO - The following glyphs appear in non-first ClassDefs only, and are not in the Coverage. Note this table includes class-zero rules; these glyphs will not trigger them: [12, 14, 16]
    reconcile_test - INFO - The following glyphs appear in the Coverage but are not in either ClassDef, but this is OK since there are class 0 keys and all these glyphs will be mapped to class 0 for purposes of matching the first glyph: [17]
    reconcile_test - INFO - The following glyphs appear in the Coverage and in only the first ClassDef: [11, 13, 15]
    >>> okToProceed
    True
    >>> sorted(covSet)
    [11, 13, 15, 17]
    >>> cd1.pprint()
    11: 1
    13: 2
    15: 3
    >>> cd2.pprint()
    12: 1
    14: 2
    16: 3
    """
    
    covSet = set(covIter)
    keys = set(keys)
    _removeSuperfluousZeroes(cds, **kwArgs)
    
    anyKeyHasC0 = any(c == 0 for k in keys for c in k)

    if anyKeyHasC0:
        # do not remove "unused" classes if any key uses class 0
        okToProceed = True
    else:
        if len(cds) > 1:
            okToProceed = _removeUnusedClasses_paired(keys, cds, **kwArgs)
        else:
            okToProceed = _removeUnusedClasses_single(keys, cds[0], **kwArgs)
    
        if not okToProceed:
            return False, covSet
    
    hasC0 = 0 in {k[0] for k in keys}
    allSubsequents = {k for cd in cds[1:] for k in cd}
    unionGlyphs = set(cds[0]) | allSubsequents | covSet
    d = collections.defaultdict(set)
    
    for g in unionGlyphs:
        t = (g in covSet, g in cds[0], g in allSubsequents, hasC0)
        d[t].add(g)

    for t in sorted(d):
        thisOK = _handlers[t](d[t], covSet, cds, **kwArgs)
        okToProceed = thisOK and okToProceed

    if hasC0 and not (covSet - set(cds[0])):
        logger = kwArgs.get('logger', None)
        if logger is not None:
            logger.error((
                'V1072',
                (),
                "Key uses class zero, "
                "but there are no extra glyphs in the coverage set."))
            okToProceed = False

    return okToProceed, covSet

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.opentype import classdef

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()

