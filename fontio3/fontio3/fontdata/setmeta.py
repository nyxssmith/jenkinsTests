#
# setmeta.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for fontdata sets (whether mutable or immutable). Clients wishing to
add fontdata capabilities to their set classes should specify FontDataMetaclass
as the metaclass. The following class attributes are used to control the
various behaviors and attributes of instances of the class:
    
``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``setSpec``
    A dict of specification information for the set, where the keys and their
    associated values are defined in the following list. The listed defaults
    apply if the specified key is not present in setSpec.

    Note keys starting with ``item_`` relate to individual set items, while
    keys starting with ``set_`` relate to the set as a whole. Also note that in
    general, functions have higher priority than deep calls, and ``None``
    values are never passed to either functions or deep calls.

    If a ``setSpec`` is not provided, an empty one will be used, and all
    defaults listed below will be in force.
        
    ``item_asimmutabledeep``
        If True then set values have their own ``asImmutable()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_asimmutablefunc``
        A function called on a set value and returning an immutable version of
        that value. Since set values are already supposed to be immutable,
        because of the nature of sets, you may be wondering why this flag is
        needed. It is because objects contained in sets may contain attributes
        that are not immutable (they don't contribute to the results of the
        ``hash()`` call). Using an ``item_asimmutablefunc`` can make sure the
        caller gets something guaranteed immutable.
        
        There is no default.
    
    ``item_coalescedeep``
        If True then set values have their own ``coalesced()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_compactdeep``
        If True then set values have their own ``compacted()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepconverterfunc``
        If present, then ``item_followsprotocol`` should also be True. In this
        case, if a protocol deep function is called on a set value and fails,
        this converter function will be called to get an object that will
        succeed with the call. This function takes the set value, and optional
        keyword arguments.

        A note about special methods and converters: if a set value is deep and
        uses a converter function, then any call to a special method (such as
        ``__deepcopy__()`` or ``__str__()``) on that set value will only have
        access to the optional keyword arguments if an attribute named
        '``kwArgs``' was set in the object's ``__dict__``. You should only do
        this when the extra arguments are needed by the converter function.
        
        There is no default.
    
    ``item_deepcopydeep``
        If True then set values have their own ``__deepcopy__()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepcopyfunc``
        A function that is called to deep-copy set values. It is called with
        two arguments: the value and a ``memo`` dict.
        
        There is no default.
    
    ``item_enablecyclechecktag``
        If specified (which is only allowed for deep set values) then a cyclic
        object check will be made for this set's values during ``isValid()``
        execution. A parent trace will be provided in a passed keyword argument
        called ``activeCycleCheck``, which will be a dict mapping tags to lists
        of parent objects. The tag associated with this
        ``item_enablecyclechecktag`` is what will be used to look up the
        specific parent chain for all set values.
        
        Default is ``None``.
    
    ``item_followsprotocol``
        If True then set values are themselves Protocol objects, and have all
        the Protocol methods.

        Note that this may be overridden by explicitly setting a desired "deep"
        flag to False. So, for instance, if set values are not to have
        ``compacted()`` calls, then the ``setSpec`` should have this flag set
        to True and ``item_compactdeep`` set to False.
        
        Default is False.
    
    ``item_inputcheckfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate as a set member.
        
        There is no default.
    
    ``item_islivingdeltas``
        If True then set values will be included in the output from a call to
        ``gatheredLivingDeltas()``.
        
        Default is False.
    
    ``item_islookup``
        If True then set values will be included in the output from a call to
        ``gatheredRefs()``.
        
        Default is False.
    
    ``item_isoutputglyph``
        If True then set values are treated as output glyphs. This means they
        will not be included in the output of a ``gatheredInputGlyphs()`` call,
        and they will be included in the output of a ``gatheredOutputGlyphs()``
        call. Note that ``item_renumberdirect`` must also be set; otherwise set
        values will not be added, even if this flag is True.
        
        Default is False.
    
    ``item_mergedeep``
        If True then set values have their own ``merged()`` methods. Note that
        these methods may not end up being called, even if this flag is True,
        if the ``merged()`` method is called with the ``replaceWhole`` keyword
        argument set to True.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintdeep``
        If True then set values will be pretty-printed via a call to their own
        ``pprint()`` methods. If False, and a ``set_pprintfunc`` or
        ``item_pprintfunc`` is specified, that function will be used.
        Otherwise, each item will be printed via the
        :py:meth:`~fontio3.utilities.pp.PP.simple` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintdiffdeep``
        If True then set values have their own ``pprint_changes()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintfunc``
        A function that is called to pretty-print set values. It is called with
        two arguments: the :py:class:`~fontio3.utilities.pp.PP` instance and a
        set value.
        
        There is no default.
    
    ``item_prevalidatedglyphset``
        A set or frozenset containing glyph indices which are to be considered
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
        If True then set values have their own ``recalculated()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_recalculatefunc``
        A function taking one positional argument, the object. Additional
        keyword arguments (for example, ``editor``) may be specified. This
        function returns a pair: the first value is True or False, depending on
        whether the recalculated object's value actually changed. The second
        value is the new recalculated object to be used (if the first value was
        True).
        
        There is no default.
    
    ``item_renumbercvtsdeep``
        If True then set values have their own ``cvtsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbercvtsdirect``
        If True then set values are interpreted as CVT values, and are subject
        to renumbering if the ``cvtsRenumbered()`` method is called.
        
        Default is False.
    
    ``item_renumberdeep``
        If True then set values have their own ``glyphsRenumbered()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberdirect``
        If True then all set items are interpreted as glyph indices. Any method
        that uses glyph indices (e.g. ``glyphsRenumbered()`` or
        ``gatheredInputGlyphs()``) looks at this flag to ascertain whether set
        values are available for processing.
        
        Default is False.
    
    ``item_renumberfdefsdeep``
        If True then set values have their own ``fdefsRenumbered()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdirect``
        If True then set values are interpreted as function definition numbers
        (FDEF indices), and are subject to renumbering if the
        ``fdefsRenumbered()`` method is called.
        
        Default is False.
    
    ``item_renumbernamesdeep``
        If True then set values have their own ``namesRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdirect``
        If True then non-``None`` set values are interpreted as indices
        into the ``'name'`` table, and are subject to being renumbered via a
        ``namesRenumbered()`` call.
        
        Default is False.
    
    ``item_renumberpcsdeep``
        If True then the set values have their own ``pcsRenumbered()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpcsdirect``
        If True then set values are themselves PC values. These values will be
        directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``.
        
        Default is False.
    
    ``item_renumberpointsdeep``
        If True then set values understand the ``pointsRenumbered()`` protocol.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpointsdirect``
        If True then set values are themselves point indices. Note that if this
        is used, the ``kwArgs`` passed into the ``pointsRenumbered()`` call
        must include ``glyphIndex`` which is used to index into that method's
        ``mapData``.
        
        Default is False.
    
    ``item_renumberstoragedeep``
        If True then set values have their own ``storageRenumbered()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedirect``
        If True then the set values are interpreted as storage indices, and are
        subject to renumbering if the ``storageRenumbered()`` method is called.
        
        Default is False.
    
    ``item_representsx``
        If True then non-``None`` set values are interpreted as x-coordinates.
        This knowledge is used by the ``scaled()`` method, in conjunction with
        the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that
        method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated y-coordinate value will be
        forced to zero.
        
        Default is False.
    
    ``item_representsy``
        If True then non-``None`` set values are interpreted as y-coordinates.
        This knowledge is used by the ``scaled()`` method, in conjunction with
        the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that
        method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated x-coordinate value will be
        forced to zero.
        
        Default is False.
    
    ``item_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``item_scaledeep``
        If True then set entries have their own ``scaled()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_scaledirect``
        If True then non-``None`` set entries will be scaled by the
        ``scaled()`` method, with the results rounded to the nearest integral
        value (with .5 cases controlled by ``item_python3rounding``); if this
        is not desired, the client should instead specify the
        ``item_scaledirectnoround`` flag.

        The type of a rounded scaled value will be the type of the original
        value.
        
        Default is False.
    
    ``item_scaledirectnoround``
        If True then set entries will be scaled by the ``scaled()`` method. No
        rounding will be done on the result; if rounding to integral values is
        desired, use the ``item_scaledirect`` flag instead.

        The type of a non-rounded scaled value will be ``float``.
        
        Default is False.
    
    ``item_strusesrepr``
        If True then the string representation for items in the set will be
        created via ``repr()``, not ``str()``.
        
        Default is False.
    
    ``item_transformnoround``
        If True, values after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the values will always
        be left as type ``float``, irrespective of the original type. This
        differs from the default case, where rounding will be used but the
        rounded result will be the same type as the original value.

        Note the absence of an ``item_transformdirect`` flag. Calls to the
        ``transformed()`` method will only affect non-``None`` set values if
        one or more of the ``item_representsx`` or ``item_representsy`` flags
        are set (or, of course, the ``item_followsprotocol`` flag).
        
        Default is False.
    
    ``item_usenamerforstr``
        If this flag and ``item_renumberdirect`` are both True, and a
        :py:class:`~fontio3.utilities.namer.Namer` is available either from a
        :``setNamer()`` call or via
        keyword arguments, then that ``Namer`` will be used for generating the
        strings produced via the ``__str__()`` special method.
        
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
        CVT index. (Note that values of type ``float`` representing integers
        are fine, and will not trigger this)
        
        Default is ``'G0027'``.
    
    ``item_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is used for a
        glyph index. (Note that values of type ``float`` representing integers
        are fine, and will not trigger this)
        
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
        If True then set values have their own ``isValid()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_validatefunc``
        A function taking one positional argument, a set value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` **will** be passed into this function, unlike most other
        actions.

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``item_validatefunc_partial`` instead.
        
        There is no default.
    
    ``item_validatefunc_partial``
        A function taking one positional argument, a set value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` **will** be passed into this function, unlike most other
        actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use an ``item_validatefunc`` instead.
        
        There is no default.
    
    ``item_wisdom``
        A string encompassing a sensible description of the value, including
        how it is used.
        
        There is, alas, no default for wisdom.
    
    ``set_asimmutablefunc``
        A function to create an immutable version of the set. This function
        takes the set as the sole positional argument, as well as the usual
        ``kwArgs``, and returns the immutable representation.
        
        There is no default.
    
    ``set_compactremovesfalses``
        If True then any values whose ``bool()`` is False will be removed from
        the set in the output of a ``compacted()`` call.
        
        Default is False.
    
    ``set_maxcontextfunc``
        A function to determine the maximum context for the set. This function
        takes a single argument, the set itself.
        
        There is no default.
    
    ``set_mergechecknooverlap``
        If True, and there exists non-empty overlap in ``self`` and ``other``
        at ``merged()`` time, a ``ValueError`` will be raised.
        
        Default is False.
    
    ``set_ppoptions``
        If specified, it should be a dict whose keys are valid options to be
        passed in for construction of a :py:class:`~fontio3.utilities.pp.PP`
        instance, and whose values are as appropriate. This can be used to make
        a custom ``noDataString``, for instance.
        
        There is no default.
    
    ``set_pprintdifffunc``
        A function to pretty-print differences between two entire sets. The
        function (which can be an unbound method, as can many other ``setSpec``
        values) takes at least three arguments: the
        :py:class:`~fontio3.utilities.pp.PP` object, the current set, and the
        prior set. Other keyword arguments may be specified, as needed.
        
        There is no default.
    
    ``set_pprintfunc``
        A function taking two arguments: a :py:class:`~fontio3.utilities.pp.PP`
        instance, and the set as a whole.
        
        There is no default.
    
    ``set_recalculatefunc``
        If specified, a function taking one positional argument, the whole set.
        Additional keyword arguments (for example, ``editor``) may be
        specified.

        The function returns a pair: the first value is True or False,
        depending on whether the recalculated list's value actually changed.
        The second value is the new recalculated object to be used (if the
        first value was True).

        If a ``set_recalculatefunc`` is provided then no individual
        ``item_recalculatefunc`` calls will be made. If you want them to be
        made, use a ``set_recalculatefunc_partial`` instead.
        
        There is no default.
    
    ``set_recalculatefunc_partial``
        A function taking one positional argument, the whole set, and optional
        additional keyword arguments. The function should return a pair: the
        first value is True or False, depending on whether the recalculated
        list's value actually changed. The second value is the new recalculated
        object to be used (if the first value was True).

        After the ``set_recalculatefunc_partial`` is done, individual
        ``item_recalculatefunc`` calls will be made. This allows you to "divide
        the labor" in useful ways.
        
        There is no default.
    
    ``set_showpresorted``
        If True, set items displayed via ``__str__()`` or the pretty- printing
        methods will be sorted before their conversion into a string
        representation. For contrast, see the ``set_showsorted`` flag.
        
        Default is False.
    
    ``set_showsorted``
        If True, set items displayed via ``__str__()`` or the pretty- printing
        methods will be sorted after their conversion into a string
        representation. For contrast, see the ``set_showpresorted`` flag.
        
        Default is False.
    
    ``set_validatefunc``
        A function taking one positional argument, the whole set and optional
        additional keyword arguments. The function returns True if the set is
        valid, and False otherwise.

        Note that this keyword prevents any ``item_validatefuncs`` from being
        run. If you want to run those as well, then use the
        ``set_validatefunc_partial`` keyword instead.
        
        There is no default.
    
    ``set_validatefunc_partial``
        A function taking one positional argument, the whole set, and optional
        additional keyword arguments. The function returns True if the set is
        valid, and False otherwise. Any ``item_validatefuncs`` will also be run
        to determine the returned True/False value, so this function should
        focus on overall set validity.

        If you want this function to do everything without allowing any
        ``item_validatefuns`` to be run, then use the ``set_validatefunc``
        keyword instead.
        
        There is no default.
    
    ``set_wisdom``
        A string encompassing a sensible description of the object as a whole,
        including how it is used.
        
        There is, alas, no default for wisdom.
