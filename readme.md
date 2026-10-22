# File System Analyzer

A command-line tool that scans a directory and models it as an in-memory tree, so you can view, search, sort and filter its contents by size.

The project mainly demonstrates tree data structures and recursive algorithms (DFS and post-order aggregation) on a real file system.

## Features

| Option | What it does |
| --- | --- |
| 📊 View tree | Prints the full hierarchy with the size of every file and directory |
| 📏 Total size | Total logical size of the root directory, plus the space it actually uses on disk |
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
python3 main.py / --cross-mounts     # also scan filesystems mounted inside it
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

**No recursion limit.** Every traversal uses an explicit stack instead of recursion, so a very deep directory tree can't crash with `RecursionError`. Python allows about 1,000 nested calls by default. The builder pushes each directory twice: once to expand its children, and once more to attach it to its parent after its whole subtree is done. That second visit keeps the post-order size aggregation. All the read-only operations (print, search, flatten, sort, filter) share one iterative pre-order `walk()` generator.

**Hard links counted once.** A hard-linked file has several names but its data is stored on disk only once. The builder tracks `(st_dev, st_ino)` pairs it has already seen. The first name found carries the bytes, and any later name stays in the tree marked `[hard link, counted once]` with 0 bytes. This matches how `du` reports disk usage.

**Size vs disk usage.** Every node tracks two numbers. `size` is the logical size, what `ls -l` reports. `disk_usage` is `st_blocks * 512`, the space actually allocated, what `du` reports. They differ for sparse files (a 100 MB file with holes can use a few KB) and for small files (10 bytes still takes a 4 KB block). Directories add their own blocks to `disk_usage`, as `du` does. On real directories the totals match `du -sxB1` to the byte.

**Stays on one filesystem.** Like `du -x`, the scan does not enter directories where another filesystem is mounted. It detects them by a change in `st_dev`. They appear in the tree marked `[mount point, not scanned]`, so pointing the tool at `/` does not wander into `/proc`, `/sys` or network shares. Use `--cross-mounts` to scan them anyway.

**Robustness.**
- Symlinks are recorded but never followed, so symlink loops can't send the scan into an endless loop. Broken links don't crash the scan.
- Entries that can't be read (permission denied, deleted mid-scan) are skipped instead of aborting the whole scan.
- Children are sorted by name, so output is the same on every run.

**Validation.** `validate_fs_tree` checks that the tree has no cycles and no negative sizes, and that files have no children. It also checks that every directory's size equals the sum of its children, and that its disk usage is at least theirs.

**Complexity.** For n entries, building the tree and every query (search, filter, flatten) is O(n). Sorting is O(n log n).

## Running tests

```bash
pip install -r requirements.txt
python3 -m pytest test
```

The tests build real directory trees in a temporary folder. They cover size aggregation, search, sort and filter, and edge cases: trailing slashes, missing paths, symlink loops, broken links, hard links, sparse files, mount points, and trees deeper than Python's recursion limit. One test checks the disk usage total against `du`. They also cover validation failures.

## Possible extensions

- Scan large directories concurrently.
- Add a non-interactive mode (e.g. `--top 10`) for scripting.
