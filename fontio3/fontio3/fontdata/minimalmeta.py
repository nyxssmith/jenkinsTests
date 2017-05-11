#
# minimalmeta.py -- Support for empty, placeholder protocol objects with
#                   their own descriptive strings. No attributes are supported;
#                   if you want attributes, use simplemeta.py.
#
# Copyright © 2010-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for Protocol classes that are totally empty except for an identifying
string. These are useful when you need a unique object that should know (and
mostly ignore) the standard protocol, but that has no behavior of its own. For
an example of this, see :py:mod:`fontio3.statetables.action_reprocess_current`.

Note that attributes are not supported by this metaclass; if you need them, use
``simplemeta`` instead.

``minSpec``
    A dict of specification information for the minimal value, where the keys
    and their associated values are defined in the following list.

    ``minimal_string``
        A string associated with this minimal object. It will be
        used for ``str()``, ``repr()``, ``pprint()``, etc.
        
        There is no default; must be specified
"""

# Other imports
from fontio3.fontdata import invariants
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Constants
#

validMinimalSpecKeys = frozenset([
  'minimal_string'])

# -----------------------------------------------------------------------------

#
# Methods
#

def M_asImmutable(self, **kwArgs):
    """
    Returns an immutable version of the object. This is just the string.
    
    >>> _testingClass().asImmutable()
    'ABC'
    """
    
    return self._MINSPEC['minimal_string']

def M_checkInput(self, valueToCheck, **kwArgs):
    """
    Returns True
    """
    
    return True

def M_coalesced(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.coalesced()
    True
    """
    
    return self

