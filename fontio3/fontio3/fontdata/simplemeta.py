#
# simplemeta.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for simple fontdata objects, which are collections of attributes.
Clients wishing to add fontdata capabilities to their object-derived classes
should specify FontDataMetaclass as the metaclass. The following class
attributes are used to control the various behaviors and attributes of
instances of the class:
    
``attrSpec``
    See attrhelper.py for this documentation.

``attrSorted``
    See attrhelper.py for this documentation.

``objSpec``
    A dict of specification information for the object as a whole, where the
    keys and their associated values are defined in the following list. The
    listed defaults apply if the specified key is not present in objSpec.

    If an ``objSpec`` is not provided an empty one will be used, and all
    defaults listed below will be in force.
    
    ``obj_boolfalseiffalseset``
        If not specified then the normal ``bool()`` logic holds: if any of the
        attributes is True then the whole object is True.
    
        If specified, it should be a set of attribute names. The ``bool()`` for
        the whole object will be False if any of the specified attributes are
        False. If all the attributes are True, the object is True.
        
        There is no default.
    
    ``obj_enableordering``
        If True then objects of the class are ordered seriatim via their
        attributes. The ``attrSorted`` list is used to determine the major
        ordering.
    
        In practical terms, setting this True adds ``__lt__()``, ``__le__()``,
        ``__gt__()``, and ``__ge__()``  methods to the class.
        
        Default is False.
    
    ``obj_pprintfunc``
        If specified, a function taking two positional arguments (the ``pp.PP``
        object and the object in question), and optional keyword arguments.
        
        There is no default.
    
    ``obj_pprintfunc_partial``
        If specified, a function taking two positional arguments (the ``pp.PP``
        object and the object in question) and optional keyword arguments. It
        performs custom printing that would not be done in the regular
        ``pprint()`` logic -- for instance, class constants that should be
        annotated in ``pprint()`` output can be done here. Once this function
        is finished, the regular ``pprint()`` call will then be made. For an
        example of how is is useful, see the ``ADFH`` object.
        
        There is no default.
    
    ``obj_recalculatefunc_partial``
        A function taking one positional argument, the whole object, and
        optional additional keyword arguments. The function returns a pair: the
        first element will be True if the recalculated object differs from the
        original object; and the second will be the recalculated object.
    
        This function may only recalculate some fields, and may leave the
        recalculation of others to their respective attr_recalculatefuncs.
    
        Note that there is no ``obj_recalculatefunc``. If a client wishes to do
        this, they can just provide their own ``recalculated()`` method.
        
        There is no default.
    
    ``obj_validatefunc_partial``
        A function taking one positional argument, the whole object, and
        optional additional keyword arguments. The function returns True if the
        object is valid, and False otherwise. Any ``attr_validatefuncs`` will
        also be run to determine the returned True/False value, so this
        function should focus on overall sequence validity, or validating
        groups of attributes where setup is expensive and you'd rather not
        duplicate it per attribute. See ``Maxp`` objects for an example of this.
    
        Note that there is no ``obj_validatefunc``. If a client wishes to do
        this, they can just provide their own ``isValid()``.
        
        There is no default.
    
    ``obj_wisdom``
        A string encompassing a sensible description of the object as a whole,
        including how it is used.
        
        There is no default for wisdom, alas...
