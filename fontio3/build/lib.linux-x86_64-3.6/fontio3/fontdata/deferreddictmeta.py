#
# deferreddictmeta.py
#
# Copyright © 2008-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Standard metaclass for all font data that is dict-like with cache limits.

There are three signal differences between generalized mappings and deferred
dicts:

    1.  Deferred dicts need not be loaded into memory all at once. There is a
        mechanism to create values for a given key on demand, and a finite
        limit may be set as to how many will be kept active.
    
    2.  Deferred dicts allow access to their keyed entries via the regular
        indexing (``d[xxx]``), but also via attribute-style dot-notation
        (``d.xxx``), where syntactically valid.
    
    3.  Your base class using ``mapmeta.FontDataMetaclass`` will usually be
        ``dict`` (or some related class, like ``defaultdict``). By contrast,
        your base class using ``deferreddictmeta.FontDataMetaclass`` will
        usually be ``object``.

The following class attributes are used to control the various behaviors and
attributes of instances of the class:

``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``deferredDictSpec``
    A dict of specification information for the deferred dict, where the
    keys and their associated values are defined in the following list. The
    listed defaults apply if the specified key is not present in the
    ``deferredDictSpec``.

    Note keys starting with ``item_`` relate to individual mapping items,
    while keys starting with ``dict_`` relate to the mapping as a whole.
    Also note that in general, functions have higher priority than deep
    calls, and ``None`` values are never passed to either functions or deep
    calls.

    If a ``deferredDictSpec`` is not provided, an empty one will be used,
    and all defaults listed below will be in force.
    
    ``dict_asimmutablefunc``
        A function to create an immutable version of the mapping. This function
        takes the mapping as the sole positional argument, as well as the usual
        ``kwArgs``, and returns the immutable representation.
        
        There is no default.
    
    ``dict_compactremovesfalses``
        If True then any values whose ``bool()`` is False will be removed from
        the mapping in the output of a ``compacted()`` call.
        
        Default is False.
    
    ``dict_compareignoresfalses``
        If True then ``__eq__()`` and ``__ne__()`` will ignore those key/value
        pairs for which ``bool(value)`` is False.
        
        Default is False.
    
    ``dict_keeplimit``
        A value specifying how many live objects should be kept at once. New
        objects created via ``item_createfunc`` will be added to the dict, and
        if the total number of such items exceeds ``dict_keeplimit``, the least
        recently used value will be replaced with ``_singletonNCV``.

        A value of ``None`` means there is no limit; all living objects are
        kept in the dict, and purging never happens. A value of zero, by
        contrast, means no values will be kept in the dict. A positive value
        specifies the actual count that will be kept.
        
        Default is ``None``.
    
    ``dict_maxcontextfunc``
        A function to determine the maximum context for the
        deferred dict. This function takes a single argument, the
        deferred dict itself.
        
        There is no default.
    
    ``dict_mergechecknooverlap``
        If True, and there exists non-empty overlap in the key sets of self and
        other at ``merged()`` time, a ``ValueError`` will be raised.
        
        Default is False.
    
    ``dict_orderdependencies``
        If specified, should be a dict mapping keys to sets of other keys. For
        instance, ``{'a': {'n', 'z'}}`` will mean that the object associated
        with key ``a`` depends on the objects associated with keys ``n`` and
        ``z``. The effects of this dependency differ by action kind; for
        example in the ``recalculated()`` method, this means that objects ``n``
        and ``z`` will be recalculated first, and only then will object ``a``
        be recalculated.

        Action-specific overrides can be introduced as they are needed; use
        tags like ``dict_orderdependencies_recalc`` for these (where the action
        is the last part of the tag).
        
        There is no default.
    
    ``dict_ppoptions``
        If specified, it should be a dict whose keys are valid options to be
        passed in for construction of a :py:class:`~fontio3.utilities.pp.PP`
        instance, and whose values are as appropriate. This can be used to make
        a custom ``noDataString``, for instance.
        
        There is no default.
    
    ``dict_pprintdifffunc``
        A function to pretty-print differences between two mappings of the same
        type. The function (which can be an unbound method, as can many other
        ``mapSpec`` values) takes at least three arguments: the
        :py:class:`~fontio3.utilities.pp.PP` object, the current mapping, and
        the prior mapping.
        
        There is no default.
    
    ``dict_pprintfunc``
        A function taking two arguments: a :py:class:`~fontio3.utilities.pp.PP`
        instance, and the mapping as a whole. The usual use for this tag is to
        specify a value of :py:meth:`mapping_grouped
        <fontio3.utilities.pp.PP.mapping_grouped>` or
        :py:meth:`mapping_grouped_deep
        <fontio3.utilities.pp.PP.mapping_grouped_deep>`, where the
        mapping's keys are integer-valued.
        
        There is no default.
    
    ``dict_recalculatefunc``
        If specified, a function taking one positional argument,
        the whole mapping. Additional keyword arguments (for
        example, ``editor``) may be specified.

        The function returns a pair: the first value is True or
        False, depending on whether the recalculated list's value
        actually changed. The second value is the new recalculated
        object to be used (if the first value was True).
    
        If a ``dict_recalculatefunc`` is provided then no individual
        ``item_recalculatefunc`` calls will be made. If you want them
        to be made, use a ``dict_recalculatefunc_partial`` instead.
        
        There is no default.
    
    ``dict_recalculatefunc_partial``
        A function taking one positional argument, the whole
        mapping, and optional additional keyword arguments. The
        function should return a pair: the first value is True or
        False, depending on whether the recalculated mapping's
        value actually changed. The second value is the new
        recalculated object to be used (if the first value was
        True).
    
        After the ``dict_recalculatefunc_partial`` call is done,
        individual ``item_recalculatefunc`` calls will be made. This
        allows you to "divide the labor" in useful ways.
        
        There is no default.
    
    ``dict_recalculatefunc_withattrs``
        A function taking one positional argument, the whole map,
        and optional keyword arguments. This acts almost exactly
        like the ``dict_recalculatefunc`` attribute, with the main
        difference being this function also recalculates the
        attributes.
        
        There is no default.
    
    ``dict_validatefunc``
        A function taking one positional argument, the whole mapping, and
        optional additional keyword arguments. The function returns True if the
        mapping is valid, and False otherwise.
        
        There is no default.
    
    ``dict_validatefunc_partial``
        A function taking one positional argument, the whole mapping, and
        optional additional keyword arguments. The function returns True if the
        mapping is valid, and False otherwise. Any ``item_validatefuncs`` and
        ``item_validatefunckeys`` will also be run to determine the returned
        True/False value, so this function should focus on overall sequence
        validity.

        If you want this function to do everything without allowing any
        ``item_validatefuns`` to be run, then use the ``dict_validatefunc``
        keyword instead.
        
        There is no default.
    
    ``dict_wisdom``
        A string with information on what the object is, along with sensible
        usage notes.
        
        There is no default for wisdom, alas...
    
    ``item_asimmutabledeep``
        If True then mapping values have their own ``asImmutable()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_asimmutablefunc``
        A function called on a mapping value and returning an
        immutable version of that value. If this is not specified,
        and neither ``item_followsprotocol`` nor ``item_asimmutabledeep``
        is True, then mapping values must already be immutable.
        
        There is no default.

    ``item_coalescedeep``
        If True then mapping values have their own ``coalesced()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_compactdeep``
        If True then mapping values have their own ``compacted()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_createfunc``
        A function that is called to create values for storage in the object.
        If ``item_createfuncneedsself`` is False (the default), then this
        function has two parameters: the first is the key of the object to be
        created; the second is a dict that can contain anything useful to the
        function for this creation process. This dict, called
        ``creationExtras`` in the class methods, can contain things like an
        original binary string for the ``Glyf`` object and an associated
        ``Loca`` object, for instance.

        If ``item_createfuncneedsself`` is True, then ``self`` will be passed
        as the second positional argument, and the ``creationExtras`` dict will
        be passed as the third.

        There is one convention for the dictionary that is passed to this
        creation function: it should contain a key named ``oneTimeKeyIterator``
        whose value is an iterator that will be used to create the initial set
        of keys for the deferred dict. These keys won't have actual values
        associated with them until the demand occurs.
        
        There is no default; this *must* be specified.
    
    ``item_createfuncneedsself``
        If True, then ``self`` will be passed as the second positional argument
        to the ``item_createfunc`` (the ``creationExtras`` dict will be passed
        third in this case).
        
        Default is False.
    
    ``item_deepcopydeep``
        If True then mapping values have their own ``__deepcopy__()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepcopyfunc``
        A function that is called to deep-copy mapping values. It is called
        with two arguments: the value and a ``memo`` dict.
        
        There is no default.
    
    ``item_enablecyclechecktag``
        If specified (which is only allowed for deep mapping values) then a
        cyclic object check will be made for this mapping's values during
        ``isValid()`` execution. A parent trace will be provided in a passed
        ``kwArg`` called ``activeCycleCheck``, which will be a dict mapping
        tags to lists of parent objects. The tag associated with this
        ``item_enablecyclechecktag`` is what will be used to look up the
        specific parent chain for all mapping values.
        
        Default is ``None``.
    
    ``item_followsprotocol``
        If True then mapping values are themselves Protocol objects, and have
        all the Protocol methods.
        
        Note that this may be overridden by explicitly setting a desired
        ``...deep`` flag to False. So, for instance, if mapping values are
        Protocol objects but are not to have ``compacted()`` calls, then the
        ``deferredDictSpec`` should have this flag set to True and
        ``item_compactdeep`` set to False.
        
        Default is False.
    
    ``item_inputcheckfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate as a mapping value.
        
        There is no default.
    
    ``item_inputcheckkeyfunc``
        If specified, should be a function that takes a single positional
        argument and keyword arguments. This function should return True if the
        specified value is appropriate as a key value.
        
        There is no default.
    
    ``item_keyisbytes``
        If keys are supposed to be ``bytes`` objects then set this flag to
        True. If True, then if a non-``bytes`` key is used, the metaclass code
        will coerce it into a ``bytes`` object (using a default encoding of
        ``ASCII``).
        
        Default is False.
    
    ``item_keyislivingdeltas``
        If True then mapping keys will be included in the output from a call to
        ``gatheredLivingDeltas()``. This is permitted because
        :py:class:`~fontio3.opentype.living_variations.LivingDeltas` objects
        are already immutable.
        
        Default is False.
    
    ``item_keyisoutputglyph``
        If True then (non-``None``) keys are treated as output glyphs. This
        means they will not be included in the output of a
        ``gatheredInputGlyphs()`` call, and they will be included in the output
        of a ``gatheredOutputGlyphs()`` call. Note that
        ``item_renumberdirectkeys`` must also be set; otherwise keys will not
        be added, even if this flag is True.
        
        Default is False.
    
    ``item_keyrepresentsx``
        If True then non-``None`` keys are interpreted as x-coordinates. This
        knowledge is used by the ``scaled()`` method, in conjunction with the
        ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated y-coordinate value will be
        forced to zero, unless the ``item_valuerepresentsy`` and
        ``item_transformkeyvaluepairs`` flags are set.
        
        Default is False.
    
    ``item_keyrepresentsy``
        If True then non-``None`` keys are interpreted as y-coordinates. This
        knowledge is used by the ``scaled()`` method, in conjunction with the
        ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated x-coordinate value will be
        forced to zero, unless the ``item_valuerepresentsx`` and
        ``item_transformkeyvaluepairs`` flags are set.
        
        Default is False.
    
    ``item_mergedeep``
        If True then mapping values have their own ``merged()`` methods. Note
        that these methods may not end up being called, even if this flag is
        True, if the ``merged()`` method is called with the ``replaceWhole``
        keyword argument set to True.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_mergefunc``
        A function that is called on mapping values sharing the same key in two
        distinct mappings (usually ``self`` and ``other``). This function takes
        two positional arguments (the items from ``self`` and ``other``), and
        optional keyword arguments that were passed in to ``merged()``. It
        returns two values: a Boolean indicating whether the merged object is
        different than the original ``self`` argument, and the merged object.
        
        There is no default.
    
    ``item_mergekeyfunc``
        A function that is used to change a key from a merging object if it
        should collide with an existing key. An example of when this is useful
        is merging two ``GPOS`` tables each of which contains a ``b'kern0001'``
        tag -- you don't wish to piecewise merge these, but rather change the
        tag for one of them to something else, like ``b'kern0002'`` for
        instance.

        Note that if this is specified then ``merged()`` keyword arguments like
        ``conflictPreferOther`` will be ignored, since the conflicts are being
        explicitly managed via this key-changing operation.

        This function takes a key, an ``inUse`` set, and keyword arguments, and
        returns a new key that does not collide.
        
        There is no default.
    
    ``item_pprintdeep``
        If True then mapping values will be pretty-printed via a call to their
        own ``pprint()`` methods. The key will be used as a label, unless an
        ``item_pprintlabelfunc`` is specified (q.v.)

        If False, and a ``dict_pprintfunc`` or ``item_pprintfunc`` is
        specified, that function will be used. Otherwise, each item will be
        printed via the :py:meth:`~fontio3.utilities.pp.PP.simple` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintdiffdeep``
        If True then mapping values have their own ``pprint_changes()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintfunc``
        A function that is called to pretty-print mapping values. It is called
        with four arguments: the :py:class:`~fontio3.utilities.pp.PP` instance,
        a mapping value, a label (which will be the key, or possibly a string
        representing a glyph name), and ``kwArgs`` for any additional keyword
        arguments. For an example of the need for the optional arguments, see
        :py:mod:`~fontio3.feat.settings`.

        A note about glyph names: if ``item_usenamerforstr`` is True and a
        :py:class:`~fontio3.utilities.namer.Namer` is available, ``pprint()``
        will add a keyword argument called ``bestNameFunc`` when it calls the
        supplied ``item_pprintfunc``. This allows that function to do the name
        string substitution.
        
        There is no default.
    
    ``item_pprintlabelfunc``
        If specified, this should be a function that is called with a mapping
        key and that returns a string suitable for passing as the label
        argument to a :py:class:`~fontio3.utilities.pp.PP` instance. (This
        function may end up being called with the mapping value as well; see
        the ``item_pprintlabelfuncneedsobj`` key for more information).
        
        Default is that the keys themselves will be used as labels.
    
    ``item_pprintlabelfuncneedsobj``
        If True, calls to the ``item_pprintlabelfunc`` will have an
        extra keyword argument added (in addition to the mapping
        key already passed in as a positional argument). This
        extra keyword will be ``obj``, and the value will be the
        object itself.
        
        Default is False.
    
    ``item_pprintlabelpresort``
        Normally, if an ``item_pprintlabelfunc`` is provided, it will be called
        to get the label strings for the keys and then the results will be
        sorted. This allows a :py:class:`~fontio3.utilities.namer.Namer` to be
        used, and the output order of glyph names will be properly alphabetic.

        However, if a label function is provided for keys like ``ppem``, where
        the numeric sort is still desired, then the behavior described above
        can lead to bad results (for instance, '19' sorting before '6'). To fix
        this you should set this flag to True. In that case, the values will be
        sorted *before* being passed one-by-one to the label function.
        
        Default is False.
    
    ``item_pprintlabelpresortfunc``
        If specified, this function will be passed into the Python ``sorted()``
        function as the ``key`` keyword argument. It should therefore be a
        function that takes a presorted key object and returns a new object
        which, when sorted, yields the desired order.

        Note that specififying this key automatically causes the
        ``item_pprintlabelpresort`` key to be used as well, and thus that key
        need not be specified as well. If you need the sort order to be
        reversed, however, you must explicitly specify the
        ``item_pprintlabelpresortreverse`` flag.
        
        There is no default.
    
    ``item_pprintlabelpresortreverse``
        The effect is like ``item_pprintlabelpresort``, but the order of the
        keys is reversed.
        
        Default is False.
    
    ``item_prevalidatedglyphsetkeys``
        A ``set`` or ``frozenset`` containing glyph indices which are to be
        considered valid as mapping keys, even though they exceed the font's
        glyph count. This is useful for passing ``0xFFFF`` values through
        validation for state tables, where that glyph code is used to indicate
        the deleted glyph.
        
        There is no default.
    
    ``item_prevalidatedglyphsetvalues``
        A ``set`` or ``frozenset`` containing glyph indices which are to be
        considered valid for mapping values, even though they exceed the font's
        glyph count. This is useful for passing ``0xFFFF`` values through
        validation for state tables, where that glyph code is used to indicate
        the deleted glyph.
        
        There is no default.
    
    ``item_python3rounding``
        If True, the Python 3 round function will be used. If
        False (the default), old-style Python 2 rounding will be
        done. This affects both scaling and transforming if one of
        the rounding options is used.
        
        Default is False.
    
    ``item_recalculatedeep``
        If True then mapping values have their own ``recalculated()`` methods.
        
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
        If True then mapping values have their own ``cvtsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbercvtsdeepkeys``
        If True then mapping keys have their own ``cvtsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbercvtsdirectkeys``
        If True then mapping keys are interpreted as CVT indices, and are
        subject to renumbering if the ``cvtsRenumbered()`` method is called.
        See also ``item_renumbercvtsdirectvalues``.
        
        Default is False.
    
    ``item_renumbercvtsdirectvalues``
        If True then mapping values are interpreted as CVT indices, and are
        subject to renumbering if the ``cvtsRenumbered()`` method is called.
        See also ``item_renumbercvtsdirectkeys``.
        
        Default is False.
    
    ``item_renumberdeep``
        If True then mapping values have their own ``glyphsRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberdeepkeys``
        If True then mapping keys are themselves objects that can be
        renumbered.
        
        Default is False.
    
    ``item_renumberdirectkeys``
        If True then mapping keys will be directly mapped via the ``oldToNew``
        dict in ``glyphsRenumbered()``. In addition, ``keepMissing`` will be
        respected. It is OK to specify this in addition to the
        ``item_renumberdeep`` key; in this case, the keys will be mapped, and
        the values will have their own ``glyphsRenumbered()`` methods called,
        but the resulting pair will only be kept if the key mapping succeeded

        Note that if ``keepMissing`` is False, and a key is not in
        ``oldToNew``, then that key-value pair will not survive the
        renumbering, even if the value is successfully mapped.
        
        Default is False.
    
    ``item_renumberdirectvalues``
        If True then all mapping values will be directly mapped via the
        ``oldToNew`` dict in ``glyphsRenumbered()``. In addition,
        ``keepMissing`` will be respected.

        Note that if ``keepMissing`` is False, and a value is not in
        ``oldToNew``, then that key-value pair will not survive the
        renumbering, even if the key is successfully mapped.
        
        Default is False.
    
    ``item_renumberfdefsdeep``
        If True then mapping values have their own ``fdefsRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdeepkeys``
        If True then mapping keys have their own ``fdefsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdirectkeys``
        If True then mapping keys are interpreted as FDEF indices, and are
        subject to renumbering if the ``fdefsRenumbered()`` method is called.
        See also ``item_renumberfdefsdirectvalues``.
        
        Default is False.
    
    ``item_renumberfdefsdirectvalues``
        If True then mapping values are interpreted as FDEF indices, and are
        subject to renumbering if the ``fdefsRenumbered()`` method is called.
        See also ``item_renumberfdefsdirectkeys``.
        
        Default is False.
    
    ``item_renumbernamesdeep``
        If True then mapping values have their own ``namesRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdeepkeys``
        If True then mapping keys have their own ``namesRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdirectkeys``
        If True then mapping keys are interpreted as ``name`` table indices,
        and are subject to renumbering if the ``namesRenumbered()`` method is
        called. See also ``item_renumbernamesdirectvalues``.
        
        Default is False.
    
    ``item_renumbernamesdirectvalues``
        If True then mapping values are interpreted as ``name`` table indices,
        and are subject to renumbering if the ``namesRenumbered()`` method is
        called. See also ``item_renumbernamesdirectkeys``.
        
        Default is False.
    
    ``item_renumberpcsdeep``
        If True then the mapping values have their own ``pcsRenumbered()``
        methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpcsdeepkeys``
        If True then the mapping keys have their own ``pcsRenumbered()``
        methods.
        
        Default is False.
    
    ``item_renumberpcsdirect``
        If True then mapping values are themselves PC values. These values will
        be directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``.
        
        Default is False.
    
    ``item_renumberpcsdirectkeys``
        If True then mapping keys are themselves PC values. These values will
        be directly mapped using the ``mapData`` list that is passed into
        ``pcsRenumbered()``.
        
        Default is False.
    
    ``item_renumberpointsdeep``
        If True then mapping values understand the ``pointsRenumbered()``
        protocol.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberpointsdeepkeys``
        If True then mapping keys understand the ``pcsRenumbered()`` protocol.

        It is an error for this flag to be set if ``item_renumberdirectkeys``
        is also set.
        
        Default is False.
    
    ``item_renumberpointsdirect``
        If True then mapping values are themselves point indices. Note that if
        this is used, the ``kwArgs`` passed into ``pointsRenumbered()`` must
        include a value, ``glyphIndex``, that is used to index into that
        method's ``mapData``, unless this is implicitly handled by the presence
        of the ``item_renumberdirectkeys`` flag (which indicates the keys are
        glyph indices).
        
        Default is False.
    
    ``item_renumberpointsdirectkeys``
        If True then mapping keys are themselves point indices. Note that if
        this is used, the ``kwArgs`` passed into ``pointsRenumbered()`` must
        include a value, ``glyphIndex``, that is used to index into that
        method's ``mapData``, unless this is implicitly handled by the presence
        of the ``item_renumberdirectkeys`` flag (which indicates the keys are
        glyph indices).

        It is an error for this flag to be set if ``item_renumberdirectkeys``
        is also set.
        
        Default is False.
    
    ``item_renumberstoragedeep``
        If True then mapping values have their own ``storageRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedeepkeys``
        If True then mapping keys have their own ``storageRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedirectkeys``
        If True then mapping keys are interpreted as storage indices, and are
        subject to renumbering if the ``storageRenumbered()`` method is called.
        See also ``item_renumberstoragedirectvalues``.
        
        Default is False.
    
    ``item_renumberstoragedirectvalues``
        If True then mapping values are interpreted as storage
        indices, and are subject to renumbering if the
        ``storageRenumbered()`` method is called. See also
        ``item_renumberstoragedirectkeys``.
        
        Default is False.
    
    ``item_roundfunckeys``
        If provided, this function will be used for rounding keys in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``item_roundfuncvalues``
        If provided, this function will be used for rounding values in
        ``scaled()`` and ``transformed()`` calls. It should take one positional
        argument (the value), at least one keyword argument (``castType``, the
        type of the returned result, or ``None`` to keep its current type), and
        other optional keyword arguments.
        
        There is no default.
    
    ``item_scaledeep``
        If True then mapping values have their own ``scaled()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_scaledirectkeys``
        If True then non-``None`` mapping keys will be scaled by the
        ``scaled()`` method, with the results rounded to the nearest integral
        value (with .5 cases controlled by ``item_python3rounding``). If this
        is not desired, use the ``item_scaledirectkeysnoround`` flag instead.

        The type of a rounded scaled key will be the type of the original key.

        If two different keys scale to the same value then a ``KeyError`` is
        raised to indicate the collision. To avoid this, use the
        ``item_scaledirectkeysgrouped`` flag.
        
        Default is False.
    
    ``item_scaledirectkeysgrouped``
        This flag has an effect similar to that of ``item_scaledirectkeys``,
        but instead of a ``KeyError`` being raised if a collision occurs, the
        values that end up sharing a key will be gathered into a list.
        
        Default is False.
    
    ``item_scaledirectkeysnoround``
        If True then non-``None`` mapping keys will be scaled by the
        ``scaled()`` method. No rounding will be done on the result. If
        rounding to integral values is desired, callers should not specify this
        flag.
    
        The type of a non-rounded scaled key will be ``float``.
        
        Default is False.
    
    ``item_scaledirectvalues``
        If True then non-``None`` mapping values will be scaled by the
        ``scaled()`` method, with the results rounded to the nearest integral
        value (with .5 cases controlled by ``item_python3rounding``). If this
        is not desired, use the ``item_scaledirectvaluesnoround`` flag instead.

        The type of a rounded scaled value will be the type of the original
        value.
        
        Default is False.
    
    ``item_scaledirectvaluesnoround``
        If True then non-``None`` mapping values will be scaled by the
        ``scaled()`` method. No rounding will be done on the result. If
        rounding to integral values is desired, callers should not specify this
        flag.
    
        The type of a non-rounded scaled value will be ``float``.
        
        Default is False.
    
    ``item_strusesrepr``
        If True then the string representation for values in the mapping will
        be created via ``repr()``, not ``str()``.
        
        Default is False.
    
    ``item_subloggernamefunc``
        A function taking a single argument, the key, and returning a string to
        be used for the ``itemLogger`` when that deep value's ``isValid()``
        method is called.
        
        There is no default; the synthesized name for the sub-logger will be
        ``'[str(key)]'`` or ``'[repr(key)]'``.
    
    ``item_subloggernamefuncneedsobj``
        If True, then the ``item_subloggernamefunc`` will be passed a keyword
        argument named ``obj`` containing the entire mapping.
        
        Default is False.
    
    ``item_transformkeysgrouped``
        If True, no ``KeyError`` will be raised if two or more keys transform
        into the same value; instead, all the values associated with the
        transformed key will be gathered into a list.
        
        Default is False.
    
    ``item_transformkeysnoround``
        If True, keys after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the keys will always be
        left as type ``float``, irrespective of the original type. This differs
        from the default case, where rounding will be used but the rounded key
        will be the same type as the original key.

        Note the absence of an ``item_transformkeysdirect`` flag. Calls to
        the ``transformed()`` method will only affect non-``None`` keys if one
        or more of the ``item_keyrepresentsx``, ``item_keyrepresentsy``, or
        ``item_transformkeyvaluepairs`` flags are set (or, of course, the
        ``item_followsprotocol`` flag).

        If two or more different keys scale to the same value then a
        ``KeyError`` is raised to indicate the collision. To avoid this, use
        the ``item_transformkeysgrouped`` flag.
        
        Default is False.
    
    ``item_transformkeyvaluepairs``
        If True then the key/value pairs in the mapping are linked for purposes
        of transformation. Which is X and which is Y depends on the other flag
        settings (for instance, ``item_keyrepresentsx`` or
        ``item_valuerepresentsx``).
        
        Default is False.
    
    ``item_transformvaluesnoround``
        If True, values after a ``transformed()`` call will not be rounded to
        integers. Note that if this flag is specified, the values will always
        be left as type ``float``, irrespective of the original type. This
        differs from the default case, where rounding will be used but the
        rounded value will be the same type as the original value.

        Note the absence of an ``item_transformvaluesdirect`` flag. Calls to
        the ``transformed()`` method will only affect non-``None`` values if
        one or more of the ``item_valuerepresentsx``,
        ``item_valuerepresentsy``, or ``item_transformkeyvaluepairs`` flags are
        set (or, of course, the ``item_followsprotocol`` flag).
        
        Default is False.
    
    ``item_usenamerforstr``
        If this flag and any of the ``item_renumberdirect...`` flags is True,
        and a :py:class:`~fontio3.utilities.namer.Namer` has been specified via
        the ``setNamer()`` call or via keyword arguments, then that Namer will
        be used for generating the strings for the glyph names.
        
        Default is False.
    
    ``item_validatecode_namenotintable``
        The code to be used for logging when a name table index is being used
        but that index is not actually present in the ``name`` table.
        
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
        The code to be used for logging when a CVT index is used but the Editor
        has no ``'cvt '`` table.
        
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
        If True then mapping values have their own ``isValid()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_validatedeepkeys``
        If True then mapping keys have their own ``isValid()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_validatefunc``
        A function taking one positional argument, a mapping value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``item_validatefunc_partial`` instead.
        
        There is no default.
    
    ``item_validatefunc_partial``
        A function taking one positional argument, a mapping value, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use an ``item_validatefunc`` instead.
        
        There is no default.
    
    ``item_validatefunckeys``
        A function taking one positional argument, a mapping key, and an
        arbitrary number of keyword arguments. The function returns True if the
        key is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function must do all item checking. If you want the default
        checking (glyph indices, scalable values, etc.) then use
        ``item_validatefunc_partial`` instead.
        
        There is no default.
    
    ``item_validatefunckeys_partial``
        A function taking one positional argument, a mapping key, and an
        arbitrary number of keyword arguments. The function returns True if the
        value is valid (that is, if no errors are present). Note that values of
        ``None`` WILL be passed into this function, unlike most other actions.

        This function does not need to do checking on standard things like
        glyph indices or scalable values. If you prefer to do all checking in
        your function, use an ``item_validatefunc`` instead.
        
        There is no default.
    
    ``item_validatekwargsfunc``
        A function taking two positional arguments (the mapping itself, and the
        key being validated) and returning a dict representing extra keyword
        arguments to be passed along to the deep values' ``isValid()`` method.
        Note this should only be provided if ``item_followsprotocol`` is True.
        
        There is no default.
    
    ``item_valueislivingdeltas``
        If True then mapping values will be included in the output from a call
        to ``gatheredLivingDeltas()``.
        
        Default is False.
    
    ``item_valueislookup``
        If True then mapping values will be included in the output from a call
        to ``gatheredRefs()``.
        
        Default is False.
    
    ``item_valueisoutputglyph``
        If True then (non-``None``) values are treated as output glyphs. This
        means they will not be included in the output of a
        ``gatheredInputGlyphs()`` call, and they will be included in the output
        of a ``gatheredOutputGlyphs()`` call. Note that
        ``item_renumberdirectvalues`` must also be set; otherwise keys will not
        be added, even if this flag is True.
        
        Default is False.
    
    ``item_valuerepresentsx``
        If True then non-``None`` values are interpreted as x-coordinates. This
        knowledge is used by the ``scaled()`` method, in conjunction with the
        ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated y-coordinate value will be
        forced to zero, unless the ``item_keyrepresentsy`` and
        ``item_transformkeyvaluepairs`` flags are set.

        Default is False.
    
    ``item_valuerepresentsy``
        If True then non-``None`` values are interpreted as y-coordinates. This
        knowledge is used by the ``scaled()`` method, in conjunction with the
        ``scaleOnlyInX`` or ``scaleOnlyInY`` keyword arguments to that method.

        The ``transformed()`` method also uses this knowledge to transform a
        point; note in this case the associated x-coordinate value will be
        forced to zero, unless the ``item_keyrepresentsx`` and
        ``item_transformkeyvaluepairs`` flags are set.
        
        Default is False.
    
    ``item_wisdom_key``
        A string with information on what the key is, along with sensible usage
        notes.
        
        There is, alas, no default for wisdom.
    
    ``item_wisdom_value``
        A string with information on what the value is, along with sensible
        usage notes.
        
        There is, alas, no default for wisdom.
