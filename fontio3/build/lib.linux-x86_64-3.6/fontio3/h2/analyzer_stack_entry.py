#
# analyzer_stack_entry.py
#
# Copyright © 2015 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for a single stack entry as used in the analysis code.
"""

# Other imports
from fontio3.fontdata import simplemeta

# -----------------------------------------------------------------------------

#
# Classes
#

class AnalyzerStackEntry(object, metaclass=simplemeta.FontDataMetaclass):
    """
    Objects representing single stack values used by the new analysis code.
    These are simple collections of the following attributes (ordered as shown):
    
        value           The actual stack value.
        
        inOut           The string 'in' or 'out'. The 'in' string will only be
                        present on values that were pushed before the start of
                        code (to provide a non-empty stack for things like
                        FDEFs).
        
        itemStamp       A unique numerical stamp identifying this stack entry
                        and distinguishing it from all others.
        
        relStackIndex   The relative stack index of the item when it was
                        originally pushed. 0 is top-of-stack.
        
        kind            A string indicating what kind of value it is. This will
                        be something like 'pointIndex', 'cvtIndex', etc.
        
        wherePushed     Information on where this value was initially pushed.
                        This will be None for the pre-execution pushes.
    
    >>> AnalyzerStackEntry(12, 'in', 992, 3, 'cvtIndex', ('FDEF 14', 12)).pprint()
    (12, 'in', 3, 'cvtIndex', ('FDEF 14', 12))
    
    Note the custom __str__() methods does not show the itemStamp field.
    """
    
    objSpec = dict(
        obj_pprintfunc = (lambda p, x, **k: p.simple(str(x), **k)))
    
    attrSpec = dict(
        value = dict(),
        inOut = dict(),
        itemStamp = dict(),
        relStackIndex = dict(),
        kind = dict(),
        wherePushed = dict(
          attr_wisdom = "If None, synthetic; else, (infostring, pc)"))
    
    attrSorted = (
      'value',
      'inOut',
      'itemStamp',
      'relStackIndex',
      'kind',
      'wherePushed')
    
    #
    # Methods
    #
    
    def __str__(self):
        return str((
          self.value,
          self.inOut,
          self.relStackIndex,
          self.kind,
          self.wherePushed))

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

