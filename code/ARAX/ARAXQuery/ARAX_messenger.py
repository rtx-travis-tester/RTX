#!/bin/env python3
import sys
def eprint(*args, **kwargs): print(*args, file=sys.stderr, **kwargs)

import os
import json
import ast
import re
from datetime import datetime
import numpy as np
import requests

from response import Response
from query_graph_info import QueryGraphInfo
from knowledge_graph_info import KnowledgeGraphInfo

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../")
from RTXConfiguration import RTXConfiguration

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../UI/OpenAPI/python-flask-server/")
from swagger_server.models.message import Message
from swagger_server.models.knowledge_graph import KnowledgeGraph
from swagger_server.models.query_graph import QueryGraph
from swagger_server.models.q_node import QNode
from swagger_server.models.q_edge import QEdge

sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../NodeSynonymizer")
from node_synonymizer import NodeSynonymizer


class ARAXMessenger:

    #### Constructor
    def __init__(self):
        self.response = None
        self.message = None
        self.parameters = None

    def describe_me(self):
        """
        Self-documentation method for internal use that returns the available actions and what they can do
        :return: A list of allowable actions supported by this class
        :rtype: list
        """
        description_list = []
        description_list.append(self.create_message(describe=True))
        description_list.append(self.add_qnode(0,0,describe=True))
        description_list.append(self.add_qedge(0,0,describe=True))
        return description_list


    # #### Create a fresh Message object and fill with defaults
    def create_message(self, describe=False):
        """
        Creates a basic empty Message object with basic boilerplate metadata
        :return: Response object with execution information and the new message object inside the data envelope
        :rtype: Response
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'create_message()',
            'description': """The `create_message` command creates a basic empty Message object with basic boilerplate metadata
                such as reasoner_id, schema_version, etc. filled in. This DSL command takes no arguments. This command is not explicitly
                necessary, as it is called implicitly when needed. e.g. If a DSL program begins with add_qnode(), the
                create_message() will be executed automatically if there is not yet a Message. If there is already Message in memory,
                then this command will destroy the previous one (in memory) and begin a new message.""",
            'parameters': {
            }
        }

        if describe:
            return command_definition





        #### Define a default response
        response = Response()
        self.response = response

        #### Create the top-level message
        response.info("Creating an empty template ARAX Message")
        message = Message()
        self.message = message

        #### Fill it with default information
        message.id = None
        message.type = "translator_reasoner_message"
        message.reasoner_id = "ARAX"
        message.tool_version = RTXConfiguration().version
        message.schema_version = "0.9.3"
        message.message_code = "OK"
        message.code_description = "Created empty template Message"
        message.context = "https://raw.githubusercontent.com/biolink/biolink-model/master/context.jsonld"

        #### Why is this _datetime ?? FIXME
        message._datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

		#### Create an empty master knowledge graph
        message.knowledge_graph = KnowledgeGraph()
        message.knowledge_graph.nodes = []
        message.knowledge_graph.edges = []

		#### Create an empty query graph
        message.query_graph = QueryGraph()
        message.query_graph.nodes = []
        message.query_graph.edges = []

        #### Create empty results
        message.results = []
        message.n_results = 0

        #### Return the response
        response.data['message'] = message
        return response


    ###############################################################################################
    # #### Add a new QNode
    def add_qnode(self, message, input_parameters, describe=False):
        """
        Adds a new QNode object to the QueryGraph inside the Message object
        :return: Response object with execution information
        :rtype: Response
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'add_qnode()',
            'description': """The `add_qnode` method adds an additional QNode to the QueryGraph in the Message object. Currently
                when a curie or name is specified, this method will only return success if a matching node is found in the KG1/KG2 KGNodeIndex.""",
            'parameters': {
                'id': { 
                    'is_required': False,
                    'examples': [ 'n00', 'n01' ],
                    'default': '',
                    'type': 'string',
                    'description': """Any string that is unique among all QNode id fields, with recommended format n00, n01, n02, etc.
                        If no value is provided, autoincrementing values beginning for n00 are used.""",
                    },
                'curie': {
                    'is_required': False,
                    'examples': [ 'DOID:9281', '[UniProtKB:P12345,UniProtKB:Q54321]' ],
                    'type': 'string',
                    'description': 'Any compact URI (CURIE) (e.g. DOID:9281) (May also be a list like [UniProtKB:P12345,UniProtKB:Q54321])',
                    },
                'name': {
                    'is_required': False,
                    'examples': [ 'hypertension', 'insulin' ],
                    'type': 'string',
                    'description': 'Any name of a bioentity that will be resolved into a CURIE if possible or result in an error if not (e.g. hypertension, insulin)',
                    },
                'type': {
                    'is_required': False,
                    'examples': [ 'protein', 'chemical_substance', 'disease' ],
                    'type': 'ARAXnode',
                    'description': 'Any valid Translator bioentity type (e.g. protein, chemical_substance, disease)',
                    },
                'is_set': {
                    'is_required': False,
                    'enum': [ "true", "false", "True", "False", "t", "f", "T", "F" ],
                    'examples': [ 'true', 'false' ],
                    'type': 'boolean',
                    'description': 'If set to true, this QNode represents a set of nodes that are all in common between the two other linked QNodes (assumed to be false if not specified or value is not recognized as true/t case insensitive)'
                    },
            }
        }

        if describe:
            return command_definition

        #### Define a default response
        response = Response()
        self.response = response
        self.message = message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'id': None,
            'curie': None,
            'name': None,
            'type': None,
            'is_set': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Adding a QueryNode to Message with input parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = []
            message.query_graph.edges = []
        if message.query_graph.nodes is None:
            message.query_graph.nodes = []

        #### Set up the NodeSynonymizer to find curies and names
        synonymizer = NodeSynonymizer()

        # Create the QNode and set the id
        qnode = QNode()
        if parameters['id'] is not None:
            id = parameters['id']
        else:
            id = self.__get_next_free_node_id()
        qnode.id = id

        # Set the is_set parameter to what the user selected
        if parameters['is_set'] is not None:
            qnode.is_set = ( parameters['is_set'].lower() == 'true' or parameters['is_set'].lower() == 't' )

        #### If the CURIE is specified, try to find that
        if parameters['curie'] is not None:

            # If the curie is a scalar then treat it here as a list of one
            if isinstance(parameters['curie'], str):
                curie_list = [ parameters['curie'] ]
                is_curie_a_list = False
                if parameters['is_set'] is not None and qnode.is_set is True:
                    response.error(f"Specified CURIE '{parameters['curie']}' is a scalar, but is_set=true, which doesn't make sense", error_code="CurieScalarButIsSetTrue")
                    return response

            # Or else set it up as a list
            elif isinstance(parameters['curie'], list):
                curie_list = parameters['curie']
                is_curie_a_list = True
                qnode.curie = []
                if parameters['is_set'] is None:
                    response.warning(f"Specified CURIE '{parameters['curie']}' is a list, but is_set was not set to true. It must be true in this context, so automatically setting to true. Avoid this warning by explictly setting to true.")
                    qnode.is_set = True
                else:
                    if qnode.is_set == False:
                        response.warning(f"Specified CURIE '{parameters['curie']}' is a list, but is_set=false, which doesn't make sense, so automatically setting to true. Avoid this warning by explictly setting to true.")
                        qnode.is_set = True

            # Or if it's neither a list or a string, then error out. This cannot be handled at present
            else:
                response.error(f"Specified CURIE '{parameters['curie']}' is neither a string nor a list. This cannot to handled", error_code="CurieNotListOrScalar")
                return response

            # Loop over the available curies and create the list
            for curie in curie_list:
                response.debug(f"Looking up CURIE {curie} in NodeSynonymizer")
                synonymizer_results = synonymizer.get_canonical_curies(curies=[curie])

                # If nothing was found, we won't bail out, but rather just issue a warning that this curie is suspect
                if synonymizer_results[curie] is None:
                    response.warning(f"A node with CURIE {curie} is not in our knowledge graph KG2, but will continue with it")
                    if is_curie_a_list:
                        qnode.curie.append(curie)
                    else:
                        qnode.curie = curie

                # And if it is found, keep the same curie but report the preferred curie
                else:

                    response.info(f"CURIE {curie} is found. Adding it to the qnode")
                    if is_curie_a_list:
                        qnode.curie.append(curie)
                    else:
                        qnode.curie = curie

                if 'type' in parameters and parameters['type'] is not None:
                    if isinstance(parameters['type'], str):
                        qnode.type = parameters['type']
                    else:
                        qnode.type = parameters['type'][0]

            message.query_graph.nodes.append(qnode)
            return response

        #### If the name is specified, try to find that
        if parameters['name'] is not None:
            name = parameters['name']
            response.debug(f"Looking up CURIE for name '{name}' in NodeSynonymizer")
            synonymizer_results = synonymizer.get_canonical_curies(curies=[name], names=[name])

            if synonymizer_results[name] is None:
                response.error(f"A node with name '{name}' is not in our knowledge graph", error_code="UnresolvableNodeName")
                return response
 
            qnode.curie = synonymizer_results[name]['preferred_curie']
            response.info(f"Creating QueryNode with curie '{qnode.curie}' for name '{name}'")
            if parameters['type'] is not None:
                qnode.type = parameters['type']
            message.query_graph.nodes.append(qnode)
            return response

        #### If the type is specified, just add that type. There should be checking that it is legal. FIXME
        if parameters['type'] is not None:
            qnode.type = parameters['type']
            if parameters['is_set'] is not None:
                qnode.is_set = (parameters['is_set'].lower() == 'true')
            message.query_graph.nodes.append(qnode)
            return response

        #### If we get here, it means that all three main parameters are null. Just a generic node with no type or anything. This is okay.
        message.query_graph.nodes.append(qnode)
        return response


    ###############################################################################################
    #### Get the next free node id like nXX where XX is a zero-padded integer starting with 00
    def __get_next_free_node_id(self):

        #### Set up local references to the message and verify the query_graph nodes
        message = self.message
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = []
            message.query_graph.edges = []
        if message.query_graph.nodes is None:
            message.query_graph.nodes = []
        qnodes = message.query_graph.nodes

        #### Loop over the nodes making a dict of the ids
        ids = {}
        for qnode in qnodes:
            id = qnode.id
            ids[id] = 1

        #### Find the first unused id
        index = 0
        while 1:
            pad = '0'
            if index > 9:
                pad = ''
            potential_node_id = f"n{pad}{str(index)}"
            if potential_node_id not in ids:
                return potential_node_id
            index += 1


    ###############################################################################################
    #### Add a new QEdge
    def add_qedge(self, message, input_parameters, describe=False):
        """
        Adds a new QEdge object to the QueryGraph inside the Message object
        :return: Response object with execution information
        :rtype: Response
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'add_qedge()',
            'description': """The `add_qedge` command adds an additional QEdge to the QueryGraph in the Message object. Currently
                source_id and target_id QNodes must already be present in the QueryGraph. The specified type is not currently checked that it is a
                valid Translator/BioLink relationship type, but it should be.""",
            'parameters': {
                'id': { 
                    'is_required': False,
                    'examples': [ 'e00', 'e01' ],
                    'default': '',
                    'type': 'string',
                    'description': """Any string that is unique among all QEdge id fields, with recommended format e00, e01, e02, etc.
                        If no value is provided, autoincrementing values beginning for e00 are used.""",
                    },
                'source_id': {
                    'is_required': True,
                    'examples': [ 'n00', 'n01' ],
                    'type': 'string',
                    'description': 'id of the source QNode already present in the QueryGraph (e.g. n00, n01)',
                    },
                'target_id': {
                    'is_required': True,
                    'examples': [ 'n01', 'n02' ],
                    'type': 'string',
                    'description': 'id of the target QNode already present in the QueryGraph (e.g. n01, n02)',
                    },
                'type': {
                    'is_required': False,
                    'examples': [ 'protein', 'physically_interacts_with', 'participates_in' ],
                    'type': 'ARAXedge',
                    'description': 'Any valid Translator/BioLink relationship type (e.g. physically_interacts_with, participates_in)',
                    },
            }
        }

        if describe:
            return command_definition


        #### Define a default response
        response = Response()
        self.response = response
        self.message = message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'id': None,
            'source_id': None,
            'target_id': None,
            'type': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Adding a QueryEdge to Message with parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = []
            message.query_graph.edges = []
        if message.query_graph.edges is None:
            message.query_graph.edges = []

        #### Create a QEdge
        qedge = QEdge()
        if parameters['id'] is not None:
            id = parameters['id']
        else:
            id = self.__get_next_free_edge_id()
        qedge.id = id

        #### Get the list of available node_ids
        qnodes = message.query_graph.nodes
        ids = {}
        for qnode in qnodes:
            id = qnode.id
            ids[id] = 1

        #### Add the source_id
        if parameters['source_id'] is not None:
            if parameters['source_id'] not in ids:
                response.error(f"While trying to add QEdge, there is no QNode with id {parameters['source_id']}", error_code="UnknownSourceId")
                return response
            qedge.source_id = parameters['source_id']
        else:
            response.error(f"While trying to add QEdge, source_id is a required parameter", error_code="MissingSourceId")
            return response

        #### Add the target_id
        if parameters['target_id'] is not None:
            if parameters['target_id'] not in ids:
                response.error(f"While trying to add QEdge, there is no QNode with id {parameters['target_id']}", error_code="UnknownTargetId")
                return response
            qedge.target_id = parameters['target_id']
        else:
            response.error(f"While trying to add QEdge, target_id is a required parameter", error_code="MissingTargetId")
            return response

        #### Add the type if any. Need to verify it's an allowed type. FIXME
        if parameters['type'] is not None:
            qedge.type = parameters['type']

        #### Add it to the query_graph edge list
        message.query_graph.edges.append(qedge)

        #### Return the response
        return response


    ###############################################################################################
    #### Get the next free edge id like eXX where XX is a zero-padded integer starting with 00
    def __get_next_free_edge_id(self):

        #### Set up local references to the message and verify the query_graph nodes
        message = self.message
        if message.query_graph is None:
            message.query_graph = QueryGraph()
            message.query_graph.nodes = []
            message.query_graph.edges = []
        if message.query_graph.edges is None:
            message.query_graph.edges = []
        qedges = message.query_graph.edges

        #### Loop over the nodes making a dict of the ids
        ids = {}
        for qedge in qedges:
            id = qedge.id
            ids[id] = 1

        #### Find the first unused id
        index = 0
        while 1:
            pad = '0'
            if index > 9:
                pad = ''
            potential_edge_id = f"e{pad}{str(index)}"
            if potential_edge_id not in ids:
                return potential_edge_id
            index += 1


    ###############################################################################################
    #### Remove a QEdge
    def remove_qedge(self, message, input_parameters, describe=False):
        """
        Removes a QEdge object in the QueryGraph inside the Message object
        :return: Response object with execution information
        :rtype: Response
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'remove_qedge()',
            'description': """The `remove_qedge` command removes a QEdge from the QueryGraph in the Message object. Currently
                the only way to specify the desired edge to remove it by its id.""",
            'parameters': {
                'id': { 
                    'is_required': True,
                    'examples': [ 'e00', 'e01' ],
                    'default': '',
                    'type': 'string',
                    'description': """The id of the QEdge to remove, such as e00, e01, e02, etc.""",
                    },
           }
        }

        if describe:
            return command_definition


        #### Define a default response
        response = Response()
        self.response = response
        self.message = message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'id': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Now apply the filters. Order of operations is probably quite important
        #### Scalar value filters probably come first like minimum_confidence, then complex logic filters
        #### based on edge or node properties, and then finally maximum_results
        response.info(f"Removing QueryEdge with parameters {parameters}")

        #### Make sure there's a query_graph already here
        if message.query_graph is None:
            response.error(f"While trying to remove a QEdge, there is no QueryGraph", error_code="QueryGraphNotFound")
            return response
        if message.query_graph.edges is None:
            response.error(f"While trying to remove a QEdge, there are no edges in the QueryGraph", error_code="NoEdgesFound")
            return response


        #### Find the QEdge to delete
        qedge_to_delete = None
        i = 0
        for qedge in message.query_graph.edges:
            if qedge.id == parameters['id']:
                qedge_to_delete = i
            i += 1

        if qedge_to_delete is not None:
            del message.query_graph.edges[qedge_to_delete]
        else:
            response.error(f"While trying to remove a QEdge, no QEdge with id {parameters['id']} was found", error_code="QEdgeIdNotfound")
            return response

        #### Return the response
        return response


    ###############################################################################################
    #### Fetch a message by its URI, return the message
    def fetch_message(self, message_uri):

        result = self.apply_fetch_message(self.message, { 'uri': message_uri })
        return self.message


    #### Fetch a message by its URI, return a full response
    def apply_fetch_message(self, message, input_parameters, describe=False):
        """
        Adds a new QEdge object to the QueryGraph inside the Message object
        :return: Response object with execution information
        :rtype: Response
        """

        # #### Command definition for autogenerated documentation
        command_definition = {
            'dsl_command': 'fetch_message()',
            'description': """The `fetch_message` command fetches a remote Message by its id and can then allow further processing on it.""",
            'parameters': {
                'id': { 
                    'is_required': True,
                    'examples': [ 'https://arax.ncats.io/api/rtx/v1/message/3164' ],
                    'default': '',
                    'type': 'string',
                    'description': """A URL/URI that identifies the Message to be fetched""",
                    },
            }
        }

        if describe:
            return command_definition


        #### Define a default response
        response = Response()
        self.response = response
        self.message = message

        #### Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        #### Define a complete set of allowed parameters and their defaults
        parameters = {
            'uri': None,
        }

        #### Loop through the input_parameters and override the defaults and make sure they are allowed
        for key,value in input_parameters.items():
            if key not in parameters:
                response.error(f"Supplied parameter {key} is not permitted", error_code="UnknownParameter")
            else:
                parameters[key] = value
        #### Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        #### Store these final parameters for convenience
        response.data['parameters'] = parameters
        self.parameters = parameters


        #### Basic checks on arguments
        message_uri = input_parameters['uri']
        if not isinstance(message_uri, str):
            response.error("Provided parameter is not a string", error_code="ParameterNotString")
            return response

        response.info(f"Fetching Message via GET to '{message_uri}'")
        response_content = requests.get(message_uri, headers={'accept': 'application/json'})
        status_code = response_content.status_code

        if status_code != 200:
            response.error(f"GET to '{message_uri}' returned HTTP code {status_code} and content '{response_content.content}'", error_code="GETFailed")
            response.error(f"GET to '{message_uri}' returned HTTP code {status_code}", error_code="GETFailed")
            return response

        #### Unpack the response content into a dict and dump
        try:
            response_dict = response_content.json()
            message = self.from_dict(response_dict)
        except:
            response.error(f"Error converting response from '{message_uri}' to objects from content", error_code="UnableToParseContent")
            return response

        #### Store the decoded message and return response
        self.message = message
        n_results = 0
        n_qg_nodes = 0
        n_kg_nodes = 0
        if message.results is not None and isinstance(message.results,list):
            n_results = len(message.results)
        if message.query_graph is not None and isinstance(message.query_graph,QueryGraph) and isinstance(message.query_graph.nodes,list):
            n_qg_nodes = len(message.query_graph.nodes)
        if message.knowledge_graph is not None and isinstance(message.knowledge_graph,KnowledgeGraph) and isinstance(message.knowledge_graph.nodes,list):
            n_kg_nodes = len(message.knowledge_graph.nodes)
        response.info(f"Retreived Message with {n_qg_nodes} QueryGraph nodes, {n_kg_nodes} KnowledgeGraph nodes, and {n_results} results")
        return response


    #### Convert a Message as a dict to a Message as objects
    def from_dict(self, message):

        if str(message.__class__) != "<class 'swagger_server.models.message.Message'>":
            message = Message().from_dict(message)
        message.query_graph = QueryGraph().from_dict(message.query_graph)
        message.knowledge_graph = KnowledgeGraph().from_dict(message.knowledge_graph)

        #### This is an unfortunate hack that fixes qnode.curie entries
        #### Officially a curie can be a str or a list. But Swagger 2.0 only permits one type and we set it to str
        #### so when it gets converted from_dict, the list gets converted to a str because that's its type
        #### Here we force it back. This should no longer be needed when we are properly on OpenAPI 3.0
        if message.query_graph is not None and message.query_graph.nodes is not None:
            for qnode in message.query_graph.nodes:
                if qnode.curie is not None and isinstance(qnode.curie,str):
                    if qnode.curie[0:2] == "['":
                        try:
                            qnode.curie = ast.literal_eval(qnode.curie)
                        except:
                            pass

        #new_nodes = []
        #for qnode in message.query_graph.nodes:
        #    print(type(qnode))
        #    new_nodes.append(QNode().from_dict(qnode))
        #message.query_graph.nodes = new_nodes
        #for qedge in message.query_graph.edges:
        #    new_edges.append(QEdge().from_dict(qedge))
        #message.query_graph.edges = new_edges

        if message.results is not None:
            for result in message.results:
                if result.result_graph is not None:
                    #eprint(str(result.result_graph.__class__))
                    if str(result.result_graph.__class__) != "<class 'swagger_server.models.knowledge_graph.KnowledgeGraph'>":
                        result.result_graph = KnowledgeGraph().from_dict(result.result_graph)

        return message



