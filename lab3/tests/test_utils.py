from src.utils import load_graph_from_edges, validate_graph

def test_load_graph():
    edges = [(1, 2), (2, 3)]
    G = load_graph_from_edges(edges)
    assert G.number_of_edges() == 2
    assert 1 in G.nodes()
    assert 3 in G.nodes()

def test_validate_graph():
    G = load_graph_from_edges([(1, 2)])
    assert validate_graph(G)

    empty_graph = load_graph_from_edges([])
    assert not validate_graph(empty_graph)
