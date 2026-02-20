class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def __repr__(self):
        return f"TreeNode({self.value})"

def traverse_tree(node, level=0):
    print('  ' * level + str(node))
    for child in sorted(node.children, key=lambda x: x.value):
        traverse_tree(child, level + 1)

# 创建树结构
root = TreeNode("A")
child1 = TreeNode("B")
child2 = TreeNode("C")
grandchild1 = TreeNode("D")
grandchild2 = TreeNode("E")

# 添加子节点
root.add_child(child1)
root.add_child(child2)
child1.add_child(grandchild1)
child1.add_child(grandchild2)

# 遍历树结构
print("Tree Structure:")
traverse_tree(root)