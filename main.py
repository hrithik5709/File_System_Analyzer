import argparse
import os
from fs_builder import build_fs_tree
from fs_utils import (
    print_tree,
    validate_fs_tree,
    search_file,
    filter_by_size,
    sort_by_size,
    flatten_fs,
    format_size,
)


def read_int(prompt, default=None):
    """
    Prompts until the user enters a non-negative integer.
    An empty answer returns the default, if one is given.
    """
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        if raw.isdigit():
            return int(raw)
        print("⚠️ Please enter a non-negative whole number.")


def print_entries(entries):
    for path, size in entries:
        print(f"{path}: {format_size(size)} ({size} bytes)")


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze a directory tree.")
    parser.add_argument("path", nargs="?", help="directory to scan (prompted if omitted)")
    parser.add_argument("--cross-mounts", action="store_true",
                        help="also scan other filesystems mounted inside the directory")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = args.path or input("📂 Enter the path to the root directory: ").strip()

    if not os.path.isdir(root_path):
        print("❌ Invalid path! Please enter a valid directory.")
        return

    print("\n📦 Building File System Tree...")
    root = build_fs_tree(root_path, one_file_system=not args.cross_mounts)

    print("\n✅ Validating File System Tree...")
    try:
        validate_fs_tree(root)
        print("✅ Validation successful.\n")
    except ValueError as ve:
        print(f"❌ Validation Error: {ve}")
        return

    while True:
        print("\n===== File System Analyzer CLI =====")
        print("1. 📊 View File System Tree")
        print("2. 📏 Show Total Size")
        print("3. 🔍 Search for File/Directory")
        print("4. 🧮 Filter by Size Range")
        print("5. 📂 Sort by Size")
        print("6. 📝 Flattened View")
        print("0. ❌ Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            print_tree(root)
        elif choice == '2':
            print(f"\n📏 Total Size of '{root.name}': {format_size(root.get_size())} ({root.get_size()} bytes)")
            print(f"💽 Disk Usage: {format_size(root.disk_usage)} ({root.disk_usage} bytes)")
        elif choice == '3':
            name = input("🔍 Enter the name to search: ").strip()
            result = search_file(root, name)
            if result:
                print(f"✅ Found {len(result)} match(es):")
                for path in result:
                    print(f"  {path}")
            else:
                print("❌ Not found.")
        elif choice == '4':
            min_size = read_int("Enter minimum size (bytes): ")
            max_size = read_int("Enter maximum size (bytes, blank for no limit): ", default=float('inf'))
            if min_size > max_size:
                print("⚠️ Minimum size cannot be greater than maximum size.")
                continue
            results = filter_by_size(root, min_size, max_size)
            if results:
                print("\n🧮 Filtered Results:")
                print_entries(results)
            else:
                print("❌ No matching files/directories found.")
        elif choice == '5':
            order = input("Sort in descending order? (Y/n): ").strip().lower()
            results = sort_by_size(root, reverse=(order != 'n'))
            print("\n📂 Sorted Results:")
            print_entries(results)
        elif choice == '6':
            flattened = flatten_fs(root)
            print("\n📝 Flattened View:")
            print_entries(flattened)
        elif choice == '0':
            print("👋 Exiting... Goodbye!")
            break
        else:
            print("⚠️ Invalid option! Try again.")

if __name__ == "__main__":
    main()
