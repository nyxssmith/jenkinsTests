#
# context.py
#
# Copyright © 2007-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 7 (Contextual) subtables for a GPOS table. This module contains a
factory function for making the specific kind needed.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import contextclass, contextcoverage, contextglyph

# -----------------------------------------------------------------------------

#
# Factory function
#

def Context(w, **kwArgs):
    """
    Factory function for creating Context objects of the relevant kind from a
    walker whose format is not known in advance.
    """
    
    format = w.unpack("H", advance=False)
    
    if format == 1:
        return contextglyph.ContextGlyph.fromwalker(w, **kwArgs)
    elif format == 2:
        return contextclass.ContextClass.fromwalker(w, **kwArgs)
    elif format == 3:
        return contextcoverage.ContextCoverage.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown Context format: %d" % (format,))

def Context_fromValidatedFontWorkerSource(fws, **kwArgs):
    """
    Factory function for creating Context objects of the relevant kind from a
    FontWorkerSource whose format is not known in advance, with source
    validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("context")
    terminalStrings = ('subtable end', 'lookup end')
    startingLineNumber = fws.lineNumber
    classTokens = {'class definition begin', 'class definition end'}
    
    covTokens = {
      'coverage definition begin',
      'coverage',
      'coverage definition end'}

    for line in fws:
        if line in terminalStrings:
            break

        if len(line) > 0:
            tokens = [x.strip() for x in line.split('\t')]

            if tokens[0].lower().startswith('glyph'):
                fws.goto(startingLineNumber)
                
                return contextglyph.ContextGlyph.fromValidatedFontWorkerSource(
                    fws,
                    logger = logger,
                    **kwArgs)

            elif tokens[0].lower() in classTokens:
                fws.goto(startingLineNumber)
                
                return contextclass.ContextClass.fromValidatedFontWorkerSource(
                    fws,
                    logger = logger,
                    **kwArgs)

            elif tokens[0].lower() in covTokens:
                fws.goto(startingLineNumber)
                
                return contextcoverage.ContextCoverage.fromValidatedFontWorkerSource(
                    fws,
                    logger = logger,
                    **kwArgs)

            else:
                logger.error((
                  'V0960',
                  (fws.lineNumber, tokens[0]),
                  'line %d -- unexpected token: %s'))
                
                return None

    logger.error((
      'V0961',
      (fws.lineNumber,),
      'line %d -- reached end of lookup unexpectedly.'))
    
    return None

def Context_validated(w, **kwArgs):
    """
    Factory function for creating Context objects of the relevant kind, with
    source validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("context")
    
    logger.debug((
      'V0001',
      (w.length(),),
      "Walker has %d remaining bytes."))
    
    if w.length() < 2:
        logger.error(('V0004', (), "Insufficient bytes."))
        return None
    
    format = w.unpack("H", advance=False)
    
    if format not in {1, 2, 3}:
        logger.error((
          'V0398',
          (format,),
          "Unknown format %d for contextual table."))
        
        return None
    
    if format == 1:
        return contextglyph.ContextGlyph.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
    
    elif format == 2:
        return contextclass.ContextClass.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
    
    return contextcoverage.ContextCoverage.fromvalidatedwalker(
      w,
      logger = logger,
      **kwArgs)

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
    _test()
