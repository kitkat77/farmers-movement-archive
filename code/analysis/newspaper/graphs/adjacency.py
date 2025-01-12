import spacy
import os
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx


# return true if article is relevant, false otherwise
def check_article_relevance(title, desc):
	keywords = [
	'kisan sabha',
	'bku',
	'tikri', 
	'singhu', 
	'anti-farmer',
	'agri-reform',
	'farm bill',
	'farm bills',
	'farmers bills',
	'farmers\' bills',
	'farm policy',
	'farm policies',
	'pro-farmer',
	'Essential Commodities (Amendment) Bill, 2020',
	'Essential Commodities Bill, 2020',
	'Essential Commodities Act, 2020',
	'agri bill',
	'agri ordinance',
	'farm ordinance',
	'trolley times',
	'Kisan Sangharsh Committee',
	'Kisan Bachao Morcha',
	'Kisan Mazdoor Sangharsh Committee',
	'Jai Kisan Andolan',
	'Punjab Kisan Union',
	'Kirti Kisan Union',
	'Terai Kisan Sangathan',
	'All India Kisan Sabha',
	'Mahila Kisan Adhikar Manch',
	'Doaba Kisan Samiti',
	'Rakesh Tikait',
	'Bhartiya Kisan Union']

	title = title.lower()
	desc = desc.lower()
	for keyword in keywords:
		keyword = keyword.lower()
		if keyword in title or keyword in desc:
			return True
	return False

# get list of text from all relevant articles
def get_relevant_text(filepath):
	file = open(filepath, 'r')
	lines = file.readlines()
	file.close()
	all_articles = []
	for line in lines:
		try:
			parts = line.strip().split('||')
			title, desc = parts[2], parts[3]
		except:
			continue
		if check_article_relevance(title, desc):
			all_articles.append(desc)
	return all_articles

# load entities and their counts from path==filename
def load_month_entities(filename):
	f = open(filename, 'r')
	lines = [line for line in f.readlines()]
	lines = lines[0:70]
	f.close()

	ners = []
	ner_counts = {}
	for line in lines:
		ners.append(line.split('||')[1])
		ner_counts[ners[-1]] = int(line.split('||')[2].strip())
	return ners, ner_counts

# add relation between ner1 and ner2 to ner_counts and relation_counts
def add_relation(ner1, ner2, ner_counts, relation_counts):
	key = frozenset([ner1, ner2])
	if key not in relation_counts.keys():
		relation_counts[key] = 0
	relation_counts[key] += 1
	
	if ner1 not in ner_counts.keys():
		ner_counts[ner1] = 0
	ner_counts[ner1] += 1

	if ner2 not in ner_counts.keys():
		ner_counts[ner2] = 0
	ner_counts[ner2] += 1
	return ner_counts, relation_counts

# get relations in one particular article (doc==text of article)
# and update ner_counts and relation counts
def get_article_relations(doc, ners, ner_counts, relation_counts):
	for ner1 in ners:
		if ner1 not in doc.lower():
			continue
		for ner2 in ners:
			if ner1 == ner2:
				break
			if ner2 not in doc.lower():
				continue
			ner_counts, relation_counts = add_relation(ner1, ner2, ner_counts, relation_counts)
	return ner_counts, relation_counts

# get all relations of a month
def get_month_relations(dir_path, ners):
	filenames = os.listdir(dir_path)
	ner_counts, relation_counts = {}, {}
	for filename in filenames:
		filepath = dir_path + '/' + filename
		articles = get_relevant_text(filepath)
		for article in articles:
			ner_counts, relation_counts = get_article_relations(article, ners, ner_counts, relation_counts)

	sorted_tuples = sorted(relation_counts.items(), key=lambda item: item[1], reverse=True)
	sorted_relation_counts = {k: v for k, v in sorted_tuples}
	return ner_counts, sorted_relation_counts

# print *all* relations in a file
def print_relations(relation_counts, filename):
	file = open(filename + '.txt', 'w')
	for rel in relation_counts:
		ners = [x for x in rel]
		count = relation_counts[rel]
		to_write = '\t'.join([str(count), ners[0], ners[1]]) + '\n'
		file.write(to_write)

# create arrays from 50 most frequent relations
def create_relation_df(relation_counts, limit=50):
	node1 = []
	node2 = []
	edge_labels = {}
	i = 0
	for rel in relation_counts:
		ners = [x for x in rel]
		count = relation_counts[rel]
		node1.append(ners[0])
		node2.append(ners[1])
		edge_labels[(ners[0], ners[1])] = count
		i+=1
		if i==limit:
			break

	return node1, node2, edge_labels

def plot_month_relations(ners, ner_counts, relation_counts, filename):
	node1, node2, edge_labels = create_relation_df(relation_counts)
	edges = [[x, y] for x,y in zip(node1, node2)]

	G = nx.Graph()
	G.add_edges_from(edges)

	nodes = G.nodes()
	max_size = 6000
	max_val = max(ner_counts.values())
	node_sizes = [max_size*(ner_counts[node]/max_val) for node in nodes]

	max_width = 5
	max_val = max(relation_counts.values())
	widths = [max_width*(relation_counts[rel]/max_val) for rel in relation_counts]

	node_colors = []
	for size in node_sizes:
		if size > max_size*0.7:
			node_colors.append('#3cd14e')
		elif size > max_size*0.4:
			node_colors.append('#f95d5d')
		else:
			node_colors.append('#5dbdfb')

	pos = nx.spring_layout(G)
	plt.rcParams["figure.figsize"] = (20,10)
	plt.figure()
	nx.draw(
	    G, pos, edge_color='black', width=widths, linewidths=1,
	    node_size=node_sizes, node_color=node_colors, alpha=0.95,
	    with_labels=True
	)

	nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,font_color='red')
	plt.axis('off')
	plt.savefig(filename + '.png')
	# plt.show()
	plt.close()

def create_directory(dir_path):
	if os.path.isdir(dir_path):
		return
	else:
		os.makedirs(dir_path)

def main_func(dir_path, ner_path, publication):
	print(dir_path)
	month = dir_path.split('/')[-1]

	image_dir = 'images/cooccurrence/' + publication
	create_directory(image_dir)
	image_filename =  image_dir + '/' + month
	
	list_dir = 'relation_lists/' + publication
	create_directory(list_dir)
	list_filename = list_dir + '/' + month

	ners, ner_counts = load_month_entities(ner_path)
	_, relation_counts = get_month_relations(dir_path, ners)
	
	if len(relation_counts) == 0:
		print("no relations found")
		return
	print_relations(relation_counts, list_filename)
	plot_month_relations(ners, ner_counts, relation_counts, image_filename)


dir_path = '../../../../corpus/telegraph/india/'
publication = 'telegraph-india'

for month in os.listdir(dir_path):
	month_path = dir_path + month
	ner_path = 'ner_lists/' + publication + '/' + month + '.txt'
	main_func(month_path, ner_path, publication)

# ner_path = 'ner_lists/hindu-01-2021.txt'
# dir_path = '../../../../corpus/hindu/01-2021'

# ner_path = 'ner_lists/toi-01-2021.txt'
# dir_path = '../../../../corpus/timesofindia/01-2021'

# main_func(dir_path, ner_path)