"""

# System imports
import functools
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

validSetSpecKeys = frozenset([
  'item_asimmutabledeep',
  'item_asimmutablefunc',
  'item_coalescedeep',
  'item_compactdeep',
  'item_deepconverterfunc',
  'item_deepcopydeep',
  'item_deepcopyfunc',
  'item_enablecyclechecktag',
  'item_followsprotocol',
  'item_inputcheckfunc',
  'item_islivingdeltas',
  'item_islookup',
  'item_isoutputglyph',
  'item_mergedeep',
  'item_pprintdeep',
  'item_pprintdiffdeep',
  'item_pprintfunc',
  'item_pprintlabelfunc',
  'item_pprintlabelfuncneedsobj',
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
  'item_wisdom',
  
  'set_asimmutablefunc',
  'set_compactremovesfalses',
  'set_maxcontextfunc',
  'set_mergechecknooverlap',
  'set_ppoptions',
  'set_pprintdifffunc',
  'set_pprintfunc',
  'set_recalculatefunc',
  'set_recalculatefunc_partial',
  'set_showpresorted',
  'set_showsorted',
  'set_validatefunc',
  'set_validatefunc_partial',
  'set_wisdom'])

# -----------------------------------------------------------------------------

#
# Methods
#

def M_asImmutable(self, **kwArgs):
    """
    Returns a ``frozenset`` with the object's contents.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: The immutable version (or ``self``, if it's already immutable).
    :raises AttributeError: If a non-Protocol object is used for a set
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id(...)`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
        
        This is optional; if one is not provided, a temporary one will be used.
    
    >>> class BottomT(frozenset, metaclass=FontDataMetaclass): pass
    >>> class TopT(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> b1 = BottomT([1, 2, 3])
    >>> b2 = BottomT([4, 5, 6])
    >>> t = TopT([b1, b2])
    >>> t.asImmutable() == (
    ...   'TopT',
    ...   frozenset({
    ...     ('BottomT', frozenset({1, 2, 3})),
    ...     ('BottomT', frozenset({4, 5, 6}))}))
    True
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass): pass
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> t.asImmutable() == (
    ...   'Top',
    ...   frozenset({
    ...     ('Bottom', frozenset({1, 2, 3})),
    ...     ('Bottom', frozenset({4, 5, 6}))}))
    True
    
    >>> class LPA(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someSet': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someSet', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA(set([3, 4, 6]), someSet=t, someNumber=5)
    >>> obj1.asImmutable() == ((
    ...   'LPA',
    ...   frozenset({3, 4, 6})),
    ...   ('someSet', (
    ...     'Top',
    ...     frozenset({
    ...       ('Bottom', frozenset({1, 2, 3})),
    ...       ('Bottom', frozenset({4, 5, 6}))}))),
    ...   ('someNumber', 5))
    True
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    
    >>> Test2([5, None, Test1([6, 7])]).asImmutable() == (
    ...   'Test2',
    ...   frozenset({('Test1', Test1((5,))), ('Test1', Test1((6, 7))), None}))
    True
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_asimmutablefunc = (lambda x,**k: tuple(sorted(x))))
    
    >>> t3 = Test3({4, 2, -1, 5, 19})
    >>> t3.asImmutable()
    (-1, 2, 4, 5, 19)
    """
    
    SS = self._SETSPEC
    fWhole = SS.get('set_asimmutablefunc', None)
    
    if fWhole is not None:
        return fWhole(self, **kwArgs)
    
    AS = self._ATTRSPEC
    f = SS.get('item_asimmutablefunc', None)
    
    if f is not None:
        t = (
          type(self).__name__,
          frozenset(None if obj is None else f(obj) for obj in self))
    
    elif SS.get('item_asimmutabledeep', SS.get('item_followsprotocol', False)):
        cf = SS.get('item_deepconverterfunc', None)
        memo = kwArgs.get('memo', {})
        v = []
        
        for obj in self:
            if obj is None:
                v.append(None)
                continue
            
            objID = id(obj)
            
            if objID not in memo:
                try:
                    boundMethod = obj.asImmutable
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).asImmutable
                    else:
                        raise
                
                memo[objID] = boundMethod(**kwArgs)
            
            v.append(memo[objID])
        
        t = (type(self).__name__, frozenset(v))
    
    else:
        t = (type(self).__name__, frozenset(self))
    
    tAttr = attrhelper.M_asImmutable(
      self._ATTRSPEC,
      self._ATTRSORT,
      self.__dict__,
      **kwArgs)
    
    return ((t,) + tAttr if tAttr else t)

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
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...   setSpec = dict(
    ...     item_inputcheckfunc = (lambda x, **k: bool(x % 2)))
    ...   attrSpec = dict(
    ...     a = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: 10 <= x < 20)))
    >>> x = Test1([1, 3, 5], a=14)
    >>> x.checkInput(4)
    False
    >>> x.checkInput(5)
    True
    >>> x.checkInput(31, attrName='a')
    False
    >>> x.checkInput(12, attrName='a')
    True
    """
    
    # This method is an odd one, because it just checks one thing in the
    # interest of speed. So we short-circuit to the attribute check if there is
    # a 'attrName' kwArg specified.
    
    if kwArgs.get('attrName', ''):
        return attrhelper.M_checkInput(
          self._ATTRSPEC,
          self.__dict__,
          valueToCheck,
          **kwArgs)
    
    SS = self._SETSPEC
    f = SS.get('item_inputcheckfunc', None)
    
    if f is None:
        return True
    
    return f(valueToCheck, **kwArgs)

def M_coalesced(self, **kwArgs):
    """
    Return new object representing self with duplicates coerced to the
    same object.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    While sets themselves do not need coalescing (since the hashing implicit in
    their operation guarantees that there are no equal-but-distinct objects),
    deep coalescing is still needed in case the set's items themselves have
    mutable attributes.
    
    Font data often comprises multiple parts that happen to be the same. One
    example here is the platform 0 (Unicode) and platform 3 (Microsoft)
    ``cmap`` subtables, which often have exactly the same data. The binary
    format for the ``cmap`` table permits sharing here (each table is actually
    an offset, so the two offsets here can refer to the same data). This method
    is used to force this sharing to occur, if possible.

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
    
    >>> class Bottom(set, metaclass=FontDataMetaclass): pass
    >>> class Middle(frozenset, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {'attr_followsprotocol': True}}
    ...     __hash__ = frozenset.__hash__
    >>> class Top(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> m1 = Middle([1, 2, 3], x=Bottom([7, 8, 9]))
    >>> m2 = Middle([4, 5, 6], x=Bottom([7, 8, 9]))
    >>> t = Top([m1, m2])
    >>> list(t)[0].x is list(t)[1].x
    False
    >>> tc = t.coalesced()
    >>> tc == t
    True
    >>> list(tc)[0].x is list(tc)[1].x
    True
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> obj = Test2([5, Test1([5])])
    >>> len(obj)
    2
    >>> len(obj.coalesced())
    1
    """
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    SS = self._SETSPEC
    vNew = [None] * len(self)
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    
    coalesceDeep = SS.get(
      'item_coalescedeep',
      SS.get('item_followsprotocol', False))
    
    immutFunc = SS.get('item_asimmutablefunc', None)
    
    immutDeep = SS.get(
      'item_asimmutabledeep',
      SS.get('item_followsprotocol', False))
    
    cf = SS.get('item_deepconverterfunc', None)
    
    # First do set objects
    for i, obj in enumerate(self):
        if obj is not None:
            if coalesceDeep:
                objID = id(obj)
                
                if objID in cwc:
                    obj = cwc[objID]
                
                else:
                    try:
                        boundMethod = obj.coalesced
                
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).coalesced
                        else:
                            raise
                
                    obj = boundMethod(pool=pool, **kwArgs)
                    cwc[objID] = obj
            
            if immutFunc is not None:
                vNew[i] = pool.setdefault(immutFunc(obj), obj)
            elif immutDeep:
                vNew[i] = pool.setdefault(obj.asImmutable(**kwArgs), obj)
            else:
                vNew[i] = pool.setdefault(obj, obj)
    
    # Now do attributes
    dNew = attrhelper.M_coalesced(
      self._ATTRSPEC,
      self.__dict__,
      pool,
      **kwArgs)
    
    # Construct and return the result
    r = type(self)(vNew, **dNew)
    cwc[id(self)] = r
    return r

def M_compacted(self, **kwArgs):
    """
    Returns a new object which has been compacted.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new compacted object
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    *Compacting* means that (if indicated by the presence of the
    ``set_compactremovesfalses`` flag in the ``setSpec``) members of the
    sequence for which the ``bool()`` result is False are removed.
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_compactremovesfalses = True,
    ...         set_showsorted=True)
    >>> t1 = Test1([3, 0, False, (), None, 4])
    >>> print(t1.compacted())
    {3, 4}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_compactremovesfalses = True,
    ...         set_showsorted = True)
    ...     attrSpec = dict(x = dict(attr_followsprotocol = True))
    >>> t2 = Test2([t1, None], x = t1)
    >>> print(t2)
    {{(), 0, 3, 4, None}, None}, x = {(), 0, 3, 4, None}
    >>> print(t2.compacted())
    {{3, 4}}, x = {3, 4}
    
    >>> class Test3(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(seq_compactremovesfalses = True)
    >>> class Test4(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test3([x])),
    ...         item_followsprotocol = True)
    
    >>> Test4([0, Test3([False, (), '', 9])]).compacted() == {(), (9,)}
    True
    """
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    SS = self._SETSPEC
    vDeep = SS.get('item_compactdeep', SS.get('item_followsprotocol', False))
    vFilter = SS.get('set_compactremovesfalses', False)
    cf = SS.get('item_deepconverterfunc', None)
    vNew = []
    
    # First do set objects
    for obj in self:
        if vDeep and (obj is not None):
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                try:
                    boundMethod = obj.compacted
            
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).compacted
                    else:
                        raise
            
                obj = boundMethod(**kwArgs)
                cwc[objID] = obj
        
        if (not vFilter) or obj:
            vNew.append(obj)
    
    # Now do attributes
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    r = type(self)(vNew, **dNew)
    cwc[id(self)] = r
    return r

def M_cvtsRenumbered(self, **kwArgs):
    """
    Return new object with CVT index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with CVT indices renumbered
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumbercvtsdirect = True,
    ...         set_showpresorted = True)
    
    >>> print(Test1([15, 80, None, 29]).cvtsRenumbered(cvtDelta=1000))
    {1015, 1029, 1080, None}
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> obj = Test1([25, 27, None, 26, 30])
    >>> print(obj.cvtsRenumbered(oldToNew=d))
    {30, 1000, 1001, 1025, None}
    >>> print(obj.cvtsRenumbered(oldToNew=d, keepMissing=False))
    {1000, 1001, 1025, None}
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1([10, 15, None]).cvtsRenumbered(cvtMappingFunc=f))
    {15, 910, None}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.cvtsRenumbered(cvtDelta=-3))
    {{12, 17, None}, {17, 87}, None}
    """
    
    SS = self._SETSPEC
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
    
    if SS.get('item_renumbercvtsdeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.cvtsRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = (
          (None if obj is None else obj.cvtsRenumbered(**kwArgs))
          for obj in _it())
    
    elif SS.get('item_renumbercvtsdirect', False):
        vNew = (
          (None if obj is None else cvtMappingFunc(obj, **kwArgs))
          for obj in self)
    
    else:
        vNew = iter(self)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberfdefsdirect = True,
    ...         set_showpresorted = True)
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> obj = Test1([25, 27, None, 26, 30])
    >>> print(obj.fdefsRenumbered(oldToNew=d))
    {30, 1000, 1001, 1025, None}
    >>> print(obj.fdefsRenumbered(oldToNew=d, keepMissing=False))
    {1000, 1001, 1025, None}
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1([10, 15, None]).fdefsRenumbered(fdefMappingFunc=f))
    {15, 910, None}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.fdefsRenumbered(fdefMappingFunc=f))
    {{15, 920, None}, {920, 990}, None}
    """
    
    SS = self._SETSPEC
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
    
    if SS.get('item_renumberfdefsdeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.fdefsRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = (
          (None if obj is None else obj.fdefsRenumbered(**kwArgs))
          for obj in _it())
    
    elif SS.get('item_renumberfdefsdirect', False):
        vNew = (
          (None if obj is None else fdefMappingFunc(obj, **kwArgs))
          for obj in self)
    
    else:
        vNew = iter(self)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.
    
    >>> class BottomIn(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True}
    >>> class BottomOut(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> bIn = BottomIn([20, 21])
    >>> bOut = BottomOut([32, 33])
    >>> t = Top([bIn, bOut])
    >>> sorted(t.gatheredInputGlyphs())
    [20, 21]
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True}
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    ...     attrSpec = dict(
    ...         topIrrelevant = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topDirect = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom([61, 62], bot=5)
    >>> t = Top([71, 72], topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredInputGlyphs())
    [5, 11, 61, 62]
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> sorted(Test2([15, None, Test1([9, 38])]).gatheredInputGlyphs())
    [9, 15, 38]
    """
    
    SS = self._SETSPEC
    r = set()
    
    if not SS.get('item_isoutputglyph', False):
        if SS.get('item_renumberdeep', SS.get('item_followsprotocol', False)):
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        boundMethod = obj.gatheredInputGlyphs
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).gatheredInputGlyphs
                        else:
                            raise
                    
                    r.update(boundMethod(**kwArgs))
        
        elif SS.get('item_renumberdirect', False):
            r.update(obj for obj in self if obj is not None)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8` ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual LivingDeltas objects. Since those objects are
    immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual LivingDeltas objects!
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...   setSpec = {'item_islivingdeltas': True}
    ...   attrSpec = {'a': {'attr_islivingdeltas': True}, 'b': {}}
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...   setSpec = {'item_followsprotocol': True}
    ...   attrSpec = {'c': {'attr_islivingdeltas': True}, 'd': {}}
    >>> botObj = Bottom({3, -1, 4}, a=9, b=-3)
    >>> topObj = Top({None, botObj}, c=13, d=-13)
    >>> sorted(topObj.gatheredLivingDeltas())
    [-1, 3, 4, 9, 13]
    """
    
    SS = self._SETSPEC
    r = set()
    
    if SS.get('item_islivingdeltas', False):
        for obj in self:
            if obj is not None:
                r.add(obj)
    
    elif SS.get('item_followsprotocol', False):
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is None:
                continue
            
            try:
                boundMethod = obj.gatheredLivingDeltas
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).gatheredLivingDeltas
                else:
                    raise
            
            r.update(boundMethod(**kwArgs))
    
    rAttr = attrhelper.M_gatheredLivingDeltas(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    return r | rAttr

def M_gatheredMaxContext(self, **kwArgs):
    """
    Return an integer representing the ``'OS/2'`` maximum context value.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The maximum context
    :rtype: int
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_maxcontextfunc': (lambda v: len(v) - 1)}
    >>> b1 = Bottom([1, 3, 5])
    >>> b2 = Bottom([6, 7, 8, 10, 12, 15, 2])
    >>> b1.gatheredMaxContext(), b2.gatheredMaxContext()
    (2, 6)
    
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top([b1, None], x = [8, 1, 4], y=b2).gatheredMaxContext()
    8
    >>> Top([b1, None], x = [4, 1, 4], y=b2).gatheredMaxContext()
    6
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(seq_maxcontextfunc = (lambda x,**k: x[0]))
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test2([5, None, Test1([2, 1, 34])]).gatheredMaxContext())
    5
    """
    
    SS = self._SETSPEC
    mcFunc = SS.get('set_maxcontextfunc', None)
    
    if mcFunc is not None:
        mc = mcFunc(self)
    
    elif SS.get('item_followsprotocol', False):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.gatheredMaxContext
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                    
                    yield obj
        
        mc = utilities.safeMax(
          obj.gatheredMaxContext(**kwArgs)
          for obj in _it())
    
    else:
        mc = 0
    
    return max(mc, attrhelper.M_gatheredMaxContext(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs))

def M_gatheredOutputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs generated as outputs from
    some process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> class BottomIn(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True}
    >>> class BottomOut(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> bIn = BottomIn([20, 21])
    >>> bOut = BottomOut([32, 33])
    >>> t = Top([bIn, bOut])
    >>> sorted(t.gatheredOutputGlyphs())
    [32, 33]
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    ...     attrSpec = dict(
    ...         topIrrelevant = {'attr_renumberdirect': True},
    ...         topDirect = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom([61, 62], bot=5)
    >>> t = Top([71, 72], topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredOutputGlyphs())
    [11, 61, 62, 71, 72]
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_isoutputglyph = True,
    ...         item_renumberdirect = True)
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> sorted(Test2([5, None, Test1([3, 18])]).gatheredOutputGlyphs())
    [3, 5, 18]
    """
    
    SS = self._SETSPEC
    r = set()
    
    if SS.get('item_renumberdeep', SS.get('item_followsprotocol', False)):
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is not None:
                try:
                    boundMethod = obj.gatheredOutputGlyphs
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).gatheredOutputGlyphs
                    else:
                        raise
                
                r.update(boundMethod(**kwArgs))
    
    elif (
      SS.get('item_renumberdirect', False) and
      SS.get('item_isoutputglyph', False)):
        
        r.update(obj for obj in self if obj is not None)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(item_islookup = True)
    >>> class Middle(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(item_followsprotocol = True)
    >>> sharedObj = object()
    >>> unsharedObj1, unsharedObj2 = object(), object()
    >>> b1 = Bottom([sharedObj, None, unsharedObj1])
    >>> b2 = Bottom([sharedObj, None, unsharedObj2])
    >>> m = Middle([b1, None, b2])
    >>> d = m.gatheredRefs()
    >>> id(sharedObj) in d, id(unsharedObj1) in d, id(unsharedObj2) in d
    (True, True, True)
    >>> id(None) in d  # None is not added
    False
    
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_islookup = True))
    >>> t = Top([1, 3, 5], x=m, y=object())
    >>> d = t.gatheredRefs()
    >>> id(sharedObj) in d, id(unsharedObj1) in d, id(t.y) in d
    (True, True, True)
    >>> id(None) in d  # None is not added
    False
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_islookup = True)
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> d = Test2({5, Test1([3, 4]), None}).gatheredRefs()
    >>> sorted(d.values())
    [3, 4, 5]
    """
    
    SS = self._SETSPEC
    r = {}
    
    # Note that deep objects themselves can be lookups, so the following two
    # blocks are not "if-elif" but just two "if"s.
    
    if SS.get('item_islookup', False):
        for obj in self:
            if obj is not None:
                r[id(obj)] = obj
    
    if SS.get('item_followsprotocol', False):
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is not None:
                try:
                    boundMethod = obj.gatheredRefs
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).gatheredRefs
                    else:
                        raise
                
                r.update(boundMethod(**kwArgs))
    
    r.update(
      attrhelper.M_gatheredRefs(
        self._ATTRSPEC,
        self.__dict__,
        **kwArgs))
    
    return r

def M_glyphsRenumbered(self, oldToNew, **kwArgs):
    """
    Returns a new object with glyphs renumbered.
    
    :param oldToNew: Map from old to new glyph index
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with glyphs renumbered.
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        None.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberdirect = True,
    ...         set_showpresorted = True)
    ...     attrSpec = dict(
    ...         x = dict(attr_renumberdirect = True))
    >>> t1 = Test1([10, 20, 30], x=40)
    >>> print(t1.glyphsRenumbered({10:5, 20:6, 30:7, 40:8}))
    {5, 6, 7}, x = 8
    >>> print(t1.glyphsRenumbered({10:5, 40:8}, keepMissing=True))
    {5, 20, 30}, x = 8
    >>> print(t1.glyphsRenumbered({10:5, 40:8}, keepMissing=False))
    {5}, x = 8
    
    >>> class Test2Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberdirect = True,
    ...         set_showpresorted = True)
    ...     attrSpec = dict(x = dict(attr_renumberdirect = True))
    ...     __hash__ = frozenset.__hash__
    >>> class Test2Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showpresorted = True)
    ...     attrSpec = dict(y = dict(attr_followsprotocol = True))
    >>> t2B1 = Test2Bottom([10, 20], x = 30)
    >>> t2B2 = Test2Bottom([40], x = 50)
    >>> t2B3 = Test2Bottom([], x = 60)
    >>> t2T = Test2Top([t2B1, t2B3], y=t2B2)
    >>> print(t2T)
    {{}, x = 60, {10, 20}, x = 30}, y = {40}, x = 50
    >>> print(t2T.glyphsRenumbered({10:5, 20:6, 30:7, 40:8, 50:9, 60:200}))
    {{}, x = 200, {5, 6}, x = 7}, y = {8}, x = 9
    >>> print(t2T.glyphsRenumbered({10:5, 40:8, 60:200}, keepMissing=True))
    {{}, x = 200, {5, 20}, x = 30}, y = {8}, x = 50
    >>> print(t2T.glyphsRenumbered({10:5, 40:8, 60:200}, keepMissing=False))
    {{}, x = 200, {5}, x = None}, y = {8}, x = None
    
    >>> class Test3(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test4(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test3([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    
    >>> md = {5: 10, 6: 11, 7: 12}
    >>> print(Test4({5, None, Test3([6, 7])}).glyphsRenumbered(md))
    {(10,), (11, 12), None}
    """
    
    SS = self._SETSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    
    if SS.get('item_renumberdeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.glyphsRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = [
          (None if obj is None else obj.glyphsRenumbered(oldToNew, **kwArgs))
          for obj in _it()]
    
    elif SS.get('item_renumberdirect', False):
        if keepMissing:
            vNew = [oldToNew.get(obj, obj) for obj in self]
        else:
            vNew = [oldToNew[obj] for obj in self if obj in oldToNew]
    
    else:
        vNew = self
    
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
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         deepAttr = dict(
    ...             attr_followsprotocol = True))
    >>> obj = Test1({1, 2, 3}, deepAttr=None)
    >>> obj.hasCycles()
    False
    >>> obj.deepAttr = obj
    >>> obj.hasCycles()
    True
    """
    
    # I think I've convinced myself that it's not theoretically possible for a
    # set or frozenset to contain a cycle; only the attributes need checking.
    
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
    
    ``activeCycleCheck``
        An optional dict mapping ``id()`` values of deep objects to the objects
        themselves. This is used to track deep usage; if at any level an object
        is encountered whose ``id()`` value is already present in this set, the
        function returns True. Note that it's safe to use object ID values,
        since this call does not mutate any data.
    
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
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_renumberdirect': True}
    >>> logger = utilities.makeDoctestLogger("t1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> t1 = Test1([140, 180, None, 45, 104])
    >>> t1.isValid(logger=logger, fontGlyphCount=200, editor=e)
    True
    
    >>> t1.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t1.element - ERROR - Glyph index 180 too large.
    False
    
    >>> class Test2(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> t2 = Test2([None, t1])
    >>> t2.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t2.element.element - ERROR - Glyph index 180 too large.
    False
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {'attr_followsprotocol': True},
    ...       'y': {'attr_scaledirect': True}}
    >>> logger = utilities.makeDoctestLogger("t3")
    >>> t3 = Test3([4, 12, None], x=t1, y="Fred")
    >>> t3.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t3.x.element - ERROR - Glyph index 180 too large.
    t3.y - ERROR - The value 'Fred' is not a real number.
    False
    
    >>> class Test4(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test5(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test4([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("t4+5", stream=f)
    >>> t5 = Test5({12, None, Test4([1.5, 'x', 60000, 4])})
    >>> t5.isValid(logger=logger, fontGlyphCount=10, editor=e)
    False
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    t4+5.element.[0] - ERROR - Glyph index 12 too large.
    t4+5.element.[0] - ERROR - The glyph index 1.5 is not an integer.
    t4+5.element.[1] - ERROR - The glyph index 'x' is not a real number.
    t4+5.element.[2] - ERROR - Glyph index 60000 too large.
    >>> f.close()
    
    >>> logger = utilities.makeDoctestLogger("Test6")
    >>> def _setVF(v, **kwArgs):
    ...     logger=kwArgs['logger']
    ...     if len(v) < 5:
    ...         logger.error(('Vxxxx', (), "Test6 objs must have len >= 5."))
    ...         return False
    ...     if not all(obj % 15 for obj in v if isinstance(obj, int)):
    ...         logger.error((
    ...           'Vxxxx',
    ...           (),
    ...           "No set element may be a multiple of 15."))
    ...         return False
    ...     return True
    >>> class Test6(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberdirect = True,
    ...         set_validatefunc_partial = _setVF)
    >>> obj = Test6([4, 5, 112, 34, 44, 56])
    >>> obj.isValid(logger=logger, fontGlyphCount=600, editor=e)
    True
    
    >>> Test6([4, 5]).isValid(logger=logger, fontGlyphCount=600, editor=e)
    Test6 - ERROR - Test6 objs must have len >= 5.
    False
    
    >>> obj = Test6([4, 5, 112, 34, 45, 56, 'x'])
    >>> f = io.StringIO()
    >>> logger = utilities.makeDoctestLogger("t6+3", stream=f)
    >>> obj.isValid(logger=logger, fontGlyphCount=100, editor=e)
    False
    >>> for s in sorted(f.getvalue().splitlines()): print(s)
    t6+3 - ERROR - No set element may be a multiple of 15.
    t6+3.element - ERROR - Glyph index 112 too large.
    t6+3.element - ERROR - The glyph index 'x' is not a real number.
    >>> f.close()
    
    >>> class Test7(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumbernamesdirect = True)
    >>> logger = utilities.makeDoctestLogger("isvalid_Test7")
    >>> e = _fakeEditor()
    >>> obj = Test7([303, 304])
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj.add(500)
    >>> obj.isValid(logger=logger, editor=e)
    isvalid_Test7.element - ERROR - Name table index 500 not present in 'name' table.
    False
    
    >>> class Test8(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_enablecyclechecktag = 'fred',
    ...         item_followsprotocol = True)
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_enablecyclechecktag = 'fred',
    ...             attr_followsprotocol = True))
    >>> logger2 = utilities.makeDoctestLogger("Test8")
    >>> e2 = utilities.fakeEditor(0x10000)
    >>> obj = Test8({None, Test8({None})})
    >>> obj.isValid(logger=logger2, editor=e2)
    True
    >>> obj.x = obj
    >>> obj.isValid(logger=logger2, editor=e2)
    Test8.x.x - ERROR - Circular object reference for attribute 'x'
    False
    """
    
    SS = self._SETSPEC
    r = True
    dACC = kwArgs.pop('activeCycleCheck', {})
    fontGlyphCount = utilities.getFontGlyphCount(**kwArgs) or 0x10000
    
    if 'editor' in kwArgs:
        editor = kwArgs['editor']
        hasMaxp = (editor is not None) and editor.reallyHas(b'maxp')
        
        if hasMaxp:
            if hasattr(editor.maxp, 'maxStorage'):
                maxStorage = editor.maxp.maxStorage
            else:
                maxStorage = 0x10000
            
        else:
            maxStorage = 0x10000
        
        if (editor is not None) and editor.reallyHas(b'name'):
            namesInTable = {x[-1] for x in editor.name}
        else:
            namesInTable = set()
    
    else:
        editor = None
        maxStorage = 0x10000
        namesInTable = set()
    
    logger = kwArgs.pop('logger', None)
    
    if logger is None:
        s = __name__[__name__.rfind('.')+1:]
        logger = logging.getLogger().getChild(s)
    
    wholeFunc = SS.get('set_validatefunc', None)
    indivFunc = SS.get('item_validatefunc', None)
    wholeFuncPartial = SS.get('set_validatefunc_partial', None)
    indivFuncPartial = SS.get('item_validatefunc_partial', None)
    deep = SS.get('item_validatedeep', SS.get('item_followsprotocol', False))
    pvs = SS.get('item_prevalidatedglyphset', set())
    eccTag = SS.get('item_enablecyclechecktag', None)
    
    if wholeFunc is not None:
        r = wholeFunc(self, logger=logger, **kwArgs)
    
    else:
        if wholeFuncPartial is not None:
            r = wholeFuncPartial(self, logger=logger, **kwArgs)
        
        if indivFunc is not None:
            # Note that unlike other methods, we pass None to the indivFunc,
            # since it needs to be able to say "No, None is not valid".
            
            itemLogger = logger.getChild("element")
            
            for obj in self:
                r = indivFunc(obj, logger=itemLogger, **kwArgs) and r
        
        elif deep:
            cf = SS.get('item_deepconverterfunc', None)
            itemLogger = logger.getChild("element")
            
            for obj in self:
                if obj is None:
                    continue
                
                if eccTag is not None:
                    dACC_copy = {x: y.copy() for x, y in dACC.items()}
                    eccDict = dACC_copy.setdefault(eccTag, {})
                    
                    if id(obj) not in eccDict:
                        eccDict[id(obj)] = obj
                    
                    else:
                        itemLogger.error((
                          'V0912',
                          (),
                          "Circular object reference in set"))
                        
                        return False  # aborts all other checks...
                    
                    kwArgs['activeCycleCheck'] = dACC_copy
                
                if hasattr(obj, 'isValid'):
                    r = obj.isValid(logger=itemLogger, **kwArgs) and r
                
                elif cf is not None:
                    cObj = cf(obj, **kwArgs)
                    r = cObj.isValid(logger=itemLogger, **kwArgs) and r
                
                else:
                    logger.warning((
                      'G0023',
                      (),
                      "Object is not None and not deep, and no converter "
                      "function is provided."))
        
        else:
            if indivFuncPartial is not None:
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    r = (
                      indivFuncPartial(obj, logger=itemLogger, **kwArgs) and
                      r)
            
            renumPCs = SS.get('item_renumberpcsdirect', False)
            renumPoints = SS.get('item_renumberpointsdirect', False)
            
            if SS.get('item_renumberdirect', False):
                val16 = functools.partial(
                  valassist.isNumber_integer_unsigned,
                  numBits = 16,
                  label = "glyph index")
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is None:
                        continue
                    
                    if not val16(obj, logger=itemLogger):
                        r = False
                    
                    elif (obj not in pvs) and (obj >= fontGlyphCount):
                        itemLogger.error((
                          SS.get(
                            'item_validatecode_toolargeglyph',
                            'G0005'),
                          (obj,),
                          "Glyph index %d too large."))
                        
                        r = False
            
            elif SS.get('item_renumbernamesdirect', False):
                val16 = functools.partial(
                  valassist.isFormat_H,
                  label = "name table index")
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is None:
                        continue
                    
                    if not val16(obj, logger=itemLogger):
                        r = False
                    
                    if obj not in namesInTable:
                        itemLogger.error((
                          SS.get(
                            'item_validatecode_namenotintable',
                            'G0042'),
                          (obj,),
                          "Name table index %d not present in 'name' table."))
                        
                        r = False
            
            elif SS.get('item_renumbercvtsdirect', False):
                val16 = functools.partial(
                  valassist.isNumber_integer_unsigned,
                  numBits = 16,
                  label = "CVT index")
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is not None:
                        if not val16(obj, logger=itemLogger):
                            r = False
                        
                        elif editor is not None:
                            if b'cvt ' not in editor:
                                itemLogger.error((
                                  SS.get('item_validatecode_nocvt', 'G0030'),
                                  (obj,),
                                  "CVT Index %d is being used, but the font "
                                  "has no Control Value Table."))
                                
                                r = False
                            
                            elif obj >= len(editor[b'cvt ']):
                                itemLogger.error((
                                  SS.get(
                                    'item_validatecode_toolargecvt',
                                    'G0029'),
                                  (obj,),
                                  "CVT index %d is not defined."))
                                
                                r = False
            
            elif renumPCs or renumPoints:
                val16 = functools.partial(
                  valassist.isNumber_integer_unsigned,
                  numBits = 16,
                  label = ("program counter" if renumPCs else "point index"))
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is not None:
                        if not val16(obj, logger=itemLogger):
                            r = False
            
            elif SS.get('item_renumberstoragedirect', False):
                val16 = functools.partial(
                  valassist.isNumber_integer_unsigned,
                  numBits = 16,
                  label = "storage index")
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is not None:
                        if not val16(obj, logger=itemLogger):
                            r = False
                        
                        elif obj > maxStorage:
                            itemLogger.error((
                              'E6047',
                              (obj, maxStorage),
                              "The storage index %d is greater than the "
                              "font's defined maximum of %d."))
                            
                            r = False
            
            elif (
              SS.get('item_scaledirect', False) or
              SS.get('item_scaledirectnoround', False)):
                
                valNum = functools.partial(
                  valassist.isNumber,
                  label = "FUnit distance")
                
                itemLogger = logger.getChild("element")
                
                for obj in self:
                    if obj is not None:
                        if not valNum(obj, logger=itemLogger):
                            r = False
    
    if eccTag is not None:
        dACC_copy = {x: y.copy() for x, y in dACC.items()}
        eccDict = dACC.setdefault(eccTag, {})
        eccDict[id(self)] = self
        kwArgs['activeCycleCheck'] = dACC_copy
    
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
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new object representing the merger
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showpresorted': True}
    >>> class BottomCheck(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {
    ...       'set_showpresorted': True,
    ...       'set_mergechecknooverlap': True}
    >>> print(Bottom([1, 3, 5]).merged(Bottom([2, 5, 6])))
    {1, 2, 3, 5, 6}
    >>> print(BottomCheck([1, 3, 5]).merged(BottomCheck([2, 5, 6])))
    Traceback (most recent call last):
      ...
    ValueError: No set overlaps allowed!
    
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showpresorted': True}
    ...     attrSpec = {'x': {'attr_followsprotocol': True}}
    >>> m1 = Top([50, 52], x=Bottom([1, 3, 5]))
    >>> m2 = Top([51, 53], x=Bottom([2, 5, 6]))
    >>> print(m1.merged(m2))
    {50, 51, 52, 53}, x = {1, 2, 3, 5, 6}
    """
    
    SS = self._SETSPEC
    
    if SS.get('set_mergechecknooverlap', False):
        if self & other:
            raise ValueError("No set overlaps allowed!")
    
    vNew = self | other
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumbernamesdirect = True,
    ...         set_showpresorted = True)
    >>> obj1 = Test1({303, None, 304})
    >>> e = _fakeEditor()
    >>> obj1.pprint(editor=e)
    303 ('Required Ligatures On')
    304 ('Common Ligatures On')
    None
    
    >>> obj1.namesRenumbered({303:306, 304:307}).pprint(editor=e)
    306 ('Regular')
    307 ('Small Caps')
    None
    
    >>> class Test2(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True)
    ...     attrSpec = dict(
    ...         name1 = dict(
    ...             attr_renumbernamesdirect = True))
    >>> obj2 = Test2({obj1, None}, name1=307)
    >>> obj2.pprint(editor=e)
    Member:
      303 ('Required Ligatures On')
      304 ('Common Ligatures On')
      None
    Member:
      (no data)
    name1: 307 ('Small Caps')
    
    >>> obj2.namesRenumbered({303:306, 304:307, 307: 355}).pprint(editor=e)
    Member:
      306 ('Regular')
      307 ('Small Caps')
      None
    Member:
      (no data)
    name1: 355
    """
    
    SS = self._SETSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    
    if SS.get('item_renumbernamesdeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.namesRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = [
          (None if obj is None else obj.namesRenumbered(oldToNew, **kwArgs))
          for obj in _it()]
    
    elif SS.get('item_renumbernamesdirect', False):
        if keepMissing:
            vNew = [oldToNew.get(obj, obj) for obj in self]
        else:
            vNew = [oldToNew[obj] for obj in self if obj in oldToNew]
    
    else:
        vNew = self
    
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
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(item_renumberpcsdirect = True)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> obj = Test1([5, 12, 50, 100])
    >>> sorted(obj.pcsRenumbered(mapData, infoString="testcode"))
    [5, 14, 53, 106]
    
    >>> class Test2(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpcsdirect = True)
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True)
    >>> t3 = Test3({20, None, Test2([5, 45, 100])})
    >>> t3New = t3.pcsRenumbered(mapData, infoString="testcode")
    >>> sorted(i for obj in t3New if obj is not None for i in obj)
    [5, 22, 48, 106]
    """
    
    SS = self._SETSPEC
    
    if SS.get('item_renumberpcsdeep', SS.get('item_followsprotocol', False)):
        vNew = set()
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is None:
                vNew.add(None)
            
            else:
                try:
                    boundMethod = obj.pcsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).pcsRenumbered
                    else:
                        raise
                
                vNew.add(boundMethod(mapData, **kwArgs))
    
    elif SS.get('item_renumberpcsdirect', False):
        vNew = set()
        
        for obj in self:
            if obj is not None:
                delta = 0
                it = mapData.get(kwArgs.get('infoString', None), [])
                
                for threshold, newDelta in it:
                    if obj < threshold:
                        break
                    
                    delta = newDelta
                
                vNew.add(obj + delta)
            
            else:
                vNew.add(None)
    
    else:
        vNew = self
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``glyphIndex``
        This is required. It is a glyph index, used to select which oldToNew
        dict is to be used for the mapping.
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the sequence, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberpointsdirect = True,
    ...         set_showpresorted = True)
    >>> myMap = {3: {10: 11, 11: 4, 4: 10}, 6: {2: 3, 3: 2}}
    >>> print(Bottom([2, 4, 10]).pointsRenumbered(myMap, glyphIndex=3))
    {2, 10, 11}
    >>> print(Bottom([2, 4, 10]).pointsRenumbered(myMap, glyphIndex=6))
    {3, 4, 10}
    
    >>> class Middle(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_showsorted = True)
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_followsprotocol = True))
    ...     __hash__ = frozenset.__hash__
    >>> obj = Middle([4, 5], x=Bottom([2, 4, 10]))
    >>> print(obj.pointsRenumbered(myMap, glyphIndex=3))
    {4, 5}, x = {2, 10, 11}
    
    >>> class Top(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> obj = Top([None, Middle([4, 5], x=Bottom([2, 4, 10]))])
    >>> print(obj)
    {{4, 5}, x = {2, 4, 10}, None}
    >>> print(obj.pointsRenumbered(myMap, glyphIndex=3))
    {{4, 5}, x = {2, 10, 11}, None}
    
    >>> class Test2(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpointsdirect = True)
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True)
    >>> t3 = Test3({20, None, Test2([5, 45, 100])})
    >>> myMap = {200: {20: 1, 45: 2, 100: 3}}
    >>> t3New = t3.pointsRenumbered(myMap, glyphIndex=200)
    >>> sorted(i for obj in t3New if obj is not None for i in obj)
    [1, 2, 3, 5]
    """
    
    SS = self._SETSPEC
    # glyphIndex is in kwArgs in all cases here, since sets are unordered
    
    if SS.get(
      'item_renumberpointsdeep',
      SS.get('item_followsprotocol', False)):
        
        vNew = set()
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is None:
                vNew.add(None)
            
            else:
                try:
                    boundMethod = obj.pointsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).pointsRenumbered
                    else:
                        raise
                
                vNew.add(boundMethod(mapData, **kwArgs))
    
    elif SS.get('item_renumberpointsdirect', False):
        vNew = set()
        thisMap = mapData.get(kwArgs.get('glyphIndex', None), {})
        
        for obj in self:
            if obj is not None:
                newPoint = thisMap.get(obj, None)
                
                if newPoint is not None:
                    vNew.add(newPoint)
                else:
                    vNew.add(obj)
    
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def M_pprint(self, **kwArgs):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Test1presort(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showpresorted': True}
    >>> obj = Test1presort([14, 2, 98])
    >>> obj.pprint(label="Sorted before string conversion")
    Sorted before string conversion:
      2
      14
      98
    
    >>> class Test1postsort(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showsorted': True}
    >>> obj = Test1postsort([14, 2, 98])
    >>> obj.pprint(label="Sorted after string conversion")
    Sorted after string conversion:
      14
      2
      98
    
    >>> class Test1presortnamer(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberdirect = True,
    ...         item_usenamerforstr = True,
    ...         set_showpresorted = True)
    >>> nm = namer.testingNamer()
    >>> obj = Test1presortnamer([14, 2, 98])
    >>> obj.pprint(label="Glyph names, presorted", namer=nm)
    Glyph names, presorted:
      xyz3
      xyz15
      afii60003
    
    >>> class Test1postsortnamer(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberdirect = True,
    ...         item_usenamerforstr = True,
    ...         set_showsorted = True)
    >>> obj = Test1postsortnamer([14, 2, 98])
    >>> obj.pprint(label="Glyph names, postsorted", namer=nm)
    Glyph names, postsorted:
      afii60003
      xyz15
      xyz3
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_pprintfunc = (lambda p,x: p.simple(x, "A number")))
    >>> Test2([14, 2, 98]).pprint(label="Custom item pprinter")
    Custom item pprinter:
      A number: 2
      A number: 14
      A number: 98
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}, 'y': {}}
    >>> obj = Test3([14, 2, 98], x="Hi", y=-5)
    >>> obj.pprint(label="Attributes after set values")
    Attributes after set values:
      2
      14
      98
      x: Hi
      y: -5
    
    >>> class Test4(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_ppoptions = dict(noDataString = "nuffin"),
    ...         set_showpresorted = True)
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(attr_ppoptions = {'noDataString': "bubkes"}))
    >>> Test4({5, 12, None}).pprint()
    5
    12
    nuffin
    a: (no data)
    b: bubkes
    
    >>> class Test5(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_pprintlabelfunc = (lambda i: "Sequence #%d" % (i + 1,)))
    >>> class Test6(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test5([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> Test6([14, None, Test5([12, 30, None, 14])]).pprint()
    Member:
      Sequence #1: 12
      Sequence #2: 30
      Sequence #3: (no data)
      Sequence #4: 14
    Member:
      Sequence #1: 14
    Member:
      (no data)
    
    >>> class Test6(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict()
    >>> class Test7(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True)
    >>> class Test8(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True)
    >>> obj6 = Test6({4, 1, 8})
    >>> obj7 = Test7({None, obj6})
    >>> obj8 = Test8([obj6, obj7])
    >>> obj8.pprint()
    0:
      8
      1
      4
    1:
      Member:
        8
        1
        4
      Member:
        (no data)
    
    >>> obj8.pprint(elideDuplicates=True)
    OBJECT 0
    0:
      8
      1
      4
    OBJECT 1
    1:
      Member: (duplicate; see OBJECT 0 above)
      Member:
        (no data)
    """
    
    SS = self._SETSPEC
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    pd = p.__dict__
    ppSaveDict = {}
    
    for key, value in SS.get('set_ppoptions', {}).items():
        ppSaveDict[key] = pd[key]
        pd[key] = value
    
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if elideDups is True:
        elideDups = {}  # object ID to serial number
        kwArgs['elideDuplicates'] = elideDups
    
    printWholeFunc = SS.get('set_pprintfunc', None)
    printItemFunc = SS.get('item_pprintfunc', None)
    kwArgs['useRepr'] = SS.get('item_strusesrepr', False)
    nm = kwArgs.get('namer', getattr(self, '_namer', None))
    intendToUseNamer = SS.get('item_usenamerforstr', False)
    glyphDirect = SS.get('item_renumberdirect', False)
    postsort = SS.get('set_showsorted', False)
    
    if glyphDirect and intendToUseNamer and (nm is None):
        postsort = False
    
    if printWholeFunc is not None:
        printWholeFunc(p, self)
    
    elif printItemFunc:
        for obj in self._iterSorted():
            printItemFunc(p, obj)
    
    elif SS.get('item_pprintdeep', SS.get('item_followsprotocol', False)):
        for obj in self._iterSorted(deepAttrString="pprint", **kwArgs):
            if elideDups is not False:
                objID = id(obj)
                
                if objID in elideDups:
                    p.simple(
                      "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                      label = "Member",
                      **kwArgs)
                    
                    continue
                
                elif obj is not None:
                    elideDups[objID] = len(elideDups)
                    p("OBJECT %d" % (elideDups[objID],))
                    
                    # ...and fall through to do the actual printing below
            
            p.deep(obj, label="Member", **kwArgs)
    
    elif glyphDirect and intendToUseNamer:
        nmbf = (None if nm is None else nm.bestNameForGlyphIndex)
        
        if (nmbf is None) and postsort:
            nmbf = str
        
        for s in self._iterSorted(decorator=nmbf):
            p.simple(s, **kwArgs)
    
    elif SS.get('item_renumbernamesdirect', False):
        for n in self._iterSorted():
            p.simple(
              utilities.nameFromKwArgs(n, **kwArgs),
              **kwArgs)
    
    else:
        deco = (str if postsort else None)
        
        for obj in self._iterSorted(decorator=deco):
            p.simple(obj, **kwArgs)
    
    while ppSaveDict:
        key, value = ppSaveDict.popitem()
        pd[key] = value
    
    # Now do attributes
    attrhelper.M_pprint(self, p, self.getNamer, **kwArgs)

def M_pprintChanges(self, prior, **kwArgs):
    """
    Displays the changes from ``prior`` to ``self``.
    
    :param prior: The previous object, to be compared to ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Test1(set, metaclass=FontDataMetaclass): pass
    >>> Test1([2, 3, 5]).pprint_changes(Test1([3, 6]), label="Differences")
    Differences:
      Additions:
        2
        5
      Deletions:
        6
    """
    
    if self == prior:
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    SS = self._SETSPEC
    ppdFunc = SS.get('set_pprintdifffunc', None)
    
    if ppdFunc is not None:
        ppdFunc(p, set(self), set(prior), **kwArgs)
    
    else:
        additions = type(self)(self - prior)
        deletions = type(self)(prior - self)
        
        printItemFunc = SS.get(
          'item_pprintfunc',
          functools.partial(
            pp.PP.simple,
            useRepr=SS.get('item_strusesrepr', False)))
        
        if additions:
            p("Additions:")
            p2 = p.makeIndentedPP()
            
            for obj in additions._iterSorted():
                printItemFunc(p2, obj)
        
        if deletions:
            p("Deletions:")
            p2 = p.makeIndentedPP()
            
            for obj in deletions._iterSorted():
                printItemFunc(p2, obj)
    
    # Now do attributes
    nm = kwArgs.get('namer', self.getNamer())
    
    attrhelper.M_pprintChanges(self, prior.__dict__, p, nm, **kwArgs)

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_recalculatefunc = (
    ...           lambda s, **k:
    ...           (True, set([-6, len(s)]))),
    ...         set_showpresorted = True)
    >>> print(Test1([4, None, 19, 'a']).recalculated())
    {-6, 4}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_recalculatefunc = (lambda x, **k: (True, x + 12)),
    ...         set_showpresorted = True)
    >>> print(Test2([4, 10, None, 200]).recalculated())
    {16, 22, 212, None}
    
    >>> class Test3(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_showpresorted = True)
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_recalculatefunc = (lambda x,**k: (True, x+5))))
    >>> print(Test3([3, 5], x=12).recalculated())
    {3, 5}, x = 17
    
    >>> class Test4(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = (lambda x,**k: (True, x + 1)))
    >>> class Test5(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test4([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    
    >>> Test5([7, None, Test4([19, -5, None])]).recalculated().pprint()
    Member:
      0: 20
      1: -4
      2: (no data)
    Member:
      0: 8
    Member:
      (no data)
    
    >>> def _t6W(v, **kwArgs):
    ...     v2 = {obj for obj in v if obj is None or obj >= 0}
    ...     return set(v) != v2, v2
    >>> def _t6I(obj, **kwArgs):
    ...     return obj != round(obj), round(obj)
    
    >>> class Test6_W(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         set_recalculatefunc_partial = _t6W,
    ...         set_showpresorted = True)
    >>> v = [1.5, 4, -5.75, -3, 13.25, 0]
    >>> print(Test6_W(v).recalculated())
    {0, 1.5, 4, 13.25}
    
    >>> class Test6_I(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_recalculatefunc = _t6I,
    ...         set_showpresorted = True)
    >>> print(Test6_I(v).recalculated())
    {-6, -3, 0, 2, 4, 13}
    
    >>> class Test6_Both(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_recalculatefunc = _t6I,
    ...         set_recalculatefunc_partial = _t6W,
    ...         set_showpresorted = True)
    >>> print(Test6_Both(v).recalculated())
    {0, 2, 4, 13}
    """
    
    SS = self._SETSPEC
    fWhole = SS.get('set_recalculatefunc', None)
    fWholePartial = SS.get('set_recalculatefunc_partial', None)
    fIndiv = SS.get('item_recalculatefunc', None)
    
    if fWhole is not None:
        vNew = fWhole(self, **kwArgs)[1]
    
    else:
        vNew = self
        
        if fWholePartial is not None:
            vNew = fWholePartial(self, **kwArgs)[1]
        
        if fIndiv is not None:
            vNew = (
              (None if obj is None else fIndiv(obj, **kwArgs)[1])
              for obj in vNew)
        
        elif (
          SS.get('item_recalculatedeep',
          SS.get('item_followsprotocol', False))):
            
            cf = SS.get('item_deepconverterfunc', None)
            vNew2 = set()
            
            for obj in vNew:
                if obj is not None:
                    try:
                        boundMethod = obj.recalculated
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).recalculated
                        else:
                            raise
                    
                    obj = boundMethod(**kwArgs)
                
                vNew2.add(obj)
            
            vNew = vNew2
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Bottom(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_scaledirect = True)
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showpresorted = True)
    >>> print(Test1([Bottom([4, 6]), None]).scaled(1.5))
    {(6, 9), None}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_scaledirect = True,
    ...         set_showpresorted = True)
    >>> print(Test2([14, 16, 18]).scaled(1.8))
    {25, 29, 32}
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_scaledirectnoround = True,
    ...         set_showpresorted = True)
    >>> print(Test3([14, 16, 18]).scaled(1.75))
    {24.5, 28.0, 31.5}
    
    >>> class Test4(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_scaledirectnoround = True)
    >>> class Test5(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test4([x])),
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    
    >>> Test5([3.5, None, Test4([1.0, 6.0, None])]).scaled(1.5).pprint()
    Member:
      0: 1.5
      1: 9.0
      2: (no data)
    Member:
      0: 5.25
    Member:
      (no data)
    
    >>> class Test6(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_scaledirect = True,
    ...         item_representsx = True,
    ...         set_showsorted = True)
    ...     attrSpec = dict(
    ...         x = dict(attr_scaledirect = True, attr_representsx = True),
    ...         y = dict(attr_scaledirect = True, attr_representsy = True),
    ...         z = dict(attr_scaledirect = True))
    
    >>> obj = Test6({2.0, 3.0, None}, x=2.0, y=2.0, z=2.0)
    >>> print(obj.scaled(5.0))
    {10.0, 15.0, None}, x = 10.0, y = 10.0, z = 10.0
    >>> obj = Test6({2.0, 3, None}, x=2.0, y=2.0, z=2.0)
    >>> print(obj.scaled(5.0, scaleOnlyInX=True))
    {10.0, 15, None}, x = 10.0, y = 2.0, z = 10.0
    >>> print(obj.scaled(5.0, scaleOnlyInY=True))
    {2.0, 3, None}, x = 2.0, y = 10.0, z = 10.0
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    SS = self._SETSPEC
    
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    if SS.get('item_representsx', False) and scaleOnlyInY:
        vNew = self
    
    elif SS.get('item_representsy', False) and scaleOnlyInX:
        vNew = self
    
    elif SS.get('item_scaledeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is None:
                    yield None
                
                else:
                    try:
                        boundMethod = obj.scaled
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).scaled
                        else:
                            raise
                    
                    yield boundMethod(scaleFactor, **kwArgs)
        
        vNew = _it()
    
    elif SS.get('item_scaledirect', False):
        roundFunc = SS.get('item_roundfunc', None)
        
        if roundFunc is None:
            if SS.get('item_python3rounding', False):
                roundFunc = utilities.newRound
            else:
                roundFunc = utilities.oldRound
        
        vNew = tuple(
          None if obj is None
          else roundFunc(scaleFactor * obj, castType=type(obj))
          for obj in self)
    
    elif SS.get('item_scaledirectnoround', False):
        vNew = ((None if obj is None else scaleFactor * obj) for obj in self)
    
    else:
        vNew = self
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumberstoragedirect = True,
    ...         set_showpresorted = True)
    
    >>> print(Test1([15, 80, None, 29]).storageRenumbered(storageDelta=1000))
    {1015, 1029, 1080, None}
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> obj = Test1([25, 27, None, 26, 30])
    >>> print(obj.storageRenumbered(oldToNew=d))
    {30, 1000, 1001, 1025, None}
    >>> print(obj.storageRenumbered(oldToNew=d, keepMissing=False))
    {1000, 1001, 1025, None}
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1([10, 15, None]).storageRenumbered(storageMappingFunc=f))
    {15, 910, None}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showsorted = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.storageRenumbered(storageDelta=-3))
    {{12, 17, None}, {17, 87}, None}
    """
    
    SS = self._SETSPEC
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
    
    if SS.get(
      'item_renumberstoragedeep',
      SS.get('item_followsprotocol', False)):
        
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.storageRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = (
          (None if obj is None else obj.storageRenumbered(**kwArgs))
          for obj in _it())
    
    elif SS.get('item_renumberstoragedirect', False):
        vNew = (
          (None if obj is None else storageMappingFunc(obj, **kwArgs))
          for obj in self)
    
    else:
        vNew = iter(self)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_representsx = True,
    ...         set_showpresorted = True)
    >>> print(Test1([1, 2.0, 3, None]).transformed(m))
    {-12, -9.0, -6, None}
    
    >>> class Test2(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_representsy = True,
    ...         set_showpresorted = True)
    >>> print(Test2([1, 2, 3, None]).transformed(m))
    {6, 8, 10, None}
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_followsprotocol = True,
    ...         set_showpresorted = True)
    >>> obj = Test3([Test1([1, 2, 3, 4]), None, Test1([-3, -4])])
    >>> obj2 = obj.transformed(m)
    >>> len(obj2)
    3
    >>> ({6, 9} in obj2), ({-15, -12, -9, -6} in obj2), (None in obj2)
    (True, True, True)
    """
    
    SS = self._SETSPEC
    mp = matrixObj.mapPoint
    
    if SS.get('item_transformnoround', False):
        roundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfunc' in SS:
        roundFunc = SS['item_roundfunc']
    elif SS.get('item_python3rounding', False):
        roundFunc = utilities.newRound
    else:
        roundFunc = utilities.oldRound
    
    if SS.get('item_followsprotocol', False):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is None:
                    yield None
                
                else:
                    try:
                        boundMethod = obj.transformed
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).transformed
                        else:
                            raise
                    
                    yield boundMethod(matrixObj, **kwArgs)
        
        vNew = _it()
    
    elif SS.get('item_representsx', False):
        def _it():
            for obj in self:
                if obj is None:
                    yield None
                else:
                    yield roundFunc(mp((obj, 0))[0], castType=type(obj))
        
        vNew = _it()
    
    elif SS.get('item_representsy', False):
        def _it():
            for obj in self:
                if obj is None:
                    yield obj
                else:
                    yield roundFunc(mp((0, obj))[1], castType=type(obj))
        
        vNew = _it()
    
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def PM_iterSorted(self, decorator=None, deepAttrString=None, **kwArgs):
    """
    Returns a generator over set members in sorted order.
    
    If ``decorator`` is ``None``, returns a generator over objects in the set
    that respects the sort settings (or lack thereof). If ``decorator`` is not
    ``None``, returns an iterator over output from that decorator for the
    objects in the set in the sorted order.

    If ``deepAttrString`` is not ``None``, then the objects are assumed to be
    deep for the purposes of this call, and the specified attribute will be
    tested for presence if an ``item_deepconverterfunc`` is available.

    In all cases, if ``None`` is a member of the set is is always yielded last,
    even in the unsorted cases.
    """
    
    SS = self._SETSPEC
    yieldFinalNone = None in self
    
    def _it():
        if deepAttrString is None:
            for obj in self:
                if obj is not None:
                    yield obj
        
        else:
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        getattr(obj, deepAttrString)
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                    
                    yield obj
    
    if decorator is not None:
        if SS.get('set_showpresorted', False):
            for obj in sorted(obj for obj in _it()):
                yield decorator(obj)
        
        elif SS.get('set_showsorted', False):
            for obj in sorted(decorator(obj) for obj in _it()):
                yield obj
        
        else:
            for obj in _it():
                yield decorator(obj)
    
    elif SS.get('set_showpresorted', False):
        for obj in sorted(obj for obj in _it()):
            yield obj
    
    elif SS.get('set_showsorted', False):
        for obj in sorted((obj for obj in _it()), key=str):
            yield obj
    
    else:
        for obj in _it():
            yield obj
     
    if yieldFinalNone:
        yield (None if decorator is None else decorator(None))

def SM_bool(self):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if the set is nonzero length, or if it is zero length 
        but one or more attributes have significant nonzero values (and by
        significant I mean values that are not selectively ignored based on the
        ``attr_ignoreforcomparisons`` and ``attr_ignoreforbool`` flags); False
        otherwise
    :rtype: bool
    
    A set of length greater than zero might return False if the class was
    defined with the ``seq_falseifcontentsfalse`` flag.
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforbool = True),
    ...         notIgnored = dict())
    >>> print(bool(Test1({1, 2, 3}, ignored=0, notIgnored=0)))
    True
    >>> print(bool(Test1(set(), ignored=0, notIgnored=0)))
    False
    >>> print(bool(Test1(set(), ignored=5, notIgnored=0)))
    False
    >>> print(bool(Test1(set(), ignored=0, notIgnored=1)))
    True
    """
    
    if len(self):
        return True
    
    # We don't test for the non-emptiness of self._ATTRSPEC here because the
    # only way this method can be executed is in the presence of attributes.
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass): pass
    >>> class Top(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> class LPA(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someSet': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someSet', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 5], someSet=t, someNumber=25)
    >>> obj2 = obj1.__copy__()
    >>> obj1 is obj2, obj1 == obj2
    (False, True)
    >>> obj1.someSet is obj2.someSet
    True
    """
    
    if self._ATTRSPEC:
        return type(self)(self, **self.__dict__)
    else:
        return type(self)(self)

def SM_deepcopy(self, memo=None):
    """
    Make a deep copy.
    
    :return: A deep copy of ``self``
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass): pass
    >>> class Top(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> class LPA(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someSet': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someSet', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 5], someSet=t, someNumber=25)
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1 is obj2, obj1 == obj2
    (False, True)
    >>> obj1.someSet is obj2.someSet
    False
    >>> sorted(obj1.someSet)[0] == sorted(obj2.someSet)[0]
    True
    
    >>> class Test1(tuple, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> t = Test1([4, 5])
    >>> obj1 = Test2([5, None, t])
    >>> obj2 = obj1.__deepcopy__()
    >>> t2 = [o for o in obj2 if o is not None if len(o) == 2][0]
    >>> t == t2, t is t2
    (True, False)
    """
    
    if memo is None:
        memo = {}
    
    SS = self._SETSPEC
    f = SS.get('item_deepcopyfunc', None)
    d = self.__dict__
    vNew = [None] * len(self)
    
    if f is not None:
        for i, value in enumerate(self):
            if value is not None:
                vNew[i] = memo.setdefault(id(value), f(value, memo))
    
    elif SS.get('item_deepcopydeep', SS.get('item_followsprotocol', False)):
        cf = SS.get('item_deepconverterfunc', None)
        
        for i, value in enumerate(self):
            if value is not None:
                try:
                    vNew[i] = memo.setdefault(
                      id(value),
                      value.__deepcopy__(memo))
                
                except AttributeError:
                    if cf is not None:
                        value = cf(value, **d.get('kwArgs', {}))
                        vNew[i] = memo.setdefault(id(value), value)
                    
                    else:
                        raise
    
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    
    # Construct and return the result
    return type(self)(vNew, **dNew)

def SM_eq(self, other):
    """
    Determine if the two objects are equal (selectively).
    
    :return: True if the sequences and their attributes are equal (allowing for
        selective inattention to certain attributes depending on their control
        flags, and depending on the ``attrSorted`` tuple)
    :rtype: bool
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass): pass
    >>> class Top(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> class LPA(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someSet': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someSet', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 4, 6], someSet=t, someNumber=5)
    >>> obj1 == obj1
    True
    >>> obj1 == None
    False
    >>> obj2 = LPA([3, 4, 6], someSet=t.__deepcopy__(), someNumber=5)
    >>> obj1 == obj2
    True
    
    >>> class Test(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    ...     attrSorted = ('x', 'y', 'z')
    >>> Test([], x=1, y=2, z=3) == Test([], x=1, y=2, z=2000)
    True
    >>> Test([], x=1, y=2, z=3) == Test([], x=1, y=200, z=3)
    False
    """
    
    if self is other:
        return True
    
    try:
        if len(self) != len(other):
            return False
    
    except TypeError:
        return False
    
    if not all(map(other.__contains__, iter(self))):
        return False
    
    return attrhelper.SM_eq(
      self._ATTRSPEC,
      getattr(other, '_ATTRSPEC', {}),
      self.__dict__,
      getattr(other, '__dict__', {}))

def SM_hash(self):
    """
    Determine ``self``’s hash value.
    
    :return: A hash value for the object and relevant attributes
    :rtype: int
    
    This method is only included by the metaclass initialization logic if:
        #. the base class is immutable, and
        #. there is at least one attribute that has
           ``attr_ignoreforcomparisons`` set to False.
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforcomparisons = True),
    ...         notIgnored = dict())
    
    >>> obj1 = Test1({1, 2, 3}, ignored=3, notIgnored=4)
    >>> obj2 = Test1({1, 2, 3}, ignored=5, notIgnored=4)
    >>> obj3 = Test1({1, 2, 3}, ignored=3, notIgnored=7)
    >>> len({obj1, obj2})
    1
    >>> len({obj1, obj3})
    2
    >>> len({obj1, obj2, obj3})
    2
    """
    
    AS = self._ATTRSPEC
    d = self.__dict__
    v = []
    
    for k in sorted(AS):  # not sortedKeys, as this needs to be exhaustive
        ks = AS[k]
        f = ks.get('attr_asimmutablefunc', None)
        obj = d[k]
        
        if not ks.get('attr_ignoreforcomparisons', False):
            if ks.get(
              'attr_asimmutabledeep',
              ks.get('attr_followsprotocol', False)):
                
                if obj is None:
                    v.append(obj)
                else:
                    v.append(obj.asImmutable())
            
            elif f is not None:
                v.append(f(obj))
            
            else:
                v.append(obj)
    
    return hash((frozenset(self), tuple(v)))

def SM_init(self, *args, **kwArgs):
    """
    Initialize the mutable set from ``args``, and the attributes from
    ``kwArgs`` if they're present, or via the attribute initialization function
    otherwise.
    
    :param args: Set initializer
    :param kwArgs: Attribute initializers
    :return: None
    
    This method is only included in the class being defined if:
        #.  The base class is mutable; and
        #.  There isn't already an ``__init__()`` defined
    
    Only one of ``__init__()`` and ``__new__()`` will be included.
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initLen = dict(
    ...             attr_initfunc = (lambda self: len(self)),
    ...             attr_initfuncneedsself = True))
    >>> v1 = Test1([-4, 'x', 19])
    >>> v1.initLen
    3
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
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
    >>> Test2([1]).pprint()
    1
    a: abc
    b: ab
    c: c
    >>> Test2([1], a="wxyz and then some").pprint()
    1
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test2([1], c="independently initialized").pprint()
    1
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showpresorted': True}
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> print(Test3([2, 4, 1], a=3))
    {1, 2, 4}, a = 3.0
    """
    
    set.__init__(self, *args)
    d = self.__dict__ = {}
    f = operator.itemgetter('attr_initfunc')
    AS = self._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        if k in kwArgs:
            d[k] = kwArgs[k]
        
        elif 'attr_initfuncchangesself' in ks:
            # We defer doing these special initializations until all the
            # other keyword arguments are done.
            deferredKeySet.add(k)
        
        else:
            v = ([self] if 'attr_initfuncneedsself' in ks else [])
            # it's now OK to do this, because we've already guaranteed
            # all attr dict specs have an attr_initfunc.
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

# def SM_ne(self, other): return not (self == other)

def SM_new(cls, *args, **kwArgs):
    """
    Initialize the immutable set from ``args``, and the attributes from
    ``kwArgs`` if they're present, or via the attribute initialization function
    otherwise.
    
    :param args: Set initializer
    :param kwArgs: Attribute initializers
    :return: The newly created object
    
    This method is only included in the class being defined if:
        #.  The base class is immutable; and
        #.  There isn't already a ``__new__()`` defined
    
    Only one of ``__init__()`` and ``__new__()`` will be included.
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initLen = dict(
    ...             attr_initfunc = (lambda self: len(self)),
    ...             attr_initfuncneedsself = True))
    >>> v1 = Test1([-4, 'x', 19, 'z'])
    >>> v1.initLen
    4
    
    >>> class Test2(frozenset, metaclass=FontDataMetaclass):
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
    >>> Test2([1]).pprint()
    1
    a: abc
    b: ab
    c: c
    >>> Test2([1], a="wxyz and then some").pprint()
    1
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test2([1], c="independently initialized").pprint()
    1
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test3(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'set_showpresorted': True}
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> print(Test3([2, 4, 1], a=3))
    {1, 2, 4}, a = 3.0
    """
    
    t = frozenset.__new__(cls, *args)
    d = t.__dict__ = {}
    f = operator.itemgetter('attr_initfunc')
    AS = cls._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        if k in kwArgs:
            d[k] = kwArgs[k]
        
        elif 'attr_initfuncchangesself' in ks:
            # We defer doing these special initializations until all the
            # other keyword arguments are done.
            deferredKeySet.add(k)
        
        else:
            v = ([t] if 'attr_initfuncneedsself' in ks else [])
            # it's now OK to do this, because we've already guaranteed
            # all attr dict specs have an attr_initfunc.
            d[k] = f(ks)(*v)
    
    for k in deferredKeySet:
        ks = AS[k]
        initFunc = f(ks)
        
        if id(initFunc) not in changedFuncIDsAlreadyDone:
            changedFuncIDsAlreadyDone.add(id(initFunc))
            initFunc(t)  # the function changes self's attributes directly
    
    # Only after everything is set up do we do a final attr_ensuretype check.
    
    for k, ks in AS.items():
        et = ks.get('attr_ensuretype', None)
        
        if (et is not None) and (not isinstance(d[k], et)):
            d[k] = et(d[k])
    
    return t

def SM_repr(baseKind):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass): pass
    >>> t1 = Test1([1, 'a', 5])
    >>> t1 == eval(repr(t1))
    True
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    >>> t2 = Test2([t1, Test1(['z', 9])])
    >>> t2 == eval(repr(t2))
    True
    
    >>> class Test3(frozenset, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test3() == eval(repr(Test3()))
    True
    
    >>> class Test4(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True}
    ...     attrSpec = {
    ...       'y': {'attr_initfunc': int},
    ...       'z': {'attr_initfunc': Test3, 'attr_followsprotocol': True}}
    >>> Test4() == eval(repr(Test4()))
    True
    """
    
    def SM_repr_closure(self):
        AS = self._ATTRSPEC
        
        if not AS:
            return "%s(%r)" % (self.__class__.__name__, baseKind(self))
        
        d = self.__dict__
        t = tuple(x for k in AS for x in (k, d[k]))
        sv = [
            self.__class__.__name__,
            '(',
            repr(baseKind(self)),
            ', ',
            (', '.join(["%s=%r"] * len(AS))) % t,
            ')']
        
        return ''.join(sv)
    
    SM_repr_closure.__doc__ = SM_repr.__doc__
    return SM_repr_closure

