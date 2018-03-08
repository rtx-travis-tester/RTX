# This will be a collection of scripts that can answer various questions
# Start out with easy ones
import ReasoningUtilities as RU


class Q4:

	def answer(self, query_terms):
		"""
		Answer a question of the type "What proteins does drug X target" but is general:
		 what <node X type> does <node Y grounded> <relatioship Z>
		:param query_terms: a triple consisting of a source node name (KG neo4j node name, the target label (KG neo4j
		"node label") and the relationship type (KG neo4j "Relationship type")
		:return:
		"""
		source_name = query_terms[0]
		target_label = query_terms[1]
		relationship_type = query_terms[2]
		# Get label/kind of node the source is
		source_label = RU.get_node_property(source_name, "label")
		# get the actual targets
		targets = RU.get_one_hop_target(source_label, source_name, target_label, relationship_type)
		# Format the results. TODO: cnage this to a call to Eric's output formatter when he's written that
		results_list = list()
		for target in targets:
			results_list.append(
				{'type': 'node',
				 'name': target,
				 'desc': RU.get_node_property(target, "description", node_label=target_label),
				 'prob': 1})  # All these are known to be true
		return results_list

	def describe(self):
		output = "Answers questions of the form: 'What proteins does tranilast target?' and 'What genes are affected by " \
				 "Fanconi anemia?'" + "\n"
		output += "You can ask: 'What X does Y Z?' where X is one of the following: \n"
		for label in RU.get_node_labels():
			output = output + label + "\n"
		output += "\n The term Y is any of the nodes that are in our graph (currently " + str(RU.count_nodes()) + " nodes in total). \n"
		output += "\n The term Z is any relationship of the following kind: \n"
		for rel in RU.get_relationship_types():
			rel_split = rel.split("_")
			for term in rel_split:
				output += term + " "
			output += "\n"
		print(output)
		return






# eg: what proteins does drug X target?
def one_hop_relationship_type(source_name, target_label, relationship_type):
	source_label = RU.get_node_property(source_name, "label")
	targets = RU.get_one_hop_target(source_label, source_name, target_label, relationship_type)
	results_list = list()
	for target in targets:
		results_list.append(
			{'type': 'node',
	 		'name': target,
	 		'desc': RU.get_node_property(target, "description", node_label=target_label),
			 'prob': 1})  # All these are known to be true
	return results_list

#########################################################
# Tests
def test_one_hop_relationship_type():
	res = one_hop_relationship_type("carbetocin", "uniprot_protein", "targets")
	assert res == [{'desc': 'OXTR', 'name': 'P30559', 'type': 'node','prob': 1}]
	res = one_hop_relationship_type("OMIM:263200", "uniprot_protein", "disease_affects")
	known_res = [{'desc': 'PKHD1', 'name': 'P08F94', 'type': 'node','prob': 1}, {'desc': 'DZIP1L', 'name': 'Q8IYY4', 'type': 'node','prob': 1}]
	for item in res:
		assert item in known_res
	for item in known_res:
		assert item in res
	res = one_hop_relationship_type("OMIM:263200", "ncbigene_microrna", "gene_assoc_with")
	assert res == [{'desc': 'MIR1225', 'name': 'NCBIGene:100188847', 'type': 'node','prob': 1}]


def test_suite():
	test_one_hop_relationship_type()