import os
from fs_builder import build_fs_tree
from fs_utils import (
    print_tree,
    validate_fs_tree,
    search_file,
    filter_by_size,
    sort_by_size,
    flatten_fs
)

def main():
    root_path = input("📂 Enter the path to the root directory: ").strip()

    if not os.path.exists(root_path):
        print("❌ Invalid path! Please enter a valid directory.")
        return

    print("\n📦 Building File System Tree...")
    root = build_fs_tree(root_path)

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
            print(f"\n📏 Total Size of '{root.name}': {root.get_size()} bytes")
        elif choice == '3':
            name = input("🔍 Enter the name to search: ").strip()
            result = search_file(root, name)
            if result:
                print(f"✅ Found: {result}")
            else:
                print("❌ Not found.")
        elif choice == '4':
            min_size = int(input("Enter minimum size (bytes): "))
            max_size = int(input("Enter maximum size (bytes): "))
            results = filter_by_size(root, min_size, max_size)
            if results:
                print("\n🧮 Filtered Results:")
                for name, size in results:
                    print(f"{name}: {size} bytes")
            else:
                print("❌ No matching files/directories found.")
        elif choice == '5':
            order = input("Sort in descending order? (y/n): ").lower()
            results = sort_by_size(root, reverse=(order == 'y'))
            print("\n📂 Sorted Results:")
            for name, size in results:
                print(f"{name}: {size} bytes")
        elif choice == '6':
            flattened = flatten_fs(root)
            print("\n📝 Flattened View:")
            for path, size in flattened:
                print(f"{path} - {size} bytes")
        elif choice == '0':
            print("👋 Exiting... Goodbye!")
            break
        else:
            print("⚠️ Invalid option! Try again.")

if __name__ == "__main__":
    main()
