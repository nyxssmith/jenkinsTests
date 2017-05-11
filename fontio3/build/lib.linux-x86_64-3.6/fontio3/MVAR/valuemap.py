#
# valuemap.py
#
# Copyright © 2016-2017 Monotype Imaging Inc. All Rights Reserved.
#

"""
Support for ValueMaps in the MVAR table.
"""

# Other imports
from fontio3.fontdata import mapmeta
from fontio3.utilities import isValidAxisTag

# -----------------------------------------------------------------------------

#
# Private constants
#

_REGISTERED_VALUE_TAGS = {
    # map of MVAR tag to (description, function to retrieve from Editor, isYCoord)
    'hasc': ('horizontal ascender', lambda x: x[b'OS/2'].sTypoAscender, True),
    'hdsc': ('horizontal descender', lambda x: x[b'OS/2'].sTypoDescender, True),
    'hlgp': ('horizontal line gap', lambda x: x[b'OS/2'].sTypoLineGap, True),
    'hcla': ('horizontal clipping ascent', lambda x: x[b'OS/2'].usWinAscent, True),
    'hcld': ('horizontal clipping descent', lambda x: x[b'OS/2'].usWinDescent, True),
    'vasc': ('vertical ascender', lambda x: x.vhea.ascent, False),
    'vdsc': ('vertical descender', lambda x: x.vhea.descent, False),
    'vlgp': ('vertical line gap', lambda x: x.vhea.lineGap, False),
    'hcrs': ('horizontal caret rise', lambda x: x.hhea.caretSlopeRise, True),
    'hcrn': ('horizontal caret run', lambda x: x.hhea.caretSlopeRun, False),
    'hcof': ('horizontal caret offset', lambda x: x.hhea.caretOffset, False),
    'vcrs': ('vertical caret rise', lambda x: x.vhea.caretSlopeRise, False),
    'vcrn': ('vertical caret run', lambda x: x.vhea.caretSlopeRun, True),
    'vcof': ('vertical caret offset', lambda x: x.vhea.caretOffset, True),
    'xhgt': ('x height', lambda x: x[b'OS/2'].sxHeight, True),
    'cpht': ('cap height', lambda x: x[b'OS/2'].sCapHeight, True),
    'sbxs': ('subscript em x size', lambda x: x[b'OS/2'].ySubscriptXSize, False),
    'sbys': ('subscript em y size', lambda x: x[b'OS/2'].ySubscriptYSize, True),
    'sbxo': ('subscript em x offset', lambda x: x[b'OS/2'].ySubscriptXOffset, False),
    'sbyo': ('subscript em y offset', lambda x: x[b'OS/2'].ySubscriptYOffset, True),
    'spxs': ('superscript em x size', lambda x: x[b'OS/2'].ySuperscriptXSize, False),
    'spys': ('superscript em y size', lambda x: x[b'OS/2'].ySuperscriptYSize, True),
    'spxo': ('superscript em x offset', lambda x: x[b'OS/2'].ySuperscriptXOffset, False),
    'spyo': ('superscript em y offset', lambda x: x[b'OS/2'].ySuperscriptYOffset, True),
    'strs': ('strikeout size', lambda x: x[b'OS/2'].yStrikeoutSize, True),
    'stro': ('strikeout offset', lambda x: x[b'OS/2'].yStrikeoutPosition, True),
    'unds': ('underline size', lambda x: x.post.header.underlineThickness, True),
    'undo': ('underline offset', lambda x: x.post.header.underlinePosition, True),
    'gsp0': ('gaspRange[0]', lambda x: sorted(x.gasp.keys())[0], False),
    'gsp1': ('gaspRange[1]', lambda x: sorted(x.gasp.keys())[1], False),
    'gsp2': ('gaspRange[2]', lambda x: sorted(x.gasp.keys())[2], False),
    'gsp3': ('gaspRange[3]', lambda x: sorted(x.gasp.keys())[3], False),
    'gsp4': ('gaspRange[4]', lambda x: sorted(x.gasp.keys())[4], False),
    'gsp5': ('gaspRange[5]', lambda x: sorted(x.gasp.keys())[5], False),
    'gsp6': ('gaspRange[6]', lambda x: sorted(x.gasp.keys())[6], False),
    'gsp7': ('gaspRange[7]', lambda x: sorted(x.gasp.keys())[7], False),
    'gsp8': ('gaspRange[8]', lambda x: sorted(x.gasp.keys())[8], False),
    'gsp9': ('gaspRange[9]', lambda x: sorted(x.gasp.keys())[9], False)}

