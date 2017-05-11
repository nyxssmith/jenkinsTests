#
# strike.py
#
# Copyright © 2009, 2011-2014, 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single bitmap strike (i.e. one single PPEM).
"""

# System imports
import itertools
import logging
import operator

# Other imports
from fontio3.fontdata import deferreddictmeta
from fontio3.fontmath import matrix

from fontio3.sbit import (
  bigglyphmetrics,
  format1,
  format2,
  format5,
  format6,
  format7,
  format8,
  format9,
  format17,
  format18,
  format19,
  linemetrics,
  smallglyphmetrics)

from fontio3.utilities import pp, span2

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ddFactory(key, stk, d):
    logger = d['logger']
    ista = d['ista']
    wDat = d['wDat']
    flavor = d['flavor']
    r = None
    
    if logger is None:
        for firstGlyph, lastGlyph, wHeader in ista:
            if firstGlyph <= key <= lastGlyph:
                wHeader.reset()
                indexFormat, imageFormat, datOffset = wHeader.unpack("2HL")
                
                return _ddFactory_dispatch[(indexFormat, imageFormat)](
                  key,
                  stk,
                  d,
                  wHeader,
                  firstGlyph,
                  datOffset)
    
    else:
        for firstGlyph, lastGlyph, wHeader in ista:
            if firstGlyph <= key <= lastGlyph:
                wHeader.reset()
                
                if wHeader.length() < 8:
                    logger.error((
                      'V0472',
                      (key,),
                      "The indexSubHeader for glyph %d is "
                      "missing or incomplete."))
                    
                    return None
                
                indexFormat, imageFormat, datOffset = wHeader.unpack("2HL")
                
                if indexFormat < 1 or indexFormat > 5:
                    logger.error((
                      'V0473',
                      (key, indexFormat),
                      "Glyph %d has invalid indexFormat %d."))
                    
                    return None
                
                if flavor == 'CBDT':
                    if imageFormat not in {1, 2, 5, 6, 7, 8, 9, 17, 18, 19}:
                        logger.error((
                          'V0475',
                          (key, imageFormat),
                          "Glyph %d has invalid imageFormat %d."))
                    
                        return None
                
                else:
                    if imageFormat not in {1, 2, 5, 6, 7, 8, 9}:
                        logger.error((
                          'V0475',
                          (key, imageFormat),
                          "Glyph %d has invalid imageFormat %d."))
                    
                        return None
                
                t = (indexFormat, imageFormat)
                
                return _ddFactory_dispatch_validated[t](
                  key,
                  stk,
                  d,
                  wHeader,
                  firstGlyph,
                  datOffset,
                  logger = logger.getChild("glyph %d" % (key,)))
    
    return None

def _ddFactory_index1_image1(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image2(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image5(*args):
    raise ValueError("Cannot use imageFormat 5 with indexFormat 1!")

def _ddFactory_index1_image6(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image7(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image8(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image9(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index1_image17(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)))

def _ddFactory_index1_image18(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    return format18.Format18.fromwalker(w)

def _ddFactory_index1_image19(*args):
    raise ValueError("Cannot use imageFormat 19 with indexFormat 1!")

def _ddFactory_index2_image1(*args):
    raise ValueError("Cannot use imageFormat 1 with indexFormat 2!")

def _ddFactory_index2_image2(*args):
    raise ValueError("Cannot use imageFormat 2 with indexFormat 2!")

def _ddFactory_index2_image5(key, stk, d, wHeader, firstGlyph, datOffset):
    imageSize = wHeader.unpack("L")
    cache25 = d['caches'].setdefault('big_2_5', {})
    
    if firstGlyph not in cache25:
        fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
        cache25[firstGlyph] = fw(wHeader)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format5.Format5.fromwalker(
      w,
      bigMetrics = cache25[firstGlyph],
      bitDepth = stk.bitDepth)

def _ddFactory_index2_image6(*args):
    raise ValueError("Cannot use imageFormat 6 with indexFormat 2!")

def _ddFactory_index2_image7(*args):
    raise ValueError("Cannot use imageFormat 7 with indexFormat 2!")

def _ddFactory_index2_image8(key, stk, d, wHeader, firstGlyph, datOffset):
    imageSize = wHeader.unpack("L")
    cache25 = d['caches'].setdefault('big_2_5', {})
    
    if firstGlyph not in cache25:
        fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
        cache25[firstGlyph] = fw(wHeader)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format8.Format8.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index2_image9(*args):
    raise ValueError("Cannot use imageFormat 9 with indexFormat 2!")

def _ddFactory_index2_image17(*args):
    raise ValueError("Cannot use imageFormat 17 with indexFormat 2!")

def _ddFactory_index2_image18(*args):
    raise ValueError("Cannot use imageFormat 18 with indexFormat 2!")

def _ddFactory_index2_image19(key, stk, d, wHeader, firstGlyph, datOffset):
    imageSize = wHeader.unpack("L")
    cache219 = d['caches'].setdefault('big_2_19', {})
    
    if firstGlyph not in cache219:
        fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
        cache219[firstGlyph] = fw(wHeader)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format19.Format19.fromwalker(
      w,
      bigMetrics = cache219[firstGlyph])

def _ddFactory_index3_image1(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image2(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image5(*args):
    raise ValueError("Cannot use imageFormat 5 with indexFormat 3!")

def _ddFactory_index3_image6(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image7(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image8(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image9(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index3_image17(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)))

def _ddFactory_index3_image18(key, stk, d, wHeader, firstGlyph, datOffset):
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    return format18.Format18.fromwalker(w)

def _ddFactory_index3_image19(*args):
    raise ValueError("Cannot use imageFormat 19 with indexFormat 3!")

def _ddFactory_index4_image1(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image2(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image5(*args):
    raise ValueError("Cannot use imageFormat 5 with indexFormat 4!")

def _ddFactory_index4_image6(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image7(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image8(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image9(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromwalker(
      w,
      bitDepth = stk.bitDepth)

def _ddFactory_index4_image17(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)))

def _ddFactory_index4_image18(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        t = wHeader.group("2H", 1 + wHeader.unpack("L"))
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    return format18.Format18.fromwalker(w)

def _ddFactory_index4_image19(*args):
    raise ValueError("Cannot use imageFormat 19 with indexFormat 4!")

def _ddFactory_index5_image1(*args):
    raise ValueError("Cannot use imageFormat 1 with indexFormat 5!")

def _ddFactory_index5_image2(*args):
    raise ValueError("Cannot use imageFormat 2 with indexFormat 5!")

def _ddFactory_index5_image5(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex5 = d['caches'].setdefault('index_5', {})
    
    if firstGlyph not in cacheIndex5:
        imageSize = wHeader.unpack("L")
        cache25 = d['caches'].setdefault('big_2_5', {})
        
        if firstGlyph not in cache25:
            fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
            cache25[firstGlyph] = fw(wHeader)
        
        t = wHeader.group("H", wHeader.unpack("L"))
        dGroup = {g: i for i, g in enumerate(t)}
        cacheIndex5[firstGlyph] = (imageSize, cache25[firstGlyph], dGroup)
    
    imageSize, m, dGroup = cacheIndex5[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i = dGroup[key]
    toKey = imageSize * i
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format5.Format5.fromwalker(
      w,
      bigMetrics = cacheIndex5[firstGlyph][1],
      bitDepth = stk.bitDepth)

def _ddFactory_index5_image6(*args):
    raise ValueError("Cannot use imageFormat 6 with indexFormat 5!")

def _ddFactory_index5_image7(*args):
    raise ValueError("Cannot use imageFormat 7 with indexFormat 5!")

def _ddFactory_index5_image8(*args):
    raise ValueError("Cannot use imageFormat 8 with indexFormat 5!")

def _ddFactory_index5_image9(*args):
    raise ValueError("Cannot use imageFormat 9 with indexFormat 5!")

def _ddFactory_index5_image17(*args):
    raise ValueError("Cannot use imageFormat 17 with indexFormat 5!")

def _ddFactory_index5_image18(*args):
    raise ValueError("Cannot use imageFormat 18 with indexFormat 5!")

def _ddFactory_index5_image19(key, stk, d, wHeader, firstGlyph, datOffset):
    cacheIndex5 = d['caches'].setdefault('index_5', {})
    
    if firstGlyph not in cacheIndex5:
        imageSize = wHeader.unpack("L")
        cache219 = d['caches'].setdefault('big_2_19', {})
        
        if firstGlyph not in cache219:
            fw = bigglyphmetrics.BigGlyphMetrics.fromwalker
            cache219[firstGlyph] = fw(wHeader)
        
        t = wHeader.group("H", wHeader.unpack("L"))
        dGroup = {g: i for i, g in enumerate(t)}
        cacheIndex5[firstGlyph] = (imageSize, cache219[firstGlyph], dGroup)
    
    imageSize, m, dGroup = cacheIndex5[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i = dGroup[key]
    toKey = imageSize * i
    wDat = d['wDat']
    wDat.reset()
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format19.Format19.fromwalker(
      w,
      bigMetrics = cacheIndex5[firstGlyph][1])

_ddFactory_dispatch = {
  (1, 1): _ddFactory_index1_image1,
  (1, 2): _ddFactory_index1_image2,
  (1, 5): _ddFactory_index1_image5,
  (1, 6): _ddFactory_index1_image6,
  (1, 7): _ddFactory_index1_image7,
  (1, 8): _ddFactory_index1_image8,
  (1, 9): _ddFactory_index1_image9,
  (1, 17): _ddFactory_index1_image17,
  (1, 18): _ddFactory_index1_image18,
  (1, 19): _ddFactory_index1_image19,
  
  (2, 1): _ddFactory_index2_image1,
  (2, 2): _ddFactory_index2_image2,
  (2, 5): _ddFactory_index2_image5,
  (2, 6): _ddFactory_index2_image6,
  (2, 7): _ddFactory_index2_image7,
  (2, 8): _ddFactory_index2_image8,
  (2, 9): _ddFactory_index2_image9,
  (2, 17): _ddFactory_index2_image17,
  (2, 18): _ddFactory_index2_image18,
  (2, 19): _ddFactory_index2_image19,
  
  (3, 1): _ddFactory_index3_image1,
  (3, 2): _ddFactory_index3_image2,
  (3, 5): _ddFactory_index3_image5,
  (3, 6): _ddFactory_index3_image6,
  (3, 7): _ddFactory_index3_image7,
  (3, 8): _ddFactory_index3_image8,
  (3, 9): _ddFactory_index3_image9,
  (3, 17): _ddFactory_index3_image17,
  (3, 18): _ddFactory_index3_image18,
  (3, 19): _ddFactory_index3_image19,
  
  (4, 1): _ddFactory_index4_image1,
  (4, 2): _ddFactory_index4_image2,
  (4, 5): _ddFactory_index4_image5,
  (4, 6): _ddFactory_index4_image6,
  (4, 7): _ddFactory_index4_image7,
  (4, 8): _ddFactory_index4_image8,
  (4, 9): _ddFactory_index4_image9,
  (4, 17): _ddFactory_index4_image17,
  (4, 18): _ddFactory_index4_image18,
  (4, 19): _ddFactory_index4_image19,
  
  (5, 1): _ddFactory_index5_image1,
  (5, 2): _ddFactory_index5_image2,
  (5, 5): _ddFactory_index5_image5,
  (5, 6): _ddFactory_index5_image6,
  (5, 7): _ddFactory_index5_image7,
  (5, 8): _ddFactory_index5_image8,
  (5, 9): _ddFactory_index5_image9,
  (5, 17): _ddFactory_index5_image17,
  (5, 18): _ddFactory_index5_image18,
  (5, 19): _ddFactory_index5_image19}

def _ddFactory_index1_image1_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image2_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image6_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image7_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image8_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image9_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index1_image17_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      logger = logger)

def _ddFactory_index1_image18_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (4 * (key - firstGlyph)) + 8:
        logger.error((
          'V0476',
          (),
          "The index 1 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(4 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2L")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format18.Format18.fromvalidatedwalker(
      w,
      logger = logger)

def _ddFactory_index2_image5_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < 4:
        logger.error((
          'V0478',
          (),
          "The index 2 data is missing or incomplete."))
        
        return None
    
    imageSize = wHeader.unpack("L")
    cache25 = d['caches'].setdefault('big_2_5', {})
    
    if firstGlyph not in cache25:
        fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
        cache25[firstGlyph] = fvw(wHeader, logger=logger)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + toKey:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format5.Format5.fromvalidatedwalker(
      w,
      bigMetrics = cache25[firstGlyph],
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index2_image8_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < 4:
        logger.error((
          'V0478',
          (),
          "The index 2 data is missing or incomplete."))
        
        return None
    
    imageSize = wHeader.unpack("L")
    cache25 = d['caches'].setdefault('big_2_5', {})
    
    if firstGlyph not in cache25:
        fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
        cache25[firstGlyph] = fvw(wHeader, logger=logger)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + toKey:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format8.Format8.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index2_image19_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < 4:
        logger.error((
          'V0478',
          (),
          "The index 2 data is missing or incomplete."))
        
        return None
    
    imageSize = wHeader.unpack("L")
    cache219 = d['caches'].setdefault('big_2_19', {})
    
    if firstGlyph not in cache219:
        fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
        cache219[firstGlyph] = fvw(wHeader, logger=logger)
    
    toKey = imageSize * (key - firstGlyph)
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + toKey:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format19.Format19.fromvalidatedwalker(
      w,
      bigMetrics = cache219[firstGlyph],
      logger = logger)

def _ddFactory_index3_image1_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index3_image2_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index3_image6_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index3_image7_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index3_image8_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth, logger = logger)

def _ddFactory_index3_image9_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index3_image17_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      logger = logger)

def _ddFactory_index3_image18_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    if wHeader.length() < (2 * (key - firstGlyph)) + 4:
        logger.error((
          'V0479',
          (),
          "The index 3 data is missing or incomplete."))
        
        return None
    
    wHeader.skip(2 * (key - firstGlyph))
    off1, off2 = wHeader.unpack("2H")
    
    if off1 == off2:
        return None
    
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format18.Format18.fromvalidatedwalker(
      w,
      logger = logger)

def _ddFactory_index4_image1_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format1.Format1.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image2_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    
    if i >= (len(t) - 1):
        logger.error((
          'V0480',
          (),
          "The index 4 data is badly formatted."))
        
        return None
    
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format2.Format2.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image6_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format6.Format6.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image7_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format7.Format7.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image8_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format8.Format8.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image9_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format9.Format9.fromvalidatedwalker(
      w,
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index4_image17_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format17.Format17.fromvalidatedwalker(
      w,
      isHorizontal = (not (stk.flags & 0x02)),
      logger = logger)

def _ddFactory_index4_image18_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex4 = d['caches'].setdefault('index_4', {})
    
    if firstGlyph not in cacheIndex4:
        if wHeader.length() < 4:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        count = 1 + wHeader.unpack("L")
        
        if wHeader.length() < 4 * count:
            logger.error((
              'V0480',
              (),
              "The index 4 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("2H", count)
        dGroup = {obj[0]: (i, obj[1]) for i, obj in enumerate(t)}
        cacheIndex4[firstGlyph] = (t, dGroup)
    
    t, dGroup = cacheIndex4[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i, off1 = dGroup[key]
    off2 = t[i + 1][1]
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + off1:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + off1)
    w = wDat.subWalker(0, relative=True, newLimit=off2-off1)
    
    return format18.Format18.fromvalidatedwalker(
      w,
      logger = logger)

def _ddFactory_index5_image5_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex5 = d['caches'].setdefault('index_5', {})
    
    if firstGlyph not in cacheIndex5:
        if wHeader.length() < 4:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        imageSize = wHeader.unpack("L")
        cache25 = d['caches'].setdefault('big_2_5', {})
        
        if firstGlyph not in cache25:
            fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
            cache25[firstGlyph] = fvw(wHeader, logger=logger)
        
        if wHeader.length() < 4:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        count = wHeader.unpack("L")
        
        if wHeader.length() < 2 * count:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("H", count)
        dGroup = {g: i for i, g in enumerate(t)}
        cacheIndex5[firstGlyph] = (imageSize, cache25[firstGlyph], dGroup)
    
    imageSize, m, dGroup = cacheIndex5[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i = dGroup[key]
    toKey = imageSize * i
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + toKey:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format5.Format5.fromvalidatedwalker(
      w,
      bigMetrics = cacheIndex5[firstGlyph][1],
      bitDepth = stk.bitDepth,
      logger = logger)

def _ddFactory_index5_image19_validated(
  key,
  stk,
  d,
  wHeader,
  firstGlyph,
  datOffset,
  logger):
    
    cacheIndex5 = d['caches'].setdefault('index_5', {})
    
    if firstGlyph not in cacheIndex5:
        if wHeader.length() < 4:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        imageSize = wHeader.unpack("L")
        cache219 = d['caches'].setdefault('big_2_19', {})
        
        if firstGlyph not in cache219:
            fvw = bigglyphmetrics.BigGlyphMetrics.fromvalidatedwalker
            cache219[firstGlyph] = fvw(wHeader, logger=logger)
        
        if wHeader.length() < 4:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        count = wHeader.unpack("L")
        
        if wHeader.length() < 2 * count:
            logger.error((
              'V0481',
              (),
              "The index 5 data is missing or incomplete."))
            
            return None
        
        t = wHeader.group("H", count)
        dGroup = {g: i for i, g in enumerate(t)}
        cacheIndex5[firstGlyph] = (imageSize, cache219[firstGlyph], dGroup)
    
    imageSize, m, dGroup = cacheIndex5[firstGlyph]
    
    if key not in dGroup:
        return None
    
    i = dGroup[key]
    toKey = imageSize * i
    wDat = d['wDat']
    wDat.reset()
    
    if wDat.length() < datOffset + toKey:
        logger.error((
          'V0477',
          (),
          "Bitmap data missing or incomplete."))
        
        return None
    
    wDat.skip(datOffset + toKey)
    w = wDat.subWalker(0, relative=True, newLimit=imageSize)
    
    return format19.Format19.fromvalidatedwalker(
      w,
      bigMetrics = cacheIndex5[firstGlyph][1],
      logger = logger)

_ddFactory_dispatch_validated = {
  (1, 1): _ddFactory_index1_image1_validated,
  (1, 2): _ddFactory_index1_image2_validated,
  (1, 5): _ddFactory_index1_image5,
  (1, 6): _ddFactory_index1_image6_validated,
  (1, 7): _ddFactory_index1_image7_validated,
  (1, 8): _ddFactory_index1_image8_validated,
  (1, 9): _ddFactory_index1_image9_validated,
  (1, 17): _ddFactory_index1_image17_validated,
  (1, 18): _ddFactory_index1_image18_validated,
  (1, 19): _ddFactory_index1_image19,
  
  (2, 1): _ddFactory_index2_image1,
  (2, 2): _ddFactory_index2_image2,
  (2, 5): _ddFactory_index2_image5_validated,
  (2, 6): _ddFactory_index2_image6,
  (2, 7): _ddFactory_index2_image7,
  (2, 8): _ddFactory_index2_image8_validated,
  (2, 9): _ddFactory_index2_image9,
  (2, 17): _ddFactory_index2_image17,
  (2, 18): _ddFactory_index2_image18,
  (2, 19): _ddFactory_index2_image19_validated,
  
  (3, 1): _ddFactory_index3_image1_validated,
  (3, 2): _ddFactory_index3_image2_validated,
  (3, 5): _ddFactory_index3_image5,
  (3, 6): _ddFactory_index3_image6_validated,
  (3, 7): _ddFactory_index3_image7_validated,
  (3, 8): _ddFactory_index3_image8_validated,
  (3, 9): _ddFactory_index3_image9_validated,
  (3, 17): _ddFactory_index3_image17_validated,
  (3, 18): _ddFactory_index3_image18_validated,
  (3, 19): _ddFactory_index3_image19,
  
  (4, 1): _ddFactory_index4_image1_validated,
  (4, 2): _ddFactory_index4_image2_validated,
  (4, 5): _ddFactory_index4_image5,
  (4, 6): _ddFactory_index4_image6_validated,
  (4, 7): _ddFactory_index4_image7_validated,
  (4, 8): _ddFactory_index4_image8_validated,
  (4, 9): _ddFactory_index4_image9_validated,
  (4, 17): _ddFactory_index4_image17_validated,
  (4, 18): _ddFactory_index4_image18_validated,
  (4, 19): _ddFactory_index4_image19,
  
  (5, 1): _ddFactory_index5_image1,
  (5, 2): _ddFactory_index5_image2,
  (5, 5): _ddFactory_index5_image5_validated,
  (5, 6): _ddFactory_index5_image6,
  (5, 7): _ddFactory_index5_image7,
  (5, 8): _ddFactory_index5_image8,
  (5, 9): _ddFactory_index5_image9,
  (5, 17): _ddFactory_index5_image17,
  (5, 18): _ddFactory_index5_image18,
  (5, 19): _ddFactory_index5_image19_validated}

def _recalc_lineMetrics(stk, **kwArgs):
    # This method only recalculates the two line metrics fields, since they're
    # really the only fields amenable to recalculation in the first place.
    
    # First, we have to gather all the BigGlyphMetrics objects.
    allBGMs = {}  # binary string to live object
    fSToB = bigglyphmetrics.BigGlyphMetrics.fromsmallmetrics
    
    for glyphIndex, bitmapObj in stk.items():
        if bitmapObj is not None:
            m = bitmapObj.metrics
            
            if m.isSmall:
                m = fSToB(m)
            
            bs = m.binaryString()
            allBGMs[bs] = m
    
    hNewLM = stk.horiLineMetrics.recalculated(
      bigMetricsIterator = iter(allBGMs.values()))
    
    vNewLM = stk.vertLineMetrics.recalculated(
      bigMetricsIterator = iter(allBGMs.values()))
    
    if hNewLM == stk.horiLineMetrics and vNewLM == stk.vertLineMetrics:
        return False, stk
    
    newObj = stk.__copy__()
    newObj.horiLineMetrics = hNewLM
    newObj.vertLineMetrics = vNewLM
    return True, newObj

def _validate_bitDepth(n, **kwArgs):
    logger = kwArgs['logger']
    
    if n not in {1, 2, 4, 8, 32}:
        logger.error((
          'E0700',
          (n,),
          "The bitDepth must be 1, 2, 4, 8, or 32, but is %d."))
        
        return False
    
    return True

def _validate_colorRef(n, **kwArgs):
    logger = kwArgs['logger']
    
    if n != 0:
        logger.warning((
          'V0461',
          (n,),
          "The colorRef value should be zero (is %d)."))
    
    return True

def _validate_flags(n, **kwArgs):
    logger = kwArgs['logger']
    
    if n != 1 and n != 2:
        logger.error((
          'V0474',
          (n,),
          "The flags value (%d) is neither 1 nor 2."))
        
        return False
    
    return True

def _validate_lineMetrics(stk, **kwArgs):
    logger = kwArgs.pop('logger')
    r = True
    allBGMs = {}  # binary string to live object
    fSToB = bigglyphmetrics.BigGlyphMetrics.fromsmallmetrics
    
    for glyphIndex, bitmapObj in stk.items():
        if bitmapObj is not None:
            m = bitmapObj.metrics
            
            if m.isSmall:
                m = fSToB(m)
            
            try:
                bs = m.binaryString()
                allBGMs[bs] = m
            
            except ValueError:
                logger.error((
                  'V1106',
                  (glyphIndex,),
                  "One or more of the bitmap metrics for glyph %d "
                  "do not fit in 8 bits."))
                
                return False
    
    it = iter(allBGMs.values())
    kwArgs['logger'] = logger.getChild("horiz line metrics")
    r = stk.horiLineMetrics.isValid(bigMetricsIterator=it, **kwArgs) and r
    
    it = iter(allBGMs.values())
    kwArgs['logger'] = logger.getChild("vert line metrics")
    r = stk.vertLineMetrics.isValid(bigMetricsIterator=it, **kwArgs) and r
    
    return r

def _validate_PPEM(n, **kwArgs):
    logger = kwArgs['logger']
    
    try:
        n * 1.5
        isNumber = True
    
    except TypeError:
        isNumber = False
    
    if not isNumber:
        logger.error((
          'G0009',
          (n,),
          "The PPEM value '%s' is not a number."))
        
        return False
    
    if n != int(n):
        logger.error((
          'G0024',
          (n,),
          "The PPEM value %s is not an integer."))
        
        return False
    
    if n < 6 or n > 50:
        logger.warning((
          'V0466',
          (n,),
          "The ppem value of %d seems to be a bit out of the normal range."))
    
    return True

# -----------------------------------------------------------------------------

#
# Private classes
#

if 0:
    def __________________(): pass

class _FakePVS:
    def __contains__(self, key): return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Strike(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    Objects representing one entire PPEM of embedded bitmaps. These are
    deferred dicts mapping glyph indices to objects of one of the following
    types: Format1, Format2, Format5, Format6, Format7, Format8, or Format9.
    
    The following attributes are also present:
    
        bitDepth
        colorRef
        flags
        horiLineMetrics
        ppemX
        ppemY
        vertLineMetrics
    """
    
    #
    # Class definition variables
    #
    
    deferredDictSpec = dict(
        dict_keeplimit = 0,
        dict_recalculatefunc_withattrs = _recalc_lineMetrics,
        dict_validatefunc_partial = _validate_lineMetrics,
        item_createfunc = _ddFactory,
        item_createfuncneedsself = True,
        item_followsprotocol = True,
        item_prevalidatedglyphsetkeys = _FakePVS(),
        item_renumberdirectkeys = True,
        item_validatekwargsfunc = (
          lambda d, i:
          {'strike': d, 'glyphIndex': i}))
    
    attrSpec = dict(
        bitDepth = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Bit depth",
            attr_validatefunc = _validate_bitDepth),
        
        colorRef = dict(
            attr_initfunc = (lambda: 0),
            attr_label = "Color reference",
            attr_showonlyiftrue = True,
            attr_validatefunc = _validate_colorRef),
        
        flags = dict(
            attr_initfunc = (lambda: 1),
            attr_label = "Flags",
            attr_validatefunc = _validate_flags),
        
        horiLineMetrics = dict(
            attr_followsprotocol = True,
            attr_initfunc = linemetrics.LineMetrics,
            attr_label = "Horizontal line metrics",
            attr_recalculatedeep = False,  # handled by _validate_lineMetrics
            attr_validatefunc = (lambda *a,**k: True)),
        
        ppemX = dict(
            attr_initfunc = (lambda: 9),
            attr_label = "PPEM in x",
            attr_validatefunc = _validate_PPEM),
        
        ppemY = dict(
            attr_initfunc = (lambda: 9),
            attr_label = "PPEM in y",
            attr_validatefunc = _validate_PPEM),
        
        vertLineMetrics = dict(
            attr_followsprotocol = True,
            attr_initfunc = linemetrics.LineMetrics,
            attr_label = "Vertical line metrics",
            attr_recalculatedeep = False,  # handled by _validate_lineMetrics
            attr_validatefunc = (lambda *a,**k: True)))
    
    #
    # Methods
    #
    
    def _consistencyCheck(self, **kwArgs):
        """
        Make sure the bit depths all match, and that any composite bitmaps only
        refer to valid glyph indices and are non-circular. Returns True if
        everything's OK and False otherwise.

        A logger may be passed in as a keyword argument, and it will be used to
        report the glyph indices that are out-of-spec.
        """
        
        badDepths = set()
        badComps = set()
        badCycles = set()
        
        for glyphIndex, obj in self.items():
            if obj.imageFormat < 8:
                if obj.image.bitDepth != self.bitDepth:
                    badDepths.add(glyphIndex)
            
            else:
                for component in obj:
                    if component.glyphCode not in self:
                        badComps.add(glyphIndex)
                        break
                
                # do circular reference check
                try:
                    self._gatherComponentGlyphs(glyphIndex, set())
                except ValueError:
                    badCycles.add(glyphIndex)
        
        if (not badDepths) and (not badComps):
            return True
        
        logger = kwArgs.get('logger', None)
        
        if logger is not None:
            if badDepths:
                logger.error((
                  'V0226',
                  (str(sorted(badDepths)),),
                  "These glyphs have inconsistent bitDepths: %s"))
            
            if badComps:
                logger.error((
                  'V0227',
                  (str(sorted(badComps)),),
                  "These glyphs refer to nonexistent components: %s"))
            
            if badCycles:
                logger.error((
                  'V0228',
                  (str(sorted(badCycles)),),
                  "These glyphs have circular component refs: %s"))
        
        return False
    
    def _gatherComponentGlyphs(self, glyphIndex, accumulation):
        obj = self[glyphIndex]
        
        if obj.imageFormat >= 8:
            theseRefs = {part.glyphCode for part in obj}
            
            if theseRefs & accumulation:
                raise ValueError("Circular reference")
            
            accumulation.update(theseRefs)
            
            for subGlyph in theseRefs:
                self._gatherComponentGlyphs(subGlyph, accumulation)
    
    def actualIterator(self, firstGlyph, lastGlyph):
        """
        Returns a generator over glyph indices that have actual data
        associated with them.
        """
        
        for glyph in range(firstGlyph, lastGlyph + 1):
            if self.get(glyph) is not None:
                yield glyph
    
    def findMonospaceCandidates(self):
        """
        Returns a dict mapping binary strings for BigGlyphMetrics objects to
        span2.Spans of all monospace glyphs of those metrics. A monospace glyph
        is a glyph whose imageFormat is 5 -- this is arbitrary, but useful.
        """
        
        d = {}
        makeBig = bigglyphmetrics.BigGlyphMetrics.fromsmallmetrics
        
        for glyph, obj in self.items():
            if obj is not None and obj.imageFormat == 5:
                m = obj.metrics
                
                if m.isSmall:
                    m = makeBig(m)
                
                # use binaryString for ease of round-trip
                d.setdefault(m.binaryString(), span2.Span()).add(glyph)
        
        return d
    
    @classmethod
    def fromscaler(cls, scaler, ppemX, ppemY, bitDepth, **kwArgs):
        """
        Creates a new Strike using the passed-in scaler, which should have the
        font set. This method will set the pointsize, etc. according to xPpem
        and yPpem, and will build values for keys using Format1. The
        'useBigMetrics' keyword can be used to force the use of Format6
        instead.
        
        Other kwArg behaviors:
        
            glyphList   if supplied, ONLY the glyphs in this list will be
                        included in the strike. If it is not supplied, the
                        'editor' keyword MUST be supplied, and will be used to
                        obtain the number of glyphs from the maxp table, and
                        ALL glyphs will be included in the strike.
        """

        glyphList = kwArgs.get('glyphList', None)
        
        if glyphList is None:
            editor = kwArgs['editor']
            glyphList = range(editor.maxp.numGlyphs)

        if ppemX == ppemY:
            scaler.setPointsize(ppemX)
        
        else:
            m = matrix.Matrix([[ppemX, 0, 0], [0, ppemY, 0], [0, 0, 1]])
            scaler.setTransform(m)

        r = cls({}, ppemX=ppemX, ppemY=ppemY, bitDepth=bitDepth)
        
        if kwArgs.get('useBigMetrics', False):
            fmtfs = format6.Format6.fromscaler
        else:
            fmtfs = format1.Format1.fromscaler
        
        for g in glyphList:
            r[g] = fmtfs(scaler, g, bitDepth)

        return r
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):  # w is wLoc
        """
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("strike")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 16:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        istaOffset, istaByteLength, istaCount, colorRef = w.unpack("4L")
        relStart = w.getOffset(relative=True)
        
        if istaOffset <= relStart:
            logger.error((
              'V0458',
              (istaOffset,),
              "The indexSubTableArrayOffset value of %d is too small, "
              "placing it within the bitmapSizeTables."))
            
            return None
        
        if (istaOffset + istaByteLength) > (relStart + w.length()):
            logger.error((
              'V0459',
              (istaOffset, istaByteLength),
              "The indexSubTableArrayOffset value of %d and indexTablesSize "
              "value of %d, combined, are past the end of the table."))
            
            return None
        
        if not istaCount:
            logger.warning((
              'V0460',
              (),
              "The numberOfIndexSubTables is zero."))
        
        if colorRef:
            logger.warning((
              'V0461',
              (colorRef,),
              "The colorRef value should be zero (is %d)."))
        
        fvw = linemetrics.LineMetrics.fromvalidatedwalker
        
        horiLineMetrics = fvw(
          w,
          isHorizontal = True,
          logger = logger,
          **kwArgs)
        
        if horiLineMetrics is None:
            return None
        
        vertLineMetrics = fvw(
          w,
          isHorizontal = False,
          logger = logger,
          **kwArgs)
        
        if vertLineMetrics is None:
            return None
        
        if w.length() < 8:
            logger.error((
              'V0462',
              (),
              "The latter portion of the bitmapSizeTable is "
              "missing or incomplete."))
            
            return None
        
        firstGlyph, lastGlyph, ppemX, ppemY, bitDepth, flags = w.unpack("2H4B")
        
        if firstGlyph > lastGlyph:
            logger.error((
              'V0463',
              (firstGlyph, lastGlyph),
              "The firstGlyph (%d) is greater than the lastGlyph (%d)."))
            
            return None
        
        fontGlyphCount = kwArgs['fontGlyphCount']
        
        if lastGlyph >= fontGlyphCount:
            logger.warning((
              'V0464',
              (lastGlyph, fontGlyphCount),
              "The endGlyphIndex (%d) is greater than or equal to "
              "the font's glyph count (%d)."))
        
        if ppemX != ppemY:
            logger.info((
              'V0465',
              (ppemX, ppemY),
              "The ppemX value (%d) does not equal the ppemY value (%d)."))
        
        if min(ppemX, ppemY) < 6 or max(ppemX, ppemY) > 50:
            logger.warning((
              'V0466',
              (ppemX, ppemY),
              "The ppemX (%d) and ppemY (%d) values seem to be "
              "a bit out of the normal range."))
        
        if bitDepth not in {1, 2, 4, 8, 32}:
            logger.error((
              'E0700',
              (bitDepth,),
              "The bitDepth value should be 1, 2, 4, 8, or 32, but is %d."))
            
            return None
        
        if flags != 1 and flags != 2:
            logger.error((
              'V0474',
              (flags,),
              "The flags value (%d) is neither 1 nor 2."))
            
            return None
        
        if istaCount == 0:
            return cls(
              colorRef = colorRef,
              horiLineMetrics = horiLineMetrics,
              vertLineMetrics = vertLineMetrics,
              ppemX = ppemX,
              ppemY = ppemY,
              bitDepth = bitDepth,
              flags = flags)
        
        wISTA = w.subWalker(istaOffset)
        
        if wISTA.length() < 8 * istaCount:
            logger.error((
              'V0467',
              (),
              "The index subtable array is missing "
              "or only partially present."))
            
            return None
        
        istaRaw = wISTA.group("2HL", istaCount)
        istaRawSorted = tuple(sorted(istaRaw))
        
        if istaRaw != istaRawSorted:
            logger.warning((
              'V0468',
              (),
              "The indexSubTableArray is not sorted by firstGlyphIndex."))
            
            istaRaw = istaRawSorted
        
        if any(t[0] > t[1] for t in istaRaw):
            logger.error((
              'V0469',
              (),
              "At least one entry in the indexSubTableArray has its "
              "firstGlyphIndex greater than its lastGlyphIndex."))
            
            return None
        
        if istaRaw[0][0] != firstGlyph:
            logger.warning((
              'V0470',
              (firstGlyph, istaRaw[0][0]),
              "The bitmapSizeTable shows the first glyph is %d, but the "
              "first indexSubTableArray record's firstGlyphIndex is %d."))
            
            return None
        
        if istaRaw[-1][1] != lastGlyph:
            logger.warning((
              'V0471',
              (lastGlyph, istaRaw[-1][1]),
              "The bitmapSizeTable shows the last glyph is %d, but the "
              "last indexSubTableArray record's lasstGlyphIndex is %d."))
            
            return None
        
        ista = [(a, b, wISTA.subWalker(c)) for a, b, c in istaRaw]
        otki = iter(range(firstGlyph, lastGlyph + 1))
        
        ce = dict(
          oneTimeKeyIterator = otki,
          logger = logger,
          wDat = kwArgs['wDat'],
          ista = ista,
          caches = {},
          flavor = kwArgs.get('flavor', 'EBDT'))
        
        return cls(
          creationExtras = ce,
          colorRef = colorRef,
          horiLineMetrics = horiLineMetrics,
          vertLineMetrics = vertLineMetrics,
          ppemX = ppemX,
          ppemY = ppemY,
          bitDepth = bitDepth,
          flags = flags)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):  # w is wLoc
        """
        """
        
        istaOffset, istaCount, colorRef = w.unpack("L4x2L")  # ignore size
        fw = linemetrics.LineMetrics.fromwalker
        horiLineMetrics = fw(w, isHorizontal=True)
        vertLineMetrics = fw(w, isHorizontal=False)
        firstGlyph, lastGlyph, ppemX, ppemY, bitDepth, flags = w.unpack("2H4B")
        wISTA = w.subWalker(istaOffset)
        istaRaw = wISTA.group("2HL", istaCount)
        ista = [(a, b, wISTA.subWalker(c)) for a, b, c in istaRaw]
        otki = iter(range(firstGlyph, lastGlyph + 1))
        
        ce = dict(
          oneTimeKeyIterator = otki,
          logger = None,
          wDat = kwArgs['wDat'],
          ista = ista,
          caches = {},
          flavor = kwArgs.get('flavor', 'EBDT'))
        
        return cls(
          creationExtras = ce,
          colorRef = colorRef,
          horiLineMetrics = horiLineMetrics,
          vertLineMetrics = vertLineMetrics,
          ppemX = ppemX,
          ppemY = ppemY,
          bitDepth = bitDepth,
          flags = flags)
    
    def stats(self, p=None):
        """
        """
        
        if p is None:
            p = pp.PP()
        
        for first, last, w in self._creationExtras['ista']:
            w.reset()
            indexFormat, imageFormat, datOffset = w.unpack("2HL")
            t = (first, last, indexFormat, imageFormat, datOffset)
            p("Range (%d, %d) has index fmt %d, image fmt %d, data %08X" % t)

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
    if __debug__:
        _test()
        #_myTest()