def M_compacted(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.compacted()
    True
    """
    
    return self

def M_converted(self, **kwArgs):
    """
    Returns an empty list if ``returnTokens`` is specified, or else None if
    ``useToken`` is specified.
    """
    
    if kwArgs.get('returnTokens', True):
        return []
    
    return None

def M_cvtsRenumbered(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.cvtsRenumbered()
    True
    """
    
    return self

def M_fdefsRenumbered(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.fdefsRenumbered()
    True
    """
    
    return self

def M_gatheredInputGlyphs(self, **kwArgs):
    """
    Returns an empty set.
    
    >>> _testingClass().gatheredInputGlyphs()
    set()
    """
    
    return set()

def M_gatheredLivingDeltas(self, **kwArgs):
    """
    Returns an empty set.
    
    >>> _testingClass().gatheredLivingDeltas()
    set()
    """
    
    return set()

def M_gatheredMaxContext(self, **kwArgs):
    """
    Returns zero.
    
    >>> _testingClass().gatheredMaxContext()
    0
    """
    
    return 0

def M_gatheredOutputGlyphs(self, **kwArgs):
    """
    Returns an empty set.
    
    >>> _testingClass().gatheredOutputGlyphs()
    set()
    """
    
    return set()

def M_gatheredRefs(self, **kwArgs):
    """
    Returns an empty dict.
    
    >>> _testingClass().gatheredRefs()
    {}
    """
    
    return {}

def M_glyphsRenumbered(self, oldToNew, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.glyphsRenumbered({})
    True
    """
    
    return self

def M_hasCycles(self, **kwArgs):
    """
    Returns False.
    """
    
    return False

def M_isValid(self, **kwArgs):
    """
    Returns True.
    
    >>> _testingClass().isValid()
    True
    """
    
    return True

def M_merged(self, other, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj2 = _testingClass()
    >>> obj1 == obj1.merged(obj2)
    True
    """
    
    return self

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.namesRenumbered({})
    True
    """
    
    return self

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.pcsRenumbered({})
    True
    """
    
    return self

def M_pointsRenumbered(self, mapData, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.pointsRenumbered({})
    True
    """
    
    return self

def M_pprint(self, **kwArgs):
    """
    Pretty-prints the object.
    
    >>> _testingClass().pprint(label="The minimal string")
    The minimal string:
      ABC
    
    >>> _testingClass().pprint(label="The minimal string", useRepr=True)
    The minimal string:
      'ABC'
    """
    
    s = self._MINSPEC['minimal_string']
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    p.simple(s, **kwArgs)

def M_pprintChanges(self, prior, **kwArgs):
    """
    Does nothing.
    """
    
    pass

def M_recalculated(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.recalculated()
    True
    """
    
    return self

def M_scaled(self, scaleFactor, **kwArgs):
    """
    Return self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.scaled(0.5)
    True
    """
    
    return self

def M_storageRenumbered(self, **kwArgs):
    """
    Returns self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.storageRenumbered()
    True
    """
    
    return self

def M_transformed(self, matrixObj, **kwArgs):
    """
    Return self.
    
    >>> obj1 = _testingClass()
    >>> obj1 == obj1.transformed(None)
    True
    """
    
    return self

def SM_copy(self):
    """
    Returns a shallow copy.
    
    >>> obj1 = _testingClass()
    >>> obj2 = obj1.__copy__()
    >>> print(obj1, obj2)
    ABC ABC
    >>> obj1 is obj2
    False
    """
    
    return type(self)()

def SM_deepcopy(self):
    """
    Returns a deep copy (which for minimal objects is the same as a shallow
    copy).
    
    >>> obj1 = _testingClass()
    >>> obj2 = obj1.__deepcopy__()
    >>> print(obj1, obj2)
    ABC ABC
    >>> obj1 is obj2
    False
    """
    
    return type(self)()

def SM_eq(self, other):
    """
    Compares the strings and returns True if they're equal. The other object
    may be either of the same type as self, or a plain string.
    
    >>> obj1 = _testingClass()
    >>> obj2 = _testingClass()
    >>> obj1 == obj2
    True
    >>> obj1 == 'ABC'
    True
    >>> obj1 == "Fred"
    False
    """
    
    selfString = self._MINSPEC['minimal_string']
    
    try:
        otherString = other._MINSPEC['minimal_string']
    except AttributeError:
        otherString = other
    
    return selfString == otherString

def SM_repr(self):
    """
    Returns the repr of the string.
    
    >>> print(repr(_testingClass()))
    'ABC'
    """
    
    return repr(self._MINSPEC['minimal_string'])

def SM_str(self):
    """
    Returns the string.
    
    >>> print(str(_testingClass()))
    ABC
    """
    
    return self._MINSPEC['minimal_string']

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__eq__': SM_eq,
    '__repr__': SM_repr,
    '__str__': SM_str,
    'asImmutable': M_asImmutable,
    'checkInput': M_checkInput,
    'coalesced': M_coalesced,
    'compacted': M_compacted,
    'converted': M_converted,
    'cvtsRenumbered': M_cvtsRenumbered,
    'fdefsRenumbered': M_fdefsRenumbered,
    'gatheredInputGlyphs': M_gatheredInputGlyphs,
    'gatheredLivingDeltas': M_gatheredLivingDeltas,
    'gatheredMaxContext': M_gatheredMaxContext,
    'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
    'gatheredRefs': M_gatheredRefs,
    'getSortedAttrNames': classmethod(lambda x: ()),
    'glyphsRenumbered': M_glyphsRenumbered,
    'hasCycles': M_hasCycles,
    'isValid': M_isValid,
    'merged': M_merged,
    'namesRenumbered': M_namesRenumbered,
    'pcsRenumbered': M_pcsRenumbered,
    'pointsRenumbered': M_pointsRenumbered,
    'pprint': M_pprint,
    'pprint_changes': M_pprintChanges,
    'recalculated': M_recalculated,
    'scaled': M_scaled,
    'storageRenumbered': M_storageRenumbered,
    'transformed': M_transformed
    }

def _addMethods(cd):
    for mKey, m in _methodDict.items():
        if mKey not in cd:
            cd[mKey] = m

def _validateMinSpec(d):
    """
    Make sure only known keys are included in the minSpec. (Checks like
    this are only possible in a metaclass, which is another reason to use them
    over traditional subclassing)
    
    >>> d = {'minimal_string': "a string"}
    >>> _validateMinSpec(d)
    >>> d = {'minimal_strinf': "a string"}
    >>> _validateMinSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown minSpec keys: ['minimal_strinf']
    """
    
    unknownKeys = set(d) - validMinimalSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown minSpec keys: %s" % (sorted(unknownKeys),))

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for minimal classes.
    
    >>> class MyClass(object, metaclass=FontDataMetaclass):
    ...     minSpec = dict(minimal_string = "My string")
    >>> print(MyClass())
    My string
    """
    
    def __new__(mcl, classname, bases, classdict):
        d = classdict['_MINSPEC'] = classdict.pop('minSpec', {})
        classdict['_MAIN_SPEC'] = d
        _validateMinSpec(d)
        _addMethods(classdict)
        invariants.addInvariantMethods(classdict)
        return super(FontDataMetaclass, mcl).__new__(mcl, classname, bases, classdict)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    class _testingClass(object, metaclass=FontDataMetaclass):
        minSpec = dict(minimal_string = "ABC")

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