"""

# System imports
import collections
import functools
import itertools
import logging
import operator

# Other imports
from fontio3 import utilities
from fontio3.fontdata import attrhelper, dictkeyutils, invariants, seqmeta
from fontio3.utilities import pp, valassist

# -----------------------------------------------------------------------------

#
# Constants and helper classes
#

_singletonNCV = object()  # unique object meaning "needs creation"

validDictSpecKeys = frozenset([
  'dict_asimmutablefunc',
  'dict_compactremovesfalses',
  'dict_compareignoresfalses',
  'dict_keeplimit',
  'dict_maxcontextfunc',
  'dict_mergechecknooverlap',
  'dict_orderdependencies',
  'dict_ppoptions',
  'dict_pprintdifffunc',
  'dict_pprintfunc',
  'dict_recalculatefunc',
  'dict_recalculatefunc_partial',
  'dict_recalculatefunc_withattrs',
  'dict_validatefunc',
  'dict_validatefunc_partial',
  'dict_wisdom',
  
  'item_asimmutabledeep',
  'item_asimmutablefunc',
  'item_coalescedeep',
  'item_compactdeep',
  'item_createfunc',
  'item_createfuncneedsself',
  'item_deepcopydeep',
  'item_deepcopyfunc',
  'item_enablecyclechecktag',
  'item_followsprotocol',
  'item_inputcheckfunc',
  'item_inputcheckkeyfunc',
  'item_keyisbytes',
  'item_keyislivingdeltas',
  'item_keyisoutputglyph',
  'item_keyrepresentsx',
  'item_keyrepresentsy',
  'item_mergedeep',
  'item_mergefunc',
  'item_mergekeyfunc',
  'item_pprintdeep',
  'item_pprintdiffdeep',
  'item_pprintfunc',
  'item_pprintlabelfunc',
  'item_pprintlabelfuncneedsobj',
  'item_pprintlabelpresort',
  'item_pprintlabelpresortfunc',
  'item_pprintlabelpresortreverse',
  'item_prevalidatedglyphsetkeys',
  'item_prevalidatedglyphsetvalues',
  'item_python3rounding',
  'item_recalculatedeep',
  'item_recalculatefunc',
  'item_renumbercvtsdeep',
  'item_renumbercvtsdeepkeys',
  'item_renumbercvtsdirectkeys',
  'item_renumbercvtsdirectvalues',
  'item_renumberdeep',
  'item_renumberdeepkeys',
  'item_renumberdirectkeys',
  'item_renumberdirectvalues',
  'item_renumberfdefsdeep',
  'item_renumberfdefsdeepkeys',
  'item_renumberfdefsdirectkeys',
  'item_renumberfdefsdirectvalues',
  'item_renumbernamesdeep',
  'item_renumbernamesdeepkeys',
  'item_renumbernamesdirectkeys',
  'item_renumbernamesdirectvalues',
  'item_renumberpcsdeep',
  'item_renumberpcsdeepkeys',
  'item_renumberpcsdirect',
  'item_renumberpcsdirectkeys',
  'item_renumberpointsdeep',
  'item_renumberpointsdeepkeys',
  'item_renumberpointsdirect',
  'item_renumberpointsdirectkeys',
  'item_renumberstoragedeep',
  'item_renumberstoragedeepkeys',
  'item_renumberstoragedirectkeys',
  'item_renumberstoragedirectvalues',
  'item_roundfunckeys',
  'item_roundfuncvalues',
  'item_scaledeep',
  'item_scaledirectkeys',
  'item_scaledirectkeysgrouped',
  'item_scaledirectkeysnoround',
  'item_scaledirectvalues',
  'item_scaledirectvaluesnoround',
  'item_strusesrepr',
  'item_subloggernamefunc',
  'item_subloggernamefuncneedsobj',
  'item_transformkeysgrouped',
  'item_transformkeysnoround',
  'item_transformkeyvaluepairs',
  'item_transformvaluesnoround',
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
  'item_validatedeepkeys',
  'item_validatefunc',
  'item_validatefunc_partial',
  'item_validatefunckeys',
  'item_validatefunckeys_partial',
  'item_validatekwargsfunc',
  'item_valueislivingdeltas',
  'item_valueislookup',
  'item_valueisoutputglyph',
  'item_valuerepresentsx',
  'item_valuerepresentsy',
  'item_wisdom_key',
  'item_wisdom_value'])

class _ScaleListShallow(list, metaclass=seqmeta.FontDataMetaclass):
    seqSpec = dict(item_strusesrepr = True)

class _ScaleListDeep(list, metaclass=seqmeta.FontDataMetaclass):
    seqSpec = dict(item_followsprotocol = True)

# -----------------------------------------------------------------------------

#
# Methods
#

if 0:
    def __________________(): pass

def M_asImmutable(self, **kwArgs):
    """
    Returns an immutable object with the same contents as ``self``.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: An immutable version of the data in ``self``
    
    What is returned is a tuple whose first element is the name of the class,
    and whose second element is a frozenset of (key, immut) pairs. If the class
    has attributes there will be further elements, which will be the results of
    the ``asImmutable()`` call on the attributes. Note, however, that this
    format has changed in the past and may change again. Clients should not
    rely on the internals of the object returned from this call, but should
    rather just use it.
    
    The following ``kwArgs`` are supported:
    
    ``memo``
        A dict mapping object IDs to the immutable value for the object. This
        only applies to deep objects. Note that it's safe to use ``id(...)`` in
        this case, since the ``asImmutable()`` call does not do any object
        mutation in situ (it creates lots of new objects, but no reuse of an
        existing ID will ever happen while the call is going on).
        
        This is optional; if one is not provided, a temporary one will be used.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> tst = (
    ...   'Top',
    ...   frozenset({
    ...     (15, ('Bottom', frozenset({('a', 14), ('b', 9), ('c', 22)}))),
    ...     (30, ('Bottom', frozenset({('a', 12), ('d', 29)})))}))
    >>> t.asImmutable() == tst
    True
    
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someDict': {'attr_followsprotocol': True},
    ...       'someList': {'attr_asimmutablefunc': tuple}}
    >>> b1 = Bottom(a=14)
    >>> b2 = Bottom(d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> t = DPA({3: 5}, someDict=t, someList=[2, 5])
    >>> tst = (
    ...   'DPA',
    ...   frozenset({(3, 5)}),
    ...   ( 'someDict',
    ...     ( 'Top',
    ...       frozenset({
    ...         (30, ('Bottom', frozenset({('d', 29)}))),
    ...         (15, ('Bottom', frozenset({('a', 14)})))}))),
    ...   ('someList', (2, 5)))
    >>> t.asImmutable() == tst
    True
    
    >>> class Test3a(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict())
    
    >>> def fSpecial(obj, **kwArgs):
    ...     if kwArgs.get('attrFirst', False):
    ...         return (obj.x,) + tuple(obj) + tuple(obj.values())
    ...     return tuple(obj) + tuple(obj.values()) + (obj.x,)
    
    >>> class Test3b(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         dict_asimmutablefunc = fSpecial)
    ...     attrSpec = dict(
    ...         x = dict())
    
    >>> t3a = Test3a({3: 5, -2: 4, 2: 6}, x=-2)
    >>> t3b = Test3b({3: 5, -2: 4, 2: 6}, x=-2)
    
    >>> tst = ('Test3a', frozenset({(-2, 4), (2, 6), (3, 5)}), ('x', -2))
    >>> t3a.asImmutable() == tst
    True
    
    >>> t3b.asImmutable()
    (2, 3, -2, 6, 5, 4, -2)
    
    >>> t3b.asImmutable(attrFirst=True)
    (-2, 2, 3, -2, 6, 5, 4)
    """
    
    DDS = self._DEFDSPEC
    fWhole = DDS.get('dict_asimmutablefunc', None)
    
    if fWhole is not None:
        return fWhole(self, **kwArgs)
    
    memo = kwArgs.pop('memo', {})
    f = DDS.get('item_asimmutablefunc', None)
    
    if f is not None:
        r = (
          type(self).__name__,
          frozenset(
            (key, (None if self[key] is None else f(self[key])))
            for key in self))
    
    elif DDS.get(
      'item_asimmutabledeep',
      DDS.get('item_followsprotocol', False)):
        
        s = set()
        
        for key in self:
            obj = self[key]
            
            if obj is None:
                s.add((key, None))
                continue
            
            objID = id(obj)
            
            if objID not in memo:
                memo[objID] = obj.asImmutable(memo=memo, **kwArgs)
            
            s.add((key, memo[objID]))
        
        r = (type(self).__name__, frozenset(s))
    
    else:
        r = (type(self).__name__, frozenset(self.items()))
    
    rAttr = attrhelper.M_asImmutable(
      self._ATTRSPEC,
      self._ATTRSORT,
      self.__dict__,
      memo = memo,
      **kwArgs)
    
    if rAttr is not None:
        r += rAttr
    
    return r

def M_changed(self, key):
    """
    Notify fontio3 that content has changed.
    
    :param key: The key whose associated value has been changed.
    :return: ``None``
    
    If you make changes to an object without replacing it outright (for
    example, appending items to a list), it would no longer match the original
    value if reconstructed for cache filling. To avoid this problem, call this
    method on the key. This will move the object into the permanent dictionary,
    and prevent it from being purged.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k,e: [k]),
    ...         dict_keeplimit = 2)
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(range(1, 11))))
    >>> t[4]
    [4]
    >>> t[4].append('x')
    >>> t[4]
    [4, 'x']
    >>> t[5], t[6]  # keeplimit of 2 means t[4] changes are lost
    ([5], [6])
    >>> t[4]
    [4]
    >>> t[4].append('x')
    >>> t[4]
    [4, 'x']
    >>> t.changed(4)
    >>> t[5], t[6]
    ([5], [6])
    >>> t[4]
    [4, 'x']
    """
    
    if key not in self._dAdded:
        assert key in self._dOrig
        obj = self[key]
        self._dAdded[key] = self._dOrig[key]
        del self._dOrig[key]
    
    if self._DEFDSPEC.get('dict_keeplimit', None):
        self._keysCurrentlyCached.discard(key)

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
    
    The check will be made on one of three things (these are evaluated in the
    specified order):
    
        #. an attribute, if ``attrName`` is in ``kwArgs``; or
        #. a key, if ``kwArgs['isKey']`` is True; or
        #. a value
    
    The following ``kwArgs`` are supported:
    
    ``attrName``
         An optional string, identifying an attribute of the object. If
         specified, this attribute's own ``checkInput()`` method will be called
         with the ``valueToCheck`` value. Otherwise, this object's checking
         function will be used.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...   deferredDictSpec = dict(
    ...     item_inputcheckfunc = (lambda x, **k: 0 <= x < 100),
    ...     item_inputcheckkeyfunc = (lambda x, **k: x > 500))
    ...   attrSpec = dict(
    ...     attr1 = dict(
    ...       attr_inputcheckfunc = (lambda x, **k: x in {'a', 'e', 'u'})))
    >>> x = Test1({1200: 41, 1355: 19}, attr1='u')
    
    Checking attribute attr1:
    
    >>> x.checkInput('r', attrName='attr1')
    False
    >>> x.checkInput('e', attrName='attr1')
    True
    
    Checking keys:
    
    >>> x.checkInput(200, isKey=True)
    False
    >>> x.checkInput(2000, isKey=True)
    True
    
    Checking values:
    
    >>> x.checkInput(-5)
    False
    >>> x.checkInput(50)
    True
    """
    
    if kwArgs.get('attrName', ''):
        return attrhelper.M_checkInput(
          self._ATTRSPEC,
          self.__dict__,
          valueToCheck,
          **kwArgs)
    
    DDS = self._DEFDSPEC
    keyCheck = kwArgs.pop('isKey', False)
    
    if keyCheck:
        f = DDS.get('item_inputcheckkeyfunc', None)
    else:
        f = DDS.get('item_inputcheckfunc', None)
    
    if f is None:
        return True
    
    return f(valueToCheck, **kwArgs)

