#
# keymeta.py
#
# Copyright © 2010-2013, 2015-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for tuple-like objects used as keys in a dict or members of a set.
There are several key characteristics of these objects that distinguish them
from simple sequences:

    - They are always immutable. Clients should use either ``tuple`` or a class
      created via ``collections.namedtuple`` as the base class.
    
    - Their elements may be different classes and have different behaviors. In
      regular sequences, all members are either ``None`` or of the same class.
    
    - They do not support attributes.

The following two class attributes are used to control the various behaviors of
instances of any class using this metaclass:

``itemSpec``
    A sequence (usually a tuple) of dicts, one for each member of the tuple.
    Each of these dicts contains the fontdata specification for that element of
    the tuple, as defined via the following keys and values:
        
    ``item_coalescedeep``
        If True, the key component value has its own ``coalesced()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_followsprotocol``
        If True, the key component is itself a Protocol object, and thus has
        all the Protocol methods.

        Note that this may be overridden by explicitly setting a desired "deep"
        flag to False. So, for instance, if the key component value should not
        have ``compacted()`` calls made on it, then the ``itemSpec`` entry
        should have this flag set to True and ``item_compactdeep`` set to
        False.
        
        Default is False.
    
    ``item_inputcheckfunc``
        A function taking one positional argument (the proposed key component
        value) and keyword arguments, one of which should be ``itemIndex``
        indicating which entry in the key is being proposed. It should return
        True if the specified value is acceptable.
        
        There is no default.
    
    ``item_islivingdeltas``
        If True, this key component will be included in the output of
        ``gatheredLivingDeltas()``.
        
        Default is False.
    
    ``item_isoutputglyph``
        If True, the key component is an output glyph index. This means it will
        not be included in the output of a ``gatheredInputGlyphs()`` call, and
        it will be included in the output of a ``gatheredOutputGlyphs()`` call.
        Note that ``item_renumberdirect`` must also be set; otherwise this
        value will not be added, even if this flag is True.
        
        Default is False.
    
    ``item_label``
        A string that will be used for instances derived from
        ``collections.namedtuple`` when string or pretty-printing is needed.
        This field is ignored if the instance descends from ``tuple``.
        
        There is no default for tuples, the field name for
        ``namedtuple``-derived instances.
    
    ``item_mergedeep``
        If True, the key component has its own ``merged()`` method. Note that
        this method may not end up being called, even if this flag is True, if
        the ``merged()`` method is called with the ``replaceWhole`` keyword
        argument set to True.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_prevalidatedglyphset``
        A set-like object containing glyph indices which are to be considered
        valid, even though they exceed the font's glyph count. This is useful
        for passing ``0xFFFF`` values through validation for state tables,
        where that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``item_python3rounding``
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
        Default is False.
    
    ``item_recalculatedeep``
        If True, the key component has its own ``recalculated()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_recalculatefunc``
        A function taking one positional argument, the key component value.
        Additional keyword arguments (for example, ``editor``) may be
        specified. This function returns a pair: the first value is True or
        False, depending on whether the value actually changed. The second
        value is the new recalculated object to be used (if the first value was
        True).
        
        There is no default.
    
    ``item_renumbercvtsdeep``
        If True, the key component has its own ``cvtsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbercvtsdirect``
        If True then key component values are interpreted as CVT values, and
        are subject to renumbering if the ``cvtsRenumbered()`` method is called.
        
        Default is False.
    
    ``item_renumberdeep``
        If True, the key component has its own ``glyphsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberdirect``
        If True, the key component is a glyph index (or ``None``). Any method
        that uses glyph indices (e.g. ``glyphsRenumbered()`` or
        ``gatheredInputGlyphs()``) looks at this flag to ascertain whether the
        key component is available for processing.
        
        Default is False.
    
    ``item_renumberfdefsdeep``
        If True then the key component has its own ``fdefsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdirect``
        If True then key component values are interpreted as function
        definition numbers (FDEF indices), and are subject to renumbering if
        the ``fdefsRenumbered()`` method is called.
        
        Default is False.
    
    ``item_renumbernamesdeep``
        If True then the key component value has its own ``namesRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdirect``
        If True then non-``None`` key component values are interpreted as
        indices into the ``'name'`` table, and are subject to being renumbered
        via a ``namesRenumbered()`` call.
        
        Default is False.
    
    ``item_renumberpcsdeep``
        If True, the key component has its own ``pcsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpcsdirect``
        If True, the key component value is a PC value. The value will be
        directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``.
        
        Default is False.
    
    ``item_renumberpointsdeep``
        If True, the key component has its own ``pointsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpointsdirect``
        If True, the key component value is interpreted as a point index. Note
        that if this is used, the ``kwArgs`` passed into the
        ``pointsRenumbered()`` call must include ``glyphIndex`` which is used
        to index into that method's ``mapData``.
        
        Default is False.
    
    ``item_renumberstoragedeep``
        If True then the key component has its own ``storageRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedirect``
        If True then the key component value is interpreted as a storage index,
        and is subject to renumbering if the ``storageRenumbered()`` method is
        called.
        
        Default is False.
    
    ``item_representsx``
        If True then this non-``None`` key component value is interpreted as an
        x-coordinate. This knowledge is used by the ``scaled()`` method, in
        conjunction with the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword
        arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated y-coordinate value will be
        forced to zero, unless an ``item_transformcounterpartfunc`` is
        specified (q.v.)
        
        Default is False.
    
    ``item_representsy``
        If True then this non-``None`` key component value is interpreted as a
        y-coordinate. This knowledge is used by the ``scaled()`` method, in
        conjunction with the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword
        arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated x-coordinate value will be
        forced to zero, unless an ``item_transformcounterpartfunc`` is
        specified (q.v.)
        
        Default is False.
    
    ``item_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the key component value), at least one keyword argument
        (``castType``, the type of the returned result, or ``None`` to keep its
        current type), and other optional keyword arguments.
        
        There is no default.
    
    ``item_scaledeep``
        If True, the key component has its own ``scaled()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_scaledirect``
        If True then this non-``None`` key component value will be scaled by
        the ``scaled()`` method, with the results rounded to the nearest
        integral value (with .5 cases controlled by ``item_python3rounding``);
        if this is not desired, the client should instead specify the
        ``item_scaledirectnoround`` flag.

        The type of a rounded scaled value will be the type of the original
        value.
        
        Default is False.
    
    ``item_scaledirectnoround``
        If True then this non-``None`` key component value will be scaled by
        the ``scaled()`` method. No rounding will be done on the result; if
        rounding to integral values is desired, use the ``item_scaledirect``
        flag instead.
        
        The type of a non-rounded scaled value will be ``float``.
        
        Default is False.
    
    ``item_strusesrepr``
        If True, the string representation for the key component value will be
        created via ``repr()``, not ``str()``.
        
        Default is False.
    
    ``item_transformcounterpartfunc``
        If the key contains both an x-coordinate and a y-coordinate this
        function can be used to link them. It takes a single argument: the
        whole key object. Note this function can also be used to provide a
        constant nonzero value (there's no need for the zero case, since that's
        presumed in the absence of other specifications).
        
        There is no default.
    
    ``item_transformnoround``
        If True then the non-``None`` key component value will not be rounded
        to the nearest integral value after a ``transformed()`` call. Note that
        if this flag is specified, the values will always be left as type
        ``float``, irrespective of the original type. This differs from the
        default case, where rounding will be used but the rounded result will
        be the same type as the original value.

        Note the absence of an "``item_transformdirect``" flag. Calls to the
        ``transformed()`` method will only affect this non-``None`` key
        component value if one or more of the ``item_representsx``,
        ``item_representsy``, or ``item_transformcounterpartfunc`` flags are
        set (or, of course, the ``item_followsprotocol`` flag).
        
        Default is False.
    
    ``item_usenamerforstr``
        If this flag and ``item_renumberdirect`` are both True, and a
        :py:class:`~fontio3.utilities.namer.Namer` is available either from a
        ``setNamer()`` call or via keyword arguments, then that ``Namer`` will
        be used for generating the strings produced via the ``__str__()``
        special method.
        
        Default is False.
    
    ``item_validatecode_namenotintable``
        The code to be used for logging when a name table index is being used
        but that index is not actually present in the ``'name'`` table.
        
        Default is ``'G0042'``.
    
    ``item_validatecode_negativecvt``
        The code to be used for logging when a negative value is used for a CVT
        index.
        
        Default is ``'G0028'``.
    
    ``item_validatecode_negativeglyph``
        The code to be used for logging when a negative value is used for a
        glyph index.
        
        Default is ``'G0004'``.
    
    ``item_validatecode_negativeinteger``
        The code to be used for logging when a negative value is used for a
        non-negative item (like a PC or a point index).
        
        Default is ``'G0008'``.
    
    ``item_validatecode_nocvt``
        The code to be used for logging when a CVT index is used but the font
        has no ``'cvt '`` table.
        
        Default is ``'G0030'``.
    
    ``item_validatecode_nonintegercvt``
        The code to be used for logging when a non-integer value is used for a
        CVT index.
        
        Default is ``'G0027'``.
    
    ``item_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is used for a
        glyph index.
        
        Default is ``'G0003'``.
    
    ``item_validatecode_nonintegralinteger``
        The code to be used for logging when a non-integer value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0007'``.
    
    ``item_validatecode_nonnumericcvt``
        The code to be used for logging when a non-numeric value is used for a
        CVT index.
        
        Default is ``'G0026'``.
    
    ``item_validatecode_nonnumericglyph``
        The code to be used for logging when a non-numeric value is used for a
        glyph index.
        
        Default is ``'G0002'``.
    
    ``item_validatecode_nonnumericinteger``
        The code to be used for logging when a non-numeric value is used for an
        integer item (like a PC or a point index).
        
        Default is ``'G0006'``.
    
    ``item_validatecode_nonnumericnumber``
        The code to be used for logging when a non-numeric value is used.
        
        Default is ``'G0009'``.
    
    ``item_validatecode_toolargecvt``
        The code to be used for logging when a CVT index is used that is
        greater than or equal to the number of CVTs in the font.
        
        Default is ``'G0029'``.
    
    ``item_validatecode_toolargeglyph``
        The code to be used for logging when a glyph index is used that is
        greater than or equal to the number of glyphs in the font.
        
        Default is ``'G0005'``.
    
    ``item_validatedeep``
        If True, the key component has its own ``isValid()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_validatefunc``
        A function taking one positional argument, the key component value, and
        an arbitrary number of keyword arguments. The function returns True if
        the value is valid (that is, if no errors are present). Note that
        values of ``None`` **will** be passed into this function, unlike most
        other actions.

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``item_validatefunc_partial`` instead.
        
        There is no default.
    
    ``item_validatefunc_partial``
        A function taking one positional argument, a key component value, and
        an arbitrary number of keyword arguments. The function returns True if
        the value is valid (that is, if no errors are present). Note that
        values of ``None`` **will** be passed into this function, unlike most
        other actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use an ``item_validatefunc`` instead.
        
        There is no default.
    
    ``item_wisdom``
        A string encompassing a sensible description of the value, including
        how it is used.
        
        There is, alas, no default for wisdom.
    
