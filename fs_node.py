class FileNode:
    """
    A node in the file system tree: either a file or a directory.

    Two sizes are tracked:
    - size: the logical (apparent) size in bytes, what `ls -l` shows.
    - disk_usage: bytes actually allocated on disk, what `du` shows. It is
      smaller for sparse files and usually larger for small files, which
      still occupy a whole block.

    A directory's totals cover everything beneath it. They are accumulated
    as children are added, so get_size() is O(1) instead of re-walking the
    subtree on every call.
    """

    def __init__(self, name, is_file=False, size=0, disk_usage=0,
                 is_hardlink=False, is_mount=False):
        self.name = name
        self.is_file = is_file
        self.size = size
        self.disk_usage = disk_usage
        # True for an extra name of a hard-linked file whose bytes were
        # already counted elsewhere in the tree.
        self.is_hardlink = is_hardlink
        # True for a directory where another filesystem is mounted; it is
        # recorded but not scanned.
        self.is_mount = is_mount
        self.children = []

    def add_child(self, child_node):
        if self.is_file:
            raise ValueError(f"Cannot add a child to file: {self.name}")
        self.children.append(child_node)
        self.size += child_node.size
        self.disk_usage += child_node.disk_usage

    def get_size(self):
        return self.size

    def __repr__(self):
        label = (f"{'[FILE]' if self.is_file else '[DIR]'} {self.name} "
                 f"({self.size} bytes, {self.disk_usage} on disk)")
        if self.is_hardlink:
            label += " [hard link, counted once]"
        if self.is_mount:
            label += " [mount point, not scanned]"
        return label