def M_clear(self):
    """
    Clears all content from the object.
    
    :return: ``None``
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(t)
    ['a', 'f', 'x', 'z']
    >>> t.clear()
    >>> list(t)
    []
    """
    
    self._dOrig.clear()
    self._dAdded.clear()
    self._creationExtras.clear()
    
    if self._DEFDSPEC.get('dict_keeplimit', None):
        self._keysCurrentlyCached.clear()

def M_coalesced(self, **kwArgs):
    """
    Return new object representing self with duplicates coerced to the
    same object.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with duplicates coalesced
    :rtype: Same as ``self``

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
        non-attribute members (e.g. mapping values) and attribute members of
        self. If True, the pool will be cleared before attributes are
        coalesced.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(x = dict())
    >>> d1 = Test1({'a': 2000, 'b': 1950 + 50}, x = 200 * 10)
    >>> d1['a'] == d1['b'], d1['a'] == d1.x, d1['b'] == d1.x
    (True, True, True)
    >>> d1['a'] is d1['b'], d1['a'] is d1.x, d1['b'] is d1.x
    (False, False, False)
    >>> d1C = d1.coalesced()
    >>> d1 == d1C, d1 is d1C
    (True, False)
    >>> d1C['a'] is d1C['b'], d1C['a'] is d1C.x, d1C['b'] is d1C.x
    (True, True, True)
    >>> d1CS = d1.coalesced(separateAttributesPool=True)
    >>> d1 == d1CS, d1 is d1CS
    (True, False)
    >>> d1CS['a'] is d1CS['b'], d1CS['a'] is d1CS.x, d1CS['b'] is d1CS.x
    (True, False, False)
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_followsprotocol = True)
    ...     attrSpec = dict(y = dict())
    >>> d2 = Test2({'i': d1, 'j': None}, y = 6000 // 3)
    >>> d2['i'].x == d2.y, d2['i'].x is d2.y
    (True, False)
    >>> d2C = d2.coalesced()
    >>> d2 == d2C
    True
    >>> d2C['i'].x == d2C.y, d2C['i'].x is d2C.y
    (True, True)
    """
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    DDS = self._DEFDSPEC
    mNew = dict.fromkeys(self)
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    
    coalesceDeep = DDS.get(
      'item_coalescedeep',
      DDS.get('item_followsprotocol', False))
    
    immutFunc = DDS.get('item_asimmutablefunc', None)
    
    immutDeep = DDS.get(
      'item_asimmutabledeep',
      DDS.get('item_followsprotocol', False))
    
    # First do mapping objects
    for k, obj in self.items():
        if obj is not None:
            if coalesceDeep:
                objID = id(obj)
                
                if objID in cwc:
                    obj = cwc[objID]
                
                else:
                    obj = obj.coalesced(pool=pool, **kwArgs)
                    cwc[objID] = obj
            
            if immutFunc is not None:
                mNew[k] = pool.setdefault(f(obj), obj)
            elif immutDeep:
                mNew[k] = pool.setdefault(obj.asImmutable(), obj)
            else:
                mNew[k] = pool.setdefault(obj, obj)
    
    # Now do attributes
    dNew = attrhelper.M_coalesced(
      self._ATTRSPEC,
      self.__dict__,
      pool,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    cwc[id(self)] = r
    return r

def M_compacted(self, **kwArgs):
    """
    Returns a new object which has been compacted.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new compacted object
    :rtype: Same as ``self``
    
    *Compacting* means that (if indicated by the presence of the
    ``dict_compactremovesfalses`` flag in the ``deferredDictSpec``) members of
    the mapping for which the ``bool()`` result is False are removed.

    Note that any attributes with their own ``compacted()`` method have access
    to the ``self`` as a ``kwArg`` named ``parentObj``. See the
    :py:class:`~fontio3.mort.features.Features` class for an example of how
    this is useful.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(dict_compactremovesfalses = True)
    >>> t1 = Test1({'a': 3, 'b': 0, 'c': False, 'd': None, 'e': '', 'f': 4})
    >>> print(t1.compacted())
    {'a': 3, 'f': 4}
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True,
    ...         dict_compactremovesfalses = True)
    ...     attrSpec = dict(x = dict(attr_followsprotocol = True))
    >>> t2 = Test2({'i': t1, 'j': None}, x = t1)
    >>> print(t2)
    {'i': {'a': 3, 'b': 0, 'c': False, 'd': None, 'e': , 'f': 4}, 'j': None}, x = {'a': 3, 'b': 0, 'c': False, 'd': None, 'e': , 'f': 4}
    >>> print(t2.compacted())
    {'i': {'a': 3, 'f': 4}}, x = {'a': 3, 'f': 4}
    """
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    DDS = self._DEFDSPEC
    mDeep = DDS.get('item_compactdeep', DDS.get('item_followsprotocol', False))
    mFilter = DDS.get('dict_compactremovesfalses', False)
    mNew = {}
    
    # First do mapping objects
    for k, obj in self.items():
        if mDeep and (obj is not None):
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                obj = obj.compacted(**kwArgs)
                cwc[objID] = obj
        
        if (not mFilter) or obj:
            mNew[k] = obj
    
    # Now do attributes
    kwArgs['parentObj'] = self
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    cwc[id(self)] = r
    return r

def M_copyCreationExtras(self):
    """
    Returns a shallow copy of ``self._creationExtras``.
    """
    
    return self._creationExtras.copy()

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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumbercvtsdirectkeys = True,
    ...         item_renumbercvtsdirectvalues = True)
    >>> d = Test1({10: 20, None: 30, 40: None, 50: 60})
    >>> print(d.cvtsRenumbered(cvtDelta=5))
    {15: 25, 45: None, 55: 65, None: 35}
    >>> print(d.cvtsRenumbered(oldToNew={40: 10, 10: 40}))
    {10: None, 40: 20, 50: 60, None: 30}
    >>> print(d.cvtsRenumbered(oldToNew={40: 10, 10: 40}, keepMissing=False))
    {10: None}
    >>> f = (lambda n,**k: (n if n % 4 else n + 900))
    >>> print(d.cvtsRenumbered(cvtMappingFunc=f))
    {10: 920, 50: 960, 940: None, None: 30}
    """
    
    DDS = self._DEFDSPEC
    
    deepKeys = DDS.get(
      'item_renumbercvtsdeepkeys',
      DDS.get('item_keyfollowsprotocol', False))
    
    deepValues = DDS.get(
      'item_renumbercvtsdeep',
      DDS.get('item_followsprotocol', False))
    
    directKeys = DDS.get('item_renumbercvtsdirectkeys', False)
    directValues = DDS.get('item_renumbercvtsdirectvalues', False)
    
    if deepKeys or deepValues or directKeys or directValues:
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
        
        mNew = {}
        
        for key, value in self.items():
            okToAdd = True
            
            if key is not None:
                if deepKeys:
                    key = key.cvtsRenumbered(**kwArgs)
                    
                    # If the key is a sequence with seq_fixedlength set, then
                    # any attempt to renumber with keepMissing False may result
                    # in an invalid object, which is now returned as None. We
                    # test for that here.
                    
                    if key is None:
                        okToAdd = False
                
                elif directKeys:
                    key = cvtMappingFunc(key, **kwArgs)
                    
                    if key is None:
                        okToAdd = False
            
            if okToAdd and (value is not None):
                if deepValues:
                    value = value.cvtsRenumbered(**kwArgs)
                
                elif directValues:
                    value = cvtMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberfdefsdirectkeys = True,
    ...         item_renumberfdefsdirectvalues = True)
    >>> d = Test1({10: 20, None: 30, 40: None, 50: 60})
    >>> print(d.fdefsRenumbered(oldToNew={40: 10, 10: 40}))
    {10: None, 40: 20, 50: 60, None: 30}
    >>> print(d.fdefsRenumbered(oldToNew={40: 10, 10: 40}, keepMissing=False))
    {10: None}
    >>> f = (lambda n,**k: (n if n % 4 else n + 900))
    >>> print(d.fdefsRenumbered(fdefMappingFunc=f))
    {10: 920, 50: 960, 940: None, None: 30}
    """
    
    DDS = self._DEFDSPEC
    
    deepKeys = DDS.get(
      'item_renumberfdefsdeepkeys',
      DDS.get('item_keyfollowsprotocol', False))
    
    deepValues = DDS.get(
      'item_renumberfdefsdeep',
      DDS.get('item_followsprotocol', False))
    
    directKeys = DDS.get('item_renumberfdefsdirectkeys', False)
    directValues = DDS.get('item_renumberfdefsdirectvalues', False)
    
    if deepKeys or deepValues or directKeys or directValues:
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
        
        mNew = {}
        
        for key, value in self.items():
            okToAdd = True
            
            if key is not None:
                if deepKeys:
                    key = key.fdefsRenumbered(**kwArgs)
                    
                    # If the key is a sequence with seq_fixedlength set, then
                    # any attempt to renumber with keepMissing False may result
                    # in an invalid object, which is now returned as None. We
                    # test for that here.
                    
                    if key is None:
                        okToAdd = False
                
                elif directKeys:
                    key = fdefMappingFunc(key, **kwArgs)
                    
                    if key is None:
                        okToAdd = False
            
            if okToAdd and (value is not None):
                if deepValues:
                    value = value.fdefsRenumbered(**kwArgs)
                
                elif directValues:
                    value = fdefMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
    
    >>> class TupleHelper(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectvalues': True}
    >>> t1 = Test1({5: 10, 6: 14, 7: 20, 8: None})
    >>> sorted(t1.gatheredInputGlyphs())
    [10, 14, 20]
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> t2 = Test2({9: t1, 10: None})
    >>> sorted(t2.gatheredInputGlyphs())
    [10, 14, 20]
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectkeys': True}
    >>> t3 = Test3({11: 'a', 14: 'b', None: 'x', 35: 'z'})
    >>> sorted(t3.gatheredInputGlyphs())
    [11, 14, 35]
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectkeys': True,
    ...       'item_renumberdirectvalues': True}
    >>> t4 = Test4({5: 20, 6: 21, 7: None, None: 8, 50: 75})
    >>> sorted(t4.gatheredInputGlyphs())
    [5, 6, 7, 8, 20, 21, 50, 75]
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdeepkeys': True}
    >>> t5 = Test5({
    ...   TupleHelper((3, 6, 10)): 90,
    ...   TupleHelper((18, 40)): 91,
    ...   None: 14})
    >>> sorted(t5.gatheredInputGlyphs())
    [3, 6, 10, 18, 40]
    
    >>> class Test6(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectkeys': True,
    ...       'item_keyisoutputglyph': True}
    >>> sorted(Test6({6: 'a', 7: 'b'}).gatheredInputGlyphs())
    []
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectvalues': True}
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectvalues': True,
    ...       'item_valueisoutputglyph': True}
    ...     attrSpec = dict(
    ...         topIrrelevant = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topDirect = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom({'a': 61, 'b': 62}, bot=5)
    >>> t = Top({'c': 71, 'd': 72}, topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredInputGlyphs())
    [5, 11, 61, 62]
    """
    
    DDS = self._DEFDSPEC
    r = set()
    
    # Gather data from keys
    if not DDS.get('item_keyisoutputglyph', False):
        if DDS.get('item_renumberdeepkeys', False):
            for key in self:
                if key is not None:
                    r.update(key.gatheredInputGlyphs(**kwArgs))
        
        elif DDS.get('item_renumberdirectkeys', False):
            r.update(key for key in self if key is not None)
    
    # Gather data from values
    if not DDS.get('item_valueisoutputglyph', False):
        
        if DDS.get(
          'item_renumberdeep',
          DDS.get('item_followsprotocol', False)):
            
            for obj in self.values():
                if obj is not None:
                    r.update(obj.gatheredInputGlyphs(**kwArgs))
        
        elif DDS.get('item_renumberdirectvalues', False):
            r.update(obj for obj in self.values() if obj is not None)
    
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
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...   deferredDictSpec = dict(
    ...     item_keyislivingdeltas = True,
    ...     item_valueislivingdeltas = True)
    ...   attrSpec = dict(
    ...     a = dict(attr_islivingdeltas = True),
    ...     b = dict())
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...   deferredDictSpec = dict(
    ...     item_followsprotocol = True)
    ...   attrSpec = dict(
    ...     c = dict(attr_islivingdeltas = True),
    ...     d = dict())
    >>> botObj = Bottom({2: 3, 4: 5, None: 6, 7: None}, a=-10, b=-9)
    >>> topObj = Top({8: botObj, 9: None}, c=-20, d=-19)
    
    Note that 8, -9, and -19 are not included here:
    
    >>> sorted(topObj.gatheredLivingDeltas())
    [-20, -10, 2, 3, 4, 5, 6, 7]
    """
    
    DDS = self._DEFDSPEC
    isDeep = DDS.get('item_followsprotocol', False)
    keyIsLD = DDS.get('item_keyislivingdeltas', False)
    valueIsLD = DDS.get('item_valueislivingdeltas', False)
    r = set()
    
    for k, v in self.items():
        if (k is not None) and keyIsLD:
            r.add(k)
        
        if v is None:
            continue
        
        if valueIsLD:
            r.add(v)
        
        elif isDeep:
            boundMethod = v.gatheredLivingDeltas
            r.update(boundMethod(**kwArgs))
    
    return r | attrhelper.M_gatheredLivingDeltas(
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
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'dict_maxcontextfunc': (lambda d: len(d) - 1)}
    >>> b1 = Bottom({1: 'a', 3: 'b', 5: 'c'})
    >>> b2 = Bottom({6: 'j', 7: 'i', 8: 'h', 10: 'g', 12: 'f', 15: 'e', 2:'d'})
    >>> b1.gatheredMaxContext(), b2.gatheredMaxContext()
    (2, 6)
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top({20: b1, 25: None}, x = [8, 1, 4], y=b2).gatheredMaxContext()
    8
    >>> Top({20: b1, 25: None}, x = [4, 1, 4], y=b2).gatheredMaxContext()
    6
    """
    
    DDS = self._DEFDSPEC
    mcFunc = DDS.get('dict_maxcontextfunc', None)
    
    if mcFunc is not None:
        mc = mcFunc(self)
    
    elif DDS.get('item_followsprotocol', False):
        mc = max(
          obj.gatheredMaxContext(**kwArgs)
          for obj in self.values()
          if obj is not None)
    
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

    Any place where glyph indices are the outputs from some rule or process, we
    call those *output glyphs*. Consider the case of *f* and *i* glyphs that
    are present in a ``GSUB`` ligature action to create an *fi* ligature. The
    *f* and *i* glyphs are the input glyphs here; the *fi* ligature glyph is
    the output glyph. Note that this method works for both OpenType and AAT
    fonts.
    
    >>> class TupleHelper(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_renumberdirect = True,
    ...         item_isoutputglyph = True)
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectvalues': True,
    ...       'item_valueisoutputglyph': True}
    >>> t1 = Test1({4: 10, 5: 22, 6: None, None: 15})
    >>> sorted(t1.gatheredOutputGlyphs())
    [10, 15, 22]
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> t2 = Test2({9: t1, 10: None})
    >>> sorted(t2.gatheredOutputGlyphs())
    [10, 15, 22]
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectkeys': True,
    ...       'item_keyisoutputglyph': True}
    >>> t3 = Test3({11: 'a', 14: 'b', None: 'x', 35: 'z'})
    >>> sorted(t3.gatheredOutputGlyphs())
    [11, 14, 35]
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_keyisoutputglyph = True,
    ...         item_renumberdirectkeys = True,
    ...         item_renumberdirectvalues = True,
    ...         item_valueisoutputglyph = True)
    >>> t4 = Test4({5: 20, 6: 21, 7: None, None: 8, 50: 75})
    >>> sorted(t4.gatheredOutputGlyphs())
    [5, 6, 7, 8, 20, 21, 50, 75]
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdeepkeys': True}
    >>> t5 = Test5({
    ...   TupleHelper((3, 6, 10)): 90,
    ...   TupleHelper((18, 40)): 91,
    ...   None: 14})
    >>> sorted(t5.gatheredOutputGlyphs())
    [3, 6, 10, 18, 40]
    
    >>> class Test6(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectkeys': True}
    >>> sorted(Test6({6: 'a', 7: 'b'}).gatheredOutputGlyphs())
    []
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_renumberdirectvalues': True,
    ...       'item_valueisoutputglyph': True}
    ...     attrSpec = {
    ...       'bot': {
    ...         'attr_renumberdirect': True,
    ...         'attr_isoutputglyph': True}}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectvalues': True}
    ...     attrSpec = dict(
    ...         topIrrelevant = {'attr_renumberdirect': True},
    ...         topDirect = {
    ...           'attr_renumberdirect': True,
    ...           'attr_isoutputglyph': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom({'a': 61, 'b': 62}, bot=5)
    >>> t = Top({'c': 71, 'd': 72}, topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredOutputGlyphs())
    [5, 11, 61, 62]
    """
    
    DDS = self._DEFDSPEC
    r = set()
    
    # Gather data from keys
    if DDS.get('item_renumberdeepkeys', False):
        for key in self:
            if key is not None:
                r.update(key.gatheredOutputGlyphs(**kwArgs))
    
    elif (
      DDS.get('item_renumberdirectkeys', False) and
      DDS.get('item_keyisoutputglyph', False)):
        
        r.update(key for key in self if key is not None)
    
    # Gather data from values
    if DDS.get('item_renumberdeep', DDS.get('item_followsprotocol', False)):
        for obj in self.values():
            if obj is not None:
                r.update(obj.gatheredOutputGlyphs(**kwArgs))
    
    elif (
      DDS.get('item_renumberdirectvalues', False) and
      DDS.get('item_valueisoutputglyph', False)):
        
        r.update(obj for obj in self.values() if obj is not None)
    
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
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_valueislookup = True)
    >>> class Middle(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_followsprotocol = True)
    >>> b1 = Bottom({5: object(), 7: None, 8: object()})
    >>> b2 = Bottom({4: b1[5], 5: None, 6: object()})
    >>> m = Middle({0: b1, 10: None, 20: b2})
    >>> kt = {}
    >>> d = m.gatheredRefs(keyTrace=kt)
    >>> id(b1[5]) in d, id(b2[6]) in d
    (True, True)
    >>> id(b1[7]) in d  # None is not added
    False
    >>> for s in sorted(repr(sorted(x)) for x in kt.values()): print(s)
    [(0, 5), (20, 4)]
    [(0, 8)]
    [(20, 6)]
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_followsprotocol = True),
    ...         y = dict(attr_islookup = True))
    >>> t = Top({1: 3, 3: 4, 5: 100}, x=m, y=object())
    >>> kt = {}
    >>> d = t.gatheredRefs(keyTrace=kt)
    >>> id(b1[5]) in d, id(b2[6]) in d, id(t.y) in d
    (True, True, True)
    >>> id(b1[7]) in d  # None is not added
    False
    >>> for s in sorted(repr(sorted(x)) for x in kt.values()): print(s)
    [('(attr)', 'x', 0, 5), ('(attr)', 'x', 20, 4)]
    [('(attr)', 'x', 0, 8)]
    [('(attr)', 'x', 20, 6)]
    [('(attr)', 'y')]
    """
    
    DDS = self._DEFDSPEC
    r = {}
    keyTrace = kwArgs.pop('keyTrace', {})
    keyTraceCurr = kwArgs.pop('keyTraceCurr', ())
    memo = kwArgs.pop('memo', set())
    
    if DDS.get('item_valueislookup', False):
        for key, value in self.items():
            if value is not None:
                r[id(value)] = value
                ktSet = keyTrace.setdefault(id(value), set())
                ktSet.add(keyTraceCurr + (key,))
    
    if DDS.get('item_followsprotocol', False):
        for key, value in self.items():
            if value is not None:
                if id(value) not in memo:
                    memo.add(id(value))
                    
                    r.update(
                      value.gatheredRefs(
                        keyTrace = keyTrace,
                        keyTraceCurr = keyTraceCurr + (key,),
                        memo = memo,
                        **kwArgs))
    
    # Now do attributes
    r.update(
      attrhelper.M_gatheredRefs(
        self._ATTRSPEC,
        self.__dict__,
        keyTrace = keyTrace,
        keyTraceCurr = keyTraceCurr + ('(attr)',),
        memo = memo,
        **kwArgs))
    
    return r

def M_get(self, key, default=None):
    """
    Gets a value, or a default if the key is not present.
    
    :param key: The key whose value is sought
    :param default: If the key is not present, this value will be returned
        instead. Default is ``None``.
    :return: The value associated with ``key``
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t.get('a', 'default')
    'aaaaa'
    >>> t.get('b', 'default')
    'default'
    """
    
    return (self[key] if key in self else default)

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
        
    ``missingKeyReplacementFunc``
        This is only used when ``item_renumberdirectkeys`` is True and
        ``keepMissing`` is False. Normally glyph keys that are missing
        from ``oldToNew`` will simply be removed from the mapping. If this
        keyword argument is present, by contrast, each key which would
        otherwise have been removed will instead be replaced with the value
        returned from this function.

        The function is called with the old key as the single positional
        argument, and with the usual keyword arguments.
    
    This is the functionality at the heart of font subsetting. To subset a
    font, you specify an ``oldToNew`` map with just the entries you want, and
    set ``keepMissing`` to False.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectvalues': True}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True,
    ...         item_pprintlabelpresort = True,
    ...         item_renumberdirectkeys = True)
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> print(t)
    {15: {'a': 14, 'b': 9, 'c': 22}, 30: {'a': 12, 'd': 29}}
    >>> m = {12: 200, 13: 201, 14: 202, 15: 203}
    >>> print(t.glyphsRenumbered(m))
    {30: {'a': 200, 'd': 29}, 203: {'a': 202, 'b': 9, 'c': 22}}
    >>> print(t.glyphsRenumbered(m, keepMissing=False))
    {203: {'a': 202}}
    
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'top': {'attr_followsprotocol': True}}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> obj = DPA({}, top=t)
    >>> print(obj.top)
    {15: {'a': 14, 'b': 9, 'c': 22}, 30: {'a': 12, 'd': 29}}
    >>> m = {12: 200, 13: 201, 14: 202, 15: 203}
    >>> print(obj.glyphsRenumbered(m).top)
    {30: {'a': 200, 'd': 29}, 203: {'a': 202, 'b': 9, 'c': 22}}
    >>> print(obj.glyphsRenumbered(m, keepMissing=False).top)
    {203: {'a': 202}}
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberdirectkeys = True)
    >>> mf = (lambda n,**k: "Gone")
    >>> otn = {11: 11, 15: 15}
    >>> d = Test1({n: "Here" for n in range(10, 16)})
    >>> print(d)
    {10: Here, 11: Here, 12: Here, 13: Here, 14: Here, 15: Here}
    >>> print(d.glyphsRenumbered(otn, keepMissing=False))
    {11: Here, 15: Here}
    >>> print(d.glyphsRenumbered(
    ...   otn,
    ...   keepMissing = False, missingKeyReplacementFunc=mf))
    {10: Gone, 11: Here, 12: Gone, 13: Gone, 14: Gone, 15: Here}
    """
    
    DDS = self._DEFDSPEC
    
    rDeepValue = DDS.get(
      'item_renumberdeep',
      DDS.get('item_followsprotocol', False))
    
    rDeepKey = DDS.get('item_renumberdeepkeys', False)
    rDirectKey = DDS.get('item_renumberdirectkeys', False)
    rDirectValue = DDS.get('item_renumberdirectvalues', False)
    keepMissing = kwArgs.get('keepMissing', True)
    missKeyFunc = kwArgs.get('missingKeyReplacementFunc', None)
    mNew = {}
    mRepl = {}
    
    for key, value in self.items():
        okToAdd = True
        dToUse = mNew
        
        if key is not None:
            if rDeepKey:
                key = key.glyphsRenumbered(oldToNew, **kwArgs)
                
                # If the key is a sequence with seq_fixedlength set, then any
                # attempt to renumber with keepMissing False may result in an
                # invalid object, which is now returned as None. We test for
                # that here.
                
                if key is None:
                    okToAdd = False
            
            elif rDirectKey:
                if key in oldToNew:
                    key = oldToNew[key]
                
                elif not keepMissing:
                    if missKeyFunc is not None:
                        value = missKeyFunc(key, **kwArgs)
                        dToUse = mRepl
                    
                    else:
                        okToAdd = False
        
        if okToAdd and (value is not None):
            if rDeepValue:
                value = value.glyphsRenumbered(oldToNew, **kwArgs)
            
            elif rDirectValue:
                if value in oldToNew:
                    value = oldToNew[value]
                elif not keepMissing:
                    okToAdd = False
        
        if okToAdd:
            dToUse[key] = value
    
    # Move any replacements into mNew
    for key, value in mRepl.items():
        if key not in mNew:
            mNew[key] = value
    
    # Now do attributes
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True)
    ...     attrSpec = dict(
    ...         deepAttr = dict(
    ...             attr_followsprotocol = True))
    >>> obj1 = Test1({'a': None, 'b': None}, deepAttr=None)
    >>> obj1.hasCycles()
    False
    >>> obj1.deepAttr = obj1
    >>> obj1.hasCycles()
    True
    >>> obj1.deepAttr = None
    >>> obj1['c'] = obj1
    >>> obj1.hasCycles()
    True
    """
    
    DDS = self._DEFDSPEC
    dACC = kwArgs.pop('activeCycleCheck', set())
    dMemo = kwArgs.get('memo', set())
    
    if DDS.get('item_followsprotocol', False):
        
        # We only check values, since keys are like sets; cycles are not
        # possible for them.
        
        for obj in self.values():
            if obj is None:
                continue
            
            objID = id(obj)
            
            if objID in dMemo:
                continue
            
            if objID in dACC:
                return True
            
            if obj.hasCycles(activeCycleCheck=(dACC | {objID}), **kwArgs):
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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_renumberdirectvalues': True}
    
    >>> logger = utilities.makeDoctestLogger("t1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> t1 = Test1({'a': 35, 'b': 90, 'c': None, 'd': 200})
    >>> t1.isValid(logger=logger, fontGlyphCount=500, editor=e)
    True
    
    >>> t1.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t1.['d'] - ERROR - Glyph index 200 too large.
    False
    
    >>> def _vf(d, **kwArgs):
    ...     if any(k % 2 for k in d):
    ...         kwArgs['logger'].error(('Vxxxx', (), "All keys must be even."))
    ...         return False
    ...     if not all(v % 2 for v in d.values()):
    ...         kwArgs['logger'].error(('Vxxx', (), "All values must be odd."))
    ...         return False
    ...     return True
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_renumberdirectvalues = True,
    ...         item_subloggernamefunc = (lambda k: "Glyph_%d" % (k,)),
    ...         dict_validatefunc_partial = _vf)
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> obj = Test2({0: 1, 26: 77})
    >>> obj.isValid(logger=logger, fontGlyphCount=150, editor=e)
    True
    
    >>> obj = Test2({0: 4, 26: 77})
    >>> obj.isValid(logger=logger, fontGlyphCount=50, editor=e)
    t2 - ERROR - All values must be odd.
    t2.Glyph_26 - ERROR - Glyph index 77 too large.
    False
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_enablecyclechecktag = 'z',
    ...         item_followsprotocol = True)
    >>> obj = Test3({14: None, 16: Test3({'z': None})})
    >>> obj.isValid(logger=logger, editor=e)
    True
    >>> obj[16]['r'] = obj  # add circular ref
    >>> obj.isValid(logger=logger, editor=e)
    t2.[16].['r'].[16] - ERROR - Circular object reference for key '16'
    False
    """
    
    DDS = self._DEFDSPEC
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
    
    wholeFunc = DDS.get('dict_validatefunc', None)
    wholeFuncPartial = DDS.get('dict_validatefunc_partial', None)
    
    keyFunc = DDS.get('item_validatefunckeys', None)
    keyFuncPartial = DDS.get('item_validatefunckeys_partial', None)
    
    keyDeep = DDS.get(
      'item_validatedeepkeys',
      DDS.get('item_keyfollowsprotocol', False))
    
    keyGlyph = DDS.get('item_renumberdirectkeys', False)
    keyName = DDS.get('item_renumbernamesdirectkeys', False)
    keyCVT = DDS.get('item_renumbercvtsdirectkeys', False)
    keySLNFunc = DDS.get('item_subloggernamefunc', None)
    keySLNFuncNeedsSelf = DDS.get('item_subloggernamefuncneedsobj', False)
    keyPVS = DDS.get('item_prevalidatedglyphsetkeys', set())
    keyStorage = DDS.get('item_renumberstoragedirectkeys', False)
    keyPC = DDS.get('item_renumberpcsdirectkeys', False)
    keyPCorPoint = DDS.get('item_renumberpcsdirectkeys', False) or keyPC
    
    keyScales = any(DDS.get(s, False) for s in (
      'item_scaledirectkeys',
      'item_scaledirectkeysgrouped',
      'item_scaledirectkeysnoround'))
    
    valFunc = DDS.get('item_validatefunc', None)
    valFuncPartial = DDS.get('item_validatefunc_partial', None)
    kwArgsFunc = DDS.get('item_validatekwargsfunc', None)
    
    valDeep = DDS.get(
      'item_validatedeep',
      DDS.get('item_followsprotocol', False))
    
    valGlyph = DDS.get('item_renumberdirectvalues', False)
    valName = DDS.get('item_renumbernamesdirectvalues', False)
    valCVT = DDS.get('item_renumbercvtsdirectvalues', False)
    valPVS = DDS.get('item_prevalidatedglyphsetvalues', set())
    valStorage = DDS.get('item_renumberstoragedirectvalues', False)
    valPC = DDS.get('item_renumberpcsdirect', False)
    valPCorPoint = DDS.get('item_renumberpointsdirect', False) or valPC
    eccTag = DDS.get('item_enablecyclechecktag', None)
    
    valScales = any(DDS.get(s, False) for s in (
      'item_scaledirectvalues', 'item_scaledirectvaluesnoround'))
    
    if wholeFunc is not None:
        r = wholeFunc(self, logger=logger, **kwArgs)
    
    else:
        if wholeFuncPartial is not None:
            r = wholeFuncPartial(self, logger=logger, **kwArgs)
        
        valU16Func = functools.partial(
          valassist.isNumber_integer_unsigned,
          numBits = 16)
        
        valNumFunc = valassist.isNumber
        
        for key, obj in self.items():
            if keySLNFunc is not None:
                d2 = ({'obj': self} if keySLNFuncNeedsSelf else {})
                itemLogger = logger.getChild(keySLNFunc(key, **d2))
            
            elif keyDeep:
                itemLogger = logger.getChild("[%s]" % (key,))
            
            else:
                itemLogger = logger.getChild("[%r]" % (key,))
            
            if keyFunc is not None:
                r = keyFunc(key, logger=itemLogger, **kwArgs) and r
            
            elif key is not None:
                if keyDeep:
                    if hasattr(key, 'isValid'):
                        r = key.isValid(logger=itemLogger, **kwArgs) and r
                
                else:
                    if keyFuncPartial is not None:
                        rPart = keyFuncPartial(key, logger=itemLogger, **kwArgs)
                        r = rPart and r
                    
                    if keyGlyph:
                        if not valU16Func(
                          key,
                          logger = itemLogger,
                          label = "glyph index"):
                            
                            r = False
                        
                        elif (key not in keyPVS) and (key >= fontGlyphCount):
                            itemLogger.error((
                              DDS.get(
                                'item_validatecode_toolargeglyph',
                                'G0005'),
                              (key,),
                              "Glyph index %d too large."))
                            
                            r = False
                    
                    elif keyName:
                        if not valU16Func(
                          key,
                          logger = itemLogger,
                          label = "name table index"):
                            
                            r = False
                        
                        elif key not in namesInTable:
                            itemLogger.error((
                              DDS.get(
                                'item_validatecode_namenotintable',
                                'G0042'),
                              (key,),
                              "Name table index %d not present in "
                              "'name' table."))
                            
                            r = False
                    
                    elif keyCVT:
                        if not valU16Func(
                          key,
                          logger = itemLogger,
                          label = "CVT index"):
                            
                            r = False
                        
                        elif editor is not None:
                            if b'cvt ' not in editor:
                                itemLogger.error((
                                  DDS.get('item_validatecode_nocvt', 'G0030'),
                                  (key,),
                                  "CVT Index %d is being used, but the font "
                                  "has no Control Value Table."))
                                
                                r = False
                            
                            elif key >= len(editor[b'cvt ']):
                                itemLogger.error((
                                  DDS.get(
                                    'item_validatecode_toolargecvt',
                                    'G0029'),
                                  (key,),
                                  "CVT index %d is not defined."))
                                
                                r = False
                    
                    elif keyPCorPoint:
                        s = ("program counter" if keyPC else "point index")
                        
                        if not valU16Func(key, logger=itemLogger, label=s):
                            r = False
                    
                    elif keyStorage:
                        if not valU16Func(
                          key,
                          logger = itemLogger,
                          label = "storage index"):
                            
                            r = False
                        
                        elif key > maxStorage:
                            itemLogger.error((
                              'E6047',
                              (key, maxStorage),
                              "The storage index %d is greater than the "
                              "font's defined maximum of %d."))
                            
                            r = False
                    
                    elif keyScales:
                        if not valNumFunc(key, logger=itemLogger):
                            r = False
            
            if valFunc is not None:
                r = valFunc(obj, logger=itemLogger, **kwArgs) and r
            
            elif obj is not None:
                if valDeep:
                    if kwArgsFunc is not None:
                        d = kwArgs.copy()
                        d.update(kwArgsFunc(self, key))
                    else:
                        d = kwArgs
                    
                    if eccTag is not None:
                        dACC_copy = {x: y.copy() for x, y in dACC.items()}
                        eccDict = dACC_copy.setdefault(eccTag, {})
                    
                        if id(obj) not in eccDict:
                            eccDict[id(obj)] = obj
                    
                        else:
                            itemLogger.error((
                              'V0912',
                              (key,),
                              "Circular object reference for key '%s'"))
                        
                            return False  # aborts all other checks...
                    
                        d['activeCycleCheck'] = dACC_copy
                
                    if hasattr(obj, 'isValid'):
                        r = obj.isValid(logger=itemLogger, **d) and r
                
                else:
                    if valFuncPartial:
                        rPart = valFuncPartial(obj, logger=itemLogger, **kwArgs)
                        r = rPart and r
                    
                    if valGlyph:
                        if not valU16Func(
                          obj,
                          logger = itemLogger,
                          label = "glyph index"):
                            
                            r = False
                        
                        elif (obj not in valPVS) and (obj >= fontGlyphCount):
                            itemLogger.error((
                              DDS.get(
                                'item_validatecode_toolargeglyph',
                                'G0005'),
                              (obj,),
                              "Glyph index %d too large."))
                            
                            r = False
                    
                    elif valName:
                        if not valU16Func(
                          obj,
                          logger = itemLogger,
                          label = "name table index"):
                            
                            r = False
                        
                        elif obj not in namesInTable:
                            itemLogger.error((
                              DDS.get(
                                'item_validatecode_namenotintable',
                                'G0042'),
                              (obj,),
                              "Name table index %d not present in "
                              "'name' table."))
                            
                            r = False
                    
                    elif valCVT:
                        if not valU16Func(
                          obj,
                          logger = itemLogger,
                          label = "CVT index"):
                            
                            r = False
                        
                        elif editor is not None:
                            if b'cvt ' not in editor:
                                itemLogger.error((
                                  DDS.get('item_validatecode_nocvt', 'G0030'),
                                  (obj,),
                                  "CVT Index %d is being used, but the font "
                                  "has no Control Value Table."))
                                
                                r = False
                            
                            elif obj >= len(editor[b'cvt ']):
                                itemLogger.error((
                                  DDS.get(
                                    'item_validatecode_toolargecvt',
                                    'G0029'),
                                  (obj,),
                                  "CVT index %d is not defined."))
                                
                                r = False
                    
                    elif valPCorPoint:
                        s = ("program counter" if valPC else "point index")
                        
                        if not valU16Func(obj, logger=itemLogger, label=s):
                            r = False
                    
                    elif valStorage:
                        if not valU16Func(
                          obj,
                          logger = itemLogger,
                          label = "storage index"):
                            
                            r = False
                        
                        elif obj > maxStorage:
                            itemLogger.error((
                              'E6047',
                              (obj, maxStorage),
                              "The storage index %d is greater than the "
                              "font's defined maximum of %d."))
                            
                            r = False
                    
                    elif valScales:
                        if not valNumFunc(obj, logger=itemLogger):
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
    
    return r and rAttr

