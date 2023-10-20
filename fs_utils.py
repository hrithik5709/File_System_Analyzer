import os
def print_tree(node, indent=""):
    """
    Pretty print the tree with sizes.
    """
    print(f"{indent}{node}")
    for child in node.children:
        print_tree(child, indent + "  ")


def validate_fs_tree(node):
    """
    Validates that the file system tree structure has no cycles and valid sizes.
    Raises ValueError if something is wrong.
    """
    seen = set()

    def dfs(n):
        if id(n) in seen:
            raise ValueError("Cycle detected in file system!")
        seen.add(id(n))
        if n.is_file:
            if n.size < 0:
                raise ValueError(f"Invalid size for file: {n.name}")
        else:
            for child in n.children:
                dfs(child)

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

def sort_by_size(node, reverse=True):
    """
    Returns all nodes in the file system sorted by size.
    """
    result = []

    def dfs(n):
        result.append((n.name, n.get_size()))
        for child in n.children:
            dfs(child)

    dfs(node)
    result.sort(key=lambda x: x[1], reverse=reverse)
    return result

def filter_by_size(node, min_size=0, max_size=float('inf')):
    """
    Returns a list of files/directories whose size is within the given range.
    """
    matches = []
    if node.get_size() >= min_size and node.get_size() <= max_size:
        matches.append((node.name, node.get_size()))

    for child in node.children:
        matches.extend(filter_by_size(child, min_size, max_size))
    
    return matches
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




