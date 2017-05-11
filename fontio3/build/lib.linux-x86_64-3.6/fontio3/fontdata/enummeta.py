#
# enummeta.py -- Support for enumerated values
#
# Copyright © 2010-2015, 2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Clients wishing to add Protocol capabilities to their numeric classes should
use this metaclass. The following class attributes are used to control the
various behaviors and attributes of instances of the class:

``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``enumSpec``
    A dict of specification information for the value, where the keys and their
    associated values are defined in the following list. The listed defaults
    apply if the specified key is not present in the ``enumSpec``.
        
    ``enum_annotatevalue``
        If True, displayed strings will have the actual numeric value shown
        after them, in parentheses. If False, the displayed strings will stand
        alone.
        
        Default is False.
    
    ``enum_inputcheckfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate as an enumerated value.
        
        There is no default.
    
    ``enum_mergecheckequality``
        If True, and a ``merged()`` call is attempted which would change the
        value, then a ``ValueError`` is raised.
        
        Default is False.
    
    ``enum_pprintlabel``
        This is the string that prefaces the value in ``pprint()`` and
        ``pprint_changes()`` output. Note that it does not preface the value in
        ``__str__()`` or ``__repr__()`` output.
        
        Default is ``'Value'``.
    
    ``enum_recalculatefunc``
        If specified, this should be a function taking at least one argument,
        the object. Additional keyword arguments (for example, ``editor``)
        conforming to the ``recalculated()`` protocol may be specified.

        The function must return a pair: the first value is True or False,
        depending on whether the recalculated object's value actually changed.
        The second value is the new recalculated value to be used. Note this
        may be a simple value, or another object of the same type.
        
        There is no default.
    
    ``enum_stringsdefault``
        If this key is specified, then any time a value is to be displayed, and
        the value is not present, then this key's value will be shown instead.
        If this key is not specified, direct mapping of ``enum_stringsdict``
        will be done.

        This provides a bit of redundancy with the existing way of using
        ``defaultdict`` objects for the ``strings`` dict, since referencing a
        non-present key can cause that key to be added, which given dicts in
        static ``enumSpecs`` is not desired behavior.
        
        There is no default.
    
    ``enum_stringsdict``
        A dict mapping the numeric value to the string actually displayed.

        If you want a default string (for numbers not explicitly provided for)
        then make this a ``defaultdict`` with a factory function that returns
        the default string.
        
        There is no default; this *must* be specified.
    
    ``enum_validatecode_badenumvalue``
        The code to be used for logging when an unrecognized enum value is used.
        
        Default is ``'G0001'``.
    
    ``enum_validatefunc``
        A function taking one positional argument, the value of the enum, and
        an arbitrary number of keyword arguments. The function returns True if
        the object is valid.

        If ``enum_validatefunc`` is not specified, or if an
        ``enum_validatefunc_partial`` is specified, then default validation
        will be done on the value by requiring it to pass a ``__contains__()``
        test with respect to the keys of the ``enum_stringsdict``.
        
        There is no default.
    
    ``enum_validatefunc_partial``
        A function taking one positional argument, the value of the enum, and
        an arbitrary number of keyword arguments. The function returns True if
        the object is valid.
        
        There is no default.
    
    ``enum_wisdom``
        A string with information on what the object is, along with sensible
        usage notes.
        
        There is, alas, no default for wisdom.
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

validEnumSpecKeys = frozenset([
  'enum_annotatevalue',
  'enum_inputcheckfunc',
  'enum_mergecheckequality',
  'enum_pprintlabel',
  'enum_recalculatefunc',
  'enum_stringsdefault',
  'enum_stringsdict',
  'enum_validatecode_badenumvalue',
  'enum_validatefunc',
  'enum_validatefunc_partial',
  'enum_wisdom'])

# -----------------------------------------------------------------------------

#
# Methods
#

def M_asImmutable(baseType):
    """
    Make an immutable version of ``self``.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: An immutable version of ``self``
    :rtype: ``tuple`` or ``type(self)``
    
    If there are no attributes, then the value of ``self`` is immediately
    usable, and is returned (since in Python all numbers are immutable). If
    there are attributes, then a tuple will be returned whose first value is
    the object's value and whose subsequent values are immutable versions of
    the attribute values, in ``attrSorted`` order.
    
    The following keyword arguments are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id()`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    
    >>> t1 = Test1(-1)
    >>> t1.asImmutable()
    ('Test1', -1)
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_asimmutabledeep = True),
    ...         b = dict(attr_asimmutablefunc = tuple),
    ...         c = dict())
    >>> t2 = Test2(4, a=t1, b=[1, 2, 3], c='xxx')
    >>> t2.asImmutable()
    ('Test2', 4, ('a', ('Test1', -1)), ('b', (1, 2, 3)), ('c', 'xxx'))
    
    Note that ``c`` must already be immutable; if it isn't, an error is raised:
    
    >>> t2.c = [4, 5]
    >>> t2.asImmutable()
    Traceback (most recent call last):
      ...
    TypeError: unhashable type: 'list'
    """
    
    def M_asImmutable_closure(self, **kwArgs):
        AS = self._ATTRSPEC
        
        if issubclass(baseType, str):
            bts = self[:]
        else:
            bts = baseType(self)
        
        r = (type(self).__name__, bts)
        
        if not AS:
            return r
        
        rAttr = attrhelper.M_asImmutable(
          AS,
          self._ATTRSORT,
          self.__dict__,
          **kwArgs)
        
        return r + rAttr
    
    M_asImmutable_closure.__doc__ = M_asImmutable.__doc__
    return M_asImmutable_closure