"""

# System imports
import logging
import operator

# Other imports
from fontio3.fontdata import attrhelper, invariants
from fontio3.utilities import pp

# -----------------------------------------------------------------------------

#
# Constants
#

validObjSpecKeys = frozenset([
  'obj_boolfalseiffalseset',
  'obj_enableordering',
  'obj_pprintfunc',
  'obj_pprintfunc_partial',
  'obj_recalculatefunc_partial',
  'obj_validatefunc_partial',
  'obj_wisdom'])

# -----------------------------------------------------------------------------

#
# Methods
#

def M_asImmutable(self, **kwArgs):
    """
    Returns a simple tuple with the object's contents, suitable for use as
    a dict key or in a set.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: The immutable version (or self, if it's already immutable).
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id(...)`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
        
        This is optional; if one is not provided, a temporary one will be used.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> print(Top(n=35, pair=Bottom(first=20, second=35)).asImmutable())
    ('Top', ('pair', ('Bottom', ('first', 20), ('second', 35))), ('n', 35))
    
    >>> class Test1(list):
    ...     def asImmutable(self, **kwArgs):
    ...         return tuple(self)
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    >>> Test2(x=Test1([1, 3, 5]), y=Test1([7])).asImmutable()
    ('Test2', ('x', (1, 3, 5)), ('y', (7,)))
    
    >>> Test2(x=Test1([1]), y=Test1([7])).asImmutable()
    ('Test2', ('x', (1,)), ('y', (7,)))
    
    >>> Test2(x=1, y=Test1([7])).asImmutable()
    ('Test2', ('x', (1,)), ('y', (7,)))
    
    >>> Test2(x=1, y=7).asImmutable()
    Traceback (most recent call last):
      ...
    AttributeError: 'int' object has no attribute 'asImmutable'
    """
    
    if 'memo' not in kwArgs:
        kwArgs['memo'] = {}
    
    return (type(self).__name__,) + attrhelper.M_asImmutable(
      self._ATTRSPEC,
      self._ATTRSORT,
      self.__dict__,
      **kwArgs)

def M_checkInput(self, valueToCheck, **kwArgs):
    """
    Check appropriateness of a value for self.
 
    :param valueToCheck: The value to be checked
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if appropriate, False otherwise
    :rtype: bool
    
    This method is used to check the appropriateness of a value for the given
    kind of object. So for example, if an ``'OS/2'`` weight-class value is
    supposed to be a number from 1 to 1000, this method's implementation for
    that object will check that specifically.
    
    The following ``kwArgs`` are supported:
    
    ``attrName``
         An optional string, identifying an attribute of the object. If
         specified, this attribute's own ``checkInput()`` method will be called
         with the ``valueToCheck`` value. Otherwise, this object's checking
         function will be used.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...   attrSpec = dict(
    ...     a = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: x in {'a', 'e', '*'})),
    ...     b = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: 0 <= x < 64)))
    >>> x = Test1(a='e', b=19)
    >>> x.checkInput('a', attrName='a')
    True
    >>> x.checkInput('z', attrName='a')
    False
    >>> x.checkInput(50, attrName='b')
    True
    >>> x.checkInput(150, attrName='b')
    False
    """
    
    return attrhelper.M_checkInput(
      self._ATTRSPEC,
      self.__dict__,
      valueToCheck,
      **kwArgs)

def M_coalesced(self, **kwArgs):
    """
    Return new object representing self with duplicates coerced to the
    same object.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``

    Font data often comprises multiple parts that happen to be the same. One
    example here is the platform 0 (Unicode) and platform 3 (Microsoft)
    ``cmap`` subtables, which often have exactly the same data. The binary
    format for the ``cmap`` table permits sharing here (each table is actually
    an offset, so the two offsets here can refer to the same data). This method
    is used to force this sharing to occur, if possible.

    It's important to remember that fontio3 deals with high-level, more abstract
    representations of font data. In order to allow for both the sharing and
    non-sharing cases, this method uses the object ID (that is, the results of
    calling the built-in ``id()`` function) as a clue. If two objects contained
    in some container object share the same ID, then they'll be shared in the
    binary representation.

    Knowing this, it's now easy to see what this method does. It compares any
    protocol objects it contains, and if it finds some that compare equal but
    have different IDs, it "coalesces" them to refer to the same ID. This will
    then ensure shared references to the same data in the binary data, once
    it is written.
    
    In the returned result, if two objects are equal then they
    will be the same object (i.e. an ``is`` test will return True).

    The following ``kwArgs`` are supported:

    ``pool``
        A dict mapping immutable representations of objects to the objects
        themselves. This is optional; a new, empty dict will be used if one is
        not specified.
    
        This is useful if you want to coalesce objects across many higher-level
        objects.

    ``separateAttributesPool``
        If False (the default), then the same pool will be used for both
        non-attribute members (e.g. sequence values) and attribute members of
        self. If True, the pool will be cleared before attributes are
        coalesced.
    
    >>> class Bottom(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_asimmutablefunc': tuple}
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'v': {'attr_followsprotocol': True}}
    >>> v1 = [1, 2, 3]
    >>> v2 = [1, 2, 3]
    >>> b = Bottom([v1, v2])
    >>> t = Test(v=b)
    >>> t.v[0] == t.v[1], t.v[0] is t.v[1]
    (True, False)
    >>> tc = t.coalesced()
    >>> tc.v[0] == tc.v[1], tc.v[0] is tc.v[1]
    (True, True)
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> obj1 = Test2(x=Test1([1]), y=Test1([1]))
    >>> obj1.x is obj1.y
    False
    >>> obj1C = obj1.coalesced()
    >>> obj1C.x is obj1C.y
    True
    >>> obj2 = Test2(x=1, y=Test1([1]))
    >>> obj2C = obj2.coalesced()
    >>> print(obj2C)  # note that x is now a Test1 object, not an integer
    x = [1], y = [1]
    >>> obj2C.x is obj2C.y
    True
    """
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    
    dNew = attrhelper.M_coalesced(
      self._ATTRSPEC,
      self.__dict__,
      pool,
      **kwArgs)
    
    r = type(self)(**dNew)
    cwc[id(self)] = r
    return r

def M_compacted(self, **kwArgs):
    """
    Return new object representing self with meaningless entries excised.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``

    Suppose you have a fontio3 object that is a list of shift values in FUnits.
    If you need to make sure that only non-trivial values remain in the list,
    use this method. It will remove anything whose boolean value is False.

    No user-visible ``kwArgs`` values are defined for this method.
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_compactremovesfalses = True)
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(x = dict(attr_followsprotocol = True))
    >>> b = Bottom([3, 0, None, False, [], {}, '', 4])
    >>> t = Top(x=b)
    >>> print(t)
    x = (3, 0, None, False, [], {}, '', 4)
    >>> print(t.compacted())
    x = (3, 4)
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_compactremovesfalses': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> print(Test2(x=1, y=Test1([1])).compacted())
    x = [1], y = [1]
    
    >>> print(Test2(x=0, y=Test1([1])).compacted())
    x = [], y = [1]
    """
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    r = type(self)(**dNew)
    cwc[id(self)] = r
    return r

def M_cvtsRenumbered(self, **kwArgs):
    """
    Return new object with CVT index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with CVT indices renumbered
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``

    CVT indices are used in TrueType hinting, and can appear in several
    different tables. If you are merging fonts together, you might want to
    renumber the CVTs in the various input fonts so they don't collide. This
    method helps you do that.

    The following ``kwArgs`` are supported:

    ``cvtDelta``
        An optional integer value (possibly negative) that will be added to the
        old CVT index to obtain the new one.

    ``cvtMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the CVT index), and should allow for arbitrary
        keyword arguments. It returns the new CVT index.

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with None.

    ``oldToNew``
        A dict mapping old CVT indices to new ones. Note that it's OK for this
        dict to not map every single old CVT index; what happens if this occurs
        is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``cvtDelta``, ``cvtMappingFunc``, or
      ``oldToNew``.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_renumbercvtsdirect = True))
    
    >>> print(Test1(x=25).cvtsRenumbered(cvtDelta=300))
    x = 325
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> print(Test1(x=25).cvtsRenumbered(oldToNew=d))
    x = 1025
    >>> print(Test1(x=29).cvtsRenumbered(oldToNew=d))
    x = 29
    >>> print(Test1(x=29).cvtsRenumbered(oldToNew=d, keepMissing=False))
    x = None
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1(x=10).cvtsRenumbered(cvtMappingFunc=f))
    x = 910
    >>> print(Test1(x=11).cvtsRenumbered(cvtMappingFunc=f))
    x = 11
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         deep = dict(
    ...             attr_followsprotocol=True,
    ...             attr_strneedsparens=True))
    
    >>> print(Test2(deep=Test1(x=25)).cvtsRenumbered(cvtDelta=400))
    deep = (x = 425)
    """
    
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    return type(self)(**dNew)

def M_fdefsRenumbered(self, **kwArgs):
    """
    Return new object with FDEF index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with FDEF indices renumbered
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``

    FDEF (Function DEFinition) indices are used in TrueType hinting, and can
    appear in several different tables. If you are merging fonts together, you
    might want to renumber the FDEFs in the various input fonts so they don't
    collide. This method helps you do that.

    The following ``kwArgs`` are supported:

    ``fdefMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the FDEF index), and should allow for arbitrary
        keyword arguments. It returns the new FDEF index.

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with None.

    ``oldToNew``
        A dict mapping old FDEF indices to new ones. Note that it's OK for this
        dict to not map every single old FDEF index; what happens if this
        occurs is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``fdefMappingFunc`` or ``oldToNew``.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_renumberfdefsdirect = True))
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> print(Test1(x=25).fdefsRenumbered(oldToNew=d))
    x = 1025
    >>> print(Test1(x=29).fdefsRenumbered(oldToNew=d))
    x = 29
    >>> print(Test1(x=29).fdefsRenumbered(oldToNew=d, keepMissing=False))
    x = None
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1(x=10).fdefsRenumbered(fdefMappingFunc=f))
    x = 910
    >>> print(Test1(x=11).fdefsRenumbered(fdefMappingFunc=f))
    x = 11
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         deep = dict(
    ...             attr_followsprotocol=True,
    ...             attr_strneedsparens=True))
    
    >>> print(Test2(deep=Test1(x=24)).fdefsRenumbered(fdefMappingFunc=f))
    deep = (x = 924)
    """
    
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return type(self)(**dNew)

def M_gatheredInputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs used as inputs to some
    process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``

    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         topIrrelevant = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topDirect = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom(5)
    >>> t = Top(topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredInputGlyphs())
    [5, 11]
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> sorted(Test2(x=1, y=Test1([2])).gatheredInputGlyphs())
    [1, 2]
    """
    
    return attrhelper.M_gatheredInputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredLivingDeltas(self, **kwArgs):
    """
    Return a set of :py:class:`~fontio3.opentype.living_variations.LivingDeltas`
    objects contained in ``self``.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of ``LivingDeltas`` objects.
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8` ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual ``LivingDeltas`` objects. Since those objects
    are immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual ``LivingDeltas`` objects!
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...   attrSpec = {'bot': {'attr_islivingdeltas': True}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...   attrSpec = dict(
    ...     a = {'attr_followsprotocol': True},
    ...     b = {'attr_islivingdeltas': True},
    ...     c = {})
    >>> botObj = Bottom(5)
    >>> topObj = Top(a=botObj, b=-4, c=2)
    >>> sorted(topObj.gatheredLivingDeltas())
    [-4, 5]
    """
    
    return attrhelper.M_gatheredLivingDeltas(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredMaxContext(self, **kwArgs):
    """
    Return an integer representing the ``'OS/2'`` maximum context value.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The maximum context
    :rtype: int
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_maxcontextfunc': (lambda v: len(v) - 1)}
    >>> b1 = Bottom([6, 7, 8, 10, 12, 15, 2])
    >>> b1.gatheredMaxContext()
    6
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top(x = [8, 1, 4], y=b1).gatheredMaxContext()
    8
    >>> Top(x = [4, 1, 4], y=b1).gatheredMaxContext()
    6
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_maxcontextfunc': (lambda obj: obj[0])}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> print(Test2(x=4, y=Test1([2, 3])).gatheredMaxContext())
    4
    """
    
    return attrhelper.M_gatheredMaxContext(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredOutputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs generated as outputs from
    some process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'bot': {
    ...         'attr_renumberdirect': True,
    ...         'attr_isoutputglyph': True}}
    ...     attrSorted = ('bot',)
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         topDirect = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topIrrelevant = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom(5)
    >>> t = Top(topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredOutputGlyphs())
    [5, 11]
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> sorted(Test2(x=1, y=Test1([2])).gatheredOutputGlyphs())
    [1, 2]
    """
    
    return attrhelper.M_gatheredOutputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredRefs(self, **kwArgs):
    """
    Return a dict with ``Lookup`` objects contained within ``self``.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A dict mapping ``id(lookupObj)`` to the ``lookupObj``
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``

    When constructing a
    :py:class:`~fontio3.opentype.lookuplist.LookupList` you will
    need to gather all the
    :py:class:`~fontio3.opentype.lookup.Lookup` objects that are
    present in self. Often these will be duplicated: the same effect might be
    present in many different chaining contextual substitution rules, for
    example. By mapping the ``id()`` of the ``Lookup`` as the key in the
    returned dict, this duplication can be eliminated, just yielding the actual
    set of unique ``Lookup`` objects being used.

    You will rarely need to call this method.

    The following ``kwArgs`` are supported:

    ``keyTrace``
        This is an optional dict. As mentioned above, often multiple copies of
        the same ``Lookup`` might appear in a given object (e.g. a
        :py:class:`GSUB <fontio3.GSUB.GSUB_v11.GSUB>`). If you need to track
        down all the specific occurrences, you can provide a ``keyTrace`` dict.
        This dict maps the ``id()`` of the ``Lookup`` to a set of immutables
        representing where in the hierarchy all occurrences of that ``Lookup``
        were.

    ``keyTraceCurr``
        This is an optional immutable (often a string), useful only if you're
        also using a ``keyTrace``. It provides information about where you are
        in the hierarchy at any given point.
    
    >>> class Bottom(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_islookup = True)
    >>> class Middle(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_islookup = True))
    >>> b1 = Bottom([object(), None, object()])
    >>> b2 = Bottom([b1[0], None, object()])
    >>> m = Middle([b1, None, b2])
    >>> t = Top(x=m, y=object())
    >>> tr = t.gatheredRefs()
    >>> id(b1[0]) in tr, id(b2[2]) in tr, id(t.y) in tr
    (True, True, True)
    >>> id(b1[1]) in tr  # None is not added
    False
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_islookup': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> obj = Test2(x='a', y=Test1(['b', 'c']))
    >>> print(sorted(obj.gatheredRefs().values()))
    ['a', 'b', 'c']
    """
    
    return attrhelper.M_gatheredRefs(self._ATTRSPEC, self.__dict__, **kwArgs)

def M_getSortedAttrNames(cls):
    """
    Return a tuple of attribute names.
    
    :return: Attribute names included in ``attrSorted``
    :rtype: tuple
    
    Note that some classes deliberately exclude attributes from their
    ``attrSorted`` tuple, and so those names won't be included in the result.
    """
    
    return cls._ATTRSORT

def M_glyphsRenumbered(self, oldToNew, **kwArgs):
    """
    Returns a new object with glyphs renumbered.
    
    :param oldToNew: Map from old to new glyph index
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with glyphs renumbered.
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        None.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph",
    ...         'attr_renumberdirect': True},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph",
    ...         'attr_renumberdirect': True}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> b = Bottom(first=20, second=35)
    >>> print(b.glyphsRenumbered({20:2, 35:4}))
    First Glyph = 2, Second Glyph = 4
    >>> print(b.glyphsRenumbered({20:2}))
    First Glyph = 2, Second Glyph = 35
    >>> print(b.glyphsRenumbered({20:2}, keepMissing=False))
    First Glyph = 2, Second Glyph = None
    >>> t = Top(n=35, pair=b)
    >>> t.glyphsRenumbered({20:2, 35:4}).pprint()
    Glyph Pair:
      First Glyph: 2
      Second Glyph: 4
    Count: 35
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> print(Test2(x=4, y=Test1([2, 3])).glyphsRenumbered({4:10, 2:11}))
    x = [10], y = [11, 3]
    """
    
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    return type(self)(**dNew)

def M_hasCycles(self, **kwArgs):
    """
    Determines if self is self-referential.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``activeCycleCheck``
        A set of ``id()`` values of deep objects. This is used to track deep
        usage; if at any level an object is encountered whose ``id()`` value is
        already present in this set, the function returns True. Note that it's
        safe to use object ID values, since this call does not mutate any data.
    
    ``memo``
        An optional set. This is used to store the ID values of objects that
        have already been found to have no cycles. It speeds up the process.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         deepAttr = dict(
    ...             attr_followsprotocol = True))
    >>> obj1 = Test1(deepAttr=None)
    >>> obj1.hasCycles()
    False
    >>> obj1.deepAttr = obj1
    >>> obj1.hasCycles()
    True
    """
    
    dACC = kwArgs.pop('activeCycleCheck', set())
    
    return attrhelper.M_hasCycles(
      self._ATTRSPEC,
      self.__dict__,
      activeCycleCheck = (dACC | {id(self)}),
      **kwArgs)

def M_isValid(self, **kwArgs):
    """
    Determine object validity.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if valid, False otherwise
    :rtype: bool
    
    The ``isValid()`` method represents the second half of the validation
    process. It checks the living object for internal consistency. The first
    half of the process is done while the object is being constructed, via one
    of the ``fromvalidated...()`` methods.
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        An :py:class:`~fontio3.fontedit.Editor`-class object. This is required.

    ``fontGlyphCount``
        The number of glyphs in the font. Will be used to check any glyph
        indices for validity. If not specified, the value will be read from the
        editor's ``'maxp'`` table, if present; otherwise, a default value of
        ``0x10000`` is used.
    
    ``logger``
        A logger to which errors will be posted. You should use a logger of the
        sort returned by :py:func:`~fontio3.utilities.makeDoctestLogger`.
    
    >>> def valFunc(obj, **kwArgs):
    ...     logger = kwArgs['logger']
    ...     try:
    ...         isOK = (obj % 2) == 1
    ...     except:
    ...         isOK = False
    ...     if not isOK:
    ...         logger.error(('Vxxxx', (obj,), "Value %s is not odd."))
    ...     return isOK
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_validatefunc = valFunc),
    ...         c = dict(attr_renumberdirect = True),
    ...         d = dict(
    ...             attr_renumberdirect = True,
    ...             attr_isoutputglyph = True),
    ...         e = dict(attr_renumberpcsdirect = True),
    ...         f = dict(attr_renumberpointsdirect = True),
    ...         g = dict(attr_scaledirect = True))
    
    >>> logger = utilities.makeDoctestLogger("t1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> t1 = Test(b = 6, c = 550, d = 160.4, e = -5, f = 9.9, g = 'Fred')
    >>> t1.isValid(logger=logger, fontGlyphCount=500, editor=e)
    t1.b - ERROR - Value 6 is not odd.
    t1.c - ERROR - Glyph index 550 too large.
    t1.d - ERROR - The glyph index 160.4 is not an integer.
    t1.e - ERROR - The program counter -5 cannot be used in an unsigned field.
    t1.f - ERROR - The point index 9.9 is not an integer.
    t1.g - ERROR - The value 'Fred' is not a real number.
    False
    
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> t2 = Test(a = t1, e = 'george')
    >>> t2.isValid(logger=logger, fontGlyphCount=500, editor=e)
    t2.a.b - ERROR - Value 6 is not odd.
    t2.a.c - ERROR - Glyph index 550 too large.
    t2.a.d - ERROR - The glyph index 160.4 is not an integer.
    t2.a.e - ERROR - The program counter -5 cannot be used in an unsigned field.
    t2.a.f - ERROR - The point index 9.9 is not an integer.
    t2.a.g - ERROR - The value 'Fred' is not a real number.
    t2.e - ERROR - The program counter 'george' is not a real number.
    False
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True,
    ...             attr_subloggernamefunc = (
    ...               lambda s:
    ...               "Fabulous %s!!!" % (s,))),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> logger = utilities.makeDoctestLogger("obj")
    >>> obj = Test2(x=1.4, y=Test1([12, 'x']))
    >>> obj.isValid(logger=logger, editor=e)
    obj.Fabulous x!!!.[0] - ERROR - The glyph index 1.4 is not an integer.
    obj.y.[1] - ERROR - The glyph index 'x' is not a real number.
    False
    
    >>> def _vf(obj, **kwArgs):
    ...     logger = kwArgs['logger']
    ...     if (obj.a + obj.b) % 5:
    ...         logger.error(('Vxxxx', (), "a+b must be a multiple of 5."))
    ...         return False
    ...     return True
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     objSpec = dict(
    ...         obj_validatefunc_partial = _vf)
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(),
    ...         c = dict(attr_renumberdirect=True))
    >>> logger = utilities.makeDoctestLogger("valobj")
    >>> Test3(a=12, b=-17, c=90).isValid(logger=logger, editor=e)
    True
    
    In the following, note that c's glyph validation still occurs:
    >>> Test3(a=2, b=4, c=-5).isValid(logger=logger, editor=e)
    valobj - ERROR - a+b must be a multiple of 5.
    valobj.c - ERROR - The glyph index -5 cannot be used in an unsigned field.
    False
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_prevalidatedglyphset = {65535},
    ...             attr_renumberdirect = True))
    >>> e = utilities.fakeEditor(0x2000)
    >>> obj = Test4(x=65535)
    >>> obj.isValid(logger=logger, editor=e)
    True
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_renumbernamesdirect = True))
    >>> logger = utilities.makeDoctestLogger("isvalid_Test5")
    >>> e = _fakeEditor()
    >>> obj = Test5(x=303)
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj.x += 500
    >>> obj.isValid(logger=logger, editor=e)
    isvalid_Test5.x - ERROR - Name table index 803 not present in 'name' table.
    False
    """
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        s = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(s)
    
    f = self._OBJSPEC.get('obj_validatefunc_partial', None)
    
    if f is not None:
        r = f(self, logger=logger, **kwArgs)
    else:
        r = True
    
    rAttr = attrhelper.M_isValid(
      self._ATTRSPEC,
      self.__dict__,
      logger = logger,
      **kwArgs)
    
    return rAttr and r

def M_merged(self, other, **kwArgs):
    """
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``conflictPreferOther``
        If True (the default) then in the absence of other controls (like deep
        merging, or an explicit merging function) attributes from ``other``
        will be used in the merged object. If False, attributes from ``self``
        will be preferred.
    
    ``replaceWhole``
        An optional Boolean, default False. If True, then in contexts where
        it's appropriate no merge will be attempted; the data in ``other`` will
        simply replace that of ``self`` in the merged object.
    
    In order to support any objects which have defined at least one attribute
    with its own ``attr_mergefunc`` this method passes along two extra keyword
    arguments: ``selfParent`` and ``otherParent``, which are just ``self`` and
    ``other``.
    
    >>> class Bottom(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someList': {'attr_followsprotocol': True}}
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([5, 2])
    >>> obj1 = Top(someNumber=4, someList=b1)
    >>> obj2 = Top(someNumber=4, someList=b2)
    >>> print(obj1.merged(obj2).someList)
    [1, 2, 3, 5]
    
    >>> class Test0(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {
    ...         'attr_initfunc': int,
    ...         'attr_mergefunc': (lambda a,b,**k: (b < a, min(a, b)))}}
    >>> x1, x2 = Test0(10), Test0(5)
    >>> print(x1)
    a = 10
    >>> print(x1.merged(x2))
    a = 5
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> obj1 = Test2(x=4, y=Test1([9, 4]))
    >>> obj2 = Test2(x=6, y=Test1([4, 5]))
    >>> print(obj1.merged(obj2))
    x = [4, 6], y = [9, 4, 5]
    """
    
    kwArgs['selfParent'] = self
    kwArgs['otherParent'] = other
    
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    return type(self)(**dNew)

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         name1 = dict(
    ...             attr_renumbernamesdirect = True))
    >>> obj = Test1(name1=304)
    >>> e = _fakeEditor()
    >>> obj.pprint(editor=e)
    name1: 304 ('Common Ligatures On')
    
    >>> obj.namesRenumbered({304:307}).pprint(editor=e)
    name1: 307 ('Small Caps')
    """
    
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    return type(self)(**dNew)

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(pc = dict(attr_renumberpcsdirect = True))
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> Bottom(5).pcsRenumbered(mapData, infoString="testcode").pc
    5
    >>> Bottom(12).pcsRenumbered(mapData, infoString="testcode").pc
    14
    >>> Bottom(50).pcsRenumbered(mapData, infoString="testcode").pc
    53
    >>> Bottom(100).pcsRenumbered(mapData, infoString="testcode").pc
    106
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(container = dict(attr_followsprotocol = True))
    >>> obj = Top(Bottom(12))
    >>> obj.pcsRenumbered(mapData, infoString="testcode").container.pc
    14
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberpcsdirect': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> md = {'test': [(5, 1), (15, 3), (30, 4)]}
    >>> obj = Test2(x=12, y=Test1([4, 20, 50]))
    >>> print(obj.pcsRenumbered(md, infoString="test"))
    x = [13], y = [4, 23, 54]
    """
    
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    return type(self)(**dNew)

def M_pointsRenumbered(self, mapData, **kwArgs):
    """
    Returns a new object with point indices renumbered.
    
    :param mapData: Dict mapping glyph index to an ``oldToNew`` dict
    :type mapData: dict(int, dict(int, int))
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with points renumbered
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``glyphIndex``
        This is required. It is a glyph index, used to select which oldToNew
        dict is to be used for the mapping.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         pointNumber = dict(attr_renumberpointsdirect = True))
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         bottom = dict(
    ...           attr_followsprotocol = True,
    ...           attr_strneedsparens = True))
    >>> b = Bottom(10)
    >>> t = Top(b)
    >>> print(t)
    bottom = (pointNumber = 10)
    >>> myMap = {5: {10: 20}, 20: {10: 11}}
    >>> print(t.pointsRenumbered(myMap, glyphIndex=5))
    bottom = (pointNumber = 20)
    
    >>> class Test1(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberpointsdirect': True}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> md = {21: {4: 10, 9: 11, 11: 9}}
    >>> obj = Test2(x=4, y=Test1([9, 40, 11]))
    >>> print(obj.pointsRenumbered(md, glyphIndex=21))
    x = [10], y = [11, 40, 9]
    """
    
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    return type(self)(**dNew)

def M_pprint(self, **kwArgs):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``elideDuplicates``
        The default is False, which means if the same object happens to appear
        in multiple places within self, each occurrence will result in a full
        printout of that object. If this flag is set to True, the first
        appearance will be full, and will be annotated with a tag; any
        subsequent appearances of the same object will be reduced to a one-line
        reference to that tag. In highly complex and layered fonts like
        Bustani, this can save literally millions of lines of output.
    
    ``keys``
        An optional tuple of attribute names. Normally, all the attributes
        listed in the ``attrSorted`` tuple are included in the ``pprint()``
        output. You can override this by providing your own tuple of attribute
        names in this keyword.
    
    ``indent``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``indentDelta``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``label``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``maxWidth``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``namer``
        An optional :py:class:`~fontio3.utilities.namer.Namer` object that will
        be used wherever glyph index values are shown.
    
    ``noDataString``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``p``
        An optional :py:class:`~fontio3.utilities.pp.PP` object to which output
        will be sent. If one is not provided, a new ``PP`` object will be
        created, potentially using ``kwArgs`` values of its own.
    
    ``stream``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph",
    ...         'attr_renumberdirect': True,
    ...         'attr_usenamerforstr': True},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph",
    ...         'attr_renumberdirect': True,
    ...         'attr_usenamerforstr': True}}
    ...     attrSorted = ('first', 'second')
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> nm = namer.testingNamer()
    >>> t = Top()
    >>> t.pprint(label="The Top object", namer=nm)
    The Top object:
      Glyph Pair:
        First Glyph: xyz1
        Second Glyph: xyz1
      Count: 1
    >>> t.pair.second = 19
    >>> t.n += 4
    >>> t.pprint(label="The changed object", namer=nm)
    The changed object:
      Glyph Pair:
        First Glyph: xyz1
        Second Glyph: xyz20
      Count: 5
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    ...   attrSorted = ('s',)
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    ...   attrSorted = ('s',)
    >>> Test1().pprint()
    s: fred
    >>> Test2().pprint()
    s: 'fred'
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    ...     attrSorted = ('x', 'y')
    >>> Test3().pprint(label="Note x is suppressed")
    Note x is suppressed:
      y: 5
    >>> Test3(x=4).pprint(label="No suppression here")
    No suppression here:
      x: 4
      y: 5
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_renumberdirect = True,
    ...             attr_usenamerforstr = True),
    ...         y = dict(attr_renumberdirect = True))
    >>> t4 = Test4(x=35, y=45)
    >>> t4.pprint()
    x: 35
    y: 45
    >>> t4.pprint(namer=namer.testingNamer())
    x: xyz36
    y: 45
    
    >>> class Test6(object, metaclass=FontDataMetaclass):
    ...     objSpec = dict(
    ...         obj_pprintfunc = (
    ...           lambda p, obj, **k:
    ...           p.simple("From %s to %s" % (obj.a, obj.b))))
    ...     attrSpec = dict(
    ...         a = dict(attr_label = "First"),
    ...         b = dict(attr_label = "Second"))
    >>> Test6(a=2, b=-15).pprint()
    From 2 to -15
    
    >>> class Test7(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(attr_ppoptions = {'noDataString': "(missing glyph)"}))
    >>> Test7().pprint()
    a: (no data)
    b: (missing glyph)
    
    >>> class Test8(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_pprintlabelfunc = (lambda i: "Entry #%d" % (i + 1,)),
    ...         item_renumberdirect = True,
    ...         item_usenamerforstr = True)
    >>> class Test9(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_deepconverterfunc = (lambda x,**k: Test8([x])),
    ...             attr_followsprotocol = True),
    ...         y = dict(
    ...             attr_followsprotocol = True))
    
    >>> Test9(x=12, y=Test8([4, 97])).pprint(namer=namer.testingNamer())
    x:
      Entry #1: xyz13
    y:
      Entry #1: xyz5
      Entry #2: afii60002
    
    >>> class Test10(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(),
    ...         c = dict())
    >>> class Test11(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_followsprotocol = True),
    ...         z = dict(attr_followsprotocol = True))
    >>> obj10 = Test10(14, 'Hi there', (4, 2))
    >>> obj11 = Test11(obj10, obj10, obj10)
    >>> obj11.pprint()
    x:
      a: 14
      b: Hi there
      c: (4, 2)
    y:
      a: 14
      b: Hi there
      c: (4, 2)
    z:
      a: 14
      b: Hi there
      c: (4, 2)
    
    >>> obj11.pprint(elideDuplicates=True)
    OBJECT 0
    x:
      a: 14
      b: Hi there
      c: (4, 2)
    y: (duplicate; see OBJECT 0 above)
    z: (duplicate; see OBJECT 0 above)
    """
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    OS = self._OBJSPEC
    f = OS.get('obj_pprintfunc', None)
    fp = OS.get('obj_pprintfunc_partial', None)
    
    if f is not None:
        f(p, self, **kwArgs)
    
    else:
        if fp is not None:
            fp(p, self, **kwArgs)
        
        attrhelper.M_pprint(self, p, self.getNamer, **kwArgs)

def M_pprintChanges(self, prior, **kwArgs):
    """
    Displays the changes from ``prior`` to ``self``.
    
    :param prior: The previous object, to be compared to ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``indent``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``indentDelta``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``keys``
        An optional tuple of attribute names. Normally, all the attributes
        listed in the ``attrSorted`` tuple are included in the
        ``pprint_changes()`` output. You can override this by providing your
        own tuple of attribute names in this keyword.
    
    ``label``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``maxWidth``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``namer``
        An optional :py:class:`~fontio3.utilities.namer.Namer` object that will
        be used for any glyph index displays.
        
        .. warning::
            
            It is a flaw in the current design of ``pprint_changes()`` that
            this ``Namer`` is used for both ``self`` and ``prior``, even though
            ``prior`` may not have the same glyph repertoire that ``self``
            does. This can result in misleading names being shown. It's safe to
            use as long as you know the glyph repertoires are the same for both
            objects.
    
    ``noDataString``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    ``p``
        An optional :py:class:`~fontio3.utilities.pp.PP` object to which output
        will be sent. If one is not provided, a new ``PP`` object will be
        created, potentially using ``kwArgs`` values of its own.
    
    ``stream``
        See the :py:class:`~fontio3.utilities.pp.PP` class for a description of
        this option.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    ...     attrSorted = ('first', 'second')
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> t = Top()
    >>> t.pair.second = 19
    >>> t.n += 4
    >>> t.pprint_changes(Top(), label="The changes")
    The changes:
      Glyph Pair:
        Second Glyph changed from 0 to 19
      Count changed from 1 to 5
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    ...     attrSorted = ('x', 'y', 'z')
    >>> Test(x=1, y=2, z=3).pprint_changes(Test(x=1, y=2, z=2000))
    """
    
    if self == prior:
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    
    attrhelper.M_pprintChanges(
      self,
      prior.__dict__,
      p,
      self.getNamer(),
      **kwArgs)

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> def inPlaceFunc(obj, **kwArgs):
    ...     oldValue = obj[0]
    ...     obj[0] = int(round(oldValue * 1.1))
    ...     return (obj[0] != oldValue, obj)
    >>> def replaceFunc(obj, **kwArgs):
    ...     newValue = int(round(obj * 6.0))
    ...     return (obj != newValue, newValue)
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         inPlace = dict(attr_recalculatefunc = inPlaceFunc),
    ...         replace = dict(attr_recalculatefunc = replaceFunc))
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(bottom = dict(
    ...         attr_recalculatedeep = True,
    ...         attr_strneedsparens = True))
    >>> b = Bottom([6], 6)
    >>> t = Top(b)
    >>> print(t)
    bottom = (inPlace = [6], replace = 6)
    >>> print(t.recalculated())
    bottom = (inPlace = [7], replace = 36)
    
    >>> def _fPartial(obj, **kwArgs):
    ...     obj2 = obj.__copy__()
    ...     if obj2.a > obj2.b:
    ...         obj2.a, obj2.b = obj2.b, obj2.a
    ...     return obj != obj2, obj2
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_scaledirect = True),
    ...         b = dict(attr_scaledirect = True),
    ...         c = dict(
    ...           attr_recalculatefunc = (
    ...             lambda x, **k:
    ...             (x != round(x), round(x)))))
    ...     objSpec = dict(obj_recalculatefunc_partial = _fPartial)
    >>> Test1(5, 2, -10.75).recalculated().pprint()
    a: 2
    b: 5
    c: -11
    """
    
    fPartial = self._OBJSPEC.get('obj_recalculatefunc_partial', None)
    
    if fPartial is not None:
        self = fPartial(self, **kwArgs)[1]
    
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    return type(self)(**dNew)

