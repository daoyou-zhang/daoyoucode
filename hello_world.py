from collections import deque, defaultdict

class GraphNode:
    def __init__(self, value):
        self.value = value
        self.neighbors = []

    def add_neighbor(self, neighbor_node):
        self.neighbors.append(neighbor_node)

    def __repr__(self):
        return f"GraphNode({self.value})"

def bfs_shortest_path(graph, start, end):
    visited = set()
    queue = deque([(start, [start])])

    while queue:
        current, path = queue.popleft()
        if current == end:
            return path
        if current not in visited:
            visited.add(current)
            for neighbor in graph[current]:
                queue.append((neighbor, path + [neighbor]))
    return None

# 创建图结构
nodes = {
    "A": GraphNode("A"),
    "B": GraphNode("B"),
    "C": GraphNode("C"),
    "D": GraphNode("D"),
    "E": GraphNode("E")
}

# 添加边
nodes["A"].add_neighbor(nodes["B"])
nodes["A"].add_neighbor(nodes["C"])
nodes["B"].add_neighbor(nodes["D"])
nodes["B"].add_neighbor(nodes["E"])
nodes["C"].add_neighbor(nodes["E"])

# 构建邻接表
graph = defaultdict(list)
for node in nodes.values():
    for neighbor in node.neighbors:
        graph[node].append(neighbor)

# 打印图结构
print("Graph Structure:")
for node, neighbors in graph.items():
    print(f"{node}: {neighbors}")

# 查找最短路径
start_node = nodes["A"]
end_node = nodes["E"]
shortest_path = bfs_shortest_path(graph, start_node, end_node)
if shortest_path:
    print(f"Shortest path from {start_node} to {end_node}: {' -> '.join(str(node) for node in shortest_path)}")
else:
    print(f"No path found from {start_node} to {end_node}")