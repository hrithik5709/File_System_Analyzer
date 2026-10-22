class FileNode:
    """
    A node in the file system tree: either a file or a directory.

    A directory's size is the total size of everything beneath it. It is
    accumulated as children are added, so get_size() is O(1) instead of
    re-walking the subtree on every call.
    """

    def __init__(self, name, is_file=False, size=0, is_hardlink=False):
        self.name = name
        self.is_file = is_file
        self.size = size
        # True for an extra name of a hard-linked file whose bytes were
        # already counted elsewhere in the tree.
        self.is_hardlink = is_hardlink
        self.children = []

    def add_child(self, child_node):
        if self.is_file:
            raise ValueError(f"Cannot add a child to file: {self.name}")
        self.children.append(child_node)
        self.size += child_node.size

    def get_size(self):
        return self.size

    def __repr__(self):
        label = f"{'[FILE]' if self.is_file else '[DIR]'} {self.name} ({self.size} bytes)"
        if self.is_hardlink:
            label += " [hard link, counted once]"
        return label
