#
# LTSH.py
#
# Copyright © 2007-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for the LTSH table.
"""

# System imports
import pickle

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import ScalerError

# -----------------------------------------------------------------------------

#
# Private functions
#

def _recalc(d, **kwArgs):
    try:
        editor = kwArgs['editor']
    except KeyError:
        raise NoEditor()
    
    # look for cached recalculated table first
    if 'ltshpicklefile' in editor.__dict__:
        tmpfile = open(editor.__dict__['ltshpicklefile'], 'rb+')
        dNew = pickle.load(tmpfile)
        return (d != dNew, dNew)

    # recalculate independently    
    try:
        scaler = kwArgs['scaler']
    except KeyError:
        return False, d
    
    dNew = type(d)(dict.fromkeys(d, 1))
    
    if not editor.reallyHas(b'head'):
        raise NoHead()
    
    if not editor.head.flags.opticalAdvanceViaHints:
        return (False, d)
    
    upem = editor.head.unitsPerEm
    
    if not editor.reallyHas(b'hmtx'):
        raise NoHmtx()
    
    hmtx = editor.hmtx
    
    try:
        f = scaler.getBitmapMetrics
    except AttributeError:
        f = scaler.getBitmap
    
    if not editor.reallyHas(b'maxp'):
        raise NoMaxp()
    
    stillInProcess = set(range(editor.maxp.numGlyphs))
    
    for ppem in range(254, 49, -1):
        if not stillInProcess:
            break
        
        try:
            scaler.setPointsize(ppem)
        except:
            raise ScalerError()
        
        toDel = set()
        
        for glyph in stillInProcess:
            #try: bmapAdvWidth = f(glyph).i_dx ### see Jira ITP-2133
            
            try:
                bmapAdvWidth = round(f(glyph).dx)
            except:
                raise ScalerError()
            
            hiResAdvWidth = int(
              (ppem * hmtx[glyph].advance / upem) * 65536.0 + 0.5)
            
            hiResAdvWidth = (((hiResAdvWidth + 512) >> 10) + 32) >> 6
            diff = abs(hiResAdvWidth - bmapAdvWidth)
            
            if diff > (0.02 * hiResAdvWidth):
                toDel.add(glyph)
                dNew[glyph] = ppem + 1
        
        stillInProcess -= toDel
    
    for ppem in range(49, 0, -1):
        if not stillInProcess:
            break
        
        try:
            scaler.setPointsize(ppem)
        except:
            raise ScalerError()
        
        toDel = set()
        
        for glyph in stillInProcess:
            #try: bmapAdvWidth = f(glyph).i_dx ### see Jira ITP-2133
            
            try:
                bmapAdvWidth = round(f(glyph).dx)
            except:
                raise ScalerError()
            
            hiResAdvWidth = int(
              (ppem * hmtx[glyph].advance / upem) * 65536.0 + 0.5)
            
            hiResAdvWidth = (hiResAdvWidth + 0x8000) >> 16
            
            if bmapAdvWidth != hiResAdvWidth:
                toDel.add(glyph)
                dNew[glyph] = ppem + 1
        
        stillInProcess -= toDel
    
    return (d != dNew, dNew)

def _validate(d, **kwArgs):
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    if not (
      editor.reallyHas(b'head') and
      editor.reallyHas(b'hmtx') and
      editor.reallyHas(b'maxp')):
        
        logger.error((
          'V0553',
          (),
          "Unable to validate 'LTSH' table because one or more of the "
          "'head', 'hmtx', and 'maxp' tables are missing or empty."))
        
        return False
    
    scaler = kwArgs.get('scaler', None)
    
    if set(d) != set(range(editor.maxp.numGlyphs)):
        logger.error((
          'V0233',
          (),
          "There are gaps or other inconsistencies in the glyph set"))
        
        return False
    
    if not editor.head.flags.opticalAdvanceViaHints:
        logger.warning((
          'V0232',
          (),
          "LTSH table shouldn't be present if head flag 4 is off"))
    
    if not all(d.values()):
        logger.warning((
          'W1800',
          (),
          "There are entries with zero yPel values"))
    
    if scaler is not None:
        try:
            changed, dNew = _recalc(d, **kwArgs)
        
        except ScalerError:
            logger.error((
              'V0554',
              (),
              "An error occured in the scaler during device metrics "
              "calculation, preventing validation."))
            
            return False

        if changed:
            badKeys = {i for i, n in d.items() if n != dNew[i]}
            
            for glyph in sorted(badKeys):
                if dNew[glyph] < 0:
                    logger.error((
                      'V0810',
                      (glyph,),
                      "Glyph %d's recalculated advance was negative"))
                
                else:
                    logger.error((
                      'E1804',
                      (glyph, dNew[glyph], d[glyph]),
                      "Glyph %d's value should be %d, but is %d"))
            
            return False
            
    else:
        logger.warning((
          'V0785',
          (),
          "Device metrics will not be tested against scaler results "
          "because a scaler was not supplied."))
        
        return False
    
    return True

# -----------------------------------------------------------------------------

#
# Exceptions
#

if 0:
    def __________________(): pass

class NoEditor(ValueError): pass
class NoHead(ValueError): pass
class NoHmtx(ValueError): pass
class NoMaxp(ValueError): pass

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class LTSH(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire LTSH tables. These are dicts whose keys are
    glyph indices and whose values are the PPEM at which linear scaling takes
    over.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_recalculatefunc = _recalc,
        map_validatefunc_partial = _validate)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the LTSH to the specified walker.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # This code presumes isValid() has already been done, and thus the
        # key set for the dict matches the font's glyph count.
        
        w.add("2H", 0, len(self))
        w.addGroup("B", (self[i] for i in sorted(self)))
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new LTSH. However, it also
        does extensive validation via the logging module (the client should
        have done a logging.basicConfig call prior to calling this method,
        unless a logger is passed in via the 'logger' keyword argument).
        
        >>> from fontio3 import utilities
        >>> logger = utilities.makeDoctestLogger('test')
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('LTSH')
        else:
            logger = logger.getChild('LTSH')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 4:
            logger.error(('V0004', (), "Insufficient bytes"))
            return None
        
        version, count = w.unpack("2H")
        
        if version != 0:
            logger.error((
              'E1803',
              (version,),
              "Expected version 0, but got %d"))
            
            return None
        else:
            logger.info((
              'V0899',
              (),
              "Table version is 0."))
        
        if count != kwArgs['fontGlyphCount']:
            logger.error((
              'E1800',
              (kwArgs['fontGlyphCount'], count),
              "Font has %d glyphs, but table count is %d"))
            
            return None
            
        else:
            logger.info((
              'V0900',
              (),
              "Table's count matches the font's number of glyphs."))
        
        if w.length() != count:
            logger.error((
              'E1802',
              (),
              "Table does not have expected length"))
            
            return None
            
        else:
            logger.info((
              'V0901',
              (),
              "Table length matches the expected value."))
        
        t = w.group("B", count)
        return cls((i, n) for i, n in enumerate(t))
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new LTSH object from the specified walker.
        """
        
        version = w.unpack("H")
        
        if version != 0:
            raise ValueError("Unknown 'LTSH' version: 0x%04X" % (version,))
        
        t = w.group("B", w.unpack("H"))
        return cls((i, n) for i, n in enumerate(t))

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