_GASPTAGS = {'gsp0', 'gsp1', 'gsp2', 'gsp3', 'gsp4', 'gsp5', 'gsp6', 'gsp7'
             'gsp8', 'gsp9'}
_OS21TAGS = {'hcla', 'hcld', 'sbxs', 'sbys', 'sbxo', 'sbyo', 'spxs', 'spys', 
             'spxo', 'spyo', 'strs', 'stro'}
_OS22TAGS = {'hasc', 'hdsc', 'xhgt', 'cpht'}
_VHEATAGS = {'vasc', 'vdsc', 'vlgp', 'vcrs', 'vcrn', 'vcof'}

# -----------------------------------------------------------------------------

#
# Private functions
#

def _validate(d, **kwArgs):
    """
    isValid() validation for whole ValueMap object.
    """
    
    logger = kwArgs['logger']
    editor = kwArgs['editor']
    
    isOK = True

    for valueTag in sorted(d):

        # check tags are registered or are valid private tags
        if valueTag in _REGISTERED_VALUE_TAGS:
            tagDesc = _REGISTERED_VALUE_TAGS.get(valueTag)[0]
            logger.info((
              'V1095',
              (valueTag, tagDesc),
              "'%s' is a registered value tag (%s)."))

        elif isValidAxisTag(valueTag, minimallyValid=True):
            logger.warning((
              'V1095',
              (valueTag,),
              "'%s' is not a registered value tag."))

        else:
            logger.error((
              'V1095',
              (valueTag,),
              "'%s' is neither a registered value tag nor a valid private tag."))
            
            isOK = False

    alltags = set(d)
    requireOS2_v1 = sorted(alltags.intersection(_OS21TAGS))
    requireOS2_v2 = sorted(alltags.intersection(_OS22TAGS))
    requirevhea = sorted(alltags.intersection(_VHEATAGS))
    requiregasp = sorted(alltags.intersection(_GASPTAGS))

    hasOS2 = editor.reallyHas(b'OS/2')
    
    vcnt = len(d)
    if len(d):
        logger.info((
          'Vxxxx',
          (vcnt,),
          "%d Value Records."))
    else:
        logger.warning((
          'Vxxxx',
          (),
          "No Value Records defined!"))
        # still valid, but dumb.
    
    if requireOS2_v1:
        if hasOS2 and editor[b'OS/2'].version >= 1:
            logger.info((
              'V1096',
              (),
              "Version 1 or greater OS/2 table is present"))
        else:
            logger.error((
              'V1096',
              (requireOS2_v1,),
              "valueTags %s require an OS/2 table version 1 or higher "
              "but the table is not present, is damaged, or is the wrong "
              "version."))
            isOK = False

    if requireOS2_v2:
        if hasOS2 and editor[b'OS/2'].version >= 2:
            logger.info((
              'V1096',
              (),
              "Version 1 or greater OS/2 table is present"))
        else:
            logger.error((
              'V1096',
              (requireOS2_v2,),
              "valueTags %s require an OS/2 table version 2 or higher "
              "but the table is not present, is damaged, or is the wrong "
              "version."))
            isOK = False

    if requirevhea:
        if editor.reallyHas(b'vhea'):
            logger.info((
              'V1096',
              (),
              "vhea table present."))
        else:
            logger.error((
              'V1096',
              (requirevhea,),
              "valueTags %s require a vhea table, but the table is not "
              "present or is damaged."))
            isOK = False

    if requiregasp:
        if editor.reallyHas(b'gasp'):
            logger.info((
              'V1096',
              (),
              "gasp table present."))

            # from the spec: "The maximum number of value records for 'gasp'
            # entries must never be more than one less the number of entries in
            # the 'gasp' table."
            limit = len(editor.gasp) - 1
            if len(requiregasp) > limit:
                logger.error((
                  'V1097',
                  (),
                  "The number of MVAR value records for gasp settings is "
                  "not in sync with the number of entries in the gasp table"))
                  
                isOK = False
              
        else:
            logger.error((
              'V1096',
              (requiregasp,),
              "valueTags %s require a gasp table, but the table is not "
              "present or is damaged"))
            isOK = False

    return isOK

# -----------------------------------------------------------------------------

#
# Classes
#

