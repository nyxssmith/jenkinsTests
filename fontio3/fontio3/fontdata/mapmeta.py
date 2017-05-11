#
# mapmeta.py
#
# Copyright © 2009-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Metaclass for fontdata mappings (whether mutable or immutable; when Python adds
immutable mappings, this metaclass is ready for them). Clients wishing to add
fontdata capabilities to their mapping classes should specify FontDataMetaclass
as the metaclass. The following class attributes are used to control the
various behaviors and attributes of instances of the class:

``attrSpec``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``attrSorted``
    See :py:mod:`~fontio3.fontdata.attrhelper` for this documentation.

``mapSpec``
    A dict of specification information for the mapping, where the keys and
    their associated values are defined in the following list. The listed
    defaults apply if the specified key is not present in ``mapSpec``.

    Note keys starting with ``item_`` relate to individual mapping items, while
    keys starting with ``map_`` relate to the mapping as a whole. Also note
    that in general, functions have higher priority than deep calls, and
    ``None`` values are never passed to either functions or deep calls.

    If a ``mapSpec`` is not provided, an empty one will be used, and all
    defaults listed below will be in force.
        
    ``item_allowfakeglyphkeys``
        If True, ``item_renumberdirectkeys`` must also be True. In this case no
        range checks will be done on glyph index key values. This is useful for
        example in ``morx`` subtables where fake glyphs are used in internal
        workflows.
        
        Default is False.
    
    ``item_allowfakeglyphvalues``
        If True, ``item_renumberdirectvalues`` must also be True. In this case
        no range checks will be done on glyph index values. This is useful for
        example in ``morx`` subtables where fake glyphs are used in internal
        workflows.
        
        Default is False.
    
    ``item_asimmutabledeep``
        If True then mapping values have their own ``asImmutable()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_asimmutablefunc``
        A function called on a mapping value and returning an immutable version
        of that value. If this is not specified, and neither
        ``item_followsprotocol`` nor ``item_asimmutabledeep`` is True, then
        mapping values must already be immutable.
        
        There is no default.
    
    ``item_coalescedeep``
        If True then mapping values have their own ``coalesced()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_compactdeep``
        If True then mapping values have their own ``compacted()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_deepconverterfunc``
        If a protocol deep function is called on a mapping value and fails,
        this converter function will be called to get an object that will
        succeed with the call. This function takes the mapping value, and
        optional keyword arguments.

        This is useful for cases like ``dict``s of items that are usually
        ``Collection`` objects, but where you wish to also allow simple integer
        values to be set. In this case, if the converter function is something
        like ``toCollection()``, then the value will automatically be converted
        for the purposes of the deep protocol method call.

        A note about special methods and converters: if a mapping value is deep
        and uses a converter function, then any call to a special method (such
        as ``__deepcopy__()`` or ``__str__()``) on that mapping value will
        only have access to the optional keyword arguments if an attribute
        named ``kwArgs`` was set in the object's ``__dict__``. You should only
        do this when the extra arguments are needed by the converter function.
        
        There is no default.
    
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
        ``kwArg`` called ``activeCycleCheck``, which will be a ``dict`` mapping
        tags to lists of parent objects. The tag associated with this
        ``item_enablecyclechecktag`` is what will be used to look up the
        specific parent chain for all mapping values.
        
        Default is ``None``.
    
    ``item_ensurekeytype``
        A type (or class) object. If this is present, then an ``isinstance()``
        check is made on the key at various parts of the class (object
        instantiation, deep key calls, etc.), and if it fails then the key is
        reassigned to the result of calling the specified type/class with the
        current key value as the only positional argument.

        If this is set, it usually makes sense to set the
        ``item_keyfollowsprotocol`` flag as well.
        
        There is no default.
    
    ``item_followsprotocol``
        If True then mapping values are themselves Protocol objects, and have
        all the Protocol methods.
        
        Note that this may be overridden by explicitly setting a desired "deep"
        flag to False. So, for instance, if mapping values are not to have
        ``compacted()`` calls, then the ``mapSpec`` should have this flag set
        to True and ``item_compactdeep`` set to False.
        
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
    
    ``item_keyfollowsprotocol``
        If True, keys are themselves Protocol objects, and will be processed
        accordingly.
        
        Default is False.
    
    ``item_keyislivingdeltas``
        If True then mapping keys will be included in the output from a call to
        ``gatheredLivingDeltas()``. This is permitted because
        :py:class:`~fontio3.opentype.living_variations.LivingDeltas` objects
        are already immutable.
        
        Default is False.
    
    ``item_keyisoutputglyph``
        If True then non-``None`` keys are treated as output glyphs. This means
        they will not be included in the output of a ``gatheredInputGlyphs()``
        call, and they will be included in the output of a
        ``gatheredOutputGlyphs()`` call. Note that ``item_renumberdirectkeys``
        must also be set; otherwise keys will not be added, even if this flag
        is True.
        
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
        optional keyword arguments that were passed into ``merged()``. It
        returns two values: a ``bool`` indicating whether the merged object is
        different than the original ``self`` argument, and the merged object.
        
        There is no default.
    
    ``item_mergekeyfunc``
        A function that is used to change a key from a merging object if it
        should collide with an existing key. An example of when this is useful
        is merging two ``GPOS`` tables, each of which contains a
        ``b'kern0001'`` tag -- you don't want to piecewise merge these, but
        rather change the tag for one of them to something else, like
        ``b'kern0002'`` for instance.

        Note that if this is specified then ``merged()`` keyword arguments like
        ``conflictPreferOther`` will be ignored, since the conflicts are being
        explicitly managed via this key-changing operation.

        This function takes a ``inUse`` set, and keyword arguments, and returns
        a new key that does not collide.
        
        There is no default.
    
    ``item_pprintdeep``
        If True then mapping values will be pretty-printed via a call to their
        own ``pprint()`` methods. The key will be used as a label, unless an
        ``item_pprintlabelfunc`` is specified (q.v.)
        
        If False, and a ``map_pprintfunc`` or ``item_pprintfunc`` is specified,
        that function will be used. Otherwise, each item will be printed via
        the :py:meth:`~fontio3.utilities.pp.PP.simple` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintdiffdeep``
        If True then mapping values have their own ``pprint_changes()`` methods.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_pprintfunc``
        A function that is called to pretty-print mapping values. It is called
        with four arguments: the :py:class:`~fontio3.utilities.pp.PP` instance,
        a mapping value, a label (which will be the key, or possibly a string
        representing a glyph name), and ``kwArgs`` for any additional keyword
        arguments. For an example of the need for the optional arguments, see
        :py:mod:`fontio3.feat.settings`.

        A note about glyph names: if ``item_usenamerforstr`` is True and a
        :py:class:`~fontio3.utilities.namer.Namer` is available, ``pprint()``
        will add a keyword argument called ``bestNameFunc`` when it calls the
        supplied ``item_pprintfunc``. This allows that function to do the name
        string substitution.
        
        There is no default.
    
    ``item_pprintlabelfunc``
        If specified, this should be a function that is called with a mapping
        key and that returns a string suitable for passing as the label
        argument to a :py:class:`~fontio3.utilities.pp.PP` method. (This
        function may end up being called with the mapping value as well; see
        the ``item_pprintlabelfuncneedsobj`` key for more information).
        
        Default is that the keys themselves will be used as labels.
    
    ``item_pprintlabelfuncneedsobj``
        If True, calls to the ``item_pprintlabelfunc`` will have an extra
        keyword argument added (in addition to the mapping key already passed
        in as a positional argument). This extra keyword will be ``obj``, and
        the value will be the object itself.
        
        Default is False.
    
    ``item_pprintlabelnosort``
        If True, labels will not be sorted in ``pprint()`` output. This can be
        useful if a custom ``__iter__()`` method has been made for the class
        (see :py:mod:`fontio3.GSUB.ligature` for an example).
        
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
        sorted *before* being passed one-by-one to the label func.
        
        Default is False.
    
    ``item_pprintlabelpresortfunc``
        If specified, this function will be passed into the Python ``sorted()``
        function as the ``key`` keyword argument. It should therefore be a
        function that takes a presorted key object and returns a new object
        which, when sorted, yields the desired order.

        Note that specififying this key automatically causes the
        ``item_pprintlabelpresort`` key to be used as well, and thus that key
        need not be specified as well. If you desire the sort order to be
        reversed, however, you must also specify the
        ``item_pprintlabelpresortreverse`` flag.
        
        Default is ``None``.
    
    ``item_pprintlabelpresortreverse``
        The effect is like ``item_pprintlabelpresort``, but the order of the
        keys is reversed.
        
        Default is False.
    
    ``item_prevalidatedglyphsetkeys``
        A ``set`` or ``frozenset`` containing glyph indices which are to be
        considered valid for mapping keys, even though they exceed the font's
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
        If True, the Python 3 round function will be used. If False (the
        default), old-style Python 2 rounding will be done. This affects both
        scaling and transforming if one of the rounding options is used.
        
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
        
        Default derives from ``item_keyfollowsprotocol``.
    
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
        renumbered. It's OK for keys to shrink; if you need to prevent this,
        use ``item_renumberdeepkeysnoshrink`` instead.
        
        Default derives from ``item_keyfollowsprotocol``.
    
    ``item_renumberdeepkeysnoshrink``
        If True then mapping keys are themselves objects that can be
        renumbered, but if the renumbering (given the state of ``keepMissing``)
        results in a new key that has fewer elements than previously, the key
        will not be kept.
        
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
        If True then mapping values have their own ``fdefsRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberfdefsdeepkeys``
        If True then mapping keys have their own ``fdefsRenumbered()`` method.
        
        Default derives from ``item_keyfollowsprotocol``.
    
    ``item_renumberfdefsdirectkeys``
        If True then mapping keys are interpreted as ``FDEF`` indices, and are
        subject to renumbering if the ``fdefsRenumbered()`` method is called.
        See also ``item_renumberfdefsdirectvalues``.
        
        Default is False.
    
    ``item_renumberfdefsdirectvalues``
        If True then mapping values are interpreted as ``FDEF`` indices, and
        are subject to renumbering if the ``fdefsRenumbered()`` method is
        called. See also ``item_renumberfdefsdirectkeys``.
        
        Default is False.
    
    ``item_renumbernamesdeep``
        If True then mapping values have their own ``namesRenumbered()`` method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumbernamesdeepkeys``
        If True then mapping keys have their own ``namesRenumbered()`` method.
        
        Default derives from ``item_keyfollowsprotocol``.
    
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
        
        Default derives from ``item_keyfollowsprotocol``.
    
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
        
        Default derives from ``item_keyfollowsprotocol``.
    
    ``item_renumberpointsdirect``
        If True then mapping values are themselves point indices. Note that if
        this is used, the ``kwArgs`` passed into ``pointsRenumbered()`` must
        include ``glyphIndex``, which is used to index into that method's
        ``mapData``, unless implicitly handled by the presence of the
        ``item_renumberdirectkeys`` flag (which indicates the keys are glyph
        indices).
        
        Default is False.
    
    ``item_renumberpointsdirectkeys``
        If True then mapping keys are themselves point indices. Note that if
        this is used, the ``kwArgs`` passed into ``pointsRenumbered()`` must
        include ``glyphIndex``, which is used to index into that method's
        ``mapData``.

        It is an error for this flag to be set if ``item_renumberdirectkeys``
        is also set.
        
        Default is False.
    
    ``item_renumberstoragedeep``
        If True then mapping values have their own ``storageRenumbered()``
        method.
        
        Default derives from ``item_followsprotocol``.
    
    ``item_renumberstoragedeepkeys``
        If True then mapping keys have their own ``storageRenumbered()`` method.
        
        Default derives from ``item_keyfollowsprotocol``.
    
    ``item_renumberstoragedirectkeys``
        If True then mapping keys are interpreted as storage indices, and are
        subject to renumbering if the ``storageRenumbered()`` method is called.
        See also ``item_renumberstoragedirectvalues``.
        
        Default is False.
    
    ``item_renumberstoragedirectvalues``
        If True then mapping values are interpreted as storage indices, and are
        subject to renumbering if the ``storageRenumbered()`` method is called.
        See also ``item_renumberstoragedirectkeys``.
        
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
        
        Default derives from ``item_keyfollowsprotocol``.
    
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
    
    ``map_asimmutablefunc``
        A function to create an immutable version of the mapping. This function
        takes the mapping as the sole positional argument, as well as the usual
        ``kwArgs``, and returns the immutable representation.
        
        There is no default.
    
    ``map_compactiblefunc``
        A function taking two positional arguments (the map itself, and a key),
        and optional keyword arguments. It returns True if the key is removable
        as part of a ``compacted()`` call.

        Note that ``map_compactremovesfalses`` is just shorthand for specifying
        ``lambda obj, key, **k: not bool(obj[key])`` as the
        ``map_compactiblefunc``.

        For an example of when this is useful, see
        :py:mod:`fontio3.opentype.pschainclass`.
        
        There is no default.
    
    ``map_compactremovesfalses``
        If True then any values whose ``bool()`` is False will be removed from
        the mapping in the output of a ``compacted()`` call.
        
        Default is False.
    
    ``map_compareignoresfalses``
        If True then ``__eq__()`` and ``__ne__()`` will ignore those key/value
        pairs for which ``bool(value)`` is False.
        
        Default is False.
    
    ``map_fixedkeyset``
        If a set is specified for this keyword, then instances of the mapping
        will be created with these keys (each with a value of ``None``). At
        ``buildBinary()`` time the key set will be checked against this set and
        if it does not match an exception will be raised.
        
        There is no default.
    
    ``map_fixedvaluefunc``
        If ``map_fixedkeyset`` is specified, then for each key the associated
        value will be obtained via a call to this function.
        
        Default is a function returning None.
    
    ``map_makefunc``
        A function taking three arguments: ``self``, ``*args``, and
        ``**kwArgs``. This function will be called when a new object of this
        type needs to be created. Note that in the vast majority of cases the
        client does not need to specify this; it's only useful for cases like
        subclasses of ``defaultdict``, where ``type(self)(d, **k)`` will not
        work.

        If this is not specified, ``type(self)(*args, **kwArgs)`` will be used,
        as usual.
        
        There is no default.
    
    ``map_maxcontextfunc``
        A function to determine the maximum context for the mapping. This
        function takes a single argument, the mapping itself.
        
        There is no default.
    
    ``map_mergecheckequalkeysets``
        If True, then the two mappings being merged must have identical key
        sets; otherwise, a ``ValueError`` will be raised.

        This flag is the opposite of the ``map_mergechecknooverlap`` flag.
        
        Default derives from ``map_fixedkeyset``.
    
    ``map_mergechecknooverlap``
        If True, and there exists non-empty overlap in the key sets of ``self``
        and ``other`` at ``merged()`` time, a ``ValueError`` will be raised.

        This flag is the opposite of the ``map_mergecheckequalkeysets`` flag.
        
        Default is False.
    
    ``map_ppoptions``
        If specified, it should be a dict whose keys are valid options to be
        passed in for construction of a :py:class:`~fontio3.utilities.pp.PP`
        instance, and whose values are as appropriate. This can be used to make
        a custom ``noDataString``, for instance.
        
        There is no default.
    
    ``map_pprintdifffunc``
        A function to pretty-print differences between two mappings of the same
        type. The function (which can be an unbound method, as can many other
        ``mapSpec`` values) takes at least three arguments: the
        :py:class:`~fontio3.utilities.pp.PP` object, the current mapping, and
        the prior mapping.
        
        There is no default.
    
    ``map_pprintfunc``
        A function taking two positional arguments: a
        :py:class:`~fontio3.utilities.pp.PP` instance, and the mapping as a
        whole, as well as optional keyword arguments. The usual use for this
        tag is to specify a value of
        :py:meth:`mapping_grouped <fontio3.utilities.pp.PP.mapping_grouped>` or
        :py:meth:`mapping_grouped_deep <fontio3.utilities.pp.PP.mapping_grouped_deep>`,
        where the mapping's keys are integer-valued.
        
        There is no default.
    
    ``map_recalculatefunc``
        If specified, a function taking one positional argument, the whole
        mapping. Additional keyword arguments (for example, ``editor``) may be
        specified.

        The function returns a pair: the first value is True or False,
        depending on whether the recalculated list's value actually changed.
        The second value is the new recalculated object to be used (if the
        first value was True).

        If a ``map_recalculatefunc`` is provided then no individual
        ``item_recalculatefunc`` calls will be made. If you want them to be
        made, use a ``map_recalculatefunc_partial`` instead.
        
        There is no default.
    
    ``map_recalculatefunc_partial``
        A function taking one positional argument, the whole mapping, and
        optional additional keyword arguments. The function should return a
        pair: the first value is True or False, depending on whether the
        recalculated mapping's value actually changed. The second value is the
        new recalculated object to be used (if the first value was True).

        After the ``map_recalculatefunc_partial`` is done, individual
        ``item_recalculatefunc`` calls will be made. This allows you to "divide
        the labor" in useful ways.
        
        There is no default.
    
    ``map_validatefunc``
        A function taking one positional argument, the whole mapping, and
        optional additional keyword arguments. The function returns True if the
        mapping is valid, and False otherwise.
        
        There is no default.
    
    ``map_validatefunc_partial``
        A function taking one positional argument, the whole mapping, and
        optional additional keyword arguments. The function returns True if the
        mapping is valid, and False otherwise. Any ``item_validatefuncs`` and
        ``item_validatefunckeys`` will also be run to determine the returned
        True/False value, so this function should focus on overall mapping
        validity.

        If you want this function to do everything without allowing any
        ``item_validatefuns`` to be run, then use the ``map_validatefunc``
        keyword instead.
        
        There is no default.
    
    ``map_wisdom``
        A string with helpful comments for using this mapping.
        
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

