#
# chain.py
#
# Copyright © 2007-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
LookupType 8 (Chaining contextual) subtables for a GPOS table.
"""

# System imports
import logging

# Other imports
from fontio3.GPOS import chainclass, chaincoverage, chainglyph

# -----------------------------------------------------------------------------

#
# Factory function
#

def Chain(w, **kwArgs):
    """
    Factory function for creating Chain objects of the relevant kind from a
    walker whose format is not known in advance.
    """
    
    format = w.unpack("H", advance=False)
    
    if format == 1:
        return chainglyph.ChainGlyph.fromwalker(w, **kwArgs)
    elif format == 2:
        return chainclass.ChainClass.fromwalker(w, **kwArgs)
    elif format == 3:
        return chaincoverage.ChainCoverage.fromwalker(w, **kwArgs)
    
    raise ValueError("Unknown Chain format: %d" % (format,))

def Chain_fromValidatedFontWorkerSource(fws, **kwArgs):
    """
    Factory function for creating Chain objects of the relevant kind from a
    FontWorkerSource whose format is not known in advance, with source
    validation.
    """
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("chaining")
    terminalStrings = ('subtable end', 'lookup end')
    startingLineNumber = fws.lineNumber

    for line in fws:
        if line in terminalStrings:
            break

        if len(line) > 0:
            tokens = [x.strip() for x in line.split('\t')]

            if tokens[0].lower() == 'glyph':
                fws.goto(startingLineNumber)
                r = chainglyph.ChainGlyph.fromValidatedFontWorkerSource(
                    fws, logger=logger, **kwArgs)
                return r

            elif tokens[0].lower() in ['backtrackclass definition begin',
                               'class definition begin',
                               'lookaheadclass definition begin',
                               'class-chain', 'class definition end']:
                fws.goto(startingLineNumber)
                r = chainclass.ChainClass.fromValidatedFontWorkerSource(
                    fws, logger=logger, **kwArgs)
                return r

            elif tokens[0].lower() in ['backtrackcoverage definition begin',
                               'inputcoverage definition begin',
                               'lookaheadcoverage definition begin', 'coverage',
                               'coverage definition end']:
                fws.goto(startingLineNumber)
                r = chaincoverage.ChainCoverage.fromValidatedFontWorkerSource(
                    fws, logger=logger, **kwArgs)
                return r

            else:
                logger.warning(('V0960',
                    (fws.lineNumber, tokens[0]),
                    'line %d -- unexpected token: %s'))

    logger.warning(('V0961',
        (fws.lineNumber,),
        'line %d -- reached end of lookup unexpectedly'))

    return None

def Chain_validated(w, **kwArgs):
    """
    Factory function for creating Chain objects of the relevant kind, with
    source validation.
    """
    
    logger = kwArgs.pop('logger', logging.getLogger())
    logger = logger.getChild("chaining")
    
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
          'V0399',
          (format,),
          "Unknown format %d for chaining contextual table."))
        
        return None
    
    if format == 1:
        return chainglyph.ChainGlyph.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
    
    elif format == 2:
        return chainclass.ChainClass.fromvalidatedwalker(
          w,
          logger = logger,
          **kwArgs)
    
    return chaincoverage.ChainCoverage.fromvalidatedwalker(
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