##########################################################################################
def main():

    #### Testing true/false
    #options = [ 'true', 'false', 'True', 'False', 'TRUE', 'FALSE', 'T', 'F', 'yes', 'no', 'y', 'n', 'toon' ]
    #for option in options:
    #    interpretation = ( option.lower() == 'true' or option.lower() == 't' )
    #    print(f"{option}\t{interpretation}")
    #exit()

    #### Create a response object
    response = Response()

    #### Test fetch_message()
    if False:
        messenger = ARAXMessenger()
        result = messenger.apply_fetch_message(messenger.message, { 'uri': 'https://arax.ncats.io/api/rtx/v1/message/3000'} )
        response.merge(result)
        if result.status != 'OK':
            print(response.show(level=Response.DEBUG))
            return response
        message = messenger.message
        print(response.show(level=Response.DEBUG))
        #print(json.dumps(message.to_dict(),sort_keys=True,indent=2))
        return

    #### Create a default ARAX Message
    messenger = ARAXMessenger()
    result = messenger.create_message()
    response.merge(result)
    if result.status != 'OK':
        print(response.show(level=Response.DEBUG))
        return response
    message = messenger.message

    #### Some qnode examples
    parameters_sets = [
#        { 'curie': 'DOID:9281'},
        { 'curie': 'Orphanet:673'},
        { 'name': 'acetaminophen'},
        { 'curie': 'NCIT:C198'},
        { 'curie': 'UMLS:C4710278'},
        { 'type': 'protein', 'id': 'n10'},
        { 'curie': ['UniProtKB:P14136','UniProtKB:P35579'] },
        { 'curie': ['UniProtKB:P14136','UniProtKB:P35579'], 'is_set': 'false' },
    ]

    for parameter in parameters_sets:
        #### Add a QNode
        result = messenger.add_qnode(message, parameter)
        response.merge(result)
        if result.status != 'OK':
            print(response.show(level=Response.DEBUG))
            return response

    #### Some qedge examples
    parameters_sets = [
        { 'source_id': 'n00', 'target_id': 'n01' },
        { 'source_id': 'n01', 'target_id': 'n10', 'type': 'treats' },
   ]

    for parameter in parameters_sets:
        #### Add a QEdge
        result = messenger.add_qedge(message, parameter)
        response.merge(result)
        if result.status != 'OK':
            print(response.show(level=Response.DEBUG))
            return response

    #### Delete one of the edges
    result = messenger.remove_qedge(message, { 'id': 'e00' } )
    response.merge(result)
    if result.status != 'OK':
        print(response.show(level=Response.DEBUG))
        return response


    #### Show the final result
    print(response.show(level=Response.DEBUG))
    print(json.dumps(message.to_dict(),sort_keys=True,indent=2))


if __name__ == "__main__": main()
