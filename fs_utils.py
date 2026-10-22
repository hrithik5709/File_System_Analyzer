import os


def format_size(num_bytes):
    """
    Converts a byte count into a human-readable string, e.g. 1536 -> '1.5 KB'.
    """
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024


def print_tree(node, indent=""):
    """
    Pretty print the tree with sizes.
    """
    print(f"{indent}{node}")
    for child in node.children:
        print_tree(child, indent + "  ")


def validate_fs_tree(node):
    """
    Validates the file system tree: no cycles, no negative sizes, files have
    no children, and every directory's size equals the sum of its children.
    Raises ValueError if something is wrong.
    """
    seen = set()

    def dfs(n):
        if id(n) in seen:
            raise ValueError("Cycle detected in file system!")
        seen.add(id(n))
        if n.size < 0:
            raise ValueError(f"Invalid size for: {n.name}")
        if n.is_file:
            if n.children:
                raise ValueError(f"File has children: {n.name}")
        else:
            for child in n.children:
                dfs(child)
            if n.size != sum(child.size for child in n.children):
                raise ValueError(f"Size mismatch for directory: {n.name}")

    dfs(node)


def search_file(node, name, path="", results=None):
    """
    DFS search for file/directory with the given name.
    Returns list of paths where the name matches.
    """
    if results is None:
        results = []

    curr_path = os.path.join(path, node.name)

    if node.name == name:
        results.append(curr_path)

    for child in node.children:
        search_file(child, name, curr_path, results)

    return results


def flatten_fs(node, path=""):
    """
    Flattens the file system and returns a list of (path, size).
    """
    flattened = []
    current_path = os.path.join(path, node.name)

    flattened.append((current_path, node.get_size()))

    for child in node.children:
        flattened.extend(flatten_fs(child, current_path))

    return flattened


def sort_by_size(node, reverse=True):
    """
    Returns all (path, size) pairs in the file system sorted by size.
    """
    return sorted(flatten_fs(node), key=lambda x: x[1], reverse=reverse)


def filter_by_size(node, min_size=0, max_size=float('inf')):
    """
    Returns (path, size) pairs for files/directories whose size is within
    the given range (inclusive).
    """
    return [(p, s) for p, s in flatten_fs(node) if min_size <= s <= max_size]
