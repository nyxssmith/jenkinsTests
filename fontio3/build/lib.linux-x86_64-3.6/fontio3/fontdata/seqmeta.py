#
# seqmeta.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for fontdata sequences (whether mutable or immutable). Clients
wishing to add fontdata capabilities to their sequence classes should specify
FontDataMetaclass as the metaclass. The following class attributes are used to
control the various behaviors and attributes of instances of the class:
    
``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``seqSpec``
    A dict of specification information for the sequence, where the keys and
    their associated values are defined in the following list. The listed
    defaults apply if the specified key is not present in ``seqSpec``.

    Note keys starting with ``item_`` relate to individual sequence items,
    while keys starting with ``seq_`` relate to the sequence as a whole. Also
    note that in general, functions have higher priority than deep calls, and
    ``None`` values are never passed to either functions or deep calls.

    If a ``seqSpec`` is not provided, an empty one will be used, and all
    defaults listed below will be in force.
        
    ``item_asimmutabledeep``
        If True then sequence values have their own ``asImmutable()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_asimmutablefunc``
        A function called on a sequence value and returning an immutable
        version of that value. If this is not specified, and neither
        ``item_followsprotocol`` nor ``item_asimmutabledeep`` is True, then
        sequence values must already be immutable.
        
        There is no default.
    
    ``item_coalescedeep``
        If True then sequence values have their own ``coalesced()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_compactdeep``
        If True then sequence values have their own ``compacted()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepconverterfunc``
        If present, then ``item_followsprotocol`` should also be True. In this
        case, if a protocol deep function is called on a sequence value and
        fails, this converter function will be called to get an object that
        will succeed with the call. This function takes the sequence value, and
        optional keyword arguments.

        This is useful for cases like sequences of items that are usually
        ``Collection`` objects, but where you wish to also allow simple integer
        values to be set. In this case, if the converter function is something
        like ``toCollection()``, then the value will automatically be converted
        for the purposes of the deep protocol method call. See
        :py:meth:`~fontio3.fontdata.simplemeta.M_asImmutable` for an example of
        :this.
        :
        A note about special methods and converters: if a sequence value is
        deep and uses a converter function, then any call to a special method
        (such as ``__deepcopy__()`` or ``__str__()``) on that sequence value
        will only have access to the optional keyword arguments if an attribute
        named ``kwArgs`` was set in the object's ``__dict__``. You should only
        do this when the extra arguments are needed by the converter function.
        
        There is no default.
    
    ``item_deepcopydeep``
        If True then sequence values have their own ``__deepcopy__()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepcopyfunc``
        A function that is called to deep-copy sequence values. It is called
        with two arguments: the value and a ``memo`` dict.
        
        There is no default.
    
    ``item_enablecyclechecktag``
        If specified (which is only allowed for deep sequence values) then a
        cyclic object check will be made for this sequence's values during
        ``isValid()`` execution. A parent trace will be provided in a passed
        ``kwArg`` called ``activeCycleCheck``, which will be a dict mapping
        tags to lists of parent objects. The tag associated with this
        ``item_enablecyclechecktag`` is what will be used to look up the
        specific parent chain for all sequence values.
        
        Default is ``None``.
    
    ``item_followsprotocol``
        If True then sequence values are themselves Protocol objects, and have
        all the Protocol methods.

        Note that this may be overridden by explicitly setting a desired "deep"
        flag to False. So, for instance, if sequence values are not to have
        ``compacted()`` calls, then the ``seqSpec`` should have this flag set
        to True and ``item_compactdeep`` set to False.
        
        Default is False.
    
    ``item_inputcheckfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate as a sequence member.
        
        There is no default.
    
    ``item_islivingdeltas``
        If True then sequence values will be included in the output from a call
        to ``gatheredLivingDeltas()``.
        
        Default is False.
    
    ``item_islookup``
        If True then sequence values will be included in the output from a call
        to ``gatheredRefs()``.
        
        Default is False.
    
    ``item_isoutputglyph``
        If True then sequence values are treated as output glyphs. This means
        they will not be included in the output of a ``gatheredInputGlyphs()``
        call, and they will be included in the output of a
        ``gatheredOutputGlyphs()`` call. Note that ``item_renumberdirect`` must
        also be set; otherwise sequence values will not be added, even if this
        flag is True.
        
        Default is False.
    
    ``item_mergedeep``
        If True then sequence values have their own ``merged()`` methods. Note
        that these methods may not end up being called, even if this flag is
        True, if the ``merged()`` method is called with the ``replaceWhole``
        keyword argument set to True.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_mergefunc``
        A function that is called on sequence members in two distinct sequences
        (usually ``self`` and ``other``) to do the seriatim merging. This
        function takes two positional arguments (the items from ``self`` and
        ``other``), and optional keyword arguments that were passed into
        ``merged()``. It returns two values: a Boolean indicating whether the
        merged object is different than the original ``self`` argument, and the
        merged object.

        Note that an ``IndexError`` is raised if the two sequences are of
        differing lengths.
        
        There is no default.
    
    ``item_pprintdeep``
        If True then sequence values will be pretty-printed via a call to their
        own ``pprint()`` methods. If False, and a ``seq_pprintfunc`` or
        ``item_pprintfunc`` is specified, that function will be used.
        Otherwise, each item will be printed via the
        :py:meth:`~fontio3.utilities.pp.PP.simple` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintdiffdeep``
        If True then sequence values have their own ``pprint_changes()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintfunc``
        A function that is called to pretty-print sequence values. It is called
        with three arguments: the :py:class:`~fontio3.utilities.pp.PP`
        instance, a sequence value, and a label.
        
        There is no default.
    
    ``item_pprintlabelfunc``
        A function that is called with a sequence index (starting at zero) and
        that returns a string suitable for passing as the label argument to a
        :py:class:`~fontio3.utilities.pp.PP` method. This function may also be
        called with an additional argument, the object itself, if the
        ``item_pprintlabelfuncneedsobj`` flag is True.
        
        There is no default.
    
    ``item_pprintlabelfuncneedsobj``
        If True then calls to the ``item_pprintlabelfunc`` will have an extra
        keyword argument added (in addition to the sequence index already
        passed in as a positional argument). This extra keyword will be
        ``obj``, and the value will be the object itself.
        
        Default is False.
    
    ``item_prevalidatedglyphset``
        A ``set`` or ``frozenset`` containing glyph indices which are to be
        considered valid, even though they exceed the font's glyph count. This
        is useful for passing ``0xFFFF`` values through validation for state
        tables, where that glyph code is used to indicate the deleted glyph.
        
        There is no default.
    
    ``item_python3rounding``
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
        Default is False.
    
    ``item_recalculatedeep``
        If True then sequence values have their own ``recalculated()`` methods.
        
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
        If True then sequence values have their own ``cvtsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbercvtsdirect``
        If True then sequence values are interpreted as CVT values, and are
        subject to renumbering if the ``cvtsRenumbered()`` method is called. If
        sequence indices themselves (rather than values) are CVT indices, use
        ``seq_indexiscvtindex``.
        
        Default is False.
    
    ``item_renumberdeep``
        If True then sequence values have their own ``glyphsRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberdirect``
        If True then all sequence items are interpreted as glyph indices. Any
        method that uses glyph indices (e.g. ``glyphsRenumbered()`` or
        ``gatheredInputGlyphs()``) looks at this flag to ascertain whether
        sequence values are available for processing.
        
        Default is False.
    
    ``item_renumberfdefsdeep``
        If True then sequence values have their own ``fdefsRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdirect``
        If True then sequence values are interpreted as function definition
        numbers (FDEF indices), and are subject to renumbering if the
        ``fdefsRenumbered()`` method is called.
        
        Default is False.
    
    ``item_renumbernamesdeep``
        If True then sequence values have their own ``namesRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdirect``
        If True then non-``None`` sequence values are interpreted as indices
        into the ``'name'`` table, and are subject to being renumbered via a
        ``namesRenumbered()`` call.
        
        Default is False.
    
    ``item_renumberpcsdeep``
        If True then the sequence values have their own ``pcsRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpcsdirect``
        If True then sequence values are themselves PC values. These values
        will be directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``.
        
        Default is False.
    
    ``item_renumberpointsdeep``
        If True then sequence values understand the ``pointsRenumbered()``
        protocol.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpointsdirect``
        If True then sequence values are themselves point indices. Note that if
        this is used, the ``kwArgs`` passed into the ``pointsRenumbered()``
        call must include ``glyphIndex`` which is used to index into that
        method's ``mapData``, unless this is implicitly handled by the presence
        of the ``seq_indexisglyphindex`` flag.
        
        Default is False.
    
    ``item_renumberpreservenone``
        If True then in a sequence for which ``item_renumberdirect`` is True,
        and ``keepMissing`` is False, ``None`` values will be preserved. See
        :py:mod:`fontio3.morx.glyphtupledict` for an example of why this is
        useful.
        
        Default is False.
    
    ``item_renumberstoragedeep``
        If True then sequence values have their own ``storageRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedirect``
        If True then the sequence values are interpreted as storage indices,
        and are subject to renumbering if the ``storageRenumbered()`` method is
        called.
        
        Default is False.
    
    ``item_representsx``
        If True then non-``None`` sequence values are interpreted as
        x-coordinates. This knowledge is used by the ``scaled()`` method, in
        conjunction with the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword
        arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated y-coordinate value will be
        forced to zero. (If both x- and y-coordinates are present in the
        sequence in alternating positions, use the
        ``item_representsxyalternating`` control).
        
        Default is False.
    
    ``item_representsxyalternating``
        If True, sequence elements are treated as x, then y values seriatim. An
        error is raised if ``transformed()`` is called on a sequence with an
        odd number of elements, if this control is set True.
        
        Default is False.
    
    ``item_representsy``
        If True then non-``None`` sequence values are interpreted as
        y-coordinates. This knowledge is used by the ``scaled()`` method, in
        conjunction with the ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword
        arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated x-coordinate value will be
        forced to zero. (If both x- and y-coordinates are present in the
        sequence in alternating positions, use the
        ``item_representsxyalternating`` control).
        
        Default is False.
    
    ``item_roundfunc``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``item_scaledeep``
        If True then sequence entries have their own ``scaled()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_scaledirect``
        If True then non-``None`` sequence entries will be scaled by the
        ``scaled()`` method, with the results rounded to the nearest integral
        value (with .5 cases controlled by ``item_python3rounding``); if this
        is not desired, the client should instead specify the
        ``item_scaledirectnoround`` flag.

        The type of a rounded scaled value will be the type of the original
        value.
        
        Default is False.
    
    ``item_scaledirectnoround``
        If True then sequence entries will be scaled by the ``scaled()``
        method. No rounding will be done on the result; if rounding to integral
        values is desired, use the ``item_scaledirect`` flag instead.

        The type of a non-rounded scaled value will be ``float``.
        
        Default is False.
    
    ``item_strusesrepr``
        If True then the string representation for items in the sequence will
        be created via ``repr()``, not ``str()``.
        
        Default is False.
    
    ``item_subloggernamefunc``
        A function taking a single argument, the key, and returning a string to
        be used for the ``itemLogger`` when that deep value's ``isValid()``
        method is called.
        
        Default is No default (name is [str(key)]).
    
    ``item_subloggernamefuncneedsobj``
        If True, then the ``item_subloggernamefunc`` will be passed a keyword
        argument named ``obj`` containing the entire sequence.
        
        Default is False.
    
    ``item_transformnoround``
        If True, values after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the values will always
        be left as type ``float``, irrespective of original type. This differs
        from the default case, where rounding will be used but the rounded
        result will be the same type as the original value.

        Note the absence of an ``item_transformdirect`` flag. Calls to the
        ``transformed()`` method will only affect non-``None`` sequence values
        if one or more of the ``item_representsx``, ``item_representsy``, or
        ``item_representsxyalternating`` flags are set (or, of course, the
        ``item_followsprotocol`` flag).
        
        Default is False.
    
    ``item_usenamerforstr``
        If this flag and ``item_renumberdirect`` are both True, and a
        :py:class:`~fontio3.utilities.namer.Namer` is available either from a
        :``setNamer()`` call or via
        keyword arguments, then that ``Namer`` will be used for generating the
        strings produced via the ``__str__()`` special method.
        
        Default is False.
    
    ``item_validatecode_badfixedlength``
        The code to be used for logging when a sequence with
        ``seq_fixedlength`` set does not have the specified length.
        
        Default is ``'G0012'``.
    
    ``item_validatecode_namenotintable``
        The code to be used for logging when a ``'name'`` table index is being
        used but that index is not actually present in the ``'name'`` table.
        
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
        The code to be used for logging when a CVT index is used but the
        :py:class:`~fontio3.fontedit.Editor` has no ``'cvt '`` table.
        
        Default is ``'G0030'``.
    
    ``item_validatecode_nonintegercvt``
        The code to be used for logging when a non-integer value is used for a
        CVT index. (Note that ``float`` values representing integral values are
        fine, and will not trigger this)
        
        Default is ``'G0027'``.
    
    ``item_validatecode_nonintegerglyph``
        The code to be used for logging when a non-integer value is used for a
        glyph index. (Note that ``float`` values representing integral values
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
        If True then sequence values have their own ``isValid()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_validatefunc``
        A function taking one positional argument, a sequence value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``item_validatefunc_partial`` instead.
        
        There is no default.
    
    ``item_validatefunc_partial``
        A function taking one positional argument, a sequence value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use an ``item_validatefunc`` instead.
        
        There is no default.
    
    ``item_validatekwargsfunc``
        A function taking two positional arguments (the mapping itself, and the
        sequence index being validated) and returning a dict representing extra
        keyword arguments to be passed along to the deep values' ``isValid()``
        method. Note this should only be provided if ``item_followsprotocol``
        is True.
        
        There is no default.
    
    ``item_wisdom``
        A string encompassing a sensible description of the value, including
        how it is used.
        
        There is, alas, no default for wisdom.
    
    ``item_wisdom_index``
        A string encompassing a sensible description of the sequence index,
        including how it is used.
        
        There is, alas, no default for wisdom.
    
    ``seq_asimmutablefunc``
        A function to create an immutable version of the sequence. This
        function takes the sequence as the sole positional argument, as well as
        the usual ``kwArgs``, and returns the immutable representation.
        
        There is no default.
    
    ``seq_compactremovesfalses``
        If True then any values whose ``bool()`` is False will be removed from
        the sequence in the output of a ``compacted()`` call.
        
        Default is False.
    
    ``seq_enableordering``
        If False (the default) then comparisons for greater-than or less-than
        will be done by the base class methods, and therefore attributes will
        be completely ignored. If attributes are present, and this flag is
        True, then the ``__lt__()``, ``__gt__()``, ``__le__()``, and
        ``__ge__()`` methods will be added, and will take the attributes into
        account.
    
    ``seq_falseifcontentsfalse``
        If True then the sequence as a whole will be treated False if all of
        its contents are either ``None`` or are themselves False. Note that
        since a client has to specify this flag explicitly, its presence forces
        the attributes (if any) to be ignored for purposes of determining
        ``bool()`` value.
        
        Default is False.
    
    ``seq_fixedlength``
        If specified, this key has one of three values: ``None``, True, or a
        positive integer. If the value is ``None`` (the default), then
        instances of the class may have differing lengths, as usual.

        If the value is True, then instances of the class, once created, may
        not change their length via any of the methods that might alter them.
        So, for instance, a call to ``glyphsRenumbered()`` with ``keepMissing``
        set to False that might result in a sequence becoming shorter will, if
        this flag is True, instead result in the sequence being marked invalid,
        and changed to ``None``. This is useful when sequences are used as keys
        in a dict representing glyph sequences, for instance to look up a
        ligature, where any glyph that goes away breaks the whole sequence.

        If the value is a positive integer, then the sequence will always be
        kept at that specified length. This means, for instance, that if glyphs
        are renumbered with ``keepMissing`` set to False, and one or more
        glyphs are not successfully mapped, then the whole sequence is marked
        as invalid (its value becomes ``None``, and a ``compacted()`` call will
        remove it).
        
        Default is ``None``.
    
    ``seq_indexiscvtindex``
        If True sequence indices are interpreted as CVT values, and will be
        subject to a ``cvtsRenumbered()`` call. This will cause the order of
        sequence entries to potentially change!

        It's OK for both this flag and one of ``item_renumbercvtsdeep`` or
        ``item_renumbercvtsdirect`` to be True. The effects will be done on
        both the content and ordering of the sequence in this case.
        
        Default is False.
    
    ``seq_indexisfdefindex``
        If True sequence indices are interpreted as FDEF indices, and will be
        subject to a ``fdefsRenumbered()`` call. This will cause the order of
        sequence entries to potentially change!

        It's OK for both this flag and one of ``item_renumberfdefsdeep`` or
        ``item_renumberfdefsdirect`` to be True. The effects will be done on
        both the content and ordering of the sequence in this case.
        
        Default is False.
    
    ``seq_indexisglyphindex``
        If True then sequence indices are treated as glyph indices by the
        ``gatheredInputGlyphs()``, ``glyphsRenumbered()``, and
        ``pointsRenumbered()`` methods. It is OK for both this flag and also
        one of ``item_renumberdeep`` or ``item_renumberdirect`` to be set.
        However, it is not permitted for this flag and
        ``seq_indexispointindex`` to both be True.
        
        Default is False.
    
    ``seq_indexispointindex``
        If True then sequence indices are treated as point indices by
        ``pointsRenumbered()``. It is OK for both this flag and also one of
        ``item_renumberdeep`` or ``item_followsprotocol`` to be True. However,
        it is not permitted for this flag and ``seq_indexisglyphindex`` to both
        be True.
        
        Default is False.
    
    ``seq_indexisstorageindex``
        If True sequence indices are interpreted as storage indices, and will
        be subject to a ``storageRenumbered()`` call. This will cause the order
        of sequence entries to potentially change!

        It's OK for both this flag and one of ``item_renumberstoragedeep`` or
        ``item_renumberstoragedirect`` to be True. The effects will be done on
        both the content and ordering of the sequence in this case.
        
        Default is False.
    
    ``seq_indexmapstoglyphindexfunc``
        A function taking two positional arguments (the sequence object, and a
        sequence index) and arbitrary keyword arguments. It returns the glyph
        index that sequence index corresponds to.

        Note that the ``seq_indexisglyphindex`` flag is shorthand for this
        function being something like ``lambda self, i, **k: i``.
        
        There is no default.
    
    ``seq_keepsorted``
        If True, then any operation (like renumbering) that can change the
        contents of the sequence will sort the values before returning the new
        sequence. For an example of this, see
        :py:class:`~fontio3.GDEF.attachpoint.AttachPointTable`.

        Note this only applies to direct renumbering, not deep or
        ``seq_indexis...`` cases.
        
        Default is False.
    
    ``seq_makefunc``
        A function taking three arguments: ``self``, ``*args``, and
        ``**kwArgs``. This function will be called when a new object of this
        type needs to be created. Note that in the vast majority of cases the
        client does not need to specify this; it's only useful for cases like
        subclasses of ``defaultdict``, where ``type(self)(d, **k)`` will not
        work.

        If this is not specified, ``type(self)(*args, **kwArgs)`` will be used,
        as usual.
        
        There is no default.
    
    ``seq_maxcontextfunc``
        A function to determine the maximum context for the sequence. This
        function takes a single argument, the sequence itself.
        
        There is no default.
    
    ``seq_mergeappend``
        If True, then any members of the other sequence whose immutable
        representations are not present in the set of immutable representations
        of ``self`` are appended to ``self``. The ``item_asimmutablefunc`` is
        used, if needed, to construct these representations.
        
        Default is False.
    
    ``seq_ppoptions``
        If specified, it should be a dict whose keys are valid options to be
        passed in for construction of a :py:class:`~fontio3.utilities.pp.PP`
        instance, and whose values are as appropriate. This can be used to make
        a custom ``noDataString``, for instance.
        
        There is no default.
    
    ``seq_pprintdifffunc``
        A function to pretty-print differences between two entire sequences.
        The function (which can be an unbound method, as can many other seqSpec
        values) takes at least three arguments: the
        :py:class:`~fontio3.utilities.pp.PP` object, the current sequence, and
        the prior sequence. Other keyword arguments may be specified, as needed.
        
        There is no default.
    
    ``seq_pprintfunc``
        A function taking two positional arguments: a
        :py:class:`~fontio3.utilities.pp.PP` instance, and the sequence as a
        whole. It also takes optional keyword arguments. A frequent use for
        this tag is to specify a value of
        :py:meth:`sequence_grouped <fontio3.utilities.pp.PP.sequence_grouped>` or
        :py:meth:`sequence_grouped_deep <fontio3.utilities.pp.PP.sequence_grouped_deep>`,
        
        There is no default.
    
    ``seq_recalculatefunc``
        If specified, a function taking one positional argument, the whole
        sequence. Additional keyword arguments (for example, ``editor``) may be
        specified.

        The function returns a pair: the first value is True or False,
        depending on whether the recalculated list's value actually changed.
        The second value is the new recalculated object to be used (if the
        first value was True).

        If a ``seq_recalculatefunc`` is provided then no individual
        ``item_recalculatefunc`` calls will be made. If you want them to be
        made, use a ``seq_recalculatefunc_partial`` instead.
        
        There is no default.
    
    ``seq_recalculatefunc_partial``
        A function taking one positional argument, the whole sequence, and
        optional additional keyword arguments. The function should return a
        pair: the first value is True or False, depending on whether the
        recalculated sequence's value actually changed. The second value is the
        new recalculated object to be used (if the first value was True).

        After the ``seq_recalculatefunc_partial`` is done, individual
        ``item_recalculatefunc`` calls will be made. This allows you to "divide
        the labor" in useful ways.
        
        There is no default.
    
    ``seq_validatefunc``
        A function taking one positional argument, the whole sequence, and
        optional additional keyword arguments. The function returns True if the
        sequence is valid, and False otherwise.

        Note that this keyword prevents any ``item_validatefuncs`` from being
        run. If you want to run those as well, then use the
        ``seq_validatefunc_partial`` keyword instead.
        
        There is no default.
    
    ``seq_validatefunc_partial``
        A function taking one positional argument, the whole sequence, and
        optional additional keyword arguments. The function returns True if the
        sequence is valid, and False otherwise. Any ``item_validatefuncs`` will
        also be run to determine the returned True/False value, so this
        function should focus on overall sequence validity.

        If you want this function to do everything without allowing any
        ``item_validatefuns`` to be run, then use the ``seq_validatefunc``
        keyword instead.
        
        There is no default.
    
    ``seq_wisdom``
        A string encompassing a sensible description of the object as a whole,
        including how it is used.
        
        There is, sadly, no default for wisdom.
"""

# System imports
import collections
import functools
import itertools
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

validSeqSpecKeys = frozenset([
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
  'item_mergefunc',
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
  'item_renumberpreservenone',
  'item_renumberstoragedeep',
  'item_renumberstoragedirect',
  'item_representsx',
  'item_representsxyalternating',
  'item_representsy',
  'item_roundfunc',
  'item_scaledeep',
  'item_scaledirect',
  'item_scaledirectnoround',
  'item_strusesrepr',
  'item_subloggernamefunc',
  'item_subloggernamefuncneedsobj',
  'item_transformnoround',
  'item_usenamerforstr',
  'item_validatecode_badfixedlength',
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
  'item_validatekwargsfunc',
  'item_wisdom',
  'item_wisdom_index',
  
  'seq_asimmutablefunc',
  'seq_compactremovesfalses',
  'seq_enableordering',
  'seq_falseifcontentsfalse',
  'seq_fixedlength',
  'seq_indexiscvtindex',
  'seq_indexisfdefindex',
  'seq_indexisglyphindex',
  'seq_indexispointindex',
  'seq_indexisstorageindex',
  'seq_indexmapstoglyphindexfunc',
  'seq_keepsorted',
  'seq_makefunc',
  'seq_maxcontextfunc',
  'seq_mergeappend',
  'seq_ppoptions',
  'seq_pprintdifffunc',
  'seq_pprintfunc',
  'seq_recalculatefunc',
  'seq_recalculatefunc_partial',
  'seq_validatefunc',
  'seq_validatefunc_partial',
  'seq_wisdom'])

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
    :raises AttributeError: If a non-Protocol object is used for a sequence
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
    
    >>> class BottomT(tuple, metaclass=FontDataMetaclass): pass
    >>> class TopT(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> b1 = BottomT([1, 2, 3])
    >>> b2 = BottomT([4, 5, 6])
    >>> t = TopT([b1, b2])
    >>> t.asImmutable()  # already immutable, so just returns t
    ('TopT', TopT((BottomT((1, 2, 3)), BottomT((4, 5, 6)))))
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> t.asImmutable()
    ('Top', ('Bottom', 1, 2, 3), ('Bottom', 4, 5, 6))
    
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...         'someNumber': {},
    ...         'someList': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 4, 6], someList=t, someNumber=5)
    >>> print(obj1.asImmutable())
    (('LPA', 3, 4, 6), ('someList', ('Top', ('Bottom', 1, 2, 3), ('Bottom', 4, 5, 6))), ('someNumber', 5))
    
    >>> class Test1(list, metaclass=FontDataMetaclass): pass
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test2([Test1([3, 4]), None, 5]).asImmutable())
    ('Test2', ('Test1', 3, 4), None, ('Test1', 5))
    
    >>> def fSpecial(obj, **kwArgs):
    ...     return frozenset(set(obj) | {('x', obj.x)})
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_asimmutablefunc = fSpecial)
    ...     attrSpec = dict(
    ...         x = dict())
    
    >>> t3 = Test3([5, 1, 3, -1, 5, 2, 5], x=-2)
    >>> t3.asImmutable() == frozenset({1, 2, 3, ('x', -2), 5, -1})
    True
    """
    
    SS = self._SEQSPEC
    fWhole = SS.get('seq_asimmutablefunc', None)
    
    if fWhole is not None:
        return fWhole(self, **kwArgs)
    
    try:
        hash(self)
        return (type(self).__name__, self)
    
    except:
        pass
    
    f = SS.get('item_asimmutablefunc', None)
    
    if f is not None:
        t = (type(self).__name__,)
        t += tuple(None if obj is None else f(obj) for obj in self)
    
    elif SS.get('item_asimmutabledeep', SS.get('item_followsprotocol', False)):
        memo = kwArgs.get('memo', {})
        cf = SS.get('item_deepconverterfunc', None)
        v = [type(self).__name__]
        
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
        
        t = tuple(v)
    
    else:
        t = (type(self).__name__,) + tuple(self)
    
    tAttr = attrhelper.M_asImmutable(
      self._ATTRSPEC,
      self._ATTRSORT,
      self.__dict__,
      **kwArgs)
    
    return ((t,) + tAttr if tAttr else t)

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
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...   seqSpec = dict(
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
    
    SS = self._SEQSPEC
    f = SS.get('item_inputcheckfunc', None)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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

    ``separateAttributesPool``
        If False (the default), then the same pool will be used for both
        non-attribute members (e.g. sequence values) and attribute members of
        self. If True, the pool will be cleared before attributes are
        coalesced.
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(x = dict())
    >>> t1 = Test1([2000, 1950 + 50], x = 200 * 10)
    >>> t1[0] == t1[1], t1[0] == t1.x, t1[1] == t1.x
    (True, True, True)
    >>> t1[0] is t1[1], t1[0] is t1.x, t1[1] is t1.x
    (False, False, False)
    >>> t1C = t1.coalesced()
    >>> t1C == t1
    True
    >>> t1C[0] is t1C[1], t1C[0] is t1C.x, t1C[1] is t1C.x
    (True, True, True)
    >>> t1CS = t1.coalesced(separateAttributesPool=True)
    >>> t1CS == t1
    True
    >>> t1CS[0] is t1CS[1], t1CS[0] is t1CS.x, t1CS[1] is t1CS.x
    (True, False, False)
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    ...     attrSpec = dict(y = dict())
    >>> t2 = Test2([t1, None], y = 6000 // 3)
    >>> t2[0].x == t2.y, t2[0].x is t2.y
    (True, False)
    >>> t2C = t2.coalesced()
    >>> t2 == t2C
    True
    >>> t2C[0].x == t2C.y, t2C[0].x is t2C.y
    (True, True)
    
    >>> NT = collections.namedtuple("MyNT", "a b c")
    >>> class S(NT, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_asimmutablefunc = tuple,
    ...         seq_makefunc = (lambda v,a: type(v)(*a)))
    >>> s = S([0, 1], [1, 2], [1, 2])
    >>> s.b == s.c, s.b is s.c
    (True, False)
    >>> sCoalesced = s.coalesced()
    >>> sCoalesced == s
    True
    >>> sCoalesced.b == sCoalesced.c, sCoalesced.b is sCoalesced.c
    (True, True)
    
    >>> class Test3(list, metaclass=FontDataMetaclass): pass
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test3([x])),
    ...         item_followsprotocol = True)
    
    >>> obj = Test4([5, Test3([5])]).coalesced()
    >>> obj[0] is obj[1]
    True
    """
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    SS = self._SEQSPEC
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
    
    # First do sequence objects
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
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        r = makeFunc(self, vNew, **dNew)
    else:
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
    ``seq_compactremovesfalses`` flag in the ``seqSpec``) members of the
    sequence for which the ``bool()`` result is False are removed.

    Note that any attributes with their own ``compacted()`` method have access
    to the compacted sequence (just a list, not an object of the same class as
    ``self``) as a ``kwArg`` named ``parentObj``. See the
    :py:class:`~fontio3.mort.features.Features` class for an example of how
    this is useful.
    
    If entries are removed from a sequence for which ``seq_fixedlength`` is
    True, then None will be returned instead.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_compactremovesfalses = True)
    >>> t1 = Test1([3, 0, False, None, '', 4])
    >>> print(t1.compacted())
    (3, 4)
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True,
    ...         seq_compactremovesfalses = True)
    ...     attrSpec = dict(x = dict(attr_followsprotocol = True))
    >>> t2 = Test2([t1, None], x = t1)
    >>> print(t2)
    ((3, 0, False, None, , 4), None), x = (3, 0, False, None, , 4)
    >>> print(t2.compacted())
    ((3, 4),), x = (3, 4)
    
    >>> class Test3(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'seq_fixedlength': True,
    ...       'seq_compactremovesfalses': True}
    >>> print(Test3([1, 2]).compacted())
    (1, 2)
    >>> print(Test3([0, '', 1, 2]).compacted())
    None
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_compactremovesfalses = True,
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [0, 3, None, '', [], {}])
    >>> print(s)
    [0, 3, None, '', [], {}]
    >>> sCompacted = s.compacted()
    >>> print(sCompacted)
    [3]
    >>> print(sCompacted.name)
    fred
    
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_compactremovesfalses = True)
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test4([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test5([0, Test4([0, '', False, 3, {}])]).compacted())
    [[], [3]]
    """
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    SS = self._SEQSPEC
    vDeep = SS.get('item_compactdeep', SS.get('item_followsprotocol', False))
    vFilter = SS.get('seq_compactremovesfalses', False)
    vFixedLen = SS.get('seq_fixedlength', None)
    cf = SS.get('item_deepconverterfunc', None)
    vNew = []
    
    # First do sequence objects
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
    
    # If the length is fixed but items were removed, we are no longer valid
    
    if (
      (len(vNew) != len(self)) and
      (vFixedLen is True or vFixedLen is not None)):
        
        return None
    
    # Now do attributes
    kwArgs['parentObj'] = vNew
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        r = makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumbercvtsdirect = True)
    
    >>> print(Test1([15, 80, None, 29]).cvtsRenumbered(cvtDelta=1000))
    (1015, 1080, None, 1029)
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> t = Test1([25, 27, None, 26, 30])
    >>> print(t.cvtsRenumbered(oldToNew=d))
    (1025, 1001, None, 1000, 30)
    >>> print(t.cvtsRenumbered(oldToNew=d, keepMissing=False))
    (1025, 1001, None, 1000, None)
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1([10, 15, None]).cvtsRenumbered(cvtMappingFunc=f))
    (910, 15, None)
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.cvtsRenumbered(cvtDelta=-3))
    [(12, None, 17), None, (17, 87)]
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_indexiscvtindex = True)
    >>> t = Test3(['a', 'b', 'c', 'd'])
    >>> print(t.cvtsRenumbered(cvtDelta=4))
    ['a', 'b', 'c', 'd', 'a', 'b', 'c', 'd']
    >>> print(t.cvtsRenumbered(cvtDelta=4, keepMissing=False))
    [None, None, None, None, 'a', 'b', 'c', 'd']
    >>> print(t.cvtsRenumbered(oldToNew={0:2, 2:0}))
    ['c', 'b', 'a', 'd']
    >>> print(t.cvtsRenumbered(oldToNew={0:2, 2:0}, keepMissing=False))
    ['c', None, 'a', None]
    """
    
    SS = self._SEQSPEC
    cvtMappingFunc = kwArgs.get('cvtMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    cvtDelta = kwArgs.get('cvtDelta', None)
    fixedLen = SS.get('seq_fixedlength', None)
    
    if cvtMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        cvtMappingFunc = (
          lambda x,**k: oldToNew.get(x, (x if keepMissing else None)))
    
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
        
        vNew = [None] * len(self)
        
        for i, obj in enumerate(_it()):
            if obj is not None:
                vNew[i] = obj.cvtsRenumbered(**kwArgs)
    
    elif SS.get('item_renumbercvtsdirect', False):
        vNew = [None] * len(self)
        
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = cvtMappingFunc(obj, **kwArgs)
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = list(self)
    
    if vNew and SS.get('seq_indexiscvtindex', False):
        saved = list(vNew)
        newIndices = {i: cvtMappingFunc(i, **kwArgs) for i in range(len(self))}
        revIndices = {n: i for i, n in newIndices.items() if n is not None}
        count = max(len(saved), 1 + utilities.safeMax(revIndices))
        vNew = [None] * count
        
        for new in range(count):
            if new in revIndices:
                vNew[new] = saved[revIndices[new]]
            elif keepMissing and (new < len(saved)):
                vNew[new] = saved[new]
            else:
                vNew[new] = None
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberfdefsdirect = True)
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> t = Test1([25, 27, None, 26, 30])
    >>> print(t.fdefsRenumbered(oldToNew=d))
    (1025, 1001, None, 1000, 30)
    >>> print(t.fdefsRenumbered(oldToNew=d, keepMissing=False))
    (1025, 1001, None, 1000, None)
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens go up by 900
    >>> print(Test1([10, 15, None]).fdefsRenumbered(fdefMappingFunc=f))
    (910, 15, None)
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.fdefsRenumbered(fdefMappingFunc=f))
    [(15, None, 920), None, (920, 990)]
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_indexisfdefindex = True)
    >>> t = Test3(['a', 'b', 'c', 'd'])
    >>> print(t.fdefsRenumbered(oldToNew={0:2, 2:0}))
    ['c', 'b', 'a', 'd']
    >>> print(t.fdefsRenumbered(oldToNew={0:2, 2:0}, keepMissing=False))
    ['c', None, 'a', None]
    """
    
    SS = self._SEQSPEC
    fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    fixedLen = SS.get('seq_fixedlength', None)
    
    if fdefMappingFunc is not None:
        pass
    
    elif oldToNew is not None:
        fdefMappingFunc = (
          lambda x,**k: oldToNew.get(x, (x if keepMissing else None)))
    
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
        
        vNew = [None] * len(self)
        
        for i, obj in enumerate(_it()):
            if obj is not None:
                vNew[i] = obj.fdefsRenumbered(**kwArgs)
    
    elif SS.get('item_renumberfdefsdirect', False):
        vNew = [None] * len(self)
        
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = fdefMappingFunc(obj, **kwArgs)
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = list(self)
    
    if vNew and SS.get('seq_indexisfdefindex', False):
        saved = list(vNew)
        
        newIndices = {
          i: fdefMappingFunc(i, **kwArgs)
          for i in range(len(self))}
        
        revIndices = {n: i for i, n in newIndices.items() if n is not None}
        count = max(len(saved), 1 + utilities.safeMax(revIndices))
        vNew = [None] * count
        
        for new in range(count):
            if new in revIndices:
                vNew[new] = saved[revIndices[new]]
            elif keepMissing:
                vNew[new] = saved[new]
            else:
                vNew[new] = None
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class BottomIn(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class BottomOut(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> class BottomLIIGI(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_indexisglyphindex': True}
    >>> class BottomLIIGIFunc(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'seq_indexmapstoglyphindexfunc': (lambda obj,i,**k: len(obj)+i)}
    >>> class BottomBoth(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_renumberdirect': True,
    ...       'seq_indexisglyphindex': True}
    >>> class BottomAll(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_renumberdirect': True,
    ...       'seq_indexisglyphindex': True,
    ...       'item_isoutputglyph': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> bIn = BottomIn([20, 21])
    >>> bOut = BottomOut([32, 33])
    >>> bLIIGI = BottomLIIGI([-1])
    >>> bBoth = BottomBoth([7, 6])
    >>> bAll = BottomAll([3, 3, 3])
    >>> t = Top([bIn, bOut, bLIIGI, bBoth, bAll])
    >>> print(sorted(t.gatheredInputGlyphs()))
    [0, 1, 2, 6, 7, 20, 21]
    >>> bLIIGIFunc = BottomLIIGIFunc([2, 5, 6, 9, 11])
    >>> sorted(bLIIGIFunc.gatheredInputGlyphs())
    [5, 6, 7, 8, 9]
    
    >>> class Bottom(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    ...     attrSorted = ('bot',)
    >>> class Top(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
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
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> sorted(Test2([3, Test1([4, 5])]).gatheredInputGlyphs())
    [3, 4, 5]
    """
    
    SS = self._SEQSPEC
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
        
    # We assume list indices used as glyph indices are always input glyphs
    if SS.get('seq_indexisglyphindex', False):
        r.update(range(len(self)))
    
    else:
        mapFunc = SS.get('seq_indexmapstoglyphindexfunc', None)
        
        if mapFunc is not None:
            r.update(
              map(
                mapFunc,
                itertools.repeat(self, len(self)),
                range(len(self))))
    
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
    integers in lieu of actual ``LivingDeltas`` objects. Since those objects
    are immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual ``LivingDeltas`` objects!
    
    >>> class Bottom(tuple, metaclass=FontDataMetaclass):
    ...   seqSpec = {'item_islivingdeltas': True}
    ...   attrSpec = {'a': {'attr_islivingdeltas': True}, 'b': {}}
    >>> class Top(tuple, metaclass=FontDataMetaclass):
    ...   seqSpec = {'item_followsprotocol': True}
    ...   attrSpec = {'c': {'attr_islivingdeltas': True}, 'd': {}}
    >>> botObj = Bottom([3, -1, 4], a=9, b=-3)
    >>> topObj = Top([None, botObj], c=13, d=-13)
    >>> sorted(topObj.gatheredLivingDeltas())
    [-1, 3, 4, 9, 13]
    """
    
    SS = self._SEQSPEC
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
    
    >>> class Bottom(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_maxcontextfunc': (lambda v: len(v) - 1)}
    >>> b1 = Bottom([1, 3, 5])
    >>> b2 = Bottom([6, 7, 8, 10, 12, 15, 2])
    >>> b1.gatheredMaxContext(), b2.gatheredMaxContext()
    (2, 6)
    
    >>> class Top(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top([b1, None], x = [8, 1, 4], y=b2).gatheredMaxContext()
    8
    >>> Top([b1, None], x = [4, 1, 4], y=b2).gatheredMaxContext()
    6
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_maxcontextfunc = len)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test2([Test1([3, 4]), None, 5]).gatheredMaxContext())
    2
    >>> print(Test2([Test1([]), None, 5]).gatheredMaxContext())
    1
    """
    
    SS = self._SEQSPEC
    mcFunc = SS.get('seq_maxcontextfunc', None)
    
    if mcFunc is not None:
        mc = mcFunc(self, **kwArgs)
    
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
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> class BottomIn(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class BottomOut(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    >>> class BottomLIIGI(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_indexisglyphindex': True}
    >>> class BottomBoth(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_renumberdirect': True,
    ...       'seq_indexisglyphindex': True}
    >>> class BottomAll(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_renumberdirect': True,
    ...       'seq_indexisglyphindex': True,
    ...       'item_isoutputglyph': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> bIn = BottomIn([20, 21])
    >>> bOut = BottomOut([32, 33])
    >>> bLIIGI = BottomLIIGI([-1])
    >>> bBoth = BottomBoth([7, 6])
    >>> bAll = BottomAll([3, 3, 3])
    >>> t = Top([bIn, bOut, bLIIGI, bBoth, bAll])
    >>> sorted(t.gatheredOutputGlyphs())
    [3, 32, 33]
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True, 'item_isoutputglyph': True}
    ...     attrSpec = {
    ...       'bot': {
    ...         'attr_renumberdirect': True,
    ...         'attr_isoutputglyph': True}}
    ...     attrSorted = ('bot',)
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    ...     attrSpec = dict(
    ...         topDirect = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topIrrelevant = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom([61, 62], bot=5)
    >>> t = Top([71, 72], topDirect=11, topDeep=b, topIrrelevant=20)
    >>> print(sorted(t.gatheredOutputGlyphs()))
    [5, 11, 61, 62]
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_isoutputglyph = True,
    ...         item_renumberdirect = True)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> sorted(Test2([3, Test1([4, 5])]).gatheredOutputGlyphs())
    [3, 4, 5]
    """
    
    SS = self._SEQSPEC
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

    :param kwArgs: Optional keyword arguments (see below)
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
        have already been found to have no cycles. It speeds up the process.
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_islookup = True)
    >>> class Middle(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> b1 = Bottom([object(), None, object()])
    >>> b2 = Bottom([b1[0], None, object()])
    >>> m = Middle([b1, None, b2])
    >>> kt = {}
    >>> d = m.gatheredRefs(keyTrace=kt)
    >>> id(b1[0]) in d, id(b2[2]) in d
    (True, True)
    >>> id(b1[1]) in d  # None is not added
    False
    >>> for s in sorted(repr(sorted(x)) for x in kt.values()): print(s)
    [(0, 0), (2, 0)]
    [(0, 2)]
    [(2, 2)]
    
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_islookup = True))
    >>> t = Top([1, 3, 5], x=m, y=object())
    >>> kt = {}
    >>> d = t.gatheredRefs(keyTrace=kt)
    >>> id(b1[0]) in d, id(b2[2]) in d, id(t.y) in d
    (True, True, True)
    >>> id(b1[1]) in d  # None is not added
    False
    >>> for s in sorted(repr(sorted(x)) for x in kt.values()): print(s)
    [('(attr)', 'x', 0, 0), ('(attr)', 'x', 2, 0)]
    [('(attr)', 'x', 0, 2)]
    [('(attr)', 'x', 2, 2)]
    [('(attr)', 'y')]
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_islookup = True)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> d = Test2([5, Test1([3, 4]), None]).gatheredRefs()
    >>> sorted(d.values())
    [3, 4, 5]
    """
    
    SS = self._SEQSPEC
    r = {}
    keyTrace = kwArgs.pop('keyTrace', {})
    keyTraceCurr = kwArgs.pop('keyTraceCurr', ())
    memo = kwArgs.pop('memo', set())
    
    # Note that deep objects themselves can be lookups, so the following two
    # blocks are not "if-elif" but just two "if"s.
    
    if SS.get('item_islookup', False):
        for i, obj in enumerate(self):
            if obj is not None:
                r[id(obj)] = obj
                ktSet = keyTrace.setdefault(id(obj), set())
                ktSet.add(keyTraceCurr + (i,))
    
    if SS.get('item_followsprotocol', False):
        cf = SS.get('item_deepconverterfunc', None)
        
        for i, obj in enumerate(self):
            if obj is not None:
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
                        keyTraceCurr = keyTraceCurr + (i,),
                        memo = memo,
                        **kwArgs))
    
    r.update(
      attrhelper.M_gatheredRefs(
        self._ATTRSPEC,
        self.__dict__,
        keyTrace = keyTrace,
        keyTraceCurr = keyTraceCurr + ('(attr)',),
        memo = memo,
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
        
    ``missingKeyReplacementFunc``
        This is only useful if ``seq_indexisglyphindex`` is True. In this case,
        if ``keepMissing`` is False, normally sequence indices that are missing
        from ``oldToNew`` will simply be removed from the sequence. If this
        keyword argument is present, by contrast, each index which would
        otherwise have been changed to ``None`` will instead be replaced with
        the value returned from this function.

        The function is called with the old sequence index as the single
        positional argument, and with the usual keyword arguments.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    ...     attrSpec = dict(
    ...         x = dict(attr_renumberdirect = True))
    >>> t1 = Test1([10, 20, 30], x=40)
    >>> print(t1.glyphsRenumbered({10:5, 20:6, 30:7, 40:8}))
    (5, 6, 7), x = 8
    >>> print(t1.glyphsRenumbered({10:5, 40:8}, keepMissing=True))
    (5, 20, 30), x = 8
    >>> print(t1.glyphsRenumbered({10:5, 40:8}, keepMissing=False))
    (5,), x = 8
    
    >>> class Test2Bottom(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    ...     attrSpec = dict(x = dict(attr_renumberdirect = True))
    >>> class Test2Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    ...     attrSpec = dict(y = dict(attr_followsprotocol = True))
    >>> t2B1 = Test2Bottom([10, 20], x = 30)
    >>> t2B2 = Test2Bottom([40], x = 50)
    >>> t2B3 = Test2Bottom([], x = 60)
    >>> t2T = Test2Top([t2B1, t2B3], y=t2B2)
    >>> print(t2T)
    [(10, 20), x = 30, (), x = 60], y = (40,), x = 50
    >>> print(t2T.glyphsRenumbered({10:5, 20:6, 30:7, 40:8, 50:9, 60:200}))
    [(5, 6), x = 7, (), x = 200], y = (8,), x = 9
    >>> print(t2T.glyphsRenumbered({10:5, 40:8, 60:200}, keepMissing=True))
    [(5, 20), x = 30, (), x = 200], y = (8,), x = 50
    >>> print(t2T.glyphsRenumbered({10:5, 40:8, 60:200}, keepMissing=False))
    [(5,), x = None, (), x = 200], y = (8,), x = None
    
    >>> class Test3(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_indexisglyphindex = True)
    >>> t3 = Test3([200, 250, 300])
    >>> print(t3.glyphsRenumbered({0: 3, 1: 0, 2: 1}))
    (250, 300, 300, 200)
    >>> print(t3.glyphsRenumbered({0: 3, 1: 0, 2: 1}, keepMissing=False))
    (250, 300, None, 200)
    
    >>> class Test4(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_fixedlength': True, 'item_renumberdirect': True}
    >>> d = {10: 2, 15: 3}
    >>> print(Test4([10, 15, 20]).glyphsRenumbered(d, keepMissing=True))
    (2, 3, 20)
    >>> print(Test4([10, 15, 20]).glyphsRenumbered(d, keepMissing=False))
    None
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True,
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [10, 25, 35])
    >>> print(s)
    [10, 25, 35]
    >>> sRenumbered = s.glyphsRenumbered(
    ...   {10: 1, 20: 2, 25: 3},
    ...   keepMissing=False)
    >>> print(sRenumbered)
    [1, 3]
    >>> sRenumbered.name
    'fred'
    
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test6(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test5([x])),
    ...         item_followsprotocol = True)
    
    >>> md = {5: 10, 6: 11, 7: 12}
    >>> print(Test6([5, None, Test5([6, 7])]).glyphsRenumbered(md))
    [[10], None, [11, 12]]
    
    >>> class Test7(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_indexmapstoglyphindexfunc = (
    ...           lambda obj, i, **k: obj.firstGlyph + i))
    ...     attrSpec = dict(
    ...         firstGlyph = dict(attr_renumberdirect = True))
    >>> obj = Test7(['a', 'b', 'c', 'd', 'e', 'f'], firstGlyph=35)
    >>> md = {36: 38, 38: 36}
    >>> print(obj.glyphsRenumbered(md))
    ('a', 'd', 'c', 'b', 'e', 'f'), firstGlyph = 35
    
    >>> class Test8(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_indexisglyphindex = True)
    >>> fn = (lambda i, **k: "Gone %d" % (i,))
    >>> otn = {1: 1, 5: 5}
    >>> t = Test8(['Here 0', 'Here 1', 'Here 2', 'Here 3', 'Here 4', 'Here 5'])
    >>> print(t)
    (Here 0, Here 1, Here 2, Here 3, Here 4, Here 5)
    >>> print(t.glyphsRenumbered(otn, keepMissing=False))
    (None, Here 1, None, None, None, Here 5)
    >>> print(
    ...   t.glyphsRenumbered(
    ...     otn,
    ...     keepMissing = False,
    ...     missingKeyReplacementFunc = fn))
    (Gone 0, Here 1, Gone 2, Gone 3, Gone 4, Here 5)
    
    >>> class Test9(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True)
    >>> class Test9P(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True,
    ...         item_renumberpreservenone = True)
    >>> Test9([2, None]).glyphsRenumbered({2: 2}, keepMissing=False)
    Test9((2,))
    >>> Test9P([2, None]).glyphsRenumbered({2: 2}, keepMissing=False)
    Test9P((2, None))
    """
    
    SS = self._SEQSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    fixedLen = SS.get('seq_fixedlength', None)
    preserveNone = SS.get('item_renumberpreservenone', False)
    
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
          ( None if obj is None
            else obj.glyphsRenumbered(oldToNew, **kwArgs))
          for obj in _it()]
    
    elif SS.get('item_renumberdirect', False):
        if keepMissing:
            vNew = [oldToNew.get(obj, obj) for obj in self]
        
        elif preserveNone:
            vNew = []
            
            for obj in self:
                if obj is None:
                    vNew.append(obj)
                elif obj in oldToNew:
                    vNew.append(oldToNew[obj])
        
        else:
            vNew = [oldToNew[obj] for obj in self if obj in oldToNew]
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = list(self)
    
    mapFunc = SS.get('seq_indexmapstoglyphindexfunc', None)
    
    if SS.get('seq_indexisglyphindex', False):
        saved = list(vNew)
        count = 1 + utilities.safeMax(oldToNew.values())
        missKeyFunc = kwArgs.get('missingKeyReplacementFunc', None)
        
        if missKeyFunc is None:
            vNew[:] = [None] * count
        else:
            vNew[:] = [missKeyFunc(i, **kwArgs) for i in range(count)]
        
        revMap = dict(zip(oldToNew.values(), oldToNew.keys()))
        
        for new in range(count):
            if new in revMap:
                vNew[new] = saved[revMap[new]]
            elif keepMissing:
                vNew[new] = saved[new]
    
    elif mapFunc is not None:
        # For the seq_indexmapstoglyphindexfunc case we need to pre-construct a
        # mapping of sequence index to resolved glyph index. This will limit
        # the mappings done through oldToNew. Note that this means the sequence
        # will NOT resize if the largest value in oldToNew happens to be larger
        # than the largest computed sequence index; unlike the simpler
        # seq_indexisglyphindex case, this will only affect values where both
        # the old and new are present in the glyph index space.
        #
        # An example might help. Suppose we have the following sequence, with
        # the natural and mapped indices below:
        #
        # ['a', 'b', 'c', 'd', 'e', 'f']
        #   0    1    2    3    4    5
        #  19   21   23   25  100   27
        #
        # Further, suppose oldToNew is {19: 23, 23: 25, 25: 19}. We then expect
        # this output:
        #
        # ['d', 'b', 'a', 'c', 'e', 'f']
        
        naturalToMapped = {
          i: mapFunc(self, i, **kwArgs)
          for i in range(len(self))}
        
        mappedToNatural = {
          value: key
          for key, value in naturalToMapped.items()}
        
        revMap = {value: key for key, value in oldToNew.items()}
        saved = list(vNew)
        
        for natural, value in enumerate(saved):
            newGlyphIndex = naturalToMapped.get(natural, None)
            
            if newGlyphIndex is not None and newGlyphIndex in revMap:
                oldGlyphIndex = revMap[newGlyphIndex]
                savedIndex = mappedToNatural.get(oldGlyphIndex, None)
                
                if savedIndex is not None:
                    vNew[natural] = saved[savedIndex]
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
        return type(self)(vNew, **dNew)

def M_hasCycles(self, **kwArgs):
    """
    Determines if self is self-referential.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``activeCycleCheck``
        A set of ``id()`` values of deep objects. This is used to track deep
        usage; if at any level an object is encountered whose ``id()`` value is
        already present in this set, the function returns True. Note that it's
        safe to use object ID values, since this call does not mutate any data.
    
    ``memo``
        An optional set. This is used to store the ID values of objects that
        have already been found to have no cycles. It speeds up the process.
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True)
    ...     attrSpec = dict(
    ...         deepAttr = dict(
    ...             attr_followsprotocol = True))
    >>> obj1 = Test1([None], deepAttr=None)
    >>> obj2 = Test1([obj1, None], deepAttr=obj1)
    >>> obj1.hasCycles(), obj2.hasCycles()
    (False, False)
    >>> obj2.deepAttr = obj2
    >>> obj2.hasCycles()
    True
    >>> obj2.deepAttr = None
    >>> obj2.append(obj2)
    >>> obj2.hasCycles()
    True
    """
    
    SS = self._SEQSPEC
    dACC = kwArgs.pop('activeCycleCheck', set())
    dMemo = kwArgs.get('memo', set())
    
    if SS.get('item_followsprotocol', False):
        cf = SS.get('item_deepconverterfunc', None)
        
        for obj in self:
            if obj is None:
                continue
            
            objID = id(obj)
            
            if objID in dMemo:
                continue
            
            if objID in dACC:
                return True
            
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
    
    >>> logger = utilities.makeDoctestLogger("Test1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...       item_renumberdirect = True,
    ...       item_subloggernamefunc = (lambda i: "glyph_%d" % (i,)))
    >>> Test1([10, 20, None]).isValid(logger=logger, editor=e)
    True
    
    >>> t1 = Test1([4, None, 500, -3, 2.75, 'Fred'])
    >>> t1.isValid(logger=logger, editor=e, fontGlyphCount=280)
    Test1.glyph_2 - ERROR - Glyph index 500 too large.
    Test1.glyph_3 - ERROR - The glyph index -3 cannot be used in an unsigned field.
    Test1.glyph_4 - ERROR - The glyph index 2.75 is not an integer.
    Test1.glyph_5 - ERROR - The glyph index 'Fred' is not a real number.
    False
    
    >>> logger = utilities.makeDoctestLogger("Test2")
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> t2 = Test2([None, t1])
    >>> t2.isValid(logger=logger, editor=e, fontGlyphCount=280)
    Test2.[1].glyph_2 - ERROR - Glyph index 500 too large.
    Test2.[1].glyph_3 - ERROR - The glyph index -3 cannot be used in an unsigned field.
    Test2.[1].glyph_4 - ERROR - The glyph index 2.75 is not an integer.
    Test2.[1].glyph_5 - ERROR - The glyph index 'Fred' is not a real number.
    False
    
    >>> logger = utilities.makeDoctestLogger("Test3")
    >>> class Test3(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_scaledirect': True}
    ...     attrSpec = {'x': {'attr_renumberdirect': True}}
    >>> Test3([2.1, -4, None, 18], x = 300).isValid(logger=logger, editor=e)
    True
    
    >>> Test3([12, 15, 'fred'], x = -5).isValid(logger=logger, editor=e)
    Test3.[2] - ERROR - The FUnit distance 'fred' is not a real number.
    Test3.x - ERROR - The glyph index -5 cannot be used in an unsigned field.
    False
    
    >>> logger = utilities.makeDoctestLogger("Test4")
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_fixedlength': 3}
    >>> v = Test4([1, 2, 3])
    >>> v.isValid(logger=logger, editor=e)
    True
    >>> del v[0]
    >>> v.isValid(logger=logger, editor=e)
    Test4 - ERROR - Length should be 3, but is 2.
    False
    
    >>> logger = utilities.makeDoctestLogger("Test5+6")
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    >>> class Test6(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test5([x])),
    ...         item_followsprotocol = True)
    >>> Test6([5.5, None, Test5([14, 'x'])]).isValid(logger=logger, editor=e)
    Test5+6.[0].[0] - ERROR - The glyph index 5.5 is not an integer.
    Test5+6.[2].[1] - ERROR - The glyph index 'x' is not a real number.
    False
    
    >>> logger = utilities.makeDoctestLogger("Test7")
    >>> def _seqVF(v, **kwArgs):
    ...     logger=kwArgs['logger']
    ...     if len(v) < 5:
    ...         logger.error(('Vxxxx', (), "Test7 objs must have len >= 5."))
    ...         return False
    ...     if v[4] % 15:
    ...         logger.error((
    ...           'Vxxxx',
    ...           (),
    ...           "Sequence [4] element must be a multiple of 15."))
    ...         return False
    ...     return True
    >>> class Test7(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True,
    ...         seq_validatefunc_partial = _seqVF)
    >>> Test7([4, 5, 112, 34, 45, 56]).isValid(
    ...   logger=logger,
    ...   fontGlyphCount=600,
    ...   editor=e)
    True
    
    >>> Test7([4, 5]).isValid(logger=logger, fontGlyphCount=600, editor=e)
    Test7 - ERROR - Test7 objs must have len >= 5.
    False
    
    >>> Test7([4, 5, 112, 34, 44, 56, 'x']).isValid(
    ...   logger=logger,
    ...   fontGlyphCount=100,
    ...   editor=e)
    Test7 - ERROR - Sequence [4] element must be a multiple of 15.
    Test7.[2] - ERROR - Glyph index 112 too large.
    Test7.[6] - ERROR - The glyph index 'x' is not a real number.
    False
    
    >>> class Test8(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_prevalidatedglyphset = {65535},
    ...         item_renumberdirect = True)
    >>> e = utilities.fakeEditor(2000)
    >>> Test8([1500, 3000, 65535]).isValid(logger=logger, editor=e)
    Test7.[1] - ERROR - Glyph index 3000 too large.
    False
    
    >>> class Test9(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumbernamesdirect = True)
    >>> logger = utilities.makeDoctestLogger("isvalid_Test9")
    >>> e = _fakeEditor()
    >>> obj = Test9([303, 304])
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj.append(500)
    >>> obj.isValid(logger=logger, editor=e)
    isvalid_Test9.[2] - ERROR - Name table index 500 not present in 'name' table.
    False
    
    >>> class Test10(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_enablecyclechecktag = 'Test10',
    ...         item_followsprotocol = True)
    >>> obj = Test10([None, Test10([None, Test10([None, None])]), None])
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj[1][1][1] = obj  # introduces circularity
    >>> obj.isValid(logger=logger, editor=e)
    isvalid_Test9.[1].[1].[1].[1] - ERROR - Circular object reference for index 1
    False
    """
    
    SS = self._SEQSPEC
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
    
    fixedLen = SS.get('seq_fixedlength', None)
    wholeFunc = SS.get('seq_validatefunc', None)
    indivFunc = SS.get('item_validatefunc', None)
    wholeFuncPartial = SS.get('seq_validatefunc_partial', None)
    indivFuncPartial = SS.get('item_validatefunc_partial', None)
    deep = SS.get('item_validatedeep', SS.get('item_followsprotocol', False))
    keySLNFunc = SS.get('item_subloggernamefunc', None)
    keySLNFuncNeedsSelf = SS.get('item_subloggernamefuncneedsobj', False)
    kwArgsFunc = SS.get('item_validatekwargsfunc', None)
    pvs = SS.get('item_prevalidatedglyphset', set())
    eccTag = SS.get('item_enablecyclechecktag', None)
    
    if wholeFunc is not None:
        r = wholeFunc(self, logger=logger, **kwArgs)
    
    else:
        if wholeFuncPartial is not None:
            r = wholeFuncPartial(self, logger=logger, **kwArgs)
        
        if (
          (fixedLen is not None) and
          (fixedLen is not True) and
          (len(self) != fixedLen)):
            
            logger.error((
              SS.get('item_validatecode_badfixedlength', 'G0012'),
              (fixedLen, len(self)),
              "Length should be %d, but is %d."))
            
            r = False
        
        if indivFunc is not None:
            # Note that unlike other methods, we pass None to the indivFunc,
            # since it needs to be able to say "No, None is not valid".
            
            for i, obj in enumerate(self):
                if kwArgsFunc is not None:
                    d = kwArgs.copy()
                    d.update(kwArgsFunc(self, i))
                else:
                    d = kwArgs
                
                if keySLNFunc is not None:
                    d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                    itemLogger = logger.getChild(keySLNFunc(i, **d2))
                
                else:
                    itemLogger = logger.getChild("[%d]" % (i,))
                
                r = indivFunc(obj, logger=itemLogger, **d) and r
        
        elif deep:
            cf = SS.get('item_deepconverterfunc', None)
            
            for i, obj in enumerate(self):
                if obj is None:
                    continue
                
                if kwArgsFunc is not None:
                    d = kwArgs.copy()
                    d.update(kwArgsFunc(self, i))
                else:
                    d = kwArgs
                
                if keySLNFunc is not None:
                    d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                    itemLogger = logger.getChild(keySLNFunc(i, **d2))
                
                else:
                    itemLogger = logger.getChild("[%d]" % (i,))
                
                if eccTag is not None:
                    dACC_copy = {x: y.copy() for x, y in dACC.items()}
                    eccDict = dACC_copy.setdefault(eccTag, {})
                    
                    if id(obj) not in eccDict:
                        eccDict[id(obj)] = obj
                    
                    else:
                        itemLogger.error((
                          'V0912',
                          (i,),
                          "Circular object reference for index %d"))
                        
                        return False  # aborts all other checks...
                    
                    d['activeCycleCheck'] = dACC_copy
                
                if hasattr(obj, 'isValid'):
                    r = obj.isValid(logger=itemLogger, **d) and r
                
                elif cf is not None:
                    cObj = cf(obj, **kwArgs)
                    r = cObj.isValid(logger=itemLogger, **d) and r
                
                else:
                    itemLogger.warning((
                      'G0023',
                      (),
                      "Object is not None and not deep, and no converter "
                      "function is provided."))
        
        else:
            if indivFuncPartial is not None:
                for i, obj in enumerate(self):
                    if keySLNFunc is not None:
                        d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                        itemLogger = logger.getChild(keySLNFunc(i, **d2))
                    
                    else:
                        itemLogger = logger.getChild("[%d]" % (i,))
                    
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
                
                for i, obj in enumerate(self):
                    if obj is None:
                        continue
                    
                    if keySLNFunc is not None:
                        d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                        itemLogger = logger.getChild(keySLNFunc(i, **d2))
                    
                    else:
                        itemLogger = logger.getChild("[%d]" % (i,))
                    
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
                
                for i, obj in enumerate(self):
                    if obj is None:
                        continue
                    
                    if keySLNFunc is not None:
                        d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                        itemLogger = logger.getChild(keySLNFunc(i, **d2))
                    
                    else:
                        itemLogger = logger.getChild("[%d]" % (i,))
                    
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
                
                for i, obj in enumerate(self):
                    if obj is not None:
                        if keySLNFunc is not None:
                            d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                            itemLogger = logger.getChild(keySLNFunc(i, **d2))
                        
                        else:
                            itemLogger = logger.getChild("[%d]" % (i,))
                        
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
                
                for i, obj in enumerate(self):
                    if obj is not None:
                        if keySLNFunc is not None:
                            d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                            itemLogger = logger.getChild(keySLNFunc(i, **d2))
                        
                        else:
                            itemLogger = logger.getChild("[%d]" % (i,))
                        
                        if not val16(obj, logger=itemLogger):
                            r = False
            
            elif SS.get('item_renumberstoragedirect', False):
                val16 = functools.partial(
                  valassist.isNumber_integer_unsigned,
                  numBits = 16,
                  label = "storage index")
                
                for i, obj in enumerate(self):
                    if obj is not None:
                        if keySLNFunc is not None:
                            d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                            itemLogger = logger.getChild(keySLNFunc(i, **d2))
                        
                        else:
                            itemLogger = logger.getChild("[%d]" % (i,))
                        
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
                
                for i, obj in enumerate(self):
                    if obj is not None:
                        if keySLNFunc is not None:
                            d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                            itemLogger = logger.getChild(keySLNFunc(i, **d2))
                        
                        else:
                            itemLogger = logger.getChild("[%d]" % (i,))
                        
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
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``replaceWhole``
        An optional Boolean, default False. If True, then in contexts where
        it's appropriate no merge will be attempted; the data in ``other`` will
        simply replace that of ``self`` in the merged object.
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> obj1 = Top([Bottom([1, 2, 3]), Bottom([4, 5, 6])])
    >>> obj2 = Top([Bottom([1, 4]), Bottom([6, 8])])
    >>> print(obj1.merged(obj2))
    [[1, 2, 3, 4], [4, 5, 6, 8]]
    >>> obj1 = Top([Bottom([1, 2, 3])])
    >>> print(obj1.merged(obj2))
    Traceback (most recent call last):
      ...
    IndexError: Merging <class '__main__.Top'> lists requires same lengths!
    >>> obj1 = Top([Bottom([1, 2, 3]), Bottom([4, 5, 6])])
    >>> print(obj1.merged(obj2, replaceWhole=True))
    [[1, 4], [6, 8]]
    
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someList': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([5, 2])
    >>> obj1 = LPA([], someNumber=4, someList=b1)
    >>> obj2 = LPA([], someNumber=4, someList=b2)
    >>> print(obj1.merged(obj2))
    [], someList = [1, 2, 3, 5], someNumber = 4
    
    >>> class TopT(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> t1 = TopT([Bottom([1, 2, 3]), Bottom([4, 5, 6])])
    >>> t2 = TopT([Bottom([1, 4]), Bottom([6, 8])])
    >>> print(t1.merged(t2))
    ([1, 2, 3, 4], [4, 5, 6, 8])
    
    >>> class Test(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_fixedlength': True, 'seq_mergeappend': True}
    >>> print(Test([1, 2]).merged(Test([1])))
    [1, 2]
    >>> print(Test([1, 2]).merged(Test([1, 3])))
    None
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)),
    ...         seq_mergeappend = True)
    >>> s1 = S("fred", [10, 25, 35])
    >>> s2 = S("fred", [35, 15, 25])
    >>> print(s1.merged(s2))
    [10, 25, 35, 15]
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict()
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True,
    ...         seq_mergeappend = True)
    
    >>> obj1 = Test3([5, Test2([4])])
    >>> obj2 = Test3([4, Test2([5])])
    
    Note the 5 is kept unchanged by the converter
    >>> print(obj1.merged(obj2))
    [5, [4]]
    
    Note here it's the reverse, based on arg order
    >>> print(obj2.merged(obj1))
    [4, [5]]
    """
    
    SS = self._SEQSPEC
    fixedLen = SS.get('seq_fixedlength', None)
    itemFunc = SS.get('item_mergefunc', None)
    cf = SS.get('item_deepconverterfunc', None)
    vNew = list(self)
    
    if kwArgs.get('replaceWhole', False):
        vNew = list(other)
    
    elif SS.get('seq_mergeappend', False):
        f = SS.get('item_asimmutablefunc', None)
        
        if f is not None:
            pool = set(f(obj) for obj in self if obj is not None)
            
            for obj in other:
                if obj is not None:
                    im = f(obj)
                    
                    if im not in pool:
                        pool.add(im)
                        vNew.append(obj)
        
        elif SS.get(
          'item_asimmutabledeep',
          SS.get('item_followsprotocol', False)):
            
            def _it():
                for obj in self:
                    if obj is not None:
                        try:
                            obj.asImmutable
                        
                        except AttributeError:
                            if cf is not None:
                                obj = cf(obj, **kwArgs)
                            else:
                                raise
                        
                        yield obj
            
            pool = set(obj.asImmutable(**kwArgs) for obj in _it())
            
            for obj in other:
                if obj is not None:
                    try:
                        obj.asImmutable
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                    
                    im = obj.asImmutable(**kwArgs)
                    
                    if im not in pool:
                        pool.add(im)
                        vNew.append(obj)
        
        else:
            pool = set(obj for obj in self if obj is not None)
            
            for obj in other:
                if obj is not None and obj not in pool:
                    pool.add(obj)
                    vNew.append(obj)
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    elif SS.get('item_mergedeep', SS.get('item_followsprotocol', False)):
        if len(self) != len(other):
            raise IndexError(
              "Merging %s lists requires same lengths!" %
              (type(self),))
        
        for i, selfObj in enumerate(self):
            otherObj = other[i]
            
            if selfObj is not None and otherObj is not None:
                try:
                    boundMethod = selfObj.merged
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(selfObj, **kwArgs).merged
                    else:
                        raise
                
                try:
                    otherObj.merged
                
                except AttributeError:
                    if cf is not None:
                        otherObj = cf(otherObj, **kwArgs)
                    else:
                        raise
                
                vNew[i] = boundMethod(otherObj, **kwArgs)
            
            elif selfObj is None:
                vNew[i] = otherObj
    
    elif itemFunc is not None:
        if len(self) != len(other):
            raise IndexError(
              "Merging %s lists requires same lengths!" %
              (type(self),))
        
        for i, selfObj in enumerate(self):
            otherObj = other[i]
            
            if selfObj is not None and otherObj is not None:
                changed, obj = itemFunc(selfObj, otherObj, **kwArgs)
                
                if changed:
                    vNew[i] = obj
            
            elif selfObj is None:
                vNew[i] = otherObj
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumbernamesdirect = True)
    >>> obj1 = Test1([303, None, 304])
    >>> e = _fakeEditor()
    >>> obj1.pprint(editor=e)
    0: 303 ('Required Ligatures On')
    1: None
    2: 304 ('Common Ligatures On')
    
    >>> obj1.namesRenumbered({303:306, 304:307}).pprint(editor=e)
    0: 306 ('Regular')
    1: None
    2: 307 ('Small Caps')
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True)
    ...     attrSpec = dict(
    ...         name1 = dict(
    ...             attr_renumbernamesdirect = True))
    >>> obj2 = Test2([obj1, None], name1=307)
    >>> obj2.pprint(editor=e)
    0:
      0: 303 ('Required Ligatures On')
      1: None
      2: 304 ('Common Ligatures On')
    1:
      (no data)
    name1: 307 ('Small Caps')
    
    >>> obj2.namesRenumbered({303:306, 304:307, 307: 355}).pprint(editor=e)
    0:
      0: 306 ('Regular')
      1: None
      2: 307 ('Small Caps')
    1:
      (no data)
    name1: 355
    """
    
    SS = self._SEQSPEC
    keepMissing = kwArgs.get('keepMissing', True)
    fixedLen = SS.get('seq_fixedlength', None)
    
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
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = list(self)
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
        return type(self)(vNew, **dNew)

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpcsdirect = True)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> t1 = Test1([5, 12, 50, 100])
    >>> print(t1.pcsRenumbered(mapData, infoString="testcode"))
    (5, 14, 53, 106)
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    ...     attrSpec = dict(x = dict(attr_renumberpcsdirect = True))
    >>> t2 = Test2([None, t1], x = 30)
    >>> print(t2.pcsRenumbered(mapData, infoString="testcode"))
    [None, (5, 14, 53, 106)], x = 32
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberpcsdirect = True,
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [5, 12, 50, 100])
    >>> print(s.pcsRenumbered(mapData, infoString="testcode"))
    [5, 14, 53, 106]
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpcsdirect = True)
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test3([x])),
    ...         item_followsprotocol = True)
    
    >>> md = {"test": ((5, 1), (15, 3), (30, 4))}
    >>> t = Test4([12, None, Test3([2, 20, 60])])
    >>> print(t.pcsRenumbered(md, infoString="test"))
    [[13], None, [2, 23, 64]]
    """
    
    SS = self._SEQSPEC
    
    if SS.get('item_renumberpcsdeep', SS.get('item_followsprotocol', False)):
        def _it():
            cf = SS.get('item_deepconverterfunc', None)
            
            for obj in self:
                if obj is not None:
                    try:
                        obj.pcsRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            obj = cf(obj, **kwArgs)
                        else:
                            raise
                
                yield obj
        
        vNew = [
          (None if obj is None else obj.pcsRenumbered(mapData, **kwArgs))
          for obj in _it()]
    
    elif SS.get('item_renumberpcsdirect', False):
        vNew = []
        
        for obj in self:
            if obj is not None:
                delta = 0
                it = mapData.get(kwArgs.get('infoString', None), [])
                
                for threshold, newDelta in it:
                    if obj < threshold:
                        break
                    
                    delta = newDelta
                
                vNew.append(obj + delta)
            
            else:
                vNew.append(None)
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = self
    
    # Now do attributes
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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

    >>> class Bottom_LIIGI(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_indexisglyphindex = True,
    ...         item_renumberpointsdirect = True)
    >>> myMapData = {2: {5: 6, 11: 12}, 4: {9: 25}}
    >>> b = Bottom_LIIGI([4, None, 11, 6, 9, 15, None])
    >>> print(b.pointsRenumbered(myMapData))
    [4, None, 12, 6, 25, 15, None]
    
    >>> class Bottom_Direct(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpointsdirect = True)
    >>> b = Bottom_Direct(iter(range(3, 13)))
    >>> print(b.pointsRenumbered(myMapData, glyphIndex=2))
    [3, 4, 6, 6, 7, 8, 9, 10, 12, 12]
    
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpointsdeep = True)
    >>> b1 = Bottom_LIIGI([4, None, 11, 6, 9, 15, None])
    >>> b2 = Bottom_Direct(iter(range(13)))
    >>> t = Top([b1, None, b2])
    
    In the following, glyphIndex only used by b2
    >>> print(t.pointsRenumbered(myMapData, glyphIndex=2))
    [[4, None, 12, 6, 25, 15, None], None, [0, 1, 2, 3, 4, 6, 6, 7, 8, 9, 10, 12, 12]]
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...       seq_indexispointindex = True,
    ...       item_strusesrepr = True)
    >>> t1 = Test1(['a', 'b', 'c', 'd'])
    >>> t1 = t1.pointsRenumbered({5: {0:1,1:2,2:3,3:0}}, glyphIndex=5)
    >>> print(t1)
    ['d', 'a', 'b', 'c']
    >>> t1 = t1.pointsRenumbered({5: {2:0,0:2}}, glyphIndex=5)
    >>> print(t1)
    ['b', 'a', 'd', 'c']
    >>> t2 = t1.pointsRenumbered(
    ...   {5: {2: 0,0: 2}},
    ...   glyphIndex = 5,
    ...   keepMissing = False)
    >>> print(t2)
    ['d', None, 'b', None]
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         pointNumber = dict(attr_renumberpointsdirect = True))
    ...     attrSorted = ('pointNumber',)
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         bottom = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    ...     attrSorted = ('bottom',)
    >>> b = Bottom([], pointNumber=10)
    >>> t = Top([], bottom=b)
    >>> print(t)
    [], bottom = ([], pointNumber = 10)
    >>> myMap = {5: {10: 20}, 20: {10: 11}}
    >>> t = t.pointsRenumbered(myMap, glyphIndex=5)
    >>> print(t)
    [], bottom = ([], pointNumber = 20)
    >>> print(t.pointsRenumbered(myMap, glyphIndex=49))
    [], bottom = ([], pointNumber = 20)
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberpointsdirect = True,
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [10, 14])
    >>> print(s.pointsRenumbered(myMap, glyphIndex=5))
    [20, 14]
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberpointsdirect = True)
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True)
    
    >>> md = {12: {4: 7, 5: 6, 6: 5, 7: 4}}
    >>> t = Test3([5, None, Test2([4, 6, 7])])
    >>> print(t.pointsRenumbered(md, glyphIndex=12))
    [[6], None, [7, 5, 4]]
    
    >>> class Test4(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberpointsdirect = True,
    ...         seq_indexmapstoglyphindexfunc = (
    ...           lambda obj, i, **k:
    ...           obj.firstGlyph + i))
    ...     attrSpec = dict(firstGlyph = dict(attr_renumberdirect = True))
    >>> obj = Test4([4, 5, 6], firstGlyph=30)
    >>> md = {31: {4: 7, 5: 19, 7: 4, 19: 5}}
    >>> print(obj.pointsRenumbered(md))
    (4, 19, 6), firstGlyph = 30
    """
    
    SS = self._SEQSPEC
    origMapFunc = SS.get('seq_indexmapstoglyphindexfunc', None)
    
    setIndex = (
      (origMapFunc is not None) or
      SS.get('seq_indexisglyphindex', False))
    
    if origMapFunc is not None:
        indexMapFunc = lambda i: origMapFunc(self, i, **kwArgs)
    else:
        indexMapFunc = lambda i: i
    
    deep = SS.get(
      'item_renumberpointsdeep',
      SS.get('item_followsprotocol', False))
    
    cf = SS.get('item_deepconverterfunc', None)
    vNew = list(self)
    
    if SS.get('seq_indexispointindex', False):
        # list index is point index; list entries may be deep
        if deep:
            for i, obj in enumerate(self):
                if obj is not None:
                    try:
                        boundMethod = obj.pointsRenumbered
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).pointsRenumbered
                        else:
                            raise
                        
                    vNew[i] = boundMethod(mapData, **kwArgs)
        
        # now reorder the list
        thisMap = mapData.get(kwArgs.get('glyphIndex', None), {})
        keepMissing = kwArgs.get('keepMissing', True)
        work = (list(vNew) if keepMissing else [None] * len(self))
        
        for i, obj in enumerate(vNew):
            j = thisMap.get(i, None)
            
            if j is not None:
                work[j] = obj
        
        vNew = work
    
    elif deep:
        for i, obj in enumerate(self):
            if obj is not None:
                if setIndex:
                    kwArgs['glyphIndex'] = indexMapFunc(i)
                
                try:
                    boundMethod = obj.pointsRenumbered
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).pointsRenumbered
                    else:
                        raise
                
                vNew[i] = boundMethod(mapData, **kwArgs)
    
    elif SS.get('item_renumberpointsdirect', False):
        if setIndex:
            # list index is glyph index, list entry is point
            for i, obj in enumerate(self):
                newPoint = mapData.get(indexMapFunc(i), {}).get(obj, None)
                
                if newPoint is not None:
                    vNew[i] = newPoint
        
        else:
            # glyph index is in kwArgs
            thisMap = mapData.get(kwArgs.get('glyphIndex', None), {})
            
            for i, obj in enumerate(self):
                newPoint = thisMap.get(obj, None)
                
                if newPoint is not None:
                    vNew[i] = newPoint
            
            if SS.get('seq_keepsorted', False):
                vNew.sort()
    
    # Now do attributes
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'seq_indexisglyphindex': True,
    ...       'item_renumberdirect': True,
    ...       'item_usenamerforstr': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_followsprotocol': True,
    ...       'item_pprintlabelfunc': (
    ...         lambda x:
    ...         "Sublist number %d" % (x + 1,))}
    >>> b1 = Bottom([1, 2, 3])
    >>> nm = namer.testingNamer()
    >>> b1.pprint(label="This is b1")
    This is b1:
      0: 1
      1: 2
      2: 3
    >>> b1.pprint(label="This is b1", namer=nm)
    This is b1:
      xyz1: xyz2
      xyz2: xyz3
      xyz3: xyz4
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2, b1])
    >>> t.pprint(label="This is t")
    This is t:
      Sublist number 1:
        0: 1
        1: 2
        2: 3
      Sublist number 2:
        0: 4
        1: 5
        2: 6
      Sublist number 3:
        0: 1
        1: 2
        2: 3
    >>> t.pprint(label="This is t", namer=nm)
    This is t:
      Sublist number 1:
        xyz1: xyz2
        xyz2: xyz3
        xyz3: xyz4
      Sublist number 2:
        xyz1: xyz5
        xyz2: xyz6
        xyz3: xyz7
      Sublist number 3:
        xyz1: xyz2
        xyz2: xyz3
        xyz3: xyz4
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_pprintfunc=pp.PP.sequence_grouped)
    >>> t = Test1([3, 3, 3, 3, 5, None, None, None, 2, 2, -5])
    >>> t.pprint(label="Grouped")
    Grouped:
      [0-3]: 3
      [4]: 5
      [5-7]: (no data)
      [8-9]: 2
      [10]: -5
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_pprintlabelfunc = (
    ...           lambda i, obj:
    ...           "Item #%d is a %s" % (i + 1, type(obj))),
    ...         item_pprintlabelfuncneedsobj = True)
    >>> Test2([4, "Hi", [1, 2, 3]]).pprint(label="Using object to make label")
    Using object to make label:
      Item #1 is a <class 'int'>: 4
      Item #2 is a <class 'str'>: Hi
      Item #3 is a <class 'list'>: [1, 2, 3]
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_followsprotocol': True,
    ...       'item_pprintlabelfunc': (
    ...         lambda x:
    ...         "Sublist number %d" % (x + 1,))}
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_pprintfunc': pp.PP.sequence}
    ...     attrSpec = {
    ...       'someNumber': {
    ...         'attr_initfunc': (lambda: 15),
    ...         'attr_label': "Count"},
    ...       'someList': {
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> b3 = Bottom([1, 2, 3])
    >>> t = Top([b1, b2, b3])
    >>> obj = LPA([3, 4, 6], someList=t, someNumber=5)
    >>> obj.pprint(label="Here are the data")
    Here are the data:
      3
      4
      6
      Extra data:
        Sublist number 1:
          0: 1
          1: 2
          2: 3
        Sublist number 2:
          0: 4
          1: 5
          2: 6
        Sublist number 3:
          0: 1
          1: 2
          2: 3
      Count: 5
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    ...   attrSorted = ('s',)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    ...   attrSorted = ('s',)
    >>> Test1([1, 2]).pprint()
    0: 1
    1: 2
    s: fred
    >>> Test2([1, 2]).pprint()
    0: 1
    1: 2
    s: 'fred'
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    ...     attrSorted = ('x', 'y')
    >>> Test3([]).pprint(label="Note x is suppressed")
    Note x is suppressed:
      y: 5
    >>> Test3([], x=4).pprint(label="No suppression here")
    No suppression here:
      x: 4
      y: 5
    
    Note the sequence in the following does not have item_usenamerforstr
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_renumberdirect = True,
    ...             attr_usenamerforstr = True),
    ...         y = dict(attr_renumberdirect = True))
    >>> t4 = Test4([4, 9], x=35, y=45)
    >>> t4.pprint()
    0: 4
    1: 9
    x: 35
    y: 45
    >>> t4.pprint(namer=namer.testingNamer())
    0: 4
    1: 9
    x: xyz36
    y: 45
    
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_ppoptions = dict(noDataString = "nuffin"))
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(attr_ppoptions = {'noDataString': "bubkes"}))
    
    Note that attributes don't inherit the ppoptions from the sequence!
    >>> Test5([3, None, -5, None]).pprint()
    0: 3
    1: nuffin
    2: -5
    3: nuffin
    a: (no data)
    b: bubkes
    
    >>> class Test6(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_pprintlabelfunc = (lambda i: "Position %d" % (i,)),
    ...         item_strusesrepr = True)
    >>> class Test7(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test6([x])),
    ...         item_followsprotocol = True)
    
    >>> Test7(['a', None, Test6(['b', 'c'])]).pprint()
    0:
      Position 0: 'a'
    1:
      (no data)
    2:
      Position 0: 'b'
      Position 1: 'c'
    
    >>> class Test8(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_usenamerforstr = True,
    ...         seq_indexmapstoglyphindexfunc = (
    ...           lambda obj, i, **k:
    ...           obj.firstGlyph + i))
    ...     attrSpec = dict(firstGlyph = dict())
    ...     attrSorted = ()
    >>> t = Test8(['a', 'b', 'c'], firstGlyph=30)
    >>> t.pprint(namer=namer.testingNamer())
    xyz31: a
    xyz32: b
    xyz33: c
    
    >>> class Test9(tuple, metaclass=FontDataMetaclass):
    ...     attrSpec = dict()
    >>> class Test10(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True)
    >>> obj9 = Test9([14, 'Hi there', (4, 2)])
    >>> obj10 = Test10([obj9, obj9, obj9, None, obj9])
    >>> obj10.pprint()
    0:
      0: 14
      1: Hi there
      2: (4, 2)
    1:
      0: 14
      1: Hi there
      2: (4, 2)
    2:
      0: 14
      1: Hi there
      2: (4, 2)
    3:
      (no data)
    4:
      0: 14
      1: Hi there
      2: (4, 2)
    
    >>> obj10.pprint(elideDuplicates=True)
    OBJECT 0
    0:
      0: 14
      1: Hi there
      2: (4, 2)
    1: (duplicate; see OBJECT 0 above)
    2: (duplicate; see OBJECT 0 above)
    3:
      (no data)
    4: (duplicate; see OBJECT 0 above)
    """
    
    SS = self._SEQSPEC
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    pd = p.__dict__
    ppSaveDict = {}
    
    for key, value in SS.get('seq_ppoptions', {}).items():
        ppSaveDict[key] = pd[key]
        pd[key] = value
    
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if elideDups is True:
        elideDups = {}  # object ID to serial number
        kwArgs['elideDuplicates'] = elideDups
    
    deep = SS.get('item_pprintdeep', SS.get('item_followsprotocol', False))
    printWholeFunc = SS.get('seq_pprintfunc', None)
    printFunc = SS.get('item_pprintfunc', None)
    labelFunc = SS.get('item_pprintlabelfunc', str)
    lfNeedsObj = SS.get('item_pprintlabelfuncneedsobj', False)
    cf = SS.get('item_deepconverterfunc', None)
    assert (not lfNeedsObj) or (labelFunc is not str)
    kwArgs['useRepr'] = SS.get('item_strusesrepr', False)
    
    if SS.get('item_usenamerforstr', False):
        nm = kwArgs.get('namer', self.getNamer())
    else:
        nm = None
    
    if printWholeFunc:
        printWholeFunc(p, self, **kwArgs)
    
    elif printFunc:
        if lfNeedsObj:
            for i, obj in enumerate(self):
                printFunc(p, obj, label=labelFunc(i, obj=obj))
        else:
            for i, obj in enumerate(self):
                printFunc(p, obj, label=labelFunc(i))
    
    else:
        nmbf = (None if nm is None else nm.bestNameForGlyphIndex)
        mapFunc = SS.get('seq_indexmapstoglyphindexfunc', None)
        
        if (mapFunc is not None):
            if (nm is not None) and (labelFunc is str):
                f = (lambda i, **k: nmbf(mapFunc(self, i, **k), **k))
            else:
                f = (lambda i, **k: str(mapFunc(self, i, **k)))
        
        elif (
          SS.get('seq_indexisglyphindex', False) and
          (nm is not None) and
          (labelFunc is str)):
            
            f = nmbf
        
        else:
            f = labelFunc
        
        if deep:
            for key, value in enumerate(self):
                if value is not None:
                    try:
                        value.pprint
                    
                    except AttributeError:
                        if cf is not None:
                            value = cf(value, **kwArgs)  # yes, kwArgs
                        else:
                            raise
                
                if elideDups is not False:
                    objID = id(value)
                    
                    if objID in elideDups:
                        p.simple(
                          "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                          label = (f(key, obj=value) if lfNeedsObj else f(key)),
                          **kwArgs)
                        
                        continue
                    
                    elif value is not None:
                        elideDups[objID] = len(elideDups)
                        p("OBJECT %d" % (elideDups[objID],))
                        
                        # ...and fall through to do the actual printing below
                
                if lfNeedsObj:
                    p.deep(value, label=f(key, obj=value), **kwArgs)
                else:
                    p.deep(value, label=f(key), **kwArgs)
        
        else:
            if SS.get('item_renumberdirect', False) and (nm is not None):
                if lfNeedsObj:
                    for key, value in enumerate(self):
                        p.simple(
                          nmbf(value),
                          label=f(key, obj=value),
                          **kwArgs)
                
                else:
                    for key, value in enumerate(self):
                        p.simple(nmbf(value), label=f(key), **kwArgs)
            
            elif SS.get('item_renumbernamesdirect', False):
                if lfNeedsObj:
                    for key, value in enumerate(self):
                        p.simple(
                          utilities.nameFromKwArgs(value, **kwArgs),
                          label = f(key, obj=value),
                          **kwArgs)
                
                else:
                    for key, value in enumerate(self):
                        p.simple(
                          utilities.nameFromKwArgs(value, **kwArgs),
                          label = f(key),
                          **kwArgs)
            
            else:
                if lfNeedsObj:
                    for key, value in enumerate(self):
                        p.simple(value, label=f(key, obj=value), **kwArgs)
                else:
                    for key, value in enumerate(self):
                        p.simple(value, label=f(key), **kwArgs)
    
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
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> b3 = Bottom([1, 2, 3])
    >>> t = Top([b1, b2, b3])
    >>> t2 = t.__deepcopy__()
    >>> t2.append(b1)
    >>> t2[1][1] += 22
    >>> t2.pprint_changes(t, label="From t to t2")
    From t to t2:
      Appended at end:
        0: 1
        1: 2
        2: 3
      This sequence at new index 1:
        0: 4
        1: 27
        2: 6
      replaced this sequence at old index 1:
        0: 4
        1: 5
        2: 6
    
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_followsprotocol = True,
    ...         seq_pprintdifffunc = pp.PP.diff_sequence_deep)
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_pprintfunc': pp.PP.sequence}
    ...     attrSpec = {
    ...       'someNumber': {
    ...         'attr_initfunc': (lambda: 15),
    ...         'attr_label': "Count"},
    ...       'someList': {
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t1 = Top([b1, b2])
    >>> obj1 = LPA([3, 4, 6], someList=t1, someNumber=5)
    >>> t2 = t1.__deepcopy__()
    >>> t2[1][1] -= 11
    >>> obj2 = LPA([3, 5, 6], someList=t2, someNumber=12)
    >>> obj2.pprint_changes(obj1, label="Here are the changes")
    Here are the changes:
      This sequence at new index 1:
        5
      replaced this sequence at old index 1:
        4
      Extra data:
        This sequence at new index 1:
          0: 4
          1: -6
          2: 6
        replaced this sequence at old index 1:
          0: 4
          1: 5
          2: 6
      Count changed from 5 to 12
    
    >>> class Test(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    ...     attrSorted = ('x', 'y', 'z')
    >>> Test([], x=1, y=2, z=3).pprint_changes(Test([], x=1, y=2, z=2000))
    
    >>> class Test2(list, metaclass=FontDataMetaclass): pass
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True)
    
    >>> curr = Test3([5, None, Test2([1, 2])])
    >>> prev = Test3([4, None, Test2([1, 4])])
    >>> curr.pprint_changes(prev)
    This sequence at new index 0:
      0: 5
    replaced this sequence at old index 0:
      0: 4
    This sequence at new index 2:
      0: 1
      1: 2
    replaced this sequence at old index 2:
      0: 1
      1: 4
    """
    
    if self == prior:
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    SS = self._SEQSPEC
    ppdFunc = SS.get('seq_pprintdifffunc', None)
    
    deep = SS.get(
      'item_pprintdiffdeep',
      SS.get('item_followsprotocol', False))
    
    useRepr = SS.get('item_strusesrepr', False)
    cf = SS.get('item_deepconverterfunc', None)
    nm = kwArgs.get('namer', self.getNamer())
    
    # If we're deep and there's a converter func, check both sequences
    if deep and (cf is not None):
        v = self.__copy__()
        
        for i, obj in enumerate(self):
            if obj is not None:
                try:
                    obj.pprint_changes
                except AttributeError:
                    v[i] = cf(obj, **kwArgs)
        
        self = v
        v = prior.__copy__()
        
        for i, obj in enumerate(prior):
            if obj is not None:
                try:
                    obj.pprint_changes
                except AttributeError:
                    v[i] = cf(obj, **kwArgs)
        
        prior = v
    
    if ppdFunc is None:
        if deep:
            ppdFunc = pp.PP.diff_sequence_deep
        else:
            ppdFunc = pp.PP.diff_sequence
    
    f = SS.get('item_asimmutablefunc', None)
    
    if f is not None:
        ppdFunc(p, self, prior, decorator=f, useRepr=useRepr)
    
    elif SS.get(
      'item_asimmutabledeep',
      SS.get('item_followsprotocol', False)):
        
        ai = (
          lambda obj:
          (None if obj is None else obj.asImmutable(**kwArgs)))
        
        ppdFunc(p, self, prior, decorator=ai, useRepr=useRepr)
    
    else:
        ppdFunc(p, self, prior, useRepr=useRepr)
    
    # Now do attributes
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
    
    >>> def wholeInPlaceFunc(oldList, **kwArgs):
    ...     cmpCopy = list(oldList)
    ...     if len(oldList) > 1:
    ...         oldList[:] = [oldList[1]]
    ...     else:
    ...         oldList[:] = []
    ...     return (list(oldList) != cmpCopy, oldList)
    >>> def wholeReplaceFunc(oldList, **kwArgs):
    ...     r = ([] if len(oldList) < 2 else [oldList[1]])
    ...     return (r != list(oldList), r)
    >>> def indivInPlaceFunc(obj, **kwArgs):
    ...     obj[0] *= 2
    ...     return (bool(obj[0]), obj)
    >>> def indivReplaceFunc(obj, **kwArgs):
    ...     return (bool(obj), [obj[0] * 2] + obj[1:])
    >>> class Bottom_WholeInPlace(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_recalculatefunc = wholeInPlaceFunc)
    >>> class Bottom_WholeReplace(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_recalculatefunc = wholeReplaceFunc)
    >>> class Bottom_IndivInPlace(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_recalculatefunc = indivInPlaceFunc)
    >>> class Bottom_IndivReplace(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_recalculatefunc = indivReplaceFunc)
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> b1 = Bottom_WholeInPlace([2, 3, 4])
    >>> b2 = Bottom_WholeReplace([2, 3, 4])
    >>> b3 = Bottom_IndivInPlace([[4], [6], [0]])
    >>> b4 = Bottom_IndivReplace([[4], [6], [0]])
    >>> t = Top([b1, b2, b3, b4])
    >>> print(t)
    [[2, 3, 4], [2, 3, 4], [[4], [6], [0]], [[4], [6], [0]]]
    >>> print(t.recalculated())
    [[3], [3], [[8], [12], [0]], [[8], [12], [0]]]
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = (lambda x, **k: (x != 0, x * 1.5)))
    ...     attrSpec = dict(
    ...         x = dict(attr_recalculatefunc = (
    ...             lambda x, **k:
    ...             (True, 2 * x - k['adj']))))
    >>> t = Test([3, 4], x=9)
    >>> print(t)
    (3, 4), x = 9
    >>> print(t.recalculated(adj=4))
    (4.5, 6.0), x = 14
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = (lambda x: (x != 0, 2 * x)),
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [10, 14])
    >>> print(s.recalculated())
    [20, 28]
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = (
    ...             lambda x,**k:
    ...             (bool(x % 14 == 0), (x + 12 if x % 14 == 0 else x))))
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test2([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test3([28, None, Test2([14, 15])]).recalculated())
    [[40], None, [26, 15]]
    
    >>> def _t4W(v, **kwArgs):
    ...     v2 = sorted(v)
    ...     return list(v) != v2, v2
    >>> def _t4I(obj, **kwArgs):
    ...     return obj != round(obj), round(obj)
    
    >>> class Test4_W(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_recalculatefunc_partial = _t4W)
    >>> v = [1.5, 4, -5.75, -3, 13, 0]
    >>> Test4_W(v).recalculated()
    Test4_W((-5.75, -3, 0, 1.5, 4, 13))
    
    >>> class Test4_I(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = _t4I)
    >>> Test4_I(v).recalculated()
    Test4_I((2, 4, -6, -3, 13, 0))
    
    >>> class Test4_Both(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_recalculatefunc = _t4I,
    ...         seq_recalculatefunc_partial = _t4W)
    >>> Test4_Both(v).recalculated()
    Test4_Both((-6, -3, 0, 2, 4, 13))
    """
    SS = self._SEQSPEC
    fWhole = SS.get('seq_recalculatefunc', None)
    fWholePartial = SS.get('seq_recalculatefunc_partial', None)
    fIndiv = SS.get('item_recalculatefunc', None)
    vNew = list(self)
    
    if fWhole is not None:
        changed, vNew = fWhole(self, **kwArgs)
    
    else:
        if fWholePartial is not None:
            changed, vNew = fWholePartial(self, **kwArgs)
        
        if fIndiv is not None:
            for i, obj in enumerate(vNew):
                if obj is not None:
                    changed, vNew[i] = fIndiv(obj, **kwArgs)
        
        elif SS.get(
          'item_recalculatedeep',
          SS.get('item_followsprotocol', False)):
            
            cf = SS.get('item_deepconverterfunc', None)
            
            for i, obj in enumerate(vNew):
                if obj is not None:
                    try:
                        boundMethod = obj.recalculated
                    
                    except AttributeError:
                        if cf is not None:
                            boundMethod = cf(obj, **kwArgs).recalculated
                        else:
                            raise
                    
                    vNew[i] = boundMethod(**kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_scaledirect': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> t = Top([Bottom([2, 4, 6]), None, Bottom([25])])
    >>> print(t)
    [[2, 4, 6], None, [25]]
    >>> print(t.scaled(1.5))
    [[3, 6, 9], None, [38]]
    
    >>> class Top(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_scaledirect': True}
    ...     attrSpec = {'v': {'attr_followsprotocol': True}}
    ...     attrSorted = ('v',)
    >>> t = Top([-10], v=Bottom([2, 4, 6]))
    >>> print(t)
    (-10,), v = [2, 4, 6]
    >>> print(t.scaled(1.5))
    (-15,), v = [3, 6, 9]
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_scaledirect': True}
    ...     attrSpec = {'x': {'attr_scaledirect': True}}
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_scaledirectnoround': True}
    ...     attrSpec = {'x': {'attr_scaledirectnoround': True}}
    >>> print(Test1([10.0, 11.0, 12.0], x=13.0).scaled(0.25))
    (3.0, 3.0, 3.0), x = 3.0
    >>> print(Test2([10.0, 11.0, 12.0], x=13.0).scaled(0.25))
    (2.5, 2.75, 3.0), x = 3.25
    
    >>> class WeirdList(list):
    ...     def __init__(self, name, *args):
    ...         super(WeirdList, self).__init__(*args)
    ...         self.name = name
    >>> class S(WeirdList, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_scaledirectnoround = True,
    ...         seq_makefunc = (lambda v,*a,**k: type(v)(v.name, *a)))
    >>> s = S("fred", [10.0, 14.0])
    >>> print(s.scaled(1.5))
    [15.0, 21.0]
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_scaledirectnoround = True)
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test3([x])),
    ...         item_followsprotocol = True)
    
    >>> print(Test4([3.0, None, Test3([1.0, 2.0])]).scaled(1.5))
    [[4.5], None, [1.5, 3.0]]
    
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_scaledirect = True,
    ...         item_representsx = True)
    ...     attrSpec = dict(
    ...         x = dict(attr_scaledirect = True, attr_representsx = True),
    ...         y = dict(attr_scaledirect = True, attr_representsy = True),
    ...         z = dict(attr_scaledirect = True))
    
    >>> obj = Test5([2.0, 3.0, None], x=2.0, y=2.0, z=2.0)
    >>> print(obj.scaled(5.0))
    [10.0, 15.0, None], x = 10.0, y = 10.0, z = 10.0
    >>> print(obj.scaled(5.0, scaleOnlyInX=True))
    [10.0, 15.0, None], x = 10.0, y = 2.0, z = 10.0
    >>> print(obj.scaled(5.0, scaleOnlyInY=True))
    [2.0, 3.0, None], x = 2.0, y = 10.0, z = 10.0
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    SS = self._SEQSPEC
    vNew = list(self)
    
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    if SS.get('item_representsx', False) and scaleOnlyInY:
        pass
    
    elif SS.get('item_representsy', False) and scaleOnlyInX:
        pass
    
    elif SS.get('item_scaledeep', SS.get('item_followsprotocol', False)):
        cf = SS.get('item_deepconverterfunc', None)
        
        for i, obj in enumerate(self):
            if obj is not None:
                try:
                    boundMethod = obj.scaled
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).scaled
                    else:
                        raise
                
                vNew[i] = boundMethod(scaleFactor, **kwArgs)
    
    elif SS.get('item_scaledirect', False):
        roundFunc = SS.get('item_roundfunc', None)
        
        if roundFunc is None:
            if SS.get('item_python3rounding', False):
                roundFunc = utilities.newRound
            else:
                roundFunc = utilities.oldRound
        
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = roundFunc(scaleFactor * obj, castType=type(obj))
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    elif SS.get('item_scaledirectnoround', False):
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = scaleFactor * obj
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    # Now do attributes
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberstoragedirect = True)
    
    >>> print(Test1([15, 80, None, 29]).storageRenumbered(storageDelta=1000))
    (1015, 1080, None, 1029)
    
    >>> d = {25: 1025, 26: 1000, 27: 1001}
    >>> obj = Test1([25, 27, None, 26, 30])
    >>> print(obj.storageRenumbered(oldToNew=d))
    (1025, 1001, None, 1000, 30)
    >>> print(obj.storageRenumbered(oldToNew=d, keepMissing=False))
    (1025, 1001, None, 1000, None)
    
    >>> f = lambda x,**k: (x if x % 2 else x + 900)  # evens move up by 900
    >>> print(Test1([10, 15, None]).storageRenumbered(storageMappingFunc=f))
    (910, 15, None)
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> v = Test2([Test1([15, None, 20]), None, Test1([20, 90])])
    >>> print(v.storageRenumbered(storageDelta=-3))
    [(12, None, 17), None, (17, 87)]
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True,
    ...         seq_indexisstorageindex = True)
    >>> obj = Test3(['a', 'b', 'c', 'd'])
    >>> print(obj.storageRenumbered(storageDelta=4))
    ['a', 'b', 'c', 'd', 'a', 'b', 'c', 'd']
    >>> print(obj.storageRenumbered(storageDelta=4, keepMissing=False))
    [None, None, None, None, 'a', 'b', 'c', 'd']
    >>> print(obj.storageRenumbered(oldToNew={0:2, 2:0}))
    ['c', 'b', 'a', 'd']
    >>> print(obj.storageRenumbered(oldToNew={0:2, 2:0}, keepMissing=False))
    ['c', None, 'a', None]
    """
    
    SS = self._SEQSPEC
    storageMappingFunc = kwArgs.get('storageMappingFunc', None)
    oldToNew = kwArgs.get('oldToNew', None)
    keepMissing = kwArgs.get('keepMissing', True)
    storageDelta = kwArgs.get('storageDelta', None)
    fixedLen = SS.get('seq_fixedlength', None)
    
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
        
        vNew = [None] * len(self)
        
        for i, obj in enumerate(_it()):
            if obj is not None:
                vNew[i] = obj.storageRenumbered(**kwArgs)
    
    elif SS.get('item_renumberstoragedirect', False):
        vNew = [None] * len(self)
        
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = storageMappingFunc(obj, **kwArgs)
        
        if SS.get('seq_keepsorted', False):
            vNew.sort()
    
    else:
        vNew = list(self)
    
    if vNew and SS.get('seq_indexisstorageindex', False):
        saved = list(vNew)
        
        newIndices = {
          i: storageMappingFunc(i, **kwArgs)
          for i in range(len(self))}
        
        revIndices = {n: i for i, n in newIndices.items() if n is not None}
        count = max(len(saved), 1 + utilities.safeMax(revIndices))
        vNew = [None] * count
        
        for new in range(count):
            if new in revIndices:
                vNew[new] = saved[revIndices[new]]
            elif keepMissing:
                vNew[new] = saved[new]
            else:
                vNew[new] = None
    
    # If the length is fixed but items were removed, we are no longer valid
    if (len(vNew) != len(self)) and (fixedLen is True or fixedLen is not None):
        return None
    
    # Now do attributes
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
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
    
    >>> matrix = _getMatrixModule()
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_representsxyalternating = True)
    >>> print(Test1([1, 2, 3, 4]).transformed(m))
    (-6, 8, -12, 12)
    >>> print(Test1([3, 4, 5]).transformed(m))
    Traceback (most recent call last):
      ...
    ValueError: Sequence with item_representsxyalternating cannot have odd length!
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_representsx = True)
    >>> print(Test2([1, 2, 3, None]).transformed(m))
    [-6, -9, -12, None]
    
    >>> class Test3(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_followsprotocol = True)
    >>> obj = Test3([Test1([1, 2, 3, 4]), None, Test1([-3, -4])])
    >>> print(obj.transformed(m))
    ((-6, 8, -12, 12), None, (6, -4))
    
    >>> class Test4(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_representsxyalternating = True,
    ...         item_roundfunc = utilities.truncateRound)
    >>> m = matrix.Matrix.forScale(1.75, -0.25)
    >>> print(Test4([1, -2, -3, 4, 5, -6, -7, 8]).transformed(m))
    (1, 0, -6, -1, 8, 1, -13, -2)
    """
    
    SS = self._SEQSPEC
    vNew = list(self)
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
        cf = SS.get('item_deepconverterfunc', None)
        
        for i, obj in enumerate(self):
            if obj is not None:
                try:
                    boundMethod = obj.transformed
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj, **kwArgs).transformed
                    else:
                        raise
                
                vNew[i] = boundMethod(matrixObj, **kwArgs)
    
    elif SS.get('item_representsxyalternating', False):
        if len(self) % 2:
            raise ValueError(
              "Sequence with item_representsxyalternating cannot "
              "have odd length!")
        
        i = 0
        
        while i < len(self):
            x, y = mp(self[i:i+2])
            vNew[i] = roundFunc(x, castType=type(self[i]))
            vNew[i+1] = roundFunc(y, castType=type(self[i+1]))
            i += 2
    
    elif SS.get('item_representsx', False):
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = roundFunc(mp((obj, 0))[0], castType=type(obj))
    
    elif SS.get('item_representsy', False):
        for i, obj in enumerate(self):
            if obj is not None:
                vNew[i] = roundFunc(mp((0, obj))[1], castType=type(obj))
    
    # Now do attributes
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
        return type(self)(vNew, **dNew)

