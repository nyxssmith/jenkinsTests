#
# vdmxrecord.py
#
# Copyright © 2010-2013, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to single entries in the top-level VDMX object.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.fontmath import matrix
from fontio3.utilities import ScalerError, span2, oldRound
from fontio3.VDMX import group, ratio_v1, record

# -----------------------------------------------------------------------------

#
# Private functions
#

def _recalc(d, **kwArgs):
    editor = kwArgs['editor']
    
    if editor is None or (not editor.reallyHas(b'maxp')):
        return False, d
        
    fontGlyphCount = editor.maxp.numGlyphs
    scaler = kwArgs.get('scaler', None)
    r = d
    
    if (scaler is not None) and editor.reallyHas(b'glyf'):
        r = d.__deepcopy__()
        ratio = d.ratio
        
        if ratio.xRatio > 1 or ratio.yEndRatio > 1:
            xs = (ratio.xRatio * 1.0) / (ratio.yEndRatio * 1.0)
        else:
            xs = 1.0

        for p in d.group.keys():
            mat = matrix.Matrix((
              (xs * p, 0.0, 0.0),
              (0.0, p * 1.0, 0.0),
              (0.0, 0.0, 1.0)))
            
            try:
                scaler.setTransform(mat)
            except:
                raise ScalerError()
            
            r_ymax = -32768
            r_ymin = 32767
            
            for g in range(fontGlyphCount):
                try:
                    m = scaler.getOutlineMetrics(g)
                except:
                    raise ScalerError()
                
                r_ymax = max(r_ymax, int(oldRound(m.hi_y)))
                r_ymin = min(r_ymin, int(oldRound(m.lo_y)))
            
            r.group[p] = record.Record(yMin=r_ymin, yMax=r_ymax)            
            
    return (r != d), r

def _validate(d, **kwArgs):
    editor = kwArgs['editor']
    scaler = kwArgs.get('scaler', None)
    logger = kwArgs['logger']
    
    logger = logger.getChild(
      'vdmxrecord %d:%d' % (d.ratio.xRatio, d.ratio.yEndRatio))
    
    if editor is None or (not editor.reallyHas(b'maxp')):
        logger.warning((
            'W2503',
            (),
            "Unable to validate contents because there was no Editor "
            "or no 'maxp' table was available."))
        
        return False

    try:
        r = kwArgs.get('recalculateditem', None)
        diff = r != d
        
        if r is None:
            diff, r = _recalc(d, **kwArgs)
    
    except:
        logger.error((
          'V0554',
          (),
          "An error occured in the scaler during device metrics "
          "calculation, preventing validation."))
        
        return False
    
    if diff:
        fontGlyphCount = editor.maxp.numGlyphs
        
        for ppem, recalcrec in r.group.items():
            currec = d.group[ppem]
            
            if currec.yMax > recalcrec.yMax or currec.yMin < recalcrec.yMin:
                
                # VDMX is "too big"...only a warning. This is just
                # "inefficient"; it won't cause clipping.
                
                logger.warning((
                    'W2500',
                    ( ppem,
                      currec.yMax,
                      currec.yMin,
                      recalcrec.yMax,
                      recalcrec.yMin),
                    "Record for %d ppem [%d,%d] is larger than "
                    "the calculated value [%d,%d]."))
            
            if currec.yMax < recalcrec.yMax or currec.yMin > recalcrec.yMin:
                
                # VDMX is "too small"...this is an error, as it will cause
                # clipping under Windows. If we have a scaler, report on
                # individual glyphs.
                
                if scaler is not None:
                    try:
                        ratio = d.ratio
                        
                        if ratio.xRatio > 1 or ratio.yEndRatio > 1:
                            xs = (ratio.xRatio * 1.0) / (ratio.yEndRatio * 1.0)
                        else:
                            xs = 1
                        
                        mat = matrix.Matrix((
                          [xs * ppem, 0.0, 0.0],
                          [0.0, ppem * 1.0, 0.0],
                          [0.0, 0.0, 1.0]))
                        
                        try:
                            scaler.setTransform(mat)
                        except:
                            raise ScalerError()
                        
                        badYMax = span2.Span()
                        badYMin = span2.Span()
                        
                        for g in range(fontGlyphCount):
                            try:
                                m = scaler.getOutlineMetrics(g)
                            except:
                                raise ScalerError()
                            
                            if oldRound(m.hi_y) > currec.yMax:
                                badYMax.add(g)
                            
                            if oldRound(m.lo_y) < currec.yMin:
                                badYMin.add(g)
                                
                        if len(badYMax) > 0:
                            logger.error((
                                'V0775',
                                (currec.yMax, ppem, str(badYMax)),
                                "The following glyphs' actual yMax values "
                                "exceed the stored value of %d at %d ppem: "
                                "%s. Clipping may occur."))
                        
                        if len(badYMin) > 0:
                            logger.error((
                                'V0775',
                                (currec.yMin, ppem, str(badYMin)),
                                "The following glyphs' actual yMin values "
                                "exceed the stored value of %d at %d ppem: "
                                "%s. Clipping may occur."))

                    except ScalerError:
                        logger.error((
                          'V0554',
                          (),
                          "An error occured in the scaler during device "
                          "metrics calculation, preventing validation."))
                        
                        return False

                # Otherwise just report generically for the ppem (using MS
                # error code).
                
                else:
                    logger.error((
                        'E2500',
                        ( ppem,
                          currec.yMax,
                          currec.yMin,
                          recalcrec.yMax,
                          recalcrec.yMin),
                        "Record for %d ppem [%d,%d] is smaller than the "
                        "calculated value [%d,%d]. Clipping may occur."))
        return False

    logger.info((
        'P2500',
        (),
        "The VDMX data matches the expected values."))
    
    return True

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class VDMXRecord(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing a single record in the top-level VDMX object. These
    are simple objects with two attributes:
    
        ratio   A Ratio object (either version 0 or version 1). Because the
                specification recommends version 1 be used for all new VDMX
                tables, the default Ratio object is version 1.
        
        group   A Group object.
    
    Note that there are no fromwalker() or buildBinary() methods here; that
    job is handled by the top-level VDMX object.
    
    >>> _testingValues[1].pprint()
    Ratio:
      Start ratio: 2:1
      End ratio: 1:1
      Char set: All glyphs (0)
    Group:
      14 PPEM:
        Maximum y-value (in pixels): 10
        Minimum y-value (in pixels): -3
      15 PPEM:
        Maximum y-value (in pixels): 11
        Minimum y-value (in pixels): -3
      16 PPEM:
        Maximum y-value (in pixels): 11
        Minimum y-value (in pixels): -4
    """
    
    #
    # Class definition variables
    #

    objSpec = dict(
        obj_recalculatefunc_partial = _recalc,
        obj_validatefunc_partial = _validate)
    
    attrSpec = dict(
        ratio = dict(
            attr_followsprotocol = True,
            attr_initfunc = ratio_v1.Ratio,
            attr_label = "Ratio"),
        
        group = dict(
            attr_followsprotocol = True,
            attr_initfunc = group.Group,
            attr_label = "Group"))
    
    attrSorted = ('ratio', 'group')

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _rv = ratio_v1._testingValues
    _gv = group._testingValues
    
    _testingValues = (
        VDMXRecord(),
        VDMXRecord(ratio=_rv[1], group=_gv[1]),
        VDMXRecord(ratio=_rv[2], group=_gv[2]))
    
    del _rv, _gv

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