``keySpec``
    A dict containing the fontdata specification for the tuple as a whole, as
    defined via the following keys and values:
        
    ``key_maxcontextfunc``
        A function to determine the maximum context for the key. This function
        takes a single argument, the key itself, and optional keyword arguments.
        
        There is no default.
    
    ``key_pprintfunc``
        A function taking three positional arguments (a
        :py:class:`~fontio3.utilities.pp.PP` object, the key object, and a
        label), and optional keyword arguments. It should pretty-print the
        entire key.
        
        There is no default.
    
    ``key_recalculatefunc``
        If specified, a function taking one positional argument, the whole key
        object. Additional keyword arguments (for example, ``editor``) may be
        specified.

        The function returns a pair: the first value is True or False,
        depending on whether the recalculated key object's value actually
        changed. The second value is the new recalculated object to be used (if
        the first value was True).

        If a ``key_recalculatefunc`` is provided then no individual
        ``item_recalculatefunc`` calls will be made. If you want them to be
        made, use a ``key_recalculatefunc_partial`` instead.
        
        There is no default.
    
    ``key_recalculatefunc_partial``
        A function taking one positional argument, the whole key object, and
        optional additional keyword arguments. The function should return a
        pair: the first value is True or False, depending on whether the
        recalculated key object's value actually changed. The second value is
        the new recalculated object to be used (if the first value was True).

        After the ``key_recalculatefunc_partial`` is done, individual
        ``item_recalculatefunc`` calls will be made. This allows you to "divide
        the labor" in useful ways.
        
        There is no default.
    
    ``key_validatefunc``
        A function taking one positional argument, the whole key component, and
        optional additional keyword arguments. The function returns True if the
        key component is valid, and False otherwise.

        Note that this keyword prevents any ``item_validatefuncs`` from being
        run. If you want to run those as well, then use the
        ``key_validatefunc_partial`` keyword instead.
        
        There is no default.
    
    ``key_validatefunc_partial``
        A function taking one positional argument, the whole key component, and
        optional additional keyword arguments. The function returns True if the
        key component is valid, and False otherwise. Any ``item_validatefuncs``
        will also be run to determine the returned True/False value, so this
        function should focus on overall key component validity.

        If you want this function to do everything without allowing any
        ``item_validatefuns`` to be run, then use the ``key_validatefunc``
        keyword instead.
        
        There is no default.
    
    ``key_wisdom``
        A string encompassing a sensible description of the key as a whole,
        including how it is used.
        
        There is, alas, no default for wisdom.
