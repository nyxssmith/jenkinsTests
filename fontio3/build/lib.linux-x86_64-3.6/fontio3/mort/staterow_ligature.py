#
# staterow_ligature.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for single states in a 'mort' ligature subtable.
"""

# Other imports
from fontio3 import utilities
from fontio3.fontdata import mapmeta
from fontio3.mort import glyphtupledict

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, label, **k):
    okToPrint = (
      obj.newState != "Start of text" or
      obj.push or
      obj.noAdvance or
      obj.actions)
    
    if okToPrint:
        p.deep(obj, label=label, **k)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class StateRow(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing single rows in the state array for a 'mort' table.
    These are dicts mapping class names to Entry objects.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintfunc = _ppf,
        item_pprintlabelfunc = (lambda k: "Class '%s'" % (k,)))
    
    #
    # Public methods
    #
    
    def combinedActions(self):
        """
        Returns a new StateRow object where any cells whose flags and nextState
        values are the same and whose keys are identical except for the last
        glyph have their actions combined into a unified dict. This can reduce
        the total number of entries required, which for a 'mort' table can be
        very useful since the limit is 8 bits.
        """
        
        pool = {}  # (newState, push, noAdv, key[:-1]) -> ({classNames}, gtd)
        
        for className, cell in self.items():
            a = cell.actions
            
            if a:
                
                # First we have to check that all keys are the same up to but
                # not including the last glyph index. We can't coalesce if this
                # is not the case!
                
                firsts = {k[:-1] for k in a}
                
                if len(firsts) != 1:
                    continue
                
                # Now see if we've already added an entry for this set of items
                # to the pool, and if not, do so.
                
                t = (cell.newState, cell.push, cell.noAdvance, firsts.pop())
                
                if t not in pool:
                    pool[t] = (set(), glyphtupledict.GlyphTupleDict())
                
                pool[t][0].add(className)
                pool[t][1].update(a)
        
        # Now that we have the pooled entries, go through and construct the
        # combined object (that will be returned).
        
        r = self.__deepcopy__()
        
        for classNames, gtd in pool.values():
            for className in classNames:
                r[className].actions = gtd
        
        return r
    
    def trimmedToValidEntries(self, classTable):
        """
        For each cell, call that cell's trimmedToValidEntries method with the
        set of glyphs matching the class name for the cell. If any returned
        result is different from the original StateRow, return a new StateRow
        with those changes; otherwise, return self.
        """
        
        dNew = type(self)()
        sawChanges = False
        revMap = utilities.invertDictFull(classTable, asSets=True)
        
        for className, cell in self.items():
            origActions = cell.actions.__copy__()
            newCell = cell.trimmedToValidEntries(revMap.get(className, set()))
            
            if newCell.actions != origActions:
                sawChanges = True
                dNew[className] = newCell
            
            else:
                dNew[className] = cell
        
        if sawChanges:
            return dNew
        
        return self

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
