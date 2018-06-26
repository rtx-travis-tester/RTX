# test script for local stuff
import os
import sys
import argparse
import ReasoningUtilities as RU
import FormatOutput
import networkx as nx
from QueryCOHD import QueryCOHD
from COHDUtilities import COHDUtilities
import SimilarNodesInCommon
import CustomExceptions
import numpy as np
import fisher_exact

disease_id = "OMIM:605724"
use_json = False

num_omim_keep = 15  # number of genetic conditions to keep
num_protein_keep = 15  # number of implicated proteins to keep
num_pathways_keep = 15  # number of pathways to keep
num_pathway_proteins_selected = 15  # number of proteins enriched for the above pathways to select
num_drugs_keep = 15  # number of drugs that target those proteins to keep

# The kinds of paths we're looking for
path_type = ["gene_mutations_contribute_to", "protein", "participates_in", "pathway", "participates_in",
			 "protein", "physically_interacts_with", "chemical_substance"]

# Initialize the response class
response = FormatOutput.FormatResponse(6)
response.response.table_column_names = ["disease name", "disease ID", "drug name", "drug ID", "confidence"]

# get the description of the disease
disease_description = RU.get_node_property(disease_id, 'name')

# Find symptoms of disease
symptoms = RU.get_one_hop_target("disease", disease_id, "phenotypic_feature", "has_phenotype")

# Find diseases enriched for that phenotype
fisher_res = fisher_exact.fisher_exact(symptoms, "phenotypic_feature", "disease", rel_type="has_phenotype")
fisher_res_tuples_sorted = []
for key in fisher_res.keys():
	odds, prob = fisher_res[key]
	fisher_res_tuples_sorted.append((key, prob))
fisher_res_tuples_sorted.sort(key=lambda x: x[1])

# select only the omims from that, making sure they are on the kinds of paths we want
genetic_diseases_selected = []
num_selected = 0
for id, prob in fisher_res_tuples_sorted:
	if id.split(":")[0] == "OMIM":
		if RU.paths_of_type_source_fixed_target_free_exists(id, "disease", path_type, limit=1):
			genetic_diseases_selected.append(id)
			num_selected += 1
	if num_selected >= num_omim_keep:
		break

# find the most representative proteins in these diseases
fisher_res = fisher_exact.fisher_exact(genetic_diseases_selected, "disease", "protein",
									   rel_type="gene_mutations_contribute_to")
fisher_res_tuples_sorted = []
for key in fisher_res.keys():
	odds, prob = fisher_res[key]
	fisher_res_tuples_sorted.append((key, prob))
fisher_res_tuples_sorted.sort(key=lambda x: x[1])
implicated_proteins_selected = []
num_selected = 0
path_type = ["participates_in", "pathway", "participates_in",
			 "protein", "physically_interacts_with", "chemical_substance"]
for id, prob in fisher_res_tuples_sorted:
	if RU.paths_of_type_source_fixed_target_free_exists(id, "protein", path_type, limit=1):
		implicated_proteins_selected.append(id)
		num_selected += 1
	if num_selected >= num_protein_keep:
		break

# find enriched pathways from those proteins
fisher_res = fisher_exact.fisher_exact(implicated_proteins_selected, "protein", "pathway",
									   rel_type="participates_in")
fisher_res_tuples_sorted = []
for key in fisher_res.keys():
	odds, prob = fisher_res[key]
	fisher_res_tuples_sorted.append((key, prob))
fisher_res_tuples_sorted.sort(key=lambda x: x[1])
pathways_selected = []
num_selected = 0
path_type = ["participates_in", "protein", "physically_interacts_with", "chemical_substance"]
for id, prob in fisher_res_tuples_sorted:
	if RU.paths_of_type_source_fixed_target_free_exists(id, "pathway", path_type, limit=1):
		pathways_selected.append(id)
		num_selected += 1
	if num_selected >= num_pathways_keep:
		break

# find proteins enriched for those pathways
fisher_res = fisher_exact.fisher_exact(pathways_selected, "pathway", "protein",
									   rel_type="participates_in")
fisher_res_tuples_sorted = []
for key in fisher_res.keys():
	odds, prob = fisher_res[key]
	fisher_res_tuples_sorted.append((key, prob))
fisher_res_tuples_sorted.sort(key=lambda x: x[1])
pathway_proteins_selected = []
num_selected = 0
path_type = ["physically_interacts_with", "chemical_substance"]
for id, prob in fisher_res_tuples_sorted:
	if RU.paths_of_type_source_fixed_target_free_exists(id, "protein", path_type, limit=1):
		pathway_proteins_selected.append(id)  # TODO: could also make sure this is not one of the proteins from above
		num_selected += 1
	if num_selected >= num_pathway_proteins_selected:
		break

# find drugs enriched for targeting those proteins
fisher_res = fisher_exact.fisher_exact(pathway_proteins_selected, "protein", "chemical_substance",
									   rel_type="physically_interacts_with")
fisher_res_tuples_sorted = []
for key in fisher_res.keys():
	odds, prob = fisher_res[key]
	fisher_res_tuples_sorted.append((key, prob))
fisher_res_tuples_sorted.sort(key=lambda x: x[1])
drugs_selected = []
num_selected = 0
for id, prob in fisher_res_tuples_sorted:
	drugs_selected.append(id)
	num_selected += 1
	if num_selected >= num_drugs_keep:
		break

# print out the results
if not use_json:
	for drug in drugs_selected:
		name = RU.get_node_property(drug, "name", node_label="chemical_substance")
		print("%s\n" % name)
else:
	path_type = ["gene_mutations_contribute_to", "protein", "participates_in", "pathway", "participates_in",
			"protein", "physically_interacts_with", "chemical_substance"]
	for drug_id in drugs_selected:
		drug_description = RU.get_node_property(drug_id, "name", node_label="chemical_substance")
		g = RU.return_subgraph_through_node_labels(disease_id, "disease", drug_id, "chemical_substance",
										["protein", "pathway", "protein"],
										with_rel=["disease", "gene_mutations_contribute_to", "protein"],
										directed=False)
		res = response.add_subgraph(g.nodes(data=True), g.edges(data=True), "The drug %s is predicted to treat %s." % (drug_description, disease_description), "-1",
									return_result=True)
		res.essence = "%s" % drug_description  # populate with essence of question result
		row_data = []  # initialize the row data
		row_data.append("%s" % disease_description)
		row_data.append("%s" % disease_id)
		row_data.append("%s" % drug_description)
		row_data.append("%s" % drug_id)
		row_data.append("%f" % -1)
		res.row_data = row_data