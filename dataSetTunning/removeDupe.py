import csv
import shutil
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# CHANGE THIS to your actual dataset directory
DATASET_DIR = Path("/home/ezz-mahdy/gitRepos/CV-Model-0/dataSetTunning/DS")

CSV_FILE = DATASET_DIR / "duplicate_images_2ndDS.csv"

# Backup is INSIDE the dataset
BACKUP_DIR = DATASET_DIR / "removed_duplicates"

# First run MUST be True
DRY_RUN = False


# ============================================================
# UNION-FIND
# ============================================================

class UnionFind:

    def __init__(self):
        self.parent = {}

    def add(self, item):
        if item not in self.parent:
            self.parent[item] = item

    def find(self, item):

        if self.parent[item] != item:
            self.parent[item] = self.find(
                self.parent[item]
            )

        return self.parent[item]

    def union(self, a, b):

        self.add(a)
        self.add(b)

        root_a = self.find(a)
        root_b = self.find(b)

        if root_a != root_b:
            self.parent[root_b] = root_a


# ============================================================
# RESOLVE IMAGE PATH
# ============================================================

def resolve_image_path(csv_path):

    csv_path = Path(csv_path)

    # --------------------------------------------------------
    # Case 1:
    # CSV already contains the correct absolute path
    # --------------------------------------------------------

    if csv_path.is_absolute() and csv_path.exists():
        return csv_path.resolve()

    # --------------------------------------------------------
    # Case 2:
    # CSV contains a path relative to dataset
    # --------------------------------------------------------

    candidate = DATASET_DIR / csv_path

    if candidate.exists():
        return candidate.resolve()

    # --------------------------------------------------------
    # Case 3:
    # CSV contains something like:
    #
    # /old/path/dataset/train/images/horse.jpg
    #
    # We only use the part starting at train/valid/test
    # --------------------------------------------------------

    parts = csv_path.parts

    for split in ["train", "valid", "val", "test"]:

        if split in parts:

            index = parts.index(split)

            relative_path = Path(
                *parts[index:]
            )

            candidate = DATASET_DIR / relative_path

            if candidate.exists():
                return candidate.resolve()

    return None


# ============================================================
# FIND LABEL
# ============================================================

def get_label_path(image_path):

    parts = list(image_path.parts)

    if "images" in parts:

        index = parts.index("images")

        parts[index] = "labels"

        label = Path(*parts).with_suffix(".txt")

        if label.exists():
            return label

    # Fallback
    label = image_path.with_suffix(".txt")

    if label.exists():
        return label

    return None


# ============================================================
# READ CSV
# ============================================================

if not CSV_FILE.exists():

    print("ERROR:")
    print(f"CSV not found:")
    print(CSV_FILE)
    exit()


uf = UnionFind()

unresolved = []

print("Reading CSV...\n")

with open(
    CSV_FILE,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        raw1 = row["image_1"]
        raw2 = row["image_2"]

        image1 = resolve_image_path(raw1)
        image2 = resolve_image_path(raw2)

        if image1 is None:
            unresolved.append(raw1)
            continue

        if image2 is None:
            unresolved.append(raw2)
            continue

        uf.union(image1, image2)


# ============================================================
# BUILD GROUPS
# ============================================================

groups = {}

for image in uf.parent:

    root = uf.find(image)

    if root not in groups:
        groups[root] = []

    groups[root].append(image)


print("=" * 70)
print(f"Duplicate groups found: {len(groups)}")
print("=" * 70)


# ============================================================
# SHOW UNRESOLVED
# ============================================================

if unresolved:

    print("\nWARNING:")
    print(
        f"{len(unresolved)} image paths from the CSV "
        "could not be found."
    )

    for path in unresolved[:20]:
        print("  ", path)

    if len(unresolved) > 20:
        print(
            f"  ... and "
            f"{len(unresolved) - 20} more."
        )


# ============================================================
# PROCESS GROUPS
# ============================================================

total_to_remove = 0

for number, images in enumerate(
    groups.values(),
    start=1
):

    images = sorted(images)

    # --------------------------------------------------------
    # KEEP FIRST
    # --------------------------------------------------------

    keep = images[0]

    duplicates = images[1:]

    print("\n" + "=" * 70)

    print(
        f"GROUP {number} "
        f"({len(images)} images)"
    )

    print("\nKEEP:")
    print(f"  {keep}")

    print("\nDUPLICATES:")

    for image in duplicates:

        print(f"  {image}")

    total_to_remove += len(duplicates)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)

print(
    f"Total duplicate images to move: "
    f"{total_to_remove}"
)

print(f"Backup location:")
print(f"  {BACKUP_DIR}")

print("=" * 70)


# ============================================================
# DRY RUN
# ============================================================

if DRY_RUN:

    print("\nDRY RUN")
    print("Nothing has been moved.")

    print("\nIf the paths above are correct,")
    print("change:")

    print("    DRY_RUN = True")

    print("to:")

    print("    DRY_RUN = False")

    print("\nThen run the script again.")

    exit()


# ============================================================
# ACTUAL MOVE
# ============================================================

print("\nStarting removal...\n")

moved_images = 0
moved_labels = 0

for number, images in enumerate(
    groups.values(),
    start=1
):

    images = sorted(images)

    # Keep first
    keep = images[0]

    # Remove the rest
    duplicates = images[1:]

    for image in duplicates:

        print("-" * 60)

        print(f"GROUP {number}")

        print(f"Keeping:")
        print(f"  {keep}")

        print(f"\nMoving image:")
        print(f"  {image}")

        # ----------------------------------------------------
        # IMAGE DESTINATION
        # ----------------------------------------------------

        try:

            relative_image = image.relative_to(
                DATASET_DIR
            )

        except ValueError:

            print(
                "ERROR: Image is outside dataset."
            )

            continue

        destination_image = (
            BACKUP_DIR / relative_image
        )

        destination_image.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.move(
            str(image),
            str(destination_image)
        )

        moved_images += 1

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        label = get_label_path(image)

        if label is not None:

            try:

                relative_label = label.relative_to(
                    DATASET_DIR
                )

            except ValueError:

                print(
                    "  Label outside dataset."
                )

                continue

            destination_label = (
                BACKUP_DIR / relative_label
            )

            destination_label.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            print(f"Moving label:")
            print(f"  {label}")

            shutil.move(
                str(label),
                str(destination_label)
            )

            moved_labels += 1

        else:

            print(
                "WARNING: No YOLO label found."
            )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 70)

print("DONE")

print(
    f"Images moved: {moved_images}"
)

print(
    f"Labels moved: {moved_labels}"
)

print(
    f"\nBackup:"
)

print(
    BACKUP_DIR
)

print("=" * 70)