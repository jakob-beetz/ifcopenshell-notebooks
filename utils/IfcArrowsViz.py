from pprint import pprint

import jsonpickle
import ifcopenshell


class IFCArrowsGraphGenerator:
    """
    IfcP21 to arrows.apo (and a bit of neo4j) mapper.
    Translates a given IFC model in P21 encoding into a propertyGraph representation
    """

    def __init__(self, model_path):
        """
        @param model_path: the path to the model to be processed
        """

        # try to open the ifc model and load the content into the model variable
        try:
            self.model_path = model_path
            self.model = ifcopenshell.open(model_path)
            ifc_version = self.model.schema
            self.schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(
                ifc_version)
        except:
            print('file path: {}'.format(model_path))
            raise Exception('Unable to open IFC model on given file path')

    def generate_arrows_visualization(self, ignore_null_values: bool = False):
        """
        creates a json that can be used for arrows.app visualization
        @ignore_null_values: only parse those attributes that are not None
        """

        # load base json
        with open("utils/base_arrows_format.json") as f:
            content = f.read()
        arrows = jsonpickle.decode(content)

        x_pos = 0
        y_pos = 0

        # ToDo: enhance layout and initial positioning of all nodes

        rel_counter = 0
        for entity in self.model:

            # get node data
            attr_dict, entity_type = self.__extract_node_data(entity=entity)

            # escape lists into strings
            for key, val in attr_dict.items():
                if type(val) in [list, tuple, dict]:
                    attr_dict[key] = str(val)

            if ignore_null_values:
                new_dict = {k: v for k, v in attr_dict.items() if v is not None}
                attr_dict = new_dict

            # check if the primary_node_type is either an ObjectDef or Relationship or neither of them.
            # These labels are relevant to control the color-coding.
            if entity.is_a('IfcObjectDefinition'):
                node_type = "PrimaryNode"
            elif entity.is_a('IfcRelationship'):
                node_type = "ConnectionNode"
            else:
                node_type = "SecondaryNode"

            node_identifier = attr_dict['p21_id']
            attr_dict.pop("p21_id")

            node_border_colors = {"PrimaryNode": "#0062b1",
                                  "SecondaryNode": "#fcc400",
                                  "ConnectionNode": "#68bc00"}

            # build arrows expression
            arrows_node = {
                "id": "n" + str(node_identifier),
                "position": {
                    "x": x_pos,
                    "y": y_pos
                },
                "caption": str(node_identifier),
                "style": {
                    "border-color": node_border_colors[node_type],
                    "radius": 20
                    # "outside-position": "top"
                },
                "properties": attr_dict,

            }
            arrows["nodes"].append(arrows_node)

            x_pos += 100

            # process relationships
            _, single_associations, aggregated_associations = self.__separate_attributes(entity)

            for assoc in single_associations:
                # get relationship target
                target = entity.get_info()[assoc]

                # association target may be set to None, then continue
                if target is None:
                    continue

                # build arrows expression
                rel = {
                    "id": "n" + str(rel_counter),
                    "type": "REL",
                    "style": {},
                    "type": assoc,
                    "fromId": "n" + str(node_identifier),
                    "toId": "n" + str(target.get_info()["id"])
                }

                arrows["relationships"].append(rel)

                rel_counter += 1

            # process lists of relationships
            list_item = 0
            for agg_assoc in aggregated_associations:
                targets = entity.get_info()[agg_assoc]

                for target in targets:
                    if target is None:
                        continue

                    # build arrows expression
                    rel = {
                        "id": "n" + str(rel_counter),
                        "type": "REL",
                        "style": {},
                        "type": agg_assoc,
                        "properties": {
                            "listItem": str(list_item)
                        },
                        "fromId": "n" + str(node_identifier),
                        "toId": "n" + str(target.get_info()["id"])
                    }

                    arrows["relationships"].append(rel)
                    list_item += 1

                rel_counter += 1

        return arrows

        # save
        # f = open(r"tmp_graph.json", 'w')
        # f.write(jsonpickle.dumps(arrows, unpicklable=True))
        # f.close()

    def __separate_attributes(self, entity) -> tuple:
        """"
        processes the node attributes and separates attributes with atomic data types from pointers
        @primary_node_type:
        @return:
        """
        info = entity.get_info()
        clsName = info['type']
        entity_id = info['id']

        # separate attributes into node attributes, simple associations, and sets of associations
        node_attributes = []
        single_associations = []
        aggregated_associations = []

        try:
            class_definition = self.schema.declaration_by_name(
                clsName).all_attributes()
        except:
            raise Exception("Failed to query schema specification in IFC2GraphTranslator.\n "
                            "Schema: {}, Entity: {} ".format(self.schema, clsName))

        for attr in class_definition:

            try:
                attr_type = attr.type_of_attribute().declared_type()
            except:
                attr_type = attr.type_of_attribute()

            # get the value structure
            is_entity = isinstance(
                attr_type, ifcopenshell.ifcopenshell_wrapper.entity)
            is_type = isinstance(
                attr_type, ifcopenshell.ifcopenshell_wrapper.type_declaration)
            is_select = isinstance(
                attr_type, ifcopenshell.ifcopenshell_wrapper.select_type)

            is_pdt_select = False
            is_entity_select = False
            is_nested_select = False
            is_enumeration = isinstance(
                attr_type, ifcopenshell.ifcopenshell_wrapper.enumeration_type)
            is_aggregation = isinstance(
                attr_type, ifcopenshell.ifcopenshell_wrapper.aggregation_type)

            # ToDo: Distinguish if it is a select of entities or a select of predefinedTypes
            if is_select:
                # methods = attr.type_of_attribute().declared_type()
                # print(dir(methods))
                lst = attr.type_of_attribute().declared_type().select_list()

                is_entity_select = all(
                    [isinstance(x, ifcopenshell.ifcopenshell_wrapper.entity) for x in lst])
                is_pdt_select = all(
                    [isinstance(x, ifcopenshell.ifcopenshell_wrapper.type_declaration) for x in lst])
                is_nested_select = all(
                    [isinstance(x, ifcopenshell.ifcopenshell_wrapper.select_type) for x in lst])

                # handle mixed cases
                if isinstance(lst[0], ifcopenshell.ifcopenshell_wrapper.entity) \
                        and isinstance(lst[1], ifcopenshell.ifcopenshell_wrapper.type_declaration):
                    is_aggregation = True

            # catch some weird cases with IfcDimensionalExponents
            #  as this primary_node_type doesnt use types but atomic attr declarations
            if attr.name() in ['LengthExponent',
                               'MassExponent',
                               'TimeExponent',
                               'ElectricCurrentExponent',
                               'ThermodynamicTemperatureExponent',
                               'AmountOfSubstanceExponent',
                               'LuminousIntensityExponent',
                               'Exponent',  # from IfcDerivedUnitElement
                               'Precision',  # from IfcGeometricRepresentationContext
                               'Scale',  # from IfcCartesianPointTransformationOperator3D in 2x3
                               'Orientation',  # from IfcFaceOuterBound in 2x3
                               'SelfIntersect',  # from IfcCompositeCurve in 2x3
                               'SameSense',  # from IfcCompositeCurveSegment in IFC2x3
                               'SenseAgreement',  # from IfcTrimmedCurve in IFC2x3
                               'AgreementFlag',  # from IfcPolygonalBoundedHalfSpace
                               'ParameterTakesPrecedence',
                               'ClosedCurve',
                               'SelfIntersect',
                               'LayerOn',
                               'LayerFrozen',
                               'LayerBlocked',
                               'ProductDefinitional',
                               'Scale2',  # IfcCartesianTransformationOperator2DnonUniform
                               'Scale3',
                               'RelatedPriorities',
                               'RelatingPriorities',
                               'SameSense',
                               'AgreementFlag',
                               'USense',
                               'VSense',
                               'WeightsData',
                               'Weights',
                               'Sizeable',
                               'ParameterTakesPrecedence',
                               'IsCritical',
                               'DestabilizingLoad',
                               'IsLinear',
                               'RepeatS',
                               'RepeatT',
                               'IsHeading',
                               'IsMilestone',
                               'Priority',
                               'SenseAgreement',
                               'IsPotable',
                               'NumberOfRiser',
                               'NumberOfTreads',
                               'Pixel',
                               'InputPhase',
                               'Degree',
                               'CurveFont',
                               'DiffuseColour',
                               'TransmissionColour',
                               'DiffuseTransmissionColour',
                               'ReflectionColour',
                               'SpecularColour',
                               'ColourList',
                               'ColourIndex',
                               'NominalValue',
                               'AddressLines'

                               ]:
                node_attributes.append(attr.name())

            elif is_type or is_enumeration or is_pdt_select or is_nested_select:
                node_attributes.append(attr.name())
            elif is_entity or is_entity_select:
                single_associations.append(attr.name())
            elif is_aggregation:
                # ToDo: check if it is an aggregation of types or an aggregation of entities
                # https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/link/ifctrimmedcurve.htm -> trimSelect
                if attr.name() in [
                    'Coordinates',
                    'DirectionRatios',
                    'CoordList',
                    'segments',
                    'MiddleNames',
                    'PrefixTitles',
                    'SuffixTitles',
                    'Roles',
                    'Addresses',
                    'CoordIndex',
                    'InnerCoordIndices',
                    'Trim1',
                    'Trim2',
                    'Orientation',
                    'RefLongitude',
                    'RefLatitude',
                    'NominalValue'
                ]:
                    node_attributes.append(attr.name())
                else:
                    aggregated_associations.append(attr.name())
            else:
                raise Exception('Tried to encode the attribute type of primary_node_type #{} clsName: {} attribute {}. '
                                'Please check your graph translator.'.format(entity_id, clsName, attr.name()))
        node_attributes.append('id')
        node_attributes.append('type')
        return node_attributes, single_associations, aggregated_associations

    def __extract_node_data(self, entity):
        """
        extracts the relevant information from a given IFC entity instance. Returns the label,
        @param entity:
        @return:
        """

        # get some basic data
        info = entity.get_info()

        # node_properties, single_associations, aggregated_associations = self.separate_attributes(primary_node_type)
        node_properties, _, _ = self.__separate_attributes(entity)

        # create a dictionary of properties
        node_properties_dict = {}
        for p_name in node_properties:
            p_val = info[p_name]

            if p_name == 'NominalValue':
                wrapped_val = p_val.wrappedValue
                p_val = 'IfcLabel({})'.format(str(wrapped_val).replace("'", ""))
                p_val = str(p_val)
                # ToDo: consider this workaround when translating a graph back in its SPF representation

            node_properties_dict[p_name] = p_val

        # rename some keys
        node_properties_dict['p21_id'] = node_properties_dict.pop('id')
        node_properties_dict['EntityType'] = node_properties_dict.pop('type')

        entity_type = node_properties_dict['EntityType']

        return node_properties_dict, entity_type
