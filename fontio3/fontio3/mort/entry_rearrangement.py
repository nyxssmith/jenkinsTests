#
# entry_rearrangement.py
#
# Copyright © 2011, 2012 Monotype Imaging Inc. All Rights Reserved.
#

"""
Definitions of a rearrangement action for a 'mort' rearrangement subtable.
"""

# Other imports
from fontio3.fontdata import simplemeta
from fontio3.mort import verbs_rearrangement

# -----------------------------------------------------------------------------

#
# Private constants
#

# The following is indexed by (markFirst, markLast, noAdvance, bool(verb))
_ppf_strings = {
  (False, False, False, False):
    "Go to state '%s'",
  
  (False, False, False, True):
    "Process the group via rule %s, then go to state '%s'",
  
  (False, False, True, False):
    "Go to state '%s' without advancing the glyph pointer",
  
  (False, False, True, True):
    "Process the group via rule %s, then go to state '%s' without "
    "advancing the glyph pointer",
  
  (False, True, False, False):
    "Mark end of grouping, then go to state '%s'",
  
  (False, True, False, True):
    "Mark end of grouping and process the group via rule %s, "
    "then go to state '%s'",
  
  (False, True, True, False):
    "Mark end of grouping, then go to state '%s' without advancing "
    "the glyph pointer",
  
  (False, True, True, True):
    "Mark end of grouping and process the group via rule %s, then go "
    "to state '%s' without advancing the glyph pointer",
  
  (True, False, False, False):
    "Mark start of grouping, then go to state '%s'",
  
  (True, False, False, True):
    "Mark start of grouping and process the group via rule %s, "
    "then go to state '%s'",
  
  (True, False, True, False):
    "Mark start of grouping, then go to state '%s' without advancing "
    "the glyph pointer",
  
  (True, False, True, True):
    "Mark start of grouping and process the group via rule %s, "
    "then go to state '%s' without advancing the glyph pointer",
  
  (True, True, False, False):
    "Mark both start and end of grouping, then go to state '%s'",
  
  (True, True, False, True):
    "Mark both start and end of grouping and process the group via rule %s, "
    "then go to state '%s'",
  
  (True, True, True, False):
    "Mark both start and end of grouping, then go to state '%s' without "
    "advancing the glyph pointer",
  
  (True, True, True, True):
    "Mark both start and end of grouping and process the group via rule %s, "
    "then go to state '%s' without advancing the glyph pointer"
  }

# -----------------------------------------------------------------------------

#
# Private functions
#

def _ppf(p, obj, **k):
    hasRule = bool(obj.verb)
    t = ((obj.verb, obj.newState) if hasRule else (obj.newState,))
    p(_ppf_strings[(obj.markFirst, obj.markLast, obj.noAdvance, hasRule)] % t)

# -----------------------------------------------------------------------------

#
# Classes
#

if 0:
    def __________________(): pass

class Entry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single entries in an entry table for a rearrangement
    subtable. These are the contents of a single cell in the state array.
    
    These are simple objects with the following attributes:
    
        markFirst       A Boolean which, if True, marks the current glyph as
                        being the start of a grouping. Default is False.
        
        markLast        A Boolean which, if True, marks the current glyph as
                        being the end of a grouping. Default is False.
        
        newState        A string representing the new state to go to after this
                        Entry is finished. Default is "Start of text".
        
        noAdvance       A Boolean which, if True, prevents the glyph pointer
                        from advancing to the next glyph after this Entry is
                        finished. Default is False.
        
        verb            A Verb object, representing the action to take place,
                        if any. Default is Verb(0) indicating no action.
    
    >>> _testingValues[0].pprint()
    Go to state 'Start of text'
    
    >>> _testingValues[1].pprint()
    Mark start of grouping, then go to state 'Saw thing'
    
    >>> _testingValues[2].pprint()
    Mark end of grouping and process the group via rule ABx => xAB, then go to state 'Start of text'
    """
    
    #
    # Class definition variables
    #
    
    attrSpec = dict(
        markFirst = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Mark start of grouping",
            attr_showonlyiftrue = True),
        
        markLast = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Mark end of grouping",
            attr_showonlyiftrue = True),
        
        newState = dict(
            attr_initfunc = (lambda: "Start of text"),
            attr_label = "Name of next state"),
        
        noAdvance = dict(
            attr_initfunc = (lambda: False),
            attr_label = "Don't advance to next glyph",
            attr_showonlyiftrue = True),
        
        verb = dict(
            attr_followsprotocol = True,
            attr_initfunc = (lambda: verbs_rearrangement.Verb(0)),
            attr_label = "Action"))
    
    objSpec = dict(
        obj_pprintfunc = _ppf)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    _testingValues = (
        Entry(),
        Entry(newState="Saw thing", markFirst=True),
        Entry(markLast=True, verb=verbs_rearrangement.Verb(4)))

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
