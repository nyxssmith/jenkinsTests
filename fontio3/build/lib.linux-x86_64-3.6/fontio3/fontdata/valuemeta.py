#
# valuemeta.py -- Support for single values, with optional extra attributes
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for fontdata numeric values. Clients wishing to add fontdata
capabilities to their numeric classes should specify FontDataMetaclass as the
metaclass. The following class attributes are used to control the various
behaviors and attributes of instances of the class:

``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``valueSpec``
    A dict of specification information for the value, where the keys and their
    associated values are defined in the following list. The listed defaults
    apply if the specified key is not present in the ``valueSpec``.
        
    ``value_asimmutablecoercetobasetype``
        If True, then the value's ``asImmutable()`` result will always be of
        the actual base type.
        
        Default is False.
    
    ``value_inputcheckfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate.
        
        There is no default.
    
    ``value_iscvtindex``
        If True, the value is a CVT index, and is subject to being renumbered
        if ``cvtsRenumbered()`` is called.
        
        Default is False.
    
    ``value_isfdefindex``
        If True, the value is an FDEF index, and is subject to being renumbered
        if ``fdefsRenumbered()`` is called.
        
        Default is False.
    
    ``value_isglyphindex``
        If True, the value is to be treated as a glyph index, which means, for
        example, that it participates in ``glyphsRenumbered()`` calls.
        
        Default is False.
    
    ``value_isnameindex``
        If True, the value is to be treated as a ``'name'`` table index, which
        means, for example, that it participates in ``namesRenumbered()`` calls.
        
        Default is False.
    
    ``value_isoutputglyph``
        If True, then the value is treated as an output glyph. This means it
        will not be added to the accumulating set by a
        ``gatheredInputGlyphs()`` call, and it will be added by a
        ``gatheredOutputGlyphs()`` call (in both cases, of course, assuming
        ``value_isglyphindex`` is set; if that is not the case, the value will
        not be added, even if this flag is True).
        
        Default is False.
    
    ``value_ispc``
        If True, then the value is treated as a Program Counter value and is
        subject to modification via the ``pcsRenumbered()`` call.
        
        Default is False.
    
    ``value_ispointindex``
        If True, the value is to be treated as the index of a point in a glyph
        definition, which means the value participates in
        ``pointsRenumbered()`` calls.
        
        Default is False.
    
    ``value_isstorageindex``
        If True, the value is a storage index, and is subject to being
        renumbered if ``storageRenumbered()`` is called.
        
        Default is False.
    
    ``value_mergecheckequality``
        If True, and a ``merged()`` call is attempted which would change the
        value, then a ``ValueError`` is raised.
        
        Default is False.
    
    ``value_pprintlabel``
        This is the string that prefaces the value in ``pprint()`` and
        ``pprint_changes()`` output. Note that it does not preface the value in
        ``__str__()`` or ``__repr__()`` output.
        
        Default is The string "Value".
    
    ``value_prevalidatedglyphset``
        A set or frozenset containing glyph indices which are to be considered
        valid, even though they exceed the font's glyph count. This is useful
        for passing ``0xFFFF`` values through validation for state tables,
        where that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``value_python3rounding``
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
        Default is False.
    
    ``value_recalculatefunc``
        If specified, this should be a function taking at least one argument,
        the object. Additional keyword arguments (for example, ``editor``)
        conforming to the ``recalculated()`` protocol may be specified.

        The function must return a pair: the first value is True or False,
        depending on whether the recalculated object's value actually changed.
        The second value is the new recalculated value to be used. Note this
        may be a simple value, or another object of the same type.
        
        There is no default.
    
    ``value_representsx``
        If True, the value is an x-coordinate. This information is used during
        scaling, if the client specifies one of the ``scaleOnlyInX`` or
        ``scaleOnlyInY`` keyword arguments to the ``scaled()`` call.
        
        Default is False.
    
    ``value_representsy``
        If True, the value is a y-coordinate. This information is used during
        scaling, if the client specifies one of the ``scaleOnlyInX`` or
        ``scaleOnlyInY`` keyword arguments to the ``scaled()`` call.
        
        Default is False.
    
    ``value_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``value_scales``
        If True then a non-``None`` value will be scaled by the ``scaled()``
        method, with the results rounded to the nearest integral value (with .5
        cases controlled by ``value_python3rounding``); if this is not desired,
        the client should instead specify the ``value_scalesnoround`` flag.
        
        Default is False.
    
    ``value_scalesnoround``
        If True then a non-``None`` value will be scaled by the ``scaled()``
        method. No rounding will be done on the result; if rounding to integral
        values is desired, use the ``value_scales`` flag instead.
        
        Default is False.
    
    ``value_transformcounterpartfunc``
        If the value represents one of the two coordinates of a two-dimensional
        point, then this function can be used to provide the value of the other
        coordinate for purposes of the ``transformed()`` call. The function
        takes a single positional argument (the value itself), and also takes
        keyword arguments. Note this function can be used to provide a simple
        constant nonzero value (there's no need for the zero case, since that's
        presumed in the absence of other specifications).

        Note that whether the transformed value is rounded to an integer is
        controlled by ``value_transformnoround`` (q.v.)
        
        There is no default.
    
    ``value_transformnoround``
        If True then a non-``None`` value will not be rounded to the nearest
        integral value after a ``transformed()`` call.

        Note the absence of an "``value_transforms``" flag. Calls to the
        ``transformed()`` method will only affect a non-``None`` value if one
        or more of the ``value_representsx``, ``value_representsy``, or
        ``value_transformcounterpartfunc`` flags are set.
        
        Default is False.
    
    ``value_usenamerforstr``
        If True, and ``value_isglyphindex`` is True, and a
        :py:class:`~fontio3.utilities.namer.Namer` is available (either via the
        ``setNamer()`` call or a keyword argument), then that ``Namer`` will be
        used for generating the strings produced via the ``__str__()`` special
        method.

        If a ``Namer`` has been set then it will be used in ``pprint()`` and
        ``pprint_changes()``, unless one is explicitly provided, in which case
        that one will be used instead.
        
        Default is False.
    
    ``value_validatecode_namenotintable``
        The code to be used for logging when a name index is not actually
        present in the ``'name'`` table.
        
        Default is ``'G0042'``.
    
    ``value_validatecode_negativecvt``
        The code to be used for logging when a negative value is used for a CVT
        index.
        
        Default is ``'G0028'``.
    
    ``value_validatecode_negativeglyph``
        The code to be used for logging when a negative value is used for a
        glyph index.
        
        Default is ``'G0004'``.
    
    ``value_validatecode_negativeinteger``
        The code to be used for logging when a negative value is used for a
        non-negative item (like a PC or a point index).
        
        Default is ``'G0008'``.
    
    ``value_validatecode_nocvt``
        The code to be used for logging when a CVT index is used but the font
        has no ``'cvt '`` table.
        
        Default is ``'G0030'``.
    
    ``value_validatecode_nonintegercvt``
        The code to be used for logging when a non-integer value is used for a
        CVT index.
        
        Default is ``'G0027'``.
    
    ``value_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is used for a
        glyph index.
        
        Default is ``'G0003'``.
    
    ``value_validatecode_nonintegralinteger``
        The code to be used for logging when a non-integer value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0007'``.
    
    ``value_validatecode_nonnumericcvt``
        The code to be used for logging when a non-numeric value is used for a
        CVT index.
        
        Default is ``'G0026'``.
    
    ``value_validatecode_nonnumericglyph``
        The code to be used for logging when a non-numeric value is used for a
        glyph index.
        
        Default is ``'G0002'``.
    
    ``value_validatecode_nonnumericinteger``
        The code to be used for logging when a non-numeric value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0006'``.
    
    ``value_validatecode_toolargecvt``
        The code to be used for logging when a CVT index is used that is
        greater than or equal to the number of CVTs in the font.
        
        Default is ``'G0029'``.
    
    ``value_validatecode_toolargeglyph``
        The code to be used for logging when a glyph index is used that is
        greater than or equal to the number of glyphs in the font.
        
        Default is ``'G0005'``.
    
    ``value_validatefunc``
        A function taking one positional argument, the value, and an arbitrary
        number of keyword arguments. The function returns True if the object is
        valid (that is, if no errors are present).
        
        There is no default.
    
    ``value_validatefunc_partial``
        A function taking one positional argument, the value, and an arbitrary
        number of keyword arguments. The function returns True if the object is
        valid (that is, if no errors are present). Standard tests (like glyph
        too large) do not need to be included in this function, unlike the
        ``value_validatefunc``.
        
        There is no default.
    
    ``value_wisdom``
        A string encompassing a sensible description of the object as a whole,
        including how it is used.
        
        There is, alas, no default for wisdom.