def M_scaled(self, scaleFactor, **kwArgs):
    """
    Returns a object with FUnit distances scaled.
    
    :param float scaleFactor: The scale factor to use
    :param kwArgs: Optional keyword arguments (see below)
    :return: The scaled object
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``scaleOnlyInX``
        An optional flag. If True, scaling will only happen in X. If False, it
        will happen in both X and Y.
    
    ``scaleOnlyInY``
        An optional flag. If True, scaling will only happen in Y. If False, it
        will happen in both X and Y.
    
    .. note::
        
        It's generally better if you use the ``transformed()`` method in lieu
        of this method, as this method is limited to simple scaling, whereas
        the ``transformed()`` method can also handle skew and rotation.
    
    >>> class Bottom(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_scaledirect': True}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       v = dict(attr_followsprotocol = True),
    ...       n = dict(attr_scaledirect = True))
    ...     attrSorted = ('v', 'n')
    >>> b = Bottom([2, 4, 6])
    >>> t = Top(v=b, n=25)
    >>> print(t)
    v = [2, 4, 6], n = 25
    >>> print(t.scaled(1.5))
    v = [3, 6, 9], n = 38
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {'attr_scaledirect': True}}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {'attr_scaledirectnoround': True}}
    >>> print(Test1(3.5).scaled(1.5))
    x = 5.0
    >>> print(Test2(3.5).scaled(1.5))
    x = 5.25
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_scaledirect = True, attr_representsx = True),
    ...         y = dict(attr_scaledirect = True, attr_representsy = True),
    ...         z = dict(attr_scaledirect = True))
    >>> print(Test3(2.0, 2.0, 2.0).scaled(5.0))
    x = 10.0, y = 10.0, z = 10.0
    >>> print(Test3(2.0, 2.0, 2.0).scaled(5.0, scaleOnlyInX=True))
    x = 10.0, y = 2.0, z = 10.0
    >>> print(Test3(2.0, 2.0, 2.0).scaled(5.0, scaleOnlyInY=True))
    x = 2.0, y = 10.0, z = 10.0
    """
    
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    return type(self)(**dNew)