"""

# System imports
import collections
import functools
import logging

# Other imports
from fontio3 import utilities
from fontio3.fontdata import invariants
from fontio3.utilities import pp, valassist

# -----------------------------------------------------------------------------

#
# Constants
#

validItemSpecKeys = frozenset([
  'item_coalescedeep',
  'item_followsprotocol',
  'item_inputcheckfunc',
  'item_islivingdeltas',
  'item_isoutputglyph',
  'item_label',
  'item_mergedeep',
  'item_prevalidatedglyphset',
  'item_python3rounding',
  'item_recalculatedeep',
  'item_recalculatefunc',
  'item_renumbercvtsdeep',
  'item_renumbercvtsdirect',
  'item_renumberdeep',
  'item_renumberdirect',
  'item_renumberfdefsdeep',
  'item_renumberfdefsdirect',
  'item_renumbernamesdeep',
  'item_renumbernamesdirect',
  'item_renumberpcsdeep',
  'item_renumberpcsdirect',
  'item_renumberpointsdeep',
  'item_renumberpointsdirect',
  'item_renumberstoragedeep',
  'item_renumberstoragedirect',
  'item_representsx',
  'item_representsy',
  'item_roundfunc',
  'item_scaledeep',
  'item_scaledirect',
  'item_scaledirectnoround',
  'item_strusesrepr',
  'item_transformcounterpartfunc',
  'item_transformnoround',
  'item_usenamerforstr',
  'item_validatecode_namenotintable',
  'item_validatecode_negativecvt',
  'item_validatecode_negativeglyph',
  'item_validatecode_negativeinteger',
  'item_validatecode_nocvt',
  'item_validatecode_nonintegercvt',
  'item_validatecode_nonintegerglyph',
  'item_validatecode_nonintegralinteger',
  'item_validatecode_nonnumericcvt',
  'item_validatecode_nonnumericglyph',
  'item_validatecode_nonnumericinteger',
  'item_validatecode_nonnumericnumber',
  'item_validatecode_toolargecvt',
  'item_validatecode_toolargeglyph',
  'item_validatedeep',
  'item_validatefunc',
  'item_validatefunc_partial',
  'item_wisdom'])

validKeySpecKeys = frozenset([
  'key_maxcontextfunc',
  'key_pprintfunc',
  'key_recalculatefunc',
  'key_recalculatefunc_partial',
  'key_validatefunc',
  'key_validatefunc_partial',
  'key_wisdom'])

# -----------------------------------------------------------------------------

#
# Methods
#

def M_asImmutable(self, **kwArgs):
    """
    Returns an immutable version of ``self``.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: An immutable version of ``self``
    
    Since instances of classes descended from this metaclass are always
    immutable and have no attributes, this method doesn't need to do much work.
    It just returns a tuple whose first element is the name of the type object,
    and whose remaining elements are the contents of ``self``.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (dict(), dict(), dict())
    >>> obj = Test([15, (4, 5), 'hi there'])
    >>> obj.asImmutable()
    ('Test', 15, (4, 5), 'hi there')
    """
    
    assert len(self) == len(self._ITEMSPEC)
    return (type(self).__name__,) + tuple(self)

def M_checkInput(self, valueToCheck, **kwArgs):
    """
    Checks if the specified value is acceptable for a slot within ``self``.
    
    :param valueToCheck: The value to be checked
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if appropriate, False otherwise
    :rtype: bool
    
    This method is used to check the appropriateness of a value for the given
    kind of object. So for example, if an ``'OS/2'`` weight-class value is
    supposed to be a number from 1 to 1000, this method's implementation for
    that object will check that specifically.
    
    The following ``kwArgs`` are supported:
    
    ``itemIndex``
        This required keyword argument identifies which slot (i.e. array index)
        is being checked. This is needed since the values in different slots
        can have different types.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...   itemSpec = (
    ...     dict(item_inputcheckfunc=(lambda x, **k: 10 <= x < 20)),
    ...     dict(item_inputcheckfunc=(lambda x, **k: -20 <= x < -10)))
    >>> k = Test([14, -18])
    >>> k.checkInput(16, itemIndex=0)
    True
    >>> k.checkInput(36, itemIndex=0)
    False
    >>> k.checkInput(-16, itemIndex=1)
    True
    >>> k.checkInput(36, itemIndex=1)
    False
    """
    
    itemIndex = kwArgs['itemIndex']  # must be present
    kid = self._ITEMSPEC[itemIndex]
    f = kid.get('item_inputcheckfunc', None)
    
    if f is None:
        return True
    
    return f(valueToCheck, **kwArgs)

def M_coalesced(self, **kwArgs):
    """
    Return new object representing ``self`` with duplicates coerced to the
    same object.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``

    Font data often comprises multiple parts that happen to be the same. One
    example here is the platform 0 (Unicode) and platform 3 (Microsoft)
    ``'cmap'`` subtables, which often have exactly the same data. The binary
    format for the ``'cmap'`` table permits sharing here (each table is
    actually an offset, so the two offsets here can refer to the same data).
    This method is used to force this sharing to occur, if possible.

    It's important to remember that fontio3 deals with high-level, more
    abstract representations of font data. In order to allow for both the
    sharing and non-sharing cases, this method uses the object ID (that is, the
    results of calling the built-in ``id()`` function) as a clue. If two
    objects contained in some container object share the same ID, then they'll
    be shared in the binary representation.

    Knowing this, it's now easy to see what this method does. It compares any
    protocol objects it contains, and if it finds some that compare equal but
    have different IDs, it "coalesces" them to refer to the same ID. This will
    then ensure shared references to the same data in the binary data, once
    it is written.
    
    In the returned result, if two objects are equal then they will be the same
    object (i.e. an ``is`` test will return True).

    The following ``kwArgs`` are supported:

    ``pool``
        A dict mapping immutable representations of objects to the objects
        themselves. This is optional; a new, empty dict will be used if one is
        not specified.
    
        This is useful if you want to coalesce objects across many higher-level
        objects.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (dict(), dict(), dict(item_followsprotocol = True))
    >>> t1 = Test(["Outrageous!", "Out" + "rageous!", None])
    >>> t1[0] is t1[1]
    False
    
    >>> t1Coalesced = t1.coalesced()
    >>> t1Coalesced == t1, t1Coalesced[0] is t1Coalesced[1]
    (True, True)
    
    >>> t2 = Test(["O" + "utrageous!", "fred", t1])
    >>> t2[0] is t2[2][0], t2[0] is t2[2][1]
    (False, False)
    >>> t2Coalesced = t2.coalesced()
    >>> t2Coalesced[0] is t2Coalesced[2][0]
    True
    >>> t2Coalesced[0] is t2Coalesced[2][1]
    True
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b"),
    ...       dict(item_label = "c"))
    >>> t3 = Test2("Swell!", "S" + "well!", None)
    >>> t3.a == t3.b, t3.a is t3.b
    (True, False)
    >>> t3Coalesced = t3.coalesced()
    >>> t3Coalesced.a == t3Coalesced.b, t3Coalesced.a is t3Coalesced.b
    (True, True)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    pool = kwArgs.pop('pool', {})  # allows for multi-level coalescing
    vNew = list(self)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_coalescedeep',
              kid.get('item_followsprotocol', False)):
                
                obj = obj.coalesced(pool=pool, **kwArgs)
            
            vNew[i] = pool.setdefault(obj, obj)
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def M_compacted(self, **kwArgs):
    """
    Return ``self``.
    
    Compacting has no effect on instances of classes descending from this
    metaclass, so this method just returns ``self``.
    """
    
    assert len(self) == len(self._ITEMSPEC)
    return self

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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_renumbercvtsdirect = True),
    ...         dict(item_followsprotocol = True))
    
    >>> k1 = Test1([20, None])
    >>> k2 = Test1([35, k1])
    
    >>> print(k1.cvtsRenumbered(cvtDelta=50))
    (70, None)
    >>> print(k2.cvtsRenumbered(cvtDelta=50))
    (85, (70, None))
    
    >>> print(k1.cvtsRenumbered(oldToNew={20: 400}))
    (400, None)
    >>> print(k2.cvtsRenumbered(oldToNew={20: 400}))
    (35, (400, None))
    >>> print(k2.cvtsRenumbered(oldToNew={20: 400}, keepMissing=False))
    (None, (400, None))
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.cvtsRenumbered(cvtMappingFunc=f))
    (108, None)
    >>> print(k2.cvtsRenumbered(cvtMappingFunc=f))
    (185, (108, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumbercvtsdirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.cvtsRenumbered(cvtDelta=100))
    (a = 5, b = 105, c = 5)
    >>> print(t.cvtsRenumbered(oldToNew={5:30}))
    (a = 5, b = 30, c = 5)
    >>> print(t.cvtsRenumbered(oldToNew={10:29}))
    (a = 5, b = 5, c = 5)
    >>> print(t.cvtsRenumbered(oldToNew={10:29}, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
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
    
    vNew = [None] * len(self)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            
            if kid.get(
              'item_renumbercvtsdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.cvtsRenumbered(**kwArgs)
            
            elif kid.get('item_renumbercvtsdirect', False):
                vNew[i] = cvtMappingFunc(obj, **kwArgs)
            
            else:
                vNew[i] = self[i]
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_renumberfdefsdirect = True),
    ...         dict(item_followsprotocol = True))
    
    >>> k1 = Test1([20, None])
    >>> k2 = Test1([35, k1])
    
    >>> print(k1.fdefsRenumbered(oldToNew={20: 400}))
    (400, None)
    >>> print(k2.fdefsRenumbered(oldToNew={20: 400}))
    (35, (400, None))
    >>> print(k2.fdefsRenumbered(oldToNew={20: 400}, keepMissing=False))
    (None, (400, None))
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.fdefsRenumbered(fdefMappingFunc=f))
    (108, None)
    >>> print(k2.fdefsRenumbered(fdefMappingFunc=f))
    (185, (108, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumberfdefsdirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.fdefsRenumbered(oldToNew={5:30}))
    (a = 5, b = 30, c = 5)
    >>> print(t.fdefsRenumbered(oldToNew={10:29}))
    (a = 5, b = 5, c = 5)
    >>> print(t.fdefsRenumbered(oldToNew={10:29}, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
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
    
    vNew = [None] * len(self)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_renumberfdefsdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.fdefsRenumbered(**kwArgs)
            
            elif kid.get('item_renumberfdefsdirect', False):
                vNew[i] = fdefMappingFunc(obj, **kwArgs)
            
            else:
                vNew[i] = self[i]
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_renumberdirect = True),
    ...         dict(item_renumberdirect = True, item_isoutputglyph = True))
    >>> t1 = Test1([5, 6, 7])
    >>> t1.gatheredInputGlyphs()
    {6}
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_followsprotocol = True),
    ...         dict(item_renumberdirect = True),
    ...         dict(item_renumberdirect = True, item_isoutputglyph = True))
    >>> t2 = Test2([t1, 8, 9])
    >>> sorted(t2.gatheredInputGlyphs())
    [6, 8]
    
    >>> class Test3(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(
    ...             item_label = "a",
    ...             item_renumberdirect = True),
    ...         dict(
    ...             item_label = "b",
    ...             item_renumberdirect = True,
    ...             item_isoutputglyph = True),
    ...         dict(
    ...             item_label = "c"))
    >>> t3 = Test3(20, 30, 40)
    >>> print(sorted(t3.gatheredInputGlyphs()))
    [20]
    """
    
    assert len(self) == len(self._ITEMSPEC)
    r = set()
    
    for obj, kid in zip(self, self._ITEMSPEC):
        if obj is not None:
            if kid.get(
              'item_renumberdeep',
              kid.get('item_followsprotocol', False)):
                
                r.update(obj.gatheredInputGlyphs(**kwArgs))
            
            elif (
              kid.get('item_renumberdirect', False) and
              (not kid.get('item_isoutputglyph', False))):
                
                r.add(obj)
    
    return r

def M_gatheredLivingDeltas(self, **kwArgs):
    """
    Return a set of :py:class:`~fontio3.opentype.living_variations.LivingDeltas`
    objects contained in ``self``.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of ``LivingDeltas`` objects.
    :rtype: set

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8` ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual LivingDeltas objects. Since those objects are
    immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual LivingDeltas objects!
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...   itemSpec = (
    ...     dict(item_islivingdeltas = True),
    ...     dict())
    >>> sorted(Test([3, 4]).gatheredLivingDeltas())
    [3]
    """
    
    assert len(self) == len(self._ITEMSPEC)
    r = set()
    
    for obj, kid in zip(self, self._ITEMSPEC):
        if obj is None:
            continue
        
        if kid.get('item_islivingdeltas', False):
            r.add(obj)
        elif kid.get('item_followsprotocol', False):
            r.update(obj.gatheredLivingDeltas(**kwArgs))
    
    return r

def M_gatheredMaxContext(self, **kwArgs):
    """
    Return an integer representing the ``'OS/2'`` maximum context value.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The maximum context
    :rtype: int

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     keySpec = dict(key_maxcontextfunc = (lambda x: x[0] + 1))
    ...     itemSpec = (dict(), dict())
    >>> t1 = Test1([2, 6])
    >>> print(t1.gatheredMaxContext())
    3
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (dict(item_followsprotocol = True), dict())
    >>> t2 = Test2([t1, 9])
    >>> print(t2.gatheredMaxContext())
    3
    
    >>> class Test3(
    ...   collections.namedtuple("_NT", "a b c"),
    ...   metaclass = FontDataMetaclass):
    ...     keySpec = dict(key_maxcontextfunc = (lambda x: x[0] + 1))
    ...     itemSpec = (
    ...         dict(item_label = "a"),
    ...         dict(item_label = "b"),
    ...         dict(item_label = "c"))
    >>> t3 = Test3(1, 5, 9)
    >>> print(t3.gatheredMaxContext())
    2
    """
    
    assert len(self) == len(self._ITEMSPEC)
    mcFunc = self._KEYSPEC.get('key_maxcontextfunc', None)
    
    if mcFunc is not None:
        mc = mcFunc(self, **kwArgs)
    
    else:
        mc = 0
        
        for obj, kid in zip(self, self._ITEMSPEC):
            if obj is not None:
                if kid.get('item_followsprotocol', False):
                    mc = max(mc, obj.gatheredMaxContext(**kwArgs))
    
    return mc

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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_renumberdirect = True),
    ...         dict(item_renumberdirect = True, item_isoutputglyph = True))
    >>> t1 = Test1([5, 6, 7])
    >>> t1.gatheredOutputGlyphs()
    {7}
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_followsprotocol = True),
    ...         dict(item_renumberdirect = True),
    ...         dict(item_renumberdirect = True, item_isoutputglyph = True))
    >>> t2 = Test2([t1, 8, 9])
    >>> sorted(t2.gatheredOutputGlyphs())
    [7, 9]
    
    >>> class Test3(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(
    ...             item_label = "a",
    ...             item_renumberdirect = True),
    ...         dict(
    ...             item_label = "b",
    ...             item_renumberdirect = True,
    ...             item_isoutputglyph = True),
    ...         dict(
    ...             item_label = "c"))
    >>> t3 = Test3(20, 30, 40)
    >>> print(sorted(t3.gatheredOutputGlyphs()))
    [30]
    """
    
    assert len(self) == len(self._ITEMSPEC)
    r = set()
    
    for obj, kid in zip(self, self._ITEMSPEC):
        if obj is not None:
            if kid.get(
              'item_renumberdeep',
              kid.get('item_followsprotocol', False)):
                
                r.update(obj.gatheredOutputGlyphs(**kwArgs))
            
            elif (
              kid.get('item_renumberdirect', False) and
              kid.get('item_isoutputglyph', False)):
                
                r.add(obj)
    
    return r

def M_gatheredRefs(self, **kwArgs):
    """
    Return an empty dict.
    """
    
    assert len(self) == len(self._ITEMSPEC)
    return {}

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
        the sequence, or (if attributes or an index map) will be changed to
        None.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_renumberdirect = True),
    ...         dict(item_followsprotocol = True))
    >>> t1 = Test([40, None])
    >>> print(t1.glyphsRenumbered({40: 20}))
    (20, None)
    
    >>> print(t1.glyphsRenumbered({15: 25}))
    (40, None)
    
    >>> print(t1.glyphsRenumbered({15: 25}, keepMissing=False))
    (None, None)
    
    >>> t2 = Test([60, t1])
    >>> print(t2.glyphsRenumbered({40: 20, 60: 21}))
    (21, (20, None))
    
    >>> print(t2.glyphsRenumbered({2: 3}))
    (60, (40, None))
    
    >>> print(t2.glyphsRenumbered({2: 3}, keepMissing=False))
    (None, (None, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumberdirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.glyphsRenumbered(oldToNew={5:30}))
    (a = 5, b = 30, c = 5)
    >>> print(t.glyphsRenumbered(oldToNew={10:29}))
    (a = 5, b = 5, c = 5)
    >>> print(t.glyphsRenumbered(oldToNew={10:29}, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    keepMissing = kwArgs.get('keepMissing', True)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t  # Python 3.x-friendly
        
        if obj is not None:
            if kid.get(
              'item_renumberdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.glyphsRenumbered(oldToNew, **kwArgs)
            
            elif kid.get('item_renumberdirect', False):
                vNew[i] = oldToNew.get(obj, (obj if keepMissing else None))
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def M_hasCycles(self, **kwArgs):
    """
    Return False.
    
    Note that classes using this metaclass will always get back False from this
    call, since there are no attributes, and since the key is hashable and thus
    cannot have cycles.
    """
    
    return False

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
    
    >>> def valEntry(obj, **kwArgs):
    ...     if obj % 3: return True
    ...     logger = kwArgs['logger']
    ...     logger.error(('Vxxxx', (obj,), "Value %d is divisible by three"))
    ...     return False
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         {'item_renumberdirect': True},
    ...         {'item_renumberpointsdirect': True},
    ...         {'item_scaledirect': True},
    ...         {'item_validatefunc': valEntry},
    ...         {'item_followsprotocol': True},
    ...         {'item_renumbernamesdirect': True})
    
    >>> logger = utilities.makeDoctestLogger("t1")
    >>> e = _fakeEditor()
    >>> t1 = Test([200, 1.5, "fred", 6, None, 500])
    >>> t1.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t1.[0] - ERROR - Glyph index 200 too large.
    t1.[1] - ERROR - The point index 1.5 is not an integer.
    t1.[2] - ERROR - The value 'fred' is not a real number.
    t1.[3] - ERROR - Value 6 is divisible by three
    t1.[5] - ERROR - Name table index 500 not present in 'name' table.
    False
    
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> t2 = Test([100, 4, -19, 9, t1, 'xy'])
    >>> t2.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t2.[3] - ERROR - Value 9 is divisible by three
    t2.[4].[0] - ERROR - Glyph index 200 too large.
    t2.[4].[1] - ERROR - The point index 1.5 is not an integer.
    t2.[4].[2] - ERROR - The value 'fred' is not a real number.
    t2.[4].[3] - ERROR - Value 6 is divisible by three
    t2.[4].[5] - ERROR - Name table index 500 not present in 'name' table.
    t2.[5] - ERROR - The name table index 'xy' is not a real number.
    False
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label="a", item_renumberdirect=True),
    ...         dict(item_label="b", item_scaledirect=True),
    ...         dict(item_label="c", item_renumbernamesdirect=True))
    >>> t3 = Test2(200, 'z', 159)
    >>> t3.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t2.a - ERROR - Glyph index 200 too large.
    t2.b - ERROR - The value 'z' is not a real number.
    t2.c - ERROR - Name table index 159 not present in 'name' table.
    False
    """
    
    IS = self._ITEMSPEC
    assert len(self) == len(IS)
    r = True
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        s = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(s)
    
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
    
    wholeFunc = self._KEYSPEC.get('key_validateFunc', None)
    wholeFuncPartial = self._KEYSPEC.get('key_validateFunc_partial', None)
    
    if wholeFunc is not None:
        r = wholeFunc(self, logger=logger, **kwArgs)
    
    else:
        if wholeFuncPartial is not None:
            r = wholeFuncPartial(self, logger=logger, **kwArgs)
        
        for i, (obj, kid) in enumerate(zip(self, IS)):
            if kid.get('item_label', None) is not None:
                itemLogger = logger.getChild(kid['item_label'])
            else:
                itemLogger = logger.getChild("[%d]" % (i,))
            
            indivFunc = kid.get('item_validatefunc', None)
            indivFuncPartial = kid.get('item_validatefunc_partial', None)
            pvs = kid.get('item_prevalidatedglyphset', set())
            
            if indivFunc is not None:
                r = indivFunc(obj, logger=itemLogger, **kwArgs) and r
            
            elif obj is None:
                continue
            
            elif kid.get(
              'item_validatedeep',
              kid.get('item_followsprotocol', False)):
                
                r = obj.isValid(logger=itemLogger, **kwArgs) and r
            
            else:
                if indivFuncPartial is not None:
                    r = indivFuncPartial(obj, logger=logger, **kwArgs) and r
                
                if kid.get('item_renumberdirect', False):
                    if not valassist.isNumber_integer_unsigned(
                      obj,
                      numBits = 16,
                      label = "glyph index",
                      logger = itemLogger):
                        
                        r = False
                    
                    elif (obj not in pvs) and (obj >= fontGlyphCount):
                        itemLogger.error((
                          kid.get('item_validatecode_toolargeglyph', 'G0005'),
                          (obj,),
                          "Glyph index %d too large."))
                        
                        r = False
                
                if kid.get('item_renumbernamesdirect', False):
                    if not valassist.isFormat_H(
                      obj,
                      label = "name table index",
                      logger = itemLogger):
                        
                        r = False
                    
                    elif obj not in namesInTable:
                        itemLogger.error((
                          kid.get('item_validatecode_namenotintable', 'G0042'),
                          (obj,),
                          "Name table index %d not present in 'name' table."))
                        
                        r = False
                
                elif kid.get('item_renumbercvtsdirect', False):
                    if not valassist.isNumber_integer_unsigned(
                      obj,
                      numBits = 16,
                      label = "CVT index",
                      logger = itemLogger):
                        
                        r = False
                    
                    elif editor is not None:
                        if b'cvt ' not in editor:
                            itemLogger.error((
                              kid.get('item_validatecode_nocvt', 'G0030'),
                              (obj,),
                              "CVT Index %d is being used, but the font "
                              "has no Control Value Table."))
                            
                            r = False
                        
                        elif obj >= len(editor[b'cvt ']):
                            itemLogger.error((
                              kid.get(
                                'item_validatecode_toolargecvt',
                                'G0029'),
                              (obj,),
                              "CVT index %d is not defined."))
                            
                            r = False
                
                elif kid.get('item_renumberpcsdirect', False):
                    if not valassist.isNumber_integer_unsigned(
                      obj,
                      numBits = 16,
                      label = "program counter",
                      logger = itemLogger):
                        
                        r = False
                
                elif kid.get('item_renumberpointsdirect', False):
                    if not valassist.isNumber_integer_unsigned(
                      obj,
                      numBits = 16,
                      label = "point index",
                      logger = itemLogger):
                        
                        r = False
                
                elif kid.get('item_renumberstoragedirect', False):
                    if not valassist.isNumber_integer_unsigned(
                      obj,
                      numBits = 16,
                      label = "storage index",
                      logger = itemLogger):
                        
                        r = False
                    
                    elif obj > maxStorage:
                        itemLogger.error((
                          'E6047',
                          (obj, maxStorage),
                          "The storage index %d is greater than the "
                          "font's defined maximum of %d."))
                        
                        r = False
                
                elif (
                  kid.get('item_scaledirect', False) or
                  kid.get('item_scaledirectnoround', False)):
                    
                    if not valassist.isNumber(obj, logger=itemLogger):
                        r = False
    
    return r

def M_merged(self, other, **kwArgs):
    """
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    
    The following ``kwArgs`` are supported:
    
    ``conflictPreferOther``
        True if the caller wishes the contents in ``other`` to have precedence;
        False if ``self`` should prevail. Default is True.
        
    ``replaceWhole``
        True if the entire contents of other should replace self. Default is
        False (i.e. it is done piecewise).
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (dict(), dict(), dict(item_followsprotocol = True))
    >>> t1Self = Test([15, 10, None])
    >>> t1Other = Test([25, 20, None])
    >>> print(t1Self.merged(t1Other))
    (25, 20, None)
    
    >>> print(t1Self.merged(t1Other, conflictPreferOther=False))
    (15, 10, None)
    
    >>> t2Self = Test([9, 20, t1Self])
    >>> t2Other = Test([-5, -10, t1Other])
    >>> print(t2Self.merged(t2Other))
    (-5, -10, (25, 20, None))
    
    >>> print(t2Self.merged(t2Other, conflictPreferOther=False))
    (9, 20, (15, 10, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label = "a"),
    ...         dict(item_label = "b"),
    ...         dict(item_label = "c"))
    >>> t3 = Test2(4, 5, 6)
    >>> t4 = Test2(7, 8, 9)
    >>> print(t3.merged(t4))
    (a = 7, b = 8, c = 9)
    >>> print(t3.merged(t4, conflictPreferOther=False))
    (a = 4, b = 5, c = 6)
    """
    
    assert len(self) == len(other) == len(self._ITEMSPEC)
    
    if kwArgs.get('replaceWhole', False):
        vNew = list(other)
    
    else:
        vNew = list(self)
        preferOther = kwArgs.get('conflictPreferOther', True)
        
        for i, t in enumerate(zip(self, other, self._ITEMSPEC)):
            selfObj, otherObj, kid = t
            
            if selfObj is not None and otherObj is not None:
                if kid.get(
                  'item_mergedeep',
                  kid.get('item_followsprotocol', False)):
                    
                    vNew[i] = selfObj.merged(otherObj, **kwArgs)
                
                elif preferOther:
                    vNew[i] = otherObj
            
            elif (selfObj is None) and preferOther:
                vNew[i] = otherObj
            
            # elif otherObj is None: pass (implicit since we copied self into
            # vNew to start)
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_renumbernamesdirect=True))
    >>> t1 = Test1([303, 303])
    >>> e = _fakeEditor()
    >>> t1.pprint(editor=e)
    (303, 303 ('Required Ligatures On'))
    >>> t1.namesRenumbered({303:306}).pprint(editor=e)
    (303, 306 ('Regular'))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumbernamesdirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.namesRenumbered(oldToNew={5:30}))
    (a = 5, b = 30, c = 5)
    >>> print(t.namesRenumbered(oldToNew={10:29}))
    (a = 5, b = 5, c = 5)
    >>> print(t.namesRenumbered(oldToNew={10:29}, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    keepMissing = kwArgs.get('keepMissing', True)
    
    for i, (obj, kid) in enumerate(zip(self, self._ITEMSPEC)):
        if obj is not None:
            if kid.get(
              'item_renumbernamesdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.namesRenumbered(oldToNew, **kwArgs)
            
            elif kid.get('item_renumbernamesdirect', False):
                vNew[i] = oldToNew.get(obj, (obj if keepMissing else None))
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_renumberpcsdirect = True),
    ...         dict(item_followsprotocol = True))
    >>> t1 = Test([15, None])
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> print(t1.pcsRenumbered(mapData, infoString="testcode"))
    (17, None)
    
    >>> t2 = Test([50, t1])
    >>> print(t2.pcsRenumbered(mapData, infoString="testcode"))
    (53, (17, None))
    
    >>> print(t2.pcsRenumbered(mapData, infoString="something else"))
    (50, (15, None))
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    thisMapData = mapData.get(kwArgs.get('infoString', None), [])
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_renumberpcsdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.pcsRenumbered(mapData, **kwArgs)
            
            elif kid.get('item_renumberpcsdirect', False):
                delta = 0
                
                for threshold, newDelta in thisMapData:
                    if obj < threshold:
                        break
                    
                    delta = newDelta
                
                vNew[i] = obj + delta
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_renumberpointsdirect = True),
    ...         dict(item_followsprotocol = True))
    >>> t1 = Test([5, 10, None])
    >>> mapData = {45: {5: 11, 10: 12, 15: 13}}
    >>> print(t1.pointsRenumbered(mapData, glyphIndex=45))
    (5, 12, None)
    
    >>> md2 = {45: {6: 7}}
    >>> print(t1.pointsRenumbered(md2, glyphIndex=45, keepMissing=True))
    (5, 10, None)
    
    >>> print(t1.pointsRenumbered(md2, glyphIndex=45, keepMissing=False))
    (5, None, None)
    
    >>> print(Test([10, 15, t1]).pointsRenumbered(mapData, glyphIndex=45))
    (10, 13, (5, 12, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumberpointsdirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.pointsRenumbered(mapData={10: {5:30, 30:5}}, glyphIndex=10))
    (a = 5, b = 30, c = 5)
    >>> print(t.pointsRenumbered(mapData={11: {5:30, 30:5}}, glyphIndex=10))
    (a = 5, b = 5, c = 5)
    >>> print(t.pointsRenumbered(mapData={11: {5:30, 30:5}}, glyphIndex=10, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    thisMapData = mapData.get(kwArgs.get('glyphIndex', None), {})
    keepMissing = kwArgs.get('keepMissing', True)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_renumberpointsdeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.pointsRenumbered(mapData, **kwArgs)
            
            elif kid.get('item_renumberpointsdirect', False):
                vNew[i] = thisMapData.get(obj, (obj if keepMissing else None))
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def M_pprint(self, **kwArgs):
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_strusesrepr = True),
    ...         dict(item_usenamerforstr = True, item_renumberdirect = True))
    >>> t1 = Test1(["fred", "fred", 96])
    >>> t1.pprint(label="With no namer")
    With no namer:
      (fred, 'fred', 96)
    
    >>> t1.pprint(label="With namer", namer=namer.testingNamer())
    With namer:
      (fred, 'fred', afii60001)
    
    >>> _NT = collections.namedtuple("_NT", ['red', 'green', 'blue'])
    >>> class Test2(_NT, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_label = "Green level"),
    ...         dict(item_label = "Blue level"))
    >>> Test2(255, 0, 128).pprint()
    (red = 255, Green level = 0, Blue level = 128)
    
    >>> def _pf(p, obj, label, **kwArgs):
    ...     s = "#%02X%02X%02X" % obj
    ...     p.simple(s, label=label, **kwArgs)
    >>> class Test3(_NT, metaclass=FontDataMetaclass):
    ...     itemSpec = ({}, {}, {})
    ...     keySpec = {'key_pprintfunc': _pf}
    >>> p = pp.PP()
    >>> Test3(255, 0, 128).pprint(p=p, label="Internet color identifier")
    Internet color identifier: #FF0080
    
    >>> class Test4(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_renumbernamesdirect=True))
    >>> t4 = Test4([303, 303])
    >>> e = _fakeEditor()
    >>> t4.pprint(editor=e, label="Second is name index")
    Second is name index:
      (303, 303 ('Required Ligatures On'))
    """
    
    assert len(self) == len(self._ITEMSPEC)
    printFunc = self._KEYSPEC.get('key_pprintfunc', None)
    
    if printFunc is not None:
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        label = kwArgs.pop('label', None)
        printFunc(p, self, label, **kwArgs)
    
    else:
        if 'namer' in kwArgs:
            savedNamer = self.getNamer()
            self.setNamer(kwArgs.pop('namer'))
        else:
            savedNamer = -1
        
        p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
        kwArgs.pop('label', None)
        self.__dict__.setdefault('kwArgs', {}).update(kwArgs)
        p.simple(str(self), **kwArgs)
        
        if savedNamer != -1:
            self.setNamer(savedNamer)

def M_pprintChanges(self, prior, **kwArgs):
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_strusesrepr = True),
    ...         dict(item_usenamerforstr = True, item_renumberdirect = True))
    >>> t1 = Test1(["fred", "fred", 96])
    >>> t2 = Test1(["fred", "george", 12])
    >>> t1.pprint_changes(t1, namer=namer.testingNamer())
    >>> t2.pprint_changes(t1, namer=namer.testingNamer())
    Value changed from (fred, 'fred', afii60001) to (fred, 'george', xyz13)
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label = "a"),
    ...         dict(item_label = "b"),
    ...         dict(item_label = "c"))
    >>> t3 = Test2(2, 5, 6)
    >>> t4 = Test2(1, 5, 5)
    >>> t4.pprint_changes(t3)
    Value changed from (a = 2, b = 5, c = 6) to (a = 1, b = 5, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    
    if self == prior:
        return
    
    namersReset = False
    
    if 'namer' in kwArgs:
        nm = kwArgs.pop('namer')
        savedSelfNamer = self.getNamer()
        self.setNamer(nm)
        savedPriorNamer = prior.getNamer()
        prior.setNamer(nm)
        namersReset = True
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    p.simple("Value changed from %s to %s" % (prior, self), **kwArgs)
    
    if namersReset:
        self.setNamer(savedSelfNamer)
        prior.setNamer(savedPriorNamer)

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> def f(self, **kwArgs):
    ...     t = (self[0] + self[2], self[1] - self[2], self[2])
    ...     return t != self, t
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(),
    ...         dict())
    ...     keySpec = dict(key_recalculatefunc = f)
    >>> print(Test1([2, 3, 5]).recalculated())
    (7, -2, 5)
    
    >>> print(Test1([2, 3, 5]).recalculated().recalculated())
    (12, -7, 5)
    
    >>> def g(obj, **kwArgs):
    ...     newObj = obj + kwArgs.get('delta', 0)
    ...     return newObj != obj, newObj
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_recalculatefunc = g),
    ...         dict())
    >>> print(Test2([4, 5]).recalculated())
    (4, 5)
    
    >>> print(Test2([4, 5]).recalculated(delta=5))
    (9, 5)
    
    >>> class Test3(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label = "a", item_recalculatefunc = g),
    ...         dict(item_label = "b"),
    ...         dict(item_label = "c"))
    >>> print(Test3(3, 4, 5).recalculated(delta=-10))
    (a = -7, b = 4, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    fWhole = self._KEYSPEC.get('key_recalculatefunc', None)
    fWholePartial = self._KEYSPEC.get('key_recalculatefunc_partial', None)
    
    if fWhole is not None:
        changed, vNew = fWhole(self, **kwArgs)
    
    else:
        if fWholePartial is not None:
            changed, vNew = fWholePartial(self, **kwArgs)
        
        for i, t in enumerate(zip(vNew, self._ITEMSPEC)):
            obj, kid = t
            
            if obj is not None:
                fIndiv = kid.get('item_recalculatefunc', None)
                
                if fIndiv is not None:
                    changed, newObj = fIndiv(obj, **kwArgs)
                    
                    if changed:
                        vNew[i] = newObj
                
                elif kid.get(
                  'item_recalculatedeep',
                  kid.get('item_followsprotocol', False)):
                    
                    vNew[i] = obj.recalculated(**kwArgs)
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_scaledirect = True),
    ...         dict(item_scaledirect = True, item_python3rounding = True),
    ...         dict(item_scaledirectnoround = True),
    ...         dict(item_followsprotocol = True))
    >>> t1 = Test([4.0, 7, 7, 7.0, None])
    >>> print(t1.scaled(1.25))
    (4.0, 9, 9, 8.75, None)
    
    >>> print(Test([1.0, 2.0, 2.0, 3.0, t1]).scaled(1.25))
    (1.0, 3.0, 2.0, 3.75, (4.0, 9, 9, 8.75, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label = "a"),
    ...         dict(item_label = "b", item_scaledirect = True),
    ...         dict(item_label = "c", item_scaledirectnoround = True))
    >>> t2 = Test2(3, 5, 7)
    >>> print(t2.scaled(0.5))
    (a = 3, b = 3, c = 3.5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    
    if scaleFactor == 1.0:
        return self  # don't need deep copy, since it's immutable
    
    vNew = list(self)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_scaledeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.scaled(scaleFactor, **kwArgs)
            
            elif kid.get('item_scaledirectnoround', False):
                vNew[i] *= scaleFactor
            
            elif kid.get('item_scaledirect', False):
                roundFunc = kid.get('item_roundfunc', None)
                
                if roundFunc is None:
                    if kid.get('item_python3rounding', False):
                        roundFunc = utilities.newRound
                    else:
                        roundFunc = utilities.oldRound
                
                vNew[i] = roundFunc(scaleFactor * obj, castType=type(obj))
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_renumberstoragedirect = True),
    ...         dict(item_followsprotocol = True))
    
    >>> k1 = Test1([20, None])
    >>> k2 = Test1([35, k1])
    
    >>> print(k1.storageRenumbered(storageDelta=50))
    (70, None)
    >>> print(k2.storageRenumbered(storageDelta=50))
    (85, (70, None))
    
    >>> print(k1.storageRenumbered(oldToNew={20: 400}))
    (400, None)
    >>> print(k2.storageRenumbered(oldToNew={20: 400}))
    (35, (400, None))
    >>> print(k2.storageRenumbered(oldToNew={20: 400}, keepMissing=False))
    (None, (400, None))
    
    >>> def f(n, **k):
    ...     return n + (150 if n % 10 else 88)
    >>> print(k1.storageRenumbered(storageMappingFunc=f))
    (108, None)
    >>> print(k2.storageRenumbered(storageMappingFunc=f))
    (185, (108, None))
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b", item_renumberstoragedirect = True),
    ...       dict(item_label = "c"))
    >>> t = Test2(5, 5, 5)
    >>> print(t.storageRenumbered(storageDelta=100))
    (a = 5, b = 105, c = 5)
    >>> print(t.storageRenumbered(oldToNew={5:30}))
    (a = 5, b = 30, c = 5)
    >>> print(t.storageRenumbered(oldToNew={10:29}))
    (a = 5, b = 5, c = 5)
    >>> print(t.storageRenumbered(oldToNew={10:29}, keepMissing=False))
    (a = 5, b = None, c = 5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
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
    
    vNew = [None] * len(self)
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get(
              'item_renumberstoragedeep',
              kid.get('item_followsprotocol', False)):
                
                vNew[i] = obj.storageRenumbered(**kwArgs)
            
            elif kid.get('item_renumberstoragedirect', False):
                vNew[i] = storageMappingFunc(obj, **kwArgs)
            
            else:
                vNew[i] = self[i]
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

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
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(
    ...             item_representsx = True,
    ...             item_transformcounterpartfunc = (lambda x: x[2])),
    ...         dict(
    ...             item_representsy = True,
    ...             item_transformcounterpartfunc = (lambda x: x[1])),
    ...         dict(item_representsy = True),
    ...         dict(item_representsy = True, item_python3rounding = True),
    ...         dict(item_representsy = True, item_transformnoround = True))
    >>> print(Test([10, -4, -3, -0.75, -0.75, -0.75]).transformed(m))
    (10, 9, -2, 3.0, 2.0, 2.5)
    
    >>> class Test2(collections.namedtuple("_NT", "a b c"), metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(
    ...             item_label = "a",
    ...             item_representsx = True,
    ...             item_transformcounterpartfunc = (lambda x: x.c)),
    ...         dict(
    ...             item_label = "b"),
    ...         dict(
    ...             item_label = "c",
    ...             item_representsy = True,
    ...             item_transformcounterpartfunc = (lambda x: x.a)))
    >>> mRotate = matrix.Matrix.forRotation(90)
    >>> print(Test2(-5, 4, 3).transformed(mRotate))
    (a = -3, b = 4, c = -5)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    vNew = list(self)
    mp = matrixObj.mapPoint
    
    for i, t in enumerate(zip(self, self._ITEMSPEC)):
        obj, kid = t
        
        if obj is not None:
            if kid.get('item_followsprotocol', False):
                vNew[i] = obj.transformed(matrixObj, **kwArgs)
            
            else:
                if kid.get('item_transformnoround', False):
                    roundFunc = (lambda x,**k: x)  # ignores the castType
                elif 'item_roundfunc' in kid:
                    roundFunc = kid['item_roundfunc']
                elif kid.get('item_python3rounding', False):
                    roundFunc = utilities.newRound
                else:
                    roundFunc = utilities.oldRound
                
                cptFunc = kid.get('item_transformcounterpartfunc', None)
                
                if cptFunc is not None:
                    cptValue = cptFunc(self)
                else:
                    cptValue = 0
                
                if kid.get('item_representsx', False):
                    vNew[i] = roundFunc(
                      mp((obj, cptValue))[0],
                      castType=type(obj))
                
                elif kid.get('item_representsy', False):
                    vNew[i] = roundFunc(
                      mp((cptValue, obj))[1],
                      castType=type(obj))
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    """
    
    assert len(self) == len(self._ITEMSPEC)
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def SM_deepcopy(self, memo=None):
    """
    Make a deep copy, which for this type of object is the same as a shallow
    copy (no attributes, and the object is immutable).
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    """
    
    assert len(self) == len(self._ITEMSPEC)
    
    try:
        return type(self)(vNew)
    except TypeError:
        return type(self)(*vNew)  # named tuples initialize this way

def SM_repr(self):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (dict(), dict(), dict(item_followsprotocol = True))
    >>> t1 = Test([4, 'fred', None])
    >>> print(repr(t1))
    Test((4, 'fred', None))
    
    >>> t1 == eval(repr(t1))
    True
    
    >>> t2 = Test([10, 'george', t1])
    >>> print(repr(t2))
    Test((10, 'george', Test((4, 'fred', None))))
    
    >>> t2 == eval(repr(t2))
    True
    
    >>> _NT = collections.namedtuple("_NT", "a b c")
    >>> class Test2(_NT, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...       dict(item_label = "a"),
    ...       dict(item_label = "b"),
    ...       dict(item_label = "c"))
    >>> t3 = Test2(4, 'hi there', -2.25)
    >>> t3 == eval(repr(t3))
    True
    """
    
    assert len(self) == len(self._ITEMSPEC)
    
    try:
        self._make
        r = "%s%r" % (self.__class__.__name__, tuple(self))
    
    except AttributeError:
        r = "%s(%r)" % (self.__class__.__name__, tuple(self))
    
    return r

def SM_str(self):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(),
    ...         dict(item_strusesrepr = True),
    ...         dict(item_renumberdirect = True),
    ...         dict(item_usenamerforstr = True, item_renumberdirect = True))
    >>> t1 = Test1(["fred", "fred", 96, 96])
    >>> t1.setNamer(namer.testingNamer())
    >>> print(t1)
    (fred, 'fred', 96, afii60001)
    
    >>> _NT = collections.namedtuple("_NT", ['red', 'green', 'blue'])
    >>> class Test2(_NT, metaclass=FontDataMetaclass):
    ...     itemSpec = (
    ...         dict(item_label = "Red level"),
    ...         dict(item_label = "Green level"),
    ...         dict(item_label = "Blue level"))
    >>> print(Test2(255, 0, 128))
    (Red level = 255, Green level = 0, Blue level = 128)
    """
    
    assert len(self) == len(self._ITEMSPEC)
    sv = []
    selfNamer = getattr(self, '_namer', None)
    
    try:
        t = self._fields
        
        labels = [
          kid.get('item_label', d)
          for d, kid in zip(t, self._ITEMSPEC)]
    
    except AttributeError:
        labels = [None] * len(self)
    
    for obj, kid, label in zip(self, self._ITEMSPEC, labels):
        f = (repr if kid.get('item_strusesrepr', False) else str)
        
        if obj is None:
            sv.append("None" if label is None else "%s = None" % (label,))
        
        elif (
          kid.get('item_usenamerforstr', False) and
          (selfNamer is not None)):
            
            if kid.get(
              'item_renumberdeep',
              kid.get('item_followsprotocol', False)):
                
                savedNamer = obj.getNamer()
                obj.setNamer(selfNamer)
                
                sv.append(
                  str(obj) if label is None
                  else "%s = %s" % (label, obj))
                
                obj.setNamer(savedNamer)
            
            elif kid.get('item_renumberdirect', False):
                s = selfNamer.bestNameForGlyphIndex(obj)
                sv.append(s if label is None else "%s = %s" % (label, s))
            
            else:
                sv.append(
                  f(obj) if label is None
                  else "%s = %s" % (label, f(obj)))
        
        elif kid.get('item_renumbernamesdirect', False):
            kwa = self.__dict__.get('kwArgs', {})
            f = functools.partial(utilities.nameFromKwArgs, **kwa)
            
            if label is None:
                sv.append(f(obj))
            else:
                sv.append("%s = %s" % (label, f(obj)))
        
        else:
            sv.append(
              f(obj) if label is None
              else "%s = %s" % (label, f(obj)))
    
    final = (',' if len(self) == 1 else '')
    return "(%s%s)" % (', '.join(sv), final)

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
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
    stdClasses = (tuple, frozenset, int, float, str, bytes, object)
    
    for mKey, m in _methodDict.items():
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
            cd[mKey] = m

def _validateItemSpec(v):
    """
    Make sure only known keys are included in the itemSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> v = ({'item_followsprotocol': True},)
    >>> _validateItemSpec(v)
    >>> v = ({'item_bollowsprotocol': True},)
    >>> _validateItemSpec(v)
    Traceback (most recent call last):
      ...
    ValueError: Unknown itemSpec keys: ['item_bollowsprotocol']
    """
    
    for d in v:
        unknownKeys = set(d) - validItemSpecKeys
        
        if unknownKeys:
            raise ValueError(
              "Unknown itemSpec keys: %s" %
              (sorted(unknownKeys),))

def _validateKeySpec(d):
    """
    Make sure only known keys are included in the keySpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> d = {'key_recalculatefunc': None}
    >>> _validateKeySpec(d)
    >>> d = {'key_decalculatefunc': True}
    >>> _validateKeySpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown keySpec keys: ['key_decalculatefunc']
    """
    
    unknownKeys = set(d) - validKeySpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown keySpec keys: %s" % (sorted(unknownKeys),))
    
    if 'item_prevalidatedglyphset' in d:
        if not d.get('item_renumberdirect', False):
            raise ValueError(
              "Prevalidated glyph set provided for values, but values "
              "are not glyph indices!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for key-like classes. The base class should be tuple or a class
    created via collections.namedtuple.
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_ITEMSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            IS = list(c._ITEMSPEC)
            IS.extend(classdict.pop('itemSpec', []))
            classdict['_ITEMSPEC'] = classdict['_EXTRA_SPEC'] = IS
            _validateItemSpec(IS)
            KS = c._KEYSPEC.copy()
            extraKeySpecs = classdict.pop('keySpec', {})
            KS.update(extraKeySpecs)
            classdict['_KEYSPEC'] = classdict['_MAIN_SPEC'] = KS
            _validateKeySpec(KS)
        
        else:
            IS = classdict['_ITEMSPEC'] = classdict.pop('itemSpec', ())
            classdict['_EXTRA_SPEC'] = IS
            _validateItemSpec(IS)
            KS = classdict['_KEYSPEC'] = classdict.pop('keySpec', {})
            classdict['_MAIN_SPEC'] = KS
            _validateKeySpec(KS)
        
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