def SM_bool(self):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if the sequence is nonzero length, or if it is zero length 
        but one or more attributes have significant nonzero values (and by
        significant I mean values that are not selectively ignored based on the
        ``attr_ignoreforcomparisons`` and ``attr_ignoreforbool`` flags); False
        otherwise
    :rtype: bool
    
    A sequence of length greater than zero might return False if the class was
    defined with the ``seq_falseifcontentsfalse`` flag.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforbool = True),
    ...         notIgnored = dict())
    >>> print(bool(Test1([1, 2, 3], ignored=0, notIgnored=0)))
    True
    >>> print(bool(Test1([], ignored=0, notIgnored=0)))
    False
    >>> print(bool(Test1([], ignored=5, notIgnored=0)))
    False
    >>> print(bool(Test1([], ignored=0, notIgnored=1)))
    True
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_falseifcontentsfalse = True)
    >>> t = (0, 0, None)
    >>> bool(t), bool(Test1(t)), bool(Test2(t))
    (True, True, False)
    """
    
    if len(self):
        if not self._SEQSPEC.get('seq_falseifcontentsfalse', False):
            return True
        
        return any(self)
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someList': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 5], someList=t, someNumber=25)
    >>> obj2 = obj1.__copy__()
    >>> obj1 is obj2, obj1 == obj2
    (False, True)
    >>> obj1.someList is obj2.someList
    True
    
    >>> NT = collections.namedtuple("MyNT", "a b c")
    >>> class S(NT, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         seq_makefunc = (lambda v,a: type(v)(*a)))
    >>> s = S(1, 2, 3)
    >>> s.b
    2
    >>> sCopy = s.__copy__()
    >>> sCopy == s, sCopy is s
    (True, False)
    """
    
    makeFunc = self._SEQSPEC.get('seq_makefunc', None)
    
    if makeFunc is not None:
        if self._ATTRSPEC:
            return makeFunc(self, self, **self.__dict__)
        else:
            return makeFunc(self, self)
    
    else:
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
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someList': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 5], someList=t, someNumber=25)
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1 is obj2, obj1 == obj2
    (False, True)
    >>> obj1.someList is obj2.someList
    False
    >>> obj1.someList[0] is obj2.someList[0]
    False
    
    >>> class Test1(list, metaclass=FontDataMetaclass): pass
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1([x])),
    ...         item_followsprotocol = True)
    
    >>> obj1 = Test2([5, None, Test1([4, 5])])
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1[0] is obj2[0], obj1[2] is obj2[2]
    (False, False)
    """
    
    if memo is None:
        memo = {}
    
    SS = self._SEQSPEC
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
                        # We use self.kwArgs here (used for special methods)
                        value = cf(value, **d.get('kwArgs', {}))
                        vNew[i] = memo.setdefault(id(value), value)
                    
                    else:
                        raise

    
    else:
        vNew[:] = self[:]
    
    # Now do attributes
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, d, memo)
    
    # Construct and return the result
    makeFunc = SS.get('seq_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, vNew, **dNew)
    else:
        return type(self)(vNew, **dNew)

def SM_eq(self, other):
    """
    Determine if the two objects are equal (selectively).
    
    :return: True if the sequences and their attributes are equal (allowing for
        selective inattention to certain attributes depending on their control
        flags, and depending on the ``attrSorted`` tuple)
    :rtype: bool
    
    >>> class Bottom(list, metaclass=FontDataMetaclass): pass
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someNumber': {},
    ...       'someList': {'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom([1, 2, 3])
    >>> b2 = Bottom([4, 5, 6])
    >>> t = Top([b1, b2])
    >>> obj1 = LPA([3, 4, 6], someList=t, someNumber=5)
    >>> obj1 == obj1
    True
    >>> obj1 == None
    False
    >>> obj2 = LPA([3, 4, 6], someList=t.__deepcopy__(), someNumber=5)
    >>> obj1 == obj2
    True
    >>> obj2.someList[0].append(3.5)
    >>> obj1 == obj2
    False
    
    >>> class Test(list, metaclass=FontDataMetaclass):
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
    
    if any(map(operator.ne, iter(self), iter(other))):
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
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforcomparisons = True),
    ...         notIgnored = dict())
    
    >>> obj1 = Test1((1, 2, 3), ignored=3, notIgnored=4)
    >>> obj2 = Test1((1, 2, 3), ignored=5, notIgnored=4)
    >>> obj3 = Test1((1, 2, 3), ignored=3, notIgnored=7)
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
    
    for k in sorted(AS):  # don't use sortedKeys; this needs to be exhaustive
        ks = AS[k]
        f = ks.get('attr_asimmutablefunc', None)
        obj = d[k]
        
        if not ks.get('attr_ignoreforcomparisons', False):
            if ks.get(
              'attr_asimmutabledeep',
              ks.get('attr_followsprotocol', False)):
                
                cf = ks.get('attr_deepconverterfunc', None)
                
                try:
                    boundMethod = obj.asImmutable
                
                except AttributeError:
                    if cf is not None:
                        boundMethod = cf(obj).asImmutable
                    else:
                        raise
                
                # Note we use self.kwArgs here (used for special methods)
                v.append(boundMethod(**d.get('kwArgs', {})))
            
            elif f is not None:
                v.append(f(obj))
            
            else:
                hash(obj)  # make sure it's hashable
                v.append(obj)
    
    return hash((tuple(self), tuple(v)))