def M_storageRenumbered(self, **kwArgs):
    """
    Return new object with storage index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with storage indices renumbered
    :rtype: Same as self
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``

    Storage indices are used in TrueType hinting, and can appear in several
    different tables. If you are merging fonts together, you might want to
    renumber the storage indices in the various input fonts so they don't
    collide. This method helps you do that.

    The following ``kwArgs`` are supported:

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with None.

    ``oldToNew``
        A dict mapping old storage indices to new ones. Note that it's OK for
        this dict to not map every single old storage index; what happens if
        this occurs is specified by the ``keepMissing`` flag.

    ``storageDelta``
        An optional integer value (possibly negative) that will be added to the
        old storage index to obtain the new one.

    ``storageMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the storage index), and should allow for arbitrary
        keyword arguments. It returns the new storage index.

    .. note::
  
      You should choose exactly *one* of ``storageDelta``,
      ``storageMappingFunc``, or ``oldToNew``.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_renumberstoragedirect = True))
    
    >>> print(Test1(x=25).storageRenumbered(storageDelta=300))
    x = 325
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> print(Test1(x=25).storageRenumbered(oldToNew=d))
    x = 1025
    >>> print(Test1(x=29).storageRenumbered(oldToNew=d))
    x = 29
    >>> print(Test1(x=29).storageRenumbered(oldToNew=d, keepMissing=False))
    x = None
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1(x=10).storageRenumbered(storageMappingFunc=f))
    x = 910
    >>> print(Test1(x=11).storageRenumbered(storageMappingFunc=f))
    x = 11
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         deep = dict(
    ...             attr_followsprotocol=True,
    ...             attr_strneedsparens=True))
    
    >>> print(Test2(deep=Test1(x=25)).storageRenumbered(storageDelta=400))
    deep = (x = 425)
    """
    
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return type(self)(**dNew)

