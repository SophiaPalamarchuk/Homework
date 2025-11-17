import networkx as nx
from collections import deque

class GraphAnalyzer:
    def __init__(self, graph: nx.DiGraph):
        if not isinstance(graph, nx.DiGraph):
            raise TypeError("Graph must be a networkx.DiGraph")
        self.graph = graph

    def bfs(self, start):
        """Пошук в ширину"""
        visited = []
        queue = deque([start])
        visited_set = set()

        while queue:
            node = queue.popleft()
            if node not in visited_set:
                visited.append(node)
                visited_set.add(node)
                for neighbor in self.graph.successors(node):
                    queue.append(neighbor)

        return visited

    def dfs(self, start):
        """Пошук в глибину"""
        visited = []
        stack = [start]
        visited_set = set()

        while stack:
            node = stack.pop()
            if node not in visited_set:
                visited.append(node)
                visited_set.add(node)
                for neighbor in reversed(list(self.graph.successors(node))):
                    stack.append(neighbor)

        return visited

    def connected_components(self):
        """Пошук компонент зв’язності (ігноруємо орієнтацію)"""
        undirected = self.graph.to_undirected()
        components = list(nx.connected_components(undirected))
        return components