def M_items(self):
    """
    Returns a generator over (key, value) pairs.
    
    :return: Generator over (key, value) pairs
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(t.items())
    [('a', 'aaaaa'), ('f', 'fffff'), ('x', 'xxxxx'), ('z', 'zzzzz')]
    """
    
    return ((k, self[k]) for k in self)

def M_keys(self):
    """
    Returns a generator over keys.
    
    :return: Generator over keys
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(t.keys())
    ['a', 'f', 'x', 'z']
    """
    
    return (k for k in self)

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
        
    ``mergedKeyChanges``
        If an ``item_mergekeyfunc`` is present then changes from old to new
        will be noted in this dict.
    
    ``replaceWhole``
        True if any keys in other matching keys in ``self`` will cause the
        entire replacement of those values; no deep merging will occur for
        those values, even if ``item_mergedeep`` is specified. Default is False.
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    
    >>> b1 = Bottom({'b': 1, 'c': 2, 'd': 3, 'x': 4})
    >>> b2 = Bottom({'b': 8, 'c': 9, 'd': 10, 'e': 11})
    >>> t1 = Top({'a': b1, 'i': Bottom({'r': -50})})
    >>> t2 = Top({'a': b2, 'j': Bottom({'s': -200})})
    
    >>> t1.merged(t2, conflictPreferOther=False, replaceWhole=False).pprint()
    'a':
      'b': 1
      'c': 2
      'd': 3
      'e': 11
      'x': 4
    'i':
      'r': -50
    'j':
      's': -200
    
    >>> t1.merged(t2, conflictPreferOther=False, replaceWhole=True).pprint()
    'a':
      'b': 1
      'c': 2
      'd': 3
      'x': 4
    'i':
      'r': -50
    'j':
      's': -200
    
    >>> t1.merged(t2, conflictPreferOther=True, replaceWhole=False).pprint()
    'a':
      'b': 8
      'c': 9
      'd': 10
      'e': 11
      'x': 4
    'i':
      'r': -50
    'j':
      's': -200
    
    >>> t1.merged(t2, conflictPreferOther=True, replaceWhole=True).pprint()
    'a':
      'b': 8
      'c': 9
      'd': 10
      'e': 11
    'i':
      'r': -50
    'j':
      's': -200
    
    >>> def mergeFunc(a1, a2, **kwArgs):
    ...     newVal = int(str(a1) + str(a2))
    ...     return (a1 != newVal), newVal
    >>> class WithAttrs(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(attr_mergefunc = mergeFunc),
    ...         y = dict(attr_followsprotocol = True))
    >>> w1 = WithAttrs({'a': 1, 'b': 2}, x=6, y=b1)
    >>> w2 = WithAttrs({'a': 4, 'c': 9}, x=7, y=b2)
    >>> w1.merged(w2).pprint()
    'a': 4
    'b': 2
    'c': 9
    x: 67
    y:
      'b': 8
      'c': 9
      'd': 10
      'e': 11
      'x': 4
    
    >>> class TopNoConflicts(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_followsprotocol': True,
    ...       'dict_mergechecknooverlap': True}
    
    >>> t1NC = TopNoConflicts({'a': b1, 'i': Bottom({'r': -50})})
    >>> t2NC = TopNoConflicts({'a': b2, 'j': Bottom({'s': -200})})
    >>> err = t1NC.merged(t2NC)
    Traceback (most recent call last):
      ...
    ValueError: Key overlaps not permitted in this class!
    
    >>> def kmf(oldKey, inUse, **kwArgs):
    ...     newKey = oldKey + 1
    ...     while newKey in inUse:
    ...         newKey += 1
    ...     return newKey
    >>> class TestMergeKeys(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_pprintlabelpresort = True,
    ...         item_mergekeyfunc = kmf)
    >>> d1 = TestMergeKeys({4: 'a', 19: 'b', 20: 'd'})
    >>> d2 = TestMergeKeys({6: 'z', 19: 'r'})
    >>> mkc = {}
    >>> d1.merged(d2, mergedKeyChanges=mkc).pprint()
    4: a
    6: z
    19: b
    20: d
    21: r
    >>> mkc[19]
    21
    """
    
    DDS = self._DEFDSPEC
    
    deepValues = DDS.get(
      'item_mergedeep',
      DDS.get('item_followsprotocol', False))
    
    prefOther = kwArgs.get('conflictPreferOther', True)
    repWhole = kwArgs.get('replaceWhole', False)
    itemFunc = DDS.get('item_mergefunc', None)
    keyFunc = DDS.get('item_mergekeyfunc', None)
    keyChanges = kwArgs.pop('mergedKeyChanges', {})
    selfKeys = set(self)
    otherKeys = set(other)
    keysInCommon = selfKeys & otherKeys
    
    if keysInCommon and (keyFunc is not None):
        altOther = other.__copy__()
        
        # The following two lines are needed because __copy__() doesn't make
        # clones of _dAdded or _dOrig, and for our purposes we need that (and
        # making a deep copy would be too expensive in many cases).
        
        altOther._dOrig = altOther._dOrig.copy()
        altOther._dAdded = altOther._dAdded.copy()
        inUse = (selfKeys | otherKeys) - keysInCommon
        
        for key in keysInCommon:
            del altOther[key]
            newKey = keyFunc(key, inUse, **kwArgs)
            altOther[newKey] = other[key]
            keyChanges[key] = newKey
            inUse.add(newKey)
        
        other = altOther
        otherKeys = set(other)
        keysInCommon = set()
    
    mNew = dict(self)
    
    if DDS.get('dict_mergechecknooverlap', False):
        if keysInCommon:
            raise ValueError("Key overlaps not permitted in this class!")
    
    # In all cases, non-conflicting keys in other are simply added to self
    for key in otherKeys - selfKeys:
        mNew[key] = other[key]
    
    # Process the mapping's merges
    if itemFunc is not None:
        for key in keysInCommon:
            mNew[key] = itemFunc(self[key], other[key], **kwArgs)[1]
    
    elif prefOther:
        if repWhole:
            # prefer other and prohibit deep;
            # just move any conflicting keys from other into self
            for key in keysInCommon:
                mNew[key] = other[key]
        
        else:
            # prefer other and permit deep
            if deepValues:
                # deep call merged() on the values for the conflicting keys
                for key in keysInCommon:
                    selfValue = self[key]
                    
                    if selfValue is not None:
                        mNew[key] = selfValue.merged(other[key], **kwArgs)
            
            else:
                # we have no guidance about the values,
                # so just replace the conflicts
                for key in keysInCommon:
                    mNew[key] = other[key]
    
    else:
        if repWhole:
            # prefer self and prohibit deep
            # (so only non-conflicting keys will be added)
            pass  # already done above
        
        else:
            # prefer self and permit deep
            if deepValues:
                # deep call merged() on the values for the conflicting keys
                for key in keysInCommon:
                    selfValue = self[key]
                    
                    if selfValue is not None:
                        mNew[key] = selfValue.merged(other[key], **kwArgs)
            
            else:
                # do nothing, as self is preferred
                # and we have no other guidance
                pass
    
    # Now do attributes
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
        simply be kept unmodified. If False, the values will be deleted from
        the mapping, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumbernamesdirectvalues = True)
    >>> obj1 = Test1({'name1': 303, 'name2': 304})
    >>> e = _fakeEditor()
    >>> obj1.pprint(editor=e)
    'name1': 303 ('Required Ligatures On')
    'name2': 304 ('Common Ligatures On')
    
    >>> obj1.namesRenumbered({303:306, 304:307}).pprint(editor=e)
    'name1': 306 ('Regular')
    'name2': 307 ('Small Caps')
    """
    
    DDS = self._DEFDSPEC
    rDirectKey = DDS.get('item_renumbernamesdirectkeys', False)
    rDirectValue = DDS.get('item_renumbernamesdirectvalues', False)
    keepMissing = kwArgs.get('keepMissing', True)
    mNew = {}
    
    rDeepValue = DDS.get(
      'item_renumbernamesdeep',
      DDS.get('item_followsprotocol', False))
    
    rDeepKey = DDS.get(
      'item_renumbernamesdeepkeys',
      DDS.get('item_keyfollowsprotocol', False))
    
    for key, value in self.items():
        okToAdd = True
        
        if key is not None:
            if rDeepKey:
                key = key.namesRenumbered(oldToNew, **kwArgs)
                
                # If the key is a sequence with seq_fixedlength set, then any
                # attempt to renumber with keepMissing False may result in an
                # invalid object, which is now returned as None. We test for
                # that here.
                
                if key is None:
                    okToAdd = False
            
            elif rDirectKey:
                if key in oldToNew:
                    key = oldToNew[key]
                elif not keepMissing:
                    okToAdd = False
        
        if okToAdd and (value is not None):
            if rDeepValue:
                try:
                    boundMethod = value.namesRenumbered
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(value, **kwArgs).namesRenumbered
                
                value = boundMethod(oldToNew, **kwArgs)
            
            elif rDirectValue:
                if value in oldToNew:
                    value = oldToNew[value]
                elif not keepMissing:
                    okToAdd = False
        
        if okToAdd:
            mNew[key] = value
    
    # Now do attributes
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberpcsdirect = True,
    ...         item_renumberpcsdirectkeys = True)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> obj = Test1({5: 12, 50: 100})
    >>> print(obj.pcsRenumbered(mapData, infoString="testcode"))
    {5: 14, 53: 106}
    """
    
    DDS = self._DEFDSPEC
    thisMap = mapData.get(kwArgs.get('infoString', None), [])
    
    if thisMap:
        mNew = {}
        
        deep = DDS.get(
          'item_renumberpcsdeep',
          DDS.get('item_followsprotocol', False))
        
        direct = DDS.get('item_renumberpcsdirect', False)
        deepKeys = DDS.get('item_renumberpcsdeepkeys', False)
        directKeys = DDS.get('item_renumberpcsdirectkeys', False)
        
        for key, obj in self.items():
            if key is not None:
                if deepKeys:
                    key = key.pcsRenumbered(mapData, **kwArgs)
                
                elif directKeys:
                    delta = 0
                    
                    for threshold, newDelta in thisMap:
                        if key < threshold:
                            break
                        
                        delta = newDelta
                    
                    key += delta
            
            if obj is not None:
                if deep:
                    obj = obj.pcsRenumbered(mapData, **kwArgs)
                
                elif direct:
                    delta = 0
                    
                    for threshold, newDelta in thisMap:
                        if obj < threshold:
                            break
                        
                        delta = newDelta
                    
                    obj += delta
            
            mNew[key] = obj
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
        the mapping, or (if attributes or an index map) will be changed to
        ``None``.
    
    In the following class, "KIGI" means "key is glyph index".
    
    In the following class, the key is the glyph index
    >>> class Bottom_KIGI(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_renumberpointsdirect = True)
    >>> myMapData = {2: {5: 6, 11: 12}, 4: {9: 25}}
    >>> b = Bottom_KIGI({0: 4, 2: 11, 3: 6, 4: 9, 5: 15})
    >>> print(b.pointsRenumbered(myMapData))
    {0: 4, 2: 12, 3: 6, 4: 25, 5: 15}
    
    >>> class Bottom_Direct(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_pprintlabelpresort = True,
    ...         item_renumberpointsdirect = True)
    >>> b = Bottom_Direct(zip(range(13), range(13)))
    >>> b.pointsRenumbered(myMapData, glyphIndex=2).pprint()
    0: 0
    1: 1
    2: 2
    3: 3
    4: 4
    5: 6
    6: 6
    7: 7
    8: 8
    9: 9
    10: 10
    11: 12
    12: 12
    
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_renumberpointsdeep = True)
    >>> b1 = Bottom_KIGI({0: 4, 2: 11, 3: 6, 4: 9, 5: 15})
    >>> b2 = Bottom_Direct(zip(range(13), range(13)))
    >>> t = Top({5: b1, 8: None, 9: b2})
    
    In the following the glyphIndex is only used by b2
    >>> t2 = t.pointsRenumbered(myMapData, glyphIndex=2)
    >>> print(t2[5])
    {0: 4, 2: 12, 3: 6, 4: 25, 5: 15}
    >>> t2[9].pprint()
    0: 0
    1: 1
    2: 2
    3: 3
    4: 4
    5: 6
    6: 6
    7: 7
    8: 8
    9: 9
    10: 10
    11: 12
    12: 12
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         pointNumber = dict(attr_renumberpointsdirect = True))
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         bottom = dict(
    ...             attr_followsprotocol = True,
    ...             attr_strneedsparens = True))
    >>> b = Bottom({}, pointNumber=10)
    >>> t = Top({}, bottom=b)
    >>> print(t)
    {}, bottom = ({}, pointNumber = 10)
    >>> myMap = {5: {10: 20}, 20: {10: 11}}
    >>> t2 = t.pointsRenumbered(myMap, glyphIndex=5)
    >>> print(t2)
    {}, bottom = ({}, pointNumber = 20)
    >>> print(t2.pointsRenumbered(myMap, glyphIndex=49))
    {}, bottom = ({}, pointNumber = 20)
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberpointsdirect = True,
    ...         item_renumberpointsdirectkeys = True)
    >>> d = Test1({10: 35, 12: 10, 15: 88})
    >>> mapData = {150: {10: 1, 12: 2, 15: 3, 35: 4}}
    >>> print(d.pointsRenumbered(mapData, glyphIndex=150))
    {1: 4, 2: 1, 3: 88}
    """
    
    DDS = self._DEFDSPEC
    
    deep = DDS.get(
      'item_renumberpointsdeep',
      DDS.get('item_followsprotocol', False))
    
    direct = DDS.get('item_renumberpointsdirect', False)
    deepKeys = DDS.get('item_renumberpointsdeepkeys', False)
    directKeys = DDS.get('item_renumberpointsdirectkeys', False)
    
    if (
      DDS.get('item_renumberdirectkeys', False) or
      DDS.get('item_keyisoutputglyph', False)):
        
        mNew = dict(self)
        
        if deep:
            for key, obj in self.items():
                if obj is not None:
                    kwArgs['glyphIndex'] = key
                    mNew[key] = obj.pointsRenumbered(mapData, **kwArgs)
        
        elif direct:
            for key, obj in self.items():
                thisMap = mapData.get(key, {})
                
                if obj in thisMap:
                    obj = thisMap[obj]
                
                mNew[key] = obj
    
    else:  # key is not glyph index
        mNew = dict()
        thisMap = mapData.get(kwArgs.get('glyphIndex', None), {})
        
        for key, obj in self.items():
            if key is not None:
                if deepKeys:
                    key = key.pointsRenumbered(mapData, **kwArgs)
                elif directKeys:
                    key = thisMap.get(key, key)
            
            if obj is not None:
                if deep:
                    obj = obj.pointsRenumbered(mapData, **kwArgs)
                elif direct:
                    obj = thisMap.get(obj, obj)
            
            mNew[key] = obj
    
    # Now do attributes
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