def SM_init(self, *args, **kwArgs):
    """
    Initialize the mutable sequence from ``args``, and the attributes from
    ``kwArgs`` if they're present, or via the attribute initialization function
    otherwise.
    
    :param args: Sequence initializer
    :param kwArgs: Attribute initializers
    :return: None
    :raises ValueError: If a sequence with ``seq_fixedlength`` set is
        initialized with a different number of items than expected
    
    This method is only included in the class being defined if:
        #.  The base class is mutable; and
        #.  There isn't already an ``__init__()`` defined
    
    Only one of ``__init__()`` and ``__new__()`` will be included.
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initLen = dict(
    ...             attr_initfunc = (lambda self: len(self)),
    ...             attr_initfuncneedsself = True))
    >>> v1 = Test1([-4, 'x', 19])
    >>> v1.initLen
    3
    
    >>> class Test2(list, metaclass=FontDataMetaclass):
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
    >>> Test2([1, 2]).pprint()
    0: 1
    1: 2
    a: abc
    b: ab
    c: c
    >>> Test2([1, 2], a="wxyz and then some").pprint()
    0: 1
    1: 2
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test2([1, 2], c="independently initialized").pprint()
    0: 1
    1: 2
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_fixedlength': 3}
    
    >>> x = Test3([1, 2])
    Traceback (most recent call last):
      ...
    ValueError: Incorrect length for fixed-length object!
    
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> Test4([1, 2, 3], a=5)
    Test4([1, 2, 3], a=5.0)
    """
    
    list.__init__(self, *args)
    fixedLen = self._SEQSPEC.get('seq_fixedlength', None)
    
    if (
      (fixedLen is not True) and
      (fixedLen is not None) and
      (len(self) != fixedLen)):
        
        raise ValueError("Incorrect length for fixed-length object!")
    
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