def M_transformed(self, matrixObj, **kwArgs):
    """
    Returns a object with FUnit distances transformed.
    
    :param matrixObj: The :py:class:`~fontio3.fontmath.matrix.Matrix` to use
    :param kwArgs: Optional keyword arguments (see below)
    :return: The transformed object
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``attr_followsprotocol`` is set, provided there is no
        ``attr_deepconverterfunc``
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_representsx = True,
    ...             attr_transformcounterpart = 'y'),
    ...         y = dict(
    ...             attr_representsy = True,
    ...             attr_transformcounterpart = 'x'))
    >>> m = matrix.Matrix.forShift(5, 6)
    >>> print(Test1(x=2, y=-2).transformed(m))
    x = 7, y = 4
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_representsx = True,
    ...             attr_roundfunc = utilities.truncateRound,
    ...             attr_transformcounterpart = 'y'),
    ...         y = dict(
    ...             attr_representsy = True,
    ...             attr_transformcounterpart = 'x'))
    >>> m = matrix.Matrix.forScale(1.75, -0.25)
    >>> print(Test2(2, 6).transformed(m))
    x = 3, y = -2
    """
    
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    return type(self)(**dNew)

def SM_bool(self):
    """
    Return True if at least one of the attributes has a value for which
    ``bool()`` returns True. Attributes with ``attr_ignoreforcomparisons`` set
    True are always treated as False for this method.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 0)),
    ...         z = dict(
    ...             attr_initfunc = (lambda: 0),
    ...             attr_ignoreforcomparisons = True))
    >>> t = Test()
    >>> bool(t)
    False
    >>> t.z = 10
    >>> bool(t)
    False
    >>> t.y = 1
    >>> bool(t)
    True
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(),
    ...         y = dict(attr_ignoreforbool = True))
    >>> bool(Test2(5, 0))
    True
    >>> bool(Test2(0, 5))
    False
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(),
    ...         c = dict())
    ...     objSpec = dict(
    ...         obj_boolfalseiffalseset = set(['a', 'b']))
    >>> bool(Test3(1, 2, 0))
    True
    >>> bool(Test3(1, 0, 1))
    False
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_ignoreforcomparisons = True),
    ...         b = dict(attr_ignoreforbool = True),
    ...         c = dict())
    ...     objSpec = dict(
    ...         obj_boolfalseiffalseset = set(['a', 'b']))
    Traceback (most recent call last):
      ...
    ValueError: Key(s) ['a', 'b'] cannot have attr_ignore* flags set!
    """
    
    bfifs = self._OBJSPEC.get('obj_boolfalseiffalseset', None)
    
    if bfifs is not None:
        return all(bool(self.__dict__[k]) for k in bfifs)
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_copy(self):
    """
    Return a shallow copy.
    
    :return: A shallow copy of ``self``
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> b = Bottom(first=20, second=35)
    >>> t = Top(n=35, pair=b)
    >>> t2 = t.__copy__()
    >>> t == t2, t is t2
    (True, False)
    >>> t.pair is t2.pair
    True
    """
    
    return type(self)(**self.__dict__)