def M_pop(self, key, *args):
    """
    Pops (removes) an item from ``self``.
    
    :param key: The key to remove
    :param args: Remaining positional arguments; only the ``[0]`` entry is used
        as a default if the ``key`` is not present
    :return: ``self[key]`` or ``args[0]``
    :raises KeyError: if ``key`` is not present and no default is provided
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> len(t)
    3
    >>> sorted([t.pop('a'), t.pop('f'), t.pop('z')])
    ['aaaaa', 'fffff', 'zzzzz']
    >>> len(t)
    0
    >>> t.pop('x', 'yyy')
    'yyy'
    >>> t.pop('x')
    Traceback (most recent call last):
      ...
    KeyError: 'x'
    """
    
    if key in self:
        obj = self[key]
        del self[key]
        return obj
    
    if len(args) == 1:
        return args[0]
    
    raise KeyError(key)

def M_popitem(self):
    """
    Pops (removes) a (key, value) pair from ``self``. Added keys will be
    exhausted before original keys start to get popped.
    
    :return: A (key, value) pair
    :raises KeyError: if the dict is empty
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a'])))
    >>> t.b = 'bbbbb'
    >>> sorted([t.popitem(), t.popitem()])
    [('a', 'aaaaa'), ('b', 'bbbbb')]
    >>> t.popitem()
    Traceback (most recent call last):
      ...
    KeyError: 'popitem() dictionary is empty'
    """
    
    if self._dAdded:
        key = next(iter(self._dAdded))
        return (key, self.pop(key))
    
    if self._dOrig:
        key = next(iter(self._dOrig))
        return (key, self.pop(key))
    
    raise KeyError("popitem() dictionary is empty")

