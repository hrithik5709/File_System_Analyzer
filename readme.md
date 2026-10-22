# File System Analyzer

A command-line tool that scans a directory and models it as an in-memory tree, so you can view, search, sort and filter its contents by size.

The project mainly demonstrates tree data structures and recursive algorithms (DFS and post-order aggregation) on a real file system.

## Features

| Option | What it does |
| --- | --- |
| 📊 View tree | Prints the full hierarchy with the size of every file and directory |
| 📏 Total size | Total size of the root directory |
| 🔍 Search | Finds every file or directory with a given name and prints its full path |
| 🧮 Filter by size | Lists entries whose size falls within a range (inclusive) |
| 📂 Sort by size | Lists all entries sorted largest-first (or smallest-first) |
| 📝 Flattened view | Lists every path in the tree with its size |

Sizes are shown in both human-readable form and exact bytes, e.g. `1.5 KB (1536 bytes)`.

## Usage

Needs Python 3.6 or newer. There are no runtime dependencies.

```bash
python3 main.py /path/to/directory   # pass the directory as an argument
python3 main.py                      # or enter it when prompted
```

## Project structure

```
fs_node.py      FileNode: one file or directory in the tree
fs_builder.py   build_fs_tree(): scans the disk and builds the tree
fs_utils.py     Operations on the tree: print, validate, search, sort, filter, flatten
main.py         Interactive CLI menu
test/           pytest test suite
```

## Design

**Tree model.** Each `FileNode` is either a file (a leaf with its own size) or a directory (a list of children). A directory's size is the sum of all its children's sizes.

**Size aggregation in O(n).** `build_fs_tree` builds the tree depth-first and attaches each child only once its subtree is complete (post-order). `add_child` adds the child's size to the parent, so each directory's total is computed exactly once during the scan. After that, `get_size()` is O(1), so sorting, filtering and printing are not slowed down by recomputing subtree sizes.

**Robustness.**
- Symlinks are recorded but never followed, so symlink loops can't cause infinite recursion. Broken links don't crash the scan.
- Entries that can't be read (permission denied, deleted mid-scan) are skipped instead of aborting the whole scan.
- Children are sorted by name, so output is the same on every run.

**Validation.** `validate_fs_tree` checks that the tree has no cycles and no negative sizes, that files have no children, and that every directory's size equals the sum of its children.

**Complexity.** For n entries, building the tree and every query (search, filter, flatten) is O(n). Sorting is O(n log n).

## Running tests

```bash
pip install -r requirements.txt
python3 -m pytest test
```

The tests build real directory trees in a temporary folder. They cover size aggregation, search, sort and filter, edge cases (trailing slashes, missing paths, symlink loops, broken links) and validation failures.

## Possible extensions

- Very deep trees could hit Python's recursion limit. An iterative traversal with an explicit stack would remove that limit.
- Scan large directories concurrently.
- Add a non-interactive mode (e.g. `--top 10`) for scripting.