def SM_deepcopy(self, memo=None):
    """
    Return a deep copy.
    
    :param memo: An optional dict to control duplicates
    :return: A deep copy of ``self``
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...           'attr_label': "Glyph Pair",
    ...           'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> b = Bottom(first=20, second=35)
    >>> t = Top(n=35, pair=b)
    >>> t2 = t.__deepcopy__()
    >>> t == t2, t is t2
    (True, False)
    >>> t.pair is t2.pair
    False
    """
    
    if memo is None:
        memo = {}
    
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    return type(self)(**dNew)

def SM_eq(self, other):
    """
    Return True if the two objects are equal.
    
    :return: True if objects are equal; False otherwise
    :rtype: bool
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(),
    ...         y = dict(attr_ignoreforcomparisons = True))
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict())
    >>> t1 = Top(Bottom(2, 3), 4)
    >>> t1 == t1
    True
    
    In the following, Bottom.y is ignored as specified
    >>> t1 == Top(Bottom(2, 5), 4)
    True
    
    >>> t1 == Top(Bottom(5, 3), 4)
    False
    """
    
    if self is other:
        return True
    
    return attrhelper.SM_eq(
        self._ATTRSPEC,
        getattr(other, '_ATTRSPEC', {}),
        self.__dict__,
        getattr(other, '__dict__', {}))

