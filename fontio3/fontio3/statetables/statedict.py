#
# statedict.py
#
# Copyright © 2010, 2011 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for entire state tables (here referred to as state dicts).
"""

# System imports
import functools
import itertools

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.statetables import classmap

# -----------------------------------------------------------------------------

#
# Classes
#

class StateDict(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects representing entire state tables. These are dicts whose keys are
    state names and whose values are State objects. There is one attribute:
    
        classMap    A defaultdict mapping glyph indices to class names. Glyphs
                    not present always map to the "Out of bounds" class.
    """
    
    #
    # Class definition variables
    #
    
    mapSpec = dict(
        item_followsprotocol = True,
        item_pprintlabelfunc = (lambda s: "State %r" % (s,)))
    
    attrSpec = dict(
        classMap = dict(
            attr_followsprotocol = True,
            attr_initfunc = classmap.ClassMap))
    
    #
    # Public methods
    #
    
    def iteractions(self):
        """
        Returns an iterator over all actions present in the entire StateDict.
        """
        
        return itertools.chain.from_iterable(obj.iteractions() for obj in self.values())
    
    def marksUsed(self):
        """
        Returns a set of all marks used in the action (or the empty set, if no
        marks are used. Note this refers to marks referenced, not defined.
        """
        
        return functools.reduce(set.union, (obj.marksUsed() for obj in self.values()))
    
    def removeUnusedPushes(self):
        """
        Often, glyphs are pushed onto the stack as a convenience but are never
        actually moved. This can clutter up the resulting StateDict. This
        method will find all cases where a mark is pushed but never used, and
        will remove the mark action in these cases.
        """
        
        used = self.marksUsed()
        
        for stateObj in self.values():
            for cellObj in stateObj.values():
                if cellObj.actions:
                    toDel = []
                    
                    for i, actionObj in enumerate(cellObj.actions):
                        if actionObj.kind == "mark_current" and actionObj.markLabel not in used:
                            toDel.append(i)
                    
                    for i in reversed(toDel):
                        del cellObj.actions[i]

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
