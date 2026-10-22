import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fs_builder import build_fs_tree
from fs_node import FileNode
from fs_utils import (
    filter_by_size,
    flatten_fs,
    format_size,
    print_tree,
    search_file,
    sort_by_size,
    validate_fs_tree,
    walk,
)


@pytest.fixture
def sample_dir(tmp_path):
    """
    root/
      a.txt         (10 bytes)
      docs/
        b.txt       (20 bytes)
        nested/
          a.txt     (30 bytes)
      empty/
    """
    root = tmp_path / "root"
    (root / "docs" / "nested").mkdir(parents=True)
    (root / "empty").mkdir()
    (root / "a.txt").write_bytes(b"x" * 10)
    (root / "docs" / "b.txt").write_bytes(b"x" * 20)
    (root / "docs" / "nested" / "a.txt").write_bytes(b"x" * 30)
    return root


def find(node, name):
    if node.name == name:
        return node
    for child in node.children:
        match = find(child, name)
        if match:
            return match
    return None


def test_builds_tree_with_aggregated_sizes(sample_dir):
    root = build_fs_tree(str(sample_dir))
    assert root.name == "root"
    assert root.get_size() == 60
    assert find(root, "docs").get_size() == 50
    assert find(root, "empty").get_size() == 0
    validate_fs_tree(root)


def test_trailing_slash_keeps_root_name(sample_dir):
    root = build_fs_tree(str(sample_dir) + os.sep)
    assert root.name == "root"


def test_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_fs_tree(str(tmp_path / "does-not-exist"))


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unsupported")
def test_symlink_loop_and_broken_link_do_not_crash(sample_dir):
    os.symlink(sample_dir, sample_dir / "docs" / "loop")
    os.symlink(sample_dir / "nowhere", sample_dir / "broken")
    root = build_fs_tree(str(sample_dir))
    loop = find(root, "loop")
    assert loop is not None and loop.is_file
    assert find(root, "broken").is_file
    validate_fs_tree(root)


@pytest.mark.skipif(not hasattr(os, "link"), reason="hard links unsupported")
def test_hard_links_are_counted_once(sample_dir):
    os.link(sample_dir / "docs" / "b.txt", sample_dir / "b_link.txt")
    root = build_fs_tree(str(sample_dir))
    assert root.get_size() == 60
    first, extra = find(root, "b.txt"), find(root, "b_link.txt")
    # Whichever name is visited first carries the bytes ("b_link.txt" sorts
    # before "docs"), the other is kept in the tree as a 0-byte hard link.
    assert (extra.size, extra.is_hardlink) == (20, False)
    assert (first.size, first.is_hardlink) == (0, True)
    validate_fs_tree(root)


def test_deep_directory_does_not_hit_recursion_limit(tmp_path):
    depth = sys.getrecursionlimit() + 100
    top = tmp_path / "deep"
    top.mkdir()
    # os.makedirs is itself recursive and fails at this depth, so build the
    # chain one level at a time.
    current = str(top)
    for _ in range(depth):
        current = os.path.join(current, "d")
        os.mkdir(current)
    with open(os.path.join(current, "leaf.txt"), "wb") as f:
        f.write(b"x" * 7)

    root = build_fs_tree(str(top))
    assert root.get_size() == 7
    assert len(search_file(root, "leaf.txt")) == 1
    validate_fs_tree(root)


def test_utils_handle_very_deep_trees(capsys):
    depth = sys.getrecursionlimit() * 5
    root = node = FileNode("root")
    chain = [root]
    for _ in range(depth):
        child = FileNode("d")
        node.children.append(child)
        chain.append(child)
        node = child
    leaf = FileNode("leaf.txt", is_file=True, size=3)
    node.children.append(leaf)
    for n in chain:
        n.size = 3

    validate_fs_tree(root)
    assert len(flatten_fs(root)) == depth + 2
    assert len(search_file(root, "leaf.txt")) == 1
    print_tree(root)
    assert capsys.readouterr().out.count("\n") == depth + 2


def test_walk_visits_in_preorder(sample_dir):
    root = build_fs_tree(str(sample_dir))
    paths = [p for p, _, _ in walk(root)]
    assert paths == [
        "root",
        os.path.join("root", "a.txt"),
        os.path.join("root", "docs"),
        os.path.join("root", "docs", "b.txt"),
        os.path.join("root", "docs", "nested"),
        os.path.join("root", "docs", "nested", "a.txt"),
        os.path.join("root", "empty"),
    ]


def test_search_finds_all_matches(sample_dir):
    root = build_fs_tree(str(sample_dir))
    assert sorted(search_file(root, "a.txt")) == [
        os.path.join("root", "a.txt"),
        os.path.join("root", "docs", "nested", "a.txt"),
    ]
    assert search_file(root, "missing.txt") == []


def test_sort_by_size(sample_dir):
    root = build_fs_tree(str(sample_dir))
    sizes = [size for _, size in sort_by_size(root)]
    assert sizes == sorted(sizes, reverse=True)
    assert sort_by_size(root)[0] == ("root", 60)
    assert sort_by_size(root, reverse=False)[-1] == ("root", 60)


def test_filter_by_size_is_inclusive(sample_dir):
    root = build_fs_tree(str(sample_dir))
    paths = {p for p, _ in filter_by_size(root, 20, 30)}
    assert paths == {
        os.path.join("root", "docs", "b.txt"),
        os.path.join("root", "docs", "nested", "a.txt"),
        os.path.join("root", "docs", "nested"),
    }


def test_flatten_includes_every_node(sample_dir):
    root = build_fs_tree(str(sample_dir))
    assert len(flatten_fs(root)) == 7


def test_validate_detects_cycle():
    root = FileNode("root")
    child = FileNode("child")
    root.add_child(child)
    child.children.append(root)
    with pytest.raises(ValueError, match="Cycle"):
        validate_fs_tree(root)


def test_validate_detects_size_mismatch():
    root = FileNode("root")
    root.add_child(FileNode("f", is_file=True, size=5))
    root.size = 999
    with pytest.raises(ValueError, match="Size mismatch"):
        validate_fs_tree(root)


def test_cannot_add_child_to_file():
    with pytest.raises(ValueError):
        FileNode("f", is_file=True).add_child(FileNode("x"))


@pytest.mark.parametrize("num_bytes, expected", [
    (0, "0 B"),
    (1023, "1023 B"),
    (1536, "1.5 KB"),
    (5 * 1024 ** 3, "5.0 GB"),
])
def test_format_size(num_bytes, expected):
    assert format_size(num_bytes) == expected
