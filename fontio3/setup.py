#
# setup.py -- setup for fontio3 package
#
# Copyright © 2004-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Setup for fontio3 package.
"""

# System imports
import sys
from distutils.core import setup, Extension
import fontio3

# -----------------------------------------------------------------------------

if sys.platform == "darwin":
    eca = ['-Wall']
else:
    eca = []

fastMathHelper = Extension(
    "fontio3.fastmathbackend",
    sources = ["fontio3/backend/fastmath.c"],
    extra_compile_args = eca)

fileWalkerBitHelper = Extension(
    "fontio3.filewalkerbitbackend",
    sources = ["fontio3/backend/filewalkerbit.c"],
    extra_compile_args = eca)

fileWalkerHelper = Extension(
    "fontio3.filewalkerbackend",
    sources = ["fontio3/backend/filewalker.c"],
    extra_compile_args = eca)

walkerBitHelper = Extension(
    "fontio3.walkerbitbackend",
    sources = ["fontio3/backend/walkerbit.c"],
    extra_compile_args = eca)

walkerHelper = Extension(
    "fontio3.walkerbackend",
    sources = ["fontio3/backend/walker.c"],
    extra_compile_args = eca)

utilitiesHelper = Extension(
    "fontio3.utilitiesbackend",
    sources = ["fontio3/backend/utilities.c"],
    extra_compile_args = eca)

cSpanHelper = Extension(
    "fontio3.cspanbackend",
    sources = ["fontio3/backend/cspan.c"],
    extra_compile_args = eca)

setup(
  name = "fontio3",
  version = "3.6.x%s" % (fontio3.__version__,),
  description = "Font utilities for sfnt analysis and construction",
  author = "Dave Opstad, Chuck Rowe, Josh Hadley, Daisy Gallardo, Christopher Chapman",
  author_email = "dave.opstad@monotypeimaging.com",
  url = "http://wiki/display/FT/fontio",
  
  packages = [
    'fontio3',
    'fontio3/ADFH',
    'fontio3/ankr',
    'fontio3/avar',
    'fontio3/BASE',
    'fontio3/bsln',
    'fontio3/CFF',
    'fontio3/cmap',
    'fontio3/COLR',
    'fontio3/CPAL',
    'fontio3/cvar',
    'fontio3/DSIG',
    'fontio3/EBSC',
    'fontio3/fdsc',
    'fontio3/feat',
    'fontio3/fontdata',
    'fontio3/fontmath',
    'fontio3/fvar',
    'fontio3/gasp',
    'fontio3/GDEF',
    'fontio3/glyf',
    'fontio3/GPOS',
    'fontio3/GSUB',
    'fontio3/gvar',
    'fontio3/h2',
    'fontio3/hdmx',
    'fontio3/head',
    'fontio3/hints',
    'fontio3/hints/details',
    'fontio3/hints/history',
    'fontio3/JSTF',
    'fontio3/just',
    'fontio3/HVAR',
    'fontio3/kern',
    'fontio3/kerx',
    'fontio3/lcar',
    'fontio3/maxp',
    'fontio3/meta',
    'fontio3/mort',
    'fontio3/morx',
    'fontio3/MTad',
    'fontio3/MTap',
    'fontio3/MTcc',
    'fontio3/MTcl',
    'fontio3/MTsf',
    'fontio3/MVAR',
    'fontio3/name',
    'fontio3/opbd',
    'fontio3/opentype',
    'fontio3/OS_2',
    'fontio3/PCLT',
    'fontio3/post',
    'fontio3/prop',
    'fontio3/sbit',
    'fontio3/sbix',
    'fontio3/SparkHints',
    'fontio3/SPRK',
    'fontio3/STAT',
    'fontio3/statetables',
    'fontio3/trak',
    'fontio3/triple',
    'fontio3/TSI',
    'fontio3/utilities',
    'fontio3/VDMX',
    'fontio3/vhea',
    'fontio3/VVAR',
    'fontio3/Zapf'],
  
  ext_modules = [
    fastMathHelper,
    fileWalkerBitHelper,
    fileWalkerHelper,
    walkerBitHelper,
    walkerHelper,
    utilitiesHelper,
    cSpanHelper
    ])
