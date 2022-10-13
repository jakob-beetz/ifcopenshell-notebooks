import ifcopenshell
import uuid
from graphviz import Digraph
import networkx as nx


## If you are reading this, and are interested, please helpme to reimplement this in networkx!
## TODO Jakob

class IfcGraphViz:
    node_attr = dict(
        shape='record',
        align='left',
        fontsize='8',
        fontname='Arial',
        ranksep='0.1',
        height='0.2',
        width='1',
    )
    edge_attr = dict(
        fontsize='8',
        fontname='Arial',
    )

    nodes = None
    edges = None
    graph = None

    def __init__(self):
        # initializes the attributes specified above
        self.nx_graph = nx.DiGraph()

    def build_nx_graph(self, model, entity_instance, forward=10):

        # create node for current entity instance
        self.nx_graph.add_node(entity_instance.id())
        # extract entity attributes
        entity_attributes = entity_instance.get_info()
        # remove p21 id as it is used as the node identifier and not inside the attributes of a node
        del entity_attributes["id"]
        # loop over attributes and traverse
        if forward >= 0:
            for attr, val in entity_attributes.items():
                if type(val) == ifcopenshell.entity_instance:
                    # build child node and traverse
                    self.nx_graph = self.build_nx_graph(model, val, forward=forward - 1)
                    # build connecting edge
                    self.nx_graph.add_edge(entity_instance.id(), val.id(), label=attr)

                elif type(val) == tuple:
                    if len(val) == 0:
                        self.graph = self.build_nx_graph(model, val[0], forward=forward - 1)
                        self.graph.edge(str(entity_instance.id()), str(val[0].id()), label=attr)

        # finally set node attributes
        node_attributes = {entity_instance.id(): entity_attributes}
        nx.set_node_attributes(self.nx_graph, node_attributes)

        return self.nx_graph

    def plot_graph(self, model, node, forward=10, direction="LR"):
        """
        Prints all entity instances that are associated under the specified node
        :param model: an IFC model loaded into IfcOpenShell
        :param node: the entity instance in question
        :param forward: integer that specifies the number of traversals that should be considered
        :param graph:
        :param direction:
        :return:
        """
        if not self.graph:
            self.graph = Digraph(node_attr=self.node_attr, edge_attr=self.edge_attr)
            self.graph.attr(rankdir=direction, fontname="Arial", fontsize="8")
            self.nodes = []
            self.edges = []

        info_str = """"""
        if forward >= 0:
            for attr, val in node.get_info().items():
                if type(val) == ifcopenshell.entity_instance:

                    self.graph = self.plot_graph(model, val, forward=forward - 1)
                    self.graph.edge(str(node.id()), str(val.id()), label=attr)
                elif type(val) == tuple:
                    if len(val) == 0:
                        self.graph = self.plot_graph(model, val[0], forward=forward - 1)
                        self.graph.edge(str(node.id()), str(val[0].id()), label=attr)


                else:
                    if attr == "id":
                        info_str += str(f"#{val} \\n")
                    elif attr == "type":
                        info_str += str(f"({val}) \\n\\n")
                    else:
                        info_str += str(f"{attr} : {val} \\l")

            # print(info_str)
            node = self.graph.node(name=str(node.id()), label=info_str)

        return self.graph

    def plot_reverse_graph(self, model, node, reverse=3, graph=None, direction="LR"):

        ## TODO: backwards
        if not graph:
            self.graph = Digraph(node_attr=self.node_attr, edge_attr=self.edge_attr)
            self.graph.attr(rankdir=direction, fontname="Arial", fontsize="8")
        info_str = f"#{node.id()}"
        # self.graph = self.plot_graph(model, node, forward=1, graph=self.graph)
        if reverse >= 0 and node:
            inverse_rels = model.get_inverse(node)
            for inverse in inverse_rels:
                # print (f"{type(inverse)}: {inverse}")
                if type(inverse) == ifcopenshell.entity_instance:

                    for attr, value in inverse.get_info().items():
                        if type(value) == ifcopenshell.entity_instance:
                            if value.id() == inverse.id():
                                # self.graph = self.plot_graph(model, inverse, forward=1, graph=self.graph)

                                self.graph.node(name=str(value.id()), label=info_str)
                                self.graph.edge(str(reverse.id()), str(value.id()), label=attr)
                        if type(value) == tuple:
                            for item in value:
                                if type(item) == ifcopenshell.entity_instance:
                                    if item.id() == node.id():
                                        # self.graph = self.plot_graph(model, node, forward=1, graph=self.graph)
                                        self.graph.node(name=str(item.id()), label=info_str)
                                        self.graph.edge(str(inverse.id()), str(item.id()), label=attr)

            # print(info_str)
        node = self.graph.node(name=str(node.id()), label=info_str)
        return self.graph

    def plot_relation_graph(self, m, node, relationships=["IfcRelContainedInSpatialStructure", "IfcRelVoidsElement",
                                                          "IfcRelFillsElement", "IfcRelAggregates"],
                            depth=1):
        dot = Digraph(node_attr=self.node_attr, edge_attr=self.edge_attr)
        dot.attr(rankdir='TD', fontname="Arial", fontsize="8")
        # relations = m.by_type("IfcRelationship")
        temp_relations = m.get_inverse(node)

        relations = []
        for rel in temp_relations:
            # print(rel)
            if rel.is_a().startswith("IfcRel"):
                # print(f"added    {rel}")
                relations.append(rel)

        for relation in relations:

            if relation.is_a() in relationships or len(relationships) == 0:
                relatedNodeId = None

                # dot.node(relation.GlobalId)
                for key, value in relation.get_info().items():
                    if key.startswith("Relating") and value.id == node.id:
                        # print("Relating"))
                        dot.node(getattr(value, "GlobalId", f'#{value.id}'),
                                 f'name:{getattr(value, "Name", value.id)} ‚\n {value.is_a()}')
                        relatedNodeId = getattr(value, "GlobalId", f"#{value.id}")

                    if key.startswith("Related"):
                        # print (type(value))
                        if type(value) == ifcopenshell.entity_instance:

                            dot.node(getattr(value, "GlobalId", "No Id"), getattr(value, "Name", "NaN"))
                        elif type(value) == tuple:
                            for related in value:
                                # print (value) 
                                dot.node(getattr(related, "GlobalId", "No GlobalId"),
                                         f'name:{getattr(related, "Name", "no name")}\n {related.is_a()} ')

                for key, value in relation.get_info().items():

                    if key.startswith("Related"):
                        # print (type(value))
                        if type(value) == ifcopenshell.entity_instance and relatedNodeId:
                            dot.edge(relatedNodeId, getattr(value, "GlobalId", "none"))
                        elif relatedNodeId:
                            for related in value:
                                dot.edge(relatedNodeId, getattr(related, "GlobalId", "none"))

                    # print (f'\t\t{key}  : \t\t\t{value}')
        return dot