def M_pprint(self, **kwArgs):
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
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...       item_followsprotocol = True,
    ...       item_renumberdirectkeys = True,
    ...       item_usenamerforstr = True)
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> Top(((15, b1), (30, b2))).pprint()
    15:
      'a': 14
      'b': 9
      'c': 22
    30:
      'a': 12
      'd': 29
    >>> Top(((15, b1), (30, b2))).pprint(namer=namer.testingNamer())
    xyz16:
      'a': 14
      'b': 9
      'c': 22
    xyz31:
      'a': 12
      'd': 29
    
    >>> class Grouped(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'dict_pprintfunc': pp.PP.mapping_grouped}
    >>> d = Grouped({3: 8, 4: 8, 5: 8, 6: None, 9: None, 10: 6, 11: 6})
    >>> d.pprint(label="Grouped data")
    Grouped data:
      [3-5]: 8
      [6, 9]: (no data)
      [10-11]: 6
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_followsprotocol': True,
    ...       'item_pprintlabelfunc': (lambda x: "Top key %r" % (x,))}
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = {
    ...         'attr_initfunc': lambda: 15,
    ...         'attr_label': "Count"},
    ...       someDict = {
    ...         'attr_followsprotocol': True,
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data"})
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> obj = DPA({3: 16, 5: -2}, someDict=t, someNumber=5)
    >>> obj.pprint(label="Here are the data")
    Here are the data:
      3: 16
      5: -2
      Extra data:
        Top key 15:
          'a': 14
          'b': 9
          'c': 22
        Top key 30:
          'a': 12
          'd': 29
      Count: 5
    
    >>> class Top2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True,
    ...         item_renumberdirectkeys = True,
    ...         item_usenamerforstr = True)
    >>> t = Top2(((15, b1), (30, b2)))
    >>> nm = namer.testingNamer()
    >>> obj = DPA({3: 16, 5: -2}, someDict=t, someNumber=5)
    >>> obj.pprint(label="Here are the data", namer=nm)
    Here are the data:
      3: 16
      5: -2
      Extra data:
        xyz16:
          'a': 14
          'b': 9
          'c': 22
        xyz31:
          'a': 12
          'd': 29
      Count: 5
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_pprintlabelpresort': True}
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': False}}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_pprintlabelpresort': True}
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': True}}
    >>> Test1({3: 17, 20: -1}).pprint()
    3: 17
    20: -1
    s: fred
    >>> Test2({3: 17, 20: -1}).pprint()
    3: 17
    20: -1
    s: 'fred'
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> Test3({}).pprint(label="Note x is suppressed")
    Note x is suppressed:
      y: 5
    >>> Test3({}, x=4).pprint(label="No suppression here")
    No suppression here:
      x: 4
      y: 5
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_pprintlabelpresortreverse': True}
    >>> Test4({2: 'a', 5: 'b', 10: 'c'}).pprint()
    10: c
    5: b
    2: a
    
    >>> class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     attrSpec = {
    ...       'order': {
    ...         'attr_initfunc': (lambda: 0),
    ...         'attr_label': "Key order"}}
    ...     __hash__ = tuple.__hash__
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_pprintlabelpresortfunc': (lambda obj: (obj[0], obj.order))}
    >>> k1 = Key([25, 30], order=1)
    >>> k2 = Key([25, 40], order=0)
    >>> k3 = Key([30, 40], order=0)
    >>> d = Test5({k1: 'a', k2: 'b', k3: 'c'})
    >>> d.pprint()  # note sort order: first key value, then order attribute
    Key((25, 40), order=0): b
    Key((25, 30), order=1): a
    Key((30, 40), order=0): c
    
    >>> class Test7(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         dict_ppoptions = dict(noDataString = "nuffin"))
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(attr_ppoptions = {'noDataString': "bubkes"}))
    >>> Test7({18: None}).pprint()
    18: nuffin
    a: (no data)
    b: bubkes
    
    >>> class Test8(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumbernamesdirectvalues = True)
    >>> obj8 = Test8({'name1': 303, 'name2': 304})
    >>> obj8.pprint()
    'name1': 303
    'name2': 304
    >>> e = _fakeEditor()
    >>> obj8.pprint(editor=e)
    'name1': 303 ('Required Ligatures On')
    'name2': 304 ('Common Ligatures On')
    
    >>> class Test11(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict()
    >>> class Test12(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True)
    >>> obj11_1 = Test11([5, 2, 16, 23, 9])
    >>> obj11_2 = Test11([19, 19])
    >>> obj12 = Test12({'a': obj11_1, 'b': obj11_1, 'c': obj11_2, 'd': obj11_1})
    >>> obj12.pprint()
    'a':
      0: 5
      1: 2
      2: 16
      3: 23
      4: 9
    'b':
      0: 5
      1: 2
      2: 16
      3: 23
      4: 9
    'c':
      0: 19
      1: 19
    'd':
      0: 5
      1: 2
      2: 16
      3: 23
      4: 9
    
    >>> obj12.pprint(elideDuplicates=True)
    OBJECT 0
    'a':
      0: 5
      1: 2
      2: 16
      3: 23
      4: 9
    'b': (duplicate; see OBJECT 0 above)
    OBJECT 1
    'c':
      0: 19
      1: 19
    'd': (duplicate; see OBJECT 0 above)
    """
    
    DDS = self._DEFDSPEC
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    pd = p.__dict__
    ppSaveDict = {}
    
    for key, value in DDS.get('dict_ppoptions', {}).items():
        ppSaveDict[key] = pd[key]
        pd[key] = value
    
    printWholeFunc = DDS.get('dict_pprintfunc', None)
    kwArgs['useRepr'] = DDS.get('item_strusesrepr', False)
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if elideDups is True:
        elideDups = {}  # object ID to serial number
        kwArgs['elideDuplicates'] = elideDups
    
    if printWholeFunc is not None:
        printWholeFunc(p, self)
        
        while ppSaveDict:
            key, value = ppSaveDict.popitem()
            pd[key] = value
        
        return
    
    if DDS.get('item_usenamerforstr', False):
        nm = kwArgs.get('namer', self.getNamer())
    else:
        nm = None
    
    keyStringsList = dictkeyutils.makeKeyStringsList(self, DDS, nm)
    printItemFunc = DDS.get('item_pprintfunc', None)
    
    if printItemFunc is not None:
        if nm is not None:
            kwArgs['bestNameFunc'] = nm.bestNameForGlyphIndex
        
        for ks, key in keyStringsList:
            printItemFunc(p, self[key], ks, **kwArgs)
    
    elif nm is not None:
        self._pprint_namer(p, nm, keyStringsList, **kwArgs)
    
    else:
        self._pprint_nonamer(p, keyStringsList, **kwArgs)
    
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
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True,
    ...         item_renumberdirectkeys = True,
    ...         item_usenamerforstr = True)
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t1 = Top(((15, b1), (30, b2)))
    >>> t2 = t1.__deepcopy__()
    >>> t2[15]['b'] = 90
    >>> t2[30]['z'] = 144
    >>> t2.pprint_changes(t1)
    Changed records:
      15 changed from:
        'a': 14
        'b': 9
        'c': 22
      to:
        'a': 14
        'b': 90
        'c': 22
      30 changed from:
        'a': 12
        'd': 29
      to:
        'a': 12
        'd': 29
        'z': 144
    >>> n = namer.testingNamer()
    >>> t2.pprint_changes(t1, namer=n)
    Changed records:
      'xyz16' changed from:
        'a': 14
        'b': 9
        'c': 22
      to:
        'a': 14
        'b': 90
        'c': 22
      'xyz31' changed from:
        'a': 12
        'd': 29
      to:
        'a': 12
        'd': 29
        'z': 144
    
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = {
    ...         'attr_initfunc': (lambda: 15),
    ...         'attr_label': "Count"},
    ...       someDict = {
    ...         'attr_followsprotocol': True,
    ...         'attr_initfunc': Top,
    ...         'attr_label': "Extra data"})
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> obj1 = DPA({3: 16, 5: -2}, someDict=t, someNumber=5)
    >>> obj2 = obj1.__deepcopy__()
    >>> obj2[3] += 200
    >>> obj2[29] = 28
    >>> obj2.someDict[30]['a'] += 40
    >>> obj2.someNumber = 38
    >>> nm = namer.testingNamer()
    >>> obj2.pprint_changes(obj1, namer=nm)
    Added records:
      29: 28
    Changed records:
      3: from 16 to 216
    Extra data:
      Changed records:
        'xyz31' changed from:
          'a': 12
          'd': 29
        to:
          'a': 52
          'd': 29
    Count changed from 5 to 38
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    >>> Test({}, x=1, y=2, z=3).pprint_changes(Test({}, x=1, y=2, z=2000))
    """
    
    if self == prior:
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    DDS = self._DEFDSPEC
    f = DDS.get('dict_pprintdifffunc', None)
    
    deep = DDS.get(
      'item_pprintdiffdeep',
      DDS.get('item_followsprotocol', False))
    
    useRepr = DDS.get('item_strusesrepr', False)
    keyIsGlyphIndex = DDS.get('item_renumberdirectkeys', False)
    valueIsGlyphIndex = DDS.get('item_renumberdirectvalues', False)
    
    if DDS.get('item_usenamerforstr', False):
        nm = kwArgs.get('namer', self.getNamer())
    else:
        nm = None
    
    origSelf = self
    origPrior = prior
    
    # Rather than changing the diff_mapping* methods in PP, we just
    # construct alternate dicts with the keys and/or values mapped to
    # their names, if they are glyph indices and so indicated.
    
    if (keyIsGlyphIndex or valueIsGlyphIndex) and (nm is not None):
        nmbf = nm.bestNameForGlyphIndex
        d = {}
        
        for key, value in self.items():
            if keyIsGlyphIndex:
                key = nmbf(key)
            
            if valueIsGlyphIndex:
                value = nmbf(value)
            
            d[key] = value
        
        self = d
        d = {}
        
        for key, value in prior.items():
            if keyIsGlyphIndex:
                key = nmbf(key)
            
            if valueIsGlyphIndex:
                value = nmbf(value)
            
            d[key] = value
        
        prior = d
    
    if f:
        f(p, self, prior)
    elif deep:
        p.diff_mapping_deep(self, prior, useRepr=useRepr)
    else:
        p.diff_mapping(self, prior, useRepr=useRepr)
    
    attrhelper.M_pprintChanges(
      origSelf,
      origPrior.__dict__,
      p,
      kwArgs.get('namer', origSelf.getNamer()),
      **kwArgs)

def M_reallyHas(self, key):
    """
    Determines whether ``key`` is substantially present in ``self``.
    
    :param key: The key being sought
    :return: True if ``key`` is both present and its value is not ``None``
    :rtype: bool
    
    Note that the value associated with ``key`` might not be living; it may
    just be a binary string.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k,e: e['prefix'] + str(k)))
    >>> t = Test(
    ...   creationExtras = {
    ...     'oneTimeKeyIterator': iter([1, 2, 4]),
    ...     'prefix': "Obj "})
    >>> t[19] = "Object nineteen"
    >>> t[20] = None
    >>> t.reallyHas(1), t.reallyHas(3), t.reallyHas(19), t.reallyHas(20)
    (True, False, True, False)
    """
    
    if self._DEFDSPEC.get('item_keyisbytes', False):
        if not isinstance(key, bytes):
            key = key.encode('ascii')
    
    return (
      ((key in self._dOrig) and (self._dOrig[key] is not None)) or
      ((key in self._dAdded) and (self._dAdded[key] is not None)))

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    
    The following ``kwArgs`` are supported:
    
    ``editor``
        This is required, and should be an
        :py:class:`~fontio3.fontedit.Editor`-class object.
    
    >>> def wholeInPlaceFunc(oldDict, **kwArgs):
    ...     cmpCopy = dict(oldDict)
    ...     oldDict.clear()
    ...     oldDict[1] = 'a'
    ...     return (dict(oldDict) != cmpCopy, oldDict)
    >>> def wholeReplaceFunc(oldDict, **kwArgs):
    ...     r = {1: 'a'}
    ...     return (r != dict(oldDict), r)
    >>> def indivInPlaceFunc(obj, **kwArgs):
    ...     obj[0] *= 2
    ...     return (bool(obj[0]), obj)
    >>> def indivReplaceFunc(obj, **kwArgs):
    ...     return (bool(obj), [obj[0] * 2] + obj[1:])
    >>> class Bottom_WholeInPlace(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(dict_recalculatefunc = wholeInPlaceFunc)
    >>> class Bottom_WholeReplace(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(dict_recalculatefunc = wholeReplaceFunc)
    >>> class Bottom_IndivInPlace(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_recalculatefunc = indivInPlaceFunc)
    >>> class Bottom_IndivReplace(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_recalculatefunc = indivReplaceFunc)
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_followsprotocol = True,
    ...         item_pprintlabelpresort = True)
    >>> b1 = Bottom_WholeInPlace({1: 10, 6: -20})
    >>> b2 = Bottom_WholeReplace({1: 10, 6: -20})
    >>> b3 = Bottom_IndivInPlace({0: [4], 3: [6]})
    >>> b4 = Bottom_IndivReplace({0: [4], 3: [6]})
    >>> t = Top({3: b1, 5: b2, 6: b3, 11: b4})
    >>> t.pprint()
    3:
      1: 10
      6: -20
    5:
      1: 10
      6: -20
    6:
      0: [4]
      3: [6]
    11:
      0: [4]
      3: [6]
    
    >>> tRecalc = t.recalculated()
    >>> tRecalc.pprint()
    3:
      1: a
    5:
      1: a
    6:
      0: [8]
      3: [12]
    11:
      0: [8]
      3: [12]
    
    >>> t[6][0] is tRecalc[6][0], t[11][0] is tRecalc[11][0]
    (True, False)
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_recalculatefunc = (
    ...               lambda x, **k:
    ...               (True, 2 * x - k['adj']))))
    >>> t = Test({4: 'y'}, x=9)
    >>> print(t)
    {4: y}, x = 9
    >>> print(t.recalculated(adj=4))
    {4: y}, x = 14
    
    >>> def _fp(d, **kwArgs):
    ...     d2 = {}
    ...     for k, n in d.items():
    ...         if n >= 0:
    ...             d2[k] = n
    ...     return dict(d) != d2, d2
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_recalculatefunc = (
    ...           lambda n, **k:
    ...           (n != round(n), round(n))),
    ...         dict_recalculatefunc_partial = _fp)
    >>> obj = Test2({'a': -4, 'b': 0.75, 'e': 12})
    >>> obj.recalculated() == Test2({'b': 1, 'e': 12})
    True
    """
    
    DDS = self._DEFDSPEC
    fWholeAttr = DDS.get('dict_recalculatefunc_withattrs', None)
    fWhole = DDS.get('dict_recalculatefunc', None)
    mNew = dict(self)
    
    if fWholeAttr is not None:
        changed, mNew = fWholeAttr(self, **kwArgs)
        return (mNew if changed else self)
    
    if fWhole is not None:
        changed, mNew = fWhole(self, **kwArgs)
    
    else:
        fWholePartial = DDS.get('dict_recalculatefunc_partial', None)
        fIndiv = DDS.get('item_recalculatefunc', None)
        dOD = DDS.get('dict_orderdependencies', {})
        
        if fWholePartial is not None:
            changed, mNew = fWholePartial(self, **kwArgs)
        
        if fIndiv is not None:
            it = utilities.constrainedOrderItems(mNew, dOD)
            
            for k, obj in it:
                if obj is not None:
                    changed, mNew[k] = fIndiv(obj, **kwArgs)
        
        elif DDS.get(
          'item_recalculatedeep',
          DDS.get('item_followsprotocol', False)):
            
            it = utilities.constrainedOrderItems(mNew, dOD)
            
            for k, obj in it:
                if obj is not None:
                    mNew[k] = obj.recalculated(**kwArgs)
    
    # Now do attributes
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result. Because deferreddicts are not the same
    # as regular dicts, there are two possible branches here. If mNew was made
    # as the result of a dict_recalculatefunc or something similar, then it may
    # already have its own copies of the _creationExtras and other custom
    # attributes. If it was created by accretion, though, it may not have these
    # custom fields. So the logic here looks and either copies self's custom
    # fields (if they're not in mNew), or leaves them alone if they're already
    # there.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    if (
      (not hasattr(mNew, '__dict__')) or
      ('_creationExtras' not in mNew.__dict__)):
        
        r = self.__copy__()
        r._dAdded = {}
        r._dOrig = {}
        r.update(mNew)
    
    else:
        r = mNew
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
    
    >>> class ScaleKeys(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_scaledirectkeys = True,
    ...         item_strusesrepr = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleKeysGroup(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_scaledirectkeysgrouped = True,
    ...         item_strusesrepr = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleValues(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_scaledirectvalues = True)
    
    >>> class ScaleBoth(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_scaledirectvalues = True,
    ...         item_scaledirectkeys = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleBothGroup(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_scaledirectvalues = True,
    ...         item_scaledirectkeysgrouped = True,
    ...         item_pprintlabelpresort = True,
    ...         item_python3rounding = True)
    
    >>> k = ScaleKeys({22: 'a', 24: 'b', None: 'c'})
    >>> print(k.scaled(1.5))
    {33: 'a', 36: 'b', None: 'c'}
    >>> print(ScaleKeys({22: 'a', 24: 'b'}).scaled(0.1))
    Traceback (most recent call last):
      ...
    KeyError: 2
    >>> kg = ScaleKeysGroup({22: 'a', 24: 'b', None: 'c'})
    >>> print(kg.scaled(0.1))  # note that list ordering is not defined!
    {2: ['b', 'a'], None: 'c'}
    >>> v = ScaleValues({'a': 22, 'b': 24, 'c': None})
    >>> print(v.scaled(1.5))
    {'a': 33, 'b': 36, 'c': None}
    >>> b = ScaleBoth({22: 4, 24: 6, None: 8, 26: None})
    >>> print(b.scaled(1.5))
    {33: 6, 36: 9, 39: None, None: 12}
    >>> print(ScaleBoth({22: 4, 24: 6, None: 8, 26: None}).scaled(0.1))
    Traceback (most recent call last):
      ...
    KeyError: 2
    >>> bg = ScaleBothGroup({22: 4, 24: 6, None: 8, 26: None})
    >>> print(bg.scaled(0.125))
    {3: [1, None, 0], None: 1}
    
    >>> class Bottom(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_scaledirectvalues': True,
    ...       'item_strusesrepr': True}
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {
    ...       'item_scaledirectkeys': True,
    ...       'item_strusesrepr': True}
    ...     attrSpec = {'v': {'attr_followsprotocol': True}}
    >>> t = Top({22: 'a', 24: 'b'}, v=Bottom({'c': 80, 'd': 100}))
    >>> print(t)
    {22: 'a', 24: 'b'}, v = {'c': 80, 'd': 100}
    >>> print(t.scaled(1.5))
    {33: 'a', 36: 'b'}, v = {'c': 120, 'd': 150}
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...    deferredDictSpec = dict(
    ...         item_pprintlabelpresort = True,
    ...         item_scaledirectkeys = True,
    ...         item_scaledirectvalues = True,
    ...         item_keyrepresentsx = True,
    ...         item_valuerepresentsy = True)
    
    >>> print(Test1({4.0: 6.0, 10.0: -20.0}).scaled(0.5))
    {2.0: 3.0, 5.0: -10.0}
    >>> print(Test1({4.0: 6.0, 10.0: -20.0}).scaled(0.5, scaleOnlyInX=True))
    {2.0: 6.0, 5.0: -20.0}
    >>> print(Test1({4.0: 6.0, 10.0: -20.0}).scaled(0.5, scaleOnlyInY=True))
    {4.0: 3.0, 10.0: -10.0}
    """
    
    if scaleFactor == 1.0:
        return self.__deepcopy__()
    
    scaleOnlyInX = kwArgs.get('scaleOnlyInX', False)
    scaleOnlyInY = kwArgs.get('scaleOnlyInY', False)
    
    if scaleOnlyInX and scaleOnlyInY:
        scaleOnlyInX = scaleOnlyInY = False
    
    DDS = self._DEFDSPEC
    
    rDeepValue = DDS.get(
      'item_scaledeep',
      DDS.get('item_followsprotocol', False))
    
    rDVR = DDS.get('item_scaledirectvalues', False)
    rDVNR = DDS.get('item_scaledirectvaluesnoround', False)
    rDKER = DDS.get('item_scaledirectkeys', False)
    rDKENR = DDS.get('item_scaledirectkeysnoround', False)
    rDKGR = DDS.get('item_scaledirectkeysgrouped', False)
    rDirectValue = rDVR or rDVNR
    rDirectKeyRaise = rDKER or rDKENR
    rDirectKeyGroup = rDKGR
    rKX = DDS.get('item_keyrepresentsx', False)
    rKY = DDS.get('item_keyrepresentsy', False)
    rVX = DDS.get('item_valuerepresentsx', False)
    rVY = DDS.get('item_valuerepresentsy', False)
    doKey = not ((scaleOnlyInX and rKY) or (scaleOnlyInY and rKX))
    doValue = not((scaleOnlyInX and rVY) or (scaleOnlyInY and rVX))
    
    if rDKENR:
        keyRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfunckeys' in DDS:
        keyRoundFunc = DDS['item_roundfunckeys']
    elif DDS.get('item_python3rounding', False):
        keyRoundFunc = utilities.newRound
    else:
        keyRoundFunc = utilities.oldRound
    
    if rDVNR:
        valueRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfuncvalues' in DDS:
        valueRoundFunc = DDS['item_roundfuncvalues']
    elif DDS.get('item_python3rounding', False):
        valueRoundFunc = utilities.newRound
    else:
        valueRoundFunc = utilities.oldRound
    
    mNew = {}
    
    if rDirectKeyGroup or rDirectKeyRaise:
        collisionKeys = set()
        
        for key, obj in self.items():
            if key:  # not None and nonzero, means it scales
                if doKey:
                    key = keyRoundFunc(scaleFactor * key, castType=type(key))
            
            if doValue:
                if rDeepValue and (obj is not None):
                    obj = obj.scaled(scaleFactor, **kwArgs)
                
                elif rDirectValue and obj:
                    obj = valueRoundFunc(scaleFactor * obj, castType=type(obj))
            
            if key not in mNew:
                mNew[key] = obj
            
            elif rDirectKeyRaise:
                raise KeyError(key)
            
            elif key in collisionKeys:
                mNew[key].append(obj)
            
            else:
                collisionKeys.add(key)
                
                if rDeepValue:
                    mNew[key] = _ScaleListDeep([mNew[key], obj])
                else:  # this works irrespective of rDirectValue
                    mNew[key] = [mNew[key], obj]
    
    elif rDeepValue or rDirectValue:
        if doValue:
            for key, obj in self.items():
                if rDeepValue and (obj is not None):
                    obj = obj.scaled(scaleFactor, **kwArgs)
                
                elif rDirectValue and obj:
                    obj = valueRoundFunc(scaleFactor * obj, castType=type(obj))
                
                mNew[key] = obj
        
        else:
            mNew.update(self)
    
    else:
        mNew.update(self)
    
    # Now do attributes
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