validMapSpecKeys = frozenset([
  'item_allowfakeglyphkeys',
  'item_allowfakeglyphvalues',
  'item_asimmutabledeep',
  'item_asimmutablefunc',
  'item_coalescedeep',
  'item_compactdeep',
  'item_deepconverterfunc',
  'item_deepcopydeep',
  'item_deepcopyfunc',
  'item_enablecyclechecktag',
  'item_ensurekeytype',
  'item_followsprotocol',
  'item_inputcheckfunc',
  'item_inputcheckkeyfunc',
  'item_keyfollowsprotocol',
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
  'item_pprintlabelnosort',
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
  'item_renumberdeepkeysnoshrink',
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
  'item_wisdom_value',
  
  'map_asimmutablefunc',
  'map_compactiblefunc',
  'map_compactremovesfalses',
  'map_compareignoresfalses',
  'map_fixedkeyset',
  'map_fixedvaluefunc',
  'map_makefunc',
  'map_maxcontextfunc',
  'map_mergecheckequalkeysets',
  'map_mergechecknooverlap',
  'map_ppoptions',
  'map_pprintdifffunc',
  'map_pprintfunc',
  'map_recalculatefunc',
  'map_recalculatefunc_partial',
  'map_validatefunc',
  'map_validatefunc_partial',
  'map_wisdom'])