def SM_lt(self, other):
    """
    Determine whether ``self`` is less than ``other``.
    
    :param other: The value to compare against ``self``
    :return: True if self is less than other; False otherwise
    :rtype: bool
    
    This method (and the three derived methods ``__le__()``, ``__gt__()``, and
    ``__ge__()``) is only added if attributes are defined, and if
    seq_enableordering is True. In this case the attributes will be used to
    determine whether ``self`` is less than ``other``, but **only** if the
    non-attribute (i.e. main sequence) value compares equal.
    
    >>> class EOFalse(tuple, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         a = dict(attr_initfunc = (lambda: 0)),
    ...         b = dict(attr_initfunc = (lambda: 0)))
    ...     attrSorted = ('a', 'b')
    >>> t1 = EOFalse((1, 2, 3), a=5, b=9)
    >>> t2 = EOFalse((1, 2, 2), a=5, b=9)
    >>> t3 = EOFalse((1, 2, 4), a=5, b=9)
    >>> t4 = EOFalse((1, 2, 3), a=5, b=11)
    >>> (t1 < t1, t1 < t2, t1 < t3, t1 < t4)
    (False, False, True, False)
    
    >>> class EOTrue(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(seq_enableordering=True)
    ...     attrSpec = dict(
    ...         a = dict(attr_initfunc = (lambda: 0)),
    ...         b = dict(attr_initfunc = (lambda: 0)))
    ...     attrSorted = ('a', 'b')
    >>> t1 = EOTrue((1, 2, 3), a=5, b=9)
    >>> t2 = EOTrue((1, 2, 2), a=5, b=9)
    >>> t3 = EOTrue((1, 2, 4), a=5, b=9)
    >>> t4 = EOTrue((1, 2, 3), a=5, b=11)
    >>> (t1 < t1, t1 < t2, t1 < t3, t1 < t4)
    (False, False, True, True)
    """
    
    tSelf = tuple(self)
    tOther = tuple(other)
    
    if tSelf < tOther:
        return True
    
    if tSelf > tOther:
        return False
    
    return attrhelper.SM_lt(
      self._ATTRSPEC,
      self._ATTRSORT,
      getattr(other, '_ATTRSPEC', {}),
      self.__dict__,
      getattr(other, '__dict__', {}))