def M_setdefault(self, key, default=None):
    """
    Returns a value from the object for the specified key. If the key is not
    present, sets the object to the specified value.
    
    :param key: The key being sought
    :param default: The default to use if ``key`` is not present
    :return: ``self[key]``
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t.setdefault('a', 'default')
    'aaaaa'
    >>> len(t)
    3
    >>> t.setdefault('b', 'default')
    'default'
    >>> len(t)
    4
    """
    
    if key not in self:
        self[key] = default
    
    return self[key]

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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberstoragedirectkeys = True,
    ...         item_renumberstoragedirectvalues = True)
    >>> d = Test1({10: 20, None: 30, 40: None, 50: 60})
    >>> print(d.storageRenumbered(storageDelta=5))
    {15: 25, 45: None, 55: 65, None: 35}
    >>> print(d.storageRenumbered(oldToNew={40: 10, 10: 40}))
    {10: None, 40: 20, 50: 60, None: 30}
    >>> print(d.storageRenumbered(oldToNew={40: 10, 10:40}, keepMissing=False))
    {10: None}
    >>> f = (lambda n,**k: (n if n % 4 else n + 900))
    >>> print(d.storageRenumbered(storageMappingFunc=f))
    {10: 920, 50: 960, 940: None, None: 30}
    """
    
    DDS = self._DEFDSPEC
    
    deepKeys = DDS.get(
      'item_renumberstoragedeepkeys',
      DDS.get('item_keyfollowsprotocol', False))
    
    deepValues = DDS.get(
      'item_renumberstoragedeep',
      DDS.get('item_followsprotocol', False))
    
    directKeys = DDS.get('item_renumberstoragedirectkeys', False)
    directValues = DDS.get('item_renumberstoragedirectvalues', False)
    
    if deepKeys or deepValues or directKeys or directValues:
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
        
        mNew = {}
        
        for key, value in self.items():
            okToAdd = True
            
            if key is not None:
                if deepKeys:
                    key = key.storageRenumbered(**kwArgs)
                    
                    # If the key is a sequence with seq_fixedlength set, then
                    # any attempt to renumber with keepMissing False may result
                    # in an invalid object, which is now returned as None. We
                    # test for that here.
                    
                    if key is None:
                        okToAdd = False
                
                elif directKeys:
                    key = storageMappingFunc(key, **kwArgs)
                    
                    if key is None:
                        okToAdd = False
            
            if okToAdd and (value is not None):
                if deepValues:
                    value = value.storageRenumbered(**kwArgs)
                
                elif directValues:
                    value = storageMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

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
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_valuerepresentsx = True)
    >>> print(Test1({'a': 4, 'b': -3}).transformed(m))
    {'a': -15, 'b': 6}
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_valuerepresentsy = True)
    >>> print(Test2({'a': 4, 'b': -3}).transformed(m))
    {'a': 12, 'b': -2}
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeyvaluepairs = True,
    ...         item_valuerepresentsy = True)
    >>> print(Test3({1: 2, -3: -4}).transformed(m))
    {-6: 8, 6: -4}
    
    Key collisions normally generate KeyErrors:
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_keyrepresentsx = True)
    >>> print(Test4({1.21: 'a', 1.22: 'b'}).transformed(m))
    Traceback (most recent call last):
      ...
    KeyError: -7.0
    
    Collisions can be avoided either by not rounding, or by grouping:
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeysnoround = True)
    >>> print(Test5({1.21: 'a', 1.22: 'b'}).transformed(m))
    {-6.63: a, -6.66: b}
    
    >>> class Test6(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeysgrouped = True)
    >>> print(Test6({1.21: 'a', 1.22: 'b'}).transformed(m))
    {-7.0: ['a', 'b']}
    """
    
    DDS = self._DEFDSPEC
    
    if DDS.get('item_transformkeysnoround', False):
        keyRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfunckeys' in DDS:
        keyRoundFunc = DDS['item_roundfunckeys']
    elif DDS.get('item_python3rounding', False):
        keyRoundFunc = utilities.newRound
    else:
        keyRoundFunc = utilities.oldRound
    
    if DDS.get('item_transformvaluesnoround', False):
        valueRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfuncvalues' in DDS:
        valueRoundFunc = DDS['item_roundfuncvalues']
    elif DDS.get('item_python3rounding', False):
        valueRoundFunc = utilities.newRound
    else:
        valueRoundFunc = utilities.oldRound
    
    mp = matrixObj.mapPoint
    flagKeyFollowsProtocol = DDS.get('item_keyfollowsprotocol', False)
    flagValueFollowsProtocol = DDS.get('item_followsprotocol', False)
    flagLinked = DDS.get('item_transformkeyvaluepairs', False)
    flagKeyIsX = DDS.get('item_keyrepresentsx', False)
    flagKeyIsY = DDS.get('item_keyrepresentsy', False)
    flagValueIsX = DDS.get('item_valuerepresentsx', False)
    flagValueIsY = DDS.get('item_valuerepresentsy', False)
    
    mNew = collections.defaultdict(
      (_ScaleListDeep if flagValueFollowsProtocol else _ScaleListShallow))
    
    # We sort the keys for reproducibility in the grouped case. I'm not super
    # happy about it.
    
    for key in sorted(self):
        value = self[key]
        
        if flagKeyFollowsProtocol or flagValueFollowsProtocol:
            if flagKeyFollowsProtocol and (key is not None):
                key = key.transformed(matrixObj, **kwArgs)
        
            if flagValueFollowsProtocol and (value is not None):
                value = value.transformed(matrixObj, **kwArgs)
        
        elif flagLinked:
            # transform both key and value at the same time
            if flagKeyIsX and flagValueIsY:
                assert not (flagKeyIsY or flagValueIsX)
                t = mp((key, value))
                key = keyRoundFunc(t[0], castType=type(key))
                value = valueRoundFunc(t[1], castType=type(value))
            
            else:
                assert (flagKeyIsY and flagValueIsX)
                t = mp((value, key))
                key = keyRoundFunc(t[1], castType=type(key))
                value = valueRoundFunc(t[0], castType=type(value))
        
        else:
            if (flagKeyIsX or flagKeyIsY) and (key is not None):
                # transform the key
                if flagKeyIsX:
                    key = keyRoundFunc(mp((key, 0))[0], castType=type(key))
                else:
                    key = keyRoundFunc(mp((0, key))[1], castType=type(key))
            
            if (flagValueIsX or flagValueIsY) and (value is not None):
                # transform the value
                if flagValueIsX:
                    value = valueRoundFunc(
                      mp((value, 0))[0],
                      castType=type(value))
                
                else:
                    value = valueRoundFunc(
                      mp((0, value))[1],
                      castType=type(value))
        
        # Now that key and value have their transformed versions (or were
        # unaffected because they don't transform), add them
        
        if (key in mNew) and (not DDS.get('item_transformkeysgrouped', False)):
            raise KeyError(key)
        
        mNew[key].append(value)
    
    # replace any length-one lists in dNew with just the element
    for key, v in mNew.items():
        if len(v) == 1:
            mNew[key] = v[0]
    
    # Now do attributes
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

def M_unmadeKeys(self):
    """
    Find keys not yet "brought to life".
    
    :return: all keys originally provided via the one-time iterator but not
        yet turned into living Protocol objects
    :rtype: set
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> sorted(t.unmadeKeys())
    ['a', 'f', 'z']
    >>> t['f']
    'fffff'
    >>> sorted(t.unmadeKeys())
    ['a', 'z']
    """
    
    return set(k for k, v in self._dOrig.items() if v is _singletonNCV)

def M_update(self, other):
    """
    Adds all values from other to self, replacing any values with matching
    keys.
    
    :param other: A mapping whose contents will be put into ``self``
    :return: None
    
    It's OK if the type of ``other`` is something different from the type of
    ``self`` -- so long as it supports the standard mapping accesses, no
    worries.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k, e: k*5),
    ...         item_strusesrepr = True)
    >>> t1 = Test(creationExtras=dict(oneTimeKeyIterator=iter(['f', 'z'])))
    >>> t2 = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a'])))
    >>> t2.z = 'new z string'
    >>> t1.update(t2)
    >>> print(t1)
    {'a': 'aaaaa', 'f': 'fffff', 'z': 'new z string'}
    """
    
    for key, value in other.items():
        self[key] = value

def M_values(self):
    """
    Returns a generator over values.
    
    :return: Generator over values
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(t.values())
    ['aaaaa', 'fffff', 'xxxxx', 'zzzzz']
    """
    
    return (self[k] for k in self)

def PM_pprint_namer(self, p, nm, ksv, **kwArgs):
    """
    This is a private method.
    """
    
    DDS = self._DEFDSPEC
    nmbf = nm.bestNameForGlyphIndex
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if DDS.get('item_pprintdeep', DDS.get('item_followsprotocol', False)):
        for ks, key in ksv:
            value = self[key]
            
            if value is None:
                p.simple(None, label=ks, **kwArgs)
            
            else:
                if elideDups is not False:
                    objID = id(value)
                    
                    if objID in elideDups:
                        p.simple(
                          "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                          label = ks,
                          **kwArgs)
                        
                        continue
                    
                    else:  # already know value is not None
                        elideDups[objID] = len(elideDups)
                        p("OBJECT %d" % (elideDups[objID],))
                        
                        # ...and fall through to actual printing below
                
                oldNamer = value.getNamer()
                value.setNamer(nm)
                p.deep(value, label=ks, **kwArgs)
                value.setNamer(oldNamer)
    
    elif (
      DDS.get('item_renumberdirectvalues', False) and
      DDS.get('item_usenamerforstr', False)):
        
        for ks, key in ksv:
            p.simple(nmbf(self[key]), label=ks, **kwArgs)
    
    elif DDS.get('item_renumbernamesdirectvalues', False):
        for ks, key in ksv:
            p.simple(
              utilities.nameFromKwArgs(self[key], **kwArgs),
              label = ks,
              **kwArgs)
    
    else:
        for ks, key in ksv:
            p.simple(self[key], label=ks, **kwArgs)

def PM_pprint_nonamer(self, p, ksv, **kwArgs):
    """
    This is a private method.
    """
    
    DDS = self._DEFDSPEC
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if DDS.get('item_pprintdeep', DDS.get('item_followsprotocol', False)):
        for ks, key in ksv:
            value = self[key]   
            
            if value is None:
                p.simple(None, label=ks, **kwArgs)
            
            else:
                if elideDups is not False:
                    objID = id(value)
                    
                    if objID in elideDups:
                        p.simple(
                          "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                          label = ks,
                          **kwArgs)
                        
                        continue
                    
                    else:  # already know value is not None
                        elideDups[objID] = len(elideDups)
                        p("OBJECT %d" % (elideDups[objID],))
                        
                        # ...and fall through to actual printing below
                
                p.deep(value, label=ks, **kwArgs)
    
    elif DDS.get('item_renumbernamesdirectvalues', False):
        for ks, key in ksv:
            p.simple(
              utilities.nameFromKwArgs(self[key], **kwArgs),
              label = ks,
              **kwArgs)
    
    else:
        for ks, key in ksv:
            p.simple(self[key], label=ks, **kwArgs)

def SM_bool(self):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if there is any content. This means either the dict portion
        is nonempty, or there are some attributes that are nonzero and not
        flagged as ``attr_ignoreforcomparisons`` or ``attr_ignoreforbool``.
        
        Note that the "dict portion is nonempty" test may be modified if
        ``dict_compareignoresfalses`` is True; see the doctests below for an
        example.
    :rtype: bool
    
    >>> class Test1(object, metaclass=FontDataMetaclass): pass
    >>> bool(Test1()), bool(Test1({0: 0}))
    (False, True)
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'dict_compareignoresfalses': True}
    >>> bool(Test2()), bool(Test2({0: 0})), bool(Test2({0: 1}))
    (False, False, True)
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}}
    >>> bool(Test3())
    False
    
    >>> class Test4(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {'attr_ignoreforbool': True}}
    >>> bool(Test4({}, x=5)), bool(Test4({'a': 1}, x=0))
    (False, True)
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict()
    ...     attrSpec = dict(
    ...         ignored = dict(attr_ignoreforbool = True),
    ...         notIgnored = dict())
    >>> print(bool(Test5({'a': 0}, ignored=0, notIgnored=0)))
    True
    >>> print(bool(Test5({}, ignored=0, notIgnored=0)))
    False
    >>> print(bool(Test5({}, ignored=5, notIgnored=0)))
    False
    >>> print(bool(Test5({}, ignored=0, notIgnored=1)))
    True
    """
    
    if self._DEFDSPEC.get('dict_compareignoresfalses', False):
        if any(bool(value) for value in self.values()):
            return True
    
    elif len(self):
        return True
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_contains(self, key):
    """
    Returns True if key is present (note that it might not be living, but its
    key will be).
    
    :param key: The key being sought
    :return: True if present; False otherwise
    :rtype: bool
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k,e: e['prefix'] + str(k)))
    >>> t = Test(
    ...   creationExtras = {
    ...     'oneTimeKeyIterator': iter([1, 2, 4]),
    ...     'prefix': "Obj "})
    >>> t[19] = "Object nineteen"
    >>> 1 in t, 3 in t, 19 in t
    (True, False, True)
    """
    
    if self._DEFDSPEC.get('item_keyisbytes', False):
        if not isinstance(key, bytes):
            key = key.encode('ascii')
    
    return key in self._dOrig or key in self._dAdded

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k,e: [k]),
    ...         dict_keeplimit = 2)
    >>> t1 = Test(creationExtras=dict(oneTimeKeyIterator=iter(range(1, 11))))
    >>> t2 = t1.__copy__()
    >>> t1 is t2, t1._dOrig is t2._dOrig, t1 == t2
    (False, True, True)
    
    .. warning::
    
        Because of the way deferred dicts work, a shallow copy may not behave
        in the way you expect::
    
            >>> class Test2(object, metaclass=FontDataMetaclass): pass
            >>> d1 = Test2({3: 'a', 5: 'c'})
            >>> 3 in d1
            True
            >>> d2 = d1.__copy__()
            >>> del d2[3]
            >>> 3 in d1
            False
    
        If you need to make a legitimate shallow copy, do something like this::
    
            myCopy = defDict.__copy__()
            myCopy._dOrig = myCopy._dOrig.copy()
            myCopy._dAdded = myCopy._dAdded.copy()
    """
    
    r = type(self)()
    r.__dict__.update(self.__dict__)
    return r

def SM_deepcopy(self, memo=None):
    """
    Make a deep copy.
    
    :param memo: A dict (default ``None``) to reduce reprocessing
    :return: A deep copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> d1 = Top(((15, b1), (30, b2), (45, b1)))
    >>> d2 = d1.__deepcopy__()
    >>> d1 == d2, d1 is d2
    (True, False)
    >>> d2[15] is d1[15], d2[30] is d1[30], d2[45] is d1[45]
    (False, False, False)
    >>> d2[15] is d2[45]
    True
    
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    ...     attrSpec = {
    ...       'someDict': {'attr_followsprotocol': True},
    ...       'someNumber': {}}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2), (45, b1)))
    >>> obj1 = DPA({3: None, 5: b2}, someDict=t, someNumber=25)
    >>> obj1.someDict[15] == obj1.someDict[45]
    True
    >>> obj1.someDict[15] is obj1.someDict[45]
    True
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1 == obj2
    True
    >>> obj1.someDict is obj2.someDict
    False
    >>> obj2.someDict[15] is obj2.someDict[45]
    True
    >>> obj1.someDict[15] == obj2.someDict[15]
    True
    >>> obj1.someDict[15] is obj2.someDict[15]
    False
    >>> obj2[5] == obj1[5], obj2[5] is obj1[5]
    (True, False)
    >>> obj2[5] is obj2.someDict[30]
    True
    """
    
    if memo is None:
        memo = {}
    
    DDS = self._DEFDSPEC
    AS = self._ATTRSPEC
    f = DDS.get('item_deepcopyfunc', None)
    deep = DDS.get('item_deepcopydeep', DDS.get('item_followsprotocol', False))
    mNew = {}
    
    if f is not None:
        for key, value in self.items():
            if value is not None:
                mNew[key] = memo.setdefault(id(value), f(value, memo))
    
    elif deep:
        for key, value in self.items():
            if value is None:
                mNew[key] = None
            
            else:
                mNew[key] = memo.setdefault(
                  id(value),
                  value.__deepcopy__(memo))
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    
    # Construct and return the result. Since mNew was created by accretion, it
    # does not have the _creationExtras or the other custom fields. So the
    # logic here copies self's custom fields.
    #
    # Note that the _creationExtras become a bit academic in the new object.
    # One of the side-effects of this process is that all of the values in the
    # new object are in _dAdded, and _dOrig is empty. Since any item request
    # will always be satisfied by direct access to _dAdded, this means that the
    # item_createfunc will never again be called for the new object, and also
    # that any dict_keeplimit will be ignored (since that limit only applies to
    # the item count in _dOrig). We keep the _creationExtras because the client
    # may have put extra information in there (e.g. the CFF object).
    
    r = self.__copy__()
    r._dAdded = {}
    r._dOrig = {}
    r.update(mNew)
    
    for k, obj in dNew.items():
        setattr(r, k, obj)
    
    return r

def SM_delattr(self, key):
    """
    Delete an attribute *or key* in the mapping.
    
    :param key: The attribute or entry to be deleted
    :return: None
    :raises ValueError: if ``key`` is defined in the ``attrSpec``
    :raises AttributeError: if ``key`` is not in ``self``
    
    Because of the nature of deferred dicts, a reference like ``d.x`` might
    mean one of two things: attribute ``x`` of the object; or else the actual
    dict entry with key ``'x'``. This method handles both of these cases.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> len(t)
    3
    >>> del t.z
    >>> len(t)
    2
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}}
    >>> t2 = Test2({1: 5, 3: -1}, x=9)
    >>> del t2.x
    Traceback (most recent call last):
      ...
    ValueError: 'x' is a permanent attribute and cannot be deleted!
    """
    
    if key in self._ATTRSPEC:
        raise ValueError(
          "%r is a permanent attribute and cannot be deleted!" %
          (key,))
    
    else:
        if self._DEFDSPEC.get('item_keyisbytes', False):
            if not isinstance(key, bytes):
                key = key.encode('ascii')
        
        if key in self.__dict__:
            del self.__dict__[key]
        
        else:
            try:
                del self[key]
            except KeyError:
                raise AttributeError(key)

def SM_delitem(self, key):
    """
    Deletes the specified item.
    
    :param key: The item to be deleted
    :return: None
    :raises KeyError: if ``key`` is not in ``self``
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> len(t)
    3
    >>> del t['z']
    >>> len(t)
    2
    """
    
    if self._DEFDSPEC.get('item_keyisbytes', False):
        if not isinstance(key, bytes):
            key = key.encode('ascii')
    
    if key in self._dAdded:
        del self._dAdded[key]
    
    elif key in self._dOrig:
        del self._dOrig[key]
        
        if self._DEFDSPEC.get('dict_keeplimit', None):
            self._keysCurrentlyCached.discard(key)
    
    else:
        raise KeyError(key)

def SM_eq(self, other):
    """
    Determine if the two objects are equal (selectively).
    
    :return: True if the mappings and their attributes are equal (allowing for
        selective inattention to certain attributes depending on their control
        flags, and depending on the ``attrSorted`` tuple)
    :rtype: bool
    
    >>> class TestIgnore(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'dict_compareignoresfalses': True}
    >>> d1 = TestIgnore({'a': 1, 'b': 2})
    >>> d2 = TestIgnore({'a': 1, 'b': 2, 'c': 0})
    >>> d1 == d2
    True
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'someDict': {'attr_followsprotocol': True},
    ...       'someNumber': {}}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2), (45, b1)))
    >>> obj1 = DPA({3: 5, 5: 3}, someDict=t, someNumber=25)
    >>> obj1 == obj1
    True
    >>> obj1 == None
    False
    >>> obj2 = obj1.__deepcopy__()
    >>> obj1 == obj2
    True
    >>> obj2.someDict[30]['y'] = 3.5
    >>> obj1 == obj2
    False
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {},
    ...       'y': {},
    ...       'z': {'attr_ignoreforcomparisons': True}}
    >>> Test({}, x=1, y=2, z=3) == Test({}, x=1, y=2, z=2000)
    True
    >>> Test({}, x=1, y=2, z=3) == Test({}, x=1, y=200, z=3)
    False
    """
    
    if self is other:
        return True
    
    if self._DEFDSPEC.get('dict_compareignoresfalses', False):
        selfFiltered = {key: value for key, value in self.items() if value}
        
        try:
            otherFiltered = {k: v for k, v in other.items() if v}
        except AttributeError:
            otherFiltered = {}
        
        return selfFiltered == otherFiltered
    
    selfKeys = set(self)
    
    # we do the following in case other is not iterable
    
    try:
        otherKeys = set(other)
    except:
        otherKeys = {}
    
    if selfKeys != otherKeys:
        return False
    
    if not all(self[k] == other[k] for k in selfKeys):
        return False
    
    return attrhelper.SM_eq(
      self._ATTRSPEC,
      getattr(other, '_ATTRSPEC', {}),
      self.__dict__,
      getattr(other, '__dict__', {}))

def SM_getattr(self, key):
    """
    Get the value associated with an attribute *or key* in the mapping.
    
    :param key: The key (attribute or actual dict key) being sought
    :return: The associated value
    :raises AttributeError: if key is not present
    
    Remember that deferred dicts allow ``d.x`` to mean either attribute ``x``
    *or* key ``'x'``. This method disambiguates these cases. If necessary, the
    value will be created via a call to the ``item_createfunc``. The resulting
    item may or may not be cached, depending on the current ``dict_limit``.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> [
    ...   (k, (None if v is _singletonNCV else v))
    ...   for k, v in sorted(t._dOrig.items(), key=operator.itemgetter(0))]
    [('a', None), ('f', None), ('z', None)]
    >>> t.f
    'fffff'
    >>> [
    ...   (k, (None if v is _singletonNCV else v))
    ...   for k, v in sorted(t._dOrig.items(), key=operator.itemgetter(0))]
    [('a', None), ('f', 'fffff'), ('z', None)]
    """
    
    try:
        if self._DEFDSPEC.get('item_keyisbytes', False):
            if not isinstance(key, bytes):
                key = key.encode('ascii')
        
        return self[key]
    
    except KeyError:
        raise AttributeError(key)