# Note that it's important the following two types are not sets or frozensets,
# despite the appeal of doing so, because there is no guarantee that the values
# accumulated into these lists are immutable.

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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
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
    
    >>> class DPA(dict, metaclass=FontDataMetaclass):
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

    
    >>> class Test1(dict, metaclass=FontDataMetaclass): pass
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1({'dummy': x})),
    ...         item_followsprotocol = True)
    >>> t = Test2({'x': 4, 'y': Test1({'normal': -5})})
    >>> tst = (
    ...   'Test2',
    ...   frozenset({
    ...     ('x', ('Test1', frozenset({('dummy', 4)}))),
    ...     ('y', ('Test1', frozenset({('normal', -5)})))}))
    >>> t.asImmutable() == tst
    True
    
    >>> class Test3a(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict())
    
    >>> def fSpecial(obj, **kwArgs):
    ...     ks = sorted(obj)
    ...     if kwArgs.get('attrFirst', False):
    ...         return (obj.x,) + tuple(ks) + tuple(obj[k] for k in ks)
    ...     return tuple(ks) + tuple(obj[k] for k in ks) + (obj.x,)
    
    >>> class Test3b(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         map_asimmutablefunc = fSpecial)
    ...     attrSpec = dict(
    ...         x = dict())
    
    >>> t3a = Test3a({3: 5, -2: 4, 2: 6}, x=-2)
    >>> t3b = Test3b({3: 5, -2: 4, 2: 6}, x=-2)
    
    >>> tst = ('Test3a', frozenset({(-2, 4), (2, 6), (3, 5)}), ('x', -2))
    >>> t3a.asImmutable() == tst
    True
    
    # In the following, note that fSpecial did not prepend the type to the
    # returned tuple. The metaclass leaves decisions like that up to the
    # function, but it's a good idea to do so, to avoid pool collisions.
    
    >>> t3b.asImmutable()
    (-2, 2, 3, 4, 6, 5, -2)
    
    >>> t3b.asImmutable(attrFirst=True)
    (-2, -2, 2, 3, 4, 6, 5)
    """
    
    MS = self._MAPSPEC
    fWhole = MS.get('map_asimmutablefunc', None)
    
    if fWhole is not None:
        return fWhole(self, **kwArgs)
    
    memo = kwArgs.pop('memo', {})
    f = MS.get('item_asimmutablefunc', None)
    
    # Mapping keys are always immutable, so we can use them directly, even if
    # they're deep.
    
    if f is not None:
        r = (
          type(self).__name__,
          frozenset(
            (key, (None if self[key] is None else f(self[key])))
            for key in self))
    
    elif MS.get('item_asimmutabledeep', MS.get('item_followsprotocol', False)):
        cf = MS.get('item_deepconverterfunc', None)
        s = set()
        
        for key in self:
            obj = self[key]
            
            if obj is None:
                s.add((key, None))
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
                
                memo[objID] = boundMethod(memo=memo, **kwArgs)
            
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...   mapSpec = dict(
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
    
    MS = self._MAPSPEC
    keyCheck = kwArgs.pop('isKey', False)
    
    if keyCheck:
        f = MS.get('item_inputcheckkeyfunc', None)
    else:
        f = MS.get('item_inputcheckfunc', None)
    
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
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
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_followsprotocol = True)
    ...     attrSpec = dict(y = dict())
    >>> d2 = Test2({'i': d1, 'j': None}, y = 6000 // 3)
    >>> d2['i'].x == d2.y, d2['i'].x is d2.y
    (True, False)
    >>> d2C = d2.coalesced()
    >>> d2 == d2C
    True
    >>> d2C['i'].x == d2C.y, d2C['i'].x is d2C.y
    (True, True)
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].append('x')
    >>> m[6].append('x')
    >>> m[4] is m[6]
    False
    >>> mCoalesced = m.coalesced()
    >>> m == mCoalesced, mCoalesced[4] is mCoalesced[6]
    (True, True)
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_asimmutablefunc = tuple)
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test1({'dummy': x})),
    ...         item_followsprotocol = True)
    >>> obj = Test2({'x': [1, 2], 'y': Test1({'normal': [1, 2]})})
    >>> obj['x'] == obj['y']['normal']
    True
    >>> obj['x'] is obj['y']['normal']
    False
    >>> obj2 = obj.coalesced()
    >>> obj2['x']['dummy'] is obj2['y']['normal']
    True
    
    >>> class Test3(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True)
    ...     def __repr__(self):
    ...         s = str(tuple(self))[1:-1]
    ...         return ''.join(['^', s, '^'])
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_ensurekeytype = Test3,
    ...         item_keyfollowsprotocol = True)
    >>> obj = Test4({(1, 2): (1, 2, 3), (1, 3): tuple([1] + [2, 3])})
    >>> print(obj)
    {^1, 2^: (1, 2, 3), ^1, 3^: (1, 2, 3)}
    >>> v = list(obj.values())
    >>> v[0] is v[1]
    False
    
    >>> obj2 = obj.coalesced()
    >>> print(obj2)
    {^1, 2^: (1, 2, 3), ^1, 3^: (1, 2, 3)}
    >>> v2 = list(obj2.values())
    >>> v2[0] is v2[1]
    True
    """
    
    cwc = kwArgs.setdefault('_coalescedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    MS = self._MAPSPEC
    mNew = {}
    pool = kwArgs.pop('pool', {})  # allows for sharing across objects
    immutFunc = MS.get('item_asimmutablefunc', None)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    coalesceDeep = MS.get(
      'item_coalescedeep',
      MS.get('item_followsprotocol', False))
    
    immutDeep = MS.get(
      'item_asimmutabledeep',
      MS.get('item_followsprotocol', False))
    
    # First do mapping objects
    for k, obj in self.items():
        if ekt is not None and k is not None and (not isinstance(k, ekt)):
            k = ekt(k)
        
        if obj is None:
            mNew[k] = None
            continue
        
        if coalesceDeep:
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                try:
                    boundMethod = obj.coalesced
            
                except AttributeError:
                    if cf is None:
                        raise
                
                    boundMethod = cf(obj, **kwArgs).coalesced
            
                obj = boundMethod(pool=pool, **kwArgs)
                cwc[objID] = obj
        
        if immutFunc is not None:
            mNew[k] = pool.setdefault(immutFunc(obj), obj)
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
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        r = makeFunc(self, mNew, **dNew)
    else:
        r = type(self)(mNew, **dNew)
    
    cwc[id(self)] = r
    return r

def M_compacted(self, **kwArgs):
    """
    Returns a new object which has been compacted.
    
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A new compacted object
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    *Compacting* means that (if indicated by the presence of the
    ``map_compactremovesfalses`` flag in the ``mapSpec``) members of the
    mapping for which the ``bool()`` result is False are removed.

    Note that any attributes with their own ``compacted()`` method have access
    to the ``self`` as a ``kwArg`` named ``parentObj``. See the
    :py:class:`~fontio3.mort.features.Features` class for an example of how
    this is useful.
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(map_compactremovesfalses = True)
    >>> t1 = Test1({'a': 3, 'b': 0, 'c': False, 'd': None, 'e': '', 'f': 4})
    >>> print(t1.compacted())
    {'a': 3, 'f': 4}
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_compactremovesfalses = True)
    ...     attrSpec = dict(x = dict(attr_followsprotocol = True))
    >>> t2 = Test2({'i': t1, 'j': None}, x = t1)
    >>> t2.pprint()
    'i':
      'a': 3
      'b': 0
      'c': False
      'd': (no data)
      'e': 
      'f': 4
    'j': (no data)
    x:
      'a': 3
      'b': 0
      'c': False
      'd': (no data)
      'e': 
      'f': 4
    
    >>> t2.compacted().pprint()
    'i':
      'a': 3
      'f': 4
    x:
      'a': 3
      'f': 4
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_compactremovesfalses': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)),
    ...         map_compactremovesfalses = True)
    >>> m = M()
    >>> m[4].extend([0, 3, False, '', {}])
    >>> m[6].append(0)
    >>> print(m)
    {4: [0, 3, False, , {}], 6: [0]}
    >>> print(m.compacted())
    {4: [3]}
    
    >>> def canRemove(mapping, key, **kwArgs):
    ...     if isinstance(key, str):
    ...         return True
    ...     return not bool(mapping[key])
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(map_compactiblefunc = canRemove)
    >>> print(Test3({2: 0, 5: 1, 6: 12, 'a': 14}).compacted())
    {5: 1, 6: 12}
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         map_compactremovesfalses = True)
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_deepconverterfunc = (lambda x,**k: Test4({'dummy': x})),
    ...         item_followsprotocol = True,
    ...         map_compactremovesfalses = True)
    >>> Test5({'x': False, 'y': Test4({'normal': 0.0})}).compacted()
    Test5({})
    """
    
    cwc = kwArgs.setdefault('_compactedWorkingCache', {})
    
    if id(self) in cwc:
        return cwc[id(self)]
    
    MS = self._MAPSPEC
    mDeep = MS.get('item_compactdeep', MS.get('item_followsprotocol', False))
    mFilter = MS.get('map_compactremovesfalses', False)
    mFunc = MS.get('map_compactiblefunc', None)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    mNew = {}
    
    # First do mapping objects
    for k, obj in self.items():
        if (mFunc is not None) and (mFunc(self, k, **kwArgs)):
            continue
        
        if ekt is not None and k is not None and (not isinstance(k, ekt)):
            k = ekt(k)
        
        if mDeep and (obj is not None):
            objID = id(obj)
            
            if objID in cwc:
                obj = cwc[objID]
            
            else:
                try:
                    boundMethod = obj.compacted
            
                except AttributeError:
                    if cf is None:
                        raise
                
                    boundMethod = cf(obj, **kwArgs).compacted
            
                obj = boundMethod(**kwArgs)
                cwc[objID] = obj
        
        if (not mFilter) or obj:
            mNew[k] = obj
    
    # Now do attributes
    kwArgs['parentObj'] = self
    dNew = attrhelper.M_compacted(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        r = makeFunc(self, mNew, **dNew)
    else:
        r = type(self)(mNew, **dNew)
    
    cwc[id(self)] = r
    return r

def M_cvtsRenumbered(self, **kwArgs):
    """
    Return new object with CVT index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with CVT indices renumbered
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    directKeys = MS.get('item_renumbercvtsdirectkeys', False)
    directValues = MS.get('item_renumbercvtsdirectvalues', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    deepKeys = MS.get(
      'item_renumbercvtsdeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    deepValues = MS.get(
      'item_renumbercvtsdeep',
      MS.get('item_followsprotocol', False))
    
    if deepKeys or deepValues or directKeys or directValues:
        cvtMappingFunc = kwArgs.get('cvtMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        cvtDelta = kwArgs.get('cvtDelta', None)
        
        if cvtMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            cvtMappingFunc = (
              lambda x,**k:
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
                    try:
                        boundMethod = value.cvtsRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(value, **kwArgs).cvtsRenumbered
                    
                    value = boundMethod(**kwArgs)
                
                elif directValues:
                    value = cvtMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_cvtsRenumbered(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_fdefsRenumbered(self, **kwArgs):
    """
    Return new object with FDEF index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with FDEF indices renumbered
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    directKeys = MS.get('item_renumberfdefsdirectkeys', False)
    directValues = MS.get('item_renumberfdefsdirectvalues', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    deepKeys = MS.get(
      'item_renumberfdefsdeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    deepValues = MS.get(
      'item_renumberfdefsdeep',
      MS.get('item_followsprotocol', False))
    
    if deepKeys or deepValues or directKeys or directValues:
        fdefMappingFunc = kwArgs.get('fdefMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        
        if fdefMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            fdefMappingFunc = (
              lambda x,**k:
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
                    try:
                        boundMethod = value.fdefsRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(value, **kwArgs).fdefsRenumbered
                    
                    value = boundMethod(**kwArgs)
                
                elif directValues:
                    value = fdefMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_fdefsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_gatheredInputGlyphs(self, **kwArgs):
    """
    Return a set of glyph indices for those glyphs used as inputs to some
    process.

    :param kwArgs: Optional keyword arguments (there are none here)
    :return: A set of glyph indices
    :rtype: set
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    Any place where glyph indices are the inputs to some rule or process, we
    call those *input glyphs*. Consider the case of *f* and *i* glyphs that are
    present in a ``GSUB`` ligature action to create an *fi* ligature. The *f*
    and *i* glyphs are the input glyphs here; the *fi* ligature glyph is the
    output glyph. Note that this method works for both OpenType and AAT fonts.
    
    >>> class TupleHelper(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(item_renumberdirect = True)
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectvalues': True}
    >>> t1 = Test1({5: 10, 6: 14, 7: 20, 8: None})
    >>> sorted(t1.gatheredInputGlyphs())
    [10, 14, 20]
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> t2 = Test2({9: t1, 10: None})
    >>> sorted(t2.gatheredInputGlyphs())
    [10, 14, 20]
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectkeys': True}
    >>> t3 = Test3({11: 'a', 14: 'b', None: 'x', 35: 'z'})
    >>> sorted(t3.gatheredInputGlyphs())
    [11, 14, 35]
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_renumberdirectvalues = True)
    >>> t4 = Test4({5: 20, 6: 21, 7: None, None: 8, 50: 75})
    >>> sorted(t4.gatheredInputGlyphs())
    [5, 6, 7, 8, 20, 21, 50, 75]
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdeepkeys': True}
    >>> t5 = Test5({
    ...   TupleHelper((3, 6, 10)): 90,
    ...   TupleHelper((18, 40)): 91,
    ...   None: 14})
    >>> sorted(t5.gatheredInputGlyphs())
    [3, 6, 10, 18, 40]
    
    >>> class Test6(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_keyisoutputglyph = True)
    >>> sorted(Test6({6: 'a', 7: 'b'}).gatheredInputGlyphs())
    []
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectvalues': True}
    ...     attrSpec = {'bot': {'attr_renumberdirect': True}}
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectvalues = True,
    ...         item_valueisoutputglyph = True)
    ...     attrSpec = dict(
    ...         topIrrelevant = dict(
    ...             attr_renumberdirect = True,
    ...             attr_isoutputglyph = True),
    ...         topDirect = {'attr_renumberdirect': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom({'a': 61, 'b': 62}, bot=5)
    >>> t = Top({'c': 71, 'd': 72}, topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredInputGlyphs())
    [5, 11, 61, 62]
    """
    
    MS = self._MAPSPEC
    r = set()
    
    # Gather data from keys
    if not MS.get('item_keyisoutputglyph', False):
        if (
          MS.get('item_renumberdeepkeys', False) or
          MS.get('item_renumberdeepkeysnoshrink', False)):
            
            for key in self:
                if key is not None:
                    r.update(key.gatheredInputGlyphs(**kwArgs))
        
        elif MS.get('item_renumberdirectkeys', False):
            r.update(key for key in self if key is not None)
    
    # Gather data from values
    if not MS.get('item_valueisoutputglyph', False):
        if MS.get('item_renumberdeep', MS.get('item_followsprotocol', False)):
            cf = MS.get('item_deepconverterfunc', None)
            
            for obj in self.values():
                if obj is not None:
                    try:
                        boundMethod = obj.gatheredInputGlyphs
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).gatheredInputGlyphs
                    
                    r.update(boundMethod(**kwArgs))
        
        elif MS.get('item_renumberdirectvalues', False):
            r.update(obj for obj in self.values() if obj is not None)
    
    return r | attrhelper.M_gatheredInputGlyphs(
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    This method is used to gather all deltas used in variable fonts so they may
    be converted into an :title-reference:`OpenType 1.8`
    ``ItemVariationStore``.

    You will rarely need to call this method.
    
    A note about the following doctests: for simplicity, I'm using simple
    integers in lieu of actual LivingDeltas objects. Since those objects are
    immutable, the effect is the same. Clients of this method in real code
    should, of course, only use actual LivingDeltas objects!
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...   mapSpec = dict(
    ...     item_keyislivingdeltas = True,
    ...     item_valueislivingdeltas = True)
    ...   attrSpec = dict(
    ...     a = dict(attr_islivingdeltas = True),
    ...     b = dict())
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...   mapSpec = dict(
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
    
    MS = self._MAPSPEC
    isDeep = MS.get('item_followsprotocol', False)
    keyIsLD = MS.get('item_keyislivingdeltas', False)
    valueIsLD = MS.get('item_valueislivingdeltas', False)
    cf = MS.get('item_deepconverterfunc', None)
    r = set()
    
    for k, v in self.items():
        if (k is not None) and keyIsLD:
            r.add(k)
        
        if v is None:
            continue
        
        if valueIsLD:
            r.add(v)
        
        elif isDeep:
            try:
                boundMethod = v.gatheredLivingDeltas
            
            except AttributeError:
                if cf is not None:
                    boundMethod = cf(v, **kwArgs).gatheredLivingDeltas
                else:
                    raise
            
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

    This method is used to recursively walk OpenType or AAT tables to obtain
    the largest matching context used anywhere.

    You will rarely need to call this method.
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_maxcontextfunc': (lambda d: len(d) - 1)}
    >>> b1 = Bottom({1:'a', 3:'b', 5:'c'})
    >>> b2 = Bottom({6:'j', 7:'i', 8:'h', 10:'g', 12:'f', 15:'e', 2:'d'})
    >>> b1.gatheredMaxContext(), b2.gatheredMaxContext()
    (2, 6)
    
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    ...     attrSpec = dict(
    ...         x = dict(attr_maxcontextfunc = (lambda obj: obj[0])),
    ...         y = dict(attr_followsprotocol = True))
    >>> Top({20: b1, 25: None}, x = [8, 1, 4], y=b2).gatheredMaxContext()
    8
    >>> Top({20: b1, 25: None}, x = [4, 1, 4], y=b2).gatheredMaxContext()
    6
    """
    
    MS = self._MAPSPEC
    mcFunc = MS.get('map_maxcontextfunc', None)
    
    if mcFunc is not None:
        mc = mcFunc(self)
    
    elif MS.get('item_followsprotocol', False):
        cf = MS.get('item_deepconverterfunc', None)
        mc = 0
        
        for obj in self.values():
            if obj is not None:
                try:
                    boundMethod = obj.gatheredMaxContext
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(obj, **kwArgs).gatheredMaxContext
                
                mc = max(mc, boundMethod(**kwArgs))
    
    else:
        mc = 0
    
    return max(
      mc,
      attrhelper.M_gatheredMaxContext(
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``

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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectvalues = True,
    ...         item_valueisoutputglyph = True)
    >>> t1 = Test1({4: 10, 5: 22, 6: None, None: 15})
    >>> sorted(t1.gatheredOutputGlyphs())
    [10, 15, 22]
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> t2 = Test2({9: t1, 10: None})
    >>> sorted(t2.gatheredOutputGlyphs())
    [10, 15, 22]
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_keyisoutputglyph = True)
    >>> t3 = Test3({11: 'a', 14: 'b', None: 'x', 35: 'z'})
    >>> sorted(t3.gatheredOutputGlyphs())
    [11, 14, 35]
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_keyisoutputglyph = True,
    ...         item_renumberdirectkeys = True,
    ...         item_renumberdirectvalues = True,
    ...         item_valueisoutputglyph = True)
    >>> t4 = Test4({5: 20, 6: 21, 7: None, None: 8, 50: 75})
    >>> sorted(t4.gatheredOutputGlyphs())
    [5, 6, 7, 8, 20, 21, 50, 75]
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdeepkeys': True}
    >>> t5 = Test5({
    ...   TupleHelper((3, 6, 10)): 90,
    ...   TupleHelper((18, 40)): 91,
    ...   None: 14})
    >>> sorted(t5.gatheredOutputGlyphs())
    [3, 6, 10, 18, 40]
    
    >>> class Test6(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectkeys': True}
    >>> sorted(Test6({6: 'a', 7: 'b'}).gatheredOutputGlyphs())
    []
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectvalues = True,
    ...         item_valueisoutputglyph = True)
    ...     attrSpec = dict(
    ...         bot = dict(
    ...             attr_renumberdirect = True,
    ...             attr_isoutputglyph = True))
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectvalues': True}
    ...     attrSpec = dict(
    ...         topIrrelevant = {'attr_renumberdirect': True},
    ...         topDirect = {
    ...             'attr_renumberdirect': True,
    ...             'attr_isoutputglyph': True},
    ...         topDeep = {'attr_followsprotocol': True})
    ...     attrSorted = ('topDirect', 'topDeep', 'topIrrelevant')
    >>> b = Bottom({'a': 61, 'b': 62}, bot=5)
    >>> t = Top({'c': 71, 'd': 72}, topDirect=11, topDeep=b, topIrrelevant=20)
    >>> sorted(t.gatheredOutputGlyphs())
    [5, 11, 61, 62]
    """
    
    MS = self._MAPSPEC
    r = set()
    
    # Gather data from keys
    if (
      MS.get('item_renumberdeepkeys', False) or
      MS.get('item_renumberdeepkeysnoshrink', False)):
      
        for key in self:
            if key is not None:
                r.update(key.gatheredOutputGlyphs(**kwArgs))
    
    elif MS.get('item_renumberdirectkeys', False):
        if MS.get('item_keyisoutputglyph', False):
            r.update(key for key in self if key is not None)
    
    # Gather data from values
    if MS.get('item_renumberdeep', MS.get('item_followsprotocol', False)):
        cf = MS.get('item_deepconverterfunc', None)
        
        for obj in self.values():
            if obj is not None:
                try:
                    boundMethod = obj.gatheredOutputGlyphs
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(obj, **kwArgs).gatheredOutputGlyphs
                
                r.update(boundMethod(**kwArgs))
    
    elif MS.get('item_renumberdirectvalues', False):
        if MS.get('item_valueisoutputglyph', False):
            r.update(obj for obj in self.values() if obj is not None)
    
    return r | attrhelper.M_gatheredOutputGlyphs(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)

def M_gatheredRefs(self, **kwArgs):
    """
    Return a dict with ``Lookup`` objects contained within ``self``.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A dict mapping ``id(lookupObj)`` to the ``lookupObj``
    :rtype: dict
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
        have already been looked at. It speeds up the process.
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_valueislookup = True)
    >>> class Middle(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_followsprotocol = True)
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
    
    >>> class Top(dict, metaclass=FontDataMetaclass):
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
    
    MS = self._MAPSPEC
    r = {}
    keyTrace = kwArgs.pop('keyTrace', {})
    keyTraceCurr = kwArgs.pop('keyTraceCurr', ())
    memo = kwArgs.pop('memo', set())
    
    if MS.get('item_valueislookup', False):
        for key, value in self.items():
            if value is not None:
                r[id(value)] = value
                ktSet = keyTrace.setdefault(id(value), set())
                ktSet.add(keyTraceCurr + (key,))
    
    if MS.get('item_followsprotocol', False):
        cf = MS.get('item_deepconverterfunc', None)
        
        for key, value in self.items():
            if value is not None:
                try:
                    boundMethod = value.gatheredRefs
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(value, **kwArgs).gatheredRefs
                
                if id(value) not in memo:
                    memo.add(id(value))
                    
                    r.update(
                      boundMethod(
                        keyTrace = keyTrace,
                        keyTraceCurr = keyTraceCurr + (key,),
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct mapping, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the mapping, or (if attributes or an index map) will be changed to
        None.
        
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectvalues': True}
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class DPA(dict, metaclass=FontDataMetaclass):
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
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberdirect': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[5].extend([10, 20, 30])
    >>> print(m)
    {5: [10, 20, 30]}
    >>> print(m.glyphsRenumbered({5: 200, 10: 201, 20: 202, 50: 203}))
    {5: [201, 202, 30]}
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    rDirectKey = MS.get('item_renumberdirectkeys', False)
    rDirectValue = MS.get('item_renumberdirectvalues', False)
    ekt = MS.get('item_ensurekeytype', None)
    keepMissing = kwArgs.get('keepMissing', True)
    missKeyFunc = kwArgs.get('missingKeyReplacementFunc', None)
    mNew = {}
    mRepl = {}
    
    rDeepValue = MS.get(
      'item_renumberdeep',
      MS.get('item_followsprotocol', False))
    
    rDeepKey = MS.get(
      'item_renumberdeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    rDeepKeyNoShrink = MS.get('item_renumberdeepkeysnoshrink', False)
    
    for key, value in self.items():
        okToAdd = True
        dToUse = mNew
        
        if key is not None:
            if rDeepKey or rDeepKeyNoShrink:
                keyNew = key.glyphsRenumbered(oldToNew, **kwArgs)
                
                if (
                  (keyNew is None) or
                  (rDeepKeyNoShrink and (len(keyNew) < len(key)))):
                    
                    okToAdd = False
                
                else:
                    key = keyNew
            
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
                try:
                    boundMethod = value.glyphsRenumbered
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(value, **kwArgs).glyphsRenumbered
                
                value = boundMethod(oldToNew, **kwArgs)
            
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
    
    # Ensure key types, as needed
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_glyphsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_hasCycles(self, **kwArgs):
    """
    Determines if self is self-referential.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: True if self-referential cycles are present; False otherwise
    :rtype: bool
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    dACC = kwArgs.pop('activeCycleCheck', set())
    dMemo = kwArgs.get('memo', set())
    
    if MS.get('item_followsprotocol', False):
        cf = MS.get('item_deepconverterfunc', None)
        
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_renumberdirectvalues': True}
    
    >>> logger = utilities.makeDoctestLogger("t1")
    >>> e = utilities.fakeEditor(0x10000)
    >>> t1 = Test1({'a': 35, 'b': 90, 'c': None, 'd': 200})
    >>> t1.isValid(logger=logger, fontGlyphCount=500, editor=e)
    True
    
    >>> t1.isValid(logger=logger, fontGlyphCount=150, editor=e)
    t1.['d'] - ERROR - Glyph index 200 too large.
    False
    
    >>> t1['r'] = -3.5
    >>> t1.isValid(logger=logger, editor=e, fontGlyphCount=500)
    t1.['r'] - ERROR - The glyph index -3.5 is not an integer.
    False
    
    >>> def _vf(d, **kwArgs):
    ...     if any(k % 2 for k in d):
    ...         kwArgs['logger'].error(('Vxxxx', (), "All keys must be even."))
    ...         return False
    ...     if not all(v % 2 for v in d.values()):
    ...         kwArgs['logger'].error(('Vxxx', (), "All values must be odd."))
    ...         return False
    ...     return True
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_renumberdirectvalues = True,
    ...         item_subloggernamefunc = (lambda k: "Glyph_%d" % (k,)),
    ...         map_validatefunc_partial = _vf)
    >>> logger = utilities.makeDoctestLogger("t2")
    >>> obj = Test2({0: 1, 26: 77})
    >>> obj.isValid(logger=logger, fontGlyphCount=150, editor=e)
    True
    
    >>> obj[0] = 4
    >>> obj.isValid(logger=logger, fontGlyphCount=50, editor=e)
    t2 - ERROR - All values must be odd.
    t2.Glyph_26 - ERROR - Glyph index 77 too large.
    False
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
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
    
    cf = MS.get('item_deepconverterfunc', None)
    wholeFunc = MS.get('map_validatefunc', None)
    wholeFuncPartial = MS.get('map_validatefunc_partial', None)
    
    keyFunc = MS.get('item_validatefunckeys', None)
    keyFuncPartial = MS.get('item_validatefunckeys_partial', None)
    keyGlyph = MS.get('item_renumberdirectkeys', False)
    keyName = MS.get('item_renumbernamesdirectkeys', False)
    keyCVT = MS.get('item_renumbercvtsdirectkeys', False)
    keySLNFunc = MS.get('item_subloggernamefunc', None)
    keySLNFuncNeedsSelf = MS.get('item_subloggernamefuncneedsobj', False)
    keyPVS = MS.get('item_prevalidatedglyphsetkeys', set())
    keyStorage = MS.get('item_renumberstoragedirectkeys', False)
    keyPC = MS.get('item_renumberpcsdirectkeys', False)
    keyPCorPoint = MS.get('item_renumberpcsdirectkeys', False) or keyPC
    keyType = MS.get('item_ensurekeytype', None)
    keyFakeOK = MS.get('item_allowfakeglyphkeys', False)
    
    keyDeep = MS.get(
      'item_validatedeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    keyScales = any(
      MS.get(s, False)
      for s in (
        'item_scaledirectkeys',
        'item_scaledirectkeysgrouped',
        'item_scaledirectkeysnoround'))
    
    valFunc = MS.get('item_validatefunc', None)
    valFuncPartial = MS.get('item_validatefunc_partial', None)
    valGlyph = MS.get('item_renumberdirectvalues', False)
    valName = MS.get('item_renumbernamesdirectvalues', False)
    valCVT = MS.get('item_renumbercvtsdirectvalues', False)
    kwArgsFunc = MS.get('item_validatekwargsfunc', None)
    valPVS = MS.get('item_prevalidatedglyphsetvalues', set())
    valStorage = MS.get('item_renumberstoragedirectvalues', False)
    valPC = MS.get('item_renumberpcsdirect', False)
    valPCorPoint = MS.get('item_renumberpointsdirect', False) or valPC
    valFakeOK = MS.get('item_allowfakeglyphvalues', False)
    eccTag = MS.get('item_enablecyclechecktag', None)
    
    valDeep = MS.get(
      'item_validatedeep',
      MS.get('item_followsprotocol', False))
    
    valScales = any(
      MS.get(s, False)
      for s in (
        'item_scaledirectvalues',
        'item_scaledirectvaluesnoround'))
    
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
                if keyType is not None and (not isinstance(key, keyType)):
                    itemlogger.warning((
                      'G0025',
                      (key,),
                      "Key '%s' is not of the correct type."))
                
                if keyDeep:
                    if hasattr(key, 'isValid'):
                        r = key.isValid(logger=itemLogger, **kwArgs) and r
                
                else:
                    if keyFuncPartial is not None:
                        r = (
                          keyFuncPartial(key, logger=itemLogger, **kwArgs) and
                          r)
                    
                    if keyGlyph:
                        if not valU16Func(
                          key,
                          logger = itemLogger,
                          label = "glyph index"):
                            
                            r = False
                        
                        elif (
                          (not keyFakeOK) and
                          (key not in keyPVS) and
                          (key >= fontGlyphCount)):
                            
                            itemLogger.error((
                              MS.get(
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
                              MS.get(
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
                                  MS.get('item_validatecode_nocvt', 'G0030'),
                                  (key,),
                                  "CVT Index %d is being used, but the font "
                                  "has no Control Value Table."))
                                
                                r = False
                            
                            elif key >= len(editor[b'cvt ']):
                                itemLogger.error((
                                  MS.get(
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
                    if valFuncPartial:
                        rThis = valFuncPartial(
                          obj,
                          logger = itemLogger,
                          **kwArgs)
                        
                        r = rThis and r
                    
                    if valGlyph:
                        if not valU16Func(
                          obj,
                          logger = itemLogger,
                          label = "glyph index"):
                            
                            r = False
                        
                        elif (
                          (not valFakeOK) and
                          (obj not in valPVS) and
                          (obj >= fontGlyphCount)):
                            
                            itemLogger.error((
                              MS.get(
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
                              MS.get(
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
                                  MS.get('item_validatecode_nocvt', 'G0030'),
                                  (obj,),
                                  "CVT Index %d is being used, but the font "
                                  "has no Control Value Table."))
                                
                                r = False
                            
                            elif obj >= len(editor[b'cvt ']):
                                itemLogger.error((
                                  MS.get(
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
    
    return rAttr and r

def M_merged(self, other, **kwArgs):
    """
    Returns a new object representing the merger of ``other`` into ``self``.
    
    :param other: The object to be merged into ``self``
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object representing the merger
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    
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
    
    >>> print(t1.merged(t2, conflictPreferOther=False, replaceWhole=True))
    {'a': {'b': 1, 'c': 2, 'd': 3, 'x': 4}, 'i': {'r': -50}, 'j': {'s': -200}}
    
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
    >>> class WithAttrs(dict, metaclass=FontDataMetaclass):
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
    
    >>> class TopNoConflicts(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_mergechecknooverlap = True)
    
    >>> t1NC = TopNoConflicts({'a': b1, 'i': Bottom({'r': -50})})
    >>> t2NC = TopNoConflicts({'a': b2, 'j': Bottom({'s': -200})})
    >>> err = t1NC.merged(t2NC)
    Traceback (most recent call last):
      ...
    ValueError: Key overlaps not permitted in this class!
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'seq_mergeappend': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].extend([10, 30, 40])
    >>> print(m)
    {4: [10, 30, 40]}
    >>> m2 = M()
    >>> m2[4].extend([20, 10, 35])
    >>> print(m.merged(m2))
    {4: [10, 30, 40, 20, 35]}
    
    >>> def mf(obj1, obj2, **k):
    ...     newObj = obj1 | {x + 10 for x in obj2}
    ...     return ((newObj != obj1), newObj)
    >>> class IndivTest(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_mergefunc': mf}
    >>> d1 = IndivTest({'a': {2, 5, 19}, 'b': {13, 15}})
    >>> d2 = IndivTest({'a': {-7, 9}, 'c': {5}})
    >>> sorted((k, sorted(v)) for k, v in d1.merged(d2).items())
    [('a', [2, 3, 5, 19]), ('b', [13, 15]), ('c', [5])]
    
    >>> class TestEqKeySets(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_mergefunc = (lambda a,b,**k: (a != b, a | b)),
    ...         map_mergecheckequalkeysets = True)
    >>> d1 = TestEqKeySets({1: set([2, 3]), 2: set([5, 4])})
    >>> d2 = TestEqKeySets({1: set([2, 4]), 2: set([9, 4])})
    >>> sorted((k, sorted(v)) for k, v in d1.merged(d2).items())
    [(1, [2, 3, 4]), (2, [4, 5, 9])]
    >>> d1[5] = set([8, 9])
    >>> print(d1.merged(d2))
    Traceback (most recent call last):
      ...
    ValueError: Key sets must be identical in this class!
    
    >>> def kmf(oldKey, inUse, **kwArgs):
    ...     newKey = oldKey + 1
    ...     while newKey in inUse:
    ...         newKey += 1
    ...     return newKey
    >>> class TestMergeKeys(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    
    deepValues = MS.get(
      'item_mergedeep',
      MS.get('item_followsprotocol', False))
    
    prefOther = kwArgs.get('conflictPreferOther', True)
    repWhole = kwArgs.get('replaceWhole', False)
    itemFunc = MS.get('item_mergefunc', None)
    keyFunc = MS.get('item_mergekeyfunc', None)
    keyChanges = kwArgs.pop('mergedKeyChanges', {})
    selfKeys = set(self)
    otherKeys = set(other)
    keysInCommon = selfKeys & otherKeys
    
    if keysInCommon and (keyFunc is not None):
        altOther = other.__copy__()
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
    
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    mNew = dict(self)
    
    if MS.get('map_mergechecknooverlap', False):
        if keysInCommon:
            raise ValueError("Key overlaps not permitted in this class!")
    
    if MS.get('map_mergecheckequalkeysets', MS.get('map_fixedkeyset', False)):
        if selfKeys != otherKeys:
            raise ValueError("Key sets must be identical in this class!")
    
    # In all cases, non-conflicting keys in other are simply added to self
    for key in otherKeys - selfKeys:
        mNew[key] = other[key]
    
    # Process the mapping's merges
    if itemFunc is not None:
        for key in keysInCommon:
            mNew[key] = itemFunc(self[key], other[key], **kwArgs)[1]
    
    elif prefOther:
        if repWhole:
            # prefer other and prohibit deep; just move any conflicting
            # keys from other into self
            for key in keysInCommon:
                mNew[key] = other[key]
        
        else:
            # prefer other and permit deep
            if deepValues:
                # deep call merged() on the values for the conflicting keys
                for key in keysInCommon:
                    selfValue = self[key]
                    
                    if selfValue is not None:
                        try:
                            boundMethod = selfValue.merged
                        
                        except AttributeError:
                            if cf is None:
                                raise
                            
                            boundMethod = cf(selfValue, **kwArgs).merged
                        
                        mNew[key] = boundMethod(other[key], **kwArgs)
            
            else:
                # we have no guidance about the values, so just replace
                # the conflicts
                for key in keysInCommon:
                    mNew[key] = other[key]
    
    else:
        if repWhole:
            # prefer self and prohibit deep (so only non-conflicting
            # keys will be added)
            pass  # already done above
        
        else:
            # prefer self and permit deep
            if deepValues:
                # deep call merged() on the values for the conflicting keys
                for key in keysInCommon:
                    selfValue = self[key]
                    
                    if selfValue is not None:
                        try:
                            boundMethod = selfValue.merged
                        
                        except AttributeError:
                            if cf is None:
                                raise
                            
                            boundMethod = cf(selfValue, **kwArgs).merged
                        
                        mNew[key] = boundMethod(other[key], **kwArgs)
            
            else:
                # do nothing; self is preferred and we have no other guidance
                pass
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_merged(
      self._ATTRSPEC,
      self.__dict__,
      other.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_namesRenumbered(self, oldToNew, **kwArgs):
    """
    Return a new object with ``'name'`` table references renumbered.
    
    :param oldToNew: A dict mapping old to new indices
    :type oldToNew: dict(int, int)
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with names renumbered
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    The following ``kwArgs`` are supported:
    
    ``keepMissing``
        If True for direct names, then values missing from ``oldToNew`` will
        simply be kept unmodified. If False, the values will be deleted from
        the mapping, or (if attributes or an index map) will be changed to
        ``None``.
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    rDirectKey = MS.get('item_renumbernamesdirectkeys', False)
    rDirectValue = MS.get('item_renumbernamesdirectvalues', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    keepMissing = kwArgs.get('keepMissing', True)
    mNew = {}
    
    rDeepValue = MS.get(
      'item_renumbernamesdeep',
      MS.get('item_followsprotocol', False))
    
    rDeepKey = MS.get(
      'item_renumbernamesdeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
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
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_namesRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      oldToNew,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_pcsRenumbered(self, mapData, **kwArgs):
    """
    .. warning::
  
        This is a deprecated method and should not be used.
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberpcsdirect = True,
    ...         item_renumberpcsdirectkeys = True)
    >>> mapData = {"testcode": ((12, 2), (40, 3), (67, 6))}
    >>> d = Test1({5: 12, 50: 100})
    >>> print(d.pcsRenumbered(mapData, infoString="testcode"))
    {5: 14, 53: 106}
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberpcsdirect': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].extend([12, 100])
    >>> print(m)
    {4: [12, 100]}
    >>> print((m.pcsRenumbered(mapData, infoString="testcode")))
    {4: [14, 106]}
    """
    
    MS = self._MAPSPEC
    thisMap = mapData.get(kwArgs.get('infoString', None), [])
    
    if thisMap:
        mNew = {}
        direct = MS.get('item_renumberpcsdirect', False)
        directKeys = MS.get('item_renumberpcsdirectkeys', False)
        cf = MS.get('item_deepconverterfunc', None)
        ekt = MS.get('item_ensurekeytype', None)
        
        deep = MS.get(
          'item_renumberpcsdeep',
          MS.get('item_followsprotocol', False))
        
        deepKeys = MS.get(
          'item_renumberpcsdeepkeys',
          MS.get('item_keyfollowsprotocol', False))
        
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
                    try:
                        boundMethod = obj.pcsRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).pcsRenumbered
                    
                    obj = boundMethod(mapData, **kwArgs)
                
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
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_pcsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_pointsRenumbered(self, mapData, **kwArgs):
    """
    Returns a new object with point indices renumbered.
    
    :param mapData: Dict mapping glyph index to an ``oldToNew`` dict
    :type mapData: dict(int, dict(int, int))
    :param kwArgs: Optional keyword arguments (see below)
    :return: New object with points renumbered
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    
    >>> class Bottom_KIGI(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectkeys = True,
    ...         item_renumberpointsdirect = True)
    >>> myMapData = {2: {5: 6, 11: 12}, 4: {9: 25}}
    >>> b = Bottom_KIGI({0: 4, 2: 11, 3: 6, 4: 9, 5: 15})
    >>> print(b.pointsRenumbered(myMapData))
    {0: 4, 2: 12, 3: 6, 4: 25, 5: 15}
    
    >>> class Bottom_Direct(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_pprintlabelpresort=True,
    ...         item_renumberpointsdirect=True)
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
    
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_renumberpointsdeep = True)
    >>> b1 = Bottom_KIGI({0: 4, 2: 11, 3: 6, 4: 9, 5: 15})
    >>> b2 = Bottom_Direct(zip(range(13), range(13)))
    >>> t = Top({5: b1, 8: None, 9: b2})
    
    In the following, glyphIndex is only used by b2.
    
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         pointNumber = dict(attr_renumberpointsdirect = True))
    >>> class Top(dict, metaclass=FontDataMetaclass):
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberpointsdirect = True,
    ...         item_renumberpointsdirectkeys = True)
    >>> d = Test1({10: 35, 12: 10, 15: 88})
    >>> mapData = {150: {10: 1, 12: 2, 15: 3, 35: 4}}
    >>> print(d.pointsRenumbered(mapData, glyphIndex=150))
    {1: 4, 2: 1, 3: 88}
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_renumberpointsdirect': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].extend([10, 15, 35, 45])
    >>> print(m)
    {4: [10, 15, 35, 45]}
    >>> print(m.pointsRenumbered(mapData, glyphIndex=150))
    {4: [1, 3, 4, 45]}
    """
    
    MS = self._MAPSPEC
    direct = MS.get('item_renumberpointsdirect', False)
    directKeys = MS.get('item_renumberpointsdirectkeys', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    deep = MS.get(
      'item_renumberpointsdeep',
      MS.get('item_followsprotocol', False))
    
    deepKeys = MS.get(
      'item_renumberpointsdeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    if (
      MS.get('item_renumberdirectkeys', False) or
      MS.get('item_keyisoutputglyph', False)):
        mNew = dict(self)
        
        if deep:
            for key, obj in self.items():
                if obj is not None:
                    kwArgs['glyphIndex'] = key
                    
                    try:
                        boundMethod = obj.pointsRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).pointsRenumbered
                    
                    mNew[key] = boundMethod(mapData, **kwArgs)
        
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
                    try:
                        boundMethod = obj.pointsRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).pointsRenumbered
                    
                    obj = boundMethod(mapData, **kwArgs)
                
                elif direct:
                    obj = thisMap.get(obj, obj)
            
            mNew[key] = obj
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_pointsRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      mapData,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_pprint(self, **kwArgs):
    """
    Pretty-print the object and its attributes.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: None
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class Grouped(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_pprintfunc': pp.PP.mapping_grouped}
    >>> d = Grouped({3: 8, 4: 8, 5: 8, 6: None, 9: None, 10: 6, 11: 6})
    >>> d.pprint(label="Grouped data")
    Grouped data:
      [3-5]: 8
      [6, 9]: (no data)
      [10-11]: 6
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {
    ...       'item_followsprotocol': True,
    ...       'item_pprintlabelfunc': (lambda x: "Top key %r" % (x,))}
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = dict(
    ...         attr_initfunc = (lambda: 15),
    ...         attr_label = "Count"),
    ...       someDict = dict(
    ...         attr_followsprotocol = True,
    ...         attr_initfunc = Top,
    ...         attr_label = "Extra data"))
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
    
    >>> class Top2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_pprintlabelpresort = True)
    ...     attrSpec = dict(
    ...         s = dict(
    ...             attr_initfunc = (lambda: 'fred'),
    ...             attr_strusesrepr = False))
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_pprintlabelpresort = True)
    ...     attrSpec = dict(
    ...         s = dict(
    ...             attr_initfunc = (lambda: 'fred'),
    ...             attr_strusesrepr = True))
    >>> Test1({3: 17, 20: -1}).pprint()
    3: 17
    20: -1
    s: fred
    >>> Test2({3: 17, 20: -1}).pprint()
    3: 17
    20: -1
    s: 'fred'
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
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
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_pprintlabelpresortreverse': True}
    >>> Test4({2: 'a', 5: 'b', 10: 'c'}).pprint()
    10: c
    5: b
    2: a
    
    >>> class Key(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     attrSpec = dict(
    ...         order = dict(
    ...             attr_initfunc = (lambda: 0),
    ...             attr_label = "Key order"))
    ...     __hash__ = tuple.__hash__
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_pprintlabelpresortfunc= (lambda obj: (obj[0], obj.order)))
    >>> k1 = Key([25, 30], order=1)
    >>> k2 = Key([25, 40], order=0)
    >>> k3 = Key([30, 40], order=0)
    >>> d = Test5({k1: 'a', k2: 'b', k3: 'c'})
    >>> d.pprint()  # note sort order: first key value, then order attribute
    Key((25, 40), order=0): b
    Key((25, 30), order=1): a
    Key((30, 40), order=0): c
    
    >>> class Test6(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberdirectvalues = True)  # NOT item_usenamerforstr!
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_renumberdirect = True,
    ...             attr_usenamerforstr = True),
    ...         y = dict(attr_renumberdirect = True))
    >>> t6 = Test6({4: 12}, x=35, y=45)
    >>> t6.pprint()
    4: 12
    x: 35
    y: 45
    >>> t6.pprint(namer=namer.testingNamer())
    4: 12
    x: xyz36
    y: 45
    
    >>> class Test7(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         map_ppoptions = dict(noDataString = "nuffin"))
    ...     attrSpec = dict(
    ...         a = dict(),
    ...         b = dict(attr_ppoptions = {'noDataString': "bubkes"}))
    >>> Test7({18: None}).pprint()
    18: nuffin
    a: (no data)
    b: bubkes
    
    >>> class Test8(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumbernamesdirectvalues = True)
    >>> obj8 = Test8({'name1': 303, 'name2': 304})
    >>> obj8.pprint()
    'name1': 303
    'name2': 304
    >>> e = _fakeEditor()
    >>> obj8.pprint(editor=e)
    'name1': 303 ('Required Ligatures On')
    'name2': 304 ('Common Ligatures On')
    
    >>> class Test9(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict(
    ...         item_strusesrepr = True)
    ...     def __repr__(self):
    ...         s = str(tuple(self))[1:-1]
    ...         return ''.join(['^', s, '^'])
    >>> class Test10(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_ensurekeytype = Test9,
    ...         item_keyfollowsprotocol = True)
    >>> obj = Test10({(1, 2): 'a', (5, 3): 'b'})
    >>> obj.pprint()
    ^1, 2^: a
    ^5, 3^: b
    
    >>> obj[(2, 5)] = 'z'
    >>> obj.pprint()
    ^1, 2^: a
    ^2, 5^: z
    ^5, 3^: b
    
    >>> class Test11(tuple, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = dict()
    >>> class Test12(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    pd = p.__dict__
    ppSaveDict = {}
    
    for key, value in MS.get('map_ppoptions', {}).items():
        ppSaveDict[key] = pd[key]
        pd[key] = value
    
    printWholeFunc = MS.get('map_pprintfunc', None)
    kwArgs['useRepr'] = MS.get('item_strusesrepr', False)
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if elideDups is True:
        elideDups = {}  # object ID to serial number
        kwArgs['elideDuplicates'] = elideDups
    
    if printWholeFunc is not None:
        printWholeFunc(p, self, **kwArgs)
        
        while ppSaveDict:
            key, value = ppSaveDict.popitem()
            pd[key] = value
        
        return
    
    if MS.get('item_usenamerforstr', False):
        nm = kwArgs.get('namer', self.getNamer())
    else:
        nm = None
    
    ekt = MS.get('item_ensurekeytype', None)
    
    if ekt is not None:
        badKeys = set(
          k
          for k in self 
          if k is not None and (not isinstance(k, ekt)))
        
        if badKeys:
            
            # If we get here, there is at least one key that is not the
            # correct type, so we make a copy and use that instead.
            
            selfTemp = self.__copy__()  # shallow is fine (and faster)
            
            for k in badKeys:
                obj = self[k]
                del selfTemp[k]
                selfTemp[ekt(k)] = obj
            
            self = selfTemp  # I love Python!
    
    keyStringsList = dictkeyutils.makeKeyStringsList(self, MS, nm)
    printItemFunc = MS.get('item_pprintfunc', None)
    
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
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = dict(
    ...         attr_initfunc = (lambda: 15),
    ...         attr_label = "Count"),
    ...       someDict = dict(
    ...         attr_followsprotocol = True,
    ...         attr_initfunc = Top,
    ...         attr_label = "Extra data",
    ...         attr_usenamerforstr = True))
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
    
    >>> class Test(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(),
    ...         y = dict(),
    ...         z = dict(attr_ignoreforcomparisons = True))
    >>> Test({}, x=1, y=2, z=3).pprint_changes(Test({}, x=1, y=2, z=2000))
    """
    
    if self == prior:
        return
    
    p = (kwArgs.pop('p') if 'p' in kwArgs else pp.PP(**kwArgs))
    kwArgs.pop('label', None)
    MS = self._MAPSPEC
    f = MS.get('map_pprintdifffunc', None)
    deep = MS.get('item_pprintdiffdeep', MS.get('item_followsprotocol', False))
    useRepr = MS.get('item_strusesrepr', False)
    keyIsGlyphIndex = MS.get('item_renumberdirectkeys', False)
    valueIsGlyphIndex = MS.get('item_renumberdirectvalues', False)
    cf = MS.get('item_deepconverterfunc', None)
    origSelf = self
    origPrior = prior
    
    if MS.get('item_usenamerforstr', False):
        nm = kwArgs.get('namer', self.getNamer())
    else:
        nm = None
    
    # Rather than changing the diff_mapping* methods in PP, we just
    # construct alternate dicts with the keys and/or values mapped to
    # their names, if they are glyph indices and so indicated.
    
    if (
      (cf is not None) or
      ((keyIsGlyphIndex or valueIsGlyphIndex) and (nm is not None))):
        
        nmbf = nm.bestNameForGlyphIndex
        d = {}
        
        for key, value in self.items():
            if (key is not None) and keyIsGlyphIndex:
                key = nmbf(key)
            
            if value is not None:
                if valueIsGlyphIndex:
                    value = nmbf(value)
                
                elif deep:
                    try:
                        value.pprint_changes
                    except AttributeError:
                        value = cf(value, **kwArgs)
            
            d[key] = value
        
        self = d
        d = {}
        
        for key, value in prior.items():
            if (key is not None) and keyIsGlyphIndex:
                key = nmbf(key)
            
            if value is not None:
                if valueIsGlyphIndex:
                    value = nmbf(value)
                
                elif deep:
                    try:
                        value.pprint_changes
                    except AttributeError:
                        value = cf(value, **kwArgs)
            
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

def M_recalculated(self, **kwArgs):
    """
    Creates and returns a new object whose contents have been recalculated.
    
    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with recalculated values
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
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
    >>> class Bottom_WholeInPlace(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(map_recalculatefunc = wholeInPlaceFunc)
    >>> class Bottom_WholeReplace(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(map_recalculatefunc = wholeReplaceFunc)
    >>> class Bottom_IndivInPlace(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_recalculatefunc = indivInPlaceFunc)
    >>> class Bottom_IndivReplace(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(item_recalculatefunc = indivReplaceFunc)
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class Test(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_recalculatefunc = (
    ...               lambda x, **k: (True, 2 * x - k['adj']))))
    >>> t = Test({4: 'y'}, x=9)
    >>> print(t)
    {4: y}, x = 9
    >>> print(t.recalculated(adj=4))
    {4: y}, x = 14
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_recalculatefunc': (lambda x: (True, 2 * x or 19))}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].extend([0, 5, 8])
    >>> print(m)
    {4: [0, 5, 8]}
    >>> print(m.recalculated())
    {4: [19, 10, 16]}
    
    >>> def _fp(d, **kwArgs):
    ...     d2 = {}
    ...     for k, n in d.items():
    ...         if n >= 0:
    ...             d2[k] = n
    ...     return dict(d) != d2, d2
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_recalculatefunc = (
    ...           lambda n,**k: (n != round(n), round(n))),
    ...         map_recalculatefunc_partial = _fp)
    >>> obj = Test2({'a': -4, 'b': 0.75, 'e': 12})
    >>> obj.recalculated() == Test2({'b': 1, 'e': 12})
    True
    """
    
    MS = self._MAPSPEC
    fWhole = MS.get('map_recalculatefunc', None)
    fWholePartial = MS.get('map_recalculatefunc_partial', None)
    fIndiv = MS.get('item_recalculatefunc', None)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    mNew = dict(self)
    
    if fWhole is not None:
        changed, mNew = fWhole(self, **kwArgs)
    
    else:
        if fWholePartial is not None:
            changed, mNew = fWholePartial(self, **kwArgs)
        
        if fIndiv is not None:
            for k, obj in mNew.items():
                if obj is not None:
                    changed, mNew[k] = fIndiv(obj, **kwArgs)
        
        elif MS.get(
          'item_recalculatedeep',
          MS.get('item_followsprotocol', False)):
            for k, obj in mNew.items():
                if obj is not None:
                    try:
                        boundMethod = obj.recalculated
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).recalculated
                    
                    mNew[k] = boundMethod(**kwArgs)
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_recalculated(self._ATTRSPEC, self.__dict__, **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_scaled(self, scaleFactor, **kwArgs):
    """
    Returns a object with FUnit distances scaled.
    
    :param float scaleFactor: The scale factor to use
    :param kwArgs: Optional keyword arguments (see below)
    :return: The scaled object
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class ScaleKeys(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_scaledirectkeys = True,
    ...         item_strusesrepr = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleKeysGroup(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_scaledirectkeysgrouped = True,
    ...         item_strusesrepr = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleValues(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_scaledirectvalues = True)
    
    >>> class ScaleBoth(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_scaledirectvalues = True,
    ...         item_scaledirectkeys = True,
    ...         item_pprintlabelpresort = True)
    
    >>> class ScaleBothGroup(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    >>> kgs = kg.scaled(0.1)
    >>> set(kgs) == {2, None}
    True
    >>> sorted(kgs[2]), kgs[None]
    (['a', 'b'], 'c')
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
    >>> bgs = bg.scaled(0.125)
    >>> set(bgs) == {3, None}
    True
    >>> sorted(bgs[3], key=str)
    [0, 1, None]
    >>> bgs[None]
    1
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_scaledirectvalues = True,
    ...         item_strusesrepr = True)
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_scaledirectkeys': True, 'item_strusesrepr': True}
    ...     attrSpec = {'v': {'attr_followsprotocol': True}}
    >>> t = Top({22: 'a', 24: 'b'}, v=Bottom({'c': 80, 'd': 100}))
    >>> print(t)
    {22: 'a', 24: 'b'}, v = {'c': 80, 'd': 100}
    >>> print(t.scaled(1.5))
    {33: 'a', 36: 'b'}, v = {'c': 120, 'd': 150}
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass):
    ...     seqSpec = {'item_scaledirectnoround': True}
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].extend([10.0, 15.0])
    >>> print(m)
    {4: [10.0, 15.0]}
    >>> print(m.scaled(1.5))
    {4: [15.0, 22.5]}
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    MS = self._MAPSPEC
    cf = MS.get('item_deepconverterfunc', None)
    rDVR = MS.get('item_scaledirectvalues', False)
    rDVNR = MS.get('item_scaledirectvaluesnoround', False)
    rDKER = MS.get('item_scaledirectkeys', False)
    rDKENR = MS.get('item_scaledirectkeysnoround', False)
    rDKGR = MS.get('item_scaledirectkeysgrouped', False)
    rDirectValue = rDVR or rDVNR
    rDirectKeyRaise = rDKER or rDKENR
    rDirectKeyGroup = rDKGR
    rKX = MS.get('item_keyrepresentsx', False)
    rKY = MS.get('item_keyrepresentsy', False)
    rVX = MS.get('item_valuerepresentsx', False)
    rVY = MS.get('item_valuerepresentsy', False)
    doKey = not ((scaleOnlyInX and rKY) or (scaleOnlyInY and rKX))
    doValue = not((scaleOnlyInX and rVY) or (scaleOnlyInY and rVX))
    ekt = MS.get('item_ensurekeytype', None)
    
    rDeepValue = MS.get(
      'item_scaledeep',
      MS.get('item_followsprotocol', False))
    
    if rDKENR:
        keyRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfunckeys' in MS:
        keyRoundFunc = MS['item_roundfunckeys']
    elif MS.get('item_python3rounding', False):
        keyRoundFunc = utilities.newRound
    else:
        keyRoundFunc = utilities.oldRound
    
    if rDVNR:
        valueRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfuncvalues' in MS:
        valueRoundFunc = MS['item_roundfuncvalues']
    elif MS.get('item_python3rounding', False):
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
                    try:
                        boundMethod = obj.scaled
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).scaled
                    
                    obj = boundMethod(scaleFactor, **kwArgs)
                
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
                else:  # works for both rDirectValue and (not rDirectValue)
                    mNew[key] = [mNew[key], obj]
    
    elif rDeepValue or rDirectValue:
        if doValue:
            for key, obj in self.items():
                if rDeepValue and (obj is not None):
                    try:
                        boundMethod = obj.scaled
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).scaled
                    
                    obj = boundMethod(scaleFactor, **kwArgs)
                
                elif rDirectValue and obj:
                    obj = valueRoundFunc(scaleFactor * obj, castType=type(obj))
                
                mNew[key] = obj
        
        else:
            mNew.update(self)
    
    else:
        mNew.update(self)
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_scaled(
      self._ATTRSPEC,
      self.__dict__,
      scaleFactor,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_storageRenumbered(self, **kwArgs):
    """
    Return new object with storage index values renumbered.

    :param kwArgs: Optional keyword arguments (see below)
    :return: A new object with storage indices renumbered
    :rtype: Same as self
    :raises AttributeError: If a non-Protocol object is used for a mapping
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
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumberstoragedirectkeys = True,
    ...         item_renumberstoragedirectvalues = True)
    >>> d = Test1({10: 20, None: 30, 40: None, 50: 60})
    >>> print(d.storageRenumbered(storageDelta=5))
    {15: 25, 45: None, 55: 65, None: 35}
    >>> print(d.storageRenumbered(oldToNew={40: 10, 10: 40}))
    {10: None, 40: 20, 50: 60, None: 30}
    >>> print(
    ...   d.storageRenumbered(oldToNew={40: 10, 10: 40}, keepMissing=False))
    {10: None}
    >>> f = (lambda n,**k: (n if n % 4 else n + 900))
    >>> print(d.storageRenumbered(storageMappingFunc=f))
    {10: 920, 50: 960, 940: None, None: 30}
    """
    
    MS = self._MAPSPEC
    directKeys = MS.get('item_renumberstoragedirectkeys', False)
    directValues = MS.get('item_renumberstoragedirectvalues', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    deepKeys = MS.get(
      'item_renumberstoragedeepkeys',
      MS.get('item_keyfollowsprotocol', False))
    
    deepValues = MS.get(
      'item_renumberstoragedeep',
      MS.get('item_followsprotocol', False))
    
    if deepKeys or deepValues or directKeys or directValues:
        storageMappingFunc = kwArgs.get('storageMappingFunc', None)
        oldToNew = kwArgs.get('oldToNew', None)
        keepMissing = kwArgs.get('keepMissing', True)
        storageDelta = kwArgs.get('storageDelta', None)
        
        if storageMappingFunc is not None:
            pass
        
        elif oldToNew is not None:
            storageMappingFunc = (
              lambda x,**k:
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
                    try:
                        boundMethod = value.storageRenumbered
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        boundMethod = cf(obj, **kwArgs).storageRenumbered
                    
                    value = boundMethod(**kwArgs)
                
                elif directValues:
                    value = storageMappingFunc(value, **kwArgs)
                    
                    if value is None:
                        okToAdd = False
            
            if okToAdd:
                mNew[key] = value
    
    else:
        mNew = dict(self)
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_storageRenumbered(
      self._ATTRSPEC,
      self.__dict__,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    else:
        return type(self)(mNew2, **dNew)

def M_transformed(self, matrixObj, **kwArgs):
    """
    Returns a object with FUnit distances transformed.
    
    :param matrixObj: The :py:class:`~fontio3.fontmath.matrix.Matrix` to use
    :param kwArgs: Optional keyword arguments (there are none here)
    :return: The transformed object
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    This method is preferred to the older ``scaled()`` method, because it
    allows for skews and rotations, in addition to scales and shifts.
    
    >>> mShift = matrix.Matrix.forShift(1, 2)
    >>> mScale = matrix.Matrix.forScale(-3, 2)
    >>> m = mShift.multiply(mScale)
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_valuerepresentsx = True)
    >>> print(Test1({'a': 4, 'b': -3}).transformed(m))
    {'a': -15, 'b': 6}
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_valuerepresentsy = True)
    >>> print(Test2({'a': 4, 'b': -3}).transformed(m))
    {'a': 12, 'b': -2}
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeyvaluepairs = True,
    ...         item_valuerepresentsy = True)
    >>> print(Test3({1: 2, -3: -4}).transformed(m))
    {-6: 8, 6: -4}
    
    Key collisions normally generate KeyErrors:
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_keyrepresentsx = True)
    >>> print(Test4({1.21: 'a', 1.22: 'b'}).transformed(m))
    Traceback (most recent call last):
      ...
    KeyError: -7.0
    
    Collisions can be avoided either by not rounding, or by grouping:
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeysnoround = True)
    >>> print(Test5({1.21: 'a', 1.22: 'b'}).transformed(m))
    {-6.63: a, -6.66: b}
    
    >>> class Test6(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_keyrepresentsx = True,
    ...         item_transformkeysgrouped = True)
    >>> print(Test6({1.21: 'a', 1.22: 'b'}).transformed(m))
    {-7.0: ['a', 'b']}
    """
    
    MS = self._MAPSPEC
    
    if MS.get('item_transformkeysnoround', False):
        keyRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfunckeys' in MS:
        keyRoundFunc = MS['item_roundfunckeys']
    elif MS.get('item_python3rounding', False):
        keyRoundFunc = utilities.newRound
    else:
        keyRoundFunc = utilities.oldRound
    
    if MS.get('item_transformvaluesnoround', False):
        valueRoundFunc = (lambda x,**k: x)  # ignores the castType
    elif 'item_roundfuncvalues' in MS:
        valueRoundFunc = MS['item_roundfuncvalues']
    elif MS.get('item_python3rounding', False):
        valueRoundFunc = utilities.newRound
    else:
        valueRoundFunc = utilities.oldRound
    
    mp = matrixObj.mapPoint
    flagKeyFollowsProtocol = MS.get('item_keyfollowsprotocol', False)
    flagValueFollowsProtocol = MS.get('item_followsprotocol', False)
    flagLinked = MS.get('item_transformkeyvaluepairs', False)
    flagKeyIsX = MS.get('item_keyrepresentsx', False)
    flagKeyIsY = MS.get('item_keyrepresentsy', False)
    flagValueIsX = MS.get('item_valuerepresentsx', False)
    flagValueIsY = MS.get('item_valuerepresentsy', False)
    cf = MS.get('item_deepconverterfunc', None)
    ekt = MS.get('item_ensurekeytype', None)
    
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
                try:
                    boundMethod = value.transformed
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(value, **kwArgs).transformed
                
                value = boundMethod(matrixObj, **kwArgs)
        
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
        
        if (key in mNew) and (not MS.get('item_transformkeysgrouped', False)):
            raise KeyError(key)
        
        mNew[key].append(value)
    
    # replace any length-one lists in mNew with just the element
    for key, v in mNew.items():
        if len(v) == 1:
            mNew[key] = v[0]
    
    if ekt is not None:
        mNew2 = {}
        
        for key, value in mNew.items():
            if key is not None and (not isinstance(key, ekt)):
                key = ekt(key)
            
            mNew2[key] = value
    
    else:
        mNew2 = mNew
    
    # Now do attributes
    dNew = attrhelper.M_transformed(
      self._ATTRSPEC,
      self.__dict__,
      matrixObj,
      **kwArgs)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew2, **dNew)
    
    return type(self)(mNew2, **dNew)

def PM_pprint_namer(self, p, nm, ksv, **kwArgs):
    """
    This is a private method.
    """
    
    MS = self._MAPSPEC
    nmbf = nm.bestNameForGlyphIndex
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if MS.get('item_renumbernamesdirectkeys', False):
        keyFunc = functools.partial(utilities.nameFromKwArgs, **kwArgs)
    else:
        keyFunc = str  # I have a faint memory that this might cause trouble...
    
    if MS.get('item_pprintdeep', MS.get('item_followsprotocol', False)):
        cf = MS.get('item_deepconverterfunc', None)
        
        for ks, key in ksv:
            value = self[key]
            
            if value is None:
                p.simple(None, label=keyFunc(ks), **kwArgs)
            
            else:
                try:
                    value.pprint
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    value = cf(value, **kwArgs)
                
                if elideDups is not False:
                    objID = id(value)
                    
                    if objID in elideDups:
                        p.simple(
                          "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                          label = keyFunc(ks),
                          **kwArgs)
                        
                        continue
                    
                    else:  # already know value is not None
                        elideDups[objID] = len(elideDups)
                        p("OBJECT %d" % (elideDups[objID],))
                        
                        # ...and fall through to actual printing below
                
                oldNamer = value.getNamer()
                value.setNamer(nm)
                p.deep(value, label=keyFunc(ks), **kwArgs)
                value.setNamer(oldNamer)
    
    elif (
      MS.get('item_renumberdirectvalues', False) and
      MS.get('item_usenamerforstr', False)):
        
        for ks, key in ksv:
            p.simple(nmbf(self[key]), label=keyFunc(ks), **kwArgs)
    
    elif MS.get('item_renumbernamesdirectvalues', False):
        for ks, key in ksv:
            p.simple(
              utilities.nameFromKwArgs(self[key], **kwArgs),
              label = keyFunc(ks),
              **kwArgs)
    
    else:
        for ks, key in ksv:
            p.simple(self[key], label=keyFunc(ks), **kwArgs)

def PM_pprint_nonamer(self, p, ksv, **kwArgs):
    """
    This is a private method.
    """
    
    MS = self._MAPSPEC
    cf = MS.get('item_deepconverterfunc', None)
    kwArgs.pop('label', None)
    elideDups = kwArgs.get('elideDuplicates', False)
    
    if MS.get('item_renumbernamesdirectkeys', False):
        keyFunc = functools.partial(utilities.nameFromKwArgs, **kwArgs)
    else:
        keyFunc = str  # I have a faint memory that this might cause trouble...
    
    if MS.get('item_pprintdeep', MS.get('item_followsprotocol', False)):
        for ks, key in ksv:
            value = self[key]   
            
            if value is None:
                p.simple(None, label=keyFunc(ks), **kwArgs)
            
            else:
                try:
                    value.pprint
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    value = cf(value, **kwArgs)
                
                if elideDups is not False:
                    objID = id(value)
                    
                    if objID in elideDups:
                        p.simple(
                          "(duplicate; see OBJECT %d above)" % (elideDups[objID],),
                          label = keyFunc(ks),
                          **kwArgs)
                        
                        continue
                    
                    else:  # already know value is not None
                        elideDups[objID] = len(elideDups)
                        p("OBJECT %d" % (elideDups[objID],))
                        
                        # ...and fall through to actual printing below
                
                p.deep(value, label=keyFunc(ks), **kwArgs)
    
    elif MS.get('item_renumbernamesdirectvalues', False):
        for ks, key in ksv:
            p.simple(
              utilities.nameFromKwArgs(self[key], **kwArgs),
              label = keyFunc(ks),
              **kwArgs)
    
    else:
        for ks, key in ksv:
            p.simple(self[key], label=keyFunc(ks), **kwArgs)

def SM_bool(self):
    """
    Determines the Boolean truth or falsehood of ``self``.
    
    :return: True if there is any content. This means either the dict portion
        is nonempty, or there are some attributes that are nonzero and not
        flagged as ``attr_ignoreforcomparisons`` or ``attr_ignoreforbool``.
        
        Note that the "dict portion is nonempty" test may be modified if
        ``map_compareignoresfalses`` is True; see the doctests below for an
        example.
    :rtype: bool
    
    >>> class Test1(dict, metaclass=FontDataMetaclass): pass
    >>> bool(Test1()), bool(Test1({0: 0}))
    (False, True)
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_compareignoresfalses': True}
    >>> bool(Test2()), bool(Test2({0: 0})), bool(Test2({0: 1}))
    (False, False, True)
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}}
    >>> bool(Test3())
    False
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {'attr_ignoreforbool': True}}
    >>> bool(Test4({}, x=5)), bool(Test4({'a': 1}, x=0))
    (False, True)
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict()
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
    
    if self._MAPSPEC.get('map_compareignoresfalses', False):
        if any(bool(value) for value in self.values()):
            return True
    
    elif len(self):
        return True
    
    return attrhelper.SM_bool(self._ATTRSPEC, self.__dict__)

def SM_copy(self):
    """
    Make a shallow copy.
    
    :return: A shallow copy of ``self``
    :rtype: Same as ``self``
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t1 = Top(((15, b1), (30, b2), (45, b1)))
    >>> t2 = t1.__copy__()
    >>> t1 == t2, t1 is t2
    (True, False)
    >>> t2[15] is t2[45], t1[45] is t2[45]
    (True, True)
    
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         someDict = dict(attr_followsprotocol = True),
    ...         someNumber = dict())
    >>> b1 = Bottom(a=14, b=9, c=22)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2), (45, b1)))
    >>> obj1 = DPA({3: 5, 5: 3}, someDict=t, someNumber=25)
    >>> obj1.someDict[15] == obj1.someDict[45]
    True
    >>> obj1.someDict[15] is obj1.someDict[45]
    True
    >>> obj2 = obj1.__copy__()
    >>> obj1.someDict is obj2.someDict
    True
    >>> obj2.someDict[15] == obj2.someDict[45]
    True
    >>> obj2.someDict[15] is obj2.someDict[45]
    True
    
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = []
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_makefunc': (lambda s,*a,**k: type(s)(DD, *a, **k))}
    >>> m = M()
    >>> m[4].append('x')
    >>> mCopy = m.__copy__()
    >>> m == mCopy, m is mCopy, m[4] is mCopy[4]
    (True, False, True)
    """
    
    makeFunc = self._MAPSPEC.get('map_makefunc', None)
    
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
    
    :param memo: A dict (default ``None``) to reduce reprocessing
    :return: A deep copy of ``self``
    :rtype: Same as ``self``
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
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
    
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    ...     attrSpec = dict(
    ...         someDict = dict(attr_followsprotocol = True),
    ...         someNumber = dict())
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
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M()
    >>> m[4].append('x')
    >>> mCopy = m.__deepcopy__()
    >>> m == mCopy, m is mCopy, m[4] is mCopy[4]
    (True, False, False)
    """
    
    if memo is None:
        memo = {}
    
    MS = self._MAPSPEC
    f = MS.get('item_deepcopyfunc', None)
    deep = MS.get('item_deepcopydeep', MS.get('item_followsprotocol', False))
    cf = MS.get('item_deepconverterfunc', None)
    d = self.__dict__
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
                try:
                    boundMethod = value.__deepcopy__
                
                except AttributeError:
                    if cf is None:
                        raise
                    
                    boundMethod = cf(value, **d.get('kwArgs', {})).__deepcopy__
                
                mNew[key] = memo.setdefault(id(value), boundMethod(memo))
    
    else:
        mNew = dict(self)
    
    # Now do attributes
    dNew = attrhelper.SM_deepcopy(self._ATTRSPEC, self.__dict__, memo)
    
    # Construct and return the result
    makeFunc = MS.get('map_makefunc', None)
    
    if makeFunc is not None:
        return makeFunc(self, mNew, **dNew)
    else:
        return type(self)(mNew, **dNew)

def SM_eq(self, other):
    """
    Determine if the two objects are equal (selectively).
    
    :return: True if the mappings and their attributes are equal (allowing for
        selective inattention to certain attributes depending on their control
        flags, and depending on the ``attrSorted`` tuple)
    :rtype: bool
    
    .. note::
    
        This method will only be present if either ``map_compareignoresfalses``
        is True, or there are attributes defined in an ``attrSpec``. If neither
        of these conditions holds, the default ``dict.__eq__()`` will be used
        (which is much faster), and this method won't even be present.
    
    >>> class TestIgnore(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_compareignoresfalses': True}
    >>> d1 = TestIgnore({'a': 1, 'b': 2})
    >>> d2 = TestIgnore({'a': 1, 'b': 2, 'c': 0})
    >>> d1 == d2
    True
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         someDict = dict(attr_followsprotocol = True),
    ...         someNumber = dict())
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
    
    >>> class Test(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(),
    ...         y = dict(),
    ...         z = dict(attr_ignoreforcomparisons = True))
    >>> Test({}, x=1, y=2, z=3) == Test({}, x=1, y=2, z=2000)
    True
    >>> Test({}, x=1, y=2, z=3) == Test({}, x=1, y=200, z=3)
    False
    """
    
    if self is other:
        return True
    
    if other is None:
        return False
    
    MS = self._MAPSPEC
    
    if MS.get('map_compareignoresfalses', False):
        dSelf = dict((k, v) for k, v in self.items() if bool(v))
        dOther = dict((k, v) for k, v in other.items() if bool(v))
        
        if dSelf != dOther:
            return False
    
    else:
        if dict(self) != dict(other):
            return False
    
    return attrhelper.SM_eq(
      self._ATTRSPEC,
      getattr(other, '_ATTRSPEC', {}),
      self.__dict__,
      getattr(other, '__dict__', {}))

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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = dict(
    ...         attr_initfunc = (lambda: 15),
    ...         attr_label = "Count"),
    ...       someDict = dict(
    ...         attr_initfunc = Top,
    ...         attr_label = "Extra data"))
    >>> b1 = Bottom({'c': 44})
    
    >>> print(DPA({'a': 3, 'z': 9}, someDict=Top({39: b1})))
    {'a': 3, 'z': 9}, Extra data = {39: {'c': 44}}, Count = 15
    >>> print(DPA({'a': 3, 'z': 9}, someNumber=-2))
    {'a': 3, 'z': 9}, Extra data = {}, Count = -2
    >>> print(DPA())
    {}, Extra data = {}, Count = 15
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         initLen = dict(
    ...             attr_initfunc = (lambda self: len(self)),
    ...             attr_initfuncneedsself = True))
    >>> v1 = Test1({'a': 4, 'j': -19, 'z': 200})
    >>> v1.initLen
    3
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
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
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'map_fixedkeyset': set([1, 2, 3])}
    >>> Test3().pprint()
    1: (no data)
    2: (no data)
    3: (no data)
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         map_fixedkeyset = set([1, 2, 3]),
    ...         map_fixedvaluefunc = list)
    >>> t = Test4()
    >>> t.pprint()
    1: []
    2: []
    3: []
    >>> t[1] is t[2]
    False
    
    >>> class V(list, metaclass=seqmeta.FontDataMetaclass): pass
    >>> class DD(collections.defaultdict):
    ...     def __missing__(self, key):
    ...         v = self[key] = V()
    ...         return v
    >>> class M(DD, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_followsprotocol = True,
    ...         item_pprintlabelpresort = True,
    ...         map_makefunc = (lambda s,*a,**k: type(s)(DD, *a, **k)))
    >>> m = M({3: V([1, 2]), 15: V([19])})
    >>> m[20].append(-4)
    >>> m.pprint()
    3:
      0: 1
      1: 2
    15:
      0: 19
    20:
      0: -4
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {'a': {'attr_ensuretype': float}}
    >>> Test5({3: 5}, a=1)
    Test5({3: 5}, a=1.0)
    """
    
    MS = self._MAPSPEC
    fixedKeySet = MS.get('map_fixedkeyset', None)
    ekt = MS.get('item_ensurekeytype', None)
    
    if ekt is not None:
        if fixedKeySet:
            fixedValueFunc = MS.get('map_fixedvaluefunc', (lambda: None))
            
            for key in fixedKeySet:
                if key is not None and (not isinstance(key, ekt)):
                    key = ekt(key)
                
                self[key] = fixedValueFunc()
        
        elif args:
            for key, value in args[-1].items():
                if key is not None and (not isinstance(key, ekt)):
                    key = ekt(key)
                
                self[key] = value
    
    else:
        if fixedKeySet:
            fixedValueFunc = MS.get('map_fixedvaluefunc', (lambda: None))
            
            for key in fixedKeySet:
                self[key] = fixedValueFunc()
        
        elif args:
            for key, value in args[-1].items():
                self[key] = value
    
    d = self.__dict__
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
                # it's now OK to do this, because we've already guaranteed all
                # attr dict specs have an attr_initfunc.
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

# Python 3 does this automatically now
#
# def SM_ne(self, other):
#     return not (self == other)

def SM_repr(self):
    """
    Return a string representation of ``self``.
    
    :return: The string representation
    :rtype: str
    
    The returned string can be passed to ``eval()`` in order to get back an
    object equal to the original ``self``.
    
    >>> class Test0(dict, metaclass=FontDataMetaclass): pass
    >>> d = Test0({'a': 1, 'x': Test0({'b': 9})})
    >>> d == eval(repr(d))
    True
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {
    ...       'a': {'attr_initfunc': (lambda: 'x')},
    ...       'b': {'attr_initfunc': list}}
    ...     attrSorted = ('b', 'a')
    >>> Test1() == eval(repr(Test1()))
    True
    
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
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

def SM_str(self):
    """
    Return a nicely readable string representation of the object.
    
    :return: A string representation of ``self``
    :rtype: str
    :raises AttributeError: If a non-Protocol object is used for a mapping
        for which ``item_followsprotocol`` is set, provided there is no
        ``item_deepconverterfunc``
    
    >>> class Test(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
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
    
    >>> class Bottom(dict, metaclass=FontDataMetaclass): pass
    >>> class Top(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = {'item_followsprotocol': True}
    >>> class DPA(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       someNumber = dict(
    ...         attr_initfunc = (lambda: 15),
    ...         attr_label = "Count"),
    ...       someDict = dict(
    ...         attr_initfunc = Top,
    ...         attr_label = "Extra data"))
    >>> b1 = Bottom(a=14)
    >>> b2 = Bottom(a=12, d=29)
    >>> t = Top(((15, b1), (30, b2)))
    >>> print(DPA({3: 5}, someDict=t, someNumber=25))
    {3: 5}, Extra data = {15: {'a': 14}, 30: {'a': 12, 'd': 29}}, Count = 25
    
    >>> class Part1(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {'x': {}, 'y': {}}
    >>> class Part2(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = {'part1': {'attr_strneedsparens': True}, 'z': {}}
    >>> print(Part2({}, part1=Part1({}, x=2, y=3), z=4))
    {}, part1 = ({}, x = 2, y = 3), z = 4
    
    >>> class Test(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       x = dict(
    ...         attr_labelfunc = (lambda x,**k: ("Odd" if x % 2 else "Even"))))
    >>> print(Test({}, x=2))
    {}, Even = 2
    >>> print(Test({}, x=3))
    {}, Odd = 3
    
    >>> class Test1(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       s = dict(
    ...         attr_initfunc = (lambda: 'fred'),
    ...         attr_strusesrepr = False))
    >>> class Test2(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...       s = dict(
    ...         attr_initfunc = (lambda: 'fred'),
    ...         attr_strusesrepr = True))
    >>> print(Test1())
    {}, s = fred
    >>> print(Test2())
    {}, s = 'fred'
    
    >>> class Test3(dict, metaclass=FontDataMetaclass):
    ...     attrSpec = dict(
    ...         x = dict(
    ...             attr_showonlyiftrue = True,
    ...             attr_initfunc = (lambda: 0)),
    ...         y = dict(attr_initfunc = (lambda: 5)))
    >>> print(Test3({}))
    {}, y = 5
    >>> print(Test3({}, x=4))
    {}, x = 4, y = 5
    
    >>> class Test4(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...       item_renumberdirectvalues = True)  # note NOT item_usenamerforstr
    ...     attrSpec = dict(
    ...       x = dict(attr_renumberdirect = True, attr_usenamerforstr = True),
    ...       y = dict(attr_renumberdirect = True))
    >>> t4 = Test4({4: 9}, x=35, y=45)
    >>> print(t4)
    {4: 9}, x = 35, y = 45
    >>> t4.setNamer(namer.testingNamer())
    >>> print(t4)
    {4: 9}, x = xyz36, y = 45
    
    >>> class Test5(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_renumbernamesdirectvalues = True)
    >>> obj5 = Test5({'name1': 303, 'name2': 304})
    >>> print(obj5)
    {'name1': 303, 'name2': 304}
    >>> obj5.kwArgs = {'editor': _fakeEditor()}
    >>> print(obj5)
    {'name1': 303 ('Required Ligatures On'), 'name2': 304 ('Common Ligatures On')}
    """
    
    MS = self._MAPSPEC
    AS = self._ATTRSPEC
    nm = self.getNamer()
    
    ekt = MS.get('item_ensurekeytype', None)
    
    if ekt is not None:
        badKeys = set(
          k
          for k in self 
          if k is not None and (not isinstance(k, ekt)))
        
        if badKeys:
            
            # If we get here, there is at least one key that is not the
            # correct type, so we make a copy and use that instead.
            
            selfTemp = self.__copy__()  # shallow is fine (and faster)
            
            for k in badKeys:
                obj = self[k]
                del selfTemp[k]
                selfTemp[ekt(k)] = obj
            
            self = selfTemp  # I love Python!
    
    keyStringsList = dictkeyutils.makeKeyStringsList(self, MS, nm)
    sr = (repr if MS.get('item_strusesrepr', False) else str)
    sv = None
    cf = MS.get('item_deepconverterfunc', None)
    d = self.__dict__
    
    if (nm is not None) and (MS.get('item_usenamerforstr', False)):
        if MS.get(
          'item_renumberdeepvalues',
          MS.get('item_followsprotocol', False)):
            
            sv = [None] * len(self)
            
            for i, (ks, key) in enumerate(keyStringsList):
                obj = self[key]
                
                if obj is None:
                    sv[i] = "%s: %r" % (ks, obj)
                
                else:
                    try:
                        obj.setNamer, obj.getNamer
                    
                    except AttributeError:
                        if cf is None:
                            raise
                        
                        obj = cf(obj, **d.get('kwArgs', {}))
                    
                    oldNamer = obj.getNamer()
                    obj.setNamer(nm)
                    sv[i] = "%s: %s" % (ks, sr(obj))
                    obj.setNamer(oldNamer)
        
        elif MS.get('item_renumberdirectvalues', False):
            nmbf = nm.bestNameForGlyphIndex
            
            sv = [
              "%s: %s" % (ks, nmbf(self[key]))
              for ks, key in keyStringsList]
    
    elif MS.get('item_renumbernamesdirectvalues', False):
        nfka = utilities.nameFromKwArgs
        k = d.get('kwArgs', {})
        
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
    '__copy__': SM_copy,
    '__deepcopy__': SM_deepcopy,
    '__repr__': SM_repr,
    '__str__': SM_str,
    '_pprint_namer': PM_pprint_namer,
    '_pprint_nonamer': PM_pprint_nonamer,
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

def _addMethods(cd, bases):
    MS = cd['_MAPSPEC']
    AS = cd['_ATTRSPEC']
    needEqNe, needBool = attrhelper.determineNeedForEqBool(AS)
    stdClasses = (dict, collections.defaultdict)
    
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
    
    # Only include __eq__ and __ne__ methods as needed
    if needEqNe or MS.get('map_compareignoresfalses', False):
        if '__eq__' not in cd:
            cd['__eq__'] = SM_eq
        
#         if '__ne__' not in cd:
#             cd['__ne__'] = SM_ne
    
    # Only include __bool__ method as needed
    if needBool or MS.get('map_compareignoresfalses', False):
        if '__bool__' not in cd:
            cd['__bool__'] = SM_bool
    
    # Only include an __init__ method if there are attributes,
    # or a fixed key set is present
    
    if (
      ( AS or
        MS.get('map_fixedkeyset', None) or
        MS.get('item_ensurekeytype', None) or
        (bases[0] is not dict)) and
      ('__init__' not in cd)):
        
        cd['__init__'] = SM_init

def _validateMapSpec(d):
    """
    Make sure only known keys are included in the mapSpec. Also check that
    incoherent attribute groups are not specified (for instance, specifying
    both item_renumberdirectvalues and item_renumberdeepvalues). Any problems
    will cause a ValueError to be raised.

    Checks like this are only possible in a metaclass, which is another reason
    to use them over traditional subclassing.
    
    >>> _validateMapSpec({'item_followsprotocol': True})
    >>> _validateMapSpec({'item_bollowsprotocol': True})
    Traceback (most recent call last):
      ...
    ValueError: Unknown mapSpec keys: ['item_bollowsprotocol']
    
    >>> _validateMapSpec({'item_keyisoutputglyph': True, 'item_renumberpointsdirectkeys': True})
    Traceback (most recent call last):
      ...
    ValueError: Keys cannot be glyphs and/or points and/or PCs!
    
    >>> _validateMapSpec({'item_valueisoutputglyph': True, 'item_renumberpointsdirect': True})
    Traceback (most recent call last):
      ...
    ValueError: Values cannot be glyphs and/or points and/or PCs!
    
    >>> _validateMapSpec({'map_mergechecknooverlap': True, 'map_mergecheckequalkeysets': True})
    Traceback (most recent call last):
      ...
    ValueError: Cannot both require and prohibit merge overlaps!
    """
    
    unknownKeys = set(d) - validMapSpecKeys
    
    if unknownKeys:
        raise ValueError("Unknown mapSpec keys: %s" % (sorted(unknownKeys),))
    
    keyIsGlyph = (
      d.get('item_keyisoutputglyph', False) or
      d.get('item_renumberdirectkeys', False) or
      d.get('item_renumberdeepkeys', False) or
      d.get('item_renumberdeepkeysnoshrink', False))
    
    keyIsPoint = (
      d.get('item_renumberpointsdirectkeys', False) or
      d.get('item_renumberpointsdeepkeys', False))
    
    keyIsPC = (
      d.get('item_renumberpcsdirectkeys', False) or
      d.get('item_renumberpcsdeepkeys', False))
    
    if sum([keyIsGlyph, keyIsPoint, keyIsPC]) > 1:
        raise ValueError("Keys cannot be glyphs and/or points and/or PCs!")
    
    valueIsGlyph = (
      d.get('item_renumberdirectvalues', False) or
      d.get('item_valueisoutputglyph', False))
    
    valueIsPoint = d.get('item_renumberpointsdirect', False)
    valueIsPC = d.get('item_renumberpcsdirect', False)
    
    if sum([valueIsGlyph, valueIsPoint, valueIsPC]) > 1:
        raise ValueError("Values cannot be glyphs and/or points and/or PCs!")
    
    mapOverlapProhibited = d.get('map_mergechecknooverlap', False)
    mapOverlapRequired = d.get('map_mergecheckequalkeysets', False)
    
    if mapOverlapProhibited and mapOverlapRequired:
        raise ValueError("Cannot both require and prohibit merge overlaps!")
    
    if 'map_validatefunc_partial' in d and 'map_validatefunc' in d:
        raise ValueError(
          "Cannot specify both a map_validatefunc_partial "
          "and a map_validatefunc.")
    
    if 'item_validatefunc_partial' in d and 'item_validatefunc' in d:
        raise ValueError(
          "Cannot specify both an item_validatefunc_partial "
          "and an item_validatefunc.")
    
    if 'item_validatefunckeys_partial' in d and 'item_validatefunckeys' in d:
        raise ValueError(
          "Cannot specify both an item_validatefunckeys_partial "
          "and an item_validatefunckeys.")
    
    if ('item_validatekwargsfunc' in d) and ('item_followsprotocol' not in d):
        raise ValueError(
          "Cannot specify an item_validatekwargsfunc unless "
          "item_followsprotocol is also True.")
    
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
    
    if 'item_allowfakeglyphkeys' in d:
        if not d.get('item_renumberdirectkeys', False):
            raise ValueError(
              "Fake glyphs are permitted as keys, but keys are not "
              "designated as glyph indices!")
    
    if 'item_allowfakeglyphvalues' in d:
        if not d.get('item_renumberdirectvalues', False):
            raise ValueError(
              "Fake glyphs are permitted as values, but values are not "
              "designated as glyph indices!")

# -----------------------------------------------------------------------------

#
# Metaclasses
#

if 0:
    def __________________(): pass

class FontDataMetaclass(type):
    """
    Metaclass for dict-like classes. If this metaclass is applied to a class
    whose base class (or one of whose base classes) is already one of the
    FontData classes, the seqSpec and attrSpec will define additions to the
    original. In this case, if an 'attrSorted' is provided, it will be used for
    the combined attributes (original and newly-added); otherwise the new
    attributes will be added to the end of the attrSorted list.
    
    >>> class D1(dict, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_strusesrepr = True)
    ...     attrSpec = dict(
    ...         attr1 = dict())
    >>> print(D1({2: 'x', 3: 'y'}, attr1=10))
    {2: 'x', 3: 'y'}, attr1 = 10
    
    >>> class D2(D1, metaclass=FontDataMetaclass):
    ...     mapSpec = dict(
    ...         item_pprintlabelfunc = (lambda k: 'Z/' + str(k)))
    ...     attrSpec = dict(
    ...         attr2 = dict())
    ...     attrSorted = ('attr2', 'attr1')
    >>> print(D2({2: 'x', 3: 'y'}, attr1=10, attr2=9))
    {Z/2: 'x', Z/3: 'y'}, attr2 = 9, attr1 = 10
    """
    
    def __new__(mcl, classname, bases, classdict):
        v = ['_MAPSPEC' in c.__dict__ for c in reversed(bases)]
        
        if any(v):
            c = bases[v.index(True)]
            MS = c._MAPSPEC.copy()
            MS.update(classdict.pop('mapSpec', {}))
            classdict['_MAPSPEC'] = classdict['_MAIN_SPEC'] = MS
            _validateMapSpec(MS)
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
            d = classdict['_MAPSPEC'] = classdict.pop('mapSpec', {})
            classdict['_MAIN_SPEC'] = d
            _validateMapSpec(d)
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