def SM_new(cls, *args, **kwArgs):
    """
    Initialize the immutable sequence from ``args``, and the attributes from
    ``kwArgs`` if they're present, or via the attribute initialization function
    otherwise.
    
    :param args: Sequence initializer
    :param kwArgs: Attribute initializers
    :return: The newly created object
    :raises ValueError: If a sequence with ``seq_fixedlength`` set is
        initialized with a different number of items than expected
    
    This method is only included in the class being defined if:
        #.  The base class is immutable; and
        #.  There isn't already a ``__new__()`` defined
    
    Only one of ``__init__()`` and ``__new__()`` will be included.
    
    >>> class Test1(tuple, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initLen = dict(
    ...             attr_initfunc = (lambda self: len(self)),
    ...             attr_initfuncneedsself = True))
    >>> v1 = Test1([-4, 'x', 19, 'z'])
    >>> v1.initLen
    4
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
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
    >>> Test2([1, 2]).pprint()
    0: 1
    1: 2
    a: abc
    b: ab
    c: c
    >>> Test2([1, 2], a="wxyz and then some").pprint()
    0: 1
    1: 2
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test2([1, 2], c="independently initialized").pprint()
    0: 1
    1: 2
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test3(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'seq_fixedlength': 3}
    
    >>> x = Test3([1, 2])
    Traceback (most recent call last):
      ...
    ValueError: Incorrect length for fixed-length object!
    
    >>> class Test4(tuple, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> Test4([1, 2, 3], a=5)
    Test4((1, 2, 3), a=5.0)
    """
    
    try:
        t = tuple.__new__(cls, *args)
    except TypeError:
        t = tuple.__new__(cls, args)  # handles namedtuple-like cases
    
    fixedLen = cls._SEQSPEC.get('seq_fixedlength', None)
    
    if (
      (fixedLen is not True) and
      (fixedLen is not None) and
      (len(t) != fixedLen)):
        
        raise ValueError("Incorrect length for fixed-length object!")
    
    d = t.__dict__ = {}
    AS = cls._ATTRSPEC
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for k, ks in AS.items():
        if k in kwArgs:
            d[k] = kwArgs[k]
        
        elif 'attr_initfuncchangesself' in ks:
            # We defer doing these special initializations until all the
            # other positional and keyword arguments are done.
            deferredKeySet.add(k)
        
        else:
            v = ([t] if 'attr_initfuncneedsself' in ks else [])
            # it's now OK to do this, because we've already guaranteed
            # all attr dict specs have an attr_initfunc.
            d[k] = ks['attr_initfunc'](*v)
    
    for k in deferredKeySet:
        ks = AS[k]
        initFunc = ks['attr_initfunc']
        
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
    
    >>> class Test1(list, metaclass=FontDataMetaclass): pass
    >>> t1 = Test1([1, 'a', 5])
    >>> t1 == eval(repr(t1))
    True
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> t2 = Test2([t1, Test1(['z', 9])])
    >>> t2 == eval(repr(t2))
    True
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> t3 = Test3()
    >>> t3 == eval(repr(t3))
    True
    
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    ...     attrSpec = {
    ...       'y': {'attr_initfunc': int},
    ...       'z': {'attr_initfunc': Test3, 'attr_followsprotocol': True}}
    ...     attrSorted = ('y', 'z')
    >>> t4 = Test4()
    >>> t4 == eval(repr(t4))
    True
    
    >>> t3a = Test3(a='r', b=[1, 3])
    >>> t4a = Test4([t3a, None], y=-5)
    >>> t4a == eval(repr(t4a))
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

