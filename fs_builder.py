import os
from fs_node import FileNode

def build_fs_tree(root_path):
    """
    Recursively builds the file system tree from a given root directory.
    Returns the root FileNode object.
    """
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    root = FileNode(os.path.basename(root_path), is_file=os.path.isfile(root_path))

    if os.path.isdir(root_path):
        try:
            entries = os.listdir(root_path)
        except PermissionError:
            entries = []

        for entry in entries:
            entry_path = os.path.join(root_path, entry)
            child_node = build_fs_tree(entry_path)
            root.add_child(child_node)

        root.size = sum(child.size for child in root.children)

    else:
        root.size = os.path.getsize(root_path)

    return root











