#
# attrhelper.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
This module does **not** house a metaclass; rather, it contains helper
functions which handle the attribute-related portion for the other Protocol
metaclasses.

The handling of attributes is controlled via the following variables:
    
``attrSorted``
    A sorted sequence of keys from ``attrSpec``. This order is respected in the
    ``__str__()``, ``asImmutable()``, ``pprint()``, and ``pprint_changes()``
    methods.
    
``attrSpec``
    A dict mapping strings representing attribute names (the keys) to
    information sub-dicts. These sub-dicts map special keys, defined below, to
    values (or defaults if the keys are not present). Note that all these
    special keys start with ``attr_``, which allows them to be distinguished
    from the other keys that start with ``item_``, or ``seq_``, or ``map_``,
    etc.
    
    The following keys are defined, including notes on what the default values
    are or how they're derived:

    ``attr_asimmutabledeep``
        If True then the attribute's value has its own ``asImmutable()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_asimmutablefunc``
        A function called on the attribute value and returning an immutable
        version of that value.
        
        If this is not specified, and neither ``attr_followsprotocol`` nor
        ``attr_asimmutabledeep`` is True, then the attribute value must already
        be immutable.
    
    ``attr_coalescedeep``
        If True then the attribute's value has its own ``coalesced()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_compactdeep``
        If True then the attribute's value has its own ``compacted()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_deepconverterfunc``
        If present, then ``attr_followsprotocol`` should also be True. In this
        case, if a protocol deep function is called on the attribute's value
        and fails, this converter function will be called to get an object that
        will succeed with the call. This function takes the attribute's value,
        and optional keyword arguments.

        This is useful for cases like attributes which are usually collection
        objects, but where you wish to also allow simple integer values to be
        set. In this case, if the converter function is something like
        ``toCollection()``, then the value will automatically be converted for
        the purposes of the deep protocol method call. See
        :py:func:`~fontio3.fontdata.simplemeta.M_asImmutable` for an example of
        this.

        A note about special methods and converters: if an attribute is deep
        and uses a converter function, then any call to a special method (such
        as ``__deepcopy__()`` or ``__str__()``) on that attribute's value will
        only have access to the optional keyword arguments if an attribute
        named ``kwArgs`` was set in the object's ``__dict__``. You should only
        do this when the extra arguments are needed by the converter function.
        
        There is no default.
    
    ``attr_deepcopydeep``
        If True then the attribute's value has its own ``__deepcopy__()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_deepcopyfunc``
        A function that is called to deep-copy the attribute's value. It is
        called with two arguments: the value and a memo dict.
        
        There is no default.
    
    ``attr_enablecyclechecktag``
        If specified (which is only allowed for deep attribute values) then a
        cyclic object check will be made for this attribute's value during
        ``isValid()`` execution. A parent trace will be provided in a passed
        ``kwArg`` called ``activeCycleCheck``, which will be a dict mapping
        tags to lists of parent objects. The tag associated with this
        ``attr_enablecyclechecktag`` is what will be used to look up the
        specific parent chain for this attribute's value.
        
        Default is the value None.
    
    ``attr_ensuretype``
        A type (or class) object. When an object of a given class is
        instantiated, and an attribute has this set, then an ``isinstance()``
        check is made, and if it fails then the attribute value is reassigned
        to the result of calling the specified type/class with the current
        attribute value as the only positional argument.

        This is here to take care of cases where, for instance, an attribute is
        intended to be a tuple, but the positional initialization uses an
        iterator.

        There is no default.
    
    ``attr_followsprotocol``
        If True then the attribute's value is itself a Protocol object, and has
        all the Protocol methods.
        
        Default is False.

        Note that this may be overridden by explicitly setting a desired "deep"
        flag to False. So, for instance, if the attribute value is not to allow
        ``compacted()`` calls, then the sub-dict should have this flag set to
        True and ``attr_compactdeep`` set to False.
    
    ``attr_ignoreforbool``
        If True then the attribute's value will not be considered for
        ``__bool__()`` calls. Note this effect can also be obtained via the
        ``attr_ignoreforcomparisons`` flag, but that flag also affects equality
        comparisons.
        
        Default is False.
    
    ``attr_ignoreforcomparisons``
        If True then the attribute's value will not be considered for
        ``__eq__()``, ``__ne__()``, ``__bool__()``, or ``pprint_changes()``
        calls. That is, even if values differ, they will be treated as the
        same. This can be useful for internal recordkeeping attributes.
        
        Default is False.
    
    ``attr_initfunc``
        A function, called with no arguments, which provides a default initial
        value for the attribute.
        
        Default is a function that returns None.
    
    ``attr_initfuncchangesself``
        If True then the ``attr_initfunc`` function will be called with
        ``self`` as the single argument, as with ``attr_initfuncneedsself``.
        However, the specified function will do its initialization directly by
        adding attribute value(s) to ``self``; the function will not return a
        value.

        The usual way this is used is for linked attributes that are
        initialized as a group. Set this attribute True for all the linked
        attributes, and set their ``attr_initfunc`` to the same function (it
        will only be called once). Remember to check in the function for values
        already having been bound to the attribute names, as might happen if
        the client explicitly initializes one or more values via keyword
        arguments. See the doctests for
        :py:func:`fontio3.fontdata.simplemeta.SM_init` for an example.

        Note that attributes with this flag set will be initialized last, after
        all other keyword arguments (and positional arguments) have been set.

        Default is False.
    
    ``attr_initfuncneedsself``
        If True then an ``attr_initfunc`` will be passed ``self`` as a
        single argument, rather than the usual no arguments.
        
        Default is False.
    
    ``attr_inputcheckfunc``
        If specified this should be a function that takes a single positional
        argument and keyword arguments, one of which must be ``attrName`` with
        the name of the attribute being checked. This function should return
        True if the specified value is appropriate for the attribute in
        question.

        Note that if the positional argument is None, then the actual value of
        the attribute will be checked.

        There is no default.
    
    ``attr_islivingdeltas``
        If True the attribute is a ``LivingDeltas`` object (as used in OpenType
        1.8 variable fonts), and will be included in the result of a
        ``gatheredLivingDeltas()`` call.
        
        Default is False.
    
    ``attr_islookup``
        If True then the attribute's value will be included in the output from
        a call to ``gatheredRefs()``.
        
        Default is False.
    
    ``attr_isoutputglyph``
        If True then the attribute's value is treated as an output glyph. This
        means it will not be included in the output of a
        ``gatheredInputGlyphs()`` call, and it will be included in the output
        of a ``gatheredOutputGlyphs()`` call. Note that ``attr_renumberdirect``
        must also be set; otherwise the value will not be added, even if this
        flag is True.
        
        Default is False.
    
    ``attr_label``
        A string labelling the attribute. This will be used in any method that
        outputs the attribute's value.
        
        Default is the attribute name as a string.
    
    ``attr_labelfunc``
        A function normally taking one positional argument (the attribute's
        value), as well as the usual optional keyword arguments, and returning
        a string. However a second positional argument (the object itself) will
        be provided if the ``attr_labelfuncneedsobj`` flag is set True. This is
        useful for those cases where the interpretation of one field, and thus
        its label, varies depending on the value of another field. For an
        example of this, see the
        :py:class:`~fontio3.sbit.smallglyphmetrics.SmallGlyphMetrics` class.
        
        There is no default.
    
    ``attr_labelfuncneedsobj``
        If True, then the ``attr_labelfunc`` will be provided with a second
        positional argument, the object itself.
        
        There is no default.
    
    ``attr_maxcontextfunc``
        A function to determine the maximum context for the attribute's value.
        This function takes a single argument, the attribute's value itself.
        
        There is no default.
    
    ``attr_mergedeep``
        If True then the attribute's value has its own ``merged()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_mergefunc``
        If specified, a function taking two positional arguments, the
        attribute's value, and another value to be merged into it. Additional
        keyword arguments (for example, ``conflictPreferOther``) may be
        specified.

        The function returns a pair: the first value is True or False,
        depending on whether the first object's value actually changed. The
        second value is the new merged object to be used (if the first value
        was True).
        
        There is no default.
    
    ``attr_ppoptions``
        If specified, it should be a dict whose keys are valid options to be
        passed in for construction of a ``pp.PP`` instance, and whose values
        are as appropriate. This can be used to make a custom ``noDataString``,
        for instance.
        
        There is no default.
    
    ``attr_pprintdeep``
        If True then the attribute's value has its own ``pprint()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_pprintdiffdeep``
        If True then the attribute's value has its own ``pprint_changes()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_pprintdifffunc``
        A function taking four arguments: a ``pp.PP`` instance, the current
        value of the attribute, the prior value, and a label.
        
        There is no default.
    
    ``attr_pprintfunc``
        A function taking three positional arguments: a ``pp.PP`` instance, the
        attribute's value, and a label. It also takes optional keyword
        arguments. The function should print the attribute's value.
        
        There is no default.
    
    ``attr_pprintfuncneedsobj``
        If this flag is True, then an extra keyword argument will be passed to
        the ``attr_printfunc``. This extra keyword argument is named ``parent``
        and holds the whole object.
        
        Default is False.
    
    ``attr_prevalidatedglyphset``
        A set or frozenset containing glyph indices which are to be considered
        valid, even though they exceed the font's glyph count. This is useful
        for passing 0xFFFF values through validation for state tables, where
        that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``attr_python3rounding``
        If True, the Python 3 rounding function will be used. If False,
        old-style Python 2 rounding will be done. This affects both scaling and
        transforming if one of the rounding options is used.
        
        Default is False (yes, even in Python 3).
    
    ``attr_recalculatedeep``
        If True then the attribute's value has its own ``recalculated()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_recalculatefunc``
        A function taking one positional argument, the attribute's value.
        Additional keyword arguments (for example,``editor``) may be specified.
        This function returns a pair: the first element of the pair is True or
        False, depending on whether the recalculated value differs from the
        original value. The second element of the pair is the newly
        recalculated value to be used (if the first element was True).
        
        There is no default.
    
    ``attr_renumbercvtsdeep``
        If True then the attribute's value has its own ``cvtsRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumbercvtsdirect``
        If True then the attribute's value is interpreted as a CVT value and is
        subject to renumbering if the ``cvtsRenumbered()`` method is called.
        
        Default is False.
    
    ``attr_renumberdeep``
        If True then the attribute's value has its own ``glyphsRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumberdirect``
        If True then the attribute's value is interpreted as a glyph index. Any
        method that uses glyph indices (e.g. ``glyphsRenumbered()`` or
        ``gatheredInputGlyphs()``) looks at this flag to ascertain whether this
        attribute's value is available for processing.
        
        Default is False.
    
    ``attr_renumberfdefsdeep``
        If True then the attribute's value has its own ``fdefsRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumberfdefsdirect``
        If True then the attribute's value is interpreted as a function
        definition number (FDEF index), and is subject to renumbering if
        ``fdefsRenumbered()`` is called.
        
        Default is False.
    
    ``attr_renumbernamesdeep``
        If True then the attribute's value has its own ``namesRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumbernamesdirect``
        If True then the attribute's value is interpreted as an index into the
        ``'name'`` table, and is subject to being renumbered via a
        ``namesRenumbered()`` call.
        
        Default is False.
    
    ``attr_renumberpcsdeep``
        If True then the attribute's value has its own ``pcsRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumberpcsdirect``
        If True then the attribute's value is itself a PC value. This value
        will be directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``. Note this is not indexed by glyph index, since PCs
        may occur in non-glyph sources.
        
        Default is False.
    
    ``attr_renumberpointsdeep``
        If True then the attribute's value has its own ``pointsRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumberpointsdirect``
        If True then the attribute's value is itself a point index. Note that
        if this is used, the ``kwArgs`` passed into the ``pointsRenumbered()``
        call must include a ``glyphIndex`` value that is used to index into
        that method's ``mapData``.
        
        Default is False.
    
    ``attr_renumberstoragedeep``
        If True then the attribute's value has its own ``storageRenumbered()``
        method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_renumberstoragedirect``
        If True then the attribute's value is interpreted as a storage index,
        and is subject to renumbering if the ``storageRenumbered()`` method is
        called.
        
        Default is False.
    
    ``attr_representsx``
        If True then this attribute's value is interpreted as an x-coordinate.
        This knowledge is used by the ``scaled()`` method, in conjunction with
        the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that
        method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case there will usually be an associated
        y-coordinate value linked to this one (see the
        ``attr_transformcounterpart`` control, below, for more details).
        
        Default is False.
    
    ``attr_representsy``
        If True then this attribute's value is interpreted as a y-coordinate.
        This knowledge is used by the ``scaled()`` method, in conjunction with
        the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that
        method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case there will usually be an associated
        x-coordinate value linked to this one (see the
        ``attr_transformcounterpart`` control, below for more details).
        
        Default is False.
    
    ``attr_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or None to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``attr_scaledeep``
        If True then the attribute's value has its own ``scaled()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_scaledirect``
        If True then the attribute's value will be scaled by the ``scaled()``
        method. Note that the results of this scaling will always be rounded to
        the nearest integral value (with .5 cases controlled by
        ``attr_python3rounding``); if this is not desired, the client should
        instead specify the ``attr_scaleddirectnoround`` flag.

        The type of a rounded scaled value will be the type of the original
        value.
        
        Default is False.
    
    ``attr_scaledirectnoround``
        If True then the attribute's value will be scaled by the ``scaled()``
        method. No rounding will be done on the result; if rounding to integral
        values is desired, the client should instead specify the
        ``attr_scaledirect`` flag.
    
        The type of a non-rounded scaled value will be float.
        
        Default is False.
    
    ``attr_showonlyiffunc``
        A function taking a single value and returning True or
        False depending on whether the attribute should be shown or
        not, respectively. Note that the ``attr_showonlyiftrue`` is an
        older and less powerful way of doing this as well.
        
        There is no default.
    
    ``attr_showonlyiffuncobj``
        A function taking two positional arguments (the attribute
        value and the original object to which the attribute is
        attached), and returning True or False depending on whether
        the attribute should be shown or not, respectively. Clients
        not needing the original object should just use
        ``attr_showonlyiffunc`` instead.
        
        There is no default.
    
    ``attr_showonlyiftrue``
        If True and if the attribute's ``bool()`` result is False, then the
        attribute won't appear in the output from ``__str__()`` or
        ``pprint()``. Note that this flag has no effect on ``__repr__()`` or
        ``pprint_changes()``.

        If you need more powerful logic to determine whether a value should be
        shown, then use ``attr_showonlyiffunc`` or ``attr_showonlyiffuncobj``
        instead.
        
        Default is False.

    ``attr_strneedsparens``
        If True, this attribute's string representation will have a set of
        parentheses placed around it.
        
        Default is False.
    
    ``attr_strusesrepr``
        If True then the string representation for the attribute's value will
        be created via ``repr()``, not ``str()``.
        
        Default is False.
    
    ``attr_subloggernamefunc``
        A function taking a single argument, the attribute name, and returning
        a string to be used for the ``attrLogger`` when that deep value's
        ``isValid()`` method is called.
        
        If not provided, a function returning the attribute name will be used.
    
    ``attr_transformcounterpart``
        If the attribute represents one of the two coordinates of a
        two-dimensional point, this attribute contains the string naming the
        other part. (Knowledge of which is X and which is Y is derived from the
        ``attr_representsx`` and ``attr_representsy`` controls). This is used
        to construct a virtual point for the purposes of the ``transformed()``
        call.

        Note that whether the transformed value is rounded to an integer is
        controlled by ``attr_transformnoround``.
        
        There is no default.
    
    ``attr_transformnoround``
        If True, values after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the values will always
        be left as floats, irrespective of their original types. This differs
        from the default case, where rounding will be used but the rounded
        result will be the same type as the original value.

        Note the absence of an ``attr_transformdirect`` flag. Calls to the
        ``transformed()`` method will only affect attribute values marked with
        the ``attr_representsx`` or ``attr_representsy`` flags (or, of course,
        the ``attr_followsprotocol`` flag).
        
        Default is False.
    
    ``attr_useimmutableforcomparisons``
        If True, then the attribute's ``asImmutable()`` result will be used for
        comparisons, instead of the attribute's value itself.
        
        Default is False.
    
    ``attr_usenamerforstr``
        If True, permits the use of namers for displaying the value of the
        attribute (if a namer is available, and the value is designated as a
        glyph via one of the ``attr_renumber...`` flags).
        
        Default is False.
    
    ``attr_validatecode_deepnone``
        The code to be used for logging when a deep ``isValid()`` call is
        attempted on a value of None.
        
        Default is 'G0013'.
    
    ``attr_validatecode_namenotintable``
        The code to be used for logging when a ``'name'`` table index is being
        used but that index is not actually present in the ``'name'`` table.
        
        Default is 'G0042'.
    
    ``attr_validatecode_negativecvt``
        The code to be used for logging when a negative value is used for a CVT
        index.
        
        Default is 'G0028'.
    
    ``attr_validatecode_negativeglyph``
        The code to be used for logging when a negative value is used for a
        glyph index.
        
        Default is 'G0004'.
    
    ``attr_validatecode_negativeinteger``
        The code to be used for logging when a negative value is used for a
        non-negative item (like a PC or a point index).
        
        Default is 'G0008'.
    
    ``attr_validatecode_nocvt``
        The code to be used for logging when a CVT index is used but the
        ``Editor`` has no ``'cvt '`` table.
        
        Default is 'G0030'.
    
    ``attr_validatecode_nonintegercvt``
        The code to be used for logging when a non-integer value is
        used for a CVT index. (Note that floats representing
        integral values are fine, and will not trigger this)
        
        Default is 'G0027'.
    
    ``attr_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is
        used for a glyph index. (Note that floats representing
        integral values are fine, and will not trigger this)
        
        Default is 'G0003'.
    
    ``attr_validatecode_nonintegralinteger``
        The code to be used for logging when a non-integer value is
        used for an integer item (like a PC or a point index).
        
        Default is 'G0007'.
    
    ``attr_validatecode_nonnumericcvt``
        The code to be used for logging when a non-numeric value is
        used for a CVT index.
        
        Default is 'G0026'.
    
    ``attr_validatecode_nonnumericglyph``
        The code to be used for logging when a non-numeric value is
        used for a glyph index.
        
        Default is 'G0002'.
    
    ``attr_validatecode_nonnumericinteger``
        The code to be used for logging when a non-numeric value is
        used for an integer item (like a PC or a point index).
        
        Default is 'G0006'.
    
    ``attr_validatecode_nonnumericnumber``
        The code to be used for logging when a non-numeric value is
        used.
        
        Default is 'G0009'.
    
    ``attr_validatecode_toolargecvt``
        The code to be used for logging when a CVT index is used
        that is greater than or equal to the number of CVTs in
        the font.
        
        Default is 'G0029'.
    
    ``attr_validatecode_toolargeglyph``
        The code to be used for logging when a glyph index is used
        that is greater than or equal to the number of glyphs in
        the font.
        
        Default is 'G0005'.
    
    ``attr_validatedeep``
        If True then the attribute's value has its own ``isValid()`` method.
        
        Default derives from ``attr_followsprotocol``.
    
    ``attr_validatefunc``
        A function taking one positional argument, the attribute's
        value, and an arbitrary number of keyword arguments. The
        function returns True if the object is valid (that is, if
        no errors are present).
    
        This function must do all item checking. If you want the
        default checking (glyph indices, scalable values, etc.)
        then use ``attr_validatefunc_partial`` instead.
        
        There is no default.
    
    ``attr_validatefunc_partial``
        A function taking one positional argument, an attribute
        value, and an arbitrary number of keyword arguments. The
        function returns True if the value is valid (that is, if no
        errors are present). Note that values of None WILL be
        passed into this function, unlike most other actions.
    
        This function does not need to do checking on standard
        things like glyph indices or scalable values. If you prefer
        to do all checking in your function, use an
        ``attr_validatefunc`` instead.
        
        There is no default.
    
    ``attr_validatenone``
        If True, then an attribute value of None will be tested in
        an ``isValid()`` call. Normally this is False, so None values
        will not be tested.
        
        Default is False.
    
    ``attr_wisdom``
        A string encompassing a sensible description of the attribute,
        including how it is used.
        
        There is no default for wisdom, alas...