def M_checkInput(self, valueToCheck, **kwArgs):
    """
    Check appropriateness of a value for ``self``.
    
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
    """
    
    # We short-circuit to the attribute check if there is an 'attrName'
    # kwArg specified.
    
    if 'attrName' in kwArgs:
        return attrhelper.M_checkInput(
          self._ATTRSPEC,
          self.__dict__,
          valueToCheck,
          **kwArgs)
    
    f = self._ENUMSPEC.get('enum_inputcheckfunc', None)
    
    if f is None:
        return True
    
    return f(valueToCheck, **kwArgs)

def M_coalesced(self, **kwArgs):
    """
    Make a coalesced version of ``self``.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: The coalesced object
    :rtype: Same as ``self``
    
    Creates a new object of the same type and value whose attributes have been
    "coalesced." This means that any attributes that have equal values but
    different ids are converted into references to the same id. This changes
    the topology of the object!

    The following ``kwArgs`` are supported:
    
    ``pool``
        A dict mapping immutable representations of objects to the objects
        themselves. A new, empty dictionary will be used as the pool if one is
        not specified.

        This is useful if you want to coalesce objects across many higher-level
        objects.
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = {
    ...       'a': {'attr_asimmutablefunc': tuple},
    ...       'b': {'attr_asimmutablefunc': tuple}}
    >>> t = Test1(10, a=[1, 2, 3], b = [1] + [2, 3])
    >>> t.a is t.b
    False
    >>> tCoal = t.coalesced()
    >>> tCoal == t
    True
    >>> tCoal.a is tCoal.b
    True
    """
    
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    
    dNew = attrhelper.M_coalesced(
      self._ATTRSPEC,
      self.__dict__,
      pool,
      **kwArgs)
    
    return type(self)(self, **dNew)

def M_compacted(self, **kwArgs):
    """
    Makes a compacted version of ``self``.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The compacted object
    :rtype: Same as ``self``.
    
    Since enumerated values are essentially numbers, and are themselves thus
    already as compact as possible, this method only affects attributes.
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_compactremovesfalses': True}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict1,
    ...         enum_annotatevalue = True)
    ...     attrSpec = {'a': {'attr_followsprotocol': True}}
    >>> t = Top(15, a=Bottom([2, False, 0, None, [], 3]))
    >>> print(t)
    What? (15), a = (2, False, 0, None, [], 3)
    >>> print(t.compacted())
    What? (15), a = (2, 3)
    """
    
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    return type(self)(self, **dNew)