def SM_init(self, *args, **kwArgs):
    """
    Initialize a new empty object.
    
    If positional arguments are specified, they will be matched with attributes
    in the order specified by ``attrSorted` (note this means there may be no
    more than ``len(attrSorted)`` positional arguments). Any attributes not
    explicitly set via the positional arguments or in ``kwArgs`` will be
    initialized according to their ``attr_initfunc`` functions.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> obj = Top(pair=Bottom(4, second=12))  # n gets default initial value
    >>> obj.n, obj.pair.first, obj.pair.second
    (1, 4, 12)
    
    >>> obj.pprint()
    Glyph Pair:
      First Glyph: 4
      Second Glyph: 12
    Count: 1
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     def _init_b_c(self):
    ...         if 'b' not in self.__dict__:
    ...             self.b = self.a[:2]
    ...         if 'c' not in self.__dict__:
    ...             self.c = self.a[2:]
    ...     attrSpec = dict(
    ...         a = dict(attr_initfunc = (lambda: "abc")),
    ...         b = dict(
    ...             attr_initfunc = _init_b_c,
    ...             attr_initfuncchangesself = True),
    ...         c = dict(
    ...             attr_initfunc = _init_b_c,
    ...             attr_initfuncchangesself = True))
    
    >>> Test1().pprint()
    a: abc
    b: ab
    c: c
    
    >>> Test1(a="wxyz and then some").pprint()
    a: wxyz and then some
    b: wx
    c: yz and then some
    
    >>> Test1(c="independently initialized").pprint()
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test2T(tuple, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class Test2S(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(
    ...             attr_ensuretype = Test2T,
    ...             attr_followsprotocol = True))
    >>> g = (i*i for i in (1, 2, 5))
    >>> obj = Test2S(g)
    >>> print(isinstance(obj.a, Test2T))
    True
    >>> print(obj.a)
    (1, 4, 25)
    """
    
    d = self.__dict__
    AS = self._ATTRSORT
    
    if args:
        if len(args) > len(AS):
            raise AttributeError("Too many positional arguments!")
        
        for i, value in enumerate(args):
            d[AS[i]] = value
    
    AS = self._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        # can't use kwArgs.get here, because no lazy eval on 2nd arg
        if k not in d:  # might have already been set positionally
            if k in kwArgs:
                d[k] = kwArgs[k]
            
            elif 'attr_initfuncchangesself' in ks:
                # We defer doing these special initializations until all the
                # other positional and keyword arguments are done.
                deferredKeySet.add(k)
            
            else:
                args = ([self] if 'attr_initfuncneedsself' in ks else [])
                d[k] = ks['attr_initfunc'](*args)
    
    for k in deferredKeySet:
        ks = AS[k]
        initFunc = ks['attr_initfunc']
        
        if id(initFunc) not in changedFuncIDsAlreadyDone:
            changedFuncIDsAlreadyDone.add(id(initFunc))
            initFunc(self)  # the function changes self's attributes directly
    
    # Only after everything is set up do we do a final attr_ensuretype check.
    
    for k, ks in AS.items():
        et = ks.get('attr_ensuretype', None)
        
        if (et is not None) and (not isinstance(d[k], et)):
            d[k] = et(d[k])

def SM_lt(self, other):
    """
    Returns True if self is less than other. Note that this will only be added
    to the class if obj_enableordering is True.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 0)),
    ...         z = dict(attr_initfunc = (lambda: 0)))
    ...     objSpec = dict(obj_enableordering = True)
    >>> Test(1, 2, 3) < Test(5, 6, 7)
    True
    >>> Test(1, 2, 3) < Test(1, 2, 2)
    False
    >>> Test(1, 2, 3) < Test(1, 2, 3)
    False
    
    The other three comparison operators are also added at the same time:
    
    >>> Test(1, 2, 2) <= Test(1, 2, 3)
    True
    >>> Test(1, 2, 3) <= Test(1, 2, 3)
    True
    >>> Test(1, 2, 4) <= Test(1, 2, 3)
    False
    
    >>> Test(1, 2, 2) >= Test(1, 2, 3)
    False
    >>> Test(1, 2, 3) >= Test(1, 2, 3)
    True
    >>> Test(1, 2, 4) >= Test(1, 2, 3)
    True
    
    >>> Test(1, 2, 2) > Test(1, 2, 3)
    False
    >>> Test(1, 2, 3) > Test(1, 2, 3)
    False
    >>> Test(1, 2, 4) > Test(1, 2, 3)
    True
    """
    
    if self is other:
        return False
    
    return attrhelper.SM_lt(
        self._ATTRSPEC,
        self._ATTRSORT,
        getattr(other, '_ATTRSPEC', {}),
        self.__dict__,
        getattr(other, '__dict__', {}))

def SM_repr(self):
    """
    Returns a string that can be ``eval()``'d back to an equal object.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test1() == eval(repr(Test1()))
    True
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'combo': {'attr_initfunc': Test1, 'attr_followsprotocol': True},
    ...       'n': {'attr_initfunc': (lambda: 15)}}
    ...     attrSorted = ('combo', 'n')
    >>> Test2() == eval(repr(Test2()))
    True
    """
    
    AS = self._ATTRSPEC
    d = self.__dict__
    fmt = "%s(%s)" % (self.__class__.__name__, ', '.join(["%s=%r"] * len(AS)))
    t = tuple(x for k in AS for x in (k, d[k]))
    return fmt % t

