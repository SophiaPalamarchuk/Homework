import networkx as nx
from src.graph_analysis import GraphAnalyzer
from src.utils import load_graph_from_edges

def test_bfs():
    G = load_graph_from_edges([(1,2), (2,3), (1,4)])
    analyzer = GraphAnalyzer(G)
    assert analyzer.bfs(1) == [1, 2, 4, 3]

def dfs(self, start):
    visited = []
    stack = [start]
    visited_set = set()

    while stack:
        node = stack.pop()
        if node not in visited_set:
            visited.append(node)
            visited_set.add(node)
            # важливо: без reversed
            for neighbor in self.graph.successors(node):
                stack.append(neighbor)

    return visited

def test_connected_components():
    G = load_graph_from_edges([(1, 2), (3, 4)])
    analyzer = GraphAnalyzer(G)
    comps = analyzer.connected_components()
    assert len(comps) == 2
    assert {1, 2} in comps
    assert {3, 4} in comps

def test_wrong_graph_type():
    try:
        GraphAnalyzer("not a graph")
        assert False, "Exception must be raised"
    except TypeError:
        assert True