class ValueMap(dict, metaclass=mapmeta.FontDataMetaclass):
    """
    Objects mapping value tags to LivingDeltas.
    
    >>> fakeIVS = {(0, 0): 'FakeLivingDelta0', (0, 1): 'FakeLivingDelta1'}
    >>> vm = ValueMap({'unds': fakeIVS[(0,0)], 'Test': fakeIVS[(0, 1)]})
    >>> logger=utilities.makeDoctestLogger('test')
    >>> ed = utilities.fakeEditor(100)
    >>> vm.isValid(logger=logger, editor=ed)
    test - WARNING - 'Test' is not a registered value tag.
    test - INFO - 'unds' is a registered value tag (underline size).
    test - INFO - 2 Value Records.
    True

    >>> logger.logger.setLevel("WARNING")
    >>> vm = ValueMap({'hcla': fakeIVS[(0,0)], 'hasc': fakeIVS[(0,1)], 
    ...                'vasc': fakeIVS[(0,1)], 'gsp0': fakeIVS[(0,0)]})
    >>> vm.isValid(logger=logger, editor=ed)
    test - ERROR - valueTags ['hcla'] require an OS/2 table version 1 or higher but the table is not present, is damaged, or is the wrong version.
    test - ERROR - valueTags ['hasc'] require an OS/2 table version 2 or higher but the table is not present, is damaged, or is the wrong version.
    test - ERROR - valueTags ['vasc'] require a vhea table, but the table is not present or is damaged.
    test - ERROR - valueTags ['gsp0'] require a gasp table, but the table is not present or is damaged
    False
    
    >>> logger.logger.setLevel("INFO")
    >>> ed[b'OS/2'] = OS_2_v3.OS_2()
    >>> ed.vhea = vhea_v11.Vhea()
    >>> ed.gasp = gasp.Gasp()
    >>> vm.isValid(logger=logger, editor=ed)
    test - INFO - 'gsp0' is a registered value tag (gaspRange[0]).
    test - INFO - 'hasc' is a registered value tag (horizontal ascender).
    test - INFO - 'hcla' is a registered value tag (horizontal clipping ascent).
    test - INFO - 'vasc' is a registered value tag (vertical ascender).
    test - INFO - 4 Value Records.
    test - INFO - Version 1 or greater OS/2 table is present
    test - INFO - Version 1 or greater OS/2 table is present
    test - INFO - vhea table present.
    test - INFO - gasp table present.
    test - ERROR - The number of MVAR value records for gasp settings is not in sync with the number of entries in the gasp table
    False
    """

    #
    # Class definition variables
    #

    mapSpec = dict(
        item_valueislivingdeltas = True,
        map_validatefunc = _validate)

    #
    # Methods
    #

    def buildBinary(self, w, **kwArgs):
        """
        Adds the binary data for the ValueMap object to the specified
        LinkedWriter.

        The following kwArg is required:
        
            ldmap   a map of LivingDeltas to (outerIndex, innerIndex) Delta Set keys.

        >>> fakeLDmap = {'FakeLivingDelta0': (0,0), 'FakeLivingDelta1': (0, 1)}
        >>> vm = ValueMap({'unds': 'FakeLivingDelta0', 'Test': 'FakeLivingDelta1'})
        >>> utilities.hexdump(vm.binaryString(ldmap=fakeLDmap))
               0 | 5465 7374 0000 0001  756E 6473 0000 0000 |Test....unds....|
        """

        if 'stakeValue' in kwArgs:
            stakeValue = kwArgs.pop('stakeValue')
            w.stakeCurrentWithValue(stakeValue)

        else:
            stakeValue = w.stakeCurrent()

        ldmap = kwArgs.pop('ldmap')

        for k, v in sorted(self.items()):
            safe_k = (k + "    ")[0:4].encode('ascii')
            outer, inner = ldmap.get(v)

            w.addString(safe_k)
            w.add("H", outer)
            w.add("H", inner)


    @classmethod
    def fromvalidatedwalker(cls, w, **kwArgs):
        """
        Like fromwalker(), but with validation.

        The following kwArgs are recognized:
        
            ivs         a fontio IVS object mapping DeltaSetIndices to LivingDeltas

            logger      a logging.logger-like object for receiving logger messages.
            
            recordCount the count of values in the map (from header)
            
        
        >>> logger = utilities.makeDoctestLogger('test')
        >>> s = ("41 42 43 44 00 01 00 02 61 62 63 64 00 05 00 07")
        >>> b = utilities.fromhex(s)
        >>> fakeIVS = {(5, 7): 'FakeLivingDelta0', (1, 2): 'FakeLivingDelta1'}
        >>> fvb  = ValueMap.fromvalidatedbytes
        >>> obj = fvb(b, logger=logger, recordCount=2, ivs=fakeIVS)
        test.valuemap - DEBUG - Walker has 16 remaining bytes.
        test.valuemap - DEBUG - Tag: b'ABCD': (1, 2)
        test.valuemap - DEBUG - Tag: b'abcd': (5, 7)
        >>> obj['abcd']
        'FakeLivingDelta0'

        >>> logger.logger.setLevel("WARNING")
        >>> s = ("61 62 63 64 00 05 00 07 41 42 43 44 00 01 00 02 ")
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, logger=logger, recordCount=2, ivs=fakeIVS)
        test.valuemap - ERROR - valueTags are not stored in sorted order
        
        >>> obj = fvb(b'ZZx', logger=logger, recordCount=99, ivs=fakeIVS)
        test.valuemap - ERROR - Insufficient bytes.

        >>> s = ("93 62 63 64 00 05 00 07 ")
        >>> b = utilities.fromhex(s)
        >>> obj = fvb(b, logger=logger, recordCount=1, ivs=fakeIVS)
        test.valuemap - ERROR - valueTag b'\x93bcd' does not consist of ASCII characters
        """

        ivs = kwArgs['ivs']
        logger = kwArgs.pop('logger', None)
        recordCount = kwArgs['recordCount']

        if logger is None:
            logger = logging.getLogger().getChild('valuemap')
        else:
            logger = logger.getChild('valuemap')

        logger.debug((
          'V0001',
          (w.length(),),
          "Walker has %d remaining bytes."))

        d = {}

        rawTagOrder = []
        for r in range(recordCount):

            if w.length() < 8:
                logger.error(('V0004', (), "Insufficient bytes."))
                return None

            tag, outer, inner = w.unpack("4s2H")

            logger.debug(('Vxxxx', (tag, outer, inner), "Tag: %s: (%d, %d)"))

            try:
                tag_ascii = tag.decode('ascii')
            except UnicodeDecodeError:
                logger.error((
                  'Vxxxx',
                  (tag,),
                  "valueTag %s does not consist of ASCII characters"))
                tag_ascii = (tag.decode('ascii', errors='ignore') + "    ")[0:4]

            rawTagOrder.append(tag_ascii)

            if (outer, inner) in ivs:
                d[tag_ascii] = ivs[(outer, inner)]
            else:
                logger.error((
                  'Vxxxx',
                  (outer, inner),
                  "No Deltas for index (%d, %d) in Item Variation Store!"))
                return None

        if rawTagOrder != sorted(rawTagOrder):
            logger.error((
              'Vxxxx',
              (),
              "valueTags are not stored in sorted order"))

        return cls(d)


    @classmethod
    def fromwalker(cls, w, **kwArgs):
        """
        Creates and returns a new ValueMap object from the specified walker.

        The following kwArgs are recognized:
        
            ivs         a fontio IVS object mapping DeltaSetIndices to LivingDeltas

            recordCount the count of values in the map (from header)

        >>> s = ("41 42 43 44 00 01 00 02 61 62 63 64 00 05 00 07")
        >>> b = utilities.fromhex(s)
        >>> fakeIVS = {(5, 7): 'FakeLivingDelta0', (1, 2): 'FakeLivingDelta1'}
        >>> fb = ValueMap.frombytes
        >>> obj = fb(b, recordCount=2, ivs=fakeIVS)
        >>> obj.pprint()
        'ABCD': FakeLivingDelta1
        'abcd': FakeLivingDelta0
        """

        ivs = kwArgs['ivs']
        recordCount = kwArgs['recordCount']
        d = {}

        for r in range(recordCount):
            tag, outer, inner = w.unpack("4s2H")
            tag_ascii = tag.decode('ascii')
            d[tag_ascii] = ivs.get((outer, inner))

        return cls(d)


# -----------------------------------------------------------------------------

#
# Test code
#

if 0:
    def __________________(): pass

if __debug__:
    from fontio3 import utilities
    from fontio3.gasp import gasp
    from fontio3.OS_2 import OS_2_v3
    from fontio3.vhea import vhea_v11

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if __debug__:
        _test()


