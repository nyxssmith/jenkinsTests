#
# dictkeyutils.py
#
# Copyright © 2009-2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module contains key-related utilities, used for ordering keys in mappings
during ``pprint()`` output.
"""

# System imports
import operator

# -----------------------------------------------------------------------------

#
# Private functions
#

def _makeKeysTheLongWay(self, **d):
    
    # In Python 3 type ordering is completely strict, so we need to
    # separate the keys into groups of like kind.
    
    numLike = set()
    other = set()
    hasNone = False
    v = []
    hasKeyFunc = 'keyFunc' in d
    
    for k in self:
        try:
            k * 1.5
            numLike.add(k)
        
        except TypeError:
            if k is None:
                hasNone = True
            elif hasKeyFunc:
                other.add(k)
            else:
                other.add((str(k), k))
    
    if numLike:
        v.extend(sorted(numLike, reverse=d['reverse'], key=d['keyFunc']))
    
    if other:
        if hasKeyFunc:
            v.extend(sorted(other, reverse=d['reverse'], key=d['keyFunc']))
        
        else:
            oSorted = sorted(
              other,
              reverse = d['reverse'],
              key = operator.itemgetter(0))
            
            v.extend(k for s, k in oSorted)
    
    if hasNone:
        v.append(None)
    
    return v

def _mksv_hasNM_hasLF_noPre_deep(self, **d):
    nm = d['nm']
    lf = d['lf']
    lfno = d['lfno']
    v = [None] * len(self)
    
    if lfno:
        for i, key in enumerate(self):
            oldNamer = key.getNamer()
            key.setNamer(nm)
            
            v[i] = (
              (repr(key) if key is None else lf(str(key), self[key])),
              key)
            
            key.setNamer(oldNamer)
    
    else:
        for i, key in enumerate(self):
            oldNamer = key.getNamer()
            key.setNamer(nm)
            v[i] = ((repr(key) if key is None else lf(str(key))), key)
            key.setNamer(oldNamer)
    
    if not d['noSort']:
        v.sort()
    
    return v

def _mksv_hasNM_hasLF_noPre_dir(self, **d):
    nmbf = d['nm'].bestNameForGlyphIndex
    lf = d['lf']
    lfno = d['lfno']
    
    if lfno:
        v = [
          ((repr(key) if key is None else lf(nmbf(key), self[key])), key)
          for key in self]
    
    else:
        v = [
          ((repr(key) if key is None else lf(nmbf(key))), key)
          for key in self]
    
    if not d['noSort']:
        v.sort()
    
    return v

def _mksv_hasNM_hasLF_pre_deep(self, **d):
    nm = d['nm']
    lf = d['lf']
    v = [None] * len(self)
    
    if d['noSort']:
        kv = list(self)
    else:
        kv = _makeKeysTheLongWay(self, **d)
    
    if d['lfno']:
        for i, key in enumerate(kv):
            if key is not None:
                oldNamer = key.getNamer()
                key.setNamer(nm)
                v[i] = (lf(str(key), self[key]), key)
                key.setNamer(oldNamer)
            
            else:
                v[i] = ("None", None)
    
    else:
        for i, key in enumerate(kv):
            if key is not None:
                oldNamer = key.getNamer()
                key.setNamer(nm)
                v[i] = (lf(str(key)), key)
                key.setNamer(oldNamer)
            
            else:
                v[i] = ("None", None)
    
    return v

def _mksv_hasNM_hasLF_pre_dir(self, **d):
    nmbf = d['nm'].bestNameForGlyphIndex
    lf = d['lf']
    
    if d['noSort']:
        kv = list(self)
    else:
        kv = _makeKeysTheLongWay(self, **d)
    
    if d['lfno']:
        return [
          ((repr(k) if k is None else lf(nmbf(k), self[k])), k)
          for k in kv]
    
    else:
        return [
          ((repr(k) if k is None else lf(nmbf(k))), k)
          for k in kv]

def _mksv_hasNM_noLF_noPre_deep(self, **d):
    nm = d['nm']
    v = [None] * len(self)
    
    for i, key in enumerate(self):
        oldNamer = key.getNamer()
        key.setNamer(nm)
        v[i] = (str(key), key)
        key.setNamer(oldNamer)
    
    if not d['noSort']:
        v.sort()
    
    return v

def _mksv_hasNM_noLF_noPre_dir(self, **d):
    nmbf = d['nm'].bestNameForGlyphIndex
    
    return (list if d['noSort'] else sorted)(
      ((repr(key) if key is None else nmbf(key)), key)
      for key in self)

def _mksv_hasNM_noLF_pre_deep(self, **d):
    nm = d['nm']
    v = [None] * len(self)
    
    if d['noSort']:
        kv = list(self)
    else:
        kv = _makeKeysTheLongWay(self, **d)
    
    for i, key in enumerate(kv):
        if key is not None:
            oldNamer = key.getNamer()
            key.setNamer(nm)
            v[i] = (str(key), key)
            key.setNamer(oldNamer)
        
        else:
            v[i] = ("None", None)
    
    return v

def _mksv_hasNM_noLF_pre_dir(self, **d):
    nmbf = d['nm'].bestNameForGlyphIndex
    
    if d['noSort']:
        kv = list(self)
    else:
        kv = _makeKeysTheLongWay(self, **d)
    
    return [((repr(k) if k is None else nmbf(k)), k) for k in kv]

def _mksv_noNM_hasLF_noPre(self, **d):
    lf = d['lf']
    lfno = d['lfno']
    
    if lfno:
        g = (
          ((repr(key) if key is None else lf(key, self[key])), key)
          for key in self)
    
    else:
        g = (
          ((repr(key) if key is None else lf(key)), key)
          for key in self)
    
    return (list if d['noSort'] else sorted)(g)

def _mksv_noNM_hasLF_pre(self, **d):
    lf = d['lf']
    
    if d['noSort']:
        kv = list(self)
    else:
        kv = _makeKeysTheLongWay(self, **d)
    
    if d['lfno']:
        v = [((repr(k) if k is None else lf(k, self[k])), k) for k in kv]
    else:
        v = [((repr(k) if k is None else lf(k)), k) for k in kv]
    
    return v

def _mksv_noNM_noLF_noPre(self, **d):
    return (list if d['noSort'] else sorted)((repr(key), key) for key in self)

def _mksv_noNM_noLF_pre(self, **d):
    if d['noSort']:
        v = [(repr(k), k) for k in self]
    else:
        v = [(repr(k), k) for k in _makeKeysTheLongWay(self, **d)]
    
    return v

# -----------------------------------------------------------------------------

#
# Dispatch tables
#

_mksv_dispatch = {
  (False, False, False): _mksv_noNM_noLF_noPre,
  (False, False, True): _mksv_noNM_noLF_pre,
  (False, True, False): _mksv_noNM_hasLF_noPre,
  (False, True, True): _mksv_noNM_hasLF_pre,
  (True, False, False, False, False): _mksv_noNM_noLF_noPre,
  (True, False, False, False, True): _mksv_hasNM_noLF_noPre_dir,
  (True, False, False, True, False): _mksv_hasNM_noLF_noPre_deep,
  (True, False, True, False, False): _mksv_noNM_noLF_pre,
  (True, False, True, False, True): _mksv_hasNM_noLF_pre_dir,
  (True, False, True, True, False): _mksv_hasNM_noLF_pre_deep,
  (True, True, False, False, False): _mksv_noNM_hasLF_noPre,
  (True, True, False, False, True): _mksv_hasNM_hasLF_noPre_dir,
  (True, True, False, True, False): _mksv_hasNM_hasLF_noPre_deep,
  (True, True, True, False, False): _mksv_noNM_hasLF_pre,
  (True, True, True, False, True): _mksv_hasNM_hasLF_pre_dir,
  (True, True, True, True, False): _mksv_hasNM_hasLF_pre_deep}

# -----------------------------------------------------------------------------

#
# Public functions
#

def makeKeyStringsList(origDict, DS, nm):
    """
    Make a list of dict key strings.
    
    :param origDict: The dict whose keys will be sorted
    :param DS: The ``mapSpec`` or ``deferredDictSpec``
    :param nm: The :py:class:`~fontio3.utilities.namer.Namer` to use
    
    The strings in the returned list and their ordering will take into account
    all of the various controls present that affect them, such as::
    
        item_pprintlabelpresort
        item_pprintlabelpresortreverse
        item_pprintlabelpresortfunc
        item_pprintlabelfunc
        item_pprintlabelfuncneedsobj
        item_renumberdeepkeys
        item_renumberdeepkeysnoshrink
        item_renumberdirectkeys
        item_usenamerforstr
        item_pprintlabelnosort
    """
    
    presort = DS.get('item_pprintlabelpresort', False)
    presortRev = DS.get('item_pprintlabelpresortreverse', False)
    presortFunc = DS.get('item_pprintlabelpresortfunc', None)
    ps = presort or presortRev or (presortFunc is not None)
    labelFunc = DS.get('item_pprintlabelfunc', None)
    labelFuncNeedsObj = DS.get('item_pprintlabelfuncneedsobj', False)
    
    keyDeep = DS.get(
      'item_renumberdeepkeys',
      DS.get('item_keyfollowsprotocol', False))
    
    keyDeepNoShrink = DS.get('item_renumberdeepkeysnoshrink', False)
    
    keyDirect = DS.get('item_renumberdirectkeys', False)
    intendsToUseNamer = DS.get('item_usenamerforstr', False)
    
    hasNM = nm is not None
    hasLF = labelFunc is not None
    
    d = {
      'reverse': presortRev,
      'keyFunc': presortFunc,
      'noSort': DS.get('item_pprintlabelnosort', False)}
    
    if hasLF:
        d['lf'] = labelFunc
        d['lfno'] = labelFuncNeedsObj
    
    if hasNM:
        d['nm'] = nm
        dk = (True, hasLF, ps, (keyDeep or keyDeepNoShrink), keyDirect)
    
    else:
        if (keyDirect or keyDeep or keyDeepNoShrink) and intendsToUseNamer:
            ps = True  # force this
        
        dk = (False, hasLF, ps)
    
    return _mksv_dispatch[dk](origDict, **d)

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
