class FileNode:
    def __init__(self, name, is_file=False, size=0):
        self.name = name
        self.is_file = is_file
        self.size = size
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def get_size(self):
        if self.is_file:
            return self.size
        return sum(child.get_size() for child in self.children)

    def __repr__(self):
        return f"{'[FILE]' if self.is_file else '[DIR]'} {self.name} ({self.get_size()} bytes)"
