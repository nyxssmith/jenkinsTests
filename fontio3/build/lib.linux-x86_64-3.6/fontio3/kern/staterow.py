#
# staterow.py
#
# Copyright © 2011-2013 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'kern' state table.
"""

# System imports
import logging

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.kern import entry
from fontio3.statetables import classmap

# -----------------------------------------------------------------------------

#
# Private functions
#

def _pprint(p, d, **kwArgs):
    sigOnly = kwArgs.get('onlySignificant', False)
    vFixed = classmap.fixedNames
    sFixed = set(vFixed)
    kwArgs.pop('label', None)
    
    for s in vFixed:
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)
    
    for s in sorted(d):
        if s in sFixed:
            continue
        
        if (not sigOnly) or d[s].isSignificant():
            p.deep(d[s], label=("Class '%s'" % (s,)), **kwArgs)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows in the state array for a 'kern' table.
    These are dicts mapping class names to Entry objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        map_pprintfunc = _pprint)
    
    #
    # Methods
    #
    
    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the StateRow object to the specified walker.
        The following keyword arguments are used:
        
            classNameList           A sequence of the class names (including
                                    the fixed names). This is required.
            
            entryPool               A dict mapping immutable versions of the
                                    Entry objects to (index, object) pairs.
                                    This is required, as it is the sole means
                                    by which correlation between indices and
                                    Entry objects is made at
                                    Format1.buildBinary() time.
            
            stakeValue              A stake value representing the start of
                                    this chunk of binary data. This is
                                    optional.
        """
        
        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)
        else:
            stakeValue = w.stakeCurrent()
        
        entryPool = kwArgs['entryPool']
        
        for className in kwArgs['classNameList']:
            obj = self[className]
            immut = obj.asImmutable()
            
            if immut not in entryPool:
                entryPool[immut] = (len(entryPool), obj)
            
            w.add("B", entryPool[immut][0])
    
    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Creates and returns a new StateRow object from the specified walker,
        doing source validation. The following keyword arguments are used:
        
            classNames              A sequence of the class names (including
                                    the fixed names). This is required.
            
            entryPool               A dict mapping entryIndex values to the
                                    corresponding Entry object. This is
                                    optional.
        
            isCrossStream           True if the state table is cross-stream,
                                    False otherwise. It is not used directly,
                                    but is used in methods called from here.
                                    This is required.
            
            logger                  A logger to which messages will be posted.
            
            stateArrayBaseOffset    Byte offset from the start of the state
                                    table to the start of the state array. It
                                    is not used directly, but is used in
                                    methods called from here. This is required.
            
            stateNames              A sequence of the state names (including
                                    the fixed names). This is required.
            
            valueTuplePool          A dict mapping ValueOffsets (as present in
                                    the binary data) to ValueTuples. It is not
                                    used directly, but is used in methods
                                    called from here. This is optional.
            
            wEntryTable             A walker whose base is the start of the
                                    entry table. This is required.
            
            wSubtable               A walker whose base address is the start of
                                    the entire state table. It is not used
                                    directly, but is used in methods called
                                    from here. This is required.
        """
        
        logger = kwArgs.pop('logger', logging.getLogger())
        logger = logger.getChild("staterow")
        
        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))
        
        names = kwArgs['classNames']
        kwArgs['numClasses'] = numClasses = len(names)
        
        if w.length() < numClasses:
            logger.error(('V0004', (), "Insufficient bytes."))
            return None
        
        data = w.group("B", numClasses)
        
        r = cls()
        wEntryTable = kwArgs['wEntryTable']
        fvw = entry.Entry.fromvalidatedwalker
        entryPool = kwArgs.get('entryPool', {})
        
        for colIndex, entryIndex in enumerate(data):
            if entryIndex not in entryPool:
                # The '4' below is for 4 bytes per entry for 'kern'
                wSub = wEntryTable.subWalker(4 * entryIndex)
                itemLogger = logger.getChild("class %d" % (colIndex,))
                obj = fvw(wSub, logger=itemLogger, **kwArgs)
                
                if obj is None:
                    return None
                
                entryPool[entryIndex] = obj
            
            r[names[colIndex]] = entryPool[entryIndex]
        
        return r
    
    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new StateRow object from the specified walker.
        The following keyword arguments are used:
        
            classNames              A sequence of the class names (including
                                    the fixed names). This is required.
            
            entryPool               A dict mapping entryIndex values to the
                                    corresponding Entry object. This is
                                    optional.
        
            isCrossStream           True if the state table is cross-stream,
                                    False otherwise. It is not used directly,
                                    but is used in methods called from here.
                                    This is required.
            
            stateArrayBaseOffset    Byte offset from the start of the state
                                    table to the start of the state array. It
                                    is not used directly, but is used in
                                    methods called from here. This is required.
            
            stateNames              A sequence of the state names (including
                                    the fixed names). This is required.
            
            valueTuplePool          A dict mapping ValueOffsets (as present in
                                    the binary data) to ValueTuples. It is not
                                    used directly, but is used in methods
                                    called from here. This is optional.
            
            wEntryTable             A walker whose base is the start of the
                                    entry table. This is required.
            
            wSubtable               A walker whose base address is the start of
                                    the entire state table. It is not used
                                    directly, but is used in methods called
                                    from here. This is required.
        """
        
        r = cls()
        wEntryTable = kwArgs['wEntryTable']
        fw = entry.Entry.fromwalker
        names = kwArgs['classNames']
        entryPool = kwArgs.get('entryPool', {})
        kwArgs['numClasses'] = numClasses = len(names)
        
        for colIndex, entryIndex in enumerate(w.group("B", numClasses)):
            if entryIndex not in entryPool:
                # The '4' below is for 4 bytes per entry for 'kern'
                wSub = wEntryTable.subWalker(4 * entryIndex)
                entryPool[entryIndex] = fw(wSub, **kwArgs)
            
            r[names[colIndex]] = entryPool[entryIndex]
        
        return r

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
