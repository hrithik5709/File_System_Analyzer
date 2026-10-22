import os
from fs_node import FileNode


def build_fs_tree(root_path):
    """
    Builds the file system tree from a given root directory.
    Returns the root FileNode object.

    The walk is iterative (an explicit stack instead of recursion), so very
    deep directory trees cannot hit Python's recursion limit.

    Symlinks are recorded as files (using the link's own size) and never
    followed, so symlink loops cannot cause infinite traversal. Hard links
    are counted once: later names for an already-seen inode are kept in the
    tree but contribute 0 bytes, matching how `du` reports usage. Entries
    that cannot be read (permission denied, removed mid-scan) are skipped.
    """
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    root_path = os.path.abspath(root_path)
    # basename("/") is "", so fall back to the path itself for the root.
    name = os.path.basename(root_path) or root_path

    if not os.path.isdir(root_path):
        return FileNode(name, is_file=True, size=os.path.getsize(root_path))

    root = FileNode(name)
    seen_inodes = set()

    # Each stack item is (node, path, parent, expanded). A directory is popped
    # twice: first to push its children, then again (expanded=True) once its
    # whole subtree is done, at which point it is attached to its parent.
    # Attaching only completed nodes keeps the post-order size aggregation
    # that add_child relies on.
    stack = [(root, root_path, None, False)]
    while stack:
        node, path, parent, expanded = stack.pop()

        if node.is_file or expanded:
            if parent is not None:
                parent.add_child(node)
            continue

        stack.append((node, path, parent, True))
        # Pushed in reverse so they pop (and are attached) in name order.
        for entry in reversed(_scan_dir(path)):
            child = _make_node(entry, seen_inodes)
            if child is not None:
                stack.append((child, entry.path, node, False))

    return root


def _scan_dir(dir_path):
    try:
        with os.scandir(dir_path) as it:
            return sorted(it, key=lambda e: e.name)
    except OSError:
        return []


def _make_node(entry, seen_inodes):
    """
    Creates the FileNode for a directory entry, or returns None if the entry
    cannot be read.
    """
    try:
        if entry.is_dir(follow_symlinks=False):
            return FileNode(entry.name)

        st = entry.stat(follow_symlinks=False)
    except OSError:
        return None

    size = st.st_size
    if st.st_nlink > 1:
        # Same (device, inode) pair means the same data on disk.
        key = (st.st_dev, st.st_ino)
        if key in seen_inodes:
            return FileNode(entry.name, is_file=True, size=0, is_hardlink=True)
        seen_inodes.add(key)
    return FileNode(entry.name, is_file=True, size=size)
