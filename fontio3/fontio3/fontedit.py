#
# fontedit.py
#
# Copyright © 2004-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Top-level support for displaying and editing font data.
"""

# System imports
import itertools
import io
import logging
import operator
import tempfile
import pickle
import os
import struct
from xml.dom import minidom
from xml.parsers.expat import ExpatError
import zlib

# Other imports
from fontio3 import (
  cvt,
  fmtx,
  fpgm,
  hhea,
  hmtx,
  loca,
  LTSH,
  MTet,
  MTsc,
  prep,
  utilitiesbackend,
  vmtx,
  VORG)

from fontio3.ADFH import ADFH
from fontio3.ankr import ankr
from fontio3.avar import avar
from fontio3.BASE import BASE
from fontio3.bsln import bsln
from fontio3.CFF import CFF
from fontio3.cmap import cmap
from fontio3.COLR import COLR
from fontio3.CPAL import CPAL
from fontio3.cvar import cvar
from fontio3.DSIG import DSIG
from fontio3.EBSC import EBSC
from fontio3.fdsc import fdsc
from fontio3.feat import feat
from fontio3 import fmtx
from fontio3.fontdata import binary, deferreddictmeta
from fontio3.fontmath import matrix
from fontio3.fvar import fvar
from fontio3.gasp import gasp
from fontio3.GDEF import GDEF
from fontio3.glyf import glyf
from fontio3.GPOS import GPOS
from fontio3.GSUB import GSUB
from fontio3.gvar import gvar
from fontio3.hdmx import hdmx, ppemdict
from fontio3.head import head
from fontio3.hints import validate
from fontio3.HVAR import HVAR
from fontio3.JSTF import JSTF
from fontio3.kern import kern
from fontio3.kerx import kerx
from fontio3.lcar import lcar
from fontio3.maxp import maxp
from fontio3.meta import meta
from fontio3.mort import mort
from fontio3.morx import morx
from fontio3.MTad import MTad
from fontio3.MTap import MTap
from fontio3.MTcc import MTcc
from fontio3.MTcl import MTcl
from fontio3.MTsf import MTsf
from fontio3.MVAR import MVAR
from fontio3.name import name
from fontio3.opbd import opbd
from fontio3.opentype.living_variations import IVS
from fontio3.OS_2 import OS_2
from fontio3.PCLT import PCLT
from fontio3.post import post
from fontio3.prop import prop
from fontio3.sbit import sbit
from fontio3.sbix import sbix
from fontio3.SPRK import SPRK
from fontio3.STAT import STAT
from fontio3.trak import trak
from fontio3.TSI import TSILoc, TSIDat, TSI5

from fontio3.utilities import (
  bsh,
  filewalkerbit,
  namer,
  oldRound,
  ScalerError,
  walkerbit,
  writer)

from fontio3.VDMX import VDMX, record
from fontio3.VVAR import VVAR
from fontio3.vhea import vhea
from fontio3.Zapf import Zapf

# -----------------------------------------------------------------------------

#
# Constants (including dispatch tables)
#

_makerInfo = {
  b'ADFH': (ADFH.ADFH, (lambda x: {})),
  b'ankr': (ankr.Ankr.fromwalker, (lambda x: {})),
  b'avar': (avar.Avar.fromwalker, (lambda x: {'editor': x})),
  b'BASE': (BASE.BASE.fromwalker, (lambda x: {})),
  
  b'bdat': (
    sbit.Sbit.fromwalker,
    (lambda x: {'wLoc': x.getRawWalker(b'bloc'), 'flavor': 'bdat'})),
  
  b'bsln': (
    bsln.Bsln.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'CBDT': (
    sbit.Sbit.fromwalker,
    (lambda x: {'wLoc': x.getRawWalker(b'CBLC'), 'flavor': 'CBDT'})),
  
  b'CFF ': (CFF.CFF.fromwalker, (lambda x: {})),
  b'cmap': (cmap.Cmap.fromwalker, (lambda x: {})),
  b'COLR': (COLR.COLR.fromwalker, (lambda x: {})),
  b'CPAL': (CPAL.CPAL, (lambda x: {})),
  b'cvar': (cvar.Cvar.fromwalker, (lambda x: {'editor': x})),
  b'cvt ': (cvt.Cvt.fromwalker, (lambda x: {})),
  b'DSIG': (DSIG.DSIG.fromwalker, (lambda x: {})),
  
  b'EBDT': (
    sbit.Sbit.fromwalker,
    (lambda x: {'wLoc': x.getRawWalker(b'EBLC'), 'flavor': 'EBDT'})),
  
  b'EBSC': (EBSC.EBSC.fromwalker, (lambda x: {})),
  b'fdsc': (fdsc.Fdsc.fromwalker, (lambda x: {})),
  b'feat': (feat.Feat.fromwalker, (lambda x: {})),
  b'fmtx': (fmtx.Fmtx.fromwalker, (lambda x: {})),
  b'fpgm': (fpgm.Fpgm.fromwalker, (lambda x: {})),
  b'fvar': (fvar.Fvar.fromwalker, (lambda x: {'editor': x})),
  b'gasp': (gasp.Gasp.fromwalker, (lambda x: {})),
  b'GDEF': (GDEF.GDEF, (lambda x: {'editor': x})),
  b'glyf': (glyf.Glyf.fromwalker, (lambda x: {'locaObj': x.loca})),
  b'GPOS': (GPOS.GPOS, (lambda x: {'GDEF': x.GDEF} if b'GDEF' in x else {})),
  b'GSUB': (GSUB.GSUB, (lambda x: {'editor': x})),
  b'gvar': (gvar.Gvar.fromwalker, (lambda x: {'editor': x})),
  
  b'hdmx': (
    hdmx.Hdmx.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'head': (head.Head.fromwalker, (lambda x: {})),
  b'hhea': (hhea.Hhea.fromwalker, (lambda x: {})),
  
  b'hmtx': (
    hmtx.Hmtx.fromwalker,
    (lambda x: {
      'fontGlyphCount': x.maxp.numGlyphs,
      'numLongMetrics': x.hhea.numLongMetrics})),

  b'HVAR': (
    HVAR.HVAR.fromwalker,
    (lambda x: {
      'axisOrder': x.fvar.axisOrder,
      'editor': x})),  

  b'JSTF': (JSTF.JSTF.fromwalker, (lambda x: {'editor': x})),
  b'kern': (kern.Kern.fromwalker, (lambda x: {})),
  b'kerx': (
    kerx.Kerx.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),

  b'lcar': (
    lcar.Lcar.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'loca': (
    loca.Loca.fromwalker,
    (lambda x: {'isLongOffsets': bool(x.head.indexToLocFormat)})),
  
  b'LTSH': (
    LTSH.LTSH.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'maxp': (maxp.Maxp, (lambda x: {})),
  b'meta': (meta.Meta.fromwalker, (lambda x: {})),
  b'mort': (mort.Mort.fromwalker, (lambda x: {})),
  b'morx': (
    morx.Morx.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  b'MTad': (MTad.MTad.fromwalker, (lambda x: {})),
  b'MTap': (MTap.MTap, (lambda x: {'editor': x})),
  b'MTcc': (MTcc.MTcc.fromwalker, (lambda x: {})),
  b'MTcl': (MTcl.MTcl.fromwalker, (lambda x: {})),
  
  b'MTet': (
    MTet.MTet.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'MTsc': (MTsc.MTsc.fromwalker, (lambda x: {})),
  b'MTsf': (MTsf.MTsf.fromwalker, (lambda x: {'editor': x})),
  b'MVAR': (MVAR.MVAR.fromwalker, (lambda x: {'axisOrder': x.fvar.axisOrder})),  
  b'name': (name.Name.fromwalker, (lambda x: {})),
  
  b'opbd': (
    opbd.Opbd.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'OS/2': (OS_2.OS_2, (lambda x: {})),
  b'PCLT': (PCLT.PCLT.fromwalker, (lambda x: {})),
  b'post': (post.Post.fromwalker, (lambda x: {})),
  b'prep': (prep.Prep.fromwalker, (lambda x: {})),
  b'prop': (prop.Prop, (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'sbix': (
    sbix.Sbix.fromwalker,
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'SPRK': (SPRK.SPRK, (lambda x: {})),
  b'STAT': (STAT.STAT, (lambda x: {})),
  b'trak': (trak.Trak.fromwalker, (lambda x: {})),
  b'TSI0': (TSILoc.TSILoc.fromwalker, (lambda x: {})),
  b'TSI1': (TSIDat.TSIDat.fromwalker, (lambda x: {'flavor':'TSI0', 'TSILocTable':x.TSI0})),
  b'TSI2': (TSILoc.TSILoc.fromwalker, (lambda x: {})),
  b'TSI3': (TSIDat.TSIDat.fromwalker, (lambda x: {'flavor':'TSI2', 'TSILocTable':x.TSI2})),
  b'TSI5': (TSI5.TSI5.fromwalker, (lambda x: {'dataTable': x.TSI1})),
  b'VDMX': (VDMX.VDMX.fromwalker, (lambda x: {})),
  b'vhea': (vhea.Vhea, (lambda x: {})),
  
  b'vmtx': (
    vmtx.Vmtx.fromwalker,
    (lambda x: {'numLongMetrics': x.vhea.numLongMetrics})),
  
  b'VORG': (VORG.VORG.fromwalker, (lambda x: {})),
  b'VVAR': (
    VVAR.VVAR.fromwalker,
    (lambda x: {
      'axisOrder': x.fvar.axisOrder,
      'editor': x})),  

  b'Zapf': (
    Zapf.Zapf.fromwalker, 
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}))
  }

#
# IMPORTANT NOTE:
#
# The format of the entries in _validatedMakerInfo used to be the same as those
# in _makerInfo. THIS IS NO LONGER TRUE!! There is an additional argument in-
# between the two original arguments, a sequence of tags to be checked via the
# reallyHas() method before the function is called.
#

_validatedMakerInfo = {
  b'ADFH': (ADFH.ADFH_validated, (), (lambda x: {})),
  b'ankr': (ankr.Ankr.fromvalidatedwalker, (), (lambda x: {})),
  b'avar': (avar.Avar.fromvalidatedwalker, (), (lambda x: {'editor': x})),
  b'BASE': (BASE.BASE.fromvalidatedwalker, (), (lambda x: {})),
  
  b'bdat': (
    sbit.Sbit.fromvalidatedwalker,
    (b'bloc', b'maxp'),
    (lambda x: {
      'wLoc': x.getRawWalker(b'bloc'),
      'fontGlyphCount': x.maxp.numGlyphs,
      'flavor': 'bdat'})),
  
  b'bsln': (
    bsln.Bsln.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'CBDT': (
    sbit.Sbit.fromvalidatedwalker,
    (b'CBLC', b'maxp'),
    (lambda x: {
      'wLoc': x.getRawWalker(b'CBLC'),
      'fontGlyphCount': x.maxp.numGlyphs,
      'flavor': 'CBDT'})),
  
  b'CFF ': (CFF.CFF.fromvalidatedwalker, (), (lambda x: {})),
  b'cmap': (cmap.Cmap.fromvalidatedwalker, (), (lambda x: {})),
  b'COLR': (COLR.COLR.fromvalidatedwalker, (b'CPAL',), (lambda x: {})),
  b'CPAL': (CPAL.CPAL, (), (lambda x: {})),
  
  b'cvar': (
    cvar.Cvar.fromvalidatedwalker,
    (b'fvar',),
    (lambda x: {'editor': x})),
  
  b'cvt ': (cvt.Cvt.fromvalidatedwalker, (), (lambda x: {})),
  b'DSIG': (DSIG.DSIG.fromvalidatedwalker, (), (lambda x: {})),

  b'EBDT': (
    sbit.Sbit.fromvalidatedwalker,
    (b'EBLC', b'maxp'),
    (lambda x: {
      'wLoc': x.getRawWalker(b'EBLC'),
      'fontGlyphCount': x.maxp.numGlyphs,
      'flavor': 'EBDT'})),
  
  b'EBSC': (EBSC.EBSC.fromvalidatedwalker, (), (lambda x: {})),
  b'fdsc': (fdsc.Fdsc.fromvalidatedwalker, (), (lambda x: {})),
  b'fpgm': (fpgm.Fpgm.fromvalidatedwalker, (), (lambda x: {})),
  b'fmtx': (fmtx.Fmtx.fromvalidatedwalker, (), (lambda x: {})),
  b'fvar': (fvar.Fvar.fromvalidatedwalker, (), (lambda x: {'editor': x})),
  b'gasp': (gasp.Gasp.fromvalidatedwalker, (), (lambda x: {})),
  b'GDEF': (GDEF.GDEF_validated, (), (lambda x: {'editor': x})),
  
  b'glyf': (
    glyf.Glyf.fromvalidatedwalker,
    (b'loca',),
    (lambda x: {'locaObj': x.loca})),
  
  b'GPOS': (
    GPOS.GPOS_validated, 
    (),
    (lambda x: {'GDEF': x.GDEF} if b'GDEF' in x else {})),

  b'GSUB': (
    GSUB.GSUB_validated,
    (),
    (lambda x: {'editor': x})),
  
  b'gvar': (
    gvar.Gvar.fromvalidatedwalker,
    (b'fvar', b'glyf'),
    (lambda x: {'editor': x})),
  
  b'hdmx': (
    hdmx.Hdmx.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'head': (head.Head.fromvalidatedwalker, (), (lambda x: {})),
  b'hhea': (hhea.Hhea.fromvalidatedwalker, (), (lambda x: {})),
  
  b'hmtx': (
    hmtx.Hmtx.fromvalidatedwalker,
    (b'hhea', b'maxp'),
    (lambda x: {
      'numLongMetrics': x.hhea.numLongMetrics,
      'fontGlyphCount': x.maxp.numGlyphs})),

  b'HVAR': (
    HVAR.HVAR.fromvalidatedwalker,
    (b'fvar', b'maxp'),
    (lambda x: {
      'axisOrder': x.fvar.axisOrder,
      'editor': x})),

  b'kern': (
    kern.Kern.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'kerx': (
    kerx.Kerx.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),

  b'loca': (
    loca.Loca.fromvalidatedwalker,
    (b'RAW glyf', b'head', b'maxp'),
    (lambda x: {
      'fontGlyphCount': x.maxp.numGlyphs,
      'glyfLength': len(x.getRawTable(b'glyf') or []),
      'isLongOffsets': bool(x.head.indexToLocFormat)})),
  
  b'LTSH': (
    LTSH.LTSH.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'maxp': (maxp.Maxp_validated, (), (lambda x: {})),
  b'meta': (meta.Meta.fromvalidatedwalker, (), (lambda x: {})),
  b'mort': (mort.Mort.fromvalidatedwalker, (), (lambda x: {})),
  
  b'morx': (
    morx.Morx.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
    
  b'MTcl': (MTcl.MTcl.fromvalidatedwalker, (), (lambda x: {})),

  b'MVAR': (MVAR.MVAR.fromvalidatedwalker,
    (b'fvar',),
    (lambda x: {'axisOrder': x.fvar.axisOrder})),
  
  b'name': (name.Name.fromvalidatedwalker, (), (lambda x: {})),
  
  b'opbd': (
    opbd.Opbd.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'OS/2': (OS_2.OS_2_validated, (), (lambda x: {})),
  b'PCLT': (PCLT.PCLT.fromvalidatedwalker, (), (lambda x: {})),
  b'post': (post.Post.fromvalidatedwalker, (), (lambda x: {})),
  
  b'prop': (
    prop.Prop_validated,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
  
  b'sbix': (
    sbix.Sbix.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})),
    
  b'SPRK': (SPRK.SPRK_validated, (), (lambda x: {})),
  b'STAT': (STAT.STAT_validated, (), (lambda x: {})),
  b'trak': (trak.Trak.fromvalidatedwalker, (), (lambda x: {})),

  b'TSI0': (
    TSILoc.TSILoc.fromvalidatedwalker,
    (b'maxp', b'TSI1'),
    (lambda x: {
      'flavor': 'TSI0',
      'fontGlyphCount': x.maxp.numGlyphs, 
      'TSIDataTableLength': len(x.getRawTable(b'TSI1') or [])})),

  b'TSI1': (
    TSIDat.TSIDat.fromvalidatedwalker,
    (b'TSI0',),
    (lambda x: {
      'flavor':'TSI0',
      'TSILocTable': x.TSI0})),

  b'TSI2': (
    TSILoc.TSILoc.fromvalidatedwalker,
    (b'maxp', b'TSI3'),
    (lambda x: {
      'flavor': 'TSI2',
      'fontGlyphCount': x.maxp.numGlyphs, 
      'TSIDataTableLength': len(x.getRawTable(b'TSI3') or [])})),

  b'TSI3': (
    TSIDat.TSIDat.fromvalidatedwalker,
    (b'TSI2',),
    (lambda x: {
      'flavor':'TSI2',
      'TSILocTable': x.TSI2})),

  b'TSI5': (
    TSI5.TSI5.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {
      'fontGlyphCount': x.maxp.numGlyphs,
      'dataTable': x.TSI1})),
    
  b'VDMX': (VDMX.VDMX.fromvalidatedwalker, (), (lambda x: {})),
  b'vhea': (vhea.Vhea_validated, (), (lambda x: {})),
  
  b'vmtx': (
    vmtx.Vmtx.fromvalidatedwalker,
    (b'maxp', b'vhea'),
    (lambda x: {
      'numLongMetrics': x.vhea.numLongMetrics,
      'fontGlyphCount': x.maxp.numGlyphs})),

  b'VORG': (VORG.VORG.fromvalidatedwalker, (), (lambda x: {})),
  
  b'VVAR': (
    VVAR.VVAR.fromvalidatedwalker,
    (b'fvar', b'maxp'),
    (lambda x: {
      'axisOrder': x.fvar.axisOrder,
      'editor': x})),

  b'Zapf': (
    Zapf.Zapf.fromvalidatedwalker,
    (b'maxp',),
    (lambda x: {
      'fontGlyphCount': x.maxp.numGlyphs}))
  }

_bbInfo = {
  b'cmap': (lambda x: {'forceNonEmpty': True}),
  b'hdmx': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'head': (lambda x: {'useIndexMap': True}),
  b'GDEF': (lambda x: {'editor': x}),
  b'GPOS': (lambda x: {'forGPOS': True,  'editor': x}),
  b'GSUB': (lambda x: {'forGPOS': False, 'editor': x}),
  b'gvar': (lambda x: {'editor': x}),
  b'HVAR': (lambda x: {'axisOrder': x.fvar.axisOrder}),
  b'JSTF': (lambda x: {'editor': x}),
  b'kerx': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'lcar': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'morx': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'MTap': (lambda x: {'editor': x}),
  b'MTsf': (lambda x: {'editor': x}),
  b'MVAR': (lambda x: {'axisOrder': x.fvar.axisOrder}),
  b'opbd': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'sbix': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs}),
  b'VVAR': (lambda x: {'axisOrder': x.fvar.axisOrder}),
  b'Zapf': (lambda x: {'fontGlyphCount': x.maxp.numGlyphs})
  }

_fixedLengthTables = {
  b'head': 54,
  b'hhea': 36,
  b'vhea': 36}

_windowsOptimalOrdering_TT = {
  b'head':  0,
  b'hhea':  1,
  b'maxp':  2,
  b'OS/2':  3,
  b'hmtx':  4,
  b'LTSH':  5,
  b'VDMX':  6,
  b'hdmx':  7,
  b'cmap':  8,
  b'fpgm':  9,
  b'prep': 10,
  b'cvt ': 11,
  b'loca': 12,
  b'glyf': 13,
  b'kern': 14,
  b'name': 15,
  b'post': 16,
  b'gasp': 17,
  b'PCLT': 18,
  b'DSIG': 19}

_windowsOptimalOrdering_CFF = {
  b'head': 0,
  b'hhea': 1,
  b'maxp': 2,
  b'OS/2': 3,
  b'name': 4, 
  b'cmap': 5,
  b'post': 6,
  b'CFF ': 7}

_repertoire_TT_min = frozenset([
  b'cmap',
  b'glyf',
  b'head',
  b'hhea',
  b'hmtx',
  b'loca',
  b'maxp',
  b'name',
  b'OS/2',      # note this is a MS requirement, not an Apple one
  b'post'])

_repertoire_CFF_min = frozenset([
  b'CFF ',
  b'cmap',
  b'head',
  b'hhea',
  b'hmtx',
  b'maxp',
  b'name',
  b'OS/2',      # note this is a MS requirement, not an Apple one
  b'post',
  #b'VORG',      # 'VORG' is only "strongly recommended", not required.
  ])

_repertoire_bare_min = frozenset([
  b'cmap',
  b'head',
  b'hhea',
  b'hmtx',
  b'maxp',
  b'name',
  b'post'])
  
# -----------------------------------------------------------------------------

#
# Private functions
#

def _ddFactory(key, self, d):
    w = d['pieceInfo'][key]
    w.reset()
    toSkip = d['tablesToSkip']
    pto = d['perTableOptions']
    
    if d['doValidation']:
        logger = d['logger']
        
        if key in _validatedMakerInfo and key not in toSkip:
            f, tagsToCheck, kwArgsFunc = _validatedMakerInfo[key]
            _sncv = deferreddictmeta._singletonNCV
            
            for t in tagsToCheck:
                if len(t) == 8 and t[0:4] == b'RAW ':
                    t = t[4:]
                    isRawCase = True
                
                else:
                    isRawCase = False
                
                if not self.reallyHas(t):
                    break
                
                if isRawCase:
                    continue
                
                if self._dOrig[t] is not _sncv:
                    continue
                
                # We can't use "if self[t] is None" in the following, because
                # that leads to infinite recursion.
                
                if (
                  self._dOrig.get(t, -1) is None or
                  self._dAdded.get(t, -1) is None):
                    
                    break
            
            else:
                dKWArgs = kwArgsFunc(self)
                
                if key in pto:
                    dKWArgs.update(pto[key])
                
                return f(w, logger=d['logger'], **dKWArgs)
            
            logger.warning((
              'G0041',
              (key, tagsToCheck),
              "Unable to create the '%s' table, because one or more "
              "prerequisite tables in the group %s was not present or "
              "had errors preventing their own creation."))
            
            return None
        
        elif key in _makerInfo:
            f, kwArgsFunc = _makerInfo[key]
            
            try:
                dKWArgs = kwArgsFunc(self)
                
                if key in pto:
                    dKWArgs.update(pto[key])
                
                return f(w, **dKWArgs)
            
            except:
                logger.warning((
                  'G0022',
                  (key,),
                  "Could not validate '%s' table (no fromvalidatedwalker call "
                  "and fromwalker call failed)."))
            
            return None
        
        return binary.Binary(w.rest())
    
    if key in _makerInfo:
        f, kwArgsFunc = _makerInfo[key]
        dKWArgs = kwArgsFunc(self)
        
        if key in pto:
            dKWArgs.update(pto[key])
        
        return f(w, **dKWArgs)
    
    return binary.Binary(w.rest())

def _recalc_device_metrics(obj, **kwArgs):
    if b'CFF ' in obj:
        return  # don't try to recalc a CFF, at least for now
    
    scaler = kwArgs.get('scaler', None)
    toRecalc = kwArgs.get('deviceTablesToRecalculate', [])
    ratios = []
    minppem = 255
    maxppem = 1
    fontGlyphCount = obj.maxp.numGlyphs
    hmtxTbl = obj.hmtx
    upem = obj.head.unitsPerEm
    
    # Set up blank tables; establish min/max ppems, ratios, etc. from existing
    # tables, if present.
    
    if b'VDMX' in toRecalc:
        vdmxrecalc = VDMX.VDMX()
        tmprecord = record.Record(yMin = 32767, yMax = -32768)
        
        if b'VDMX' in obj:
            # re-use existing ratios/ppems
            for g in range(len(obj.VDMX)):
                grp = obj.VDMX[g].group
                
                if not grp:
                    continue
                
                ppems = sorted(grp)
                minppem = min(minppem, ppems[0])
                maxppem = max(maxppem, ppems[-1])
                tmpratio = obj.VDMX[g].ratio
                tmpgroup = VDMX.group.Group(dict.fromkeys(ppems, tmprecord))
                
                vdmxrecalc.append(
                  VDMX.vdmxrecord.VDMXRecord(
                    group = tmpgroup,
                    ratio = tmpratio))
                
                if tmpratio.xRatio and tmpratio.yEndRatio:
                    ratios.append((tmpratio.xRatio, tmpratio.yEndRatio))
                else:
                    ratios.append ((1, 1))
        
        else:
            # just do single default 1:1 ratio, 8-255 ppem
            tmpratio = VDMX.ratio_v1.Ratio(
              yEndRatio = 1,
              yStartRatio = 1,
              xRatio = 1)
            
            tmpgroup = VDMX.group.Group(
              dict.fromkeys(
                range(8, 256),
                tmprecord))
            
            vdmxrecalc.append(
              VDMX.vdmxrecord.VDMXRecord(
                group = tmpgroup,
                ratio = tmpratio))                
            
            minppem = 8
            maxppem = 255
                
    if b'hdmx' in toRecalc:
        defaultppems = [11, 12, 13, 15, 16, 17, 19, 21, 24, 
                        27, 29, 32, 33, 37, 42, 46, 50,
                        54, 58, 67, 75, 83, 92, 100]

        if obj.reallyHas(b'hdmx'):
            # reallyHas can be true with bad hdmx because it's deferreddict...
            try:
                hdmxppems = sorted(obj.hdmx)
            except:
                del(obj.hdmx) # remove it, or we have problems in _ddFactory
                hdmxppems = defaultppems
        else:
            hdmxppems = defaultppems
       
        minppem = min(minppem, hdmxppems[0])
        maxppem = max(maxppem, hdmxppems[-1])
        hdmxrecalc = hdmx.Hdmx()
        
        for p in hdmxppems:
            hdmxrecalc[p] = hdmx.ppemdict.PPEMDict(ppem=p)

    if b'LTSH' in toRecalc:
        minppem = 1
        maxppem = 255
        ltshrecalc = LTSH.LTSH(dict.fromkeys(range(fontGlyphCount), 1))

    # Loop on ratios/ppems/glyphs in a single pass and fill in
    # the needed metrics/values.
    
    if len(ratios) == 0:
        ratios = [(1, 1)]
    
    for i, rat in enumerate(ratios):
        xr, yr = rat

        for p in range(minppem, maxppem + 1):
            xs = xr / yr
            
            mat = matrix.Matrix((
              [xs * p, 0, 0],
              [0,      p, 0],
              [0,      0, 1]))
            
            try:
                scaler.setTransform(mat)
            except:
                raise ScalerError()
            
            ymax = -32768
            ymin = 32767

            for g in range(fontGlyphCount):
                try:
                    met = scaler.getOutlineMetrics(g)
                except:
                    raise ScalerError()

                # VDMX stuff
                
                if b'VDMX' in toRecalc:
                    ymax = max(ymax, int(oldRound(met.hi_y)))
                    ymin = min(ymin, int(oldRound(met.lo_y)))
                
                if (
                  (xr == yr == 1) and
                  (b'hdmx' in toRecalc or b'LTSH' in toRecalc)):
                    
                    #hintedAW = met.i_dx ### see Jira ITP-2133
                    hintedAW = oldRound(met.dx)
                    
                    unhintedAW = int(
                      (p * hmtxTbl[g].advance / upem) * 65536 + 0.5)
                    
                    unhintedAW_26_6 = (((unhintedAW + 512) >> 10) + 32) >> 6
                    unhintedAW = (unhintedAW + 0x8000) >> 16

                    # LTSH and hdmx values on 1:1 ratio only
                    if b'hdmx' in toRecalc and p in hdmxppems:
                        hdmxrecalc[p][g] = hintedAW

                    if b'LTSH' in toRecalc:
                        if p < 50:
                            if unhintedAW != hintedAW:
                                ltshrecalc[g] = p + 1
                        
                        elif p < 255:
                            diff = abs(unhintedAW_26_6 - hintedAW)
                            
                            if diff > (unhintedAW_26_6 * 0.02):
                                ltshrecalc[g] = p + 1

            # fill in VDMX ypel for ppem@ratio if VDMX in recalc
            if b'VDMX' in toRecalc and len(vdmxrecalc):
                if p in vdmxrecalc[i].group:
                    vdmxrecalc[i].group[p] = record.Record(
                      yMax = ymax,
                      yMin = ymin)

    # Pickle recalc'ed tables to tempfiles and add filename as attribute to obj
    # for reference in individual tables' validation routines. Using
    # 'delete=False' so that file is retained after .close(); means we need to
    # clean up ourselve (os.remove)
    
    if b'VDMX' in toRecalc:
        vpkl = tempfile.NamedTemporaryFile(
          prefix = 'tmpVDMX_',
          suffix = '.pkl',
          delete = False)
        
        pickle.dump(vdmxrecalc, vpkl)
        obj.__dict__['vdmxpicklefile'] = vpkl.name
        vpkl.close()

    if b'LTSH' in toRecalc:
        lpkl = tempfile.NamedTemporaryFile(
          prefix = 'tmpLTSH_',
          suffix = '.pkl',
          delete = False)
        
        pickle.dump(ltshrecalc, lpkl)
        obj.__dict__['ltshpicklefile'] = lpkl.name
        lpkl.close()

    if b'hdmx' in toRecalc:
        hpkl = tempfile.NamedTemporaryFile(
          prefix = 'tmphdmx_',
          suffix = '.pkl',
          delete = False)
        
        pickle.dump(hdmxrecalc, hpkl)
        obj.__dict__['hdmxpicklefile'] = hpkl.name
        hpkl.close()

def _validate(obj, **kwArgs):
    toSkip = set(kwArgs.get('tablesToSkip', []))
    logger = kwArgs.pop('logger')
    
    if b'CFF ' in obj:
        
        # We preflight getUnicodeMap() to see if it's empty; if it is,
        # this is a symbol font, and we bail immediately.
        
        if not obj.reallyHas(b'cmap'):
            logger.error((
              'V0553',
              (),
              "Unable to validate CFF font without 'cmap' table."))
            
            return False
        
        if not obj.cmap.getUnicodeMap():
            logger.error((
              'V0744',
              (),
              "A CFF symbol font cannot be validated at this time."))
            
            return False
    
    if 'editor' not in kwArgs:
        kwArgs['editor'] = obj

    if 'scaler' in kwArgs:
        
        # If a scaler is available, run the consolidated recalc routine. If
        # not, the individual tables will also look for a scaler and attempt to
        # recalc. If a scaler is not available to those routines, they will
        # issue a warning there, so we do not need to do it here.
        
        deviceMetricTables = {b'hdmx', b'LTSH', b'VDMX'} - toSkip
        recalcTables = []
        
        for t in deviceMetricTables:
            if obj.reallyHas(t):
                recalcTables.append(t)
        
        if recalcTables:
            try:
                kwArgs.pop('deviceTablesToRecalculate', None)
                
                _recalc_device_metrics(
                  obj,
                  deviceTablesToRecalculate = recalcTables,
                  **kwArgs)
            
            except ScalerError:
                # NOTE: V0554 is a more generic form of E1202, E1801, and E2503
                tstr = ', '.join([str(i) for i in recalcTables])
                logger.error((
                  'V0554',
                  (tstr,),
                  "An error occured in the scaler during device metrics "
                  "calculation (%s), preventing validation."))
 
    r = True
    
    if obj.reallyHas(b'GSUB') and obj.reallyHas(b'GPOS'):
        subIndex = set(obj.GSUB.scripts.featureIndex())
        posIndex = set(obj.GPOS.scripts.featureIndex())
        
        if subIndex != posIndex:
            logger.warning((
              'V1009',
              (),
              "The script and language repertoires for the GSUB and "
              "GPOS tables are not the same."))
    
    for key, table in obj.items():
        if key not in toSkip and hasattr(table, 'isValid'):
            subLogger = logger.getChild(key.decode('ascii'))
            r = table.isValid(logger=subLogger, **kwArgs) and r
    
    if kwArgs.get('doRasterizationTests', True):
        v = validate.HintsValidator(obj, logger=logger)
        r = v.validate() and r

    for cachefile in ['hdmxpicklefile', 'vdmxpicklefile', 'ltshpicklefile']:
        if cachefile in obj.__dict__:
            os.remove(obj.__dict__[cachefile])

    return r

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Editor(object, metaclass=deferreddictmeta.FontDataMetaclass):
    """
    Editors are the fundamental object allowing access to all font data. They
    are dictionaries mapping keys representing table tags to the living table
    objects.
    
    Note that in fontio3, the table tags are bytestrings (although Editor
    objects will automatically coerce regular strings, if they're used
    instead).
    
    You may also access tables using attribute notation, except for those
    tables (like 'OS/2' or 'cvt ') that have characters that Python does not
    allow in attribute names.
    """
    
    #
    # Class definition variables
    #
    
    deferredDictSpec = dict(
        dict_orderdependencies = {b'head': set([b'glyf'])},
        dict_validatefunc = _validate,
        dict_wisdom = (
          "Contains all the content of a font, either TrueType or TTC. Note "
          "that you don't have to worry about the binary representation of "
          "the data here; fontio3 automatically handles that for you. So, for "
          "instance, things like checksums are automatically dealt with."),
        item_createfunc = _ddFactory,
        item_createfuncneedsself = True,
        item_followsprotocol = True,
        item_keyisbytes = True,
        item_subloggernamefunc = (lambda k: k),
        item_usenamerforstr = True,
        item_wisdom_key = (
          "Keys are table tags. You may add new ones or delete old ones, as "
          "well as editing the contents. By ancient convention, tags that are "
          "all lower-case are reserved for Apple, so any new tags you add "
          "should be either mixed lower-case and upper-case, or all "
          "upper-case."),
        item_wisdom_value = (
          "Values are objects representing living font data. Note that "
          "unlike tools like TTX or the Apple Font Tools, these do not "
          "slavishly follow the exact binary data; rather, those data are "
          "interpreted into a more natural representation. So Python "
          "constructs like dicts are often used for these values, in order "
          "to make the data easier to edit."))
    
    #
    # Methods
    #
    
    def _makeOffsetOrdering(self, forApple):
#         if forApple:
#             return sorted(self)
        
        v = []
        
        if b'CFF ' in self:
            dOrder = _windowsOptimalOrdering_CFF
        else:
            dOrder = _windowsOptimalOrdering_TT
        
        for tag, order in sorted(dOrder.items(), key=operator.itemgetter(1)):
            if tag in self:
                v.append(tag)
        
        v.extend(sorted(set(self) - set(dOrder)))
        return v
    
    def _updateDependentObjects(self, **kwArgs):
        """
        """
        
        allk = set(self)
        ck = set(self._dAdded)
        
        if ck:
            self.changed(b'head')  # force checkSumAdjustment recalc
        
        if {b'glyf', b'loca'} & ck:
            self.changed(b'glyf')
            self.changed(b'loca')
        
        if {b'glyf', b'prep', b'fpgm', b'cvt '} & ck:
            self.changed(b'maxp')
        
        if b'GDEF' in ck:
            gdef_v = self.GDEF.version
            if gdef_v.major == 1 and gdef_v.minor >= 3:
                gdce = getattr(self.GDEF, '_creationExtras', {})
                otcd = gdce.get('otcommondeltas', set())
                otcd.update(self.GDEF.gatheredLivingDeltas())
                gdce['otcommondeltas'] = otcd
                self.GDEF._creationExtras = gdce
        
        if b'GPOS' in ck:
            # check for variable data and ensure that
            # we have a GDEF in which to store the IVS
            gpld = self.GPOS.gatheredLivingDeltas()
            if gpld:
                if b'GDEF' in allk:
                    gdef_v = self.GDEF.version
                    if gdef_v.major == 1 and gdef_v.minor < 3:
                        newGDEF = GDEF.GDEF_v13.GDEF()
                        for attr in self.GDEF._ATTRSORT:
                            setattr(newGDEF, attr, getattr(self.GDEF, attr))
                        self.GDEF = newGDEF
                else:
                    newGDEF = GDEF.GDEF_v13.GDEF()
                    gctfn = newGDEF.glyphClasses.fromeditor
                    newGDEF.glyphClasses = gctfn(self)
                    self.GDEF = newGDEF
                
                # add/update any GDEF LivingDeltas that might be present
                gdce = getattr(self.GDEF, '_creationExtras', {})
                otcd = gdce.get('otcommondeltas', self.GDEF.gatheredLivingDeltas())
                otcd.update(gpld)
                gdce['otcommondeltas'] = otcd
                self.GDEF._creationExtras = gdce
                self.changed(b'GDEF')
                
        if (b'hhea' in allk) and (b'glyf' in ck or b'hmtx' in ck):
            self.hhea = self.hhea.recalculated(editor=self)
            if b'hmtx' in ck:
                if kwArgs.get('okToCompact', True):
                    self.hhea.numLongMetrics = self.hmtx.getLongMetricsCount(True)
                else:
                    self.hhea.numLongMetrics = self.maxp.numGlyphs

        if (b'vhea' in allk) and (b'glyf' in ck or b'vmtx' in ck):
            self.vhea = self.vhea.recalculated(editor=self)
            if b'vmtx' in ck:
                if kwArgs.get('okToCompact', True):
                    self.vhea.numLongMetrics = self.vmtx.getLongMetricsCount(True)
                else:
                    self.vhea.numLongMetrics = self.maxp.numGlyphs
        
        if b'MTap' in ck:
            anchorObjs = {}
            connectionObjs = {}
            
            for apObj in self.MTap.values():
                adObj = apObj.anchorData
                ccObj = apObj.connectionData
                
                if adObj is not None:
                    immut = adObj.asImmutable()
                    
                    if immut not in anchorObjs:
                        anchorObjs[immut] = adObj
                
                if ccObj is not None:
                    immut = ccObj.asImmutable()
                    
                    if immut not in connectionObjs:
                        connectionObjs[immut] = ccObj
            
            if anchorObjs:
                v = sorted(anchorObjs.items(), key=operator.itemgetter(0))
                self.MTad = MTad.MTad(t[1] for t in v)
            
            if connectionObjs:
                v = sorted(connectionObjs.items(), key=operator.itemgetter(0))
                self.MTcc = MTcc.MTcc(t[1] for t in v)
        
        if b'MTsf' in ck:
            sf = self.MTsf
            v = sorted(set(obj.className for obj in sf.values()) - set([None]))
            self.MTsc = MTsc.MTsc(v)
    
    @staticmethod
    def _validate_binSearch(w, logger):
        okToProceed = True
        numTables = None
        
        if w.length() < 8:
            logger.critical((
              'V0142',
              (),
              "Not enough bytes to read sfnt binary search fields."))
            
            okToProceed = False
        
        else:
            numTables, searchRange, entrySelector, rangeShift = w.unpack("4H")
            
            if not numTables:
                logger.critical(('E0012', (), "The sfnt's numTables is zero."))
                okToProceed = False
            
            else:
                logger.info((
                  'V0143',
                  (numTables,),
                  "The sfnt's numTables is %d"))
                
                bshAvatar = bsh.BSH(nUnits=numTables, unitSize=16)
                
                if searchRange != bshAvatar.searchRange:
                    logger.warning((
                      'E0014',
                      (bshAvatar.searchRange, searchRange),
                      "The sfnt's searchRange should be %d, but is %d."))
                
                else:
                    logger.info((
                      'V0144',
                      (),
                      "The sfnt's searchRange is correct."))
                
                if entrySelector != bshAvatar.entrySelector:
                    logger.warning((
                      'E0010',
                      (bshAvatar.entrySelector, entrySelector),
                      "The sfnt's entrySelector should be %d, but is %d."))
                
                else:
                    logger.info((
                      'V0145',
                      (),
                      "The sfnt's entrySelector is correct."))
                
                if rangeShift != bshAvatar.rangeShift:
                    logger.warning((
                      'E0013',
                      (bshAvatar.rangeShift, rangeShift),
                      "The sfnt's rangeShift should be %d, but is %d."))
                
                else:
                    logger.info((
                      'V0146',
                      (),
                      "The sfnt's rangeShift is correct."))
                
                if w.length() < 16 * numTables:
                    logger.critical((
                      'V0147',
                      (),
                      "The sfnt's table of contents is shorter than required "
                      "by the specified value of numTables."))
                    
                    okToProceed = False
        
        return okToProceed, numTables
    
    @staticmethod
    def _validate_repertoire(logger, toc, isTrueType):
        okToProceed = True
        presentTags = set(t[0] for t in toc)
        presentNonZeroTags = set(t[0] for t in toc if t[3] != 0)
        
        minComplement = set(_repertoire_bare_min)
        minComplement -= presentNonZeroTags        
        if minComplement:
            v = sorted(str(x) for x in minComplement)
            logger.critical((
                'V0302',
                (v,),
                "Essential tables not present or have length of zero: %s"))
            return False

        if isTrueType:
            minComplement = set(_repertoire_TT_min)
            minComplement -= presentTags
            
            if minComplement:
                v = sorted(str(x) for x in minComplement)
                
                logger.error((
                  'E0020',
                  (v,),
                  "Required TrueType tables not present: %s"))
        
        else:
            minComplement = set(_repertoire_CFF_min)
            minComplement -= presentTags
            
            if minComplement:
                v = sorted(str(x) for x in minComplement)
                
                logger.error((
                  'V0148',
                  (v,),
                  "Required CFF tables not present: %s"))
        
        return okToProceed
    
    @staticmethod
    def _validate_toc(w, logger, numTables, startOffset, endOfFile, fromTTC):
        okToProceed = True
        toc = []
        minValidOffset = startOffset + 12 + 16 * numTables
        csaOffset = None  # checkSumAdjustment absolute offset
        
        for i in range(numTables):
            tag, checksum, offset, length = w.unpack("4s3L")
            allClear = True
            
            if any(n < 32 or n > 126 for n in tag):
                n = tag[0] * 16777216 + tag[1] * 65536 + tag[2] * 256 + tag[3]
                
                logger.warning((
                  'E0037',
                  (n,),
                  "Tag 0x%08X contains non-ASCII characters."))
                
                allClear = False
            
            if toc:
                if tag < toc[-1][0]:
                    logger.warning((
                      'E0038',
                      (),
                      "The sfnt's table of contents is not sorted "
                      "by the table tag."))
                    
                    allClear = False
                
                elif tag == toc[-1][0]:
                    logger.critical((
                      'E0031',
                      (tag,),
                      "The '%s' table is present more than once."))
                    
                    allClear = False
                    okToProceed = False
            
            if offset < minValidOffset:
                logger.critical((
                  'E0034',
                  (tag,),
                  "The '%s' table starts at an invalid offset (too low)."))
                
                allClear = False
                okToProceed = False
            
            if offset % 4:
                logger.warning((
                  'V0149',
                  (tag,),
                  "The '%s' table starts at a non-longword-aligned offset."))
                
                allClear = False
            
            if not length:
                logger.warning((
                  'E0032',
                  (tag,),
                  "The '%s' table has a zero length."))
                
                allClear = False
            
            if (offset + length) > endOfFile:
                logger.critical((
                  'E0036',
                  (tag,),
                  "The sfnt's table-of-contents record for the '%s' table "
                  "extends past the end of the font."))
                
                allClear = False
                okToProceed = False
            
            if tag in _fixedLengthTables:
                if length != _fixedLengthTables[tag]:
                    logger.critical((
                      'V0150',
                      (tag,),
                      "The '%s' table has an incorrect length."))
                    
                    allClear = False
                    okToProceed = False
            
            if okToProceed:
                s = w.piece(length, offset, relative=False)
                
                if tag == b'head':
                    # Special 'head' hack to zero checkSumAdjustment
                    # Note we've already checked the length
                    s = s[:8] + b'\x00\x00\x00\x00' + s[12:]
                    csaOffset = offset + 8
                
                if checksum != utilitiesbackend.utChecksum(s):
                    logger.warning((
                      'E0030',
                      (tag,),
                      "Checksum for '%s' table is incorrect."))
                    
                    allClear = False
                
                if allClear:
                    logger.info((
                      'V0151',
                      (tag,),
                      "Table of contents record for table '%s' is correct."))
            
                toc.append((tag, checksum, offset, length))
        
        if (not fromTTC) and csaOffset is not None:
            # check whole-font checksum
            wSub = w.subWalker(0)
            s = wSub.chunk(csaOffset)
            cs = utilitiesbackend.utChecksum(s)
            del s
            fontCSA = wSub.unpack("L")
            s = wSub.absRest(csaOffset + 4)
            cs = (cs + utilitiesbackend.utChecksum(s)) % 0x100000000
            del s
            cs = (0xB1B0AFBA - cs) % 0x100000000
            
            if fontCSA != cs:
                logger.warning((
                  'E1305',
                  (cs, fontCSA),
                  "Font's checksum should be 0x%08X, but is 0x%08X."))
        
        return okToProceed, toc
    
    @staticmethod
    def _validate_topology(w, logger, toc, isTrueType, forApple, fromTTC):
        okToProceed = True
        toc.sort(key=operator.itemgetter(2))
        
        for i in range(len(toc) - 1):
            thisRec = toc[i]
            nextRec = toc[i+1]
            
            if thisRec[2:] == nextRec[2:]:
                logger.warning(('V0152', (), "Some font tables are shared."))
            
            elif thisRec[2] + thisRec[3] > nextRec[2]:
                logger.critical((
                  'E0035',
                  (),
                  "The font has overlapping tables."))
                
                okToProceed = False
        
        if okToProceed and (not fromTTC):
            if not forApple:
                if isTrueType:
                    d = _windowsOptimalOrdering_TT
                    v = [d[t[0]] for t in toc if t[0] in d]
                    
                    if v != sorted(v):
                        logger.warning((
                          'V0153',
                          (),
                          "Tables not in Windows-optimized order "
                          "for a TrueType font."))
                
                else:
                    d = _windowsOptimalOrdering_CFF
                    v = [d[t[0]] for t in toc if t[0] in d]
                    
                    if v != sorted(v):
                        logger.warning((
                          'V0154',
                          (),
                          "Tables not in Windows optimized order for a CFF font."))
        
        return okToProceed
    
    @staticmethod
    def _validate_version(w, forApple, logger):
        """
        2016-06-17 JH: return the actual version bytes instead of simply 'isTrueType'; 
                       version will get stored in Editor._creationExtras['pieceInfo']
                       for reference in downstream tests.
        """
        okToProceed = True

        if w.length() < 4:
            logger.critical((
              'V0001',
              (),
              "Not enough bytes to read sfnt version."))
              
            version = None  # avoid UnboundLocalError downstream
            
            okToProceed = False
        
        else:
            version = w.unpack("4s")
            
            if version == b'\x00\x01\x00\x00':
                logger.info((
                  'V0155',
                  (),
                  "Font version is 1.0 (original TrueType)."))
            
            elif version == b'true':
                if forApple:
                    logger.info((
                      'V0156',
                      (),
                      "Font version is 'true' (Apple TrueType)."))
                
                else:
                    logger.error((
                      'E0011',
                      (),
                      "Non-Apple systems cannot deal with the 'true' "
                      "sfnt version; please change it to 0x00010000."))
                    
                    # okToProceed = False
            
            elif version == b'OTTO':
                logger.info((
                  'V0157',
                  (),
                  "Font version is 'OTTO' (CFF OpenType)."))
                
            elif version == b'typ1':
                if forApple:
                    logger.info((
                      'V0158',
                      (),
                      "Font version is 'typ1' (CFF AAT)."))
                
                else:
                    logger.error((
                      'E0011',
                      (),
                      "Non-Apple systems cannot deal with the 'typ1' "
                      "sfnt version; please change it to OTTO."))
                    
                    okToProceed = False
                
            else:
                logger.critical((
                  'E0003',
                  (version,),
                  "Unknown sfnt version: %s"))
                
                okToProceed = False
        
        return okToProceed, version


    def addGlyphs(self, glyphObjs, advances, **kwArgs):
        """
        Adds one or more new glyphs to the Editor. Note that this, unlike most
        methods in fontio, actually changes the Editor in situ, rather than
        returning a new Editor object. Much cheaper and faster that way.
        
        Note that no attempt is made to "merge" things here, so glyphs whose
        hints refer to CVT or storage indices must use what is already present;
        no renumbering will be done.
        
        The positional arguments are as follows:
        
            advances            An iterator over FUnit values representing the
                                advance widths of the glyph(s) being added.
            
            glyphObjs           An iterator over objects which must be of type
                                TTSimpleGlyph or TTCompositeGlyph. The order of
                                glyphs presented by this iterator is the order
                                the glyphs will appear in the Editor.
        
        The following optional keyword arguments are supported; note that in
        all cases if the caller wishes to omit values from a provided iterator
        then the iterator should just provide None as the value.
        
            forcePostNames      Normally post names won't be added if the
                                existing dict is empty (to prevent overriding
                                a format 3 table). However, the merge code
                                sometimes need to start with an utterly empty
                                dict; if this keyword (default False) is
                                specified, then the empty check is overridden.
            
            glyphIDs            An iterator over glyph indices to be used for
                                the glyphs being added. If not provided, the
                                glyphs will be added to the end of the current
                                Glyf object.
            
            hdmxDicts           An iterator over dicts, each of which maps PPEM
                                values to pixel advances. If not provided, and
                                an 'hdmx' table is present, the values will be
                                calculated from the 'hmtx' values.
            
            ltshValues          An iterator over PPEM values, used for the
                                glyph's entry in the 'LTSH' table. If not
                                provided, and an 'LTSH' table is present, a
                                value of 1 will be used.
            
            sidebearings        An iterator over FUnit values representing the
                                sidebearings for the glyphs. If not provided
                                then each glyph will get a sidebearing based on
                                its bounding rectangle.
            
            postNames           An iterator over strings representing the names
                                for the glyphs. If not provided, and a Post
                                object of nonzero length is present, then names
                                will be synthesized based of the form "gnnnn",
                                where the nnnn refers to the new glyph index.
            
            unicodes            An iterator over Unicodes (integers), or over
                                iterables of integers. If not provided, no
                                changes will be made to the Cmap object.
            
            vertAdvances        An iterator over FUnit values representing the
                                vertical advances (i.e. the advances from the
                                'vmtx' table. If not provided, and a 'vmtx'
                                table is present, the values will be computed
                                based on the bounding rectangle.
            
            vertSidebearings    An iterator over FUnit values representing the
                                sidebearings for the 'vmtx' table. If not
                                provided, and the font has a 'vmtx' table, then
                                a value will be calculated from the advance and
                                bounding box for the glyph.

            vttGroups           An iterator over VTT glyph groups. If not supplied
                                and the font contains a TSI5 table, an entry of
                                'AnyGroup' will be added.

            vttPgms             An iterator over VTT pgm codes ("Low Level 
                                hints"). If not supplied and the font has a TSI1 
                                table, an empty entry will be added.                                

            vttTalks            An iterator over VTTTalk codes ("High Level 
                                hints"). If not supplied and the font has a TSI3 
                                table, an empty entry will be added.
        """
        
        # Add the glyphs
        
        glyfTable = self.glyf
        newIndices = []
        addedCount = 0
        
        for glyphObj, glyphID in zip(
          glyphObjs,
          kwArgs.get('glyphIDs', itertools.repeat(None))):
          
            if glyphID is None:
                glyphID = max(glyfTable) + 1
            
            if glyphID not in glyfTable:
                addedCount += 1
            
            glyfTable[glyphID] = glyphObj
            newIndices.append(glyphID)
            self.changed(b'glyf')
        
        if addedCount:
            self.maxp.numGlyphs += addedCount
            self.changed(b'maxp')
        
        # Add the horizontal metrics
        
        hmtxTable = self.hmtx
        
        for glyphID, advance, sidebearing in zip(
          newIndices,
          advances,
          kwArgs.get('sidebearings', itertools.repeat(None))):
          
            if sidebearing is None:
                sidebearing = glyfTable[glyphID].bounds.xMin
            
            hmtxTable[glyphID] = hmtx.MtxEntry(advance, sidebearing)
            self.changed(b'hmtx')
        
        self.hhea.numLongMetrics += addedCount
        self.changed(b'hhea')
        
        # Add the vertical metrics
        
        if b'vmtx' in self:
            vmtxTable = self.vmtx
            
            for glyphID, advance, sidebearing in zip(
              newIndices,
              kwArgs.get('vertAdvances', itertools.repeat(None)),
              kwArgs.get('vertSidebearings', itertools.repeat(None))):
              
                bounds = glyfTable[glyphID].bounds
                
                if advance is None:
                    advance = self.head.unitsPerEm
                
                if sidebearing is None:
                  if bounds:
                    height = bounds.yMax - bounds.yMin
                    sidebearing = (advance - height) // 2
                  else:
                    sidebearing = 0

                vmtxTable[glyphID] = hmtx.MtxEntry(advance, sidebearing)
                self.changed(b'vmtx')
        
        # Add the Unicode mappings
        
        unicodeSubtable = self.cmap[self.cmap.getUnicodeKeys()[0]]
        
        for glyphID, uCode in zip(
          newIndices,
          kwArgs.get('unicodes', itertools.repeat(None))):
          
            if uCode is not None:
                try:
                    it = iter(uCode)
                except TypeError:
                    it = iter({uCode})
                
                for uCode in it:
                    unicodeSubtable[uCode] = glyphID
                
                self.changed(b'cmap')
        
        # Add the Postscript names
        
        postTable = self.post
        
        if len(postTable) or kwArgs.get('forcePostNames', False):
            
            for glyphID, psName in zip(
              newIndices,
              kwArgs.get('postNames', itertools.repeat(None))):
              
                if psName is None:
                    psName = "g%d" % (glyphID,)
                
                postTable[glyphID] = psName
                self.changed(b'post')
        
        # Add the 'hdmx' values
        
        if b'hdmx' in self:
            hdmxTable = self.hdmx
            
            for glyphID, hdmxDict in zip(
              newIndices,
              kwArgs.get('hdmxDicts', itertools.repeat(None))):
              
                if hdmxDict is None:
                    continue
                
                for ppem, n in hdmxDict.items():
                    if n is None:
                        n = ppem * hmtxTable[glyphID][0] / self.head.unitsPerEm
                        n = int(n + 0.5)
                    
                    if ppem in hdmxTable:
                        hdmxTable[ppem][glyphID] = n
                    else:
                        hdmxTable[ppem] = ppemdict.PPEMDict({glyphID: n})
                
                self.changed(b'hdmx')
        
        # Add the 'LTSH' values
        
        if b'LTSH' in self:
            ltshTable = self.LTSH
            
            for glyphID, ltshValue in zip(
              newIndices,
              kwArgs.get('ltshValues', itertools.repeat(None))):
              
                if ltshValue is None:
                    ltshValue = 1
                
                ltshTable[glyphID] = ltshValue
                self.changed(b'LTSH')
        
        # Add the TSI table values
        
        if b'TSI1' in self:
            t = self.TSI1
            
            for glyphID, vttpgmValue in zip(
              newIndices,
              kwArgs.get('vttPgms', itertools.repeat(None))):
              
                if vttpgmValue is None:
                    vttpgmValue = b''
                
                t[glyphID] = vttpgmValue
                self.changed(b'TSI1')
        
        if b'TSI3' in self:
            t = self.TSI3
            
            for glyphID, vttHLValue in zip(
              newIndices,
              kwArgs.get('vttTalks', itertools.repeat(None))):
              
                if vttHLValue is None:
                    vttHLValue = b''
                    
                t[glyphID] = vttHLValue
                self.changed(b'TSI3')
        
        if b'TSI5' in self:
            t = self.TSI5
            
            for glyphID, vttGroupValue in zip(
              newIndices,
              kwArgs.get('vttGroups', itertools.repeat(None))):
              
                if vttGroupValue is None:
                    vttGroupValue = 'AnyGroup'
                    
                t[glyphID] = vttGroupValue
                self.changed(b'TSI5')
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the editor (i.e. the whole font) to the
        specified LinkedWriter. The following keyword arguments are supported:
        
            forApple        Default is False; if True, the value 'true' will be
                            written for the TrueType version, flagging it as an
                            Apple-specific font.
        
        Additionally, the perTableOptions keyword argument may be specified.
        This is a dict whose keys are bytestrings representing tables, and
        whose values are in turn dicts with arguments that will be passed into
        the buildBinary method for the specified table. This allows us to
        provide namespace-like separation of keyword arguments, reducing the
        risk of duplicate names for different tables being used for different
        purposes. Note that these values will override the ones in the default
        arguments dictionary that lives in _bbInfo.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self._updateDependentObjects(**kwArgs)
        
        if kwArgs.get('forApple', False):
            w.addString(b"true")
        elif b'CFF ' in self:
            w.addString(b"OTTO")
        else:
            w.add("L", 0x10000)
        
        b = bsh.BSH(nUnits=len(self), unitSize=16)
        b.buildBinary(w, skipUnitSize=True)
        tagOffsetStake = {tag: w.getNewStake() for tag in self}
        
        for tag in sorted(self):
            w.addString(tag)
            w.addUnresolvedIndex("L", "checksums", tag)
            w.addUnresolvedOffset("L", stakeValue, tagOffsetStake[tag])
            w.addUnresolvedIndex("L", "lengths", tag)
        
        # Now add the actual tables
        checksums = {tag: 0 for tag in self}
        lengths = checksums.copy()
        w.addIndexMap("checksums", checksums)  # temp, for w.checkSum() calls
        w.addIndexMap("lengths", lengths)  # temp, for w.checkSum() calls
        self.head.checkSumAdjustment = 0
        undoneChecksums = {}
        ck = set(self._dAdded) | {b'head'}
        pto = kwArgs.pop('perTableOptions', {})
        wGlyfCached = None
        
        if b'TSI0' in ck or b'TSI1' in ck:
            ck.add(b'TSI0')
            ck.discard(b'TSI1')
        
        if b'TSI2' in ck or b'TSI3' in ck:
            ck.add(b'TSI2')
            ck.discard(b'TSI3')
        
        for tag in self._makeOffsetOrdering(kwArgs.get('forApple', False)):
            bsForced = None
            
            if (tag == b'TSI1') and (b'TSI0' in ck):
                continue
            
            elif (tag == b'TSI3') and (b'TSI2' in ck):
                continue
            
            w.stakeCurrentWithValue(tagOffsetStake[tag])
            startByteLength = w.byteLength
            
            if tag not in ck:
                s = self.getRawTable(tag)
                w.addString(s)
                checksums[tag] = utilitiesbackend.utChecksum(s)
            
            else:
                d = (_bbInfo[tag](self) if tag in _bbInfo else {})
                d.update(kwArgs)
                
                if tag == b'bdat':
                    def _lc(newLoc): self.bloc = newLoc
                    d['locCallback'] = _lc
                    d['forApple'] = True  # override this
                    ck.add(b'bloc')
                
                elif tag == b'CBDT':
                    def _lc(newLoc): self.CBLC = newLoc
                    d['locCallback'] = _lc
                    d['forApple'] = False  # override this
                    ck.add(b'CBLC')

                elif tag == b'CFF ':
                    wCFFCached = writer.LinkedWriter()
                    self['CFF '].buildBinary(wCFFCached)
                    bsForced = wCFFCached.binaryString()
                
                elif tag == b'EBDT':
                    def _lc(newLoc): self.EBLC = newLoc
                    d['locCallback'] = _lc
                    d['forApple'] = False  # override this
                    ck.add(b'EBLC')
                
                elif tag == b'head':
                    if b'glyf' in ck:
                        if wGlyfCached is None:
                            wGlyfCached = writer.LinkedWriter()
                            
                            dTemp = (
                              _bbInfo[b'glyf'](self) if b'glyf' in _bbInfo
                              else {})
                            
                            dTemp.update(kwArgs)
                            dTemp.update(pto.get(b'glyf', {}))
                            def _lc(newLoca): self.loca = newLoca
                            dTemp['locaCallback'] = _lc
                            self.glyf.buildBinary(wGlyfCached, **dTemp)
                        
                        self[tag].indexToLocFormat = int(
                          self.loca.needsLongOffsets())
                
                elif tag == b'glyf':
                    if wGlyfCached is None:
                        wGlyfCached = writer.LinkedWriter()
                        
                        dTemp = (
                          _bbInfo[b'glyf'](self) if b'glyf' in _bbInfo
                          else {})
                        
                        dTemp.update(kwArgs)
                        dTemp.update(pto.get(b'glyf', {}))
                        def _lc(newLoca): self.loca = newLoca
                        dTemp['locaCallback'] = _lc
                        self.glyf.buildBinary(wGlyfCached, **dTemp)
                    
                    bsForced = wGlyfCached.binaryString()

                elif tag == b'loca':
                    if wGlyfCached is None:
                        wGlyfCached = writer.LinkedWriter()
                        
                        dTemp = (
                          _bbInfo[b'glyf'](self) if b'glyf' in _bbInfo
                          else {})
                        
                        dTemp.update(kwArgs)
                        dTemp.update(pto.get(b'glyf', {}))
                        def _lc(newLoca): self.loca = newLoca
                        dTemp['locaCallback'] = _lc
                        self.glyf.buildBinary(wGlyfCached, **dTemp)
                
                elif tag == b'TSI0':  # this logic does both TSI0 and TSI1
                    dForTSI1 = (_bbInfo[b'TSI1'](self) if b'TSI1' in _bbInfo else {})
                    dForTSI1.update(kwArgs)
                    dForTSI1.update(pto.get(b'TSI1', {}))
                    locResult = []
                    dForTSI1['locCallback'] = (lambda newLoc: locResult.append(newLoc))
                    sTSI1 = self[b'TSI1'].binaryString(**dForTSI1)
                    d.update(pto.get(b'TSI0', {}))
                    sTSI0 = locResult[0].binaryString(**d)
                    w.addString(sTSI0)
                    undoneChecksums[b'TSI0'] = (startByteLength, w.byteLength)
                    lengths[b'TSI0'] = len(sTSI0)
                    w.alignToByteMultiple(4)
                    w.stakeCurrentWithValue(tagOffsetStake[b'TSI1'])
                    startByteLength = w.byteLength
                    w.addString(sTSI1)
                    undoneChecksums[b'TSI1'] = (startByteLength, w.byteLength)
                    lengths[b'TSI1'] = len(sTSI1)
                    w.alignToByteMultiple(4)
                    continue
                
                elif tag == b'TSI2':  # this logic does both TSI2 and TSI3
                    dForTSI3 = (_bbInfo[b'TSI3'](self) if b'TSI3' in _bbInfo else {})
                    dForTSI3.update(kwArgs)
                    dForTSI3.update(pto.get(b'TSI3', {}))
                    locResult = []
                    dForTSI3['locCallback'] = (lambda newLoc: locResult.append(newLoc))
                    sTSI3 = self[b'TSI3'].binaryString(**dForTSI3)
                    d.update(pto.get(b'TSI2', {}))
                    sTSI2 = locResult[0].binaryString(**d)
                    w.addString(sTSI2)
                    undoneChecksums[b'TSI2'] = (startByteLength, w.byteLength)
                    lengths[b'TSI2'] = len(sTSI2)
                    w.alignToByteMultiple(4)
                    w.stakeCurrentWithValue(tagOffsetStake[b'TSI3'])
                    startByteLength = w.byteLength
                    w.addString(sTSI3)
                    undoneChecksums[b'TSI3'] = (startByteLength, w.byteLength)
                    lengths[b'TSI3'] = len(sTSI3)
                    w.alignToByteMultiple(4)
                    continue
                
                d.update(pto.get(tag, {}))
                
                if bsForced is not None:
                    w.addString(bsForced)
                
                else:
                    try:
                       self[tag].buildBinary  # Note: just checks for existence of method
                       isKnown = True
                    except AttributeError:
                       isKnown = False

                    if isKnown:
                       self[tag].buildBinary(w, **d)
                    else:
                       w.addString(self[tag])

                undoneChecksums[tag] = (startByteLength, w.byteLength)
            
            lengths[tag] = w.byteLength - startByteLength
            w.alignToByteMultiple(4)
        
        for tag, (start, stop) in undoneChecksums.items():
            checksums[tag] = w.checkSum(start, stop)
        
        # Now do final 'head' checksum adjustment
        w.deleteIndexMap("checksums")
        w.addIndexMap("checksums", checksums)
        w.deleteIndexMap("lengths")
        w.addIndexMap("lengths", lengths)
        # we checksum with zero in the 'head' checkSumAdjustment
        totalChecksum = w.checkSum()
        adjValue = (0xB1B0AFBA - totalChecksum) % 0x100000000
        w.deleteIndexMap("headAdj")
        w.addIndexMap("headAdj", {'head': adjValue})
    
    def buildBinary_headerOnly(
      self,
      w,
      stakes,
      baseStake,
      familyIndex,
      **kwArgs):
        
        """
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        self._updateDependentObjects()
        
        if kwArgs.get('forApple', False):
            w.addString(b"true")
        elif b'CFF ' in self:
            w.addString(b"OTTO")
        else:
            w.add("L", 0x10000)
        
        b = bsh.BSH(nUnits=len(self), unitSize=16)
        b.buildBinary(w, skipUnitSize=True)
        
        for tag in sorted(self):
            w.addString(tag)
            w.addUnresolvedIndex("L", "checksums", (familyIndex, tag))
            w.addUnresolvedOffset("L", baseStake, stakes[familyIndex][tag])
            w.addUnresolvedIndex("L", "lengths", (familyIndex, tag))
    
    def buildBinary_tablesOnly(
      self,
      w,
      stakes,
      changedKeys,
      uniques,
      familyIndex,
      checksums,
      lengths,
      headerChecksumRanges,
      **kwArgs):
        
        """
        """
        
        ck = changedKeys[familyIndex] | {b'head'}
        pto = kwArgs.pop('perTableOptions', {})
        wGlyfCached = None
        
        if b'TSI0' in ck or b'TSI1' in ck:
            ck.add(b'TSI0')
            ck.discard(b'TSI1')
        
        if b'TSI2' in ck or b'TSI3' in ck:
            ck.add(b'TSI2')
            ck.discard(b'TSI3')
        
        for tag in self._makeOffsetOrdering(kwArgs.get('forApple', False)):
            bsForced = None
            
            if (tag == b'TSI1') and (b'TSI0' in ck):
                continue
            
            elif (tag == b'TSI3') and (b'TSI2' in ck):
                continue
            
            # we only output a table if it's an avatar in uniques
            if familyIndex in uniques[tag]:
                if tag not in ck:
                    s = self.getRawTable(tag)
                
                else:
                    d = (_bbInfo[tag](self) if tag in _bbInfo else {})
                    d.update(kwArgs)
                    
                    if tag == b'bdat':
                        def _lc(newLoc): self.bloc = newLoc
                        d['locCallback'] = _lc
                        d['forApple'] = True  # override this
                        ck.add(b'bloc')
                    
                    elif tag == b'CBDT':
                        def _lc(newLoc): self.CBLC = newLoc
                        d['locCallback'] = _lc
                        d['forApple'] = False  # override this
                        ck.add(b'CBLC')
                    
                    elif tag == b'EBDT':
                        def _lc(newLoc): self.EBLC = newLoc
                        d['locCallback'] = _lc
                        d['forApple'] = False  # override this
                        ck.add(b'EBLC')
                    
                    elif tag == b'glyf':
                        if wGlyfCached is None:
                            wGlyfCached = writer.LinkedWriter()
                            d.update(pto.get(tag, {}))
                            def _lc(newLoca): self.loca = newLoca
                            d['locaCallback'] = _lc
                            self[tag].buildBinary(wGlyfCached, **d)
                        
                        bsForced = wGlyfCached.binaryString()
                    
                    elif tag == b'loca':
                        if wGlyfCached is None:
                            wGlyfCached = writer.LinkedWriter()
                            d.update(pto.get(b'glyf', {}))
                            def _lc(newLoca): self.loca = newLoca
                            d['locaCallback'] = _lc
                            self[b'glyf'].buildBinary(wGlyfCached, **d)
                    
                    elif tag == b'TSI0':  # this logic does both TSI0 and TSI1
                        dForTSI1 = (_bbInfo[b'TSI1'](self) if b'TSI1' in _bbInfo else {})
                        dForTSI1.update(kwArgs)
                        dForTSI1.update(pto.get(b'TSI1', {}))
                        locResult = []
                        dForTSI1['locCallback'] = (lambda newLoc: locResult.append(newLoc))
                        sTSI1 = self[b'TSI1'].binaryString(**dForTSI1)
                        d.update(pto.get(b'TSI0', {}))
                        sTSI0 = locResult[0].binaryString(**d)
                        w.addString(sTSI0)
                        undoneChecksums[b'TSI0'] = (startByteLength, w.byteLength)
                        lengths[b'TSI0'] = len(sTSI0)
                        w.alignToByteMultiple(4)
                        w.stakeCurrentWithValue(tagOffsetStake[b'TSI1'])
                        startByteLength = w.byteLength
                        w.addString(sTSI1)
                        undoneChecksums[b'TSI1'] = (startByteLength, w.byteLength)
                        lengths[b'TSI1'] = len(sTSI1)
                        w.alignToByteMultiple(4)
                        continue
                    
                    elif tag == b'TSI2':  # this logic does both TSI2 and TSI3
                        dForTSI3 = (_bbInfo[b'TSI3'](self) if b'TSI3' in _bbInfo else {})
                        dForTSI3.update(kwArgs)
                        dForTSI3.update(pto.get(b'TSI3', {}))
                        locResult = []
                        dForTSI3['locCallback'] = (lambda newLoc: locResult.append(newLoc))
                        sTSI3 = self[b'TSI3'].binaryString(**dForTSI3)
                        d.update(pto.get(b'TSI2', {}))
                        sTSI2 = locResult[0].binaryString(**d)
                        w.addString(sTSI2)
                        undoneChecksums[b'TSI2'] = (startByteLength, w.byteLength)
                        lengths[b'TSI2'] = len(sTSI2)
                        w.alignToByteMultiple(4)
                        w.stakeCurrentWithValue(tagOffsetStake[b'TSI3'])
                        startByteLength = w.byteLength
                        w.addString(sTSI3)
                        undoneChecksums[b'TSI3'] = (startByteLength, w.byteLength)
                        lengths[b'TSI3'] = len(sTSI3)
                        w.alignToByteMultiple(4)
                        continue
                    
                    d.update(pto.get(tag, {}))
                    
                    if tag == b'head':
                        d['useIndexMap'] = ('headAdj', familyIndex)
                    
                    if bsForced is not None:
                        s = bsForced
                    
                    else:
                        try:
                            s = self[tag].binaryString(**d)
                        except AttributeError:
                            s = self[tag]
                    
                w.stakeCurrentWithValue(stakes[familyIndex][tag])
                cs = utilitiesbackend.utChecksum(s)
                checksums[(familyIndex, tag)] = cs
                lengths[(familyIndex, tag)] = len(s)
                
                for otherIndex in uniques[tag][familyIndex]:
                    w.stakeCurrentWithValue(stakes[otherIndex][tag])
                    checksums[(otherIndex, tag)] = cs
                    lengths[(otherIndex, tag)] = len(s)
                
                w.addString(s)
                w.alignToByteMultiple(4)
        
        # Now do final 'head' adjustment
        start, stop = headerChecksumRanges[familyIndex]
        totalChecksum = w.checkSum(start, stop, unresolvedOK=True)
        
        for index, tag in sorted(checksums):
            if index == familyIndex:
                totalChecksum += checksums[(index, tag)]
        
        adjValue = (0xB1B0AFBA - totalChecksum) % 0x100000000
        w.addIndexMap(("headAdj", familyIndex), {'head': adjValue})
    
    @classmethod
    def frommissingglyph(cls, missingGlyphObj, mtxObj, **kwArgs):
        """
        Creates and returns a new Editor with the specified missing glyph.
        
        %start
        %kind
        classmethod
        %return
        A newly-created Editor, empty except for glyphs 0-3.
        %pos
        missingGlyphObj
        A TTSimpleGlyph representing the missing glyph.
        %pos
        mtxObj
        A hmtx.MtxEntry object with the metrics for the missingGlyphObj.
        %kw
        unitsPerEm
        An optional integer with the unitsPerEm used by the missingGlyphObj. If
        not specified, the default of 2048 will be used.
        %notes
        This classmethod can be used to make an essentially empty Editor, to
        which you can then make repeated addGlyph() calls to fill it with
        content. Glyphs 0-3 will be set up as .notdef, null, nonmarkingreturn,
        and space, respectively.
        %end
        """
        
        from fontio3 import hmtx
        from fontio3.cmap import cmapsubtable
        from fontio3.glyf import ttsimpleglyph
        from fontio3.maxp import maxp_tt
        from fontio3.name import name_key
        from fontio3.OS_2 import OS_2_v5
        
        emptyGlyph = ttsimpleglyph.TTSimpleGlyph()
        emptyMetrics = hmtx.MtxEntry()
        unitsPerEm = kwArgs.pop('unitsPerEm', 2048)
        r = cls()
        r.maxp = maxp_tt.Maxp_TT(numGlyphs=4)
        r.head = head.Head(unitsPerEm=unitsPerEm)
        r.head.flags.sidebearingAtX0 = True
        r.head.fontDirectionHint = 2
        # The following are filler values; they will be recalculated
        r.loca = loca.Loca([(0, 2), (2, 0), (2, 0), (2, 0)])
        
        r.glyf = glyf.Glyf({
          0: missingGlyphObj,
          1: emptyGlyph,
          2: emptyGlyph,
          3: emptyGlyph})
          
        cSub = cmapsubtable.CmapSubtable(
          {0: 1, 13: 2, 32: 3, 160: 3},
          preferredFormat = 4)
        
        r.cmap = cmap.Cmap({(3, 1, 0): cSub})
        r.hhea = hhea.Hhea()
        r.hhea.numLongMetrics = 4
        
        r.name = name.Name({
          name_key.Name_Key((1, 0, 0, 0)): "Copyright © 2015 Monotype",
          name_key.Name_Key((3, 1, 1033, 0)): "Copyright © 2015 Monotype",
          name_key.Name_Key((1, 0, 0, 1)): "Empty",
          name_key.Name_Key((3, 1, 1033, 1)): "Empty",
          name_key.Name_Key((1, 0, 0, 2)): "Regular",
          name_key.Name_Key((3, 1, 1033, 2)): "Regular",
          name_key.Name_Key((1, 0, 0, 4)): "Empty Regular",
          name_key.Name_Key((3, 1, 1033, 4)): "Empty Regular",
          name_key.Name_Key((1, 0, 0, 5)): "Version 0.00",
          name_key.Name_Key((3, 1, 1033, 5)): "Version 0.00",
          name_key.Name_Key((1, 0, 0, 6)): "empty",
          name_key.Name_Key((3, 1, 1033, 6)): "empty",
          })
        
        r.post = post.Post(
          {0: ".notdef", 1: "null", 2: "nonmarkingreturn", 3: "space"})
        
        r.post.preferredFormat = 2
        
        r.hmtx = hmtx.Hmtx({
          0: mtxObj,
          1: emptyMetrics,
          2: emptyMetrics,
          3: hmtx.MtxEntry()})
        
        r.hmtx[3].advance = r.hmtx[0].advance + 5
        r['OS/2'] = OS_2_v5.OS_2()
        r = r.recalculated(editor=r)
        r.hhea.ascent = r.head.yMax
        r['OS/2'].usWinAscent = r.head.yMax
        r.hhea.descent = r.head.yMin - 5
        r['OS/2'].usWinDescent = abs(r.head.yMin - 5)
        return r
    
    @classmethod
    def frompath(cls, path, **kwArgs):
        """
        """
        
        return cls.fromwalker(
          filewalkerbit.FileWalkerBit(path),
          originalPath = path,
          **kwArgs)
    
    @classmethod
    def fromvalidatedpath(cls, path, **kwArgs):
        """
        """
        
        return cls.fromvalidatedwalker(
          filewalkerbit.FileWalkerBit(path),
          originalPath = path,
          **kwArgs)
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new Editor. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method).
        """
        
        forApple = kwArgs.pop('forApple', False)
        fromTTC = kwArgs.pop('fromTTC', False)
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('fontedit')
        else:
            logger = logger.getChild('fontedit')
        
        startOffset = w.getOffset()
        endOfFile = int(w.length())
        logger.debug(('V0001', (endOfFile,), "Walker has %d remaining bytes"))
        endOfFile += startOffset
        
        okToProceed, version = cls._validate_version(w, forApple, logger)
        isTrueType = (version == b'\x00\x01\x00\x00' or version == b'true')
        
        if not okToProceed:
            return None
        
        okToProceed, numTables = cls._validate_binSearch(w, logger)
        
        if not okToProceed:
            return None
        
        okToProceed, toc = cls._validate_toc(
          w,
          logger,
          numTables,
          startOffset,
          endOfFile,
          fromTTC)
        
        if not okToProceed:
            return None
        
        okToProceed = cls._validate_topology(
          w,
          logger,
          toc,
          isTrueType,
          forApple,
          fromTTC)
        
        if not okToProceed:
            return None
        
        okToProceed = cls._validate_repertoire(logger, toc, isTrueType)
        
        if not okToProceed:
            return None
        
        w.reset()
        w.skip(startOffset)
        kwArgs.pop('doValidation', None)
        r = cls.fromwalker(w, doValidation=True, logger=logger, **kwArgs)
        tablesToValidate = sorted(set(r) - set(kwArgs.get('tablesToSkip', [])))
        skippedTables = sorted(set(r) - set(tablesToValidate))
        
        for s in skippedTables:
            t_logger = logger.getChild(s)
            
            t_logger.error((
              'V0532',
              (),
              "Incomplete validation: table was skipped."))
        
        for key in tablesToValidate:
            obj = r[key]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        """
        
        version = w.unpack("4s", advance=False)
        toc = w.group("4s3L", w.unpack("4xH6x"))
        otki = (obj[0] for obj in toc)
        pieceInfo = {}
        
        for tag, ignore, offset, size in toc:
            pieceInfo[tag] = w.subWalker(offset, newLimit=offset+size)
        
        ce = dict(
          oneTimeKeyIterator = otki,
          pieceInfo = pieceInfo,
          doValidation = kwArgs.get('doValidation', False),
          logger = kwArgs.get('logger', None),
          tablesToSkip = kwArgs.get('tablesToSkip', []),
          originalPath = kwArgs.get('originalPath', None),
          perTableOptions = kwArgs.get('perTableOptions', {}),
          version=version)
        
        return cls(creationExtras=ce)
    
    def getNamer(self):
        d = self.__dict__
        
        if '_namer' not in d or d['_namer'] is None:
            d['_namer'] = namer.Namer(self)
        
        return d['_namer']
    
    def getRawTable(self, key):
        """
        Returns a bytes object with the raw data for the specified key. If the
        specified table is not in the Editor, returns None.
        """
        
        rw = self.getRawWalker(key)
        return (None if rw is None else rw.rest())
    
    def getRawWalker(self, key):
        """
        Returns a subWalker with the raw data for the specified key. Note that
        this doesn't go through a string intermediary first, so it should be
        very fast even for filewalkers.
        
        This returns None if the key is not present, or if the Editor was
        reconstructed such that the pieceInfo key is not present in
        self._creationExtras.
        """
        
        if not isinstance(key, bytes):
            key = key.encode('ascii')
        
        if (key not in self) or ('pieceInfo' not in self._creationExtras):
            return None
        
        ce = self._creationExtras['pieceInfo']
        
        if key not in ce:
            return None
        
        w = ce[key]
        w.reset()
        return w.subWalker(0, relative=True)
    
    def glyphsRenumbered(self, oldToNew, **kwArgs):
        """
        Returns a new Editor with glyphs renumbered as specified.
        """
        
        from fontio3.glyf import ttsimpleglyph
        from fontio3.CFF import cffglyph
        d = {}
        numGlyphs = self.maxp.numGlyphs
        km = kwArgs.pop('keepMissing', True)
        toDel = set()

        for tag, tableObj in self.items():
            if tag == b'CFF ':
                d[tag] = tableObj.glyphsRenumbered(
                  oldToNew,
                  keepMissing = km)

                for n in range(max(oldToNew.values()) + 1, numGlyphs):
                    if n in d[tag]:
                        del d[tag][n]

            elif tag == b'glyf':
                fn = lambda i, **k: ttsimpleglyph.TTSimpleGlyph()
        
                d[tag] = tableObj.glyphsRenumbered(
                  oldToNew,
                  keepMissing = km,
                  missingKeyReplacementFunc = fn)
        
                for n in range(max(oldToNew.values()) + 1, numGlyphs):
                    if n in d[tag]:
                        del d[tag][n]
    
            elif tag in {b'hmtx', b'vmtx'}:
                fn = lambda i, **k: hmtx.MtxEntry()
        
                d[tag] = tableObj.glyphsRenumbered(
                  oldToNew,
                  keepMissing = km,
                  missingKeyReplacementFunc = fn)
        
                for n in range(max(oldToNew.values()) + 1, numGlyphs):
                    if n in d[tag]:
                        del d[tag][n]
    
            elif tag == b'post':
                fn = lambda i, **k: "g%d" % (i,)
        
                d[tag] = tableObj.glyphsRenumbered(
                  oldToNew,
                  keepMissing = km,
                  missingKeyReplacementFunc = fn)
        
                for n in range(max(oldToNew.values()) + 1, numGlyphs):
                    if n in d[tag]:
                        del d[tag][n]
    
            elif tag in {b'fpgm', b'loca', b'prep'}:
                d[tag] = tableObj
    
            elif tag in {b'GPOS', b'GSUB'}:
                obj = tableObj.glyphsRenumbered(oldToNew, keepMissing=False)
                obj = obj.compacted()
                
                if obj is None or obj.scripts is None:
                    toDel.add(tag)
                    continue
                
                obj.scripts.trimToValidFeatures(set(obj.features))
                obj = obj.coalesced()
                d[tag] = obj
    
            elif tag in {b'morx'}:
                obj = tableObj.glyphsRenumbered(oldToNew, keepMissing=False)
                obj = obj.compacted()
                obj = obj.coalesced()
                d[tag] = obj
    
            else:
                d[tag] = tableObj.glyphsRenumbered(
                  oldToNew,
                  keepMissing = km)

        d[b'maxp'].numGlyphs = max(oldToNew.values()) + 1
        d[b'hhea'].numLongMetrics = d[b'maxp'].numGlyphs
        r = self.__copy__()
        r._dOrig = r._dOrig.copy()
        r._dAdded = r._dAdded.copy()
        r.update(d)

        for tag in toDel:
            del r[tag]

        for tag in d:
            r.changed(tag)

        if '_namer' in r.__dict__ and r.__dict__['_namer'] is not None:
            r.__dict__['_namer'] = namer.Namer(r)

        return r
    
    def setRawTable(self, key, value, **kwArgs):
        """
        Sets the value (which must be a bytestring) for the specified key. The
        following keyword arguments are supported:
        
            doValidation    A Boolean (default False) determining whether the
                            object will be "brought to life" with validation.
                            Note this only happens if the key is known (i.e.
                            it is present in the _validatedMakerInfo dict).
            
            logger          If validation is to be done, this logger will be
                            passed into the fromvalidated...() calls.
            
            reanimate       If a setRawTable() call is made to set a known kind
                            of table, the bytes will normally be read to bring
                            the object to life. If you wish to prevent that,
                            set reanimate to False (default is True).
        """
        
        if not isinstance(key, bytes):
            key = key.encode('ascii')
        
        doValidation = kwArgs.pop('doValidation', False)
        logger = kwArgs.pop('logger', logging.getLogger())
        reanimate = kwArgs.pop('reanimate', True)
        
        if reanimate and doValidation and (key in _validatedMakerInfo):
            w = walkerbit.StringWalker(value)
            f, tagsToCheck, kwArgsFunc = _validatedMakerInfo[key]
            
            if all(self.reallyHas(t) for t in tagsToCheck):
                value = f(w, logger=logger, **(kwArgsFunc(self)))
            
            else:
                logger.warning((
                  'G0041',
                  (key, tagsToCheck),
                  "Unable to create the '%s' table, because one or more "
                  "prerequisite tables in the group %s was not present or "
                  "had errors preventing their own creation."))
                
                value = None
        
        elif reanimate and (not doValidation) and (key in _makerInfo):
            w = walkerbit.StringWalker(value)
            f, kwArgsFunc = _makerInfo[key]
            value = f(w, **(kwArgsFunc(self)))
        
        if reanimate:
            self[key] = value
        
        else:
            self._dAdded[key] = value
            
            if key in self._dOrig:
                del self._dOrig[key]
    
    def writeFont(self, path, **kwArgs):
        """
        """
        
        f = open(path, "wb")
        f.write(self.binaryString(**kwArgs))
        f.close()

    def writeEOTFont(self, path, **kwArgs):
        """
        Write Editor as an EOT file. Simple XOR "encryption" may be
        specified with the 'doXOREncryption' kwArg. The presence of an
        object for the 'mtx' kwArg implies that you desire
        MicroTypeExpress (MTX) compression, 'cause compressors gonna
        compress...
        """
        
        pflags = 0

        mtx = kwArgs.get('mtx', None)
        if mtx:
            ucdata = self.binaryString(**kwArgs)
            fontdata = mtx.compress(ucdata)
            pflags = pflags | 0x00000004
            sfntSize = len(fontdata)
        else:
            fontdata = self.binaryString(**kwArgs)
            sfntSize = len(fontdata)
            
        if kwArgs.get('doXOREncryption', False):
            pflags = pflags | 0x10000000
            # each byte of fontdata is simply XOR-ed with 0x50
            xordata = ''.join( [chr(ord(b) ^ 0x50) for b in fontdata] )
            fontdata = xordata
            # note that this doesn't change sfntSize, only the content.
        
        # EOT Header. Note EOT *header* is Little Endian, while the
        # FontData section is Big Endian. Yeah, really.
        eb = io.BytesIO()
        eb.write(b'\xDE\xAD\xBE\xEF')            # temp EOTSize
        eb.write(struct.pack("<L", sfntSize))   # FontDataSize
        eb.write(struct.pack("<L", 0x00020001)) # Version
        eb.write(struct.pack("<L", pflags))     # Flags

        pb = self['OS/2'].panoseArray.binaryString()
        eb.write(struct.pack("<BBBBBBBBBB", *[b for b in iter(bytes(pb))])) # Panose
        eb.write(b'\x00')                       # Charset (=ANSI_CHARSET)
        eb.write(b'\x01' if self['OS/2'].fsSelection.italic else b'\x00') # Italic
        eb.write(struct.pack("<L", self['OS/2'].usWeightClass)) # Weight
        tpl = struct.unpack(">H", self['OS/2'].fsType.binaryString())
        eb.write(struct.pack("<H", *tpl))       # fsType
        eb.write(struct.pack("<H", 0x504C))     # MagicNumber

        tpl = struct.unpack(">LLLL", self['OS/2'].unicodeRanges.binaryString())
        eb.write(struct.pack("<LLLL", *tpl))    # UnicodeRange1-4

        tpl = struct.unpack(">LL", self['OS/2'].codePageRanges.binaryString())
        eb.write(struct.pack("<LL", *tpl))      # CodePageRange1-2
        eb.write(struct.pack("<L", self.head.checkSumAdjustment)) # CheckSumAdjustment
        eb.write(struct.pack("<LLLL", 0, 0, 0, 0)) # Reserved1-4

        eb.write(b'\x00\x00')                   # Padding1
        nUTF16 = self.name.getNameFromID(1).encode('UTF-16LE')
        eb.write(struct.pack("<H", len(nUTF16)))
        eb.write(nUTF16)                        # FamilyName

        eb.write(b'\x00\x00')                   # Padding2        
        nUTF16 = self.name.getNameFromID(2).encode('UTF-16LE')
        eb.write(struct.pack("<H", len(nUTF16)))
        eb.write(nUTF16)                        # SubfamilyName

        eb.write(b'\x00\x00')                   # Padding3
        nUTF16 = self.name.getNameFromID(5).encode('UTF-16LE')
        eb.write(struct.pack("<H", len(nUTF16)))
        eb.write(nUTF16)                        # VersionName
        
        eb.write(b'\x00\x00')                   # Padding4
        nUTF16 = self.name.getNameFromID(4).encode('UTF-16LE')
        eb.write(struct.pack("<H", len(nUTF16)))
        eb.write(nUTF16)                        # FullName

        eb.write(b'\x00\x00')                   # Padding5
        eb.write(b'\x00\x00')                   # RootStringSize (=0; no RootStrings)

        eb.write(fontdata)                           # FontData        
        eotSize = eb.tell()
        eb.seek(0)
        eb.write(struct.pack("<L", eotSize))    # EOTSize

        f = open(path, "wb")
        f.write(eb.getvalue())
        f.close()

    def writeWoffFont(self, path, **kwArgs):
        """
        Write Editor as a WOFF file. Optional meta and private data
        to include as part of the WOFF may be specified with the
        'metadata' or 'privatedata' kwArgs.
        """
        
        sbb = self.binaryString(**kwArgs)
        sfntSize = len(sbb)
        sb = io.BytesIO(sbb)
        
        metadata = kwArgs.get('metadata', "")
        # metadata MUST be well-formed XML; if it's not, we don't include it.
        try:
            md = minidom.parseString(metadata)
        except ExpatError:
            metadata = ""
        
        metadataCmp = zlib.compress(metadata, 9)
        privatedata = kwArgs.get('privatedata', "")
        wb = writer.LinkedWriter()
        tStart = wb.stakeCurrent()
        wb.addString(b'wOFF')                                # WOFF signature
        wb.addString(sb.read(4))                             # flavor
        tEnd = wb.getNewStake()                              
        wb.addUnresolvedOffset("L", tStart, tEnd)            # WOFF length
        numTables = struct.unpack(">H", sb.read(2))[0]
        wb.add("H", numTables)                               # numTables
        wb.add("H", 0)                                       # reserved (0)
        wb.add("L", sfntSize)                                # totalSfntSize
        wb.add("L", self.head.fontRevision)                  # majorVersion, minorVersion

        if metadata:
            tMetaOffset = wb.getNewStake()             
            wb.addUnresolvedOffset("L", tStart, tMetaOffset) # metaOffset
            wb.add("L", len(metadataCmp))                    # metaLength
            wb.add("L", len(metadata))                       # metaOrigLength
        else:
            wb.add("LLL", 0,0,0)                             # all MUST be 0

        if privatedata:        
            tPrivOffset = wb.getNewStake()
            wb.addUnresolvedOffset("L", tStart, tPrivOffset) # privOffset
            wb.add("L", len(privatedata))                    # privLength
        else:
            wb.add("LL", 0,0 )                               # all MUST be 0

        
        # Table Directory
        sb.seek(12)
        dTKOL = {}
        tOFstakes = {}
        tLCstakes = {}
        for t in range(numTables):
            ttag, tcks, toff, tlen = struct.unpack(">LLLL", sb.read(16))
            dTKOL[t] = (ttag, tcks, toff, tlen)

            wb.add("L", ttag)                                    # tag
            tOFstakes[t] = wb.getNewStake()
            wb.addUnresolvedOffset("L", tStart, tOFstakes[t])    # offset
            tLCstakes[t] = wb.addDeferredValue("L")              # lenCompressed
            wb.add("L", tlen)                                    # lenUncompressed
            wb.add("L", tcks)                                    # checksumUncompressed


        # Table Data
        tOrder = sorted(dTKOL, key=lambda x:dTKOL[x][2])
        for t in tOrder:
            wb.alignToByteMultiple(4)
            sb.seek(dTKOL[t][2])
            tblRaw = sb.read(dTKOL[t][3])
            tblCmp = zlib.compress(tblRaw, 9)
            if len(tblCmp) >= len(tblRaw): tblCmp = tblRaw
            wb.setDeferredValue(tLCstakes[t], "L", len(tblCmp))
            wb.stakeCurrentWithValue(tOFstakes[t])
            wb.addString(tblCmp)            
        wb.alignToByteMultiple(4)
        
        # meta and private data, if present
        if metadata:
            wb.alignToByteMultiple(4)
            wb.stakeCurrentWithValue(tMetaOffset)
            wb.addString(metadataCmp)

        if privatedata:
            wb.alignToByteMultiple(4)
            wb.stakeCurrentWithValue(tPrivOffset)
            wb.addString(privatedata)

        wb.stakeCurrentWithValue(tEnd)            

        wf = open(path, "wb")
        wf.write(wb.binaryString())
        wf.close()

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