def SM_getitem(self, key):
    """
    Get the value associated with the specified key.
    
    :param key: The key being sought
    :return: The associated value
    :raises KeyError: if ``key`` is not in ``self``
    
    The value is created, if necessary, via a call to the ``item_createfunc``.
    The item thus created may be cached or not, depending on the
    ``dict_keeplimit``.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> [
    ...   (k, (None if v is _singletonNCV else v))
    ...   for k, v in sorted(t._dOrig.items(), key=operator.itemgetter(0))]
    [('a', None), ('f', None), ('z', None)]
    >>> t['f']
    'fffff'
    >>> [
    ...   (k, (None if v is _singletonNCV else v))
    ...   for k, v in sorted(t._dOrig.items(), key=operator.itemgetter(0))]
    [('a', None), ('f', 'fffff'), ('z', None)]
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k, s, e: k*len(s)),
    ...         item_createfuncneedsself = True)
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['a']
    'aaa'
    >>> t['r'] = 'something new has been added'
    >>> t['z']
    'zzzz'
    """
    
    if self._DEFDSPEC.get('item_keyisbytes', False):
        if not isinstance(key, bytes):
            key = key.encode('ascii')
    
    if key in self._dAdded:
        return self._dAdded[key]
    
    if key in self._dOrig:
        obj = self._dOrig[key]
        
        if obj is _singletonNCV:
            DDS = self._DEFDSPEC
            f = DDS['item_createfunc']
            kl = DDS.get('dict_keeplimit', None)
            
            if DDS.get('item_createfuncneedsself', False):
                obj = f(key, self, self._creationExtras)
            else:
                obj = f(key, self._creationExtras)
            
            if kl:
                kcc = self._keysCurrentlyCached
                
                if kl == len(kcc):
                    self._dOrig[kcc.pop()] = _singletonNCV
                
                self._dOrig[key] = obj
                kcc.add(key)
            
            elif kl is None:
                self._dOrig[key] = obj
        
        return obj
    
    raise KeyError(key)

def SM_init(self, *args, **kwArgs):
    """
    Initialize the mapping from ``args``, and the attributes from ``kwArgs`` if
    they're present, or via the attribute initialization function otherwise.
    
    :param args: Mapping initializer
    :param kwArgs: Attribute initializers
    :return: None

    Note that if an attribute has the same name as a potential valid key for
    the dict, you can still specify both, by making the dict up before this
    call and passing it in as the sole positional argument, and the attribute
    in kwArgs. This is somewhat inelegant; it's better to avoid such name
    conflicts to begin with.
    
    There may be a keyword argument named ``creationExtras`` (which will be
    popped from ``kwArgs``). This should be a dict with keys used to construct
    objects (see the description above of the ``item_createfunc`` function).
    The ``creationExtras`` dict may contain a key called ``oneTimeKeyIterator``
    the associated value of which will be used to fill the initial dictionary
    with ``_singletonNCV``.

    If ``creationExtras`` is not provided, then objects of this class act like
    regular dicts, and no ``keeplimit`` is observed.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_createfunc = (lambda k,e: e['prefix'] + str(k)))
    >>> t = Test(
    ...   creationExtras={
    ...     'oneTimeKeyIterator': iter([1, 2, 4]),
    ...     'prefix': "Obj "})
    >>> t[2]
    'Obj 2'
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     def _init_b_c(self):
    ...         d = self.__dict__  # avoid invoking __setattr__
    ...         if 'b' not in d:
    ...             d['b'] = d['a'][:2]
    ...         if 'c' not in d:
    ...             d['c'] = d['a'][2:]
    ...     attrSpec = dict(
    ...         a = dict(attr_initfunc = (lambda: "abc")),
    ...         b = dict(
    ...             attr_initfunc = _init_b_c,
    ...             attr_initfuncchangesself = True),
    ...         c = dict(
    ...             attr_initfunc = _init_b_c,
    ...             attr_initfuncchangesself = True))
    >>> Test2({1: 2}).pprint()
    1: 2
    a: abc
    b: ab
    c: c
    >>> Test2({1: 2}, a="wxyz and then some").pprint()
    1: 2
    a: wxyz and then some
    b: wx
    c: yz and then some
    >>> Test2({1: 2}, c="independently initialized").pprint()
    1: 2
    a: abc
    b: ab
    c: independently initialized
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> Test3({3: 5}, a=-9)
    Test3({3: 5}, a=-9.0)
    """
    
    # Note that we set attributes via direct assignment to self.__dict__ in
    # order to avoid unwantedly invoking the special __setattr__ method.
    
    d = self.__dict__
    ce = d['_creationExtras'] = kwArgs.pop('creationExtras', {})
    da = d['_dAdded'] = dict(*args)
    
    it = itertools.filterfalse(
      da.__contains__,
      ce.pop('oneTimeKeyIterator', iter([])))
    
    d['_dOrig'] = dict.fromkeys(it, _singletonNCV)
    d['_namer'] = None
    
    if self._DEFDSPEC.get('dict_keeplimit', None):
        d['_keysCurrentlyCached'] = set()
    
    AS = self._ATTRSPEC
    f = operator.itemgetter('attr_initfunc')
    
    for key, obj in kwArgs.items():
        (d if key in AS else self)[key] = obj
    
    changedFuncIDsAlreadyDone = set()
    deferredKeySet = set()
    
    for key, ks in AS.items():
        if key not in d:
            if 'attr_initfuncchangesself' in ks:
                # We defer doing these special initializations until all the
                # other positional and keyword arguments are done.
                deferredKeySet.add(key)
            
            else:
                v = ([self] if 'attr_initfuncneedsself' in ks else [])
                # it's now OK to do this, because we've already guaranteed
                # all attr dict specs have an attr_initfunc.
                d[key] = f(ks)(*v)
    
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

def SM_iter(self):
    """
    Returns an iterator over all keys (both original and added).
    
    :return: Iterator
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(iter(t))
    ['a', 'f', 'x', 'z']
    """
    
    return iter(set(self._dOrig) | set(self._dAdded))
    #return itertools.chain(self._dOrig.keys(), self._dAdded.keys())

def SM_len(self):
    """
    Returns the current length of the dict (which includes both original and
    added entries).
    
    :return: Length of dict
    :rtype: int
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> len(t)
    4
    """
    
    return len(self._dOrig) + len(self._dAdded)

# def SM_ne(self, other): return not (self == other)

def SM_repr(self):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> class Test0(object, metaclass=FontDataMetaclass): pass
    >>> d = Test0({'a': 1, 'x': Test0({'b': 9})})
    >>> d == eval(repr(d))
    True
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test1() == eval(repr(Test1()))
    True
    
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    ...     attrSpec = {
    ...       'y': {'attr_initfunc': int},
    ...       'z': {'attr_initfunc': Test1, 'attr_followsprotocol': True}}
    >>> Test2() == eval(repr(Test2()))
    True
    """
    
    AS = self._ATTRSPEC
    
    if not AS:
        return "%s(%r)" % (self.__class__.__name__, dict(self))
    
    d = self.__dict__
    t = tuple(x for k in AS for x in (k, d[k]))
    sv = [
        self.__class__.__name__,
        '(',
        repr(dict(self)),
        ', ',
        (', '.join(["%s=%r"] * len(AS))) % t,
        ')']
    
    return ''.join(sv)

def SM_setattr(self, key, value):
    """
    Set a value (attribute or dict entry).
    
    :param key: The key whose attribute or value is to be set
    :param value: The value to be set
    
    If ``key`` is the name of an entry already in ``self.__dict__``, this
    method updates the value as specified. Otherwise, it adds a new dict entry.

    Note that this means that if you are adding a new attribute to a
    deferreddict then you must use::
    
        self.__dict__[yourKey] = yourAttribute
        
    Otherwise it will just be added as a standard dict entry.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    ...     attrSpec = {'fred': {}}
    >>> t = Test(
    ...   creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])),
    ...   fred=5)
    >>> t.x = 'xxxxx'
    >>> sorted(t)
    ['a', 'f', 'x', 'z']
    >>> t.fred
    5
    >>> t.fred = 20
    >>> t.fred
    20
    >>> sorted(t)
    ['a', 'f', 'x', 'z']
    >>> t.george = 8
    >>> sorted(t)
    ['a', 'f', 'george', 'x', 'z']
    
    To add an actual attribute, use the ``__dict__`` directly:
    
    >>> t.__dict__['charlie'] = -100
    >>> sorted(t)
    ['a', 'f', 'george', 'x', 'z']
    
    These come from two separate places:
    
    >>> t.george, t.charlie
    (8, -100)
    """
    
    if key in self.__dict__:
        self.__dict__[key] = value
    
    else:
        if self._DEFDSPEC.get('item_keyisbytes', False):
            if not isinstance(key, bytes):
                key = key.encode('ascii')
        
        self[key] = value

def SM_setitem(self, key, value):
    """
    Sets the specified value for the specified key.
    
    :param key: The key whose associated value is to be changed
    :param value: The new value
    :return: None
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(item_createfunc = (lambda k, e: k*5))
    >>> t = Test(creationExtras=dict(oneTimeKeyIterator=iter(['a', 'f', 'z'])))
    >>> t['x'] = 'xxxxx'
    >>> sorted(iter(t))
    ['a', 'f', 'x', 'z']
    """
    
    if self._DEFDSPEC.get('item_keyisbytes', False):
        if not isinstance(key, bytes):
            key = key.encode('ascii')
    
    if key in self._dOrig:
        self.changed(key)
    
    self._dAdded[key] = value

def SM_str(self):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    
    Note that the keys will be sorted.
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_strusesrepr = True,
    ...         item_usenamerforstr = True)
    >>> t = Test({1: 'Obj 1', 2: 'Obj 2', 4: 'Obj 4'})
    >>> print(t)
    {1: 'Obj 1', 2: 'Obj 2', 4: 'Obj 4'}
    >>> t[3] = "Object three"
    >>> print(t)
    {1: 'Obj 1', 2: 'Obj 2', 3: 'Object three', 4: 'Obj 4'}
    >>> t.setNamer(namer.testingNamer())
    >>> print(t)
    {xyz2: 'Obj 1', xyz3: 'Obj 2', xyz4: 'Object three', xyz5: 'Obj 4'}
    
    >>> class Bottom(object, metaclass=FontDataMetaclass): pass
    >>> class Top(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = {'item_followsprotocol': True}
    >>> class DPA(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = {
    ...         'attr_initfunc': lambda: 15,
    ...         'attr_label': "Count"},
    ...       someDict = {'attr_initfunc': Top, 'attr_label': "Extra data"})
    >>> b1 = Bottom(a=14)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> print(DPA({3: 5}, someDict=t, someNumber=25))
    {3: 5}, Extra data = {15: {'a': 14}, 30: {'a': 12, 'd': 29}}, Count = 25
    
    >>> class Part1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}, 'y': {}}
    >>> class Part2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {'part1': {'attr_strneedsparens': True}, 'z': {}}
    >>> print(Part2({}, part1=Part1({}, x=2, y=3), z=4))
    {}, part1 = ({}, x = 2, y = 3), z = 4
    
    >>> class Test(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'x': {
    ...         'attr_labelfunc': (
    ...           lambda x, **k:
    ...           ("Odd" if x % 2 else "Even"))}}
    >>> print(Test({}, x=2))
    {}, Even = 2
    >>> print(Test({}, x=3))
    {}, Odd = 3
    
    >>> class Test1(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': False}}
    >>> class Test2(object, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       's': {
    ...         'attr_initfunc': (lambda: 'fred'),
    ...         'attr_strusesrepr': True}}
    >>> print(Test1())
    {}, s = fred
    >>> print(Test2())
    {}, s = 'fred'
    
    >>> class Test3(object, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> print(Test3({}))
    {}, y = 5
    >>> print(Test3({}, x=4))
    {}, x = 4, y = 5
    
    >>> class Test5(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_renumbernamesdirectvalues = True)
    >>> obj5 = Test5({'name1': 303, 'name2': 304})
    >>> print(obj5)
    {'name1': 303, 'name2': 304}
    >>> obj5.__dict__['kwArgs'] = {'editor': _fakeEditor()}
    >>> print(obj5)
    {'name1': 303 ('Required Ligatures On'), 'name2': 304 ('Common Ligatures On')}
    """
    
    DDS = self._DEFDSPEC
    AS = self._ATTRSPEC
    nm = self.getNamer()
    keyStringsList = dictkeyutils.makeKeyStringsList(self, DDS, nm)
    sr = (repr if DDS.get('item_strusesrepr', False) else str)
    sv = None
    
    if (nm is not None) and (DDS.get('item_usenamerforstr', False)):
        if DDS.get(
          'item_renumberdeepvalues',
          DDS.get('item_followsprotocol', False)):
            
            sv = [None] * len(self)
            
            for i, (ks, key) in enumerate(keyStringsList):
                obj = self[key]
                
                if obj is None:
                    sv[i] = "%s: %r" % (ks, obj)
                
                else:
                    oldNamer = obj.getNamer()
                    obj.setNamer(nm)
                    sv[i] = "%s: %s" % (ks, sr(obj))
                    obj.setNamer(oldNamer)
        
        elif DDS.get('item_renumberdirectvalues', False):
            nmbf = nm.bestNameForGlyphIndex
            
            sv = [
              "%s: %s" % (ks, nmbf(self[key]))
              for ks, key in keyStringsList]
    
    elif DDS.get('item_renumbernamesdirectvalues', False):
        nfka = utilities.nameFromKwArgs
        k = self.__dict__.get('kwArgs', {})
        
        sv = [
          "%s: %s" % (ks, nfka(self[key], **k))
          for ks, key in keyStringsList]
    
    if sv is None:
        sv = ["%s: %s" % (ks, sr(self[key])) for ks, key in keyStringsList]
    
    s = ''.join(['{', ', '.join(sv), '}'])
    
    if not AS:
        return s
    
    svAttr = attrhelper.SM_str(self, nm)
    return ', '.join([s] + svAttr)

# -----------------------------------------------------------------------------

#
# Private functions
#

if 0:
    def __________________(): pass

_methodDict = {
    '__bool__': SM_bool,
    '__contains__': SM_contains,
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__delattr__': SM_delattr,
    '__delitem__': SM_delitem,
    '__eq__': SM_eq,
    '__getattr__': SM_getattr,
    '__getitem__': SM_getitem,
    '__init__': SM_init,
    '__iter__': SM_iter,
    '__len__': SM_len,
#   '__ne__': SM_ne,
    '__repr__': SM_repr,
    '__setattr__': SM_setattr,
    '__setitem__': SM_setitem,
    '__str__': SM_str,
    '_pprint_namer': PM_pprint_namer,
    '_pprint_nonamer': PM_pprint_nonamer,
    'asImmutable': M_asImmutable,
    'changed': M_changed,
    'checkInput': M_checkInput,
    'clear': M_clear,
    'coalesced': M_coalesced,
    'compacted': M_compacted,
    'copy': SM_copy,
    'copyCreationExtras': M_copyCreationExtras,
    'cvtsRenumbered': M_cvtsRenumbered,
    'fdefsRenumbered': M_fdefsRenumbered,
    'gatheredInputGlyphs': M_gatheredInputGlyphs,
    'gatheredLivingDeltas': M_gatheredLivingDeltas,
    'gatheredMaxContext': M_gatheredMaxContext,
    'gatheredOutputGlyphs': M_gatheredOutputGlyphs,
    'gatheredRefs': M_gatheredRefs,
    'get': M_get,
    'getSortedAttrNames': classmethod(lambda x: x._ATTRSORT),
    'glyphsRenumbered': M_glyphsRenumbered,
    'hasCycles': M_hasCycles,
    'isValid': M_isValid,
    'items': M_items,
    'keys': M_keys,
    'merged': M_merged,
    'namesRenumbered': M_namesRenumbered,
    'pcsRenumbered': M_pcsRenumbered,
    'pointsRenumbered': M_pointsRenumbered,
    'pop': M_pop,
    'popitem': M_popitem,
    'pprint': M_pprint,
    'pprint_changes': M_pprintChanges,
    'reallyHas': M_reallyHas,
    'recalculated': M_recalculated,
    'scaled': M_scaled,
    'setdefault': M_setdefault,
    'storageRenumbered': M_storageRenumbered,
    'transformed': M_transformed,
    'unmadeKeys': M_unmadeKeys,
    'update': M_update,
    'values': M_values
    }

def _addMethods(cd, bases):
    stdClasses = (object,)
    
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

def _badCreateFunc(k, e):
    raise KeyError(k)

def _validateDeferredDictSpec(d):
    """
    Make sure only known keys are included in the deferredDictSpec, and that a
    fallback is used as an item_createfunc if one is not specified. (Checks
    like this are only possible in a metaclass, which is another reason to use
    them over traditional subclassing)
    
    >>> d = {'item_createfunc': (lambda k,e:k*2), 'item_followsprotocol': True}
    >>> _validateDeferredDictSpec(d)
    >>> d = {'item_createfunc': (lambda k,e:k*2), 'item_bollowsprotocol': True}
    >>> _validateDeferredDictSpec(d)
    Traceback (most recent call last):
      ...
    ValueError: Unknown deferredDictSpec keys: ['item_bollowsprotocol']
    """
    
    unknownKeys = set(d) - validDictSpecKeys
    
    if unknownKeys:
        raise ValueError(
          "Unknown deferredDictSpec keys: %s" % (sorted(unknownKeys),))
    
    if 'item_createfunc' not in d:
        d['item_createfunc'] = _badCreateFunc
    
    if 'dict_validatefunc_partial' in d and 'dict_validatefunc' in d:
        raise ValueError(
          "Cannot specify both a dict_validatefunc_partial "
          "and a dict_validatefunc.")
    
    if 'item_validatefunc_partial' in d and 'item_validatefunc' in d:
        raise ValueError(
          "Cannot specify both an item_validatefunc_partial and "
          "an item_validatefunc.")
    
    if 'item_validatefunckeys_partial' in d and 'item_validatefunckeys' in d:
        raise ValueError(
          "Cannot specify both an item_validatefunckeys_partial and "
          "an item_validatefunckeys.")
    
    if 'item_prevalidatedglyphsetkeys' in d:
        if not d.get('item_renumberdirectkeys', False):
            raise ValueError(
              "Prevalidated glyph set provided for keys, but keys "
              "are not glyph indices!")
    
    if 'item_prevalidatedglyphsevalues' in d:
        if not d.get('item_renumberdirectvalues', False):
            raise ValueError(
              "Prevalidated glyph set provided for values, but values "
              "are not glyph indices!")
    
    if 'dict_orderdependencies' in d:
        od = d['dict_orderdependencies']
        s = {k for depSet in od.values() for k in depSet}
        s.update(od)
        it = utilities.constrainedOrderItems(dict.fromkeys(s), od)
        v = list(it)  # will raise ValueError if cycles exist

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for deferreddict-like classes. If this metaclass is applied to
    some class whose base class (or one of whose base classes) is already a
    FontData class, the deferredDictSpec and attrSpec will define additions to
    the original. In this case, if an 'attrSorted' is provided, it will be used
    for the combined attributes (original and newly-added); otherwise the new
    attributes will be added to the end of the attrSorted list.
    
    >>> class D1(object, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_strusesrepr = True)
    ...     attrSpec = dict(
    ...         attr1 = dict())
    >>> print(D1({2: 'x', 3: 'y'}, attr1=10))
    {2: 'x', 3: 'y'}, attr1 = 10
    
    >>> class D2(D1, metaclass=FontDataMetaclass):
    ...     deferredDictSpec = dict(
    ...         item_pprintlabelfunc = (lambda k: 'Z/' + str(k)))
    ...     attrSpec = dict(
    ...         attr2 = dict())
    ...     attrSorted = ('attr2', 'attr1')
    >>> print(D2({2: 'x', 3: 'y'}, attr1=10, attr2=9))
    {Z/2: 'x', Z/3: 'y'}, attr2 = 9, attr1 = 10
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_DEFDSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            DDS = c._DEFDSPEC.copy()
            DDS.update(classdict.pop('deferredDictSpec', {}))
            classdict['_DEFDSPEC'] = classdict['_MAIN_SPEC'] = DDS
            _validateDeferredDictSpec(DDS)
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
            d = classdict['_DEFDSPEC'] = classdict.pop('deferredDictSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateDeferredDictSpec(d)
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