def M_cvtsRenumbered(self, **kwArgs):
    """
    Return new object with CVT index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with CVT indices renumbered
    :rtype: Same as ``self``

    CVT indices are used in TrueType hinting, and can appear in several
    different tables. If you are merging fonts together, you might want to
    renumber the CVTs in the various input fonts so they don't collide. This
    method helps you do that.
    
    Because of the nature of enumerated values, this method really only
    affects the attributes.

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
        be replaced with ``None``.

    ``oldToNew``
        A dict mapping old CVT indices to new ones. Note that it's OK for this
        dict to not map every single old CVT index; what happens if this occurs
        is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``cvtDelta``, ``cvtMappingFunc``, or
      ``oldToNew``.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumbercvtsdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(-1, a=11, b=Test(3, a=13, b=None))
    >>> print(t)
    Ahh..., a = 11, b = (What?, a = 13, b = (None))
    >>> print(t.cvtsRenumbered(cvtDelta=300))
    Ahh..., a = 311, b = (What?, a = 313, b = (None))
    """
    
    vNew = self
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_fdefsRenumbered(self, **kwArgs):
    """
    Return new object with FDEF index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with FDEF indices renumbered
    :rtype: Same as ``self``

    FDEF (Function DEFinition) indices are used in TrueType hinting, and can
    appear in several different tables. If you are merging fonts together, you
    might want to renumber the FDEFs in the various input fonts so they don't
    collide. This method helps you do that.

    Because of the nature of enumerated values, this method really only
    affects the attributes.

    The following ``kwArgs`` are supported:

    ``fdefMappingFunc``
        This is optional. If specified, it should be a function taking one
        positional argument (the FDEF index), and should allow for arbitrary
        keyword arguments. It returns the new FDEF index.

    ``keepMissing``
        If True (the default) then any values not explicitly included in the
        ``oldToNew`` dict will be left unchanged. If False, those values will
        be replaced with ``None``.

    ``oldToNew``
        A dict mapping old FDEF indices to new ones. Note that it's OK for this
        dict to not map every single old FDEF index; what happens if this
        occurs is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``fdefMappingFunc`` or ``oldToNew``.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberfdefsdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(-1, a=11, b=Test(3, a=13, b=None))
    >>> print(t)
    Ahh..., a = 11, b = (What?, a = 13, b = (None))
    >>> print(t.fdefsRenumbered(fdefMappingFunc=(lambda n,**k:n+300)))
    Ahh..., a = 311, b = (What?, a = 313, b = (None))
    """
    
    vNew = self
    
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_gatheredInputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs used as inputs to some
    process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set

    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.
    
    >>> class BottomIn(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> bIn = BottomIn([1, 2, 3])
    
    >>> class BottomOut(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> bOut = BottomOut([4, 5, 6])
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(Top(-1, a=bIn, b=11, c=bOut).gatheredInputGlyphs())
    [1, 2, 3, 11]
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

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8`
    ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual LivingDeltas objects. Since those objects are
    immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual LivingDeltas objects!
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...   enumSpec = dict(enum_stringsdict = _testDict1)
    ...   attrSpec = dict(a={'attr_islivingdeltas': True}, b={})
    >>> obj = Test(-1, a=5, b=7)
    >>> sorted(obj.gatheredLivingDeltas())
    [5]
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

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Bot(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(seq_maxcontextfunc = (lambda obj: obj[0]))
    >>> bot = Bot([3, 1, 5, 2])
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(xTop = dict(attr_followsprotocol = True))
    >>> top = Top(-1, xTop=bot)
    >>> print(top.gatheredMaxContext())
    3
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

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> class BottomIn(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> bIn = BottomIn([1, 2, 3])
    
    >>> class BottomOut(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> bOut = BottomOut([4, 5, 6])
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(Top(-1, a=bIn, b=11, c=bOut).gatheredOutputGlyphs())
    [4, 5, 6]
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
    
    ``memo``
        An optional set. This is used to store the ID values of objects that
        have already been looked at. It speeds up the process.
    
    >>> class Test(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_islookup = True))
    >>> look1 = object()
    >>> look2 = object()
    >>> t = Test(0.75, a=Test(0.5, a=None, b=look1), b=look2)
    >>> d = t.gatheredRefs()
    >>> len(d)
    2
    >>> id(look1) in d, id(look2) in d
    (True, True)
    """
    
    return attrhelper.M_gatheredRefs(self._ATTRSPEC, self.__dict__, **kwArgs)

def M_glyphsRenumbered(self, oldToNew, **kwArgs):
    """
    Returns a new object with glyphs renumbered.
    
    :param oldToNew: Map from old to new glyph index
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with glyphs renumbered.
    :rtype: Same as ``self``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the mapping, or (if attributes or an index map) will be changed to
        ``None``.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(-1, a=11, b=Test(3, a=13, b=None))
    >>> print(t)
    Ahh..., a = 11, b = (What?, a = 13, b = (None))
    >>> print(t.glyphsRenumbered({10: 40, 11: 45, 12: 50, 13: 55}))
    Ahh..., a = 45, b = (What?, a = 55, b = (None))
    >>> print(t.glyphsRenumbered({10: 40, 11: 45, 12: 50}, keepMissing=False))
    Ahh..., a = 45, b = (What?, a = None, b = (None))
    """
    
    vNew = self
    
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_hasCycles(self, **kwArgs):
    """
    Determines if self is self-referential.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    
    The following ``kwArgs`` are supported:
    
    ``activeCycleCheck``
        A set of ``id()`` values of deep objects. This is used to track deep
        usage; if at any level an object is encountered whose ``id()`` value is
        already present in this set, the function returns True. Note that it's
        safe to use object ID values, since this call does not mutate any data.
    
    ``memo``
        An optional set. This is used to store the ID values of objects that
        have already been found to have no cycles. It speeds up the process.
    """
    
    # Enumerated values are always cycle-free; just check the attributes
    
    dACC = kwArgs.pop('activeCycleCheck', set())
    
    return attrhelper.M_hasCycles(
      self._ATTRSPEC,
      self.__dict__,
      activeCycleCheck = (dACC | {id(self)}),
      **kwArgs)

def M_isValid(baseType):
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
    
    >>> class Test(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    
    >>> logger = utilities.makeDoctestLogger("n")
    >>> e = utilities.fakeEditor(0x10000)
    >>> n = Test(0.5)
    >>> print(n.isValid(logger=logger, editor=e))
    True
    
    >>> n = Test(1.25)
    >>> print(n.isValid(logger=logger, editor=e))
    n - ERROR - Value 1.25 is not a valid enum value.
    False
    
    >>> def _vf(n, **kwArgs):
    ...     if int(n) == 1:
    ...         kwArgs['logger'].warning((
    ...           'Vxxxx',
    ...           (),
    ...           "Red is deprecated; use blue."))
    ...     return True
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_validatefunc_partial = _vf)
    >>> Test2(2).isValid(logger=logger, editor=e)
    True
    >>> Test2(1).isValid(logger=logger, editor=e)
    n - WARNING - Red is deprecated; use blue.
    True
    """
    
    def M_isValid_closure(self, **kwArgs):
        ES = self._ENUMSPEC
        r = True
        logger = kwArgs.pop('logger', None)
        
        if logger is None:
            s = __name__[__name__.rfind('.')+1:]
            logger = logging.getLogger().getChild(s)
        
        f = ES.get('enum_validatefunc', None)
        
        if f is not None:
            r = f(self, logger=logger, **kwArgs)
        
        else:
            fp = ES.get('enum_validatefunc_partial', None)
            
            if fp is not None:
                r = fp(self, logger=logger, **kwArgs)
            
            k = (self[:] if issubclass(baseType, str) else baseType(self))
            
            if k not in ES['enum_stringsdict']:
                logger.error((
                  ES.get('enum_validatecode_badenumvalue', 'G0001'),
                  (k,),
                  "Value %r is not a valid enum value."))
                
                r = False
        
        rAttr = attrhelper.M_isValid(self._ATTRSPEC, self.__dict__, **kwArgs)
        return rAttr and r
    
    M_isValid_closure.__doc__ = M_isValid.__doc__
    return M_isValid_closure

def M_merged(self, other, **kwArgs):
    """
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    
    The following ``kwArgs`` are supported:
    
    ``conflictPreferOther``
        True if when there is a key conflict the caller wishes the contents in
        ``other`` to have precedence; False if ``self`` should prevail. Default
        is True.
        
    ``replaceWhole``
        True if any keys in other matching keys in ``self`` will cause the
        entire replacement of those values; no deep merging will occur for
        those values. Default is False.
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
    >>> print(Test1(1).merged(Test1(2)))  # other is preferred by default
    Green
    >>> print(Test1(1).merged(Test1(2), conflictPreferOther=False))
    Red
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict3,
    ...         enum_mergecheckequality = True)
    >>> print(Test2(0.5).merged(Test2(0.5)))
    Half
    >>> print(Test2(0.5).merged(Test2(2.75)))
    Traceback (most recent call last):
      ...
    ValueError: Attempt to merge unequal values!
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someTuple': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someTuple', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([5, 2])
    >>> obj1 = Top(2, someNumber=4, someTuple=b1)
    >>> obj2 = Top(3, someNumber=8, someTuple=b2)
    >>> print(obj1.merged(obj2))
    Blue, someTuple = (1, 2, 3, 5), someNumber = 8
    >>> print(obj1.merged(obj2, conflictPreferOther=False))
    Green, someTuple = (1, 2, 3, 5), someNumber = 4
    """
    
    prefOther = kwArgs.get('conflictPreferOther', True)
    
    if self != other:
        if self._ENUMSPEC.get('enum_mergecheckequality', False):
            raise ValueError("Attempt to merge unequal values!")
        
        replaceWhole = kwArgs.get('replaceWhole', False)
        vNew = (other if prefOther or replaceWhole else self)
    
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct names, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be changed to
        ``None``.
    """
    
    vNew = self
    
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberpcsdirect = True))
    >>> t = Test(-1, a=20)
    >>> print(t)
    Ahh..., a = 20
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> print(t.pcsRenumbered(mapData, infoString="testcode"))
    Ahh..., a = 22
    """
    
    vNew = self
    
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_pointsRenumbered(self, mapData, **kwArgs):
    """
    Returns a new object with point indices renumbered.
    
    :param mapData: Dict mapping glyph index to an ``oldToNew`` dict
    :type mapData: dict(int, dict(int, int))
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with points renumbered
    
    The following ``kwArgs`` are supported:
    
    ``glyphIndex``
        This is required. It is a glyph index, used to select which oldToNew
        dict is to be used for the mapping.
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be changed to
        ``None``.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberpointsdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(-1, a=15, b=Test(4, a=25, b=None))
    >>> print(t)
    Ahh..., a = 15, b = (What?, a = 25, b = (None))
    >>> myMap = {440: {10: 12, 12: 15, 15: 10}, 444: {15: 25, 25: 15}}
    >>> print(t.pointsRenumbered(myMap, glyphIndex=440))
    Ahh..., a = 10, b = (What?, a = 25, b = (None))
    >>> print(t.pointsRenumbered(myMap, glyphIndex=444))
    Ahh..., a = 25, b = (What?, a = 15, b = (None))
    """
    
    vNew = self
    
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_pprint(baseType):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
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
    
    >>> class Test0(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_annotatevalue = True,
    ...         enum_stringsdict = _testDict2,
    ...         enum_pprintlabel = "Color")
    >>> Test0(1).pprint()
    Color: Red (1)
    
    >>> class Test1(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict3,
    ...         enum_pprintlabel = "Portion")
    ...     attrSpec = dict(
    ...         g = dict(
    ...             attr_label = "Glyph extra",
    ...             attr_renumberdirect = True,
    ...             attr_usenamerforstr = True))
    >>> Test1(0.5, g=98).pprint()
    Portion: Half
    Glyph extra: 98
    >>> Test1(0.75, g=98).pprint(namer=namer.testingNamer())
    Portion: Three-quarters
    Glyph extra: afii60003
    """
    
    def M_pprint_closure(self, **kwArgs):
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        ES = self._ENUMSPEC
        nm = kwArgs.get('namer', self.getNamer())
        label = ES.get('enum_pprintlabel', "Value")
        default = ES.get('enum_stringsdefault', None)
        key = (self[:] if issubclass(baseType, str) else baseType(self))
        
        if default is None:
            s = ES['enum_stringsdict'][key]
        else:
            s = ES['enum_stringsdict'].get(key, default)
        
        if ES.get('enum_annotatevalue', False):
            s = "%s (%s)" % (s, key)
        
        p.simple(s, label=label)
        
        # Now do attributes
        attrhelper.M_pprint(self, p, (lambda: nm), **kwArgs)
    
    M_pprint_closure.__doc__ = M_pprint.__doc__
    return M_pprint_closure

def M_pprintChanges(baseType):
    """
    Displays the changes from ``prior`` to ``self``.
    
    :param prior: The previous object, to be compared to ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    
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
    
    >>> class Test0(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_pprintlabel = "Color")
    >>> Test0(3).pprint_changes(Test0(2))
    Color changed from Green to Blue
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_pprintlabel = "Color",
    ...         enum_annotatevalue = True)
    >>> Test1(3).pprint_changes(Test1(2))
    Color changed from Green (2) to Blue (3)
    """
    
    def M_pprintChanges_closure(self, prior, **kwArgs):
        if self == prior:
            return
        
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        ES = self._ENUMSPEC
        nm = kwArgs.get('namer', self.getNamer())
        selfValue = (self[:] if issubclass(baseType, str) else baseType(self))
        priorValue = (prior[:] if issubclass(baseType, str) else baseType(prior))
        
        if selfValue != priorValue:
            label = ES.get('enum_pprintlabel', "Value")
            default = ES.get('enum_stringsdefault', None)
            d = ES['enum_stringsdict']
            
            if default is None:
                if ES.get('enum_annotatevalue', False):
                    t = (
                      label,
                      d[priorValue],
                      priorValue,
                      d[selfValue],
                      selfValue)
                    
                    p("%s changed from %s (%s) to %s (%s)" % t)
                
                else:
                    p(
                      "%s changed from %s to %s" %
                      (label, d[priorValue], d[selfValue]))
            
            else:
                if ES.get('enum_annotatevalue', False):
                    t = (
                      label,
                      d.get(priorValue, default),
                      priorValue,
                      d.get(selfValue, default),
                      selfValue)
                    
                    p("%s changed from %s (%s) to %s (%s)" % t)
                
                else:
                    t = (
                      label,
                      d.get(priorValue, default),
                      d.get(selfValue, default))
                    
                    p("%s changed from %s to %s" % t)
        
        attrhelper.M_pprintChanges(
          self,
          prior.__dict__,
          p,
          nm,
          **kwArgs)
    
    M_pprintChanges_closure.__doc__ = M_pprintChanges.__doc__
    return M_pprintChanges_closure

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> def recalc(oldObj):
    ...     newObj = oldObj * 2 - 1
    ...     return newObj != oldObj, newObj
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_annotatevalue = True,
    ...         enum_recalculatefunc = recalc,
    ...         enum_stringsdict = _testDict2)
    >>> print(Test1(2).recalculated())
    Blue (3)
    """
    
    ES = self._ENUMSPEC
    f = ES.get('enum_recalculatefunc', None)
    
    if f is not None:
        changed, vNew = f(self, **kwArgs)
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_scaled(self, scaleFactor, **kwArgs):
    """
    Returns a object with FUnit distances scaled.
    
    :param float scaleFactor: The scale factor to use
    :param kwArgs: Optional keyword arguments (see below)
    :return: The scaled object
    
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
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     enumSpec = {
    ...       'enum_stringsdict': _testDict3,
    ...       'enum_annotatevalue': True}
    ...     attrSpec = dict(
    ...         y = dict(attr_scaledirect = True))
    >>> print(Test2(0.75, y=-6).scaled(2.5))
    Three-quarters (0.75), y = -15
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    vNew = self
    
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_storageRenumbered(self, **kwArgs):
    """
    Return new object with storage index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with storage indices renumbered
    :rtype: Same as self

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
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberstoragedirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(-1, a=11, b=Test(3, a=13, b=None))
    >>> print(t)
    Ahh..., a = 11, b = (What?, a = 13, b = (None))
    >>> print(t.storageRenumbered(storageDelta=300))
    Ahh..., a = 311, b = (What?, a = 313, b = (None))
    """
    
    vNew = self
    
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_transformed(self, matrixObj, **kwArgs):
    """
    Returns a object with FUnit distances transformed.
    
    :param matrixObj: The :py:class:`~fontio3.fontmath.matrix.Matrix` to use
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The transformed object
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    
    >>> class Test1(float, metaclass=FontDataMetaclass):
    ...     enumSpec = {
    ...       'enum_stringsdict': _testDict3,
    ...       'enum_annotatevalue': True}
    ...     attrSpec = dict(
    ...         y = dict(
    ...             attr_representsy = True,
    ...             attr_transformcounterpart = 0))
    >>> print(Test1(0.75, y=-6).transformed(m))
    Three-quarters (0.75), y = -8
    """
    
    vNew = self
    
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def SM_bool(baseType):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if there is any content. This means either the dict portion
        is nonempty, or there are some attributes that are nonzero and not
        flagged as ``attr_ignoreforcomparisons`` or ``attr_ignoreforbool``.
    :rtype: bool
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = {
    ...           0: "No color",
    ...           1: "Red",
    ...           2: "Blue"})
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforbool = True),
    ...         notIgnored = dict())
    >>> print(bool(Test1(1, ignored=0, notIgnored=0)))
    True
    >>> print(bool(Test1(0, ignored=0, notIgnored=0)))
    False
    >>> print(bool(Test1(0, ignored=5, notIgnored=0)))
    False
    >>> print(bool(Test1(0, ignored=0, notIgnored=1)))
    True
    """
    
    def SM_bool_closure(self):
        if (self[:] if issubclass(baseType, str) else baseType(self)):
            return True
        
        return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)
    
    SM_bool_closure.__doc__ = SM_bool.__doc__
    return SM_bool_closure

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    >>> b = Bottom(10.25)
    >>> bCopy = b.__copy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    ...     attrSpec = {'a': {}}
    >>> t = Top(5, a=[1, 2, 3])
    >>> tCopy = t.__copy__()
    >>> t == tCopy, t is tCopy
    (True, False)
    >>> t.a is tCopy.a
    True
    """
    
    if self._ATTRSPEC:
        return type(self)(self, **self.__dict__)
    else:
        return type(self)(self)

def SM_deepcopy(self, memo=None):
    """
    Make a deep copy.
    
    :param memo: A dict (default ``None``) to reduce reprocessing
    :return: A deep copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    >>> b = Bottom(10.25)
    >>> bCopy = b.__deepcopy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    ...     attrSpec = {'a': {'attr_deepcopyfunc': (lambda x,m: list(x))}}
    >>> t = Top(5, a=[1, 2, 3])
    >>> tCopy = t.__deepcopy__()
    >>> t == tCopy, t is tCopy
    (True, False)
    >>> t.a is tCopy.a
    False
    
    >>> class Topper(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    ...     attrSpec = {'b': {'attr_followsprotocol': True}}
    >>> p = Topper(-0.75, b=t)
    >>> pCopy = p.__deepcopy__()
    >>> p == pCopy, p is pCopy
    (True, False)
    >>> p.b is pCopy.b, p.b.a is pCopy.b.a
    (False, False)
    """
    
    if memo is None:
        memo = {}
    
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    return type(self)(self, **dNew)

def SM_eq(baseType):
    """
    Determine if the two objects are equal (selectively).
    
    :return: True if the mappings and their attributes are equal (allowing for
        selective inattention to certain attributes depending on their control
        flags, and depending on the ``attrSorted`` tuple)
    :rtype: bool
    
    This method is only included in a class with one or more defined
    attributes.
    
    >>> class Test(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    ...     attrSpec = {'a': {}, 'b': {'attr_ignoreforcomparisons': True}}
    >>> Test(0.5) == Test(0.5)
    True
    >>> Test(0.5) == 0.5
    True
    >>> Test(2.0) == Test(2)
    True
    >>> Test(5.0) == Test(4.5)
    False
    >>> Test(5.0) == 4.5
    False
    >>> Test(5.0, a=1, b=2) == Test(5.0, a=2, b=2)
    False
    >>> Test(5.0, a=1, b=2) == Test(5.0, a=1, b=30)
    True
    """
    
    def SM_eq_closure(self, other):
        if self is other:
            return True
        
        bts = (self[:] if issubclass(baseType, str) else baseType(self))
        bto = (other[:] if issubclass(baseType, str) else baseType(other))
        
        if bts != bto:
            return False
        
        # We now guarantee that other is the same type as self
        try:
            if self._ATTRSPEC != other._ATTRSPEC:
                other = type(self)(bto)
        
        except:
            other = type(self)(bto)
        
        return attrhelper.SM_eq(
          self._ATTRSPEC,
          other._ATTRSPEC,
          self.__dict__,
          other.__dict__)
    
    SM_eq_closure.__doc__ = SM_eq.__doc__
    return SM_eq_closure

# def SM_hash(baseType):
#     """
#     Returns a hash value for the object. Note this method is only included by
#     the metaclass initialization logic if there is at least one attribute that
#     has attr_ignoreforcomparisons set to False.
#     
#     >>> class Test1(int, metaclass=FontDataMetaclass):
#     ...     enumSpec = dict(enum_stringsdict = _testDict2)
#     ...     attrSpec = dict(
#     ...         ignored = dict(attr_ignoreforcomparisons = True),
#     ...         notIgnored = dict())
#     
#     >>> obj1 = Test1(1, ignored=3, notIgnored=4)
#     >>> obj2 = Test1(1, ignored=5, notIgnored=4)
#     >>> obj3 = Test1(1, ignored=3, notIgnored=7)
#     >>> len({obj1, obj2})
#     1
#     >>> len({obj1, obj3})
#     2
#     >>> len({obj1, obj2, obj3})
#     2
#     >>> d = {obj1: 15, obj3: 20}
#     >>> len(d)
#     2
#     """
#     
#     def SM_hash_closure(self):
#         AS = self._ATTRSPEC
#         d = self.__dict__
#         v = []
#         
#         for k in sorted(AS):  # don't use sortedKeys, as this needs to be exhaustive
#             ks = AS[k]
#             f = ks.get('attr_asimmutablefunc', None)
#             obj = d[k]
#             
#             if not ks.get('attr_ignoreforcomparisons', False):
#                 if ks.get('attr_asimmutabledeep', ks.get('attr_followsprotocol', False)):
#                     v.append(obj.asImmutable())
#                 elif f is not None:
#                     v.append(f(obj))
#                 else:
#                     v.append(obj)
#         
#         return hash((baseType(self), tuple(v)))
#     
#     SM_hash_closure.__doc__ = SM_hash.__doc__
#     return SM_hash_closure

def SM_init(self, value, *args, **kwArgs):
    """
    Initialize the attributes from ``kwArgs`` if they're present, or the
    attribute initialization function otherwise.
    """
    
    AS = self._ATTRSORT
    d = self.__dict__
    f = operator.itemgetter('attr_initfunc')
    
    if args:
        if len(args) > len(AS):
            raise ValueError("Too many positional arguments!")
        
        for i, n in enumerate(args):
            d[AS[i]] = n
    
    AS = self._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        if k not in d:  # might have been initialized from positional args
            if k in kwArgs:
                d[k] = kwArgs[k]
            
            elif 'attr_initfuncchangesself' in ks:
                # We defer doing these special initializations until all the
                # other positional and keyword arguments are done.
                deferredKeySet.add(k)
            
            else:
                v = ([self] if 'attr_initfuncneedsself' in ks else [])
                # it's now OK to do this, because we've already guaranteed all
                # attrdict specs have an attr_initfunc.
                d[k] = f(ks)(*v)
    
    for k in deferredKeySet:
        ks = AS[k]
        initFunc = f(ks)
        
        if id(initFunc) not in changedFuncIDsAlreadyDone:
            changedFuncIDsAlreadyDone.add(id(initFunc))
            initFunc(self)  # the function changes self's attributes directly
    
    # Only after everything is set up do we do a final attr_ensuretype check.
    
    for k, ks in AS.items():
        et = ks.get('attr_ensuretype', None)
        
        if (et is not None) and (not isinstance(d[k], et)):
            d[k] = et(d[k])

def SM_new(baseType):
    """
    Create a new instance, but defer attribute initialization to __init__. Note
    this method is only included in the class if attributes are present.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
    ...     attrSpec = {'a': {}}
    >>> int(Test(6))
    6
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_annotatevalue = True)
    ...     attrSpec = dict(
    ...         initValueSquared = dict(
    ...             attr_initfunc = (lambda n: n * n),
    ...             attr_initfuncneedsself = True))
    >>> n = Test2(3)
    >>> print(n)
    Blue (3), initValueSquared = 9
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
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
    >>> Test3(1).pprint()
    Value: Red
    a: abc
    b: ab
    c: c
    >>> Test3(1, a="wxyz and then some").pprint()
    Value: Red
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test3(1, c="independently initialized").pprint()
    Value: Red
    a: abc
    b: ab
    c: independently initialized
    """
    
    def SM_new_closure(cls, value, *args, **kwArgs):
        if issubclass(baseType, str):
            return str.__new__(cls, value)
        else:
            return baseType.__new__(cls, value)
    
    SM_new_closure.__doc__ = SM_new.__doc__
    return SM_new_closure

def SM_repr(baseType):
    """
    Return a string that can be eval()'d back to an equal object.
    
    >>> class Test1(float, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict3)
    >>> t1 = Test1(52.5)
    >>> print(repr(t1))
    Test1(52.5)
    >>> t1 == eval(repr(t1))
    True
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test2(-5) == eval(repr(Test2(-5)))
    True
    """
    
    def SM_repr_closure(self):
        AS = self._ATTRSPEC
        
        if issubclass(baseType, str):
            bts = self[:]
        else:
            bts = baseType(self)
        
        if not AS:
            return "%s(%r)" % (self.__class__.__name__, bts)
        
        d = self.__dict__
        t = tuple(x for k in AS for x in (k, d[k]))
        sv = [
            self.__class__.__name__,
            '(',
            repr(bts),
            ', ',
            (', '.join(["%s=%r"] * len(AS))) % t,
            ')']
        
        return ''.join(sv)
    
    SM_repr_closure.__doc__ = SM_repr.__doc__
    return SM_repr_closure

def SM_str(baseKind):
    """
    Return a nicely readable string representation of the object.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict1,
    ...         enum_annotatevalue = True)
    >>> print(Test(15))
    What? (15)
    >>> print(Test(-1))
    Ahh... (-1)
    
    >>> class Bottom(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict1)
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(enum_stringsdict = _testDict2)
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': (lambda: Bottom(15)),
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True,
    ...         'attr_strneedsparens': True}}
    ...     attrSorted = ('pair', 'n')
    >>> print(Bottom(8, first=20, second=25))
    What?, First Glyph = 20, Second Glyph = 25
    >>> print(Top(2, n=40, pair=Bottom(-1, first=20, second=25)))
    Green, Glyph Pair = (Ahh..., First Glyph = 20, Second Glyph = 25), Count = 40
    """
    
    def SM_str_closure(self):
        ES = self._ENUMSPEC
        AS = self._ATTRSPEC
        default = ES.get('enum_stringsdefault', None)
        
        if issubclass(baseKind, str):
            key = self
        else:
            key = baseKind(self)
        
        if default is None:
            r = ES['enum_stringsdict'][key]
        else:
            r = ES['enum_stringsdict'].get(key, default)
        
        if ES.get('enum_annotatevalue', False):
            r = "%s (%s)" % (r, baseKind(self))
        
        if not AS:
            return r
        
        sv = [r] + attrhelper.SM_str(self, self.getNamer())
        return ', '.join(sv)
    
    SM_str_closure.__doc__ = SM_str.__doc__
    return SM_str_closure

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    'coalesced': M_coalesced,
    'compacted': M_compacted,
    'cvtsRenumbered': M_cvtsRenumbered,
    'fdefsRenumbered': M_fdefsRenumbered,
    'gatheredInputGlyphs': M_gatheredInputGlyphs,
    'gatheredLivingDeltas': M_gatheredLivingDeltas,
    'gatheredMaxContext': M_gatheredMaxContext,
    'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
    'gatheredRefs': M_gatheredRefs,
    'getSortedAttrNames': classmethod(lambda x: x._ATTRSORT),
    'glyphsRenumbered': M_glyphsRenumbered,
    'hasCycles': M_hasCycles,
    'merged': M_merged,
    'namesRenumbered': M_namesRenumbered,
    'pcsRenumbered': M_pcsRenumbered,
    'pointsRenumbered': M_pointsRenumbered,
    'recalculated': M_recalculated,
    'scaled': M_scaled,
    'storageRenumbered': M_storageRenumbered,
    'transformed': M_transformed
    }

_methodDictAttr = {
    '__init__': SM_init
    }

_methodDictNeedType = {
    '__repr__': SM_repr,
    '__str__': SM_str,
    'asImmutable': M_asImmutable,
    'isValid': M_isValid,
    'pprint': M_pprint,
    'pprint_changes': M_pprintChanges
    }

_methodDictNeedTypeAttr = {
    '__new__': SM_new
    }

def _addMethods(cd, bases):
    AS = cd['_ATTRSPEC']
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
    baseType = (int if issubclass(bases[0], int) else float)
    stdClasses = (int, float)
    
    for mDict, needKind in ((_methodDict, False), (_methodDictNeedType, True)):
        for mKey, m in mDict.items():
            if mKey in cd:
                continue
            
            for c in reversed(bases):  # do nearest ancestor first
                if hasattr(c, mKey):
                    cand = getattr(c, mKey)
                    
                    if any(getattr(d, mKey, None) is cand for d in stdClasses):
                        continue
                    
                    cd[mKey] = cand
                    break
            
            else:
                cd[mKey] = (m(baseType) if needKind else m)
    
    # Only include __eq__ if needed
    if needEqNe:
        if '__eq__' not in cd:
            cd['__eq__'] = SM_eq(baseType)

    # Only include __bool__ if needed
    if needBool:
        if '__bool__' not in cd:
            cd['__bool__'] = SM_bool(baseType)
    
    if AS:
        t = ((_methodDictAttr, False), (_methodDictNeedTypeAttr, True))
        
        for mDict, needKind in t:
            for mKey, m in mDict.items():
                if mKey in cd:
                    continue
                
                for c in reversed(bases):  # do nearest ancestor first
                    if hasattr(c, mKey):
                        cand = getattr(c, mKey)
                        
                        if any(getattr(d, mKey, None) is cand for d in stdClasses):
                            continue
                        
                        cd[mKey] = cand
                        break
                
                else:
                    cd[mKey] = (m(baseType) if needKind else m)
    
    # This is a Python 3 thing
    if '__hash__' not in cd:
        cd['__hash__'] = baseType.__hash__

def _validateEnumSpec(d):
    """
    Make sure only known keys are included in the enumSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> d = {'enum_stringsdict': {1: "X"}, 'enum_pprintlabel': "Fred"}
    >>> _validateEnumSpec(d)
    >>> d = {'enum_stringsdict': {1: "X"}, 'enum_pprintlab': "Fred"}
    >>> _validateEnumSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown enumSpec keys: ['enum_pprintlab']
    """
    
    unknownKeys = set(d) - validEnumSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown enumSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'enum_stringsdict' not in d:
        raise ValueError("Required enum_stringsdict not present!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for enum-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already a Protocol
    class, the ``enumSpec`` and ``attrSpec`` will define additions to the
    original. In this case, if an ``attrSorted`` is provided, it will be used
    for the combined attributes (original and newly-added); otherwise the new
    attributes will be added to the end of the ``attrSorted`` list.
    
    >>> class L1(int, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_annotatevalue = True)
    ...     attrSpec = {'attr1': {}}
    >>> v1 = L1(2, attr1=10)
    >>> print(v1)
    Green (2), attr1 = 10
    
    >>> class L2(L1, metaclass=FontDataMetaclass):
    ...     enumSpec = dict(
    ...         enum_stringsdict = _testDict2,
    ...         enum_annotatevalue = False)
    ...     attrSpec = {'attr2': {}}
    ...     attrSorted = ('attr2', 'attr1')
    >>> v2 = L2(2, attr1=10, attr2=9)
    >>> print(v2)
    Green, attr2 = 9, attr1 = 10
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_ENUMSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            ES = c._ENUMSPEC.copy()
            ES.update(classdict.pop('enumSpec', {}))
            classdict['_ENUMSPEC'] = classdict['_MAIN_SPEC'] = ES
            _validateEnumSpec(ES)
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
        
        else:
            d = classdict['_ENUMSPEC'] = classdict.pop('enumSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateEnumSpec(d)
            d = classdict['_ATTRSPEC'] = classdict.pop('attrSpec', {})
            classdict['_EXTRA_SPEC'] = d
            
            classdict['_ATTRSORT'] = classdict.pop(
              'attrSorted',
              tuple(sorted(d)))
            
            attrhelper.validateAttrSpec(d)
        
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
    import collections
    from fontio3 import utilities
    from fontio3.fontdata import seqmeta
    from fontio3.fontmath import matrix
    from fontio3.utilities import namer
    
    _testDict1 = collections.defaultdict(lambda: "What?", {-1: "Ahh..."})
    _testDict2 = collections.defaultdict(lambda: "What?",
      {0: "No value", 1: "Red", 2: "Green", 3: "Blue"})
    _testDict3 = collections.defaultdict(lambda: "What?", {0.5: "Half", 0.75: "Three-quarters"})

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
