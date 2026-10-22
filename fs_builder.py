import os
from fs_node import FileNode


def build_fs_tree(root_path, one_file_system=True):
    """
    Builds the file system tree from a given root directory.
    Returns the root FileNode object.

    By default the scan stays on the root's filesystem, like `du -x`:
    directories where another filesystem is mounted (/proc, network
    shares, external drives) are recorded but not scanned. Pass
    one_file_system=False to cross them.

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

    root_stat = os.stat(root_path)
    if not os.path.isdir(root_path):
        return FileNode(name, is_file=True, size=root_stat.st_size,
                        disk_usage=_disk_usage(root_stat))

    root = FileNode(name, disk_usage=_disk_usage(root_stat))
    root_dev = _device(root_path) if one_file_system else None
    seen_inodes = set()

    # Each stack item is (node, path, parent, expanded). A directory is popped
    # twice: first to push its children, then again (expanded=True) once its
    # whole subtree is done, at which point it is attached to its parent.
    # Attaching only completed nodes keeps the post-order size aggregation
    # that add_child relies on.
    stack = [(root, root_path, None, False)]
    while stack:
        node, path, parent, expanded = stack.pop()

        if node.is_file or node.is_mount or expanded:
            if parent is not None:
                parent.add_child(node)
            continue

        stack.append((node, path, parent, True))
        # Children are created in name order, so of two hard-linked names in
        # one directory the first alphabetically carries the bytes.
        children = []
        for entry in _scan_dir(path):
            child = _make_node(entry, seen_inodes, root_dev)
            if child is not None:
                children.append((child, entry.path, node, False))
        # Pushed in reverse so they pop (and are attached) in name order.
        stack.extend(reversed(children))

    return root


def _scan_dir(dir_path):
    try:
        with os.scandir(dir_path) as it:
            return sorted(it, key=lambda e: e.name)
    except OSError:
        return []


def _device(path):
    return os.stat(path).st_dev


def _disk_usage(st):
    """
    Bytes allocated on disk. st_blocks is always in 512-byte units,
    whatever the filesystem's block size. Platforms without st_blocks
    (Windows) fall back to the logical size.
    """
    blocks = getattr(st, "st_blocks", None)
    return st.st_size if blocks is None else blocks * 512


def _make_node(entry, seen_inodes, root_dev):
    """
    Creates the FileNode for a directory entry, or returns None if the entry
    cannot be read. root_dev is the root's device id, or None to allow
    crossing into other filesystems.
    """
    try:
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return None

    if entry.is_dir(follow_symlinks=False):
        if root_dev is not None and st.st_dev != root_dev:
            # A different device id means another filesystem is mounted here.
            return FileNode(entry.name, is_mount=True)
        # A directory's own blocks (its list of entries) count too, as in du.
        return FileNode(entry.name, disk_usage=_disk_usage(st))

    if st.st_nlink > 1:
        # Same (device, inode) pair means the same data on disk.
        key = (st.st_dev, st.st_ino)
        if key in seen_inodes:
            return FileNode(entry.name, is_file=True, is_hardlink=True)
        seen_inodes.add(key)
    return FileNode(entry.name, is_file=True, size=st.st_size,
                    disk_usage=_disk_usage(st))