def SM_str(baseKind):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    :raises AttributeError: If a non-Protocol object is used for a sequence
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_strusesrepr': True}
    >>> t1 = Test1([1, 'a', 5])
    >>> print(str(t1))
    [1, 'a', 5]
    
    >>> class Test2(tuple, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> t2 = Test2([t1, Test1(['z', 9])])
    >>> print(str(t2))
    ([1, 'a', 5], ['z', 9])
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {
    ...       'item_usenamerforstr': True,
    ...       'item_renumberdirect': True}
    >>> t = Test3([11, 60, 98])
    >>> print(str(t))
    [11, 60, 98]
    >>> t.setNamer(namer.testingNamer())
    >>> print(str(t))
    [xyz12, xyz61, afii60003]
    
    >>> class Bottom(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_strusesrepr': True}
    >>> class Top(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_followsprotocol': True}
    >>> class LPA(list, metaclass=FontDataMetaclass):
    ...     seqSpec = {'item_strusesrepr': True}
    ...     attrSpec = {
    ...       'someNumber': {
    ...         'attr_initfunc': (lambda: 15),
    ...         'attr_label': "Count"},
    ...       'someList': {
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data",
    ...         'attr_followsprotocol': True}}
    ...     attrSorted = ('someList', 'someNumber')
    >>> b1 = Bottom(['b'])
    >>> b2 = Bottom(['a', 'm'])
    >>> print(LPA([3, 5], someNumber=6, someList=Top([b1, b2])))
    [3, 5], Extra data = [['b'], ['a', 'm']], Count = 6
    
    >>> class Part1(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}, 'y': {}}
    ...     attrSorted = ('x', 'y')
    >>> class Part2(list, metaclass=FontDataMetaclass):
    ...     attrSpec = {'part1': {'attr_strneedsparens': True}, 'z': {}}
    ...     attrSorted = ('part1', 'z')
    >>> print(Part2([], part1=Part1([], x=2, y=3), z=4))
    [], part1 = ([], x = 2, y = 3), z = 4
    
    >>> class Test(tuple, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {
    ...         'attr_labelfunc': (
    ...           lambda x, **k:
    ...           ("Odd" if x % 2 else "Even"))}}
    ...     attrSorted = ('x',)
    >>> print(Test([34], x=2))
    (34,), Even = 2
    >>> print(Test([34], x=3))
    (34,), Odd = 3
    
    >>> class Test1(list, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': False}}
    ...   attrSorted = ('s',)
    >>> class Test2(list, metaclass=FontDataMetaclass):
    ...   attrSpec = {
    ...     's': {
    ...       'attr_initfunc': (lambda: 'fred'),
    ...       'attr_strusesrepr': True}}
    ...   attrSorted = ('s',)
    >>> print(Test1())
    [], s = fred
    >>> print(Test2())
    [], s = 'fred'
    
    >>> class Test3(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    ...     attrSorted = ('x', 'y')
    >>> print(Test3([]))
    [], y = 5
    >>> print(Test3([], x=4))
    [], x = 4, y = 5
    
    >>> class Test4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_renumberdirect = True,
    ...             attr_usenamerforstr = True),
    ...         y = dict(attr_renumberdirect = True))
    >>> t4 = Test4([4, 9], x=35, y=45)
    >>> print(t4)
    [4, 9], x = 35, y = 45
    >>> t4.setNamer(namer.testingNamer())
    >>> print(t4)
    [4, 9], x = xyz36, y = 45
    
    >>> class Test5(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True,
    ...         item_usenamerforstr = True)
    >>> class Test6(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_deepconverterfunc = (lambda x, **k: Test5([x])),
    ...         item_followsprotocol = True,
    ...         item_usenamerforstr = True)
    
    >>> obj = Test6([15, None, Test5([97, 2])])
    >>> obj.setNamer(namer.testingNamer())
    >>> print(obj)
    [[xyz16], None, [afii60002, xyz3]]
    
    >>> class Test7(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumbernamesdirect = True)
    >>> obj = Test7([303, None, 304])
    >>> print(obj)
    [303, None, 304]
    
    >>> obj.kwArgs = {'editor': _fakeEditor()}
    >>> print(obj)
    [303 ('Required Ligatures On'), None, 304 ('Common Ligatures On')]
    """
    
    def SM_str_closure(self):
        SS = self._SEQSPEC
        AS = self._ATTRSPEC
        d = self.__dict__
        savedNamers = []
        f = str
        selfNamer = getattr(self, '_namer', None)
        v = list(self)
        
        if SS.get('item_usenamerforstr', False) and selfNamer is not None:
            if SS.get(
              'item_renumberdeep',
              SS.get('item_followsprotocol', False)):
                
                cf = SS.get('item_deepconverterfunc', None)
                madeAChange = False
                
                for i, obj in enumerate(self):
                    if obj is not None:
                        try:
                            obj.setNamer, obj.getNamer
                        
                        except AttributeError:
                            if cf is not None:
                                obj = cf(obj, **d.get('kwArgs', {}))
                                madeAChange = True
                            
                            else:
                                raise
                        
                        savedNamers.append((obj, obj.getNamer()))
                        obj.setNamer(selfNamer)
                        v[i] = obj
            
            elif SS.get('item_renumberdirect', False):
                f = selfNamer.bestNameForGlyphIndex
        
        elif SS.get('item_renumbernamesdirect', False):
            kwa = d.get('kwArgs', {})
            f = functools.partial(utilities.nameFromKwArgs, **kwa)
        
        elif SS.get('item_strusesrepr', False):
            f = repr
        
        sv = [f(obj) for obj in v]
        sv = [("None" if obj is None else obj) for obj in sv]
        
        if baseKind is list:
            r = "[%s]" % (', '.join(sv),)
        else:
            final = (',' if len(self) == 1 else '')
            r = "(%s%s)" % (', '.join(sv), final)
        
        for obj, oldNamer in savedNamers:
            obj.setNamer(oldNamer)
        
        if not AS:
            return r
        
        svAttr = attrhelper.SM_str(self, selfNamer)
        return ', '.join([r] + svAttr)
    
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
    '__repr__': SM_repr,
    '__str__': SM_str
    }

def _addMethods(cd, bases):
    baseClassIsMutable = hasattr(bases[-1], '__delitem__')  # a bit hacky...
    AS = cd['_ATTRSPEC']
    SS = cd['_SEQSPEC']
    baseKind = (list if baseClassIsMutable else tuple)
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
    stdClasses = (list, tuple)
    
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
        
        cd['__ne__'] = (lambda a, b: not (a == b))
        
        if (not baseClassIsMutable) and ('__hash__' not in cd):
            cd['__hash__'] = SM_hash
    
    # Only include a __bool__ method if needed
    if needBool or SS.get('seq_falseifcontentsfalse', False):
        if '__bool__' not in cd:
            cd['__bool__'] = SM_bool
    
    # Only include __lt__ (and the other three) if there are attributes AND
    # if seq_enableordering is True
    if AS and SS.get('seq_enableordering', False):
        if '__lt__' not in cd:
            cd['__lt__'] = SM_lt
        
        cd['__gt__'] = (lambda a, b: not ((a < b) or (a == b)))
        cd['__ge__'] = (lambda a, b: not (a < b))
        cd['__le__'] = (lambda a, b: (a < b) or (a == b))
    
    # Only include an __init__ method if there are attributes or a fixed length
    fixedLen = SS.get('seq_fixedlength', None)
    
    if AS or (fixedLen is not None and fixedLen is not True):
        if baseClassIsMutable and ('__init__' not in cd):
            cd['__init__'] = SM_init
        elif (not baseClassIsMutable) and ('__new__' not in cd):
            cd['__new__'] = SM_new

def _validateSeqSpec(d):
    """
    Make sure only known keys are included in the ``seqSpec`` (checks like this
    are only possible in a metaclass, which is another reason to use them over
    traditional subclassing).
    
    >>> d = {'item_followsprotocol': True}
    >>> _validateSeqSpec(d)
    >>> d = {'item_bollowsprotocol': True}
    >>> _validateSeqSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown seqSpec keys: ['item_bollowsprotocol']
    """
    
    unknownKeys = set(d) - validSeqSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown seqSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'seq_validatefunc_partial' in d and 'seq_validatefunc' in d:
        raise ValueError("Cannot specify both a seq_validatefunc_partial "
        "and a seq_validatefunc.")
    
    if 'item_validatefunc_partial' in d and 'item_validatefunc' in d:
        raise ValueError("Cannot specify both an item_validatefunc_partial "
        "and an item_validatefunc.")
    
    if 'item_prevalidatedglyphset' in d:
        if not d.get('item_renumberdirect', False):
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
    Metaclass for list-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already one of the
    Protocol classes, the ``seqSpec`` and ``attrSpec`` will define additions to
    the original. In this case, if an ``attrSorted`` is provided, it will be
    used for the combined attributes (original and newly-added); otherwise the
    new attributes will be added to the end of the ``attrSorted`` list.

    The rules for combining ``attrSpecs`` are a little trickier: note that
    these are dicts of dicts, and so a simple ``update()`` call will
    potentially remove important content. For this reason, the new ``attrSpec``
    for a subclass is walked and the sub-dicts merged separately.
    
    >>> class L1(list, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         attr1 = dict())
    >>> print(L1(['x', 'y'], attr1=10))
    [x, y], attr1 = 10
    
    >>> class L2(L1, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True)
    ...     attrSpec = dict(
    ...         attr2 = dict())
    ...     attrSorted = ('attr2', 'attr1')
    >>> print(L2(['x', 'y'], attr1=10, attr2=9))
    ['x', 'y'], attr2 = 9, attr1 = 10
    
    >>> class L3(L1, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True)
    ...     attrSpec = dict(
    ...         attr2 = dict())
    ...     attrSorted = ('attr2', 'attr1')
    >>> print(L3(['x', 'y'], attr1=10, attr2=9))
    ['x', 'y'], attr2 = 9, attr1 = 10
    
    >>> class L4(list, metaclass=FontDataMetaclass):
    ...     seqSpec = dict(item_strusesrepr = True)
    ...     attrSpec = dict(
    ...         a = dict(attr_initfunc = (lambda: 14)))
    
    >>> class L5(L4):
    ...     attrSpec = dict(
    ...         a = dict(attr_ignoreforbool = True),
    ...         b = dict(attr_label = "Look, a label"))
    
    >>> print(L5(['a', 'b'], b=5))
    ['a', 'b'], a = 14, Look, a label = 5
    >>> obj = L5([], b=0)
    >>> obj.a
    14
    >>> bool(obj)
    False
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_SEQSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            SS = c._SEQSPEC.copy()
            SS.update(classdict.pop('seqSpec', {}))
            classdict['_SEQSPEC'] = classdict['_MAIN_SPEC'] = SS
            _validateSeqSpec(SS)
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
            d = classdict['_SEQSPEC'] = classdict.pop('seqSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateSeqSpec(d)
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
    from fontio3.utilities import namer
    
    def _getMatrixModule():
        from fontio3.fontmath import matrix
        
        return matrix
    
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
