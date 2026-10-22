import os
from fs_node import FileNode


def build_fs_tree(root_path):
    """
    Recursively builds the file system tree from a given root directory.
    Returns the root FileNode object.

    Symlinks are recorded as files (using the link's own size) and never
    followed, so symlink loops cannot cause infinite recursion. Entries that
    cannot be read (permission denied, removed mid-scan) are skipped.
    """
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    root_path = os.path.abspath(root_path)
    # basename("/") is "", so fall back to the path itself for the root.
    name = os.path.basename(root_path) or root_path

    if not os.path.isdir(root_path):
        return FileNode(name, is_file=True, size=os.path.getsize(root_path))

    root = FileNode(name)
    _add_children(root, root_path)
    return root


def _add_children(dir_node, dir_path):
    try:
        with os.scandir(dir_path) as it:
            entries = sorted(it, key=lambda e: e.name)
    except OSError:
        return

    for entry in entries:
        try:
            if entry.is_dir(follow_symlinks=False):
                child = FileNode(entry.name)
                _add_children(child, entry.path)
            else:
                size = entry.stat(follow_symlinks=False).st_size
                child = FileNode(entry.name, is_file=True, size=size)
        except OSError:
            continue
        # Children are fully built before being attached, so the parent's
        # size accumulates correctly (post-order aggregation).
        dir_node.add_child(child)