"""

# System imports
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, invariants
from fontio3.utilities import pp, valassist

# -----------------------------------------------------------------------------

#
# Constants
#

validValueSpecKeys = frozenset([
  'value_asimmutablecoercetobasetype',
  'value_inputcheckfunc',
  'value_iscvtindex',
  'value_isfdefindex',
  'value_isglyphindex',
  'value_isnameindex',
  'value_isoutputglyph',
  'value_ispc',
  'value_ispointindex',
  'value_isstorageindex',
  'value_mergecheckequality',
  'value_pprintlabel',
  'value_prevalidatedglyphset',
  'value_python3rounding',
  'value_recalculatefunc',
  'value_representsx',
  'value_representsy',
  'value_roundfunc',
  'value_scales',
  'value_scalesnoround',
  'value_transformcounterpartfunc',
  'value_transformnoround',
  'value_usenamerforstr',
  'value_validatecode_badfixedlength',
  'value_validatecode_namenotintable',
  'value_validatecode_negativecvt',
  'value_validatecode_negativeglyph',
  'value_validatecode_negativeinteger',
  'value_validatecode_nocvt',
  'value_validatecode_nonintegercvt',
  'value_validatecode_nonintegerglyph',
  'value_validatecode_nonintegralinteger',
  'value_validatecode_nonnumericcvt',
  'value_validatecode_nonnumericglyph',
  'value_validatecode_nonnumericinteger',
  'value_validatecode_toolargecvt',
  'value_validatecode_toolargeglyph',
  'value_validatefunc',
  'value_validatefunc_partial',
  'value_wisdom'])

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
    
    >>> class Test1(int, metaclass=FontDataMetaclass): pass
    >>> t1 = Test1(-1)
    >>> t1.asImmutable()
    ('Test1', Test1(-1))
    
    The value_asimmutablecoercetobasetype flag forces coercion to the base
    type:
    
    >>> class Test1C(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(value_asimmutablecoercetobasetype = True)
    
    >>> print(Test1C(-1).asImmutable())
    ('Test1C', -1)
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_asimmutabledeep = True),
    ...         b = dict(attr_asimmutablefunc = tuple),
    ...         c = dict())
    >>> t2 = Test2(4, a=t1, b=[1, 2, 3], c='xxx')
    >>> t2.asImmutable()
    ('Test2', 4, ('a', ('Test1', Test1(-1))), ('b', (1, 2, 3)), ('c', 'xxx'))
    
    Note that c must already be immutable; if it isn't, an error is raised:
    
    >>> t2.c = [4, 5]
    >>> t2.asImmutable()
    Traceback (most recent call last):
      ...
    TypeError: unhashable type: 'list'
    """
    
    def M_asImmutable_closure(self, **kwArgs):
        AS = self._ATTRSPEC
        coerce = self._VALSPEC.get('value_asimmutablecoercetobasetype', False)
        bt = (baseType(self) if (AS or coerce) else self)
        
        r = (type(self).__name__, bt)
        
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...   valueSpec = dict(
    ...     value_inputcheckfunc = (lambda x, **k: 0 <= x < 100))
    ...   attrSpec = dict(
    ...     a = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: x in {2, 19, 81})))
    >>> v = Test1(39, a=81)
    >>> v.checkInput(50)
    True
    >>> v.checkInput(150)
    False
    >>> v.checkInput(2, attrName='a')
    True
    >>> v.checkInput(3, attrName='a')
    False
    """
    
    # We short-circuit to the attribute check if there is an 'attrName'
    # kwArg specified.
    
    if kwArgs.get('attrName', ''):
        return attrhelper.M_checkInput(
          self._ATTRSPEC,
          self.__dict__,
          valueToCheck,
          **kwArgs)
    
    f = self._VALSPEC.get('value_inputcheckfunc', None)
    
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
    
    Numbers are already as compact as possible, so this method only affects
    attributes.
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_compactremovesfalses': True}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_followsprotocol': True}}
    >>> t = Top(15, a=Bottom([2, False, 0, None, [], 3]))
    >>> print(t)
    15, a = (2, False, 0, None, [], 3)
    >>> print(t.compacted())
    15, a = (2, 3)
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_iscvtindex = True)
    
    >>> print(Test1(12).cvtsRenumbered(cvtDelta=9))
    21
    
    >>> print(Test1(12).cvtsRenumbered(oldToNew={12:20}))
    20
    >>> print(Test1(12).cvtsRenumbered(oldToNew={25:35}))
    12
    >>> print(Test1(12).cvtsRenumbered(oldToNew={25:35}, keepMissing=False))
    Traceback (most recent call last):
      ...
    ValueError: Cannot renumber CVT index, and keepMissing is False!
    
    >>> f = (lambda n, **k: n + (200 if n % 5 else 0))
    >>> print(Test1(12).cvtsRenumbered(cvtMappingFunc=f))
    212
    >>> print(Test1(15).cvtsRenumbered(cvtMappingFunc=f))
    15
    """
    
    if self._VALSPEC.get('value_iscvtindex', False):
        cvtMappingFunc = kwArgs.get('cvtMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        cvtDelta = kwArgs.get('cvtDelta', None)
        
        if cvtMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            cvtMappingFunc = (
              lambda x, **k:
              oldToNew.get(x, (x if keepMissing else None)))
        
        elif cvtDelta is not None:
            cvtMappingFunc = lambda x,**k: x + cvtDelta
        
        else:
            cvtMappingFunc = lambda x,**k: x
        
        vNew = cvtMappingFunc(int(self), **kwArgs)
        
        if vNew is None:
            raise ValueError(
              "Cannot renumber CVT index, and keepMissing is False!")
    
    else:
        vNew = self
    
    # Now do attributes
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
        This must be set True for classes derived from this metaclass, or a
        ``ValueError`` will be raised.

    ``oldToNew``
        A dict mapping old FDEF indices to new ones. Note that it's OK for this
        dict to not map every single old FDEF index; what happens if this
        occurs is specified by the ``keepMissing`` flag.

    .. note::
  
      You should choose exactly *one* of ``fdefMappingFunc`` or ``oldToNew``.
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_isfdefindex = True)
    
    >>> print(Test1(12).fdefsRenumbered(oldToNew={12:20}))
    20
    >>> print(Test1(12).fdefsRenumbered(oldToNew={25:35}))
    12
    >>> print(Test1(12).fdefsRenumbered(oldToNew={25:35}, keepMissing=False))
    Traceback (most recent call last):
      ...
    ValueError: Cannot renumber FDEF index, and keepMissing is False!
    
    >>> f = (lambda n, **k: n + (200 if n % 5 else 0))
    >>> print(Test1(12).fdefsRenumbered(fdefMappingFunc=f))
    212
    >>> print(Test1(15).fdefsRenumbered(fdefMappingFunc=f))
    15
    """
    
    if self._VALSPEC.get('value_isfdefindex', False):
        fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        
        if fdefMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            fdefMappingFunc = (
              lambda x, **k:
              oldToNew.get(x, (x if keepMissing else None)))
        
        else:
            fdefMappingFunc = lambda x,**k: x
        
        vNew = fdefMappingFunc(int(self), **kwArgs)
        
        if vNew is None:
            raise ValueError(
              "Cannot renumber FDEF index, and keepMissing is False!")
    
    else:
        vNew = self
    
    # Now do attributes
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
    
    >>> class TopIn(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_isglyphindex': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(TopIn(10, a=bIn, b=11, c=bOut).gatheredInputGlyphs())
    [1, 2, 3, 10, 11]
    
    >>> class TopOut(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {
    ...       'value_isglyphindex': True,
    ...       'value_isoutputglyph': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(TopOut(10, a=bIn, b=11, c=bOut).gatheredInputGlyphs())
    [1, 2, 3, 11]
    """
    
    VS = self._VALSPEC
    
    if (
     VS.get('value_isglyphindex', False) and
     (not VS.get('value_isoutputglyph', False))):
        
        r = set([int(self)])  # glyph indices are always ints
    
    else:
        r = set()
    
    rAttr = attrhelper.M_gatheredInputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return r | rAttr

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
    
    >>> class Test(float, metaclass=FontDataMetaclass):
    ...   attrSpec = dict(
    ...     a = dict(attr_islivingdeltas = True),
    ...     b = dict())
    >>> obj = Test(-1.5, a=4, b=76)
    >>> sorted(obj.gatheredLivingDeltas())
    [4]
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
    
    >>> class BottomIsGlyph(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_isglyphindex': True}
    >>> class BottomIsNotGlyph(int, metaclass=FontDataMetaclass): pass
    >>> BottomIsGlyph(10).gatheredMaxContext()
    1
    >>> BottomIsNotGlyph(10).gatheredMaxContext()
    0
    
    >>> class Top(float, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top(-2.75, x = [8, 1, 4], y=BottomIsGlyph(10)).gatheredMaxContext()
    8
    >>> Top(-2.75, x = [0, 1, 4], y=BottomIsGlyph(10)).gatheredMaxContext()
    1
    """
    
    VS = self._VALSPEC
    mc = (1 if VS.get('value_isglyphindex', False) else 0)
    
    return max(
      mc,
      attrhelper.M_gatheredMaxContext(self._ATTRSPEC, self.__dict__, **kwArgs))

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
    
    >>> class TopIn(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_isglyphindex': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(TopIn(10, a=bIn, b=11, c=bOut).gatheredOutputGlyphs())
    [4, 5, 6]
    
    >>> class TopOut(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {
    ...       'value_isglyphindex': True,
    ...       'value_isoutputglyph': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_renumberdirect = True),
    ...         c = dict(attr_followsprotocol = True))
    >>> sorted(TopOut(10, a=bIn, b=11, c=bOut).gatheredOutputGlyphs())
    [4, 5, 6, 10]
    """
    
    VS = self._VALSPEC
    
    if (
      VS.get('value_isglyphindex', False) and
      VS.get('value_isoutputglyph', False)):
        
        r = set([int(self)])  # glyph indices are always ints
    
    else:
        r = set()
    
    rAttr = attrhelper.M_gatheredOutputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return r | rAttr

def M_gatheredRefs(self, **kwArgs):
    """
    Return a dict with ``Lookup`` objects contained within ``self``.

    :param kwArgs: Optional keyword arguments (there are none here)
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
    
    >>> class Test(float, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_followsprotocol = True),
    ...         b = dict(attr_islookup = True))
    >>> look1 = object()
    >>> look2 = object()
    >>> t = Test(1.5, a=Test(-0.75, a=None, b=look1), b=look2)
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
    ...     valueSpec = {'value_isglyphindex': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(10, a=11, b=Test(12, a=13, b=None))
    >>> print(t)
    10, a = 11, b = (12, a = 13, b = (None))
    >>> print(t.glyphsRenumbered({10: 40, 11: 45, 12: 50, 13: 55}))
    40, a = 45, b = (50, a = 55, b = (None))
    >>> print(t.glyphsRenumbered({10: 40, 11: 45, 12: 50}, keepMissing=False))
    40, a = 45, b = (50, a = None, b = (None))
    >>> print(t.glyphsRenumbered({11: 45, 12: 50}, keepMissing=False))
    Traceback (most recent call last):
      ...
    ValueError: Cannot renumber glyph, and keepMissing is False!
    """
    
    vNew = self
    VS = self._VALSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    
    if VS.get('value_isglyphindex', False):
        intSelf = int(self)
        
        if intSelf in oldToNew:  # can't use "self in oldToNew"; hash issues
            vNew = oldToNew[intSelf]
        
        elif keepMissing:
            vNew = intSelf
        
        else:
            raise ValueError(
              "Cannot renumber glyph, and keepMissing is False!")
    
    # Now do attributes
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_isglyphindex': True}
    ...     attrSpec = {'a': {'attr_renumberdirect': True}}
    ...     attrSorted = ()
    
    >>> logger = utilities.makeDoctestLogger("Test1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> Test1(-50, a=5).isValid(logger=logger, editor=e)
    Test1 - ERROR - The glyph index -50 cannot be used in an unsigned field.
    False
    
    >>> Test1(500, a=-1).isValid(logger=logger, fontGlyphCount=200, editor=e)
    Test1 - ERROR - Glyph index 500 too large.
    Test1.a - ERROR - The glyph index -1 cannot be used in an unsigned field.
    False
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_ispointindex': True}
    
    >>> logger = utilities.makeDoctestLogger("Test2")
    >>> Test2(2.5).isValid(logger=logger, editor=e)
    Test2 - ERROR - The point index 2.5 is not an integer.
    False
    
    >>> def valFunc(obj, **kwArgs):
    ...     logger = kwArgs['logger']
    ...     if (obj % 2) == 0:
    ...         logger.error(('Vxxxx', (obj,), "Value %s is not odd."))
    ...         return False
    ...     return True
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_validatefunc': valFunc}
    
    >>> logger = utilities.makeDoctestLogger("Test3+4")
    >>> Test3(4).isValid(logger=logger, editor=e)
    Test3+4 - ERROR - Value 4 is not odd.
    False
    """
    
    VS = self._VALSPEC
    r = True
    fontGlyphCount = kwArgs.get('fontGlyphCount')
    
    if 'editor' in kwArgs:
        editor = kwArgs['editor']
        hasMaxp = (editor is not None) and editor.reallyHas(b'maxp')
        
        if hasMaxp:
            if fontGlyphCount is None:
                fontGlyphCount = editor.maxp.numGlyphs
            
            if hasattr(editor.maxp, 'maxStorage'):
                maxStorage = editor.maxp.maxStorage
            else:
                maxStorage = 0x10000
            
        else:
            if fontGlyphCount is None:
                fontGlyphCount = 0x10000
            
            maxStorage = 0x10000
        
        if (editor is not None) and editor.reallyHas(b'name'):
            namesInTable = {x[-1] for x in editor.name}
        else:
            namesInTable = set()
    
    else:
        editor = None
        maxStorage = 0x10000
        namesInTable = set()
        
        if fontGlyphCount is None:
            fontGlyphCount = 0x10000
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        s = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(s)
    
    f = VS.get('value_validatefunc', None)
    
    if f is not None:
        r = f(self, logger=logger, **kwArgs)
    
    else:
        intSelf = int(self)
        fp = VS.get('value_validatefunc_partial', None)
        
        if fp is not None:
            r = fp(self, logger=logger, **kwArgs)
        
        if (
          VS.get('value_isglyphindex', False) or
          VS.get('value_isoutputglyph', False)):
            
            pvs = VS.get('value_prevalidatedglyphset', set())
            
            if not valassist.isNumber_integer_unsigned(
              float(self),
              numBits = 16,
              label = "glyph index",
              logger = logger):
              
                r = False
            
            elif (intSelf not in pvs) and (intSelf >= fontGlyphCount):
                logger.error((
                  VS.get('value_validatecode_toolargeglyph', 'G0005'),
                  (intSelf,),
                  "Glyph index %d too large."))
                
                r = False
        
        elif VS.get('value_isnameindex', False):
            if not valassist.isFormat_H(
              float(self),
              label = "name table index",
              logger = logger):
              
                r = False
            
            elif intSelf not in namesInTable:
                logger.error((
                  VS.get('value_validatecode_namenotintable', 'G0042'),
                  (intSelf,),
                  "Name table index %d not present in 'name' table."))
                
                r = False
        
        elif VS.get('value_iscvtindex', False):
            if not valassist.isNumber_integer_unsigned(
              float(self),
              numBits = 16,
              label = "CVT index",
              logger = logger):
              
                r = False
            
            elif editor is not None:
                if b'cvt ' not in editor:
                    logger.error((
                      VS.get('value_validatecode_nocvt', 'G0030'),
                      (int(self),),
                      "CVT Index %d is being used, but the font "
                      "has no Control Value Table."))
                    
                    r = False
                
                elif intSelf >= len(editor[b'cvt ']):
                    logger.error((
                      VS.get('value_validatecode_toolargecvt', 'G0029'),
                      (intSelf,),
                      "CVT index %d is not defined."))
                    
                    r = False
        
        elif (
          VS.get('value_ispc', False) or
          VS.get('value_ispointindex', False)):
            
            if VS.get('value_ispc', False):
                doc = "program counter"
            else:
                doc = "point index"
            
            if not valassist.isNumber_integer_unsigned(
              float(self),
              numBits = 16,
              label = doc,
              logger = logger):
              
                r = False
        
        elif VS.get('value_isstorageindex', False):
            if not valassist.isNumber_integer_unsigned(
              float(self),
              numBits = 16,
              label = "storage index",
              logger = logger):
              
                r = False
            
            elif intSelf > maxStorage:
                logger.error((
                  'E6047',
                  (intSelf, maxStorage),
                  "The storage index %d is greater than the "
                  "font's defined maximum of %d."))
                
                r = False
    
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
    
    The following ``kwArgs`` are supported:
    
    ``conflictPreferOther``
        True if when there is a key conflict the caller wishes the contents in
        ``other`` to have precedence; False if ``self`` should prevail. Default
        is True.
        
    ``replaceWhole``
        True if any keys in other matching keys in ``self`` will cause the
        entire replacement of those values; no deep merging will occur for
        those values. Default is False.
    
    >>> class Test1(int, metaclass=FontDataMetaclass): pass
    >>> print(Test1(15).merged(Test1(10)))  # other is preferred by default
    10
    >>> print(Test1(15).merged(Test1(10), conflictPreferOther=False))
    15
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_mergecheckequality': True}
    >>> print(Test2(1.5).merged(Test2(1.5)))
    1.5
    >>> print(Test2(1.5).merged(Test2(2.75)))
    Traceback (most recent call last):
      ...
    ValueError: Attempt to merge unequal values!
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someTuple': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someTuple', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([5, 2])
    >>> obj1 = Top(6, someNumber=4, someTuple=b1)
    >>> obj2 = Top(15, someNumber=8, someTuple=b2)
    >>> print(obj1.merged(obj2))
    15, someTuple = (1, 2, 3, 5), someNumber = 8
    >>> print(obj1.merged(obj2, conflictPreferOther=False))
    6, someTuple = (1, 2, 3, 5), someNumber = 4
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {
    ...         'attr_initfunc': int,
    ...         'attr_mergefunc': (lambda a,b,**k: (b < a, min(a, b)))}}
    >>> x1 = Test3(-1, a=10)
    >>> x2 = Test3(-2, a=5)
    >>> print(x1)
    -1, a = 10
    >>> print(x1.merged(x2))
    -2, a = 5
    """
    
    prefOther = kwArgs.get('conflictPreferOther', True)
    
    if self != other:
        if self._VALSPEC.get('value_mergecheckequality', False):
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
        simply be kept unmodified. If False, a ``ValueError`` will be raised.
    """
    
    vNew = self
    VS = self._VALSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    
    if VS.get('value_isnameindex', False):
        intSelf = int(self)
        
        if intSelf in oldToNew:  # can't use "self in oldToNew"; hash issues
            vNew = oldToNew[intSelf]
        
        elif keepMissing:
            vNew = intSelf
        
        else:
            raise ValueError(
              "Cannot renumber glyph, and keepMissing is False!")
    
    # Now do attributes
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
    
    >>> class Bottom(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(value_ispc = True)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> print(Bottom(5).pcsRenumbered(mapData, infoString="testcode"))
    5
    >>> print(Bottom(12).pcsRenumbered(mapData, infoString="testcode"))
    14
    >>> print(Bottom(50).pcsRenumbered(mapData, infoString="testcode"))
    53
    >>> print(Bottom(100).pcsRenumbered(mapData, infoString="testcode"))
    106
    """
    
    vNew = self
    
    if self._VALSPEC.get('value_ispc', False):
        
        # example of mapData: [(12, 2), (40, 3), (67, 6)]
        # note obj and the [0] elements of mapData are in
        # original, unchanged space
        
        delta = 0
        it = mapData.get(kwArgs.get('infoString', None), [])
        
        for threshold, newDelta in it:
            if vNew < threshold:
                break
            
            delta = newDelta
        
        vNew += delta
    
    # Now do attributes
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
    ...     valueSpec = {'value_ispointindex': True}
    ...     attrSpec = dict(
    ...         a = dict(attr_renumberpointsdirect = True),
    ...         b = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> t = Test(10, a=15, b=Test(20, a=25, b=None))
    >>> print(t)
    10, a = 15, b = (20, a = 25, b = (None))
    >>> myMap = {440: {10: 12, 12: 15, 15: 10}, 444: {10: 25, 25: 10}}
    >>> print(t.pointsRenumbered(myMap, glyphIndex=440))
    12, a = 10, b = (20, a = 25, b = (None))
    >>> print(t.pointsRenumbered(myMap, glyphIndex=444))
    25, a = 15, b = (20, a = 10, b = (None))
    """
    
    vNew = self
    
    if self._VALSPEC.get('value_ispointindex', False):
        glyphIndex = kwArgs.get('glyphIndex', None)
        
        if glyphIndex is not None:
            thisMap = mapData.get(glyphIndex, {})
            oldValue = int(self)
            
            if oldValue in thisMap:
                newValue = thisMap[oldValue]
                
                if newValue != oldValue:
                    vNew = newValue
    
    # Now do attributes
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
    
    >>> class Test0(float, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_pprintlabel': "Factor"}
    >>> Test0(3.75).pprint()
    Factor: 3.75
    
    >>> class Bottom(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_pprintlabel': "The bottom value"}
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
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_pprintlabel': "The top value"}
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': (lambda: Bottom(5)),
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> t = Top(-200)
    >>> nm = namer.testingNamer()
    >>> t.pprint(label="The Top object", namer=nm)
    The Top object:
      The top value: -200
      Glyph Pair:
        The bottom value: 5
        First Glyph: xyz1
        Second Glyph: xyz1
      Count: 1
    >>> t.pair.second = 19
    >>> t.n += 4
    >>> t.pprint(label="The changed object", namer=nm)
    The changed object:
      The top value: -200
      Glyph Pair:
        The bottom value: 5
        First Glyph: xyz1
        Second Glyph: xyz20
      Count: 5
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': False}}
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': True}}
    >>> Test1(5).pprint()
    Value: 5
    s: fred
    >>> Test2(5).pprint()
    Value: 5
    s: 'fred'
    
    >>> class Test3(float, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> Test3(1.75).pprint(label="Note x is suppressed")
    Note x is suppressed:
      Value: 1.75
      y: 5
    >>> Test3(1.75, x=4).pprint(label="No suppression here")
    No suppression here:
      Value: 1.75
      x: 4
      y: 5
    
    >>> class Test4(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_isnameindex = True)
    >>> e = _fakeEditor()
    >>> Test4(303).pprint()
    Value: 303
    
    >>> Test4(303).pprint(editor=e)
    Value: 303 ('Required Ligatures On')
    """
    
    def M_pprint_closure(self, **kwArgs):
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        VS = self._VALSPEC
        nm = kwArgs.get('namer', self.getNamer())
        label = VS.get('value_pprintlabel', "Value")
        
        if (
          VS.get('value_isglyphindex', False) and
          VS.get('value_usenamerforstr', False)):
            
            obj = (nm.bestNameForGlyphIndex(int(self)) if nm else int(self))
        
        elif VS.get('value_isnameindex', False):
            obj = utilities.nameFromKwArgs(int(self), **kwArgs)
        
        else:
            obj = baseType(self)
        
        p.simple(obj, label=label)
        
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass): pass
    >>> Test1(4).pprint_changes(Test1(4))
    >>> Test1(4).pprint_changes(Test1(12))
    Value changed from 12 to 4
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {
    ...       'value_isglyphindex': True,
    ...       'value_usenamerforstr': True}
    >>> Test2(25).pprint_changes(Test2(98), namer=namer.testingNamer())
    Value changed from afii60003 to xyz26
    >>> tnr = namer.testingNamer(remapAFII=True)
    >>> Test2(25).pprint_changes(Test2(98), namer=tnr)
    Value changed from U+0162 to xyz26
    
    >>> class Bottom(int, metaclass=FontDataMetaclass):
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
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': (lambda: Bottom(-1)),
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('pair', 'n')
    >>> t = Top(5)
    >>> nm = namer.testingNamer()
    >>> t.pair.second = 19
    >>> t.n += 4
    >>> t.pprint_changes(Top(2), label="The changes", namer=nm)
    The changes:
      Value changed from 2 to 5
      Glyph Pair:
        Second Glyph changed from xyz1 to xyz20
      Count changed from 1 to 5
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    >>> Test3(9, x=1, y=2, z=3).pprint_changes(Test3(9, x=1, y=2, z=2000))
    """
    
    def M_pprintChanges_closure(self, prior, **kwArgs):
        if self == prior:
            return
        
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        VS = self._VALSPEC
        nm = kwArgs.get('namer', self.getNamer())
        selfValue = baseType(self)
        priorValue = baseType(prior)
        
        if selfValue != priorValue:
            label = VS.get('value_pprintlabel', "Value")
            
            if nm is not None:
                if (
                  VS.get('value_isglyphindex', False) and
                  VS.get('value_usenamerforstr', False)):
                    
                    selfValue = nm.bestNameForGlyphIndex(selfValue)
                    priorValue = nm.bestNameForGlyphIndex(priorValue)
            
            p("%s changed from %s to %s" % (label, priorValue, selfValue))
        
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
    ...     valueSpec = {'value_recalculatefunc': recalc}
    >>> print(Test1(10).recalculated())
    19
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_recalculatefunc = recalc))
    >>> print(Test2(1.5, x=Test1(10), y=-3).recalculated())
    1.5, x = 19, y = -7
    """
    
    VS = self._VALSPEC
    f = VS.get('value_recalculatefunc', None)
    
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_scales': True}
    >>> print(Test1(20).scaled(1.5))
    30
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_scales': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_scaledirect = True))
    >>> class Test3(float, metaclass=FontDataMetaclass):
    ...     valueSpec = {'value_scalesnoround': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_scaledirectnoround = True))
    >>> print(Test2(2.5, x=Test1(20), y=-6).scaled(2.5))
    6.0, x = 50, y = -15
    >>> print(Test3(2.5, x=Test1(20), y=-6).scaled(2.5))
    6.25, x = 50, y = -15.0
    
    >>> class Test3(float, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_representsx = True,
    ...         value_scales = True)
    
    >>> print(Test3(10.0).scaled(0.5))
    5.0
    >>> print(Test3(10.0).scaled(0.5, scaleOnlyInY=True))
    10.0
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    VS = self._VALSPEC
    vNew = self
    
    if VS.get('value_scalesnoround', False):
        roundFunc = (lambda x,**k: x)
    
    elif VS.get('value_scales', False):
        roundFunc = VS.get('value_roundfunc', None)
        
        if roundFunc is None:
            if VS.get('value_python3rounding', False):
                roundFunc = utilities.newRound
            else:
                roundFunc = utilities.oldRound
    
    else:
        roundFunc = None
    
    if roundFunc is not None:
        if VS.get('value_representsx', False) and scaleOnlyInY:
            pass
        elif VS.get('value_representsy', False) and scaleOnlyInX:
            pass
        else:
            vNew = roundFunc(scaleFactor * self)  # no castType (redone below)
    
    # Now do attributes
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
    
    >>> class Test1(int, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_isstorageindex = True)
    
    >>> print(Test1(12).storageRenumbered(storageDelta=9))
    21
    
    >>> print(Test1(12).storageRenumbered(oldToNew={12:20}))
    20
    >>> print(Test1(12).storageRenumbered(oldToNew={25:35}))
    12
    >>> print(Test1(12).storageRenumbered(oldToNew={25:35}, keepMissing=False))
    Traceback (most recent call last):
      ...
    ValueError: Cannot renumber storage index, and keepMissing is False!
    
    >>> f = (lambda n, **k: n + (200 if n % 5 else 0))
    >>> print(Test1(12).storageRenumbered(storageMappingFunc=f))
    212
    >>> print(Test1(15).storageRenumbered(storageMappingFunc=f))
    15
    """
    
    if self._VALSPEC.get('value_isstorageindex', False):
        storageMappingFunc = kwArgs.get('storageMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        storageDelta = kwArgs.get('storageDelta', None)
        
        if storageMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            storageMappingFunc = (
              lambda x, **k:
              oldToNew.get(x, (x if keepMissing else None)))
        
        elif storageDelta is not None:
            storageMappingFunc = lambda x,**k: x + storageDelta
        
        else:
            storageMappingFunc = lambda x,**k: x
        
        vNew = storageMappingFunc(int(self), **kwArgs)
        
        if vNew is None:
            raise ValueError(
              "Cannot renumber storage index, and keepMissing is False!")
    
    else:
        vNew = self
    
    # Now do attributes
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
    ...     valueSpec = dict(
    ...         value_representsx = True)
    >>> print(Test1(-2.5).transformed(m))
    5.0
    
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_python3rounding = True,
    ...         value_representsx = True)
    >>> print(Test2(-2.5).transformed(m))
    4.0
    
    >>> class Test3(float, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_representsx = True,
    ...         value_transformnoround = True)
    >>> print(Test3(-2.5).transformed(m))
    4.5
    
    >>> mRotate = matrix.Matrix.forRotation(-90.0)  # 90 degrees clockwise
    
    >>> class Test4(float, metaclass=FontDataMetaclass):
    ...     valueSpec = dict(
    ...         value_representsx = True,
    ...         value_transformcounterpartfunc = (lambda x, **k: 3.0 - x),
    ...         value_transformnoround = True)
    >>> print(Test4(1.0).transformed(mRotate))  # point will be (1, 2)
    2.0
    >>> print(Test4(-1.0).transformed(mRotate))  # point will be (-1, 4)
    4.0
    """
    
    VS = self._VALSPEC
    vNew = self
    mp = matrixObj.mapPoint
    
    if VS.get('value_transformnoround', False):
        roundFunc = (lambda x: x)
    elif 'value_roundfunc' in VS:
        roundFunc = VS['value_roundfunc']
    elif VS.get('value_python3rounding', False):
        roundFunc = utilities.newRound
    else:
        roundFunc = utilities.oldRound
    
    cptFunc = VS.get('value_transformcounterpartfunc', None)
    
    if cptFunc is not None:
        otherValue = cptFunc(self, **kwArgs)
    else:
        otherValue = 0
    
    if VS.get('value_representsx', False):
        vNew = roundFunc(mp((self, otherValue))[0])  # no castType
    elif VS.get('value_representsy', False):
        vNew = roundFunc(mp((otherValue, self))[1])  # no castType
    
    # Now do attributes
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
    ...     valueSpec = dict()
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
        if baseType(self):
            return True
        
        return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)
    
    SM_bool_closure.__doc__ = SM_bool.__doc__
    return SM_bool_closure

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(float, metaclass=FontDataMetaclass): pass
    >>> b = Bottom(10.25)
    >>> bCopy = b.__copy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(int, metaclass=FontDataMetaclass):
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
    
    >>> class Bottom(float, metaclass=FontDataMetaclass): pass
    >>> b = Bottom(10.25)
    >>> bCopy = b.__deepcopy__()
    >>> b == bCopy, b is bCopy
    (True, False)
    
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_deepcopyfunc': (lambda x,m: list(x))}}
    >>> t = Top(5, a=[1, 2, 3])
    >>> tCopy = t.__deepcopy__()
    >>> t == tCopy, t is tCopy
    (True, False)
    >>> t.a is tCopy.a
    False
    
    >>> class Topper(float, metaclass=FontDataMetaclass):
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
        
        if baseType(self) != baseType(other):
            return False
        
        return attrhelper.SM_eq(
            self._ATTRSPEC,
            getattr(other, '_ATTRSPEC', {}),
            self.__dict__,
            getattr(other, '__dict__', {}))
    
    SM_eq_closure.__doc__ = SM_eq.__doc__
    return SM_eq_closure

def SM_hash(baseType):
    """
    Returns a hash value for the object.
    
    :return: The hash value
    :rtype: int
    
    Note this method is only included by the metaclass initialization logic if
    there is at least one attribute that has ``attr_ignoreforcomparisons`` set
    to False.
    
    >>> class Test1(float, metaclass=FontDataMetaclass):
    ...     valueSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforcomparisons = True),
    ...         notIgnored = dict())
    
    >>> obj1 = Test1(1.75, ignored=3, notIgnored=4)
    >>> obj2 = Test1(1.75, ignored=5, notIgnored=4)
    >>> obj3 = Test1(1.75, ignored=3, notIgnored=7)
    >>> len({obj1, obj2})
    1
    >>> len({obj1, obj3})
    2
    >>> len({obj1, obj2, obj3})
    2
    >>> d = {obj1: 15, obj3: 20}
    >>> len(d)
    2
    
    The following may seem strange, but remember the keys are subject to
    hashing, and hash(1.75) is different than hash(obj1) or hash(obj3).
    
    >>> 1.75 in d
    False
    >>> len({hash(1.75), hash(obj1), hash(obj3)})
    3
    """
    
    def SM_hash_closure(self):
        AS = self._ATTRSPEC
        d = self.__dict__
        v = []
        
        for k in sorted(AS):  # not sortedKeys (this needs to be exhaustive)
            ks = AS[k]
            f = ks.get('attr_asimmutablefunc', None)
            obj = d[k]
            
            if not ks.get('attr_ignoreforcomparisons', False):
                if ks.get(
                  'attr_asimmutabledeep',
                  ks.get('attr_followsprotocol', False)):
                    
                    v.append(obj.asImmutable())
                
                elif f is not None:
                    v.append(f(obj))
                
                else:
                    v.append(obj)
        
        return hash((baseType(self), tuple(v)))
    
    SM_hash_closure.__doc__ = SM_hash.__doc__
    return SM_hash_closure

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
                # other keyword arguments are done.
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
    Create a new instance, but defer attribute initialization to
    ``__init__()``. Note this method is only included in the class if
    attributes are present.
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {}}
    >>> int(Test(6))
    6
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initValueSquared = dict(
    ...             attr_initfunc = (lambda n: n * n),
    ...             attr_initfuncneedsself = True))
    >>> n = Test2(12)
    >>> print(n)
    12, initValueSquared = 144
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
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
    Value: 1
    a: abc
    b: ab
    c: c
    >>> Test3(1, a="wxyz and then some").pprint()
    Value: 1
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test3(1, c="independently initialized").pprint()
    Value: 1
    a: abc
    b: ab
    c: independently initialized
    """
    
    def SM_new_closure(cls, value, *args, **kwArgs):
        return baseType.__new__(cls, value)
    
    SM_new_closure.__doc__ = SM_new.__doc__
    return SM_new_closure

def SM_repr(baseType):
    """
    Return a string that can be eval()'d back to an equal object.
    
    >>> class Test1(float, metaclass=FontDataMetaclass): pass
    >>> t1 = Test1(52.5)
    >>> print(repr(t1))
    Test1(52.5)
    >>> t1 == eval(repr(t1))
    True
    
    >>> class Test2(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test2(-5) == eval(repr(Test2(-5)))
    True
    """
    
    def SM_repr_closure(self):
        AS = self._ATTRSPEC
        
        if not AS:
            return "%s(%r)" % (self.__class__.__name__, baseType(self))
        
        d = self.__dict__
        t = tuple(x for k in AS for x in (k, d[k]))
        sv = [
            self.__class__.__name__,
            '(',
            repr(baseType(self)),
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
    ...     valueSpec = dict(
    ...         value_isglyphindex = True,
    ...         value_usenamerforstr = True)
    >>> v1 = Test(52)
    >>> v2 = Test(52)
    >>> v2.setNamer(namer.testingNamer())
    >>> print(v1)
    52
    >>> print(v2)
    xyz53
    
    >>> class Bottom(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'first': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "First Glyph"},
    ...       'second': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Second Glyph"}}
    >>> class Top(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'n': {'attr_initfunc': (lambda: 1), 'attr_label': "Count"},
    ...       'pair': {
    ...         'attr_initfunc': (lambda: Bottom(15)),
    ...         'attr_label': "Glyph Pair",
    ...         'attr_followsprotocol': True,
    ...         'attr_strneedsparens': True}}
    ...     attrSorted = ('pair', 'n')
    >>> print(Bottom(8, first=20, second=25))
    8, First Glyph = 20, Second Glyph = 25
    >>> print(Top(-6, n=40, pair=Bottom(11, first=20, second=25)))
    -6, Glyph Pair = (11, First Glyph = 20, Second Glyph = 25), Count = 40
    
    >>> class Test(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {
    ...         'attr_labelfunc': (
    ...           lambda x, **k: ("Odd" if x % 2 else "Even"))}}
    >>> print(Test(5, 2))
    5, Even = 2
    >>> print(Test(5, 3))
    5, Odd = 3
    
    >>> class Test1(float, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    >>> class Test2(float, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    >>> print(Test1(1.75))
    1.75, s = fred
    >>> print(Test2(1.75))
    1.75, s = 'fred'
    
    >>> class Test3(int, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> print(Test3(-3))
    -3, y = 5
    >>> print(Test3(-3, x=4))
    -3, x = 4, y = 5
    """
    
    def SM_str_closure(self):
        VS = self._VALSPEC
        AS = self._ATTRSPEC
        selfNamer = getattr(self, '_namer', None)
        kwa = self.__dict__.get('kwArgs', {})
        
        if selfNamer is None:
            selfNamer = kwa.get('editor', None)
            
            if selfNamer is not None:
                selfNamer = selfNamer.getNamer()
        
        if VS.get('value_isglyphindex', False):
            if VS.get('value_usenamerforstr', False):
                if selfNamer is not None:
                    r = selfNamer.bestNameForGlyphIndex(int(self))
                else:
                    r = str(baseKind(self))
            else:
                r = str(baseKind(self))
        
        elif VS.get('value_isnameindex', False):
            r = utilities.nameFromKwArgs(int(self), **kwa)
        
        else:
            r = str(baseKind(self))
        
        if not AS:
            return r
        
        sv = [r] + attrhelper.SM_str(self, selfNamer)
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
    'getSortedAttrNames': classmethod(lambda x: x._ATTRSORT),
    'glyphsRenumbered': M_glyphsRenumbered,
    'hasCycles': M_hasCycles,
    'isValid': M_isValid,
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
    '__init__': SM_init,
    }