def SM_str(self):
    """
    Returns a string representation of the object.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    ...     attrSorted = ('first', 'second')
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': Bottom,
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True,
    ...         'attr_strneedsparens': True}}
    ...     attrSorted = ('pair', 'n')
    >>> print(Bottom(first=20, second=25))
    First Glyph = 20, Second Glyph = 25
    >>> print(Top(n=40, pair=Bottom(first=20, second=25)))
    Glyph Pair = (First Glyph = 20, Second Glyph = 25), Count = 40
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {
    ...         'attr_labelfunc': (
    ...           lambda x, **k:
    ...           ("Odd" if x % 2 else "Even"))}}
    ...     attrSorted = ('x',)
    >>> print(Test(2))
    Even = 2
    >>> print(Test(3))
    Odd = 3
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    ...   attrSorted = ('s',)
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    ...   attrSorted = ('s',)
    >>> print(Test1())
    s = fred
    >>> print(Test2())
    s = 'fred'
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    ...     attrSorted = ('x', 'y')
    >>> print(Test3())
    y = 5
    >>> print(Test3(x=4))
    x = 4, y = 5
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         g = dict(
    ...             attr_label = "Glyph",
    ...             attr_usenamerforstr = True,
    ...             attr_renumberdirect = True))
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         top = dict(
    ...             attr_label = "Top-level",
    ...             attr_followsprotocol = True,
    ...             attr_usenamerforstr = True,
    ...             attr_strneedsparens = True))
    >>> x = Test4(29)
    >>> y = Test5(x)
    >>> print(y)
    Top-level = (Glyph = 29)
    >>> y.setNamer(namer.testingNamer())
    >>> print(y)
    Top-level = (Glyph = xyz30)
    >>> print(x)
    Glyph = 29
    
    >>> def f(value, obj, **k):
    ...     if obj.horiz: return "Distance from Y-axis"
    ...     return "Distance from X-axis"
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         horiz = dict(attr_initfunc = (lambda: True)),
    ...         distance = dict(
    ...             attr_initfunc = (lambda: 0),
    ...             attr_labelfunc = f,
    ...             attr_labelfuncneedsobj = True))
    ...     attrSorted = ('horiz', 'distance')
    
    >>> print(Test5(True, 5))
    horiz = True, Distance from Y-axis = 5
    
    >>> print(Test5(False, -8))
    horiz = False, Distance from X-axis = -8
    """
    
    sv = attrhelper.SM_str(self, self.getNamer())
    return ', '.join(sv)

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__bool__': SM_bool,
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__eq__': SM_eq,
    '__init__': SM_init,
    '__ne__': (lambda a, b: not (a == b)),
    '__repr__': SM_repr,
    '__str__': SM_str,
    'asImmutable': M_asImmutable,
    'checkInput': M_checkInput,
    'coalesced': M_coalesced,
    'compacted': M_compacted,
    'cvtsRenumbered': M_cvtsRenumbered,
    'fdefsRenumbered': M_fdefsRenumbered,
    'gatheredInputGlyphs': M_gatheredInputGlyphs,
    'gatheredLivingDeltas': M_gatheredLivingDeltas,
    'gatheredMaxContext': M_gatheredMaxContext,
    'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
    'gatheredRefs': M_gatheredRefs,
    'getSortedAttrNames': classmethod(M_getSortedAttrNames),
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

def _addMethods(cd, bases):
    cd['__hash__'] = None
    stdClasses = (object,)
    
    for mKey, m in _methodDict.items():
        if mKey in cd:
            continue
        
        for c in reversed(bases):  # do nearest ancestor first
            if hasattr(c, mKey):
                cand = getattr(c, mKey)
                
                if cand.__class__.__name__ == 'method-wrapper':
                    continue
                
                if any(getattr(d, mKey, None) is cand for d in stdClasses):
                    continue
                
                cd[mKey] = cand
                break
    
        else:
            cd[mKey] = m
    
    if cd['_OBJSPEC'].get('obj_enableordering', False):
        if '__lt__' not in cd:
            cd['__lt__'] = SM_lt
        
        cd['__gt__'] = (lambda a, b: not ((a < b) or (a == b)))
        cd['__ge__'] = (lambda a, b: not (a < b))
        cd['__le__'] = (lambda a, b: (a < b) or (a == b))

def _validateObjSpec(OS, AS):
    """
    Make sure only known keys are included in the objSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> d = {'obj_pprintfunc': None}
    >>> _validateObjSpec(d, {})
    >>> d = {'obj_xprintfunc': None}
    >>> _validateObjSpec(d, {})
    Traceback (most recent call last):
      ...
    ValueError: Unknown objSpec keys: ['obj_xprintfunc']
    """
    
    unknownKeys = set(OS) - validObjSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown objSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'obj_boolfalseiffalseset' in OS:
        badKeys = set()
        missingKeys = set()
        
        for k in OS['obj_boolfalseiffalseset']:
            if k not in AS:
                missingKeys.add(k)
            
            else:
                d = AS[k]
                
                if (
                  d.get('attr_ignoreforbool', False) or
                  d.get('attr_ignoreforcomparisons', False)):
                    
                    badKeys.add(k)
        
        if missingKeys:
            raise ValueError(
              "False set names %r are not defined!" %
              (sorted(missingKeys),))
        
        if badKeys:
            raise ValueError(
              "Key(s) %r cannot have attr_ignore* flags set!" %
              (sorted(badKeys),))

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for simple object classes. This is used most often to provide
    Protocol functionality to a collection of attributes.

    If this metaclass is applied to a class whose base class (or one of whose
    base classes) is already a Protocol class, the ``attrSpec`` will define
    additions to the original. In this case, if an ``attrSorted`` is provided,
    it will be used for the combined attributes (original and newly-added);
    otherwise the new attributes will be added to the end of the ``attrSorted``
    list.
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_OBJSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            AS = {k: v.copy() for k, v in c._ATTRSPEC.items()}
            extraAttrs = classdict.pop('attrSpec', {})
            
            for attrName, attrDict in extraAttrs.items():
                if attrName in AS:
                    AS[attrName].update(attrDict)
                else:
                    AS[attrName] = attrDict
            
            classdict['_ATTRSPEC'] = classdict['_EXTRA_SPEC'] = AS
            attrhelper.validateAttrSpec(AS)
            
            if 'attrSorted' in classdict:
                AT = classdict.pop('attrSorted')
            
            else:
                s = frozenset(c._ATTRSORT)
                v = [x for x in sorted(extraAttrs) if x not in s]
                AT = c._ATTRSORT + tuple(v)
            
            classdict['_ATTRSORT'] = AT
            OS = c._OBJSPEC.copy()
            OS.update(classdict.pop('objSpec', {}))
            classdict['_OBJSPEC'] = classdict['_MAIN_SPEC'] = OS
            _validateObjSpec(OS, AS)
        
        else:
            AS = classdict['_ATTRSPEC'] = classdict.pop('attrSpec', {})
            classdict['_EXTRA_SPEC'] = AS
            
            classdict['_ATTRSORT'] = classdict.pop(
              'attrSorted',
              tuple(sorted(AS)))
            
            attrhelper.validateAttrSpec(AS)
            OS = classdict['_OBJSPEC'] = classdict.pop('objSpec', {})
            classdict['_MAIN_SPEC'] = OS
            _validateObjSpec(OS, AS)
        
        _addMethods(classdict, bases)
        invariants.addInvariantMethods(classdict)
        
        return super(FontDataMetaclass, mcl).__new__(
          mcl,
          classname,
          bases,
          classdict)

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.fontdata import seqmeta
    from fontio3.fontmath import matrix
    from fontio3.utilities import namer
    
    def _fakeEditor():
        from fontio3.name.name import Name
        
        _fakeNameTable = {
            (1, 0, 0, 303): "Required Ligatures On",
            (1, 0, 0, 304): "Common Ligatures On",
            (1, 0, 0, 306): "Regular",
            (1, 0, 0, 307): "Small Caps"}
        
        e = utilities.fakeEditor(0x1000)
        e.name = Name(_fakeNameTable)
        return e

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
