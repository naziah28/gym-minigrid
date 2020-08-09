import networkx as nx

path=[
    (1, 1), (2, 1), (5, 1), (6, 1), (7, 1), (8, 1),(9,1), (10,1),
    (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (10, 2),
    (1, 3), (5, 3), (10, 3),
    (1, 4), (5, 4), (10, 4),
    (1, 5), (5, 5), (10, 5),
    (1, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6), (10, 6),
    (1, 7), (7, 7), (10, 7),
    (1, 8), (7, 8), (10, 8),
    (1, 9), (2, 9), (3, 9), (4, 9), (5, 9), (6, 9), (7, 9), (10, 9),
    (1, 10), (7, 10), (8, 10), (9, 10), (10, 10)]


def get_graph(path_nodes): 
	G = nx.Graph()


	# Add all nodes into graph 
	for coord in path: 
		G.add_node(coord)

	for node_a in path: 
		for node_b in path: 
			# make sure they not the same node 
			if node_a != node_b: 
				if (node_a[0] == node_b[0] and abs(node_a[1]-node_b[1]) == 1) or \
				((node_a[1] == node_b[1]) and (abs(node_a[0]-node_b[0])==1)):
					G.add_edge(node_a, node_b)

	return G

G = get_graph(path)
print(nx.shortest_path(G, source=(1,1), target=(10,10)))

