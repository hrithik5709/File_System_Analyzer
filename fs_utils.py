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


def walk(node):
    """
    Iterative pre-order traversal. Yields (path, depth, node) for every node,
    parents before children and children in order.

    Uses an explicit stack instead of recursion, so tree depth is limited
    only by memory, not by Python's recursion limit.
    """
    stack = [(node, node.name, 0)]
    while stack:
        n, path, depth = stack.pop()
        yield path, depth, n
        # Pushed in reverse so the first child is popped (visited) first.
        for child in reversed(n.children):
            stack.append((child, os.path.join(path, child.name), depth + 1))


def print_tree(node):
    """
    Pretty print the tree with sizes.
    """
    for _, depth, n in walk(node):
        print(f"{'  ' * depth}{n}")


def validate_fs_tree(node):
    """
    Validates the file system tree: no cycles, no negative sizes, files have
    no children, and every directory's size equals the sum of its children.
    Raises ValueError if something is wrong.
    """
    seen = set()
    stack = [node]

    while stack:
        n = stack.pop()
        if id(n) in seen:
            raise ValueError("Cycle detected in file system!")
        seen.add(id(n))
        if n.size < 0:
            raise ValueError(f"Invalid size for: {n.name}")
        if n.is_file:
            if n.children:
                raise ValueError(f"File has children: {n.name}")
        else:
            if n.size != sum(child.size for child in n.children):
                raise ValueError(f"Size mismatch for directory: {n.name}")
            stack.extend(n.children)


def search_file(node, name):
    """
    Search for files/directories with the given name.
    Returns list of paths where the name matches.
    """
    return [path for path, _, n in walk(node) if n.name == name]


def flatten_fs(node):
    """
    Flattens the file system and returns a list of (path, size).
    """
    return [(path, n.get_size()) for path, _, n in walk(node)]


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
