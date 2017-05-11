#
# attachlist.py
#
# Copyright © 2005-2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions relating to lists of attachment points for all glyphs in GDEF
tables.
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.GDEF import attachpoint
from fontio3.opentype import coverage

# -----------------------------------------------------------------------------

#
# Private methods
#

def _pprint(p, obj, **kwArgs):
    if not obj:
        p.simple("No attachment data", **kwArgs)
        return
    
    nm = kwArgs.get('namer', obj.getNamer())
    
    if nm is not None:
        nf = nm.bestNameForGlyphIndex
        names = sorted((nf(i), i) for i in obj)
    
    else:
        names = [(str(i), i) for i in sorted(obj)]
    
    kwArgs.pop('label', None)
    
    for name, gi in names:
        p.simple(sorted(obj[gi]), label=name, **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class AttachListTable(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects containing attachment point indices for a set of glyphs.
    
    These are dictionaries whose keys are glyph indices and whose values are
    AttachPointTable objects.
    
    >>> alt = _testingValues[2]
    >>> alt.pprint(namer=namer.testingNamer())
    afii60003: [1, 4]
    xyz46: [3, 19, 20]
    
    >>> alt.pointsRenumbered({45: {19: 40}}).pprint(namer=namer.testingNamer())
    afii60003: [1, 4]
    xyz46: [3, 20, 40]
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_renumberdirectkeys = True,
        item_usenamerforstr = True,
        map_mergechecknooverlap = True,
        map_pprintfunc = _pprint)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data to the specified LinkedWriter.
        
        >>> utilities.hexdump(_testingValues[1].binaryString())
               0 | 000A 0003 0014 001C  001C 0001 0003 002D |...............-|
              10 | 0032 0062 0003 0003  0013 0014 0002 0001 |.2.b............|
              20 | 0004                                     |..              |
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        # Add content and unresolved references
        keys = sorted(self)
        covTable = coverage.Coverage(zip(keys, range(len(keys))))
        covStake = w.getNewStake()
        w.addUnresolvedOffset("H", stakeValue, covStake)
        w.add("H", len(keys))
        localPool = {}
        
        for key in keys:
            objID = id(self[key])
            
            if objID not in localPool:
                localPool[objID] = (self[key], w.getNewStake())
            
            w.addUnresolvedOffset("H", stakeValue, localPool[objID][1])
        
        # Resolve the references
        covTable.buildBinary(w, stakeValue=covStake, **kwArgs)
        
        for obj, stake in localPool.values():
            obj.buildBinary(w, stakeValue=stake, **kwArgs)
    
    @classmethod
    def fromValidatedFontWorkerSource(cls, fws, **kwArgs):
        """
        Returns a new AttachListTable object initialized from the specified
        FontWorker source code with extensive validation via the logging module
        (the client should have done a logging.basicConfig call prior to
        calling this method, unless a logger is passed in via the 'logger'
        keyword argument).

        >>> _test_FW_fws.goto(0) # go back to the start of the file
        >>> logger = utilities.makeDoctestLogger('test_FW.GDEF')
        >>> alt = AttachListTable.fromValidatedFontWorkerSource(_test_FW_fws, namer=_test_FW_namer, logger=logger)
        >>> alt.pprint()
        5: [42]
        7: [50, 55]
        11: [12, 17, 37]
        >>> alt2 = AttachListTable.fromValidatedFontWorkerSource(_test_FW_fws2, namer=_test_FW_namer, logger=logger)
        test_FW.GDEF.attachlist - WARNING - line 3 -- missing attachment points
        test_FW.GDEF.attachlist - WARNING - line 5 -- glyph 'z' not found
        test_FW.GDEF.attachlist - WARNING - line 0 -- did not find matching 'attachment list end'
        >>> alt2.pprint()
        5: [42]
        11: [12, 17, 37]
        """
        
        logger = kwArgs.pop('logger', None)

        if logger is None:
            logger = logging.getLogger().getChild('attachlist')
        else:
            logger = logger.getChild('attachlist')

        namer = kwArgs['namer']

        r = cls()

        terminalString = 'attachment list end'
        startingLineNumber = fws.lineNumber
        
        for line in fws:
            if line.lower() == terminalString:
                return r
            
            elif len(line) > 0:
                tokens = line.split('\t')
                
                if len(tokens) < 2:
                    logger.warning(('V0954',(fws.lineNumber),
                        'line %d -- missing attachment points'))
                    
                    continue
                
                glyphName = tokens[0]
                glyphIndex = namer.glyphIndexFromString(glyphName)
                attachmentPoints = [int(x) for x in tokens[1:]]

                if glyphIndex is not None:
                    r[glyphIndex] = attachpoint.AttachPointTable(
                        attachmentPoints)
                else:
                    logger.warning(('V0956', (fws.lineNumber, glyphName),
                        "line %d -- glyph '%s' not found"))

        logger.warning(('V0958', (startingLineNumber, terminalString),
            'line %d -- did not find matching \'%s\''))

        return r

    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), this method returns a new AttachListTable. However,
        it also does extensive validation via the logging module (the client
        should have done a logging.basicConfig call prior to calling this
        method, unless a logger is passed in via the 'logger' keyword
        argument).
        
        >>> logger = utilities.makeDoctestLogger('test.GDEF')
        >>> fvb = AttachListTable.fromvalidatedbytes
        >>> s = _testingValues[1].binaryString()
        >>> obj = fvb(s, logger=logger)
        test.GDEF.attachlist - DEBUG - Walker has 34 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Walker has 24 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Format is 1, count is 3
        test.GDEF.attachlist.coverage - DEBUG - Raw data are [45, 50, 98]
        test.GDEF.attachlist - INFO - Number of groups: 3.
        
        >>> fvb(s[:1], logger=logger)
        test.GDEF.attachlist - DEBUG - Walker has 1 remaining bytes.
        test.GDEF.attachlist - ERROR - Insufficient bytes.
        
        >>> fvb(s[:2], logger=logger)
        test.GDEF.attachlist - DEBUG - Walker has 2 remaining bytes.
        test.GDEF.attachlist.coverage - DEBUG - Walker has 0 remaining bytes.
        test.GDEF.attachlist.coverage - ERROR - Insufficient bytes.
        """
        
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            logger = logging.getLogger().getChild('attachlist')
        else:
            logger = logger.getChild('attachlist')
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        if w.length() < 2:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        covOffset = w.unpack("H")
        
        covTable = coverage.Coverage.fromvalidatedwalker(
          w.subWalker(covOffset),
          logger = logger,
          **kwArgs)
        
        if covTable is None:
            return None
        
        revTable = utilities.invertDictFull(covTable)
        localPool = {}
        fw = attachpoint.AttachPointTable.fromwalker
        
        if w.length() < 2:
            logger.error(('V0096', (), "Insufficient bytes for group count."))
            return None
        
        groupCount = w.unpack("H")
        logger.info(('V0097', (groupCount,), "Number of groups: %d."))
        
        if w.length() < 2 * groupCount:
            logger.error((
              'V0098',
              (),
              "Insufficient bytes for group offsets."))
            
            return None
        
        offsets = w.group("H", groupCount)
        r = cls()
        okToProceed = True
        
        for coverIndex, offset in enumerate(offsets):
            if offset:
                if offset not in localPool:
                    subLogger = logger.getChild("[%d]" % (coverIndex,))
                    obj = fw(w.subWalker(offset), logger=subLogger, **kwArgs)
                    
                    if obj is None:
                        okToProceed = False
                    
                    localPool[offset] = obj
                
                thisList = localPool[offset]
                
                if thisList is not None:
                    for glyphIndex in revTable.get(coverIndex, []):
                        r[glyphIndex] = thisList
        
        return (r if okToProceed else None)
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Returns a new AttachListTable object initialized from the specified
        walker.
        
        >>> alt = _testingValues[2]
        >>> alt == AttachListTable.frombytes(alt.binaryString())
        True
        """
        
        r = cls()
        covTable = coverage.Coverage.fromwalker(w.subWalker(w.unpack("H")))
        revTable = utilities.invertDictFull(covTable)
        localPool = {}
        fw = attachpoint.AttachPointTable.fromwalker
        
        for coverIndex, offset in enumerate(w.group("H", w.unpack("H"))):
            if offset:
                
                # Note: we cannot use setdefault in following, because the
                # argument is always evaluated!
                
                if offset not in localPool:
                    localPool[offset] = fw(w.subWalker(offset))
                
                thisList = localPool[offset]
                
                for glyphIndex in revTable.get(coverIndex, []):
                    r[glyphIndex] = thisList
        
        return r

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3.utilities import namer
    from io import StringIO
    from fontio3.opentype.fontworkersource import FontWorkerSource
    
    _aptv = attachpoint._testingValues
    
    _testingValues = (
        AttachListTable(),
        AttachListTable({45: _aptv[2], 50: _aptv[3], 98: _aptv[3]}),
        AttachListTable({45: _aptv[2], 98: _aptv[3]}))

    _test_FW_namer = namer.Namer(None)
    _test_FW_namer._nameToGlyph = {
        'a': 5,
        'b': 7,
        'c': 11
    }
    _test_FW_namer._initialized = True
    
    _test_FW_fws = FontWorkerSource(StringIO(
        """
        a\t42
        b\t50\t55
        c\t12\t17\t37
        Attachment list end
        """
    ))
    _test_FW_fws2 = FontWorkerSource(StringIO(
        """
        a\t42
        b
        c\t12\t17\t37
        z\t14\t16
        """
    ))


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