"""

# System imports
import logging

# Other imports
from fontio3 import utilities
from fontio3.utilities import valassist

# -----------------------------------------------------------------------------

#
# Constants
#

validAttrSpecKeys = frozenset([
  'attr_asimmutabledeep',
  'attr_asimmutablefunc',
  'attr_coalescedeep',
  'attr_compactdeep',
  'attr_deepconverterfunc',
  'attr_deepcopydeep',
  'attr_deepcopyfunc',
  'attr_enablecyclechecktag',
  'attr_ensuretype',
  'attr_followsprotocol',
  'attr_ignoreforbool',
  'attr_ignoreforcomparisons',
  'attr_initfunc',
  'attr_initfuncchangesself',
  'attr_initfuncneedsself',
  'attr_inputcheckfunc',
  'attr_islivingdeltas',
  'attr_islookup',
  'attr_isoutputglyph',
  'attr_label',
  'attr_labelfunc',
  'attr_labelfuncneedsobj',
  'attr_maxcontextfunc',
  'attr_mergedeep',
  'attr_mergefunc',
  'attr_ppoptions',
  'attr_pprintdeep',
  'attr_pprintdiffdeep',
  'attr_pprintdifffunc',
  'attr_prevalidatedglyphset',
  'attr_python3rounding',
  'attr_pprintfunc',
  'attr_pprintfuncneedsobj',
  'attr_recalculatedeep',
  'attr_recalculatefunc',
  'attr_renumbercvtsdeep',
  'attr_renumbercvtsdirect',
  'attr_renumberdeep',
  'attr_renumberdirect',
  'attr_renumberfdefsdeep',
  'attr_renumberfdefsdirect',
  'attr_renumbernamesdeep',
  'attr_renumbernamesdirect',
  'attr_renumberpcsdeep',
  'attr_renumberpcsdirect',
  'attr_renumberpointsdeep',
  'attr_renumberpointsdirect',
  'attr_renumberstoragedeep',
  'attr_renumberstoragedirect',
  'attr_representsx',
  'attr_representsy',
  'attr_roundfunc',
  'attr_scaledeep',
  'attr_scaledirect',
  'attr_scaledirectnoround',
  'attr_showonlyiffunc',
  'attr_showonlyiffuncobj',
  'attr_showonlyiftrue',
  'attr_strneedsparens',
  'attr_strusesrepr',
  'attr_subloggernamefunc',
  'attr_transformcounterpart',
  'attr_transformnoround',
  'attr_useimmutableforcomparisons',
  'attr_usenamerforstr',
  'attr_validatecode_deepnone',
  'attr_validatecode_namenotintable',
  'attr_validatecode_negativecvt',
  'attr_validatecode_negativeglyph',
  'attr_validatecode_negativeinteger',
  'attr_validatecode_nocvt',
  'attr_validatecode_nonintegercvt',
  'attr_validatecode_nonintegerglyph',
  'attr_validatecode_nonintegralinteger',
  'attr_validatecode_nonnumericcvt',
  'attr_validatecode_nonnumericglyph',
  'attr_validatecode_nonnumericinteger',
  'attr_validatecode_nonnumericnumber',
  'attr_validatecode_toolargecvt',
  'attr_validatecode_toolargeglyph',
  'attr_validatedeep',
  'attr_validatefunc',
  'attr_validatefunc_partial',
  'attr_validatenone',
  'attr_wisdom'])

# -----------------------------------------------------------------------------

#
# Functions
#

# Note that doctests for all these are found in the metaclasses

def determineNeedForEqBool(attrSpec):
    """
    Determines whether ``__eq__()`` and/or ``__bool__()`` are needed.
    
    :param dict attrSpec: The defined attribute specification
    :return: Flag for eq/ne and flag for bool
    :rtype: tuple(bool, bool)
    
    Analyzes the state of ``attr_ignoreforcomparisons`` and
    ``attr_ignoreforbool`` in the specified ``attrSpec`` and returns a pair of
    booleans ``(needEqNe, needBool)`` to allow the metaclass to customize
    whether these special methods are needed.
    
    >>> d = {}
    >>> print(determineNeedForEqBool(d))
    (False, False)
    
    >>> d['a'] = {}
    >>> print(determineNeedForEqBool(d))
    (True, True)
    
    >>> d['a'] = {'attr_ignoreforcomparisons': True}
    >>> print(determineNeedForEqBool(d))
    (False, False)
    
    >>> d['a'] = {'attr_ignoreforbool': True}
    >>> print(determineNeedForEqBool(d))
    (True, False)
    """
    
    needEqNe, needBool = False, False
    
    for ks in attrSpec.values():
        if not ks.get('attr_ignoreforcomparisons', False):
            needEqNe = True
            
            if not ks.get('attr_ignoreforbool', False):
                needBool = True
    
    return (needEqNe, needBool)

def M_asImmutable(attrSpec, attrSorted, d, **kwArgs):
    """
    Make immutable versions of the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param tuple attrSorted: The defined sort order; note that any attributes
                             present in the ``attrSpec`` but not in
                             ``attrSorted`` will not appear in the output
                             tuple!
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: Immutable versions of attributes in ``attrSorted`` order
    :rtype: tuple
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    Returns an immutable version of the attributes (specifically, a tuple in
    ``attrSorted`` order).
    
    The following ``kwArgs`` are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id()`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
    
    >>> class Deep(tuple, metaclass=_FDM('seq')): pass
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_asimmutablefunc=tuple),
    ...   c = dict(attr_followsprotocol=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=Deep),
    ...   e = dict(),
    ...   f = dict(attr_followsprotocol=True))
    >>> aSo = ('a', 'b', 'c', 'd', 'f')  # note 'e' is not present
    >>> d = {'a': 4, 'b': [1, 2], 'c': Deep([6, 7]), 'd': [9, 10], 'e': -1, 'f': None}
    >>> M_asImmutable(aSp, aSo, d)
    (('a', 4), ('b', (1, 2)), ('c', ('Deep', Deep((6, 7)))), ('d', ('Deep', Deep((9, 10)))), ('f', None))
    
    >>> d['f'] = [11, 12]  # no converter func will trigger exception
    >>> M_asImmutable(aSp, aSo, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'list' object has no attribute 'asImmutable'
    """
    
    v = []
    memo = kwArgs.get('memo', {})
    
    for k in attrSorted:
        obj = d[k]
        ks = attrSpec[k]
        f = ks.get('attr_asimmutablefunc', None)
        
        if obj is None:
            v.append((k, None))
        
        elif f is not None:
            v.append((k, f(obj)))
        
        elif ks.get(
          'attr_asimmutabledeep',
          ks.get('attr_followsprotocol', False)):
            
            objID = id(obj)
            
            if objID not in memo:
                cf = ks.get('attr_deepconverterfunc', None)
            
                try:
                    boundMethod = obj.asImmutable
            
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).asImmutable
                    else:
                        raise
                
                memo[objID] = boundMethod(**kwArgs)
            
            v.append((k, memo[objID]))
        
        else:
            hash(obj)  # we make sure it's immutable
            v.append((k, obj))
    
    return tuple(v)

def M_checkInput(attrSpec, d, valueToCheck=None, **kwArgs):
    """
    Determines if a value is appropriate for an attribute.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param valueToCheck: The value to be checked; if None, check the current
                         value of the named attribute instead (see ``attrName``
                         below in the ``kwArgs`` description)
    :param kwArgs: Optional keyword arguments (described below)
    :return: True/False for whether value is appropriate
    :rtype: bool
    :raises ValueError: If an ``attrName`` is specified but is not present
                        in ``attrSpec``
    
    The following ``kwArgs`` are supported:
    
    ``attrName``
        An optional string, identifying an attribute of the object. If
        specified, this attribute's own ``checkInput()`` method will be called
        with the ``valueToCheck`` value. Otherwise, this object's checking
        function (``attr_inputcheckfunc``) will be used.
    
    >>> func = lambda n, **k: -10 < n < 10
    >>> aSp = {'a': {}, 'b': {'attr_inputcheckfunc': func}}
    >>> d = {'a': 4, 'b': 8}
    
    Not specifying an ``attrName`` always returns True:
    
    >>> M_checkInput(aSp, d)
    True
    
    Specifying an unknown attribute raises a ``ValueError``:
    
    >>> M_checkInput(aSp, d, attrName='x')
    Traceback (most recent call last):
      ...
    ValueError: Unknown attribute: 'x'
    
    An attribute without a check function always returns True:
    
    >>> M_checkInput(aSp, d, attrName='a')
    True
    
    Not specifying a specific value to check uses the current value of the
    attribute:
    
    >>> M_checkInput(aSp, d, attrName='b')
    True
    >>> d['b'] = -23
    >>> M_checkInput(aSp, d, attrName='b')
    False
    
    Explicitly specifying a value checks that value, and ignores the current
    value of the attribute:
    
    >>> M_checkInput(aSp, d, valueToCheck=-2, attrName='b')
    True
    """
    
    attrName = kwArgs.pop('attrName', None)
    
    if attrName is None:
        return True
    
    if attrName not in attrSpec:
        raise ValueError("Unknown attribute: '%s'" % (attrName,))
    
    ks = attrSpec[attrName]
    
    if 'attr_inputcheckfunc' not in ks:
        return True
    
    if valueToCheck is None:
        valueToCheck = d[attrName]
    
    return ks['attr_inputcheckfunc'](valueToCheck, **kwArgs)

def M_coalesced(attrSpec, d, pool, **kwArgs):
    """
    Make coalesced versions of the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param pool: A map from ``id()`` for an object to the object itself
    :type pool: dict(int, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with objects coalesced
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``separateAttributesPool``
        If False (the default), then the pool will be cleared before
        processing.
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_followsprotocol=True),
    ...   d = dict(attr_followsprotocol=True),
    ...   e = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   f = dict(attr_asimmutablefunc=tuple),
    ...   g = dict())
    >>> d = {'a': 4, 'b': MyList([6, 7]), 'c': MyList([6, 7]), 'e': (6, 7), 'f': [6, 7], 'g': None}
    >>> d['d'] = d['b']
    >>> d['b'] is d['c']
    False
    >>> dOut = M_coalesced(aSp, d, {})
    >>> dOut['b'] is dOut['c']
    True
    
    The ``separateAttributesPool`` flag controls whether the attributes can
    share with values specified in pool (default is False):
    
    >>> sepVal = MyList([6, 7])
    >>> pool = {sepVal.asImmutable(): sepVal}
    >>> dOut = M_coalesced(aSp, d, pool, separateAttributesPool=False)
    >>> dOut['b'] is sepVal
    True
    >>> dOut = M_coalesced(aSp, d, pool, separateAttributesPool=True)
    >>> dOut['b'] is sepVal
    False
    
    An ``AttributeError`` is raised for missing converters on deep attributes:
    
    >>> d['d'] = (6, 7)
    >>> dOut = M_coalesced(aSp, d, {})
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'coalesced'
    """
    
    dNew = dict.fromkeys(attrSpec)  # all None initially
    
    # It's OK to use object IDs here, since we're constructing an entirely new
    # object. Since the original object continues to exist, its addresses are
    # safe from reuse for the duration of the compacted() processing.
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if kwArgs.get('separateAttributesPool', False):
        pool.clear()
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get(
          'attr_coalescedeep',
          ks.get('attr_followsprotocol', False)):
            
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                cf = ks.get('attr_deepconverterfunc', None)
            
                try:
                    boundMethod = obj.coalesced
            
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).coalesced
                    else:
                        raise
            
                obj = boundMethod(pool=pool, **kwArgs)
                cwc[objID] = obj
        
        aFunc = ks.get('attr_asimmutablefunc', None)
        
        if aFunc is not None:
            dNew[k] = pool.setdefault(aFunc(obj), obj)
        
        elif ks.get(
          'attr_asimmutabledeep',
          ks.get('attr_followsprotocol', False)):
            
            dNew[k] = pool.setdefault(obj.asImmutable(**kwArgs), obj)
        
        else:
            dNew[k] = pool.setdefault(obj, obj)
    
    return dNew

def M_compacted(attrSpec, d, **kwArgs):
    """
    Make compacted versions of the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A dict matching ``d`` but with objects coalesced
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` provided there is no
        ``attr_deepconverterfunc``
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'seq_compactremovesfalses': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(),
    ...   c = dict(attr_followsprotocol=True),
    ...   d = dict(attr_followsprotocol=True),
    ...   e = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   f = dict(attr_followsprotocol=True))
    >>> d = {'a': 0, 'b': None, 'c': MyList([0, 1, False, '', None]), 'e': (True, False), 'f': None}
    >>> d['d'] = d['c']
    >>> dOut = M_compacted(aSp, d)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (0, None, MyList([1]), MyList([1]), MyList([True]))
    
    >>> d['f'] = (0, 1, 2)
    >>> dOut = M_compacted(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'compacted'
    """
    
    dNew = dict.fromkeys(attrSpec)
    
    # It's OK to use object IDs here, since we're constructing an entirely new
    # object. Since the original object continues to exist, its addresses are
    # safe from reuse for the duration of the compacted() processing.
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get(
          'attr_compactdeep',
          ks.get('attr_followsprotocol', False)):
            
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                cf = ks.get('attr_deepconverterfunc', None)
            
                try:
                    boundMethod = obj.compacted
            
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).compacted
                    else:
                        raise
            
                obj = boundMethod(**kwArgs)
                cwc[objID] = obj
        
        dNew[k] = obj
    
    return dNew

def M_cvtsRenumbered(attrSpec, d, **kwArgs):
    """
    Renumber CVT indices in the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with CVTs renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
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
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_renumbercvtsdirect': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_renumbercvtsdirect=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (12, 20), 'e': 12}
    >>> dOut = M_cvtsRenumbered(aSp, d, cvtDelta=300)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (None, MyList([312, None, 315]), 315, MyList([312, 320]), 12)
    
    >>> dOut = M_cvtsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=True)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295, None, 15]), 15, MyList([295, 20]), 12)
    
    >>> dOut = M_cvtsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=False)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295, None, None]), None, MyList([295, None]), 12)
    
    >>> func = lambda x, **k: 2 * x - 1
    >>> dOut = M_cvtsRenumbered(aSp, d, cvtMappingFunc=func)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (None, MyList([23, None, 29]), 29, MyList([23, 39]), 12)
    
    >>> dOut = M_cvtsRenumbered(aSp, d)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (None, MyList([12, None, 15]), 15, MyList([12, 20]), 12)
    
    >>> d['b'] = (12, 20)  # will fail; no converter func
    >>> M_cvtsRenumbered(aSp, d, cvtDelta=300)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'cvtsRenumbered'
    """
    
    dNew = dict.fromkeys(attrSpec)
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
        cvtMappingFunc = (lambda x, **k: x + cvtDelta)
    
    else:
        cvtMappingFunc = (lambda x, **k: x)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get(
          'attr_renumbercvtsdeep',
          ks.get('attr_followsprotocol', False)):
            
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.cvtsRenumbered
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).cvtsRenumbered
                else:
                    raise
            
            dNew[k] = boundMethod(**kwArgs)
        
        elif ks.get('attr_renumbercvtsdirect', False):
            dNew[k] = cvtMappingFunc(obj, **kwArgs)
        
        else:
            dNew[k] = obj
    
    return dNew

def M_fdefsRenumbered(attrSpec, d, **kwArgs):
    """
    Renumber FDEF indices in the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with FDEFs renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
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
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_renumberfdefsdirect': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_renumberfdefsdirect=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (12, 20), 'e': 12}
    >>> dOut = M_fdefsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=True)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295, None, 15]), 15, MyList([295, 20]), 12)
    
    >>> dOut = M_fdefsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=False)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295, None, None]), None, MyList([295, None]), 12)
    
    >>> func = lambda x, **k: 2 * x - 1
    >>> dOut = M_fdefsRenumbered(aSp, d, fdefMappingFunc=func)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (None, MyList([23, None, 29]), 29, MyList([23, 39]), 12)
    
    >>> dOut = M_fdefsRenumbered(aSp, d)
    >>> dOut['a'], dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (None, MyList([12, None, 15]), 15, MyList([12, 20]), 12)
    
    >>> d['b'] = (12, 20)  # will fail; no converter func
    >>> M_fdefsRenumbered(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'fdefsRenumbered'
    """
    
    dNew = dict.fromkeys(attrSpec)
    fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    
    if fdefMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        fdefMappingFunc = (
          lambda x,**k: oldToNew.get(x, (x if keepMissing else None)))
    
    else:
        fdefMappingFunc = lambda x,**k: x
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get(
          'attr_renumberfdefsdeep',
          ks.get('attr_followsprotocol', False)):
            
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.fdefsRenumbered
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).fdefsRenumbered
                else:
                    raise
            
            dNew[k] = boundMethod(**kwArgs)
        
        elif ks.get('attr_renumberfdefsdirect', False):
            dNew[k] = fdefMappingFunc(obj, **kwArgs)
        
        else:
            dNew[k] = obj
    
    return dNew

def M_gatheredInputGlyphs(attrSpec, d, **kwArgs):
    """
    Returns a set containing all input glyph indices.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (none defined here)
    :return: A set with all input glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.

    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_renumberdirect': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_renumberdirect=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict(attr_renumberdirect=True, attr_isoutputglyph=True),
    ...   f = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (13, 20), 'e': 14, 'f': 39}
    >>> x = M_gatheredInputGlyphs(aSp, d)
    >>> (isinstance(x, set), sorted(x))
    (True, [12, 13, 15, 20])
    
    >>> d['b'] = (13, 14)
    >>> x = M_gatheredInputGlyphs(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'gatheredInputGlyphs'
    """
    
    r = set()
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None or ks.get('attr_isoutputglyph', False):
            continue
        
        if ks.get('attr_renumberdeep', ks.get('attr_followsprotocol', False)):
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.gatheredInputGlyphs
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).gatheredInputGlyphs
                else:
                    raise
            
            r.update(boundMethod(**kwArgs))
        
        elif ks.get('attr_renumberdirect', False):
            r.add(obj)
    
    return r

def M_gatheredLivingDeltas(attrSpec, d, **kwArgs):
    """
    Returns a set containing all living deltas.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (none defined here)
    :return: A set with all
             :py:class:`~fontio3.opentype.living_variations.LivingDeltas`
             objects
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_islivingdeltas': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_islivingdeltas=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (13, 20), 'e': 39}
    >>> x = M_gatheredLivingDeltas(aSp, d)
    >>> (isinstance(x, set), sorted(x))
    (True, [12, 13, 15, 20])
    
    >>> d['b'] = (13, 14)
    >>> x = M_gatheredLivingDeltas(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'gatheredLivingDeltas'
    """
    
    r = set()
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get('attr_islivingdeltas', False):
            r.add(obj)
        
        elif ks.get('attr_followsprotocol', False):
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.gatheredLivingDeltas
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).gatheredLivingDeltas
                else:
                    raise
            
            r.update(boundMethod(**kwArgs))
    
    return r

def M_gatheredMaxContext(attrSpec, d, **kwArgs):
    """
    Returns an integer representing the maximum context.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (none defined here)
    :return: The longest input context used in glyph substitution
    :rtype: int
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    This is just for the ``'OS/2'`` table, and is antiquated at this point.
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'seq_maxcontextfunc': len}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_maxcontextfunc=max),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': (-1, -3, -5), 'd': (13, 20), 'e': 39}
    >>> M_gatheredMaxContext(aSp, d)
    3
    
    >>> d['b'] = (9, 10)
    >>> M_gatheredMaxContext(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'gatheredMaxContext'
    """
    
    mc = 0
    
    for k, ks in attrSpec.items():
        obj = d[k]
        mcFunc = ks.get('attr_maxcontextfunc', None)
        
        if mcFunc is not None:
            mc = max(mc, mcFunc(obj))
        
        elif ks.get('attr_followsprotocol', False) and obj is not None:
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.gatheredMaxContext
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).gatheredMaxContext
                else:
                    raise
            
            mc = max(mc, boundMethod(**kwArgs))
    
    return mc

def M_gatheredOutputGlyphs(attrSpec, d, **kwArgs):
    """
    Returns a set containing all output glyph indices.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (none defined here)
    :return: A set with all output glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.

    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_renumberdirect': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_renumberdirect=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict(attr_renumberdirect=True, attr_isoutputglyph=True),
    ...   f = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (13, 20), 'e': 14, 'f': 39}
    >>> x = M_gatheredOutputGlyphs(aSp, d)
    >>> (isinstance(x, set), sorted(x))
    (True, [14])
    
    >>> d['b'] = (13, 14)
    >>> x = M_gatheredOutputGlyphs(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'gatheredOutputGlyphs'
    """
    
    r = set()
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get('attr_renumberdeep', ks.get('attr_followsprotocol', False)):
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.gatheredOutputGlyphs
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).gatheredOutputGlyphs
                else:
                    raise
            
            r.update(boundMethod(**kwArgs))
        
        elif (
          ks.get('attr_renumberdirect', False) and
          ks.get('attr_isoutputglyph', False)):
            
            r.add(obj)
    
    return r

def M_gatheredRefs(attrSpec, d, **kwArgs):
    """
    Return a dict with ``Lookup`` objects contained within self.

    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (none defined here)
    :return: A dict mapping ``id(obj)`` to ``obj`` for all objects of type
             :py:class:`~fontio3.opentype.lookup.Lookup`
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
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
    
    ``memo``
        An optional set used to hold the ``id()`` values for the ``Lookup``
        objects. This allows faster execution by preventing potentially deep
        recursive looks through ``Lookup`` objects in fonts like Bustani.
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_islookup': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_islookup=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (13, 20), 'e': 39}
    >>> x = M_gatheredRefs(aSp, d)
    >>> sorted(x.values())
    [12, 13, 15, 20]
    
    >>> d['b'] = (13, 14)
    >>> x = M_gatheredRefs(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'gatheredRefs'
    """
    
    r = {}
    keyTrace = kwArgs.pop('keyTrace', {})
    keyTraceCurr = kwArgs.pop('keyTraceCurr', ())
    memo = kwArgs.pop('memo', set())
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get('attr_islookup', False):
                r[id(obj)] = obj
                ktSet = keyTrace.setdefault(id(obj), set())
                ktSet.add(keyTraceCurr + (k,))
            
            if ks.get('attr_followsprotocol', False):
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.gatheredRefs
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).gatheredRefs
                    else:
                        raise
                
                if id(obj) not in memo:
                    memo.add(id(obj))
                    
                    r.update(
                      boundMethod(
                        keyTrace = keyTrace,
                        keyTraceCurr = keyTraceCurr + (k,),
                        memo = memo,
                        **kwArgs))
    
    return r

def M_glyphsRenumbered(attrSpec, d, oldToNew, **kwArgs):
    """
    Returns a dict matching d, but with glyph indices renumbered.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param oldToNew: Map from old to new glyph index
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with glyphs renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
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
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_renumberdirect': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(attr_renumberdirect=True),
    ...   d = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList),
    ...   e = dict())
    >>> d = {'a': None, 'b': MyList([12, None, 15]), 'c': 15, 'd': (12, 20), 'e': 12}
    >>> dOut = M_glyphsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=True)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295, None, 15]), 15, MyList([295, 20]), 12)
    
    >>> dOut = M_glyphsRenumbered(aSp, d, oldToNew={12: 295}, keepMissing=False)
    >>> dOut['b'], dOut['c'], dOut['d'], dOut['e']
    (MyList([295]), None, MyList([295]), 12)
    
    >>> d['b'] = (12, 20)  # will fail; no converter func
    >>> M_glyphsRenumbered(aSp, d, {12: 295})
    Traceback (most recent call last):
      ...
    AttributeError: 'tuple' object has no attribute 'glyphsRenumbered'
    """
    
    dNew = dict.fromkeys(attrSpec)
    keepMissing = kwArgs.get('keepMissing', True)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get(
              'attr_renumberdeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.glyphsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).glyphsRenumbered
                    else:
                        raise
                
                dNew[k] = boundMethod(oldToNew, **kwArgs)
            
            elif ks.get('attr_renumberdirect', False):
                dNew[k] = oldToNew.get(obj, (obj if keepMissing else None))
            
            else:
                dNew[k] = obj
    
    return dNew

def M_hasCycles(attrSpec, d, **kwArgs):
    """
    Determine if any attribute contains self-referential cycles.

    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
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
    
    >>> class MyList(list, metaclass=_FDM('seq')):
    ...   seqSpec = {'item_followsprotocol': True}
    ...   def __init__(self, v, **k): self[:] = v
    >>> aSp = dict(
    ...   a = dict(attr_followsprotocol=True),
    ...   b = dict(attr_followsprotocol=True),
    ...   c = dict(),
    ...   d = dict(attr_followsprotocol=True),
    ...   e = dict(attr_followsprotocol=True, attr_deepconverterfunc=MyList))
    >>> v1 = MyList([None])
    >>> v2 = MyList([None, v1])
    >>> d = {'a': None, 'b': v2, 'c': 14, 'd': v2, 'e': [None, v1]}
    >>> M_hasCycles(aSp, d)
    False
    >>> M_hasCycles(aSp, d, activeCycleCheck={id(v2)})
    True
    >>> v1.append(v2)
    >>> M_hasCycles(aSp, d)
    True
    
    >>> d = {'a': None, 'b': [None, v1], 'c': None, 'd': None, 'e': None}
    >>> M_hasCycles(aSp, d)
    Traceback (most recent call last):
      ...
    AttributeError: 'list' object has no attribute 'hasCycles'
    """
    
    dACC = kwArgs.pop('activeCycleCheck', set())
    dMemo = kwArgs.get('memo', set())
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if not ks.get('attr_followsprotocol', False):
            continue
        
        objID = id(obj)
        
        if objID in dMemo:
            continue
        
        if objID in dACC:
            return True
        
        cf = ks.get('attr_deepconverterfunc', None)
    
        try:
            boundMethod = obj.hasCycles
    
        except AttributeError:
            if cf is not None:
                boundMethod = cf(obj, **kwArgs).hasCycles
            else:
                raise
        
        if boundMethod(activeCycleCheck=(dACC | {objID}), **kwArgs):
            return True
        
        dMemo.add(objID)
    
    return False

def M_isValid(attrSpec, d, **kwArgs):
    """
    Return True if the data are runtime-valid.

    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: True if the object is valid; False otherwise
    :rtype: bool
    
    Note this is one-half of the validation process; this checks for validity
    of the living object. The other part, validation of the in-font binary
    data, is done by the ``fromvalidated...()`` methods.
    
    The following ``kwArgs`` are supported:
    
    ``activeCycleCheck``
        A dict mapping ``id()`` values of deep objects to the objects
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
    """
    
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
    
    for k in sorted(attrSpec):
        ks = attrSpec[k]
        obj = d[k]
        f = ks.get('attr_subloggernamefunc', None)
        attrLogger = logger.getChild(utilities.ensureUnicode(f(k) if f is not None else k))
        f = ks.get('attr_validatefunc', None)
        fp = ks.get('attr_validatefunc_partial', None)
        vn = ks.get('attr_validatenone', False)
        et = ks.get('attr_ensuretype', None)
        eccTag = ks.get('attr_enablecyclechecktag', None)
        
        if obj is not None and et is not None and (not isinstance(obj, et)):
            attrLogger.error((
              'G0025',
              (),
              "Attribute is not the correct type."))
            
            r = False
        
        elif f is not None:
            if (obj is not None) or vn:
                r = f(obj, logger=attrLogger, **kwArgs) and r
            
            continue  # to next attribute
        
        if fp is not None:
            r = fp(obj, logger=attrLogger, **kwArgs) and r
        
        if (obj is None) and (not vn):
            continue
        
        if ks.get(
          'attr_validatedeep',
          ks.get('attr_followsprotocol', False)):
            
            if eccTag is not None:
                eccDict = dACC.setdefault(eccTag, {})
                
                if id(obj) not in eccDict:
                    eccDict[id(obj)] = obj
                
                else:
                    attrLogger.error((
                      'V0912',
                      (k,),
                      "Circular object reference for attribute '%s'"))
                    
                    return False  # aborts all other checks...
                
                kwArgs['activeCycleCheck'] = dACC
            
            if obj is None:
                attrLogger.error((
                  ks.get('attr_validatecode_deepnone', 'G0013'),
                  (),
                  "None cannot be passed to a deep isValid()."))
                
                r = False
            
            elif hasattr(obj, 'isValid'):
                r = obj.isValid(logger=attrLogger, **kwArgs) and r
            
            else:
                dcf = ks.get('attr_deepconverterfunc', None)
                
                if dcf is not None:
                    cObj = dcf(obj, **kwArgs)
                    r = cObj.isValid(logger=attrLogger, **kwArgs) and r
                
                else:
                    attrLogger.warning((
                      'G0023',
                      (),
                      "Object is not None and not deep, and no converter "
                      "function is provided."))
        
        else:
            renumPCs = ks.get('attr_renumberpcsdirect', False)
            renumPoints = ks.get('attr_renumberpointsdirect', False)
            renumStorage = ks.get('attr_renumberstoragedirect', False)
            
            if ks.get('attr_renumberdirect', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  allowNone = vn,
                  numBits = 16,
                  logger = attrLogger,
                  label = "glyph index"):
                    
                    r = False
                
                elif obj is not None:  # ...since vn might be True
                    pvs = ks.get('attr_prevalidatedglyphset', set())
                    
                    if (obj not in pvs) and (obj >= fontGlyphCount):
                        attrLogger.error((
                          ks.get(
                            'attr_validatecode_toolargeglyph',
                            'G0005'),
                          (obj,),
                          "Glyph index %d too large."))
                        
                        r = False
            
            elif ks.get('attr_renumbernamesdirect', False):
                if not valassist.isFormat_H(
                  obj,
                  allowNone = vn,
                  logger = attrLogger,
                  label = "name table index"):
                  
                    r = False
                
                elif obj not in namesInTable:
                    attrLogger.error((
                      ks.get(
                        'attr_validatecode_namenotintable',
                        'G0042'),
                      (obj,),
                      "Name table index %d not present in 'name' table."))
                    
                    r = False
            
            elif ks.get('attr_renumbercvtsdirect', False):
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  allowNone = vn,
                  numBits = 16,
                  logger = attrLogger,
                  label = "CVT index"):
                    
                    r = False
                
                elif editor is not None:
                    if b'cvt ' not in editor:
                        attrLogger.error((
                          ks.get('attr_validatecode_nocvt', 'G0030'),
                          (obj,),
                          "CVT Index %d is being used, but the font has "
                          "no Control Value Table."))
                        
                        r = False
                    
                    elif obj >= len(editor[b'cvt ']):
                        attrLogger.error((
                          ks.get('attr_validatecode_toolargecvt', 'G0029'),
                          (obj,),
                          "CVT index %d is not defined."))
                        
                        r = False
            
            elif renumPCs or renumPoints or renumStorage:
                if renumPCs:
                    label = "program counter"
                elif renumPoints:
                    label = "point index"
                else:
                    label = "storage index"
            
                if not valassist.isNumber_integer_unsigned(
                  obj,
                  allowNone = vn,
                  numBits = 16,
                  logger = attrLogger,
                  label = label):
                    
                    r = False
                
                elif renumStorage and (editor is not None):
                    if obj > maxStorage:
                        attrLogger.error((
                          'E6047',
                          (obj, maxStorage),
                          "The storage index %d is greater than "
                          "the font's defined maximum of %d."))
                        
                        r = False
            
            elif (
              ks.get('attr_scaledirect', False) or
              ks.get('attr_scaledirectnoround', False)):
              
                if not valassist.isNumber(
                  obj,
                  allowNone = vn,
                  logger = attrLogger):
                    
                    r = False
    
    return r

def M_merged(attrSpec, dSelf, dOther, **kwArgs):
    """
    Create merged attributes.

    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param dSelf: A map from attribute name string to the actual value of the
                  attribute for self
    :type d: dict(str, object)
    :param dOther: A map from attribute name string to the actual value of the
                   attribute for other
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with values merged
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``conflictPreferOther``
        If True (the default) then in the absence of other controls (like deep
        merging, or an explicit merging function) attributes from ``other``
        will be used in the merged object. If False, attributes from ``self``
        will be preferred.
    """
    
    dNew = {}
    prefOther = kwArgs.get('conflictPreferOther', True)
    
    for k, ks in attrSpec.items():
        selfAttr = dSelf[k]
        otherAttr = dOther[k]
        
        if selfAttr is otherAttr:
            dNew[k] = selfAttr
        
        elif selfAttr is not None and otherAttr is not None:
            f = ks.get('attr_mergefunc', None)
            
            if f is not None:
                changed, dNew[k] = f(selfAttr, otherAttr, **kwArgs)
            
            elif ks.get(
              'attr_mergedeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = selfAttr.merged
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(selfAttr, **kwArgs).merged
                    else:
                        raise
                
                try:
                    otherAttr.merged
                
                except AttributeError:
                    if cf is not None:
                        otherAttr = cf(otherAttr, **kwArgs)
                    else:
                        raise
                
                dNew[k] = boundMethod(otherAttr, **kwArgs)
            
            elif prefOther:
                dNew[k] = otherAttr
            
            else:
                dNew[k] = selfAttr
        
        elif otherAttr is not None:
            dNew[k] = otherAttr
        
        else:
            dNew[k] = selfAttr
    
    return dNew

def M_namesRenumbered(attrSpec, d, oldToNew, **kwArgs):
    """
    Returns a dict matching ``d``, but with names renumbered.
    
    :param attrSpec: The attribute specification mapping attribute name
        strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
        attribute
    :type d: dict(str, object)
    :param oldToNew: Map from old to new ``nameID``
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with names renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` without a ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be changed to
        ``None``.
    """
    
    dNew = dict.fromkeys(attrSpec)
    keepMissing = kwArgs.get('keepMissing', True)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get(
              'attr_renumbernamesdeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.namesRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).namesRenumbered
                    else:
                        raise
                
                dNew[k] = boundMethod(oldToNew, **kwArgs)
            
            elif ks.get('attr_renumbernamesdirect', False):
                dNew[k] = oldToNew.get(obj, (obj if keepMissing else None))
            
            else:
                dNew[k] = obj
    
    return dNew

def M_pcsRenumbered(attrSpec, d, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    """
    
    dNew = dict.fromkeys(attrSpec)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get(
              'attr_renumberpcsdeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.pcsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).pcsRenumbered
                    else:
                        raise
                
                dNew[k] = boundMethod(mapData, **kwArgs)
            
            elif ks.get('attr_renumberpcsdirect', False):
                
                # example of mapData: {"Glyph 14": [(12, 2), (40, 3), (67, 6)]}
                # note obj and the [0] elements of mapData are in
                # original, unchanged space
                
                delta = 0
                it = mapData.get(kwArgs.get('infoString', None), [])
                
                for threshold, newDelta in it:
                    if obj < threshold:
                        break
                    
                    delta = newDelta
                
                dNew[k] = obj + delta
            
            else:
                dNew[k] = obj
    
    return dNew

def M_pointsRenumbered(attrSpec, d, mapData, **kwArgs):
    """
    Returns a dict matching ``d``, but with point indices renumbered.
    
    :param attrSpec: The attribute specification mapping attribute name
        strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
        attribute
    :type d: dict(str, object)
    :param mapData: Dict mapping glyph index to an ``oldToNew`` dict
    :type mapData: dict(int, dict(int, int))
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with names renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
        marked as ``attr_followsprotocol`` without a ``attr_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``glyphIndex``
        This is required. It is a glyph index, used to select which
        ``oldToNew`` dict is to be used for the mapping.
    """
    
    dNew = dict.fromkeys(attrSpec)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get(
              'attr_renumberpointsdeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.pointsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).pointsRenumbered
                    else:
                        raise
                
                dNew[k] = boundMethod(mapData, **kwArgs)
            
            elif ks.get('attr_renumberpointsdirect', False):
                glyphIndex = kwArgs.get('glyphIndex')
                glyphMap = mapData.get(glyphIndex, {})
                dNew[k] = glyphMap.get(obj, obj)
            
            else:
                dNew[k] = obj
    
    return dNew

def M_pprint(origObj, p, getNamerFunc, **kwArgs):
    """
    Pretty-print the attributes of ``origObj``.
    
    :param origObj: The object which contains attributes
    :param p: A pretty-printer
    :type p: :py:class:`~fontio3.utilities.pp.PP`
    :param getNamerFunc: A function taking no arguments and returning a
        :py:class:`~fontio3.utilities.namer.Namer`
    :param kwArgs: Optional keyword arguments (described below)
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
    
    ``namer``
        An optional :py:class:`~fontio3.utilities.namer.Namer` object that will
        be used wherever glyph index values are shown.
    """
    
    attrSpec = origObj._ATTRSPEC
    attrSorted = origObj._ATTRSORT
    d = origObj.__dict__
    pd = p.__dict__
    ppSaveDict = {}
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if elideDups is True:
        elideDups = {}  # object ID to serial number
        kwArgs['elideDuplicates'] = elideDups
    
    for k in kwArgs.pop('keys', attrSorted):
        ks = attrSpec[k]
        obj = d[k]
        soif = ks.get('attr_showonlyiffunc', None)
        soifo = ks.get('attr_showonlyiffuncobj', None)
        
        if (soifo is not None) and (not soifo(obj, origObj)):
            continue
        elif (soif is not None) and (not soif(obj)):
            continue
        elif ks.get('attr_showonlyiftrue', False) and (not bool(obj)):
            continue
        
        deep = ks.get('attr_pprintdeep', ks.get('attr_followsprotocol', False))
        f = ks.get('attr_labelfunc', None)
        
        if f is None:
            label = ks.get('attr_label', k)
        elif ks.get('attr_labelfuncneedsobj', False):
            label = f(obj, origObj, **kwArgs)
        else:
            label = f(obj, **kwArgs)
        
        # In the following, we can't just do "if elideDups" since its initial
        # state is an empty dict, which would bool() to False.
        
        if deep and (elideDups is not False):
            objID = id(obj)
            
            if objID in elideDups:
                p.simple(
                  "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                  label = label,
                  **kwArgs)
                
                continue
            
            elif obj is not None:
                elideDups[objID] = len(elideDups)
                p("OBJECT %d" % (elideDups[objID],))
                
                # ...and fall through to do the actual printing below
        
        for key, value in ks.get('attr_ppoptions', {}).items():
            ppSaveDict[key] = pd[key]
            pd[key] = value
        
        if ks.get('attr_usenamerforstr', False):
            nm = kwArgs.get('namer', getNamerFunc())
        else:
            nm = None
        
        f = ks.get('attr_pprintfunc', None)
        fNeedsObj = ks.get('attr_pprintfuncneedsobj', False)
        kwArgs['useRepr'] = ks.get('attr_strusesrepr', False)
        
        if obj is None or (f is None and (not deep)):
            if ks.get('attr_renumberdirect', False) and (nm is not None):
                obj = nm.bestNameForGlyphIndex(obj)
            
            elif ks.get('attr_renumbernamesdirect', False):
                obj = utilities.nameFromKwArgs(obj, **kwArgs)
            
            p.simple(obj, label=label, **kwArgs)
        
        elif f:
            if fNeedsObj:
                kwArgs['parent'] = origObj
            
            f(p, obj, label=label, **kwArgs)
        
        elif deep:
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                obj.getNamer, obj.setNamer, obj.pprint
            
            except AttributeError:
                if cf is not None:
                    obj = cf(obj, **kwArgs)
                else:
                    raise
            
            if nm is not None:
                savedObjNamer = obj.getNamer()
                obj.setNamer(nm)
            
            p.deep(obj, label=label, **kwArgs)
            
            if nm is not None:
                obj.setNamer(savedObjNamer)
        
        while ppSaveDict:
            key, value = ppSaveDict.popitem()
            pd[key] = value

def M_pprintChanges(origSelf, dPrior, p, nm, **kwArgs):
    """
    Pretty-print the differences from the attributes between ``origSelf`` and
    ``dPrior``.
    
    :param origSelf: The object which contains attributes
    :param dPrior: A map from attribute name string to the actual value of the
        attribute for the prior object being compared against
    :type dPrior: dict(str, object)
    :param p: A pretty-printer
    :type p: :py:class:`~fontio3.utilities.pp.PP`
    :param nm: A namer used to show glyph names
    :type nm: :py:class:`~fontio3.utilities.namer.Namer`
    :param kwArgs: Optional keyword arguments (described below)
    :return: None
    
    The following ``kwArgs`` are supported:
    
    ``keys``
        An optional tuple of attribute names. Normally, all the attributes
        listed in the ``attrSorted`` tuple are included in the
        ``pprint_changes()`` output. You can override this by providing your
        own tuple of attribute names in this keyword.
    """
    
    # This function only gets called if self != prior, so we don't need
    # to explicitly check for that case here.
    
    attrSpec = origSelf._ATTRSPEC
    attrSorted = origSelf._ATTRSORT
    dSelf = origSelf.__dict__
    kwArgs.pop('label', None)
    
    for k in kwArgs.get('keys', attrSorted):
        ks = attrSpec[k]
        selfValue = dSelf[k]
        priorValue = dPrior[k]
        
        if (
          (not ks.get('attr_ignoreforcomparisons', False)) and
          (selfValue != priorValue)):
            
            f = ks.get('attr_labelfunc', None)
            
            if f is None:
                label = ks.get('attr_label', k)
            elif ks.get('attr_labelfuncneedsobj', False):
                label = f(selfValue, origSelf, **kwArgs)
            else:
                label = f(selfValue, **kwArgs)
            
            f = ks.get('attr_pprintdifffunc', None)
            useRepr = ks.get('attr_strusesrepr', False)
            
            if f:
                f(p, selfValue, priorValue, label=label)
            
            elif ks.get(
              'attr_pprintdiffdeep',
              ks.get('attr_followsprotocol', False)):
                
                kwArgs['useRepr'] = useRepr
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    selfValue.pprint_changes
                
                except AttributeError:
                    if cf is not None:
                        selfValue = cf(selfValue, **kwArgs)
                    else:
                        raise
                
                p.diff_deep(selfValue, priorValue, label=label, **kwArgs)
            
            else:
                f = (repr if useRepr else str)
                
                if ks.get('attr_renumberdirect', False):
                    if ks.get('attr_usenamerforstr', False):
                        if nm is not None:
                            priorValue = nm.bestNameForGlyphIndex(priorValue)
                            selfValue = nm.bestNameForGlyphIndex(selfValue)
                            f = str  # glyph names are always shown via
                                     # str, not repr
                
                elif ks.get('attr_renumbernamesdirect', False):
                    priorValue = utilities.nameFromKwArgs(priorValue, **kwArgs)
                    selfValue = utilities.nameFromKwArgs(selfValue, **kwArgs)
                    f = str
                
                t = (label, f(priorValue), f(selfValue))
                p("%s changed from %s to %s" % t)

def M_recalculated(attrSpec, d, **kwArgs):
    """
    Recalculate attribute values.
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A dict matching ``d`` but with attributes recalculated
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    """
    
    dNew = dict.fromkeys(attrSpec)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            f = ks.get('attr_recalculatefunc', None)
            
            if f is not None:
                changed, dNew[k] = f(obj, **kwArgs)
            
            elif ks.get(
              'attr_recalculatedeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.recalculated
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).recalculated
                    else:
                        raise
                
                dNew[k] = boundMethod(**kwArgs)
            
            else:
                dNew[k] = obj
    
    return dNew

def M_scaled(attrSpec, d, scaleFactor, **kwArgs):
    """
    Scale attribute values (that is, multiply ``FUnits`` by a scale factor).
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param scaleFactor: The scale factor to use
    :type scaleFactor: float
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with attributes scaled
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
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
    """
    
    dNew = dict.fromkeys(attrSpec)
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            if ks.get('attr_representsx', False) and scaleOnlyInY:
                dNew[k] = obj
            
            elif ks.get('attr_representsy', False) and scaleOnlyInX:
                dNew[k] = obj
            
            elif ks.get(
              'attr_scaledeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.scaled
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).scaled
                    else:
                        raise
                
                dNew[k] = boundMethod(scaleFactor, **kwArgs)
            
            # In the following two direct cases, if the attempt to create a new
            # object via type(obj)(...) fails, then a direct multiplication
            # (possibly with rounding) is attempted instead. This handles cases
            # like triple.collection.Collection objects, which are not protocol
            # objects but which still understand direct arithmetic.
            
            elif ks.get('attr_scaledirect', False):
                roundFunc = ks.get('attr_roundfunc', None)
                
                if roundFunc is None:
                    if ks.get('attr_python3rounding', False):
                        roundFunc = utilities.newRound
                    else:
                        roundFunc = utilities.oldRound
                
                try:
                    dNew[k] = roundFunc(scaleFactor * obj, castType=type(obj))
                except:
                    dNew[k] = roundFunc(scaleFactor * obj)
            
            elif ks.get('attr_scaledirectnoround', False):
                dNew[k] = scaleFactor * obj
            
            else:
                dNew[k] = obj
    
    return dNew

def M_storageRenumbered(attrSpec, d, **kwArgs):
    """
    Renumber storage indices in the attributes.
    
    :param attrSpec: The attribute specification mapping attribute name
        strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
        attribute
    :type d: dict(str, object)
    :param kwArgs: Optional keyword arguments (described below)
    :return: A dict matching ``d`` but with storage indices renumbered
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    
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
    """
    
    dNew = dict.fromkeys(attrSpec)
    storageMappingFunc = kwArgs.get('storageMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    storageDelta = kwArgs.get('storageDelta', None)
    
    if storageMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        storageMappingFunc = (
          lambda x,**k: oldToNew.get(x, (x if keepMissing else None)))
    
    elif storageDelta is not None:
        storageMappingFunc = lambda x,**k: x + storageDelta
    
    else:
        storageMappingFunc = lambda x,**k: x
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is None:
            continue
        
        if ks.get(
          'attr_renumberstoragedeep',
          ks.get('attr_followsprotocol', False)):
            
            cf = ks.get('attr_deepconverterfunc', None)
            
            try:
                boundMethod = obj.storageRenumbered
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(obj, **kwArgs).storageRenumbered
                else:
                    raise
            
            dNew[k] = boundMethod(**kwArgs)
        
        elif ks.get('attr_renumberstoragedirect', False):
            dNew[k] = storageMappingFunc(obj, **kwArgs)
        
        else:
            dNew[k] = obj
    
    return dNew

def M_transformed(attrSpec, d, matrixObj, **kwArgs):
    """
    Transform attribute values (that is, multiply attribute values representing
    X or Y coordinate values in FUnits by a matrix)
    
    :param attrSpec: The attribute specification mapping attribute name
                     strings to dicts of specification flags for that attribute
    :type attrSpec: dict(str, dict)
    :param d: A map from attribute name string to the actual value of the
              attribute
    :type d: dict(str, object)
    :param matrixObj: The matrix to transform x- and y-coordinates
    :type matrixObj: :py:class:`~fontio3.fontmath.matrix.Matrix`
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A dict matching ``d`` but with attributes scaled
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for an attribute
                            marked as ``attr_followsprotocol`` without a
                            ``attr_deepconverterfunc``
    """
    
    dNew = dict.fromkeys(attrSpec)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        cpt = ks.get('attr_transformcounterpart', None)
        
        if obj is not None:
            if ks.get('attr_followsprotocol', False):
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.transformed
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).transformed
                    else:
                        raise
                
                dNew[k] = boundMethod(matrixObj, **kwArgs)
            
            elif cpt is not None:
                try:
                    otherValue = d[cpt]  # might be a key...
                except KeyError:
                    otherValue = cpt     # might just be a number
                
                if ks.get('attr_representsx', False):
                    p = matrixObj.mapPoint((obj, otherValue))[0]
                
                else:
                    assert ks['attr_representsy']
                    p = matrixObj.mapPoint((otherValue, obj))[1]
                
                if not ks.get('attr_transformnoround', False):
                    roundFunc = ks.get('attr_roundfunc', None)
                    
                    if roundFunc is None:
                        if ks.get('attr_python3rounding', False):
                            roundFunc = utilities.newRound
                        else:
                            roundFunc = utilities.oldRound
                    
                    p = roundFunc(p)
                
                dNew[k] = type(obj)(p)
            
            else:
                dNew[k] = obj
    
    return dNew

def SM_bool(attrSpec, d):
    for k, ks in attrSpec.items():
        ignoreBoolean = ks.get('attr_ignoreforbool', False)
        ignoreComparisons = ks.get('attr_ignoreforcomparisons', False)
        ignore = ignoreBoolean or ignoreComparisons
        
        if (not ignore) and bool(d[k]):
            return True
    
    return False

def SM_deepcopy(attrSpec, d, memo):
    dNew = dict.fromkeys(attrSpec)
    
    for k, ks in attrSpec.items():
        obj = d[k]
        
        if obj is not None:
            f = ks.get('attr_deepcopyfunc', None)
            
            if f is not None:
                dNew[k] = memo.setdefault(id(obj), f(obj, memo))
            
            elif ks.get(
              'attr_deepcopydeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    obj.__deepcopy__
                
                except AttributeError:
                    if cf is not None:
                        # Given the temporary nature of obj here, I'm not sure
                        # this code makes a lot of sense...
                        obj = cf(obj, **d.get('kwArgs', {}))
                    
                    else:
                        raise
                
                dNew[k] = memo.setdefault(id(obj), obj.__deepcopy__(memo))
            
            else:
                dNew[k] = obj
    
    return dNew

def SM_eq(attrSpec, otherSpec, dSelf, dOther):
    s = 'attr_ignoreforcomparisons'
    
    for k in set(attrSpec) | set(otherSpec):
        AS = attrSpec.get(k, {})
        OS = otherSpec.get(k, {})
        
        if AS.get(s, False) or OS.get(s, False):
            continue
        
        selfValue = dSelf.get(k, None)
        
        if selfValue is not None:
            if AS.get('attr_useimmutableforcomparisons', False):
                f = AS.get('attr_asimmutablefunc', None)
            
                if f is not None:
                    selfValue = f(selfValue)
                else:
                    selfValue = selfValue.asImmutable()
        
        otherValue = dOther.get(k, None)
        
        if otherValue is not None:
            if OS.get('attr_useimmutableforcomparisons', False):
                f = OS.get('attr_asimmutablefunc', None)
            
                if f is not None:
                    otherValue = f(otherValue)
                else:
                    otherValue = otherValue.asImmutable()
        
        if selfValue is None:
            if otherValue is None:
                continue
            
            return False
        
        elif otherValue is None:
            return False
        
        if selfValue is not otherValue and selfValue != otherValue:
            return False
    
    return True

def SM_lt(attrSpec, attrSorted, otherSpec, dSelf, dOther):
    s = 'attr_ignoreforcomparisons'
    
    for k in attrSorted:  # unlike __eq__, order is important for __lt__
        AS = attrSpec.get(k, {})
        OS = otherSpec.get(k, {})
        
        if AS.get(s, False) or OS.get(s, False):
            continue
        
        selfValue = dSelf.get(k, None)
        
        if selfValue is not None:
            if AS.get('attr_useimmutableforcomparisons', False):
                f = AS.get('attr_asimmutablefunc', None)
            
                if f is not None:
                    selfValue = f(selfValue)
                else:
                    selfValue = selfValue.asImmutable()
        
        otherValue = dOther.get(k, None)
        
        if otherValue is not None:
            if OS.get('attr_useimmutableforcomparisons', False):
                f = OS.get('attr_asimmutablefunc', None)
            
                if f is not None:
                    otherValue = f(otherValue)
                else:
                    otherValue = otherValue.asImmutable()
        
        if selfValue is None:
            if otherValue is None:
                continue
            
            raise TypeError("Cannot do ordering tests on None!")
        
        elif otherValue is None:
            raise TypeError("Cannot do ordering tests on None!")
        
        if selfValue is otherValue:
            continue
        
        if selfValue < otherValue:
            return True
        
        elif selfValue != otherValue:
            return False
    
    return False

def SM_str(origObj, selfNamer):
    attrSpec = origObj._ATTRSPEC
    attrSorted = origObj._ATTRSORT
    d = origObj.__dict__
    sv = []
    fmtStr = ("%s = %s", "%s = (%s)")
    fmtRepr = ("%s = %r", "%s = (%r)")
    
    for k in attrSorted:
        ks = attrSpec[k]
        obj = d[k]
        soif = ks.get('attr_showonlyiffunc', None)
        soifo = ks.get('attr_showonlyiffuncobj', None)
        
        if (soifo is not None) and (not soifo(obj, origObj)):
            continue
        elif (soif is not None) and (not soif(obj)):
            continue
        elif ks.get('attr_showonlyiftrue', False) and (not bool(obj)):
            continue
        
        f = ks.get('attr_labelfunc', None)
        
        if f is None:
            label = ks.get('attr_label', k)
        elif ks.get('attr_labelfuncneedsobj', False):
            label = f(obj, origObj)
        else:
            label = f(obj)
        
        L = (fmtRepr if ks.get('attr_strusesrepr', False) else fmtStr)
        setDeepNamer = False
        
        if ks.get('attr_renumberdeep', ks.get('attr_followsprotocol', False)):
            if (
              ks.get('attr_usenamerforstr', False) and
              (selfNamer is not None)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    obj.getNamer, obj.setNamer, obj.__str__
                
                except AttributeError:
                    if cf is not None:
                        obj = cf(obj, **d.get('kwArgs', {}))
                    else:
                        raise
                
                savedObjNamer = obj.getNamer()
                obj.setNamer(selfNamer)
                setDeepNamer = True
        
        elif (
          ks.get('attr_renumberdirect', False) and
          ks.get('attr_usenamerforstr', False)):
            
            if selfNamer is not None:
                t = (label, selfNamer.bestNameForGlyphIndex(obj))
                sv.append(fmtStr[0] % t)
                continue
        
        elif ks.get('attr_renumbernamesdirect', False):
            t = (label, utilities.nameFromKwArgs(obj, **d.get('kwArgs', {})))
            sv.append(fmtStr[0] % t)
            continue
        
        sv.append(L[ks.get('attr_strneedsparens', False)] % (label, obj))
        
        if setDeepNamer:
            obj.setNamer(savedObjNamer)
    
    return sv

def validateAttrSpec(d):
    """
    Make sure every attribute has an attr_initfunc, and that only known keys
    are present in the attrSpec. (Checks like this are only possible in a
    metaclass, which is another reason to use them over traditional
    subclassing)
    
    >>> d = {'x': {}}
    >>> validateAttrSpec(d)
    >>> 'attr_initfunc' in d['x']
    True
    >>> d = {'x': {'attr_unknownoption': True}}
    >>> validateAttrSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown attrSpec keys: ['attr_unknownoption']
    
    >>> d = {'y': {'attr_initfuncneedsself': True}}
    >>> validateAttrSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Cannot omit attr_initfunc if attr_initfuncneedsself or attr_initfuncchangesself is True!
    
    >>> d = {'z': {'attr_representsx': True, 'attr_representsy': True}}
    >>> validateAttrSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Cannot specify both attr_representsx and attr_representsy at the same time!
    
    >>> d = {'z': {'attr_prevalidatedglyphset': {0, 1}}}
    >>> validateAttrSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Prevalidated glyph set provided for an attribute that is not a glyph index!
    """
    
    for k, ks in d.items():
        unknownKeys = set(ks) - validAttrSpecKeys
        
        if unknownKeys:
            raise ValueError(
              "Unknown attrSpec keys: %s" %
              (sorted(unknownKeys),))
        
        if 'attr_initfunc' not in ks:
            if (
              'attr_initfuncneedsself' in ks or
              'attr_initfuncchangesself' in ks):
                
                raise ValueError(
                  "Cannot omit attr_initfunc if attr_initfuncneedsself "
                  "or attr_initfuncchangesself is True!")
            
            ks['attr_initfunc'] = (lambda: None)
        
        if (
          ks.get('attr_representsx', False) and
          ks.get('attr_representsy', False)):
            
            raise ValueError(
              "Cannot specify both attr_representsx and attr_representsy "
              "at the same time!")
        
        if 'attr_prevalidatedglyphset' in ks:
            if not ks.get('attr_renumberdirect', False):
                raise ValueError(
                  "Prevalidated glyph set provided for an attribute "
                  "that is not a glyph index!")

# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    def _FDM(kind):
        from fontio3.fontdata import seqmeta
        
        if kind == 'seq':
            return seqmeta.FontDataMetaclass
        elif kind == 'map':
            return mapmeta.FontDataMetaclass

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()
