#
# validate.py
#
# Copyright © 2012-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for hint validation.
"""

# System imports
import logging

# Other imports
from fontio3.hints import ttstate

# -----------------------------------------------------------------------------

#
# Classes
#

class HintsValidator:
    """
    Class to support validating the hints in an entire Editor.
    """
    
    #
    # Initialization method
    #
    
    def __init__(self, editor, **kwArgs):
        """
        """
        
        self.logger = kwArgs.pop('logger', logging.getLogger())
        
        if b'CFF ' in editor:
            self.logger.warning((
              'V0533',
              (),
              "Rasterization tests are not currently performed on CFF fonts."))
            
            self.editor = None
        
        elif b'SPRK' in editor:
            self.logger.warning((
              'Vxxxx',
              (),
              "Spark hint validation must be done separately"))
            
            self.editor = None
        
        else:
            self.editor = editor
        
        self._tableConsistencyCheck()  # sets self.okToDoGlyphs
    
    #
    # Private methods
    #
    
    def _tableConsistencyCheck(self):
        e = self.editor
        
        if e is None:
            self.okToDoGlyphs = False
            return
        
        hasFuncs = e.reallyHas(b'fpgm')
        hasPrep = e.reallyHas(b'prep')
        hasCVTs = e.reallyHas(b'cvt ')
        glyfCohortMissing = not (e.reallyHas(b'glyf') and e.reallyHas(b'maxp'))
        
        if glyfCohortMissing:
            hasHints = False
        else:
            hasHints = any(x.hintBytes for x in e.glyf.values() if x)
        
        t = (hasFuncs, hasPrep, hasCVTs, hasHints)
        self._consistencyFuncs[t](self)
    
    def _tcc_allHints(self):
        self.logger.info((
          'V0549',
          (),
          "Font has a full complement of hint-related tables."))
        
        self.okToDoGlyphs = True
    
    def _tcc_cvt(self):
        self.logger.warning((
          'V0534',
          (),
          "Font has CVT but no glyph hints, function definitions, or "
          "pre-program. The CVT may be removed to save space."))
        
        self.okToDoGlyphs = False
    
    def _tcc_func(self):
        self.logger.warning((
          'V0542',
          (),
          "Font has function definitions, but no CVT, glyph hints, or "
          "pre-program. The fpgm may be removed to save space."))
        
        self.okToDoGlyphs = False
    
    def _tcc_func_cvt(self):
        self.logger.warning((
          'V0546',
          (),
          "Font has function definitions and a control value table, but "
          "no glyph hints or pre-program. The fpgm and CVT may be removed "
          "to save space."))
        
        self.okToDoGlyphs = False
    
    def _tcc_func_prep(self):
        self.logger.warning((
          'V0545',
          (),
          "Font has function definitions and a pre-program, but no "
          "glyph hints or control value table."))
        
        self.okToDoGlyphs = False
    
    def _tcc_func_prep_cvt(self):
        self.logger.warning((
          'V0549',
          (),
          "Font has function definitions, a pre-program, and a control "
          "value program, but no glyph hints."))
        
        self.okToDoGlyphs = False
    
    def _tcc_glyph(self):
        self.logger.warning((
          'V0536',
          (),
          "Font has glyph hints but no CVT, function definitions, or "
          "pre-program."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_cvt(self):
        self.logger.warning((
          'V0537',
          (),
          "Font has glyph hints and a control value table, but no "
          "pre-program or function definitions."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_func(self):
        self.logger.warning((
          'V0543',
          (),
          "Font has glyph hints and function definitions, but no "
          "pre-program or control value table."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_func_cvt(self):
        self.logger.warning((
          'V0544',
          (),
          "Font has glyph hints, a control value table, and function "
          "definitions, but no pre-program."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_func_prep(self):
        self.logger.warning((
          'V0547',
          (),
          "Font has glyph hints, function definitions, and a pre-program, "
          "but no control value table."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_prep(self):
        self.logger.warning((
          'V0539',
          (),
          "Font has glyph hints and a pre-program, but no "
          "CVT or function definitions."))
        
        self.okToDoGlyphs = True
    
    def _tcc_glyph_prep_cvt(self):
        self.logger.info((
          'V0541',
          (),
          "Font has glyph hints, a pre-program, and a control value table, "
          "but no function definitions."))
        
        self.okToDoGlyphs = True
    
    def _tcc_noHints(self):
        self.logger.warning((
          'V0535',
          (),
          "Font has no hints of any kind, so no rasterization tests "
          "will be run."))
        
        self.okToDoGlyphs = False
    
    def _tcc_prep(self):
        self.logger.warning((
          'V0538',
          (),
          "Font has only a pre-program, but no glyph hints, CVT, or "
          "function definitions."))
        
        self.okToDoGlyphs = False
    
    def _tcc_prep_cvt(self):
        self.logger.warning((
          'V0540',
          (),
          "Font has a pre-program and a CVT, but no glyph hints or "
          "function definitions."))
        
        self.okToDoGlyphs = False
    
    _consistencyFuncs = {
        (False, False, False, False): _tcc_noHints,
        (False, False, False, True): _tcc_glyph,
        (False, False, True, False): _tcc_cvt,
        (False, False, True, True): _tcc_glyph_cvt,
        (False, True, False, False): _tcc_prep,
        (False, True, False, True): _tcc_glyph_prep,
        (False, True, True, False): _tcc_prep_cvt,
        (False, True, True, True): _tcc_glyph_prep_cvt,
        (True, False, False, False): _tcc_func,
        (True, False, False, True): _tcc_glyph_func,
        (True, False, True, False): _tcc_func_cvt,
        (True, False, True, True): _tcc_glyph_func_cvt,
        (True, True, False, False): _tcc_func_prep,
        (True, True, False, True): _tcc_glyph_func_prep,
        (True, True, True, False): _tcc_func_prep_cvt,
        (True, True, True, True): _tcc_allHints}
    
    #
    # Public methods
    #
    
    def validate(self, **kwArgs):
        """
        """
        
        e = self.editor
        
        if e is None:
            return True
        
        if not (e.reallyHas(b'prep') and self.okToDoGlyphs):
            return True
        
        logger = kwArgs.pop('logger', self.logger).getChild("hints")
        
        if not e.reallyHas(b'head'):
            logger.error((
              'V0553',
              (),
              "Unable to validate hints because one or more "
              "table is missing."))
            
            return False
        
        s = ttstate.TrueTypeState.fromeditor(e)
        s._validationFailed = False
        
        try:
            s.runPreProgram(logger=logger)
        
        except ValueError:
            logger.error((
              'V0553',
              (),
              "Unable to validate hints because one or more "
              "table is missing."))
            
            return False
        
        failed = s._validationFailed
        extraInfo = {}
        
        if self.okToDoGlyphs:
            g = e.glyf
            
            for i in range(e.maxp.numGlyphs):
                if g[i] is None:
                    logger.error((
                      'V0551',
                      (i,),
                      "Unable to validate hints on glyph %d because it was "
                      "ill-formed and could not be created."))
                    
                    continue
                
                logger.debug(('Vxxxx', (i,), "Validating glyph %d"))
                h, sSub = s.runGlyphSetup(i)
                
                if h:
                    sSub._validationFailed = False
                    h.run(sSub, logger=logger, extraInfo=extraInfo)
                    failed = failed or sSub._validationFailed
        
        if e.head.flags.opticalAdvanceViaHints:
            if extraInfo.get('phantomAdvanceHinted', False):
                logger.info((
                  'V0693',
                  (),
                  "At least one glyph hints the advance, which is in "
                  "agreement with the state of 'head' flag bit 4."))
            
            else:
                logger.warning((
                  'V0696',
                  (),
                  "No glyph hints the advance, which is not in agreement "
                  "with the state of 'head' flag bit 4."))
        
        elif extraInfo.get('phantomAdvanceHinted', False):
            logger.warning((
              'V0694',
              (),
              "At least one glyph hints the advance, which is not in "
              "agreement with the state of 'head' flag bit 4."))
        
        else:
            logger.info((
              'V0695',
              (),
              "No glyph hints the advance, which is in agreement with "
              "the state of 'head' flag bit 4."))
        
        return (not failed)

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