def SM_str(self):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    
    >>> class Test1(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_strusesrepr': True, 'set_showsorted': True}
    >>> t1 = Test1([1, 'a', 5])
    >>> print(str(t1))
    {'a', 1, 5}
    
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True, 'set_showsorted': True}
    >>> t2 = Test2([t1, Test1(['z', 9])])
    >>> print(str(t2))
    {{'a', 1, 5}, {'z', 9}}
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_usenamerforstr = True,
    ...         item_renumberdirect = True,
    ...         set_showpresorted = True)
    >>> t = Test3([11, 60, 98])
    >>> print(str(t))
    {11, 60, 98}
    >>> t.setNamer(namer.testingNamer())
    >>> print(str(t))
    {xyz12, xyz61, afii60003}
    
    >>> class Bottom(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_strusesrepr': True, 'set_showsorted': True}
    >>> class Top(frozenset, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_followsprotocol': True, 'set_showsorted': True}
    >>> class LPA(set, metaclass=FontDataMetaclass):
    ...     setSpec = {'item_strusesrepr': True, 'set_showpresorted': True}
    ...     attrSpec = {
    ...       'someNumber': {
    ...         'attr_initfunc': (lambda: 15),
    ...         'attr_label': "Count"},
    ...       'someSet': {
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('someSet', 'someNumber')
    >>> b1 = Bottom(['b'])
    >>> b2 = Bottom(['a', 'm'])
    >>> print(LPA([3, 25], someNumber=6, someSet=Top([b1, b2])))
    {3, 25}, Extra data = {{'a', 'm'}, {'b'}}, Count = 6
    
    >>> class Part1(frozenset, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}, 'y': {}}
    >>> class Part2(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {'part1': {'attr_strneedsparens': True}, 'z': {}}
    >>> print(Part2([], part1=Part1([], x=2, y=3), z=4))
    {}, part1 = ({}, x = 2, y = 3), z = 4
    
    >>> class Test(set, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {
    ...         'attr_labelfunc': (
    ...           lambda x, **k:
    ...           ("Odd" if x % 2 else "Even"))}}
    >>> print(Test([34], x=2))
    {34}, Even = 2
    >>> print(Test([34], x=3))
    {34}, Odd = 3
    
    >>> class Test1(set, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    >>> class Test2(set, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    >>> print(Test1())
    {}, s = fred
    >>> print(Test2())
    {}, s = 'fred'
    
    >>> class Test3(set, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> print(Test3([]))
    {}, y = 5
    >>> print(Test3([], x=4))
    {}, x = 4, y = 5
    
    >>> class Test4(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(
    ...         item_renumbernamesdirect = True,
    ...         set_showpresorted = True)
    >>> obj = Test4([303, None, 304])
    >>> print(obj)
    {303, 304, None}
    
    >>> obj.kwArgs = {'editor': _fakeEditor()}
    >>> print(obj)
    {303 ('Required Ligatures On'), 304 ('Common Ligatures On'), None}
    """
    
    SS = self._SETSPEC
    AS = self._ATTRSPEC
    savedNamers = None
    f = str
    selfNamer = getattr(self, '_namer', None)
    deepAttrString = None
    d = self.__dict__
    kwArgs = d.get('kwArgs', {}).copy()
    
    if SS.get('item_usenamerforstr', False) and selfNamer is not None:
        if SS.get('item_renumberdeep', SS.get('item_followsprotocol', False)):
            deepAttrString = '__str__'
            savedNamers = [obj.getNamer() for obj in self]
            
            for obj in self:
                obj.setNamer(selfNamer)
        
        elif SS.get('item_renumberdirect', False):
            f = selfNamer.bestNameForGlyphIndex
    
    elif SS.get('item_renumbernamesdirect', False):
        kwa = d.get('kwArgs', {})
        f = functools.partial(utilities.nameFromKwArgs, **kwa)
    
    elif SS.get('item_strusesrepr', False):
        f = repr
        
        if deepAttrString is not None:
            deepAttrString = '__repr__'
    
    kwArgs.pop('decorator', None)
    kwArgs.pop('deepAttrString', None)
    
    fmt = ', '.join(
      self._iterSorted(decorator=f, deepAttrString=deepAttrString, **kwArgs))
    
    r = "{%s}" % (fmt,)
    
    if savedNamers:
        for obj, oldNamer in zip(self, savedNamers):
            obj.setNamer(oldNamer)
    
    if not AS:
        return r
    
    sv = [r] + attrhelper.SM_str(self, selfNamer)
    return ', '.join(sv)

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__str__': SM_str,
    '_iterSorted': PM_iterSorted,
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
    'getSortedAttrNames': classmethod(lambda x: x._ATTRSORT),
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

_methodKindDict = {
    '__repr__': SM_repr
    }

def _addMethods(cd, bases):
    baseClassIsMutable = hasattr(bases[-1], '__iand__')  # a bit hacky...
    AS = cd['_ATTRSPEC']
    baseKind = (set if baseClassIsMutable else frozenset)
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
    stdClasses = (set, frozenset)
    
    for mDict, needKind in ((_methodDict, False), (_methodKindDict, True)):
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
                cd[mKey] = (m(baseKind) if needKind else m)
    
    # Only include __eq__ and __ne__ methods if needed
    if needEqNe:
        if '__eq__' not in cd:
            cd['__eq__'] = SM_eq
        
#         if '__ne__' not in cd:
#             cd['__ne__'] = SM_ne
        
        if (not baseClassIsMutable) and ('__hash__' not in cd):
            cd['__hash__'] = SM_hash
    
    # Only include a __bool__ method if needed
    if needBool:
        if '__bool__' not in cd:
            cd['__bool__'] = SM_bool
    
    # Only include an __init__ or __new__ method if there are attributes
    if AS:
        if baseClassIsMutable and ('__init__' not in cd):
            cd['__init__'] = SM_init
        elif (not baseClassIsMutable) and ('__new__' not in cd):
            cd['__new__'] = SM_new

def _validateSetSpec(d):
    """
    Make sure only known keys are included in the setSpec. (Checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing)
    
    >>> d = {'item_followsprotocol': True}
    >>> _validateSetSpec(d)
    >>> d = {'item_bollowsprotocol': True}
    >>> _validateSetSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown setSpec keys: ['item_bollowsprotocol']
    """
    
    unknownKeys = set(d) - validSetSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown setSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'set_validatefunc_partial' in d and 'set_validatefunc' in d:
        raise ValueError(
          "Cannot specify both a set_validatefunc_partial "
          "and a set_validatefunc.")
    
    if 'item_validatefunc_partial' in d and 'item_validatefunc' in d:
        raise ValueError(
          "Cannot specify both an item_validatefunc_partial "
          "and an item_validatefunc.")
    
    if 'item_prevalidatedglyphset' in d:
        if not d.get('item_renumberdirect', False):
            raise ValueError(
              "Prevalidated glyph set provided but set values "
              "are not glyph indices!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for set-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already one of the
    Protocol classes, the ``setSpec`` and ``attrSpec`` will define additions to
    the original. In this case, if an ``attrSorted`` is provided, it will be
    used for the combined attributes (original and newly-added); otherwise the
    new attributes will be added to the end of the ``attrSorted`` list.
    
    >>> class L1(set, metaclass=FontDataMetaclass):
    ...     setSpec = dict(set_showsorted = True)
    ...     attrSpec = dict(attr1 = dict())
    >>> print(L1(['x', 'y'], attr1=10))
    {x, y}, attr1 = 10
    
    >>> class L2(L1, metaclass=FontDataMetaclass):
    ...     setSpec = dict(item_strusesrepr = True)
    ...     attrSpec = dict(attr2 = dict())
    ...     attrSorted = ('attr2', 'attr1')
    >>> print(L2(['x', 'y'], attr1=10, attr2=9))
    {'x', 'y'}, attr2 = 9, attr1 = 10
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_SETSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            SS = c._SETSPEC.copy()
            SS.update(classdict.pop('setSpec', {}))
            classdict['_SETSPEC'] = classdict['_MAIN_SPEC'] = SS
            _validateSetSpec(SS)
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
            d = classdict['_SETSPEC'] = classdict.pop('setSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateSetSpec(d)
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
    import io
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