_methodDictNeedType = {
    '__repr__': SM_repr,
    '__str__': SM_str,
    'asImmutable': M_asImmutable,
    'pprint': M_pprint,
    'pprint_changes': M_pprintChanges
    }

_methodDictNeedTypeAttr = {
    '__new__': SM_new
    }

def _addMethods(cd, bases):
    AS = cd['_ATTRSPEC']
    baseType = (int if issubclass(bases[0], int) else float)  # ???
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
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
    
    # Only include __eq__ and __ne__ methods if needed
    if needEqNe:
        if '__eq__' not in cd:
            cd['__eq__'] = SM_eq(baseType)
        
        if '__ne__' not in cd:
            cd['__ne__'] = (lambda a, b: not (a == b))
        
        if '__hash__' not in cd:
            cd['__hash__'] = SM_hash(baseType)
    
    # Only include __bool__ method if needed
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

def _validateValueSpec(d):
    """
    Make sure only known keys are included in the valueSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> d = {'value_isglyphindex': True}
    >>> _validateValueSpec(d)
    >>> d = {'value_isglyphinde': True}
    >>> _validateValueSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown valueSpec keys: ['value_isglyphinde']
    """
    
    unknownKeys = set(d) - validValueSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown valueSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'value_prevalidatedglyphset' in d:
        
        if not (
          d.get('value_isglyphindex', False) or
          d.get('value_isoutputglyph', False)):
            
            raise ValueError(
              "Prevalidated glyph set provided but sequence values "
              "are not glyph indices!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for value-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already one of the
    FontData classes, the valueSpec and attrSpec will define additions to the
    original. In this case, if an 'attrSorted' is provided, it will be used for
    the combined attributes (original and newly-added); otherwise the new
    attributes will be added to the end of the attrSorted list.
    
    >>> class L1(int, metaclass=FontDataMetaclass):
    ...     attrSpec = {'attr1': {}}
    >>> v1 = L1(29.1, attr1=10)
    >>> v1.setNamer(namer.testingNamer())
    >>> print(v1)
    29, attr1 = 10
    
    >>> class L2(L1, metaclass=FontDataMetaclass):
    ...     valueSpec = {
    ...       'value_isglyphindex': True,
    ...       'value_usenamerforstr': True}
    ...     attrSpec = {'attr2': {}}
    ...     attrSorted = ('attr2', 'attr1')
    >>> v2 = L2(29, attr1=10, attr2=9)
    >>> v2.setNamer(namer.testingNamer())
    >>> print(v2)
    xyz30, attr2 = 9, attr1 = 10
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_VALSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            VS = c._VALSPEC.copy()
            VS.update(classdict.pop('valueSpec', {}))
            classdict['_VALSPEC'] = classdict['_MAIN_SPEC'] = VS
            _validateValueSpec(VS)
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
            d = classdict['_VALSPEC'] = classdict.pop('valueSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateValueSpec(d)
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
