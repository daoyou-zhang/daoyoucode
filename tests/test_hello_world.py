import unittest
from hello_world import GraphNode, bfs_shortest_path

class TestHelloWorld(unittest.TestCase):
    def setUp(self):
        self.nodes = {
            'A': GraphNode('A'),
            'B': GraphNode('B'),
            'C': GraphNode('C'),
            'D': GraphNode('D'),
            'E': GraphNode('E')
        }
        self.nodes['A'].add_neighbor(self.nodes['B'])
        self.nodes['A'].add_neighbor(self.nodes['C'])
        self.nodes['B'].add_neighbor(self.nodes['D'])
        self.nodes['B'].add_neighbor(self.nodes['E'])
        self.nodes['C'].add_neighbor(self.nodes['E'])
        
        # 构建邻接表
        self.graph = defaultdict(list)
        for node in self.nodes.values():
            for neighbor in node.neighbors:
                self.graph[node].append(neighbor)

    def test_bfs_shortest_path(self):
        start_node = self.nodes['A']
        end_node = self.nodes['E']
        shortest_path = bfs_shortest_path(self.graph, start_node, end_node)
        expected_path = [self.nodes['A'], self.nodes['B'], self.nodes['E']]
        self.assertEqual(shortest_path, expected_path)

if __name__ == '__main__':
    unittest.main()